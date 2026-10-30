"""
Unified AI Pair-Programmer Explainer.
Coordinates Gemini API calls with offline heuristic fallback.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from ..runner.executor import TestResult, ExecutionStatus
from ..ast_analyzer.base import FileAnalysisResult
from .heuristic_rules import explain_failure_offline
from .gemini_client import query_gemini_pair_programmer


def get_pair_programmer_explanation(
    result: TestResult,
    analysis: FileAnalysisResult,
    source_code: str,
    api_key: Optional[str] = None,
    use_ai: bool = True,
) -> Dict[str, Any]:
    if result.status == ExecutionStatus.PASS:
        return {
            "title": "Passed",
            "root_cause_explanation": "All assertions and edge cases satisfied within limits.",
            "guiding_questions": [],
            "invariant_to_maintain": "Continue verifying edge cases.",
            "next_step_hint": "Good job!",
        }

    if use_ai:
        gemini_explanation = query_gemini_pair_programmer(
            result=result,
            analysis=analysis,
            source_code=source_code,
            api_key=api_key,
        )
        if gemini_explanation and "root_cause_explanation" in gemini_explanation:
            gemini_explanation["engine"] = "Gemini AI"
            return gemini_explanation

    offline_diag = explain_failure_offline(result, analysis, source_code)
    offline_diag["engine"] = "Offline Expert Heuristic Engine"
    return offline_diag
