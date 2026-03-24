# Review Fixes Session Notes

## GOAL
Execute all 26 fixes from the code review, TDD style, under Foreman protocol.

## BASELINE
975 tests passing. Now at ~988.

## BATCH 1 — COMPLETE
- 1A: SQL injection fix. Commit `85d0415`. +5 tests. VERIFIED.
- 1B: Lying status fix. Commit `f25d55d`. +1 test. VERIFIED.
- 1C: Bare except narrowing. Commit `60ff347`. +2 tests. VERIFIED.

## BATCH 2 — IN PROGRESS
- 2A: Cayrol DRY. Commit `7486395`. VERIFIED.
- 2B: Grounded extension attacks. Commits `5fecb88` (red), `2f48db1` (green). VERIFIED.
- 2C: Cayrol fixpoint — agent running

## BATCH 3 — IN PROGRESS
- 3A: Z3 div-zero — agent running
- 3B: Context fallthrough — agent running
- 3C: CEL unescape. Commit `293e678`. +3 tests. VERIFIED.

## BATCHES 4-8 — READY
All prompt files written.

## ANOMALY
- 3 pre-existing test failures in test_contexts.py (CONTEXT_PHI_NODE) — will be fixed by 3B
- Commit `b0242d1` unrelated to plan — schema file only, harmless

## NEXT
- When 2C completes: read report, verify — Batch 2 done
- When 3A, 3B complete: read reports, verify — Batch 3 done
- Then dispatch Batch 4 (sequential: 4A, then 4B+4C parallel)
- Can also start Batch 5 in parallel (different files)
