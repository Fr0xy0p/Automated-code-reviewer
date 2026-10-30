"""
Unit tests for Edge-Case Test Vector Generator.
"""

import unittest
from codereview.testgen.generator import (
    generate_array_edge_cases,
    generate_array_with_target_edge_cases,
    generate_string_edge_cases,
    generate_integer_edge_cases,
    generate_test_vectors_for_parameters,
)


class TestTestGen(unittest.TestCase):

    def test_array_edge_cases_contain_critical_vectors(self):
        vectors = generate_array_edge_cases()
        names = [v.name for v in vectors]

        self.assertIn("Empty Array", names)
        self.assertIn("Single Element (Zero)", names)
        self.assertIn("All Identical Elements", names)
        self.assertIn("Extreme 32-Bit Integer Bounds", names)
        self.assertIn("Moderate Scale Stress Test (N = 2,000)", names)

    def test_array_with_target_generator(self):
        vectors = generate_array_with_target_edge_cases()
        names = [v.name for v in vectors]
        self.assertIn("Empty Array with Zero Target", names)
        self.assertIn("Duplicate Numbers Target Sum", names)
        for v in vectors:
            self.assertEqual(len(v.args), 2)

    def test_string_edge_cases(self):
        vectors = generate_string_edge_cases()
        names = [v.name for v in vectors]
        self.assertIn("Empty String", names)
        self.assertIn("Single Character", names)
        self.assertIn("All Same Character", names)

    def test_integer_edge_cases(self):
        vectors = generate_integer_edge_cases()
        names = [v.name for v in vectors]
        self.assertIn("Zero", names)
        self.assertIn("Negative One", names)
        self.assertIn("Extreme INT_MAX", names)

    def test_parameter_inference(self):
        vecs_two = generate_test_vectors_for_parameters(["nums", "target"])
        self.assertEqual(len(vecs_two[0].args), 2)

        vecs_str = generate_test_vectors_for_parameters(["s"])
        self.assertIsInstance(vecs_str[0].args[0], str)

        vecs_int = generate_test_vectors_for_parameters(["n"])
        self.assertIsInstance(vecs_int[0].args[0], int)


if __name__ == "__main__":
    unittest.main()

