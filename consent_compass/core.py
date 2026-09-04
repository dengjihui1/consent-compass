"""Core policy-to-intent comparison for Consent Compass.

The engine is deliberately conservative: it reports evidence and gaps rather
than making legal or ethical conclusions.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional

ALLOWED = "ALLOWED"
REVIEW = "NEEDS_REVIEW"
BLOCKED = "BLOCKED"
UNKNOWN = "UNKNOWN"


def _scope(policy: Dict[str, Any]) -> Dict[str, Any]:
    return policy.get("scope", {}) or {}


def _evidence(policy: Dict[str, Any], key: str) -> List[str]:
    refs = policy.get("evidence", {}) or {}
    value = refs.get(key, [])
    if isinstance(value, str):
        return [value]
    return list(value or [])


def _list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


def _contains(values: Any, requested: str) -> bool:
    items = _list(values)
    return requested in items or "*" in items


def _finding(
    finding_id: str,
    status: str,
    category: str,
    requested: Any,
    policy_value: Any,
    explanation: str,
    rule_id: str,
    evidence: Iterable[str],
    alternative: Optional[str] = None,
) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "id": finding_id,
        "status": status,
        "category": category,
        "requested": requested,
        "policy_value": policy_value,
        "explanation": explanation,
        "rule_id": rule_id,
        "evidence": list(evidence),
    }
    if alternative:
        item["lower_risk_alternative"] = alternative
    return item


def _purpose_finding(policy: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    scope = _scope(policy)
    purpose = (intent.get("analysis", {}) or {}).get("purpose")
    allowed = _list(scope.get("allowed_purposes"))
    prohibited = _list(scope.get("prohibited_purposes"))
    evidence = _evidence(policy, "purpose")
    if not purpose:
        return _finding("purpose-1", UNKNOWN, "purpose", None, allowed,
                        "No analysis purpose was supplied.", "PURPOSE-MISSING", evidence)
    if purpose in prohibited or "*" in prohibited:
        return _finding("purpose-1", BLOCKED, "purpose", purpose, prohibited,
                        "The declared policy explicitly excludes this purpose.",
                        "PURPOSE-EXPLICIT-PROHIBITION", evidence)
    if _contains(allowed, purpose):
        return _finding("purpose-1", ALLOWED, "purpose", purpose, allowed,
                        "The declared purpose is explicitly covered.",
                        "PURPOSE-EXPLICIT-PERMISSION", evidence)
    return _finding("purpose-1", UNKNOWN, "purpose", purpose, allowed,
                    "The supplied policy does not explicitly cover this purpose.",
                    "PURPOSE-MISSING-EVIDENCE", evidence)


def _operation_findings(policy: Dict[str, Any], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    scope = _scope(policy)
    analysis = intent.get("analysis", {}) or {}
    requested_ops = _list(analysis.get("operations"))
    prohibited = _list(scope.get("prohibited_operations"))
    permitted = _list(scope.get("allowed_operations"))
    evidence = _evidence(policy, "operations") or _evidence(policy, "scope")
    findings: List[Dict[str, Any]] = []
    known = {"cross_dataset_linkage", "individual_level_model", "aggregate_statistics",
             "read_fields", "public_release", "commercial_use"}

    for index, operation in enumerate(requested_ops, start=1):
        if operation in prohibited or "*" in prohibited:
            alternative = None
            if operation == "cross_dataset_linkage":
                alternative = "Analyse each dataset separately, or use a pre-approved aggregate exchange without record linkage."
            elif operation == "individual_level_model":
                alternative = "Produce aggregate estimates only, subject to the applicable policy condition."
            findings.append(_finding(f"operation-{index}", BLOCKED, "operation", operation,
                                     prohibited, "The declared policy explicitly prohibits this requested operation.",
                                     "OP-EXPLICIT-PROHIBITION", evidence, alternative))
        elif _contains(permitted, operation):
            findings.append(_finding(f"operation-{index}", ALLOWED, "operation", operation,
                                     permitted, "The requested operation is explicitly listed as allowed.",
                                     "OP-EXPLICIT-PERMISSION", evidence))
        elif operation in known:
            findings.append(_finding(f"operation-{index}", UNKNOWN, "operation", operation,
                                     permitted, "The policy does not establish whether this operation is covered.",
                                     "OP-MISSING-EVIDENCE", evidence))
        else:
            findings.append(_finding(f"operation-{index}", REVIEW, "operation", operation,
                                     permitted, "This operation is not in the starter vocabulary and needs a policy owner to interpret it.",
                                     "OP-UNMAPPED", evidence))
    return findings


def _output_findings(policy: Dict[str, Any], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    scope = _scope(policy)
    output_policy = scope.get("output", {}) or {}
    output = (intent.get("analysis", {}) or {}).get("output", {}) or {}
    evidence = _evidence(policy, "output") or _evidence(policy, "scope")
    findings: List[Dict[str, Any]] = []

    requested_granularity = output.get("granularity")
    maximum = output_policy.get("max_granularity")
    order = {"aggregate": 0, "group": 1, "individual": 2}
    if requested_granularity and maximum:
        if order.get(requested_granularity, 99) > order.get(maximum, 99):
            findings.append(_finding("output-granularity-1", BLOCKED, "output_granularity",
                                     requested_granularity, maximum,
                                     "The requested output is more granular than the declared maximum.",
                                     "OUTPUT-GRANULARITY-EXCEEDS-MAX", evidence,
                                     "Use aggregate or group-level output within the declared maximum granularity."))
        else:
            findings.append(_finding("output-granularity-1", ALLOWED, "output_granularity",
                                     requested_granularity, maximum,
                                     "The requested output is within the declared granularity limit.",
                                     "OUTPUT-GRANULARITY-WITHIN-MAX", evidence))
    elif requested_granularity:
        findings.append(_finding("output-granularity-1", UNKNOWN, "output_granularity",
                                 requested_granularity, maximum, "No maximum output granularity was supplied.",
                                 "OUTPUT-MAX-MISSING", evidence))

    audience = output.get("audience")
    audiences = _list(output_policy.get("allowed_audiences"))
    prohibited = _list(output_policy.get("prohibited_audiences"))
    if audience and audience in prohibited:
        findings.append(_finding("output-audience-1", BLOCKED, "output_audience", audience,
                                 prohibited, "The declared policy explicitly excludes this audience.",
                                 "OUTPUT-AUDIENCE-PROHIBITED", evidence,
                                 "Keep the output internal or use an audience explicitly covered by the policy."))
    elif audience and audiences and _contains(audiences, audience):
        findings.append(_finding("output-audience-1", ALLOWED, "output_audience", audience,
                                 audiences, "The requested audience is explicitly covered.",
                                 "OUTPUT-AUDIENCE-PERMITTED", evidence))
    elif audience:
        findings.append(_finding("output-audience-1", UNKNOWN, "output_audience", audience,
                                 audiences, "The policy does not explicitly cover this audience.",
                                 "OUTPUT-AUDIENCE-MISSING", evidence,
                                 "Use an explicitly covered audience while requesting review for broader sharing."))
    return findings


def _scalar_findings(policy: Dict[str, Any], intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    scope = _scope(policy)
    analysis = intent.get("analysis", {}) or {}
    evidence = _evidence(policy, "sharing") or _evidence(policy, "scope")
    findings: List[Dict[str, Any]] = []

    redistribution = analysis.get("redistribution")
    policy_redistribution = scope.get("redistribution", "unknown")
    if redistribution is True and policy_redistribution == "prohibited":
        findings.append(_finding("sharing-1", BLOCKED, "redistribution", True, policy_redistribution,
                                 "The plan includes redistribution but the policy prohibits it.",
                                 "SHARE-EXPLICIT-PROHIBITION", evidence,
                                 "Keep outputs private or obtain a written permission that covers redistribution."))
    elif redistribution is True and policy_redistribution == "allowed":
        findings.append(_finding("sharing-1", ALLOWED, "redistribution", True, policy_redistribution,
                                 "Redistribution is explicitly allowed by the supplied policy.",
                                 "SHARE-EXPLICIT-PERMISSION", evidence))
    elif redistribution is True:
        findings.append(_finding("sharing-1", UNKNOWN, "redistribution", True, policy_redistribution,
                                 "The plan includes redistribution but the policy does not establish whether it is allowed.",
                                 "SHARE-MISSING-EVIDENCE", evidence))

    commercial = analysis.get("commercial")
    policy_commercial = scope.get("commercial_use", "unknown")
    if commercial is True and policy_commercial == "prohibited":
        findings.append(_finding("commercial-1", BLOCKED, "commercial_use", True, policy_commercial,
                                 "The plan includes commercial use but the policy prohibits it.",
                                 "COMMERCIAL-EXPLICIT-PROHIBITION", evidence,
                                 "Remove the commercial use or obtain a policy that explicitly covers it."))
    elif commercial is True and policy_commercial == "allowed":
        findings.append(_finding("commercial-1", ALLOWED, "commercial_use", True, policy_commercial,
                                 "Commercial use is explicitly allowed by the supplied policy.",
                                 "COMMERCIAL-EXPLICIT-PERMISSION", evidence))
    elif commercial is True:
        findings.append(_finding("commercial-1", UNKNOWN, "commercial_use", True, policy_commercial,
                                 "The plan includes commercial use but the policy does not establish whether it is allowed.",
                                 "COMMERCIAL-MISSING-EVIDENCE", evidence))

    field_policy = scope.get("field_rules", {}) or {}
    for index, field in enumerate(sorted(set(_list(analysis.get("fields")))), start=1):
        rule = field_policy.get(field)
        field_evidence = _evidence(policy, "fields") or evidence
        if rule == "prohibited":
            findings.append(_finding(f"field-{index}", BLOCKED, "field", field, rule,
                                     "The requested field is explicitly marked as prohibited.",
                                     "FIELD-EXPLICIT-PROHIBITION", field_evidence))
        elif rule == "allowed":
            findings.append(_finding(f"field-{index}", ALLOWED, "field", field, rule,
                                     "The requested field is explicitly marked as allowed.",
                                     "FIELD-EXPLICIT-PERMISSION", field_evidence))
        else:
            findings.append(_finding(f"field-{index}", UNKNOWN, "field", field, rule,
                                     "No explicit use rule was supplied for this field.",
                                     "FIELD-MISSING-EVIDENCE", field_evidence))
    return findings


def check_boundary(policy: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
    """Compare a policy and an analysis intent and return a stable report dict."""
    policy = deepcopy(policy)
    intent = deepcopy(intent)
    findings = [_purpose_finding(policy, intent)]
    findings.extend(_operation_findings(policy, intent))
    findings.extend(_output_findings(policy, intent))
    findings.extend(_scalar_findings(policy, intent))
    statuses = {item["status"] for item in findings}
    if BLOCKED in statuses:
        overall = BLOCKED
    elif REVIEW in statuses:
        overall = REVIEW
    elif UNKNOWN in statuses:
        overall = UNKNOWN
    else:
        overall = ALLOWED
    counts = {status: sum(item["status"] == status for item in findings)
              for status in (ALLOWED, REVIEW, BLOCKED, UNKNOWN)}
    return {
        "schema_version": "0.1",
        "engine": "consent-compass",
        "overall_status": overall,
        "dataset": policy.get("dataset", {}),
        "intent_id": intent.get("id"),
        "finding_counts": counts,
        "findings": findings,
        "disclaimer": "This is a data-use preflight report, not legal advice, ethics approval, a consent determination, or permission to publish.",
    }
