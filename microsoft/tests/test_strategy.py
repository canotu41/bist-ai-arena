import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.strategy import make_recommendations, score_company, SAMPLE_COMPANIES


class StrategyTests(unittest.TestCase):
    def test_scoring_returns_expected_label(self) -> None:
        recommendation = score_company(SAMPLE_COMPANIES[0])
        self.assertGreaterEqual(recommendation.score, 0.0)
        self.assertLessEqual(recommendation.score, 100.0)
        self.assertIn(recommendation.label, {"AL", "BEKLE", "SAT"})

    def test_recommendations_are_sorted(self) -> None:
        recommendations = make_recommendations(SAMPLE_COMPANIES)
        scores = [item.score for item in recommendations]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
