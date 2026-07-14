"""DeepSeek BIST30 - Temel Analiz Modülü"""
from __future__ import annotations

from typing import Dict
from .data_models import FundamentalData

# BIST30 temel analiz verileri (simüle edilmiş)
BIST30_FUNDAMENTAL: Dict[str, Dict] = {
    "AKBNK":  {"fk": 3.8, "pddd": 0.85, "net_profit_growth": 15.2, "debt_equity": 5.6,
               "roe": 22.5, "ebitda_margin": 58.0, "dividend_yield": 2.8, "revenue_growth": 28.5, "current_ratio": 1.15},
    "GARAN":  {"fk": 4.2, "pddd": 0.92, "net_profit_growth": 12.8, "debt_equity": 5.2,
               "roe": 21.0, "ebitda_margin": 55.0, "dividend_yield": 2.2, "revenue_growth": 25.0, "current_ratio": 1.10},
    "ISCTR":  {"fk": 5.5, "pddd": 1.05, "net_profit_growth": 8.5, "debt_equity": 6.1,
               "roe": 18.0, "ebitda_margin": 50.0, "dividend_yield": 1.8, "revenue_growth": 20.0, "current_ratio": 1.05},
    "YKBNK":  {"fk": 3.5, "pddd": 0.78, "net_profit_growth": 18.5, "debt_equity": 5.0,
               "roe": 24.0, "ebitda_margin": 60.0, "dividend_yield": 3.0, "revenue_growth": 30.0, "current_ratio": 1.20},
    "VAKBN":  {"fk": 4.8, "pddd": 0.95, "net_profit_growth": 10.2, "debt_equity": 5.8,
               "roe": 19.5, "ebitda_margin": 52.0, "dividend_yield": 2.0, "revenue_growth": 22.0, "current_ratio": 1.08},
    "KCHOL":  {"fk": 6.8, "pddd": 1.15, "net_profit_growth": 8.0, "debt_equity": 1.8,
               "roe": 16.5, "ebitda_margin": 22.0, "dividend_yield": 3.5, "revenue_growth": 15.0, "current_ratio": 1.35},
    "SAHOL":  {"fk": 5.2, "pddd": 0.88, "net_profit_growth": 10.5, "debt_equity": 1.5,
               "roe": 18.5, "ebitda_margin": 25.0, "dividend_yield": 3.8, "revenue_growth": 18.0, "current_ratio": 1.40},
    "THYAO":  {"fk": 5.8, "pddd": 1.25, "net_profit_growth": -5.2, "debt_equity": 2.8,
               "roe": 14.0, "ebitda_margin": 28.0, "dividend_yield": 1.2, "revenue_growth": 8.0, "current_ratio": 0.95},
    "PGSUS":  {"fk": 7.2, "pddd": 1.50, "net_profit_growth": 22.0, "debt_equity": 2.5,
               "roe": 20.5, "ebitda_margin": 32.0, "dividend_yield": 0.8, "revenue_growth": 25.0, "current_ratio": 1.05},
    "TUPRS":  {"fk": 4.5, "pddd": 1.10, "net_profit_growth": 6.0, "debt_equity": 1.2,
               "roe": 28.0, "ebitda_margin": 15.0, "dividend_yield": 6.5, "revenue_growth": 12.0, "current_ratio": 1.50},
    "EREGL":  {"fk": 6.0, "pddd": 0.72, "net_profit_growth": 14.0, "debt_equity": 0.9,
               "roe": 12.5, "ebitda_margin": 18.0, "dividend_yield": 4.2, "revenue_growth": 10.0, "current_ratio": 1.60},
    "BIMAS":  {"fk": 12.5, "pddd": 4.80, "net_profit_growth": 8.5, "debt_equity": 0.5,
               "roe": 38.0, "ebitda_margin": 12.0, "dividend_yield": 1.5, "revenue_growth": 65.0, "current_ratio": 0.80},
    "MGROS":  {"fk": 8.5, "pddd": 2.20, "net_profit_growth": 10.0, "debt_equity": 1.0,
               "roe": 25.0, "ebitda_margin": 10.0, "dividend_yield": 2.0, "revenue_growth": 55.0, "current_ratio": 0.85},
    "FROTO":  {"fk": 6.2, "pddd": 1.85, "net_profit_growth": 12.0, "debt_equity": 0.7,
               "roe": 30.0, "ebitda_margin": 14.0, "dividend_yield": 5.0, "revenue_growth": 20.0, "current_ratio": 1.30},
    "TOASO":  {"fk": 7.8, "pddd": 2.50, "net_profit_growth": 18.0, "debt_equity": 0.6,
               "roe": 32.0, "ebitda_margin": 16.0, "dividend_yield": 3.5, "revenue_growth": 28.0, "current_ratio": 1.25},
    "ASELS":  {"fk": 15.5, "pddd": 5.50, "net_profit_growth": 28.0, "debt_equity": 0.4,
               "roe": 35.0, "ebitda_margin": 22.0, "dividend_yield": 0.5, "revenue_growth": 35.0, "current_ratio": 1.80},
    "TCELL":  {"fk": 7.0, "pddd": 1.40, "net_profit_growth": 5.0, "debt_equity": 1.3,
               "roe": 17.0, "ebitda_margin": 38.0, "dividend_yield": 4.0, "revenue_growth": 14.0, "current_ratio": 1.10},
    "TTKOM":  {"fk": 6.5, "pddd": 1.25, "net_profit_growth": 4.5, "debt_equity": 1.1,
               "roe": 16.0, "ebitda_margin": 35.0, "dividend_yield": 4.5, "revenue_growth": 12.0, "current_ratio": 1.15},
    "SISE":   {"fk": 9.5, "pddd": 2.80, "net_profit_growth": 6.5, "debt_equity": 0.8,
               "roe": 15.0, "ebitda_margin": 20.0, "dividend_yield": 2.5, "revenue_growth": 16.0, "current_ratio": 1.40},
    "AKSEN":  {"fk": 8.0, "pddd": 1.60, "net_profit_growth": 20.0, "debt_equity": 2.2,
               "roe": 18.0, "ebitda_margin": 30.0, "dividend_yield": 1.8, "revenue_growth": 22.0, "current_ratio": 0.90},
    "ULKER":  {"fk": 9.0, "pddd": 2.10, "net_profit_growth": 5.5, "debt_equity": 1.5,
               "roe": 13.0, "ebitda_margin": 15.0, "dividend_yield": 2.8, "revenue_growth": 10.0, "current_ratio": 1.20},
    "CCOLA":  {"fk": 10.5, "pddd": 3.20, "net_profit_growth": 12.0, "debt_equity": 0.6,
               "roe": 28.0, "ebitda_margin": 20.0, "dividend_yield": 1.2, "revenue_growth": 18.0, "current_ratio": 1.15},
    "ARCLK":  {"fk": 8.2, "pddd": 1.80, "net_profit_growth": 3.0, "debt_equity": 1.0,
               "roe": 14.0, "ebitda_margin": 10.0, "dividend_yield": 3.0, "revenue_growth": 8.0, "current_ratio": 1.25},
    "EKGYO":  {"fk": 4.5, "pddd": 0.55, "net_profit_growth": 25.0, "debt_equity": 0.8,
               "roe": 12.0, "ebitda_margin": 35.0, "dividend_yield": 1.0, "revenue_growth": 30.0, "current_ratio": 1.55},
}


# Sektör eşleştirmeleri
SECTOR_MAP = {
    "AKBNK": "Bankacılık", "GARAN": "Bankacılık", "ISCTR": "Bankacılık",
    "YKBNK": "Bankacılık", "VAKBN": "Bankacılık",
    "KCHOL": "Holding", "SAHOL": "Holding", "SISE": "Holding",
    "THYAO": "Ulaştırma", "PGSUS": "Ulaştırma",
    "TUPRS": "Enerji", "AKSEN": "Enerji",
    "EREGL": "Demir-Çelik",
    "BIMAS": "Perakende", "MGROS": "Perakende",
    "FROTO": "Otomotiv", "TOASO": "Otomotiv",
    "ASELS": "Savunma",
    "TCELL": "Telekom", "TTKOM": "Telekom",
    "ULKER": "Gıda", "CCOLA": "Gıda",
    "ARCLK": "Dayanıklı Tüketim",
    "EKGYO": "Gayrimenkul",
}

# Şirket isimleri
COMPANY_NAMES = {
    "AKBNK": "Akbank", "GARAN": "Garanti BBVA", "ISCTR": "İş Bankası (C)",
    "YKBNK": "Yapı Kredi Bankası", "VAKBN": "VakıfBank",
    "KCHOL": "Koç Holding", "SAHOL": "Sabancı Holding", "SISE": "Şişecam",
    "THYAO": "Türk Hava Yolları", "PGSUS": "Pegasus Hava Yolları",
    "TUPRS": "Tüpraş", "AKSEN": "Aksa Enerji",
    "EREGL": "Ereğli Demir Çelik",
    "BIMAS": "BİM Mağazalar", "MGROS": "Migros",
    "FROTO": "Ford Otosan", "TOASO": "Tofaş Oto Fabrika",
    "ASELS": "Aselsan",
    "TCELL": "Turkcell", "TTKOM": "Türk Telekom",
    "ULKER": "Ülker Bisküvi", "CCOLA": "Coca-Cola İçecek",
    "ARCLK": "Arçelik",
    "EKGYO": "Emlak Konut GYO",
}


def normalize(value: float, lower: float, upper: float) -> float:
    """Bir değeri 0-100 arası normalize eder"""
    if upper == lower:
        return 50.0
    return max(0.0, min(100.0, ((value - lower) / (upper - lower)) * 100.0))


def _live_fundamentals_map() -> Dict[str, dict]:
    """Canlı temel veri haritası (varsa); hata/kapalıysa boş."""
    try:
        from .live_fundamentals import get_all_live_fundamentals
        return get_all_live_fundamentals(list(BIST30_FUNDAMENTAL.keys()))
    except Exception:
        return {}


def get_fundamental_data(ticker: str) -> FundamentalData:
    """Bir hisse için temel analiz verisi üretir (önce canlı Yahoo, eksik alan curated)."""
    data = dict(BIST30_FUNDAMENTAL.get(ticker) or
                {"fk": 10.0, "pddd": 1.5, "net_profit_growth": 5.0, "debt_equity": 1.5,
                 "roe": 15.0, "ebitda_margin": 15.0, "dividend_yield": 2.0,
                 "revenue_growth": 10.0, "current_ratio": 1.2})

    # Canlı değerlerle üzerine yaz (yalnızca gelen alanlar; gerisi curated kalır)
    live = _live_fundamentals_map().get(ticker)
    if live:
        for k in ("fk", "pddd", "roe", "ebitda_margin", "debt_equity",
                  "revenue_growth", "net_profit_growth", "dividend_yield", "current_ratio"):
            v = live.get(k)
            if v is not None and v == v:  # NaN değil
                data[k] = v

    return FundamentalData(
        ticker=ticker,
        fk_ratio=data["fk"],
        pddd_ratio=data["pddd"],
        net_profit_growth_qoq=data["net_profit_growth"],
        debt_to_equity=data["debt_equity"],
        roe=data["roe"],
        ebitda_margin=data["ebitda_margin"],
        dividend_yield=data["dividend_yield"],
        revenue_growth_yoy=data["revenue_growth"],
        current_ratio=data["current_ratio"],
    )


def score_fundamental(data: FundamentalData) -> float:
    """Temel analiz skoru hesaplar (0-100)"""
    score = 0.0

    # F/K: düşük iyidir; gerçek BIST aralığı ~5-45. Aykırı (negatif ya da >60,
    # zarar/near-sıfır kâr) değerleri sınırla ki eksen bozulmasın (ör. EREGL F/K 598).
    fk = data.fk_ratio if 0 < data.fk_ratio <= 60 else 60.0
    score += normalize(fk, 45.0, 5.0) * 0.20

    # PD/DD: düşük iyidir; aykırıları sınırla (ör. THYAO 21)
    pddd = min(data.pddd_ratio, 8.0) if data.pddd_ratio > 0 else 8.0
    score += normalize(pddd, 6.0, 0.5) * 0.15

    # Net kâr büyümesi: Yüksek iyidir (-10 ile +30 arası)
    score += normalize(data.net_profit_growth_qoq, -10.0, 30.0) * 0.15

    # Borç/Özsermaye: Düşük iyidir
    score += normalize(data.debt_to_equity, 5.0, 0.3) * 0.10

    # ROE: Yüksek iyidir (%5-40 arası)
    score += normalize(data.roe, 5.0, 40.0) * 0.15

    # FAVÖK marjı: Yüksek iyidir (%5-60 arası)
    score += normalize(data.ebitda_margin, 5.0, 60.0) * 0.10

    # Temettü verimi: Orta-yüksek iyidir
    score += normalize(data.dividend_yield, 0.0, 6.5) * 0.05

    # Ciro büyümesi: Yüksek iyidir
    score += normalize(data.revenue_growth_yoy, 5.0, 65.0) * 0.05

    # Cari oran: >1 iyidir
    score += normalize(data.current_ratio, 0.5, 2.0) * 0.05

    return round(score, 1)


def scan_all_bist30_fundamental() -> Dict[str, FundamentalData]:
    """Tüm BIST30 temel verilerini döndürür"""
    return {ticker: get_fundamental_data(ticker) for ticker in BIST30_FUNDAMENTAL}