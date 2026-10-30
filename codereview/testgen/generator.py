"""
Edge-Case Test Vector Generator.
Generates adversarial inputs to probe hidden bugs, segmentation faults,
off-by-one errors, recursion depth issues, and Time Limit Exceeded (TLE).
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from .types import TestVector


def generate_array_edge_cases(param_name: str = "nums") -> List[TestVector]:
    INT32_MIN = -2147483648
    INT32_MAX = 2147483647

    return [
        TestVector(
            name="Empty Array",
            category="boundary",
            args=[[]],
            stdin="0\n",
            description="Tests behavior on empty input (catches unhandled IndexError / nullptr dereference / division by zero).",
            tags=["empty", "index-error", "segfault"],
        ),
        TestVector(
            name="Single Element (Zero)",
            category="boundary",
            args=[[0]],
            stdin="1\n0\n",
            description="Tests minimal non-empty boundary: single zero element.",
            tags=["single", "boundary"],
        ),
        TestVector(
            name="Single Element (Positive)",
            category="boundary",
            args=[[42]],
            stdin="1\n42\n",
            description="Tests single non-zero positive element.",
            tags=["single"],
        ),
        TestVector(
            name="Two Elements (Sorted)",
            category="boundary",
            args=[[1, 2]],
            stdin="2\n1 2\n",
            description="Minimal pair test case.",
            tags=["minimal-pair"],
        ),
        TestVector(
            name="Two Elements (Reverse Inverted)",
            category="boundary",
            args=[[2, 1]],
            stdin="2\n2 1\n",
            description="Minimal inverted pair; tests swap or comparison logic.",
            tags=["inversion"],
        ),
        TestVector(
            name="All Identical Elements",
            category="duplicates",
            args=[[7, 7, 7, 7, 7, 7]],
            stdin="6\n7 7 7 7 7 7\n",
            description="Tests pivot selection, duplicate counting, and infinite loop conditions.",
            tags=["duplicates", "pivot"],
        ),
        TestVector(
            name="Strictly Ascending (Sorted)",
            category="boundary",
            args=[[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],
            stdin="10\n1 2 3 4 5 6 7 8 9 10\n",
            description="Tests sorted sequence; frequently triggers O(N^2) worst-case in naive QuickSort.",
            tags=["sorted", "quicksort-killer"],
        ),
        TestVector(
            name="Strictly Descending (Reverse Sorted)",
            category="boundary",
            args=[[10, 9, 8, 7, 6, 5, 4, 3, 2, 1]],
            stdin="10\n10 9 8 7 6 5 4 3 2 1\n",
            description="Tests reverse sorted order.",
            tags=["reverse-sorted"],
        ),
        TestVector(
            name="Negative Numbers Only",
            category="adversarial",
            args=[[-50, -20, -5, -2, -1]],
            stdin="5\n-50 -20 -5 -2 -1\n",
            description="Tests algorithms that mistakenly initialize max values to 0 instead of -infinity (e.g., Kadane's).",
            tags=["negative", "initialization"],
        ),
        TestVector(
            name="Extreme 32-Bit Integer Bounds",
            category="bounds",
            args=[[INT32_MIN, -1, 0, 1, INT32_MAX]],
            stdin=f"5\n{INT32_MIN} -1 0 1 {INT32_MAX}\n",
            description="Tests 32-bit signed integer limits: catches integer overflow, sign-flip bugs on INT_MIN.",
            tags=["overflow", "bounds"],
        ),
        TestVector(
            name="Alternating Values (Zig-Zag)",
            category="adversarial",
            args=[[1, -1, 1, -1, 1, -1, 1, -1]],
            stdin="8\n1 -1 1 -1 1 -1 1 -1\n",
            description="Tests alternating signs / monotonic sequence handling.",
            tags=["alternating"],
        ),
        TestVector(
            name="Moderate Scale Stress Test (N = 2,000)",
            category="scale",
            args=[list(range(2000, 0, -1))],
            stdin=f"2000\n{' '.join(str(x) for x in range(2000, 0, -1))}\n",
            description="Tests asymptotic runtime against ~4*10^6 ops. Quadratic O(N^2) algorithms will lag significantly.",
            tags=["scale", "tle-check"],
        ),
    ]


def generate_array_with_target_edge_cases() -> List[TestVector]:
    return [
        TestVector(
            name="Empty Array with Zero Target",
            category="boundary",
            args=[[], 0],
            stdin="0 0\n",
            description="Tests empty array with zero target.",
            tags=["empty"],
        ),
        TestVector(
            name="Single Element Matching Target",
            category="boundary",
            args=[[5], 5],
            stdin="1 5\n5\n",
            description="Single element that equals target.",
            tags=["single", "target"],
        ),
        TestVector(
            name="Single Element Missing Target",
            category="boundary",
            args=[[5], 99],
            stdin="1 99\n5\n",
            description="Single element that does not match target.",
            tags=["single", "missing"],
        ),
        TestVector(
            name="Two Elements Exact Sum Target",
            category="boundary",
            args=[[2, 7], 9],
            stdin="2 9\n2 7\n",
            description="Minimal pair meeting target sum.",
            tags=["minimal-pair"],
        ),
        TestVector(
            name="Duplicate Numbers Target Sum",
            category="duplicates",
            args=[[3, 3], 6],
            stdin="2 6\n3 3\n",
            description="Tests handling of identical elements satisfying target sum (avoids index self-reuse).",
            tags=["duplicates", "self-reuse"],
        ),
        TestVector(
            name="Target Not Found In Array",
            category="boundary",
            args=[[1, 2, 3, 4, 5], 100],
            stdin="5 100\n1 2 3 4 5\n",
            description="Tests correct handling of unsuccessful search / no pair found.",
            tags=["missing"],
        ),
        TestVector(
            name="Negative Numbers with Negative Target",
            category="bounds",
            args=[[-10, -5, -2, -1], -15],
            stdin="4 -15\n-10 -5 -2 -1\n",
            description="Tests negative integer addition and bounds.",
            tags=["negative"],
        ),
        TestVector(
            name="Large Scale Target Search (N = 2,500)",
            category="scale",
            args=[list(range(2500)), 4997],
            stdin=f"2500 4997\n{' '.join(str(x) for x in range(2500))}\n",
            description="Stress tests O(N^2) nested loops searching for target.",
            tags=["scale", "tle"],
        ),
    ]


def generate_string_edge_cases() -> List[TestVector]:
    return [
        TestVector(
            name="Empty String",
            category="boundary",
            args=[""],
            stdin="\n",
            description="Catches out of bounds on s[0] or s[-1].",
            tags=["empty", "index-error"],
        ),
        TestVector(
            name="Single Character",
            category="boundary",
            args=["a"],
            stdin="a\n",
            description="Tests base case for palindromes or string transformations.",
            tags=["single"],
        ),
        TestVector(
            name="All Same Character",
            category="duplicates",
            args=["aaaaaa"],
            stdin="aaaaaa\n",
            description="Tests repeated character compression or substring logic.",
            tags=["duplicates"],
        ),
        TestVector(
            name="Special Characters & Spaces",
            category="adversarial",
            args=["A man, a plan, a canal: Panama!"],
            stdin="A man, a plan, a canal: Panama!\n",
            description="Tests non-alphanumeric filtering and case sensitivity.",
            tags=["punctuation"],
        ),
        TestVector(
            name="Long String Scale Test (N = 5,000)",
            category="scale",
            args=["a" * 2500 + "b" * 2500],
            stdin=("a" * 2500 + "b" * 2500) + "\n",
            description="Tests quadratic string concatenation or nested matching against TLE.",
            tags=["scale", "tle"],
        ),
    ]


def generate_integer_edge_cases() -> List[TestVector]:
    INT32_MAX = 2147483647
    return [
        TestVector(
            name="Zero",
            category="boundary",
            args=[0],
            stdin="0\n",
            description="Standard zero boundary.",
            tags=["zero"],
        ),
        TestVector(
            name="One",
            category="boundary",
            args=[1],
            stdin="1\n",
            description="Minimal positive unit boundary.",
            tags=["one"],
        ),
        TestVector(
            name="Negative One",
            category="boundary",
            args=[-1],
            stdin="-1\n",
            description="Negative boundary for functions expecting natural numbers.",
            tags=["negative"],
        ),
        TestVector(
            name="Small Positive (N = 5)",
            category="boundary",
            args=[5],
            stdin="5\n",
            description="Small typical case.",
            tags=["small"],
        ),
        TestVector(
            name="Scale Test (N = 40)",
            category="scale",
            args=[40],
            stdin="40\n",
            description="Exponential O(2^N) killer test: 2^40 operations takes ~1,000 seconds without DP.",
            tags=["scale", "tle-fibonacci"],
        ),
        TestVector(
            name="Scale Test (N = 1000)",
            category="scale",
            args=[1000],
            stdin="1000\n",
            description="Recursion limit test (default Python recursion limit is 1000).",
            tags=["scale", "recursion-depth"],
        ),
        TestVector(
            name="Extreme INT_MAX",
            category="bounds",
            args=[INT32_MAX],
            stdin=f"{INT32_MAX}\n",
            description="Max 32-bit signed integer boundary.",
            tags=["overflow"],
        ),
    ]


def generate_test_vectors_for_parameters(param_names: List[str]) -> List[TestVector]:
    clean_params = [p.lower() for p in param_names if p not in ("self", "cls")]

    if not clean_params:
        return generate_array_edge_cases()

    if len(clean_params) == 2:
        p0, p1 = clean_params[0], clean_params[1]
        if any(kw in p0 for kw in ("nums", "arr", "list", "vec")) and any(kw in p1 for kw in ("target", "k", "val", "x")):
            return generate_array_with_target_edge_cases()

    if any(kw in clean_params[0] for kw in ("s", "str", "word", "text")):
        return generate_string_edge_cases()

    if any(kw in clean_params[0] for kw in ("n", "num", "val", "x", "k", "target")):
        return generate_integer_edge_cases()

    return generate_array_edge_cases(clean_params[0])
