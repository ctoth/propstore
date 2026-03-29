# Multi-Source Structured Merge Gap Audit

**Date:** 2026-03-29
**Purpose:** map the current repo state against `proposals/multi-source-structured-merge.md` and identify the precise remaining work before Phase 6 coding

---

## Verdict

The merge stack is materially further along than the draft proposal says.

The repo already has:

- a canonical partial-framework kernel
- exact merge operators
- completion queries
- a repo-facing merge object
- CLI inspection and commit surfaces
- a first branch-local structured-summary slice

The main remaining gap is **not** kernel invention. It is **consolidation**:

- remove or reduce bridge semantics
- tighten the structured boundary
- prepare explicit policy insertion points
- make the proposal/checklist match the actual code

---

## Canonical Pieces Already Implemented

### Formal kernel

- [merge_framework.py](C:/Users/Q/code/propstore/propstore/repo/merge_framework.py)
  - `PartialArgumentationFramework`
  - partitioned `attack / ignorance / non_attacks`
  - exact completion enumeration
- [paf_merge.py](C:/Users/Q/code/propstore/propstore/repo/paf_merge.py)
  - `consensual_expand`
  - exact `sum`, `max`, `leximax`
- [paf_queries.py](C:/Users/Q/code/propstore/propstore/repo/paf_queries.py)
  - skeptical and credulous queries over completions

Assessment:

- this is the canonical merge kernel already
- future work should preserve and harden it, not redesign it casually

### Repo merge object

- [merge_classifier.py](C:/Users/Q/code/propstore/propstore/repo/merge_classifier.py)
  - `MergeArgument`
  - `RepoMergeFramework`
  - `build_merge_framework(...)`
- [merge_commit.py](C:/Users/Q/code/propstore/propstore/repo/merge_commit.py)
  - storage merge commit from the formal object
- [merge_report.py](C:/Users/Q/code/propstore/propstore/repo/merge_report.py)
  - repo-facing merge summaries

Assessment:

- the repo merge boundary is already formal-object-first
- this part of the proposal should be framed as completed baseline, not future work

### Public surfaces

- [merge_cmds.py](C:/Users/Q/code/propstore/propstore/cli/merge_cmds.py)
  - `pks merge inspect`
  - `pks merge commit`
- [semantic-merge.md](C:/Users/Q/code/propstore/docs/semantic-merge.md)
  - current public explanation of the merge layer

Assessment:

- there is already a user-visible path over the formal merge object
- future work should extend or tighten this surface, not pretend it does not exist

### First structured slice

- [structured_merge.py](C:/Users/Q/code/propstore/propstore/repo/structured_merge.py)
  - branch-local structured summaries
  - exact merge candidates over those summaries

Assessment:

- this is a real first slice, not vapor
- but it is still under-specified relative to the target structured boundary

---

## Bridge Code Still Present

### Synthetic contradiction export

- [branch_reasoning.py](C:/Users/Q/code/propstore/propstore/repo/branch_reasoning.py)
  - `inject_branch_stances(...)`

Why it matters:

- this re-expresses merge attacks as synthetic `contradicts` stances for older consumers
- that is useful as a bridge, but it is not the canonical merge semantics

Assessment:

- this is the highest-signal bridge path to target first
- it should either shrink or become explicitly transitional in docs/tests

### Structured summary contract

- [structured_merge.py](C:/Users/Q/code/propstore/propstore/repo/structured_merge.py)

Why it matters:

- the module exists, but the precise contract for summary identity and preserved semantics is still too loose

Assessment:

- this is not legacy code
- it is an incomplete boundary and needs specification plus stronger tests before major extension

---

## Missing Or Under-Specified Work

### Structured boundary semantics

Missing:

- explicit contract for branch-local summary IDs
- precise statement of what information is preserved versus intentionally collapsed
- stronger invariants for provenance and out-of-scope uncertainty

Impact:

- without this, Phase 7 structured-state work can drift semantically

### Policy insertion point

Missing:

- clear statement of where source trust and preference influence merge:
  - merge kernel
  - post-merge defeat
  - explanation only

Impact:

- Phase 8 policy work will either entangle the kernel or invent hidden defaults unless this seam is made explicit

### System-level audit framing

Missing:

- the draft proposal still describes too much of the merge kernel as future work
- the repo now needs a completion plan, not a from-scratch plan

Impact:

- implementation work could be mis-sequenced or duplicated

---

## Test Baseline

Evidence of already-landed coverage:

- [test_paf_core.py](C:/Users/Q/code/propstore/tests/test_paf_core.py)
- [test_paf_merge.py](C:/Users/Q/code/propstore/tests/test_paf_merge.py)
- [test_paf_queries.py](C:/Users/Q/code/propstore/tests/test_paf_queries.py)
- [test_repo_merge_object.py](C:/Users/Q/code/propstore/tests/test_repo_merge_object.py)
- [test_structured_merge_projection.py](C:/Users/Q/code/propstore/tests/test_structured_merge_projection.py)
- [test_branch_reasoning.py](C:/Users/Q/code/propstore/tests/test_branch_reasoning.py)
- [test_merge_cli.py](C:/Users/Q/code/propstore/tests/test_merge_cli.py)
- [test_merge_report.py](C:/Users/Q/code/propstore/tests/test_merge_report.py)

Assessment:

- the merge area already has meaningful test coverage
- the next coding pass should add missing bridge-replacement tests, not restart kernel testing from zero

---

## Recommended Next Coding Target

Target:

- [branch_reasoning.py](C:/Users/Q/code/propstore/propstore/repo/branch_reasoning.py)

Reason:

- it is the clearest remaining bridge from formal merge semantics back into older contradiction-based consumers
- it is small enough to tackle in a test-first slice
- replacing or narrowing it will prove whether the merge object is truly authoritative in production paths

Recommended RED tests first:

1. consumers that still need stance export are explicitly identified
2. no canonical merge query path depends on `inject_branch_stances(...)`
3. ignorance remains non-nogood and non-stance-generating
4. mutual attacks remain the only branch-nogood source

---

## Recommendation

Proceed with Phase 6 as **merge-kernel completion and consolidation**.

Do not spend the next pass inventing new kernel abstractions.

Do:

1. replace or narrow bridge semantics
2. tighten the structured summary contract
3. prepare the policy seam cleanly
