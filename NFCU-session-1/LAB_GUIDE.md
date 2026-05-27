# Lab Guide: Replicating the Session 1 Pipeline

This guide walks you through running the full deployment pipeline yourself, after the
webinar, in your own AWS sandbox. Work the four segments in order. Each ends with a
**Success criterion** — confirm it before moving on.

---

## Prerequisites

Before segment 1, you need:

- **An AWS sandbox account** you can safely create and destroy resources in (us-east-1).
- **`lab-platform-iac` applied** in that account. Follow
  [lab-platform-iac/README.md](lab-platform-iac/README.md) — it provisions the network,
  KMS key, S3 buckets, ECR repo, GitHub OIDC provider, and the scoped IAM roles. Note
  the SageMaker quota lead time (up to 7 business days on new accounts).
- **The `AWS_ROLE_ARN` repository variable set** to the `workflow_role_arn` output from
  `lab-platform-iac` (Settings → Secrets and variables → Actions → Variables). Set the
  other `vars.*` referenced by the workflows the same way (ECR registry, bucket names,
  KMS key id, model data URL, image digest).
- **Three GitHub Environments created**: `nfcu-session-1-dev`, `nfcu-session-1-staging`,
  and `nfcu-session-1-production`. Add **at least one required reviewer** to
  `nfcu-session-1-production`. The other two need no reviewers.

You do **not** need long-lived AWS access keys. Every workflow authenticates to AWS
through OIDC and assumes the role above.

---

## Segment 1 — Validation gate

The validation job rejects bad artifacts before anything is built or deployed.

1. Make a trivial change under `NFCU-session-1/` (e.g. edit a comment), commit, and
   push to `main`. Watch the **Deploy Dev** workflow run green through the `validate`
   job.
2. Now trigger the deliberate failure. Create
   `NFCU-session-1/terraform/environments/dev/terraform.tfvars` with:

   ```hcl
   model_version = "latest"
   ```

   Because `*.tfvars` is gitignored, force-add it for this exercise:
   `git add -f NFCU-session-1/terraform/environments/dev/terraform.tfvars`, commit, push.
3. Watch the `validate` job go **red**. Open the failed step — the visible failure cause
   is exactly:

   ```
   VALIDATION FAILED: Mutable artifact reference — 'latest' is not allowed; use immutable semver
   ```

4. Revert: `git rm -f NFCU-session-1/terraform/environments/dev/terraform.tfvars`,
   commit, push. The `validate` job goes green again.

**Success criterion:** you have seen the pipeline both pass on an immutable version and
fail with the specific mutable-reference message on `latest`.

---

## Segment 2 — Container build, scan, and sign

1. In `.github/workflows/nfcu-session-1-deploy-dev.yml`, set the workflow-level env
   `ENABLE_CONTAINER_STAGE` to `"true"`. Commit and push.
2. Watch the `containerize` job run the full path: build the image, scan it with Trivy
   (any HIGH/CRITICAL fails the run), sign it with Cosign via KMS, and push it to ECR.
3. In the AWS console (or CLI), confirm the image exists in your ECR repository and that
   a Cosign signature artifact sits alongside it.
4. Confirm the digest the build emitted (`image_digest` job output) matches the digest of
   the image in ECR.

**Success criterion:** a scanned, signed image is in ECR and the build's emitted digest
matches the registry digest.

---

## Segment 3 — Dev deploy

1. With a green validate (and a signed image, or a `CONTAINER_IMAGE_URI` variable set to
   an existing signed image), let the `deploy-dev` job run.
2. Review the `terraform plan` output in the job log before the apply.
3. Watch the SageMaker endpoint provision (typically **4–6 minutes**).
4. Invoke the endpoint with [tests/smoke/sample-payload.json](tests/smoke/sample-payload.json)
   and confirm the response shape matches
   [tests/smoke/known-input-output.json](tests/smoke/known-input-output.json):
   `income_over_50k: false` with a probability inside the documented range.

**Success criterion:** the dev endpoint is live and returns the expected prediction for
the sample payload.

---

## Segment 4 — Promote to production

1. Open a PR from a `promote-to-staging` branch into `main`. Merging it triggers the
   **Deploy Staging** workflow, which validates, **verifies the existing signed image
   digest (no rebuild)**, and applies staging.
2. When staging is healthy, run the **Deploy Production** workflow manually
   (`workflow_dispatch`) with input `change_ticket_reference=LAB-001`.
3. Approve at the production environment gate (the required reviewer prompt).
4. Note the separation-of-duties step: it compares the change author to the deploy actor.
   On a single-user demo account it warns and continues; **to exercise the blocking path,
   use two GitHub accounts** — have one account author/merge the change and a different
   account trigger and approve the production deploy, then set `ENFORCE_SOD=true` to make
   the mismatch required.
5. After apply, confirm the endpoint is live, then check the audit bucket: there is a new
   object at `audit/<YYYY-MM-DD>/<commit-sha>.json` with all 15 fields, including
   `schema_version: 1` as the first key.

**Success criterion:** production is live and a complete audit-trail entry (15 fields,
`schema_version: 1`) exists for the deploy.
