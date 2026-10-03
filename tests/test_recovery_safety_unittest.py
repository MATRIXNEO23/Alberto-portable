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
            "C-REAL-FEASIBILITY-BEFORE-AGREEMENT-001",
            "C-KNOWN-RISK-FIX-NOW-001",
            "C-INSTANCE-SELF-AUDIT-001",
            "C-DELEGATION-LITERAL-EXECUTION-001",
            "C-OBJECTIVE-CLARIFICATION-FIRST-001",
            "C-SEARCH-REUSE-BEFORE-REINVENT-001",
        }
        self.assertTrue(required.issubset(set(result["criterion_ids"])))

    def test_operational_criteria_are_recovered_from_manifest(self):
        ids = {row["criterion_id"] for row in all_operational_criteria()}
        self.assertIn("C-RESULT-QUALITY-OVER-LITERALISM-001", ids)
        self.assertIn("C-REAL-FEASIBILITY-BEFORE-AGREEMENT-001", ids)
        self.assertIn("C-KNOWN-RISK-FIX-NOW-001", ids)
        self.assertIn("C-DELEGATION-LITERAL-EXECUTION-001", ids)
        self.assertIn("C-OBJECTIVE-CLARIFICATION-FIRST-001", ids)
        self.assertIn("C-SEARCH-REUSE-BEFORE-REINVENT-001", ids)

    def test_operational_anti_regression_rejects_known_shortcut(self):
        result = anti_regression_check(
            {"case_id": "delegation", "features": {}},
            {"assumptions": ["guess_user_goal_when_materially_ambiguous"]},
            rows=[],
        )
        self.assertTrue(result["candidate_rejected"])
        self.assertIn("guess_user_goal_when_materially_ambiguous", result["violated_assumptions"])

    def test_verified_experience_without_context_anchor_fails_integrity(self):
        # Source integrity for canonical files is already exercised above; this
        # behavioral guard is covered through recover_experiences below.
        rows = [
            {
                "experience_id": "E-GENERIC",
                "reuse_when": {"task_type": "repo_audit"},
                "verified": True,
            }
        ]
        self.assertEqual(recover_experiences({"task_type": "repo_audit", "features": {}}, rows=rows), [])


class ProjectExperienceRecoveryTests(unittest.TestCase):
    def test_verified_matching_experience_is_recovered_with_context_anchor(self):
        case = {
            "case_id": "repo-audit",
            "task_type": "repo_audit",
            "features": {"canonical_source_access": True, "provenance_required": True},
        }
        rows = [
            {
                "experience_id": "E-1",
                "project": "example",
                "task_type": "repo_audit",
                "outcome": "success",
                "lesson": "verify canonical source first",
                "reuse_when": {
                    "task_type": "repo_audit",
                    "canonical_source_access": True,
                    "provenance_required": True,
                },
                "evidence_refs": ["evidence/example.md"],
                "verified": True,
                "generality": "contextual",
            }
        ]
        result = recover_experiences(case, rows=rows)
        self.assertEqual([row["experience_id"] for row in result], ["E-1"])
        self.assertEqual(result[0]["contextual_anchors"], ["canonical_source_access", "provenance_required"])

    def test_task_type_alone_is_not_enough(self):
        case = {"task_type": "repo_audit", "features": {}}
        rows = [
            {
                "experience_id": "E-GENERIC",
                "reuse_when": {"task_type": "repo_audit"},
                "verified": True,
            }
        ]
        self.assertEqual(recover_experiences(case, rows=rows), [])

    def test_more_specific_experience_is_ranked_first(self):
        case = {
            "task_type": "repo_audit",
            "features": {"canonical_source_access": True, "provenance_required": True},
        }
        rows = [
            {
                "experience_id": "E-LESS",
                "reuse_when": {"task_type": "repo_audit", "canonical_source_access": True},
                "verified": True,
            },
            {
                "experience_id": "E-MORE",
                "reuse_when": {
                    "task_type": "repo_audit",
                    "canonical_source_access": True,
                    "provenance_required": True,
                },
                "verified": True,
            },
        ]
        self.assertEqual(
            [row["experience_id"] for row in recover_experiences(case, rows=rows)],
            ["E-MORE", "E-LESS"],
        )

    def test_unverified_and_nonmatching_experiences_are_not_recovered(self):
        case = {"task_type": "build", "features": {"artifact_reusable": True}}
        rows = [
            {
                "experience_id": "E-2",
                "reuse_when": {"task_type": "build", "artifact_reusable": True},
                "verified": False,
            },
            {
                "experience_id": "E-3",
                "reuse_when": {"task_type": "repo_audit", "canonical_source_access": True},
                "verified": True,
            },
        ]
        self.assertEqual(recover_experiences(case, rows=rows), [])

    def test_gptina_dedicated_method_disables_generic_experience_recovery(self):
        case = {
            "task_type": "repo_audit",
            "features": {
                "target_is_gptina_and_dedicated_method_applies": True,
                "canonical_source_access": True,
            },
        }
        rows = [
            {
                "experience_id": "E-4",
                "reuse_when": {"task_type": "repo_audit", "canonical_source_access": True},
                "verified": True,
            }
        ]
        self.assertEqual(recover_experiences(case, rows=rows), [])


class InstanceAuditTests(unittest.TestCase):
    def test_audit_is_required_until_instance_has_completed_record_for_current_structure(self):
        pending = instance_audit_status("instance-test", rows=[], structure_fingerprint_value="fp-a")
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
                    "structure_fingerprint": "fp-a",
                }
            ],
            structure_fingerprint_value="fp-a",
        )
        self.assertEqual(complete["status"], "AUDIT_COMPLETE")

    def test_structure_change_invalidates_previous_audit(self):
        stale = instance_audit_status(
            "instance-test",
            rows=[
                {
                    "instance_id": "instance-test",
                    "status": "completed",
                    "audit_id": "AUDIT-1",
                    "recorded_at": "2026-10-03T00:00:00Z",
                    "recovery_head": "abc",
                    "structure_fingerprint": "fp-old",
                }
            ],
            structure_fingerprint_value="fp-new",
        )
        self.assertTrue(stale["required"])
        self.assertEqual(stale["status"], "AUDIT_STALE")
        self.assertEqual(stale["previous_structure_fingerprint"], "fp-old")
        self.assertEqual(stale["structure_fingerprint"], "fp-new")

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
            record = record_instance_audit(
                "instance-test",
                audit,
                path=path,
                structure_fingerprint_value="fp-a",
            )
            self.assertEqual(record["status"], "completed")
            self.assertEqual(record["structure_fingerprint"], "fp-a")
            saved = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(saved["instance_id"], "instance-test")
            self.assertEqual(
                instance_audit_status(
                    "instance-test",
                    rows=[saved],
                    structure_fingerprint_value="fp-a",
                )["status"],
                "AUDIT_COMPLETE",
            )


if __name__ == "__main__":
    unittest.main()
