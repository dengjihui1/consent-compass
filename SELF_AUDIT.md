# Self-audit

## Product boundary

Consent Compass compares user-supplied declarations. It does not establish that a policy is authentic, legally sufficient, or applicable to a jurisdiction. `ALLOWED` is deliberately scoped to the supplied policy and starter rules.

## Evidence boundary

Every finding carries a rule identifier and the policy evidence references available in the input. The engine does not invent citations. Empty evidence is shown as empty in the report.

## Privacy boundary

The MVP accepts metadata JSON and does not need raw records. The repository uses synthetic fixtures. The `.gitignore` excludes generated output, caches, and zip files from source history.

## Known limitations

- The executable MVP accepts JSON; natural-language policy interpretation is intentionally outside the deterministic engine.
- Conditional permissions are reserved for future policy fields and must be reviewed rather than inferred.
- This is not an IRB, ethics, privacy, or legal decision system.
- The starter vocabulary is deliberately narrow and unknown operations become review findings.

## Claims not made

The project does not claim universal regulatory coverage, automatic consent verification, safe de-identification, or permission to publish. These constraints are part of the product design, not disclaimers added after the fact.
