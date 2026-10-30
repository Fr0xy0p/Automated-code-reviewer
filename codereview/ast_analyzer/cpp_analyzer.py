"""
C & C++ Source Code Static Analyzer.
Performs lexical/structural AST-like analysis, loop depth & recursion extraction,
Big-O complexity calculation, and memory safety / edge-case risk detection.
"""

from __future__ import annotations
import re
from typing import List, Dict, Set, Tuple, Optional
from .base import (
    FileAnalysisResult,
    FunctionMetrics,
    RiskIssue,
    Severity,
)
from ..complexity.big_o import BigO
from ..complexity.metrics import (
    calculate_halstead_volume,
    calculate_maintainability_index,
)

UNSAFE_C_FUNCTIONS = {
    "gets": ("Buffer overflow vulnerability; function removed in C11.", "fgets"),
    "strcpy": ("Unbounded string copy; potential buffer overflow.", "strncpy or strlcpy"),
    "strcat": ("Unbounded string concatenation; potential buffer overflow.", "strncat or strlcat"),
    "sprintf": ("Format string buffer overflow risk.", "snprintf"),
    "scanf": ("Unbounded '%s' format specifier can overflow destination buffer.", "scanf with field width limit e.g. %63s"),
}


def strip_c_comments(code: str) -> Tuple[str, int, int]:
    lines = code.splitlines()
    blank_lines = sum(1 for line in lines if not line.strip())

    comment_lines = 0
    in_block_comment = False
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if in_block_comment:
            comment_lines += 1
            if "*/" in stripped:
                in_block_comment = False
                after = stripped.split("*/", 1)[1]
                cleaned_lines.append(after)
            else:
                cleaned_lines.append("")
        elif stripped.startswith("/*"):
            comment_lines += 1
            if "*/" in stripped:
                cleaned_lines.append(re.sub(r"/\*.*?\*/", "", line))
            else:
                in_block_comment = True
                cleaned_lines.append(stripped.split("/*", 1)[0])
        elif stripped.startswith("//"):
            comment_lines += 1
            cleaned_lines.append("")
        else:
            cleaned = re.sub(r"//.*$", "", line)
            cleaned = re.sub(r"/\*.*?\*/", "", cleaned)
            cleaned_lines.append(cleaned)

    return "\n".join(cleaned_lines), comment_lines, blank_lines


def analyze_cpp_source(source_code: str, file_path: str = "source.cpp") -> FileAnalysisResult:
    is_cpp = file_path.endswith((".cpp", ".cc", ".cxx", ".hpp", ".hxx"))
    language = "cpp" if is_cpp else "c"

    raw_lines = source_code.splitlines()
    total_loc = len(raw_lines)

    clean_code, comment_lines, blank_lines = strip_c_comments(source_code)
    sloc = max(1, total_loc - comment_lines - blank_lines)

    global_issues: List[RiskIssue] = []

    for fn, (desc, alt) in UNSAFE_C_FUNCTIONS.items():
        pattern = re.compile(rf"\b{fn}\s*\(")
        for i, line in enumerate(raw_lines, 1):
            if pattern.search(line):
                global_issues.append(
                    RiskIssue(
                        category="Memory/Safety",
                        message=f"Use of unsafe function '{fn}': {desc}",
                        line_number=i,
                        severity=Severity.CRITICAL if fn in ("gets", "strcpy") else Severity.WARNING,
                        suggestion=f"Replace with safe alternative '{alt}'.",
                        code_snippet=line.strip(),
                    )
                )

    div_zero_pattern = re.compile(r"[/]\s*0\b")
    for i, line in enumerate(raw_lines, 1):
        if div_zero_pattern.search(line):
            global_issues.append(
                RiskIssue(
                    category="Edge-Case",
                    message="Literal division by zero detected (guaranteed SIGFPE floating point exception).",
                    line_number=i,
                    severity=Severity.CRITICAL,
                    suggestion="Ensure denominator is strictly non-zero before division.",
                    code_snippet=line.strip(),
                )
            )

    has_malloc = bool(re.search(r"\bmalloc\s*\(", source_code))
    has_free = bool(re.search(r"\bfree\s*\(", source_code))
    if has_malloc and not has_free:
        global_issues.append(
            RiskIssue(
                category="Memory",
                message="Memory allocated via 'malloc' without corresponding 'free' found in file (Memory Leak risk).",
                line_number=1,
                severity=Severity.WARNING,
                suggestion="Ensure all dynamically allocated memory is freed before program termination or function exit.",
            )
        )

    has_new = bool(re.search(r"\bnew\s+", source_code))
    has_delete = bool(re.search(r"\bdelete\b", source_code))
    if has_new and not has_delete and is_cpp:
        global_issues.append(
            RiskIssue(
                category="Memory",
                message="C++ 'new' used without matching 'delete' (potential memory leak).",
                line_number=1,
                severity=Severity.WARNING,
                suggestion="Prefer modern C++ smart pointers (std::unique_ptr, std::shared_ptr) or RAII containers (std::vector, std::string).",
            )
        )

    func_pattern = re.compile(
        r"(?:(?:inline|static|virtual|const|explicit)\s+)*"
        r"([a-zA-Z_][a-zA-Z0-9_:*&<>\s]+?)\s+"
        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*"
        r"\(([^)]*)\)\s*(?:const)?\s*\{",
        re.MULTILINE,
    )

    functions: List[FunctionMetrics] = []

    for match in func_pattern.finditer(source_code):
        ret_type = match.group(1).strip()
        fn_name = match.group(2).strip()
        params_str = match.group(3).strip()

        if fn_name in ("if", "while", "for", "switch", "catch"):
            continue

        start_pos = match.start()
        start_line = source_code[:start_pos].count("\n") + 1

        brace_count = 0
        end_pos = start_pos
        found_start = False
        for pos in range(match.end() - 1, len(source_code)):
            char = source_code[pos]
            if char == "{":
                brace_count += 1
                found_start = True
            elif char == "}":
                brace_count -= 1
                if found_start and brace_count == 0:
                    end_pos = pos
                    break

        fn_body = source_code[match.end():end_pos]
        end_line = source_code[:end_pos].count("\n") + 1
        fn_sloc = max(1, end_line - start_line + 1)

        max_loop_depth = 0
        current_loop_depth = 0
        cyclomatic = 1
        cognitive = 0

        fn_lines = fn_body.splitlines()
        for l in fn_lines:
            stripped = l.strip()
            for decision_kw in (r"\bif\b", r"\bfor\b", r"\bwhile\b", r"\bcase\b", r"\bcatch\b", r"&&", r"\|\|"):
                cyclomatic += len(re.findall(decision_kw, stripped))

            if re.search(r"\b(for|while)\s*\(", stripped) or re.search(r"\bdo\s*\{?", stripped):
                current_loop_depth += 1
                if current_loop_depth > max_loop_depth:
                    max_loop_depth = current_loop_depth
                cognitive += current_loop_depth
            if "}" in stripped:
                if current_loop_depth > 0:
                    current_loop_depth -= 1

        rec_matches = len(re.findall(rf"\b{re.escape(fn_name)}\s*\(", fn_body))
        has_recursion = rec_matches > 0

        has_log_step = bool(re.search(r"/\s*2\b|>>\s*1\b", fn_body))
        has_sort = bool(re.search(r"\b(qsort|std::sort|sort)\s*\(", fn_body))

        time_o = BigO.infer_from_loops_and_recursion(
            max_loop_depth=max_loop_depth,
            has_recursion=has_recursion,
            recursion_branching=rec_matches,
            has_logarithmic_step=has_log_step,
            has_sort=has_sort,
        )

        allocates_vec = bool(re.search(r"\bvector<|std::vector<|malloc\(", fn_body))
        space_o = BigO.infer_space_complexity(
            has_recursion=has_recursion,
            recursion_branching=rec_matches,
            allocates_collection=allocates_vec,
        )

        fn_issues: List[RiskIssue] = []

        if has_recursion:
            has_base_case = bool(re.search(r"\bif\s*\(", fn_body))
            if not has_base_case:
                fn_issues.append(
                    RiskIssue(
                        category="Recursion",
                        message=f"Function '{fn_name}' calls itself recursively without a detectable conditional base case (guaranteed Stack Overflow / Segfault).",
                        line_number=start_line,
                        severity=Severity.CRITICAL,
                        suggestion="Add a terminating base case check before calling itself.",
                    )
                )
            if rec_matches >= 2:
                fn_issues.append(
                    RiskIssue(
                        category="Complexity",
                        message=f"Function '{fn_name}' has branching recursion ({rec_matches} call sites per step) without dynamic programming / memoization (O(2^N) exponential time).",
                        line_number=start_line,
                        severity=Severity.WARNING,
                        suggestion="Use memoization table (e.g. vector<int> memo) or bottom-up iterative DP to achieve O(N) linear time.",
                    )
                )

        if max_loop_depth >= 2:
            fn_issues.append(
                RiskIssue(
                    category="Complexity",
                    message=f"Function '{fn_name}' has {max_loop_depth} nested loops (estimated {time_o}). High risk of Time Limit Exceeded (TLE) on large inputs.",
                    line_number=start_line,
                    severity=Severity.WARNING,
                    suggestion="Consider using an unordered_map (hash table) or sorting to avoid quadratic iteration.",
                )
            )

        params = [p.strip().split()[-1].lstrip("*&") for p in params_str.split(",") if p.strip()]

        functions.append(
            FunctionMetrics(
                name=fn_name,
                start_line=start_line,
                end_line=end_line,
                sloc=fn_sloc,
                cyclomatic_complexity=cyclomatic,
                cognitive_complexity=cognitive,
                max_loop_depth=max_loop_depth,
                has_recursion=has_recursion,
                recursion_branching=rec_matches,
                time_complexity=time_o,
                space_complexity=space_o,
                parameters=params,
                issues=fn_issues,
            )
        )

    if functions:
        overall_time = BigO.aggregate([fn.time_complexity for fn in functions])
        overall_space = BigO.aggregate([fn.space_complexity for fn in functions])
        max_cc = max(fn.cyclomatic_complexity for fn in functions)
    else:
        overall_time = BigO.O_1
        overall_space = BigO.O_1
        max_cc = 1

    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[+\-*/%=<>!&|^~]+|\d+", clean_code)
    unique_tokens = len(set(tokens))
    total_tokens = len(tokens)
    halstead_vol = calculate_halstead_volume(
        operators_count=total_tokens // 2,
        operands_count=total_tokens - (total_tokens // 2),
        unique_operators=max(1, unique_tokens // 2),
        unique_operands=max(1, unique_tokens - (unique_tokens // 2)),
    )

    mi = calculate_maintainability_index(sloc=sloc, cyclomatic_complexity=max_cc, halstead_volume=halstead_vol)

    return FileAnalysisResult(
        file_path=file_path,
        language=language,
        total_loc=total_loc,
        sloc=sloc,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
        maintainability_index=mi,
        overall_time_complexity=overall_time,
        overall_space_complexity=overall_space,
        functions=functions,
        global_issues=global_issues,
    )

