"""Claude'un katkı katmanı:
1) Konsensüs hisseleri için araştırma notları üretir (kantitatif, API'siz).
2) Bu ortak hisselerden 5. yarışmacı olan 'Konsensüs' paper portföyünü kurar
   ve her döngüde günceller (mark-to-market + stop/hedef)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

DATA_DIR = Path(__file__).resolve().parent / "data"
PORTFOLIO_JSON = DATA_DIR / "consensus_portfolio.json"

INITIAL_CAPITAL = 10000.0
MAX_WEIGHT = 0.20        # tek hissede en fazla %20
CASH_BUFFER = 0.05       # en az %5 nakit
STOP_PCT = -0.08         # -%8 stop
TARGET_PCT = 0.20        # +%20 hedef
COMMISSION = 0.002       # %0.2 işlem maliyeti
MIN_TICKET = 300.0


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _trend_label(c: dict) -> str:
    ma20, ma50, ma200, price = c["ma20"], c["ma50"], c["ma200"], c["price"]
    if ma20 and ma50 and ma200 and ma20 > ma50 > ma200:
        return "güçlü yükseliş trendi (MA20>MA50>MA200)"
    if ma50 and price > ma50:
        return "yükseliş eğilimi (fiyat MA50 üstünde)"
    if ma200 and price > ma200:
        return "nötr-pozitif (uzun vade trendinin üstünde)"
    return "zayıf/trend altı"


def _rsi_label(rsi: float) -> str:
    if rsi >= 72:
        return "aşırı alım bölgesi"
    if rsi <= 30:
        return "aşırı satım (tepki fırsatı)"
    return "sağlıklı momentum"


def generate_research(consensus: List[dict]) -> List[dict]:
    """Her konsensüs hissesi için araştırma notu."""
    notes = []
    for c in consensus:
        trend = _trend_label(c)
        rsi_l = _rsi_label(c["rsi"])
        ai_list = ", ".join(b["ai"] for b in c["backers"])

        if c["agreement"] >= 3 and c["deepscore"] >= 65 and "yükseliş" in trend:
            verdict = "GÜÇLÜ KONSENSÜS AL"
        elif c["agreement"] >= 2 and c["deepscore"] >= 60 and "zayıf" not in trend:
            verdict = "KONSENSÜS AL"
        elif c["rsi"] >= 72:
            verdict = "AL — ama aşırı alım, kademeli giriş"
        else:
            verdict = "İZLE"

        thesis = (
            "%d yapay zeka (%s) ortak noktada. DeepScore %.1f, F/K %.1f, ROE %%%.1f, "
            "20 günlük değişim %%%+.1f. Teknik: %s, RSI %.0f (%s)."
            % (c["agreement"], ai_list, c["deepscore"], c["fk"], c["roe"],
               c["change_20d"], trend, c["rsi"], rsi_l)
        )
        risk = "Stop -%%8, hedef +%%20. ATR %%%.1f — %s volatilite." % (
            c["atr_pct"], "yüksek" if c["atr_pct"] > 3.5 else ("orta" if c["atr_pct"] > 2 else "düşük"))

        notes.append({
            "ticker": c["ticker"], "name": c["name"], "sector": c["sector"],
            "agreement": c["agreement"], "verdict": verdict,
            "thesis": thesis, "risk": risk, "deepscore": c["deepscore"],
        })
    return notes


def _load_portfolio() -> dict:
    if PORTFOLIO_JSON.exists():
        try:
            return json.loads(PORTFOLIO_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "name": "Konsensüs (Claude) Portföyü", "initial": INITIAL_CAPITAL,
        "cash": INITIAL_CAPITAL, "total_value": INITIAL_CAPITAL, "return_pct": 0.0,
        "created": _now(), "last_updated": _now(),
        "positions": [], "trades": [],
    }


def _save_portfolio(pf: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    pf["last_updated"] = _now()
    PORTFOLIO_JSON.write_text(json.dumps(pf, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_consensus_portfolio(consensus: List[dict], snapshot: Dict[str, dict]) -> dict:
    """5. yarışmacı portföyünü kurar/günceller ve JSON'a yazar."""
    pf = _load_portfolio()
    now = _now()
    held = {p["ticker"]: p for p in pf["positions"]}

    # 1) Mevcut pozisyonları güncel fiyata çek (+ şirket-işlemi koruması)
    from . import corp_actions
    for p in pf["positions"]:
        snap = snapshot.get(p["ticker"], {})
        if snap.get("price"):
            new_price = float(snap["price"])
            r = corp_actions.anomaly_ratio(p.get("current") or p.get("entry"), new_price)
            if r is not None:
                corp_actions.adjust(p, r)
                pf["trades"].append({"ts": now, "side": "ADJUST", "ticker": p["ticker"],
                                     "qty": "", "price": round(new_price, 2), "amount": "",
                                     "reason": corp_actions.note(p["ticker"], r)})
            p["current"] = round(new_price, 2)

    # 2) Stop / hedef kontrolü
    survivors = []
    for p in pf["positions"]:
        entry = p["entry"]
        pnl_pct = (p["current"] - entry) / entry if entry else 0.0
        if pnl_pct <= STOP_PCT:
            amount = round(p["current"] * p["qty"], 2)
            pf["cash"] += amount * (1 - COMMISSION)
            pf["trades"].append({
                "ts": now, "side": "SELL", "ticker": p["ticker"], "qty": p["qty"],
                "price": p["current"], "amount": amount,
                "reason": "STOP-LOSS (%%%.1f)" % (pnl_pct * 100)})
        elif pnl_pct >= TARGET_PCT and p["qty"] >= 2:
            sell_qty = p["qty"] // 2
            amount = round(p["current"] * sell_qty, 2)
            pf["cash"] += amount * (1 - COMMISSION)
            p["qty"] -= sell_qty
            pf["trades"].append({
                "ts": now, "side": "SELL_PARTIAL", "ticker": p["ticker"], "qty": sell_qty,
                "price": p["current"], "amount": amount,
                "reason": "TAKE-PROFIT +%%20, %50 satış"})
            survivors.append(p)
        else:
            survivors.append(p)
    pf["positions"] = survivors
    held = {p["ticker"]: p for p in pf["positions"]}

    # 3) Yeni konsensüs adaylarına giriş (yer & nakit varsa)
    total_now = pf["cash"] + sum(p["current"] * p["qty"] for p in pf["positions"])
    for c in consensus:
        if c["ticker"] in held:
            continue
        if c["agreement"] < 2 or not c.get("price"):
            continue
        available = pf["cash"] - total_now * CASH_BUFFER
        if available < MIN_TICKET:
            break
        target_alloc = min(total_now * MAX_WEIGHT, available)
        price = float(c["price"])
        qty = int(target_alloc // price)
        if qty < 1:
            continue
        cost = qty * price
        commission = round(cost * COMMISSION, 2)
        if cost + commission > pf["cash"]:
            continue
        pf["cash"] -= (cost + commission)
        pf["positions"].append({
            "ticker": c["ticker"], "name": c["name"], "sector": c["sector"],
            "entry": round(price, 2), "qty": qty, "current": round(price, 2),
            "stop": round(price * (1 + STOP_PCT), 2),
            "target": round(price * (1 + TARGET_PCT), 2),
            "entry_ts": now, "agreement": c["agreement"],
        })
        pf["trades"].append({
            "ts": now, "side": "BUY", "ticker": c["ticker"], "qty": qty,
            "price": round(price, 2), "amount": round(cost, 2),
            "reason": "Konsensüs: %d AI ortak (%s)" % (
                c["agreement"], ", ".join(b["ai"] for b in c["backers"]))})
        held[c["ticker"]] = pf["positions"][-1]

    # 4) Değerleme
    pf["total_value"] = round(pf["cash"] + sum(p["current"] * p["qty"] for p in pf["positions"]), 2)
    pf["return_pct"] = round((pf["total_value"] - pf["initial"]) / pf["initial"] * 100, 2)
    pf["cash"] = round(pf["cash"], 2)

    _save_portfolio(pf)
    return pf
