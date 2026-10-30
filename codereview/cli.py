"""
Command Line Interface (CLI) for Automated Code Reviewer & Complexity Profiler.
"""

from __future__ import annotations
import argparse
import os
import sys
from typing import List, Dict, Any, Optional

from .ast_analyzer import analyze_file
from .ast_analyzer.base import Severity
from .complexity.limits import predict_time_limit_exceeded
from .testgen.generator import (
    generate_test_vectors_for_parameters,
    generate_array_edge_cases,
    generate_integer_edge_cases,
    generate_string_edge_cases,
)
from .runner.executor import TestResult, ExecutionStatus
from .runner.python_runner import run_python_suite
from .runner.cpp_runner import run_cpp_suite
from .ai.explainer import get_pair_programmer_explanation
from .reporting.terminal import (
    print_banner,
    print_file_summary,
    print_test_results_table,
    print_pair_programmer_advice,
)
from .reporting.markdown import generate_markdown_report
from .reporting.json_reporter import generate_json_report
from .hooks.git_hook import install_git_hook, uninstall_git_hook
from .hooks.github_action import install_github_action_workflow


def review_file(
    file_path: str,
    function_name: Optional[str] = None,
    timeout_sec: float = 1.0,
    api_key: Optional[str] = None,
    use_ai: bool = True,
    strict: bool = False,
    output_markdown: Optional[str] = None,
    output_json: Optional[str] = None,
    quiet: bool = False,
) -> int:
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        source_code = f.read()

    analysis = analyze_file(file_path)

    param_names = []
    if function_name:
        for fn in analysis.functions:
            if fn.name == function_name:
                param_names = fn.parameters
                break
    elif analysis.functions:
        param_names = analysis.functions[0].parameters

    vectors = generate_test_vectors_for_parameters(param_names)

    test_results: List[TestResult] = []
    if analysis.language == "python":
        test_results = run_python_suite(
            file_path=file_path,
            vectors=vectors,
            function_name=function_name,
            timeout_sec=timeout_sec,
        )
    elif analysis.language in ("c", "cpp"):
        test_results, compile_err = run_cpp_suite(
            source_path=file_path,
            vectors=vectors,
            language=analysis.language,
            timeout_sec=timeout_sec,
        )
    else:
        test_results = []

    ai_diagnoses: List[Dict[str, Any]] = []
    for res in test_results:
        if not res.is_success:
            diag = get_pair_programmer_explanation(
                result=res,
                analysis=analysis,
                source_code=source_code,
                api_key=api_key,
                use_ai=use_ai,
            )
            ai_diagnoses.append({
                "vector_name": res.vector_name,
                "status": res.status.value,
                "error_message": res.error_message,
                "diagnosis": diag,
            })

    if not quiet:
        print_banner()
        print_file_summary(analysis)
        print_test_results_table(test_results)
        print_pair_programmer_advice(ai_diagnoses)

    if output_markdown:
        md_content = generate_markdown_report(analysis, test_results, ai_diagnoses)
        with open(output_markdown, "w", encoding="utf-8") as f:
            f.write(md_content)
        if not quiet:
            print(f"📄 Markdown report saved to: {output_markdown}")

    if output_json:
        json_content = generate_json_report(analysis, test_results, ai_diagnoses)
        with open(output_json, "w", encoding="utf-8") as f:
            f.write(json_content)
        if not quiet:
            print(f"💾 JSON report saved to: {output_json}")

    has_critical_issues = any(i.severity == Severity.CRITICAL for i in analysis.all_issues)
    has_failed_tests = any(not r.is_success for r in test_results)

    if strict and (has_failed_tests or has_critical_issues):
        return 1

    return 0


def profile_file(file_path: str, max_n: int = 100_000) -> int:
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
        return 1

    analysis = analyze_file(file_path)
    print_banner()
    print_file_summary(analysis)

    print(f"Asymptotic Scale Limits Check (for N = {max_n:,}):")
    print("-" * 76)
    pred = predict_time_limit_exceeded(
        complexity=analysis.overall_time_complexity,
        max_expected_n=max_n,
        language=analysis.language,
    )
    print(f"  • Complexity:            {pred['complexity']}")
    print(f"  • Estimated Operations:  {pred['estimated_operations']:,.0f}")
    print(f"  • Projected Runtime:     {pred['estimated_time_sec']:.4f} seconds")
    print(f"  • TLE Verdict:           {'🚨 WILL TLE' if pred['will_tle'] else '✅ PASSES TIME LIMIT'}")
    print(f"  • Recommended Big-O:     {pred['recommended_complexity']}")
    print(f"\n  Details: {pred['explanation']}\n")
    return 0


def test_gen_cmd(file_path: str) -> int:
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist.", file=sys.stderr)
        return 1

    analysis = analyze_file(file_path)
    param_names = analysis.functions[0].parameters if analysis.functions else []
    vectors = generate_test_vectors_for_parameters(param_names)

    print(f"\nGenerated {len(vectors)} Edge-Case Test Vectors for '{file_path}':\n")
    for i, v in enumerate(vectors, 1):
        print(f"{i:2d}. [{v.category.upper()}] {v.name}")
        print(f"    • Description: {v.description}")
        print(f"    • Args:        {v.args}")
        if v.stdin:
            print(f"    • Stdin:       {repr(v.stdin)}")
        print()
    return 0


def ci_run(target_dir: str = "examples", output_markdown: Optional[str] = "report.md") -> int:
    extensions = (".py", ".c", ".cpp", ".cc")
    files_to_review = []
    search_root = target_dir if os.path.exists(target_dir) else "."

    for root, _, files in os.walk(search_root):
        if any(skip in root for skip in (".git", ".venv", "venv", "__pycache__", "build", "dist", "node_modules", "tests", "codereview")):
            continue
        for f in files:
            if f.endswith(extensions) and not f.startswith("test_") and f != "setup.py":
                files_to_review.append(os.path.join(root, f))

    if not files_to_review:
        print(f"No submission source files found in '{search_root}'.")
        return 0

    print(f"Found {len(files_to_review)} submission files to review in '{search_root}'.")
    overall_exit = 0
    all_reports = []

    for file_path in files_to_review:
        temp_md = file_path + ".review.tmp.md"
        exit_code = review_file(
            file_path=file_path,
            output_markdown=temp_md,
            quiet=True,
            strict=False,
        )
        if exit_code != 0:
            overall_exit = 1

        if os.path.exists(temp_md):
            with open(temp_md, "r", encoding="utf-8") as f:
                all_reports.append(f.read())
            os.remove(temp_md)

    if output_markdown and all_reports:
        with open(output_markdown, "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(all_reports))
        print(f"Combined CI review report written to: {output_markdown}")

    return overall_exit


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="codereview",
        description="Automated Code Reviewer & Complexity Profiler with AI Pair-Programming.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    review_parser = subparsers.add_parser("review", help="Review a file: AST, Big-O, edge-case test vectors, and AI guidance.")
    review_parser.add_argument("file", help="Path to Python, C, or C++ file")
    review_parser.add_argument("--function", "-f", help="Target function name to test (default: first function)")
    review_parser.add_argument("--timeout", "-t", type=float, default=1.0, help="Per-test timeout in seconds (default: 1.0s)")
    review_parser.add_argument("--api-key", help="Gemini API Key (or set GEMINI_API_KEY environment variable)")
    review_parser.add_argument("--no-ai", action="store_true", help="Force offline heuristic diagnostics without API calls")
    review_parser.add_argument("--strict", action="store_true", help="Exit with code 1 on failed tests or critical issues (for Git hooks / CI)")
    review_parser.add_argument("--output-markdown", "-m", help="Path to save GitHub-flavored Markdown report")
    review_parser.add_argument("--output-json", "-j", help="Path to save JSON report")
    review_parser.add_argument("--quiet", "-q", action="store_true", help="Suppress terminal banners and tables")

    profile_parser = subparsers.add_parser("profile", help="Profile Big-O complexity and predict TLE against scale N.")
    profile_parser.add_argument("file", help="Path to Python, C, or C++ file")
    profile_parser.add_argument("--scale-n", "-n", type=int, default=100_000, help="Target input scale N (default: 100,000)")

    testgen_parser = subparsers.add_parser("test-gen", help="Generate and inspect adversarial edge-case test vectors.")
    testgen_parser.add_argument("file", help="Path to source file")

    hook_parser = subparsers.add_parser("hook", help="Manage Git pre-commit hooks.")
    hook_sub = hook_parser.add_subparsers(dest="hook_action")
    hook_sub.add_parser("install", help="Install pre-commit hook into .git/hooks/pre-commit")
    hook_sub.add_parser("uninstall", help="Remove pre-commit hook")

    subparsers.add_parser("init-action", help="Generate GitHub Action workflow (.github/workflows/code_review.yml).")

    ci_parser = subparsers.add_parser("ci-run", help="Run review across workspace submission files for CI.")
    ci_parser.add_argument("--target-dir", "-d", default="examples", help="Directory containing code submissions (default: examples)")
    ci_parser.add_argument("--output-markdown", "-m", default="report.md", help="Path to output Markdown report")

    args = parser.parse_args()

    if args.command == "review":
        code = review_file(
            file_path=args.file,
            function_name=args.function,
            timeout_sec=args.timeout,
            api_key=args.api_key,
            use_ai=not args.no_ai,
            strict=args.strict,
            output_markdown=args.output_markdown,
            output_json=args.output_json,
            quiet=args.quiet,
        )
        sys.exit(code)

    elif args.command == "profile":
        code = profile_file(args.file, max_n=args.scale_n)
        sys.exit(code)

    elif args.command == "test-gen":
        code = test_gen_cmd(args.file)
        sys.exit(code)

    elif args.command == "hook":
        if args.hook_action == "install":
            ok, msg = install_git_hook()
            print(msg)
            sys.exit(0 if ok else 1)
        elif args.hook_action == "uninstall":
            ok, msg = uninstall_git_hook()
            print(msg)
            sys.exit(0 if ok else 1)
        else:
            hook_parser.print_help()
            sys.exit(1)

    elif args.command == "init-action":
        ok, msg = install_github_action_workflow()
        print(msg)
        sys.exit(0 if ok else 1)

    elif args.command == "ci-run":
        code = ci_run(target_dir=args.target_dir, output_markdown=args.output_markdown)
        sys.exit(code)

    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
