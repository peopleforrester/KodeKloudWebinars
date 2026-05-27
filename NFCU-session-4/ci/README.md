# CI

Validation for Session 4 runs through one entry point — the Makefile `validate` target —
which works the same locally and in CI:

```bash
make -C NFCU-session-4 validate
```

It runs: `yamllint`, `markdownlint`, `terraform fmt -check` + `terraform validate`,
`kubectl kustomize build` on the overlays, an offline manifest structural check
(`scripts/check-manifests.py`), `bash -n` on every script, `python -m py_compile`, and
`node --check` on the k6 scripts. Tools that aren't installed are skipped, not failed, so it
runs anywhere; CI installs the full set.

## Enabling the GitHub Actions workflow

`nfcu-session-4-validate.yml` here is a **template**. GitHub only runs workflows from the
repository root `.github/workflows/`, and this build is scoped to `NFCU-session-4/` (it does
not modify the repo root). To activate CI, a maintainer copies the template up:

```bash
mkdir -p .github/workflows
cp NFCU-session-4/ci/nfcu-session-4-validate.yml .github/workflows/
git add .github/workflows/nfcu-session-4-validate.yml && git commit -m "Enable Session 4 CI"
```

The workflow triggers only on changes under `NFCU-session-4/**` and runs `make validate`.

## Why it's a template, not installed

See `../RUN_CONFIG.md`: the run is deliberately confined to `NFCU-session-4/`. Creating a
root `.github/` is a maintainer decision (it affects the whole repo and the other sessions),
so it's deferred rather than done here.
