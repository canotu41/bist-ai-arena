"""DeepSeek BIST30 - 52 Haftalık Monte Carlo Simülasyonu"""
from __future__ import annotations

import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

from .data_models import (
    WeeklyResult, SimulationResult, PortfolioState,
    Position, Transaction, SignalType, MarketRegime,
)
from .portfolio_manager import (
    LEARNED_LESSONS, update_market_prices,
    check_stops_and_targets, find_entry_opportunities,
    load_portfolio, save_portfolio, get_sector_exposure,
)
from .signal_generator import scan_all_companies
from .technical_analysis import get_technical_data
from .fundamental_analysis import SECTOR_MAP, COMPANY_NAMES


def simulate_week(
    portfolio: PortfolioState,
    week: int,
    xu30_return_pct: float,
    competitor_returns: Dict[str, float],
    volatility_boost: float = 1.0,
) -> WeeklyResult:
    """Bir haftalık simülasyon çalıştırır"""
    start_date = (datetime(2026, 7, 3) + timedelta(weeks=week - 1)).strftime("%Y-%m-%d")
    end_date = (datetime(2026, 7, 3) + timedelta(weeks=week)).strftime("%Y-%m-%d")

    start_value = portfolio.total_value

    # Hafta boyunca 5 işlem günü × 16 kontrol noktası = 80 döngü
    for day in range(5):
        for checkpoint in range(16):  # 30dk aralıklarla
            # Fiyatları güncelle (simülasyon)
            for pos in portfolio.positions:
                tech = get_technical_data(pos.ticker)
                # Rastgele gürültü ekle
                noise = random.gauss(0, tech.atr_pct / 100 / math.sqrt(16)) * volatility_boost
                pos.current_price *= (1 + noise)
                pos.current_price = max(0.01, pos.current_price)
                pos.unrealized_pnl = (pos.current_price - pos.entry_price) * pos.quantity
                pos.unrealized_pnl_pct = ((pos.current_price - pos.entry_price) / pos.entry_price) * 100

            # Stop/hedef kontrolü
            portfolio.cash += sum(
                pos.current_price * pos.quantity
                for pos in portfolio.positions
                if pos.unrealized_pnl_pct <= -8.0
            )
            portfolio.positions = [
                pos for pos in portfolio.positions
                if pos.unrealized_pnl_pct > -8.0
            ]

            # Trailing stop güncelle
            for pos in portfolio.positions:
                if pos.unrealized_pnl_pct >= 10.0 and not pos.trailing_stop_active:
                    pos.trailing_stop_active = True
                    pos.trailing_stop_level = pos.current_price * 0.95

            portfolio.total_value = portfolio.cash + sum(
                pos.current_price * pos.quantity for pos in portfolio.positions
            )

    end_value = portfolio.total_value
    week_return = round(((end_value - start_value) / start_value) * 100, 2)
    alpha = round(week_return - xu30_return_pct, 2)

    # İşlemleri say
    week_tx = [t for t in portfolio.transactions if start_date <= t.timestamp[:10] <= end_date]
    win_trades = sum(1 for t in week_tx if t.type in ("SELL", "SELL_PARTIAL") and "TAKE-PROFIT" in (t.reason or ""))
    loss_trades = sum(1 for t in week_tx if t.type in ("SELL", "SELL_PARTIAL") and "STOP" in (t.reason or ""))

    # En iyi/kötü performans gösteren
    if portfolio.positions:
        best_pos = max(portfolio.positions, key=lambda p: p.unrealized_pnl_pct)
        worst_pos = min(portfolio.positions, key=lambda p: p.unrealized_pnl_pct)
    else:
        best_pos, worst_pos = None, None

    lessons = []
    if week_return < -3:
        lessons.append("Bu hafta stop-loss disiplini önemliydi")
    if alpha > 2:
        lessons.append("Model XU30'u anlamlı şekilde yendi")
    if loss_trades > win_trades:
        lessons.append("Stop tetiklenmeleri fazla, pozisyon boyutları gözden geçirilmeli")

    return WeeklyResult(
        week=week,
        start_date=start_date,
        end_date=end_date,
        deepseek_return_pct=week_return,
        xu30_return_pct=xu30_return_pct,
        competitor_returns=competitor_returns,
        deepseek_alpha=alpha,
        transactions_count=len(week_tx),
        win_trades=win_trades,
        loss_trades=loss_trades,
        best_performer=f"{best_pos.ticker} (+%{best_pos.unrealized_pnl_pct:.1f})" if best_pos else "-",
        worst_performer=f"{worst_pos.ticker} (%{worst_pos.unrealized_pnl_pct:.1f})" if worst_pos else "-",
        key_lessons=lessons,
        market_regime=portfolio.market_regime.value,
    )


def generate_xu30_scenario() -> List[float]:
    """52 haftalık XU30 senaryosu üretir (yıllık ~%35-40 yükseliş varsayımı)"""
    weekly_returns = []
    base_weekly = 0.006  # ~%0.6 haftalık
    for week in range(52):
        # Mevsimsellik ve rastgele değişim
        seasonal = 0.002 * math.sin(week * math.pi / 26)
        shock = random.gauss(0, 0.025)  # %2.5 std sapma
        week_ret = base_weekly + seasonal + shock
        weekly_returns.append(round(week_ret, 4))
    return weekly_returns


def run_52_week_simulation(initial_capital: float = 10000.0) -> SimulationResult:
    """Tam 52 haftalık simülasyonu çalıştırır"""
    portfolio = PortfolioState(initial_capital=initial_capital)
    xu30_returns = generate_xu30_scenario()

    # Başlangıç portföyü oluştur
    from .portfolio_manager import initialize_portfolio
    portfolio = initialize_portfolio()

    weekly_results: List[WeeklyResult] = []
    cumulative_xu30 = 0.0
    cumulative_portfolio = 0.0
    weekly_portfolio_returns: List[float] = []
    peak_value = initial_capital
    max_dd = 0.0

    all_transactions = 0
    win_trades_total = 0
    loss_trades_total = 0

    # Rakiplerin varsayımsal getirileri
    competitor_tracker = {"Claude AI": 0.0, "Codex": 0.0, "Microsoft Copilot": 0.0}

    for week in range(1, 53):
        xu30_w = xu30_returns[week - 1]
        cumulative_xu30 = (1 + cumulative_xu30 / 100) * (1 + xu30_w * 100) * 100 - 100

        # Rakipler için rastgele performans (DeepSeek'e yakın ama farklı)
        competitor_returns = {}
        for name in competitor_tracker:
            comp_ret = round(xu30_w * 100 + random.gauss(0.2, 1.5), 2)
            competitor_returns[name] = comp_ret
            competitor_tracker[name] = (1 + competitor_tracker[name] / 100) * (1 + comp_ret / 100) * 100 - 100

        # Volatilite boost (bazı dönemler daha volatil)
        vol_boost = 1.0
        if 10 <= week <= 15:  # bilanço sezonu
            vol_boost = 1.5
        elif 30 <= week <= 35:  # yıl sonu
            vol_boost = 1.3

        weekly_result = simulate_week(
            portfolio, week, xu30_w * 100, competitor_returns, vol_boost,
        )
        weekly_results.append(weekly_result)
        portfolio.week = week

        weekly_portfolio_returns.append(weekly_result.deepseek_return_pct / 100)
        cumulative_portfolio = (1 + cumulative_portfolio / 100) * (1 + weekly_result.deepseek_return_pct / 100) * 100 - 100

        all_transactions += weekly_result.transactions_count
        win_trades_total += weekly_result.win_trades
        loss_trades_total += weekly_result.loss_trades

        # DD takibi
        if portfolio.total_value > peak_value:
            peak_value = portfolio.total_value
        dd = (portfolio.total_value - peak_value) / peak_value * 100
        max_dd = min(max_dd, dd)

    # Final metrikler
    total_return = round(cumulative_portfolio, 2)

    # Sharpe ratio (risksiz faiz ~%40 yıllık = ~%0.77 haftalık)
    risk_free_weekly = 0.0077
    excess_returns = [r - risk_free_weekly for r in weekly_portfolio_returns]
    if excess_returns:
        avg_excess = sum(excess_returns) / len(excess_returns)
        std_excess = math.sqrt(sum((r - avg_excess) ** 2 for r in excess_returns) / len(excess_returns))
        sharpe = round((avg_excess / std_excess) * math.sqrt(52), 2) if std_excess > 0 else 0.0
    else:
        sharpe = 0.0

    total_trades = win_trades_total + loss_trades_total
    win_rate = round(win_trades_total / total_trades * 100, 1) if total_trades > 0 else 0.0

    # Profit factor
    gross_profit = sum(
        (t.total_amount - t.commission) for t in portfolio.transactions
        if t.type in ("SELL", "SELL_PARTIAL") and "TAKE-PROFIT" in (t.reason or "")
    )
    gross_loss = abs(sum(
        (t.total_amount - t.commission) for t in portfolio.transactions
        if t.type in ("SELL", "SELL_PARTIAL") and "STOP" in (t.reason or "")
    ))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 999.0

    return SimulationResult(
        total_return_pct=total_return,
        annualized_return_pct=total_return,
        xu30_return_pct=round(cumulative_xu30, 2),
        alpha_pct=round(total_return - cumulative_xu30, 2),
        sharpe_ratio=sharpe,
        max_drawdown_pct=round(max_dd, 2),
        win_rate_pct=win_rate,
        total_transactions=all_transactions,
        weekly_results=weekly_results,
        final_portfolio_value=round(portfolio.total_value, 2),
        best_week_pct=max(weekly_portfolio_returns) * 100 if weekly_portfolio_returns else 0.0,
        worst_week_pct=min(weekly_portfolio_returns) * 100 if weekly_portfolio_returns else 0.0,
        profit_factor=profit_factor,
    )


def quick_simulation_report() -> str:
    """Hızlı simülasyon raporu döndürür"""
    result = run_52_week_simulation(10000.0)
    lines = [
        "=" * 60,
        "   DeepSeek BIST30 — 52 Haftalık Simülasyon Sonucu",
        "=" * 60,
        "",
        f"  Başlangıç Sermayesi:     10,000.00 TL",
        f"  Final Portföy Değeri:     {result.final_portfolio_value:,.2f} TL",
        f"  Toplam Getiri:            %{result.total_return_pct:+.2f}",
        f"  XU30 Getirisi:            %{result.xu30_return_pct:+.2f}",
        f"  Alfa (Fazla Getiri):      %{result.alpha_pct:+.2f}",
        f"  Sharpe Ratio:             {result.sharpe_ratio:.2f}",
        f"  Maksimum Drawdown:        %{result.max_drawdown_pct:.2f}",
        f"  İşlem İsabet Oranı:       %{result.win_rate_pct:.1f}",
        f"  Toplam İşlem:             {result.total_transactions}",
        f"  Profit Factor:            {result.profit_factor:.2f}",
        f"  En İyi Hafta:             %{result.best_week_pct:+.2f}",
        f"  En Kötü Hafta:            %{result.worst_week_pct:+.2f}",
        "",
        "=" * 60,
    ]
    return "\n".join(lines)