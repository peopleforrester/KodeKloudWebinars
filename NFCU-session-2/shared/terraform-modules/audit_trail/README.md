# audit_trail Terraform module

Provisions a per-attendee S3 bucket for promotion and rollback audit entries:
`workshop-lab-{attendee_id}-audit`. Reused by Session 2 and (planned) Session 3.

## Inputs

| Name | Type | Description |
|---|---|---|
| `attendee_id` | string | Scopes the bucket name. |
| `tags` | map(string) | Cost-attribution / teardown tags. |

## Outputs

| Name | Description |
|---|---|
| `bucket_name` | Audit bucket name. |
| `bucket_arn` | Audit bucket ARN. |

## What this module enables

- S3 **versioning** — audit entries cannot be silently overwritten.
- **SSE-S3 (AES256)** server-side encryption with bucket keys.
- **Block-all-public-access** on the bucket.

## Lab simplifications (NOT production controls)

This module is deliberately simplified for a teaching lab. A production audit
store for SR 11-7 / Treasury FS AI RMF evidence would add:

- **MFA-delete** on the bucket — prevents credential-only deletion of versions.
- **S3 Object Lock** (compliance mode) — write-once-read-many tamper-evidence.
- **Customer-managed KMS key** instead of SSE-S3, with a key policy.
- **Access logging** to a separate, equally locked-down log bucket.
- **Multi-actor approval** for any lifecycle or policy change.

These omissions are intentional and are surfaced to attendees in the Session 2
README and `LAB_GUIDE.md`. Do not treat this module as a production reference.
