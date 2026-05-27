# Why This Lab Uses Lambda Fan-Out (Not Native SageMaker Shadow)

**SageMaker has native shadow support.** `ShadowProductionVariants` has been
generally available since re:Invent 2022: you declare a production variant and a
shadow variant on the same endpoint, SageMaker mirrors a configurable share of
inference requests to the shadow variant, returns only the production variant's
response to the caller, and captures shadow responses for analysis. Promotion is
a native `update-endpoint` operation. If your serving stack is SageMaker and you
want shadow testing in production, that feature is the right tool, and you should
use it.

This lab deliberately does **not** use it. The choice is pedagogical, not a
limitation of SageMaker.

The lab implements shadow deployment as an explicit Lambda fan-out: a function
behind an API Gateway HTTP API invokes the champion synchronously and the
challenger asynchronously, then a scheduled comparison Lambda joins the two
responses and computes agreement, latency, and disparate-impact metrics. We made
this choice for three reasons:

1. **Portability.** The same pattern works against a SageMaker endpoint, an ECS
   service, an on-prem Kubernetes deployment, or any HTTP-serving inference
   backend. Attendees leave with a pattern that is not bound to a single cloud
   feature.

2. **Inspectable mechanics.** The comparison logic is ordinary Python that
   attendees can read, modify, and reason about — request correlation by UUID,
   async isolation so a failing challenger never affects the caller, offline
   joining of responses, and a gated promotion. With the managed feature, those
   mechanics are real but hidden inside SageMaker.

3. **Transferable understanding.** Once you understand the fan-out — how
   requests are mirrored, correlated, compared, and gated — you understand what
   `ShadowProductionVariants` and Istio/Seldon mirroring do for you. The pattern
   generalizes; the managed feature is one optimized instance of it.

So treat the fan-out as a teaching scaffold. In a real SageMaker deployment you
would likely reach for `ShadowProductionVariants` and let AWS handle the
mirroring. The point of building it by hand here is to make the moving parts
visible, so the abstraction is something you understand rather than something you
trust blindly.
</content>
