"""
Code Metrics computation: Cyclomatic Complexity, Cognitive Complexity,
Halstead Volume, and Maintainability Index.
"""

from __future__ import annotations
import math
from typing import Tuple


def classify_cyclomatic_complexity(cc: int) -> Tuple[str, str]:
    """
    Returns (risk_level, recommendation) based on McCabe cyclomatic complexity.
    """
    if cc <= 5:
        return "Low", "Simple procedure, easily testable, low defect risk."
    elif cc <= 10:
        return "Moderate", "Moderate complexity, reasonably testable. Consider minor refactoring."
    elif cc <= 20:
        return "High", "Complex logic, high risk of edge-case bugs. Split into smaller functions."
    else:
        return "Extreme", "Untestable monolith, very high probability of hidden edge-case bugs."


def calculate_halstead_volume(operators_count: int, operands_count: int, unique_operators: int, unique_operands: int) -> float:
    """
    Computes Halstead program volume: V = N * log2(n)
    where N = N1 + N2 (total operators + operands), n = n1 + n2 (vocabulary size).
    """
    n = unique_operators + unique_operands
    N = operators_count + operands_count
    if n <= 1 or N <= 0:
        return 1.0
    return float(N * math.log2(n))


def calculate_maintainability_index(sloc: int, cyclomatic_complexity: int, halstead_volume: float) -> float:
    """
    Calculates Maintainability Index (MI) normalized to 0-100 scale.
    Standard formula:
    MI = 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(SLOC)
    Normalized: MI_norm = max(0.0, min(100.0, MI * 100.0 / 171.0))
    """
    safe_sloc = max(1, sloc)
    safe_vol = max(1.0, halstead_volume)
    safe_cc = max(1, cyclomatic_complexity)

    raw_mi = (
        171.0
        - 5.2 * math.log(safe_vol)
        - 0.23 * safe_cc
        - 16.2 * math.log(safe_sloc)
    )
    normalized = max(0.0, min(100.0, (raw_mi * 100.0) / 171.0))
    return round(normalized, 2)

