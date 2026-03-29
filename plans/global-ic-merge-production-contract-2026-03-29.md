# Global IC-Merge Production Contract

Date: 2026-03-29

Goal: formalize what one production `IC_MERGE` call means before wiring phase 5.

Status: design contract for phase 5 of
`plans/global-ic-merge-and-cleanup-plan-2026-03-29.md`

## Verdict

Production `IC_MERGE` should merge one globally relevant assignment, not one
target concept in isolation.

The merged object is:

- one assignment over the relevant concept domain for the current bound world

The target concept is read out from that merged assignment after the merge, not
used to define a smaller merge problem.

## Merge Problem Boundary

For one production merge call, define the concept domain as:

1. every concept with at least one active claim surviving the current bound world
   and branch filter
2. plus every concept referenced by explicit integrity constraints `mu`
3. plus any target concepts that must be reported even if they have no explicit
   active claim in the filtered set

This is the production meaning of "all concepts" for merge:

- all concepts relevant to the current merge instance
- not only the caller's target concept
- not every concept in the repository regardless of participation

## Source Construction

Each source corresponds to one branch-level or claim-level origin in the current
active world.

The default source key is:

- branch ID when present
- otherwise claim ID as a singleton source

Each source contributes one partial assignment:

- `concept_id -> value` for every active claim from that source

If a source has multiple active claims for the same concept, phase 5 should not
silently pick one. The safe behaviors are:

1. fail the merge problem construction explicitly, or
2. represent that source as multiple alternative assignments in a later phase

For phase 5, explicit failure is the safer contract.

## Constraint Construction

The global `mu` for one production merge problem is the conjunction of:

1. automatic concept-local constraints derived from concept metadata for every
   concept in the domain
2. explicit cross-concept `CUSTOM` constraints supplied by policy or caller
3. explicit CEL constraints supplied by policy or caller

All of these are constraints over the same merged assignment.

There must not be a separate "target-only constraint path".

## Branch Filters And Weights

Branch filtering acts only at source selection time:

- remove filtered-out sources before building the source multiset

Branch weights act only at source scoring time:

- they modify source contribution inside the merge operator

Neither should alter constraints or post-hoc result interpretation.

## Solving Contract

Production `IC_MERGE` must build exactly one `ICMergeProblem` and solve it once.

The caller-facing target concept is handled by projection after solving:

1. solve the global merge problem
2. inspect the winning merged assignment(s)
3. project the requested target concept value(s) from those winners

This preserves the literature direction:

- merge the world, then query the target

not:

- merge only the target and ignore the rest of the active assignment

## Result Interpretation

For a caller asking for one target concept:

1. If there are no winning assignments, return unresolved/conflicted with the
   merge reason.
2. If winning assignments disagree on the target concept value, return conflict.
3. If winning assignments agree on the target concept value, try to map that
   value back to active claims for that concept.
4. If exactly one active claim realizes that target value, resolve to that claim.
5. If multiple active claims realize that target value, return ambiguity rather
   than pretending uniqueness.
6. If no active claim realizes that target value exactly, return conflict with a
   reason explaining that the merged assignment has no unique realizing claim.

This keeps production output honest even when the merged assignment is well
defined but the claim surface is not.

## Phase-5 RED Tests Implied By This Contract

1. A cross-concept `mu` over a non-target concept can change the resolved output
   for the target concept.
2. Branch filtering changes the merge result only through source removal during
   problem construction.
3. A branch with active claims over multiple concepts contributes one partial
   assignment, not separate target-only fragments.
4. Multiple active claims for one source and one concept fail explicitly in
   phase 5.
5. Global winners that agree on the target value but map to multiple active
   claims do not produce a fake unique winner.

## Non-Goals For Phase 5

Phase 5 does not yet need:

- alternative-assignment expansion for one source with multiple values per concept
- worldline-wide multi-target merged reporting
- cleanup of legacy scalar helper surfaces

Those belong to later phases.
