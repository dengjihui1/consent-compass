---
name: consent-compass
description: Compare a declared dataset-use policy with an intended analysis plan and produce an evidence-grounded preflight report. Use before analysing, linking, modelling, or sharing research data; do not use it as legal, IRB, or privacy advice.
---

# Consent Compass

Consent Compass is a data-use preflight, not a compliance oracle. Its job is to make the boundary between a dataset's declared use and a planned analysis explicit before code runs.

## Required behavior

1. Read the dataset policy and analysis intent from the user-provided files. Do not request or upload raw records when metadata is enough.
2. Normalize only observable declarations: purpose, operations, fields, linkage, output granularity/audience, redistribution, commercial use, and retention.
3. Apply the deterministic rules in `references/policy-rules.md`. Explicit prohibitions override permissions; missing evidence is `UNKNOWN` or `NEEDS_REVIEW`, never an implicit approval.
4. Return each finding with its rule, source location, requested operation, policy value, and a conservative explanation.
5. Use these final states: `ALLOWED`, `NEEDS_REVIEW`, `BLOCKED`, and `UNKNOWN`. `ALLOWED` means only that the supplied declarations cover the request under the starter rules.
6. Offer a lower-risk alternative only as a proposal, such as aggregate output or separate analysis. Never silently rewrite the user's research plan.
7. State clearly that the result is not legal advice, ethics approval, a consent determination, or permission to publish.

## Recommended workflow

```text
python scripts/compass.py check --policy demos/biobank-policy.json --intent demos/linkage-intent.json --output out
```

Inspect both `out/BOUNDARY_REPORT.md` and `out/boundary-decision.json`. Use `references/policy-rules.md` when a rule or state is unclear, and `references/schema.md` when authoring new policy or intent files.

Do not expose personal records, identifiers, credentials, or full restricted consent documents in a public demo. The repository's fixtures are synthetic.
