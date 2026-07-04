"""Tüm yarışmacıların durumunu ortak şemaya normalize eder.

- claude / codex / microsoft: trader.py'nin yazdığı standart "arena" portfolio.json
- deepseek: kendi LLM'li motorunun portfolio.json'u (farklı şema)
- consensus: benim (şef) portföyüm

Ortak yarışmacı dict:
  key, name, active, style, initial, cash, value, return_pct,
  positions: [{ticker,name,sector,qty,entry,current,pnl_pct,weight_pct,score,stop,target}]
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


def _pos(ticker, name, sector, qty, entry, current, total_value, **extra):
    entry = float(entry or 0)
    current = float(current or entry)
    qty = float(qty or 0)
    pnl_pct = ((current - entry) / entry * 100) if entry else 0.0
    weight = (current * qty / total_value * 100) if total_value else 0.0
    d = {
        "ticker": ticker, "name": name, "sector": sector, "qty": qty,
        "entry": round(entry, 2), "current": round(current, 2),
        "pnl_pct": round(pnl_pct, 2), "weight_pct": round(weight, 1),
    }
    d.update(extra)
    return d


def _rev_trades(trades):
    return list(reversed(trades or []))


def load_arena(folder: str, key: str, name: str) -> Optional[dict]:
    """trader.py standart şemalı portföyü."""
    raw = _read_json(ROOT / folder / "portfolio.json")
    if not raw or raw.get("_schema") != "arena":
        return None
    value = float(raw.get("total_value", raw.get("initial", 10000)))
    positions = [
        _pos(p["ticker"], p.get("name", p["ticker"]), p.get("sector", "-"),
             p.get("qty"), p.get("entry"), p.get("current"), value,
             score=p.get("score"), stop=p.get("stop"), target=p.get("target"))
        for p in raw.get("positions", [])
    ]
    return {
        "key": key, "name": name, "active": True, "engine": True,
        "style": raw.get("strategy", ""),
        "initial": float(raw.get("initial", 10000)),
        "cash": round(float(raw.get("cash", 0)), 2), "value": round(value, 2),
        "return_pct": round(float(raw.get("return_pct", 0)), 2),
        "positions": positions, "trades": _rev_trades(raw.get("trades")),
    }


def load_deepseek() -> Optional[dict]:
    raw = _read_json(ROOT / "deepseek" / "portfolio.json")
    if not raw:
        return None
    value = float(raw.get("total_value", 10000))
    positions = [
        _pos(p["ticker"], p.get("company_name", p["ticker"]), p.get("sector", "-"),
             p.get("quantity"), p.get("entry_price"), p.get("current_price"), value,
             score=p.get("deepscore_at_entry"), stop=p.get("stop_loss"), target=p.get("take_profit"))
        for p in raw.get("positions", [])
    ]
    trades = [{
        "ts": t.get("timestamp", ""), "side": t.get("type", "?"),
        "ticker": t.get("ticker", "-"), "qty": t.get("quantity", 0),
        "price": round(float(t.get("price", 0)), 2),
        "amount": round(float(t.get("total_amount", 0)), 2),
        "reason": t.get("reason", ""),
    } for t in raw.get("transactions", [])]
    return {
        "key": "deepseek", "name": "DeepSeek AI", "active": True, "engine": True,
        "style": "5-eksenli DeepScore™ + DeepSeek LLM haber + rejime adaptif ağırlık",
        "initial": float(raw.get("initial_capital", 10000)),
        "cash": round(float(raw.get("cash", 0)), 2), "value": round(value, 2),
        "return_pct": round(float(raw.get("total_return_pct", 0)), 2),
        "positions": positions, "trades": _rev_trades(trades),
    }


def load_consensus() -> Optional[dict]:
    raw = _read_json(DATA_DIR / "consensus_portfolio.json")
    if not raw:
        return None
    value = float(raw.get("total_value", 10000))
    positions = [
        _pos(p["ticker"], p.get("name", p["ticker"]), p.get("sector", "-"),
             p.get("qty"), p.get("entry"), p.get("current"), value,
             score=p.get("agreement"), stop=p.get("stop"), target=p.get("target"))
        for p in raw.get("positions", [])
    ]
    return {
        "key": "consensus", "name": "Konsensüs (Claude)", "active": True, "engine": True,
        "style": "Şef katmanı: 2+ AI'ın ortak seçtiği hisseler + Claude araştırması",
        "initial": float(raw.get("initial", 10000)),
        "cash": round(float(raw.get("cash", 0)), 2), "value": round(value, 2),
        "return_pct": round(float(raw.get("return_pct", 0)), 2),
        "positions": positions, "trades": _rev_trades(raw.get("trades")),
    }


def load_snapshot() -> Dict[str, dict]:
    rows = _read_json(DATA_DIR / "snapshot.json") or []
    return {r["ticker"]: r for r in rows}


def load_all_competitors() -> List[dict]:
    comps = []
    loaders = [
        load_consensus,
        load_deepseek,
        lambda: load_arena("claude", "claude", "Claude AI"),
        lambda: load_arena("codex", "codex", "Codex"),
        lambda: load_arena("microsoft", "microsoft", "Microsoft Copilot"),
    ]
    for loader in loaders:
        try:
            c = loader()
        except Exception:
            c = None
        if c:
            comps.append(c)
    # pasif (henüz portföy üretmemiş) yarışmacıları da göster
    seen = {c["key"] for c in comps}
    for key, name in (("claude", "Claude AI"), ("codex", "Codex"),
                      ("microsoft", "Microsoft Copilot"), ("deepseek", "DeepSeek AI")):
        if key not in seen:
            comps.append({"key": key, "name": name, "active": False, "engine": False,
                          "style": "", "initial": 10000.0, "cash": 10000.0,
                          "value": 10000.0, "return_pct": 0.0, "positions": [], "trades": []})
    return comps


def merged_trade_feed(comps: List[dict], limit: int = 40) -> List[dict]:
    feed = []
    for c in comps:
        for t in c.get("trades", []):
            item = dict(t)
            item["who"] = c["name"]
            item["who_key"] = c["key"]
            feed.append(item)
    feed.sort(key=lambda x: str(x.get("ts", "")), reverse=True)
    return feed[:limit]
