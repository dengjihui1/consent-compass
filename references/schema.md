# Input schema (v0.1)

Consent Compass accepts JSON objects. JSON is used in the zero-dependency MVP so the executable remains reproducible on a clean Python installation. YAML can be converted to this shape before running the checker.

## Dataset policy

```json
{
  "dataset": {"id": "synthetic-biobank", "version": "2026-01"},
  "scope": {
    "allowed_purposes": ["disease_research"],
    "prohibited_purposes": ["employment_screening"],
    "allowed_operations": ["read_fields", "aggregate_statistics"],
    "prohibited_operations": ["cross_dataset_linkage", "individual_level_model"],
    "output": {"max_granularity": "aggregate", "allowed_audiences": ["internal"]},
    "redistribution": "prohibited",
    "commercial_use": "unknown",
    "field_rules": {"participant_id": "prohibited", "diagnosis": "allowed"}
  },
  "evidence": {
    "purpose": ["policy.md:4"],
    "operations": ["policy.md:12"],
    "output": ["policy.md:18"],
    "sharing": ["policy.md:22"],
    "fields": ["policy.md:26"]
  }
}
```

## Analysis intent

```json
{
  "id": "intent-linkage-demo",
  "analysis": {
    "purpose": "disease_research",
    "operations": ["read_fields", "cross_dataset_linkage", "individual_level_model"],
    "fields": ["participant_id", "diagnosis"],
    "output": {"granularity": "individual", "audience": "public"},
    "redistribution": true,
    "commercial": false
  }
}
```

Unknown or omitted policy fields are not interpreted as permission. A policy may include additional fields, but the MVP only evaluates the vocabulary documented in `references/policy-rules.md`.
