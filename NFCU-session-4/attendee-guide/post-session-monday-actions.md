# Post-Session: Monday Morning Actions

Three concrete things to do the week after, while it's fresh. Each is small and pays off.

## 1. Re-run one lab from memory

Pick the lab that mattered most to your work and run it again without the recording, using
only the walkthrough. Lab 4 (canary) is the usual choice — it's the one people most want to
apply. If you get stuck, that's exactly the gap to close now, not during an incident.

## 2. Map one real model onto the InferenceService shape

Take a model your team actually serves and sketch its `InferenceService`:

- What's its `modelFormat` (or is it a custom predictor like the LLM)?
- What `containerConcurrency` matches its real per-pod capacity?
- Would scale-to-zero help (spiky traffic) or hurt (latency-sensitive, always-on)?
- What would a canary of its next version look like?

You don't have to deploy it — the exercise is translating your reality into this model.

## 3. Put one number on the table

Run OpenCost (or your existing cost tooling) against one serving workload and bring a single
number to your next platform sync: "model X costs roughly $Y/day to serve." Cost
attribution only changes decisions once it's visible. One number starts that.

## Optional: reproduce end-to-end

If you want the whole thing on your own cluster, follow
[`reproduce-on-your-aws-account.md`](reproduce-on-your-aws-account.md) (cost-anchored) or
the no-spend [`local kind path`](../cluster/local/README.md).

## Keep

This whole directory is yours to keep and adapt. The manifests, the predictor, the k6
scripts, and the Terraform are deliberately small enough to read in an afternoon.
