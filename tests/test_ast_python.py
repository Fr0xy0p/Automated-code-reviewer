"""
Unit tests for Python AST Code Analyzer.
"""

import unittest
from codereview.ast_analyzer.python_analyzer import analyze_python_source
from codereview.ast_analyzer.base import Severity
from codereview.complexity.big_o import BigO


class TestPythonASTAnalyzer(unittest.TestCase):

    def test_quadratic_complexity_detection(self):
        code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
"""
        res = analyze_python_source(code, "bubble.py")
        self.assertEqual(len(res.functions), 1)
        fn = res.functions[0]
        self.assertEqual(fn.name, "bubble_sort")
        self.assertEqual(fn.max_loop_depth, 2)
        self.assertEqual(fn.time_complexity, BigO.O_N2)

    def test_branching_recursion_exponential(self):
        code = """
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
"""
        res = analyze_python_source(code, "fib.py")
        fn = res.functions[0]
        self.assertTrue(fn.has_recursion)
        self.assertGreaterEqual(fn.recursion_branching, 2)
        self.assertEqual(fn.time_complexity, BigO.O_2N)

    def test_recursion_without_base_case(self):
        code = """
def infinite(n):
    return infinite(n + 1)
"""
        res = analyze_python_source(code, "infinite.py")
        crit_issues = [i for i in res.all_issues if i.severity == Severity.CRITICAL]
        self.assertTrue(any("base case" in i.message.lower() for i in crit_issues))

    def test_bare_except_detection(self):
        code = """
def risky():
    try:
        val = 1 / 0
    except:
        pass
"""
        res = analyze_python_source(code, "risky.py")
        issues = [i for i in res.all_issues if "bare" in i.message.lower()]
        self.assertTrue(len(issues) > 0)

    def test_mutable_default_argument(self):
        code = """
def append_item(x, lst=[]):
    lst.append(x)
    return lst
"""
        res = analyze_python_source(code, "mutable.py")
        issues = [i for i in res.all_issues if "mutable default" in i.message.lower()]
        self.assertTrue(len(issues) > 0)

    def test_literal_zero_division(self):
        code = """
def div():
    return 100 // 0
"""
        res = analyze_python_source(code, "div.py")
        issues = [i for i in res.all_issues if "zero" in i.message.lower()]
        self.assertTrue(len(issues) > 0)

    def test_maintainability_index(self):
        code = """
def simple(x):
    return x * 2
"""
        res = analyze_python_source(code, "simple.py")
        self.assertGreater(res.maintainability_index, 50.0)


if __name__ == "__main__":
    unittest.main()
