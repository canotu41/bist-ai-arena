"""DeepSeek BIST30 - Canlı Temel Veri Katmanı (Bigpara / Hürriyet, Türk kaynak).

Bigpara'nın hisseyuzeysel JSON ucu gerçek, güncel BIST verisi verir ve crumb/auth
istemez (sadece Referer). Yahoo'nun aksine Türk medya sunucusu olduğu için
datacenter IP'lerine (GitHub Actions) çok daha dostanedir.

Alınanlar: F/K (fiyatkaz), PD/DD (=piydeg/ozsermaye), ROE (=netkar/ozsermaye),
piyasa değeri, beta. Marj/borç/büyüme Bigpara'da olmadığından curated'dan tamamlanır.

Temel veri çeyreklik değişir → 14 GÜN önbellek; çekilemezse eski gerçek cache korunur.

Kapatma:  ARENA_LIVE=0
Önbellek: deepseek/data/fund_cache.json (TTL 14 gün)
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path
from typing import Dict, Optional, List

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CACHE_FILE = _DATA_DIR / "fund_cache.json"
_CACHE_TTL = 14 * 24 * 60 * 60

_BASE = "https://bigpara.hurriyet.com.tr/api/v1/borsa/hisseyuzeysel/"
_HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://bigpara.hurriyet.com.tr/", "Accept": "*/*"}

_mem: Optional[Dict[str, dict]] = None


def live_enabled() -> bool:
    return os.environ.get("ARENA_LIVE", "1") != "0"


def _fetch_one(ticker: str) -> Optional[dict]:
    try:
        req = urllib.request.Request(_BASE + ticker, headers=_HDR)
        with urllib.request.urlopen(req, timeout=12) as resp:
            d = json.loads(resp.read().decode("utf-8"))
        hy = d.get("data", {}).get("hisseYuzeysel")
        if not hy:
            return None
        fk = hy.get("fiyatkaz")
        piydeg = hy.get("piydeg") or 0
        ozsermaye = hy.get("ozsermaye") or 0
        netkar = hy.get("netkar") or 0
        rec = {}
        if fk:
            rec["fk"] = round(float(fk), 2)
        if piydeg and ozsermaye:
            rec["pddd"] = round(piydeg / ozsermaye, 2)
        if netkar and ozsermaye:
            rec["roe"] = round(netkar / ozsermaye * 100, 1)
        rec["_donem"] = hy.get("donem")  # finansalların dönemi (şeffaflık)
        return rec if (rec.get("fk") or rec.get("roe")) else None
    except Exception:
        return None


def _load_cache_any():
    try:
        raw = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        data = raw.get("data", {})
        fresh = time.time() - raw.get("_ts", 0) < _CACHE_TTL
        return (data or None), fresh
    except Exception:
        return None, False


def _save_cache(data: Dict[str, dict]) -> None:
    try:
        _DATA_DIR.mkdir(exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(
            {"_ts": int(time.time()), "_source": "bigpara", "data": data},
            ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_all_live_fundamentals(tickers: List[str]) -> Dict[str, dict]:
    """{ticker: {fk,pddd,roe,...}} — süreç başına bir kez, 14g cache."""
    global _mem
    if _mem is not None:
        return _mem
    if not live_enabled():
        _mem = {}
        return _mem

    cached, fresh = _load_cache_any()
    if cached and fresh:
        _mem = cached
        return cached

    # BİRİKİMLİ: mevcut (eski) cache'in üstüne ekle → kısmi çekim iyi hisseleri
    # kaybetmez; datacenter throttle'ında birkaç döngüde 24'e dolar.
    data: Dict[str, dict] = dict(cached or {})
    got = 0
    for i, tk in enumerate(tickers):
        rec = _fetch_one(tk)
        if rec:
            data[tk] = rec
            got += 1
        if i < len(tickers) - 1:
            time.sleep(1.2)  # Bigpara nazik hız (throttle'ı önler)
    if got:
        _save_cache(data)
        _mem = data
        return data

    # hiç çekilemedi → eski gerçek cache'i koru (kötü curated'a düşme)
    _mem = cached or {}
    return _mem
