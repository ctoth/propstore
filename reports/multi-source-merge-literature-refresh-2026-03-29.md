# Multi-Source Merge Literature Refresh

**Date:** 2026-03-29
**Purpose:** re-check the merge completion plan against the local merge, revision, and structured-argumentation literature before further implementation

---

## Verdict

The current merge direction is principled.

The literature supports four hard conclusions:

1. **Phase 6 merge should stay structural.**
   - Konieczny 2002 defines merge over admissible interpretations under hard constraints.
   - Coste-Marquis 2007 lifts that to argumentation by merging `attack / non-attack / ignorance`.
   - The right kernel object is still the partial framework, not a preference-weighted or queryable-enriched substitute.

2. **Merge should stay over attacks, not defeats.**
   - Coste-Marquis 2007 merges AF structure.
   - Prakken 2010 and Modgil 2018 make clear that defeat is downstream of attack plus preferences.
   - So source trust and preference policy should not be baked into the Phase 6 merge kernel.

3. **Structured incomplete-information reasoning is not the same task as merge completion.**
   - Odekerken 2023/2025 is about future information in ASPIC+ theories, grounded justification status, stability, and relevance.
   - That is valuable for later inquiry and investigation layers, but it is not a reason to widen the merge kernel now.
   - The structured incomplete-information line belongs downstream of merge and alongside revision, not inside Phase 6 consolidation.

4. **The next production task is canonical surface hardening, not bridge deletion for its own sake.**
   - Current code inspection shows `branch_reasoning.py` is still a bridge seam, but not a live production bottleneck.
   - The live public surfaces are still the canonical inspect/commit paths.
   - So the next coding slice should tighten those surfaces first, then return to bridge reduction only if a real consumer still depends on it.

---

## Paper-Level Judgments

### Konieczny & Pino Perez 2002

Best current use:

- hard constraint vocabulary
- operator-family distinctions
- reminder that `mu` is a real admissibility filter, not a local tie-breaker

Implementation consequence:

- keep the merge kernel honest about admissibility and operator meaning
- do not cite IC postulates for weaker scalar or bucket wrappers

### Coste-Marquis et al. 2007

Best current use:

- direct formal model for multi-source AF merge
- consensual expansion
- completion-based queries
- `sum` / `max` / `leximax` distinctions

Implementation consequence:

- preserve the partial framework as canonical
- preserve `attack / non-attack / ignorance`
- keep query semantics over completions explicit

### Prakken 2010 and Modgil 2018

Best current use:

- structured-theory side of the boundary
- attack, defeat, preferences, and rationality conditions

Implementation consequence:

- structured projection should compile into the merge kernel
- defeat should remain a downstream reasoning stage
- source preference should enter later as policy or post-merge defeat handling

### Odekerken 2023 / 2025

Best current use:

- later inquiry layer for stability/relevance over incomplete ASPIC+ theories
- warning against pretending abstract-level approximations preserve the structured notions automatically

Implementation consequence:

- do not drag queryables, `j`-stability, or `j`-relevance into Phase 6 merge completion
- keep those as later world/query/investigation capabilities built on top of the merge and revision kernels

---

## What Changes In The Plan

The literature does **not** force a redesign of the merge proposal.

It does force three clarifications:

1. **Phase 6 is not a generic "incomplete argumentation" phase.**
   It is specifically merge-kernel completion and consolidation.

2. **Phase 6.5 policy readiness should assume source preference enters after merge unless later work proves otherwise.**
   That should be the default control-surface assumption.

3. **The next coding slice should target the canonical inspect/commit path and its tests.**
   Bridge narrowing remains later unless a production dependency appears.

---

## Recommended Next Slice

Target Phase 6.1 directly on the active public surfaces:

- `propstore/repo/merge_commit.py`
- `propstore/cli/merge_cmds.py`
- `tests/test_merge_classifier.py`
- `tests/test_merge_cli.py`

Questions to pin with tests:

1. Does the storage merge commit remain a deterministic projection from `RepoMergeFramework.arguments`?
2. Are inspect and commit still clearly separated as:
   - formal merge query surface
   - provenance/storage commit surface
3. Do the active public paths stay on the canonical merge object without depending on `branch_reasoning.py`?

Only after that slice should Phase 6 return to bridge minimization.

---

## Bottom Line

The merge plan is still right.

What needed correction was not the architecture but the temptation to widen Phase 6 into structured incomplete-information inquiry. The literature says not to do that. The next correct move is to finish the canonical merge surface cleanly, keep policy downstream, and leave structured inquiry machinery for later phases.
