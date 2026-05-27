# Definition of Done

Five gated checklists with hard dates. Every item is binary — done or not done. **Any
"not done" item at its gate blocks session day (2026-06-18).** Sign off by checking the box
and initialing in the PR that flips it.

## Gate 1 — Pre-Provisioning (by 2026-06-02)

- [ ] EKS Terraform module `terraform validate` and `terraform fmt -check` pass in CI.
- [ ] `make -C NFCU-session-4 validate` passes on a clean checkout.
- [ ] TinyLlama image built multi-arch and pushed; tag recorded in the Lab 3 manifest.
- [ ] distilGPT-2 fallback image built and pushed (same tag scheme).
- [ ] Model artifacts generate deterministically (`generate-xgboost-models.py` twice → identical `.bst`).
- [ ] All four lab walkthroughs reviewed end-to-end by someone who didn't write them.

## Gate 2 — Per-Attendee Provisioning (by 2026-06-06)

- [ ] Lab platform confirms it can stamp 30 namespaces from `cluster/lab-overlays/`.
- [ ] ResourceQuota (4 vCPU / 8 Gi / 10 pods) verified on a stamped sample namespace.
- [ ] NetworkPolicy verified: attendee-A pod cannot reach attendee-B service; Knative ingress still works.
- [ ] `kserve-sa` ServiceAccount present in each namespace bound via a Pod Identity association (EKS).
- [ ] Storage initializer reads a model from S3 in a sample namespace with no static keys.

## Gate 3 — Pre-Session Validation (by 2026-06-13)

- [ ] `runbook/dry-run-checklist.md` executed end-to-end against the provisioned cluster; all green.
- [ ] **TinyLlama and distilGPT-2 images pre-pulled to every node** (the single most fragile thing).
- [ ] Labs 1–4 each completed within their time budget by a non-author.
- [ ] Grafana dashboards and OpenCost UI reachable and showing data.
- [ ] Cold-start time for Lab 1 and Lab 3 measured and recorded in `timing-notes`.
- [ ] Any failure triaged against `troubleshooting-matrix.md`; no open blockers.

## Gate 4 — Session Day (2026-06-18)

- [ ] `day-of-operations.md` T-60 checklist completed before attendees arrive.
- [ ] `cluster/addons/verify.sh` exits 0 on the live cluster.
- [ ] Smoke tests (`tests/smoke/curl-tests.sh`) pass against a sample namespace.
- [ ] Speaker's demo cluster up and a dry pass of Lab 1 done before going live.
- [ ] Support channel staffed; troubleshooting matrix open in a tab.

## Gate 5 — Post-Session

- [ ] Catch-up window (24h) confirmed working: a returning attendee's namespace is intact.
- [ ] At T+24h, attendee namespaces and the shared cluster decommissioned per `cleanup-automation.md`.
- [ ] Speaker's EKS demo cluster destroyed (`cluster/eks/down.sh`); `aws eks list-clusters` empty.
- [ ] AWS spend reconciled against `speaker-aws-spend.md`; note any surprise on the bill.
- [ ] Retro notes captured (what to change for the next infra-heavy session).
