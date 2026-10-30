"""
Gemini API Client for AI Pair-Programmer Edge-Case Explanations.
Uses pure Python standard library (urllib.request) for zero-dependency reliability.
"""

from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
from typing import Dict, Any, Optional
from ..runner.executor import TestResult
from ..ast_analyzer.base import FileAnalysisResult

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def query_gemini_pair_programmer(
    result: TestResult,
    analysis: FileAnalysisResult,
    source_code: str,
    api_key: Optional[str] = None,
    timeout_sec: float = 8.0,
) -> Optional[Dict[str, Any]]:
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return None

    prompt = f"""
You are an expert senior pair-programmer assisting a developer reviewing their daily code submission.
Their code failed on a hidden edge-case test vector.

FILE: {analysis.file_path} (Language: {analysis.language})
STATIC COMPLEXITY: Time {analysis.overall_time_complexity}, Space {analysis.overall_space_complexity}
FAILING TEST VECTOR: '{result.vector_name}' (Category: {result.category})
TEST VECTOR DESCRIPTION: {result.vector_description}
FAILURE STATUS: {result.status.value}
ERROR MESSAGE: {result.error_message}
STACK TRACE:
{result.stack_trace[:800]}

SOURCE CODE:
```{analysis.language}
{source_code[:1800]}
```

CRITICAL INSTRUCTIONS:
1. Act as a patient, brilliant pair-programmer.
2. DO NOT write or fix the solution code for them! Writing the solution defeats learning.
3. Explain the precise ROOT CAUSE at the machine / memory / algorithmic level (e.g. why an empty array triggers SIGSEGV on dereference, why nested loops exceed CPU operations budgets and cause TLE, why INT_MIN overflows when negated).
4. Provide 2-3 Socratic guiding questions to prompt the developer to discover the fix.
5. Provide the invariant or precondition they should maintain.

Reply ONLY with a valid JSON object with these exact keys:
{{
  "title": "<Short concise diagnostic title>",
  "root_cause_explanation": "<Detailed 2-3 sentence explanation of WHY this specific corner case failed>",
  "guiding_questions": ["<Question 1>", "<Question 2>"],
  "invariant_to_maintain": "<Mathematical or programmatic invariant to preserve>",
  "next_step_hint": "<Guiding conceptual hint without writing the code>"
}}
"""

    url = f"{GEMINI_API_URL}?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 800,
            "responseMimeType": "application/json",
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as response:
            resp_body = response.read().decode("utf-8")
            parsed = json.loads(resp_body)
            candidates = parsed.get("candidates", [])
            if candidates:
                text_content = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                result_json = json.loads(text_content.strip())
                return result_json
    except Exception:
        return None

    return None
