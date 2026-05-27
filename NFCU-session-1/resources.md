# Resources

Annotated reading list for going deeper on the regulatory, supply-chain, and
bill-of-materials topics behind this pipeline.

## Model risk and financial-services supervision

- **[SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm)** —
  The Federal Reserve's foundational guidance on model risk. Defines model development
  standards, validation, and governance. The "why" behind the model card, approval gate,
  and audit trail in this pipeline.
- **[FFIEC IT Examination Handbook](https://ithandbook.ffiec.gov/)** —
  The interagency examination framework for IT and operational controls. Relevant to the
  change-management, access, and audit-logging expectations the deploy gates implement.
- **[NCUA supervisory references](https://ncua.gov/regulation-supervision)** —
  Supervisory and examination material applicable to credit-union-sector institutions;
  useful context for how model and IT risk expectations land for that charter type.

## Supply-chain and AI security

- **[OWASP Top 10 for LLM Applications (Nov 2025 revision)](https://owasp.org/www-project-top-10-for-large-language-model-applications/)** —
  See especially **LLM03 (Supply Chain)** and **LLM04 (Data and Model Poisoning)** — the
  exact risks the digest pinning, signature verification, and dataset hashing here defend
  against.
- **[SLSA Framework](https://slsa.dev/)** —
  Supply-chain Levels for Software Artifacts. This pipeline targets **SLSA Level 3**:
  signed provenance, a hardened build, and non-falsifiable build metadata.

## Bills of materials for ML

- **[CycloneDX (v1.5+) ML-BOM](https://cyclonedx.org/capabilities/mlbom/)** —
  The machine-learning bill-of-materials extension: a standard way to enumerate model,
  dataset, and dependency components. The natural next step after the metadata contract
  used here.
- **[OWASP AIBOM Project (2025)](https://owasp.org/www-project-ai-bom/)** —
  Emerging guidance on AI bills of materials — what an AI system inventory should capture
  for governance and incident response.

## Regulation in flight

- **[EU AI Act — Digital Omnibus political agreement (May 7, 2026)](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)** —
  Political agreement that defers several high-risk obligations (to December 2027 and
  August 2028). Track for timelines if you operate in or serve the EU.
- **[U.S. Treasury — Financial Services AI Risk Management](https://home.treasury.gov/)** —
  Treasury's work on AI risk in financial services; sets the direction of travel for
  sector-specific expectations.
- **[Colorado AI Act (SB 24-205)](https://leg.colorado.gov/bills/sb24-205)** —
  One of the first comprehensive U.S. state AI laws focused on high-risk systems and
  consumer protection; a bellwether for state-level obligations.
