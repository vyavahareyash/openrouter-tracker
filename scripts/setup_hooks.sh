#!/usr/bin/env bash
# Configure git to use local .githooks directory

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

chmod +x .githooks/pre-commit .githooks/pre-push 2>/dev/null || true
git config core.hooksPath .githooks

echo "✅ Git hooks configured to .githooks/ successfully."
