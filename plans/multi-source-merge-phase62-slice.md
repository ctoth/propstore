# Multi-Source Merge Phase 6.2 Slice

**Date:** 2026-03-29
**Depends on:** `plans/multi-source-structured-merge-checklist.md`, `reports/multi-source-merge-operator-query-gap-audit-2026-03-29.md`
**Scope:** exact RED/GREEN plan for operator and query hardening
**Status:** Draft

---

## Goal

Pin the merge kernel/operator/query semantics more tightly with exact tests before moving on to bridge cleanup or policy work.

This slice assumes the kernel code may already be correct. The point is to prove it more sharply.

---

## Owned Files

- `tests/test_paf_merge.py`
- `tests/test_paf_queries.py`
- optionally `tests/test_paf_core.py`
- only if required:
  - `propstore/repo/paf_merge.py`
  - `propstore/repo/paf_queries.py`
  - `propstore/repo/merge_framework.py`

The default expectation is:

- tests first
- minimal or zero production changes unless a new exact regression exposes a real bug

---

## Slice 6.2A: Operator Exact Regressions

### RED tests first

1. concordant profiles yield a unique result for:
   - `sum`
   - `max`
   - `leximax`
2. a tiny exact profile where `sum` and `max` diverge
3. a tiny exact profile where `leximax` strictly refines a multi-result `max` set
4. expansion over a shared full universe introduces no new ignorance

### GREEN target

- either:
  - no code change because current operators already satisfy the stronger regressions
  - or one minimal fix in `paf_merge.py`

### Stop condition

- stop once the operator family is distinguished by exact tiny regressions, not just generic invariants

---

## Slice 6.2B: Query Exactness

### RED tests first

1. helper output matches brute-force completion evaluation on tiny profiles
2. skeptical/credulous behavior is checked under at least one non-grounded semantics case
3. ignorance fixation is tested both ways:
   - ignorance -> attack
   - ignorance -> non-attack

### GREEN target

- either:
  - no code change because current query helpers already satisfy the stronger checks
  - or one minimal fix in `paf_queries.py`

### Stop condition

- stop once helper semantics are explicitly pinned to brute-force completion behavior on tiny profiles

---

## Out Of Scope

- bridge cleanup in `branch_reasoning.py`
- structured merge contract changes
- CLI/report surface expansion
- source-weighted merge policy
- any merge/revision interaction changes

---

## Commit Sequence

1. RED tests for Slice 6.2A
2. GREEN operator change only if required
3. targeted operator tests
4. reread the checklist
5. RED tests for Slice 6.2B
6. GREEN query change only if required
7. targeted query tests
8. reread the checklist again

If both sub-slices land in one pass:

9. run combined targeted kernel/operator/query regression

---

## Recommended Test Runs

After Slice 6.2A GREEN:

```bash
uv run pytest -vv tests/test_paf_merge.py
```

After Slice 6.2B GREEN:

```bash
uv run pytest -vv tests/test_paf_queries.py
```

Combined regression if both land:

```bash
uv run pytest -vv tests/test_paf_core.py tests/test_paf_merge.py tests/test_paf_queries.py
```

All outputs should be tee'd to `logs/test-runs/`.

---

## Recommendation

Start with `tests/test_paf_merge.py`.

Reason:

- the operator family still has the biggest semantic distinction gap
- exact tiny-profile regressions will either validate the current implementation cleanly or expose the first real bug
