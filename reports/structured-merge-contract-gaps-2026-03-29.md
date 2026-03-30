# Structured Merge Contract Gaps

**Date:** 2026-03-29
**Purpose:** capture what `structured_merge.py` currently guarantees after the Phase 6.3 tightening work, and what still remains open before Phase 6 is fully closed

---

## Current Contract Actually Enforced

From the code in [structured_merge.py](C:/Users/Q/code/propstore/propstore/repo/structured_merge.py):

- `BranchStructuredSummary` contains:
  - `branch`
  - `claim_ids`
  - `claim_provenance`
  - `content_signature`
  - `active_claims`
  - `stance_rows`
  - `projection`
- `build_branch_structured_summary(...)` reads claims and stance rows directly from a branch snapshot and builds an ASPIC projection
- stance rows are canonicalized before summary identity is computed:
  - only in-scope stance rows survive
  - stance rows are deterministically ordered
- summary identity is content-based rather than branch-name-based:
  - `claim_ids`
  - normalized claim provenance
  - `content_signature`
- `build_structured_merge_candidates(...)` merges branch-local projected AFs via exact AF merge operators

From the current tests in [test_structured_merge_projection.py](C:/Users/Q/code/propstore/tests/test_structured_merge_projection.py):

1. branch snapshots can contribute stance rows that appear as attacks in the branch-local projection
2. identical branch summaries yield the same merge candidate under `sum`
3. repeated builds of the same branch snapshot are stable
4. branch-local summaries remain scoped to the current branch snapshot
5. out-of-scope stance rows do not perturb summary identity
6. summary identity is invariant to claim-order and stance-order permutations

That is the actual current contract.

---

## Contract Pieces Still Missing

### 1. Stable identity of summary elements

The summary object now has a stable top-level identity surface:

- `claim_ids`
- `claim_provenance`
- `content_signature`

But one deeper question is still open:

- what the stable identity of an individual summary element should be for future cross-branch alignment

Still not specified:

- claim-based identity versus
- projection-argument-id identity versus
- some later explicit summary-element ID

Why it matters:

- future caching, journaling, and policy layers may need element-level alignment, not only whole-summary equality

### 2. Provenance preservation boundary

Claim-level provenance is now explicitly preserved in the summary surface via `claim_provenance`.

Still not specified:

- which provenance fields are mandatory versus best-effort
- whether justification/rule provenance must survive the first summary slice
- whether stance provenance beyond the current row attributes must become explicit later

Why it matters:

- later explanation and policy layers need to know exactly what provenance survives the structured boundary

### 3. Known non-attack versus ignorance

This is still the sharpest remaining semantic gap.

The current summary slice honestly preserves:

- explicit attack information via the projected framework
- branch-local scope via filtered stance rows

But it still does **not** expose, at the summary surface:

- determined non-attack
- true ignorance
- out-of-scope relation

as distinct first-class structured-summary states.

Why it matters:

- the abstract merge kernel depends on preserving `attack / non-attack / ignorance` honestly
- right now that distinction is clearer in the merge kernel than in the structured-summary contract itself

### 4. Lossiness boundary

This is still not explicit enough in the control docs.

The current first slice appears to collapse or omit at least:

- subargument identity
- justification identity
- preference metadata
- explicit support metadata beyond what survives the ASPIC projection

Why it matters:

- without an explicit lossiness statement, later structured-policy work can overclaim what this summary preserves

### 5. Reuse and stability

Top-level stability is now meaningfully specified by tests:

- repeated builds are stable
- same-content cross-branch summaries match
- out-of-scope stances and order-only differences do not change identity

What remains open is narrower:

- whether later structured-summary artifacts beyond the current first slice must be byte-for-byte stable
- what the stability contract should be for richer summary elements, not just the current top-level summary object

---

## Remaining Documentation/Control Tasks

1. state explicitly that the current structured summary is a lossy first slice
2. document exactly which provenance fields are guaranteed today
3. document that known non-attack versus ignorance is still not first-class at the structured-summary boundary
4. decide whether future policy layers need element-level summary identity, not just whole-summary identity

---

## Recommendation

Phase 6.3 should now be treated as:

- partially implemented in code/tests
- still incomplete in its explicit lossiness and non-attack/ignorance contract

So the next honest closeout step is not more generic merge work. It is to write down:

- what this summary preserves
- what it intentionally collapses
- what remains deferred to later structured-policy or structured-inquiry phases
