"""
Heuristic Rule-Based Pair-Programmer Diagnostic Engine.
Generates comprehensive educational explanations of edge-case bugs,
hardware-level memory faults (SIGSEGV), and asymptotic bottlenecks (TLE)
without requiring an external API key or network connection.
"""

from __future__ import annotations
from typing import Dict, Any, List
from ..runner.executor import TestResult, ExecutionStatus
from ..ast_analyzer.base import FileAnalysisResult


def explain_failure_offline(
    result: TestResult,
    analysis: FileAnalysisResult,
    source_code: str,
) -> Dict[str, Any]:
    status = result.status
    vec_name = result.vector_name
    msg = result.error_message

    if status == ExecutionStatus.SIGSEGV:
        return {
            "title": "Segmentation Fault (SIGSEGV / Signal 11)",
            "root_cause_explanation": (
                f"When executing test vector '{vec_name}', the program attempted to access an invalid memory address. "
                "In C/C++, accessing an element of an empty container (e.g. vec[0]) or dereferencing a NULL / dangling "
                "pointer causes the CPU's Memory Management Unit (MMU) to trigger a hardware page fault. "
                "Because the process has no mapped virtual page at that address, the operating system kernel immediately "
                "terminates your program with SIGSEGV."
            ),
            "guiding_questions": [
                "Did you verify that the container / array has at least one element before indexing element 0?",
                "Are your loop termination conditions using strictly '< length' rather than '<= length'?",
                "If dynamically allocating memory, did you verify that malloc() returned a non-NULL pointer?",
            ],
            "invariant_to_maintain": "Array Access Invariant: 0 <= index < size() must hold strictly for every memory access.",
            "next_step_hint": "Add a guard clause at the very top of your function: if (size == 0) return ...; before reading memory.",
        }

    elif status == ExecutionStatus.TLE:
        overall_time = analysis.overall_time_complexity
        return {
            "title": "Time Limit Exceeded (TLE)",
            "root_cause_explanation": (
                f"Your code timed out ({result.execution_time_sec:.2f}s) on '{vec_name}'. "
                f"Static analysis detected an overall asymptotic time complexity of {overall_time}. "
                "Standard execution environments permit approximately 10^7 (Python) to 10^8 (C/C++) operations per second. "
                "When your algorithm encounters scaled or adversarial inputs, the operation count explodes asymptotically, "
                "preventing the process from completing before the execution timer expires."
            ),
            "guiding_questions": [
                "Notice the nested loop in your code: does the inner loop scan over elements you could have precomputed?",
                "Can you replace the inner O(N) search with an O(1) hash table lookup (dict / std::unordered_map)?",
                "If using recursion, are you re-calculating the exact same sub-problems repeatedly without memoization?",
            ],
            "invariant_to_maintain": "Asymptotic Budget: Total operations across all inputs must stay below ~10^7 per second.",
            "next_step_hint": "Try trading space for time: create a lookup map to find complement values in a single pass.",
        }

    elif status == ExecutionStatus.ASAN_ERROR:
        return {
            "title": "AddressSanitizer Memory Violation",
            "root_cause_explanation": (
                f"AddressSanitizer intercepted an out-of-bounds memory read or write while evaluating '{vec_name}'. "
                "This indicates that an array index exceeded the allocated buffer bounds, or accessed memory that "
                "has already been freed (use-after-free). In non-sanitized builds, this causes silent heap corruption "
                "or unpredictable data races."
            ),
            "guiding_questions": [
                "What is the maximum index your loop reaches? Does it reach 'size' on 0-indexed buffers?",
                "If manipulating C-strings, did you leave space for the null terminator ('\\0') at the end of the buffer?",
            ],
            "invariant_to_maintain": "Buffer Safety Invariant: Buffer write offset must satisfy: 0 <= offset < buffer_capacity.",
            "next_step_hint": "Inspect the AddressSanitizer report stack trace to find the exact line performing the out-of-bounds access.",
        }

    elif status == ExecutionStatus.RECURSION_ERROR:
        return {
            "title": "Recursion Limit Exceeded (Stack Overflow)",
            "root_cause_explanation": (
                f"Test vector '{vec_name}' triggered a Python RecursionError. "
                "Python limits call stack depth (sys.getrecursionlimit() is typically 1,000 frames) to protect against "
                "host stack overflow. When recursion does not rapidly converge to a base case, or when the recursion tree "
                "depth equals N (linear recursion on large N), the call stack fills completely and Python halts execution."
            ),
            "guiding_questions": [
                "What is your base case condition? Under what exact inputs does recursion stop?",
                "Does your recursive step strictly reduce the problem size towards the base condition?",
                "Can this recursive algorithm be rewritten iteratively using a while-loop or an explicit stack?",
            ],
            "invariant_to_maintain": "Convergence Invariant: Each recursive invocation must strictly advance closer to a base case.",
            "next_step_hint": "Convert the recursion to an iterative loop with an accumulator, or use memoization / DP.",
        }

    elif status == ExecutionStatus.INDEX_ERROR:
        return {
            "title": "Index Out of Bounds (IndexError)",
            "root_cause_explanation": (
                f"Test vector '{vec_name}' crashed with IndexError: list index out of range. "
                "This commonly occurs when code assumes an array is non-empty, accesses 'arr[0]' or 'arr[-1]', "
                "or uses a loop condition like 'range(len(arr) + 1)'."
            ),
            "guiding_questions": [
                "What happens when the input array is completely empty: []?",
                "Are you accessing arr[i + 1] inside a loop without stopping the loop at len(arr) - 1?",
            ],
            "invariant_to_maintain": "Index Validity: If len(arr) == 0, no element access arr[i] may occur.",
            "next_step_hint": "Check 'if not arr: return ...' at the start of your function.",
        }

    elif status == ExecutionStatus.ZERO_DIVISION or status == ExecutionStatus.SIGFPE:
        return {
            "title": "Division / Modulo by Zero",
            "root_cause_explanation": (
                f"Test vector '{vec_name}' attempted arithmetic division or modulo by 0. "
                "At the CPU hardware level, integer division by zero generates an arithmetic trap (SIGFPE). "
                "In Python, this raises ZeroDivisionError."
            ),
            "guiding_questions": [
                "Could the divisor variable ever evaluate to 0 on boundary inputs (e.g., when length is 0 or array sum is 0)?",
                "How should your function handle cases where the denominator has no valid non-zero value?",
            ],
            "invariant_to_maintain": "Arithmetic Precondition: Denominator D != 0 before executing (N / D) or (N % D).",
            "next_step_hint": "Add an explicit sanity check: 'if divisor == 0: ...' before performing division.",
        }

    else:
        return {
            "title": f"Runtime Crash: {result.status.value}",
            "root_cause_explanation": (
                f"Test vector '{vec_name}' failed with: {result.error_message or 'non-zero exit code'}. "
                "An unhandled condition was encountered during execution."
            ),
            "guiding_questions": [
                "Check the stack trace for the exact line number where the unhandled exception originated.",
                "Does the code make implicit assumptions about input types or formats?",
            ],
            "invariant_to_maintain": "Defensive Preconditions: Handle empty, negative, or extreme boundary inputs gracefully.",
            "next_step_hint": "Review the stack trace and add defensive checks for edge cases.",
        }

