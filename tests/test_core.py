import json
import unittest
from pathlib import Path

from consent_compass.core import ALLOWED, BLOCKED, UNKNOWN, check_boundary


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


if __name__ == "__main__":
    unittest.main()
