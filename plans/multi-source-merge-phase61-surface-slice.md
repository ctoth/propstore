# Multi-Source Merge Phase 6.1 Surface Slice

**Date:** 2026-03-29
**Depends on:** `plans/multi-source-structured-merge-checklist.md`, `reports/multi-source-merge-literature-refresh-2026-03-29.md`
**Scope:** active canonical inspect/commit surface after the literature refresh
**Status:** Implemented

---

## Goal

Advance Phase 6.1 on the live public merge path without widening the scope into bridge cleanup or structured incomplete-information inquiry.

This slice is specifically about the active canonical surface:

- `pks merge inspect`
- `pks merge commit`

The literature refresh supports this sequencing:

- merge stays structural
- inspect/commit stay the public canonical surface

---

## Owned Files

- `propstore/repo/merge_commit.py`
- `propstore/cli/merge_cmds.py`
- `tests/test_merge_classifier.py`
- `tests/test_merge_cli.py`

Optional only if forced by tests:

- `propstore/repo/merge_report.py`

Explicitly out of scope:

- `propstore/repo/structured_merge.py`
- policy-weighted merge semantics
- Odekerken-style stability/relevance machinery

---

## RED Tests To Write First

1. the commit path is a deterministic projection from the canonical `RepoMergeFramework.arguments`
2. conflicting alternatives survive into the storage merge output as canonical emitted claims rather than collapsing through any legacy bucket path
3. the CLI still keeps:
   - formal merge inspection
   - storage merge commit
   clearly separate

---

## Questions This Slice Must Answer

1. Is `claims/merged.yaml` the stable and sufficient storage projection for the canonical merge object in V1?
2. What minimum invariants on ordering, provenance, and determinism must the commit path guarantee?
3. Is any public surface still smuggling bridge semantics into the live merge path?

---

## GREEN Target

One small public-surface hardening change, or no production change if the new tests prove the current path is already correct.

The preference is:

- more tests than code
- minimal production edits

---

## Stop Condition

Stop when:

1. the active inspect/commit path is pinned by tests
2. the path is clearly canonical
3. no live dependency on bridge code is found

Do not widen into:

- bridge deletion
- structured-summary redesign
- policy/governance work

---

## Targeted Test Run

```bash
uv run pytest -vv tests/test_merge_classifier.py tests/test_merge_cli.py
```

Tee full output to `logs/test-runs/`, then reread the main checklist before picking the next slice.
