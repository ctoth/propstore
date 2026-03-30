# Multi-Source Merge Consumer Inventory

**Date:** 2026-03-29
**Purpose:** identify live production consumers, bridge consumers, and non-production consumers of the formal merge stack

---

## Verdict

The formal merge object is already used by a small number of live production surfaces.

The most important live consumers are:

- `pks merge inspect`
- `pks merge commit`

The most important non-live but strategically important consumers are:

- `structured_merge.py`
- `branch_reasoning.py`

So the first coding slice should harden active canonical surfaces and only then narrow bridge helpers.

---

## Live Production Consumers

### CLI inspect path

- [merge_cmds.py](C:/Users/Q/code/propstore/propstore/cli/merge_cmds.py)
  - `merge_inspect(...)`
- [merge_classifier.py](C:/Users/Q/code/propstore/propstore/repo/merge_classifier.py)
  - `build_merge_framework(...)`
- [merge_report.py](C:/Users/Q/code/propstore/propstore/repo/merge_report.py)
  - `summarize_merge_framework(...)`

Current role:

- this is the main user-visible read path over the formal merge object

Why it matters:

- if the output shape is semantically weak or incomplete, users get a distorted picture of the merge layer even if the kernel is correct

### CLI commit path

- [merge_cmds.py](C:/Users/Q/code/propstore/propstore/cli/merge_cmds.py)
  - `merge_commit_cmd(...)`
- [merge_commit.py](C:/Users/Q/code/propstore/propstore/repo/merge_commit.py)
  - `create_merge_commit(...)`
- [merge_classifier.py](C:/Users/Q/code/propstore/propstore/repo/merge_classifier.py)
  - `build_merge_framework(...)`

Current role:

- this is the main user-visible write path from the formal merge object to storage

Why it matters:

- it proves the formal merge object is already operationally central, not just test-only infrastructure

---

## Bridge Or Transitional Consumers

### Branch reasoning bridge

- [branch_reasoning.py](C:/Users/Q/code/propstore/propstore/repo/branch_reasoning.py)
  - `branch_nogoods_from_merge(...)`
  - `inject_branch_stances(...)`

Current observed usage:

- direct repo search shows test references, but no obvious live production callers of `inject_branch_stances(...)`

Interpretation:

- this is still bridge code
- but it is not currently the highest-risk live dependency

### Structured merge slice

- [structured_merge.py](C:/Users/Q/code/propstore/propstore/repo/structured_merge.py)
  - `build_branch_structured_summary(...)`
  - `build_structured_merge_candidates(...)`

Current observed usage:

- direct repo search shows docs and tests, but no obvious live production callers

Interpretation:

- this is not a bridge back to old semantics
- it is a forward-looking but still under-specified semantic boundary

---

## Test-Only Or Validation Consumers

Evidence:

- [test_merge_classifier.py](C:/Users/Q/code/propstore/tests/test_merge_classifier.py)
- [test_merge_report.py](C:/Users/Q/code/propstore/tests/test_merge_report.py)
- [test_merge_cli.py](C:/Users/Q/code/propstore/tests/test_merge_cli.py)
- [test_branch_reasoning.py](C:/Users/Q/code/propstore/tests/test_branch_reasoning.py)
- [test_structured_merge_projection.py](C:/Users/Q/code/propstore/tests/test_structured_merge_projection.py)

Interpretation:

- tests already cover the kernel and parts of the public surface
- the next coding slice should extend these targeted tests, not begin from a blank slate

---

## Recommended Priority Order

1. [merge_report.py](C:/Users/Q/code/propstore/propstore/repo/merge_report.py)
   - active canonical read surface
2. [merge_cmds.py](C:/Users/Q/code/propstore/propstore/cli/merge_cmds.py)
   - active canonical user surface
3. [structured_merge.py](C:/Users/Q/code/propstore/propstore/repo/structured_merge.py)
   - under-specified semantic boundary
4. [branch_reasoning.py](C:/Users/Q/code/propstore/propstore/repo/branch_reasoning.py)
   - important bridge seam, but not the first live production bottleneck

---

## Recommendation

Treat the next coding slice as:

- harden the active canonical merge-object surfaces
- define the structured-summary contract more sharply
- then revisit bridge narrowing once live-consumer needs are fully pinned down
