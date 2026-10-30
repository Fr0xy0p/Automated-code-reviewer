"""
AI Pair-Programmer explanation package.
"""

from .explainer import get_pair_programmer_explanation
from .heuristic_rules import explain_failure_offline
from .gemini_client import query_gemini_pair_programmer

__all__ = [
    "get_pair_programmer_explanation",
    "explain_failure_offline",
    "query_gemini_pair_programmer",
]
