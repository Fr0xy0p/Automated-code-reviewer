"""
Unit tests for CLI commands and report generation.
"""

import os
import json
import tempfile
import unittest
from codereview.cli import review_file, profile_file, test_gen_cmd


class TestCLI(unittest.TestCase):

    def test_review_clean_solution_succeeds(self):
        file_path = "examples/python/clean_solution.py"
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f_md:
            md_path = f_md.name
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f_json:
            json_path = f_json.name

        try:
            exit_code = review_file(
                file_path=file_path,
                strict=True,
                output_markdown=md_path,
                output_json=json_path,
                quiet=True,
            )
            self.assertEqual(exit_code, 0)

            self.assertTrue(os.path.exists(md_path))
            with open(md_path, "r", encoding="utf-8") as f:
                md_text = f.read()
            self.assertIn("Automated Code Review & Complexity Profiler", md_text)
            self.assertIn("Edge-Case Test Vector Matrix", md_text)

            self.assertTrue(os.path.exists(json_path))
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertTrue(data["summary"]["all_passed"])
            self.assertEqual(data["summary"]["language"], "python")

        finally:
            if os.path.exists(md_path):
                os.remove(md_path)
            if os.path.exists(json_path):
                os.remove(json_path)

    def test_review_buggy_solution_fails_strict(self):
        file_path = "examples/python/binary_search_buggy.py"
        exit_code = review_file(
            file_path=file_path,
            strict=True,
            timeout_sec=0.4,
            quiet=True,
        )
        self.assertEqual(exit_code, 1)

    def test_profile_command(self):
        exit_code = profile_file("examples/python/two_sum_quadratic.py", max_n=10_000)
        self.assertEqual(exit_code, 0)

    def test_test_gen_command(self):
        exit_code = test_gen_cmd("examples/python/clean_solution.py")
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()

