from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Recommendation:
    ticker: str
    company: str
    sector: str
    score: float
    label: str
    reasons: List[str]


SAMPLE_COMPANIES: List[Dict[str, object]] = [
    {
        "ticker": "THYAO",
        "company": "Türk Hava Yolları",
        "sector": "Ulaşım",
        "price": 28.4,
        "change_1d": 2.8,
        "rsi": 64,
        "ema20": 27.5,
        "ema50": 25.8,
        "roe": 18.2,
        "net_margin": 11.1,
        "debt_to_equity": 0.86,
        "revenue_growth": 14.5,
        "news_sentiment": 0.74,
        "volume_zscore": 1.35,
        "price_vs_52w_high": 0.91,
    },
    {
        "ticker": "ARCLK",
        "company": "Arçelik",
        "sector": "Dayanıklı Tüketim",
        "price": 38.7,
        "change_1d": 1.1,
        "rsi": 58,
        "ema20": 38.2,
        "ema50": 36.5,
        "roe": 16.8,
        "net_margin": 8.5,
        "debt_to_equity": 0.54,
        "revenue_growth": 9.2,
        "news_sentiment": 0.62,
        "volume_zscore": 0.82,
        "price_vs_52w_high": 0.87,
    },
    {
        "ticker": "BIMAS",
        "company": "BİM Birleşik Mağazalar",
        "sector": "Perakende",
        "price": 450.2,
        "change_1d": -0.8,
        "rsi": 47,
        "ema20": 455.0,
        "ema50": 462.0,
        "roe": 24.1,
        "net_margin": 10.4,
        "debt_to_equity": 0.42,
        "revenue_growth": 12.0,
        "news_sentiment": 0.48,
        "volume_zscore": 0.64,
        "price_vs_52w_high": 0.96,
    },
    {
        "ticker": "ASELS",
        "company": "Aselsan",
        "sector": "Savunma",
        "price": 41.3,
        "change_1d": 2.1,
        "rsi": 71,
        "ema20": 39.9,
        "ema50": 37.8,
        "roe": 20.6,
        "net_margin": 13.8,
        "debt_to_equity": 0.31,
        "revenue_growth": 16.8,
        "news_sentiment": 0.81,
        "volume_zscore": 1.5,
        "price_vs_52w_high": 0.93,
    },
    {
        "ticker": "KCHOL",
        "company": "Koç Holding",
        "sector": "Konsolide",
        "price": 19.8,
        "change_1d": -1.2,
        "rsi": 38,
        "ema20": 20.5,
        "ema50": 21.1,
        "roe": 9.8,
        "net_margin": 6.4,
        "debt_to_equity": 1.11,
        "revenue_growth": 5.1,
        "news_sentiment": 0.19,
        "volume_zscore": 0.41,
        "price_vs_52w_high": 0.84,
    },
]


def _normalize(value: float, lower: float, upper: float) -> float:
    if upper == lower:
        return 50.0
    return max(0.0, min(100.0, ((value - lower) / (upper - lower)) * 100.0))


def score_company(company: Dict[str, object]) -> Recommendation:
    rsi = float(company["rsi"])
    roe = float(company["roe"])
    margin = float(company["net_margin"])
    debt = float(company["debt_to_equity"])
    growth = float(company["revenue_growth"])
    news = float(company["news_sentiment"])
    volume_z = float(company["volume_zscore"])
    price_vs_high = float(company["price_vs_52w_high"])
    price = float(company["price"])
    ema20 = float(company["ema20"])
    ema50 = float(company["ema50"])
    change = float(company["change_1d"])

    technical = 0.0
    if rsi >= 55:
        technical += 35.0
    elif rsi >= 45:
        technical += 20.0
    else:
        technical += 5.0

    if price > ema20:
        technical += 25.0
    elif price > ema50:
        technical += 15.0
    else:
        technical += 5.0

    technical += min(20.0, max(0.0, volume_z * 10.0))
    technical += min(20.0, max(0.0, change * 4.0))

    technical = max(0.0, min(100.0, technical))

    fundamental = 0.0
    fundamental += _normalize(roe, 5.0, 25.0) * 0.4
    fundamental += _normalize(margin, 3.0, 15.0) * 0.3
    fundamental += _normalize(100.0 - debt * 100.0, 0.0, 100.0) * 0.2
    fundamental += _normalize(growth, 2.0, 18.0) * 0.1

    news_score = _normalize(news * 100.0, 10.0, 90.0)
    score = round(0.5 * technical + 0.35 * fundamental + 0.15 * news_score, 1)

    reasons: List[str] = []
    if score >= 75:
        label = "AL"
        reasons.append("Temel ve teknik veriler güçlü bir birleşim sunuyor")
    elif score >= 60:
        label = "BEKLE"
        reasons.append("Pozitif ayrışma var fakat risk yönetimi gerekiyor")
    else:
        label = "SAT"
        reasons.append("Momentum ve finansal görünüm zayıf")

    if price_vs_high >= 0.9:
        reasons.append("52 haftalık zirveye yakın fiyatlanma")
    elif price_vs_high <= 0.8:
        reasons.append("Fiyat, 52 haftalık ortalamanın altında")

    if rsi >= 60:
        reasons.append("RSI yükseliş ivmesi gösteriyor")
    elif rsi <= 40:
        reasons.append("RSI zayıf momentum işareti veriyor")

    if news >= 0.7:
        reasons.append("Haber akışı olumlu ağırlıklı")
    elif news <= 0.3:
        reasons.append("Haber akışı olumsuz ağırlıklı")

    return Recommendation(
        ticker=str(company["ticker"]),
        company=str(company["company"]),
        sector=str(company["sector"]),
        score=score,
        label=label,
        reasons=reasons,
    )


def make_recommendations(companies: List[Dict[str, object]] | None = None) -> List[Recommendation]:
    pool = companies or SAMPLE_COMPANIES
    recommendations = [score_company(company) for company in pool]
    recommendations.sort(key=lambda item: item.score, reverse=True)
    return recommendations
