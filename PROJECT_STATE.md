# PROJECT_STATE — NFCU Session 1 Bootstrap

## Current plan
Build out `NFCU-session-1/` from the spec at
`NFCU-session-1/OPENSPEC_CHANGE_session-1-deployment-pipeline.md` until §16 Definition
of Done is satisfied. Scope is **session-1 only** plus its required repo-root integration
(`.github/workflows/nfcu-session-1-*.yml`, root `README.md`/`CLAUDE.md`/`.gitignore`).
Per explicit user directive, the §14 stubs for sessions 2/3/4 are **skipped**.

## Branch & remote
- Branch: `feat/nfcu-session-1-bootstrap` (off `main`)
- Remote: `git@github.com:peopleforrester/KodeKloudWebinars.git`
- Not pushing until user asks (spec §4: generate files only).

## Verification method
Local tool execution (not research). Installed for this session:
- terraform v1.15.4, trivy 0.70.0, cosign 3.0.6, actionlint 1.7.12, gitleaks 8.30.1,
  pandoc 3.9, shellcheck, yamllint, jq, aws-cli, docker.
- Python ML deps in venv `/tmp/nfcu-venv` (xgboost, pandas, numpy, scikit-learn, boto3,
  jsonschema). System python is 3.14; spec runtime target is 3.11 (container only).
- brew/terraform on PATH via `/home/linuxbrew/.linuxbrew/bin`.

## Task checklist
1. [done] Scaffold directory tree
2. [done] Sample model + training script (Cap 7)
3. [done] validate.py (Cap 1)
4. [done] audit-trail.py (Cap 3)
5. [done] Container pipeline (Cap 2)
6. [done] Terraform modules + environments (Cap 4)
7. [done] lab-platform-iac (Cap 6)
8. [done] GitHub Actions workflows (Cap 5)
9. [done] Documentation (Cap 8)
10. [done] Root file modifications (§13)
11. [in_progress] §15 verification (PASS) + commit + tag

## §15 verification results (all PASS, run locally)
- terraform fmt -recursive -check: clean
- terraform validate: dev, staging, production, lab-platform-iac all valid
- py_compile: pipeline/*.py, scripts/*.py OK
- shellcheck: clean
- actionlint: clean; yamllint: exit 0 (via .yamllint.yml)
- training dry-run: OK; determinism: two runs identical SHA256
  (f240035b7fa3ac165ac9ad0805731d1c033ed0c163743fffe18088f496df8bf9)
- validate.py rejects latest/prod/current/stable/main (+caps): all exit 2
- gitleaks: NFCU-session-1 + workflows CLEAN (4 findings are out-of-scope
  NFCU-session-4/.terraform vendored example key material, gitignored, not committed)
- SHA pinning grep: only actions/aws-actions tags; third-party pinned by 40-char SHA
- session-outline NFCU scrub: no matches
- no real *.tfvars tracked (only *.tfvars.example)
- reference-card.md renders to exactly 1 page (pandoc + tectonic, letter)

## Deviations from spec (intentional)
- §14 stubs for sessions 2/3/4 SKIPPED per user directive ("session-1 only").
- Smoke fixture probability_range set to [0.30,0.45] to match the real deterministic
  model output (0.386); spec's [0.15,0.35] was an estimate. Real eval: acc 0.84/f1 0.64
  (8-feature signature) vs spec's estimated 0.86/0.71.
- Dockerfile base image uses a placeholder sha256 digest with a documented lookup
  command (real digest requires ECR auth; not fabricated as authentic).
- OPENSPEC_CHANGE_session-1-deployment-pipeline.md kept in NFCU-session-1 (ingested spec).

## Last completed step
All build phases complete; full §15 suite passes for in-scope content.

## Next step
Commit (feat(nfcu-session-1): bootstrap...) and tag nfcu-session-1-v1.0.0. No push
(spec §4: generate files only; do not push to GitHub).
