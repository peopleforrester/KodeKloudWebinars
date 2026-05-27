# Run Configuration — add-nfcu-session-4-kserve-collateral

Adapter notes for executing `OPENSPEC_CHANGE_session-4-kserve-serving.md` in this repo.
The spec is preserved verbatim; this file records how its assumptions map to reality.

## Scope constraint (from maintainer)

All work lands **inside `NFCU-session-4/`**. The repository root is **not** touched
unless a root change is the only way to make progress — in which case the run stops
and asks first. This mirrors the session-3 run model.

## Name / path mapping (do NOT rewrite the spec)

| Spec assumes | Reality | Rule |
|---|---|---|
| `openspec/` at repo root | `NFCU-session-4/openspec/` | Nested under this folder, matching `NFCU-session-2/openspec/`. |
| Root `README.md` gains a Session 4 entry (task 1.3) | **Skipped** | Out of scope: do not touch the repo root. The Session 4 README lives at `NFCU-session-4/README.md`. |
| Root `.github/workflows/nfcu-session-4-validate.yml` (task 12.1) | `NFCU-session-4/.github/workflows/` if used, else Makefile `validate` only | Spec already allows falling back to the Makefile target when no root workflow dir exists. We do not create a root `.github/`. |
| `NFCU-session-4/<subdir>` paths in the spec | Created literally at that path | These already sit under this folder; no rebasing needed. |

The build does **not** create anything at the real `KodeKloudWebinars/` root and does
**not** touch the peer `NFCU-session-1/2/3` or `Agentic_DevOps` directories.

## Spec-deviation log

- **Task 1.3 (root README link):** skipped — scope constraint. The capability spec
  `nfcu-session-4-collateral` requirement "Root README links Session 4" is therefore
  recorded as *deferred to the maintainer* in the archived spec, not satisfied by this run.
- **Task 12.1 (root workflow):** shipped as a copy-ready template at
  `ci/nfcu-session-4-validate.yml` (GitHub only runs workflows from the repo root, which is
  out of scope). The Makefile `validate` target is the portable entry point and passes.
- **Task 13 (archive):** DEFERRED. §6 acceptance gates archival on live-cluster runs (kind
  end-to-end, rehearsal <30 min, kubectl dry-run against the KServe CRDs) that cannot run in
  the authoring environment. Archive after the 2026-06-13 dry run passes (DoD Gate 3): move
  `openspec/changes/add-nfcu-session-4-kserve-collateral/specs/*` into `openspec/specs/`,
  then delete the change directory.

## Tooling available in this environment

terraform 1.15.4 · kubectl v1.36.1 · helm · kind 0.24.0 · docker · python3 ·
yamllint · markdownlint · jq. **Not present:** kustomize (use `kubectl kustomize`),
hadolint, k6. k6 scripts are authored and lint-checked by eye, not executed here;
live-cluster acceptance items (kind `up.sh`, end-to-end rehearsal, `terraform apply`,
multi-arch image build/push) are authored and statically validated only — they
require a real cluster / AWS account / Docker buildx the speaker runs.

## Branch

Work happens on `nfcu-session-4-build` (cut from `main`). Nothing is committed to
`main` directly. Pushing waits for explicit maintainer go-ahead.

## Status

Spec ingested. Implementation in progress — see `PROJECT_STATE.md` for the live
phase checklist.
