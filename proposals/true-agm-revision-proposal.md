# Proposal: Belief Revision Architecture In Propstore

**Updated:** 2026-05-06
**Status:** Current architecture implemented across propstore and sibling
dependencies; remaining formal gaps are dependency-owned and listed below.
**Grounded in:** the current propstore codebase, `../belief-set`,
`../argumentation`, and the project docs/tests cited in this file.

---

## Problem

Propstore originally needed a "true AGM revision layer." The current codebase no
longer implements that as a propstore-owned `propstore.revision` package.

The target architecture is now:

- formal propositional belief revision and IC merge live in the sibling
  `../belief-set` dependency, imported as `belief_set`
- formal AF revision lives in the sibling `../argumentation` dependency, under
  `argumentation.af_revision`
- propstore owns the projection, support-incision, CLI, app, worldline, and
  journal integration needed to apply scoped revision-like operations to
  propstore worlds
- source storage remains immutable during revision operations
- ATMS remains support analysis, not AGM
- merge remains separate from revision

This proposal is therefore not a plan to add a new `propstore/revision/`
package. That path has been retired and is guarded by
`tests/test_revision_retirement.py`.

---

## Non-Negotiable Rule

**Do not cite `propstore.support_revision` as formal AGM belief revision.**

Corollaries:

- formal AGM, entrenchment, iterated revision, and IC merge belong in
  `belief_set`
- formal AF revision belongs in `argumentation.af_revision`
- propstore support revision is an operational support-incision adapter over a
  scoped world projection
- source YAML, compiled sidecars, and canonical claim identity are not rewritten
  by revision operations
- ATMS labels and essential support may inform propstore support incision, but
  ATMS is not itself the reviser
- assignment-selection merge and IC merge are different surfaces
- support-incision journals are replayable propstore artifacts, not opaque
  substitutes for formal belief-set state

If the code or docs blur these boundaries, the architecture regresses.

---

## Current Owner Map

### `../belief-set`

Package: `formal-belief-set`, imported as `belief_set`.

Implemented public surfaces:

- `belief_set.language`: finite propositional formulas and worlds
  (`Atom`, `Not`, `And`, `Or`, `Top`, `Bottom`, helpers)
- `belief_set.core.BeliefSet`: finite model-set belief theories over an
  explicit alphabet
- `belief_set.core.expand`: model-set expansion by a formula
- `belief_set.agm.SpohnEpistemicState`: finite OCF over all worlds
- `belief_set.agm.revise`: Darwiche-Pearl style revision over a Spohn ranking
- `belief_set.agm.full_meet_contract`: Harper-style contraction over the finite
  theory
- `belief_set.entrenchment.EpistemicEntrenchment`: Gärdenfors-Makinson style
  entrenchment induced by a Spohn ranking
- `belief_set.iterated.lexicographic_revise`
- `belief_set.iterated.restrained_revise`
- `belief_set.ic_merge.merge_belief_profile`: Konieczny-Pino-Pérez finite
  model-theoretic IC merge with `SIGMA` and `GMAX`
- anytime guards such as `AlphabetBudgetExceeded` and `EnumerationExceeded`

Primary gates:

- `../belief-set/tests/test_belief_set_postulates.py`
- `../belief-set/tests/test_belief_set_iterated_postulates.py`
- `../belief-set/tests/test_agm_postulate_audit.py`
- `../belief-set/tests/test_paper_postulate_property_sweep.py`
- `../belief-set/tests/test_belief_set_alphabet_growth_budget.py`
- `../belief-set/tests/test_ic_merge_Maj_Arb.py`

Known formal gaps, documented in `docs/belief-set-revision.md` and
`docs/ic-merge.md`:

- AGM partial-meet contraction and explicit selection functions
- Levi and Harper as first-class public composer APIs
- Grove sphere systems
- Katsuno-Mendelzon update
- Hansson safe contraction and broader belief-base contraction families
- full Booth-Meyer admissible-revision family beyond restrained revision
- Konieczny-Pino-Pérez `Delta^Max`
- Coste-Marquis AF merge

These gaps should be closed in `../belief-set`, not by reintroducing local
propstore approximations.

### `../argumentation`

Package: `formal-argumentation`, imported as `argumentation`.

Implemented AF revision surfaces:

- `argumentation.af_revision.baumann_2015_kernel_union_expand`
- `argumentation.af_revision.baumann_2015_kernel`
- `argumentation.af_revision.stable_kernel`
- `argumentation.af_revision.ExtensionRevisionState`
- `argumentation.af_revision.diller_2015_revise_by_formula`
- `argumentation.af_revision.diller_2015_revise_by_framework`
- `argumentation.af_revision.cayrol_2014_classify_grounded_argument_addition`

Primary gates:

- `../argumentation/tests/test_af_revision.py`
- propstore consumer docs/tests in `docs/af-revision.md` and
  `tests/test_af_revision_postulates.py`

Known AF gaps are documented in `docs/af-revision.md`. Propstore should consume
public `argumentation` APIs or add thin adapters; it should not embed a new AF
revision kernel.

### `propstore.support_revision`

Package: propstore-owned operational support-incision machinery.

Implemented surfaces:

- `state.py`: `AssertionAtom`, `AssumptionAtom`, `BeliefBase`,
  `RevisionScope`, `RevisionResult`, `RevisionEpisode`, `EpistemicState`
- `projection.py`: `BoundWorld` to exact-support belief-base projection using
  `SituatedAssertion` identities and source-claim provenance
- `entrenchment.py`: deterministic support-derived ranking with override
  hooks and explanation reasons
- `operators.py`: expand, contract, revise, input normalization, stabilization,
  and bounded incision-set search
- `iterated.py`: explicit propstore epistemic state, restrained/lexicographic
  ranking update, and merge-point refusal
- `explain.py` and `explanation_types.py`: result explanation payloads
- `snapshot_types.py`: canonical snapshot serialization and strict mapping
  decoding
- `history.py`: epistemic snapshots, transition journals, chain integrity,
  deterministic replay, and semantic diffs
- `dispatch.py`: replay of journal operators from normalized inputs
- `scope_policy.py`: declarative scope-completeness policy for snapshot
  consumers
- `af_adapter.py`: projection of accepted support-revision state to
  argumentation-facing views
- `workflows.py`: owner-layer APIs used by app and CLI adapters

This package is not the formal AGM implementation. It answers a different
question: "Given a scoped propstore world with exact ATMS support, which support
assumptions must be incised to accept or remove selected projected atoms, and
how can that episode be explained and replayed?"

---

## Propstore Integration

### Bound World

`propstore.world.bound.BoundWorld` is the scoped adapter. It delegates revision
work instead of owning operator logic:

- `revision_base()`
- `revision_entrenchment(...)`
- `expand(...)`
- `contract(..., max_candidates=...)`
- `revise(..., max_candidates=..., conflicts=...)`
- `revision_explain(...)`
- `epistemic_state(...)`
- `revision_state_snapshot(state)`
- `iterated_revise(..., operator="restrained")`

The projection includes active claims only when support is exactly
reconstructible. Assertion atoms use `SituatedAssertion` identity, and each atom
retains its source claims so accepted snapshot atoms can be projected back to
source claim ids.

### App And CLI

Reusable app-layer requests live in `propstore.app.world_revision`.

The public CLI is under `pks world revision`:

```bash
pks world revision base [bindings...] [--context <context>]
pks world revision entrenchment [bindings...] [--context <context>]
pks world revision expand [bindings...] --atom '{...}' [--context <context>]
pks world revision contract [bindings...] --target <atom-id> [--context <context>]
pks world revision revise [bindings...] --atom '{...}' [--conflict <atom-id>]
pks world revision explain [bindings...] --operation <expand|contract|revise> ...
pks world revision iterated-state [bindings...] [--context <context>]
pks world revision iterated-revise [bindings...] --atom '{...}' [--operator restrained|lexicographic]
```

The CLI is a presentation adapter. It parses command input, calls
`propstore.app.world_revision`, and renders typed results.

### Worldlines And Journals

Worldline revision support is implemented in:

- `propstore.worldline.definition.WorldlineRevisionQuery`
- `propstore.worldline.revision_types`
- `propstore.worldline.revision_capture`
- `propstore.worldline.runner`
- `propstore.worldline.hashing`
- `propstore.support_revision.history`
- `propstore.support_revision.dispatch`

Worldline definitions can carry a `revision` query block. Results can carry a
revision payload with operation, input/target atom ids, accepted/rejected atom
ids, incision set, explanation, optional state snapshot, status, and typed
error.

Transition journals capture ordered support-revision operations with:

- `state_in` and `state_out` snapshots
- normalized operator input
- policy id and policy version snapshot
- content hashes
- deterministic replay through `support_revision.dispatch.dispatch`
- chain-integrity checks

At-step world projection replays the journal step by step and maps the accepted
snapshot assertions back to claim ids.

### Merge Points

`support_revision.iterated.iterated_revise` refuses iterated revision when
`RevisionScope.merge_parent_commits` contains more than one parent. The caller
must use an explicit merge path.

This is intentional. A linear within-branch revision episode is not a
multi-parent merge.

---

## Merge Boundary

There are now two named merge surfaces:

- `belief_set.ic_merge.merge_belief_profile` is the formal finite
  model-theoretic IC merge operator.
- `propstore.world.assignment_selection_merge` is observed-assignment selection
  over active typed values.

The old proposal text mentioned `propstore/repo/ic_merge.py`. The current docs
name the propstore render-time surface
`propstore.world.assignment_selection_merge`; formal IC merge lives in
`belief_set.ic_merge`.

Rules:

- use `belief_set.ic_merge` for formal formula/profile merge
- use assignment selection only for render-time selection among observed typed
  values
- do not route within-branch revision through a merge operator
- do not call support-incision output formal IC merge

---

## Projection Boundary

The current propstore projection is deliberately lossy:

- it includes only exact-support active claims in V1 support-revision bases
- it maps claims to assertion-language atoms, not raw claim-row buckets
- it carries source-claim provenance for display and reverse projection
- it carries support sets and essential support for incision/explanation
- it can include supporting assumptions
- it does not claim full deductive closure

Formal propositional closure belongs in `belief_set.BeliefSet`. Propstore's
support-revision base is an operational projected base over scoped world
evidence.

---

## Explanation Boundary

A propstore support-revision result must explain:

- accepted atom ids
- rejected atom ids
- incision set
- whether an atom was expanded, contracted, incised, or lost support
- support sets and essential support where available
- ranking reasons, including support count and explicit override metadata

This explanation is required for trust, replay, and worldline auditability. It
is not a substitute for formal postulate evidence. Formal postulate evidence
lives in dependency tests.

---

## Tests And Gates

Propstore gates:

- `tests/test_revision_retirement.py`
- `tests/test_revision_projection.py`
- `tests/test_revision_assertion_identity.py`
- `tests/test_revision_entrenchment.py`
- `tests/test_revision_operators.py`
- `tests/test_revision_properties.py`
- `tests/test_revision_state.py`
- `tests/test_revision_iterated.py`
- `tests/test_revision_iterated_examples.py`
- `tests/test_iterated_revision_recomputes_entrenchment.py`
- `tests/test_revision_explain.py`
- `tests/test_revision_bound_world.py`
- `tests/test_revision_cli.py`
- `tests/test_revision_af_adapter.py`
- `tests/test_worldline_revision.py`
- `tests/test_worldline_revision_snapshot_boundary.py`
- `tests/test_worldline_revision_merge_parent_evidence.py`
- `tests/test_world_query_at_journal_step.py`
- `tests/test_journal_entry_contract.py`
- `tests/test_capture_journal.py`
- `tests/test_replay_determinism_actually_replays.py`
- `tests/test_belief_set_docs.py`
- `tests/test_af_revision_no_stable_distinct_from_empty_stable.py`
- `tests/architecture/test_belief_set_boundary_contract.py`

Dependency gates:

- `../belief-set/tests/test_belief_set_postulates.py`
- `../belief-set/tests/test_belief_set_iterated_postulates.py`
- `../belief-set/tests/test_agm_postulate_audit.py`
- `../belief-set/tests/test_paper_postulate_property_sweep.py`
- `../belief-set/tests/test_ic_merge_Maj_Arb.py`
- `../argumentation/tests/test_af_revision.py`

Boundary gates that must remain true:

- `propstore.revision` must stay retired
- `propstore.support_revision` must not export or be described as AGM
- context lifting, ASPIC projection, and grounding must not import
  `belief_set`
- support-revision snapshots must reject malformed loose mappings
- worldline revision capture must snapshot state rather than persist live state
- changing a revision payload must change the worldline content hash

---

## Current Recommendation

Keep the architecture split exactly as it is:

1. Put formal belief-set revision, entrenchment, and IC merge in
   `../belief-set`.
2. Put formal AF revision in `../argumentation`.
3. Keep propstore's `support_revision` package as an operational
   support-incision, explanation, snapshot, and journal adapter.
4. Keep `BoundWorld`, app workflows, CLI, and worldline runner as adapters over
   owner-layer APIs.
5. Close formal gaps in the dependency that owns the formal surface, then update
   propstore adapters only where a real propstore integration is needed.

The old implementation order in this proposal has been superseded. The active
work is no longer "build `propstore/revision` through Phase 5"; it is "protect
the dependency-owned formal kernels and propstore-owned support-incision
boundary."

---

## Decisions That Are Now Pinned

### 1. Where does true AGM live?

In `../belief-set`, imported as `belief_set`.

### 2. What is propstore support revision?

An operational support-incision adapter over exact-support scoped world
projections.

### 3. What is the propstore belief atom?

`AssertionAtom` over a canonical `SituatedAssertion`, plus `AssumptionAtom` for
support assumptions.

### 4. Does propstore support revision mutate storage?

No. It returns revised projected bases, results, explanations, snapshots, and
journals.

### 5. Is iterated support revision allowed at merge points?

No. It raises and requires an explicit merge path.

### 6. Is propstore assignment selection IC merge?

No. Formal IC merge is `belief_set.ic_merge`; propstore assignment selection is
render-time observed-value selection.

### 7. Where should missing AGM constructions be added?

In `../belief-set`, with postulate/property tests there and propstore docs or
adapters updated afterward.

### 8. Where should missing AF revision constructions be added?

In `../argumentation`, with propstore consuming public APIs or adding thin
projection adapters only when needed.

### 9. What prevents architectural drift?

The concrete mechanisms are the retired `propstore.revision` test, the
`belief_set` import-boundary test, docs that explicitly separate formal revision
from support incision, worldline snapshot/hash tests, and dependency postulate
tests.
