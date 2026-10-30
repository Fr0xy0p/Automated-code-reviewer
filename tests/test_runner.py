"""
Unit tests for Sandboxed Execution Runners (Python, C, and C++).
"""

import os
import unittest
from codereview.runner.executor import ExecutionStatus
from codereview.runner.python_runner import run_python_suite, run_python_test
from codereview.runner.cpp_runner import run_cpp_suite
from codereview.testgen.generator import (
    generate_array_edge_cases,
    generate_array_with_target_edge_cases,
)
from codereview.testgen.types import TestVector


class TestRunners(unittest.TestCase):

    def test_python_clean_solution_passes(self):
        file_path = os.path.abspath("examples/python/clean_solution.py")
        vectors = generate_array_with_target_edge_cases()
        results = run_python_suite(file_path, vectors)
        for r in results:
            self.assertEqual(r.status, ExecutionStatus.PASS, f"Failed on {r.vector_name}: {r.error_message}")

    def test_python_infinite_loop_triggers_tle(self):
        file_path = os.path.abspath("examples/python/binary_search_buggy.py")
        vector = TestVector(
            name="Infinite Loop Trigger",
            category="boundary",
            args=[[1, 3], 2],
            description="Causes infinite loop",
        )
        res = run_python_test(file_path, vector, timeout_sec=0.4)
        self.assertEqual(res.status, ExecutionStatus.TLE)

    def test_c_clean_passes(self):
        file_path = os.path.abspath("examples/c/clean_c.c")
        vectors = [
            TestVector(
                name="Normal Input",
                category="boundary",
                args=[],
                stdin="3\n10 20 30\n",
                description="Valid array",
            ),
            TestVector(
                name="Empty Input",
                category="boundary",
                args=[],
                stdin="0\n",
                description="Empty array (size 0)",
            ),
        ]
        results, err = run_cpp_suite(file_path, vectors, language="c", timeout_sec=2.0)
        self.assertIsNone(err)
        for r in results:
            self.assertEqual(r.status, ExecutionStatus.PASS)

    def test_c_divide_by_zero_sigfpe(self):
        file_path = os.path.abspath("examples/c/divide_by_zero.c")
        vector = TestVector(
            name="Zero Array Trigger",
            category="boundary",
            args=[],
            stdin="0\n",
            description="Empty array size 0",
        )
        results, err = run_cpp_suite(file_path, [vector], language="c", timeout_sec=2.0)
        self.assertIsNone(err)
        self.assertEqual(results[0].status, ExecutionStatus.SIGFPE)

    def test_cpp_empty_vector_segfault(self):
        file_path = os.path.abspath("examples/cpp/segfault_null_deref.cpp")
        vector = TestVector(
            name="Empty Vector Segfault Trigger",
            category="boundary",
            args=[],
            stdin="0\n",
            description="Zero elements",
        )
        results, err = run_cpp_suite(file_path, [vector], language="cpp", timeout_sec=2.0)
        self.assertIsNone(err)
        self.assertIn(results[0].status, (ExecutionStatus.SIGSEGV, ExecutionStatus.ASAN_ERROR, ExecutionStatus.RUNTIME_ERROR))


if __name__ == "__main__":
    unittest.main()
