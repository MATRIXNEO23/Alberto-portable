#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST = ROOT / "data" / "recovery_sources.json"
INSTANCE_AUDITS = ROOT / "state" / "instance_audits.jsonl"

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


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: object required")
    return value


def load_manifest(path: Path = SOURCE_MANIFEST) -> dict:
    return read_json(path)


def _source_path(source: dict) -> Path:
    rel = source.get("path")
    if not isinstance(rel, str) or not rel:
        raise ValueError("recovery source requires non-empty path")
    return ROOT / rel


def load_source(source: dict) -> list[dict]:
    path = _source_path(source)
    fmt = source.get("format")
    if fmt == "jsonl":
        return read_jsonl(path)
    if fmt == "json":
        return [read_json(path)]
    raise ValueError(f"unsupported recovery source format {fmt!r} for {path}")


def _load_source_group(manifest: dict, key: str) -> list[dict]:
    rows: list[dict] = []
    for source in manifest.get(key, []):
        rows.extend(load_source(source))
    return rows


def all_criteria(manifest: dict | None = None) -> list[dict]:
    manifest = manifest or load_manifest()
    return _load_source_group(manifest, "criterion_sources")


def all_operational_criteria(manifest: dict | None = None) -> list[dict]:
    manifest = manifest or load_manifest()
    return _load_source_group(manifest, "operational_criterion_sources")


def get_instance_audit_criterion(manifest: dict | None = None) -> dict:
    manifest = manifest or load_manifest()
    source = manifest.get("instance_audit_source")
    if not isinstance(source, dict):
        raise ValueError("recovery manifest requires instance_audit_source")
    rows = load_source(source)
    if len(rows) != 1:
        raise ValueError("instance_audit_source must contain exactly one object")
    return rows[0]


def all_experiences(manifest: dict | None = None) -> list[dict]:
    manifest = manifest or load_manifest()
    return _load_source_group(manifest, "experience_sources")


def source_integrity(manifest: dict | None = None) -> dict:
    manifest = manifest or load_manifest()
    errors: list[str] = []
    loaded_sources: list[str] = []
    criterion_rows: list[dict] = []

    groups = ["criterion_sources", "operational_criterion_sources", "experience_sources"]
    for group in groups:
        for source in manifest.get(group, []):
            try:
                path = _source_path(source)
                if not path.is_file():
                    errors.append(f"missing source: {source.get('path')}")
                    continue
                loaded_sources.append(source.get("path"))
                rows = load_source(source)
                if group != "experience_sources":
                    criterion_rows.extend(rows)
            except (ValueError, json.JSONDecodeError) as exc:
                errors.append(str(exc))

    audit_source = manifest.get("instance_audit_source")
    if not isinstance(audit_source, dict):
        errors.append("missing instance_audit_source")
    else:
        try:
            audit_path = _source_path(audit_source)
            if not audit_path.is_file():
                errors.append(f"missing source: {audit_source.get('path')}")
            else:
                loaded_sources.append(audit_source.get("path"))
                criterion_rows.extend(load_source(audit_source))
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(str(exc))

    ids = [row.get("criterion_id") for row in criterion_rows if row.get("criterion_id")]
    duplicates = sorted({criterion_id for criterion_id in ids if ids.count(criterion_id) > 1})
    if duplicates:
        errors.append(f"duplicate criterion ids: {', '.join(duplicates)}")

    required = set(manifest.get("required_criterion_ids", []))
    missing_required = sorted(required - set(ids))
    if missing_required:
        errors.append(f"missing required criterion ids: {', '.join(missing_required)}")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "loaded_sources": loaded_sources,
        "criterion_ids": sorted(ids),
        "required_criterion_ids": sorted(required),
    }


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
    if _feature(case, "target_is_gptina_and_dedicated_method_applies") is True:
        return []

    rows = rows if rows is not None else all_experiences()
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


def instance_audit_status(instance_id: str | None, rows: list[dict] | None = None) -> dict:
    criterion = get_instance_audit_criterion()
    if not instance_id:
        return {
            "required": True,
            "status": "INSTANCE_ID_REQUIRED",
            "criterion_id": criterion.get("criterion_id"),
        }

    rows = rows if rows is not None else read_jsonl(INSTANCE_AUDITS)
    matches = [row for row in rows if row.get("instance_id") == instance_id and row.get("status") == "completed"]
    if not matches:
        return {
            "required": True,
            "status": "AUDIT_REQUIRED",
            "instance_id": instance_id,
            "criterion_id": criterion.get("criterion_id"),
            "required_output": criterion.get("required_output", []),
        }

    latest = matches[-1]
    return {
        "required": False,
        "status": "AUDIT_COMPLETE",
        "instance_id": instance_id,
        "criterion_id": criterion.get("criterion_id"),
        "audit_id": latest.get("audit_id"),
        "recorded_at": latest.get("recorded_at"),
        "recovery_head": latest.get("recovery_head"),
    }


def validate_instance_audit_payload(audit: dict) -> list[str]:
    criterion = get_instance_audit_criterion()
    missing: list[str] = []
    for field in criterion.get("required_output", []):
        if audit.get(field) in (None, "", [], {}):
            missing.append(field)
    return missing


def record_instance_audit(instance_id: str, audit: dict, path: Path = INSTANCE_AUDITS) -> dict:
    if not instance_id:
        raise ValueError("instance_id required")
    missing = validate_instance_audit_payload(audit)
    if missing:
        raise ValueError(f"instance audit missing required fields: {', '.join(missing)}")

    existing = read_jsonl(path)
    record = {
        "schema_version": 1,
        "audit_id": audit.get("audit_id") or f"AUDIT-{instance_id}-{len(existing) + 1}",
        "instance_id": instance_id,
        "recorded_at": audit.get("recorded_at") or datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "recovery_head": audit.get("recovery_head"),
        "objective": audit.get("objective"),
        "observed_gap": audit.get("observed_gap"),
        "why_it_limits_goal": audit.get("why_it_limits_goal"),
        "proposed_improvement": audit.get("proposed_improvement"),
        "verification_test": audit.get("verification_test"),
        "regression_risk": audit.get("regression_risk"),
        "separate_adoption_condition": audit.get("separate_adoption_condition"),
        "evidence_refs": audit.get("evidence_refs", []),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def _operational_snapshot(rows: list[dict] | None = None) -> list[dict]:
    rows = current_criteria(rows if rows is not None else all_operational_criteria())
    return [
        {
            "criterion_id": row.get("criterion_id"),
            "statement": row.get("statement"),
            "scope": row.get("scope", []),
            "exceptions": row.get("exceptions", []),
            "anti_regression": row.get("anti_regression", {}),
            "provenance": row.get("evidence_refs", []),
        }
        for row in rows
    ]


def recover_case(case: dict, rows: list[dict] | None = None, experience_rows: list[dict] | None = None) -> dict:
    integrity = source_integrity()
    rows = current_criteria(rows if rows is not None else all_criteria())
    matches = [evaluate_applicability(case, row) for row in rows]
    clarifications = sorted({m for row in matches for m in row.get("missing", [])})
    applicable = [row for row in matches if row.get("status") == CORRECTION_APPLIES]
    experiences = recover_experiences(case, rows=experience_rows)
    operational = _operational_snapshot()

    if integrity["status"] != "PASS":
        status = CONFLICTING
    elif clarifications:
        status = NEEDS_CLARIFICATION
    elif applicable:
        status = CORRECTION_APPLIES
    else:
        status = CLEAR

    proving_sources = {p for row in matches for p in row.get("provenance", [])}
    proving_sources.update(p for row in experiences for p in row.get("provenance", []))
    proving_sources.update(p for row in operational for p in row.get("provenance", []))

    audit_required = _feature(case, "alberto_portable_recovered_in_instance") is True or bool(case.get("instance_id"))
    audit_state = (
        instance_audit_status(case.get("instance_id") or _feature(case, "instance_id"))
        if audit_required
        else {"required": False, "status": "NOT_REQUIRED_FOR_CASE"}
    )

    return {
        "status": status,
        "case_id": case.get("case_id"),
        "relevant_corrections": matches,
        "operational_criteria": operational,
        "relevant_experiences": experiences,
        "instance_audit": audit_state,
        "source_integrity": integrity,
        "decision_critical_unknowns": clarifications,
        "proving_sources": sorted(proving_sources),
        "note": "Domain criteria require explicit applicability. Operational criteria are recovered as process constraints. Verified experiences remain contextual precedents. Per-instance self-audit is tracked separately and must be completed once per recovered instance.",
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

    for criterion in all_operational_criteria():
        shortcuts = set((criterion.get("anti_regression") or {}).get("shortcuts_to_reject", []))
        violated.extend(sorted(assumptions & shortcuts))

    violated = sorted(set(violated))
    if recovery["status"] == NEEDS_CLARIFICATION:
        status = NEEDS_CLARIFICATION
    elif recovery["source_integrity"]["status"] != "PASS":
        status = CONFLICTING
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
    parser = argparse.ArgumentParser(description="Alberto-portable recovery safety with complete sources, contextual experience and per-instance audit tracking")
    sub = parser.add_subparsers(dest="command", required=True)

    p_recover = sub.add_parser("recover")
    p_recover.add_argument("--case", required=True)

    p_check = sub.add_parser("check")
    p_check.add_argument("--case", required=True)
    p_check.add_argument("--candidate", required=True)

    sub.add_parser("sources")

    p_audit_status = sub.add_parser("audit-status")
    p_audit_status.add_argument("--instance-id", required=True)

    p_record_audit = sub.add_parser("record-audit")
    p_record_audit.add_argument("--instance-id", required=True)
    p_record_audit.add_argument("--audit", required=True)

    args = parser.parse_args()
    if args.command == "sources":
        payload = source_integrity()
    elif args.command == "audit-status":
        payload = instance_audit_status(args.instance_id)
    elif args.command == "record-audit":
        payload = record_instance_audit(args.instance_id, load_json(args.audit))
    else:
        case = load_json(args.case)
        if args.command == "recover":
            payload = recover_case(case)
        else:
            payload = anti_regression_check(case, load_json(args.candidate))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
