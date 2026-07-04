"""DeepSeek BIST30 - Veri Modelleri"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum


class SignalType(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    WEAK_HOLD = "WEAK_HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class MarketRegime(Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"


@dataclass
class FundamentalData:
    """Temel analiz verileri"""
    ticker: str
    fk_ratio: float                # F/K
    pddd_ratio: float              # PD/DD
    net_profit_growth_qoq: float   # Çeyreklik net kâr büyümesi (%)
    debt_to_equity: float          # Borç/Özsermaye
    roe: float                     # Özsermaye kârlılığı (%)
    ebitda_margin: float           # FAVÖK marjı (%)
    dividend_yield: float          # Temettü verimi (%)
    revenue_growth_yoy: float      # Yıllık ciro büyümesi (%)
    current_ratio: float           # Cari oran


@dataclass
class TechnicalData:
    """Teknik analiz verileri"""
    ticker: str
    price: float
    change_1d_pct: float
    change_5d_pct: float
    change_20d_pct: float
    change_60d_pct: float
    rsi_14: float
    macd: float
    macd_signal: float
    macd_histogram: float
    bb_upper: float
    bb_middle: float
    bb_lower: float
    bb_position_pct: float          # Fiyatın Bollinger içindeki konumu (%)
    ma_20: float
    ma_50: float
    ma_200: float
    volume: int
    volume_20d_avg: int
    volume_ratio: float             # Hacim / 20 günlük ortalama
    stochastic_k: float
    stochastic_d: float
    atr_14: float
    atr_pct: float                  # ATR / Fiyat (%)
    price_vs_52w_high_pct: float    # 52H zirveye uzaklık (%)
    price_vs_52w_low_pct: float     # 52H dibe uzaklık (%)
    relative_strength_vs_xu30: float  # XU30'a göre rölatif güç


@dataclass
class NewsItem:
    """Haber/KAP öğesi"""
    title: str
    source: str
    url: str
    sentiment: float                # -1.0 (çok negatif) ile +1.0 (çok pozitif)
    impact_score: float             # 0-10 arası piyasa etki skoru
    categories: List[str] = field(default_factory=list)
    timestamp: str = ""


@dataclass
class RiskMetrics:
    """Risk metrikleri"""
    beta: float
    var_95_daily: float             # %95 güven seviyesinde günlük VaR (%)
    max_drawdown_60d: float         # 60 günlük maksimum düşüş (%)
    volatility_20d: float           # 20 günlük volatilite (%)
    volatility_regime: str          # LOW / NORMAL / HIGH


@dataclass
class CompanySnapshot:
    """Bir şirketin tam anlık görüntüsü"""
    ticker: str
    company_name: str
    sector: str
    fundamental: Optional[FundamentalData] = None
    technical: Optional[TechnicalData] = None
    news: List[NewsItem] = field(default_factory=list)
    risk: Optional[RiskMetrics] = None
    deepscore: float = 0.0
    signal: SignalType = SignalType.HOLD
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    last_updated: str = ""


@dataclass
class Position:
    """Portföy pozisyonu"""
    ticker: str
    company_name: str
    sector: str
    entry_price: float
    quantity: int
    entry_date: str
    cost_basis: float              # Toplam maliyet
    stop_loss: float
    take_profit: float
    trailing_stop_active: bool = False
    trailing_stop_level: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    days_held: int = 0
    deepscore_at_entry: float = 0.0


@dataclass
class Transaction:
    """İşlem kaydı"""
    id: str
    timestamp: str
    type: str                       # BUY / SELL
    ticker: str
    quantity: int
    price: float
    total_amount: float
    commission: float
    reason: str
    signal_type: SignalType
    deepscore: float


@dataclass
class PortfolioState:
    """Portföy durumu"""
    name: str = "DeepSeek BIST30 Portföy"
    initial_capital: float = 50000.0
    cash: float = 50000.0
    positions: List[Position] = field(default_factory=list)
    transactions: List[Transaction] = field(default_factory=list)
    total_value: float = 50000.0
    total_return_pct: float = 0.0
    benchmark_return_pct: float = 0.0
    alpha_pct: float = 0.0
    week: int = 0
    current_drawdown_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate_pct: float = 0.0
    market_regime: MarketRegime = MarketRegime.SIDEWAYS
    last_updated: str = ""
    created_date: str = "2026-07-03"


@dataclass
class WeeklyResult:
    """Haftalık yarışma sonucu"""
    week: int
    start_date: str
    end_date: str
    deepseek_return_pct: float
    xu30_return_pct: float
    competitor_returns: Dict[str, float] = field(default_factory=dict)
    deepseek_alpha: float = 0.0
    transactions_count: int = 0
    win_trades: int = 0
    loss_trades: int = 0
    best_performer: str = ""
    worst_performer: str = ""
    key_lessons: List[str] = field(default_factory=list)
    market_regime: str = ""


@dataclass
class SimulationResult:
    """52 haftalık simülasyon sonucu"""
    total_return_pct: float
    annualized_return_pct: float
    xu30_return_pct: float
    alpha_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    total_transactions: int
    weekly_results: List[WeeklyResult] = field(default_factory=list)
    final_portfolio_value: float = 0.0
    best_week_pct: float = 0.0
    worst_week_pct: float = 0.0
    profit_factor: float = 0.0