# Structured Merge Contract Gaps

**Date:** 2026-03-29
**Purpose:** capture what `structured_merge.py` currently guarantees, and what still needs to be specified before coding Phase 6.3

---

## Current Contract Actually Enforced

From the code in [structured_merge.py](C:/Users/Q/code/propstore/propstore/repo/structured_merge.py):

- `BranchStructuredSummary` contains:
  - `branch`
  - `active_claims`
  - `stance_rows`
  - `projection`
- `build_branch_structured_summary(...)` reads claims and stance rows directly from a branch snapshot and builds an ASPIC projection
- `build_structured_merge_candidates(...)` merges branch-local projected AFs via exact AF merge operators

From the current tests in [test_structured_merge_projection.py](C:/Users/Q/code/propstore/tests/test_structured_merge_projection.py):

1. branch snapshots can contribute stance rows that appear as attacks in the branch-local projection
2. identical branch summaries yield the same merge candidate under `sum`

That is the actual current contract.

---

## Contract Pieces Still Missing

### 1. Summary identity

Not yet specified:

- what the stable identity of a branch-local summary element is
- whether it is:
  - claim-based
  - argument-based
  - projection-argument-id-based
  - some branch-local summary ID

Why it matters:

- without this, structured merge cannot promise stable cross-branch alignment

### 2. Provenance preservation

Not yet specified:

- how provenance flows from source claims/justifications into the branch-local summary
- which provenance fields are mandatory in summary objects

Why it matters:

- later explanations and policy layers need provenance-bearing merge summaries, not just AF node sets

### 3. Known non-attack versus ignorance

Not yet specified:

- how the structured summary distinguishes:
  - determined non-attack
  - true ignorance
  - out-of-scope relation

Why it matters:

- the core merge architecture depends on preserving `attack / non-attack / ignorance` honestly

### 4. Lossiness boundary

Not yet specified:

- what information from the structured theory is intentionally collapsed when producing the summary

Examples:

- subargument identity
- justification identity
- preference metadata
- support metadata beyond what the projection retains

Why it matters:

- without an explicit lossiness statement, the structured boundary can drift silently

### 5. Reuse and stability

Not yet specified:

- whether identical branch snapshots must produce byte-for-byte stable summaries
- how summary stability should be tested when branch names differ but theory content matches

Why it matters:

- later caching, journaling, and policy comparison work will need stable summary behavior

---

## Recommended RED Tests Before Coding

1. summary identity is stable across repeated builds of the same branch snapshot
2. branch provenance is preserved in the summary surface or explicitly declared absent
3. structured-summary output does not silently convert unknown relations into non-attack
4. identical theory content across different branches yields semantically identical summaries
5. any intentionally dropped structured information is documented by tests or explicit comments

---

## Recommendation

Before editing production structured merge code, we should write down the explicit first-slice contract as:

- what the summary object is
- what it preserves
- what it collapses
- what must remain stable

Phase 6.3 should then code to that contract instead of letting the current helper shape become the contract by accident.
