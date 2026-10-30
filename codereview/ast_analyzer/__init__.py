"""
AST & Static Code Analysis package for Python, C, and C++.
"""

from .base import (
    Severity,
    RiskIssue,
    FunctionMetrics,
    FileAnalysisResult,
)
from .python_analyzer import analyze_python_source
from .cpp_analyzer import analyze_cpp_source


def analyze_file(file_path: str) -> FileAnalysisResult:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        source_code = f.read()

    lower = file_path.lower()
    if lower.endswith(".py"):
        return analyze_python_source(source_code, file_path=file_path)
    elif lower.endswith((".c", ".h")):
        return analyze_cpp_source(source_code, file_path=file_path)
    elif lower.endswith((".cpp", ".cc", ".cxx", ".hpp", ".hxx")):
        return analyze_cpp_source(source_code, file_path=file_path)
    else:
        return analyze_python_source(source_code, file_path=file_path)


__all__ = [
    "Severity",
    "RiskIssue",
    "FunctionMetrics",
    "FileAnalysisResult",
    "analyze_python_source",
    "analyze_cpp_source",
    "analyze_file",
]
