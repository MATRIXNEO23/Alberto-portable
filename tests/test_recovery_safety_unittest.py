import json
import tempfile
import unittest
from pathlib import Path

from tools.recovery_safety import (
    all_operational_criteria,
    anti_regression_check,
    instance_audit_status,
    record_instance_audit,
    recover_experiences,
    source_integrity,
)


class RecoverySourceIntegrityTests(unittest.TestCase):
    def test_manifest_loads_all_required_criteria(self):
        result = source_integrity()
        self.assertEqual(result["status"], "PASS", result["errors"])
        required = {
            "C-CRITICAL-PATH-FIRST-001",
            "C-SOLUTION-NOT-IDENTITY-001",
            "C-EXPERIENCE-ACCUMULATION-001",
            "C-RESULT-QUALITY-OVER-LITERALISM-001",
            "C-INSTANCE-SELF-AUDIT-001",
            "C-DELEGATION-LITERAL-EXECUTION-001",
            "C-OBJECTIVE-CLARIFICATION-FIRST-001",
        }
        self.assertTrue(required.issubset(set(result["criterion_ids"])))

    def test_operational_criteria_are_recovered_from_manifest(self):
        ids = {row["criterion_id"] for row in all_operational_criteria()}
        self.assertIn("C-RESULT-QUALITY-OVER-LITERALISM-001", ids)
        self.assertIn("C-DELEGATION-LITERAL-EXECUTION-001", ids)
        self.assertIn("C-OBJECTIVE-CLARIFICATION-FIRST-001", ids)

    def test_operational_anti_regression_rejects_known_shortcut(self):
        result = anti_regression_check(
            {"case_id": "delegation", "features": {}},
            {"assumptions": ["guess_user_goal_when_materially_ambiguous"]},
            rows=[],
        )
        self.assertTrue(result["candidate_rejected"])
        self.assertIn("guess_user_goal_when_materially_ambiguous", result["violated_assumptions"])


class ProjectExperienceRecoveryTests(unittest.TestCase):
    def test_verified_matching_experience_is_recovered(self):
        case = {"case_id": "repo-audit", "task_type": "repo_audit", "features": {}}
        rows = [
            {
                "experience_id": "E-1",
                "project": "example",
                "task_type": "repo_audit",
                "outcome": "success",
                "lesson": "verify canonical source first",
                "reuse_when": {"task_type": "repo_audit"},
                "evidence_refs": ["evidence/example.md"],
                "verified": True,
                "generality": "contextual",
            }
        ]
        result = recover_experiences(case, rows=rows)
        self.assertEqual([row["experience_id"] for row in result], ["E-1"])

    def test_unverified_and_nonmatching_experiences_are_not_recovered(self):
        case = {"task_type": "build", "features": {}}
        rows = [
            {"experience_id": "E-2", "reuse_when": {"task_type": "build"}, "verified": False},
            {"experience_id": "E-3", "reuse_when": {"task_type": "repo_audit"}, "verified": True},
        ]
        self.assertEqual(recover_experiences(case, rows=rows), [])

    def test_gptina_dedicated_method_disables_generic_experience_recovery(self):
        case = {
            "task_type": "repo_audit",
            "features": {"target_is_gptina_and_dedicated_method_applies": True},
        }
        rows = [{"experience_id": "E-4", "reuse_when": {"task_type": "repo_audit"}, "verified": True}]
        self.assertEqual(recover_experiences(case, rows=rows), [])


class InstanceAuditTests(unittest.TestCase):
    def test_audit_is_required_until_instance_has_completed_record(self):
        pending = instance_audit_status("instance-test", rows=[])
        self.assertEqual(pending["status"], "AUDIT_REQUIRED")
        complete = instance_audit_status(
            "instance-test",
            rows=[
                {
                    "instance_id": "instance-test",
                    "status": "completed",
                    "audit_id": "AUDIT-1",
                    "recorded_at": "2026-10-03T00:00:00Z",
                    "recovery_head": "abc",
                }
            ],
        )
        self.assertEqual(complete["status"], "AUDIT_COMPLETE")

    def test_record_audit_requires_structured_gap_and_verification(self):
        audit = {
            "objective": "increase long-term decision coherence with Alberto",
            "observed_gap": "new criterion ledgers were not loaded by recovery",
            "why_it_limits_goal": "a persisted correction could disappear operationally in a new instance",
            "proposed_improvement": "use one canonical recovery source manifest and integrity check",
            "verification_test": "unittest asserts all required criterion ids are loaded",
            "regression_risk": "manifest drift could block recovery; CI must fail closed",
            "separate_adoption_condition": "keep only if source-integrity and existing recovery tests pass",
            "recovery_head": "test-head",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "audits.jsonl"
            record = record_instance_audit("instance-test", audit, path=path)
            self.assertEqual(record["status"], "completed")
            saved = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(saved["instance_id"], "instance-test")
            self.assertEqual(instance_audit_status("instance-test", rows=[saved])["status"], "AUDIT_COMPLETE")


if __name__ == "__main__":
    unittest.main()
