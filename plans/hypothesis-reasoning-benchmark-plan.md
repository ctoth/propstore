# Hypothesis-First Reasoning Benchmark Plan

Date: 2026-03-25
Status: Planned

## Goal

Make Hypothesis the primary adversarial benchmark harness for `propstore` reasoning.

The point is not to collect more canned examples. The point is to state the semantic laws the system claims to satisfy, generate many small hostile worlds, and prove those laws hold across:

- Dung semantics
- claim-graph argumentation
- structured projection
- ATMS labels and nogoods
- PrAF acceptance
- worldline capture and explanation surfaces

## Why This Should Be The Benchmark

Static benchmark cases are useful for regressions, but they are weak against reasoning bugs that only appear under odd graph shapes, irrelevant-context pollution, support/attack interaction, or edge-case uncertainty.

Hypothesis is already one of the repo's strengths. The next step is to treat it as a benchmark artifact instead of a scattered testing technique.

This benchmark should answer questions like:

- does the reasoner preserve the formal laws it claims to implement?
- do equivalent presentations produce equivalent outcomes?
- do irrelevant facts stay irrelevant?
- do probabilistic and deterministic paths agree when uncertainty collapses?
- do explanations correspond to the real semantic witness, not a post hoc story?

## Constraints

- Prefer literature-backed invariants over generic fuzzing.
- Keep generators small enough to shrink well and run in CI.
- Separate exact semantic laws from approximate statistical checks.
- Reuse existing helpers and strategies where possible.
- Add new property suites incrementally; do not land an unbounded flaky mega-suite.
- Every slice needs a targeted `pytest` command that can act as an executable gate.

## Non-Goals

- replacing all concrete regression tests
- proving the whole system correct
- generating large realistic paper corpora
- benchmarking LLM extraction quality
- conflating semantic properties with performance measurements

## Benchmark Structure

The benchmark should be split into six property families.

### 1. Core semantic laws

These are direct claims about the formal engines.

- grounded extension is unique
- every returned extension is conflict-free
- every preferred or stable extension is admissible when the semantics require it
- grounded extension is contained in every preferred extension
- Z3-backed Dung agrees with the reference implementation on supported inputs
- exact support labels are order-independent
- nogoods prune exactly the environments they subsume

Primary targets:

- `tests/test_dung.py`
- `tests/test_dung_z3.py`
- `tests/test_atms_engine.py`

### 2. Metamorphic invariants

These assert that semantics survive representation-preserving rewrites.

- renaming claim IDs does not change outcomes up to renaming
- permutation of claim and stance row order does not change outcomes
- adding isolated claims does not perturb unrelated accepted claims
- adding semantically irrelevant contexts does not perturb active results
- duplicating a support path with the same semantics does not invent a new winner
- worldline output is invariant under dependency row order

Primary targets:

- `tests/test_argumentation_integration.py`
- `tests/test_structured_argument.py`
- `tests/test_world_model.py`
- `tests/test_worldline_properties.py`

### 3. Cross-backend agreement

These check collapse conditions and bridge correctness.

- claim-graph and structured projection agree on flat no-subargument cases
- PrAF agrees with deterministic claim-graph when all relevant probabilities collapse to 0 or 1
- worldline argumentation capture matches the backend result already computed by the underlying engine
- exact PrAF and MC PrAF agree within tolerance on small worlds
- unsupported exact-DP cases fall back to the intended exact path rather than silently changing semantics

Primary targets:

- `tests/test_argumentation_integration.py`
- `tests/test_structured_argument.py`
- `tests/test_praf.py`
- `tests/test_praf_integration.py`
- `tests/test_treedecomp.py`

### 4. Explanation obligations

These check that the explanation surface is semantically honest.

- every defeated claim has at least one defeating witness when the backend reports defeat
- every justified claim in grounded semantics is undefeated or defended by the returned witness set
- ATMS `why_out` matches actual missing-support vs nogood-pruned status
- intervention and next-query outputs correspond to a real bounded future that flips status
- worldline argumentation payloads are reconstructible from the backend result they summarize

Primary targets:

- `tests/test_atms_engine.py`
- `tests/test_worldline.py`
- `tests/test_worldline_error_visibility.py`
- `tests/test_worldline_praf.py`

### 5. Context and nonmonotonicity properties

These check the places reasoning systems usually lie.

- narrowing to a disjoint context cannot create a direct contradiction with claims that are inactive there
- adding a defeating claim can retract a previous conclusion
- removing an assumption can restore a previously pruned label
- unrelated assumptions do not alter exact-support results
- context hierarchy changes only affect claims whose visibility depends on that hierarchy

Primary targets:

- `tests/test_contexts.py`
- `tests/test_world_model.py`
- `tests/test_atms_engine.py`

### 6. Probabilistic coherence properties

These check that uncertainty handling is structurally sane.

- all acceptance probabilities stay in `[0, 1]`
- collapse to dogmatic opinions yields deterministic agreement
- increasing support for an unattacked argument does not lower its acceptance probability
- adding a new independent probabilistic component does not change marginals of a disconnected component
- lower bound <= pignistic <= upper bound for reported opinions where that contract exists

Primary targets:

- `tests/test_praf.py`
- `tests/test_praf_integration.py`
- `tests/test_opinion.py`

## Generator Strategy

The generators matter more than the assertions. Bad generators produce noise.

### Small-world first

Default generated worlds should stay small:

- 1 to 8 arguments for AF-level properties
- tiny condition vocabularies
- tiny context hierarchies
- probabilities concentrated on informative edge cases:
  - `0.0`
  - `0.5`
  - `1.0`
  - near-dogmatic values

Small worlds shrink well and are usually enough to falsify semantic bugs.

### Canonical generators to build

- `af_worlds()`
  - arguments
  - attacks
  - optional separate defeats
- `claim_graph_worlds()`
  - claims with strength metadata
  - stance rows
  - optional conflict rows
- `context_worlds()`
  - acyclic context hierarchies
  - exclusions
  - claims with context and CEL conditions
- `atms_worlds()`
  - assumptions
  - claims
  - parameterizations
  - conflict-induced nogoods
- `praf_worlds()`
  - primitive probabilistic arguments
  - primitive probabilistic attacks
  - primitive probabilistic supports
  - collapse-to-deterministic edge cases

### Shrink discipline

Strategies should bias toward:

- sparse graphs over dense graphs
- short CEL expressions over complex ones
- one-step derivations before chains
- exact probabilities before arbitrary floating-point values

This should keep failures interpretable.

## Rollout Plan

### Slice 1: Benchmark harness and inventory

Status: Pending

- create one benchmark-oriented note in `tests/` or `plans/` describing the property families and owning files
- identify and tag existing Hypothesis suites that already act as benchmark coverage
- extract or consolidate shared small-world strategies where duplication is already hurting clarity

Verification:

- `uv run pytest tests/test_dung.py tests/test_dung_z3.py tests/test_world_model.py tests/test_praf.py -q`

### Slice 2: Metamorphic invariants for deterministic argumentation

Status: Pending

- add ID-renaming, permutation, and irrelevant-claim invariants
- extend AF generators so they can cover `attacks != defeats` instead of only pure Dung worlds
- ensure structured projection agrees with claim-graph on flat cases

Verification:

- `uv run pytest tests/test_dung.py tests/test_dung_z3.py tests/test_argumentation_integration.py tests/test_structured_argument.py -q`

### Slice 3: Context and ATMS adversarial properties

Status: Pending

- add properties around irrelevant assumptions, nogood pruning, and bounded future witnesses
- add metamorphic tests for context hierarchy perturbations
- add explanation-obligation tests for `why_out`, `stability`, and `next-query`

Verification:

- `uv run pytest tests/test_contexts.py tests/test_world_model.py tests/test_atms_engine.py -q`

### Slice 4: Probabilistic collapse and coherence

Status: Pending

- add collapse-to-deterministic properties for PrAF
- add disconnected-component invariants
- add exact-vs-MC agreement on small generated worlds
- keep tolerance-based assertions explicit and narrow

Verification:

- `uv run pytest tests/test_praf.py tests/test_praf_integration.py tests/test_treedecomp.py -q`

### Slice 5: Worldline and explanation honesty

Status: Pending

- add properties that reconstruct worldline argumentation payloads from the underlying backend output
- assert that reported witnesses really witness the claimed status change
- assert dependency lists are sufficient to recompute the same semantic result on regenerated small worlds where feasible

Verification:

- `uv run pytest tests/test_worldline.py tests/test_worldline_praf.py tests/test_worldline_properties.py tests/test_worldline_error_visibility.py -q`

### Slice 6: CI benchmark gate

Status: Pending

- define a bounded benchmark subset that is stable enough for normal CI
- keep slower or statistically heavier suites in a separate optional gate
- record seed/tolerance policy for approximate checks

Verification:

- `uv run pytest tests/test_dung.py tests/test_dung_z3.py tests/test_argumentation_integration.py tests/test_structured_argument.py tests/test_contexts.py tests/test_world_model.py tests/test_atms_engine.py tests/test_praf.py tests/test_praf_integration.py -q`

## Priority Properties

If only a few new properties get written first, they should be these:

1. AF invariance under argument renaming.
2. claim-graph / structured-projection agreement on flat worlds.
3. PrAF collapse to deterministic semantics for dogmatic opinions.
4. ATMS `why_out` honesty: missing support vs nogood-pruned.
5. irrelevant-claim and irrelevant-context non-interference.
6. exact-vs-MC agreement on small PrAF worlds.
7. worldline argumentation payload reconstruction.
8. attack/defeat divergence coverage with generated worlds.

## Success Criteria

This plan is succeeding when:

- the repo has a recognizable Hypothesis benchmark layer instead of isolated property tests
- the important semantic contracts are stated as executable invariants
- generated counterexamples are small enough to debug without archaeology
- cross-backend drift is caught quickly
- explanation surfaces are tested for honesty, not just presence
- a future claim like "our reasoner is principled" can point to executable semantic laws rather than demos

## Progress Log

- 2026-03-25: Plan created.
