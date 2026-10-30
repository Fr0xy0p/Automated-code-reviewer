"""
Complexity module: Big-O inference, code metrics, and limit checks.
"""

from .big_o import BigO
from .metrics import (
    classify_cyclomatic_complexity,
    calculate_halstead_volume,
    calculate_maintainability_index,
)
from .limits import (
    estimate_operations,
    predict_time_limit_exceeded,
    recommend_complexity,
)

__all__ = [
    "BigO",
    "classify_cyclomatic_complexity",
    "calculate_halstead_volume",
    "calculate_maintainability_index",
    "estimate_operations",
    "predict_time_limit_exceeded",
    "recommend_complexity",
]

