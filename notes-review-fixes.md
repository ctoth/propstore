# Review Fixes Session Notes

## GOAL
Execute all 26 fixes from the code review, TDD style, under Foreman protocol.

## BASELINE
975 tests passing. Now at 991.

## BATCH 1 — COMPLETE
- 1A: SQL injection fix. Commit `85d0415`. +5 tests. VERIFIED.
- 1B: Lying status fix. Commit `f25d55d`. +1 test. VERIFIED.
- 1C: Bare except narrowing. Commit `60ff347`. +2 tests. VERIFIED.

## BATCH 2 — COMPLETE
- 2A: Cayrol DRY. Commit `7486395`. VERIFIED.
- 2B: Grounded extension attacks. Commits `5fecb88`, `2f48db1`. VERIFIED. Literature confirmed fix via scout-2b.
- 2C: Cayrol fixpoint. Commit `db20a90`. +1 test. VERIFIED.

## BATCH 3 — COMPLETE
- 3A: Z3 div-zero guard. Code verified on disk. Commit hash confused with 2B due to concurrent agents.
- 3B: Context fallthrough. Commit `5309025`. +1 test, 4 updated. VERIFIED.
- 3C: CEL unescape. Commit `293e678`. +3 tests. VERIFIED.

## BATCH 4 — IN PROGRESS
- 4A: Test stubs DRY. Commit `89e7231`. VERIFIED.
- 4B: Future engine bindings — RUNNING (agent dispatched, touches atms.py)
- 4C: Nogood misattribution — RUNNING (agent dispatched, touches atms.py)
- RISK: 4B and 4C both touch atms.py and test_atms_engine.py. Could cause merge conflicts. If one fails, re-dispatch sequentially.

## BATCH 5 — IN PROGRESS
- 5A: Hypothetical stale conflicts — RUNNING (hypothetical.py, test_world_model.py)
- 5B: Resolution tie-breaking — RUNNING (resolution.py, test_world_model.py)
- 5C: Chain query silent skip — RUNNING (model.py, test_world_model.py)
- RISK: 5A, 5B, 5C all touch test_world_model.py. Could cause merge conflicts.

## BATCHES 6-8 — READY
All prompt files written. Waiting for 4+5 to complete.

## OBSERVATIONS
- Concurrent agents can produce commit hash confusion (3A reported 2B's hash). Code still lands correctly.
- 3B fixed the 3 pre-existing test_contexts.py failures (they were asserting the old buggy CONTEXT_PHI_NODE behavior)
- Pyright diagnostics throughout are pre-existing, not from our changes
- Ward's uncommitted-files warnings fire for notes/prompts/reports which are coordination artifacts, not source code
- Prompts dir is gitignored, so prompt files can't be committed

## NEXT
1. When 4B, 4C complete: read reports, verify. If merge conflict, re-dispatch loser.
2. When 5A, 5B, 5C complete: read reports, verify. If merge conflict, re-dispatch.
3. Dispatch Batch 6 (sequential: 6A → 6B → 6C, all touch build_sidecar.py)
4. Dispatch Batch 7 (parallel: 7A, 7B, 7C, different files)
5. Dispatch Batch 8 (sequential: 8A → 8B → 8C, shared CLI files)
6. Final verification: full test suite, pks build
