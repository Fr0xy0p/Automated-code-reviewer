"""
Big-O Intuition and Time/Memory Limit Bounds Checker.
Calculates expected operations count and predicts TLE / MLE based on constraints.
"""

from __future__ import annotations
import math
from typing import Dict, Any, Optional
from .big_o import BigO


OPS_PER_SECOND = {
    "python": 2 * 10**7,   # Python interpreted bytecode loop overhead
    "c": 5 * 10**8,        # Compiled C with optimizations
    "cpp": 5 * 10**8,      # Compiled C++ with optimizations
}

DEFAULT_TIME_LIMIT_SEC = 1.0


def estimate_operations(complexity: str, n: int) -> float:
    """
    Estimates total number of basic operations for input size n given Big-O complexity.
    """
    if complexity == BigO.O_1:
        return 1.0
    elif complexity == BigO.O_LOG_N:
        return math.log2(max(2, n))
    elif complexity == BigO.O_N:
        return float(n)
    elif complexity == BigO.O_N_LOG_N:
        return float(n * math.log2(max(2, n)))
    elif complexity == BigO.O_N2:
        return float(n) ** 2
    elif complexity == BigO.O_N3:
        return float(n) ** 3
    elif complexity == BigO.O_2N:
        return float(2 ** min(n, 60))
    elif complexity == BigO.O_N_BANG:
        return float(math.factorial(min(n, 20)))
    return float(n)


def predict_time_limit_exceeded(
    complexity: str,
    max_expected_n: int,
    language: str = "python",
    time_limit_sec: float = DEFAULT_TIME_LIMIT_SEC,
) -> Dict[str, Any]:
    """
    Evaluates whether the complexity will survive within time_limit_sec for input size max_expected_n.
    """
    lang = language.lower()
    ops_per_sec = OPS_PER_SECOND.get(lang, OPS_PER_SECOND["python"])
    max_allowed_ops = ops_per_sec * time_limit_sec

    ops = estimate_operations(complexity, max_expected_n)
    estimated_time = ops / ops_per_sec
    will_tle = ops > max_allowed_ops

    explanation = (
        f"For N = {max_expected_n:,}, estimated operations for {complexity} are ~{ops:,.0f}. "
        f"Under a {time_limit_sec}s limit ({ops_per_sec:,.0f} ops/sec for {lang}), "
        f"this takes ~{estimated_time:.2f}s."
    )

    recommended_complexity = recommend_complexity(max_expected_n)

    return {
        "complexity": complexity,
        "n": max_expected_n,
        "estimated_operations": ops,
        "estimated_time_sec": estimated_time,
        "will_tle": will_tle,
        "explanation": explanation,
        "recommended_complexity": recommended_complexity,
    }


def recommend_complexity(n: int) -> str:
    """
    Returns the target asymptotic complexity required to finish within ~1.0 second.
    """
    if n <= 11:
        return "O(N!) or O(2^N)"
    elif n <= 25:
        return "O(2^N)"
    elif n <= 500:
        return "O(N^3) or better"
    elif n <= 5000:
        return "O(N^2) or better"
    elif n <= 200_000:
        return "O(N log N) or O(N)"
    elif n <= 10_000_000:
        return "O(N)"
    else:
        return "O(log N) or O(1)"
