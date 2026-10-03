# Alberto Portable — instance self-audit follow-up 2026-10-03

## User observation

Alberto does not consider the current system complete yet. Two areas must remain explicit improvement targets:

1. Experience retrieval precision: do not recover precedents merely because they share the same broad task type. Reuse should require enough contextual similarity to make the precedent decision-relevant.
2. Audit freshness: an audit completed earlier in the same instance must not remain sufficient after a material change to the recovered structure or operating method.

## Verified current gaps

### Experience retrieval

The current `recover_experiences()` accepts an experience when every key in `reuse_when` matches. Existing experiences may use only `task_type` in `reuse_when`, so a precedent can be recovered solely because the new case has the same task class. This is too coarse for the long-term objective.

### Instance audit freshness

The current `instance_audit_status()` considers the latest completed audit for an `instance_id` sufficient. It reports the stored `recovery_head`, but it does not compare a robust fingerprint of the currently recovered method/structure against the structure that was audited.

## Required future improvements

### Experience matching

Introduce a specificity gate or ranked matching model that requires decision-relevant contextual anchors beyond generic task type, unless an experience is explicitly declared safe for broad reuse. Matching evidence should be auditable (for example matched dimensions and specificity score), and tests must reject false-positive retrieval from task-type-only similarity.

### Audit invalidation

Record a deterministic fingerprint of the recovery-relevant structure/method at audit time and compare it on subsequent status checks. A material change to canonical recovery sources, active criteria, or recovery logic must invalidate the old audit and require a new one. Mere unrelated repository changes should not cause unnecessary audits.

## Adoption conditions

Do not consider either improvement adopted merely because code exists. Adoption requires:
- targeted tests for positive and negative experience matches;
- tests proving task-type-only false positives are rejected;
- tests proving a material method/structure change invalidates an earlier audit;
- tests proving irrelevant/non-structural changes do not cause audit churn;
- full existing CI remains green.

These are open improvement gaps, not evidence that the current foundation is unusable.
