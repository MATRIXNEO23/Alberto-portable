#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITERIA = ROOT / "data" / "criteria.jsonl"
EXPERIENCE_CRITERIA = ROOT / "data" / "experience_criteria.jsonl"
PROJECT_EXPERIENCE = ROOT / "data" / "project_experience.jsonl"

CLEAR = "CLEAR"
CORRECTION_APPLIES = "CORRECTION_APPLIES"
CONFLICTING = "CONFLICTING"
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows: list[dict] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{lineno} object required")
        rows.append(value)
    return rows


def all_criteria() -> list[dict]:
    return read_jsonl(CRITERIA) + read_jsonl(EXPERIENCE_CRITERIA)


def current_criteria(rows: list[dict]) -> list[dict]:
    superseded = {r.get("supersedes") for r in rows if r.get("supersedes")}
    return [r for r in rows if r.get("criterion_id") not in superseded]


def _feature(case: dict, name: str):
    return (case.get("features") or {}).get(name, None)


def _case_value(case: dict, name: str):
    if name in case:
        return case.get(name)
    return _feature(case, name)


def evaluate_applicability(case: dict, criterion: dict) -> dict:
    cfg = criterion.get("applicability") or {}
    missing: list[str] = []
    failed: list[str] = []

    for name, expected in (cfg.get("non_applicable_if") or {}).items():
        actual = _feature(case, name)
        if actual == expected:
            return {
                "criterion_id": criterion.get("criterion_id"),
                "status": CLEAR,
                "applicable": False,
                "missing": [],
                "failed_conditions": [f"{name}={expected!r} marks criterion non-applicable"],
                "provenance": criterion.get("evidence_refs", []),
                "generality": criterion.get("generality", "contextual"),
            }

    for name in cfg.get("required_true", []):
        actual = _feature(case, name)
        if actual is None:
            missing.append(name)
        elif actual is not True:
            failed.append(name)

    if failed:
        return {
            "criterion_id": criterion.get("criterion_id"),
            "status": CLEAR,
            "applicable": False,
            "missing": [],
            "failed_conditions": failed,
            "provenance": criterion.get("evidence_refs", []),
            "generality": criterion.get("generality", "contextual"),
        }

    for name in cfg.get("decision_critical", []):
        if _feature(case, name) in (None, "unknown", ""):
            missing.append(name)

    if missing:
        return {
            "criterion_id": criterion.get("criterion_id"),
            "status": NEEDS_CLARIFICATION,
            "applicable": None,
            "missing": sorted(set(missing)),
            "failed_conditions": [],
            "provenance": criterion.get("evidence_refs", []),
            "generality": criterion.get("generality", "contextual"),
        }

    high_risk_values = cfg.get("high_risk_values") or {}
    high_risk_match = True
    for name, allowed in high_risk_values.items():
        if _feature(case, name) not in allowed:
            high_risk_match = False
            break

    return {
        "criterion_id": criterion.get("criterion_id"),
        "status": CORRECTION_APPLIES if high_risk_match else CLEAR,
        "applicable": True,
        "missing": [],
        "failed_conditions": [],
        "provenance": criterion.get("evidence_refs", []),
        "generality": criterion.get("generality", "contextual"),
        "statement": criterion.get("statement"),
        "high_risk_match": high_risk_match,
    }


def recover_experiences(case: dict, rows: list[dict] | None = None) -> list[dict]:
    # GPTina uses its dedicated continuity/recovery method; do not automatically
    # inject the generic project-experience layer into that path.
    if _feature(case, "target_is_gptina_and_dedicated_method_applies") is True:
        return []

    rows = rows if rows is not None else read_jsonl(PROJECT_EXPERIENCE)
    matches: list[dict] = []
    for row in rows:
        if row.get("verified") is not True:
            continue
        reuse_when = row.get("reuse_when") or {}
        if not reuse_when:
            continue
        if not all(_case_value(case, key) == expected for key, expected in reuse_when.items()):
            continue
        matches.append({
            "experience_id": row.get("experience_id"),
            "project": row.get("project"),
            "task_type": row.get("task_type"),
            "outcome": row.get("outcome"),
            "failure_mode": row.get("failure_mode"),
            "lesson": row.get("lesson"),
            "reuse_when": reuse_when,
            "provenance": row.get("evidence_refs", []),
            "generality": row.get("generality", "contextual"),
        })
    return matches


def recover_case(case: dict, rows: list[dict] | None = None, experience_rows: list[dict] | None = None) -> dict:
    rows = current_criteria(rows if rows is not None else all_criteria())
    matches = [evaluate_applicability(case, row) for row in rows]
    clarifications = sorted({m for row in matches for m in row.get("missing", [])})
    applicable = [row for row in matches if row.get("status") == CORRECTION_APPLIES]
    experiences = recover_experiences(case, rows=experience_rows)

    if clarifications:
        status = NEEDS_CLARIFICATION
    elif applicable:
        status = CORRECTION_APPLIES
    else:
        status = CLEAR

    proving_sources = {p for row in matches for p in row.get("provenance", [])}
    proving_sources.update(p for row in experiences for p in row.get("provenance", []))

    return {
        "status": status,
        "case_id": case.get("case_id"),
        "relevant_corrections": matches,
        "relevant_experiences": experiences,
        "decision_critical_unknowns": clarifications,
        "proving_sources": sorted(proving_sources),
        "note": "Criteria require explicit applicability. Verified experiences are contextual precedents only: they may inform the next move but do not become universal rules automatically.",
    }


def anti_regression_check(case: dict, candidate: dict, rows: list[dict] | None = None) -> dict:
    recovery = recover_case(case, rows=rows)
    assumptions = set((candidate.get("assumptions") or []))
    violated: list[str] = []

    active_ids = {
        row.get("criterion_id")
        for row in recovery.get("relevant_corrections", [])
        if row.get("status") == CORRECTION_APPLIES
    }

    criteria_rows = current_criteria(rows if rows is not None else all_criteria())
    for criterion in criteria_rows:
        if criterion.get("criterion_id") not in active_ids:
            continue
        shortcuts = set((criterion.get("anti_regression") or {}).get("shortcuts_to_reject", []))
        violated.extend(sorted(assumptions & shortcuts))

    if recovery["status"] == NEEDS_CLARIFICATION:
        status = NEEDS_CLARIFICATION
    elif violated:
        status = CORRECTION_APPLIES
    else:
        status = recovery["status"] if recovery["status"] != CORRECTION_APPLIES else CLEAR

    return {
        "status": status,
        "recovery": recovery,
        "candidate_rejected": bool(violated),
        "violated_assumptions": violated,
    }


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Alberto-portable recovery safety with contextual project experience")
    sub = parser.add_subparsers(dest="command", required=True)

    p_recover = sub.add_parser("recover")
    p_recover.add_argument("--case", required=True)

    p_check = sub.add_parser("check")
    p_check.add_argument("--case", required=True)
    p_check.add_argument("--candidate", required=True)

    args = parser.parse_args()
    case = load_json(args.case)
    if args.command == "recover":
        payload = recover_case(case)
    else:
        payload = anti_regression_check(case, load_json(args.candidate))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
