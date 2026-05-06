# Proposal: Belief Revision Architecture In Propstore

**Updated:** 2026-05-06
**Status:** Ownership split is implemented, but formal-kernel delegation from
propstore into `belief_set` is not yet implemented. The remaining work is a
deletion-first cutover from propstore-local AGM-shaped operator logic to
dependency-owned formal kernels.
**Grounded in:** the current propstore codebase, `../belief-set`,
`../argumentation`, `../belief-set/papers/*/notes.md`, and the project
docs/tests cited in this file.

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

Current caveat: `propstore.support_revision` still contains local
operator/entrenchment/iterated policy behavior. That code is operational
support-incision machinery, not formal AGM, and the target cutover is to delete
the AGM-shaped decision logic from propstore and route formal decisions through
`belief_set` via one explicit adapter.

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

- an explicit belief-base surface distinct from closed `BeliefSet` theories
- AGM partial-meet contraction with remainder sets and explicit selection
  functions
- Levi and Harper as first-class public composer APIs over the formal
  contraction/revision surfaces
- Grove sphere systems and the equivalent sentence/preorder representation
- Katsuno-Mendelzon update
- Hansson safe contraction, set-valued contraction inputs, composite/simple
  partial meet contraction, and minimal contraction for non-closed belief bases
- Spohn conditionalization with an explicit firmness parameter, where practical
- full Booth-Meyer admissible-revision family beyond restrained and
  lexicographic revision
- Konieczny-Pino-Pérez `Delta^Max` and the remaining IC merge families
- Coste-Marquis AF merge

These gaps should be closed in `../belief-set`, not by reintroducing local
propstore approximations.

### Paper-Grounded Belief-Set Target

The newly read AGM papers sharpen the target for `../belief-set`.

AGM 1985 says the dependency must expose real contraction and revision at the
closed-theory level: remainder sets, selection functions, partial meet
contraction, and Levi/Harper duality are not optional if the package is going
to claim "true AGM." The current Spohn-backed revision is useful, but it is not
the whole AGM surface.

Gärdenfors and Makinson 1988 says epistemic entrenchment should be a
first-class formal object, not only a derived explanation label. A Spohn ranking
can induce entrenchment in finite implementations, but the public API should
still make the contraction/revision/entrenchment equivalence testable.

Grove 1988 says the finite model-set implementation should also support the
semantic view of AGM: systems of spheres or equivalent total preorders over
worlds, with revision as selection of the closest input-worlds followed by
closure. This is the cleanest implementation target for finite propositional
worlds.

Spohn 1988 says iterated revision needs an epistemic state richer than the
accepted belief set. `SpohnEpistemicState` is therefore the right primitive for
ranking-based iteration, and future work should expose conditionalization with
firmness rather than collapsing every update into the same strength.

Booth and Meyer 2006 says iterated revision should not stop at "whatever
ranking update passes tests." The package should name the policy family:
lexicographic, restrained, and the broader admissible class. Restrained
revision is a conservative default, not the whole iterated-revision story.

Hansson 1989 says `belief-set` must distinguish a belief base from a closed
theory. Closed-theory AGM loses source-level distinctions that matter to
propstore, such as whether a disjunction was explicitly present or merely
derivable. The dependency should therefore expose belief-base contraction and
set-valued contraction inputs as formal surfaces, while keeping full AGM as the
closed-theory specialization.

Konieczny and Pino Pérez 2002 says merge is not revision with more inputs.
Multi-source merge needs IC postulates, integrity constraints, and distance or
preorder semantics over interpretations. `belief_set.ic_merge` is therefore the
right owner for formal merge; propstore assignment selection must remain a
separate render-time operation.

The target formal stack in `../belief-set` is therefore:

1. finite formula/world primitives
2. explicit belief bases and explicit closed theories
3. AGM theory contraction/revision via partial meet, entrenchment, and
   Grove-style sphere/preorder semantics
4. Spohn/OCF epistemic states for iterated revision
5. named iterated policies, including restrained, lexicographic, and the wider
   admissible class
6. Hansson-style belief-base contraction for non-closed source-sensitive bases
7. IC merge under integrity constraints

Propstore should consume these formal surfaces only at projection boundaries.
It should not rebuild them inside `propstore.support_revision`.

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

## Propstore Integration Target

### How Propstore Uses The Formal Behavior

This is target behavior, not a description of the current production call graph.
As of this proposal, production `propstore` has no concrete `belief_set` import
edge; `support_revision.operators`, `support_revision.iterated`, and
`support_revision.entrenchment` still own local AGM-shaped behavior. Those local
decision paths should be deleted during cutover, not wrapped or preserved in
parallel.

Propstore should use the formal dependency behavior as a decision and audit
kernel over scoped projections, then use propstore-owned support machinery only
to realize the accepted decision against source-backed world artifacts.

The concrete integration shape is:

1. project a scoped `BoundWorld` into a source-sensitive belief base
2. derive the closed theory or finite world model needed by `belief_set`
3. run the requested formal operation in `belief_set`
4. compare the formal accepted/rejected formulas with the projected support
   base
5. compute propstore support-realization incision sets, provenance,
   explanations, and journal entries
6. replay from the journal by rerunning the normalized operation against the
   captured snapshot

This keeps the behavior principled without making propstore source storage,
ATMS labels, or support-derived rankings pretend to be the formal reviser.

The integration has two typed contracts:

- decision contract: projection inputs plus the formal `belief_set` answer
- realization contract: propstore support cuts, provenance, explanation, and
  journal records needed to make the scoped world projection conform to the
  formal answer

Callers must be able to inspect both. "The formal kernel selected these
formulas/worlds" and "propstore realized that selection by cutting these support
assumptions" are distinct facts.

Closed-theory AGM is useful in propstore when the question is semantic:
"after accepting this formula, which formulas should be believed in the scoped
finite theory?" The answer should come from `belief_set` partial meet,
entrenchment, Grove sphere/preorder, or Spohn state APIs. Propstore then asks a
separate operational question: "which source-backed assumptions or support
claims must be incised so the scoped world projection conforms to that formal
answer?"

Hansson-style belief-base revision is useful when source representation matters.
If a propstore source explicitly asserted `a or b`, that assertion is not the
same artifact as deriving `a or b` from a closed theory. Propstore should
therefore project source assertions into a `belief_set` belief-base surface for
base-sensitive contraction, especially for batch removals, norm-like sources,
and cases where explicit disjunctions or independent support should survive.

Epistemic entrenchment is useful as a shared ordering language. Propstore can
derive local entrenchment hints from support count, source reliability, override
metadata, argument strength, and user policy, but the resulting order should be
validated by `belief_set` when it is used to claim AGM behavior. The support
incision layer can then explain which lower-entrenched assumptions were cut and
which higher-entrenched assertions were preserved.

Spohn/OCF state is useful for worldline journals. A linear worldline can carry a
formal epistemic state snapshot beside the propstore support snapshot. Iterated
revision updates the formal OCF or preorder in `belief_set`; propstore records
the normalized operator input, the formal policy name, the state hash, and the
support realization. At merge parents, this path still refuses and hands off to
formal merge.

IC merge is useful at multi-parent worldline points and multi-source import
points. `belief_set.ic_merge` should compute the merged model set under an
integrity constraint and a named merge policy. Propstore should then map that
merged formal result back to candidate assertions, assignments, and support
choices. Assignment selection remains render-time selection; it can consume the
formal merge result, but it is not itself IC merge.

Argumentation is useful as a preference and defeat provider, not as a substitute
for belief revision. Argument statuses, attacks, supports, and source
preferences can feed entrenchment construction, selection-function policy, or
merge distances. The actual formal revision or merge still belongs to
`belief_set`, and formal AF revision still belongs to `argumentation`.

The result is a two-layer behavior:

- `belief_set` answers the formal belief-change question over formulas, worlds,
  bases, rankings, and profiles
- propstore answers the source-realization question over claims, support sets,
  assumptions, snapshots, explanations, and journals

Neither layer should be collapsed into the other.

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

### Formal Adapter Boundary

The cutover should introduce exactly one production import edge from propstore
to `belief_set`: `propstore.support_revision.belief_set_adapter`. All other
propstore modules should call owner-layer propstore APIs and should not import
`belief_set` directly.

The adapter owns:

- projection from `BoundWorld` and `RevisionScope` into a finite formal
  alphabet, belief base or closed `BeliefSet`, optional `SpohnEpistemicState`,
  and reverse maps back to propstore atom/source identities
- propagation of `belief_set.anytime.AlphabetBudgetExceeded` and
  `EnumerationExceeded` as typed revision failures
- calls into `belief_set.agm`, `belief_set.iterated`, and `belief_set.ic_merge`
  for formal decisions
- conversion of the formal decision into a realization request for
  propstore-owned support incision

The adapter does not own support graph mutation, CLI rendering, worldline
journal hashing, source mutation, AF revision kernels, or assignment-selection
merge.

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
- after cutover, `propstore.support_revision.belief_set_adapter` must be the
  only production module importing `belief_set`
- context lifting, ASPIC projection, and grounding must not import
  `belief_set`
- support-revision snapshots must reject malformed loose mappings
- worldline revision capture must snapshot state rather than persist live state
- changing a revision payload must change the worldline content hash
- local support-revision modules must not contain hand-rolled lexicographic,
  restrained, partial-meet, remainder-set, sphere, or IC-merge kernels

Additional cutover gates to add:

- adapter projection tests showing a scoped `BoundWorld` maps to the expected
  finite `belief_set` alphabet and reverse identity maps
- direct equivalence tests between propstore adapter decisions and direct
  `belief_set` calls for expansion, revision, contraction, lexicographic
  revision, and restrained revision
- budget tests proving `AlphabetBudgetExceeded` and `EnumerationExceeded` become
  typed revision failures
- merge tests proving multi-parent worldline revision dispatches to
  `belief_set.ic_merge` and linear iterated revision still refuses merge-parent
  states
- legacy phase-1 revision suites must either be updated to the adapter boundary
  or deleted in the cutover commit

---

## Current Recommendation

Keep the ownership split, but do not preserve the current propstore-local
operator implementation as the final architecture:

1. Put formal belief-set revision, entrenchment, and IC merge in
   `../belief-set`.
2. Put formal AF revision in `../argumentation`.
3. Keep propstore's `support_revision` package as an operational
   support-incision, explanation, snapshot, and journal adapter.
4. Keep `BoundWorld`, app workflows, CLI, and worldline runner as adapters over
   owner-layer APIs.
5. Make `../belief-set` the ambitious formal package the papers imply:
   belief-base operations, closed-theory AGM, partial meet selection, Levi and
   Harper composers, entrenchment, Grove sphere/preorder semantics, OCF
   iterated states, named admissible iterated policies, and IC merge.
6. Update propstore adapters only where a real propstore projection or
   worldline integration is needed.

The old implementation order in this proposal has been superseded. The active
work is no longer "build `propstore/revision` through Phase 5"; it is "protect
the dependency-owned formal kernels and propstore-owned support-incision
boundary while completing the formal surfaces in their owning dependencies."

The production cutover is deletion-first:

- delete propstore-local AGM-shaped decision logic from `support_revision`
- route formal decisions through `support_revision.belief_set_adapter`
- keep only support-realization, explanation, snapshot, and journal behavior in
  propstore
- update every caller in the same slice

Passing tests while a parallel local decision path still exists is not
completion.

---

## Implementation Order

1. Stabilize the minimum `belief_set` public surfaces propstore will call:
   `BeliefSet`, `expand`, `SpohnEpistemicState`, `agm.revise`,
   `agm.full_meet_contract`, `entrenchment.EpistemicEntrenchment`,
   `iterated.lexicographic_revise`, `iterated.restrained_revise`, and
   `ic_merge.merge_belief_profile`.
2. Tighten the propstore architecture gate before production cutover so exactly
   `propstore.support_revision.belief_set_adapter` may import `belief_set`.
3. Add `support_revision.belief_set_adapter` with the projection bundle,
   reverse maps, budget handling, formal-operation dispatch, and typed decision
   reports.
4. Cut over `support_revision.operators` by deleting formal decision behavior
   there and making expand/contract/revise consume adapter decisions plus
   propstore support-realization.
5. Cut over `support_revision.iterated` by deleting local lexicographic and
   restrained ranking-update branches and calling the named `belief_set`
   iterated operators.
6. Cut over `support_revision.entrenchment` so propstore support reasons are a
   companion explanation for a formal entrenchment/preorder decision, not a
   substitute formal ordering.
7. Wire worldline merge points through `belief_set.ic_merge` over projected
   belief profiles and explicit integrity constraints. Keep assignment
   selection as render-time observed-value selection only.
8. Update app and CLI adapters to render the split decision/realization result
   without changing CLI command ownership.
9. Delete or rewrite legacy phase-1 revision tests in the same slice that makes
   the stricter architecture gate pass.
10. Add deferred `belief_set` surfaces one at a time: partial meet selection,
    Levi/Harper composers, Grove spheres/preorders, Hansson belief-base
    contraction, Katsuno-Mendelzon update, and remaining IC merge families.

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

### 8. Are we implementing full AGM anywhere?

Yes. Full closed-theory AGM belongs in `../belief-set`: partial meet
contraction, explicit selection functions, Levi and Harper composition,
entrenchment equivalence, and Grove-style sphere/preorder semantics. Propstore
does not implement that kernel locally.

### 9. Does `belief-set` also need belief-base revision?

Yes. Hansson's examples show that closed theories collapse representation
differences that propstore cares about. `../belief-set` should therefore expose
source-sensitive belief-base contraction/revision as a sibling formal surface,
not as a replacement for closed-theory AGM.

### 10. Where should missing AF revision constructions be added?

In `../argumentation`, with propstore consuming public APIs or adding thin
projection adapters only when needed.

### 11. What prevents architectural drift?

The concrete mechanisms are the retired `propstore.revision` test, the
`belief_set` import-boundary test, docs that explicitly separate formal revision
from support incision, worldline snapshot/hash tests, and dependency postulate
tests.
