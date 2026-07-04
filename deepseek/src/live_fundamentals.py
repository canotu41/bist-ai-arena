"""DeepSeek BIST30 - Canlı Temel Veri Katmanı (Yahoo Finance + crumb, stdlib).

Yahoo'nun fundamental uçları crumb+cookie ister. Bu modül crumb dansını yapıp
F/K, PD/DD, ROE, marj, borç/özsermaye, ciro/kâr büyümesi, temettü ve cari oranı
çeker. Temel veriler çeyreklik değiştiği için 24 SAAT önbelleklenir.

Hata/eksik alanda ilgili değer curated (statik) veriden tamamlanır → sistem asla
kırılmaz, sadece o alan statik kalır.

Kapatma:  ARENA_LIVE=0
Önbellek: deepseek/data/fund_cache.json (TTL 24 saat)
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Optional, List

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CACHE_FILE = _DATA_DIR / "fund_cache.json"
_CACHE_TTL = 24 * 60 * 60

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")

_mem: Optional[Dict[str, dict]] = None
_opener = None
_crumb: Optional[str] = None


def live_enabled() -> bool:
    return os.environ.get("ARENA_LIVE", "1") != "0"


def _session():
    """crumb + cookie'li opener'ı (bir kez) kur."""
    global _opener, _crumb
    if _opener is not None:
        return _opener, _crumb
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", _UA), ("Accept", "*/*")]
    try:
        try:
            op.open("https://fc.yahoo.com", timeout=12)
        except Exception:
            pass
        crumb = op.open("https://query1.finance.yahoo.com/v1/test/getcrumb", timeout=12).read().decode()
        if not crumb or "<" in crumb:
            crumb = None
    except Exception:
        crumb = None
    _opener, _crumb = op, crumb
    return op, crumb


def _fetch_quote_batch(tickers: List[str]) -> Dict[str, dict]:
    """Tek istekte F/K, PD/DD, temettü (v7/quote)."""
    op, crumb = _session()
    if not crumb:
        return {}
    syms = ",".join(f"{t}.IS" for t in tickers)
    url = ("https://query1.finance.yahoo.com/v7/finance/quote?symbols="
           + urllib.parse.quote(syms)
           + "&fields=trailingPE,priceToBook,trailingAnnualDividendYield&crumb="
           + urllib.parse.quote(crumb))
    out = {}
    try:
        d = json.load(op.open(url, timeout=15))
        for r in d.get("quoteResponse", {}).get("result", []):
            tk = r.get("symbol", "").replace(".IS", "")
            out[tk] = {
                "fk": r.get("trailingPE"),
                "pddd": r.get("priceToBook"),
                "dividend_yield": (r.get("trailingAnnualDividendYield") or 0) * 100,
            }
    except Exception:
        pass
    return out


def _fetch_financials(ticker: str) -> dict:
    """ROE, marj, borç, büyüme, cari oran (v10/quoteSummary financialData)."""
    op, crumb = _session()
    if not crumb:
        return {}
    url = ("https://query1.finance.yahoo.com/v10/finance/quoteSummary/"
           + f"{ticker}.IS?modules=financialData&crumb=" + urllib.parse.quote(crumb))
    try:
        d = json.load(op.open(url, timeout=15))
        fd = d["quoteSummary"]["result"][0]["financialData"]

        def raw(k):
            v = fd.get(k)
            return v.get("raw") if isinstance(v, dict) else None

        roe = raw("returnOnEquity")
        margin = raw("ebitdaMargins")
        if margin is None:
            margin = raw("profitMargins")
        d2e = raw("debtToEquity")
        rev_g = raw("revenueGrowth")
        earn_g = raw("earningsGrowth")
        cur = raw("currentRatio")
        return {
            "roe": roe * 100 if roe is not None else None,
            "ebitda_margin": margin * 100 if margin is not None else None,
            "debt_equity": d2e / 100 if d2e is not None else None,  # Yahoo % → oran
            "revenue_growth": rev_g * 100 if rev_g is not None else None,
            "net_profit_growth": earn_g * 100 if earn_g is not None else None,
            "current_ratio": cur,
        }
    except Exception:
        return {}


def _load_cache() -> Optional[Dict[str, dict]]:
    try:
        raw = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        if time.time() - raw.get("_ts", 0) < _CACHE_TTL:
            return raw.get("data", {})
    except Exception:
        pass
    return None


def _save_cache(data: Dict[str, dict]) -> None:
    try:
        _DATA_DIR.mkdir(exist_ok=True)
        _CACHE_FILE.write_text(json.dumps({"_ts": int(time.time()), "data": data},
                                          ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def get_all_live_fundamentals(tickers: List[str]) -> Dict[str, dict]:
    """{ticker: {fk,pddd,roe,...}} — süreç başına bir kez, 24s cache."""
    global _mem
    if _mem is not None:
        return _mem
    if not live_enabled():
        _mem = {}
        return _mem
    cached = _load_cache()
    if cached is not None:
        _mem = cached
        return cached

    quotes = _fetch_quote_batch(tickers)
    data: Dict[str, dict] = {}
    for tk in tickers:
        rec = dict(quotes.get(tk, {}))
        fin = _fetch_financials(tk)
        rec.update({k: v for k, v in fin.items() if v is not None})
        # sadece anlamlı (en az F/K veya ROE) kayıtları tut
        if rec.get("fk") or rec.get("roe"):
            data[tk] = rec
    if data:
        _save_cache(data)
    _mem = data
    return data
