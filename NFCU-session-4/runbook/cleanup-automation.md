# Cleanup & Retention

What dies when, after the 2026-06-18 session. Three tiers: kill the expensive ephemeral
stuff fast, keep attendee work for a 24-hour catch-up window, then decommission everything.

## T+30 min — Ephemeral, killed now

These cost money or compute and have no catch-up value:

- Speaker's EKS demo cluster, **unless** it's serving the catch-up window (decide at T+30 and
  note which). If done: `bash cluster/eks/down.sh`.
- Any load-test leftovers (k6 has exited; nothing persistent).
- Scale all InferenceServices to zero implicitly (idle → scale-to-zero handles it).

Confirm: `kubectl top nodes` shows load dropping; no k6 processes running.

## T+24 hours — Attendee namespaces persist

The shared cluster and every attendee namespace stay up for 24 hours so attendees can
finish or re-run labs:

- Attendee namespaces, their applied manifests, and quotas remain intact.
- A returning attendee finds their `InferenceService`/Deployment exactly as they left it
  (idle, scaled to zero — a request wakes it).

Confirm at any point in the window: pick a namespace, re-run a lab, it works without
re-provisioning.

## By 2026-06-20 — Full decommission

48 hours after the session, nothing remains billable:

- Lab platform tears down all attendee namespaces and the shared cluster.
- Speaker's EKS cluster destroyed if not already: `bash cluster/eks/down.sh`, then
  `aws eks list-clusters --region <region>` returns empty.
- S3 model-artifact bucket: empty and delete (or let the lab platform's lifecycle handle it).
  Check for leftover NLBs, EBS volumes, and the NAT gateway — these are the silent costs.

Confirm decommission from automation logs and a final `aws` sweep:

```bash
aws eks list-clusters --region us-east-1
aws elbv2 describe-load-balancers --query 'LoadBalancers[?contains(LoadBalancerName, `nfcu`)]'
aws ec2 describe-nat-gateways --filter Name=state,Values=available
```

All three should be empty of session resources. Record the result in the DoD Gate 5 checklist.

## Why these tiers

The expensive things (GPU? no — but NAT gateway, NLB, node hours, EKS control plane) burn
money whether or not anyone's using them. Kill those fast. Attendee *work* is cheap to keep
(scaled to zero) and valuable for the catch-up window, so it gets 24 hours. Then everything
goes, verified — because the most expensive mistake is a cluster nobody remembered to delete.
