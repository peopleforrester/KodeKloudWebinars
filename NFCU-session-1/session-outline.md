# Session 1 — Presenter Outline: ML Deployment Pipelines

**Format:** ~2 hours, live demo. Audience: DevOps engineers at a regulated financial
services organization. The spine of the session is one question, returned to at the
start and the end:

> Can you trace any prediction your model made, all the way back to the data it was
> trained on, in under five minutes?

This outline is the public-safe version of the speaker notes; it preserves the slide
flow so anyone can re-run the session.

---

## Slide 1 — The opening question (5 min)

Pose the trace question cold. Ask for a show of hands: who could answer it for a model
in production today? Most cannot. Frame the session: we will build the pipeline that
makes the answer "yes, in five minutes," and we will do it the way a regulated FS shop
has to — auditable, least-privilege, no long-lived credentials.

## Slide 2 — Why this is hard (8 min)

The gap between "the model works in a notebook" and "the model is safely in production
and accountable." Three failure modes: untraceable artifacts (which data? which run?),
mutable references (`latest` deployed something — what?), and unsigned images (is this
the bytes we scanned?). These are governance failures, not modeling failures.

## Slide 3 — The artifact contract (10 min)

Introduce the model artifact: a single immutable tarball containing the model, its
inference handler, a signature, metadata (training run id, dataset hash, evaluation),
and a model card. Show the sample model card — including its explicitly documented
limitations. The pipeline never inspects what the model *is*; it enforces that the
artifact is complete, versioned, and traceable.

## Slide 4 — Stage 1: Validation (15 min, live)

Run `validate.py` against a good artifact (green). Then set the model version to
`latest` and run it again — watch it fail with one clear line, exit code 2. Make the
point: the gate rejects mutable references before anything is built. This is the
deliberate failure attendees reproduce in the lab.

## Slide 5 — Stage 2: Build, scan, sign (20 min, live)

Build the serving image from a digest-pinned base. Scan with Trivy — any HIGH or
CRITICAL fails the build. Tell the supply-chain story: the March 2026 incident where a
scanner's own action tags were force-pushed to malicious commits, and why every
third-party action here is pinned by full commit SHA. Sign the image with Cosign backed
by KMS. The output is an immutable, scanned, signed digest.

## Slide 6 — Stage 3: Traceable deploy (20 min, live)

Terraform applies the endpoint into private subnets, KMS-encrypted, from the signed
digest — never a tag. Show the security defaults baked into the module: no public
ingress path, encryption on by default, a caller-supplied execution role rather than a
shared one. Deploy to dev, invoke with the sample payload, get a prediction.

## Slide 7 — Stage 4: Approval and audit (15 min, live)

Promote to production: a manual trigger with a change ticket, an environment reviewer
gate, and a separation-of-duties check (the approver should not be the change author).
On apply, the final step writes the audit record to object storage — every field needed
to trace the deploy, with a schema version as the first key.

## Slide 8 — The five-minute trace, answered (10 min, live)

Now answer the opening question for real. Take a prediction, pull the audit record for
that deploy, read the training run id and dataset hash, and walk from prediction to the
exact training data — live, with a stopwatch. This is the payoff.

## Slide 9 — No long-lived credentials (8 min)

Explain OIDC federation: workflows assume a role via short-lived tokens, scoped to this
repository. Contrast with stored access keys. Note the production-grade pattern
(per-environment roles scoped to an environment claim) versus the lab simplification.

## Slide 10 — What you take home (6 min)

The repository is the take-home. Point at the lab guide and the reference card. The five
non-negotiables. Preview the next three sessions: champion-challenger, monitoring and
drift, and Kubernetes-native serving — each builds on the endpoint and audit foundation
laid today.

## Slide 11 — Q&A (15 min)

Use the FAQ as a backstop: framework choices, other model types, registries,
dependency conflicts, scale, cost, and how this maps to model-risk expectations.
