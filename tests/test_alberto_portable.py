import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

MODULE = Path(__file__).resolve().parents[1] / "tools" / "alberto_portable.py"
spec = importlib.util.spec_from_file_location("alberto_portable", MODULE)
ap = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(ap)


class AlbertoPortableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_data = ap.DATA
        self.old_decisions = ap.DECISIONS
        self.old_outcomes = ap.OUTCOMES
        self.old_methods = ap.METHODS
        root = Path(self.tmp.name)
        ap.DATA = root
        ap.DECISIONS = root / "decisions.jsonl"
        ap.OUTCOMES = root / "outcomes.jsonl"
        ap.METHODS = root / "method_observations.jsonl"

    def tearDown(self):
        ap.DATA = self.old_data
        ap.DECISIONS = self.old_decisions
        ap.OUTCOMES = self.old_outcomes
        ap.METHODS = self.old_methods
        self.tmp.cleanup()

    def test_append_only_decision_ids(self):
        args = SimpleNamespace(
            decision_id="D1", task_type="repo_audit", context="x",
            alternatives="A|B", choice="B", reasons="r1|r2", evidence_refs="",
            risk="high", reversible=False, expected_outcome="safe", supersedes=None,
        )
        ap.cmd_record_decision(args)
        with self.assertRaises(SystemExit):
            ap.cmd_record_decision(args)

    def test_outcome_requires_existing_decision(self):
        args = SimpleNamespace(
            outcome_id="O1", decision_id="missing", technical_result="passed",
            tests_passed=True, regressions="", artifact_refs="",
            alberto_validation="accepted", alberto_notes="", notes="",
        )
        with self.assertRaises(SystemExit):
            ap.cmd_record_outcome(args)

    def test_contextual_score_penalizes_hallucination(self):
        good = {
            "verified_result": "correct", "hallucination": False,
            "build_result": "passed", "alberto_validation": "accepted",
            "canonical_source_access": True,
        }
        bad = {
            "verified_result": "correct", "hallucination": True,
            "build_result": "passed", "alberto_validation": "accepted",
            "canonical_source_access": True,
        }
        self.assertGreater(
            ap.observation_score(good, require_canonical=True, risk="high"),
            ap.observation_score(bad, require_canonical=True, risk="high"),
        )

    def test_same_method_can_differ_by_role(self):
        rows = [
            {
                "schema_version": 1, "observation_id": "M1", "method": "qwen",
                "task_type": "repo_work", "role": "explore",
                "canonical_source_access": False, "verified_result": "correct",
                "hallucination": False, "build_result": "not_applicable",
                "alberto_validation": "not_tested", "evidence_refs": []
            },
            {
                "schema_version": 1, "observation_id": "M2", "method": "qwen",
                "task_type": "repo_work", "role": "verify",
                "canonical_source_access": False, "verified_result": "wrong",
                "hallucination": True, "build_result": "not_applicable",
                "alberto_validation": "not_tested", "evidence_refs": []
            }
        ]
        for row in rows:
            ap.append_jsonl(ap.METHODS, row)
        loaded = ap.read_jsonl(ap.METHODS)
        explore = [r for r in loaded if r["role"] == "explore"]
        verify = [r for r in loaded if r["role"] == "verify"]
        self.assertEqual(len(explore), 1)
        self.assertEqual(len(verify), 1)
        self.assertGreater(
            ap.observation_score(explore[0], require_canonical=False, risk="low"),
            ap.observation_score(verify[0], require_canonical=False, risk="low"),
        )

    def test_alberto_rejection_is_negative_evidence(self):
        accepted = {
            "verified_result": "correct", "hallucination": False,
            "build_result": "passed", "alberto_validation": "accepted",
            "canonical_source_access": True,
        }
        rejected = dict(accepted, alberto_validation="rejected")
        self.assertGreater(
            ap.observation_score(accepted, require_canonical=False, risk="medium"),
            ap.observation_score(rejected, require_canonical=False, risk="medium"),
        )


if __name__ == "__main__":
    unittest.main()
