"""DeepSeek BIST30 - Gerçek Haber + DeepSeek API Muhakeme Katmanı.

Akış: Google News RSS'ten (ücretsiz, anahtarsız) gerçek Türkçe başlıklar çekilir;
DEEPSEEK_API_KEY varsa DeepSeek LLM ile başlıklar üzerinden sentiment skoru (0-100)
üretilir. Anahtar yoksa/hata olursa None döner ve çağıran taraf mevcut haber havuzuna
güvenle geri düşer.

Kısıt uyumu: izin verilen TEK API DeepSeek'tir. Anahtar ortam değişkeninden okunur,
asla koda gömülmez.

Kapatma:  DEEPSEEK_NEWS=0
Anahtar:  DEEPSEEK_API_KEY
Önbellek: deepseek/data/news_cache.json  (TTL 3 saat)
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CACHE_FILE = _DATA_DIR / "news_cache.json"
_CACHE_TTL = 3 * 60 * 60  # 3 saat
_API_URL = "https://api.deepseek.com/chat/completions"
_MODEL = "deepseek-chat"

_bundle_cache: Optional[dict] = None
_bundle_loaded = False


def deepseek_enabled() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY")) and os.environ.get("DEEPSEEK_NEWS", "1") != "0"


# ---------- Gerçek başlıklar (Google News RSS) ----------

def fetch_headlines(query: str, max_items: int = 4) -> List[str]:
    url = ("https://news.google.com/rss/search?q="
           + urllib.parse.quote(query) + "&hl=tr&gl=TR&ceid=TR:tr")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        titles = []
        for it in root.findall(".//item")[:max_items]:
            t = it.find("title")
            if t is not None and t.text:
                titles.append(t.text.strip())
        return titles
    except Exception:
        return []


# ---------- DeepSeek API ----------

def _deepseek_chat(system: str, user: str) -> Optional[dict]:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        return None
    body = json.dumps({
        "model": _MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_tokens": 1500,
    }).encode("utf-8")
    req = urllib.request.Request(
        _API_URL, data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        return None


# ---------- Bundle (bir döngüde tek LLM çağrısı) ----------

def _build_bundle(tickers: List[str], names: Dict[str, str]) -> Optional[dict]:
    market_titles = fetch_headlines("Borsa İstanbul BIST 100 piyasa", 6)
    per_ticker: Dict[str, List[str]] = {}
    for tk in tickers:
        q = f"{tk} {names.get(tk, '')} hisse"
        hl = fetch_headlines(q, 3)
        if hl:
            per_ticker[tk] = hl

    if not per_ticker and not market_titles:
        return None

    system = (
        "Sen bir BIST finans analistisin. Sadece verilen haber başlıklarına dayanarak "
        "duygu (sentiment) skoru üret. Skor 0-100: 50 nötr, >50 pozitif, <50 negatif. "
        "Uydurma; başlık yoksa 50 ver. Kesin ve tutarlı ol. Yalnızca şu JSON şemasında yanıt ver: "
        '{\"market\":{\"score\":<0-100>,\"trend\":\"<kisa>\"},'
        '\"tickers\":{\"<KOD>\":{\"score\":<0-100>,\"note\":\"<kisa gerekce>\"}}}'
    )
    lines = ["## Piyasa başlıkları:"]
    lines += [f"- {t}" for t in market_titles] or ["- (yok)"]
    lines.append("\n## Hisse başlıkları:")
    for tk, hls in per_ticker.items():
        lines.append(f"{tk} ({names.get(tk,'')}):")
        lines += [f"  - {h}" for h in hls]
    user = "\n".join(lines)

    result = _deepseek_chat(system, user)
    if not result or "tickers" not in result:
        return None
    result["_ts"] = int(time.time())
    result["_source"] = "deepseek-llm"
    return result


def _load_cache() -> Optional[dict]:
    try:
        raw = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        if time.time() - raw.get("_ts", 0) < _CACHE_TTL:
            return raw
    except Exception:
        pass
    return None


def _save_cache(bundle: dict) -> None:
    try:
        _DATA_DIR.mkdir(exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def get_news_bundle(tickers: List[str], names: Dict[str, str]) -> Optional[dict]:
    """Süreç başına bir kez: {market:{score,trend}, tickers:{tk:{score,note}}} ya da None."""
    global _bundle_cache, _bundle_loaded
    if _bundle_loaded:
        return _bundle_cache
    _bundle_loaded = True

    if not deepseek_enabled():
        _bundle_cache = None
        return None

    cached = _load_cache()
    if cached:
        _bundle_cache = cached
        return cached

    bundle = _build_bundle(tickers, names)
    if bundle:
        _save_cache(bundle)
    _bundle_cache = bundle
    return bundle
