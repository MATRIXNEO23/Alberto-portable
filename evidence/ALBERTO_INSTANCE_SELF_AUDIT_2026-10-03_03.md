# Alberto-portable instance self-audit 03

Recorded: 2026-10-03
Instance: `chat-2026-10-03-alberto-portable-01`

## Objective

Increase long-term coherence with Alberto by preventing over-generic experience reuse and by invalidating self-audits when the recovery structure or operating method materially changes.

## Gaps addressed

1. Experience retrieval previously allowed `task_type` alone to select a verified precedent.
2. A completed instance audit remained valid even after relevant recovery structure/method changes.

## Implemented corrections

- Verified reusable experiences now require at least one contextual anchor beyond generic `task_type` / `project` fields.
- Canonical experiences were enriched with explicit contextual reuse anchors.
- Matching results are ordered by specificity and expose their contextual anchors.
- Source integrity rejects canonical verified experiences with generic-only reuse conditions.
- A deterministic `structure_fingerprint` now covers the recovery manifest, domain/operational criterion sources, instance-audit criterion, recovery engine, and repository validator, while deliberately excluding ordinary experience-ledger additions.
- Instance audit records store the structure fingerprint.
- `instance_audit_status` returns `AUDIT_STALE` when the latest completed audit fingerprint differs from the current structure/method fingerprint.

## Verification

CI run #80 on commit `b4c5063a6650d89f4f1d02949b054359c10af32b` passed repository validation, source integrity and the full unittest suite: 76 tests PASS.

Validated structure fingerprint:
`04a1f91978d159ce0ecfe949b8b9cb65b991b0b22b4310d6da3002692b707c94`

Specific tests cover:
- task-type-only experience rejection;
- contextual experience recovery;
- specificity ordering;
- stale audit detection after a structure fingerprint change;
- completed audit acceptance when fingerprints match.

## Regression considerations

The fingerprint intentionally excludes normal additions to `data/project_experience.jsonl`, because gaining a new case is not by itself a structural/method change requiring a full instance self-audit. Changes to criteria, manifest, audit policy, recovery logic or validation logic do invalidate the audit.

The retrieval gate may reduce recall compared with task-type-only matching, but this is intentional: a missed precedent is safer than applying a materially unrelated precedent. Additional contextual anchors can be added to cases as experience grows.
