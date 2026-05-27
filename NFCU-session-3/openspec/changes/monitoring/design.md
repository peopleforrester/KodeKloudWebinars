# Design — `monitoring` (NFCU Session 3)

> Split from `NFCU-session-3/OPENSPEC_CHANGE_monitoring.md` §2. See the combined
> document for the full architecture diagram and folder tree.

## Architecture overview

Per-attendee resources sit in a lab-platform-managed AWS sandbox. The Session 1/2
SageMaker endpoint (`workshop-lab-{attendee-id}-production`, `ml.m5.xlarge`, UCI
Adult binary classifier) is the monitoring target. Session 3 layers monitoring,
drift detection, and incident simulation on top:

- Synthetic prod traffic → SageMaker endpoint → CloudWatch native metrics.
- Prediction logs → S3 shadow-logs bucket.
- `drift-detector` Lambda runs every 2 min: reads last 5 min of logs +
  `reference.parquet`, computes per-feature PSI, emits `DriftPSI/{feature}`
  metrics, forces the drift alarm on PSI > 0.25.
- Manual-invoke Lambdas: `evidently-runner` (HTML report → S3), `nannyml-runner`
  (estimated AUC JSON), `drift-simulator` (drifted endpoint traffic),
  `incident-simulator` (one of 5 scenarios).
- CloudWatch dashboard (2 rows: infra + ML), 3 alarms → SNS (visible, not paging).

## Session self-containment principle

Session 3 does not assume Sessions 1/2/4 are built. The baseline model artifact
and UCI Adult fixtures live under `NFCU-session-3/shared/` (session-owned copies),
and OpenSpec is per-session at `NFCU-session-3/openspec/`.

## Key design decisions

- **D1. Evidently pin & API.** `evidently==0.7.21`, 0.7.x API (`from evidently
  import Report`; `from evidently.presets import DataDriftPreset,
  DataQualityPreset`; `Dataset(..., data_definition=...)`;
  `report.run(current, reference)`). Re-verify on PyPI ≥ June 9, ≤ June 11. Bump
  to 0.7.22+ if stable; do NOT auto-bump to 0.8.x — Michael reviews.
- **D2. Packaging.** Zip: drift-detector, drift-simulator, incident-simulator.
  Container (1024 MB): evidently-runner, nannyml-runner (pandas/plotly/scipy).
- **D3. Alarm shortcut (workshop-only).** drift-detector calls
  `cloudwatch:SetAlarmState` to force ALARM on PSI > 0.25 for fast visual
  feedback. Flagged in code as workshop-only, not production practice.
- **D4. Round-robin incidents.** `scenario = (attendee_index % 5) + 1`; guarantees
  ~6 of each across 30 (random would skew the Slide 18 debrief).
- **D5. UCI Adult.** Academically dated (Ding et al., "Retiring Adult", 2021);
  preserved for continuity, framed as a stand-in for any production binary
  classifier. Fixtures at `shared/fixtures/uci-adult/`.
- **D6. Concept-drift time compression.** Real concept drift manifests over
  months; the lab compresses it to ~15 min. `runbooks/concept-drift-confirmed.md`
  must disclose this.
- **D7. Reference capture.** `scripts/capture-reference-distribution.py` runs once
  at build time against clean S1/2 traffic → `reference.parquet` (8 features,
  ≥1000 rows). Uploaded to each `workshop-lab-{attendee_id}-baseline` bucket.
- **D8. Restore script.** Idempotent; no-op fast if InService; else recreate from
  baseline artifact; ≤ 4 min wall-clock.
- **D9. Drift sim & Lab-2 timing.** `hours_per_week += Normal(15,5)` clip [0,100],
  10 req/s for 5 min; detector 2-min schedule on 5-min window → PSI crosses 0.25
  in 4–6 min. Tuning fallback (one knob at a time): schedule 2→1 min; shift
  +15→+25; window 5→3 min.
- **D10. NannyML anchor.** AUC delta must be > 0.01 absolute on drifted data or
  the lesson falls flat; measure on real fixtures, apply D9 opt 2 if too small.
- **D11. Touch boundary.** Only `NFCU-session-3/**` (workflow nested per build
  override). No `Agentic_DevOps/`, peer sessions, or repo-root files touched.
- **D12. NFCU framing.** No NCUA/FFIEC compliance claims; "aligned with model risk
  principles," not an attestation. Never call NFCU a "bank." PSI thresholds and
  routing language match what a model-risk reviewer expects.

## Dependencies

| Dependency | Source | Status |
|---|---|---|
| S1/2 SageMaker endpoint | Lab sandbox, preserved through June 18 | Verify pre-session |
| S1/2 model artifact | `shared/baseline-models/session-1-2-uci-adult/` + shared S3 | Build before June 2 |
| UCI Adult dataset | `shared/fixtures/uci-adult/` | Reuse/copy |
| `evidently==0.7.21` | PyPI | Re-verify June 9 |
| `nannyml` (latest stable) | PyPI | Re-verify June 9 |
| Terraform ≥ 1.6 | Lab platform | Present |
| AWS `us-east-1` | Lab sandbox | Standard |

## Cost envelope

- Session 3-specific per attendee: $0.40–$0.80; total at 30: $12–$24.
- Standing endpoint carry (NOT this scope): ~$84/attendee × 30 ≈ $2,500 across
  the series window (June 2 → June 18, `ml.m5.xlarge` @ $0.22/hr).
