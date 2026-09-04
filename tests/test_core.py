import json
import unittest
from pathlib import Path

from consent_compass.core import ALLOWED, BLOCKED, REVIEW, UNKNOWN, check_boundary
from consent_compass.cli import render_html


ROOT = Path(__file__).resolve().parents[1]


def fixture(name):
    return json.loads((ROOT / "demos" / name).read_text(encoding="utf-8"))


class BoundaryTests(unittest.TestCase):
    def test_blocked_linkage_fixture_exposes_each_conflict(self):
        report = check_boundary(fixture("biobank-policy.json"), fixture("linkage-intent.json"))
        self.assertEqual(report["overall_status"], BLOCKED)
        self.assertGreaterEqual(report["finding_counts"][BLOCKED], 5)
        self.assertTrue(any(item["rule_id"] == "OP-EXPLICIT-PROHIBITION" for item in report["findings"]))

    def test_safe_aggregate_fixture_is_allowed(self):
        report = check_boundary(fixture("biobank-policy.json"), fixture("aggregate-intent.json"))
        self.assertEqual(report["overall_status"], ALLOWED)
        self.assertEqual(report["finding_counts"][UNKNOWN], 0)

    def test_missing_policy_evidence_is_not_approval(self):
        policy = {"dataset": {"id": "minimal"}, "scope": {}, "evidence": {}}
        intent = {"id": "unknown", "analysis": {"purpose": "new_purpose", "operations": ["aggregate_statistics"]}}
        report = check_boundary(policy, intent)
        self.assertEqual(report["overall_status"], UNKNOWN)
        self.assertGreater(report["finding_counts"][UNKNOWN], 0)

    def test_same_inputs_are_deterministic(self):
        policy = fixture("biobank-policy.json")
        intent = fixture("linkage-intent.json")
        self.assertEqual(check_boundary(policy, intent), check_boundary(policy, intent))

    def test_explicit_prohibition_wins_over_permission(self):
        policy = {
            "scope": {"allowed_operations": ["read_fields"], "prohibited_operations": ["read_fields"]},
            "evidence": {"operations": ["policy.md:1"]},
        }
        intent = {"id": "conflict", "analysis": {"operations": ["read_fields"]}}
        report = check_boundary(policy, intent)
        self.assertEqual(report["overall_status"], BLOCKED)
        self.assertEqual(report["findings"][1]["status"], BLOCKED)

    def test_unknown_operation_requires_review(self):
        policy = {"scope": {"allowed_operations": []}, "evidence": {}}
        intent = {"id": "new-operation", "analysis": {"operations": ["export_to_mars"]}}
        report = check_boundary(policy, intent)
        self.assertEqual(report["overall_status"], REVIEW)
        self.assertEqual(report["findings"][1]["rule_id"], "OP-UNMAPPED")

    def test_html_escapes_user_values(self):
        policy = {"dataset": {"id": "<unsafe>"}, "scope": {}, "evidence": {}}
        intent = {"id": "<intent>", "analysis": {"purpose": "<script>alert(1)</script>"}}
        report = check_boundary(policy, intent)
        page = render_html(report)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()
