#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DECISIONS = DATA / "decisions.jsonl"
OUTCOMES = DATA / "outcomes.jsonl"
METHODS = DATA / "method_observations.jsonl"
REFLECTIONS = DATA / "reflections.jsonl"
CRITERIA = DATA / "criteria.jsonl"
LINKS = DATA / "causal_links.jsonl"
CLARIFICATIONS = DATA / "clarifications.jsonl"

EXIT_NEEDS_CLARIFICATION = 3

EPISTEMIC_STATES = {"verified", "declared_by_alberto", "observed", "inferred",
                    "conflicting", "unknown"}
AUTHORS = {"alberto", "agent", "system"}
TRIGGER_KINDS = {"outcome_failed", "outcome_rejected_by_alberto", "build_result",
                 "test_result", "contradiction", "question", "observation",
                 "regression", "manual_note", "other"}
CHANGE_TYPES = {"none", "confirmed", "doubted", "exception_created",
                "question_opened", "events_linked", "refined", "narrowed",
                "widened", "replaced", "hypothesized", "contradicted"}
CAUSALITY_STATUSES = {"declared", "evidenced", "multiple_candidates", "unknown"}
SOURCE_TYPES = {"decision_ledger", "outcome_ledger", "method_ledger",
                "reflection_ledger", "criterion_ledger", "commit", "path",
                "build", "test", "ci_run", "alberto_statement", "external_url",
                "other"}
STRENGTHS = {"hypothesis", "candidate", "contextual_active", "contested", "deprecated"}
EPISTEMIC_BASES = {"declared_by_alberto", "observed", "inferred", "mixed"}
RELATIONS = {"caused_by", "caused_or_contributed_to", "contributed_to",
             "influenced", "supported", "contradicts", "implements",
             "superseded_by", "related_to"}
CLARIFICATION_STATUSES = {"open", "answered", "cancelled", "obsolete"}

# `verified` is decided STRUCTURALLY, never by text analysis (no keyword/regex
# heuristics: they are fragile and produce false verified). The claim kind is
# declared explicitly via --claim-kind:
#   technical_ref_fact -> the claim refers DIRECTLY to the resolvable object
#                         itself (path exists / commit resolves / ledger id);
#   alberto_statement  -> only with author=alberto + his verbatim;
#   alberto_interpretation / observation / other -> motivations, intentions,
#         preferences or emotional states about Alberto can NEVER be verified
#         through a generic technical source; use declared_by_alberto (real
#         verbatim), inferred, unknown or conflicting instead.
CLAIM_KINDS = {"technical_ref_fact", "alberto_statement",
               "alberto_interpretation", "observation", "other"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


_LAST_APPEND_TARGET: list[Path] = []


def append_jsonl(path: Path, record: dict) -> None:
    _LAST_APPEND_TARGET.append(path)
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
    # v0.3 ADDITIVE: surface relevant reflections/criteria as context only.
    # Scores and ordering above are computed exactly as v0.2; nothing here mutates them.
    relevant_reflections = []
    for r in read_jsonl(REFLECTIONS):
        if r.get("status") != "recorded":
            continue
        if args.task_type and r.get("task_type") not in (None, args.task_type):
            continue
        relevant_reflections.append({
            "reflection_id": r.get("reflection_id"),
            "epistemic_state": r.get("epistemic_state"),
            "change_type": r.get("change", {}).get("type"),
            "causality_status": r.get("change", {}).get("causality", {}).get("status"),
            "context": r.get("context"),
        })
    relevant_criteria = []
    for c in read_jsonl(CRITERIA):
        cur = _current_criterion_id(c.get("criterion_id"))
        rec = next((x for x in read_jsonl(CRITERIA) if x.get("criterion_id") == cur), c)
        if rec.get("strength") not in {"contextual_active", "candidate"}:
            continue
        scopes = set(rec.get("scope", []))
        if args.task_type and scopes and args.task_type not in scopes \
                and not ({"any", "all"} & scopes):
            continue
        relevant_criteria.append({
            "criterion_id": rec.get("criterion_id"),
            "statement": rec.get("statement"),
            "strength": rec.get("strength"),
            "epistemic_basis": rec.get("epistemic_basis"),
            "exceptions": rec.get("exceptions", []),
        })
    print(json.dumps({
        "status": "ok" if ranked else "insufficient_evidence",
        "task_type": args.task_type,
        "role": args.role,
        "risk": args.risk,
        "reversible": args.reversible,
        "require_canonical": args.require_canonical,
        "recommendations": ranked,
        "relevant_reflections": relevant_reflections,
        "relevant_criteria": relevant_criteria,
        "note": "This is contextual routing evidence, not a global ranking of methods.",
    }, ensure_ascii=False, indent=2))


def parse_conf(name: str, raw: str | None) -> float | None:
    if raw is None:
        return None
    try:
        v = float(raw)
    except ValueError:
        raise SystemExit(f"{name} must be a number")
    if not 0.0 <= v <= 1.0:
        raise SystemExit(f"{name} must be within [0,1]")
    return v


def parse_pipe_kv(spec: str) -> tuple[str, float | None]:
    """Parse 'text|0.4' into ('text', 0.4); confidence optional."""
    parts = spec.split("|")
    text = "|".join(parts[:-1]).strip() if len(parts) > 1 else spec.strip()
    conf = None
    if len(parts) > 1 and parts[-1].strip():
        try:
            conf = float(parts[-1])
        except ValueError:
            conf = None
    if not text:
        raise SystemExit(f"empty candidate/spec in {spec!r}")
    return text, conf


def _known_ids() -> set[str]:
    ids = set()
    for path, key in ((DECISIONS, "decision_id"), (OUTCOMES, "outcome_id"),
                      (METHODS, "observation_id"), (REFLECTIONS, "reflection_id"),
                      (CRITERIA, "criterion_id")):
        ids.update(str(r.get(key)) for r in read_jsonl(path) if r.get(key))
    return ids


def resolve_ref(ref: str) -> tuple[bool, str]:
    """Resolve a reference WITHOUT ever inventing it. Returns (resolved, kind)."""
    ref = ref.strip()
    if not ref:
        return False, "empty"
    if re.fullmatch(r"(D|O|R|C|M)-\S+", ref):
        return (True, "ledger_id") if ref in _known_ids() else (False, "ledger_id")
    if re.fullmatch(r"[0-9a-f]{7,40}", ref):
        # commit-ish: cannot verify locally in a shallow clone -> honest verdict
        try:
            import subprocess
            out = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", ref],
                                 capture_output=True)
            return (out.returncode == 0), "commit"
        except Exception:
            return False, "commit"
    candidate = ROOT / ref.split("#")[0]
    if candidate.exists():
        return True, "repo_path"
    if ref.startswith(("http://", "https://")):
        return False, "external_unverified"
    return False, "unresolvable"


def canonical_technical_claim(ref: str) -> tuple[str, str]:
    """Return the only proposition v0.3 can verify automatically for a ref.

    This deliberately avoids NLP entailment. A resolvable source proves only its
    own structural existence/identity, not arbitrary free-text claims nearby.
    """
    ok, kind = resolve_ref(ref)
    if not ok:
        raise SystemExit(f"technical_ref_fact requires a resolvable ref: {ref}")
    if kind == "repo_path":
        return f"path {ref} exists", kind
    if kind == "commit":
        return f"commit {ref} exists in repository", kind
    if kind == "ledger_id":
        return f"ledger id {ref} exists", kind
    raise SystemExit(f"technical_ref_fact unsupported ref kind: {kind}")


def provenance_entry(source_type: str, source_ref: str | None,
                     verbatim: str | None = None,
                     persistent_source_ref: str | None = None) -> dict:
    return {
        "source_type": source_type,
        "source_ref": source_ref,
        "persistent_source_ref": persistent_source_ref,
        "verbatim_excerpt": verbatim,
        "recorded_at": now_iso(),
        "resolves": bool(source_ref) and resolve_ref(str(source_ref))[0],
    }


class NeedsClarification(SystemExit):
    """Raised to abort a write and emit a machine-readable clarification payload.

    Exit code 3. The offending ledger receives ZERO bytes; a row is appended to
    the clarifications queue so the question is auditable and closable later.
    """

    def __init__(self, *, missing: list, reason: str, question_for_alberto: str,
                 would_affect: list, trigger_refs: list | None = None):
        self.payload = {
            "status": "NEEDS_CLARIFICATION",
            "missing": missing,
            "reason": reason,
            "question_for_alberto": question_for_alberto,
            "would_affect": would_affect,
        }
        self.trigger_refs = trigger_refs or []
        self.target_file_written = False
        super().__init__(EXIT_NEEDS_CLARIFICATION)

    def emit(self) -> None:
        qid = next_clarification_id()
        row = {
            "schema_version": 1,
            "clarification_event_id": next_clarification_event_id(),
            "clarification_id": qid,
            "created_at": now_iso(),
            "status": "open",
            "trigger_ref": self.trigger_refs[0] if self.trigger_refs else None,
            "trigger_refs": self.trigger_refs,
            "question_for_alberto": self.payload["question_for_alberto"],
            "missing": self.payload["missing"],
            "reason": self.payload["reason"],
            "would_affect": self.payload["would_affect"],
            "answer": None,
            "answered_at": None,
            "answer_provenance": None,
            "supersedes": None,
        }
        append_jsonl(CLARIFICATIONS, row)
        self.payload["clarification_id"] = qid
        print(json.dumps(self.payload, ensure_ascii=False, indent=2))


def next_clarification_id() -> str:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    taken = {r.get("clarification_id") for r in read_jsonl(CLARIFICATIONS)}
    i = len(taken) + 1 if taken else 1
    base = f"Q-{day}-{i:02d}"
    while base in taken:
        i += 1
        base = f"Q-{day}-{i:02d}"
    return base


def next_clarification_event_id() -> str:
    """Every row of clarifications.jsonl is an immutable EVENT snapshot.

    clarification_id identifies the QUESTION (may repeat across snapshots);
    clarification_event_id identifies THIS row and must be unique.
    """
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    taken = {r.get("clarification_event_id") for r in read_jsonl(CLARIFICATIONS)}
    i = len(taken) + 1 if taken else 1
    base = f"QE-{day}-{i:04d}"
    while base in taken:
        i += 1
        base = f"QE-{day}-{i:04d}"
    return base


# ---------------------------------------------------------------------------
# record-reflection
# ---------------------------------------------------------------------------

def rid_or(args) -> str:
    return getattr(args, "reflection_id", "?")


def cmd_record_reflection(args: argparse.Namespace) -> None:
    if any(r.get("reflection_id") == args.reflection_id for r in read_jsonl(REFLECTIONS)):
        raise SystemExit(f"reflection_id already exists: {args.reflection_id}")
    author = args.author
    state = args.epistemic_state
    context = args.context
    trigger_desc = args.trigger_desc
    trigger_refs = parse_list(args.trigger_ref)

    # --- collect blocking gaps first, ask ONE specific question -------------
    missing: list[str] = []
    why_ask = ""
    question = ""

    if state == "declared_by_alberto":
        if author != "alberto":
            raise SystemExit(
                "author cannot claim declared_by_alberto unless author=alberto: "
                f"author={author!r}, epistemic_state={state!r}")
        if not args.statement_excerpt:
            missing.append("statement_excerpt (verbatim quote of Alberto)")
            why_ask = ("declared_by_alberto requires a real verbatim statement; "
                       "without it we would fabricate what Alberto said")
            question = ("Puoi riportare (anche parafrasando fedelmente) la frase esatta "
                        "con cui dichiari questa riflessione?")
    if state == "verified":
        # No text heuristics and no entailment engine: v0.3 verifies only a
        # canonical structural proposition derived from exactly one real ref.
        claim_kind = getattr(args, "claim_kind", None)
        if claim_kind != "technical_ref_fact":
            raise SystemExit(
                "epistemic_state=verified requires --claim-kind technical_ref_fact; "
                "use declared_by_alberto/inferred/unknown/conflicting for personal interpretations")
        evidence = parse_list(args.evidence_ref)
        if len(evidence) != 1:
            raise SystemExit("verified technical_ref_fact requires exactly one --evidence-ref")
        ref = evidence[0]
        if not resolve_ref(ref)[0]:
            missing.append("one resolvable evidence_ref (commit/path/ledger id)")
            why_ask = "verified without a resolvable source would fabricate a fact"
            question = "Qual è il riferimento reale e verificabile per questo fatto tecnico?"
        else:
            canonical_claim, _claim_ref_kind = canonical_technical_claim(ref)
            if (args.interpretation or "").strip() != canonical_claim:
                raise SystemExit(
                    "verified technical_ref_fact must use the canonical claim derived from its ref: "
                    f"{canonical_claim!r}")

    for r in trigger_refs:
        if not resolve_ref(r)[0]:
            missing.append(f"trigger_ref risolvibile ({r} non esiste nei ledger/file)")
    if not context.strip():
        missing.append("context")
        why_ask = why_ask or "una riflessione senza contesto non è riagganciabile in futuro"
        question = question or "In quale contesto è avvenuta questa riflessione?"

    if missing:
        raise NeedsClarification(
            missing=missing,
            reason=why_ask,
            question_for_alberto=question,
            would_affect=["reflection_record_integrity", "future_retrieval",
                          "causal_trust"],
            trigger_refs=trigger_refs,
        )

    # --- non-blocking checks: refs that do not resolve are reported, not hidden
    unresolved_refs = [r for r in trigger_refs + parse_list(args.evidence_ref)
                       if not resolve_ref(r)[0]]
    if unresolved_refs and state in {"observed", "inferred"}:
        # keep going but mark honestly: they will be recorded as unresolved provenance
        pass

    # --- interpretation ------------------------------------------------------
    interp_state = args.interpretation_state or ("unknown" if not args.interpretation
                                                 else "inferred")
    interpretation = {
        "text": args.interpretation or "",
        "epistemic_state": interp_state,
        "confidence": parse_conf("interpretation-confidence", args.interpretation_confidence),
        "alternative_interpretations": parse_list(args.alternative_interpretation),
    }

    # --- change block (optional per design: not every reflection changes a rule)
    change_type = args.change_type or "none"
    why_changed = args.why_changed
    candidates = []
    specs = args.candidate_cause if isinstance(args.candidate_cause, list) \
        else parse_list(args.candidate_cause)
    for spec in specs:
        text, conf = parse_pipe_kv(spec)
        candidates.append({"cause": text, "confidence": conf})
    if args.causal_declared:
        causality_status = "declared"
    elif args.causal_evidence and why_changed:
        causality_status = "evidenced"
    elif candidates:
        causality_status = "multiple_candidates"
    else:
        causality_status = "unknown"
    if causality_status == "unknown":
        why_changed = None  # never invent the cause
    if causality_status == "evidenced" and author != "alberto" \
            and not any(resolve_ref(e)[0] for e in parse_list(args.evidence_ref)):
        raise NeedsClarification(
            missing=["evidence_ref risolvibile a supporto della causa"],
            reason="una causa marcata 'evidenced' da un agente deve poggiare su evidenza reale",
            question_for_alberto=("Qual è l'evidenza che supporta questa causa? "
                                  "(commit/test/build/CI/file o ID ledger esistente)"),
            would_affect=[f"{rid_or(args)}.change.causality.status"],
            trigger_refs=trigger_refs,
        )
    if causality_status in {"declared", "evidenced"} and not why_changed:
        raise NeedsClarification(
            missing=["why_changed"],
            reason=f"causality marked {causality_status} ma la causa non è dichiarata",
            question_for_alberto="Perché questo criterio è cambiato? Qual è la causa?",
            would_affect=["causal_chain_integrity"],
            trigger_refs=trigger_refs,
        )
    change = {
        "type": change_type,
        "previous_criterion": args.previous_criterion or None,
        "new_criterion": args.new_criterion or None,
        "what_changed": args.what_changed or (None if change_type == "none" else ""),
        "why_changed": why_changed or None,
        "causality": {
            "status": causality_status,
            "primary_cause": why_changed if causality_status in {"declared", "evidenced"} else None,
            "candidate_causes": candidates,
        },
    }

    # --- provenance ----------------------------------------------------------
    provenance = []
    if state == "declared_by_alberto":
        provenance.append(provenance_entry("alberto_statement", None,
                                           verbatim=args.statement_excerpt))
    for ref in parse_list(args.evidence_ref):
        ok, kind = resolve_ref(ref)
        stype = {"ledger_id": _ledger_source_type(ref), "repo_path": "path",
                 "commit": "commit"}.get(kind, "other")
        entry = provenance_entry(stype, ref)
        entry["resolves"] = ok
        provenance.append(entry)
    for ref in trigger_refs:
        ok, kind = resolve_ref(ref)
        entry = provenance_entry(_ledger_source_type(ref) if kind == "ledger_id" else "other", ref)
        entry["resolves"] = ok
        provenance.append(entry)

    rid = args.reflection_id
    if any(r.get("reflection_id") == rid for r in read_jsonl(REFLECTIONS)):
        raise SystemExit(f"reflection_id already exists: {rid}")

    record = {
        "schema_version": 1,
        "reflection_id": rid,
        "recorded_at": now_iso(),
        "occurred_at": args.occurred_at or None,
        "author": author,
        "status": "recorded",
        "context": context,
        "task_type": args.task_type or None,
        "trigger": {"kind": args.trigger_kind, "description": trigger_desc,
                    "refs": trigger_refs},
        "situation": args.situation or None,
        "interpretation": interpretation,
        "change": change,
        "exception_refs": parse_list(args.exception_ref),
        "applicability_conditions": parse_list(args.condition),
        "implications": parse_list(args.implication),
        "decision_refs": [r for r in parse_list(args.decision_ref)],
        "outcome_refs": [r for r in parse_list(args.outcome_ref)],
        "epistemic_state": state,
        "claim_kind": getattr(args, "claim_kind", None) or "other",
        "verified_fact": ({
            "ref": parse_list(args.evidence_ref)[0],
            "claim": canonical_technical_claim(parse_list(args.evidence_ref)[0])[0],
            "ref_kind": canonical_technical_claim(parse_list(args.evidence_ref)[0])[1],
        } if state == "verified" else None),
        "confidence": {
            "source_confidence": parse_conf("source-confidence", args.source_confidence),
            "model_confidence": parse_conf("model-confidence", args.model_confidence),
            "generality_confidence": parse_conf("generality-confidence", args.generality_confidence),
        },
        "provenance": provenance,
        "unresolved_refs": unresolved_refs,
        "supersedes": args.supersedes,
        "notes": args.notes or "",
    }
    append_jsonl(REFLECTIONS, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def _ledger_source_type(ref: str) -> str:
    return {"D": "decision_ledger", "O": "outcome_ledger", "M": "method_ledger",
            "R": "reflection_ledger", "C": "criterion_ledger"}.get(ref[:1], "other")


# ---------------------------------------------------------------------------
# flag-reflection-needed  (event activates the NEED, never the explanation)
# ---------------------------------------------------------------------------

def cmd_flag_reflection_needed(args: argparse.Namespace) -> None:
    refs = parse_list(args.ref)
    unresolved = [r for r in refs if not resolve_ref(r)[0]]
    if unresolved:
        raise SystemExit(f"cannot flag on unknown refs (nothing is invented): {unresolved}")
    rid = args.reflection_id
    if any(r.get("reflection_id") == rid for r in read_jsonl(REFLECTIONS)):
        raise SystemExit(f"reflection_id already exists: {rid}")
    record = {
        "schema_version": 1,
        "reflection_id": rid,
        "recorded_at": now_iso(),
        "occurred_at": None,
        "author": args.author,
        "status": "REFLECTION_NEEDED",
        "context": args.context,
        "task_type": args.task_type or None,
        "trigger": {"kind": args.trigger_kind,
                    "description": args.trigger_desc or "",
                    "refs": refs},
        "situation": None,
        "interpretation": {"text": "", "epistemic_state": "unknown",
                           "confidence": None, "alternative_interpretations": []},
        "change": {"type": "none", "previous_criterion": None, "new_criterion": None,
                   "what_changed": None, "why_changed": None,
                   "causality": {"status": "unknown", "primary_cause": None,
                                 "candidate_causes": []}},
        "exception_refs": [], "applicability_conditions": [], "implications": [],
        "decision_refs": [r for r in refs if r.startswith("D-")],
        "outcome_refs": [r for r in refs if r.startswith("O-")],
        "epistemic_state": "unknown",
        "confidence": {"source_confidence": None, "model_confidence": None,
                       "generality_confidence": None},
        "provenance": [provenance_entry(_ledger_source_type(r), r) for r in refs],
        "unresolved_refs": [],
        "supersedes": None,
        "notes": args.notes or "",
    }
    append_jsonl(REFLECTIONS, record)
    print(json.dumps({"status": "flagged", "reflection_id": rid,
                      "note": "Event flagged as needing reflection; no cause was inferred."},
                     ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# confirm-causality  (explicit act by Alberto upgrades causality.status)
# ---------------------------------------------------------------------------

def cmd_confirm_causality(args: argparse.Namespace) -> None:
    rows = read_jsonl(REFLECTIONS)
    target = next((r for r in rows if r.get("reflection_id") == args.reflection_id), None)
    if target is None:
        raise SystemExit(f"unknown reflection_id: {args.reflection_id}")
    by = getattr(args, "by", "alberto") or "alberto"
    if by != "alberto":
        # agent/system cannot fabricate an Alberto declaration; they may only
        # mark a cause as evidenced, and only on real resolvable evidence.
        if not args.provenance_ref:
            raise NeedsClarification(
                missing=["provenance_ref risolvibile (commit/test/build/CI/path/ledger id)"],
                reason=(f"confirm-causality --by {by} non può produrre 'declared': "
                        "solo Alberto dichiara; un agente può al più documentare una "
                        "causa supportata da evidenza reale"),
                question_for_alberto=("La causa è tua o si basa su evidenza tecnica? "
                                      "Indica la fonte verificabile."),
                would_affect=[f"{args.reflection_id}.change.causality.status"],
                trigger_refs=[args.reflection_id],
            )
        unresolved = [p for p in parse_list(args.provenance_ref) if not resolve_ref(p)[0]]
        if unresolved:
            raise SystemExit(f"evidence must be REAL artifacts, got: {unresolved}")
        new_status = "evidenced"
        prov_entries = []
        for p in parse_list(args.provenance_ref):
            ok, kind = resolve_ref(p)
            stype = {"ledger_id": _ledger_source_type(p), "repo_path": "path",
                     "commit": "commit"}.get(kind, "other")
            entry = provenance_entry(stype, p)
            entry["resolves"] = ok
            prov_entries.append(entry)
        link_state = "inferred"
    else:
        if not args.statement_excerpt:
            raise NeedsClarification(
                missing=["statement_excerpt"],
                reason="confirm-causality is an act attributed to Alberto: it needs his verbatim words",
                question_for_alberto=("Confermi che la causa è quella dichiarata? Riporta la frase "
                                      "con cui lo affermi."),
                would_affect=[f"{args.reflection_id}.change.causality.status"],
                trigger_refs=[args.reflection_id],
            )
        new_status = "declared"
        prov_entries = [provenance_entry("alberto_statement", None,
                                         verbatim=args.statement_excerpt)]
        link_state = "declared_by_alberto"
    supersede_id = args.new_reflection_id or f"{args.reflection_id}-ca{len(rows) + 1}"
    if any(r.get("reflection_id") == supersede_id for r in rows):
        raise SystemExit(f"reflection_id already exists: {supersede_id}")
    updated = json.loads(json.dumps(target))  # deep copy; original row stays on disk
    updated["reflection_id"] = supersede_id
    updated["recorded_at"] = now_iso()
    updated["supersedes"] = args.reflection_id
    updated["status"] = "recorded"
    updated["change"]["causality"]["status"] = new_status
    updated["change"]["causality"]["primary_cause"] = args.cause
    updated["change"]["why_changed"] = args.cause
    updated["provenance"].extend(prov_entries)
    append_jsonl(REFLECTIONS, updated)
    append_jsonl(LINKS, {
        "schema_version": 1,
        "link_id": f"L-{now_iso()}-{supersede_id}",
        "recorded_at": now_iso(),
        "event": "causality_confirmed",
        "confirmed_by": by,
        "from": args.reflection_id, "to": supersede_id,
        "relation": "superseded_by", "validity": "active",
        "epistemic_state": link_state, "confidence": 1.0,
        "explanation": args.cause,
        "provenance": prov_entries,
    })
    print(json.dumps(updated, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# link-cause / refute-link  (the causal graph, correction #5)
# ---------------------------------------------------------------------------

def cmd_link_cause(args: argparse.Namespace) -> None:
    src, dst = getattr(args, "from"), getattr(args, "to")
    for node in (src, dst):
        if node not in _known_ids():
            raise SystemExit(f"unknown node ref (nothing is invented): {node}")
    prov_refs = parse_list(args.provenance_ref)
    unresolved = [p for p in prov_refs if not resolve_ref(p)[0]]
    if unresolved:
        raise NeedsClarification(
            missing=[f"provenance_ref risolvibile per ognuno di: {unresolved}"],
            reason="un arco causale deve avere provenienza reale",
            question_for_alberto="Da quale fonte verificabile dipende questa relazione causale?",
            would_affect=[f"link:{src}->{dst}"],
            trigger_refs=[src, dst],
        )
    links = read_jsonl(LINKS)
    lid = f"L-{len(links) + 1:04d}"
    record = {
        "schema_version": 1,
        "link_id": lid,
        "recorded_at": now_iso(),
        "event": "link",
        "from": src, "to": dst,
        "relation": args.relation,
        "validity": "active",
        "epistemic_state": args.epistemic_state,
        "confidence": parse_conf("confidence", args.confidence),
        "explanation": args.explanation or None,
        "provenance": [provenance_entry(_ledger_source_type(p) if resolve_ref(p)[1] == "ledger_id"
                                       else "path", p) for p in prov_refs],
        "alternative_of": None,
    }
    append_jsonl(LINKS, record)

    # conflict detection: same (from,to) same relation, different explanations
    # -> BOTH kept, graph status becomes conflicting. No auto-choice, ever.
    siblings = [l for l in links
                if l.get("from") == src and l.get("to") == dst
                and l.get("relation") == args.relation
                and l.get("validity", "active") == "active"
                and l.get("event") == "link"]
    conflicting = any((s.get("explanation") or "") != (args.explanation or "")
                      for s in siblings) if args.explanation else bool(siblings)
    status = "conflicting" if conflicting else "ok"
    print(json.dumps({"status": "linked", "link_id": lid, "graph_status": status,
                      "note": ("due spiegazioni incompatibili sulla stessa relazione: "
                               "entrambe conservate, stato=conflicting"
                               if status == "conflicting" else
                               "archi multipli consentiti su nodi diversi")},
                     ensure_ascii=False, indent=2))


def cmd_refute_link(args: argparse.Namespace) -> None:
    links = read_jsonl(LINKS)
    target = next((l for l in links if l.get("link_id") == args.link_id
                   and l.get("event") == "link"), None)
    if target is None:
        raise SystemExit(f"unknown link_id: {args.link_id}")
    prov_refs = parse_list(args.provenance_ref)
    unresolved = [p for p in prov_refs if not resolve_ref(p)[0]]
    if unresolved:
        raise SystemExit(f"refutation needs resolvable provenance, got: {unresolved}")
    event = {
        "schema_version": 1,
        "link_id": f"{args.link_id}-refuted",
        "recorded_at": now_iso(),
        "event": "refutation",
        "refutes": args.link_id,
        "from": target["from"], "to": target["to"],
        "relation": target["relation"],
        "validity": "refuted",
        "epistemic_state": args.epistemic_state or "observed",
        "confidence": parse_conf("confidence", args.confidence),
        "explanation": args.reason,
        "provenance": [provenance_entry("path" if resolve_ref(p)[1] == "repo_path"
                                       else _ledger_source_type(p), p) for p in prov_refs],
    }
    append_jsonl(LINKS, event)
    print(json.dumps(event, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# trace-chain  (bidirectional traversal across all ledgers)
# ---------------------------------------------------------------------------

def _node_meta(node_id: str) -> dict:
    prefix = node_id[:1]
    store = {"D": DECISIONS, "O": OUTCOMES, "M": METHODS,
             "R": REFLECTIONS, "C": CRITERIA}.get(prefix)
    key = {"D": "decision_id", "O": "outcome_id", "M": "observation_id",
           "R": "reflection_id", "C": "criterion_id"}.get(prefix, "")
    kind = {"D": "decision", "O": "outcome", "M": "method_observation",
            "R": "reflection", "C": "criterion"}.get(prefix, "unknown")
    rec = next((r for r in read_jsonl(store) if r.get(key) == node_id), {}) if store else {}
    current = node_id
    if kind == "criterion":
        current = _current_criterion_id(node_id)
    return {"id": node_id, "kind": kind, "current": current,
            "recorded_at": rec.get("recorded_at")}


def cmd_trace_chain(args: argparse.Namespace) -> None:
    start = getattr(args, "from")
    if start not in _known_ids():
        raise SystemExit(f"unknown node ref: {start}")

    raw_links = read_jsonl(LINKS)
    refuted = {l.get("refutes") for l in raw_links if l.get("event") == "refutation"}
    active_links = [l for l in raw_links
                    if l.get("event") == "link" and l.get("link_id") not in refuted]

    # Build a single adjacency graph from REAL explicit links plus structural
    # append-only relations. No disconnected ledger scanning is used.
    graph_edges: list[dict] = []
    for l in active_links:
        graph_edges.append({
            "link_id": l.get("link_id"), "from": l.get("from"), "to": l.get("to"),
            "relation": l.get("relation"), "epistemic_state": l.get("epistemic_state"),
            "confidence": l.get("confidence"), "explanation": l.get("explanation"),
            "provenance": l.get("provenance"),
        })

    # Ledger FK: a decision produces its recorded outcomes. This is a structural
    # verified relation and becomes traversable only if the decision/outcome is
    # connected to the requested chain.
    for out in read_jsonl(OUTCOMES):
        did, oid = out.get("decision_id"), out.get("outcome_id")
        if did and oid and did in _known_ids() and oid in _known_ids():
            graph_edges.append({
                "link_id": None, "from": did, "to": oid, "relation": "produced",
                "epistemic_state": "verified", "confidence": 1.0,
                "explanation": "outcome ledger FK", "provenance": ["outcomes.jsonl"],
            })

    # Reflection correction history is also structural and append-only.
    refl_rows = read_jsonl(REFLECTIONS)
    refl_ids = {r.get("reflection_id") for r in refl_rows}
    for r in refl_rows:
        sup, rid = r.get("supersedes"), r.get("reflection_id")
        if sup and rid and sup in refl_ids:
            graph_edges.append({
                "link_id": None, "from": sup, "to": rid, "relation": "superseded_by",
                "epistemic_state": "verified", "confidence": 1.0,
                "explanation": "reflection supersedes chain (append-only)",
                "provenance": ["reflections.jsonl"],
            })

    adj = defaultdict(list)
    for e in graph_edges:
        src, dst = e.get("from"), e.get("to")
        if not src or not dst:
            continue
        adj[src].append((e, dst))
        adj[dst].append((e, src))

    seen, queue, edges = {start}, [start], []
    nodes = []
    while queue:
        cur = queue.pop(0)
        nodes.append(_node_meta(cur))
        for edge, nxt in adj.get(cur, []):
            if edge not in edges:
                edges.append(edge)
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)

    print(json.dumps({
        "status": "ok", "root": start, "nodes": nodes, "edges": edges,
        "note": "Archi espliciti attivi + FK decisione→outcome + catene supersedes. "
                "Link refutati esclusi dal cammino attivo; la storia resta nei ledger.",
    }, ensure_ascii=False, indent=2))


def _reflection_supersede_view() -> tuple[list, list]:
    """Expose reflection supersedes chains so trace-chain shows which reflection
    version is CURRENT and which are HISTORICAL (corrections never erase)."""
    rows = read_jsonl(REFLECTIONS)
    by_id = {r.get("reflection_id"): r for r in rows}
    edges, nodes = [], []
    for r in rows:
        sup = r.get("supersedes")
        if sup and sup in by_id:
            edges.append({"link_id": None, "from": sup, "to": r["reflection_id"],
                          "relation": "superseded_by", "epistemic_state": "verified",
                          "confidence": 1.0,
                          "explanation": "reflection supersedes chain (append-only)",
                          "provenance": ["reflections.jsonl"]})
            for nid in (sup, r["reflection_id"]):
                nodes.append(_node_meta(nid))
    return edges, nodes


# ---------------------------------------------------------------------------
# criteria  (strength ≠ epistemic_basis; derived metrics recomputed, never stored)
# ---------------------------------------------------------------------------

def _current_criterion_id(cid: str) -> str:
    rows = read_jsonl(CRITERIA)
    cur = cid
    while True:
        nxt = next((r["criterion_id"] for r in rows if r.get("supersedes") == cur), None)
        if not nxt:
            return cur
        cur = nxt


def cmd_current_criterion(args: argparse.Namespace) -> None:
    if args.criterion_id not in {r.get("criterion_id") for r in read_jsonl(CRITERIA)}:
        raise SystemExit(f"unknown criterion_id: {args.criterion_id}")
    cur = _current_criterion_id(args.criterion_id)
    rec = next(r for r in read_jsonl(CRITERIA) if r.get("criterion_id") == cur)
    history = []
    cid = args.criterion_id
    rows = read_jsonl(CRITERIA)
    while cid:
        r = next((x for x in rows if x.get("criterion_id") == cid), None)
        if not r:
            break
        history.append({"criterion_id": cid, "strength": r["strength"],
                        "recorded_at": r["recorded_at"]})
        cid = next((x["criterion_id"] for x in rows if x.get("supersedes") == cid), None)
    print(json.dumps({"status": "ok", "current": rec, "history": history},
                     ensure_ascii=False, indent=2))


def _validate_criterion_args(args, *, creating: bool) -> dict:
    basis = args.epistemic_basis
    excerpt = getattr(args, "statement_excerpt", None)
    if basis == "declared_by_alberto" and not excerpt:
        raise NeedsClarification(
            missing=["statement_excerpt (verbatim)"],
            reason="declared_by_alberto come base epistemica richiede le parole reali di Alberto",
            question_for_alberto="Puoi fornire la dichiarazione letterale su cui si basa questo criterio?",
            would_affect=[f"criterion:{args.criterion_id}.epistemic_basis"],
            trigger_refs=parse_list(getattr(args, "origin_reflection", None)),
        )
    evidence = parse_list(args.evidence_ref)
    unresolved = [e for e in evidence if not resolve_ref(e)[0]]
    if unresolved:
        raise NeedsClarification(
            missing=[f"evidence_ref risolvibile per: {unresolved}"],
            reason="un criterio con evidenza inventata contaminerebbe ogni retrieval futuro",
            question_for_alberto="Qual è il riferimento reale (ID ledger o path esistente) di questa evidenza?",
            would_affect=[f"criterion:{args.criterion_id}.evidence_refs"],
            trigger_refs=evidence,
        )
    counterexamples = parse_list(getattr(args, "counterexample_ref", None))
    bad_ce = [c for c in counterexamples if not resolve_ref(c)[0]]
    if bad_ce:
        raise SystemExit(f"counterexample refs must resolve: {bad_ce}")
    strength = getattr(args, "strength", None) or "hypothesis"
    if strength not in STRENGTHS:
        raise SystemExit(f"invalid strength: {strength}")
    if basis == "declared_by_alberto" and strength in {"contextual_active"}:
        raise SystemExit("activation requires explicit activate-criterion --by alberto")
    return {"strength": strength, "basis": basis, "evidence": evidence,
            "counterexamples": counterexamples}


def cmd_upsert_criterion(args: argparse.Namespace) -> None:
    rows = read_jsonl(CRITERIA)
    v = _validate_criterion_args(args, creating=True)
    # duplicate/supersedes checks run only after validation passes, so a rejected
    # command never appends anything to criteria.jsonl (zero-partial-write rule)
    if any(r.get("criterion_id") == args.criterion_id for r in rows):
        raise SystemExit(f"criterion_id already exists: {args.criterion_id}")
    supersedes = args.supersedes
    if supersedes and supersedes not in {r.get("criterion_id") for r in rows}:
        raise SystemExit(f"unknown supersedes: {supersedes}")
    origins = parse_list(args.origin_reflection)
    bad_origin = [o for o in origins if not resolve_ref(o)[0]]
    if bad_origin:
        raise SystemExit(f"origin reflections must exist: {bad_origin}")
    record = {
        "schema_version": 1,
        "criterion_id": args.criterion_id,
        "recorded_at": now_iso(),
        "statement": args.statement,
        "scope": parse_list(args.scope),
        "exceptions": parse_list(args.exception),
        "strength": v["strength"],
        "epistemic_basis": v["basis"],
        "evidence_refs": v["evidence"],
        "counterexample_refs": v["counterexamples"],
        "origin_reflections": origins,
        "confidence": {
            "source_confidence": parse_conf("source-confidence", args.source_confidence),
            "model_confidence": parse_conf("model-confidence", args.model_confidence),
            "generality_confidence": parse_conf("generality-confidence", args.generality_confidence),
        },
        "supersedes": supersedes,
        "notes": args.notes or "",
    }
    append_jsonl(CRITERIA, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))


def cmd_amend_criterion(args: argparse.Namespace) -> None:
    args.supersedes = getattr(args, "supersedes", None)
    cmd_upsert_criterion(args)


def cmd_activate_criterion(args: argparse.Namespace) -> None:
    rows = read_jsonl(CRITERIA)
    target_id = _current_criterion_id(args.criterion_id)
    target = next((r for r in rows if r.get("criterion_id") == target_id), None)
    if target is None:
        raise SystemExit(f"unknown criterion_id: {args.criterion_id}")
    if args.by != "alberto":
        raise SystemExit("only Alberto can activate a criterion (no automatic promotion)")
    if not args.statement_excerpt:
        raise NeedsClarification(
            missing=["statement_excerpt (verbatim)"],
            reason="attivare un criterio è un atto attribuito ad Alberto",
            question_for_alberto="Con quali parole attivi questo criterio?",
            would_affect=[f"{target_id}.strength"],
            trigger_refs=[target_id],
        )
    new_id = args.new_criterion_id or f"{target_id}-act{len(rows) + 1}"
    if any(r.get("criterion_id") == new_id for r in rows):
        raise SystemExit(f"criterion_id already exists: {new_id}")
    updated = json.loads(json.dumps(target))
    updated["criterion_id"] = new_id
    updated["recorded_at"] = now_iso()
    updated["supersedes"] = target_id
    updated["strength"] = "contextual_active"
    updated.setdefault("provenance_activation", []).append(
        provenance_entry("alberto_statement", None, verbatim=args.statement_excerpt))
    append_jsonl(CRITERIA, updated)
    print(json.dumps(updated, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# evaluate-criterion  (pure function: DERIVES metrics, never writes)
# ---------------------------------------------------------------------------

def cmd_evaluate_criterion(args: argparse.Namespace) -> None:
    rows = read_jsonl(CRITERIA)
    target_id = _current_criterion_id(args.criterion_id)
    target = next((r for r in rows if r.get("criterion_id") == target_id), None)
    if target is None:
        raise SystemExit(f"unknown criterion_id: {args.criterion_id}")
    chain_ids = {target_id}
    cid = args.criterion_id
    while cid:
        chain_ids.add(cid)
        cid = next((x["criterion_id"] for x in rows if x.get("supersedes") == cid), None)
    versions = [r for r in rows if r.get("criterion_id") in chain_ids]

    refl_rows = read_jsonl(REFLECTIONS)
    dec_rows = read_jsonl(DECISIONS)
    out_rows = read_jsonl(OUTCOMES)
    ev_refs = sorted({e for r in versions for e in r.get("evidence_refs", [])})

    contexts = set()
    independent = set()
    for e in ev_refs:
        ok, _ = resolve_ref(e)
        if not ok:
            continue
        if e.startswith("R-"):
            rr = next((x for x in refl_rows if x.get("reflection_id") == e), None)
            if rr:
                independent.add(rr.get("recorded_at", e))
                contexts.add((rr.get("task_type"), rr.get("context")))
        elif e.startswith("D-"):
            dr = next((x for x in dec_rows if x.get("decision_id") == e), None)
            if dr:
                independent.add(dr.get("recorded_at", e))
                contexts.add((dr.get("task_type"), dr.get("context")))
        else:
            independent.add(e)
            contexts.add(("file", e))
    timestamps = [r.get("recorded_at") for r in versions if r.get("recorded_at")]
    stability_days = None
    if len(timestamps) >= 2:
        fmt = "%Y-%m-%dT%H:%M:%S%z"
        ts = sorted(datetime.strptime(t[:25], fmt[:25]) for t in
                    (x.replace("+00:00", "+0000") for x in timestamps))
        stability_days = round((ts[-1] - ts[0]).total_seconds() / 86400, 2)
    elif len(timestamps) == 1:
        age = datetime.now(timezone.utc).replace(tzinfo=None) - \
            datetime.strptime(timestamps[0][:19], "%Y-%m-%dT%H:%M:%S")
        stability_days = round(age.total_seconds() / 86400, 2)

    counterexamples = sorted({c for r in versions for c in r.get("counterexample_refs", [])})
    declared = any(r.get("epistemic_basis") == "declared_by_alberto" for r in versions)
    distinct_contexts = len({c for c in contexts if c and c != (None, None)})
    max_strength = target["strength"]
    recommendation = {
        "contextual_active": "keep scoped; activation was explicit",
        "candidate": ("promovable only by Alberto (activate-criterion --by alberto)"
                      if declared else
                      "needs Alberto declaration or broader independent evidence"),
        "hypothesis": "single-case hypothesis; gather more independent evidence",
        "contested": "has counterexamples; narrow scope or deprecate via new version",
        "deprecated": "historical only",
    }.get(max_strength, "?")
    report = {
        "status": "report_only",
        "criterion_id": target_id,
        "strength": target["strength"],
        "epistemic_basis": target["epistemic_basis"],
        "derived": {
            "independent_observations": len(independent),
            "distinct_contexts": distinct_contexts,
            "counterexamples": len(counterexamples),
            "temporal_stability_days": stability_days,
            "explicit_alberto_declaration": declared,
        },
        "recommendation": recommendation,
        "note": "Derived values are recomputed from real refs at query time; "
                "they are never canonical stored facts.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# find-reflections  (retrieval incl. superseded/refuted awareness)
# ---------------------------------------------------------------------------

def cmd_find_reflections(args: argparse.Namespace) -> None:
    rows = read_jsonl(REFLECTIONS)
    superseded_by = {r.get("supersedes") for r in rows if r.get("supersedes")}
    results = []
    for r in rows:
        if not args.include_superseded and r.get("reflection_id") in superseded_by:
            continue
        if args.author and r.get("author") != args.author:
            continue
        if args.epistemic_state and r.get("epistemic_state") != args.epistemic_state:
            continue
        if args.change_type and r.get("change", {}).get("type") != args.change_type:
            continue
        if args.trigger_kind and r.get("trigger", {}).get("kind") != args.trigger_kind:
            continue
        if args.exception and args.exception not in r.get("exception_refs", []):
            continue
        if args.influenced_decision:
            links = read_jsonl(LINKS)
            hit = any(l.get("from") == r["reflection_id"]
                      and l.get("to") == args.influenced_decision
                      and l.get("event") == "link"
                      for l in links)
            if not hit:
                continue
        results.append({
            "reflection_id": r["reflection_id"],
            "status": r.get("status"),
            "author": r.get("author"),
            "epistemic_state": r.get("epistemic_state"),
            "change_type": r.get("change", {}).get("type"),
            "causality": r.get("change", {}).get("causality", {}).get("status"),
            "superseded": r["reflection_id"] in superseded_by,
            "context": r.get("context"),
        })
    print(json.dumps({"status": "ok", "count": len(results), "results": results},
                     ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# clarifications queue
# ---------------------------------------------------------------------------

def cmd_answer_clarification(args: argparse.Namespace) -> None:
    rows = read_jsonl(CLARIFICATIONS)
    latest = _latest_queue()
    target = latest.get(args.clarification_id)
    if target is None or target.get("status") != "open":
        raise SystemExit(f"no OPEN clarification with id: {args.clarification_id}")
    prov_type = args.answer_provenance or "alberto_statement"
    if prov_type == "alberto_statement" and not args.verbatim:
        raise SystemExit("an answer attributed to Alberto needs the verbatim text "
                         "(we do not paraphrase him into a fact)")
    answer_row = json.loads(json.dumps(target))  # deep copy; original row stays on disk
    answer_row["clarification_event_id"] = next_clarification_event_id()
    answer_row["clarification_id"] = args.clarification_id
    answer_row["status"] = "answered"
    answer_row["answer"] = args.answer
    answer_row["answered_at"] = now_iso()
    answer_row["answer_provenance"] = provenance_entry(prov_type, args.source_ref,
                                                       verbatim=args.verbatim)
    answer_row["supersedes"] = None
    # queue rows are mutable-by-versioning: append the answered snapshot; readers
    # take the LAST row per clarification_id (documented in validate).
    append_jsonl(CLARIFICATIONS, answer_row)
    print(json.dumps(answer_row, ensure_ascii=False, indent=2))


def _latest_queue() -> dict[str, dict]:
    """Current state of each question = its LAST appended snapshot."""
    latest: dict[str, dict] = {}
    for r in read_jsonl(CLARIFICATIONS):
        latest[r["clarification_id"]] = r
    return latest


def cmd_cancel_clarification(args: argparse.Namespace) -> None:
    target = _latest_queue().get(args.clarification_id)
    if target is None or target.get("status") != "open":
        raise SystemExit(f"no OPEN clarification: {args.clarification_id}")
    row = json.loads(json.dumps(target))
    row["clarification_event_id"] = next_clarification_event_id()
    row["status"] = "cancelled"
    row["answer"] = None
    row["answered_at"] = now_iso()
    row["answer_provenance"] = None
    row["cancellation_reason"] = args.reason
    append_jsonl(CLARIFICATIONS, row)
    print(json.dumps(row, ensure_ascii=False, indent=2))


def cmd_obsolete_clarification(args: argparse.Namespace) -> None:
    """Close an OPEN clarification as obsolete, preserving append-only history."""
    target = _latest_queue().get(args.clarification_id)
    if target is None or target.get("status") != "open":
        raise SystemExit(f"no OPEN clarification: {args.clarification_id}")
    row = json.loads(json.dumps(target))
    row["clarification_event_id"] = next_clarification_event_id()
    row["status"] = "obsolete"
    row["answer"] = None
    row["answered_at"] = None
    row["answer_provenance"] = None
    row["obsolete_at"] = now_iso()
    row["obsolete_reason"] = args.reason
    append_jsonl(CLARIFICATIONS, row)
    print(json.dumps(row, ensure_ascii=False, indent=2))


def cmd_list_clarifications(args: argparse.Namespace) -> None:
    latest = _latest_queue()
    rows = [r for r in latest.values() if not args.status or r.get("status") == args.status]
    print(json.dumps({"status": "ok", "count": len(rows), "clarifications": rows},
                     ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# persist-statement  (attach a real transcript WITHOUT rewriting the record)
# ---------------------------------------------------------------------------

def cmd_persist_statement(args: argparse.Namespace) -> None:
    ok, kind = resolve_ref(args.persistent_source_ref)
    if not ok:
        raise SystemExit(f"persistent_source_ref must be a REAL artifact: "
                         f"{args.persistent_source_ref} ({kind})")
    rows = read_jsonl(REFLECTIONS)
    target = next((r for r in rows if r.get("reflection_id") == args.reflection_id), None)
    if target is None:
        raise SystemExit(f"unknown reflection_id: {args.reflection_id}")
    has_statement = any(p.get("source_type") == "alberto_statement"
                        for p in target.get("provenance", []))
    if not has_statement:
        raise SystemExit(f"{args.reflection_id} has no alberto_statement provenance to attach")
    event = {
        "schema_version": 1,
        "link_id": f"E-{now_iso()}-{args.reflection_id}",
        "recorded_at": now_iso(),
        "event": "statement_persisted",
        "from": args.reflection_id,
        "to": args.persistent_source_ref,
        "relation": "persistent_source_of",
        "validity": "active",
        "epistemic_state": "verified",
        "confidence": 1.0,
        "explanation": "transcript/file persisted after the inline statement; "
                       "original reflection record NOT rewritten",
        "provenance": [provenance_entry("path" if kind == "repo_path" else "other",
                                        args.persistent_source_ref)],
    }
    append_jsonl(LINKS, event)
    print(json.dumps(event, ensure_ascii=False, indent=2))


ID_KEYS = ("decision_id", "outcome_id", "observation_id", "reflection_id",
           "criterion_id", "link_id")
# clarifications are versioned snapshots: clarification_id REPEATS by design
# (open → answered/cancelled/obsolete); only clarification_event_id is unique.
CLARIFICATION_TRANSITIONS = {
    "open": {"answered", "cancelled", "obsolete"},
    "answered": set(),
    "cancelled": set(),
    "obsolete": set(),
}


def _supersedes_cycle_checks(rows, id_key, path, errors):
    """no self-supersede, unknown target, or supersede cycle (report only)."""
    ids = {r.get(id_key) for r in rows}
    parent = {}
    for i, row in enumerate(rows, 1):
        rid = row.get(id_key)
        sup = row.get("supersedes")
        if not sup:
            continue
        if sup == rid:
            errors.append(f"{path}:{i} self-supersede {rid}")
            continue
        if sup not in ids:
            errors.append(f"{path}:{i} supersedes unknown id: {sup}")
            continue
        parent[rid] = sup
    for start in parent:
        seen, cur = set(), start
        while cur in parent:
            if cur in seen:
                errors.append(f"{path}: supersede cycle involving {start}")
                break
            seen.add(cur)
            cur = parent[cur]


def cmd_validate(_: argparse.Namespace) -> None:
    errors: list[str] = []
    specs = [
        (DECISIONS, {"decision_id", "task_type", "choice", "reasons"}),
        (OUTCOMES, {"outcome_id", "decision_id", "technical_result", "alberto_validation"}),
        (METHODS, {"observation_id", "method", "task_type", "role", "verified_result"}),
        (REFLECTIONS, {"schema_version", "reflection_id", "recorded_at", "author",
                       "status", "context", "trigger", "interpretation", "change",
                       "epistemic_state", "confidence", "provenance"}),
        (CRITERIA, {"schema_version", "criterion_id", "recorded_at", "statement",
                    "scope", "strength", "epistemic_basis", "evidence_refs"}),
        (LINKS, {"schema_version", "link_id", "recorded_at", "event"}),
        (CLARIFICATIONS, {"schema_version", "clarification_event_id", "clarification_id",
                          "created_at", "status", "question_for_alberto"}),
    ]
    ledger_rows: dict[Path, list[dict]] = {}
    for path, required in specs:
        try:
            rows = read_jsonl(path)
        except SystemExit as exc:
            errors.append(str(exc))
            continue
        ledger_rows[path] = rows
        seen: set[tuple] = set()
        for i, row in enumerate(rows, 1):
            missing = required - set(row)
            if missing:
                errors.append(f"{path}:{i} missing {sorted(missing)}")
            ident = None
            for key in ID_KEYS:          # deterministic, unlike iter(set)
                if key in row:
                    ident = (key, row[key])
                    break
            if ident and ident in seen:
                errors.append(f"{path}:{i} duplicate id {ident}")
            if ident:
                seen.add(ident)
            # semantic checks for the new ledgers
            if path == REFLECTIONS:
                if row.get("author") not in AUTHORS:
                    errors.append(f"{path}:{i} bad author {row.get('author')!r}")
                if row.get("epistemic_state") not in EPISTEMIC_STATES:
                    errors.append(f"{path}:{i} bad epistemic_state {row.get('epistemic_state')!r}")
                ct = row.get("change", {}).get("type")
                if ct not in CHANGE_TYPES:
                    errors.append(f"{path}:{i} bad change.type {ct!r}")
                cs = row.get("change", {}).get("causality", {}).get("status")
                if cs not in CAUSALITY_STATUSES:
                    errors.append(f"{path}:{i} bad causality.status {cs!r}")
                if row.get("author") != "alberto" and \
                        row.get("epistemic_state") == "declared_by_alberto":
                    errors.append(f"{path}:{i} non-alberto author claims declared_by_alberto")
                claim_kind = row.get("claim_kind", "other")
                if claim_kind not in CLAIM_KINDS:
                    errors.append(f"{path}:{i} bad claim_kind {claim_kind!r}")
                if row.get("epistemic_state") == "verified":
                    if claim_kind != "technical_ref_fact":
                        errors.append(f"{path}:{i} verified requires claim_kind=technical_ref_fact")
                    vf = row.get("verified_fact") or {}
                    ref = vf.get("ref")
                    if not ref or not resolve_ref(str(ref))[0]:
                        errors.append(f"{path}:{i} verified without resolvable verified_fact.ref")
                    else:
                        try:
                            expected_claim, expected_kind = canonical_technical_claim(str(ref))
                            if vf.get("claim") != expected_claim or vf.get("ref_kind") != expected_kind:
                                errors.append(f"{path}:{i} verified_fact does not match canonical ref claim")
                            if row.get("interpretation", {}).get("text") != expected_claim:
                                errors.append(f"{path}:{i} verified interpretation is not canonical ref claim")
                        except SystemExit as exc:
                            errors.append(f"{path}:{i} {exc}")
                    if not any(p.get("resolves") for p in row.get("provenance", [])):
                        errors.append(f"{path}:{i} verified without resolvable provenance")
                if row.get("epistemic_state") == "declared_by_alberto" and not any(
                        p.get("source_type") == "alberto_statement" and p.get("verbatim_excerpt")
                        for p in row.get("provenance", [])):
                    errors.append(f"{path}:{i} declared_by_alberto without verbatim statement")
                if row.get("change", {}).get("causality", {}).get("status") == "unknown" \
                        and row.get("change", {}).get("why_changed"):
                    errors.append(f"{path}:{i} why_changed present with unknown causality")
            if path == CRITERIA:
                if row.get("strength") not in STRENGTHS:
                    errors.append(f"{path}:{i} bad strength {row.get('strength')!r}")
                if row.get("epistemic_basis") not in EPISTEMIC_BASES:
                    errors.append(f"{path}:{i} bad epistemic_basis {row.get('epistemic_basis')!r}")
                if row.get("epistemic_basis") == "declared_by_alberto" and \
                        row.get("strength") == "contextual_active" and \
                        not row.get("provenance_activation"):
                    errors.append(f"{path}:{i} active without explicit activation act")
            if path == LINKS and row.get("event") == "link":
                if row.get("relation") not in RELATIONS:
                    errors.append(f"{path}:{i} bad relation {row.get('relation')!r}")
                if row.get("epistemic_state") not in EPISTEMIC_STATES:
                    errors.append(f"{path}:{i} bad epistemic_state on link")
            if path == CLARIFICATIONS:
                st = row.get("status")
                if st not in CLARIFICATION_STATUSES:
                    errors.append(f"{path}:{i} bad clarification status {st!r}")
                if st == "answered" and not row.get("answer_provenance"):
                    errors.append(f"{path}:{i} answered without answer_provenance")
                ap_ = row.get("answer_provenance") or {}
                if ap_.get("source_type") == "alberto_statement" \
                        and not ap_.get("verbatim_excerpt"):
                    errors.append(f"{path}:{i} answer attributed to Alberto without verbatim")
    # cross-row structural checks (report only, never auto-repair)
    _supersedes_cycle_checks(ledger_rows.get(REFLECTIONS, []), "reflection_id",
                             REFLECTIONS, errors)
    _supersedes_cycle_checks(ledger_rows.get(CRITERIA, []), "criterion_id",
                             CRITERIA, errors)
    # causal links: unique endpoints/events, refutation targets an existing link
    link_rows = ledger_rows.get(LINKS, [])
    link_ids = {r.get("link_id") for r in link_rows}
    for i, row in enumerate(link_rows, 1):
        if row.get("event") == "refutation":
            tgt = row.get("refutes")
            if tgt not in link_ids:
                errors.append(f"{LINKS}:{i} refutation targets unknown link: {tgt}")
            elif not any(l.get("link_id") == tgt and l.get("event") == "link"
                         for l in link_rows):
                errors.append(f"{LINKS}:{i} refutation must target a 'link' event: {tgt}")
    # clarifications: per-question snapshot sequences must be legal
    per_q: dict[str, list[tuple[int, str]]] = {}
    ev_seen: set = set()
    for i, row in enumerate(ledger_rows.get(CLARIFICATIONS, []), 1):
        eid = row.get("clarification_event_id")
        if eid in ev_seen:
            errors.append(f"{CLARIFICATIONS}:{i} duplicate clarification_event_id {eid}")
        ev_seen.add(eid)
        per_q.setdefault(row.get("clarification_id"), []).append((i, row.get("status")))
    for qid, seq in per_q.items():
        statuses = [s for _, s in seq]
        if statuses and statuses[0] != "open":
            errors.append(f"{CLARIFICATIONS}: first snapshot of {qid} must be open, "
                          f"got {statuses[0]!r}")
        for pos in range(1, len(statuses)):
            prev, nxt = statuses[pos - 1], statuses[pos]
            if nxt not in CLARIFICATION_TRANSITIONS.get(prev, set()):
                errors.append(f"{CLARIFICATIONS}: illegal transition on {qid}: "
                              f"{prev} -> {nxt}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("OK")


class _StrengthProvided(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        setattr(namespace, "strength_provided", True)


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

    # ---- v0.3 reflections ----------------------------------------------------
    p = sub.add_parser("record-reflection")
    p.add_argument("--reflection-id", required=True)
    p.add_argument("--author", choices=sorted(AUTHORS), required=True)
    p.add_argument("--occurred-at")
    p.add_argument("--context", required=True)
    p.add_argument("--task-type")
    p.add_argument("--situation", default="")
    p.add_argument("--trigger-kind", choices=sorted(TRIGGER_KINDS), required=True)
    p.add_argument("--trigger-desc", default="")
    p.add_argument("--trigger-ref", default="")
    p.add_argument("--interpretation", default="")
    p.add_argument("--interpretation-state", choices=sorted(EPISTEMIC_STATES - {"declared_by_alberto"}))
    p.add_argument("--interpretation-confidence")
    p.add_argument("--alternative-interpretation", default="")
    p.add_argument("--change-type", choices=sorted(CHANGE_TYPES))
    p.add_argument("--previous-criterion")
    p.add_argument("--new-criterion")
    p.add_argument("--what-changed")
    p.add_argument("--why-changed")
    p.add_argument("--candidate-cause", action="append", default=[],
                   help="'cause text|confidence' (repeatable; keeps alternatives)")
    p.add_argument("--causal-declared", action="store_true",
                   help="cause explicitly declared (requires --why-changed)")
    p.add_argument("--causal-evidence", action="store_true",
                   help="cause supported by evidence (requires --why-changed)")
    p.add_argument("--exception-ref", default="")
    p.add_argument("--condition", default="")
    p.add_argument("--implication", default="")
    p.add_argument("--decision-ref", default="")
    p.add_argument("--outcome-ref", default="")
    p.add_argument("--evidence-ref", default="")
    p.add_argument("--statement-excerpt", default="",
                   help="verbatim Alberto words (required when declared_by_alberto)")
    p.add_argument("--epistemic-state", choices=sorted(EPISTEMIC_STATES), required=True)
    p.add_argument("--claim-kind", choices=sorted(CLAIM_KINDS), default="other",
                   help="structural claim type; verified requires technical_ref_fact")
    p.add_argument("--source-confidence")
    p.add_argument("--model-confidence")
    p.add_argument("--generality-confidence")
    p.add_argument("--supersedes")
    p.add_argument("--notes", default="")
    p.set_defaults(func=cmd_record_reflection)

    p = sub.add_parser("flag-reflection-needed")
    p.add_argument("--reflection-id", required=True)
    p.add_argument("--author", choices=sorted(AUTHORS), default="system")
    p.add_argument("--context", required=True)
    p.add_argument("--task-type")
    p.add_argument("--trigger-kind", choices=sorted(TRIGGER_KINDS), required=True)
    p.add_argument("--trigger-desc", default="")
    p.add_argument("--ref", required=True, help="existing node(s) D-/O-/R-/M-/C- or path")
    p.add_argument("--notes", default="")
    p.set_defaults(func=cmd_flag_reflection_needed)

    p = sub.add_parser("confirm-causality")
    p.add_argument("--reflection-id", required=True)
    p.add_argument("--cause", required=True)
    p.add_argument("--by", choices=["alberto", "agent", "system"], default="alberto",
                   help="who performs the act; only alberto can produce 'declared'")
    p.add_argument("--statement-excerpt", default="")
    p.add_argument("--provenance-ref", default="",
                   help="resolvable evidence refs (required for --by agent/system)")
    p.add_argument("--new-reflection-id")
    p.set_defaults(func=cmd_confirm_causality)

    p = sub.add_parser("find-reflections")
    p.add_argument("--author", choices=sorted(AUTHORS))
    p.add_argument("--epistemic-state", choices=sorted(EPISTEMIC_STATES))
    p.add_argument("--change-type", choices=sorted(CHANGE_TYPES))
    p.add_argument("--trigger-kind", choices=sorted(TRIGGER_KINDS))
    p.add_argument("--exception")
    p.add_argument("--influenced-decision")
    p.add_argument("--include-superseded", action="store_true")
    p.set_defaults(func=cmd_find_reflections)

    p = sub.add_parser("persist-statement")
    p.add_argument("--reflection-id", required=True)
    p.add_argument("--persistent-source-ref", required=True)
    p.set_defaults(func=cmd_persist_statement)

    # ---- v0.3 causal graph ----------------------------------------------------
    p = sub.add_parser("link-cause")
    p.add_argument("--from", required=True, dest="from")
    p.add_argument("--to", required=True)
    p.add_argument("--relation", choices=sorted(RELATIONS), required=True)
    p.add_argument("--epistemic-state", choices=sorted(EPISTEMIC_STATES), required=True)
    p.add_argument("--confidence", required=True)
    p.add_argument("--explanation", default="")
    p.add_argument("--provenance-ref", required=True,
                   help="pipe-separated resolvable refs")
    p.set_defaults(func=cmd_link_cause)

    p = sub.add_parser("refute-link")
    p.add_argument("--link-id", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--epistemic-state", choices=sorted(EPISTEMIC_STATES))
    p.add_argument("--confidence")
    p.add_argument("--provenance-ref", required=True)
    p.set_defaults(func=cmd_refute_link)

    p = sub.add_parser("trace-chain")
    p.add_argument("--from", required=True, dest="from")
    p.set_defaults(func=cmd_trace_chain)

    # ---- v0.3 criteria ---------------------------------------------------------
    p = sub.add_parser("upsert-criterion")
    p.add_argument("--criterion-id", required=True)
    p.add_argument("--statement", required=True)
    p.add_argument("--scope", required=True, help="pipe-separated scopes")
    p.add_argument("--exception", default="")
    p.add_argument("--strength", choices=sorted(STRENGTHS - {"contextual_active"}),
                   action=_StrengthProvided)
    p.add_argument("--epistemic-basis", choices=sorted(EPISTEMIC_BASES), required=True)
    p.add_argument("--evidence-ref", default="")
    p.add_argument("--counterexample-ref", default="")
    p.add_argument("--origin-reflection", default="")
    p.add_argument("--statement-excerpt", default="")
    p.add_argument("--source-confidence")
    p.add_argument("--model-confidence")
    p.add_argument("--generality-confidence")
    p.add_argument("--supersedes")
    p.add_argument("--notes", default="")
    p.set_defaults(func=cmd_upsert_criterion, strength_provided=False)

    p = sub.add_parser("amend-criterion")
    p.add_argument("--criterion-id", required=True)
    p.add_argument("--supersedes", required=True)
    p.add_argument("--statement", required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--exception", default="")
    p.add_argument("--strength", choices=sorted(STRENGTHS - {"contextual_active"}),
                   default="candidate")
    p.add_argument("--epistemic-basis", choices=sorted(EPISTEMIC_BASES), required=True)
    p.add_argument("--evidence-ref", default="")
    p.add_argument("--counterexample-ref", default="")
    p.add_argument("--origin-reflection", default="")
    p.add_argument("--statement-excerpt", default="")
    p.add_argument("--source-confidence")
    p.add_argument("--model-confidence")
    p.add_argument("--generality-confidence")
    p.add_argument("--notes", default="")
    p.set_defaults(func=cmd_amend_criterion)

    p = sub.add_parser("activate-criterion")
    p.add_argument("--criterion-id", required=True)
    p.add_argument("--by", choices=["alberto", "agent", "system"], required=True)
    p.add_argument("--statement-excerpt", default="")
    p.add_argument("--new-criterion-id")
    p.set_defaults(func=cmd_activate_criterion)

    p = sub.add_parser("evaluate-criterion")
    p.add_argument("--criterion-id", required=True)
    p.set_defaults(func=cmd_evaluate_criterion)

    p = sub.add_parser("current-criterion")
    p.add_argument("--criterion-id", required=True)
    p.set_defaults(func=cmd_current_criterion)

    # ---- v0.3 clarifications ----------------------------------------------------
    p = sub.add_parser("answer-clarification")
    p.add_argument("--clarification-id", required=True)
    p.add_argument("--answer", required=True)
    p.add_argument("--answer-provenance", choices=sorted(SOURCE_TYPES),
                   default="alberto_statement")
    p.add_argument("--verbatim", default="")
    p.add_argument("--source-ref", default=None)
    p.set_defaults(func=cmd_answer_clarification)

    p = sub.add_parser("cancel-clarification")
    p.add_argument("--clarification-id", required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_cancel_clarification)

    p = sub.add_parser("obsolete-clarification")
    p.add_argument("--clarification-id", required=True)
    p.add_argument("--reason", required=True)
    p.set_defaults(func=cmd_obsolete_clarification)

    p = sub.add_parser("list-clarifications")
    p.add_argument("--status", choices=sorted(CLARIFICATION_STATUSES))
    p.set_defaults(func=cmd_list_clarifications)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    _LAST_APPEND_TARGET.clear()
    try:
        args.func(args)
    except NeedsClarification as nc:
        # zero-partial-write rule: if the rejected command already appended rows to
        # its own ledger before discovering a gap, undo is impossible by design —
        # commands are therefore written so that ALL validation precedes ANY append.
        # The queue row is persisted only when nothing was written for this command.
        if _LAST_APPEND_TARGET and _LAST_APPEND_TARGET[-1] != CLARIFICATIONS:
            nc.payload["warning"] = ("comando ha gia' scritto righe prima del blocco; "
                                     "verificare lo stato del ledger")
        nc.emit()
        raise SystemExit(EXIT_NEEDS_CLARIFICATION)


if __name__ == "__main__":
    main()
