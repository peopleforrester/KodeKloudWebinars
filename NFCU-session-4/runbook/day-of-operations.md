# Day-of Operations

Session start: **2026-06-18, 10:00 AM ET.** Times below are relative to that. Each entry
says what to run, what to check, and where to shout if it's wrong. No improvisation — if
something is off, the [troubleshooting matrix](troubleshooting-matrix.md) has the fix.

## T-60 — Cluster and add-ons

- [ ] `cluster/addons/verify.sh` exits 0 on the shared cluster. → if not, fix the named add-on.
- [ ] Speaker's EKS demo cluster: `bash cluster/eks/up.sh` done; `verify.sh` green.
- [ ] Confirm TinyLlama + distilGPT-2 images are pre-pulled on all nodes (`kubectl get nodes`,
      spot-check `crictl images` on one). → if missing, pre-pull now; this is the fragile bit.
- [ ] Grafana and OpenCost reachable (port-forward, open both). → dashboard check.
- [ ] Post in the support channel: "cluster green, T-60."

## T-30 — Per-attendee namespaces

- [ ] All attendee namespaces present: `kubectl get ns | grep attendee | wc -l` = expected count.
- [ ] Smoke a sample namespace: `NAMESPACE=attendee-0001 bash tests/smoke/curl-tests.sh`.
- [ ] Speaker: dry pass of Lab 1 on the demo cluster (deploy, predict, scale-to-zero).
- [ ] Confirm the recording/stream is up.

## T-5 — Final

- [ ] Troubleshooting matrix open in a tab. Support staff online.
- [ ] Speaker terminal reset to a clean prompt; env vars (`BASE_URL`, etc.) exported.

## T+0 to T+12 — Intro

- Speaker frames the session; attendees run `prerequisites.md` access checks.
- Watch for auth failures in the support channel; most are wrong context/namespace.

## T+12 / T+24 / T+36 / T+51 — Labs 1 / 2 / 3 / 4

- For each lab: watch the support channel for the lab's known symptom (cold-start 503s in
  Lab 1, k6 host-header errors in Lab 2, OOM/cost-data in Lab 3, split/rollback in Lab 4).
- Keep an eye on cluster headroom: `kubectl top nodes`. If pods go `Pending`, the node
  autoscaler should react; manual node-group bump is the fallback (matrix row 2/14).

## T+111 to T+120 — Wrap

- Point attendees at `post-session-monday-actions.md` and `reproduce-on-your-aws-account.md`.
- Announce the 24-hour catch-up window.

## T+30 (post-end) — Begin teardown

- Start the cleanup per [`cleanup-automation.md`](cleanup-automation.md): ephemeral resources
  down now, attendee namespaces persist 24h, full decommission by 2026-06-20.
- Speaker: `bash cluster/eks/down.sh` once the demo is truly done (or keep for the catch-up
  window if attendees will use the demo cluster — decide and note it).
