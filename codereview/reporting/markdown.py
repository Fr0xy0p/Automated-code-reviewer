"""
Markdown Report Generator.
Generates comprehensive GitHub-flavored Markdown reports for PRs, CI, and local review.
"""

from __future__ import annotations
from typing import List, Dict, Any
from ..ast_analyzer.base import FileAnalysisResult, Severity
from ..runner.executor import TestResult, ExecutionStatus


def generate_markdown_report(
    analysis: FileAnalysisResult,
    test_results: List[TestResult],
    ai_diagnoses: List[Dict[str, Any]],
) -> str:
    passed_count = sum(1 for r in test_results if r.is_success)
    total_tests = len(test_results)
    all_passed = (passed_count == total_tests) and (total_tests > 0)

    status_badge = (
        "![Status: PASS](https://img.shields.io/badge/Review-PASSED-brightgreen?style=for-the-badge)"
        if all_passed
        else f"![Status: FAIL](https://img.shields.io/badge/Review-FAILED_{passed_count}%2F{total_tests}-red?style=for-the-badge)"
    )

    lines = [
        "# 🛡️ Automated Code Review & Complexity Profiler",
        "",
        status_badge,
        "",
        f"**File:** `{analysis.file_path}`  ",
        f"**Language:** `{analysis.language.upper()}`  ",
        "",
        "## 📊 Code & Complexity Metrics",
        "",
        "| Metric | Value | Rating / Benchmark |",
        "| :--- | :--- | :--- |",
        f"| **Source Lines (SLOC)** | `{analysis.sloc}` (Total: `{analysis.total_loc}`) | Comments: `{analysis.comment_lines}` |",
        f"| **Maintainability Index** | `{analysis.maintainability_index:.1f} / 100` | {'🟢 Good' if analysis.maintainability_index >= 65 else '🟡 Moderate' if analysis.maintainability_index >= 40 else '🔴 Low'} |",
        f"| **Max Cyclomatic Complexity** | `{analysis.max_cyclomatic_complexity}` | {'🟢 Low Risk' if analysis.max_cyclomatic_complexity <= 5 else '🟡 Moderate' if analysis.max_cyclomatic_complexity <= 10 else '🔴 High Risk'} |",
        f"| **Estimated Time Complexity** | `{analysis.overall_time_complexity}` | Asymptotic upper bound |",
        f"| **Estimated Space Complexity** | `{analysis.overall_space_complexity}` | Auxiliary memory / call stack |",
        "",
    ]

    if analysis.functions:
        lines.extend([
            "### Function Breakdown",
            "",
            "| Function | Lines | Cyclomatic | Nesting Depth | Time | Space | Issues |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for fn in analysis.functions:
            lines.append(
                f"| `{fn.name}()` | L{fn.start_line}-L{fn.end_line} ({fn.sloc}) | {fn.cyclomatic_complexity} | {fn.max_loop_depth} | `{fn.time_complexity}` | `{fn.space_complexity}` | {len(fn.issues)} |"
            )
        lines.append("")

    all_issues = analysis.all_issues
    if all_issues:
        lines.extend([
            "## ⚠️ Static Code & Edge-Case Vulnerabilities",
            "",
            "| Line | Severity | Category | Description | Suggested Fix |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ])
        for issue in all_issues:
            sev_icon = "🔴" if issue.severity == Severity.CRITICAL else "🟡" if issue.severity == Severity.WARNING else "ℹ️"
            lines.append(
                f"| L{issue.line_number} | {sev_icon} {issue.severity.value} | `{issue.category}` | {issue.message} | {issue.suggestion} |"
            )
        lines.append("")

    lines.extend([
        "## 🧪 Edge-Case Test Vector Matrix",
        "",
        f"Summary: **{passed_count} / {total_tests}** test vectors passed.",
        "",
        "| Status | Test Vector | Category | Time (ms) | Edge-Case Probed |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ])

    for res in test_results:
        ms = res.execution_time_sec * 1000.0
        if res.status == ExecutionStatus.PASS:
            badge = "✅ PASS"
        elif res.status == ExecutionStatus.TLE:
            badge = "⏱️ **TLE**"
        elif res.status in (ExecutionStatus.SIGSEGV, ExecutionStatus.ASAN_ERROR):
            badge = f"💥 **{res.status.value}**"
        else:
            badge = f"❌ **{res.status.value}**"

        lines.append(
            f"| {badge} | `{res.vector_name}` | {res.category} | `{ms:.2f} ms` | {res.vector_description} |"
        )
    lines.append("")

    if ai_diagnoses:
        lines.extend([
            "## 🤖 AI Pair-Programmer Diagnostic & Coaching",
            "",
            "> [!NOTE]",
            "> *Rather than rewriting the code for you, the Pair-Programmer explains why the machine or algorithm fails on this corner case and provides Socratic guiding questions to help you solve it.*",
            "",
        ])

        for diag_entry in ai_diagnoses:
            diag = diag_entry.get("diagnosis", {})
            vec_name = diag_entry.get("vector_name", "")
            status = diag_entry.get("status", "")
            engine = diag.get("engine", "Pair Programmer")

            lines.extend([
                f"### 🔍 {diag.get('title', 'Failure Diagnosis')} (`{vec_name}` - {status})",
                f"*Diagnosis provided by: **{engine}***  ",
                "",
                "#### Root Cause Analysis",
                diag.get("root_cause_explanation", ""),
                "",
            ])

            questions = diag.get("guiding_questions", [])
            if questions:
                lines.append("#### 💡 Socratic Guiding Questions")
                for q in questions:
                    lines.append(f"- {q}")
                lines.append("")

            inv = diag.get("invariant_to_maintain")
            if inv:
                lines.extend([
                    "#### 🛡️ Invariant to Maintain",
                    f"> **{inv}**",
                    "",
                ])

            hint = diag.get("next_step_hint")
            if hint:
                lines.extend([
                    "#### 👉 Next Step Hint",
                    f"_{hint}_",
                    "",
                ])

    elif all_passed:
        lines.extend([
            "## 🤖 AI Pair-Programmer Feedback",
            "",
            "🎉 **Flawless Execution!** Your solution passed all boundary vectors (empty arrays, minimal singletons, extreme 32-bit bounds, duplicates, sorted sequences, and scale stress tests).",
            "",
        ])

    lines.extend([
        "---",
        "*Generated automatically by Automated Code Reviewer & Complexity Profiler.*",
    ])

    return "\n".join(lines)
