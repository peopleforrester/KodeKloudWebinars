# Day 60 Decision Gate Checklist

Use this checklist in the Day 60 gate review meeting. Every item in sections 1 and 2 must be checked before making the go/no-go decision in section 3. If you can't check an item, that's data — it tells you what's missing.

Print this or share it on screen. Walk through it item by item. Don't skip items because you're "pretty sure" they're covered.

---

## 1. Data Requirements

All of these must be in place before the meeting. If any are missing, the meeting is premature — reschedule once the data exists.

- [ ] **30+ agent recommendations logged and reviewed.** Not 30 recommendations generated — 30 recommendations where a human reviewed the agent's output and recorded whether they agreed, modified, or rejected it. If volume is below 30 after 30 days, extend the validation period.

- [ ] **Recommendation accuracy rate calculated.** (Accepted without modification / total recommendations) × 100. This is the primary metric for the go/no-go decision. Have the exact number ready, not an estimate.

- [ ] **False positive rate calculated.** (Recommendations where the agent identified the wrong root cause / total recommendations) × 100. Track separately from "recommendations the human modified" — a modified recommendation is not the same as a wrong one.

- [ ] **Human override frequency tracked.** (Recommendations rejected or significantly modified / total recommendations) × 100. Bring the trend line, not just the aggregate — is override frequency stable, declining, or increasing?

- [ ] **Net time saved documented with actual numbers.** Total estimated time saved by agent recommendations minus total time engineers spent reviewing recommendations. This should come from engineer self-reports, not assumptions. If net time saved is negative or negligible, that's important data for the decision.

---

## 2. Governance Requirements

All of these must be in place. These are the guardrails that make expanding agent scope responsible rather than reckless.

- [ ] **IAM policy for agent service principal documented and reviewed.** The dedicated service account used by the agent has a documented permission set. A human has reviewed it against the principle of least privilege. It's committed to the repository alongside the permission matrix.

- [ ] **Permission matrix committed and reviewed by security.** The [permission matrix](../agent-boundary-design/permission-matrix-template.md) defining agent IAM scope is committed to the repository and reviewed by the security team. If an AGENTS.md file is also in use (for coding agent codebase context), it should be committed and reviewed as well — but the permission matrix is the governance artifact.

- [ ] **Eval suite passing on all 10 baseline scenarios.** The eval suite built during Days 1–30 has been run against the current agent configuration and passes with a score of 8/10 or higher. Bring the most recent eval results to the meeting.

- [ ] **Observability dashboard live and showing last 30 days.** The agent observability dashboard (token cost, recommendation accuracy, override frequency, tool call patterns) is live and populated with at least 30 days of data. If anyone at the meeting can't access it, fix that before making a decision.

---

## 3. Go / No-Go Decision

Walk through the decision tree in order. Stop at the first matching condition.

### If any data requirement (Section 1) is NOT met:

**Decision: Extend Days 31–60 by two weeks.**

Identify which data requirement is missing and assign an owner to close the gap. Do not proceed to the expansion phase with incomplete data — the whole point of this gate is to make the expansion decision on evidence, not optimism.

### If all data requirements are met AND recommendation accuracy is ≥70%:

**Decision: Proceed to Days 61–90.**

Begin planning the second use case (AI-assisted incident triage). Carry forward all governance requirements — the incident triage agent gets its own permission matrix and its own eval suite.

### If all data requirements are met but recommendation accuracy is <70%:

**Decision: Diagnosis required before proceeding.**

Do not proceed to Days 61–90. Do not extend indefinitely. Instead, diagnose the accuracy gap using this decision tree:

1. **Review the false positive cases.** Categorize them. Are the failures concentrated in specific types of CI failures, or spread evenly? Concentration means the agent lacks context for that specific failure type. Spread means a broader context problem.

2. **Check the AGENTS.md and context configuration.** In the majority of sub-70% cases, the issue is insufficient context, not a model capability problem. The agent doesn't have enough information about your specific environment to reason accurately. Adding detail to the AGENTS.md — how your test database is configured, what your deployment pipeline stages mean, how your monorepo is structured — often has more impact than any prompt change.

3. **Evaluate whether the use case is right.** Some CI failure types require architectural knowledge or institutional context that can't be captured in documentation. If your most common failures involve complex cross-service interactions that aren't documented anywhere, the agent is being asked to reason without sufficient information. Consider narrowing to failure types the agent can realistically diagnose.

4. **Set a specific improvement target and timeline.** "We'll improve context and try again" is not a plan. "We'll add environment documentation to AGENTS.md, re-run the eval suite, and review accuracy again in two weeks" is a plan.

---

## After the Meeting

Regardless of the decision, document the outcome and share it with the team:

- The decision (go, extend, or diagnose)
- The key metrics that drove the decision
- Action items with owners and timelines
- The date of the next review

This documentation becomes part of your organizational learning. When another team runs their own pilot, your Day 60 gate review is the most useful reference they'll have.
