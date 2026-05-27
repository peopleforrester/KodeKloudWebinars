# UCI Adult fixtures (session-local)

**Ownership:** session-local to NFCU Session 3. This is a Session 3-owned copy so
the lab is self-contained and does not depend on Sessions 1/2/4 being built. A
future session may copy these into its own `shared/` or reference these paths —
that is the consuming session's call, not Session 3's.

## Contents

- `adult.test` — the real UCI Adult **test split** (16,281 labelled rows + 1
  header comment line), downloaded from the UCI Machine Learning Repository. Raw
  format: comma-space separated, no header, trailing `.` on the income label, and
  a `|1x3 Cross validator` comment on line 1.
- `adult.names` — the UCI column/feature documentation.

## The 8 lab features

The Session 1/2 model is framed as an 8-feature binary income classifier
(`>50K` vs `<=50K`). The lab uses these 8 input features:

| Feature | Type | Notes |
|---|---|---|
| `age` | numeric | |
| `workclass` | categorical | set to NULL by the `feature_pipeline_broken` incident |
| `education_num` | numeric | ordinal education level |
| `marital_status` | categorical | |
| `occupation` | categorical | |
| `race` | categorical | |
| `sex` | categorical | |
| `hours_per_week` | numeric | the drift target in Lab 2 (`+ Normal(15, 5)`) |

`fnlwgt`, `education` (redundant with `education_num`), `relationship`,
`capital_gain`, `capital_loss`, and `native_country` are present in the raw file
but are not among the 8 lab features.

## Why UCI Adult (D5)

The dataset is academically dated (Ding et al., "Retiring Adult", NeurIPS 2021,
recommends `folktables`/ACSIncome). It is preserved here for series continuity and
framed in the lab as a stand-in for **any** production binary classifier. A
refresh is a candidate for the next iteration, not this build.
