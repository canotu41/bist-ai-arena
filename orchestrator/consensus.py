"""Konsensüs motoru: birden fazla yapay zekanın 'beğendiği' (tuttuğu ya da
AL önerdiği) hisseleri bulur. Konsensüs portföyünün kendisi hesaba katılmaz
(döngüsellik olmasın diye)."""
from __future__ import annotations

from typing import Dict, List


def _likes_of(comp: dict) -> Dict[str, str]:
    """Bir yarışmacının beğendiği tickerlar -> gerekçe kısaltması."""
    likes: Dict[str, str] = {}
    for p in comp.get("positions", []):
        likes[p["ticker"]] = "tutuyor (%%%.0f ağırlık)" % p.get("weight_pct", 0)
    # microsoft öneri motoru: AL etiketli öneriler de birer 'beğeni'
    for r in comp.get("recommendations", []):
        if str(r.get("label", "")).upper() == "AL":
            likes.setdefault(r["ticker"], "AL önerisi (skor %.0f)" % float(r.get("score", 0)))
    return likes


def compute_consensus(comps: List[dict], snapshot: Dict[str, dict]) -> List[dict]:
    """Ortak hisseleri döndürür (agreement_count>=2), en güçlüden zayıfa."""
    voters = [c for c in comps if c["key"] != "consensus" and c.get("active")]

    tally: Dict[str, List[dict]] = {}
    for c in voters:
        for ticker, why in _likes_of(c).items():
            tally.setdefault(ticker, []).append({"ai": c["name"], "why": why})

    consensus = []
    for ticker, backers in tally.items():
        if len(backers) < 2:
            continue
        snap = snapshot.get(ticker, {})
        consensus.append({
            "ticker": ticker,
            "name": snap.get("company", ticker),
            "sector": snap.get("sector", "-"),
            "agreement": len(backers),
            "backers": backers,
            "deepscore": snap.get("deepscore", 0.0),
            "signal": snap.get("signal", "-"),
            "price": snap.get("price", 0.0),
            "rsi": snap.get("rsi", 0.0),
            "fk": snap.get("fk", 0.0),
            "roe": snap.get("roe", 0.0),
            "change_20d": snap.get("change_20d", 0.0),
            "ma20": snap.get("ma20", 0.0),
            "ma50": snap.get("ma50", 0.0),
            "ma200": snap.get("ma200", 0.0),
            "atr_pct": snap.get("atr_pct", 0.0),
        })

    consensus.sort(key=lambda x: (x["agreement"], x["deepscore"]), reverse=True)
    return consensus
