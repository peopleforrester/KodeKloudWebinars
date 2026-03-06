# Eval Framework

Eval-driven development is the same discipline as TDD applied to agents. If you wouldn't deploy code without tests, don't deploy agents without evals. The eval suite defines what correct agent behavior looks like — including when the correct behavior is expressing uncertainty or deferring to a human — and it runs before deployment, after any context change, and on a weekly sample of production runs to detect drift.

See [eval-suite-starter.md](eval-suite-starter.md) for the starter framework with 10 complete scenarios.
