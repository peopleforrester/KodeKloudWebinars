#!/usr/bin/env bash
# ABOUTME: Root-level local validation: delegates to each session validator,
# ABOUTME: then runs cross-cutting checks that never touch Agentic_DevOps/.
set -euo pipefail

# Run from the repo root (this script lives in scripts/).
cd "$(dirname "$0")/.."

# Prefer the project venv's tooling when present.
if [[ -d .venv/bin ]]; then
  PATH="$PWD/.venv/bin:$PATH"
  export PATH
fi

shopt -s nullglob
for session_validator in MLOps_Deployment_Workshop/Session_*/scripts/validate-session-*.sh; do
  echo "==> Running $session_validator"
  bash "$session_validator"
done
shopt -u nullglob

echo "==> Cross-cutting checks (excluding Agentic_DevOps/)"
ruff check . --extend-exclude Agentic_DevOps
ruff format --check . --extend-exclude Agentic_DevOps
# Each lambda handler.py is type-checked from its own directory: the hyphenated
# lambda dirs share the basename handler.py and cannot be checked in one process.
for handler_dir in MLOps_Deployment_Workshop/*/lambdas/*/; do
  (cd "$handler_dir" && mypy --strict ./*.py)
done
pytest --cov=MLOps_Deployment_Workshop

echo "==> validate-local.sh: all checks passed"
