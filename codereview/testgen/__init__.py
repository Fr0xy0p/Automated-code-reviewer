"""
Edge-case test vector generation module.
"""

from .types import TestVector
from .generator import (
    generate_array_edge_cases,
    generate_array_with_target_edge_cases,
    generate_string_edge_cases,
    generate_integer_edge_cases,
    generate_test_vectors_for_parameters,
)

__all__ = [
    "TestVector",
    "generate_array_edge_cases",
    "generate_array_with_target_edge_cases",
    "generate_string_edge_cases",
    "generate_integer_edge_cases",
    "generate_test_vectors_for_parameters",
]
