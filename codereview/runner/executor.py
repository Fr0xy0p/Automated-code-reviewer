"""
Execution sandbox and process isolation models.
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Dict, Any
from ..testgen.types import TestVector


class ExecutionStatus(str, Enum):
    PASS = "PASS"
    TLE = "TLE"                         # Time Limit Exceeded
    SIGSEGV = "SIGSEGV"                 # Segmentation Fault
    SIGFPE = "SIGFPE"                   # Floating Point Exception / Zero Division
    ASAN_ERROR = "ASAN_ERROR"           # AddressSanitizer Memory Violation
    RECURSION_ERROR = "RECURSION_ERROR" # Python maximum recursion depth exceeded
    INDEX_ERROR = "INDEX_ERROR"         # Out of bounds array indexing
    ZERO_DIVISION = "ZERO_DIVISION"     # Python ZeroDivisionError
    RUNTIME_ERROR = "RUNTIME_ERROR"     # General runtime crash / non-zero exit
    COMPILE_ERROR = "COMPILE_ERROR"     # Compilation failure in C/C++


@dataclass
class TestResult:
    vector_name: str
    category: str
    status: ExecutionStatus
    execution_time_sec: float
    output: str = ""
    error_message: str = ""
    stack_trace: str = ""
    vector_description: str = ""

    @property
    def is_success(self) -> bool:
        return self.status == ExecutionStatus.PASS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "vector_name": self.vector_name,
            "category": self.category,
            "status": self.status.value,
            "execution_time_sec": round(self.execution_time_sec, 4),
            "output": self.output,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "vector_description": self.vector_description,
        }
