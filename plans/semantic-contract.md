# Semantic Contract

Date: 2026-03-23

## Purpose

This document defines the semantic contract for the next implementation phase of propstore.

It exists to do three things:

1. state what the system means right now for the semantic boundaries we are about to change
2. state what implementation behavior is required for those meanings to be true
3. define the proof obligations and compatibility checks that must hold before any round is considered complete

This contract is intentionally narrower than a final ontology.
It is a phase contract, not the last word on the system.

## Status Of This Contract

This contract is authoritative for R0 through R6 of [semantic-foundations-and-atms-plan.md](semantic-foundations-and-atms-plan.md).

It is deliberately written to preserve, not foreclose, the path toward:

- ATMS-style environments, labels, and nogoods
- a stronger proposition/evidence/method/derivation split
- a richer proposal or draft artifact pipeline
- more explicit justification structure

Anything that contradicts those future moves should not be treated as locked in by this document.

## Global Contract Rules

### 1. Source artifacts are authoritative; sidecars are projections

The repository source files under `knowledge/` and their adjacent validated inputs are the semantic authority.

The SQLite sidecar is:

- a compiled projection
- an index
- a query accelerator

The sidecar is not allowed to silently define semantics that the source repository does not have.

Required consequence:

- any semantic input change must invalidate the sidecar projection

### 2. Rival artifacts are preserved, not overwritten

The system is designed to preserve incompatible claims, incompatible contexts, challenge relations, and hypothetical alternatives.

Resolution happens at query or analysis time, not by deleting rival source artifacts.

Required consequence:

- fixes in this phase must not “solve” inconsistency by destructive normalization

### 3. Semantic redesign must not be disguised as compatibility

If behavior changes semantically, that must be:

- named
- tested
- called out in round notes

We do not keep shims merely to avoid acknowledging a semantic change.

### 4. We do not claim full ATMS semantics prematurely

The project may become ATMS-based.
It is not yet entitled to claim ATMS semantics unless environments, labels, and nogoods are first-class in the relevant behavior.

Required consequence:

- interim context behavior must be described as an ATMS-compatible approximation, not as a full ATMS

## Contract: Contexts And Environments

### Meaning

A named context denotes a scoped belief-space input to reasoning.

In the current phase, a context consists of:

- an identifier
- an inheritance relation
- zero or more assumptions
- zero or more exclusions

The active environment for a query is:

- explicit bindings supplied by the caller
- plus the selected named context, if any
- plus the named context’s effective inherited assumptions

This is a near-term environment model, not yet a full ATMS label model.

The bound runtime environment representation for this phase must expose the effective assumptions of the selected context as a discrete enumerable collection.

The contract does not require those assumptions to drive all filtering logic yet.
It does require them to exist as addressable runtime data so later ATMS-style environment work extends the structure instead of replacing it.

### Required Runtime Semantics

If a query binds to context `C`, then:

- claims in `C` are visible
- claims in ancestors of `C` are visible
- claims in unrelated contexts are not visible
- claims with no context remain universally visible unless some future policy explicitly says otherwise

If no context is bound, behavior remains the current broad visibility behavior.

### Required Conflict Semantics

Conflict classification is belief-space relative.

Two claims in unrelated contexts must not be classified as an ordinary overlap or contradiction merely because their values differ.

Near-term required behavior:

- unrelated contexts classify as context phi-nodes before ordinary value or condition conflict classification proceeds
- a context phi-node classification is a classification exit, not an ordinary conflict
- a context phi-node pair must not also receive `CONFLICT`, `OVERLAP`, or other ordinary conflict classes in the same evaluation path unless a later explicit policy re-evaluates cross-context pairs

### Allowed Future Evolution

This contract intentionally leaves open:

- replacing named contexts with assumption-generated contexts
- representing context membership as environment labels rather than row tags
- deriving visibility from minimal assumption sets rather than hierarchy alone

### Proof Obligations

Required example proofs:

- `WorldModel.bind(Environment(..., context_id=...))` and manual `BoundWorld(..., context_hierarchy=...)` agree on visibility for equivalent setups
- build-time and render-time conflict paths agree on unrelated-context handling
- the bound runtime environment representation exposes effective assumptions as discrete enumerable data for a selected context

Required property proofs:

- self-visibility is reflexive
- ancestor visibility holds
- unrelated visibility does not hold
- effective assumptions are monotone under inheritance
- two environments built from different context IDs but identical effective assumption sets and no exclusion differences produce identical visibility results

### Compatibility Expectations

The following must continue to work:

- repositories with no context files
- bindings without `context_id`
- existing tests asserting universal claims remain visible everywhere

## Contract: Stance Graph Integrity

### Meaning

A stance is a first-class directed relation between two extant claims.

Its source claim, target claim, and stance type are part of the semantic graph, not optional annotations.

The current accepted stance types are:

- `rebuts`
- `undercuts`
- `undermines`
- `supports`
- `explains`
- `supersedes`
- `none`

`none` means:

- an explicitly recorded non-relation or reviewed-but-non-epistemic relation between two extant claims
- it may be stored for audit, provenance, or review trace purposes
- it must be ignored by attack/support/defeat computation and must not influence argumentation semantics

### Required Validation Semantics

A stance row is valid only if:

- its source claim exists
- its target claim exists
- its type is recognized

Any authored stance that fails those conditions must not be silently persisted as valid graph structure.

### Required Storage Semantics

The sidecar must enforce the graph contract, not merely describe it.

Required consequence:

- foreign key enforcement must actually be enabled when building the sidecar

### Required Argumentation Semantics

Argumentation procedures may assume:

- stance rows form a graph over extant claims only
- graph queries over active claim IDs do not leak edges to absent nodes

This contract does not yet settle the final support/challenge ontology.
It only requires graph integrity.

### Allowed Future Evolution

This contract intentionally leaves open:

- splitting support and challenge into richer artifact classes
- separate storage for proposal or inferred stance edges
- more expressive stance provenance and confidence semantics

### Proof Obligations

Required example proofs:

- invalid target claims are rejected by validation or build
- invalid stance rows cannot persist in `claim_stance`

Required property proofs:

- persisted stance edges always reference extant claim IDs
- active-subgraph filtering never returns an edge outside the active subgraph

### Compatibility Expectations

The following must continue to work:

- valid inline stances in claim YAML
- valid stance files in the repository stances area
- current argumentation semantics over valid stance graphs

## Contract: Measurements

### Meaning

A measurement claim is evidence or data about a target concept.

It is not semantically identical to a parameter claim.

Its core identity is:

- claim type `measurement`
- `target_concept`
- `measure`
- value or bounds
- provenance

Optional qualifiers such as population or methodology may further refine interpretation.

### Required Query Semantics

A measurement about concept `X` must be reachable from the concept-facing runtime model for `X`.

Near-term acceptable implementations:

- broaden concept-facing claim queries to include `target_concept`
- or add type-aware query methods that the runtime consistently uses

What is not acceptable:

- compiling measurement rows and then making them largely invisible to normal concept reasoning surfaces

### Required Distinction Semantics

Even when measurements become concept-visible:

- they remain type-distinct from parameter claims
- downstream code must still be able to tell that a returned row is a measurement

### Allowed Future Evolution

This contract intentionally leaves open:

- a later evidence/data layer distinct from proposition claims
- richer method or dataset artifacts supporting measurements
- more explicit linkage between measurements and claims they support or challenge

### Proof Obligations

Required example proofs:

- a compiled measurement about concept `X` appears in the runtime query surface for `X`

Required property proofs:

- for any input set containing at least one measurement about concept `X`, the concept-facing runtime query surface for `X` includes at least one measurement row
- measurement visibility is invariant under input claim ordering
- measurement query results are permutation-invariant over equivalent input sets

### Compatibility Expectations

The following must continue to work:

- parameter-only concept queries
- current measurement conflict grouping by `(target_concept, measure)` unless a later contract changes it explicitly

## Contract: Algorithm Claims

### Meaning

An algorithm claim is a claim about a declared output concept, implemented procedurally and dependent on input concepts.

Its semantic owner is the declared output concept in `claim["concept"]`.

Its inputs are dependencies, not ownership keys.

### Required Runtime Semantics

When querying algorithms for concept `X`, the relevant claims are the algorithm claims whose declared output concept is `X`.

### Required Conflict Semantics

Alternative algorithm claims conflict or compare as alternatives for their declared output concept, not as claims belonging to the first input variable concept.

### Allowed Future Evolution

This contract intentionally leaves open:

- a later method or derivation artifact type
- stage-specific pipelines that compose multiple algorithms
- explicit justification or implementation provenance graphs for procedures

### Proof Obligations

Required example proofs:

- conflict attribution for algorithm alternatives follows the declared output concept

Required property proofs:

- algorithm attribution is invariant under variable ordering
- algorithm attribution is invariant under variable renaming where semantics are preserved

### Compatibility Expectations

The following must continue to work:

- current runtime treatment of algorithms as relevant to their declared output concept
- mixed worlds where parameter claims and algorithm claims coexist for the same concept

## Contract: Draft Versus Final Claims

### Meaning

Not every extracted artifact is automatically a valid final claim.

The repository needs a disciplined boundary between:

- draft or proposal-like extracted artifacts
- validated final claims accepted into the main compiler path

### Required Current-Phase Rule

Final observation claims remain semantically strict.

A final observation claim must:

- have a statement
- reference at least one known concept
- satisfy the normal validation contract

The system must not weaken final observation semantics merely because extraction is currently underlinked.

### Required Pipeline Rule

If the research-papers plugin emits artifacts that are not yet concept-linked strongly enough to be final claims, those artifacts must be treated as:

- draft artifacts
- proposal artifacts
- or some other explicitly non-final stage

This contract does not force the exact representation yet.
It does force the distinction.

### Allowed Future Evolution

This contract intentionally leaves open:

- a proposal directory or proposal artifact type
- staged acceptance workflows
- human-in-the-loop concept linking before final compilation

### Proof Obligations

Required example proofs:

- current plugin/compiler mismatch is captured in an explicit round-trip test
- the chosen draft/final boundary behaves consistently end to end

Required property proofs:

- final observations always reference at least one known concept
- draft artifacts, if introduced, are never silently accepted as final claims

### Compatibility Expectations

The following must continue to work:

- existing valid final claim files
- valid plugin outputs that already satisfy final claim requirements

## Contract: Sidecar Projection Integrity

### Meaning

The sidecar is semantically valid only if it reflects the current semantic inputs.

The rebuild key must therefore depend on every input that can change the compiled meaning of the repository.

### Required Semantic Inputs

At minimum, sidecar validity depends on:

- concepts
- claims
- forms
- contexts
- stances
- compiler or schema version markers used to define interpretation

### Required Invalidation Semantics

If any semantic input changes, a normal build must not silently report that the sidecar is unchanged.

### Allowed Future Evolution

This contract intentionally leaves open:

- more granular rebuild keys
- separate caches for subprojections
- explicit migration/version tables inside the sidecar

### Proof Obligations

Required example proofs:

- changing a context, form, or stance input forces rebuild
- changing only the compiler or schema version marker, with no source artifact changes, forces rebuild

Required property proofs:

- changing any semantic artifact changes the rebuild key

### Compatibility Expectations

The following must continue to work:

- stable rebuild behavior when semantic inputs are unchanged
- embedding snapshot or restore behavior, if present, must not bypass semantic invalidation rules

## Test Contract

### TDD Requirement

For each semantic change in this phase:

1. write the specific failing regression first
2. add at least one property test for the corresponding invariant where practical
3. only then change implementation

### Hypothesis Requirement

Hypothesis should be used on invariants that come directly from the literature or from this contract.

Priority areas:

- context visibility and inheritance
- conflict-classification symmetry and non-leakage
- stance graph closure
- query permutation invariance
- rebuild-key sensitivity to semantic inputs

### Compatibility Requirement

Every round must explicitly test:

- no-context repositories
- no-stance repositories
- parameter-only worlds
- valid plugin outputs
- unchanged behavior for intentionally unaffected public surfaces

## Binding Decisions For This Phase

These decisions are binding for R1-R5 unless explicitly amended.

### B1. Near-term environment model

Decision:

- the active environment in this phase is `explicit bindings + selected named context + the selected context's effective inherited assumptions`

Consequence:

- implementations in R1 must not treat `context_id` as a bare visibility tag

### B2. Measurement access contract

Decision:

- the normal concept-facing runtime path must include measurement claims associated via `target_concept`
- the exact store method shape may be either a broadened existing query or a new helper, but runtime behavior must be singular and consistent

Consequence:

- R3 may choose the API shape, but not the semantic outcome

### B3. Draft versus final observation boundary

Decision:

- final observation claims remain strict and concept-linked
- underlinked plugin outputs are not final claims in this phase

Consequence:

- R4 must introduce or use an explicit non-final stage rather than weakening final observation validation

### B4. ATMS scope for this phase

Decision:

- this phase implements environment-correct semantics only
- it does not implement first-class label storage or nogood maintenance as required for a full ATMS

Consequence:

- no implementation in R1-R5 may market itself as a full ATMS layer

## Rename, Move, And Deletion Contract

### Rename Rule

If a change is a pure rename or symbol move:

- prefer tool-backed refactoring support
- otherwise keep scope narrow and verify with exact `rg` checks for the old symbol

No rename is considered complete until the old symbol or path has been mechanically checked and either removed or explicitly documented.

### Deletion Rule

No deletion is allowed merely because a new path now exists.

Code may be deleted in this phase only if:

- its replacement exists
- references have been mechanically checked
- the round gate suite that would catch stale imports is green

### Temporary Artifact Rule

Any temporary shim, helper, or experimental artifact introduced during a round must either:

- be deleted before round close
- or be added explicitly to the execution ledger in the plan

## What This Contract Does Not Settle

This document does not settle:

- the final proposition/evidence/method ontology
- the final ATMS substrate shape
- whether environments eventually become explicit assumption sets, labels, or both
- the final representation of draft artifacts
- final preference or revision policy for contradiction handling

Those remain open intentionally.

## Round-Entry Questions

Before starting any round, ask:

1. What semantic rule from this contract is being changed or enforced?
2. What is the smallest write set that can satisfy that rule?
3. What existing behavior might break?
4. What failing example proves the current defect?
5. What property test proves the broader invariant?
6. Which binding decision in this contract constrains the implementation?

## Round-Close Questions

Before closing any round, answer:

1. Which semantic rule is now better enforced?
2. Which tests prove it?
3. Which compatibility checks were run?
4. Did any public symbol or file path move?
5. Was any code deleted, and if so, where is the proof no references remain?
