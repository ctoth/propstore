# ASPIC+ Implementation Notes — 2026-03-22

## GOAL
Implement ASPIC+ argumentation semantics in propstore (TDD, Hypothesis-heavy).

## DONE
- Step 1 COMPLETE: `propstore/dung.py` + `tests/test_dung.py` — 42 tests pass (12 property, 30 concrete)
  - Committed: bc41bc9 on branch `aspic-argumentation`
  - ArgumentationFramework dataclass, grounded/preferred/stable/complete extensions
  - All Dung 1995 theorems verified via Hypothesis

## DONE (continued)
- Step 2 COMPLETE: `propstore/preference.py` + `tests/test_preference.py` — 27 tests pass
  - Committed: e313d17
  - strictly_weaker (Def 19), defeat_holds (Def 9), claim_strength
- Step 3 COMPLETE: `propstore/argumentation.py` + `tests/test_argumentation_integration.py` — 15 tests pass
  - Not yet committed
  - build_argumentation_framework, compute_justified_claims
  - In-memory SQLite fixtures with direct SQL INSERT (fast, no build_sidecar dependency)
  - Property tests: no supports in defeats, grounded is conflict-free, justified subset of input

## BASELINE
- 1 pre-existing failure: `test_missing_claims_key_errors` in test_validate_claims.py (unrelated)
- 406 tests pass on clean master

## DONE (continued)
- Step 3 committed: fadf7d0
- Step 4 committed: f6e7848 — 600 tests pass, 0 failures
  - types.py: STANCE → ARGUMENTATION
  - resolution.py: removed _resolve_stance/_STANCE_WEIGHTS, added _resolve_argumentation
  - compiler_cmds.py: updated CLI choices, added --semantics and --set-comparison options
  - test_world_model.py: rewrote 3 stance tests as argumentation tests

## DONE (continued)
- Step 4c/4d committed: 8255ccf
  - defeat table schema + _populate_defeats in build_sidecar.py
  - world extensions CLI command
  - Fixed row_factory issue: _populate_defeats saves/restores conn.row_factory since build_sidecar doesn't set sqlite3.Row
  - 600 tests pass, 84 new tests (42 dung + 27 preference + 15 integration)

## STATUS: COMPLETE
All 5 steps done. Branch: aspic-argumentation (5 commits ahead of master).
No blockers. 1 pre-existing failure (test_validate_claims) unchanged.
