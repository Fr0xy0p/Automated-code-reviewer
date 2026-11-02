#!/usr/bin/env bash
# Uninstallation script for Automated Code Reviewer & Complexity Profiler

set -e

BIN_DIR="$HOME/.local/bin"

echo "Removing codereview links from $BIN_DIR..."
rm -f "$BIN_DIR/codereview"
rm -f "$BIN_DIR/code-profiler"

echo "✅ Uninstalled 'codereview' and 'code-profiler'."

