# Probabilistic Refactor Plan

Date: 2026-03-25
Status: Planned

## Goal

Replace the current mixed PrAF model with a principled primitive-relation model:

- store probabilistic uncertainty on primitive argument, attack, and support artifacts
- derive semantic defeats from sampled primitive worlds instead of treating derived defeats as authoritative probabilistic inputs
- make every exact, MC, and fallback path use one canonical world-realization pipeline
- preserve the project’s non-commitment discipline: no build-time gating, no fabricated certainty, provenance carried to the argumentation layer

## Constraints

- Preserve public behavior unless a regression test proves it is wrong.
- Add or tighten executable tests before each behavioral slice.
- Do not stage or revert unrelated worktree changes.
- Keep the current public entry points usable during migration:
  - `build_praf()`
  - `compute_praf_acceptance()`
  - `build_argumentation_framework()`
- Defer any storage migration until the in-memory model is stable and covered.
- Prefer deterministic verification for small worlds and cross-check approximate paths against exact ones.

## Target Architecture

### Primitive probabilistic model

- `ProbabilisticAF` should represent:
  - `p_args`
  - primitive `p_attacks`
  - primitive `p_supports`
  - deterministic preference policy / direct-defeat classification
  - provenance for every probabilistic relation
- Derived defeats should not be first-class probabilistic inputs.
- Any probability reported for a derived defeat should be a derived query result with explicit provenance.

### Canonical world realization

- One helper should realize a world from primitive probabilistic artifacts:
  1. sample arguments
  2. sample primitive attacks
  3. sample primitive supports
  4. derive direct defeats from sampled attacks plus deterministic preference policy
  5. derive Cayrol defeats from sampled direct defeats plus sampled supports
  6. build `ArgumentationFramework(arguments, attacks, defeats)`
- MC, exact enumeration, and all exact fallbacks must call this same helper.

### Exact algorithms

- Exact DP should be explicit about its supported domain.
- The current DP should remain grounded-only and defeat-only until a new primitive-relation DP exists.
- Relation-rich worlds should use canonical exact enumeration until a correct richer DP is implemented.

## Work Plan

### Slice 1: Characterization and invariants

Status: Pending

- Add tests that define the new semantic invariants:
  - attack-only edges affect conflict-freeness under exact, MC, and exact-DP dispatch
  - support-only connectivity prevents component separation when it can induce Cayrol defeats
  - derived defeats are recomputed from sampled primitive worlds, not sampled independently
  - structured projection never prunes vacuous stances at build time
- Extend cross-validation so exact enum is the reference for all small relation-rich worlds.

Files:

- `tests/test_review_regressions.py`
- `tests/test_praf.py`
- `tests/test_treedecomp.py`
- `tests/test_bipolar_argumentation.py`
- `tests/test_structured_argument.py`

Verification:

- `uv run pytest tests/test_review_regressions.py tests/test_praf.py tests/test_treedecomp.py tests/test_bipolar_argumentation.py tests/test_structured_argument.py -q`

### Slice 2: Separate primitive relation collection from semantic AF derivation

Status: Pending

- Extract a first-class relation collector from `build_argumentation_framework()` and `build_praf()`.
- The collector should return:
  - active arguments
  - primitive attacks
  - primitive supports
  - direct defeats after preference filtering
  - stance provenance / opinion payloads for primitive relations
- Keep AF derivation as a separate pure step.

Files:

- `propstore/argumentation.py`
- optionally a new module such as `propstore/probabilistic_relations.py`

Verification:

- `uv run pytest tests/test_argumentation_integration.py tests/test_bipolar_argumentation.py tests/test_praf_integration.py -q`

### Slice 3: Introduce canonical world realization API

Status: Pending

- Add a single world-realization API in `propstore/praf.py` or a new helper module.
- The API should support:
  - exact enumeration over primitive relation events
  - one sampled world for MC
  - subworld realization for component-local computation
- Remove strategy-specific ad hoc reconstruction of `ArgumentationFramework`.

Files:

- `propstore/praf.py`
- optionally `propstore/praf_worlds.py`

Verification:

- `uv run pytest tests/test_praf.py tests/test_review_regressions.py -q`

### Slice 4: Remove derived defeat summaries from core semantics

Status: Pending

- Stop treating `p_defeats` as the authoritative source for derived defeats in semantic computation.
- Restrict `p_defeats` to direct defeats or replace it with a clearer field such as `p_direct_defeats`.
- If backward compatibility requires `p_defeats`, make it a compatibility view for direct defeats only.
- Add an explicit helper for reporting derived-defeat marginals as derived summaries, not inputs.

Files:

- `propstore/praf.py`
- `propstore/argumentation.py`
- callers in tests and any render/explanation code that inspects `p_defeats`

Verification:

- `uv run pytest tests/test_praf.py tests/test_praf_integration.py tests/test_review_regressions.py -q`

### Slice 5: Add provenance-bearing probabilistic relation records

Status: Pending

- Introduce a dataclass for primitive probabilistic relations with:
  - relation kind
  - source / target
  - opinion
  - provenance
  - derivation marker
- Teach `build_praf()` to populate these records from stance rows.
- Keep a compatibility adapter for current dict-shaped consumers during migration.

Files:

- new module such as `propstore/probabilistic_relations.py`
- `propstore/argumentation.py`
- `propstore/praf.py`

Verification:

- `uv run pytest tests/test_praf_integration.py tests/test_render_time_filtering.py tests/test_argumentation_integration.py -q`

### Slice 6: Make MC and exact enumeration consume only canonical worlds

Status: Pending

- Route `_compute_mc()` and `_compute_exact_enumeration()` through the same primitive-relation world builder.
- Ensure component decomposition operates on primitive semantic dependencies:
  - primitive attacks
  - primitive supports
- Remove duplicated relation filtering logic.

Files:

- `propstore/praf.py`

Verification:

- `uv run pytest tests/test_praf.py tests/test_review_regressions.py tests/test_praf_integration.py -q`

### Slice 7: Narrow and isolate exact DP support

Status: Pending

- Make the current DP explicitly operate only on grounded, defeat-only worlds where `attacks == defeats` and there are no supports.
- Move the capability check to one place.
- Ensure all unsupported cases fall back to canonical exact enumeration rather than custom partial logic.
- Update docstrings and tests to match the real support boundary.

Files:

- `propstore/praf_treedecomp.py`
- `tests/test_treedecomp.py`

Verification:

- `uv run pytest tests/test_treedecomp.py tests/test_review_regressions.py tests/test_praf.py -q`

### Slice 8: Redesign exact DP for primitive relations

Status: Pending

- Only start after slices 1-7 are stable.
- Design a new DP around primitive-relation local state rather than global accumulated edge sets.
- Supported scope for the first redesign:
  - grounded semantics
  - primitive attacks plus optional support
  - canonical derivation of direct and Cayrol defeats inside the DP state transition rules
- If support-aware DP is too large for one pass, split it:
  - Phase A: attack-aware DP where `attacks` may differ from `defeats`
  - Phase B: support-aware DP with local Cayrol closure semantics

Files:

- `propstore/praf_treedecomp.py`
- supporting helpers as needed

Verification:

- `uv run pytest tests/test_treedecomp.py tests/test_praf.py tests/test_review_regressions.py -q`

### Slice 9: Honest claims and cleanup

Status: Pending

- Update literature claims to match the real implementation:
  - `claim_strength()` is heuristic, not a faithful Def. 19 implementation
  - tree-decomposition support is narrower than the full Popescu paper until Slice 8 lands
- Clean compatibility shims only after the new primitive model has full test coverage.

Files:

- `propstore/preference.py`
- `propstore/praf_treedecomp.py`
- any docs/comments touched by the migration

Verification:

- `uv run pytest tests/test_praf.py tests/test_treedecomp.py tests/test_argumentation_integration.py -q`

## Acceptance Criteria

- No semantic path reconstructs an AF without preserving the relevant primitive relations.
- No build-time pruning removes vacuous uncertainty from argumentation structure.
- Derived defeats are never sampled as independent primitive events.
- Small-world exact enum is the single oracle for MC/DP cross-validation.
- Unsupported exact-DP cases fail over to canonical exact enumeration, not to a semantically weaker shortcut.
- The code and docstrings no longer overclaim literature fidelity where the implementation is heuristic or partial.

## Full Regression Gate

Run after each completed slice once the touched surface widens:

- `uv run pytest tests/test_review_regressions.py tests/test_praf.py tests/test_praf_integration.py tests/test_treedecomp.py tests/test_structured_argument.py tests/test_bipolar_argumentation.py tests/test_argumentation_integration.py tests/test_render_time_filtering.py -q`

Run before deleting any compatibility shim:

- `uv run pytest tests/ -q`

## Progress Log

- 2026-03-25: Plan created after landing the first correctness fixes for relation-rich PrAF semantics, structured projection vacuous-edge preservation, and exact-DP safety fallback.
