#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CRITERIA = ROOT / "data" / "criteria.jsonl"
ACTIVATIONS = ROOT / "data" / "criterion_activation_events.jsonl"

ACTIVATION_ERROR_RE = re.compile(r"data/criteria\.jsonl:(\d+) active without explicit activation act$")


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.is_file():
        return rows
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{lineno}: object required")
        rows.append(value)
    return rows


def validate_activation_events(criteria_rows: list[dict]) -> tuple[dict[str, dict], list[str]]:
    errors: list[str] = []
    events = read_jsonl(ACTIVATIONS)
    known = {row.get("criterion_id") for row in criteria_rows if row.get("criterion_id")}
    by_criterion: dict[str, dict] = {}
    seen_activation_ids: set[str] = set()

    for index, event in enumerate(events, 1):
        prefix = f"{ACTIVATIONS.relative_to(ROOT)}:{index}"
        activation_id = event.get("activation_id")
        criterion_id = event.get("criterion_id")
        if not activation_id:
            errors.append(f"{prefix} missing activation_id")
        elif activation_id in seen_activation_ids:
            errors.append(f"{prefix} duplicate activation_id {activation_id}")
        else:
            seen_activation_ids.add(str(activation_id))
        if criterion_id not in known:
            errors.append(f"{prefix} unknown criterion_id {criterion_id!r}")
            continue
        if criterion_id in by_criterion:
            errors.append(f"{prefix} duplicate activation event for {criterion_id}")
            continue
        if event.get("activated_by") != "alberto":
            errors.append(f"{prefix} activation must be attributed to alberto")
            continue
        refs = event.get("evidence_refs") or []
        if not refs:
            errors.append(f"{prefix} activation requires evidence_refs")
            continue
        missing_refs = [ref for ref in refs if not (ROOT / str(ref)).is_file()]
        if missing_refs:
            errors.append(f"{prefix} unresolved evidence_refs: {missing_refs}")
            continue
        by_criterion[str(criterion_id)] = event
    return by_criterion, errors


def run_legacy_validator(criteria_rows: list[dict], activations: dict[str, dict]) -> list[str]:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "alberto_portable.py"), "validate"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = "\n".join(part for part in (proc.stdout, proc.stderr) if part).strip()
    if proc.returncode == 0:
        return []

    remaining: list[str] = []
    for raw in output.splitlines():
        line = raw.strip()
        normalized = line.replace(str(ROOT) + "/", "").replace(str(ROOT) + "\\", "")
        match = ACTIVATION_ERROR_RE.search(normalized)
        if not match:
            if line:
                remaining.append(line)
            continue
        lineno = int(match.group(1))
        if lineno < 1 or lineno > len(criteria_rows):
            remaining.append(line)
            continue
        criterion_id = criteria_rows[lineno - 1].get("criterion_id")
        if criterion_id not in activations:
            remaining.append(line)
    return remaining


def main() -> int:
    try:
        criteria_rows = read_jsonl(CRITERIA)
        activations, activation_errors = validate_activation_events(criteria_rows)
    except (ValueError, json.JSONDecodeError) as exc:
        print(exc, file=sys.stderr)
        return 1

    errors = list(activation_errors)
    errors.extend(run_legacy_validator(criteria_rows, activations))

    recovery_fp = None
    try:
        from recovery_safety import source_integrity, structure_fingerprint
        integrity = source_integrity()
        recovery_fp = structure_fingerprint()
        if integrity.get("status") != "PASS":
            errors.extend(integrity.get("errors", []))
    except Exception as exc:
        errors.append(f"recovery source integrity check failed: {exc}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(json.dumps({
        "status": "PASS",
        "legacy_validator": "PASS_WITH_APPEND_ONLY_ACTIVATION_PROVENANCE",
        "activation_events": len(activations),
        "recovery_source_integrity": "PASS",
        "structure_fingerprint": recovery_fp,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
