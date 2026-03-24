# Review Fixes Session Notes

## GOAL
Execute all 26 fixes from the code review, TDD style, under Foreman protocol.

## TEST COUNT PROGRESSION
975 → 984 → 988 → 991 → 998 → 1001 (current)

## BATCH 1 — COMPLETE
- 1A: SQL injection. `85d0415`. VERIFIED.
- 1B: Lying status. `f25d55d`. VERIFIED.
- 1C: Bare except. `60ff347`. VERIFIED.

## BATCH 2 — COMPLETE
- 2A: Cayrol DRY. `7486395`. VERIFIED.
- 2B: Grounded attacks. `5fecb88`, `2f48db1`. VERIFIED.
- 2C: Cayrol fixpoint. `db20a90`. VERIFIED.

## BATCH 3 — COMPLETE
- 3A: Z3 div-zero. Code on disk, hash confused. VERIFIED.
- 3B: Context fallthrough. `5309025`. VERIFIED.
- 3C: CEL unescape. `293e678`. VERIFIED.

## BATCH 4 — COMPLETE
- 4A: Test stubs DRY. `89e7231`. VERIFIED.
- 4B: Future bindings. `89f6ad8`. VERIFIED.
- 4C: Nogood misattribution. `3ff117a`. VERIFIED.

## BATCH 5 — COMPLETE
- 5A: Hypothetical stale. `c3f1185`. VERIFIED.
- 5B: Tie-breaking. `a8633c6`. VERIFIED.
- 5C: Chain query skip. `ea4aaa9`. VERIFIED.

## BATCH 6 — IN PROGRESS
- 6A: Form algebra filter — RUNNING
- 6B, 6C: Waiting on 6A

## BATCH 7 — IN PROGRESS
- 7A: collect_known_values DRY — RUNNING
- 7B: Worldline silent except — RUNNING
- 7C: Wrong error labels — RUNNING

## BATCH 8 — READY
Prompts written. Waiting for 6+7.

## NEXT
- When 6A completes: verify, dispatch 6B
- When 7A/7B/7C complete: verify
- When 6+7 done: dispatch Batch 8 (sequential)
