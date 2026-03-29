# IC-Merge `mu` Design

Date: 2026-03-29

Status: design only for issue 9 in [review-remediation-plan-2026-03-29.md](/C:/Users/Q/code/propstore/plans/review-remediation-plan-2026-03-29.md)

## Verdict

The current `propstore/repo/ic_merge.py` shape is not enough for literature-faithful
IC merging. Konieczny and Pino Perez merge a belief multiset `Psi` into a set of
models:

`mod(Delta_mu(Psi)) = min(mod(mu), <=_Psi)`

So `mu` is not a tie-breaker and not a local value validator. It is a hard filter on
the admissible merged interpretations before Sigma, Max, or GMax choose minimal
elements.

The current scalar API:

- takes one concept-local profile `dict[str, Any]`
- scores candidate values only
- returns one winning value

That can support a useful adaptation, but by itself it cannot justify the full
IC0-IC8 claims from the paper.

## What The Literature Requires

The semantic object being merged is an interpretation or model, not an isolated
scalar. In propstore terms, the closest honest analogue is a merged assignment:

- `concept_id -> chosen value`

over one or more conflicted concepts.

Under that reading:

- each source contributes a partial assignment or belief base
- `mu` constrains the whole merged assignment
- Sigma/Max/GMax compare admissible assignments by distance to each source

This matters because the interesting constraints are often cross-concept:

- category/value compatibility
- form/range/unit admissibility
- equation or parameterization consistency
- branch- or policy-level hard requirements

A per-concept predicate can only say "this value is allowed for this concept". It
cannot say "these two chosen values are jointly allowed".

## Right Target For Propstore

The principled target is a world-level IC-merge problem with four typed pieces:

1. Source assignments
   Each source is one branch/world/profile contributing values for a set of
   concepts.

2. Candidate domain
   The discrete candidate assignments that may be selected. For the first honest
   version, this should be the Cartesian product of source-observed values for the
   concepts being merged.

3. Integrity constraint `mu`
   A hard predicate on the whole candidate assignment.

4. Aggregation operator
   Sigma, Max, or GMax over assignment-to-source distance vectors.

That yields:

- assignment-level correctness claims for constrained merging
- a clean place to use existing branch filters and branch weights
- a natural future path to cross-concept constraints via CEL/Z3

## Smallest Honest Architecture

We should separate the mathematical kernels from the production entrypoint.

### A. Kernel Layer

Keep `sigma_merge`, `max_merge`, and `gmax_merge` as local distance kernels, but stop
claiming full IC postulates for the unconstrained scalar wrappers.

Add typed structures in `propstore/world/types.py`:

- `IntegrityConstraintKind(StrEnum)`
  - `FORM`
  - `CATEGORY`
  - `RANGE`
  - `CEL`
  - `CUSTOM`
- `IntegrityConstraint`
  - `kind`
  - `concept_ids`
  - `cel`
  - `metadata`
- `MergeSource`
  - `source_id`
  - `assignment`
  - `weight`
- `MergeAssignment`
  - `values`
- `ICMergeProblem`
  - `concept_ids`
  - `sources`
  - `constraints`
  - `operator`
- `ICMergeResult`
  - `winners`
  - `scores`
  - `admissible_count`
  - `reason`

Add assignment-level functions in `propstore/repo/ic_merge.py`:

- `enumerate_candidate_assignments(problem)`
- `assignment_satisfies_mu(problem, assignment)`
- `assignment_distance(assignment, source)`
- `solve_ic_merge(problem)`

The existing scalar helpers can delegate to the assignment solver for the
single-concept case.

### B. Constraint Layer

The first real `mu` should come from facts the repo already treats as hard:

- category value sets from `concept.form_parameters.values`
- category extensibility when it is `false`
- numeric `range_min` / `range_max`
- unit/form admissibility where the concept form gives a canonical domain

The next layer should be optional CEL constraints over multiple concepts, evaluated
against a candidate merged assignment. The repo already has the right ingredients:

- concept registry data in `WorldModel`
- CEL parsing
- `Z3ConditionSolver`

So the honest medium-term target is:

- atomic form constraints generated automatically
- optional explicit `mu` as CEL over canonical concept names

### C. Production Entry Point

`ResolutionStrategy.IC_MERGE` currently exists in `propstore/world/types.py` but is
not implemented in `propstore/world/resolution.py`.

The narrowest honest integration is:

1. Implement `ResolutionStrategy.IC_MERGE` for the single-concept case first.
2. Build an `ICMergeProblem` from the active claims for that concept.
3. Derive automatic concept-local constraints from form metadata.
4. Solve the constrained assignment problem.
5. Return a `ResolvedResult` only if exactly one active claim matches the winning
   merged value.

If multiple active claims map to the same winning value, return `resolved` with a
deterministic chosen claim only if the policy explicitly allows that tie-break. If
the merged value is admissible but not uniquely represented by one active claim,
the safer result is `conflicted` plus an explanation.

This keeps the current world-resolution surface honest while leaving room for a
future world-level merge API that returns a merged assignment rather than one claim.

Concept-local `mu` must not ship as a direct scalar patch to `ic_merge(profile)`.
If we ship it at all, it should ship only through `ICMergeProblem` over full
assignments, with the single-concept case represented as the degenerate
`len(concept_ids) == 1` case. Otherwise the code will look constrained while still
hiding the wrong semantic object.

## What We Must Not Claim

Until the assignment-level solver exists, we must not keep claiming:

- Sigma satisfies IC0-IC8 + Maj in the current scalar wrapper
- Max/GMax satisfy their paper-level postulate packages in the current wrapper

What we can claim after the first implementation:

- single-concept constrained adaptation of Sigma/Max/GMax
- real enforcement of concept-local `mu`
- no claim yet of full literature-faithful global IC semantics

Once assignment-level `mu` exists and the production entrypoint can merge jointly
over multiple concepts, then the stronger claims become defensible.

## Recommended Build Order

1. Narrow the current docstrings and tests so they stop overclaiming.
2. Add the typed `IntegrityConstraint` / `ICMergeProblem` / `ICMergeResult` layer.
3. Implement automatic concept-local `mu` from form metadata only through that
   assignment-level abstraction.
4. Implement `ResolutionStrategy.IC_MERGE` for one concept through the new solver.
5. Add optional CEL constraints over merged assignments.
6. Add a world-level API for multi-concept constrained merge.

Steps 2 through 4 should be treated as one architecture slice, not three loosely
related tweaks. Shipping concept-local `mu` or `ResolutionStrategy.IC_MERGE`
without the assignment-level problem type would create a worse honesty gap than the
current unconstrained code.

## Main Risk

The main failure mode is faking `mu` as a per-concept predicate and then talking
about Konieczny-style IC merging as if nothing changed.

That would preserve the same core mismatch:

- local picks can be individually admissible but jointly impossible
- IC0/IC2/IC7/IC8 become false in the intended global sense
- the code still overstates its literature faithfulness

So the right design is:

- assignment-level target
- concept-local first implementation only if it is explicitly labeled as an
  adaptation and wired through the same future assignment-level abstractions
