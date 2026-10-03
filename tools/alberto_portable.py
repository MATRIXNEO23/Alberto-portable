#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DECISIONS = DATA / "decisions.jsonl"
OUTCOMES = DATA / "outcomes.jsonl"
METHODS = DATA / "method_observations.jsonl"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    rows = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSONL {path}:{i}: {exc}")
        if not isinstance(value, dict):
            raise SystemExit(f"Invalid JSONL {path}:{i}: object required")
        rows.append(value)
    return rows


def parse_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def cmd_record_decision(args: argparse.Namespace) -> None:
    record = {
        "schema_version": 1,
        "decision_id": args.decision_id,
        "recorded_at": now_iso(),
        "task_type": args.task_type,
        "context": args.context,
        "alternatives": parse_list(args.alternatives),
        "choice": args.choice,
        "reasons": parse_list(args.reasons),
        "evidence_refs": parse_list(args.evidence_refs),
        "risk": args.risk,
        "reversible": args.reversible,
        "expected_outcome": args.expected_outcome,
        "supersedes": args.supersedes,
    }
    if any(r.get("decision_id") == args.decision_id for r in read_jsonl(DECISIONS)):
        raise SystemExit(f"decision_id already exists: {args.decision_id}")
    append_jsonl(DECISIONS, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def cmd_record_outcome(args: argparse.Namespace) -> None:
    decisions = {r.get("decision_id") for r in read_jsonl(DECISIONS)}
    if args.decision_id not in decisions:
        raise SystemExit(f"unknown decision_id: {args.decision_id}")
    record = {
        "schema_version": 1,
        "outcome_id": args.outcome_id,
        "decision_id": args.decision_id,
        "recorded_at": now_iso(),
        "technical_result": args.technical_result,
        "tests_passed": args.tests_passed,
        "regressions": parse_list(args.regressions),
        "artifact_refs": parse_list(args.artifact_refs),
        "alberto_validation": {
            "status": args.alberto_validation,
            "notes": args.alberto_notes or "",
        },
        "notes": args.notes or "",
    }
    append_jsonl(OUTCOMES, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def cmd_record_method(args: argparse.Namespace) -> None:
    record = {
        "schema_version": 1,
        "observation_id": args.observation_id,
        "recorded_at": now_iso(),
        "method": args.method,
        "task_type": args.task_type,
        "role": args.role,
        "canonical_source_access": args.canonical_source_access,
        "verified_result": args.verified_result,
        "hallucination": args.hallucination,
        "build_result": args.build_result,
        "alberto_validation": args.alberto_validation,
        "cost_class": args.cost_class,
        "latency_class": args.latency_class,
        "evidence_refs": parse_list(args.evidence_refs),
        "notes": args.notes or "",
    }
    append_jsonl(METHODS, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def observation_score(obs: dict, *, require_canonical: bool, risk: str) -> float:
    score = 0.0
    result = obs.get("verified_result")
    if result == "correct":
        score += 4.0
    elif result == "partial":
        score += 1.5
    elif result == "wrong":
        score -= 4.0

    if obs.get("hallucination") is True:
        score -= 5.0
    if obs.get("build_result") == "passed":
        score += 2.0
    elif obs.get("build_result") == "failed":
        score -= 2.0

    av = obs.get("alberto_validation")
    if av == "accepted":
        score += 4.0
    elif av == "accepted_with_notes":
        score += 2.0
    elif av == "rejected":
        score -= 4.0

    if require_canonical and not obs.get("canonical_source_access"):
        score -= 3.0 if risk == "high" else 1.0
    return score


def cmd_route(args: argparse.Namespace) -> None:
    rows = read_jsonl(METHODS)
    exact = [r for r in rows if r.get("task_type") == args.task_type and r.get("role") == args.role]
    task_only = [r for r in rows if r.get("task_type") == args.task_type]
    evidence = exact if exact else task_only

    if not evidence:
        print(json.dumps({
            "status": "insufficient_evidence",
            "task_type": args.task_type,
            "role": args.role,
            "recommendations": [],
        }, ensure_ascii=False, indent=2))
        return

    by_method: dict[str, list[dict]] = defaultdict(list)
    for row in evidence:
        if args.require_canonical and not row.get("canonical_source_access") and args.risk == "high":
            continue
        by_method[str(row.get("method"))].append(row)

    ranked = []
    for method, observations in by_method.items():
        scores = [observation_score(o, require_canonical=args.require_canonical, risk=args.risk) for o in observations]
        ranked.append({
            "method": method,
            "task_type": args.task_type,
            "role": args.role,
            "observations": len(observations),
            "evidence_score": round(sum(scores) / len(scores), 3),
            "accepted_by_alberto": sum(o.get("alberto_validation") in {"accepted", "accepted_with_notes"} for o in observations),
            "hallucinations": sum(o.get("hallucination") is True for o in observations),
            "evidence_refs": sorted({ref for o in observations for ref in o.get("evidence_refs", [])}),
        })

    ranked.sort(key=lambda item: (-item["evidence_score"], -item["observations"], item["method"]))
    print(json.dumps({
        "status": "ok" if ranked else "insufficient_evidence",
        "task_type": args.task_type,
        "role": args.role,
        "risk": args.risk,
        "reversible": args.reversible,
        "require_canonical": args.require_canonical,
        "recommendations": ranked,
        "note": "This is contextual routing evidence, not a global ranking of methods.",
    }, ensure_ascii=False, indent=2))


def cmd_validate(_: argparse.Namespace) -> None:
    errors = []
    for path, required in [
        (DECISIONS, {"decision_id", "task_type", "choice", "reasons"}),
        (OUTCOMES, {"outcome_id", "decision_id", "technical_result", "alberto_validation"}),
        (METHODS, {"observation_id", "method", "task_type", "role", "verified_result"}),
    ]:
        try:
            rows = read_jsonl(path)
        except SystemExit as exc:
            errors.append(str(exc))
            continue
        seen = set()
        for i, row in enumerate(rows, 1):
            missing = required - set(row)
            if missing:
                errors.append(f"{path}:{i} missing {sorted(missing)}")
            ident = row.get(next(iter(required & {"decision_id", "outcome_id", "observation_id"}), ""))
            if ident and ident in seen:
                errors.append(f"{path}:{i} duplicate id {ident}")
            if ident:
                seen.add(ident)
    if errors:
        raise SystemExit("\n".join(errors))
    print("OK")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Alberto-portable decision memory and contextual method router")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("record-decision")
    p.add_argument("--decision-id", required=True)
    p.add_argument("--task-type", required=True)
    p.add_argument("--context", required=True)
    p.add_argument("--alternatives", default="")
    p.add_argument("--choice", required=True)
    p.add_argument("--reasons", required=True)
    p.add_argument("--evidence-refs", default="")
    p.add_argument("--risk", choices=["low", "medium", "high"], required=True)
    p.add_argument("--reversible", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--expected-outcome", required=True)
    p.add_argument("--supersedes")
    p.set_defaults(func=cmd_record_decision)

    p = sub.add_parser("record-outcome")
    p.add_argument("--outcome-id", required=True)
    p.add_argument("--decision-id", required=True)
    p.add_argument("--technical-result", choices=["passed", "partial", "failed"], required=True)
    p.add_argument("--tests-passed", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--regressions", default="")
    p.add_argument("--artifact-refs", default="")
    p.add_argument("--alberto-validation", choices=["accepted", "accepted_with_notes", "rejected", "not_tested"], default="not_tested")
    p.add_argument("--alberto-notes", default="")
    p.add_argument("--notes", default="")
    p.set_defaults(func=cmd_record_outcome)

    p = sub.add_parser("record-method")
    p.add_argument("--observation-id", required=True)
    p.add_argument("--method", required=True)
    p.add_argument("--task-type", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--canonical-source-access", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--verified-result", choices=["correct", "partial", "wrong", "unverified"], required=True)
    p.add_argument("--hallucination", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--build-result", choices=["passed", "failed", "not_applicable", "not_tested"], default="not_tested")
    p.add_argument("--alberto-validation", choices=["accepted", "accepted_with_notes", "rejected", "not_tested"], default="not_tested")
    p.add_argument("--cost-class", choices=["low", "medium", "high", "unknown"], default="unknown")
    p.add_argument("--latency-class", choices=["low", "medium", "high", "unknown"], default="unknown")
    p.add_argument("--evidence-refs", default="")
    p.add_argument("--notes", default="")
    p.set_defaults(func=cmd_record_method)

    p = sub.add_parser("route")
    p.add_argument("--task-type", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--risk", choices=["low", "medium", "high"], required=True)
    p.add_argument("--reversible", action=argparse.BooleanOptionalAction, default=False)
    p.add_argument("--require-canonical", action=argparse.BooleanOptionalAction, default=False)
    p.set_defaults(func=cmd_route)

    p = sub.add_parser("validate")
    p.set_defaults(func=cmd_validate)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
