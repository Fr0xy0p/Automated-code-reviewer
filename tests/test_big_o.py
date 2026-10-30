"""
Unit tests for Big-O Intuition and Limits module.
"""

import unittest
from codereview.complexity.big_o import BigO
from codereview.complexity.limits import (
    estimate_operations,
    predict_time_limit_exceeded,
    recommend_complexity,
)
from codereview.complexity.metrics import (
    classify_cyclomatic_complexity,
    calculate_maintainability_index,
)


class TestBigOModule(unittest.TestCase):

    def test_big_o_ranking_and_max(self):
        self.assertEqual(BigO.max_complexity(BigO.O_1, BigO.O_N), BigO.O_N)
        self.assertEqual(BigO.max_complexity(BigO.O_N, BigO.O_N2), BigO.O_N2)
        self.assertEqual(BigO.max_complexity(BigO.O_N2, BigO.O_2N), BigO.O_2N)

    def test_aggregate_complexities(self):
        items = [BigO.O_1, BigO.O_LOG_N, BigO.O_N2, BigO.O_N]
        self.assertEqual(BigO.aggregate(items), BigO.O_N2)

    def test_estimate_operations(self):
        self.assertEqual(estimate_operations(BigO.O_1, 1000), 1.0)
        self.assertEqual(estimate_operations(BigO.O_N, 1000), 1000.0)
        self.assertEqual(estimate_operations(BigO.O_N2, 1000), 1_000_000.0)

    def test_predict_tle_quadratic_at_large_n(self):
        pred = predict_time_limit_exceeded(BigO.O_N2, 100_000, "python", time_limit_sec=1.0)
        self.assertTrue(pred["will_tle"])
        self.assertGreater(pred["estimated_time_sec"], 1.0)

    def test_predict_pass_linear_at_large_n(self):
        pred = predict_time_limit_exceeded(BigO.O_N, 100_000, "python", time_limit_sec=1.0)
        self.assertFalse(pred["will_tle"])

    def test_recommend_complexity(self):
        self.assertIn("O(N log N)", recommend_complexity(100_000))
        self.assertIn("O(2^N)", recommend_complexity(20))
        self.assertIn("O(N^2)", recommend_complexity(3000))

    def test_cyclomatic_classification(self):
        risk, _ = classify_cyclomatic_complexity(3)
        self.assertEqual(risk, "Low")
        risk, _ = classify_cyclomatic_complexity(15)
        self.assertEqual(risk, "High")


if __name__ == "__main__":
    unittest.main()
