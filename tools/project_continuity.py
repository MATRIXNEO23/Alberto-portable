#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTINUITY_ROOT = ROOT / "continuity" / "projects"

PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
REQUIRED_FIELDS = (
    "schema_version",
    "checkpoint_id",
    "project_id",
    "captured_at",
    "repository",
    "branch",
    "head",
    "objective",
    "completed",
    "verified",
    "unverified",
    "decisions",
    "corrections",
    "constraints",
    "touched_components",
    "open_loops",
    "next_action",
    "regression_risks",
    "provenance_refs",
)
LIST_FIELDS = (
    "completed",
    "verified",
    "unverified",
    "decisions",
    "corrections",
    "constraints",
    "touched_components",
    "open_loops",
    "regression_risks",
    "provenance_refs",
)


class ContinuityError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ContinuityError("captured_at must be a non-empty ISO-8601 string")
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ContinuityError(f"invalid captured_at: {value!r}") from exc
    if parsed.tzinfo is None:
        raise ContinuityError("captured_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def _validate_project_id(project_id: str) -> str:
    if not isinstance(project_id, str) or not PROJECT_ID_RE.fullmatch(project_id):
        raise ContinuityError("project_id must match ^[a-z0-9][a-z0-9._-]{1,63}$")
    return project_id


def _project_dir(project_id: str, root: Path = CONTINUITY_ROOT) -> Path:
    return root / _validate_project_id(project_id)


def _canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_obj(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContinuityError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContinuityError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContinuityError(f"{path}: object required")
    return value


def _safe_checkpoint_relpath(captured_at: str, checkpoint_id: str) -> Path:
    stamp = _parse_time(captured_at)
    if not isinstance(checkpoint_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]{3,96}", checkpoint_id):
        raise ContinuityError("checkpoint_id contains unsupported characters")
    return Path("micro-checkpoints") / f"{stamp.year:04d}" / f"{stamp.month:02d}" / f"{stamp.day:02d}" / f"{checkpoint_id}.json"


def validate_checkpoint(payload: dict[str, Any], expected_project: str | None = None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ContinuityError("checkpoint payload must be an object")
    missing = [name for name in REQUIRED_FIELDS if name not in payload]
    if missing:
        raise ContinuityError(f"checkpoint missing required fields: {', '.join(missing)}")
    if payload.get("schema_version") != 1:
        raise ContinuityError("checkpoint schema_version must be 1")
    project_id = _validate_project_id(payload.get("project_id"))
    if expected_project is not None and project_id != expected_project:
        raise ContinuityError(f"checkpoint project_id {project_id!r} does not match requested project {expected_project!r}")
    _parse_time(payload.get("captured_at"))
    for field in ("repository", "branch", "head", "objective", "next_action"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ContinuityError(f"{field} must be a non-empty string")
    for field in LIST_FIELDS:
        if not isinstance(payload.get(field), list):
            raise ContinuityError(f"{field} must be a list")
    if payload["verified"] and payload["provenance_refs"] == []:
        raise ContinuityError("verified facts require at least one provenance_refs entry")
    dedicated = payload.get("dedicated_recovery")
    if dedicated is not None and not isinstance(dedicated, bool):
        raise ContinuityError("dedicated_recovery must be boolean when present")
    return payload


def _pointer_path(project_id: str, root: Path = CONTINUITY_ROOT) -> Path:
    return _project_dir(project_id, root) / "LIVE_CONTEXT.json"


def _load_pointer(project_id: str, root: Path = CONTINUITY_ROOT) -> dict[str, Any] | None:
    path = _pointer_path(project_id, root)
    if not path.is_file():
        return None
    pointer = _read_json(path)
    if pointer.get("project_id") != project_id:
        raise ContinuityError("LIVE_CONTEXT project_id mismatch")
    return pointer


def _resolve_pointer_checkpoint(project_id: str, pointer: dict[str, Any], root: Path = CONTINUITY_ROOT) -> tuple[Path, dict[str, Any]]:
    rel = pointer.get("latest_checkpoint")
    if not isinstance(rel, str) or not rel:
        raise ContinuityError("LIVE_CONTEXT missing latest_checkpoint")
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise ContinuityError("LIVE_CONTEXT checkpoint path escapes project directory")
    if not rel_path.parts or rel_path.parts[0] != "micro-checkpoints":
        raise ContinuityError("LIVE_CONTEXT checkpoint must live under micro-checkpoints/")
    project_dir = _project_dir(project_id, root).resolve()
    checkpoint_path = (project_dir / rel_path).resolve()
    if project_dir not in checkpoint_path.parents:
        raise ContinuityError("LIVE_CONTEXT checkpoint escapes project directory")
    checkpoint = validate_checkpoint(_read_json(checkpoint_path), expected_project=project_id)
    actual_sha = _sha256_obj(checkpoint)
    expected_sha = pointer.get("checkpoint_sha256")
    if expected_sha != actual_sha:
        raise ContinuityError(f"LIVE_CONTEXT checksum mismatch: expected {expected_sha}, got {actual_sha}")
    if pointer.get("checkpoint_id") != checkpoint.get("checkpoint_id"):
        raise ContinuityError("LIVE_CONTEXT checkpoint_id mismatch")
    return checkpoint_path, checkpoint


def write_checkpoint(payload: dict[str, Any], root: Path = CONTINUITY_ROOT) -> dict[str, Any]:
    checkpoint = validate_checkpoint(dict(payload))
    project_id = checkpoint["project_id"]
    if checkpoint.get("dedicated_recovery") is True:
        raise ContinuityError("generic project micro-checkpoint disabled because dedicated_recovery=true")
    project_dir = _project_dir(project_id, root)
    rel = _safe_checkpoint_relpath(checkpoint["captured_at"], checkpoint["checkpoint_id"])
    path = project_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = validate_checkpoint(_read_json(path), expected_project=project_id)
        if _canonical_json(existing) != _canonical_json(checkpoint):
            raise ContinuityError(f"immutable checkpoint already exists with different content: {path}")
    else:
        path.write_text(json.dumps(checkpoint, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    existing_pointer = _load_pointer(project_id, root)
    if existing_pointer is not None:
        _, existing_checkpoint = _resolve_pointer_checkpoint(project_id, existing_pointer, root)
        if _parse_time(checkpoint["captured_at"]) < _parse_time(existing_checkpoint["captured_at"]):
            raise ContinuityError("refusing to move LIVE_CONTEXT backwards to an older checkpoint")
    pointer = {
        "schema_version": 1,
        "project_id": project_id,
        "updated_at": _now(),
        "checkpoint_id": checkpoint["checkpoint_id"],
        "latest_checkpoint": rel.as_posix(),
        "checkpoint_sha256": _sha256_obj(checkpoint),
        "canonicality": "derived_pointer_to_immutable_checkpoint",
    }
    pointer_path = _pointer_path(project_id, root)
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    pointer_path.write_text(json.dumps(pointer, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return {"checkpoint": checkpoint, "pointer": pointer, "path": rel.as_posix()}


def recover_project(project_id: str, root: Path = CONTINUITY_ROOT) -> dict[str, Any]:
    project_id = _validate_project_id(project_id)
    pointer = _load_pointer(project_id, root)
    if pointer is None:
        return {"status": "NO_CHECKPOINT", "project_id": project_id, "checkpoint": None}
    path, checkpoint = _resolve_pointer_checkpoint(project_id, pointer, root)
    return {
        "status": "RECOVERED",
        "project_id": project_id,
        "pointer": pointer,
        "checkpoint_path": path.relative_to(_project_dir(project_id, root)).as_posix(),
        "checkpoint": checkpoint,
        "rule": "checkpoint is operational continuity; repository/project sources remain canonical for live state",
    }


def audit_project(project_id: str, root: Path = CONTINUITY_ROOT) -> dict[str, Any]:
    project_id = _validate_project_id(project_id)
    project_dir = _project_dir(project_id, root)
    errors: list[str] = []
    warnings: list[str] = []
    checkpoint_ids: set[str] = set()
    checkpoints: list[tuple[Path, dict[str, Any]]] = []
    micro_root = project_dir / "micro-checkpoints"
    if micro_root.is_dir():
        for path in sorted(micro_root.rglob("*.json")):
            try:
                checkpoint = validate_checkpoint(_read_json(path), expected_project=project_id)
                checkpoint_id = checkpoint["checkpoint_id"]
                if checkpoint_id in checkpoint_ids:
                    errors.append(f"duplicate checkpoint_id: {checkpoint_id}")
                checkpoint_ids.add(checkpoint_id)
                checkpoints.append((path, checkpoint))
            except ContinuityError as exc:
                errors.append(str(exc))
    pointer = None
    pointer_path = _pointer_path(project_id, root)
    if pointer_path.is_file():
        try:
            pointer = _load_pointer(project_id, root)
            pointer_path_resolved, pointer_checkpoint = _resolve_pointer_checkpoint(project_id, pointer, root)
            if checkpoints:
                newest = max(checkpoints, key=lambda item: _parse_time(item[1]["captured_at"]))
                if _parse_time(pointer_checkpoint["captured_at"]) != _parse_time(newest[1]["captured_at"]):
                    warnings.append("LIVE_CONTEXT does not point to the newest captured_at checkpoint")
                if pointer_path_resolved != newest[0].resolve():
                    warnings.append("LIVE_CONTEXT path differs from newest checkpoint path")
        except ContinuityError as exc:
            errors.append(str(exc))
    elif checkpoints:
        errors.append("checkpoints exist but LIVE_CONTEXT.json is missing")
    return {
        "status": "PASS" if not errors else "FAIL",
        "project_id": project_id,
        "checkpoint_count": len(checkpoints),
        "pointer_present": pointer is not None,
        "errors": errors,
        "warnings": warnings,
    }


def _load_input(path: str) -> dict[str, Any]:
    if path == "-":
        value = json.load(sys.stdin)
        if not isinstance(value, dict):
            raise ContinuityError("stdin JSON must be an object")
        return value
    return _read_json(Path(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project-partitioned micro-checkpoint continuity for Alberto-portable")
    parser.add_argument("--root", type=Path, default=CONTINUITY_ROOT, help="continuity/projects root")
    sub = parser.add_subparsers(dest="command", required=True)
    checkpoint_p = sub.add_parser("checkpoint")
    checkpoint_p.add_argument("--project", required=True)
    checkpoint_p.add_argument("--input", required=True, help="JSON file or - for stdin")
    recover_p = sub.add_parser("recover")
    recover_p.add_argument("--project", required=True)
    audit_p = sub.add_parser("audit")
    audit_p.add_argument("--project", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "checkpoint":
            payload = _load_input(args.input)
            if payload.get("project_id") != args.project:
                raise ContinuityError("input project_id must exactly match --project")
            result = write_checkpoint(payload, args.root)
        elif args.command == "recover":
            result = recover_project(args.project, args.root)
        else:
            result = audit_project(args.project, args.root)
    except ContinuityError as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result.get("status") not in {"FAIL", "ERROR"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
