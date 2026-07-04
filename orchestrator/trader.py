"""Genel stateful paper-trading motoru.

Bir strateji config'i + canlı snapshot alır; o AI'ın kendi skoruna göre alım/satım
kararı verir, portföyünü mark-to-market eder, stop/hedef/skor-çıkışı uygular ve
klasörüne standart şemalı portfolio.json yazar. deepseek hariç 3 AI bunu kullanır."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .strategies import score_for
from . import corp_actions

ROOT = Path(__file__).resolve().parent.parent
COMMISSION = 0.002
MIN_TICKET = 300.0


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _pf_path(strategy: dict) -> Path:
    return ROOT / strategy["folder"] / "portfolio.json"


def _load(strategy: dict) -> dict:
    p = _pf_path(strategy)
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if "positions" in raw and "cash" in raw and raw.get("_schema") == "arena":
                return raw
        except Exception:
            pass
    cap = strategy["initial"]
    return {
        "_schema": "arena", "name": strategy["name"] + " Portföyü",
        "strategy": strategy["style"], "initial": cap, "cash": cap,
        "total_value": cap, "return_pct": 0.0, "created": _now(),
        "last_updated": _now(), "positions": [], "trades": [],
    }


def _save(strategy: dict, pf: dict) -> None:
    pf["last_updated"] = _now()
    _pf_path(strategy).write_text(json.dumps(pf, ensure_ascii=False, indent=2), encoding="utf-8")


def _sector_exposure(pf: dict, sector: str) -> float:
    tv = pf["total_value"] or 1.0
    return sum(p["current"] * p["qty"] for p in pf["positions"] if p["sector"] == sector) / tv


def run_strategy(strategy: dict, snapshot: Dict[str, dict]) -> dict:
    """Bir stratejiyi bir döngü ilerletir, portföyü kaydeder ve döndürür."""
    pf = _load(strategy)
    now = _now()

    # skorları hesapla
    scored = {}
    for tk, snap in snapshot.items():
        scored[tk] = score_for(strategy, snap.get("breakdown", {}))

    # 1) mark-to-market (+ şirket-işlemi koruması)
    for p in pf["positions"]:
        snap = snapshot.get(p["ticker"], {})
        new_price = float(snap["price"]) if snap.get("price") else None
        if new_price:
            r = corp_actions.anomaly_ratio(p.get("current") or p.get("entry"), new_price)
            if r is not None:
                corp_actions.adjust(p, r)
                pf["trades"].append({"ts": now, "side": "ADJUST", "ticker": p["ticker"],
                                     "qty": "", "price": round(new_price, 2), "amount": "",
                                     "reason": corp_actions.note(p["ticker"], r)})
            p["current"] = round(new_price, 2)
        p["score"] = scored.get(p["ticker"], p.get("score", 0))

    # 2) çıkışlar: stop / hedef / skor düşüşü
    survivors = []
    for p in pf["positions"]:
        entry = p["entry"] or 1.0
        pnl = (p["current"] - entry) / entry
        sc = scored.get(p["ticker"], 50.0)
        if pnl <= strategy["stop_pct"]:
            _sell(pf, p, p["qty"], now, "STOP-LOSS (%%%.1f)" % (pnl * 100))
        elif pnl >= strategy["target_pct"] and p["qty"] >= 2:
            half = p["qty"] // 2
            _sell(pf, p, half, now, "TAKE-PROFIT +%%%.0f, %%50 satış" % (strategy["target_pct"] * 100))
            p["qty"] -= half
            survivors.append(p)
        elif sc < strategy["sell_threshold"]:
            _sell(pf, p, p["qty"], now, "SKOR düştü (%.0f < %.0f)" % (sc, strategy["sell_threshold"]))
        else:
            survivors.append(p)
    pf["positions"] = survivors
    held = {p["ticker"] for p in pf["positions"]}

    # 3) girişler: skor >= buy_threshold, en yüksekten
    pf["total_value"] = pf["cash"] + sum(p["current"] * p["qty"] for p in pf["positions"])
    candidates = sorted(
        (tk for tk in snapshot if tk not in held and scored.get(tk, 0) >= strategy["buy_threshold"]),
        key=lambda t: scored[t], reverse=True,
    )
    for tk in candidates:
        if len(pf["positions"]) >= strategy["max_positions"]:
            break
        snap = snapshot[tk]
        price = float(snap.get("price") or 0)
        if price <= 0:
            continue
        available = pf["cash"] - pf["total_value"] * strategy["min_cash_pct"]
        if available < MIN_TICKET:
            break
        sector = snap.get("sector", "-")
        room_sector = max(0.0, strategy["max_sector_pct"] - _sector_exposure(pf, sector))
        alloc = min(pf["total_value"] * strategy["max_single_pct"],
                    pf["total_value"] * room_sector, available)
        qty = int(alloc // price)
        if qty < 1:
            continue
        cost = qty * price
        commission = round(cost * COMMISSION, 2)
        if cost + commission > pf["cash"]:
            continue
        pf["cash"] -= (cost + commission)
        pf["positions"].append({
            "ticker": tk, "name": snap.get("company", tk), "sector": sector,
            "entry": round(price, 2), "qty": qty, "current": round(price, 2),
            "stop": round(price * (1 + strategy["stop_pct"]), 2),
            "target": round(price * (1 + strategy["target_pct"]), 2),
            "entry_ts": now, "score": scored[tk],
        })
        pf["trades"].append({
            "ts": now, "side": "BUY", "ticker": tk, "qty": qty,
            "price": round(price, 2), "amount": round(cost, 2),
            "reason": "%s skoru %.0f (>=%.0f)" % (strategy["name"], scored[tk], strategy["buy_threshold"])})
        held.add(tk)

    # 4) değerleme
    pf["total_value"] = round(pf["cash"] + sum(p["current"] * p["qty"] for p in pf["positions"]), 2)
    pf["return_pct"] = round((pf["total_value"] - pf["initial"]) / pf["initial"] * 100, 2)
    pf["cash"] = round(pf["cash"], 2)
    _save(strategy, pf)
    return pf


def _sell(pf: dict, pos: dict, qty: int, ts: str, reason: str) -> None:
    amount = round(pos["current"] * qty, 2)
    pf["cash"] += amount * (1 - COMMISSION)
    pf["trades"].append({
        "ts": ts, "side": "SELL" if qty >= pos["qty"] else "SELL_PARTIAL",
        "ticker": pos["ticker"], "qty": qty, "price": pos["current"],
        "amount": amount, "reason": reason})
