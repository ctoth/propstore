# IC Merge

There are two different merge surfaces, and they are intentionally named
differently.

## Model-Theoretic IC Merge

`belief_set.ic_merge` is the Konieczny-Pino-Pérez belief-set merge surface in
the external `formal-belief-set` dependency.
`merge_belief_profile(alphabet, profile, mu, operator=...)` enumerates all
`mu-models` over the finite propositional signature, scores each candidate world
by distance to each profile formula, and returns the winning worlds as a
`belief_set.BeliefSet`.

Available operators:

- `ICMergeOperator.SIGMA`: minimizes the sum of Hamming distances to the input
  bases.
- `ICMergeOperator.GMAX`: minimizes the sorted distance vector lexicographically
  after descending sort.

The important architectural point is candidate space: this operator considers
all worlds satisfying `mu`, including worlds not directly observed in any input
source. That is the model-theoretic IC-merge behavior required by
Konieczny-Pino-Pérez 2002.

The property gate lives in the external package test suite and checks the
finite IC postulates exercised by the current implementation.

## Assignment Selection

`propstore.world.assignment_selection_merge` is not the literature IC-merge
operator. It is an assignment-selection operator over observed typed values in
active claims. It enumerates `product(observed_values_per_concept)` and filters
those assignments through range/category/CEL integrity constraints.

That operator is useful for rendering a conflicted typed value from branch
sources, but it cannot invent an admissible unobserved value. For example, if
sources only observed `x=5` and `x=10`, assignment selection will not return
`x=7` even when the integrity constraint permits it. The model-theoretic
belief-set merge can choose any `mu-model`.

The assignment-selection gate is
`tests/test_assignment_selection_merge.py` plus resolution integration tests in
`tests/test_resolution_helpers.py`.

## Choosing The Surface

Use `belief_set.ic_merge` for formal IC merge over formulas and belief bases.
Use `propstore.world.assignment_selection_merge` only for
render-time selection among observed typed assignments.

## Not Implemented

These merge constructions are not present in `belief_set.ic_merge`:

- Konieczny-Pino-Pérez 2002 `Delta^Max`, introduced alongside the arbitration
  results on p.790. The current `GMAX` operator is the lexicographic max-vector
  operator used for Arb coverage; it is not the separate `Delta^Max`
  construction.
- Coste-Marquis 2007 abstract-argumentation merging. That is an AF-level merge
  problem, not a propositional belief-set merge problem, and belongs to the
  upstream argumentation work tracked by WS-O-arg.
- Any observed-assignment merge that invents or repairs typed source values.
  `propstore.world.assignment_selection_merge` only selects among observed
  assignments and is deliberately separate from IC model enumeration.

The propositional missing merge work rolls into REMEDIATION-PLAN T6.5. The
argumentation merge work is owned by WS-O-arg.
