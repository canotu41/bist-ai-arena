import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.portfolio import build_initial_portfolio, apply_weekly_update
from src.strategy import make_recommendations, SAMPLE_COMPANIES


class PortfolioTests(unittest.TestCase):
    def test_initial_portfolio_contains_selected_positions(self) -> None:
        recommendations = make_recommendations(SAMPLE_COMPANIES)
        portfolio = build_initial_portfolio(recommendations, initial_cash=100000.0, max_positions=3)
        self.assertEqual(len(portfolio.positions), 3)
        self.assertEqual(portfolio.week, 1)
        self.assertGreater(portfolio.total_value, 0.0)

    def test_weekly_update_changes_total_value(self) -> None:
        recommendations = make_recommendations(SAMPLE_COMPANIES)
        portfolio = build_initial_portfolio(recommendations, initial_cash=100000.0, max_positions=3)
        previous_value = portfolio.total_value
        updated = apply_weekly_update(portfolio)
        self.assertEqual(updated.week, 2)
        self.assertNotEqual(updated.total_value, previous_value)


if __name__ == "__main__":
    unittest.main()
