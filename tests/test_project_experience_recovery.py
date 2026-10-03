from tools.recovery_safety import recover_experiences


def test_verified_matching_experience_is_recovered():
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
    assert [row["experience_id"] for row in result] == ["E-1"]


def test_unverified_experience_is_not_recovered():
    case = {"task_type": "repo_audit", "features": {}}
    rows = [
        {
            "experience_id": "E-2",
            "reuse_when": {"task_type": "repo_audit"},
            "verified": False,
        }
    ]
    assert recover_experiences(case, rows=rows) == []


def test_nonmatching_experience_is_not_recovered():
    case = {"task_type": "build", "features": {}}
    rows = [
        {
            "experience_id": "E-3",
            "reuse_when": {"task_type": "repo_audit"},
            "verified": True,
        }
    ]
    assert recover_experiences(case, rows=rows) == []


def test_gptina_dedicated_method_disables_generic_experience_recovery():
    case = {
        "task_type": "repo_audit",
        "features": {"target_is_gptina_and_dedicated_method_applies": True},
    }
    rows = [
        {
            "experience_id": "E-4",
            "reuse_when": {"task_type": "repo_audit"},
            "verified": True,
        }
    ]
    assert recover_experiences(case, rows=rows) == []
