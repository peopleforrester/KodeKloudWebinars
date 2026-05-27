#!/usr/bin/env bash
# ABOUTME: Static validation harness for the Session 4 collateral. Runs yaml, markdown,
# ABOUTME: terraform, kustomize, shell, and python checks; skips absent tools, fails loud.
set -uo pipefail

# Resolve the session root (parent of this script's dir) regardless of CWD.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT"

FAILED=0
SKIPPED=()

section() { printf '\n\033[1m== %s ==\033[0m\n' "$1"; }
have()    { command -v "$1" >/dev/null 2>&1; }
skip()    { SKIPPED+=("$1"); printf '   (skipped: %s not installed)\n' "$1"; }
fail()    { FAILED=1; printf '\033[31m   FAIL: %s\033[0m\n' "$1"; }

# --- YAML -------------------------------------------------------------------
section "yamllint"
if have yamllint; then
  # Exclude vendored terraform; .disabled reference manifests are not matched.
  mapfile -t YAML_FILES < <(find . -type f \( -name '*.yaml' -o -name '*.yml' \) \
      -not -path '*/.terraform/*' -not -path '*/.git/*')
  if [[ ${#YAML_FILES[@]} -eq 0 ]]; then
    echo "   (no yaml files yet)"
  elif yamllint -c .yamllint "${YAML_FILES[@]}"; then
    echo "   ok"
  else
    fail "yamllint reported errors"
  fi
else
  skip yamllint
fi

# --- Markdown ---------------------------------------------------------------
section "markdownlint"
if have markdownlint; then
  if markdownlint --config .markdownlint.json --ignore-path .markdownlintignore '**/*.md'; then
    echo "   ok"
  else
    fail "markdownlint reported errors"
  fi
else
  skip markdownlint
fi

# --- Terraform --------------------------------------------------------------
section "terraform fmt + validate"
if have terraform; then
  TF_DIR="cluster/eks/terraform"
  if [[ -d "$TF_DIR" ]]; then
    if ! terraform -chdir="$TF_DIR" fmt -check -recursive; then
      fail "terraform fmt -check (run 'terraform -chdir=$TF_DIR fmt')"
    fi
    if terraform -chdir="$TF_DIR" init -backend=false -input=false >/dev/null 2>&1; then
      if terraform -chdir="$TF_DIR" validate; then
        echo "   ok"
      else
        fail "terraform validate"
      fi
    else
      echo "   (init -backend=false failed offline; fmt checked only)"
    fi
  fi
else
  skip terraform
fi

# --- Kustomize overlays -----------------------------------------------------
section "kustomize build"
KUSTOMIZE_CMD=""
if have kustomize; then KUSTOMIZE_CMD="kustomize build"
elif have kubectl; then KUSTOMIZE_CMD="kubectl kustomize"; fi
if [[ -n "$KUSTOMIZE_CMD" ]]; then
  for k in cluster/lab-overlays/base cluster/lab-overlays/overlays/attendee-sample; do
    if [[ -d "$k" ]]; then
      if $KUSTOMIZE_CMD "$k" >/dev/null; then
        echo "   ok: $k"
      else
        fail "kustomize build $k"
      fi
    fi
  done
else
  skip "kustomize/kubectl"
fi

# --- Manifests (structural; offline substitute for kubectl dry-run) ---------
section "manifest structure"
if have python3 && [[ -d manifests ]]; then
  if python3 scripts/check-manifests.py; then :; else fail "manifest structure"; fi
else
  echo "   (no manifests dir or python3)"
fi

# --- Shell scripts ----------------------------------------------------------
section "bash -n (syntax)"
while IFS= read -r f; do
  if bash -n "$f"; then :; else fail "bash -n $f"; fi
done < <(find . -type f -name '*.sh' -not -path '*/.terraform/*' -not -path '*/.git/*')
echo "   ok"

# --- Python -----------------------------------------------------------------
section "python compile"
if have python3; then
  while IFS= read -r f; do
    if python3 -m py_compile "$f"; then :; else fail "py_compile $f"; fi
  done < <(find . -type f -name '*.py' -not -path '*/.terraform/*' -not -path '*/.git/*')
  echo "   ok"
else
  skip python3
fi

# --- k6 / JavaScript syntax -------------------------------------------------
section "javascript syntax (node --check)"
if have node; then
  found=0
  while IFS= read -r f; do
    found=1
    if node --check "$f"; then :; else fail "node --check $f"; fi
  done < <(find . -type f -name '*.js' -not -path '*/.terraform/*' -not -path '*/.git/*' -not -path '*/node_modules/*')
  [[ "$found" == "1" ]] && echo "   ok" || echo "   (no js files)"
else
  skip "node (k6 scripts not parse-checked)"
fi

# --- Tools we cannot run here ----------------------------------------------
section "advisory (not run here)"
have hadolint || skip "hadolint (Dockerfile lint)"
have k6       || skip "k6 (load scripts authored, not executed)"

# --- Summary ----------------------------------------------------------------
section "summary"
if [[ ${#SKIPPED[@]} -gt 0 ]]; then
  printf 'Skipped (not installed): %s\n' "${SKIPPED[*]}"
fi
if [[ "$FAILED" -ne 0 ]]; then
  printf '\033[31mVALIDATION FAILED\033[0m\n'
  exit 1
fi
printf '\033[32mVALIDATION PASSED\033[0m\n'
