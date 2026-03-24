# Review Fixes Session Notes

## GOAL
Execute all 26 fixes from the code review, TDD style, under Foreman protocol.

## BASELINE
975 tests passing, 0 failures.

## ALL PROMPT FILES COMPLETE
- Batch 1: fix-1a, fix-1b, fix-1c (DISPATCHED — awaiting)
- Batch 2: fix-2a, scout-2b, fix-2c (ready; 2B coder prompt pending scout verdict)
- Batch 3: fix-3a, fix-3b, fix-3c (ready)
- Batch 4: fix-4a, fix-4b, fix-4c (ready)
- Batch 5: fix-5a, fix-5b, fix-5c (ready)
- Batch 6: fix-6a, fix-6b, fix-6c (ready)
- Batch 7: fix-7a, fix-7b, fix-7c (ready)
- Batch 8: fix-8a, fix-8b, fix-8c (ready)

## DONE
- Plan written and approved
- All 24 prompt files written

## AWAITING
- fix-1a agent (SQL injection) — background
- fix-1b agent (lying status) — background
- fix-1c agent (bare except) — background

## NEXT
- When Batch 1 completes: read reports, verify against plan, update notes
- Dispatch Batch 2 (sequential: 2A first, then scout-2B, then 2B coder if confirmed, then 2C)
- Dispatch Batch 3 in parallel (3A, 3B, 3C independent)
- Can run Batch 2 and 3 concurrently since no file overlap
