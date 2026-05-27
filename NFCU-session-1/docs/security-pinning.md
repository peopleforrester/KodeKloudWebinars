# Why we pin third-party Actions by commit SHA

## The March 19, 2026 supply-chain compromise

On March 19, 2026, the GitHub Actions published by the Trivy project were compromised by
tag manipulation:

- **`aquasecurity/trivy-action`** — 75 of its 76 version tags were force-pushed to point
  at malicious commits. Anyone referencing the action by tag (`@v0.x`, `@v1`, etc.)
  silently started running attacker-controlled code on their next run.
- **`aquasecurity/setup-trivy`** — all 7 of its tags were force-pushed the same way.
- The associated poisoned Trivy binary builds were **`v0.69.4`, `v0.69.5`, and
  `v0.69.6`**. This is why this repo requires Trivy **`>= 0.70.0`** and treats those three
  releases as explicitly blocked.

The lesson: **a Git tag is a mutable pointer.** A tag you trusted yesterday can point at
different code today. The only immutable reference to a commit is its full 40-character
SHA.

## The mitigation: pin every third-party action by full commit SHA

In every workflow under `.github/workflows/nfcu-session-1-*.yml`:

- **Third-party actions** (anything not owned by GitHub) are referenced by their full
  40-character commit SHA, with the human-readable tag in a trailing comment.
- **GitHub-owned actions** (`actions/*`) and AWS's (`aws-actions/*`) may use a major
  version tag, because GitHub/AWS control those repositories.

A pinned SHA cannot be force-pushed out from under you: if the upstream repo is
compromised, your workflow keeps running the exact commit you reviewed until you
deliberately bump it.

## Bad vs. good

```yaml
# BAD — mutable tag; this is exactly what the March 2026 attack exploited.
- uses: aquasecurity/setup-trivy@v0.2.6
- uses: aquasecurity/trivy-action@master
- uses: sigstore/cosign-installer@v3

# GOOD — immutable 40-char commit SHA, tag kept as a comment for readability.
- uses: aquasecurity/setup-trivy@3fb12ec12f41e471780db15c232d5dd185dcb514  # v0.2.6
- uses: hashicorp/setup-terraform@b9cd54a3c349d3f38e8881555d616ced269862dd  # v3
- uses: sigstore/cosign-installer@398d4b0eeef1380460a10c8013a76f728fb906ac  # v3
```

## How to look up the SHA for a tag

```bash
# List a repo's tags and their object SHAs without cloning it.
git ls-remote https://github.com/aquasecurity/setup-trivy

# For an annotated tag, the line ending in ^{} is the commit the tag dereferences to —
# that is the SHA to pin.
git ls-remote https://github.com/sigstore/cosign-installer 'refs/tags/v3*'
```

Review the commit the SHA points at before you pin it, then record the tag in a comment
so the next maintainer knows which version that SHA corresponds to. Bump deliberately:
re-run `git ls-remote`, review the diff, and update the SHA — never switch back to a tag
for convenience.

## Related lab-platform note

The OIDC trust in `lab-platform-iac` is repo-scoped (`repo:<org>/<repo>:*`) as a
deliberate lab simplification. The production pattern is per-environment roles whose trust
is narrowed to a specific environment claim
(`repo:<org>/<repo>:environment:production`), so a dev workflow can never assume the
production role. Same principle as SHA pinning: narrow the trust to exactly what you
reviewed.
