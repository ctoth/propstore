# Unwired and Missing Code Convergence Plan

## Objective

Converge the code that is substantially implemented but unreachable, complete
the genuinely missing representation and result-status seams, and remove stale
claims of missing functionality without creating parallel owners.

This plan is based on current production code and tests, recorded in:

- `docs/reports/relation-calibration-extraction.md`
- `docs/reports/verification-views-owners.md`
- `docs/reports/values-praf-stale-gaps.md`

The reports are research evidence. This file is the execution control surface.

## Non-negotiable boundaries

- Use existing `WorldQuery`/world read APIs for similarity and semantic reads;
  do not create another embedding store or relation-store adapter hierarchy.
- Use existing stance, predicate, and rule proposal/promotion owners; do not add
  another proposal writer or write classifier output directly to canonical
  stances/rules/predicates.
- Keep source-branch state in the source subsystem and canonical semantic state
  in canonical families/micropublications.
- Do not productionize the test-only `FormRepository`, `ContextRepository`, or
  dead `RuleRepository`; production storage is `Repository.families`.
- Do not add direct canonical rule mutation or direct source-derived
  micropublication mutation. Their existing proposal/finalize/promotion paths
  remain authoritative.
- Keep direct scalar values distinct from numeric derivation. Category/boolean
  values must not leak into dimensional algebra, sensitivity, parameterization,
  or numeric conflict math.
- Treat grounding, ASPIC, PrAF, and ATMS completeness as separate owner-specific
  contracts. Do not invent a generic status adapter before the owner results are
  correct.
- All Python tests run through `scripts/run_logged_pytest.ps1`; the package type
  gate is `uv run pyright propstore`.
- For each deletion-first slice, load and follow `protocols:cleanup-refactor`
  before mutation, classify every broken dependency edge, and commit or fully
  revert the slice before starting the next source slice.

## Decisions required before affected phases

These are real semantic authorities missing from code. They are not safe to infer
during implementation.

### Q1. Canonical claim scalar

Recommended: preserve the four JSON scalar classes `str | bool | int | float`,
with `None` for absence. Preserve boolean separately from integer and preserve
integer rather than silently converting it to float.

Decision required:

- exact scalar set;
- tagged JSON storage versus discriminator plus typed columns;
- whether the standalone LinkML/JSON schemas remain supported contracts.

### Q2. Incomplete reasoning policy

Recommended: resolution and committed worldline materialization fail closed on
incomplete computation; diagnostic/inspection commands may display partial
evidence only when the partial status is explicit.

Decision required: confirm this policy for grounding, ASPIC, PrAF, and ATMS.

### Q3. Calibration authority

No persisted human-judgment authority currently exists.

Decision required:

- the identity and storage owner for labeled judgments;
- whether category priors are measured from that corpus or supplied as explicit
  provenance-bearing policy;
- version dimensions for model, prompt, pass, and category.

No production calibration-count producer may be built before this is decided.

### Q4. Durable LLM evidence

Decision required: whether stance/predicate/rule proposals retain raw prompts and
responses, only hashes/call ids plus model metadata, or a separately retained
evidence artifact. This affects privacy, reproducibility, and proposal schemas.

### Q5. View semantics

Decision required before the named optional surfaces:

- what makes a conflict “notable”;
- which provenance aggregates belong on the repository overview;
- source focus identity (`SourceRef.name`, canonical source URI, or explicit
  resolution of both) and whether a source neighborhood shows branch-local,
  canonical, or two-part state;
- whether form/context/lifting-rule mutation is allowed after initialization and
  its deletion/reference/proposal policy;
- whether micropublication lift means all claims, principal claim, or bundle-node
  support.

## Phase 0 — Correct invalid premises before feature work

Purpose: ensure later work is not justified by stale skips or descriptions.

- [ ] Delete the obsolete skipped ATMS resolution placeholder; add a real test
  only if a specific uncovered behavior is identified.
- [ ] Correct ASPIC module prose that says `build_aspic_projection` is absent.
- [ ] Correct relation prose claiming reverse distances survive classification.
- [ ] Correct grounding/fragility prose claiming non-empty grounding authoring is
  absent.
- [ ] Replace or delete the three empty fragility placeholder test classes only
  after driving the existing collectors with a real non-empty production bundle.
- [ ] Remove stale “embedding deferred” labels while retaining genuine optional
  `sqlite_vec` dependency skips.
- [ ] Rewrite the PrAF/grounding skipped-test description so it names the actual
  missing propagation seam rather than claiming low-level budget capture is absent.

Gate:

- The changed tests either execute meaningful production paths or are deleted;
  no skip remains whose stated prerequisite already exists.
- Focused logged tests for ATMS resolution, ASPIC projection, fragility, grounding,
  and embeddings pass.
- `uv run pyright propstore` passes.

## Workstream A — Canonical scalar value convergence

This is the foundational representation change. Complete it before the categorical
ATMS test or any consumer-specific workaround.

### A1. Prove and encode the scalar contract

- [ ] Resolve Q1.
- [ ] Add source-to-world round-trip tests for string category, boolean, integer,
  float, and absent value.
- [ ] Change `SourceClaimDocument.value` and canonical `Claim.value` together.
- [ ] Make the Quire charter-derived SQL representation preserve scalar type.
- [ ] Update source decode/CLI/import contracts and promotion without introducing
  a second claim representation.
- [ ] Regenerate supported external schemas or explicitly retire them, per Q1.

Required vertical gate:

`source decode -> source save/load -> promotion -> canonical save/load -> sidecar -> WorldQuery`

must preserve both scalar value and runtime type for all selected scalar classes.

### A2. Form-aware authoring validation

- [ ] Numeric forms retain current bounds, unit, uncertainty, and confidence rules.
- [ ] Closed category forms reject values outside their authored vocabulary.
- [ ] Extensible category forms accept new category values.
- [ ] Boolean forms accept booleans and reject textual lookalikes such as
  `"true"`.
- [ ] Category/boolean values never enter numeric bounds or dimensional checks.

### A3. Direct runtime consumers

- [ ] Preserve scalar identity in direct resolution and presentation; remove bool
  stringification and unintended int-to-float conversion from direct-value paths.
- [ ] Keep equation/parameterization, sensitivity, dimensional comparison,
  parameterization conflicts, and assignment-selection explicitly numeric.
- [ ] Preserve typed grounding constants and worldline results.
- [ ] Drive a real authored categorical provider through the bound world and
  unskip the existing ATMS incompatibility test, reusing the already-implemented
  visible rejection node.

Workstream A gate:

- Focused source, charter, sidecar, world-value, worldline, grounding, and ATMS
  tests pass through the logged wrapper.
- Numeric derivation behavior is unchanged for numeric inputs and explicitly
  rejects nonnumeric inputs.
- `uv run pyright propstore` passes.

## Workstream B — Reasoning completeness propagation

Resolve Q2 first. Execute each backend as a separate committed slice.

### B1. Grounding

- [ ] Thread `max_arguments` through `build_grounded_bundle` and production
  callers.
- [ ] Preserve `GroundedRulesBundle.status`, partial arguments, and reason through
  inspection/CLI/build surfaces.
- [ ] Persist or otherwise make build status available beside grounded rows.
- [ ] Prevent a budget-exceeded bundle from entering ASPIC as a complete theory.

Gate: a deliberately tiny budget yields visible partial arguments and
`budget_exceeded` at every production boundary; no caller renders it as complete.

### B2. ASPIC

- [ ] Reject incomplete grounding by default or explicitly carry partial status,
  according to Q2.
- [ ] Add an explicit completeness result for goal-directed `max_depth` exhaustion.
- [ ] Promote optional solver `package_status` from generic metadata into the
  existing typed analyzer result surface.
- [ ] Verify world and worldline never convert failed/partial ASPIC computation
  into an empty successful extension.

### B3. PrAF owner package and Propstore propagation

- [ ] Change the argumentation package owner to accept caller-supplied
  `max_samples` and return explicit convergence/cap status.
- [ ] Propagate that owner result through `AnalyzerResult`, resolution, CLI, and
  worldline without conflating it with COH convergence.
- [ ] Distinguish epsilon met, sample cap hit, exact strategy, Monte Carlo strategy,
  and automatic downgrade.

### B4. ATMS

- [ ] Carry build `fixpoint_reached`, iteration count, and warnings into existing
  worldline argumentation results.
- [ ] Make ATMS resolution refuse an unqualified winner or mark it incomplete when
  the build did not reach a fixpoint, per Q2.
- [ ] Keep future-query `BudgetExhausted(examined, total)` separate; do not replace
  it with build-fixpoint status.

Workstream B gate:

- Owner-focused logged suites distinguish complete, partial/capped, and failed
  outcomes for each backend.
- No generic result status obscures backend-specific cause or evidence.
- `uv run pyright propstore` passes in Propstore and the changed owner package.

## Workstream C — Relation classification to proposal workflow

Do not create a new embedding or proposal owner.

### C1. Typed classifier convergence

- [ ] Delete the reachable loose-dictionary stance result path.
- [ ] Make one typed proposal-ready result carry source/target ids, `StanceType`,
  model/call provenance, direction-specific distance, optional opinion, and
  unresolved-calibration detail.
- [ ] Normalize errors to typed `ABSTAIN`; do not persist a non-vocabulary
  `"error"` stance.
- [ ] Pass distinct forward and reverse embedding distances to their corresponding
  classifier calls.

Gate:

`powershell -File scripts/run_logged_pytest.ps1 tests/test_classify.py tests/test_classify_forward_reverse_independent.py tests/test_classify_no_silent_fallback.py tests/test_relate_perspective_isolation.py tests/test_relate_wbf.py -q`

### C2. Relation reads over existing world owners

- [ ] Replace `ClaimRelationStore` with direct use of existing world query/store
  capabilities unless a concrete remaining owner proves the protocol necessary.
- [ ] Project canonical claims to `RelatableClaim` at the heuristic boundary.
- [ ] Derive source attribution from canonical micropublication membership; do not
  add claim-local provenance.
- [ ] Bound candidate selection and retain the existing vector-store owner.

### C3. Calibration inputs

- [ ] Resolve Q3.
- [ ] Add the chosen labeled-judgment owner and reproducible calibration-count
  computation in the derived-build owner.
- [ ] Add the provenance-bearing category-prior provider.
- [ ] Load counts/priors in the production relation workflow and pass them through
  to typed classification.
- [ ] Keep absent authority explicit as unresolved; never invent defaults.

### C4. Record proposals

- [ ] Resolve Q4 for durable evidence fields.
- [ ] Record each directional typed result through existing
  `commit_stance_proposal()`.
- [ ] Preserve `pks proposal promote` as the only canonical acceptance step.
- [ ] Add a thin bounded CLI/app entry point only after the owner path passes.

Required vertical gate:

Built sidecar + real `WorldQuery` + deterministic model-boundary response -> two
typed directional stance proposals on `proposal/stances`, with distinct distances,
honest calibration state, and no canonical stance mutation.

Then run the logged stance-proposal/CLI suites and `uv run pyright propstore`.

## Workstream D — Predicate and rule extraction completion

### D1. Shared requirements without a new client abstraction

- [ ] Resolve repository paper inputs from the selected `Repository`, never the
  process working directory.
- [ ] Resolve Q4 for durable model evidence.
- [ ] Use lazy LiteLLM calls at each heuristic owner boundary; do not introduce a
  new interface/helper solely to share two small calls.
- [ ] Preserve current typed decoding, rejection, proposal transactions, and
  promotion owners.

### D2. Predicate extraction

- [ ] Replace the raising predicate `_llm_call` with the real model boundary.
- [ ] Add one production adapter. Recommended command:
  `pks proposal propose-predicates`, parallel to `propose-rules`; do not also add
  `pks predicate extract`.
- [ ] Keep manual `pks predicate declare` and existing promotion unchanged.

Gate: command -> model boundary -> typed decode -> existing predicate proposal
owner, with no canonical predicate write; logged predicate lifecycle suites pass.

### D3. Rule extraction

- [ ] Replace only the raising rule `_llm_call` boundary.
- [ ] Keep predicate admission, typed rejections, fixture injection used by tests,
  proposal transaction, and selective promotion unchanged.

Gate: command -> model boundary -> typed admitted/rejected results -> existing rule
proposal owner; logged rule extraction/promotion suites pass.

## Workstream E — Provenance, verification, and views

### E1. Typed indexing foundation

- [ ] Add a source-owner index that enumerates `SourceRef` values and resolves
  source identity and promoted source-claim artifact ids without exposing branch
  parsing to app code.
- [ ] Add one typed claim-provenance index over canonical micropublications.
- [ ] Preserve multiple sources and distinguish unbundled claims from source-less
  claims; do not collapse to a single source.

Gate: one source, multiple sources for one claim, unbundled claim, unknown source,
and source enumeration are covered by focused tests.

### E2. Verification composition

- [ ] Add a typed app request/report combining existing source artifact/origin
  verification with existing world/ATMS claim status.
- [ ] Keep storage verification world-free; composition belongs in app code.
- [ ] Add thin CLI adapters only after the app owner passes.

Gate: mismatched, unstamped, missing-origin, unknown-claim, no-label, and supported
claim cases pass alongside existing tree verification.

### E3. Correct existing views

- [ ] Replace hard-coded missing claim/concept provenance with the canonical
  micropublication index.
- [ ] Replace unavailable claim assumptions with existing bound-world ATMS support.
- [ ] Preserve render-policy visibility and honest unbundled/vacuous states.

### E4. Repository overview

- [ ] Reuse `build_log_report`, `world.conflicts`, and the provenance index.
- [ ] Replace prose-only placeholders with typed activity, provenance, and conflict
  rows.
- [ ] Do not implement conflict ranking or provenance aggregates until Q5 selects
  their semantics; unranked factual rows/counts may land first.

### E5. Neighborhoods

- [ ] Implement concept focus as an app projection over existing world/concept
  view inputs.
- [ ] Implement worldline focus as an app projection over existing definition,
  result dependency, and journal inputs.
- [ ] Implement source focus only after Q5 selects identity and branch/canonical
  scope; keep it in a source-aware app owner, not `WorldQuery`.
- [ ] Add CLI/web adapters only after each app projection passes focused tests.

Workstream E gate:

- Logged verification, app-view, neighborhood, web, history, source, and worldline
  suites pass.
- `uv run pyright propstore` passes.

## Workstream F — Owner-surface disposition

These are explicit dispositions, not an automatic feature backlog.

### Existing behavior to keep

- [ ] Form `show` remains on its existing app owner.
- [ ] Rule and source-derived micropublication mutation remain proposal/source
  owned; no direct mutation commands are added.
- [ ] Test-only alternate repositories remain non-production until deletion-first
  cleanup separately proves they are dead and deletes them.

### Valid missing read owners

- [ ] Add typed app list/show owners for contexts, rules, and micropublications,
  then move CLI presentation to those owners without changing behavior.

### Decision-blocked mutations

- [ ] Form mutation: blocked on Q5 reference/deletion/proposal policy.
- [ ] Context/lifting-rule mutation: blocked on Q5 authoring and reference policy.
- [ ] Micropublication lift inspection: blocked on Q5 bundle-lift semantics.

These blocked items are not plan failures and must not be replaced by direct
family writes.

## Final convergence gate

- [ ] Every implemented phase ends in a focused production-path test, a committed
  kept slice, and the named logged suites.
- [ ] Full logged pytest suite passes.
- [ ] `uv run pyright propstore` passes.
- [ ] No old/new production path coexistence remains for typed classifier results,
  source/provenance indexing, or result-completeness propagation.
- [ ] No stale skip/comment claims a capability is missing when it is production
  wired.
- [ ] Every decision-blocked item remains visibly deferred rather than replaced by
  an inferred policy.
- [ ] Review the plan from top to bottom and verify every phase is complete or
  explicitly deferred by the user before declaring convergence complete.
