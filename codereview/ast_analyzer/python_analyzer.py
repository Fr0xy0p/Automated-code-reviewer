"""
Python AST Static Code Analyzer.
Extracts metrics, loop depths, Big-O estimates, and catches logical edge-case bugs.
"""

from __future__ import annotations
import ast
import re
from typing import List, Dict, Set, Tuple, Optional, Any
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


class PythonASTVisitor(ast.NodeVisitor):
    """
    Visits Python AST to compute metrics and detect edge-case risks.
    """

    def __init__(self, source_code: str, file_path: str):
        self.source_code = source_code
        self.file_path = file_path
        self.source_lines = source_code.splitlines()
        self.functions: List[FunctionMetrics] = []
        self.global_issues: List[RiskIssue] = []

        # Current function context
        self.current_function: Optional[str] = None
        self.current_function_node: Optional[ast.FunctionDef | ast.AsyncFunctionDef] = None
        self.current_loop_depth = 0
        self.max_loop_depth_in_fn = 0
        self.cyclomatic_in_fn = 1
        self.cognitive_in_fn = 0
        self.nesting_level = 0
        self.recursive_calls_count = 0
        self.has_memoization = False
        self.has_log_step = False
        self.has_sort = False
        self.fn_issues: List[RiskIssue] = []
        self.allocated_collection = False
        self.allocated_matrix = False

        # Halstead tracking
        self.operators: List[str] = []
        self.operands: List[str] = []

    def _get_snippet(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> Any:
        # Save previous context
        prev_fn = self.current_function
        prev_node = self.current_function_node
        prev_loop_depth = self.current_loop_depth
        prev_max_loop = self.max_loop_depth_in_fn
        prev_cc = self.cyclomatic_in_fn
        prev_cog = self.cognitive_in_fn
        prev_nesting = self.nesting_level
        prev_rec = self.recursive_calls_count
        prev_memo = self.has_memoization
        prev_log = self.has_log_step
        prev_sort = self.has_sort
        prev_issues = self.fn_issues
        prev_alloc = self.allocated_collection
        prev_mat = self.allocated_matrix

        # Initialize for this function
        self.current_function = node.name
        self.current_function_node = node
        self.current_loop_depth = 0
        self.max_loop_depth_in_fn = 0
        self.cyclomatic_in_fn = 1
        self.cognitive_in_fn = 0
        self.nesting_level = 0
        self.recursive_calls_count = 0
        self.has_log_step = False
        self.has_sort = False
        self.fn_issues = []
        self.allocated_collection = False
        self.allocated_matrix = False

        # Check memoization decorators (e.g., lru_cache, cache)
        self.has_memoization = False
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name) and dec.id in ("lru_cache", "cache"):
                self.has_memoization = True
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id in ("lru_cache", "cache"):
                self.has_memoization = True
            elif isinstance(dec, ast.Attribute) and dec.attr in ("lru_cache", "cache"):
                self.has_memoization = True

        # Check mutable default arguments
        self._check_mutable_defaults(node)

        # Inspect body
        self.generic_visit(node)

        # Check recursion without base case
        if self.recursive_calls_count > 0:
            has_if = any(isinstance(child, (ast.If, ast.IfExp)) for child in ast.walk(node))
            if not has_if:
                self.fn_issues.append(
                    RiskIssue(
                        category="Recursion",
                        message=f"Function '{node.name}' makes recursive calls with no conditional base case (guaranteed RecursionError / stack overflow).",
                        line_number=node.lineno,
                        severity=Severity.CRITICAL,
                        suggestion="Add a terminating base-case condition (e.g., 'if n <= 1: return n') before recursive invocation.",
                        code_snippet=self._get_snippet(node.lineno),
                    )
                )

        # Infer Big-O
        branching = self.recursive_calls_count
        if self.has_memoization and branching > 0:
            # Memoized recursion reduces exponential branching to O(N) or O(N^2)
            time_o = BigO.O_N
        else:
            time_o = BigO.infer_from_loops_and_recursion(
                max_loop_depth=self.max_loop_depth_in_fn,
                has_recursion=self.recursive_calls_count > 0,
                recursion_branching=branching,
                has_logarithmic_step=self.has_log_step,
                has_sort=self.has_sort,
            )

        space_o = BigO.infer_space_complexity(
            has_recursion=self.recursive_calls_count > 0,
            recursion_branching=branching,
            allocates_collection=self.allocated_collection,
            allocates_matrix=self.allocated_matrix,
        )

        # Warn if exponential or quadratic
        if time_o == BigO.O_2N and not self.has_memoization:
            self.fn_issues.append(
                RiskIssue(
                    category="Complexity",
                    message=f"Function '{node.name}' exhibits branching recursion without memoization (O(2^N) exponential time). Large inputs will cause Time Limit Exceeded (TLE).",
                    line_number=node.lineno,
                    severity=Severity.WARNING,
                    suggestion="Add '@functools.lru_cache(None)' or convert to iterative dynamic programming (DP).",
                    code_snippet=self._get_snippet(node.lineno),
                )
            )
        elif self.max_loop_depth_in_fn >= 2:
            self.fn_issues.append(
                RiskIssue(
                    category="Complexity",
                    message=f"Function '{node.name}' contains {self.max_loop_depth_in_fn} nested loops (estimated {time_o}). High probability of TLE on arrays of size N >= 10^5.",
                    line_number=node.lineno,
                    severity=Severity.WARNING,
                    suggestion="Consider using a hash table / set for O(1) lookups or sorting beforehand to achieve O(N) or O(N log N).",
                    code_snippet=self._get_snippet(node.lineno),
                )
            )

        # Collect parameters
        param_names = [arg.arg for arg in node.args.args]

        docstring = ast.get_docstring(node)
        sloc = (node.end_lineno - node.lineno + 1) if hasattr(node, "end_lineno") and node.end_lineno else len(node.body)

        fn_metric = FunctionMetrics(
            name=node.name,
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno + len(node.body)),
            sloc=sloc,
            cyclomatic_complexity=self.cyclomatic_in_fn,
            cognitive_complexity=self.cognitive_in_fn,
            max_loop_depth=self.max_loop_depth_in_fn,
            has_recursion=self.recursive_calls_count > 0,
            recursion_branching=self.recursive_calls_count,
            time_complexity=time_o,
            space_complexity=space_o,
            parameters=param_names,
            docstring=docstring,
            issues=self.fn_issues,
        )
        self.functions.append(fn_metric)

        # Restore context
        self.current_function = prev_fn
        self.current_function_node = prev_node
        self.current_loop_depth = prev_loop_depth
        self.max_loop_depth_in_fn = prev_max_loop
        self.cyclomatic_in_fn = prev_cc
        self.cognitive_in_fn = prev_cog
        self.nesting_level = prev_nesting
        self.recursive_calls_count = prev_rec
        self.has_memoization = prev_memo
        self.has_log_step = prev_log
        self.has_sort = prev_sort
        self.fn_issues = prev_issues
        self.allocated_collection = prev_alloc
        self.allocated_matrix = prev_mat

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        return self.visit_FunctionDef(node)

    def _check_mutable_defaults(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for default in node.args.defaults + [d for d in node.args.kw_defaults if d]:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.fn_issues.append(
                    RiskIssue(
                        category="Anti-Pattern",
                        message=f"Mutable default argument used in '{node.name}'. Mutable defaults retain state across function calls, causing unexpected side effects across test cases.",
                        line_number=default.lineno,
                        severity=Severity.WARNING,
                        suggestion="Use 'None' as default value and initialize inside the function (e.g., 'if arg is None: arg = []').",
                        code_snippet=self._get_snippet(default.lineno),
                    )
                )

    def visit_If(self, node: ast.If) -> Any:
        self.cyclomatic_in_fn += 1
        self.cognitive_in_fn += (1 + self.nesting_level)
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        self.cyclomatic_in_fn += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For | ast.AsyncFor) -> Any:
        self.cyclomatic_in_fn += 1
        self.cognitive_in_fn += (1 + self.nesting_level)
        self.current_loop_depth += 1
        if self.current_loop_depth > self.max_loop_depth_in_fn:
            self.max_loop_depth_in_fn = self.current_loop_depth

        self.nesting_level += 1
        self._check_for_loop_bounds(node)
        self.generic_visit(node)
        self.nesting_level -= 1
        self.current_loop_depth -= 1

    def visit_AsyncFor(self, node: ast.AsyncFor) -> Any:
        return self.visit_For(node)

    def _check_for_loop_bounds(self, node: ast.For | ast.AsyncFor) -> None:
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
            args = node.iter.args
            for arg in args:
                if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                    if (isinstance(arg.left, ast.Call) and isinstance(arg.left.func, ast.Name) and arg.left.func.id == "len") or \
                       (isinstance(arg.right, ast.Call) and isinstance(arg.right.func, ast.Name) and arg.right.func.id == "len"):
                        self.fn_issues.append(
                            RiskIssue(
                                category="Edge-Case",
                                message="Potential off-by-one IndexError: range includes 'len(...) + k'. Iterating up to len(x) exceeds 0-indexed bounds.",
                                line_number=node.lineno,
                                severity=Severity.CRITICAL,
                                suggestion="Verify loop boundary. If 0-indexed, range should typically end at 'len(x)'.",
                                code_snippet=self._get_snippet(node.lineno),
                            )
                        )

    def visit_While(self, node: ast.While) -> Any:
        self.cyclomatic_in_fn += 1
        self.cognitive_in_fn += (1 + self.nesting_level)
        self.current_loop_depth += 1
        if self.current_loop_depth > self.max_loop_depth_in_fn:
            self.max_loop_depth_in_fn = self.current_loop_depth

        for child in ast.walk(node):
            if isinstance(child, ast.BinOp) and isinstance(child.op, (ast.FloorDiv, ast.RShift)):
                if isinstance(child.right, ast.Constant) and child.right.value in (2, 1):
                    self.has_log_step = True

        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1
        self.current_loop_depth -= 1

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        self.cyclomatic_in_fn += max(1, len(node.values) - 1)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> Any:
        self.cyclomatic_in_fn += 1
        if node.type is None:
            issue = RiskIssue(
                category="Safety",
                message="Bare 'except:' clause caught. This catches KeyboardInterrupt, MemoryError, and masks critical edge-case exceptions.",
                line_number=node.lineno,
                severity=Severity.WARNING,
                suggestion="Catch specific exceptions, e.g. 'except Exception:' or 'except (IndexError, ValueError):'.",
                code_snippet=self._get_snippet(node.lineno),
            )
            if self.current_function:
                self.fn_issues.append(issue)
            else:
                self.global_issues.append(issue)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        if self.current_function:
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute) and node.func.attr == self.current_function:
                callee_name = self.current_function

            if callee_name == self.current_function:
                self.recursive_calls_count += 1

        if isinstance(node.func, ast.Name) and node.func.id == "sorted":
            self.has_sort = True
        elif isinstance(node.func, ast.Attribute) and node.func.attr == "sort":
            self.has_sort = True

        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            if isinstance(node.right, ast.Constant) and node.right.value == 0:
                issue = RiskIssue(
                    category="Edge-Case",
                    message="Literal division/modulo by zero detected (guaranteed ZeroDivisionError).",
                    line_number=node.lineno,
                    severity=Severity.CRITICAL,
                    suggestion="Ensure denominator is strictly non-zero before division.",
                    code_snippet=self._get_snippet(node.lineno),
                )
                if self.current_function:
                    self.fn_issues.append(issue)
                else:
                    self.global_issues.append(issue)

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> Any:
        self.allocated_collection = True
        if any(isinstance(elt, (ast.ListComp, ast.List)) for elt in [node.elt]):
            self.allocated_matrix = True
        for gen in node.generators:
            self.cyclomatic_in_fn += len(gen.ifs)
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> Any:
        self.allocated_collection = True
        for gen in node.generators:
            self.cyclomatic_in_fn += len(gen.ifs)
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> Any:
        self.allocated_collection = True
        for gen in node.generators:
            self.cyclomatic_in_fn += len(gen.ifs)
        self.generic_visit(node)


def analyze_python_source(source_code: str, file_path: str = "source.py") -> FileAnalysisResult:
    lines = source_code.splitlines()
    total_loc = len(lines)
    blank_lines = sum(1 for line in lines if not line.strip())
    comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
    sloc = max(1, total_loc - blank_lines - comment_lines)

    try:
        tree = ast.parse(source_code, filename=file_path)
    except SyntaxError as e:
        syntax_issue = RiskIssue(
            category="Syntax",
            message=f"SyntaxError: {e.msg} at line {e.lineno}, column {e.offset}",
            line_number=e.lineno or 1,
            column=e.offset or 0,
            severity=Severity.CRITICAL,
            suggestion="Fix the syntax error to enable AST parsing and automated testing.",
            code_snippet=e.text.strip() if e.text else "",
        )
        return FileAnalysisResult(
            file_path=file_path,
            language="python",
            total_loc=total_loc,
            sloc=sloc,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            maintainability_index=0.0,
            overall_time_complexity="Unknown (SyntaxError)",
            overall_space_complexity="Unknown (SyntaxError)",
            functions=[],
            global_issues=[syntax_issue],
        )

    visitor = PythonASTVisitor(source_code, file_path)
    visitor.visit(tree)

    if visitor.functions:
        overall_time = BigO.aggregate([fn.time_complexity for fn in visitor.functions])
        overall_space = BigO.aggregate([fn.space_complexity for fn in visitor.functions])
        max_cc = max(fn.cyclomatic_complexity for fn in visitor.functions)
    else:
        overall_time = BigO.O_1
        overall_space = BigO.O_1
        max_cc = 1

    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[+\-*/%=<>!&|^~]+|\d+", source_code)
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
        language="python",
        total_loc=total_loc,
        sloc=sloc,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
        maintainability_index=mi,
        overall_time_complexity=overall_time,
        overall_space_complexity=overall_space,
        functions=visitor.functions,
        global_issues=visitor.global_issues,
    )
