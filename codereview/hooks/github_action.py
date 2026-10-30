"""
GitHub Action Generator & CI integration.
Generates .github/workflows/code_review.yml for automated PR reviews and daily push checks.
"""

from __future__ import annotations
import os
from typing import Tuple

GITHUB_ACTION_TEMPLATE = """name: Automated Code Reviewer & Complexity Profiler

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  code-review:
    name: Code Review & Edge-Case Profiler
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Set up Clang & AddressSanitizer
        run: |
          sudo apt-get update
          sudo apt-get install -y clang libasan6

      - name: Install Reviewer Tool
        run: |
          pip install .

      - name: Run Reviewer on Changed Submissions
        id: review
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          python3 -m codereview.cli ci-run --output-markdown report.md || true

      - name: Publish Review Report to Job Summary
        if: always()
        run: |
          if [ -f report.md ]; then
            cat report.md >> $GITHUB_STEP_SUMMARY
          fi

      - name: Upload Review Artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: code-review-report
          path: report.md
"""


def install_github_action_workflow(repo_path: str = ".") -> Tuple[bool, str]:
    workflow_dir = os.path.join(repo_path, ".github", "workflows")
    os.makedirs(workflow_dir, exist_ok=True)
    workflow_path = os.path.join(workflow_dir, "code_review.yml")

    with open(workflow_path, "w", encoding="utf-8") as f:
        f.write(GITHUB_ACTION_TEMPLATE)

    return True, f"GitHub Action workflow created at {workflow_path}"
