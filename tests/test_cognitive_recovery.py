import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import recovery_safety as rs


class CognitiveRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = rs.read_jsonl(ROOT / "data" / "criteria.jsonl")
        cls.criterion = next(r for r in cls.rows if r["criterion_id"] == "C-SEMANTIC-ISOLATION-001")

    def test_high_value_semantic_contamination_applies(self):
        case = {
            "case_id": "A",
            "features": {
                "experimental_component": True,
                "can_affect_persistent_semantics": True,
                "production_state_exists": True,
                "project_value": "maximum",
                "semantic_contamination_cost": "maximum",
            },
        }
        out = rs.recover_case(case, self.rows)
        self.assertEqual(out["status"], rs.CORRECTION_APPLIES)
        self.assertIn("evidence/ALBERTO_CASE_2026-10-03_SEMANTIC_CONTAMINATION.md", out["proving_sources"])
        match = next(x for x in out["relevant_corrections"] if x["criterion_id"] == self.criterion["criterion_id"])
        self.assertEqual(match["generality"], "contextual")

    def test_unknown_project_value_fails_closed(self):
        case = {
            "case_id": "B",
            "features": {
                "experimental_component": True,
                "can_affect_persistent_semantics": True,
                "production_state_exists": True,
                "semantic_contamination_cost": "high",
            },
        }
        out = rs.recover_case(case, self.rows)
        self.assertEqual(out["status"], rs.NEEDS_CLARIFICATION)
        self.assertIn("project_value", out["decision_critical_unknowns"])

    def test_low_value_case_does_not_become_sandbox_always(self):
        case = {
            "case_id": "C",
            "features": {
                "experimental_component": True,
                "can_affect_persistent_semantics": True,
                "production_state_exists": True,
                "project_value": "low",
                "semantic_contamination_cost": "low",
            },
        }
        out = rs.recover_case(case, self.rows)
        self.assertEqual(out["status"], rs.CLEAR)
        match = next(x for x in out["relevant_corrections"] if x["criterion_id"] == self.criterion["criterion_id"])
        self.assertTrue(match["applicable"])
        self.assertFalse(match["high_risk_match"])

    def test_no_persistent_semantic_effect_is_not_applicable(self):
        case = {
            "case_id": "D",
            "features": {
                "experimental_component": True,
                "can_affect_persistent_semantics": False,
                "production_state_exists": True,
                "project_value": "maximum",
                "semantic_contamination_cost": "maximum",
            },
        }
        out = rs.recover_case(case, self.rows)
        self.assertEqual(out["status"], rs.CLEAR)
        match = next(x for x in out["relevant_corrections"] if x["criterion_id"] == self.criterion["criterion_id"])
        self.assertFalse(match["applicable"])

    def test_candidate_with_known_bad_shortcut_is_rejected(self):
        case = {
            "case_id": "E",
            "features": {
                "experimental_component": True,
                "can_affect_persistent_semantics": True,
                "production_state_exists": True,
                "project_value": "high",
                "semantic_contamination_cost": "high",
            },
        }
        candidate = {"assumptions": ["additive_implies_safe"]}
        out = rs.anti_regression_check(case, candidate, self.rows)
        self.assertEqual(out["status"], rs.CORRECTION_APPLIES)
        self.assertTrue(out["candidate_rejected"])
        self.assertEqual(out["violated_assumptions"], ["additive_implies_safe"])

    def test_similarity_alone_cannot_activate_criterion(self):
        case = {
            "case_id": "F",
            "description": "A very similar sounding experiment with persistent memory",
            "features": {},
        }
        out = rs.recover_case(case, self.rows)
        self.assertEqual(out["status"], rs.NEEDS_CLARIFICATION)
        self.assertIn("experimental_component", out["decision_critical_unknowns"])
        self.assertIn("can_affect_persistent_semantics", out["decision_critical_unknowns"])

    def test_cli_recover_returns_auditable_packet(self):
        case = {
            "case_id": "CLI-A",
            "features": {
                "experimental_component": True,
                "can_affect_persistent_semantics": True,
                "production_state_exists": True,
                "project_value": "maximum",
                "semantic_contamination_cost": "maximum",
            },
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "case.json"
            path.write_text(json.dumps(case), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "recovery_safety.py"), "recover", "--case", str(path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["status"], rs.CORRECTION_APPLIES)
        self.assertTrue(payload["proving_sources"])


if __name__ == "__main__":
    unittest.main()
