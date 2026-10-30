"""
Base data models and abstractions for AST and code analysis.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class RiskIssue:
    """Represents a potential bug, anti-pattern, or edge-case vulnerability."""
    category: str  # e.g., "Edge-Case", "Recursion", "Memory", "Complexity", "Safety"
    message: str
    line_number: int
    column: int = 0
    severity: Severity = Severity.WARNING
    suggestion: str = ""
    code_snippet: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class FunctionMetrics:
    """Metrics calculated for an individual function or method."""
    name: str
    start_line: int
    end_line: int
    sloc: int
    cyclomatic_complexity: int
    cognitive_complexity: int
    max_loop_depth: int
    has_recursion: bool
    recursion_branching: int = 0  # Number of recursive call sites in the body (e.g., 2 -> O(2^N))
    time_complexity: str = "O(1)"
    space_complexity: str = "O(1)"
    parameters: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    issues: List[RiskIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "sloc": self.sloc,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "cognitive_complexity": self.cognitive_complexity,
            "max_loop_depth": self.max_loop_depth,
            "has_recursion": self.has_recursion,
            "recursion_branching": self.recursion_branching,
            "time_complexity": self.time_complexity,
            "space_complexity": self.space_complexity,
            "parameters": self.parameters,
            "docstring": self.docstring,
            "issues": [issue.to_dict() for issue in self.issues],
        }


@dataclass
class FileAnalysisResult:
    """Consolidated static analysis result for a source file."""
    file_path: str
    language: str  # "python", "c", "cpp"
    total_loc: int
    sloc: int
    comment_lines: int
    blank_lines: int
    maintainability_index: float
    overall_time_complexity: str
    overall_space_complexity: str
    functions: List[FunctionMetrics] = field(default_factory=list)
    global_issues: List[RiskIssue] = field(default_factory=list)

    @property
    def all_issues(self) -> List[RiskIssue]:
        issues = list(self.global_issues)
        for fn in self.functions:
            issues.extend(fn.issues)
        return issues

    @property
    def max_cyclomatic_complexity(self) -> int:
        if not self.functions:
            return 1
        return max(fn.cyclomatic_complexity for fn in self.functions)

    @property
    def max_loop_depth(self) -> int:
        if not self.functions:
            return 0
        return max(fn.max_loop_depth for fn in self.functions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "language": self.language,
            "total_loc": self.total_loc,
            "sloc": self.sloc,
            "comment_lines": self.comment_lines,
            "blank_lines": self.blank_lines,
            "maintainability_index": round(self.maintainability_index, 2),
            "max_cyclomatic_complexity": self.max_cyclomatic_complexity,
            "max_loop_depth": self.max_loop_depth,
            "overall_time_complexity": self.overall_time_complexity,
            "overall_space_complexity": self.overall_space_complexity,
            "functions": [fn.to_dict() for fn in self.functions],
            "global_issues": [issue.to_dict() for issue in self.global_issues],
            "all_issues": [issue.to_dict() for issue in self.all_issues],
        }
