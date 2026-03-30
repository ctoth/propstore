# Multi-Source Merge Policy Readiness

**Date:** 2026-03-30
**Purpose:** define where policy belongs after the merge-kernel consolidation work, and record the minimum metadata the current merge path must preserve for later policy objects

---

## Verdict

The merge kernel should remain structural.

Current literature-backed default still stands:

- keep source preference out of the merge kernel
- keep `attack / non-attack / ignorance` structural
- apply source-aware weighting, trust, or admissibility later as:
  - post-merge defeat policy
  - explanation policy
  - or a higher-level selection/governance layer

The codebase is now in a good enough state to make that insertion point explicit.

---

## Where Policy Does And Does Not Belong

### Not in the merge kernel

The following should remain policy-free:

- `propstore/repo/merge_framework.py`
- `propstore/repo/paf_merge.py`
- `propstore/repo/paf_queries.py`
- the repo merge object emitted by `propstore/repo/merge_classifier.py`

Reason:

- this layer is about structural disagreement over relations
- it should not silently decide which branch/source deserves to win

### Allowed downstream policy insertion points

Policy may enter in three places:

1. **Post-merge defeat / argument selection**
   - after the merged partial framework exists
   - especially for structured or preference-aware consumers

2. **Explanation and reporting**
   - e.g. source weighting in explanations
   - branch trust overlays in decision support

3. **Workflow/governance layer**
   - review gates
   - branch approval rules
   - policy profiles for different operational contexts

---

## Current Implicit Defaults That Must Eventually Become Policy

These are not all bad. But they are currently hard-coded choices rather than explicit policy objects.

### Merge-query/report defaults

- `pks merge inspect` defaults to `grounded` semantics in `propstore/cli/merge_cmds.py`
- structured merge candidates default to `sum` in `propstore/repo/structured_merge.py`

These are fine as v1 defaults, but later policy/governance work should make them inspectable and replayable.

### Storage projection defaults

- `pks merge commit` defaults `target_branch` to `master` in `propstore/cli/merge_cmds.py`
- `create_merge_commit()` preserves non-claim files with a left-over-right overwrite rule in `propstore/repo/merge_commit.py`

This is operational policy, not merge-kernel semantics.

It should remain separate from the formal merge operator and be surfaced honestly as storage-merge policy.

### Structured-summary defaults

The current branch-local structured summary:

- preserves `claim_ids`
- preserves normalized `claim_provenance`
- preserves in-scope canonicalized `stance_rows`
- computes a stable `content_signature`

But it currently drops or abstracts over:

- subargument identity
- justification identity
- preference metadata
- explicit known-non-attack versus ignorance at the summary surface

That is acceptable for the current slice, but later structured-policy work must not assume those details survived.

---

## Minimum Metadata The Merge Path Must Preserve

The current merge stack already preserves enough metadata to support a later policy layer, with one notable future gap.

### Must preserve now

These are required and already present or should remain present:

- branch pair identity:
  - `branch_a`
  - `branch_b`
- per-emitted-argument branch provenance:
  - `branch_origins`
  - `provenance.branch_origin` where disambiguated alternatives are emitted
- semantic alignment metadata:
  - `canonical_claim_id`
  - `concept_id`
- structured-summary provenance:
  - `claim_provenance`
  - `content_signature`
- merge storage manifest provenance:
  - `merge/manifest.yaml`
  - branch names
  - emitted argument identities

### Recommended future preservation upgrade

The next policy/governance layer will likely benefit from preserving:

- source branch tip commit SHAs at merge time
- policy profile identifiers when policy becomes first-class

These are not required to keep the kernel honest today, but they are the clean next metadata upgrade for auditability.

---

## Recommended Policy Boundary

The clean model is:

1. build branch-local summaries
2. build the merged partial framework
3. query the merged framework structurally
4. only then apply any source-trust, preference, or governance overlay

That keeps these separations intact:

- merge is not revision
- storage merge is not the merge operator
- source preference is not hidden inside structural merge

---

## Immediate Consequence For The Roadmap

Phase 6 should stop at:

- structural merge completion
- structured-summary contract honesty
- explicit policy insertion points

Phase 8 should own:

- `MergePolicy`
- trust/source profiles
- admissibility/governance objects
- policy-aware replay and auditing

---

## Recommendation

Treat merge policy readiness as complete for Phase 6 once the docs/checklist say clearly:

- the kernel is structural
- current defaults are defaults, not theory
- preserved metadata is sufficient for later policy objects
- future source preference belongs downstream of merge by default
