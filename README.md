# Consent Compass

> Before you analyse the data, check whether the declared boundary covers what you plan to do.

Consent Compass is a local-first, zero-dependency Python Skill and CLI that compares a structured dataset-use policy with an analysis intent. It catches explicit mismatches such as prohibited record linkage, individual-level output, unapproved audiences, and missing redistribution evidence before analysis code runs.

It is intentionally not a legal, ethics, IRB, privacy, or consent oracle. `ALLOWED` means only that the supplied declarations cover the requested use under the starter rules. Ambiguity remains visible as `UNKNOWN` or `NEEDS_REVIEW`.

## The 30-second demo

From this directory:

```powershell
python scripts/compass.py check `
  --policy demos/biobank-policy.json `
  --intent demos/linkage-intent.json `
  --output demo-out
```

This intentionally unsafe synthetic intent should produce `BLOCKED` and write:

```text
demo-out/
├── boundary-decision.json
├── BOUNDARY_REPORT.md
└── BOUNDARY_REPORT.html
```

Run the safe aggregate example:

```powershell
python scripts/compass.py check `
  --policy demos/biobank-policy.json `
  --intent demos/aggregate-intent.json `
  --output aggregate-out
```

## Why this is different

- It checks the **intended operation**, not merely whether a user can open a file.
- It compares data-use boundaries with planned fields, linkage, output granularity, audience, redistribution, and commercial use.
- It uses explicit rule IDs and source locations instead of a single unexplained risk score.
- It never turns missing evidence into permission.
- It can run without raw records, network access, an API key, or a model.

## Input and output

See [references/schema.md](references/schema.md) for the v0.1 JSON shape and [references/policy-rules.md](references/policy-rules.md) for the deterministic protocol.

The report states one of four statuses:

| Status | Meaning |
| --- | --- |
| `ALLOWED` | Supplied declarations cover the request under the starter rules. |
| `NEEDS_REVIEW` | A condition or human policy-owner interpretation is required. |
| `BLOCKED` | An explicit prohibition conflicts with the request. |
| `UNKNOWN` | The supplied evidence does not establish coverage. |

## Development

```powershell
python -m unittest discover -s tests -v
python scripts/compass.py check --policy demos/biobank-policy.json --intent demos/linkage-intent.json --output demo-out
```

The repository contains synthetic fixtures only. Do not commit real participant data, identifiers, credentials, restricted consent documents, or institutional approval records.

## Research question

Can a transparent, metadata-only preflight catch data-use boundary mismatches early enough to change an analysis plan, while keeping uncertainty and human review visible? The MVP makes this question testable with synthetic policy/intent pairs and a deterministic baseline.

## License

MIT. See [LICENSE](LICENSE).
