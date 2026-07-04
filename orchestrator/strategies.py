"""Her klasör-AI'ın KENDİ strateji kimliği (kendi STRATEJI.md'sinden türetildi).

Hepsi aynı canlı-veriden gelen bileşen skorlarını (Temel/Teknik/Haber/Momentum/Risk)
KENDİ ağırlıkları, eşikleri ve risk kurallarıyla birleştirir → farklı portföyler.
deepseek burada YOK; o kendi LLM'li motorunda (deepseek/main.py) kalır."""
from __future__ import annotations

# axis'ler snapshot breakdown ile birebir: Temel, Teknik, Haber, Momentum, Risk
STRATEGIES = {
    "claude": {
        "key": "claude", "name": "Claude AI", "folder": "claude",
        "initial": 50000.0,
        "style": "Kalite+değer, yoğun portföy: ROE≥%10 ve F/K≤35, uzun-vade trend üstü hisseler",
        "weights": {"Temel": 0.40, "Teknik": 0.35, "Haber": 0.25, "Momentum": 0.0, "Risk": 0.0},
        "buy_threshold": 62.0, "sell_threshold": 46.0,
        "max_single_pct": 0.22, "min_cash_pct": 0.10, "max_sector_pct": 0.40,
        "max_positions": 6, "stop_pct": -0.09, "target_pct": 0.18,
        # sert eleme: kaliteli + aşırı pahalı olmayan + uzun vade trend üstü
        "filters": {"roe_min": 10.0, "fk_max": 35.0, "above_ma200": True},
    },
    "codex": {
        "key": "codex", "name": "Codex", "folder": "codex",
        "initial": 50000.0,
        "style": "Önce risk: düşük volatilite (ATR≤%3.6), RSI 40-68, MA50 üstü teyitli; sıkı stop",
        "weights": {"Temel": 0.35, "Teknik": 0.30, "Haber": 0.20, "Momentum": 0.0, "Risk": 0.15},
        "buy_threshold": 62.0, "sell_threshold": 48.0,
        "max_single_pct": 0.15, "min_cash_pct": 0.12, "max_sector_pct": 0.30,
        "max_positions": 8, "stop_pct": -0.07, "target_pct": 0.15,
        # sert eleme: düşük vol + aşırı alım/panik değil + teyitli
        "filters": {"atr_max": 3.6, "rsi_min": 40.0, "rsi_max": 68.0, "above_ma50": True},
    },
    "microsoft": {
        "key": "microsoft", "name": "Microsoft Copilot", "folder": "microsoft",
        "initial": 50000.0,
        "style": "Momentum/trend takibi: 20g değişim≥%4 ve MA20>MA50 kırılım; kazananı bırakma, geniş stop",
        "weights": {"Temel": 0.20, "Teknik": 0.45, "Haber": 0.15, "Momentum": 0.20, "Risk": 0.0},
        "buy_threshold": 60.0, "sell_threshold": 45.0,
        "max_single_pct": 0.25, "min_cash_pct": 0.05, "max_sector_pct": 0.45,
        "max_positions": 6, "stop_pct": -0.10, "target_pct": 0.25,
        # sert eleme: momentum + yükseliş trendi kırılımı (temele bakmaz)
        "filters": {"chg20_min": 4.0, "uptrend_20_50": True},
    },
}


def score_for(strategy: dict, breakdown: dict) -> float:
    """Bir hissenin bu stratejiye göre skoru (0-100)."""
    w = strategy["weights"]
    total_w = sum(w.values()) or 1.0
    s = sum(breakdown.get(axis, 50.0) * weight for axis, weight in w.items())
    return round(s / total_w, 1)


def passes_filter(strategy: dict, snap: dict) -> bool:
    """Stratejinin SERT eleme kurallarına göre hisse uygun mu (giriş için)."""
    f = strategy.get("filters", {})
    if not f:
        return True
    price = snap.get("price") or 0
    rsi = snap.get("rsi", 50)
    atr = snap.get("atr_pct", 2.5)
    chg20 = snap.get("change_20d", 0)
    fk = snap.get("fk", 0)
    roe = snap.get("roe", 0)
    ma20, ma50, ma200 = snap.get("ma20", 0), snap.get("ma50", 0), snap.get("ma200", 0)

    if "roe_min" in f and roe < f["roe_min"]:
        return False
    if "fk_max" in f and fk and fk > f["fk_max"]:
        return False
    if "atr_max" in f and atr > f["atr_max"]:
        return False
    if "rsi_min" in f and rsi < f["rsi_min"]:
        return False
    if "rsi_max" in f and rsi > f["rsi_max"]:
        return False
    if "chg20_min" in f and chg20 < f["chg20_min"]:
        return False
    if f.get("above_ma50") and ma50 and price < ma50:
        return False
    if f.get("above_ma200") and ma200 and price < ma200:
        return False
    if f.get("uptrend_20_50") and not (ma20 and ma50 and ma20 > ma50):
        return False
    return True
