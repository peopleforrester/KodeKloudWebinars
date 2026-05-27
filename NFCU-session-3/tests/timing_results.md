# Timing Results

**Verification method:** Local TDD establishes the request volume and transform
correctness. End-to-end wall-clock timing against a live SageMaker endpoint is
**deferred** — it requires a lab sandbox and is measured during the June 11
dry-run (see `../RUN_CONFIG.md`). This file states the expected timing and the
measurement procedure; live numbers are filled in at dry-run.

---

## Lab 2 — drift detection budget (tasks 3.2, 10.2)

**Requirement:** PSI on `hours_per_week` crosses 0.25 within 5 minutes of the
drift simulator starting (drift-detection spec, "Lab 2 Timing Budget").

**Mechanism (D9):**
- drift-simulator sends `hours_per_week += Normal(15, 5)` (clip [0,100]) at
  10 req/s for 5 min = **3000 requests** (verified locally:
  `test_drift_simulator.py::test_handler_sends_3000_drifted_only`).
- drift-detector runs every 2 min on a 5-min rolling window.
- Expected crossing: **4–6 minutes**.

**Measurement procedure (dry-run):**
1. Note T0 = drift-simulator invocation time.
2. Poll `Drift-PSI-{attendee_id}` alarm state every 15s.
3. Record T1 = first ALARM transition. Target: `T1 - T0 ≤ 5 min`.

**Tuning fallback if T1 - T0 > 5 min (one knob at a time, smallest blast radius):**
1. EventBridge schedule 2 min → 1 min (lab window only).
2. Drift shift mean +15 → +25.
3. Detector reference window 5 min → 3 min.

| Run date | T1 - T0 | Knob applied | Result |
|----------|---------|--------------|--------|
| _pending dry-run (June 11)_ | — | — | — |

---

## Lab 3 — Evidently + NannyML budget (task 5.4)

**Requirement:** Evidently ~10 min, NannyML ~5 min within the Lab 3 window.

**Measurement procedure (dry-run):**
1. Invoke `evidently-runner`; record cold-start + run duration to signed-URL return.
2. Invoke `nannyml-runner`; record duration to JSON response.

| Component | Target | Measured | Notes |
|-----------|--------|----------|-------|
| evidently-runner | ~10 min | _pending_ | container cold start dominates first run |
| nannyml-runner | ~5 min | _pending_ | CBPE fit + estimate |
