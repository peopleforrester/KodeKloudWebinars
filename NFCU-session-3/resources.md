# Resources

Curated external reading for NFCU Session 3 — model monitoring, drift detection,
and ground-truth-free performance estimation. Every entry has a date, a source,
and a reason to read it.

---

## Drift detection and monitoring tooling

**Evidently AI — Documentation**
Source: Evidently AI, 0.7.x docs (re-verify pin June 9, 2026)
The library behind Lab 3 Part 1. Read the "Reports and Presets" and "Data
Definition" pages: the 0.7.x API replaced the legacy `column_mapping` argument
with `Dataset(..., data_definition=...)` and `Report([DataDriftPreset(),
DataQualityPreset()])`. Tutorials written for 0.4.x still teach the old API — do
not follow them. See `lambdas/evidently-runner/PIN_VERIFICATION.md` for the exact
pinned version used in the lab.

**NannyML — Documentation (CBPE)**
Source: NannyML, latest stable (re-verify pin June 9, 2026)
The library behind Lab 3 Part 2. Read the "Confidence-Based Performance
Estimation (CBPE)" guide: CBPE estimates ROC-AUC on a production window **without
ground-truth labels**, which is the entire point — you usually do not have labels
in real time. This is the conceptual anchor for why monitoring inputs (drift) is
not enough; you also estimate output quality.

**Population Stability Index (PSI) — a primer**
Source: Standard model-risk literature (see any model-validation reference)
PSI quantifies how much a feature's distribution has shifted between a reference
and a current window. The lab's working thresholds: < 0.10 = stable, 0.10–0.25 =
moderate shift (investigate), > 0.25 = significant shift (alarm). These thresholds
are what an NFCU model-risk reviewer will expect to see. PSI is computed
**per feature**, never as a single aggregate — an aggregate hides which feature
moved.

---

## Dataset context

**Ding et al., "Retiring Adult: New Datasets for Fair Machine Learning"**
Source: NeurIPS 2021
The UCI Adult income dataset used by the Session 1/2 model is academically dated;
this paper documents its sampling problems and recommends the `folktables` /
ACSIncome replacements. We keep UCI Adult for series continuity and frame it in
the lab as a stand-in for *any* production binary classifier. Read this so you can
answer the inevitable "why are we still using Adult?" question honestly. A dataset
refresh is a candidate for the next iteration, not this build.

---

## The session itself

**Session 3 — Keeping 100+ Models Healthy, v2.1 (May 14, 2026)**
Source: Internal session design doc (Performant Pro)
The authoritative source this lab is built from. The "silent wrongness" framing —
a model returning 200s with good latency while quietly degrading — is the thesis
of the whole session and the reason model-layer monitoring exists alongside
infrastructure-layer monitoring.
