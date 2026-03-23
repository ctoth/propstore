# Semantic Foundations And ATMS Plan

Date: 2026-03-23

## Execution Status

- R0: Completed
- R1: Completed
- R2: Completed
- R3: Completed
- R4: Completed
- R5: Completed
- R6: Completed

Baseline verification before implementation:

- Confirmed defects reproduced directly against the current codebase:
  - context binding ignores hierarchy when using `WorldModel.bind()`
  - conflict detection does not apply context-aware pair classification
  - invalid stance targets can persist into `claim_stance`
  - measurement claims compile but are mostly invisible to runtime concept queries
  - sidecar cache invalidation ignores contexts, forms, and stances
  - algorithm conflict attribution follows an input concept instead of the declared output concept
  - plugin-generated observation claims can fail propstore validation immediately
- Relevant regression suites already passing on the current branch:
  - `uv run pytest tests\test_build_sidecar.py tests\test_world_model.py tests\test_contexts.py tests\test_conflict_detector.py -q`
  - Result: `248 passed, 196 warnings`
  - `uv run pytest ..\research-papers-plugin\plugins\research-papers\tests\test_generate_claims.py ..\research-papers-plugin\plugins\research-papers\tests\test_bootstrap_concepts.py ..\research-papers-plugin\plugins\research-papers\tests\test_generate_paper_index.py -q`
  - Result: `31 passed, 1 skipped`

## Purpose

This plan defines the next semantic phase for propstore.

The immediate goal is to resolve the confirmed defects in a way that is faithful to the local literature and that moves the architecture toward a real ATMS-capable core instead of toward a better-organized flat claim store.

This plan is not a bug list. It is a semantic alignment plan.

## Desired End State

The eventual good place is:

- a repository that preserves rival claims, rival supports, rival challenges, and rival hypothetical assumptions without destructive normalization
- a runtime model where belief status is evaluated relative to explicit environments rather than ad hoc row filters
- a context system that can evolve into true ATMS-style environments, labels, and nogoods rather than stopping at named visibility scopes
- an argument layer where support and challenge edges are first-class validated artifacts, not best-effort annotations
- a claim architecture that can separate proposition, evidence, method, derivation, and proposal artifacts when we are ready, without forcing a rewrite of every API
- a compiler that is an indexed projection of repository truth, never a silent semantic fork

The destination is ATMS-compatible semantics with structured argumentation and publication-grade provenance.

This plan should move us toward that destination while deliberately not foreclosing:

- a fuller proposition/evidence/method split
- a more explicit justification graph
- environment labels stored directly on derived artifacts
- nogood maintenance in sidecar or runtime form
- a later transition from named contexts to assumption-generated contexts
- a richer proposal or draft artifact layer between extraction and accepted claims

## Why This Plan Exists

The current code already points in the right direction, but only in pieces.

- `propstore/validate_contexts.py` already models context inheritance, exclusions, and effective assumptions.
- `propstore/world/bound.py` already has a context-aware visibility path.
- `propstore/conflict_detector.py` already defines `_classify_pair_context()`.
- `propstore/argumentation.py` already distinguishes attacks, defeats, and supports in a way that is recognizably Dung plus Cayrol plus Modgil.
- `propstore/build_sidecar.py` already compiles context, conflict, and stance tables that look like a future semantic substrate.

What is missing is semantic closure across those pieces.

Today the system still behaves too much like:

- claims as flat rows
- contexts as optional tags
- measurements as special rows outside the runtime model
- stance edges as semi-validated decorations
- cache rebuild as an optimization hint rather than a semantic guarantee

That is exactly the wrong place to stop if the destination is a real many-worlds, provenance-rich reasoning system.

## Governing Literature Commitments

These commitments are load-bearing.

### 1. Contexts are belief-space semantics, not labels

From Martins 1983, McDermott 1983, de Kleer 1986, Dixon 1993, and Forbus 1993:

- a context or environment determines what is visible, believed, or derivable
- retrieval must be relative to the current belief space
- contradictions outside the active belief space are recorded but should not collapse the active one
- belief revision should be non-destructive: drop assumptions from the active context, do not delete knowledge

Minimum consequence for propstore:

- context must affect runtime querying and conflict interpretation, not just validation and storage

### 2. Argument relations are first-class semantic objects

From Dung 1995, Cayrol 2005, Modgil 2014, Modgil 2018, Clark 2014, and Groth 2010:

- attack, support, and defeat are not interchangeable
- support and challenge relations must be structurally valid before semantics run
- preferences filter attacks into defeats; they do not define incompatibility by themselves
- provenance-bearing claim networks should preserve support and challenge explicitly

Minimum consequence for propstore:

- stance edges must be validated as real graph edges, and the argumentation layer must run on a coherent graph

### 3. Compiler artifacts are projections, not authority

From Groth 2010, Clark 2014, and the compiler/runtime split already present in the codebase:

- the sidecar is a compiled projection over source artifacts
- projections must rebuild whenever model-defining inputs change
- compiled shortcuts must never silently redefine the semantics of the source repository

Minimum consequence for propstore:

- cache invalidation is a semantic guarantee, not a performance nicety

### 4. Measurements and methods are not reducible to parameter assertions

From Clark 2014 and the current schema:

- evidence, data, method, and claim are related but not identical layers
- a measurement is about a target concept, but it is not the same thing as a parameter claim

Minimum consequence for propstore:

- measurement claims must stay distinct in type while still being queryable through the concept they are about

### 5. We should not claim ATMS semantics until labels and environments are real

From de Kleer 1986 and Forbus 1993:

- ATMS semantics means datums labeled by minimal assumption sets
- contexts are derived from environments, not simulated by a single tag
- nogoods and minimality matter

Minimum consequence for propstore:

- near-term work should preserve the path to ATMS, but should not pretend we already have it

## Explicit Non-Goals

This phase does not require:

- a full ATMS implementation in one pass
- immediate storage of full label sets on every datum
- immediate replacement of all current claim tables
- a final proposition/evidence ontology
- a final policy for proposal artifacts
- solving all future belief revision questions now

This phase must not:

- hard-code the current flat claim row model as the permanent semantic center
- weaken validation just to make extraction outputs pass
- use cache shortcuts that can leave the compiled world semantically stale
- introduce “ATMS” naming for mechanisms that are only context filters

## Current Semantic Gaps

### 1. Context semantics are split across validation, storage, and runtime

- Context inheritance and assumptions are validated and stored.
- `BoundWorld` can enforce hierarchy visibility if manually supplied a `ContextHierarchy`.
- `WorldModel.bind()` does not currently supply that hierarchy.
- conflict detection has a context-aware classifier but does not apply it in the main comparison pipeline.

This is the central seam to close first.

### 2. Argument graph integrity is weaker than the reasoning layer assumes

- stance rows can be authored against missing claims
- foreign keys are declared but not effectively enforced unless SQLite foreign keys are enabled
- the argumentation layer assumes it can build a coherent graph from stance rows

This is a semantic integrity breach, not just a validation omission.

### 3. The claim type system is internally inconsistent at runtime

- measurements are stored by `target_concept` but queried mainly by `concept_id`
- algorithm conflicts are grouped by an input concept even though the world model treats algorithms as claims about their declared output concept
- plugin observations are emitted in a draft-like state but validated as final claims

This means the compiler and runtime disagree about what some claim types are.

### 4. The sidecar can become semantically stale

- build hashes do not cover all model-defining artifacts
- the sidecar can therefore disagree with source truth even when the user runs the normal build path

This undermines every higher-level reasoning guarantee.

## Target Architectural Direction

The target direction is:

`Repository artifacts` + `Environment` + `RenderPolicy` + `validated argument graph` => `BeliefSpace`

Longer-term, the same shape should be able to evolve into:

`Repository artifacts` + `assumption vocabulary` + `environment labels` + `nogoods` + `argumentation policy` => `ATMS-capable BeliefSpace`

The near-term architecture should therefore:

- treat named contexts as compiled environment approximations
- keep effective assumptions available and meaningful
- centralize active-belief-space semantics
- avoid APIs that permanently assume “one claim belongs to exactly one flat concept query path”
- preserve enough provenance and structure for later justification-label work

## Design Rules For This Phase

### Rule 1. Fix seams by strengthening semantics, not by patching call sites ad hoc

If context visibility matters, it should be available through the normal world binding path, not only through tests or manual construction.

### Rule 2. Prefer preserving distinct artifact types over flattening them

Measurements, observations, algorithms, supports, and challenges should not be “simplified” into one generic claim path if that loses semantics.

### Rule 3. Where extraction outputs are weaker than validated claims, introduce staging, not validator decay

Raw extraction can be draft-like.
Compiled repository claims should remain semantically meaningful.

### Rule 4. Any interim design should make a full ATMS more possible, not less

Every near-term choice should be checked against this question:

Would a future implementation of labels, environments, and nogoods fit naturally on top of this?

If not, the near-term fix is probably wrong.

### Rule 5. Semantic changes are TDD-first, not patch-first

For every semantic correction:

- write the failing example test first
- add at least one generalized property test where the invariant is broader than the single bug repro
- only then change implementation

This phase should accumulate proofs, not just examples.

### Rule 6. Use property testing where the literature states invariants

Hypothesis is already part of the dev toolchain and already used across the repo.
We should use it much more aggressively on the exact semantic boundaries this phase touches.

If a paper gives us a theorem-like invariant, a monotonicity rule, a symmetry rule, a conflict-freedom rule, or a visibility rule, that should usually become a property test instead of only a hand-picked unit example.

### Rule 7. Renames and symbol moves require refactoring discipline

If a change is a true rename or symbol move rather than a semantic redesign, use refactoring tooling or an equivalent mechanically checked rename path.

Current note:

- `rope` is declared in dev dependencies and importable from the project venv
- there is no standalone `rope` CLI on the current PATH, so any tool-backed rename needs to run through the Python environment or editor integration

Do not do search-and-replace renames in semantic code unless the scope is trivially local and verified immediately by tests and repo-wide search.

## Resolution Decisions

These are the current planning decisions unless later research disproves them.

### D1. Contexts become environment-bearing runtime inputs

Named contexts remain useful, but their semantics must compile to:

- hierarchical visibility
- effective assumptions
- exclusion constraints

Near-term implication:

- `WorldModel.bind()` should bind a real context-aware environment using sidecar context tables or a repository-backed hierarchy loader

Long-term implication:

- named contexts can later become a convenience layer over assumption sets and environment generation

### D2. Conflict detection becomes belief-space aware

Conflict is never purely global.

Near-term implication:

- unrelated contexts classify as context phi-nodes before ordinary conflict classification
- render-time recomputation and build-time conflict population must follow the same rule

Long-term implication:

- conflict status can later be derived from overlap among environments and nogoods instead of only context relations

### D3. Stance validity becomes a hard precondition

Stance edges are not optional metadata. They are part of the argument structure.

Near-term implication:

- validation must reject missing stance targets and invalid types
- sidecar build must enable foreign key enforcement

Long-term implication:

- support and challenge graphs can later be split into richer artifact types without losing integrity

### D4. Measurements remain distinct but become concept-visible

A measurement is evidence about a target concept, not a parameter claim.

Near-term implication:

- concept-facing runtime APIs must include measurement claims associated through `target_concept`
- where necessary, APIs may expose type-aware query variants

Long-term implication:

- measurements can later sit under a fuller evidence or data layer without changing user-level concept access

### D5. Algorithm ownership follows the declared output concept

Inputs are dependencies, not identity.

Near-term implication:

- algorithm conflict grouping must follow `claim["concept"]`
- tests should model algorithms as alternative procedures for the output concept

Long-term implication:

- later method or derivation ontologies can refine procedure identity without changing basic ownership

### D6. Extraction and validated claims are separate stages

The plugin currently emits some observation-like artifacts before concept linking is resolved.

Near-term implication:

- either the plugin must emit valid final observations, or it must emit a draft/proposal artifact shape that propstore does not treat as a final compiled claim

Long-term implication:

- the repository can support a disciplined pipeline from extraction proposal to accepted claim

### D7. Sidecar rebuild depends on the full semantic input set

Near-term implication:

- content hashes must cover concepts, claims, forms, contexts, stances, and a compiler/schema version marker

Long-term implication:

- future semantic layers can safely rely on the sidecar as a projection cache

## Research Questions To Resolve Before Deep Code Work

These questions should be answered explicitly, not implicitly through patches.

### Q1. What is the right near-term environment model?

Options still intentionally open:

- named context plus inherited assumptions plus explicit bindings
- named context compiled into one effective CEL conjunction
- named context as a seed for a more explicit assumption set object

Current planning preference:

- named context plus effective assumptions plus bindings, because it preserves the ATMS path best

### Q2. Should measurement access be folded into `claims_for()` or exposed through a richer query API?

Options still open:

- broaden `claims_for(concept)` to include both `concept_id` and `target_concept`
- add type-aware query methods and make render use them

Current planning preference:

- broaden the concept-facing query path while keeping type distinctions explicit in returned rows

### Q3. What is the minimal acceptable draft artifact for plugin extraction?

Options still open:

- require the plugin to concept-link observations before emission
- introduce a new draft claim type
- introduce a separate proposals area outside final claim validation

Current planning preference:

- keep final claim validation strict and add a draft/proposal stage rather than weakening observation semantics

### Q4. How much of ATMS should be made explicit in this phase?

Options still open:

- no label storage yet, only environment-correct semantics
- partial label storage for derived artifacts
- a parallel experimental ATMS substrate

Current planning preference:

- environment-correct semantics first, with explicit plan hooks for later label and nogood work

## Work Plan

## Execution Protocol

This plan is intended to be mechanically executable.

Round ordering rule:

- R0 must complete before any implementation round
- R1 through R5 must execute in declared order
- R6 may begin after R3 only if R1-R3 are complete and its output is clearly marked as readiness analysis, not implementation authorization

Dependency rule:

- each round's compatibility checks and assumptions are evaluated against the repository state produced by all prior completed rounds

Every round should follow the same protocol:

1. Confirm the round scope and write set.
2. Add or update failing tests first.
3. Run the smallest relevant test slice and confirm failure for the intended reason.
4. Make the implementation change.
5. Re-run the small slice until green.
6. Run the round gate suite.
7. Run the repo search gates.
8. Resolve or explicitly record any compatibility break.
9. Do not move to the next round until all gates pass.

Canonical command style for this repo:

- Python and pytest should be invoked through `uv run`
- Search checks should use `rg`
- File edits should continue to use patch-based edits

Canonical baseline commands:

- focused semantic slice:
  - `uv run pytest tests\test_build_sidecar.py tests\test_world_model.py tests\test_contexts.py tests\test_conflict_detector.py tests\test_validate_claims.py tests\test_argumentation_integration.py -q`
- plugin/compiler handoff slice:
  - `uv run pytest ..\research-papers-plugin\plugins\research-papers\tests\test_generate_claims.py ..\research-papers-plugin\plugins\research-papers\tests\test_bootstrap_concepts.py ..\research-papers-plugin\plugins\research-papers\tests\test_generate_paper_index.py -q`
- broad repo gate:
  - `uv run pytest -q`

Global search gates:

- old symbol or shim checks should use exact `rg` patterns before closeout
- no temporary helper introduced for one round may survive into later rounds without being named here

Temporary artifacts ledger:

- None currently authorized

Deletion ledger:

- No planned module deletions in R1-R5
- If a temporary shim, compatibility helper, or exploratory module is introduced, it must be added to this ledger immediately and deleted in the same round unless the plan is updated explicitly

Rename and move protocol:

1. Decide whether the change is:
   - a pure rename
   - a symbol move
   - a semantic redesign
2. If it is a pure rename or symbol move across multiple files:
   - prefer editor or Python-environment refactoring support
   - if no tool-backed path is practical, keep the scope narrow and verify mechanically with `rg`
3. For every rename or move, record:
   - old symbol or path
   - new symbol or path
   - files expected to change
4. Before closeout, run:
   - `rg -n "<old_symbol_or_old_path>" propstore tests ..\research-papers-plugin`
5. A rename is not complete until that search is empty or every remaining hit is intentional and documented

Compatibility review protocol:

Every round must answer these questions before closeout:

- Does behavior with no contexts still work?
- Does behavior with no stances still work?
- Do parameter-only worlds still behave the same?
- Do valid plugin outputs still pass?
- Did any query surface widen or narrow?
- Did any public symbol or path move?

If any answer is yes for widened or narrowed behavior, the change must be covered by explicit tests and called out in the round notes.

### R0. Freeze The Semantic Contract

Produce a short design note that records:

- what a context means now
- what a measurement means now
- what an algorithm claim is about
- what counts as a valid stance edge
- what the sidecar is allowed to cache

Exit condition:

- we have a written semantic contract that all subsequent changes are judged against
- the contract includes explicit test obligations and compatibility expectations
- Q1-Q4 from this plan are each either decided in the contract or explicitly deferred there with rationale and round ownership

Write set:

- `plans/semantic-contract.md`
- optional updates back into `plans/semantic-foundations-and-atms-plan.md` if the contract changes plan assumptions

Round gates:

- `rg -n "TODO|TBD|decide later|maybe" plans/semantic-contract.md`
- `test -f plans/semantic-contract.md`
- `rg -n "## Binding Decisions For This Phase|### B1\\.|### B2\\.|### B3\\.|### B4\\." plans/semantic-contract.md`

Deletion and rename checks:

- no code deletion expected
- no public rename expected

### R1. Unify Context Semantics Across Build, Runtime, And Conflict Detection

Deliverables:

- repository-backed loading of context hierarchy into the normal world binding path
- runtime use of effective context semantics during active claim filtering
- context-aware pair classification integrated into conflict detection and render-time conflict recomputation
- tests proving that unrelated contexts do not become active together unless a policy explicitly says so

TDD requirements:

- add direct regression tests for the current `WorldModel.bind()` hierarchy gap
- add Hypothesis tests over randomly generated acyclic context hierarchies checking:
  - visibility is reflexive
  - ancestor visibility holds
  - unrelated visibility does not hold
  - binding through the normal world path matches manual context-hierarchy binding for equivalent setups
  - two environments with identical effective assumption sets and no exclusion differences produce identical visibility results
- add compatibility tests proving that builds without contexts still behave exactly as before

Structural readiness requirement:

- the bound runtime environment representation introduced or used in R1 must expose effective assumptions as a discrete enumerable collection, not only as context metadata looked up on demand from YAML or hierarchy files

Refactor discipline:

- if context-loading logic is being moved or renamed across modules, use a tool-backed rename or keep the scope small enough for exhaustive search verification
- no public API rename should land without an explicit repo-wide reference check

Proof obligations:

- `WorldModel.bind(Environment(..., context_id=...))` behaves the same as manual `BoundWorld(..., context_hierarchy=...)` for visibility
- build-time conflicts and render-time conflicts agree on unrelated-context handling
- context phi-node classification acts as a classification exit and does not also produce ordinary conflict classes on the same evaluation path

Primary write set:

- `propstore/world/model.py`
- `propstore/world/bound.py`
- `propstore/conflict_detector.py`
- `propstore/validate_contexts.py` only if hierarchy loading or API additions require it
- `propstore/build_sidecar.py` only if sidecar-backed context loading needs compiler support
- `tests/test_contexts.py`
- `tests/test_world_model.py`
- `tests/test_conflict_detector.py`

Round gates:

- focused context slice:
  - `uv run pytest tests\test_contexts.py tests\test_world_model.py tests\test_conflict_detector.py -q`
- compatibility slice with build:
  - `uv run pytest tests\test_build_sidecar.py tests\test_contexts.py tests\test_world_model.py tests\test_conflict_detector.py -q`

Search gates:

- `rg -n "context_hierarchy" propstore tests`
- `rg -n "_classify_pair_context" propstore tests`
- if any helper is renamed, `rg -n "<old_name>" propstore tests ..\research-papers-plugin`

Deletion and rename checks:

- no module deletion expected
- if any new context-loading helper is introduced only as a bridge, it must either be listed in the temporary artifacts ledger or deleted before round close

### R2. Make Argument Graph Integrity Non-Negotiable

Deliverables:

- stance validation against known claim IDs
- foreign key enforcement enabled in sidecar build
- clear policy for externally-authored stance files and inline claim stances
- tests proving invalid stance targets cannot be persisted

TDD requirements:

- add failing example tests for missing-target and invalid-type stance rows
- add Hypothesis tests generating small claim/stance graphs and asserting:
  - every persisted edge points to an extant node
  - filtering by active claim IDs never returns edges outside the active subgraph
  - attack/support partitioning in the argumentation layer preserves graph closure

Compatibility checks:

- verify that valid authored stance files still compile unchanged
- verify that argumentation semantics over valid graphs are unchanged apart from removal of invalid rows that previously leaked through
- verify that `none` stance rows, if retained, remain audit-only and do not affect attack/support/defeat semantics

Proof obligations:

- a missing target claim causes validation or build failure
- no invalid row can enter `claim_stance`

Primary write set:

- `propstore/validate_claims.py`
- `propstore/build_sidecar.py`
- `propstore/argumentation.py` only if graph closure checks require adjustment
- `tests/test_validate_claims.py`
- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`
- `tests/test_argumentation_integration.py`

Round gates:

- stance integrity slice:
  - `uv run pytest tests\test_validate_claims.py tests\test_build_sidecar.py tests\test_argumentation_integration.py tests\test_world_model.py -q`

Search gates:

- `rg -n "claim_stance|stances_between|FOREIGN KEY \\(claim_id\\)|FOREIGN KEY \\(target_claim_id\\)" propstore tests`
- `rg -n "\"none\"|_NON_ATTACK_TYPES|_ATTACK_TYPES|_SUPPORT_TYPES" propstore tests`
- if validation helpers are renamed, `rg -n "<old_name>" propstore tests ..\research-papers-plugin`

Deletion and rename checks:

- no module deletion expected
- if stance-loading logic is split into helper functions, no dead legacy helper may remain unused at round close

### R3. Reconcile Claim-Type Semantics In Runtime APIs

Deliverables:

- measurement claims visible through concept-centered runtime access
- algorithm conflict grouping and world-model ownership aligned on declared output concept
- tests for mixed parameter, measurement, and algorithm scenarios

TDD requirements:

- add direct regressions for measurement invisibility and algorithm mis-attribution
- add Hypothesis tests generating mixed claim sets and asserting:
  - for any input set containing at least one measurement about concept `X`, the runtime concept-facing query surface for `X` includes at least one measurement row
  - concept-facing measurement access is invariant under claim ordering
  - algorithm conflict attribution is invariant under variable ordering and variable names
  - query results are stable under permutation of input claim files

Compatibility checks:

- verify that existing parameter-only concept queries retain current behavior
- verify that algorithm runtime resolution keeps its current output-concept semantics

Proof obligations:

- measurements about a concept appear in the relevant runtime query surface
- algorithm conflict attribution follows the declared output concept

Primary write set:

- `propstore/world/model.py`
- `propstore/world/bound.py`
- `propstore/conflict_detector.py`
- `propstore/build_sidecar.py` only if row-shape normalization changes
- `tests/test_world_model.py`
- `tests/test_conflict_detector.py`
- `tests/test_build_sidecar.py`

Round gates:

- claim-type semantic slice:
  - `uv run pytest tests\test_world_model.py tests\test_conflict_detector.py tests\test_build_sidecar.py -q`

Search gates:

- `rg -n "target_concept|claims_for\\(|_collect_algorithm_claims|algorithm_for\\(" propstore tests`
- if any method name changes, `rg -n "<old_name>" propstore tests ..\research-papers-plugin`

Deletion and rename checks:

- no module deletion expected
- if a new query helper supersedes an old one, the old helper must either remain intentionally public and tested or be deleted in the same round

### R4. Separate Draft Extraction From Final Claims

Deliverables:

- a decision on where plugin-generated underlinked observations live
- either plugin upgrades to emit valid final claims or a draft/proposal pipeline is introduced
- tests covering the chosen contract end to end

TDD requirements:

- first write the failing round-trip demonstrating the current plugin/compiler mismatch
- then add property tests around the chosen draft/final boundary, for example:
  - final observations always reference at least one known concept
  - draft artifacts, if introduced, are never accepted as final compiled claims by accident

Compatibility checks:

- existing valid plugin outputs must still pass
- any new draft path must not silently widen what `pks build` accepts as final knowledge

Cross-repo coordination protocol:

- plugin changes must be tested against the propstore branch state produced by prior rounds, not against plugin `main` in isolation
- R4 closeout must record the exact compatible plugin commit if the plugin remains a separate repository
- no propstore-side validator tightening may be closed out without the paired plugin/validator round-trip gate passing

Proof obligations:

- generated plugin outputs no longer fail immediately at the propstore boundary unless they are intentionally draft artifacts rejected by final compilation

Primary write set:

- `..\research-papers-plugin\plugins\research-papers\scripts\generate_claims.py`
- `propstore/validate_claims.py`
- possibly one new repository-side draft/proposal module or schema file if that is the chosen design
- `..\research-papers-plugin\plugins\research-papers\tests\test_generate_claims.py`
- `tests/test_validate_claims.py`
- any new round-trip integration test file if needed

Round gates:

- plugin/validator handoff slice:
  - `uv run pytest ..\research-papers-plugin\plugins\research-papers\tests\test_generate_claims.py tests\test_validate_claims.py -q`
- plugin broader slice:
  - `uv run pytest ..\research-papers-plugin\plugins\research-papers\tests\test_generate_claims.py ..\research-papers-plugin\plugins\research-papers\tests\test_bootstrap_concepts.py ..\research-papers-plugin\plugins\research-papers\tests\test_generate_paper_index.py -q`

Round notes requirement:

- record the compatible plugin revision or working tree state used for R4 verification

Search gates:

- `rg -n "\"type\": \"observation\"|\"concepts\": \\[\\]" ..\research-papers-plugin\plugins\research-papers tests propstore`
- if a draft artifact name is introduced, `rg -n "<draft_type_or_module_name>" propstore tests ..\research-papers-plugin`

Deletion and rename checks:

- if a temporary draft shape or compatibility bridge is introduced, it must be listed in the temporary artifacts ledger
- if a draft module is created as a permanent part of the architecture, it must be named in the semantic contract before round close

### R5. Restore Projection Integrity

Deliverables:

- semantic cache key covers all model-defining artifacts
- compiler/schema version incorporated into invalidation
- tests proving context, form, and stance changes force rebuild

TDD requirements:

- add one failing regression per omitted artifact class
- add Hypothesis tests over subsets of semantic inputs asserting:
  - changing any hashed semantic artifact changes the rebuild key
  - changing non-semantic output noise does not necessarily have to
- add one regression proving that changing only the compiler or schema version marker forces rebuild

Compatibility checks:

- rebuild behavior should remain stable when the semantic input set is unchanged

Proof obligations:

- any change to semantic inputs invalidates the sidecar

Primary write set:

- `propstore/build_sidecar.py`
- `tests/test_build_sidecar.py`
- `tests/test_contexts.py` if context artifacts participate in rebuild assertions

Round gates:

- rebuild integrity slice:
  - `uv run pytest tests\test_build_sidecar.py tests\test_contexts.py -q`

Search gates:

- `rg -n "_content_hash|with_suffix\\(\"\\.hash\"\\)|force=False|Build unchanged|Build rebuilt" propstore tests`

Deletion and rename checks:

- no module deletion expected
- any retired hash helper must be deleted if it no longer participates in rebuild decisions

### R6. ATMS Readiness Pass

This round does not implement a full ATMS unless the earlier rounds make it obviously tractable.

Deliverables:

- explicit inventory of what is still missing for a true ATMS layer:
  - assumption atoms
  - justification representation
  - labels
  - nogoods
  - minimality maintenance
  - revision policy
- recommendation for whether the next plan should be:
  - full ATMS substrate
  - partial ATMS labeling
  - proposition/evidence split first

Exit condition:

- we can say precisely what “doing the full ATMS” would mean in this codebase instead of using it as a slogan
- we also know which current APIs, names, and storage shapes would survive that move versus which are transitional
- R6 produces multiple executable property tests, preferably Hypothesis-based, that exercise assumption-based environment structure and would fail if visibility were computed from context identity alone
- at minimum, R6 must add more than one such property test and they must cover distinct invariants rather than minor variations of the same assertion

Minimum R6 property-test scope:

- one property proving visibility behavior is a function of effective assumptions rather than context identity alone
- one property proving the environment representation exposes assumption structure in a way that is stable under equivalent constructions
- one additional property chosen from:
  - exclusion behavior under equivalent assumption sets
  - monotonicity or non-monotonicity boundaries for inherited assumptions
  - consistency between runtime environment semantics and conflict classification semantics

Write set:

- one new note in `plans/` describing the ATMS readiness inventory and next-step recommendation
- optional updates to `plans/semantic-contract.md`

Round gates:

- `test -d plans`
- `rg -n "ATMS|environment label|nogood|justification" plans`

Deletion and rename checks:

- no code deletion expected unless a temporary exploratory artifact was created earlier and is now being removed

## Testing Posture

This phase should be executed as strict semantic TDD.

For each round:

1. Capture the current defect with a specific failing test.
2. Add at least one property test for the governing invariant.
3. Run the smallest affected test slice while implementing.
4. Run the broader semantic regression slice before closing the round.

The repo already uses Hypothesis well in:

- `tests/test_dung.py`
- `tests/test_dung_z3.py`
- `tests/test_preference.py`
- `tests/test_property.py`
- `tests/test_world_model.py`
- `tests/test_argumentation_integration.py`

This phase should extend that style into:

- `tests/test_contexts.py`
- `tests/test_conflict_detector.py`
- `tests/test_build_sidecar.py`
- `tests/test_validate_claims.py`
- plugin round-trip tests where extraction meets compilation

## Hypothesis Strategy

Hypothesis should target literature-backed invariants, not random surface fuzzing.

Priority property families:

### P1. Context and environment properties

- ancestor visibility is transitive
- self-visibility is reflexive
- unrelated contexts are not visible absent explicit relation
- effective assumptions are monotone under inheritance
- activating a more specific context never hides its ancestors' claims

### P2. Conflict-classification properties

- pair classification is symmetric under claim order
- unrelated contexts cannot produce ordinary conflicts
- equivalent conditions produce order-invariant classifications
- compatible values never become conflicts under permutation

### P3. Argument graph properties

- persisted stance edges form a graph over extant claim IDs only
- AF construction never introduces arguments not in the active set
- support-derived defeats never reference missing nodes
- justified-claim computation returns subsets of active claim IDs

### P4. Query and compilation properties

- concept-facing query results are permutation-invariant over input file order
- rebuild keys change when semantic inputs change
- valid final observations always remain concept-linked
- algorithm ownership follows output concept regardless of variable names

Hypothesis should be used conservatively where setup cost is high, but the default question should be:

What invariant from the papers can we encode here?

## Refactor And Rename Discipline

Not every change in this phase is a rename. Most are semantic corrections.

But when a change is primarily a rename, move, or API shape update:

1. Prefer tool-backed rename through editor integration or a Python-driven `rope` workflow.
2. If that is impractical, keep the rename scope narrow and prove it with:
   - targeted tests
   - repo-wide `rg` checks for the old symbol
   - no leftover compatibility shims unless they are explicitly temporary and scheduled for deletion
3. Distinguish clearly between:
   - pure rename
   - boundary refactor
   - semantic redesign

This matters because semantic redesign should not hide inside a rename patch.

Current expectation for this plan:

- context and stance work is mostly semantic redesign, not rename work
- measurement visibility changes are query-contract changes, not simple renames
- algorithm ownership changes are semantic alignment, not simple renames
- if new type or method names are introduced to clarify transitional concepts, they should be introduced deliberately and searched globally

## Compatibility And Breakage Review

Every round should explicitly ask what might break in the existing system.

Minimum checks:

- behavior with no contexts present
- behavior with no stances present
- parameter-only worlds
- existing valid plugin outputs
- CLI build and query flows
- render/analyzer behavior that currently depends on stored sidecar conflicts

We should assume some semantic behavior will intentionally change.
That is acceptable.

What is not acceptable is accidental breakage caused by:

- widening or narrowing query surfaces without tests
- changing a public method contract implicitly
- leaving stale compatibility shims that hide unfinished migration
- introducing new names for old semantics that confuse the ATMS path

## Round Closeout Checklist

No round is complete until all of the following are true:

- round-scoped tests are green
- relevant property tests are present and green
- relevant compatibility checks are green
- repo search gates are clean
- any rename checks for the round are clean
- any temporary artifact introduced by the round is either deleted or added explicitly to the ledger
- no dead code remains from an abandoned implementation attempt in touched files

Mechanical dead-code checks for touched files:

- `rg -n "TODO|FIXME|XXX|pass  #|pass$|return None  # temporary|temporary shim|compatibility shim" <touched_files>`
- `rg -n "<old_symbol>" propstore tests ..\research-papers-plugin`

If code is deleted in a future update to this plan, the round must also include:

- an explicit deletion list in the deletion ledger
- a repo-wide search proving no imports or references remain
- the smallest test slice that would catch a stale import path

## Verification Strategy

Every round should add executable proof before implementation closes.

Preferred proof shape:

- immutable `pytest` regressions for each confirmed defect
- targeted integration tests over build plus world-model behavior
- direct repro tests for cache invalidation and plugin handoff boundaries

Minimum proof expectations by area:

- contexts: runtime and build-time consistency checks
- stances: validation and persistence checks
- measurements: query-surface visibility checks
- algorithms: ownership and conflict-key checks
- cache: repeated build behavior under changed inputs
- plugin: extraction-to-validation round-trip checks

## Architectural Risks To Avoid

### 1. Fake ATMS terminology

Do not rename context filters to “environments” and declare victory.

### 2. Semantic flattening

Do not solve runtime inconsistency by forcing measurements, algorithms, and observations into one undifferentiated query model.

### 3. Validator weakening

Do not make final claim validation looser just because extraction emits draft-quality artifacts.

### 4. Compiler drift

Do not let sidecar convenience logic silently redefine what repository truth means.

### 5. Premature ontology closure

Do not let near-term fixes imply that the current `claim` table is the final semantic atom of the system.

## What Should Be Written Next

After this plan is accepted, the next documents in `./plans/` should be:

1. a short semantic contract note for contexts, stances, measurements, algorithms, and drafts
2. a focused implementation plan for R1 through R3 with exact target files and tests
3. a separate ATMS-readiness note after R3 or R4, depending on what the implementation reveals

## Success Criteria

This phase is successful if all of the following are true:

- the confirmed defects are resolved with executable proof
- the runtime semantics align materially better with Martins, McDermott, de Kleer, Dixon, Dung, Cayrol, Modgil, Clark, Groth, and Forbus
- the codebase is more ready for a real ATMS than it is today
- we have not foreclosed a richer proposition/evidence/derivation architecture
- “doing the full ATMS” becomes a concrete next architectural decision rather than an ambiguous aspiration
