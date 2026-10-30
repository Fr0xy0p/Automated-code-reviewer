# 🛡️ Automated Code Reviewer & Complexity Profiler

An intelligent, multi-language developer tool and CI/GitHub Action that inspects your daily code submissions (**Python, C, and C++**), calculates code metrics and asymptotic complexity, generates adversarial edge-case test vectors, and acts as a **tireless AI pair-programmer** to explain *why* corner cases trigger Segmentation Faults, Division by Zero, or Time Limit Exceeded (TLE)—guiding you to the solution without spoiling it.

---

## 🚀 Key Features

* **AST & Static Code Analysis**:
  * **Python**: Abstract Syntax Tree (`ast` module) computing McCabe Cyclomatic Complexity, Cognitive Complexity, loop nesting depth, recursion branching factor, bare `except` detection, mutable defaults, and division by zero risks.
  * **C & C++**: Lexical and structural tokenizer analyzing loop depths, recursion branching, unsafe legacy standard library functions (`gets`, `strcpy`, `strcat`, `sprintf`), raw pointer dereferencing, and dynamic memory leaks (`malloc` without `free`, `new` without `delete`).
* **Big-O Intuition & Complexity Profiler**:
  * Automatically infers asymptotic bounds: $\mathcal{O}(1)$, $\mathcal{O}(\log N)$, $\mathcal{O}(N)$, $\mathcal{O}(N \log N)$, $\mathcal{O}(N^2)$, $\mathcal{O}(N^3)$, and $\mathcal{O}(2^N)$.
  * Predicts operation budgets against competitive programming / production constraints (e.g., $N = 10^5$, CPU budget $1.0\text{s}$, $\approx 10^7 - 10^8\text{ ops/s}$).
  * Highlights asymptotic scale bottlenecks and recommends target Big-O class.
* **Standout Feature: Adversarial Edge-Case Test Vector Generation**:
  * Automatically generates edge-case vectors probing hidden logic errors:
    * **Empty collections**: `[]`, `""`, $0$
    * **Singletons**: `[0]`, `[42]`, `"a"`
    * **Identical duplicates**: `[7, 7, 7, ...]`, `"aaaa"`
    * **Extreme 32-bit signed integer bounds**: `INT32_MIN` ($-2^{31}$), `INT32_MAX` ($2^{31}-1$), $0$, $-1$, $+1$
    * **Sorted & reverse sorted arrays**: tests $\mathcal{O}(N^2)$ worst-case QuickSort pivot traps
    * **Negative number vectors**: tests algorithm initializations (e.g. Kadane's algorithm initializing max to 0 instead of $-\infty$)
    * **Scale stress tests**: tests $N = 2,000$ to $50,000$ to detect TLE and recursion call-stack exhaustion.
* **Sandboxed Execution & Crash Detection**:
  * Runs test vectors in isolated child processes with tight configurable timeouts (default 1.0s).
  * Compiles C/C++ with **AddressSanitizer (ASan)** and **UndefinedBehaviorSanitizer (UBSan)** (`-fsanitize=address,undefined`) to pinpoint heap/stack buffer overflows, use-after-free, and nullptr dereferences.
  * Identifies exact failure classes: `PASS`, `TLE`, `SIGSEGV` (signal 11), `SIGFPE` (division by zero / signal 8), `ASAN_ERROR`, `RECURSION_ERROR`, `INDEX_ERROR`, `ZERO_DIVISION`, and `RUNTIME_ERROR`.
* **AI Pair-Programmer Educational Coaching**:
  * Acts as a senior mentor explaining the machine / hardware and algorithmic root cause.
  * Provides **Socratic guiding questions** rather than giving away code.
  * Formulates invariants and preconditions to maintain.
  * **Dual Engine**: Works out-of-the-box with an **Offline Expert Heuristic Engine** (zero API key / zero dependencies required!) and optionally integrates with **Google Gemini API** (`GEMINI_API_KEY`) for personalized AI coaching.
* **Git Pre-Commit Hook & GitHub Action Pipeline**:
  * One-command installer: `python3 -m codereview.cli hook install`
  * Checks staged files before every commit, blocking commits that fail edge cases or contain critical safety bugs.
  * Generates rich GitHub Action job summaries (`$GITHUB_STEP_SUMMARY`) and Markdown reports.

---

## 📦 Installation & Quickstart

### Prerequisites
* Python 3.8+ (tested on Python 3.14)
* `clang` / `clang++` or `gcc` / `g++` (for C/C++ review)
* `git`

### Installation
You can run the tool directly with zero external dependencies (pure Python standard library), or install it into your environment:

```bash
# Clone or navigate to the repository
cd "Automated Code Reviewer"

# Install as CLI binary (optional)
pip install -e .
```

---

## 🛠️ CLI Usage Guide

### 1. Review a Code File
Inspects AST, calculates complexity, generates edge-case vectors, runs sandbox tests, and provides AI coaching:

```bash
# Review a Python file
python3 -m codereview.cli review examples/python/two_sum_quadratic.py

# Review a C file
python3 -m codereview.cli review examples/c/divide_by_zero.c

# Review a C++ file with AddressSanitizer
python3 -m codereview.cli review examples/cpp/segfault_null_deref.cpp

# Strict mode for Git hooks or CI (exits with code 1 on failure)
python3 -m codereview.cli review examples/python/clean_solution.py --strict

# Export Markdown and JSON reports
python3 -m codereview.cli review examples/python/clean_solution.py -m review.md -j review.json
```

### 2. Big-O Complexity Profiler
Profiles asymptotic scaling against large constraints ($N = 10^3, 10^5, 10^7$):

```bash
python3 -m codereview.cli profile examples/python/two_sum_quadratic.py --scale-n 100000
```
Output:
```text
Asymptotic Scale Limits Check (for N = 100,000):
----------------------------------------------------------------------------
  • Complexity:            O(N^2)
  • Estimated Operations:  10,000,000,000
  • Projected Runtime:     500.0000 seconds
  • TLE Verdict:           🚨 WILL TLE
  • Recommended Big-O:     O(N log N) or O(N)

  Details: For N = 100,000, estimated operations for O(N^2) are ~10,000,000,000. Under a 1.0s limit (20,000,000 ops/sec for python), this takes ~500.00s.
```

### 3. Generate & Inspect Hidden Edge-Case Vectors
Displays the generated adversarial test suite for any function or file:

```bash
python3 -m codereview.cli test-gen examples/python/clean_solution.py
```

### 4. Git Pre-Commit Hook Management
Protect your repository against committing code with segmentation faults, infinite loops, or critical bugs:

```bash
# Install hook into .git/hooks/pre-commit
python3 -m codereview.cli hook install

# Remove hook
python3 -m codereview.cli hook uninstall
```

### 5. Setup GitHub Action CI Workflow
Generates `.github/workflows/code_review.yml`:

```bash
python3 -m codereview.cli init-action
```

### 6. Run CI Across Submissions
Reviews all daily submissions in a directory (e.g. `examples/`):

```bash
python3 -m codereview.cli ci-run --target-dir examples/python --output-markdown ci_report.md
```

---

## 🤖 AI Pair-Programmer Explanations: Example Walkthroughs

### Example A: C++ Segmentation Fault on Empty Vector (`examples/cpp/segfault_null_deref.cpp`)
```text
  Status           Vector Name                        Category     Time (ms) 
----------------------------------------------------------------------------
  [💥 ASAN_ERROR]   Empty Array                        boundary     725.00 ms
  [✓ PASS]         Single Element (Zero)              boundary      90.38 ms
  ...

🤖 AI Pair-Programmer Diagnostic & Socratic Coaching:
▶ Corner Case Crash: Empty Array (ASAN_ERROR) [Offline Expert Heuristic Engine]
  Title: AddressSanitizer Memory Violation
  Root Cause (Machine & Algorithmic Level):
  AddressSanitizer intercepted an out-of-bounds memory read while evaluating 'Empty Array'.
  This indicates that an array index exceeded the allocated buffer bounds. When an empty vector
  is passed, dereferencing nums[0] accesses unallocated memory.

  💡 Guiding Questions to think about:
    • What is the maximum index your loop reaches? Does it reach 'size' on 0-indexed buffers?
    • Did you check if the container has at least 1 element before accessing index 0?

  🛡 Invariant to Maintain:
    Buffer Safety Invariant: 0 <= index < size() must strictly hold.

  👉 Next Step Hint:
    Add a guard check: if (nums.empty()) return 0; before indexing.
```

### Example B: C Division by Zero on Empty Input (`examples/c/divide_by_zero.c`)
```text
  Status           Vector Name                        Category     Time (ms) 
----------------------------------------------------------------------------
  [✗ SIGFPE]       Empty Array                        boundary     566.98 ms
  ...

▶ Corner Case Crash: Empty Array (SIGFPE)
  Title: Division / Modulo by Zero
  Root Cause: Test vector 'Empty Array' attempted arithmetic division by 0.
  At the CPU hardware level, integer division by zero generates an arithmetic trap (SIGFPE).

  💡 Guiding Questions:
    • Could the divisor variable ever evaluate to 0 on boundary inputs (e.g., when length is 0)?
    • How should your function handle cases where the denominator has no valid non-zero value?

  🛡 Invariant to Maintain:
    Arithmetic Precondition: Denominator D != 0 before executing (N / D).
```

---

## 🧪 Automated Test Suite

A comprehensive test suite with 36 unit tests verifies AST parsing, Big-O calculation, edge-case generation, sandboxed execution, and AI explanations:

```bash
python3 -m unittest discover -s tests
```
Output:
```text
....................................
----------------------------------------------------------------------
Ran 36 tests in 5.967s

OK
```

---

## 🏗️ Architecture

```
Automated Code Reviewer/
├── codereview/
│   ├── ast_analyzer/          # Python AST & C/C++ Lexical/Structural Analyzers
│   │   ├── python_analyzer.py # McCabe CC, Cognitive, Loop depth, Bug detectors
│   │   ├── cpp_analyzer.py    # C/C++ memory safety, loops, recursion
│   │   └── base.py            # AnalysisResult & FunctionMetrics models
│   ├── complexity/            # Big-O Asymptotic Engine & Limit Bounds
│   │   ├── big_o.py           # O(1) through O(2^N) inference rules
│   │   ├── metrics.py         # Maintainability Index & Halstead volume
│   │   └── limits.py          # Operation counts & TLE predictions
│   ├── testgen/               # Adversarial Edge-Case Vector Generator
│   │   ├── generator.py       # Empty, bounds, duplicates, scale vectors
│   │   └── types.py           # TestVector data structures
│   ├── runner/                # Sandbox Execution Engine
│   │   ├── python_runner.py   # Isolated Python subprocess runner
│   │   ├── cpp_runner.py      # Clang ASan/UBSan compiler & runner
│   │   └── executor.py        # Status codes: PASS, TLE, SIGSEGV, SIGFPE, ASan
│   ├── ai/                    # AI Pair-Programmer Diagnostic Coaching
│   │   ├── explainer.py       # Unified pair-programming interface
│   │   ├── heuristic_rules.py # Offline Expert Diagnostic Engine (Zero Dependencies)
│   │   └── gemini_client.py   # Google Gemini 2.5 Flash API Client (stdlib urllib)
│   ├── hooks/                 # Git Hooks & CI
│   │   ├── git_hook.py        # Pre-commit hook installer & runner
│   │   └── github_action.py   # GitHub Action workflow generator
│   └── reporting/             # Reporting Layer
│       ├── terminal.py        # ANSI colored terminal interface
│       ├── markdown.py        # GitHub-Flavored Markdown report with badges
│       └── json_reporter.py   # Structured JSON serialization
├── examples/                  # Python, C, and C++ sample submissions
├── tests/                     # 36 Unit tests (100% passing)
├── .github/workflows/         # GitHub Action CI workflow
└── .pre-commit-config.yaml    # pre-commit framework configuration
```

---

## 🔑 Optional Gemini API Configuration

To enable AI Pair-Programmer responses powered by Google Gemini:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

When `GEMINI_API_KEY` is not present, the tool automatically uses its **Offline Expert Heuristic Engine**, ensuring full pair-programmer functionality anywhere, offline or in sandboxed CI environments, with zero errors.

---

## 📄 License
MIT License. Created for Google DeepMind Advanced Agentic Coding.
