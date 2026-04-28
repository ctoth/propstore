# Workstream closure reports

Every workstream checked off in `../INDEX.md` gets one closure report in this
directory named `<WS-ID>-closure.md`.

Required structure:

```markdown
# <WS-ID> closure report

**Closing commit**: `<sha>`
**Closed in INDEX**: yes/no

## Findings Closed

- `<finding>` — how it was fixed.

## Tests Written First

- `<test path>` — why it failed before the fix.

## Property Gates

- `<Hypothesis/property test path>` — paper or decision invariant asserted.

## Verification

- `<logged command>` — `<log path>` — result.

## Files Changed

- `<path>` — summary.

## Remaining Risks / Successors

- None, or explicitly named successor WS.
```

No INDEX row should be changed to `CLOSED <sha>` until its closure report exists.
