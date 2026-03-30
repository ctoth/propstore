# Multi-Source Merge First Coding Slice

**Date:** 2026-03-29
**Depends on:** `plans/multi-source-structured-merge-checklist.md`, `reports/multi-source-merge-consumer-inventory-2026-03-29.md`, `reports/structured-merge-contract-gaps-2026-03-29.md`
**Scope:** exact RED/GREEN sequence for the first non-prep merge implementation work
**Status:** Draft

---

## Goal

Start Phase 6 coding on the smallest meaningful live path without drifting into speculative redesign.

This slice is intentionally split:

1. active canonical merge report surface
2. structured-summary contract tightening

Bridge cleanup is not first in line unless these two slices prove it is blocking.

---

## Slice A: Canonical Merge Report Surface

### Owned files

- `propstore/repo/merge_report.py`
- `tests/test_merge_report.py`
- optionally `propstore/cli/merge_cmds.py`
- optionally `tests/test_merge_cli.py`

### Why this slice is first

- it is the main active read surface for the formal merge object
- it is already live through `pks merge inspect`
- it can be improved or pinned down without reopening the merge kernel

### RED tests to write first

1. the report preserves per-argument provenance needed for user-facing inspection
2. the report makes attack, ignorance, and non-attack counts and memberships explicit in a stable shape
3. the report exposes canonical-claim grouping clearly enough to distinguish emitted alternatives from semantic identity
4. the CLI output remains a direct serialization of the canonical report surface rather than a parallel ad hoc summary

### Questions the tests must answer

1. Is the current `statuses` block the right public shape, or should argument objects be surfaced more directly?
2. What minimum provenance fields must be visible at the report layer?
3. Which values must remain stable for later snapshot/diff work?

### GREEN target

- one small report-surface refinement that makes the formal merge object easier to inspect without changing merge semantics

### Stop condition

- stop after the report shape is explicit and tested
- do not widen into policy or structured reasoning in this slice

---

## Slice B: Structured-Summary Contract Tightening

### Owned files

- `propstore/repo/structured_merge.py`
- `tests/test_structured_merge_projection.py`
- optionally `docs/semantic-merge.md`

### Why this slice is second

- it is the largest under-specified boundary
- but it is not the first live production user surface
- tightening it immediately after Slice A keeps momentum without guessing at policy

### RED tests to write first

1. repeated builds of the same branch snapshot produce stable summary content
2. identical theory content across two branches yields semantically identical summaries
3. branch provenance required by the current summary surface is preserved explicitly
4. unknown or out-of-scope relations are not silently collapsed into determined non-attack at the summary boundary

### Questions the tests must answer

1. What is the stable identity of a summary element in V1?
2. Which provenance facts must survive the summary boundary?
3. Which structured details are intentionally outside the first-slice contract?

### GREEN target

- one explicit contract refinement in `structured_merge.py` backed by tests

### Stop condition

- stop once the summary contract is explicit and the tests pin it
- do not yet attempt full structured/abstract equivalence or policy-aware merge

---

## Out Of Scope For The First Coding Slice

- source-weighted merge policy
- revision/merge interplay changes
- branch-reasoning bridge removal unless Slice A or B proves it blocks correctness
- worldline integration changes
- large-scope CLI redesign

---

## Commit Sequence

1. RED tests for Slice A
2. GREEN implementation for Slice A
3. targeted merge report/CLI tests
4. reread the checklist
5. RED tests for Slice B
6. GREEN implementation for Slice B
7. targeted structured merge tests
8. reread the checklist again

---

## Recommended Targeted Test Runs

After Slice A GREEN:

```bash
uv run pytest -vv tests/test_merge_report.py tests/test_merge_cli.py
```

After Slice B GREEN:

```bash
uv run pytest -vv tests/test_structured_merge_projection.py
```

If both slices land in one pass:

```bash
uv run pytest -vv tests/test_merge_report.py tests/test_merge_cli.py tests/test_structured_merge_projection.py
```

All outputs should be tee'd to `logs/test-runs/`.

---

## Recommendation

When coding starts, begin with Slice A unless a fresh code inspection finds an unaccounted live dependency.

That keeps the first GREEN target on an active canonical surface, then moves directly into the most important under-specified semantic boundary.
