"""
Terminal Pretty-Printer and ANSI Formatter for Code Reviews.
"""

from __future__ import annotations
import sys
from typing import List, Dict, Any, Optional
from ..ast_analyzer.base import FileAnalysisResult, Severity
from ..runner.executor import TestResult, ExecutionStatus


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_RED = "\033[41m\033[97m"
    BG_GREEN = "\033[42m\033[97m"
    BG_YELLOW = "\033[43m\033[30m"


def print_banner() -> None:
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 76}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.WHITE}   AUTOMATED CODE REVIEWER & COMPLEXITY PROFILER{Colors.RESET}")
    print(f"{Colors.DIM}   AST Analysis • Big-O Limits • Edge-Case Vector Testing • AI Pair-Programmer{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 76}{Colors.RESET}\n")


def print_file_summary(analysis: FileAnalysisResult) -> None:
    print(f"{Colors.BOLD}{Colors.WHITE}File:{Colors.RESET} {analysis.file_path} ({analysis.language.upper()})")
    print(f"{Colors.DIM}----------------------------------------------------------------------------{Colors.RESET}")
    print(
        f"  • {Colors.BOLD}SLOC:{Colors.RESET} {analysis.sloc} (Total: {analysis.total_loc}, Comments: {analysis.comment_lines}, Blank: {analysis.blank_lines})"
    )
    print(f"  • {Colors.BOLD}Maintainability Index:{Colors.RESET} {analysis.maintainability_index:.1f}/100")
    print(
        f"  • {Colors.BOLD}Max Cyclomatic Complexity:{Colors.RESET} {analysis.max_cyclomatic_complexity}"
    )
    print(
        f"  • {Colors.BOLD}Asymptotic Complexity:{Colors.RESET} Time: {Colors.BOLD}{Colors.CYAN}{analysis.overall_time_complexity}{Colors.RESET} | Space: {Colors.BOLD}{Colors.CYAN}{analysis.overall_space_complexity}{Colors.RESET}"
    )
    print()


def print_test_results_table(test_results: List[TestResult]) -> None:
    print(f"{Colors.BOLD}{Colors.WHITE}Edge-Case Test Vector Matrix:{Colors.RESET}")
    print(f"{Colors.DIM}{'-' * 76}{Colors.RESET}")
    print(f"  {'Status':<16} {'Vector Name':<34} {'Category':<12} {'Time (ms)':<10}")
    print(f"{Colors.DIM}{'-' * 76}{Colors.RESET}")

    for res in test_results:
        ms = res.execution_time_sec * 1000.0
        if res.status == ExecutionStatus.PASS:
            status_badge = f"{Colors.GREEN}[✓ PASS]{Colors.RESET}"
        elif res.status == ExecutionStatus.TLE:
            status_badge = f"{Colors.YELLOW}[⏱ TLE]{Colors.RESET}"
        elif res.status in (ExecutionStatus.SIGSEGV, ExecutionStatus.ASAN_ERROR):
            status_badge = f"{Colors.RED}[💥 {res.status.value}]{Colors.RESET}"
        else:
            status_badge = f"{Colors.RED}[✗ {res.status.value}]{Colors.RESET}"

        print(f"  {status_badge:<25} {res.vector_name[:32]:<34} {res.category:<12} {ms:>6.2f} ms")

    print(f"{Colors.DIM}{'-' * 76}{Colors.RESET}\n")


def print_pair_programmer_advice(failures: List[Dict[str, Any]]) -> None:
    if not failures:
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 All edge-case vectors passed successfully! No runtime crashes or TLEs detected.{Colors.RESET}\n")
        return

    print(f"{Colors.BOLD}{Colors.MAGENTA}🤖 AI Pair-Programmer Diagnostic & Socratic Coaching:{Colors.RESET}")
    print(f"{Colors.DIM}{'=' * 76}{Colors.RESET}")

    for fail in failures:
        diag = fail.get("diagnosis", {})
        vec = fail.get("vector_name", "")
        status = fail.get("status", "")
        engine = diag.get("engine", "Pair Programmer")

        print(f"\n{Colors.BOLD}{Colors.RED}▶ Corner Case Crash: {vec} ({status}){Colors.RESET} [{Colors.DIM}{engine}{Colors.RESET}]")
        print(f"  {Colors.BOLD}Title:{Colors.RESET} {diag.get('title', '')}")
        print(f"\n  {Colors.BOLD}Root Cause (Machine & Algorithmic Level):{Colors.RESET}")
        print(f"  {Colors.WHITE}{diag.get('root_cause_explanation', '')}{Colors.RESET}")

        questions = diag.get("guiding_questions", [])
        if questions:
            print(f"\n  {Colors.BOLD}{Colors.CYAN}💡 Guiding Questions to think about:{Colors.RESET}")
            for q in questions:
                print(f"    • {q}")

        inv = diag.get("invariant_to_maintain")
        if inv:
            print(f"\n  {Colors.BOLD}{Colors.YELLOW}🛡 Invariant to Maintain:{Colors.RESET}")
            print(f"    {inv}")

        hint = diag.get("next_step_hint")
        if hint:
            print(f"\n  {Colors.BOLD}{Colors.GREEN}👉 Next Step Hint:{Colors.RESET}")
            print(f"    {hint}")

    print(f"\n{Colors.DIM}{'=' * 76}{Colors.RESET}\n")
