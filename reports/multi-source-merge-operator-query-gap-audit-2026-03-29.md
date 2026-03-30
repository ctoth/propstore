# Multi-Source Merge Operator/Query Gap Audit

**Date:** 2026-03-29
**Purpose:** compare current kernel/operator/query tests to Phase 6.2 requirements before coding

---

## Verdict

This audit started as a pre-coding gap memo. After the Phase 6.2 slice landed, the main operator/query hardening work is now implemented.

Current state:

- the operator/query layer is tightly pinned by exact tests
- the Phase 6.2 control surface should now be read as implemented rather than pending
- any remaining work here is documentation/status reconciliation, not missing kernel semantics

What is already covered well:

- PAF partition and completion semantics
- distance identity/symmetry/triangle inequality
- unanimity and profile-order invariance for some merge operators
- basic majority behavior for `sum`
- basic `leximax` refinement over `max`
- basic skeptical/credulous completion-query behavior
- one monotonicity property when ignorance is fixed

What was missing or too weak at audit time:

- explicit completion-soundness phrasing at the query layer beyond grounded examples
- concordance-collapse tests across more than one operator
- sharper distinctions among `sum`, `max`, and `leximax` on tiny exact profiles
- broader literature-style exact-profile regressions instead of only generic properties

What is now covered after the slice:

- concordant unique results across `sum`, `max`, and `leximax`
- exact tiny regressions distinguishing `sum`, `max`, and `leximax`
- non-grounded helper checks
- brute-force equivalence checks for skeptical/credulous helpers
- two-way ignorance fixation checks

---

## Current Coverage Map

### `tests/test_paf_core.py`

Covered:

- partition of `attacks / ignorance / non_attacks`
- rejection of non-partitions
- completion soundness
- completion exactness and count
- distance identity
- distance symmetry
- triangle inequality

Assessment:

- strong baseline
- no urgent kernel redesign work is implied

### `tests/test_paf_merge.py`

Covered:

- consensual expansion behavior for out-of-scope pairs
- `sum` unanimity
- `sum` profile-order invariance
- `sum` majority-profile behavior on a tiny shared universe
- `max` profile-order invariance
- `leximax` subset-of-`max` refinement

Assessment:

- operator-family behavior is now meaningfully pinned by exact regressions
- future changes here should be judged against the landed exact cases, not by reopening the basic kernel story

### `tests/test_paf_queries.py`

Covered:

- grounded skeptical/credulous behavior over completions
- single-completion collapse to ordinary Dung query
- one ignorance-fixation monotonicity property

Assessment:

- helper semantics are now explicit enough for the current merge phase
- future additions here should be new operator families or policy overlays, not re-deriving the current helper contract

---

## Assertions That The Checklist Required And Are Now Landed

### Operator layer

Landed:

1. concordant profiles yield a unique merge result across:
   - `sum`
   - `max`
   - `leximax`
2. exact tiny profiles where:
   - `sum` prefers a different result set than `max`
   - `leximax` strictly refines a multi-result `max` set
3. expansion stability when all sources already share the full universe

### Query layer

Landed:

1. skeptical/credulous checks under at least one non-grounded semantics case
2. explicit equivalence between brute-force completion evaluation and helper output on tiny profiles
3. clearer fixation tests for both:
   - fixing ignorance to attack
   - fixing ignorance to non-attack

### Integration discipline

Still worth considering later:

1. exact-profile regressions that serve as future operator-policy comparison anchors beyond the current operator family
2. additional tests only if a new merge-policy layer widens the query surface

---

## Historical RED Targets

1. `tests/test_paf_merge.py`
   - add tiny exact profiles distinguishing `sum`, `max`, `leximax`
2. `tests/test_paf_queries.py`
   - add brute-force helper equivalence checks on tiny profiles
3. optionally `tests/test_paf_core.py`
   - only if a missing algebraic kernel property is discovered while writing the above

---

## Recommendation

Treat this memo as satisfied by the landed Phase 6.2 slice.

The main follow-up is:

- reconcile status/control docs
- do not reopen the kernel/operator/query layer unless a new operator family or policy layer requires it
