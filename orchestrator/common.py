"""Tüm yarışmacıların durumunu ortak bir şemaya normalize eder.

Ortak şema (her yarışmacı bir dict):
    key, name, active(bool), engine(bool), initial, cash, value, return_pct,
    positions: [{ticker, name, sector, qty, entry, current, pnl_pct, weight_pct}]
    trades:    [{ts, side, ticker, qty, price, amount, reason}]  (yeni->eski)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"


def _read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _pos(ticker, name, sector, qty, entry, current, total_value):
    entry = float(entry or 0)
    current = float(current or entry)
    qty = float(qty or 0)
    pnl_pct = ((current - entry) / entry * 100) if entry else 0.0
    weight = (current * qty / total_value * 100) if total_value else 0.0
    return {
        "ticker": ticker, "name": name, "sector": sector, "qty": qty,
        "entry": round(entry, 2), "current": round(current, 2),
        "pnl_pct": round(pnl_pct, 2), "weight_pct": round(weight, 1),
    }


def load_deepseek() -> Optional[dict]:
    raw = _read_json(ROOT / "deepseek" / "portfolio.json")
    if not raw:
        return None
    value = float(raw.get("total_value", 10000))
    positions = [
        _pos(p["ticker"], p.get("company_name", p["ticker"]), p.get("sector", "-"),
             p.get("quantity"), p.get("entry_price"), p.get("current_price"), value)
        for p in raw.get("positions", [])
    ]
    trades = []
    for t in raw.get("transactions", []):
        trades.append({
            "ts": t.get("timestamp", ""), "side": t.get("type", "?"),
            "ticker": t.get("ticker", "-"), "qty": t.get("quantity", 0),
            "price": round(float(t.get("price", 0)), 2),
            "amount": round(float(t.get("total_amount", 0)), 2),
            "reason": t.get("reason", ""),
        })
    return {
        "key": "deepseek", "name": "DeepSeek AI", "active": True, "engine": True,
        "initial": float(raw.get("initial_capital", 10000)),
        "cash": round(float(raw.get("cash", 0)), 2), "value": round(value, 2),
        "return_pct": round(float(raw.get("total_return_pct", 0)), 2),
        "positions": positions, "trades": list(reversed(trades)),
    }


def load_claude() -> Optional[dict]:
    raw = _read_json(ROOT / "claude" / "portfolio.json")
    if not raw:
        return None
    value = float(raw.get("portfoy_degeri_try", 10000))
    positions = [
        # claude portföyünde güncel fiyat yok; giriş fiyatı = güncel varsayılır
        _pos(p["sembol"], p["sembol"], p.get("sektor", "-"),
             p.get("adet"), p.get("giris_fiyati"), p.get("giris_fiyati"), value)
        for p in raw.get("pozisyonlar", [])
    ]
    trades = []
    for t in raw.get("islem_gecmisi", []):
        islem = (t.get("islem", "") or "").upper()
        side = "BUY" if "AL" in islem else ("SELL" if "SAT" in islem else islem)
        trades.append({
            "ts": t.get("tarih", ""), "side": side, "ticker": t.get("sembol", "-"),
            "qty": t.get("adet", ""), "price": t.get("fiyat", ""), "amount": "",
            "reason": t.get("detay", ""),
        })
    return {
        "key": "claude", "name": "Claude AI", "active": True, "engine": False,
        "initial": float(raw.get("baslangic_sermayesi_try", 10000)),
        "cash": round(float(raw.get("nakit_try", 0)), 2), "value": round(value, 2),
        "return_pct": round(float(raw.get("getiri_pct", 0)), 2),
        "positions": positions, "trades": list(reversed(trades)),
    }


def load_microsoft() -> Optional[dict]:
    raw = _read_json(ROOT / "microsoft" / "recommendations.json")
    if not raw:
        return None
    pf = raw.get("portfolio", {})
    initial = 100000.0
    value = float(pf.get("total_value", initial))
    positions = [
        _pos(p["ticker"], p.get("company", p["ticker"]), p.get("sector", "-"),
             p.get("quantity"), p.get("entry_price"), p.get("current_price"), value)
        for p in pf.get("positions", [])
    ]
    # microsoft ayrı bir işlem defteri tutmuyor; açılışları BUY olarak sentezle
    trades = [{
        "ts": "", "side": "BUY", "ticker": p["ticker"], "qty": p["qty"],
        "price": p["entry"], "amount": round(p["entry"] * p["qty"], 2),
        "reason": "Başlangıç pozisyonu (öneri motoru)",
    } for p in positions]
    return {
        "key": "microsoft", "name": "Microsoft Copilot", "active": True, "engine": True,
        "initial": initial, "cash": round(value - sum(p["current"] * p["qty"] for p in positions), 2),
        "value": round(value, 2),
        "return_pct": round((value - initial) / initial * 100, 2),
        "positions": positions, "trades": trades,
        "recommendations": raw.get("recommendations", []),
    }


def load_codex() -> dict:
    # codex henüz motor/portföy üretmedi — pasif placeholder
    return {
        "key": "codex", "name": "Codex", "active": False, "engine": False,
        "initial": 10000.0, "cash": 10000.0, "value": 10000.0, "return_pct": 0.0,
        "positions": [], "trades": [],
    }


def load_consensus() -> Optional[dict]:
    raw = _read_json(DATA_DIR / "consensus_portfolio.json")
    if not raw:
        return None
    value = float(raw.get("total_value", 10000))
    positions = [
        _pos(p["ticker"], p.get("name", p["ticker"]), p.get("sector", "-"),
             p.get("qty"), p.get("entry"), p.get("current"), value)
        for p in raw.get("positions", [])
    ]
    trades = raw.get("trades", [])
    return {
        "key": "consensus", "name": "Konsensüs (Claude)", "active": True, "engine": True,
        "initial": float(raw.get("initial", 10000)),
        "cash": round(float(raw.get("cash", 0)), 2), "value": round(value, 2),
        "return_pct": round(float(raw.get("return_pct", 0)), 2),
        "positions": positions, "trades": list(reversed(trades)),
    }


def load_snapshot() -> Dict[str, dict]:
    """deepseek analiz anlık görüntüsü: {ticker: {...}}"""
    rows = _read_json(DATA_DIR / "snapshot.json") or []
    return {r["ticker"]: r for r in rows}


def load_all_competitors() -> List[dict]:
    comps = []
    for loader in (load_consensus, load_deepseek, load_claude, load_microsoft, load_codex):
        try:
            c = loader()
        except Exception:
            c = None
        if c:
            comps.append(c)
    return comps


def merged_trade_feed(comps: List[dict], limit: int = 40) -> List[dict]:
    """Tüm yarışmacıların işlemlerini tek akışta birleştirir (yeni->eski)."""
    feed = []
    for c in comps:
        for t in c.get("trades", []):
            item = dict(t)
            item["who"] = c["name"]
            item["who_key"] = c["key"]
            feed.append(item)
    feed.sort(key=lambda x: str(x.get("ts", "")), reverse=True)
    return feed[:limit]
