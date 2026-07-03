"""DeepSeek BIST30 - Canlı Veri Katmanı (Yahoo Finance, anahtarsız, stdlib).

Gerçek fiyat + günlük geçmişten gerçek teknik göstergeler üretir ve
BIST30_TECHNICAL_SAMPLE ile aynı sözlük biçiminde döndürür. Ağ/hatada None
döner; çağıran taraf örnek veriye güvenle geri düşer.

Kapatmak için:  ARENA_LIVE=0
Önbellek:       deepseek/data/live_cache.json  (TTL 15 dk)
"""
from __future__ import annotations

import json
import math
import os
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CACHE_FILE = _DATA_DIR / "live_cache.json"
_CACHE_TTL = 15 * 60  # saniye
_INDEX_SYMBOL = "XU100.IS"

_mem_cache: Dict[str, dict] = {}   # süreç içi bellek önbelleği
_index_change_20d: Optional[float] = None


def live_enabled() -> bool:
    return os.environ.get("ARENA_LIVE", "1") != "0"


# ---------- Yahoo Finance getirme ----------

def _fetch_chart(symbol: str, rng: str = "1y", interval: str = "1d") -> Optional[dict]:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
           f"?range={rng}&interval={interval}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.load(resp)
        result = data["chart"]["result"][0]
        q = result["indicators"]["quote"][0]
        meta = result["meta"]
        closes = [c for c in q.get("close", []) if c is not None]
        highs = [c for c in q.get("high", []) if c is not None]
        lows = [c for c in q.get("low", []) if c is not None]
        vols = [c for c in q.get("volume", []) if c is not None]
        if len(closes) < 30:
            return None
        return {"meta": meta, "closes": closes, "highs": highs,
                "lows": lows, "vols": vols}
    except Exception:
        return None


# ---------- Gösterge matematiği (self-contained) ----------

def _sma(xs: List[float], n: int) -> float:
    if not xs:
        return 0.0
    seg = xs[-n:]
    return sum(seg) / len(seg)


def _ema(xs: List[float], n: int) -> float:
    if not xs:
        return 0.0
    k = 2 / (n + 1)
    e = xs[0]
    for x in xs[1:]:
        e = x * k + e * (1 - k)
    return e


def _rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0.0))
        losses.append(max(-d, 0.0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 100.0
    rs = ag / al
    return 100.0 - (100.0 / (1.0 + rs))


def _macd(closes: List[float]):
    if len(closes) < 35:
        return 0.0, 0.0
    macd_series = []
    # son 20 barın MACD çizgisini üret, sinyal = 9-EMA
    for i in range(26, len(closes) + 1):
        window = closes[:i]
        macd_series.append(_ema(window, 12) - _ema(window, 26))
    macd_line = macd_series[-1]
    signal = _ema(macd_series[-9:], 9) if len(macd_series) >= 9 else macd_line
    return round(macd_line, 3), round(signal, 3)


def _bollinger(closes: List[float], period: int = 20, sd: float = 2.0):
    seg = closes[-period:]
    mid = sum(seg) / len(seg)
    var = sum((x - mid) ** 2 for x in seg) / len(seg)
    std = math.sqrt(var)
    return mid + sd * std, mid, mid - sd * std


def _atr_pct(highs, lows, closes, period: int = 14) -> float:
    n = min(len(highs), len(lows), len(closes))
    if n < 2:
        return 2.0
    trs = []
    for i in range(1, n):
        tr = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]),
                 abs(lows[i] - closes[i - 1]))
        trs.append(tr)
    atr = sum(trs[-period:]) / min(period, len(trs))
    price = closes[-1] or 1.0
    return round(atr / price * 100, 2)


def _stochastic(highs, lows, closes, period: int = 14) -> float:
    n = min(len(highs), len(lows), len(closes))
    if n < period:
        return 50.0
    hh = max(highs[-period:])
    ll = min(lows[-period:])
    if hh == ll:
        return 50.0
    return round((closes[-1] - ll) / (hh - ll) * 100, 1)


def _pct_change(closes: List[float], bars: int) -> float:
    if len(closes) <= bars:
        return 0.0
    prev = closes[-1 - bars]
    if not prev:
        return 0.0
    return round((closes[-1] / prev - 1) * 100, 2)


def _max_drawdown(closes: List[float]) -> float:
    peak = closes[0]
    mdd = 0.0
    for c in closes:
        peak = max(peak, c)
        if peak:
            mdd = min(mdd, (c - peak) / peak)
    return round(abs(mdd) * 100, 1)


def _volatility(closes: List[float]) -> float:
    rets = [(closes[i] / closes[i - 1] - 1) for i in range(1, len(closes)) if closes[i - 1]]
    seg = rets[-20:]
    if len(seg) < 2:
        return 20.0
    m = sum(seg) / len(seg)
    std = math.sqrt(sum((r - m) ** 2 for r in seg) / len(seg))
    return round(std * math.sqrt(252) * 100, 1)


# ---------- Endeks (rölatif güç için) ----------

def _get_index_change_20d() -> float:
    global _index_change_20d
    if _index_change_20d is not None:
        return _index_change_20d
    ch = _fetch_chart(_INDEX_SYMBOL)
    _index_change_20d = _pct_change(ch["closes"], 20) if ch else 0.0
    return _index_change_20d


# ---------- Ana giriş ----------

def _compute(ticker: str, ch: dict) -> dict:
    closes, highs, lows, vols = ch["closes"], ch["highs"], ch["lows"], ch["vols"]
    meta = ch["meta"]
    price = float(meta.get("regularMarketPrice") or closes[-1])
    prev_close = float(meta.get("chartPreviousClose") or meta.get("previousClose") or closes[-2])
    change_1d = round((price / prev_close - 1) * 100, 2) if prev_close else 0.0

    bb_u, bb_m, bb_l = _bollinger(closes)
    macd_line, macd_sig = _macd(closes)
    idx20 = _get_index_change_20d()
    ch20 = _pct_change(closes, 20)
    rel = round((1 + ch20 / 100) / (1 + idx20 / 100), 3) if (1 + idx20 / 100) else 1.0
    hi52 = max(closes[-252:]) if closes else price
    lo52 = min(closes[-252:]) if closes else price
    stoch_k = _stochastic(highs, lows, closes)
    vol_ratio = round((vols[-1] / (_sma(vols, 20) or 1)), 2) if vols else 1.0

    return {
        "price": round(price, 2),
        "change_1d": change_1d,
        "change_5d": _pct_change(closes, 5),
        "change_20d": ch20,
        "change_60d": _pct_change(closes, 60),
        "rsi": round(_rsi(closes), 1),
        "macd": macd_line,
        "macd_signal": macd_sig,
        "bb_upper": round(bb_u, 2), "bb_middle": round(bb_m, 2), "bb_lower": round(bb_l, 2),
        "ma20": round(_sma(closes, 20), 2),
        "ma50": round(_sma(closes, 50), 2),
        "ma200": round(_sma(closes, 200), 2),
        "volume_ratio": vol_ratio,
        "stoch_k": stoch_k, "stoch_d": round(stoch_k * 0.9, 1),
        "atr_pct": _atr_pct(highs, lows, closes),
        "vs_52w_high": round(price / hi52 * 100, 1) if hi52 else 100.0,
        "vs_52w_low": round(price / lo52 * 100, 1) if lo52 else 100.0,
        "rel_strength": rel,
        "beta": 1.0,
        "volatility": _volatility(closes),
        "max_dd": _max_drawdown(closes),
        "_source": "live", "_ts": int(time.time()),
    }


def _load_file_cache() -> Dict[str, dict]:
    try:
        raw = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}


def _save_file_cache(cache: Dict[str, dict]) -> None:
    try:
        _DATA_DIR.mkdir(exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def get_live_technical(ticker: str) -> Optional[dict]:
    """Ticker için canlı teknik veri sözlüğü; hata/kapalıysa None."""
    if not live_enabled():
        return None
    now = time.time()

    if ticker in _mem_cache:
        return _mem_cache[ticker]

    file_cache = _load_file_cache()
    entry = file_cache.get(ticker)
    if entry and now - entry.get("_ts", 0) < _CACHE_TTL:
        _mem_cache[ticker] = entry
        return entry

    ch = _fetch_chart(f"{ticker}.IS")
    if not ch:
        return None
    try:
        computed = _compute(ticker, ch)
    except Exception:
        return None

    _mem_cache[ticker] = computed
    file_cache[ticker] = computed
    _save_file_cache(file_cache)
    return computed
