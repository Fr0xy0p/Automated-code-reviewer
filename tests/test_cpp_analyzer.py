"""
Unit tests for C & C++ Static Analyzer.
"""

import unittest
from codereview.ast_analyzer.cpp_analyzer import analyze_cpp_source, strip_c_comments
from codereview.complexity.big_o import BigO


class TestCppAnalyzer(unittest.TestCase):

    def test_strip_c_comments(self):
        c_code = """
        // Single line comment
        int x = 10; /* inline block comment */
        /* Multi-line
           block comment */
        int y = 20;
        """
        clean, comment_lines, blank_lines = strip_c_comments(c_code)
        self.assertNotIn("Single line comment", clean)
        self.assertNotIn("Multi-line", clean)
        self.assertIn("int x = 10;", clean)
        self.assertIn("int y = 20;", clean)
        self.assertGreater(comment_lines, 0)

    def test_unsafe_function_detection(self):
        c_code = """
        #include <stdio.h>
        #include <string.h>

        void read_name() {
            char buf[64];
            gets(buf);
            strcpy(buf, "hello");
        }
        """
        res = analyze_cpp_source(c_code, "test.c")
        issues = [i for i in res.all_issues if "unsafe" in i.message.lower()]
        self.assertTrue(any("gets" in i.message for i in issues))
        self.assertTrue(any("strcpy" in i.message for i in issues))

    def test_loop_nesting_and_big_o(self):
        cpp_code = """
        #include <vector>

        void matrix_mult(int n) {
            for (int i = 0; i < n; i++) {
                for (int j = 0; j < n; j++) {
                    int val = i * j;
                }
            }
        }
        """
        res = analyze_cpp_source(cpp_code, "matrix.cpp")
        self.assertEqual(len(res.functions), 1)
        fn = res.functions[0]
        self.assertEqual(fn.name, "matrix_mult")
        self.assertEqual(fn.max_loop_depth, 2)
        self.assertEqual(fn.time_complexity, BigO.O_N2)

    def test_recursion_detection(self):
        cpp_code = """
        long long fib(int n) {
            if (n <= 1) return n;
            return fib(n - 1) + fib(n - 2);
        }
        """
        res = analyze_cpp_source(cpp_code, "fib.cpp")
        self.assertEqual(len(res.functions), 1)
        fn = res.functions[0]
        self.assertTrue(fn.has_recursion)
        self.assertEqual(fn.time_complexity, BigO.O_2N)


if __name__ == "__main__":
    unittest.main()
