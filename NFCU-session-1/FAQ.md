# FAQ

Nine questions that come up most often about this pipeline.

## 1. Why GitHub Actions and not Jenkins / GitLab / CircleCI?

Nothing here is GitHub-specific in spirit — it's validation, signing, traceable
deploys, and audit. GitHub Actions is used because OIDC federation to AWS (no
long-lived keys) is first-class, the marketplace makes the supply-chain pinning lesson
concrete, and most attendees can fork and run it for free. The same pattern ports to
Jenkins (with the AWS plugin and an OIDC provider), GitLab CI (native OIDC and
environments), or CircleCI. The portable parts are the artifact contract, the signed
digest, and the audit record — not the YAML dialect.

## 2. Why Terraform and not CDK or Pulumi?

Terraform's plan/apply split makes the review gate explicit, and HCL is readable by
reviewers who don't write the language daily — which matters when a control gets
audited. CDK and Pulumi are excellent if your team already lives in TypeScript or
Python and wants real programming constructs. The design here would translate directly:
the same module boundaries (networking, endpoint), the same digest validation, the same
environment separation. We pin Terraform `>= 1.14` because 1.13 is end-of-life.

## 3. How does this work for HuggingFace models?

The same way. Swap the training script for your HuggingFace download/fine-tune step and
package the model into the same artifact contract (`model.xgb` becomes your weights,
`inference.py` becomes your handler, `signature.json`/`metadata.json`/`model_card.md`
stay). The container's base image changes to a PyTorch/Transformers serving image, but
validation, signing, the deploy gates, and the audit record are unchanged. The point of
the artifact contract is that the pipeline doesn't care what's inside the tarball, only
that it's complete, immutable, and traceable.

## 4. What if our model registry is MLflow, not Unity Catalog or SageMaker Model Registry?

Fine — the registry is an implementation detail behind two facts the pipeline needs: an
immutable version identifier and a resolvable artifact URI. With MLflow, the model
version (e.g. `models:/my-model/3`) becomes the immutable reference `validate.py`
checks, and the artifact URI points at MLflow's backing store. You'd add a small step to
resolve the MLflow version to its S3 path before the container build. The mutable-alias
rejection still applies: deploy by version number, never by the `champion`/`latest`
alias.

## 5. How do you handle model dependencies that conflict across models?

Containers. Each model ships its own image with its own pinned dependencies, so two
models needing incompatible library versions never share a runtime. That's the main
reason the artifact is packaged into a container rather than dropped onto a shared host.
The base image gives you a common, scanned floor; each model layers exactly what it
needs on top. Conflicts become a build-time concern isolated per model, not a
production-time collision.

## 6. Can I skip the staging environment for low-risk models?

You can collapse staging, but don't skip what staging does. Its real job here is to
prove that the **already-signed dev image** deploys cleanly to a fresh environment
without a rebuild — catching environment drift, not model defects. For a genuinely
low-risk model you might run dev and production only, but keep the "verify the existing
digest, don't rebuild" step in production. The cost of staging is minutes; the cost of
discovering an environment-specific failure in production is an incident.

## 7. How long does this scale to? 1000 models?

The per-model mechanics (validate, sign, deploy, audit) are independent and parallel, so
the pipeline itself scales horizontally. What doesn't scale linearly is the human review
gate and per-endpoint cost — 1000 always-on endpoints is expensive. At that scale you
move toward multi-model endpoints, scale-to-zero serving, and tiered review (auto-approve
low-risk model classes, human gate the rest). Session 2 (champion-challenger) and Session
4 (KServe) address the serving-density and routing side of this directly.

## 8. What's the cost overhead of all this audit machinery?

Negligible. The audit record is a single small JSON object written to S3 per production
deploy — fractions of a cent in storage and requests. Trivy and Cosign run in CI minutes
you're already paying for. The real "overhead" is the few minutes added to each deploy by
the gates, which is the point: the machinery costs less than one post-incident audit
scramble where nobody can say which data trained the model that made a given prediction.

## 9. Does this satisfy SR 11-7?

It supports SR 11-7; no tool "satisfies" it on its own. SR 11-7 is about model risk
management — development standards, validation, and governance. This pipeline provides
the technical evidence: immutable versioning, a model card documenting limitations, an
approval gate with separation of duties, and an immutable audit trail linking each
production model to its training data and approver. The model risk *program* — independent
validation, ongoing monitoring (Session 3), documented governance — is what your second
line of defense owns. This gives them auditable artifacts to point at.
