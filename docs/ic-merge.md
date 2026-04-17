# IC Merge

There are two different merge surfaces, and they are intentionally named
differently.

## Model-Theoretic IC Merge

`propstore.belief_set.ic_merge` is the Konieczny-Pino Perez belief-set merge
surface. `merge_belief_profile(alphabet, profile, mu, operator=...)` enumerates
all `mu-models` over the finite propositional signature, scores each candidate
world by distance to each profile formula, and returns the winning worlds as a
`BeliefSet`.

Available operators:

- `ICMergeOperator.SIGMA`: minimizes the sum of Hamming distances to the input
  bases.
- `ICMergeOperator.GMAX`: minimizes the sorted distance vector lexicographically
  after descending sort.

The important architectural point is candidate space: this operator considers
all worlds satisfying `mu`, including worlds not directly observed in any input
source. That is the model-theoretic IC-merge behavior required by
Konieczny-Pino Perez 2002.

The property gate is `tests/test_belief_set_postulates.py`, which checks the
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

Use `propstore.belief_set.ic_merge` for formal IC merge over formulas and
belief bases. Use `propstore.world.assignment_selection_merge` only for
render-time selection among observed typed assignments.
