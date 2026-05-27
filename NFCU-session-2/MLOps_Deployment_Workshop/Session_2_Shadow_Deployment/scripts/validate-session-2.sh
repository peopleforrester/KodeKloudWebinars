#!/usr/bin/env bash
# ABOUTME: Session 2 local validation — Terraform scanners, lint, types, tests.
# ABOUTME: Mirrors the CI chain; never touches Agentic_DevOps/.
# SPDX-License-Identifier: Apache-2.0
set -euo pipefail

cd "$(dirname "$0")/.." # cd into Session_2_Shadow_Deployment/

# Prefer the repo venv's tooling (ruff, mypy, pytest, checkov) when present.
repo_root=$(cd ../.. && pwd)
if [[ -d "$repo_root/.venv/bin" ]]; then
  PATH="$repo_root/.venv/bin:$PATH"
  export PATH
fi

echo "==> Terraform fmt / validate"
terraform -chdir=terraform init -backend=false -input=false >/dev/null
terraform -chdir=terraform fmt -check -recursive
terraform -chdir=terraform validate

echo "==> Terraform scanners"
tflint --chdir=terraform
tfsec terraform/
checkov -d terraform/ --quiet --compact
# kics ships its query/library assets next to the binary; the CLI defaults to a
# relative ./assets path, so resolve the installed assets explicitly. Only
# HIGH/CRITICAL findings fail the build; lower severities are documented
# lab simplifications.
kics_base="$(dirname "$(readlink -f "$(command -v kics)")")/.."
kics_assets=""
for cand in "$kics_base/share/kics/assets" "$(brew --prefix kics 2>/dev/null)/share/kics/assets"; do
  if [[ -d "$cand/queries" ]]; then
    kics_assets="$cand"
    break
  fi
done
kics scan -p terraform/ -e '**/.terraform/**' --fail-on high,critical \
  ${kics_assets:+-q "$kics_assets/queries" -b "$kics_assets/libraries"} \
  --report-formats json -o /tmp/kics-s2 >/dev/null

echo "==> Python lint / format"
ruff check lambdas/ models/ tests/
ruff format --check lambdas/ models/ tests/

echo "==> Python types"
# Lambda handlers live in hyphenated dirs and all share the basename handler.py,
# so each is type-checked in its own mypy process (from its own directory).
for handler_dir in lambdas/*/; do
  (cd "$handler_dir" && mypy --strict ./*.py)
done
# Models import sibling modules (_dataset/_train); run from the repo root so the
# mypy_path and library-stub overrides in pyproject.toml apply.
(cd "$repo_root" && mypy --strict MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/models)

echo "==> Tests"
pytest tests/

echo "==> Model trainers (dry-run)"
python models/train_champion.py --dry-run
python models/train_challenger.py --dry-run

echo "==> validate-session-2.sh: all checks passed"
