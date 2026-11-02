#!/usr/bin/env bash
# Installation script for Automated Code Reviewer & Complexity Profiler
# Installs 'codereview' and 'code-profiler' directly into your user bin directory.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

echo "======================================================================"
echo "🚀 Installing Automated Code Reviewer & Complexity Profiler..."
echo "======================================================================"

# Ensure ~/.local/bin exists
mkdir -p "$BIN_DIR"

# Ensure the launcher in ./bin/codereview is executable
chmod +x "$REPO_DIR/bin/codereview"

# Create symlinks in ~/.local/bin
ln -sf "$REPO_DIR/bin/codereview" "$BIN_DIR/codereview"
ln -sf "$REPO_DIR/bin/codereview" "$BIN_DIR/code-profiler"

echo "✅ Linked 'codereview' -> $BIN_DIR/codereview"
echo "✅ Linked 'code-profiler' -> $BIN_DIR/code-profiler"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "⚠️  Note: $BIN_DIR is not yet in your PATH."
    echo "To access 'codereview' from anywhere, add this line to your ~/.zshrc or ~/.bashrc:"
    echo '  export PATH="$HOME/.local/bin:$PATH"'
    echo "Then run: source ~/.zshrc"
else
    echo "✅ $BIN_DIR is already in your PATH!"
fi

echo ""
echo "🎉 Installation complete! You can now run:"
echo "    codereview review examples/python/clean_solution.py"
echo "    code-profiler profile examples/python/two_sum_quadratic.py"
echo "======================================================================"

