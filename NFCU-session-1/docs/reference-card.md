% Session 1 Reference Card — ML Deployment Pipelines

## The five non-negotiables

1. **Traceability.** Every production prediction traces to its training data via an
   immutable audit record. If you can't trace it, you can't ship it.
2. **No long-lived credentials.** Workflows assume AWS roles through OIDC. No stored
   access keys, anywhere.
3. **Artifacts stay in the VPC.** Endpoints run in private subnets; SageMaker and ECR
   traffic uses VPC endpoints. Nothing model-related crosses the public internet.
4. **Production requires approval.** A change ticket, an environment reviewer, and a
   separation-of-duties check gate every production deploy.
5. **Rollback is one click.** Deploys are digest-pinned and bounded by a rolling-update
   policy; a failed update rolls back rather than landing half-applied.

## The four-stage pipeline

```
[1] VALIDATE        [2] BUILD/SCAN/SIGN   [3] DEPLOY         [4] APPROVE+AUDIT
  schema check        digest-pinned base    private subnets    change ticket
  reject mutable      Trivy HIGH/CRIT=fail  KMS-encrypted      reviewer gate
  policy check        Cosign sign (KMS)     signed digest      approver!=author
      |                     |                    |                   |
      +-> green ----------> +-> signed digest -> +-> live --------->  +-> audit record
```

## The five-minute test

> Can you trace any prediction your model made, all the way back to the data it was
> trained on, in under five minutes? Prediction → audit record → training run id →
> dataset hash. If the answer isn't "yes," the pipeline isn't done.

## Three Monday actions

1. **Pin your actions.** Replace every third-party Action tag with its full commit SHA
   this week. Start with anything that installs a binary.
2. **Kill one long-lived key.** Pick one CI pipeline still using stored AWS keys and move
   it to OIDC role assumption.
3. **Write one audit record.** Add a single immutable deploy-event write to your most
   important model's pipeline — even before you have the rest of this.
