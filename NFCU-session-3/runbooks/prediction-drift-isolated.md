# Runbook: Prediction Drift (Isolated)

> **Routing rule — read first.**
> **If fixing requires understanding the model → page the model owner.**
> **If fixing uses infrastructure tools → DevOps handles.**

| Field | Value |
|-------|-------|
| Expected alarm/signal | `Drift-PSI-{attendee_id}` (output/prediction distribution) |
| First responder | DevOps (rollback first) |
| Severity | Sev2 |

The **output** distribution shifts while inputs look normal — the classic
signature of container or dependency corruption (a bad image, a dependency
mismatch, a wrong artifact). It's rare, and the first move is rollback, not
model analysis.

## Detection

- Prediction distribution per class (dashboard, bottom row) flips or skews sharply,
  while per-feature **input** PSI stays low — inputs normal, outputs abnormal.
- Often coincides with a recent deploy or image/dependency change to the serving
  container.

## Triage

- Compare the running container image digest / dependency versions against the
  last known-good:
  ```bash
  aws sagemaker describe-endpoint --endpoint-name workshop-lab-{attendee_id}-production \
    --query 'EndpointConfigName'
  aws sagemaker describe-endpoint-config --endpoint-config-name <config> \
    --query 'ProductionVariants[].ModelName'
  ```
- Check for a recent endpoint-config change or model swap.
- Confirm inputs are unchanged (input PSI low) to rule out data drift.

## Decision

- Apply the routing rule. Corruption is fixed with **infrastructure tools**
  (rollback) → **DevOps first**. Escalate to the model owner **only if** rollback
  does not restore correct behavior (which would suggest a genuine model issue,
  not corruption).

## Containment

- Roll the endpoint back to the last known-good endpoint config / model variant:
  ```bash
  aws sagemaker update-endpoint --endpoint-name workshop-lab-{attendee_id}-production \
    --endpoint-config-name <last-known-good-config>
  ```

## Resolution

- Confirm the prediction distribution returns to baseline after rollback. Identify
  the corrupt image/dependency, rebuild it cleanly, and re-deploy through the
  normal path. If rollback did **not** fix it, page the model owner — the problem
  is in the model, not the container.
