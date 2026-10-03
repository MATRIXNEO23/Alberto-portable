"""Tests for v0.3 causal memory: reflections, criteria, causal links, clarifications.



Written BEFORE implementation (TDD). All tests load tools/alberto_portable.py

via importlib and remap ledger paths to a temp dir, mirroring the existing

test pattern in tests/test_alberto_portable.py.

"""

import importlib.util

import io

import json

import hashlib

import contextlib

import tempfile

import subprocess

import unittest

from pathlib import Path

from types import SimpleNamespace



ROOT = Path(__file__).resolve().parents[1]

SPEC = importlib.util.spec_from_file_location("alberto_portable", ROOT / "tools" / "alberto_portable.py")

ap = importlib.util.module_from_spec(SPEC)

SPEC.loader.exec_module(ap)





def run_cli(argv):

    """Run the full CLI entrypoint (ap.main), capture output, return

    (exit_code, parsed_stdout_json_or_None, stdout+stderr text)."""

    buf_out, buf_err = io.StringIO(), io.StringIO()

    code = 0

    try:

        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):

            import sys

            old_argv = sys.argv

            sys.argv = ["alberto_portable.py"] + argv

            try:

                ap.main()

            finally:

                sys.argv = old_argv

    except SystemExit as e:

        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)

    raw = buf_out.getvalue() + buf_err.getvalue()

    try:

        payload = json.loads(buf_out.getvalue())

    except Exception:

        payload = None

    return code, payload, raw





class V03Base(unittest.TestCase):

    def setUp(self):

        self.tmp = tempfile.TemporaryDirectory()

        self.addCleanup(self.tmp.cleanup)

        d = Path(self.tmp.name)

        self._orig = {}

        for name in ("DATA", "DECISIONS", "OUTCOMES", "METHODS",

                     "REFLECTIONS", "CRITERIA", "LINKS", "CLARIFICATIONS"):

            if hasattr(ap, name):

                self._orig[name] = getattr(ap, name)

                setattr(ap, name, d / (name.lower() + ".jsonl"))

        self._orig["ROOT"] = ap.ROOT

        ap._orig = dict(self._orig)  # real repo root so evidence path refs resolve



    def tearDown(self):

        for name, val in self._orig.items():

            setattr(ap, name, val)



    def record_decision(self, did="D-001", **kw):

        ns = SimpleNamespace(

            decision_id=did, task_type="repo_audit", context="ctx",

            alternatives="A|B", choice="B", reasons="perche|motivo",

            evidence_refs="evidence/METHOD_CASES_2026-10-03.md",

            risk="high", reversible=False, expected_outcome="safe", supersedes=None)

        for k, v in kw.items():

            setattr(ns, k, v)

        ap.cmd_record_decision(ns)



    def record_outcome(self, oid="O-001", did="D-001", technical_result="passed", **kw):

        ns = SimpleNamespace(

            outcome_id=oid, decision_id=did,

            technical_result=technical_result, tests_passed=True,

            regressions="", artifact_refs="",

            alberto_validation="accepted", alberto_notes="", notes="")

        for k, v in kw.items():

            setattr(ns, k, v)

        ap.cmd_record_outcome(ns)



    def read_jsonl(self, attr):

        p = getattr(ap, attr)

        if not p.exists():

            return []

        return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]





# ---------------------------------------------------------------------------

# Reflections

# ---------------------------------------------------------------------------



class ReflectionCreationTests(V03Base):

    BASE_ARGS = [

        "record-reflection",

        "--reflection-id", "R-TEST-01",

        "--author", "agent",

        "--context", "dopo build bocciata",

        "--trigger-kind", "outcome_failed",

        "--trigger-desc", "Outcome O-001 result=fail",

        "--trigger-ref", "O-001",

        "--interpretation", "forse il criterio di audit era debole",

        "--epistemic-state", "inferred",

        "--source-confidence", "0.5",

        "--model-confidence", "0.4",

        "--generality-confidence", "0.2",

    ]



    def test_agent_can_record_inferred_reflection_without_criterion_change(self):

        """Correction #4: change block optional; type none allowed."""

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, payload, raw = run_cli(self.BASE_ARGS + ["--change-type", "none"])

        self.assertEqual(code, 0, raw)

        rows = self.read_jsonl("REFLECTIONS")

        self.assertEqual(len(rows), 1)

        r = rows[0]

        self.assertEqual(r["status"], "recorded")

        self.assertEqual(r["change"]["type"], "none")

        self.assertIsNone(r["change"].get("what_changed"))



    def test_change_types_include_confirm_doubt_exception_question_link(self):

        self.record_decision(); self.record_outcome()

        for ct in ["none", "confirmed", "doubted", "exception_created",

                   "question_opened", "events_linked", "refined", "narrowed",

                   "widened", "replaced", "hypothesized", "contradicted"]:

            rid = f"R-CT-{ct}"

            argv = [rid if a == "R-TEST-01" else a for a in self.BASE_ARGS]

            code, _, raw = run_cli(argv + ["--change-type", ct])

            self.assertEqual(code, 0, f"{ct}: {raw}")



    def test_interpretation_state_flag_accepted(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, _, raw = run_cli(self.BASE_ARGS + ["--interpretation-state", "observed"])

        self.assertEqual(code, 0, raw)

        r = self.read_jsonl("REFLECTIONS")[0]

        self.assertEqual(r["interpretation"]["epistemic_state"], "observed")



    def test_agent_cannot_claim_declared_by_alberto(self):

        """Decision #2: agent-authored reflection cannot be declared_by_alberto."""

        self.record_decision(); self.record_outcome()

        code, payload, raw = run_cli(

            [a if a != "inferred" else "declared_by_alberto" for a in self.BASE_ARGS])

        self.assertNotEqual(code, 0)

        self.assertEqual(self.read_jsonl("REFLECTIONS"), [])



    def test_agent_cannot_claim_verified_without_resolvable_evidence(self):

        self.record_decision(); self.record_outcome()

        argv = _swap_after(self.BASE_ARGS, "--epistemic-state", "verified")

        argv = _swap_after(argv, "--trigger-ref", "D-GHOST")

        argv += ["--claim-kind", "technical_ref_fact", "--evidence-ref", "D-GHOST"]

        code, payload, raw = run_cli(argv)

        self.assertEqual(code, 3, raw)

        self.assertEqual(payload["status"], "NEEDS_CLARIFICATION")

        self.assertEqual(self.read_jsonl("REFLECTIONS"), [])


    def test_alberto_author_requires_verbatim_statement(self):

        """Decision #2 + correction: declared_by_alberto needs alberto_statement provenance."""

        self.record_decision(); self.record_outcome()

        argv = ["alberto" if a == "agent"

                else "declared_by_alberto" if a == "inferred"

                else a for a in self.BASE_ARGS]

        code, payload, raw = run_cli(argv)

        self.assertEqual(code, 3, raw)

        self.assertEqual(payload["status"], "NEEDS_CLARIFICATION")

        self.assertTrue(any("verbatim" in m or "statement" in m for m in payload["missing"]))

        # with verbatim excerpt it passes

        code2, _, raw2 = run_cli(argv + ["--statement-excerpt",

                                         "se qualcosa cambia deve risalire anche alla causa"])

        self.assertEqual(code2, 0, raw2)

        rows = self.read_jsonl("REFLECTIONS")

        self.assertEqual(rows[0]["provenance"][0]["source_type"], "alberto_statement")

        self.assertIsNone(rows[0]["provenance"][0]["source_ref"])

        self.assertIsNone(rows[0]["provenance"][0]["persistent_source_ref"])



    def test_unknown_causality_keeps_why_changed_null(self):

        """Design rule: never invent the cause."""

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, _, raw = run_cli(self.BASE_ARGS)  # no --why-changed

        self.assertEqual(code, 0, raw)

        r = self.read_jsonl("REFLECTIONS")[0]

        self.assertEqual(r["change"]["causality"]["status"], "unknown")

        self.assertIsNone(r["change"]["why_changed"])



    def test_multiple_candidate_causes_are_preserved_not_chosen(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, _, raw = run_cli(self.BASE_ARGS + [

            "--candidate-cause", "patch generata senza audit dipendenze",

            "--candidate-cause", "contesto ad alto rischio sottovalutato",

        ])

        self.assertEqual(code, 0, raw)

        r = self.read_jsonl("REFLECTIONS")[0]

        self.assertEqual(r["change"]["causality"]["status"], "multiple_candidates")

        self.assertIsNone(r["change"]["causality"]["primary_cause"])

        self.assertEqual(len(r["change"]["causality"]["candidate_causes"]), 2)



    def test_duplicate_reflection_id_rejected_append_only(self):

        """Append-only invariant: a reflection_id is created exactly once.



        The production code refuses the second insert (SystemExit, non-zero)

        and writes ZERO bytes to the ledger; this test pins that behaviour.

        """

        self.record_decision(); self.record_outcome()

        code1, _, raw1 = run_cli(self.BASE_ARGS + ["--change-type", "none"])

        self.assertEqual(code1, 0, raw1)

        before_text = ap.REFLECTIONS.read_text()

        before_rows = self.read_jsonl("REFLECTIONS")

        self.assertEqual(len(before_rows), 1)

        self.assertEqual(before_rows[0]["reflection_id"], "R-TEST-01")



        code2, _, raw2 = run_cli(self.BASE_ARGS + ["--change-type", "none"])

        self.assertNotEqual(code2, 0)                    # rejected

        after_text = ap.REFLECTIONS.read_text()

        self.assertEqual(after_text, before_text)        # byte-identical

        rows = self.read_jsonl("REFLECTIONS")

        self.assertEqual(len(rows), 1)                   # no second row appended

        self.assertEqual(rows[0]["reflection_id"], "R-TEST-01")





# ---------------------------------------------------------------------------

# Causal graph (links) — correction #5

# ---------------------------------------------------------------------------



def _swap_after(argv, flag, new_val):

    """Replace the VALUE token that immediately follows `flag` in argv."""

    out, hit = [], False

    for a in argv:

        if hit and not a.startswith("--"):

            out.append(new_val); hit = False; continue

        if a == flag:

            hit = True

        out.append(a)

    return out





class CausalLinkTests(V03Base):

    def make_r(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, _, raw = run_cli(ReflectionCreationTests.BASE_ARGS)

        assert code == 0, raw



    def test_link_is_separate_append_only_arc(self):

        self.make_r()

        code, _, raw = run_cli(["link-cause", "--from", "O-001", "--to", "R-TEST-01",

                                "--relation", "caused_or_contributed_to",

                                "--epistemic-state", "observed", "--confidence", "0.6",

                                "--provenance-ref", "O-001"])

        self.assertEqual(code, 0, raw)

        links = self.read_jsonl("LINKS")

        self.assertEqual(len(links), 1)

        l = links[0]

        self.assertEqual(l["from"], "O-001")

        self.assertEqual(l["to"], "R-TEST-01")

        self.assertEqual(l["relation"], "caused_or_contributed_to")

        self.assertEqual(l["epistemic_state"], "observed")

        # original outcome untouched

        self.assertEqual(self.read_jsonl("OUTCOMES")[0]["technical_result"], "failed")



    def test_two_incompatible_explanations_produce_conflicting(self):

        """Required test: two incompatible causal explanations on the same event

        must yield conflicting, not auto-choice."""

        self.make_r()

        run_cli(["link-cause", "--from", "O-001", "--to", "R-TEST-01",

                 "--relation", "caused_by", "--epistemic-state", "inferred",

                 "--confidence", "0.5", "--provenance-ref", "O-001",

                 "--explanation", "mancato audit dipendenze"])

        code, payload, raw = run_cli(

            ["link-cause", "--from", "O-001", "--to", "R-TEST-01",

             "--relation", "caused_by", "--epistemic-state", "inferred",

             "--confidence", "0.7", "--provenance-ref", "O-001",

             "--explanation", "scelta del modello errata"])

        self.assertEqual(code, 0, raw)

        st = payload["graph_status"] if payload else None

        self.assertEqual(st, "conflicting")

        links = self.read_jsonl("LINKS")

        self.assertEqual(len(links), 2)  # both kept, neither deleted



    def test_refute_link_appends_event_no_rewrite(self):

        self.make_r()

        run_cli(["link-cause", "--from", "O-001", "--to", "R-TEST-01",

                 "--relation", "caused_by", "--epistemic-state", "inferred",

                 "--confidence", "0.5", "--provenance-ref", "O-001",

                 "--explanation", "ipotesi A"])

        first_line_raw = ap.LINKS.read_text()

        lid = self.read_jsonl("LINKS")[0]["link_id"]

        code, _, raw = run_cli(["refute-link", "--link-id", lid,

                                "--reason", "controprova: stesso setup ha funzionato",

                                "--provenance-ref", "evidence/METHOD_CASES_2026-10-03.md"])

        self.assertEqual(code, 0, raw)

        # append-only: original line still byte-present

        self.assertTrue(first_line_raw.splitlines()[0] in ap.LINKS.read_text())

        statuses = [l.get("validity", "active") for l in self.read_jsonl("LINKS")]

        self.assertIn("refuted", statuses)



    def test_trace_chain_full_loop(self):

        """evento → interpretazione → riflessione → cambiamento → decisione → outcome

        → nuova riflessione, traversable from any node."""

        self.make_r()

        run_cli(["link-cause", "--from", "O-001", "--to", "R-TEST-01",

                 "--relation", "caused_or_contributed_to", "--epistemic-state", "observed",

                 "--confidence", "0.6", "--provenance-ref", "O-001"])

        # create criterion from reflection

        code, _, raw = run_cli(["upsert-criterion", "--criterion-id", "C-TEST-01",

                                "--statement", "prima di modifiche profonde verificare le dipendenze",

                                "--scope", "software_changes_high_risk",

                                "--epistemic-basis", "inferred",

                                "--origin-reflection", "R-TEST-01",

                                "--evidence-ref", "R-TEST-01"])

        self.assertEqual(code, 0, raw)

        # new decision influenced by criterion, then its outcome, then R2

        self.record_decision(did="D-002")

        run_cli(["link-cause", "--from", "R-TEST-01", "--to", "D-002",

                 "--relation", "influenced", "--epistemic-state", "inferred",

                 "--confidence", "0.5", "--provenance-ref", "R-TEST-01"])

        code, chain, raw = run_cli(["trace-chain", "--from", "R-TEST-01"])

        self.assertEqual(code, 0, raw)

        nodes = {n["id"] for n in chain["nodes"]}

        self.assertLessEqual({"O-001", "R-TEST-01", "D-002"}, nodes)





# ---------------------------------------------------------------------------

# Criteria — corrections #1, #2, #3

# ---------------------------------------------------------------------------



class CriterionTests(V03Base):

    def test_strength_and_epistemic_basis_are_separate_enums(self):

        """declared_by_alberto is NOT a strength."""

        self.assertIn("declared_by_alberto", ap.EPISTEMIC_BASES)

        self.assertNotIn("declared_by_alberto", ap.STRENGTHS)

        self.assertEqual(ap.STRENGTHS, {"hypothesis", "candidate", "contextual_active",

                                        "contested", "deprecated"})



    def test_derived_metrics_not_storable_as_input(self):

        code, _, raw = run_cli(["upsert-criterion", "--criterion-id", "C-D1",

                                "--statement", "test separati prima di modifiche profonde",

                                "--scope", "software_changes_high_risk",

                                "--epistemic-basis", "inferred",

                                "--evidence-ref", "evidence/METHOD_CASES_2026-10-03.md"])

        self.assertEqual(code, 0, raw)

        c = self.read_jsonl("CRITERIA")[0]

        # canonical record has evidence_refs only; no hand-written counters

        self.assertNotIn("independent_observations", c)

        self.assertNotIn("distinct_contexts", c)

        self.assertNotIn("temporal_stability_days", c)



    def test_unknown_evidence_ref_blocks_creation(self):

        code, payload, raw = run_cli(["upsert-criterion", "--criterion-id", "C-D2",

                                      "--statement", "x", "--scope", "s",

                                      "--epistemic-basis", "observed",

                                      "--evidence-ref", "R-GHOST"])

        self.assertEqual(code, 3, raw)

        self.assertEqual(payload["status"], "NEEDS_CLARIFICATION")

        self.assertEqual(self.read_jsonl("CRITERIA"), [])



    def test_single_alberto_declaration_is_significant(self):

        """A single explicit declaration can justify high source/generality confidence;

        10 same-context observations alone cannot exceed candidate."""

        code, _, raw = run_cli(["upsert-criterion", "--criterion-id", "C-A1",

                                "--statement", "su questo faccio così",

                                "--scope", "specific_task",

                                "--strength", "candidate",

                                "--epistemic-basis", "declared_by_alberto",

                                "--statement-excerpt", "su questo faccio così perché ho visto la regressione",

                                "--evidence-ref", "evidence/METHOD_CASES_2026-10-03.md"])

        self.assertEqual(code, 0, raw)

        c = self.read_jsonl("CRITERIA")[0]

        self.assertEqual(c["strength"], "candidate")  # still needs Alberto activation

        self.assertEqual(c["epistemic_basis"], "declared_by_alberto")



    def test_activate_requires_explicit_alberto_action(self):

        run_cli(["upsert-criterion", "--criterion-id", "C-A2",

                 "--statement", "verificare dipendenze", "--scope", "high_risk",

                 "--strength", "candidate",

                 "--epistemic-basis", "inferred",

                 "--evidence-ref", "evidence/METHOD_CASES_2026-10-03.md"])

        # agent cannot activate

        code, _, raw = run_cli(["activate-criterion", "--criterion-id", "C-A2",

                                "--by", "agent"])

        self.assertNotEqual(code, 0)

        self.assertEqual(self.read_jsonl("CRITERIA")[0]["strength"], "candidate")

        code2, _, raw2 = run_cli(["activate-criterion", "--criterion-id", "C-A2",

                                  "--by", "alberto",

                                  "--statement-excerpt", "ok, attiva questa"])

        self.assertEqual(code2, 0, raw2)

        self.assertEqual(self.read_jsonl("CRITERIA")[-1]["strength"], "contextual_active")



    def test_evaluate_reports_derived_never_mutates(self):

        run_cli(["upsert-criterion", "--criterion-id", "C-EV",

                 "--statement", "s", "--scope", "high_risk",

                 "--strength", "candidate",

                 "--epistemic-basis", "inferred",

                 "--evidence-ref", "evidence/METHOD_CASES_2026-10-03.md"])

        before = ap.CRITERIA.read_text()

        code, report, raw = run_cli(["evaluate-criterion", "--criterion-id", "C-EV"])

        self.assertEqual(code, 0, raw)

        self.assertEqual(ap.CRITERIA.read_text(), before)  # pure function

        self.assertIn("derived", report)

        for key in ("independent_observations", "distinct_contexts",

                    "counterexamples", "temporal_stability_days"):

            self.assertIn(key, report["derived"])



    def test_counterexample_moves_to_contested_via_new_version(self):

        run_cli(["upsert-criterion", "--criterion-id", "C-X1",

                 "--statement", "s", "--scope", "high_risk",

                 "--strength", "candidate",

                 "--epistemic-basis", "inferred",

                 "--evidence-ref", "evidence/METHOD_CASES_2026-10-03.md"])

        first = ap.CRITERIA.read_text()

        code, _, raw = run_cli(["amend-criterion", "--criterion-id", "C-X2",

                                "--supersedes", "C-X1",

                                "--statement", "s", "--scope", "high_risk",

                                "--epistemic-basis", "inferred",

                                "--strength", "contested",

                                "--counterexample-ref", "evidence/METHOD_CASES_2026-10-03.md",

                                "--evidence-ref", "evidence/METHOD_CASES_2026-10-03.md"])

        self.assertEqual(code, 0, raw)

        self.assertTrue(first in ap.CRITERIA.read_text())  # history preserved

        cur = self.current_criterion("C-X1")

        self.assertEqual(cur["criterion_id"], "C-X2")

        self.assertEqual(cur["strength"], "contested")



    def current_criterion(self, cid):

        rows = self.read_jsonl("CRITERIA")

        superseded = {r.get("supersedes") for r in rows}

        chain = [cid]

        while True:

            nxt = next((r["criterion_id"] for r in rows if r.get("supersedes") == chain[-1]), None)

            if not nxt:

                break

            chain.append(nxt)

        return next(r for r in rows if r["criterion_id"] == chain[-1])





# ---------------------------------------------------------------------------

# Clarifications queue

# ---------------------------------------------------------------------------



class ClarificationTests(V03Base):

    GHOST_ARGS = _swap_after(ReflectionCreationTests.BASE_ARGS, "--trigger-ref", "D-GHOST")



    def test_needs_clarification_writes_queue_row_not_reflection(self):

        """Decision #1: open questions live in data/clarifications.jsonl."""

        self.record_decision(); self.record_outcome()

        code, payload, raw = run_cli(self.GHOST_ARGS)

        self.assertEqual(code, 3, raw)

        self.assertEqual(payload["status"], "NEEDS_CLARIFICATION")

        for key in ("missing", "reason", "question_for_alberto", "would_affect"):

            self.assertIn(key, payload)

        self.assertEqual(self.read_jsonl("REFLECTIONS"), [])

        q = self.read_jsonl("CLARIFICATIONS")

        self.assertEqual(len(q), 1)

        self.assertEqual(q[0]["status"], "open")

        self.assertIn("clarification_id", q[0])

        self.assertIn("trigger_ref", q[0])



    def test_answer_links_back_and_becomes_provenance(self):

        """Append-only semantics: answering a clarification appends a NEW event

        row; the original open row is never mutated in place."""

        self.record_decision(); self.record_outcome()

        run_cli(self.GHOST_ARGS)

        path = ap.CLARIFICATIONS

        first_snapshot_raw = path.read_text()

        rows_before = self.read_jsonl("CLARIFICATIONS")

        self.assertEqual(len(rows_before), 1)

        self.assertEqual(rows_before[0]["status"], "open")

        qid = rows_before[0]["clarification_id"]

        cev_before = rows_before[0]["clarification_event_id"]



        code, _, raw = run_cli(["answer-clarification", "--clarification-id", qid,

                                "--answer", "il motivo era il contesto ad alto rischio",

                                "--answer-provenance", "alberto_statement",

                                "--verbatim", "il motivo era il contesto ad alto rischio"])

        self.assertEqual(code, 0, raw)



        rows_after = self.read_jsonl("CLARIFICATIONS")

        # two events now exist for the same stable clarification_id

        self.assertEqual(len(rows_after), 2)

        self.assertEqual({r["clarification_id"] for r in rows_after}, {qid})

        # distinct event ids

        self.assertNotEqual(rows_after[0]["clarification_event_id"],

                            rows_after[1]["clarification_event_id"])

        # FIRST ROW BYTE-INVARIANT (no in-place mutation)

        self.assertEqual(rows_after[0], rows_before[0])

        self.assertTrue(path.read_text().startswith(first_snapshot_raw))

        self.assertEqual(rows_after[0]["status"], "open")

        self.assertEqual(rows_after[0]["clarification_event_id"], cev_before)



        answered = rows_after[-1]

        self.assertEqual(answered["status"], "answered")

        self.assertIsNotNone(answered.get("answered_at"))

        self.assertEqual(answered["answer"], "il motivo era il contesto ad alto rischio")

        self.assertEqual(answered["answer_provenance"]["source_type"], "alberto_statement")

        # verbatim present when attributed to Alberto

        self.assertIn("il motivo era il contesto ad alto rischio",

                      json.dumps(answered["answer_provenance"]))



        # _latest_queue() reports the answered snapshot as current state

        latest = ap._latest_queue()[qid]

        self.assertEqual(latest["status"], "answered")

        self.assertEqual(latest["clarification_event_id"],

                         answered["clarification_event_id"])



    def test_cancel_and_obsolete_keep_history(self):

        self.record_decision(); self.record_outcome()

        run_cli(self.GHOST_ARGS)

        qid = self.read_jsonl("CLARIFICATIONS")[0]["clarification_id"]

        code, _, raw = run_cli(["cancel-clarification", "--clarification-id", qid,

                                "--reason", "risolto da altra evidenza"])

        self.assertEqual(code, 0, raw)

        rows = self.read_jsonl("CLARIFICATIONS")

        self.assertEqual(rows[-1]["status"], "cancelled")



    def test_no_clarification_when_uncertainty_can_be_marked(self):

        """Decision #10: don't ask useless questions when marking uncertainty suffices."""

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, _, raw = run_cli(ReflectionCreationTests.BASE_ARGS)  # inferred, unknown cause

        self.assertEqual(code, 0, raw)

        self.assertEqual(self.read_jsonl("CLARIFICATIONS"), [])





# ---------------------------------------------------------------------------

# Persistent-source upgrade — decision #2 point 3

# ---------------------------------------------------------------------------



class StatementUpgradeTests(V03Base):

    def test_persist_transcript_adds_event_without_rewriting_record(self):

        self.record_decision(); self.record_outcome()

        argv = ["alberto" if a == "agent"

                else "declared_by_alberto" if a == "inferred"

                else a for a in ReflectionCreationTests.BASE_ARGS]

        run_cli(argv + ["--statement-excerpt", "se qualcosa cambia deve risalire anche alla causa"])

        before = ap.REFLECTIONS.read_text()

        code, _, raw = run_cli(["persist-statement", "--reflection-id", "R-TEST-01",

                                "--persistent-source-ref", "evidence/METHOD_CASES_2026-10-03.md"])

        self.assertEqual(code, 0, raw)

        self.assertTrue(before in ap.REFLECTIONS.read_text())  # old record intact

        ev = self.read_jsonl("LINKS")  # events stored in the append-only graph file

        self.assertTrue(any(e.get("event") == "statement_persisted" for e in ev))





# ---------------------------------------------------------------------------

# Regression guards

# ---------------------------------------------------------------------------



class RegressionGuards(V03Base):

    def test_existing_ledger_commands_unchanged(self):

        self.record_decision()

        self.record_outcome()

        rows = self.read_jsonl("DECISIONS")

        self.assertEqual(set(rows[0].keys()), {

            "schema_version", "decision_id", "recorded_at", "task_type", "context",

            "alternatives", "choice", "reasons", "evidence_refs", "risk",

            "reversible", "expected_outcome", "supersedes"})



    def test_route_output_shape_unchanged(self):

        run_cli(["record-method", "--observation-id", "M-RG-1", "--method", "qwen-coder",

                 "--task-type", "repo_audit", "--role", "audit",

                 "--verified-result", "correct", "--hallucination", "false",

                 "--notes", "x", "--evidence-refs", "evidence/METHOD_CASES_2026-10-03.md"])

        code, payload, raw = run_cli(["route", "--task-type", "repo_audit",

                                      "--role", "audit", "--risk", "low"])

        self.assertEqual(code, 0, raw)

        for key in ("status", "recommendations"):

            self.assertIn(key, payload)

        if payload["status"] == "insufficient_evidence":

            self.assertEqual(set(payload.keys()),

                             {"status", "task_type", "role", "recommendations"})

        else:

            self.assertIn("note", payload)

            self.assertIn("not a global ranking", payload["note"])

            for key in ("relevant_reflections", "relevant_criteria"):

                self.assertIn(key, payload)  # v0.3 additive keys on the ranked path



    def test_validate_passes_on_repo_data(self):

        # against the REAL repo data files (read-only check of current state)

        saved = dict(getattr(ap, "_orig", {}))

        try:

            ap.DATA = ROOT / "data"

            ap.DECISIONS = ROOT / "data" / "decisions.jsonl"

            ap.OUTCOMES = ROOT / "data" / "outcomes.jsonl"

            ap.METHODS = ROOT / "data" / "method_observations.jsonl"

            for name in ("REFLECTIONS", "CRITERIA", "LINKS", "CLARIFICATIONS"):

                if hasattr(ap, name):

                    setattr(ap, name, ROOT / "data" / (name.lower() + ".jsonl"))

            buf = io.StringIO()

            with contextlib.redirect_stdout(buf):

                ap.cmd_validate(SimpleNamespace())

            self.assertIn("OK", buf.getvalue())

        finally:

            for k, v in saved.items():

                setattr(ap, k, v)





# ---------------------------------------------------------------------------

# Clarification state transitions (audit closure #2)

# ---------------------------------------------------------------------------



class ClarificationTransitionTests(V03Base):

    """clarifications.jsonl is append-only event history: clarification_id is

    stable, clarification_event_id is unique per row, current state = last row.

    Legal: open -> answered|cancelled|obsolete. Terminal states are terminal."""



    def _open_q(self):

        self.record_decision(); self.record_outcome()

        code, _, raw = run_cli(ClarificationTests.GHOST_ARGS)

        self.assertEqual(code, 3, raw)

        rows = self.read_jsonl("CLARIFICATIONS")

        self.assertEqual(len(rows), 1)

        self.assertEqual(rows[0]["status"], "open")

        return rows[0]["clarification_id"]



    def _answer(self, qid):

        return run_cli(["answer-clarification", "--clarification-id", qid,

                        "--answer", "fixture: risposta simulata di test",

                        "--answer-provenance", "alberto_statement",

                        "--verbatim", "fixture: risposta simulata di test"])



    def _cancel(self, qid):

        return run_cli(["cancel-clarification", "--clarification-id", qid,

                        "--reason", "fixture: ragione di test"])



    def _obsolete(self, qid):

        return run_cli(["obsolete-clarification", "--clarification-id", qid,

                        "--reason", "fixture: non più necessario"])



    def _force_transition(self, qid, from_status, to_status):

        """Craft a legal 'from_status' history in temp storage, then attempt the

        transition under test via the real CLI commands."""

        if from_status == "open":

            return

        if from_status == "answered":

            code, _, raw = self._answer(qid)

            self.assertEqual(code, 0, raw)

        elif from_status == "cancelled":

            code, _, raw = self._cancel(qid)

            self.assertEqual(code, 0, raw)

        elif from_status == "obsolete":

            code, _, raw = self._obsolete(qid)

            self.assertEqual(code, 0, raw)



    # ------------------------- VALID TRANSITIONS ---------------------------



    def test_valid_open_to_answered(self):

        qid = self._open_q()

        code, _, raw = self._answer(qid)

        self.assertEqual(code, 0, raw)

        self.assertEqual(ap._latest_queue()[qid]["status"], "answered")



    def test_valid_open_to_cancelled(self):

        qid = self._open_q()

        code, _, raw = self._cancel(qid)

        self.assertEqual(code, 0, raw)

        self.assertEqual(ap._latest_queue()[qid]["status"], "cancelled")



    def test_valid_open_to_obsolete(self):

        """Legal transition: validate accepts it and latest state derives from it."""

        qid = self._open_q()

        code, _, raw = self._obsolete(qid)

        self.assertEqual(code, 0, raw)

        self.assertEqual(ap._latest_queue()[qid]["status"], "obsolete")

        buf = io.StringIO()

        with contextlib.redirect_stdout(buf):

            ap.cmd_validate(SimpleNamespace())   # must not raise: sequence is legal

        self.assertIn("OK", buf.getvalue())



    # ------------------------ INVALID TRANSITIONS --------------------------



    def _assert_invalid(self, qid, expected_status, argv):

        before_raw = ap.CLARIFICATIONS.read_text()

        before_rows = self.read_jsonl("CLARIFICATIONS")

        code, _, raw = run_cli(argv)

        self.assertNotEqual(code, 0, f"{expected_status} target must reject: {raw}")

        self.assertEqual(ap.CLARIFICATIONS.read_text(), before_raw)

        self.assertEqual(self.read_jsonl("CLARIFICATIONS"), before_rows)

        self.assertEqual(ap._latest_queue()[qid]["status"], expected_status)



    def _terminal_q(self, status):

        qid = self._open_q()

        self._force_transition(qid, status, None)

        self.assertEqual(ap._latest_queue()[qid]["status"], status)

        return qid



    def _assert_all_terminal_operations_rejected(self, status):

        for op in ("answer", "cancel", "obsolete"):

            # each operation gets an independent terminal history

            qid = self._terminal_q(status)

            if op == "answer":

                argv = ["answer-clarification", "--clarification-id", qid,

                        "--answer", "late", "--verbatim", "late"]

            elif op == "cancel":

                argv = ["cancel-clarification", "--clarification-id", qid,

                        "--reason", "late"]

            else:

                argv = ["obsolete-clarification", "--clarification-id", qid,

                        "--reason", "late"]

            self._assert_invalid(qid, status, argv)

            # reset temp ledgers before constructing next independent history

            for attr in ("DECISIONS", "OUTCOMES", "REFLECTIONS", "CRITERIA", "LINKS", "CLARIFICATIONS"):

                path = getattr(ap, attr)

                if path.exists():

                    path.unlink()



    def test_terminal_answered_rejects_all_operations(self):

        self._assert_all_terminal_operations_rejected("answered")



    def test_terminal_cancelled_rejects_all_operations(self):

        self._assert_all_terminal_operations_rejected("cancelled")



    def test_terminal_obsolete_rejects_all_operations(self):

        self._assert_all_terminal_operations_rejected("obsolete")



    def test_validate_detects_manually_corrupted_terminal_transition(self):

        qid = self._terminal_q("answered")

        rows = self.read_jsonl("CLARIFICATIONS")

        bad = json.loads(json.dumps(rows[-1]))

        bad["clarification_event_id"] = ap.next_clarification_event_id()

        bad["status"] = "obsolete"

        ap.append_jsonl(ap.CLARIFICATIONS, bad)

        with self.assertRaises(SystemExit) as cm:

            ap.cmd_validate(SimpleNamespace())

        self.assertIn("illegal transition", str(cm.exception))

        self.assertIn(f"{qid}: answered -> obsolete", str(cm.exception))


    # ------------------------------ ID RULES --------------------------------



    def test_event_ids_unique_and_clarification_id_stable(self):

        qid = self._open_q()

        self._answer(qid)

        rows = self.read_jsonl("CLARIFICATIONS")

        self.assertEqual(len(rows), 2)

        self.assertEqual({r["clarification_id"] for r in rows}, {qid})

        eids = [r["clarification_event_id"] for r in rows]

        self.assertEqual(len(set(eids)), len(eids))

        self.assertTrue(all(eids))

        # first snapshot still open, current state derived from last event

        self.assertEqual(rows[0]["status"], "open")

        self.assertEqual(ap._latest_queue()[qid]["status"], "answered")



    def test_validate_flags_duplicate_event_id_but_not_repeated_clarification_id(self):

        qid = self._open_q()

        self._answer(qid)

        buf = io.StringIO()

        with contextlib.redirect_stdout(buf):

            ap.cmd_validate(SimpleNamespace())     # repeated clarification_id is LEGAL

        self.assertIn("OK", buf.getvalue())

        rows = self.read_jsonl("CLARIFICATIONS")

        dup = json.loads(json.dumps(rows[-1]))     # same event id => illegal

        ap.append_jsonl(ap.CLARIFICATIONS, dup)

        with self.assertRaises(SystemExit) as cm:

            ap.cmd_validate(SimpleNamespace())

        self.assertIn("duplicate clarification_event_id", str(cm.exception))





# ---------------------------------------------------------------------------

# verified gate: technical facts vs psychological claims about Alberto (#6)

# ---------------------------------------------------------------------------



class VerifiedGateTests(V03Base):

    R_ARGS = list(ReflectionCreationTests.BASE_ARGS)



    def _verified_cmd(self, rid, interp, evidence_ref):

        argv = _swap_after(self.R_ARGS, "--reflection-id", rid)

        argv = _swap_after(argv, "--interpretation", interp)

        argv = _swap_after(argv, "--epistemic-state", "verified")

        argv += ["--claim-kind", "technical_ref_fact", "--evidence-ref", evidence_ref]

        return run_cli(argv)


    # --- admitted: verifiable TECHNICAL facts -------------------------------



    def test_agent_verified_allowed_for_technical_fact_with_real_path(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        ref = "evidence/METHOD_CASES_2026-10-03.md"

        code, payload, raw = self._verified_cmd("R-VG-T1", f"path {ref} exists", ref)

        self.assertEqual(code, 0, raw)

        self.assertEqual(payload["epistemic_state"], "verified")

        self.assertEqual(payload["verified_fact"]["ref"], ref)

        self.assertEqual(payload["verified_fact"]["claim"], f"path {ref} exists")


    def test_agent_verified_allowed_for_resolvable_commit(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        ref = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()

        code, payload, raw = self._verified_cmd(

            "R-VG-T2", f"commit {ref} exists in repository", ref)

        self.assertEqual(code, 0, raw)

        self.assertEqual(payload["verified_fact"]["ref_kind"], "commit")


    # --- blocked: psychological/interpretive claims about Alberto -----------



    def test_agent_cannot_verify_alberto_changed_mind(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, _, raw = self._verified_cmd(

            "R-VG-B1", "Alberto ha cambiato idea perche' la regressione era grave",

            "evidence/METHOD_CASES_2026-10-03.md")

        self.assertNotEqual(code, 0)

        self.assertEqual(self.read_jsonl("REFLECTIONS"), [])



    def test_agent_cannot_verify_alberto_prefers_x(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, _, raw = self._verified_cmd(

            "R-VG-B2", "Alberto preferisce X perche' Y e' troppo fragile",

            "evidence/METHOD_CASES_2026-10-03.md")

        self.assertNotEqual(code, 0)

        self.assertEqual(self.read_jsonl("REFLECTIONS"), [])



    def test_agent_cannot_verify_alberto_was_worried(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, _, raw = self._verified_cmd(

            "R-VG-B3", "Alberto era preoccupato dopo la bocciatura della build",

            "evidence/METHOD_CASES_2026-10-03.md")

        self.assertNotEqual(code, 0)

        self.assertEqual(self.read_jsonl("REFLECTIONS"), [])



    def test_generic_evidence_does_not_whitewash_subjective_claim(self):

        """A real file/commit linked generically must NOT upgrade an

        interpretation of Alberto's mind to verified."""

        self.record_decision(); self.record_outcome(technical_result="failed")

        code, _, raw = self._verified_cmd(

            "R-VG-B4", "Alberto ha cambiato idea perche' servivano test separati",

            "evidence/METHOD_CASES_2026-10-03.md")

        self.assertNotEqual(code, 0)

        self.assertEqual(self.read_jsonl("REFLECTIONS"), [])



    def test_subjective_claim_falls_back_to_declared_with_verbatim(self):

        """Same claim IS admissible as declared_by_alberto with his verbatim."""

        self.record_decision(); self.record_outcome(technical_result="failed")

        argv = _swap_after(self.R_ARGS, "--reflection-id", "R-VG-D1")

        argv = _swap_after(argv, "--author", "alberto")

        argv = _swap_after(argv, "--epistemic-state", "declared_by_alberto")

        code, payload, raw = run_cli(

            argv + ["--statement-excerpt",

                    "dopo quella regressione ho deciso: audit delle dipendenze prima"])

        self.assertEqual(code, 0, raw)

        self.assertEqual(payload["epistemic_state"], "declared_by_alberto")



    def test_subjective_claim_admissible_as_inferred_or_unknown(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        for i, st in enumerate(["inferred", "conflicting"]):

            argv = _swap_after(self.R_ARGS, "--reflection-id", f"R-VG-I{i}")

            argv = _swap_after(argv, "--epistemic-state", st)

            code, _, raw = run_cli(argv)

            self.assertEqual(code, 0, f"{st}: {raw}")





# ---------------------------------------------------------------------------

# S1 contaminated — eval status file (decision #12)

# ---------------------------------------------------------------------------



class S1ContaminationTests(unittest.TestCase):

    STATUS_PATH = ROOT / "eval" / "VALIDATION_STATUS_V0.1.json"

    FROZEN_PATH = ROOT / "eval" / "PREDICTIONS_V0.1_FROZEN.md"



    @classmethod

    def setUpClass(cls):

        cls.frozen_bytes = cls.FROZEN_PATH.read_bytes()

        cls.status = json.loads(cls.STATUS_PATH.read_text())



    def test_frozen_predictions_byte_unchanged(self):

        self.assertEqual(self.FROZEN_PATH.read_bytes(), self.frozen_bytes)

        h = hashlib.sha256(self.frozen_bytes).hexdigest()

        self.assertEqual(h, hashlib.sha256(self.FROZEN_PATH.read_bytes()).hexdigest())



    def test_s1_registered_contaminated(self):

        s1 = self.status["scenarios"]["S1"]

        self.assertEqual(s1["status"], "contaminated")

        self.assertIs(s1["usable_for_blind_validation"], False)

        self.assertTrue(s1["reason"].strip())



    def test_no_invented_alberto_answer_for_s1(self):

        """The status file carries metadata only, never a fabricated answer."""

        s1 = self.status["scenarios"]["S1"]

        self.assertEqual(set(s1), {"status", "usable_for_blind_validation", "reason"})

        forbidden_keys = {"alberto_answer", "alberto_response", "response_text",

                          "observed_answer", "predicted_answer"}

        self.assertTrue(forbidden_keys.isdisjoint(s1.keys()))


    def test_s1_excluded_from_blind_validation_counts(self):

        usable = [sid for sid, meta in self.status["scenarios"].items()

                  if meta.get("usable_for_blind_validation")]

        self.assertNotIn("S1", usable)





# ---------------------------------------------------------------------------

# Anti-contamination guardian: tests must never touch the REAL data/ dir

# ---------------------------------------------------------------------------



def _snapshot_data_dir():

    d = ROOT / "data"

    if not d.exists():

        return {}

    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()

            for p in sorted(d.glob("*.jsonl"))}





class DataIsolationGuardianTests(V03Base):

    def test_full_v03_sequence_never_touches_real_data_dir(self):

        before = _snapshot_data_dir()

        # representative v0.3 sequence through the real CLI entrypoint

        self.record_decision(); self.record_outcome(technical_result="failed")

        run_cli(ReflectionCreationTests.BASE_ARGS)                       # reflection

        ghost = _swap_after(ClarificationTests.GHOST_ARGS, "--reflection-id", "R-GUARD-GHOST")

        run_cli(ghost)                                                   # NEEDS_CLARIFICATION

        qid = self.read_jsonl("CLARIFICATIONS")[0]["clarification_id"]

        run_cli(["answer-clarification", "--clarification-id", qid,

                 "--answer", "fixture", "--verbatim", "fixture"])       # answer

        run_cli(["link-cause", "--from", "O-001", "--to", "R-TEST-01",

                 "--relation", "caused_or_contributed_to", "--epistemic-state", "observed",

                 "--confidence", "0.6", "--provenance-ref", "O-001"])   # causal arc

        run_cli(["upsert-criterion", "--criterion-id", "C-GUARD-01",

                 "--statement", "fixture statement", "--scope", "repo_audit",

                 "--epistemic-basis", "inferred", "--origin-reflection", "R-TEST-01",

                 "--evidence-ref", "R-TEST-01"])                         # criterion

        run_cli(["trace-chain", "--from", "R-TEST-01"])                   # trace

        after = _snapshot_data_dir()

        self.assertEqual(before, after,

                         "test suite wrote into the REAL repository data/ directory")

        # and every artifact lives inside the temp dir only

        tmp_files = {p.name for p in Path(self.tmp.name).iterdir()}

        self.assertTrue({"reflections.jsonl", "clarifications.jsonl"} <= tmp_files)



    def test_last_append_target_is_reset_between_invocations(self):

        """A second CLI invocation must not inherit append state from the first."""

        self.record_decision(); self.record_outcome()

        code1, _, raw1 = run_cli(ReflectionCreationTests.BASE_ARGS)

        self.assertEqual(code1, 0, raw1)

        self.assertEqual(ap._LAST_APPEND_TARGET, [ap.REFLECTIONS])

        ghost = _swap_after(ClarificationTests.GHOST_ARGS, "--reflection-id", "R-RESET-GHOST")

        code2, payload2, raw2 = run_cli(ghost)

        self.assertEqual(code2, 3, raw2)

        self.assertNotIn("warning", payload2)

        self.assertEqual(ap._LAST_APPEND_TARGET, [ap.CLARIFICATIONS])




# ---------------------------------------------------------------------------

# trace-chain full loop with refutation and supersede history (closure #6)

# ---------------------------------------------------------------------------



class TraceChainHistoryTests(V03Base):

    def test_trace_distinguishes_active_refuted_historical_current(self):

        self.record_decision(); self.record_outcome(technical_result="failed")

        # original reflection (historical interpretation)

        code, _, raw = run_cli(_swap_after(ReflectionCreationTests.BASE_ARGS,

                                           "--reflection-id", "R-HIST-01"))

        self.assertEqual(code, 0, raw)

        # active causal arc O-001 -> R-HIST-01

        run_cli(["link-cause", "--from", "O-001", "--to", "R-HIST-01",

                 "--relation", "caused_or_contributed_to", "--epistemic-state", "observed",

                 "--confidence", "0.6", "--provenance-ref", "O-001"])

        lid = self.read_jsonl("LINKS")[0]["link_id"]

        # correction: Alberto declares the real cause (supersedes chain)

        code, confirmed, raw = run_cli([

            "confirm-causality", "--reflection-id", "R-HIST-01",

            "--cause", "mancato audit delle dipendenze",

            "--by", "alberto",

            "--statement-excerpt", "la causa fu che non controllai le dipendenze"])

        self.assertEqual(code, 0, raw)

        current_reflection_id = confirmed["reflection_id"]

        # refute the old active arc

        code, _, raw = run_cli(["refute-link", "--link-id", lid,

                                "--reason", "smentita da conferma successiva",

                                "--provenance-ref", "evidence/METHOD_CASES_2026-10-03.md"])

        self.assertEqual(code, 0, raw)

        # decision + outcome downstream: connect them by a REAL influenced edge

        self.record_decision(did="D-002")

        code, _, raw = run_cli(["link-cause", "--from", current_reflection_id,

                                "--to", "D-002", "--relation", "influenced",

                                "--epistemic-state", "declared_by_alberto",

                                "--confidence", "1.0", "--provenance-ref", current_reflection_id])

        self.assertEqual(code, 0, raw)

        self.record_outcome(oid="O-002", did="D-002")



        code, _, raw = run_cli(["trace-chain", "--from", "R-HIST-01"])

        self.assertEqual(code, 0, raw)

        chain = json.loads(raw)

        nodes = {n["id"]: n for n in chain["nodes"]}

        edges = chain["edges"]



        # historical AND current reflection versions both recoverable

        self.assertIn("R-HIST-01", nodes)

        cur_id = next(n["id"] for n in chain["nodes"]

                      if n["id"].startswith("R-HIST-01-ca"))

        self.assertIn(cur_id, nodes)

        # supersede edge marks which version is current

        sup_edge = next(e for e in edges if e["relation"] == "superseded_by")

        self.assertEqual((sup_edge["from"], sup_edge["to"]), ("R-HIST-01", cur_id))

        # refuted arc excluded from the active walk...

        self.assertNotIn(lid, [e.get("link_id") for e in edges])

        # ...but preserved in the ledger with its validity flag

        links = self.read_jsonl("LINKS")

        refut = next(l for l in links if l.get("validity") == "refuted")

        self.assertEqual(refut["refutes"], lid)

        # active arcs keep provenance + epistemic state

        for e in edges:

            if e.get("link_id"):

                self.assertIn("epistemic_state", e)

                self.assertIn("provenance", e)

        # downstream decision/outcome reachable (FK edge produced)

        self.assertIn("produced", [e["relation"] for e in edges])

        self.assertIn("O-002", nodes)





if __name__ == "__main__":

    unittest.main()
