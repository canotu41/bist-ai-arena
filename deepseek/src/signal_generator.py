"""DeepSeek BIST30 - DeepScore™ Sinyal Üretim Motoru"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Tuple

from .data_models import (
    CompanySnapshot, SignalType, MarketRegime,
    FundamentalData, TechnicalData, RiskMetrics,
)
from .fundamental_analysis import (
    get_fundamental_data, score_fundamental,
    SECTOR_MAP, COMPANY_NAMES,
)
from .technical_analysis import get_technical_data
from .news_tracker import get_news_sentiment_score, get_overall_market_sentiment


def calculate_technical_score(tech: TechnicalData) -> float:
    """Teknik analiz skoru (0-100)"""
    score = 0.0

    # RSI: 40-70 arası ideal, <30 aşırı satım (al fırsatı), >70 aşırı alım
    if 40 <= tech.rsi_14 <= 70:
        score += 30.0
    elif tech.rsi_14 < 30:
        score += 25.0  # aşırı satım fırsatı
    elif tech.rsi_14 > 70:
        score += 10.0  # aşırı alım riski

    # Trend: MA20 > MA50 > MA200 en güçlü
    if tech.ma_20 > tech.ma_50 > tech.ma_200:
        score += 25.0
    elif tech.price > tech.ma_50:
        score += 15.0
    elif tech.price > tech.ma_200:
        score += 10.0
    else:
        score += 3.0

    # MACD
    if tech.macd_histogram > 0 and tech.macd > tech.macd_signal:
        score += 15.0
    elif tech.macd_histogram > 0:
        score += 10.0
    else:
        score += 3.0

    # Bollinger konumu: 20-80 arası normal, <20 dip, >80 zirve
    if 20 <= tech.bb_position_pct <= 80:
        score += 10.0
    elif tech.bb_position_pct < 20:
        score += 12.0  # potansiyel dip
    else:
        score += 5.0

    # Hacim: >1.2 katı olumlu
    if tech.volume_ratio > 1.5:
        score += 10.0
    elif tech.volume_ratio > 1.0:
        score += 7.0
    else:
        score += 3.0

    # Stochastic
    if 20 <= tech.stochastic_k <= 80:
        score += 5.0
    elif tech.stochastic_k < 20:
        score += 8.0  # aşırı satım
    else:
        score += 2.0

    # Göreceli güç vs XU30
    if tech.relative_strength_vs_xu30 > 1.05:
        score += 5.0
    elif tech.relative_strength_vs_xu30 > 1.0:
        score += 3.0
    else:
        score += 1.0

    return min(100.0, score)


def calculate_momentum_score(tech: TechnicalData) -> float:
    """Momentum skoru (0-100)"""
    score = 0.0
    # Kısa vadeli momentum
    if tech.change_5d_pct > 3:
        score += 30.0
    elif tech.change_5d_pct > 0:
        score += 20.0
    elif tech.change_5d_pct > -3:
        score += 10.0
    else:
        score += 3.0
    # Orta vadeli
    if tech.change_20d_pct > 8:
        score += 30.0
    elif tech.change_20d_pct > 3:
        score += 22.0
    elif tech.change_20d_pct > -3:
        score += 12.0
    else:
        score += 3.0
    # Uzun vadeli
    if tech.change_60d_pct > 15:
        score += 25.0
    elif tech.change_60d_pct > 5:
        score += 18.0
    elif tech.change_60d_pct > -5:
        score += 10.0
    else:
        score += 3.0
    # Göreceli güç
    if tech.relative_strength_vs_xu30 > 1.1:
        score += 15.0
    elif tech.relative_strength_vs_xu30 > 1.0:
        score += 10.0
    else:
        score += 5.0
    return min(100.0, score)


def calculate_risk_score(tech: TechnicalData) -> float:
    """Risk/Volatilite skoru (0-100, yüksek = düşük risk)"""
    score = 50.0  # nötr başlangıç
    # ATR düşükse risk düşük
    if tech.atr_pct < 2.0:
        score += 25.0
    elif tech.atr_pct < 3.0:
        score += 12.0
    elif tech.atr_pct > 4.0:
        score -= 15.0
    # 52H zirveye çok yakınsa riskli
    if tech.price_vs_52w_high_pct > 95:
        score -= 15.0
    elif tech.price_vs_52w_high_pct > 85:
        score -= 5.0
    if tech.price_vs_52w_low_pct > 180:
        score -= 10.0
    # Volatilite
    if tech.relative_strength_vs_xu30 > 1.2:
        score -= 5.0
    return max(10.0, min(100.0, score))


def detect_market_regime(all_tech: Dict[str, TechnicalData]) -> MarketRegime:
    """Piyasa rejimini tespit eder"""
    avg_rsi = sum(t.rsi_14 for t in all_tech.values()) / len(all_tech)
    avg_ch20 = sum(t.change_20d_pct for t in all_tech.values()) / len(all_tech)
    atrs = [t.atr_pct for t in all_tech.values()]
    avg_atr = sum(atrs) / len(atrs) if atrs else 2.5

    if avg_atr > 3.5:
        return MarketRegime.HIGH_VOLATILITY
    elif avg_rsi > 62 and avg_ch20 > 5:
        return MarketRegime.BULL
    elif avg_rsi < 42 and avg_ch20 < -3:
        return MarketRegime.BEAR
    else:
        return MarketRegime.SIDEWAYS


def calculate_deepscore(ticker: str, tech: TechnicalData, fund: FundamentalData, market_regime: MarketRegime) -> Tuple[float, Dict[str, float]]:
    """DeepScore™ hesaplama (0-100)"""
    # 5 eksenli skor
    fundamental_score = score_fundamental(fund)
    technical_score = calculate_technical_score(tech)
    news_score = get_news_sentiment_score(ticker)
    momentum_score = calculate_momentum_score(tech)
    risk_score = calculate_risk_score(tech)

    # Ağırlıklar
    weights = {"Temel": 0.25, "Teknik": 0.30, "Haber": 0.20, "Momentum": 0.15, "Risk": 0.10}

    # Piyasa rejimine göre dinamik ağırlık ayarı
    if market_regime == MarketRegime.BULL:
        weights["Momentum"] = 0.20
        weights["Risk"] = 0.05
        weights["Temel"] = 0.20
    elif market_regime == MarketRegime.BEAR:
        weights["Temel"] = 0.30
        weights["Risk"] = 0.15
        weights["Momentum"] = 0.10
    elif market_regime == MarketRegime.HIGH_VOLATILITY:
        weights["Risk"] = 0.20
        weights["Teknik"] = 0.25

    # Normalize weights
    total_w = sum(weights.values())
    weights = {k: v / total_w for k, v in weights.items()}

    deepscore = (
        fundamental_score * weights["Temel"]
        + technical_score * weights["Teknik"]
        + news_score * weights["Haber"]
        + momentum_score * weights["Momentum"]
        + risk_score * weights["Risk"]
    )

    breakdown = {
        "Temel": round(fundamental_score, 1),
        "Teknik": round(technical_score, 1),
        "Haber": round(news_score, 1),
        "Momentum": round(momentum_score, 1),
        "Risk": round(risk_score, 1),
    }

    return round(deepscore, 1), breakdown


def determine_signal(deepscore: float, market_regime: MarketRegime) -> SignalType:
    """DeepScore'a göre sinyal belirler"""
    # Piyasa rejimine göre eşikler
    if market_regime == MarketRegime.BULL:
        thresholds = {"strong_buy": 78, "buy": 68, "sell": 35}
    elif market_regime == MarketRegime.BEAR:
        thresholds = {"strong_buy": 82, "buy": 72, "sell": 40}
    else:
        thresholds = {"strong_buy": 75, "buy": 65, "sell": 35}

    if deepscore >= thresholds["strong_buy"]:
        return SignalType.STRONG_BUY
    elif deepscore >= thresholds["buy"]:
        return SignalType.BUY
    elif deepscore >= 55:
        return SignalType.HOLD
    elif deepscore >= thresholds["sell"]:
        return SignalType.WEAK_HOLD
    elif deepscore >= 30:
        return SignalType.SELL
    else:
        return SignalType.STRONG_SELL


def scan_all_companies() -> List[CompanySnapshot]:
    """Tüm BIST30 şirketlerini tarar ve skorlar"""
    all_tech = {}
    all_fund = {}
    for ticker in SECTOR_MAP:
        all_tech[ticker] = get_technical_data(ticker)
        all_fund[ticker] = get_fundamental_data(ticker)

    market_regime = detect_market_regime(all_tech)
    market_sent = get_overall_market_sentiment()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    snapshots = []
    for ticker in SECTOR_MAP:
        tech = all_tech[ticker]
        fund = all_fund[ticker]
        deepscore, breakdown = calculate_deepscore(ticker, tech, fund, market_regime)
        signal = determine_signal(deepscore, market_regime)

        snapshot = CompanySnapshot(
            ticker=ticker,
            company_name=COMPANY_NAMES.get(ticker, ticker),
            sector=SECTOR_MAP[ticker],
            fundamental=fund,
            technical=tech,
            deepscore=deepscore,
            signal=signal,
            score_breakdown=breakdown,
            risk=RiskMetrics(
                beta=tech.relative_strength_vs_xu30 if hasattr(tech, 'relative_strength_vs_xu30') else 1.0,
                var_95_daily=tech.atr_pct * 1.65,
                max_drawdown_60d=20.0,
                volatility_20d=tech.atr_pct * 5,
                volatility_regime="HIGH" if tech.atr_pct > 3.5 else ("NORMAL" if tech.atr_pct > 2.0 else "LOW"),
            ),
            last_updated=now,
        )
        snapshots.append(snapshot)

    snapshots.sort(key=lambda x: x.deepscore, reverse=True)
    return snapshots


def get_top_picks(limit: int = 10) -> List[CompanySnapshot]:
    """En yüksek skorlu hisseleri döndürür"""
    return scan_all_companies()[:limit]