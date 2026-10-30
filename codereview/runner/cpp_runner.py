"""
C & C++ Sandbox Test Runner and Compiler.
Compiles code with AddressSanitizer (ASan) and UndefinedBehaviorSanitizer (UBSan),
detecting Segmentation Faults (SIGSEGV), Division by Zero (SIGFPE/UBSan), and TLE.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
import time
from typing import List, Optional, Tuple
from .executor import TestResult, ExecutionStatus
from ..testgen.types import TestVector


def find_compiler(language: str) -> Optional[str]:
    if language == "cpp":
        for comp in ("clang++", "g++", "c++"):
            if shutil.which(comp):
                return comp
    else:
        for comp in ("clang", "gcc", "cc"):
            if shutil.which(comp):
                return comp
    return None


def compile_source(source_path: str, language: str) -> Tuple[Optional[str], Optional[str]]:
    compiler = find_compiler(language)
    if not compiler:
        return None, f"No C/C++ compiler found on system (searched clang, gcc, cc)."

    bin_file = tempfile.NamedTemporaryFile(delete=False, suffix=".out")
    bin_path = bin_file.name
    bin_file.close()

    cmd_asan = [
        compiler,
        "-O1",
        "-g",
        "-fsanitize=address,undefined",
        "-fno-omit-frame-pointer",
        source_path,
        "-o",
        bin_path,
    ]
    if language == "cpp":
        cmd_asan.insert(1, "-std=c++17")

    res = subprocess.run(cmd_asan, capture_output=True, text=True)
    if res.returncode == 0:
        return bin_path, None

    cmd_standard = [
        compiler,
        "-O2",
        "-g",
        source_path,
        "-o",
        bin_path,
    ]
    if language == "cpp":
        cmd_standard.insert(1, "-std=c++17")

    res2 = subprocess.run(cmd_standard, capture_output=True, text=True)
    if res2.returncode == 0:
        return bin_path, None

    if os.path.exists(bin_path):
        os.remove(bin_path)
    return None, res2.stderr or res.stderr


def run_cpp_test(
    binary_path: str,
    vector: TestVector,
    timeout_sec: float = 2.0,
) -> TestResult:
    stdin_data = vector.stdin or ""
    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            [binary_path],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        elapsed = time.perf_counter() - start_time
        ret = proc.returncode
        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        # Check for UBSan division by zero (especially on ARM64/Apple Silicon where CPU doesn't trap)
        if "division by zero" in stderr.lower():
            return TestResult(
                vector_name=vector.name,
                category=vector.category,
                status=ExecutionStatus.SIGFPE,
                execution_time_sec=elapsed,
                output=stdout[:200],
                error_message="UndefinedBehaviorSanitizer: division by zero detected.",
                stack_trace=stderr[:600],
                vector_description=vector.description,
            )

        # Check for AddressSanitizer crash
        if any(asan_tag in stderr for asan_tag in ("AddressSanitizer", "heap-buffer-overflow", "stack-buffer-overflow", "global-buffer-overflow", "null-pointer-dereference")):
            return TestResult(
                vector_name=vector.name,
                category=vector.category,
                status=ExecutionStatus.ASAN_ERROR,
                execution_time_sec=elapsed,
                output=stdout[:200],
                error_message="AddressSanitizer detected memory access violation (buffer overflow / nullptr dereference).",
                stack_trace=stderr[:600],
                vector_description=vector.description,
            )

        # Signal checks (on POSIX, negative returncode or code > 128 indicates signal)
        if ret in (-11, 139):
            return TestResult(
                vector_name=vector.name,
                category=vector.category,
                status=ExecutionStatus.SIGSEGV,
                execution_time_sec=elapsed,
                output=stdout[:200],
                error_message="Segmentation Fault (SIGSEGV): Invalid memory dereference or stack overflow.",
                stack_trace=stderr,
                vector_description=vector.description,
            )
        elif ret in (-8, 136):
            return TestResult(
                vector_name=vector.name,
                category=vector.category,
                status=ExecutionStatus.SIGFPE,
                execution_time_sec=elapsed,
                output=stdout[:200],
                error_message="Floating Point Exception (SIGFPE): Arithmetic error (division or modulo by zero).",
                stack_trace=stderr,
                vector_description=vector.description,
            )
        elif ret != 0:
            return TestResult(
                vector_name=vector.name,
                category=vector.category,
                status=ExecutionStatus.RUNTIME_ERROR,
                execution_time_sec=elapsed,
                output=stdout[:200],
                error_message=f"Process crashed with exit code {ret}: {stderr[:200]}",
                stack_trace=stderr,
                vector_description=vector.description,
            )

        return TestResult(
            vector_name=vector.name,
            category=vector.category,
            status=ExecutionStatus.PASS,
            execution_time_sec=elapsed,
            output=stdout[:200],
            vector_description=vector.description,
        )

    except subprocess.TimeoutExpired:
        return TestResult(
            vector_name=vector.name,
            category=vector.category,
            status=ExecutionStatus.TLE,
            execution_time_sec=timeout_sec,
            error_message=f"Time Limit Exceeded (TLE): Exceeded {timeout_sec:.2f}s time limit.",
            vector_description=vector.description,
        )


def run_cpp_suite(
    source_path: str,
    vectors: List[TestVector],
    language: str = "cpp",
    timeout_sec: float = 2.0,
) -> Tuple[List[TestResult], Optional[str]]:
    binary_path, compile_error = compile_source(source_path, language)
    if compile_error:
        results = [
            TestResult(
                vector_name=vec.name,
                category=vec.category,
                status=ExecutionStatus.COMPILE_ERROR,
                execution_time_sec=0.0,
                error_message=compile_error,
                vector_description=vec.description,
            )
            for vec in vectors
        ]
        return results, compile_error

    results = []
    try:
        for vec in vectors:
            res = run_cpp_test(binary_path, vec, timeout_sec=timeout_sec)
            results.append(res)
    finally:
        if binary_path and os.path.exists(binary_path):
            try:
                os.remove(binary_path)
            except OSError:
                pass

    return results, None
