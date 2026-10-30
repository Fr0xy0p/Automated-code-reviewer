"""
Reporting package: Terminal, Markdown, and JSON.
"""

from .terminal import (
    print_banner,
    print_file_summary,
    print_test_results_table,
    print_pair_programmer_advice,
)
from .markdown import generate_markdown_report
from .json_reporter import generate_json_report

__all__ = [
    "print_banner",
    "print_file_summary",
    "print_test_results_table",
    "print_pair_programmer_advice",
    "generate_markdown_report",
    "generate_json_report",
]

