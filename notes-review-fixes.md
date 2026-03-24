# Review Fixes Session Notes

## GOAL
Execute all 26 fixes from the code review, TDD style, under Foreman protocol.

## BASELINE
975 tests passing, 0 failures. Now at 984 passing.

## BATCH 1 — COMPLETE
- 1A: SQL injection fix. Commit `85d0415`. +5 tests. VERIFIED against plan.
- 1B: Lying status fix. Commit `f25d55d`. +1 test, 3 files changed. VERIFIED against plan.
- 1C: Bare except narrowing. Commit `60ff347`. +2 tests, 2 files changed. VERIFIED against plan.

## BATCH 2 — IN PROGRESS
- 2A: Cayrol DRY — agent running (structured_argument.py modified, work in progress)
- Scout 2B: Literature check — agent running
- 2B coder: blocked on scout verdict
- 2C: blocked on 2A completion

## BATCH 3-8 — READY
All prompt files written. Waiting for Batch 2 progress.

## ANOMALY
- Commit `b0242d1` "Generalize dimensions beyond physics" — only touches schema/generated/form.schema.json. Likely a previously staged change that an agent committed. Not a plan deviation. Not harmful.

## NEXT
- When 2A completes: read report, verify, dispatch 2C (if scout-2B not done) or 2B coder + 2C
- When scout-2B completes: read report, write 2B coder prompt if verdict is YES
- Batch 3 can start in parallel with Batch 2 remainder (no file overlap)
