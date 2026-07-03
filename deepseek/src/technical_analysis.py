"""DeepSeek BIST30 - Teknik Analiz Motoru"""
from __future__ import annotations

import math
from typing import List, Dict
from dataclasses import dataclass

from .data_models import TechnicalData


# BIST30 hisseleri için simüle edilmiş teknik veriler (gerçek veri API'si olmadığında kullanılır)
# Gerçek kullanımda yfinance veya başka bir API'den çekilir
BIST30_TECHNICAL_SAMPLE: Dict[str, Dict] = {
    "AKBNK":  {"price": 77.85, "change_1d": 1.2, "change_5d": 3.5, "change_20d": 8.2, "change_60d": 15.8,
               "rsi": 62, "macd": 1.45, "macd_signal": 1.10, "bb_upper": 82.0, "bb_middle": 75.5, "bb_lower": 69.0,
               "ma20": 74.2, "ma50": 70.5, "ma200": 62.8, "volume_ratio": 1.35, "stoch_k": 68, "stoch_d": 55,
               "atr_pct": 2.8, "vs_52w_high": 88.5, "vs_52w_low": 145.0, "rel_strength": 1.08, "beta": 1.15,
               "volatility": 28.5, "max_dd": 18.2},
    "GARAN":  {"price": 138.60, "change_1d": 0.8, "change_5d": 2.8, "change_20d": 6.5, "change_60d": 12.4,
               "rsi": 58, "macd": 2.80, "macd_signal": 2.30, "bb_upper": 148.0, "bb_middle": 135.0, "bb_lower": 122.0,
               "ma20": 134.5, "ma50": 128.0, "ma200": 110.5, "volume_ratio": 1.20, "stoch_k": 60, "stoch_d": 52,
               "atr_pct": 2.5, "vs_52w_high": 82.0, "vs_52w_low": 155.0, "rel_strength": 1.05, "beta": 1.10,
               "volatility": 26.0, "max_dd": 16.5},
    "ISCTR":  {"price": 15.20, "change_1d": -0.5, "change_5d": 1.2, "change_20d": 4.8, "change_60d": 10.5,
               "rsi": 52, "macd": 0.15, "macd_signal": 0.12, "bb_upper": 16.2, "bb_middle": 15.0, "bb_lower": 13.8,
               "ma20": 14.95, "ma50": 14.2, "ma200": 12.5, "volume_ratio": 0.95, "stoch_k": 48, "stoch_d": 45,
               "atr_pct": 2.2, "vs_52w_high": 78.0, "vs_52w_low": 135.0, "rel_strength": 0.98, "beta": 1.05,
               "volatility": 24.0, "max_dd": 15.0},
    "YKBNK":  {"price": 32.80, "change_1d": 1.5, "change_5d": 4.2, "change_20d": 9.5, "change_60d": 18.2,
               "rsi": 65, "macd": 0.85, "macd_signal": 0.65, "bb_upper": 35.0, "bb_middle": 31.5, "bb_lower": 28.0,
               "ma20": 31.2, "ma50": 29.5, "ma200": 25.8, "volume_ratio": 1.50, "stoch_k": 72, "stoch_d": 60,
               "atr_pct": 3.0, "vs_52w_high": 90.0, "vs_52w_low": 160.0, "rel_strength": 1.12, "beta": 1.20,
               "volatility": 30.0, "max_dd": 20.0},
    "KCHOL":  {"price": 191.60, "change_1d": 0.3, "change_5d": 2.1, "change_20d": 5.8, "change_60d": 11.0,
               "rsi": 55, "macd": 2.50, "macd_signal": 2.10, "bb_upper": 200.0, "bb_middle": 188.0, "bb_lower": 176.0,
               "ma20": 187.5, "ma50": 182.0, "ma200": 165.0, "volume_ratio": 1.05, "stoch_k": 55, "stoch_d": 50,
               "atr_pct": 2.0, "vs_52w_high": 85.0, "vs_52w_low": 140.0, "rel_strength": 1.02, "beta": 0.95,
               "volatility": 22.0, "max_dd": 14.5},
    "SAHOL":  {"price": 92.50, "change_1d": 0.6, "change_5d": 2.5, "change_20d": 6.2, "change_60d": 12.8,
               "rsi": 57, "macd": 1.20, "macd_signal": 1.00, "bb_upper": 98.0, "bb_middle": 91.0, "bb_lower": 84.0,
               "ma20": 90.5, "ma50": 87.0, "ma200": 78.5, "volume_ratio": 1.10, "stoch_k": 56, "stoch_d": 50,
               "atr_pct": 2.1, "vs_52w_high": 83.0, "vs_52w_low": 148.0, "rel_strength": 1.03, "beta": 0.98,
               "volatility": 23.0, "max_dd": 15.0},
    "THYAO":  {"price": 334.00, "change_1d": -1.2, "change_5d": 0.5, "change_20d": -2.5, "change_60d": 8.5,
               "rsi": 44, "macd": -1.50, "macd_signal": -0.80, "bb_upper": 355.0, "bb_middle": 338.0, "bb_lower": 321.0,
               "ma20": 338.5, "ma50": 342.0, "ma200": 315.0, "volume_ratio": 0.85, "stoch_k": 38, "stoch_d": 42,
               "atr_pct": 2.6, "vs_52w_high": 72.0, "vs_52w_low": 125.0, "rel_strength": 0.92, "beta": 1.08,
               "volatility": 27.0, "max_dd": 22.0},
    "PGSUS":  {"price": 280.50, "change_1d": 2.1, "change_5d": 5.8, "change_20d": 12.5, "change_60d": 22.0,
               "rsi": 68, "macd": 8.50, "macd_signal": 6.80, "bb_upper": 295.0, "bb_middle": 272.0, "bb_lower": 249.0,
               "ma20": 270.0, "ma50": 258.0, "ma200": 235.0, "volume_ratio": 1.60, "stoch_k": 78, "stoch_d": 68,
               "atr_pct": 3.2, "vs_52w_high": 92.0, "vs_52w_low": 175.0, "rel_strength": 1.15, "beta": 1.25,
               "volatility": 32.0, "max_dd": 24.0},
    "TUPRS":  {"price": 239.90, "change_1d": 0.2, "change_5d": 1.8, "change_20d": 4.5, "change_60d": 9.2,
               "rsi": 54, "macd": 2.20, "macd_signal": 1.90, "bb_upper": 250.0, "bb_middle": 237.0, "bb_lower": 224.0,
               "ma20": 236.5, "ma50": 230.0, "ma200": 210.0, "volume_ratio": 0.95, "stoch_k": 52, "stoch_d": 48,
               "atr_pct": 1.9, "vs_52w_high": 80.0, "vs_52w_low": 138.0, "rel_strength": 1.01, "beta": 0.90,
               "volatility": 20.0, "max_dd": 12.0},
    "EREGL":  {"price": 41.22, "change_1d": 1.8, "change_5d": 4.5, "change_20d": 8.8, "change_60d": 15.5,
               "rsi": 61, "macd": 0.65, "macd_signal": 0.50, "bb_upper": 43.5, "bb_middle": 40.0, "bb_lower": 36.5,
               "ma20": 39.8, "ma50": 37.5, "ma200": 33.0, "volume_ratio": 1.40, "stoch_k": 65, "stoch_d": 55,
               "atr_pct": 2.9, "vs_52w_high": 85.0, "vs_52w_low": 155.0, "rel_strength": 1.06, "beta": 1.12,
               "volatility": 29.0, "max_dd": 19.0},
    "BIMAS":  {"price": 512.00, "change_1d": -0.8, "change_5d": -1.5, "change_20d": 2.5, "change_60d": 8.0,
               "rsi": 46, "macd": -2.50, "macd_signal": -1.80, "bb_upper": 535.0, "bb_middle": 518.0, "bb_lower": 501.0,
               "ma20": 518.5, "ma50": 522.0, "ma200": 495.0, "volume_ratio": 0.75, "stoch_k": 40, "stoch_d": 44,
               "atr_pct": 1.8, "vs_52w_high": 70.0, "vs_52w_low": 118.0, "rel_strength": 0.95, "beta": 0.85,
               "volatility": 18.0, "max_dd": 10.0},
    "MGROS":  {"price": 696.50, "change_1d": 0.5, "change_5d": 1.8, "change_20d": 5.2, "change_60d": 14.5,
               "rsi": 56, "macd": 5.80, "macd_signal": 4.50, "bb_upper": 720.0, "bb_middle": 688.0, "bb_lower": 656.0,
               "ma20": 686.0, "ma50": 668.0, "ma200": 620.0, "volume_ratio": 1.15, "stoch_k": 58, "stoch_d": 52,
               "atr_pct": 2.2, "vs_52w_high": 82.0, "vs_52w_low": 142.0, "rel_strength": 1.04, "beta": 0.92,
               "volatility": 21.0, "max_dd": 13.0},
    "FROTO":  {"price": 86.20, "change_1d": 0.9, "change_5d": 3.2, "change_20d": 7.5, "change_60d": 16.0,
               "rsi": 60, "macd": 1.10, "macd_signal": 0.85, "bb_upper": 90.0, "bb_middle": 84.0, "bb_lower": 78.0,
               "ma20": 83.5, "ma50": 80.0, "ma200": 72.0, "volume_ratio": 1.25, "stoch_k": 63, "stoch_d": 54,
               "atr_pct": 2.4, "vs_52w_high": 84.0, "vs_52w_low": 150.0, "rel_strength": 1.07, "beta": 1.05,
               "volatility": 25.0, "max_dd": 17.0},
    "TOASO":  {"price": 385.00, "change_1d": 1.8, "change_5d": 5.5, "change_20d": 12.0, "change_60d": 25.0,
               "rsi": 70, "macd": 12.50, "macd_signal": 9.80, "bb_upper": 405.0, "bb_middle": 378.0, "bb_lower": 351.0,
               "ma20": 375.0, "ma50": 358.0, "ma200": 320.0, "volume_ratio": 1.80, "stoch_k": 82, "stoch_d": 72,
               "atr_pct": 3.5, "vs_52w_high": 95.0, "vs_52w_low": 190.0, "rel_strength": 1.18, "beta": 1.30,
               "volatility": 35.0, "max_dd": 26.0},
    "ASELS":  {"price": 78.50, "change_1d": 2.5, "change_5d": 6.8, "change_20d": 15.2, "change_60d": 28.0,
               "rsi": 72, "macd": 3.20, "macd_signal": 2.50, "bb_upper": 82.0, "bb_middle": 75.0, "bb_lower": 68.0,
               "ma20": 74.5, "ma50": 70.0, "ma200": 60.5, "volume_ratio": 2.10, "stoch_k": 85, "stoch_d": 75,
               "atr_pct": 3.8, "vs_52w_high": 96.0, "vs_52w_low": 210.0, "rel_strength": 1.22, "beta": 1.35,
               "volatility": 38.0, "max_dd": 28.0},
    "TCELL":  {"price": 98.40, "change_1d": -0.2, "change_5d": 0.8, "change_20d": 3.5, "change_60d": 6.5,
               "rsi": 50, "macd": 0.35, "macd_signal": 0.30, "bb_upper": 103.0, "bb_middle": 97.5, "bb_lower": 92.0,
               "ma20": 97.2, "ma50": 95.5, "ma200": 90.0, "volume_ratio": 0.85, "stoch_k": 48, "stoch_d": 46,
               "atr_pct": 1.6, "vs_52w_high": 75.0, "vs_52w_low": 128.0, "rel_strength": 0.96, "beta": 0.82,
               "volatility": 16.0, "max_dd": 9.0},
    "TTKOM":  {"price": 42.50, "change_1d": 0.4, "change_5d": 1.5, "change_20d": 4.0, "change_60d": 7.2,
               "rsi": 53, "macd": 0.40, "macd_signal": 0.35, "bb_upper": 44.5, "bb_middle": 42.0, "bb_lower": 39.5,
               "ma20": 41.8, "ma50": 40.5, "ma200": 38.0, "volume_ratio": 0.90, "stoch_k": 50, "stoch_d": 48,
               "atr_pct": 1.7, "vs_52w_high": 78.0, "vs_52w_low": 130.0, "rel_strength": 0.99, "beta": 0.88,
               "volatility": 17.0, "max_dd": 10.0},
    "SISE":   {"price": 55.80, "change_1d": 0.7, "change_5d": 2.2, "change_20d": 5.5, "change_60d": 10.8,
               "rsi": 56, "macd": 0.72, "macd_signal": 0.60, "bb_upper": 58.5, "bb_middle": 55.0, "bb_lower": 51.5,
               "ma20": 54.8, "ma50": 52.5, "ma200": 48.0, "volume_ratio": 1.05, "stoch_k": 54, "stoch_d": 50,
               "atr_pct": 2.0, "vs_52w_high": 82.0, "vs_52w_low": 145.0, "rel_strength": 1.02, "beta": 0.96,
               "volatility": 20.0, "max_dd": 13.0},
    "VAKBN":  {"price": 24.60, "change_1d": 1.0, "change_5d": 3.0, "change_20d": 7.2, "change_60d": 14.0,
               "rsi": 60, "macd": 0.55, "macd_signal": 0.42, "bb_upper": 26.0, "bb_middle": 24.0, "bb_lower": 22.0,
               "ma20": 23.8, "ma50": 22.5, "ma200": 20.0, "volume_ratio": 1.30, "stoch_k": 64, "stoch_d": 55,
               "atr_pct": 2.8, "vs_52w_high": 88.0, "vs_52w_low": 150.0, "rel_strength": 1.06, "beta": 1.12,
               "volatility": 27.0, "max_dd": 18.0},
    "AKSEN":  {"price": 38.20, "change_1d": 1.5, "change_5d": 4.0, "change_20d": 9.0, "change_60d": 18.0,
               "rsi": 64, "macd": 0.95, "macd_signal": 0.75, "bb_upper": 40.5, "bb_middle": 37.0, "bb_lower": 33.5,
               "ma20": 36.8, "ma50": 34.5, "ma200": 30.0, "volume_ratio": 1.45, "stoch_k": 70, "stoch_d": 58,
               "atr_pct": 3.1, "vs_52w_high": 90.0, "vs_52w_low": 165.0, "rel_strength": 1.10, "beta": 1.18,
               "volatility": 31.0, "max_dd": 21.0},
    "ULKER":  {"price": 125.50, "change_1d": 0.1, "change_5d": 1.2, "change_20d": 3.8, "change_60d": 7.5,
               "rsi": 51, "macd": 0.80, "macd_signal": 0.70, "bb_upper": 130.0, "bb_middle": 124.0, "bb_lower": 118.0,
               "ma20": 123.5, "ma50": 120.0, "ma200": 112.0, "volume_ratio": 0.90, "stoch_k": 49, "stoch_d": 47,
               "atr_pct": 1.7, "vs_52w_high": 75.0, "vs_52w_low": 130.0, "rel_strength": 0.97, "beta": 0.85,
               "volatility": 17.0, "max_dd": 10.5},
    "CCOLA":  {"price": 680.00, "change_1d": 1.2, "change_5d": 3.5, "change_20d": 8.5, "change_60d": 18.0,
               "rsi": 63, "macd": 10.50, "macd_signal": 8.50, "bb_upper": 710.0, "bb_middle": 668.0, "bb_lower": 626.0,
               "ma20": 665.0, "ma50": 642.0, "ma200": 590.0, "volume_ratio": 1.25, "stoch_k": 66, "stoch_d": 56,
               "atr_pct": 2.6, "vs_52w_high": 85.0, "vs_52w_low": 155.0, "rel_strength": 1.08, "beta": 1.00,
               "volatility": 24.0, "max_dd": 15.0},
    "ARCLK":  {"price": 175.00, "change_1d": -0.3, "change_5d": 0.5, "change_20d": 2.8, "change_60d": 5.5,
               "rsi": 48, "macd": -0.50, "macd_signal": -0.20, "bb_upper": 182.0, "bb_middle": 176.0, "bb_lower": 170.0,
               "ma20": 176.5, "ma50": 178.0, "ma200": 168.0, "volume_ratio": 0.80, "stoch_k": 42, "stoch_d": 45,
               "atr_pct": 1.5, "vs_52w_high": 68.0, "vs_52w_low": 115.0, "rel_strength": 0.93, "beta": 0.80,
               "volatility": 15.0, "max_dd": 8.0},
    "EKGYO":  {"price": 9.85, "change_1d": 2.5, "change_5d": 6.5, "change_20d": 14.0, "change_60d": 25.0,
               "rsi": 74, "macd": 0.45, "macd_signal": 0.35, "bb_upper": 10.20, "bb_middle": 9.50, "bb_lower": 8.80,
               "ma20": 9.45, "ma50": 9.00, "ma200": 8.00, "volume_ratio": 2.20, "stoch_k": 88, "stoch_d": 78,
               "atr_pct": 4.0, "vs_52w_high": 98.0, "vs_52w_low": 220.0, "rel_strength": 1.25, "beta": 1.40,
               "volatility": 40.0, "max_dd": 30.0},
}


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """RSI hesaplama"""
    if len(prices) < period + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        gains.append(diff if diff > 0 else 0)
        losses.append(abs(diff) if diff < 0 else 0)
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD hesaplama"""
    if len(prices) < slow + signal:
        return 0.0, 0.0, 0.0
    ema_fast = sum(prices[-fast:]) / fast
    ema_slow = sum(prices[-slow:]) / slow
    macd_line = ema_fast - ema_slow
    signal_line = macd_line * (2 / (signal + 1)) + macd_line
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0):
    """Bollinger Bantları hesaplama"""
    if len(prices) < period:
        mid = sum(prices) / len(prices)
        return mid * 1.05, mid, mid * 0.95, 50.0
    recent = prices[-period:]
    mid = sum(recent) / period
    variance = sum((x - mid) ** 2 for x in recent) / period
    std = math.sqrt(variance)
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    current = prices[-1]
    if upper != lower:
        position = ((current - lower) / (upper - lower)) * 100
    else:
        position = 50.0
    return round(upper, 2), round(mid, 2), round(lower, 2), round(position, 1)


def calculate_atr(prices_high: List[float], prices_low: List[float], prices_close: List[float], period: int = 14) -> float:
    """ATR hesaplama"""
    if len(prices_close) < 2:
        return prices_close[-1] * 0.02
    tr_list = []
    for i in range(1, len(prices_close)):
        h, l, pc = prices_high[i], prices_low[i], prices_close[i - 1]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        tr_list.append(tr)
    if not tr_list:
        return prices_close[-1] * 0.02
    return sum(tr_list[-period:]) / min(period, len(tr_list))


def get_technical_data(ticker: str) -> TechnicalData:
    """Bir hisse için teknik veri üretir (önce canlı Yahoo verisi, sonra örnek)."""
    data = None
    try:
        from .live_data import get_live_technical
        data = get_live_technical(ticker)
    except Exception:
        data = None
    if not data:
        data = BIST30_TECHNICAL_SAMPLE.get(ticker)
    if not data:
        data = {
            "price": 50.0, "change_1d": 0.0, "change_5d": 0.0, "change_20d": 0.0, "change_60d": 0.0,
            "rsi": 50, "macd": 0.0, "macd_signal": 0.0, "bb_upper": 55.0, "bb_middle": 50.0, "bb_lower": 45.0,
            "ma20": 50.0, "ma50": 50.0, "ma200": 50.0, "volume_ratio": 1.0, "stoch_k": 50, "stoch_d": 50,
            "atr_pct": 2.0, "vs_52w_high": 80.0, "vs_52w_low": 120.0, "rel_strength": 1.0, "beta": 1.0,
            "volatility": 20.0, "max_dd": 15.0
        }

    price = data["price"]
    bb_pos = ((price - data["bb_lower"]) / (data["bb_upper"] - data["bb_lower"])) * 100 if data["bb_upper"] != data["bb_lower"] else 50.0

    return TechnicalData(
        ticker=ticker,
        price=price,
        change_1d_pct=data["change_1d"],
        change_5d_pct=data["change_5d"],
        change_20d_pct=data["change_20d"],
        change_60d_pct=data["change_60d"],
        rsi_14=data["rsi"],
        macd=data["macd"],
        macd_signal=data["macd_signal"],
        macd_histogram=data["macd"] - data["macd_signal"],
        bb_upper=data["bb_upper"],
        bb_middle=data["bb_middle"],
        bb_lower=data["bb_lower"],
        bb_position_pct=round(bb_pos, 1),
        ma_20=data["ma20"],
        ma_50=data["ma50"],
        ma_200=data["ma200"],
        volume=0,
        volume_20d_avg=0,
        volume_ratio=data["volume_ratio"],
        stochastic_k=data["stoch_k"],
        stochastic_d=data["stoch_d"],
        atr_14=price * data["atr_pct"] / 100,
        atr_pct=data["atr_pct"],
        price_vs_52w_high_pct=data["vs_52w_high"],
        price_vs_52w_low_pct=data["vs_52w_low"],
        relative_strength_vs_xu30=data["rel_strength"],
    )


def scan_all_bist30() -> Dict[str, TechnicalData]:
    """Tüm BIST30 hisselerinin teknik verilerini üretir"""
    result = {}
    for ticker in BIST30_TECHNICAL_SAMPLE:
        result[ticker] = get_technical_data(ticker)
    return result