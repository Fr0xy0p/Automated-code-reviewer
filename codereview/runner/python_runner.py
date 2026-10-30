"""
Python Sandbox Test Runner.
Executes code against edge-case test vectors in an isolated subprocess,
detecting TLEs, RecursionErrors, IndexErrors, and memory issues.
"""

from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import time
from typing import List, Optional, Any
from .executor import TestResult, ExecutionStatus
from ..testgen.types import TestVector


HARNESS_TEMPLATE = """# Auto-generated isolated test harness
import sys
import json
import time
import traceback
import importlib.util

def run():
    file_path = {file_path!r}
    fn_name = {fn_name!r}
    args = {args!r}

    try:
        spec = importlib.util.spec_from_file_location("user_module", file_path)
        if spec is None or spec.loader is None:
            print(json.dumps({{
                "status": "RUNTIME_ERROR",
                "time": 0.0,
                "error": "Failed to load spec for file",
                "trace": ""
            }}))
            return
        mod = importlib.util.module_from_spec(spec)
        sys.modules["user_module"] = mod
        spec.loader.exec_module(mod)
    except Exception as e:
        print(json.dumps({{
            "status": "RUNTIME_ERROR",
            "time": 0.0,
            "error": f"Import/Syntax error: {{type(e).__name__}}: {{str(e)}}",
            "trace": traceback.format_exc()
        }}))
        return

    target_callable = None
    if fn_name and hasattr(mod, fn_name):
        target_callable = getattr(mod, fn_name)
    elif hasattr(mod, "Solution"):
        sol = getattr(mod, "Solution")()
        methods = [m for m in dir(sol) if not m.startswith("_") and callable(getattr(sol, m))]
        if methods:
            target_callable = getattr(sol, methods[0])
    else:
        for attr in dir(mod):
            val = getattr(mod, attr)
            if callable(val) and not attr.startswith("_") and getattr(val, "__module__", None) == "user_module":
                target_callable = val
                break

    if target_callable is None:
        print(json.dumps({{
            "status": "RUNTIME_ERROR",
            "time": 0.0,
            "error": "No callable function found to test in module.",
            "trace": ""
        }}))
        return

    start = time.perf_counter()
    try:
        result = target_callable(*args)
        elapsed = time.perf_counter() - start
        print(json.dumps({{
            "status": "PASS",
            "time": elapsed,
            "output": repr(result)[:200],
            "error": "",
            "trace": ""
        }}))
    except RecursionError as e:
        elapsed = time.perf_counter() - start
        print(json.dumps({{
            "status": "RECURSION_ERROR",
            "time": elapsed,
            "error": f"RecursionError: {{str(e)}}",
            "trace": traceback.format_exc()
        }}))
    except IndexError as e:
        elapsed = time.perf_counter() - start
        print(json.dumps({{
            "status": "INDEX_ERROR",
            "time": elapsed,
            "error": f"IndexError: {{str(e)}}",
            "trace": traceback.format_exc()
        }}))
    except ZeroDivisionError as e:
        elapsed = time.perf_counter() - start
        print(json.dumps({{
            "status": "ZERO_DIVISION",
            "time": elapsed,
            "error": f"ZeroDivisionError: {{str(e)}}",
            "trace": traceback.format_exc()
        }}))
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(json.dumps({{
            "status": "RUNTIME_ERROR",
            "time": elapsed,
            "error": f"{{type(e).__name__}}: {{str(e)}}",
            "trace": traceback.format_exc()
        }}))

if __name__ == "__main__":
    run()
"""


def run_python_test(
    file_path: str,
    vector: TestVector,
    function_name: Optional[str] = None,
    timeout_sec: float = 1.0,
) -> TestResult:
    abs_path = os.path.abspath(file_path)
    harness_code = HARNESS_TEMPLATE.format(
        file_path=abs_path,
        fn_name=function_name or "",
        args=vector.args,
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        harness_path = f.name
        f.write(harness_code)

    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, harness_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        elapsed = time.perf_counter() - start_time

        stdout = proc.stdout.strip()
        stderr = proc.stderr.strip()

        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    status_str = data.get("status", "RUNTIME_ERROR")
                    status = ExecutionStatus(status_str)
                    return TestResult(
                        vector_name=vector.name,
                        category=vector.category,
                        status=status,
                        execution_time_sec=data.get("time", elapsed),
                        output=data.get("output", ""),
                        error_message=data.get("error", ""),
                        stack_trace=data.get("trace", ""),
                        vector_description=vector.description,
                    )
                except (json.JSONDecodeError, ValueError):
                    pass

        if proc.returncode != 0:
            return TestResult(
                vector_name=vector.name,
                category=vector.category,
                status=ExecutionStatus.RUNTIME_ERROR,
                execution_time_sec=elapsed,
                output="",
                error_message=stderr or f"Process exited with code {proc.returncode}",
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
            error_message=f"Time Limit Exceeded: Process exceeded {timeout_sec:.2f}s timeout.",
            vector_description=vector.description,
        )
    finally:
        if os.path.exists(harness_path):
            try:
                os.remove(harness_path)
            except OSError:
                pass


def run_python_suite(
    file_path: str,
    vectors: List[TestVector],
    function_name: Optional[str] = None,
    timeout_sec: float = 1.0,
) -> List[TestResult]:
    results: List[TestResult] = []
    for vec in vectors:
        res = run_python_test(
            file_path=file_path,
            vector=vec,
            function_name=function_name,
            timeout_sec=timeout_sec,
        )
        results.append(res)
    return results

