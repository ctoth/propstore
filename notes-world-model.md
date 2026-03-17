# WorldModel Implementation Notes

## GOAL
Implement WorldModel (condition-binding reasoner over compiled sidecar) with TDD tests, hypothesis properties, and CLI integration.

## Key observations from codebase reading
- Z3ConditionSolver.are_disjoint(a, b) is the core primitive — returns True if conjunction is UNSAT
- _build_cel_registry in conflict_detector.py:226 converts concept rows to ConceptInfo dicts
- Sidecar schema: concept, claim, claim_stance, conflicts tables (build_sidecar.py)
- claim.conditions_cel stored as JSON-encoded list of CEL strings
- Repository class provides sidecar_path property
- Test fixtures in test_build_sidecar.py have 9 claims with known conditions

## Claim inventory (from test_build_sidecar.py fixtures)
- claim1: concept1 (F0), value=200, conds=["task == 'speech'"]
- claim2: concept1, value=350, conds=["task == 'speech'"], stances: contradicts claim1
- claim3: concept1, value=180, conds=["task == 'singing'"]
- claim4: concept2 (Ps), value=800, conds=["task == 'speech'"]
- claim5: observation, no concept_id, no conditions
- claim6: concept2, value=800, conds=["task == 'speech'"]
- claim7: concept1, value=250, conds=["task == 'speech'", "fundamental_frequency > 100"]
- claim8: equation, no concept_id, conds=["task == 'speech'"]
- claim9: concept1, value=220, conds=["task == 'whisper'"]

## Progress
- [x] Read codebase (z3_conditions, build_sidecar, conflict_detector, CLI, repository)
- [x] Fixed global CLAUDE.md notes file guidance
- [x] Write test_world_model.py — 39 tests (TDD + hypothesis properties)
- [x] Write compiler/world_model.py — WorldModel, BoundWorld, ValueResult
- [x] Wire CLI (compiler_cmds.py, __init__.py) — world status/query/bind/explain
- [x] Fix: handle missing claim tables in concepts-only sidecars
- [x] Fix: bind command argument parsing with nargs=-1
- [x] Full test suite: 422 passed, 0 failed
- [x] End-to-end verified: pks build, world status, world bind task=speech, world bind task=singing concept1
