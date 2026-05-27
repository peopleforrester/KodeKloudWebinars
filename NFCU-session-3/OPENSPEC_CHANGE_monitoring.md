# OpenSpec Change: `monitoring` (NFCU Session 3)

> **Status:** Draft, ready for implementation
> **Authoritative source:** Session 3 — Keeping 100+ Models Healthy, v2.1 (May 14, 2026)
> **Target session date:** June 16, 2026, 10:00 AM – 12:00 PM ET
> **Lab build deadline (Definition of Done):** June 6, 2026 (10 business days pre-session)
> **Owner:** Michael Forrester (Performant Pro)
> **Implementation tool:** Claude Code via `/goal`
> **Repo:** `github.com/peopleforrester/KodeKloudWebinars`
> **Session folder:** `NFCU-session-3/` (peer to existing `Agentic_DevOps/`)
> **OpenSpec change folder:** `NFCU-session-3/openspec/changes/monitoring/`

This is a single OpenSpec change document containing all four artifacts (`proposal.md`, `design.md`, `tasks.md`, and spec deltas). Claude Code should treat the sections below as if they were the individual files inside `NFCU-session-3/openspec/changes/monitoring/`. All build outputs land inside `NFCU-session-3/`, with one unavoidable exception for GitHub Actions workflows (which must live at `.github/workflows/` at the repo root).

When implementing:
- Read **§1 Proposal** for intent and scope before writing anything.
- Read **§2 Design** for the technical approach and the session folder layout.
- Execute **§3 Tasks** in order, checking each box only when its acceptance criterion holds.
- Validate the final state against **§4 Spec Deltas** (EARS-format requirements). Every scenario must be demonstrable.
- Honor the **§5 Definition of Done** gates before declaring complete.

---

## §1. Proposal

### Intent

Build the complete lab environment for NFCU Session 3 of the MLOps Learning Sessions: a 2-hour live workshop on monitoring deployed ML models, detecting drift across three drift types, integrating Evidently AI and NannyML, and executing runbooks against simulated production incidents. The lab supports up to 30 concurrent attendees in a per-attendee AWS sandbox.

The session exists because traditional infrastructure monitoring does not catch the "silent wrongness" failure mode — a model returning HTTP 200 with sub-millisecond latency while producing wrong predictions for weeks. Every artifact in this build strengthens an attendee's ability to detect that class of failure.

### What's changing

This change builds the `NFCU-session-3/` subtree inside the existing `KodeKloudWebinars` repo:

- All Session 3 source under `NFCU-session-3/` (Lambdas, monitoring, infra, runbooks, scripts, tests, session-local shared assets, and OpenSpec).
- A session-scoped GitHub Actions workflow at `.github/workflows/nfcu-session-3-deploy-monitoring.yml` — the only file landing outside the session folder, required by GitHub Actions' fixed workflow location.

No code outside `NFCU-session-3/**` or `.github/workflows/nfcu-session-3-*.yml` is modified. The existing `Agentic_DevOps/` content is untouched. Sessions 1, 2, and 4 (when they land) sit as peers; this change does not assume they exist.

This change also creates a convention shift for the repo: `KodeKloudWebinars` was doc-only (markdown + .pptx) before this change. After this change, it contains executable code (Python Lambdas, Dockerfiles, Terraform, shell scripts). The repo-root `CLAUDE.md` line "Stack: Documentation / Markdown" should be updated to reflect this, but that update is governed by a separate change, not this one.

### What's explicitly out of scope

- NFCU Sessions 1, 2, 4 builds. The Session 1/2 SageMaker endpoint is treated as an external dependency; `NFCU-session-3/scripts/restore-session2-endpoint.sh` provides the recovery path if it's torn down. The baseline model artifact lives inside `NFCU-session-3/shared/` as a session-owned copy, so Session 3 is self-recoverable without depending on Session 1 being built.
- Real PagerDuty/Slack paging. SNS topics are visible in the dashboard but do not page external systems.
- LLM-specific monitoring. Covered as a verbal aside in the session, not implemented.
- Long-horizon concept drift. The incident simulator's "concept drift confirmed" scenario is time-compressed; the runbook for it documents that compression explicitly.
- Multi-cloud or Kubernetes deployment. Session 4 covers KServe; this session stays AWS-native.
- The Session 3 slide deck (`.pptx`). Michael authors that separately and drops it into `NFCU-session-3/` per the `Agentic_DevOps/` convention.
- Updates to the repo-root `README.md`, `CLAUDE.md`, or `.gitignore`. Those are governed by a separate change.

### Impact

- **Attendees**: 30 DevOps/Platform/SRE engineers leave with monitoring instrumentation on a live production endpoint, drift detection that fires on real drift, an Evidently report rendered in their browser, a NannyML CBPE estimate, and a documented routing decision on a simulated incident.
- **Lab engineers**: A per-attendee provisioning pipeline costing $0.40–$0.80 per attendee in Session 3-specific resources. Standing infrastructure (Sessions 1/2 endpoints carrying through to June 18) is tracked separately.
- **NFCU stakeholders (Lovely, Keetra)**: A self-contained `NFCU-session-3/` folder they can review independently, with the runbook templates being directly usable as a starting point for NFCU's own ML on-call rotation.
- **Series continuity**: Session 4 (June 18, KServe) can reference the runbook templates and Evidently/NannyML patterns. Sandboxes preserved through June 18.

### Why now

Session is on the calendar for June 16, 2026. Lab build must be complete by June 6 for the dry-run window. Evidently pin re-verification must happen no later than June 9.

---

## §2. Design

### Architecture overview

Per-attendee resources sit inside a lab-platform-managed AWS sandbox. The Session 1/2 SageMaker endpoint (`workshop-lab-{attendee-id}-production`, `ml.m5.xlarge`, UCI Adult binary classifier) is the monitoring target. Session 3 layers monitoring, drift detection, and incident simulation on top of it.

```
                         ┌──────────────────────────────────────────────┐
                         │  Attendee AWS sandbox (per-attendee)         │
                         │                                              │
   prod traffic ─────►   │  SageMaker endpoint ─────► CloudWatch        │
   (synthetic)           │  (from Session 1/2)        (native metrics)  │
                         │         │                       │            │
                         │         ▼                       │            │
                         │  prediction logs ──► S3         │            │
                         │  (shadow-logs)        │         │            │
                         │                       ▼         ▼            │
                         │              ┌─────────────────────────┐     │
                         │  every 2min →│  drift-detector Lambda  │──► CW metrics
                         │              │  (PSI per feature)      │    + alarm
                         │              └─────────────────────────┘     │
                         │                       │                      │
                         │  reference.parquet ◄──┘                      │
                         │  (S3, captured S1/S2 traffic)                │
                         │                                              │
                         │  manual invoke:                              │
                         │   • evidently-runner ────► S3 HTML report    │
                         │   • nannyml-runner  ────► JSON (est. AUC)    │
                         │   • drift-simulator ────► endpoint traffic   │
                         │   • incident-simulator ──► one of 5 scenarios│
                         │                                              │
                         │  CloudWatch dashboard (2 rows: infra + ML)   │
                         │  3 alarms → SNS topic (visible, not paging)  │
                         └──────────────────────────────────────────────┘
```

### Session folder layout

Everything for Session 3 lives under `NFCU-session-3/` at the repo root, peer to the existing `Agentic_DevOps/`. The only exception is the GitHub Actions workflow (must live at `.github/workflows/` per GitHub's fixed convention).

```
KodeKloudWebinars/                                  # Existing repo root
├── Agentic_DevOps/                                 # Existing — not modified
├── .github/
│   └── workflows/
│       └── nfcu-session-3-deploy-monitoring.yml    # Per-attendee provisioning (only file outside the session folder)
├── NFCU-session-1/                                 # Peer (not modified; may not exist yet)
├── NFCU-session-2/                                 # Peer (not modified; may not exist yet)
├── NFCU-session-3/                                 # <-- THIS BUILD
│   ├── README.md                                   # Session overview, role-based starting points
│   ├── LAB_GUIDE.md                                # Lab engineer reference
│   ├── pyproject.toml                              # Session-scoped Python project
│   ├── resources.md                                # External reading list (Agentic_DevOps convention)
│   ├── openspec/
│   │   ├── project.md                              # Project context for OpenSpec/AGENTS
│   │   ├── specs/                                  # Session-3 source of truth
│   │   │   └── (populated when changes archive)
│   │   └── changes/
│   │       └── monitoring/
│   │           ├── proposal.md                     # §1 of this doc
│   │           ├── design.md                       # §2 of this doc
│   │           ├── tasks.md                        # §3 of this doc
│   │           └── specs/                          # Delta specs by domain (§4)
│   │               ├── monitoring/spec.md
│   │               ├── drift-detection/spec.md
│   │               ├── drift-reporting/spec.md
│   │               ├── performance-estimation/spec.md
│   │               ├── incident-simulation/spec.md
│   │               ├── runbooks/spec.md
│   │               ├── endpoint-recovery/spec.md
│   │               └── lab-platform/spec.md
│   ├── lambdas/
│   │   ├── drift-detector/                         # Python, zip package
│   │   │   ├── handler.py
│   │   │   ├── psi.py
│   │   │   └── requirements.txt
│   │   ├── evidently-runner/                       # Python, container image
│   │   │   ├── Dockerfile
│   │   │   ├── handler.py
│   │   │   ├── requirements.txt                    # evidently==0.7.21 (re-verify Jun 9)
│   │   │   └── PIN_VERIFICATION.md
│   │   ├── nannyml-runner/                         # Python, container image
│   │   │   ├── Dockerfile
│   │   │   ├── handler.py
│   │   │   ├── requirements.txt                    # nannyml latest stable (re-verify Jun 9)
│   │   │   └── PIN_VERIFICATION.md
│   │   ├── drift-simulator/                        # Python, zip package
│   │   │   ├── handler.py
│   │   │   └── requirements.txt
│   │   └── incident-simulator/                     # Python, zip package
│   │       ├── handler.py
│   │       ├── scenarios/
│   │       │   ├── feature_pipeline_broken.py
│   │       │   ├── data_drift.py
│   │       │   ├── prediction_drift_isolated.py
│   │       │   ├── latency_degradation.py
│   │       │   └── concept_drift_confirmed.py
│   │       └── requirements.txt
│   ├── monitoring/
│   │   ├── dashboard.json                          # CloudWatch dashboard, 2 rows
│   │   ├── alarms.tf                               # 3 alarms + SNS topic
│   │   └── variables.tf
│   ├── infra/
│   │   ├── per-attendee.tf                         # S3 buckets, IAM, EventBridge schedule
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── runbooks/
│   │   ├── runbook-template.md
│   │   ├── feature-pipeline-broken.md
│   │   ├── data-drift.md
│   │   ├── prediction-drift-isolated.md
│   │   ├── latency-degradation.md
│   │   └── concept-drift-confirmed.md
│   ├── scripts/
│   │   ├── restore-session2-endpoint.sh            # ≤4 min, idempotent
│   │   ├── capture-reference-distribution.py
│   │   └── verify-lab-readiness.sh
│   ├── shared/                                     # Session-local shared assets (NOT cross-session)
│   │   ├── baseline-models/
│   │   │   └── session-1-2-uci-adult/
│   │   │       ├── model.tar.gz                    # Baseline artifact for restore script
│   │   │       └── README.md
│   │   └── fixtures/
│   │       └── uci-adult/                          # Local copy of test split
│   └── tests/
│       ├── test_psi.py
│       ├── test_drift_simulator.py
│       ├── test_incident_simulator_round_robin.py
│       ├── test_evidently_handler.py               # Mocked S3, validates 0.7.x API
│       ├── timing_results.md                       # Dry-run timing measurements
│       ├── scenario_dry_run.md                     # Per-scenario verification
│       └── dry_run_results.md                      # Full end-to-end dry-run
└── NFCU-session-4/                                 # Peer (future, KServe — not modified)
```

### Path conventions

All paths in tasks and spec deltas below are **relative to the repo root** (`KodeKloudWebinars/`). When a task or scenario references a file path, that path is the full path from the repo root. For example: `NFCU-session-3/lambdas/drift-detector/handler.py`.

### Session self-containment principle

NFCU Session 3 is **self-contained**. It does not assume Sessions 1, 2, or 4 have been built. Specifically:

- The baseline model artifact lives at `NFCU-session-3/shared/baseline-models/session-1-2-uci-adult/`, not at a repo-root `shared/` folder. This is a Session 3-owned copy so the restore script works even if Session 1 hasn't been built.
- The UCI Adult test fixtures live at `NFCU-session-3/shared/fixtures/uci-adult/`. Session 3 ships its own copy.
- Session 4, when built, can choose to either copy these assets into its own `NFCU-session-4/shared/` or reference Session 3's paths. That's Session 4's call, not Session 3's.
- The OpenSpec directory is at `NFCU-session-3/openspec/`, not at the repo root. Each session has its own OpenSpec. If a future change spans sessions, it would warrant a repo-root OpenSpec, but no such change exists today.

### Key design decisions

#### D1. Evidently pin and API style
The v2.1 doc pins `evidently==0.7.21` using the 0.7.x API: `from evidently import Report`, `from evidently.presets import DataDriftPreset, DataQualityPreset`, `Dataset(..., data_definition=...)`, `report.run(current, reference)`. **The pin must be re-verified on PyPI no earlier than June 9, 2026 and no later than June 11.** If a stable 0.7.22+ is available, bump and re-test against fixture data. If 0.8.x is available, do not auto-bump — Michael reviews. Pin in `NFCU-session-3/lambdas/evidently-runner/requirements.txt` with rationale in adjacent `PIN_VERIFICATION.md`.

#### D2. Lambda packaging strategy
- **Zip package** (smaller surface, faster cold start): `drift-detector`, `drift-simulator`, `incident-simulator`. No heavy dependencies.
- **Container image** (clean dependency management, larger memory): `evidently-runner` (1024MB), `nannyml-runner` (1024MB). Both pull in pandas, plotly, scipy.

#### D3. Drift detector alarm transition (workshop shortcut)
`drift-detector` calls `cloudwatch:SetAlarmState` to force `Drift-PSI-{attendee_id}` into `ALARM` state when any feature PSI > 0.25. Workshop-only shortcut for fast visual feedback within the 12-minute Lab 1 window. **Must be flagged in a code comment in `NFCU-session-3/lambdas/drift-detector/handler.py` as workshop-only, not production practice.**

#### D4. Round-robin incident assignment (not random)
The lab platform assigns one of 5 scenarios per attendee in round-robin order. With N=30, random distribution produces skewed coverage that breaks the Slide 18 debrief. Round-robin guarantees ~6 of each scenario.

#### D5. UCI Adult dataset — preserve and acknowledge
Session 1/2's model classifies UCI Adult income (binary). Dataset is academically dated (Ding et al., "Retiring Adult", NeurIPS 2021 recommends folktables/ACSIncome). Preserved for continuity; lab guide and Slide 5 speaker notes frame UCI Adult as a stand-in for any production binary classifier. Local fixtures at `NFCU-session-3/shared/fixtures/uci-adult/`.

#### D6. Concept drift time compression
Real concept drift in lending/fraud manifests over months as ground truth returns. The lab compresses this into a 15-minute scenario by pushing labels showing a 20% accuracy drop. `NFCU-session-3/runbooks/concept-drift-confirmed.md` must explicitly call this compression out so attendees do not generalize lab timing to real-world response windows. This is doubly important for NFCU's regulated FS context where audit reviewers may read these runbooks.

#### D7. Reference distribution capture
`NFCU-session-3/scripts/capture-reference-distribution.py` is run **once** during lab build (not per-attendee, not at session time) against clean Session 1/2 traffic. Produces `reference.parquet` with feature distributions for all 8 input features. Uploaded to each attendee's `workshop-lab-{attendee_id}-baseline` bucket during per-attendee provisioning.

#### D8. Restore script idempotency and timing
`NFCU-session-3/scripts/restore-session2-endpoint.sh` must:
- Detect existing healthy endpoint and exit fast (no-op if InService).
- Provision a baseline endpoint from `NFCU-session-3/shared/baseline-models/session-1-2-uci-adult/model.tar.gz` (uploaded to a shared S3 bucket; see Open Question 3) if the endpoint is missing or unhealthy.
- Complete in ≤ 4 minutes wall-clock, end-to-end.
- Be idempotent.

#### D9. Drift simulator parameters and Lab 2 timing
Drift simulator transforms `hours_per_week` with `+ Normal(15, 5)` clipped to `[0, 100]`. Sends 10 req/s for 5 min. Drift detector runs every 2 min against a 5-min rolling window, so PSI on `hours_per_week` should cross 0.25 within 4–6 minutes.

**Tuning fallback** if dry-run shows PSI not crossing 0.25 within 5 minutes — adjust **one** knob (smallest-blast-radius first):
1. EventBridge schedule: 2 min → 1 min during lab window only.
2. Drift simulator shift magnitude: mean +15 → +25 hours.
3. Detector reference window: 5 min → 3 min.

#### D10. NannyML CBPE pedagogical anchor
Lab 3 Part 2 is short (~5 min) but is where the concept-drift insight lands. If NannyML's AUC delta between baseline and drifted windows is < 0.01 absolute, the lesson falls flat. Dry-run **must** measure delta on actual fixture data; if too small, apply D9 option 2 before session day.

#### D11. Touch boundary
This change touches only:
- `NFCU-session-3/**`
- `.github/workflows/nfcu-session-3-deploy-monitoring.yml`

No files in `Agentic_DevOps/`, `NFCU-session-1/`, `NFCU-session-2/`, `NFCU-session-4/`, repo-root `README.md`, repo-root `CLAUDE.md`, repo-root `.gitignore`, or `LICENSE` are modified. If `NFCU-session-3/` has remnants from a prior partial build, this change overwrites them; if peer NFCU-session-N folders exist, they are not touched.

#### D12. NFCU branding and audience framing
Speaker narrative in the v2.1 doc references "regulated FS audiences" and "lending, fraud chargebacks". Runbook content and the LAB_GUIDE should be framed in language NFCU's audit and model-risk reviewers will recognize (PSI, model risk frameworks, NCUA/FFIEC alignment) without making fabricated regulatory claims. Specifically:
- Do not claim NCUA or FFIEC compliance — these monitoring patterns *align with* model risk principles but are not a compliance attestation.
- Do not reference NFCU as a "bank" anywhere in the materials.
- PSI thresholds and runbook routing language should match what an NFCU model risk reviewer would expect to see.

### Dependencies

| Dependency | Source | Status |
|---|---|---|
| Session 1/2 SageMaker endpoint | Lab platform sandbox, preserved through June 18 | Verify pre-session |
| Session 1/2 model artifact | `NFCU-session-3/shared/baseline-models/session-1-2-uci-adult/` + shared S3 | Build/upload before June 2 |
| UCI Adult dataset | `NFCU-session-3/shared/fixtures/uci-adult/` | Reuse or copy in |
| `evidently==0.7.21` | PyPI | Re-verify June 9 |
| `nannyml` (latest stable) | PyPI | Re-verify June 9 |
| Terraform ≥ 1.6 | Lab platform | Already present |
| AWS region `us-east-1` | Lab platform sandbox provisioning | Standard |

### Cost envelope

- **Session 3-specific per attendee**: $0.40–$0.80 (Lambdas + CloudWatch + drift-reports S3).
- **Session 3-specific total at 30 attendees**: $12–$24.
- **Standing endpoint carry cost** (NOT Session 3's scope; tracked separately): Sessions 1/2 endpoints InService June 2 → June 18 at `ml.m5.xlarge` ($0.22/hr) per attendee, ~$84 per attendee × 30 ≈ $2,500 across the series window.

---

## §3. Tasks

Execute in order. Each task has an acceptance criterion. Do not check the box until the criterion holds. All paths are relative to the repo root `KodeKloudWebinars/`.

### Phase 1: Repository scaffold under `NFCU-session-3/` (by May 30)

- [ ] **1.1 Verify repo presence and create `NFCU-session-3/` subtree.** Clone `github.com/peopleforrester/KodeKloudWebinars` if not already local. Create the `NFCU-session-3/` directory tree as shown in §2 Session Folder Layout. Do not modify `Agentic_DevOps/` or any other peer directory. Acceptance: `tree -L 3 NFCU-session-3/` matches §2 exactly; `git status` shows no changes in `Agentic_DevOps/` or repo-root files.
- [ ] **1.2 Create `NFCU-session-3/openspec/changes/monitoring/` and populate** with `proposal.md` (§1 of this doc), `design.md` (§2), `tasks.md` (§3), and the eight delta spec files under `specs/` (§4, one file per domain). Also create `NFCU-session-3/openspec/project.md` with a brief description (session purpose, stack, conventions). Acceptance: file structure matches diagram in §2; if OpenSpec CLI is installed, `openspec validate monitoring --strict` (run from `NFCU-session-3/`) passes.
- [ ] **1.3 Write `NFCU-session-3/README.md`** explaining the session, the lab structure, and pointers to `LAB_GUIDE.md` and the OpenSpec. Follow the role-based-starting-points pattern from `Agentic_DevOps/README.md`. Acceptance: a new lab engineer can find Lab 1 setup instructions in ≤ 60 seconds.
- [ ] **1.4 Write `NFCU-session-3/resources.md`** as a placeholder for the external reading list (per `Agentic_DevOps/resources.md` convention). Include 3–5 starter references: the v2.1 session doc itself, Evidently docs, NannyML docs, the Ding et al. "Retiring Adult" paper, and a PSI primer. Acceptance: file exists and renders cleanly in GitHub markdown.
- [ ] **1.5 Set up `NFCU-session-3/pyproject.toml`** for Python 3.11 with pinned dev deps (`boto3`, `pandas`, `pyarrow`, `pytest`, `moto` for S3/CloudWatch mocking). Acceptance: `cd NFCU-session-3 && pytest tests/` runs and reports zero tests collected (passes vacuously).
- [ ] **1.6 Write `.github/workflows/nfcu-session-3-deploy-monitoring.yml`** that provisions dashboard + alarms via Terraform under `NFCU-session-3/monitoring/` and `NFCU-session-3/infra/`, parameterized on `attendee_id`. Triggered manually (workflow_dispatch) or via repository_dispatch. Acceptance: workflow file lints clean with `actionlint`; workflow is the only modification outside `NFCU-session-3/`.
- [ ] **1.7 Reference distribution capture script** at `NFCU-session-3/scripts/capture-reference-distribution.py`. Reads clean Session 1/2 prediction logs from a configurable S3 path; computes per-feature distribution snapshot; writes `reference.parquet` with ≥ 1000 rows. Acceptance: script run against fixture data produces a parquet file readable by pandas with 8 feature columns and ≥ 1000 rows.

### Phase 2: Drift detector and PSI math (by May 31)

- [ ] **2.1 Implement `NFCU-session-3/lambdas/drift-detector/psi.py`** with `compute_psi(reference: pd.Series, current: pd.Series, bins: int = 10) -> float`. Per-feature PSI; not aggregate. Acceptance: `NFCU-session-3/tests/test_psi.py` covers (a) identical distributions → PSI ≈ 0, (b) heavily shifted → PSI > 0.25, (c) zero-count bin edge case (small epsilon).
- [ ] **2.2 Implement `NFCU-session-3/lambdas/drift-detector/handler.py`.** EventBridge trigger every 2 min. Read shadow-logs S3 bucket for last 5 min of predictions. Read `reference.parquet` from baseline bucket. Compute PSI for all 8 features. Emit `DriftPSI/{feature}` CloudWatch custom metric per feature. If any PSI > 0.25, call `cloudwatch:SetAlarmState` on `Drift-PSI-{attendee_id}` with state `ALARM`. Code comment marks D3 shortcut as workshop-only. Acceptance: integration test with `moto`-mocked S3 + CloudWatch confirms per-feature metric emission and alarm transition.
- [ ] **2.3 Wire EventBridge schedule** in `NFCU-session-3/infra/per-attendee.tf` to invoke drift-detector every 2 min. Acceptance: `terraform validate` + `terraform plan` shows the schedule resource with `rate(2 minutes)`.

### Phase 3: Drift simulator (by June 1)

- [ ] **3.1 Implement `NFCU-session-3/lambdas/drift-simulator/handler.py`.** Sample rows from UCI Adult test split (loaded from `NFCU-session-3/shared/fixtures/uci-adult/` or baseline bucket). Apply `hours_per_week → hours_per_week + Normal(15, 5)`, clipped to `[0, 100]`. Send to production endpoint at 10 req/s for 5 min. Return JSON with request count. Acceptance: dry-run invocation against test endpoint sends 3000 ± 50 requests with drifted feature only.
- [ ] **3.2 Verify Lab 2 end-to-end timing** in local dry-run: drift simulator invoked → drift-detector runs on schedule → PSI on `hours_per_week` crosses 0.25 within 5 min. If timing fails, apply D9 fallback. Acceptance: timing measurement documented in `NFCU-session-3/tests/timing_results.md`.

### Phase 4: Evidently runner (build by June 2; **re-verify pin no earlier than June 9**)

- [ ] **4.1 Re-verify `evidently` pin on PyPI no earlier than June 9.** Document version. If 0.7.22+ available, bump pin and proceed. If 0.8.x available, halt and escalate to Michael. Acceptance: pin decision documented in `NFCU-session-3/lambdas/evidently-runner/PIN_VERIFICATION.md` with date and rationale.
- [ ] **4.2 Write `NFCU-session-3/lambdas/evidently-runner/Dockerfile`** based on `public.ecr.aws/lambda/python:3.11`. Install pinned Evidently. Memory: 1024MB. Acceptance: `docker build` succeeds; image < 1.5GB compressed.
- [ ] **4.3 Implement `NFCU-session-3/lambdas/evidently-runner/handler.py`** using 0.7.x API:
  - Read reference parquet → `Dataset(data, data_definition=DataDefinition(...))`.
  - Read current parquet (last 1 hour from production logs) → wrap similarly.
  - Build `Report([DataDriftPreset(), DataQualityPreset()])`.
  - Run `report.run(current, reference)`.
  - Render HTML; upload to drift-reports bucket; return signed URL (1-hour expiry).
  - Acceptance: `NFCU-session-3/tests/test_evidently_handler.py` (mocked S3) confirms 0.7.x API (no `column_mapping` constructor arg) and signed URL format.
- [ ] **4.4 Local end-to-end test of Evidently Lambda** against drifted fixture data. Open rendered HTML in browser; confirm `hours_per_week` flagged. Acceptance: screenshot saved to `NFCU-session-3/tests/fixtures/evidently_report_sample.png`.

### Phase 5: NannyML runner (build by June 2; re-verify pin June 9)

- [ ] **5.1 Re-verify NannyML pin on PyPI no earlier than June 9.** Acceptance: pin documented in `NFCU-session-3/lambdas/nannyml-runner/PIN_VERIFICATION.md`.
- [ ] **5.2 Write `NFCU-session-3/lambdas/nannyml-runner/Dockerfile`** (1024MB, Python 3.11 base). Acceptance: image builds; tests import `nannyml` successfully.
- [ ] **5.3 Implement `NFCU-session-3/lambdas/nannyml-runner/handler.py`:**
  - Read reference parquet (NannyML reference period).
  - Read current parquet (last 1 hour, same window as Evidently).
  - Construct `nannyml.CBPE` estimator for binary classification (UCI Adult: `≤$50K` vs `>$50K`).
  - Fit on reference; estimate ROC-AUC on current.
  - Return JSON: `{"estimated_auc_reference": X, "estimated_auc_current": Y, "delta": Y - X}`.
  - Emit `EstimatedAUC` CloudWatch metric.
  - Acceptance: invocation against drifted fixture produces measurable delta (> 0.01 absolute). If ≤ 0.01, apply D9 option 2.
- [ ] **5.4 Verify Lab 3 timing budget** end-to-end: Evidently ~10 min, NannyML ~5 min. Acceptance: timing in `NFCU-session-3/tests/timing_results.md`.

### Phase 6: Incident simulator (by June 3)

- [ ] **6.1 Implement five scenario modules** under `NFCU-session-3/lambdas/incident-simulator/scenarios/`. Each exposes `trigger()` and `cleanup()`:
  - `feature_pipeline_broken.py`: replaces `workclass` field with `NULL` in payloads for 5 min. Auto-cleanup after 15 min.
  - `data_drift.py`: invokes drift-simulator behavior inline.
  - `prediction_drift_isolated.py`: flips an inference container env var to invert outputs. Auto-cleanup. **See Open Question 4** — confirm hook exists in Session 1/2 container before implementing; if not, use SageMaker model variant swap instead (must stay inside `NFCU-session-3/`).
  - `latency_degradation.py`: injects 800ms sleep in inference path. Auto-cleanup.
  - `concept_drift_confirmed.py`: pushes synthetic ground-truth labels showing 20% accuracy drop. Auto-cleanup. Code comment references D6 time-compression note.
- [ ] **6.2 Implement round-robin scenario assignment** in `NFCU-session-3/lambdas/incident-simulator/handler.py`. Lab platform passes `attendee_index` (0-indexed); handler computes `scenario = (attendee_index % 5) + 1`. Acceptance: `NFCU-session-3/tests/test_incident_simulator_round_robin.py` confirms even distribution across 30 attendees (6 each).
- [ ] **6.3 Verify all 5 scenarios cleanup correctly** after 15 min and produce expected alarms. Acceptance: per-scenario dry-run documented in `NFCU-session-3/tests/scenario_dry_run.md` with screenshots of fired alarms + verified cleanup.

### Phase 7: Dashboard, alarms, and per-attendee infra (by June 4)

- [ ] **7.1 Write `NFCU-session-3/monitoring/dashboard.json`** with two rows:
  - **Top (infrastructure)**: SageMaker `Invocations`, `ModelLatency`, `Invocation4XXErrors` + `Invocation5XXErrors`.
  - **Bottom (ML)**: `DriftPSI/{feature}` for all 8 features, prediction distribution per class, agreement rate.
  - Acceptance: `aws cloudwatch put-dashboard` succeeds against test account; both rows render.
- [ ] **7.2 Write `NFCU-session-3/monitoring/alarms.tf`** with three alarms + one SNS topic per attendee:
  - `Drift-PSI-{attendee_id}`: any feature PSI > 0.25.
  - `Latency-P95-{attendee_id}`: p95 > 500ms.
  - `ErrorRate-{attendee_id}`: 5xx > 1%.
  - Acceptance: `terraform plan` produces four resources cleanly.
- [ ] **7.3 Write `NFCU-session-3/infra/per-attendee.tf`** for S3 buckets, IAM role/policy, EventBridge schedule. Two buckets per attendee: `workshop-lab-{attendee_id}-baseline`, `workshop-lab-{attendee_id}-drift-reports`. IAM: Lambda role gets `cloudwatch:PutMetricData`, `cloudwatch:SetAlarmState` (drift-detector only), `s3:GetObject` on baseline, `s3:PutObject` on drift-reports. Attendee role gets `lambda:InvokeFunction` on all five Session 3 Lambdas. Acceptance: full per-attendee provisioning runs end-to-end against test attendee ID and tears down cleanly.
- [ ] **7.4 Document per-attendee provisioning runbook** in `NFCU-session-3/LAB_GUIDE.md`. Acceptance: a lab engineer can provision a new attendee from scratch in ≤ 15 min following the doc.

### Phase 8: Restore script and pre-flight (by June 4)

- [ ] **8.1 Build baseline model artifact** from the Session 1/2 model. Save to `NFCU-session-3/shared/baseline-models/session-1-2-uci-adult/model.tar.gz` and upload to the shared S3 bucket (see Open Question 3). Acceptance: artifact is a SageMaker-compatible tar.gz that classifies UCI Adult.
- [ ] **8.2 Write `NFCU-session-3/scripts/restore-session2-endpoint.sh`.** Must:
  - Detect existing healthy endpoint via `aws sagemaker describe-endpoint`; exit 0 if InService.
  - Create endpoint from baseline artifact if missing/unhealthy.
  - Wait for `InService` before returning.
  - Complete in ≤ 4 minutes wall-clock.
  - Be idempotent.
  - Acceptance: dry-run against torn-down sandbox completes in ≤ 4 min and produces a working endpoint that returns predictions on a test payload.
- [ ] **8.3 Write `NFCU-session-3/scripts/verify-lab-readiness.sh`** for lab assistants to run pre-session against all 30 attendees in parallel. Outputs green/red table. Acceptance: against a mixed set of healthy and torn-down sandboxes, correctly identifies which need restore.

### Phase 9: Runbooks (by June 5)

- [ ] **9.1 Write `NFCU-session-3/runbooks/runbook-template.md`** with the 5-phase skeleton (detection → triage → decision → containment → resolution) and the routing rule prominently at the top: *"If fixing requires understanding the model → page model owner. If fixing uses infrastructure tools → DevOps handles."* Acceptance: template renders cleanly in GitHub markdown.
- [ ] **9.2 Write five incident-specific runbooks** populating the template:
  - `NFCU-session-3/runbooks/feature-pipeline-broken.md`: triage focuses on upstream data freshness, schema diffs, recent deploys. Routing: usually DevOps (data infra); page model owner if root cause is a schema change requiring retraining.
  - `NFCU-session-3/runbooks/data-drift.md`: triage compares PSI severity and feature importance. Routing: page model owner (recalibration or retraining is a model decision); DevOps handles containment.
  - `NFCU-session-3/runbooks/prediction-drift-isolated.md`: rare; usually corruption. Triage focuses on container drift, dependency mismatch. Routing: DevOps first (rollback); escalate to model owner only if rollback doesn't restore.
  - `NFCU-session-3/runbooks/latency-degradation.md`: triage on capacity, noisy neighbors, dependency latency. Routing: DevOps almost always.
  - `NFCU-session-3/runbooks/concept-drift-confirmed.md`: triage references NannyML estimate and ground truth. Routing: page model owner. Must include D6 time-compression note prominently.
  - Acceptance: each runbook has all five phases populated with concrete checks an on-call DevOps engineer can execute without model expertise. Language aligned with D12 (no fabricated regulatory claims; no "bank" reference for NFCU).

### Phase 10: Validation, dry-run, and pre-session readiness (by June 11)

- [ ] **10.1 Run full end-to-end dry-run** in workshop timing as one lab engineer playing one attendee. Time each lab segment. Acceptance: results in `NFCU-session-3/tests/dry_run_results.md`.
- [ ] **10.2 Verify Lab 2 PSI crosses 0.25 within 5 minutes.** If longer, apply D9. Acceptance: timing measurement documented.
- [ ] **10.3 Verify NannyML AUC delta** > 0.01 absolute on drifted window. If smaller, apply D9 option 2. Acceptance: delta documented.
- [ ] **10.4 Verify all 5 incident scenarios** fire expected alarms and auto-cleanup. Acceptance: per-scenario verification table in `NFCU-session-3/tests/scenario_dry_run.md`.
- [ ] **10.5 Verify Evidently report renders and signed URL accessible** for one hour. Acceptance: dated screenshot.
- [ ] **10.6 Provision all 30 attendee sandboxes** via Terraform. Acceptance: `terraform apply` clean across all 30; `verify-lab-readiness.sh` reports green.
- [ ] **10.7 Brief lab assistants** on (a) Lab 1 pre-flight protocol, (b) round-robin scenario distribution expectations for Slide 18 debrief, (c) incident simulator alarms are real-sounding but simulated. Acceptance: written briefing doc circulated.

---

## §4. Spec Deltas

The system being specified is the NFCU Session 3 lab environment. These are net-new spec deltas. Each delta file below should be created as `NFCU-session-3/openspec/changes/monitoring/specs/{domain}/spec.md`.

### `NFCU-session-3/openspec/changes/monitoring/specs/monitoring/spec.md`

#### ADDED Requirements

##### Requirement: Two-Layer Monitoring Dashboard
The system SHALL provide a single CloudWatch dashboard per attendee showing both infrastructure-layer metrics and model-layer metrics in separate rows.

###### Scenario: Dashboard renders both layers
- GIVEN an attendee has applied the dashboard via `aws cloudwatch put-dashboard`
- WHEN the attendee opens the dashboard in the AWS Console
- THEN infrastructure widgets (invocations, latency, error rates) populate in the top row
- AND ML widgets (per-feature PSI, prediction distribution per class) populate in the bottom row

##### Requirement: Three Production Alarms
The system SHALL provision exactly three CloudWatch alarms per attendee, each tied to an SNS topic visible in the lab dashboard but not configured to page external systems.

###### Scenario: All three alarms exist post-provisioning
- GIVEN an attendee sandbox has completed Terraform provisioning
- WHEN `aws cloudwatch describe-alarms --alarm-name-prefix workshop-lab-{attendee_id}` is run
- THEN exactly three alarms are returned: `Drift-PSI-{attendee_id}`, `Latency-P95-{attendee_id}`, `ErrorRate-{attendee_id}`
- AND each alarm is in `OK` state at provisioning time

### `NFCU-session-3/openspec/changes/monitoring/specs/drift-detection/spec.md`

#### ADDED Requirements

##### Requirement: Per-Feature PSI Computation
The system SHALL compute Population Stability Index per feature, not as an aggregate.

###### Scenario: PSI computed per feature on every scheduled run
- GIVEN the drift-detector Lambda is scheduled to run every 2 minutes
- WHEN the Lambda executes against recent prediction logs
- THEN it emits a `DriftPSI/{feature}` CloudWatch metric for each of the 8 input features
- AND aggregate PSI is not computed

##### Requirement: Drift Alarm Fires on Threshold Crossing
The system SHALL transition the drift alarm to `ALARM` state when any single feature's PSI exceeds 0.25.

###### Scenario: Single-feature drift triggers alarm
- GIVEN traffic is being sent with a deliberately shifted distribution on the `hours_per_week` feature
- WHEN the drift-detector observes PSI > 0.25 on `hours_per_week`
- THEN the `Drift-PSI-{attendee_id}` alarm transitions to `ALARM` state
- AND the alarm reason identifies `hours_per_week` as the drifting feature
- AND other features' PSI remains below 0.1

##### Requirement: Lab 2 Timing Budget
The system SHALL detect injected drift and transition the alarm to `ALARM` state within 5 minutes of the drift simulator beginning to send traffic.

###### Scenario: Drift detection within Lab 2 budget
- GIVEN the drift-simulator Lambda is invoked
- WHEN drifted traffic begins reaching the endpoint at 10 req/s
- THEN PSI on `hours_per_week` crosses 0.25 within 5 minutes
- AND the drift alarm transitions to `ALARM` state within the same window

### `NFCU-session-3/openspec/changes/monitoring/specs/drift-reporting/spec.md`

#### ADDED Requirements

##### Requirement: Evidently Report Generation
The system SHALL generate a complete Evidently AI drift report on demand, covering all features and all standard drift metrics.

###### Scenario: Report rendered and accessible
- GIVEN an attendee invokes `evidently-runner-{attendee_id}` Lambda manually
- WHEN the Lambda completes execution
- THEN it uploads an HTML report to the drift-reports S3 bucket
- AND returns a signed URL with 1-hour expiry
- AND the URL renders a browsable Evidently report in any modern browser
- AND the report flags features that have drifted in the current window

##### Requirement: Evidently 0.7.x API Compliance
The system SHALL use the Evidently 0.7.x API style and SHALL NOT use the legacy `column_mapping` argument.

###### Scenario: Code uses Dataset with data_definition
- GIVEN a code reviewer inspects `NFCU-session-3/lambdas/evidently-runner/handler.py`
- WHEN they search for API usage
- THEN they find `Dataset(..., data_definition=...)` and `Report([DataDriftPreset(), DataQualityPreset()])`
- AND they find no references to `column_mapping` as a Report constructor argument

### `NFCU-session-3/openspec/changes/monitoring/specs/performance-estimation/spec.md`

#### ADDED Requirements

##### Requirement: Ground-Truth-Free Performance Estimation
The system SHALL estimate model performance on a current production window without using ground truth labels, using NannyML CBPE for binary classification.

###### Scenario: CBPE produces measurable AUC delta on drifted window
- GIVEN the reference window contains clean Session 1/2 prediction traffic
- AND the current window contains traffic with injected drift on `hours_per_week`
- WHEN an attendee invokes `nannyml-runner-{attendee_id}`
- THEN the response JSON contains `estimated_auc_reference`, `estimated_auc_current`, and `delta` fields
- AND the absolute value of `delta` is greater than 0.01

### `NFCU-session-3/openspec/changes/monitoring/specs/incident-simulation/spec.md`

#### ADDED Requirements

##### Requirement: Five Distinct Incident Scenarios
The system SHALL provide exactly five incident scenarios, each with a distinct alarm pattern and a documented runbook.

###### Scenario: All five scenarios produce expected alarm patterns
- GIVEN an attendee invokes the incident-simulator with scenario parameter N in [1, 5]
- WHEN the scenario executes
- THEN the alarm pattern matches the runbook for that scenario
- AND the scenario auto-cleans up within 15 minutes
- AND no scenario leaves persistent state in the attendee's sandbox

##### Requirement: Round-Robin Scenario Assignment
The system SHALL assign incident scenarios to attendees in round-robin order across a cohort of 30, not randomly.

###### Scenario: Even scenario distribution across 30 attendees
- GIVEN a cohort of 30 attendees indexed 0–29
- WHEN scenarios are assigned by the lab platform
- THEN each of the five scenarios is assigned to exactly six attendees
- AND no scenario is over- or under-represented by more than zero

### `NFCU-session-3/openspec/changes/monitoring/specs/runbooks/spec.md`

#### ADDED Requirements

##### Requirement: Five-Phase Runbook Skeleton
The system SHALL provide a runbook template with exactly five phases in order: detection, triage, decision, containment, resolution.

###### Scenario: Template phases are present and ordered
- GIVEN a reader opens `NFCU-session-3/runbooks/runbook-template.md`
- WHEN they scan the document structure
- THEN they find five top-level sections in the order: Detection, Triage, Decision, Containment, Resolution

##### Requirement: Routing Rule Prominent
The system SHALL state the routing rule at the top of every runbook: *"If fixing requires understanding the model → page model owner. If fixing uses infrastructure tools → DevOps handles."*

###### Scenario: Routing rule appears at top of every runbook
- GIVEN any of the six runbook files in `NFCU-session-3/runbooks/`
- WHEN a reader opens the file
- THEN the routing rule appears within the first 30 lines

##### Requirement: Concept Drift Time-Compression Disclosure
The system SHALL explicitly disclose, in `NFCU-session-3/runbooks/concept-drift-confirmed.md`, that the lab time-compresses concept drift and that real-world response windows are months, not minutes.

###### Scenario: Time-compression note present
- GIVEN a reader opens `NFCU-session-3/runbooks/concept-drift-confirmed.md`
- WHEN they read the document
- THEN they find a clearly-labeled note stating real concept drift manifests over months
- AND that the lab compresses this for pedagogical purposes
- AND that response timing in the lab is not generalizable to real incidents

##### Requirement: No Fabricated Regulatory Claims
Runbook and lab guide content SHALL NOT claim compliance with NCUA, FFIEC, or any other regulatory framework. Content SHALL NOT refer to NFCU as a "bank".

###### Scenario: Content audit confirms no fabricated regulatory claims
- GIVEN a reviewer searches all files under `NFCU-session-3/runbooks/` and `NFCU-session-3/LAB_GUIDE.md`
- WHEN they grep for "NCUA", "FFIEC", "compliant", "compliance", or "bank"
- THEN any matches are either negative ("does not constitute compliance attestation"), descriptive of principles ("aligned with model risk frameworks"), or absent
- AND no claim attests that the lab content itself constitutes compliance with a specific framework

### `NFCU-session-3/openspec/changes/monitoring/specs/endpoint-recovery/spec.md`

#### ADDED Requirements

##### Requirement: Pre-Flight Restore Script
The system SHALL provide an idempotent restore script that recreates a missing or unhealthy Session 1/2 SageMaker endpoint in ≤ 4 minutes wall-clock.

###### Scenario: Restore against a torn-down sandbox completes within budget
- GIVEN an attendee's Session 1/2 endpoint has been torn down or is `Failed`
- WHEN `NFCU-session-3/scripts/restore-session2-endpoint.sh` is invoked
- THEN within 4 minutes a new endpoint with status `InService` exists in the sandbox
- AND the endpoint returns valid predictions on a UCI Adult test payload

###### Scenario: Restore against a healthy endpoint is a fast no-op
- GIVEN an attendee's Session 1/2 endpoint is already `InService`
- WHEN `NFCU-session-3/scripts/restore-session2-endpoint.sh` is invoked
- THEN the script exits 0 in under 10 seconds without modifying the endpoint

### `NFCU-session-3/openspec/changes/monitoring/specs/lab-platform/spec.md`

#### ADDED Requirements

##### Requirement: Lab Readiness Verification
The system SHALL provide a script that verifies pre-session readiness for all 30 attendee sandboxes in parallel and reports per-attendee status.

###### Scenario: Readiness check distinguishes healthy from broken sandboxes
- GIVEN 30 attendee sandboxes, some healthy and some with torn-down endpoints
- WHEN `NFCU-session-3/scripts/verify-lab-readiness.sh` is invoked
- THEN it produces a table with one row per attendee and a green/red status indicator
- AND red rows identify the specific failure mode (endpoint missing, alarm misconfigured, dashboard not provisioned, etc.)

##### Requirement: Touch Boundary
This change SHALL NOT modify code outside the touch boundary defined in D11.

###### Scenario: No files modified outside Session 3 scope
- GIVEN this change has been fully implemented
- WHEN a diff is run against the repository before and after the change
- THEN modified paths fall only within `NFCU-session-3/**` or `.github/workflows/nfcu-session-3-*.yml`
- AND no files under `Agentic_DevOps/`, `NFCU-session-1/`, `NFCU-session-2/`, `NFCU-session-4/`, or repo-root `README.md`/`CLAUDE.md`/`.gitignore`/`LICENSE` are modified

---

## §5. Definition of Done

The change is complete when **all** of the following hold.

### Pre-Provisioning (by June 2)
- [ ] Sessions 1 & 2 sandboxes confirmed preserved through June 16.
- [ ] Reference distribution captured from baseline Session 1/2 traffic.
- [ ] All five Lambda functions written, unit-tested, verified standalone.
- [ ] Evidently container image built with verified pin (re-checked June 9).
- [ ] NannyML container image built with verified pin (re-checked June 9).
- [ ] Restore script tested end-to-end against torn-down sandbox in ≤ 4 min.
- [ ] Touch boundary respected: `git diff` shows no changes outside `NFCU-session-3/` or `.github/workflows/nfcu-session-3-*.yml`.

### Per-Attendee Provisioning (by June 6)
- [ ] All Lambdas deployed per attendee.
- [ ] EventBridge schedule wired (every 2 min) per attendee.
- [ ] CloudWatch dashboard provisioned per attendee.
- [ ] Three alarms + SNS topic provisioned per attendee.
- [ ] Reference distribution uploaded to baseline bucket per attendee.
- [ ] All five runbook templates present in `NFCU-session-3/runbooks/`.
- [ ] Round-robin assignment tested across 30-attendee distribution.
- [ ] All five incident scenarios tested standalone.

### Pre-Session Validation (by June 11)
- [ ] End-to-end dry-run in workshop timing.
- [ ] Lab 2 PSI crosses 0.25 within 5 minutes verified.
- [ ] All five incident scenarios fire expected alarms verified.
- [ ] Auto-cleanup verified for all five scenarios.
- [ ] Evidently report renders, signed URL accessible.
- [ ] NannyML CBPE returns AUC delta > 0.01 absolute on drifted window.
- [ ] No fabricated regulatory claims verified by grep audit.

### Session Day (June 16)
- [ ] Pre-session endpoint verification across all 30 attendees.
- [ ] Lab assistants briefed on Lab 1 pre-flight protocol.
- [ ] Restore artifact staged for fast recovery.
- [ ] Lab assistants briefed on incident simulator behavior and round-robin distribution.

### Post-Session
- [ ] Endpoints remain InService (Session 4 dependency).
- [ ] Sandboxes preserved through June 18.

---

## §6. Open questions and known unknowns

For Michael, not Claude Code:

1. **Evidently pin** — assumes 0.7.21 holds at re-verification June 9. If 0.8.x ships, the API may change and Task 4.1 needs review before proceeding.
2. **NannyML version** — pin not explicit in the v2.1 doc. Task 5.1 marks it as "latest stable at lab build time". Verify the `CBPE` constructor signature matches handler code when the pin is locked.
3. **Shared S3 bucket for the baseline model artifact** (Task 8.1) — bucket name and region need to be set during the build. Suggest `kodekloud-mlops-shared-artifacts-us-east-1` with prefix `nfcu-session-3/baseline-model/`. Confirm with the lab platform team. The local repo path `NFCU-session-3/shared/baseline-models/session-1-2-uci-adult/` is the source; the S3 bucket is the runtime distribution point.
4. **Incident simulator scenario 3 (prediction drift isolated)** — the v2.1 doc says "flips inference container env var to invert outputs." This requires the Session 1/2 inference container to read an env var that controls output inversion. If that hook doesn't exist, scenario 3 needs an alternative implementation. Per D11, a Session 2 container rebuild would breach the touch boundary; the in-scope alternative is a SageMaker model variant swap that lives entirely in `NFCU-session-3/`. Confirm hook presence before Phase 6.
5. **Buffer dependency** — the 6-min schedule buffer is contingent on Lab 1 not spilling. Pre-flight protocol is the only thing preventing spillover. Confirm lab assistants are staffed (typically 2 assistants for a 30-person cohort).
6. **Slide deck location** — the `Agentic_DevOps/` folder ships a `.pptx` at its root. Plan is for Michael's Session 3 deck to land at `NFCU-session-3/NFCU_Session_3_Monitoring.pptx` (or similar) outside this change. Not Claude Code's deliverable.
7. **Repo-root `CLAUDE.md` update** — currently says "Stack: Documentation / Markdown". After this change, the repo also contains Python, Terraform, and Docker. Update is recommended but governed by a separate change so this build stays scoped.
8. **Convention precedent for future sessions** — once this lands, `NFCU-session-3/` becomes the precedent for NFCU-session-1, -2, -4. Confirm OpenSpec-per-session vs OpenSpec-at-repo-root is the right call before further sessions follow this layout. (My pick: OpenSpec per session, because the sessions are largely independent and self-containment matters more than spec cross-referencing here.)
