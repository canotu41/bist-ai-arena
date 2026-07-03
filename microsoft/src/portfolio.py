from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from src.strategy import Recommendation


@dataclass
class Position:
    ticker: str
    company: str
    entry_price: float
    quantity: int
    weight: float
    current_price: float | None = None


@dataclass
class Portfolio:
    initial_cash: float
    positions: List[Position] = field(default_factory=list)
    cash: float = 0.0
    week: int = 1
    total_value: float = 0.0


def _simulate_price_change(price: float, week: int) -> float:
    drift = 0.02 if week % 2 == 0 else -0.01
    noise = 0.005 if week % 3 == 0 else 0.0
    return price * (1 + drift + noise)


def build_initial_portfolio(recommendations: List[Recommendation], initial_cash: float = 100000.0, max_positions: int = 3) -> Portfolio:
    selected = recommendations[:max_positions]
    total_allocated = 0.0
    positions: List[Position] = []
    for item in selected:
        if total_allocated >= initial_cash:
            break
        position_value = initial_cash / max_positions
        quantity = max(1, int(position_value / 10))
        entry_price = 10.0 + (len(positions) * 2.5)
        total_allocated += quantity * entry_price
        positions.append(
            Position(
                ticker=item.ticker,
                company=item.company,
                entry_price=entry_price,
                quantity=quantity,
                weight=1.0 / max_positions,
                current_price=entry_price,
            )
        )

    cash = initial_cash - total_allocated
    total_value = total_allocated + cash
    return Portfolio(initial_cash=initial_cash, positions=positions, cash=cash, week=1, total_value=total_value)


def apply_weekly_update(portfolio: Portfolio) -> Portfolio:
    next_week = portfolio.week + 1
    updated_positions: List[Position] = []
    for position in portfolio.positions:
        updated_price = _simulate_price_change(position.entry_price, next_week)
        updated_positions.append(
            Position(
                ticker=position.ticker,
                company=position.company,
                entry_price=position.entry_price,
                quantity=position.quantity,
                weight=position.weight,
                current_price=updated_price,
            )
        )

    portfolio_value = sum(pos.quantity * pos.current_price for pos in updated_positions) + portfolio.cash
    portfolio.week = next_week
    portfolio.positions = updated_positions
    portfolio.total_value = round(portfolio_value, 2)
    return portfolio
