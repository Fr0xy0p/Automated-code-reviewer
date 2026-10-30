"""
JSON serialization reporter for automated pipelines and GitHub Actions.
"""

from __future__ import annotations
import json
from typing import List, Dict, Any
from ..ast_analyzer.base import FileAnalysisResult
from ..runner.executor import TestResult


def generate_json_report(
    analysis: FileAnalysisResult,
    test_results: List[TestResult],
    ai_diagnoses: List[Dict[str, Any]],
) -> str:
    passed = sum(1 for r in test_results if r.is_success)
    total = len(test_results)

    payload = {
        "summary": {
            "file": analysis.file_path,
            "language": analysis.language,
            "all_passed": (passed == total) and total > 0,
            "tests_passed": passed,
            "tests_total": total,
            "maintainability_index": analysis.maintainability_index,
            "overall_time_complexity": analysis.overall_time_complexity,
            "overall_space_complexity": analysis.overall_space_complexity,
        },
        "analysis": analysis.to_dict(),
        "test_results": [r.to_dict() for r in test_results],
        "ai_diagnoses": ai_diagnoses,
    }
    return json.dumps(payload, indent=2)
