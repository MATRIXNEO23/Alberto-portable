from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from project_continuity import ContinuityError, audit_project, recover_project, write_checkpoint


def checkpoint(project: str, checkpoint_id: str, captured_at: str, **overrides):
    value = {
        "schema_version": 1,
        "checkpoint_id": checkpoint_id,
        "project_id": project,
        "captured_at": captured_at,
        "repository": f"MATRIXNEO23/{project}",
        "branch": "main",
        "head": "a" * 40,
        "objective": "continue current project work",
        "completed": ["step one"],
        "verified": ["repository head verified"],
        "unverified": ["manual UI test pending"],
        "decisions": ["keep current architecture"],
        "corrections": ["do not restart completed work"],
        "constraints": ["preserve existing behavior"],
        "touched_components": ["component-a"],
        "open_loops": ["manual UI test"],
        "next_action": "run decisive UI test",
        "regression_risks": ["cross-project contamination"],
        "provenance_refs": ["commit:" + "a" * 40],
    }
    value.update(overrides)
    return value


class ProjectContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "projects"

    def tearDown(self):
        self.tmp.cleanup()

    def test_projects_are_partitioned_and_recover_independently(self):
        write_checkpoint(checkpoint("filum", "FILUM-001", "2026-10-04T06:00:00+00:00"), self.root)
        write_checkpoint(checkpoint("matrix", "MATRIX-001", "2026-10-04T06:05:00+00:00"), self.root)
        filum = recover_project("filum", self.root)
        matrix = recover_project("matrix", self.root)
        self.assertEqual(filum["checkpoint"]["checkpoint_id"], "FILUM-001")
        self.assertEqual(matrix["checkpoint"]["checkpoint_id"], "MATRIX-001")
        self.assertEqual(filum["checkpoint"]["project_id"], "filum")
        self.assertEqual(matrix["checkpoint"]["project_id"], "matrix")

    def test_checkpoint_is_immutable(self):
        original = checkpoint("filum", "FILUM-001", "2026-10-04T06:00:00+00:00")
        write_checkpoint(original, self.root)
        changed = dict(original)
        changed["objective"] = "silently rewritten objective"
        with self.assertRaises(ContinuityError):
            write_checkpoint(changed, self.root)

    def test_live_pointer_cannot_move_backwards(self):
        write_checkpoint(checkpoint("filum", "FILUM-002", "2026-10-04T07:00:00+00:00"), self.root)
        with self.assertRaises(ContinuityError):
            write_checkpoint(checkpoint("filum", "FILUM-001", "2026-10-04T06:00:00+00:00"), self.root)
        self.assertEqual(recover_project("filum", self.root)["checkpoint"]["checkpoint_id"], "FILUM-002")

    def test_checksum_tamper_is_detected(self):
        result = write_checkpoint(checkpoint("filum", "FILUM-001", "2026-10-04T06:00:00+00:00"), self.root)
        cp_path = self.root / "filum" / result["path"]
        data = json.loads(cp_path.read_text(encoding="utf-8"))
        data["objective"] = "tampered"
        cp_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(ContinuityError):
            recover_project("filum", self.root)

    def test_verified_requires_provenance(self):
        payload = checkpoint("filum", "FILUM-001", "2026-10-04T06:00:00+00:00")
        payload["provenance_refs"] = []
        with self.assertRaises(ContinuityError):
            write_checkpoint(payload, self.root)

    def test_dedicated_recovery_blocks_generic_checkpoint(self):
        payload = checkpoint("gptina", "GPTINA-001", "2026-10-04T06:00:00+00:00", dedicated_recovery=True)
        with self.assertRaises(ContinuityError):
            write_checkpoint(payload, self.root)

    def test_audit_detects_cross_project_record(self):
        result = write_checkpoint(checkpoint("filum", "FILUM-001", "2026-10-04T06:00:00+00:00"), self.root)
        cp_path = self.root / "filum" / result["path"]
        data = json.loads(cp_path.read_text(encoding="utf-8"))
        data["project_id"] = "matrix"
        cp_path.write_text(json.dumps(data), encoding="utf-8")
        audit = audit_project("filum", self.root)
        self.assertEqual(audit["status"], "FAIL")
        self.assertTrue(any("does not match requested project" in e for e in audit["errors"]))

    def test_recover_without_checkpoint_is_explicit(self):
        self.assertEqual(recover_project("filum", self.root)["status"], "NO_CHECKPOINT")


if __name__ == "__main__":
    unittest.main()
