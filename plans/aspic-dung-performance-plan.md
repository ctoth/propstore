# ASPIC Dung Performance Plan

Date: 2026-03-26
Status: Planned

## Goal

Reduce the runtime of the ASPIC property suite, especially `tests/test_aspic.py`, without reducing the current Hypothesis example counts.

The primary target is not "make the tests look faster." The target is:

- preserve the current ASPIC and Dung semantics
- keep the 200-example Hypothesis workload intact
- remove avoidable solver and Python overhead
- make future performance work measurable and repeatable

## Current Diagnosis

Based on the current code and local investigation:

- the first round of ASPIC memoization already landed in `propstore/aspic.py`
- the dominant remaining hotspot is `propstore/dung_z3.py`, especially `z3_complete_extensions()`
- the main cost is Python-side Z3 expression construction, not the underlying ASPIC tree machinery
- `build_arguments()` is no longer the first-order bottleneck
- `compute_attacks()` is secondary but not dominant

Relevant evidence:

- `notes/aspic-perf-investigation.md`
- `notes/aspic-perf-fix.md`
- `propstore/dung_z3.py`
- `propstore/dung.py`
- `tests/test_aspic.py`
- `tests/test_dung.py`
- `tests/test_dung_z3.py`

## Constraints

- Do not lower `max_examples=200` in the ASPIC Hypothesis tests as a shortcut.
- Preserve semantic behavior unless a failing test proves the current behavior is wrong.
- Make each optimization land behind characterization tests first.
- Prefer structural or semantic performance tests over brittle wall-clock assertions.
- Do not revert unrelated worktree changes.
- Keep benchmark timing checks outside the correctness gate unless the assertion is extremely robust.

## Non-Goals

- rewriting ASPIC semantics around a new formalism in one pass
- replacing Hypothesis with smaller smoke tests
- introducing nondeterministic caching that can change solver results
- solving all future argumentation-performance problems in this plan

## Guiding Principle

This work should follow strict TDD:

1. Add characterization tests for the existing semantics.
2. Add narrow structural tests for the intended optimization seam.
3. Implement the minimum change for one slice.
4. Prove correctness with targeted regression.
5. Run the ASPIC benchmark command and record the duration change.

Performance is important, but semantic equivalence is the gate.

## Baseline Commands

Correctness gates:

- `uv run pytest tests/test_dung.py tests/test_dung_z3.py -q`
- `uv run pytest tests/test_aspic.py -q`

Benchmark checkpoints:

- `uv run pytest tests/test_aspic.py -q --durations=20`
- `uv run pytest tests/test_aspic.py -q -k "RationalityPostulates" --durations=20`

Broader reasoning regression:

- `uv run pytest tests/test_dung.py tests/test_dung_z3.py tests/test_argumentation_integration.py tests/test_structured_argument.py tests/test_praf.py tests/test_praf_integration.py tests/test_aspic.py -q`

## Work Plan

### Slice 0: Baseline and Characterization

Status: Pending

Purpose:

- freeze the current semantic contract before optimization
- capture the current timing surface for later comparison

TDD tasks:

- confirm `tests/test_dung.py`, `tests/test_dung_z3.py`, and `tests/test_aspic.py` are the minimal semantic gate for this work
- add any missing tests that pin:
  - complete extension equivalence between brute-force and Z3 on small AFs
  - attack/defeat semantics when `attacks != defeats`
  - ASPIC rationality-postulate behavior that depends on complete extensions
- record local timing from `--durations=20` before changing the solver path

Files:

- `tests/test_dung.py`
- `tests/test_dung_z3.py`
- `tests/test_aspic.py`
- optional note update in `notes/aspic-perf-investigation.md`

Correctness gate:

- `uv run pytest tests/test_dung.py tests/test_dung_z3.py tests/test_aspic.py -q`

Benchmark checkpoint:

- `uv run pytest tests/test_aspic.py -q --durations=20`

### Slice 1: Precompute Dung Graph Adjacency

Status: Pending

Problem:

- `attackers_of()` in `propstore/dung.py` performs a linear scan of the full defeat set on every call
- `propstore/dung_z3.py` repeatedly reconstructs attacker and defender sets from raw defeat pairs

Target change:

- add an internal adjacency/index helper for frameworks:
  - attackers by target
  - defenders by attacked argument
  - optional outgoing defeat relation
- use that helper in both `dung.py` and `dung_z3.py`

TDD tasks:

- add tests proving the adjacency helper matches the current `attackers_of()` semantics
- add tests proving Z3 results remain identical after the helper is used
- if needed, add a structural test that the helper is reused rather than rebuilt repeatedly inside one extension computation

Files:

- `propstore/dung.py`
- `propstore/dung_z3.py`
- `tests/test_dung.py`
- `tests/test_dung_z3.py`

Correctness gate:

- `uv run pytest tests/test_dung.py tests/test_dung_z3.py -q`

Benchmark checkpoint:

- `uv run pytest tests/test_aspic.py -q --durations=20`

### Slice 2: Reuse Defended-Argument Z3 Expressions

Status: Pending

Problem:

- `z3_complete_extensions()` rebuilds defender disjunctions and defended-argument conjunctions repeatedly
- this creates heavy Python-to-Z3 FFI overhead, especially large `Or(...)` trees

Target change:

- precompute the logical skeleton once per framework:
  - defenders for each attacker
  - defended-expression for each argument
- reuse those expressions in:
  - admissibility constraints
  - completeness constraints

TDD tasks:

- add characterization tests for defended-expression semantics on hand-built AFs
- add Z3-vs-brute-force equivalence coverage for complete extensions after refactor
- add one small structural test around the internal defended-expression builder if helpful

Files:

- `propstore/dung_z3.py`
- `tests/test_dung_z3.py`

Correctness gate:

- `uv run pytest tests/test_dung_z3.py tests/test_dung.py -q`

Benchmark checkpoint:

- `uv run pytest tests/test_aspic.py -q --durations=20`

### Slice 3: Introduce Dung `auto` Backend Dispatch

Status: Pending

Problem:

- many Hypothesis-generated AFs are tiny
- for small frameworks, the Python cost of constructing Z3 formulas may be higher than brute-force enumeration

Target change:

- introduce an internal `auto` dispatch policy for Dung semantics
- choose brute-force for small AFs, Z3 for larger AFs
- preserve existing public semantics and outputs

Design rule:

- dispatch must be based on framework shape, not wall-clock timing
- threshold selection must be explicit and tested

TDD tasks:

- add tests proving `auto` returns the same extensions as forced `brute` and forced `z3`
- add tests for threshold edge cases
- keep existing `z3_*` direct-entry tests intact

Files:

- `propstore/dung.py`
- possibly `propstore/dung_z3.py`
- `tests/test_dung.py`
- `tests/test_dung_z3.py`

Correctness gate:

- `uv run pytest tests/test_dung.py tests/test_dung_z3.py -q`

Benchmark checkpoint:

- `uv run pytest tests/test_aspic.py -q --durations=20`

### Slice 4: Reduce ASPIC-to-Dung Rework

Status: Pending

Problem:

- `well_formed_csaf()` constructs a Dung AF after running:
  - `build_arguments()`
  - `compute_attacks()`
  - `compute_defeats()`
- the postulate tests then repeatedly call `complete_extensions(csaf.framework)` in each example

Target change:

- cache or precompute the Dung extension family inside the generated `CSAF` object where this is semantically safe
- avoid repeated complete-extension recomputation within one generated c-SAF instance

Important note:

- this is only worth doing if profiling confirms repeated recomputation is still material after slices 1-3
- do not add cross-example global caches that risk Hypothesis contamination

TDD tasks:

- add tests proving cached extension access is identical to direct `complete_extensions(csaf.framework)`
- ensure the cache lives at the c-SAF object level, not as mutable global state

Files:

- `propstore/aspic.py`
- `tests/test_aspic.py`

Correctness gate:

- `uv run pytest tests/test_aspic.py -q`

Benchmark checkpoint:

- `uv run pytest tests/test_aspic.py -q --durations=20`

### Slice 5: Secondary ASPIC Local Optimizations

Status: Pending

Problem:

- after the first memoization pass, there may still be moderate wasted work in:
  - `build_arguments()`
  - `compute_attacks()`

Target changes:

- cache or hoist `_all_concs()` results in `build_arguments()`
- pre-index potential attackers by conclusion literal or contrary class in `compute_attacks()`
- avoid full attacker-target-subargument scans where literal-based prefiltering can prove impossibility

Design rule:

- only do this after the Dung/Z3 work if the benchmark still justifies it
- do not over-engineer ASPIC if the Dung layer remains dominant

TDD tasks:

- add characterization tests for any new attacker-index helper
- prove attack sets remain identical on generated and concrete examples

Files:

- `propstore/aspic.py`
- `tests/test_aspic.py`

Correctness gate:

- `uv run pytest tests/test_aspic.py -q`

Benchmark checkpoint:

- `uv run pytest tests/test_aspic.py -q --durations=20`

### Slice 6: Full Reasoning Regression and Benchmark Readout

Status: Pending

Purpose:

- prove the performance work did not drift semantics elsewhere
- capture the final timing delta on the actual ASPIC workload

Correctness gate:

- `uv run pytest tests/test_dung.py tests/test_dung_z3.py tests/test_argumentation_integration.py tests/test_structured_argument.py tests/test_praf.py tests/test_praf_integration.py tests/test_aspic.py -q`

Benchmark readout:

- `uv run pytest tests/test_aspic.py -q --durations=20`
- `uv run pytest tests/test_aspic.py -q -k "RationalityPostulates" --durations=20`

Deliverables:

- updated note with before/after timings
- explicit statement of what changed the most
- explicit statement of what remains slow

## Test Strategy

### Correctness tests must cover

- brute-force vs Z3 equivalence for stable, complete, and preferred extensions
- behavior when `attacks != defeats`
- ASPIC rationality postulates that depend on complete extensions
- hand-built hard instances and symmetric/odd-cycle cases

### Performance tests should prefer

- structural assertions that repeated scans or rebuilds are eliminated
- local benchmark commands with `--durations`
- comparison notes checked by humans, not hardcoded millisecond thresholds

### Performance tests should avoid

- flaky assertions like "must complete in < N ms" in CI
- tests that depend on machine load or concurrent repo activity

## Decision Rules

If slices 1-3 materially reduce runtime, do not jump to more exotic solver work.

Only investigate more radical approaches if:

- the ASPIC suite is still unacceptably slow after adjacency, expression reuse, and `auto` dispatch
- profiling still points at the same remaining bottleneck

Possible escalation paths if needed later:

- alternative complete-extension encoding in Z3
- specialized bitset-based complete-extension search for small AFs
- literature-guided alternative admissibility/fixpoint encodings

These are explicitly deferred until the cheaper, more local moves are exhausted.

## Success Criteria

This plan succeeds if:

- `tests/test_aspic.py` gets materially faster without lowering Hypothesis counts
- Dung semantics remain extension-equivalent across brute-force and Z3 paths
- the optimization work is covered by characterization tests, not just timing anecdotes
- the repo ends with a repeatable benchmark command and a documented timing delta

## Progress Log

- 2026-03-26: Plan created.
