"""
Unit tests for AI Pair-Programmer Explainer.
"""

import unittest
from codereview.runner.executor import TestResult, ExecutionStatus
from codereview.ast_analyzer.base import FileAnalysisResult
from codereview.ai.explainer import get_pair_programmer_explanation


class TestAIPairProgrammer(unittest.TestCase):

    def setUp(self):
        self.dummy_analysis = FileAnalysisResult(
            file_path="solution.cpp",
            language="cpp",
            total_loc=20,
            sloc=15,
            comment_lines=2,
            blank_lines=3,
            maintainability_index=75.0,
            overall_time_complexity="O(N^2)",
            overall_space_complexity="O(1)",
        )

    def test_segfault_pair_programming_advice(self):
        res = TestResult(
            vector_name="Empty Array",
            category="boundary",
            status=ExecutionStatus.SIGSEGV,
            execution_time_sec=0.01,
            error_message="Process terminated with signal 11 (SIGSEGV)",
        )
        diag = get_pair_programmer_explanation(
            result=res,
            analysis=self.dummy_analysis,
            source_code="int main() { ... }",
            use_ai=False,
        )
        self.assertIn("SIGSEGV", diag["title"])
        self.assertIn("root_cause_explanation", diag)
        self.assertGreater(len(diag["guiding_questions"]), 0)
        self.assertIn("invariant_to_maintain", diag)
        self.assertIn("next_step_hint", diag)

        self.assertTrue(
            "memory" in diag["root_cause_explanation"].lower() or "page fault" in diag["root_cause_explanation"].lower()
        )

    def test_tle_pair_programming_advice(self):
        res = TestResult(
            vector_name="Large Scale N=50,000",
            category="scale",
            status=ExecutionStatus.TLE,
            execution_time_sec=1.05,
            error_message="Time Limit Exceeded",
        )
        diag = get_pair_programmer_explanation(
            result=res,
            analysis=self.dummy_analysis,
            source_code="for(int i=0;i<n;i++) for(int j=0;j<n;j++) ...",
            use_ai=False,
        )
        self.assertIn("Time Limit Exceeded", diag["title"])
        self.assertTrue(
            "operations" in diag["root_cause_explanation"].lower() or "asymptotic" in diag["root_cause_explanation"].lower()
        )
        self.assertIn("O(1)", str(diag["guiding_questions"]))


if __name__ == "__main__":
    unittest.main()

