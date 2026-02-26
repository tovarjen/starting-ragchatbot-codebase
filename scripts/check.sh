#!/usr/bin/env bash
# Run all code quality checks from the project root.
# Usage: ./scripts/check.sh

set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Checking formatting (black)..."
uv run black backend/ main.py --check

echo "==> Running tests (pytest)..."
cd backend
uv run pytest tests/ -q

echo ""
echo "All checks passed."
