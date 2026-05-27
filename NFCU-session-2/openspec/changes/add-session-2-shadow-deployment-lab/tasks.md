# Tasks

## 1. Repo-Wide Bootstrap (root level, must not touch Agentic_DevOps/)
- [ ] 1.1 Extend `.gitignore` with Python (`__pycache__/`, `*.pyc`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.coverage`, `dist/`, `build/`, `*.egg-info/`, `.venv/`, `venv/`) and Terraform (`.terraform/`, `*.tfstate`, `*.tfstate.*`, `.terraform.lock.hcl` — INCLUDE in commits actually; leave that ONE out of the ignore), and model artifact patterns (`*.joblib`, `*.tar.gz` under `models/`)
- [ ] 1.2 Create root `pyproject.toml` declaring a workspace-style layout where `MLOps_Deployment_Workshop/Session_*/` are packages; pin python ^3.12; add dev-deps: ruff, mypy, pytest, pytest-cov, moto, boto3, scikit-learn, pandas, numpy, pyyaml. Configure ruff with `extend-exclude = ["Agentic_DevOps"]` and mypy with explicit `files` listing only runnable directories
- [ ] 1.3 Create root `Makefile` with targets: `install`, `validate`, `validate-session-2`, `test`, `test-session-2`, `clean`, `train-models-session-2`, `package-models-session-2`
- [ ] 1.4 Create root `.pre-commit-config.yaml` with `exclude: '^Agentic_DevOps/'` at the top, invoking ruff, ruff-format, mypy, terraform fmt, tflint, tfsec, Checkov — each scoped to runnable paths only
- [ ] 1.5 Create root `scripts/validate-local.sh` that delegates to per-session validators and runs cross-cutting checks (see design.md §4.6); chmod +x
- [ ] 1.6 UPDATE root `README.md` to add a new "Available Content" section entry for `MLOps_Deployment_Workshop/` following the same format as the existing Agentic_DevOps entry. Do NOT remove or restructure the existing Agentic_DevOps section.
- [ ] 1.7 UPDATE root `CLAUDE.md` to reflect added stacks. Current content: `**Stack**: Documentation / Markdown`. New content: `**Stack**: Documentation / Markdown + Python (Lambda, scikit-learn) + Terraform (AWS) + GitHub Actions`
- [ ] 1.8 Initialize OpenSpec at the repo root: create `openspec/project.md` (content from Section 1 of this proposal), `openspec/specs/` empty, `openspec/changes/add-session-2-shadow-deployment-lab/` populated from this proposal

## 2. MLOps_Deployment_Workshop Scaffolding
- [ ] 2.1 Create `MLOps_Deployment_Workshop/` with a `README.md` listing the 4 sessions, dates, and current status (Session 2 in development; Sessions 1, 3, 4 TBD via separate proposals)
- [ ] 2.2 Create placeholder directories: `Session_1_Deployment_Pipelines/`, `Session_3_Monitoring_Drift/`, `Session_4_Kubernetes_Serving/` — each with a single `README.md` containing "Separate change proposal. Do not modify." and a link back to the workshop README
- [ ] 2.3 Create `Session_2_Shadow_Deployment/` (empty for now; populated by subsequent tasks)

## 3. Shared Audit Trail Module
- [ ] 3.1 Create `shared/terraform-modules/audit_trail/main.tf` provisioning an S3 bucket `workshop-lab-{attendee_id}-audit` with versioning enabled, AES256 server-side encryption, block-public-access ON
- [ ] 3.2 `shared/terraform-modules/audit_trail/variables.tf` declares: `attendee_id`, `tags`
- [ ] 3.3 `shared/terraform-modules/audit_trail/outputs.tf` exposes: bucket name, bucket ARN
- [ ] 3.4 README in the module flags the lab simplifications: MFA-delete NOT enabled, object-lock NOT enabled, single-actor approval — and lists production controls a real deployment would add
- [ ] 3.5 Apache 2.0 SPDX header on all `.tf` files

## 4. Session 2 Model Training
- [ ] 4.1 Implement `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/models/train_champion.py` — RandomForestClassifier(max_depth=6, n_estimators=100, random_state=42); output `model-v1.0.0.joblib`
- [ ] 4.2 Implement `models/train_challenger.py` — RandomForestClassifier(max_depth=8, n_estimators=150, random_state=42); output `model-v1.0.1.joblib`
- [ ] 4.3 Implement `models/package_model.py` — wraps a joblib model + inference.py into the SageMaker tar.gz format
- [ ] 4.4 Both trainers download UCI Adult from `https://archive.ics.uci.edu/ml/machine-learning-databases/adult/` on first run, cache locally under `models/data/`
- [ ] 4.5 Add `models/verify_agreement.py` — must land 90–94% agreement; also writes the disagreement-region row IDs to a fixed S3 key for the traffic generator
- [ ] 4.6 `models/README.md` documents protected-class fields used and the binary limitation
- [ ] 4.7 Apache 2.0 SPDX header on all `.py` files

## 5. Session 2 Lambda: shadow-mirror
- [ ] 5.1 Implement `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/lambdas/shadow-mirror/handler.py` — reads `CHAMPION_ENDPOINT_ARN`, `CHALLENGER_ENDPOINT_ARN` from env; invokes champion synchronously, challenger asynchronously
- [ ] 5.2 UUID `request_id` propagated everywhere; response includes `endpoint_source: "champion"` and `request_id`
- [ ] 5.3 Shadow-log entry written to `s3://workshop-lab-{attendee-id}-shadow-logs/raw/year=YYYY/month=MM/day=DD/{request_id}.json`
- [ ] 5.4 Challenger failure logged but never raised to caller
- [ ] 5.5 Unit tests in `tests/lambdas/test_shadow_mirror.py` with moto; ≥80% line coverage
- [ ] 5.6 Apache 2.0 SPDX header

## 6. Session 2 Lambda: comparison
- [ ] 6.1 Implement `lambdas/comparison/handler.py` — EventBridge-triggered every 5 min
- [ ] 6.2 Joins champion responses with challenger async output via request_id
- [ ] 6.3 Computes: agreement_rate, latency_p95_champion_ms, latency_p95_challenger_ms, predicted_positive_rate per protected_class group (sex × race)
- [ ] 6.4 Emits CloudWatch metrics: `ShadowAgreementRate`, `ShadowLatencyP95Delta`, `ShadowDisparateImpactRatio` in namespace `Workshop/Session2`
- [ ] 6.5 Reads `config/promotion-criteria.yaml`; evaluates criteria
- [ ] 6.6 Writes `s3://workshop-lab-{attendee-id}-comparison-results/latest.json` + timestamped archive
- [ ] 6.7 Result file contains: `metrics`, `criteria_evaluated`, `promotion_check_status`, `failure_reasons`, `evaluation_window_start`, `evaluation_window_end`
- [ ] 6.8 Unit tests cover all criteria pass/fail combinations
- [ ] 6.9 Apache 2.0 SPDX header

## 7. Session 2 Lambda: traffic-generator
- [ ] 7.1 Implement `lambdas/traffic-generator/handler.py` — invoked manually with `{"duration_minutes": N, "rate": M}`
- [ ] 7.2 Reads UCI Adult test split + disagreement-region IDs from S3
- [ ] 7.3 Sends requests biased 15% toward disagreement region at `rate` req/s for `duration_minutes`
- [ ] 7.4 Returns summary
- [ ] 7.5 Unit tests
- [ ] 7.6 Apache 2.0 SPDX header

## 8. Session 2 Terraform
- [ ] 8.1 `terraform/versions.tf` pins terraform >= 1.6 and `hashicorp/aws` ~> 5.0
- [ ] 8.2 `terraform/variables.tf` declares: `attendee_id`, `aws_region` (default us-east-1), `champion_endpoint_name`, `model_v1_0_1_artifact_s3_uri`, `tags`
- [ ] 8.3 `terraform/main.tf` composes local modules + the shared audit_trail module via `source = "../../../shared/terraform-modules/audit_trail"`
- [ ] 8.4 `terraform/modules/shadow_log_buckets/` — two S3 buckets, versioning, 30-day lifecycle, AES256, block-public-access, tags
- [ ] 8.5 `terraform/modules/shadow_mirror_lambda/` — Lambda python3.12, IAM with InvokeEndpoint + InvokeEndpointAsync + S3 write, API Gateway HTTP API, outputs invoke URL
- [ ] 8.6 `terraform/modules/comparison_lambda/` — Lambda, IAM, EventBridge schedule rate(5 minutes), DLQ
- [ ] 8.7 `terraform/modules/traffic_generator_lambda/` — Lambda, IAM, 5-min timeout, 512 MB
- [ ] 8.8 `terraform/modules/cloudwatch_dashboard/` — three-widget dashboard
- [ ] 8.9 `terraform/main.tf` also provisions the challenger SageMaker endpoint (ml.m5.xlarge)
- [ ] 8.10 All resources carry tags: `Workshop=Session2`, `Attendee={attendee_id}`, `CostCenter=KodeKloud-NFCU`, `AutoTeardown=2026-06-16`
- [ ] 8.11 Run Checkov, tfsec, tflint locally; address findings or document exceptions
- [ ] 8.12 Apache 2.0 SPDX header on all `.tf` files

## 9. GitHub Actions Workflows
- [ ] 9.1 `.github/workflows/session-2-deploy-challenger.yml` — workflow_dispatch with `attendee_id` + push to main path-filtered to `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/**` and `shared/terraform-modules/audit_trail/**`; sets `defaults.run.working-directory`; OIDC AWS auth; runs `terraform apply`; polls `describe-endpoint` (15-min timeout); writes ARN to summary
- [ ] 9.2 `.github/workflows/session-2-promote-challenger.yml` — workflow_dispatch with `attendee_id` + `dry_run: bool`; reads latest comparison result; evaluates; fails if `not_ready`; otherwise (dry_run=false) updates shadow-mirror env vars and writes audit entry
- [ ] 9.3 `.github/workflows/session-2-rollback.yml` — workflow_dispatch with `attendee_id`; reverts env vars; writes audit entry
- [ ] 9.4 Promotion workflow `required-reviewers` auto-approved by `workshop-approver-bot`; document setup in `docs/architecture.md`
- [ ] 9.5 Audit entries at `s3://workshop-lab-{attendee-id}-audit/audit/YYYY-MM-DD/{event-id}.json` with: `event_type`, `timestamp`, `actor`, `previous_champion_endpoint_arn`, `new_champion_endpoint_arn`, `criteria_snapshot`, `workflow_run_url`, `git_commit_sha`
- [ ] 9.6 Each workflow posts the audit entry path to the workflow summary
- [ ] 9.7 `.github/workflows/ci.yml` — multi-session-aware; uses path filters; **explicitly excludes** any path under `Agentic_DevOps/**`; runs root validate-local.sh against changed sessions
- [ ] 9.8 **Path-filter integration test:** open a draft PR touching only `Agentic_DevOps/README.md` and verify NO workflow runs against it (existing Agentic_DevOps PRs must not suddenly start triggering CI)
- [ ] 9.9 **Path-filter integration test:** open a draft PR touching only `MLOps_Deployment_Workshop/Session_3_Monitoring_Drift/README.md` and verify Session 2 workflows do NOT fire

## 10. Promotion Criteria Configuration
- [ ] 10.1 Create `MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/config/promotion-criteria.yaml` matching the schema in Section 7.3
- [ ] 10.2 Ship with defaults:
      - agreement_rate.minimum: 0.85
      - agreement_rate.maximum: 0.99
      - latency_p95_ms.challenger_max: 200
      - latency_p95_ms.delta_vs_champion_max_pct: 20
      - disparate_impact.max_ratio_per_group: 0.80
      - disparate_impact.must_not_be_worse_than_champion: true
      - minimum_observations: 1000
      - minimum_observations_per_protected_group: 100
      - rollback_criteria.post_promotion_accuracy_drop_pct: 5
      - rollback_criteria.post_promotion_error_rate_increase_pct: 50
      - rollback_criteria.evaluation_window_minutes: 60

## 11. Lab Guide and Documentation
- [ ] 11.1 Write `LAB_GUIDE.md` with four lab sections verbatim from the Session 2 source doc timings (Lab 1: 15 min, Lab 2: 12 min, Lab 3: 18 min, Lab 4: 15 min)
- [ ] 11.2 Each lab section: Starting State, Objective, Steps (numbered), Success Criterion, Troubleshooting
- [ ] 11.3 Lab 2 preamble: UCI Adult protected-class binary limitation callout
- [ ] 11.4 Lab 2 debrief: ground-truth-doesn't-arrive-in-production callout
- [ ] 11.5 Lab 4 preamble: auto-approval-bot stands in for human review callout
- [ ] 11.6 Lab 4 preamble: env-var-flip is a lab simplification callout
- [ ] 11.7 `docs/architecture.md` — three patterns (SageMaker Shadow Variants GA re:Invent 2022, Istio mirror / Seldon Core shadow predictor, Lambda fan-out) and why this lab chose fan-out
- [ ] 11.8 `docs/runbook-rollback.md` — when and how to use rollback
- [ ] 11.9 `docs/why-lambda-fanout.md` (200–400 words) explicitly stating SageMaker has native shadow support
- [ ] 11.10 Troubleshooting matrix in `LAB_GUIDE.md` from the source doc
- [ ] 11.11 Session 2 `README.md` — quickstart, prerequisites, links to LAB_GUIDE.md and docs/

## 12. Testing
- [ ] 12.1 `tests/lambdas/test_shadow_mirror.py` — pytest + moto; ≥80% coverage
- [ ] 12.2 `tests/lambdas/test_comparison.py` — pytest with deterministic synthetic shadow-log fixtures
- [ ] 12.3 `tests/lambdas/test_traffic_generator.py` — pytest
- [ ] 12.4 `tests/conftest.py` shared fixtures
- [ ] 12.5 All Terraform modules pass `terraform validate` standalone

## 13. Per-Attendee Provisioning Tooling
- [ ] 13.1 `scripts/provision-attendee.sh {attendee-id}` — runs `terraform apply` for that attendee; returns API Gateway URL and dashboard URL
- [ ] 13.2 `scripts/teardown-attendee.sh {attendee-id}` — destroys everything EXCEPT the audit bucket
- [ ] 13.3 Both idempotent and safe to re-run
- [ ] 13.4 Apache 2.0 SPDX header

## 14. Acceptance Verification (Dry Run)
- [ ] 14.1 Lab engineer dry-run on or before May 30, 2026 completes full attendee flow inside the timing budgets
- [ ] 14.2 Agreement rate lands 90–94%
- [ ] 14.3 Promotion workflow correctly evaluates both pass and fail cases
- [ ] 14.4 Rollback workflow reverts cleanly
- [ ] 14.5 Audit entries contain all required fields
- [ ] 14.6 Per-attendee active-lab cost lands $1.50–$2.50
- [ ] 14.7 PR touching only `Agentic_DevOps/**` triggers ZERO Session 2 workflows
- [ ] 14.8 PR touching only `MLOps_Deployment_Workshop/Session_3_*/` triggers ZERO Session 2 workflows

## Cross-Section Dependencies
- Section 1 (Bootstrap) MUST complete before any other section
- Section 2 (Workshop scaffolding) MUST complete before Sections 4-13
- Section 3 (Shared audit_trail module) MUST complete before Section 8.3 (Terraform references it)
- Section 4 (Model Training) MUST complete before Section 8.9 (Terraform references model_v1_0_1_artifact_s3_uri)
- Section 5 (shadow-mirror Lambda) MUST complete before Section 9.2 (promotion workflow mutates its env vars)
- Section 10 (promotion-criteria.yaml) MUST complete before Section 6.5 (comparison Lambda reads it)
