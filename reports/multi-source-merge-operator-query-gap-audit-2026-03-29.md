# Multi-Source Merge Operator/Query Gap Audit

**Date:** 2026-03-29
**Purpose:** compare current kernel/operator/query tests to Phase 6.2 requirements before coding

---

## Verdict

The operator/query layer is already meaningfully tested, but it is not yet fully pinned to the Phase 6.2 checklist.

What is already covered well:

- PAF partition and completion semantics
- distance identity/symmetry/triangle inequality
- unanimity and profile-order invariance for some merge operators
- basic majority behavior for `sum`
- basic `leximax` refinement over `max`
- basic skeptical/credulous completion-query behavior
- one monotonicity property when ignorance is fixed

What is still missing or too weak:

- explicit completion-soundness phrasing at the query layer beyond grounded examples
- concordance-collapse tests across more than one operator
- sharper distinctions among `sum`, `max`, and `leximax` on tiny exact profiles
- explicit “query helpers only accept canonical kernel semantics” coverage
- broader literature-style exact-profile regressions instead of only generic properties

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

- enough to trust the implementation direction
- not enough yet to say the operator family is fully pinned down by tests

### `tests/test_paf_queries.py`

Covered:

- grounded skeptical/credulous behavior over completions
- single-completion collapse to ordinary Dung query
- one ignorance-fixation monotonicity property

Assessment:

- good first slice
- still too grounded-centric and too example-centric for the full checklist

---

## Missing Assertions Relative To The Checklist

### Operator layer

Still worth adding:

1. concordant profiles yield a unique merge result across:
   - `sum`
   - `max`
   - `leximax`
2. exact tiny profiles where:
   - `sum` prefers a different result set than `max`
   - `leximax` strictly refines a multi-result `max` set
3. expansion stability when all sources already share the full universe

### Query layer

Still worth adding:

1. skeptical/credulous checks under at least one non-grounded semantics case
2. explicit equivalence between brute-force completion evaluation and helper output on tiny profiles
3. clearer fixation tests for both:
   - fixing ignorance to attack
   - fixing ignorance to non-attack

### Integration discipline

Still worth adding:

1. tests that the query helpers operate on `PartialArgumentationFramework`, not accidental bridge objects
2. exact-profile regressions that can serve as future operator-policy comparison anchors

---

## Recommended Next RED Targets

1. `tests/test_paf_merge.py`
   - add tiny exact profiles distinguishing `sum`, `max`, `leximax`
2. `tests/test_paf_queries.py`
   - add brute-force helper equivalence checks on tiny profiles
3. optionally `tests/test_paf_core.py`
   - only if a missing algebraic kernel property is discovered while writing the above

---

## Recommendation

Treat Phase 6.2 as a test-hardening and exact-regression phase first, not an implementation-invention phase.

The likely best outcome is:

- more RED tests than code changes
- maybe no kernel code changes at all if the current implementation already satisfies the stronger exact regressions
