# Deterministic policy rules (v0.1)

These rules are a transparent preflight protocol, not a legal standard. They compare declarations supplied by the user; they do not validate whether those declarations are legally sufficient or authentic.

## Precedence

```text
explicit prohibition > explicit conditional permission > explicit permission > missing evidence
```

An explicit prohibition always yields `BLOCKED`. If no prohibition exists but a requested action is not explicitly covered, the result is `UNKNOWN`. Conditional requirements that cannot be checked from the input yield `NEEDS_REVIEW`.

## Starter vocabulary

Operations: `read_fields`, `aggregate_statistics`, `cross_dataset_linkage`, `individual_level_model`, `public_release`, `commercial_use`.

Output granularity, from least to most specific: `aggregate`, `group`, `individual`.

## Rule IDs

| Rule | Meaning |
| --- | --- |
| `PURPOSE-EXPLICIT-PROHIBITION` | The declared purpose is explicitly excluded. |
| `PURPOSE-EXPLICIT-PERMISSION` | The declared purpose is explicitly covered. |
| `PURPOSE-MISSING-EVIDENCE` | No declared purpose coverage was supplied. |
| `OP-EXPLICIT-PROHIBITION` | A requested operation is explicitly prohibited. |
| `OP-EXPLICIT-PERMISSION` | A requested operation is explicitly allowed. |
| `OP-MISSING-EVIDENCE` | The policy does not establish coverage. |
| `OUTPUT-GRANULARITY-EXCEEDS-MAX` | The planned output is more specific than the declared maximum. |
| `OUTPUT-AUDIENCE-PROHIBITED` | The planned audience is explicitly excluded. |
| `SHARE-EXPLICIT-PROHIBITION` | Redistribution is planned but prohibited. |
| `COMMERCIAL-EXPLICIT-PROHIBITION` | Commercial use is planned but prohibited. |
| `FIELD-EXPLICIT-PROHIBITION` | A requested field is explicitly prohibited. |
| `FIELD-MISSING-EVIDENCE` | No field-level permission was supplied. |

The engine never promotes an inference to an explicit policy statement. If a natural-language document is ambiguous, convert it to a structured declaration and put the ambiguity in the review queue.
