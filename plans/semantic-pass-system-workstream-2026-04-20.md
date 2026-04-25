# Semantic Pass System Workstream - 2026-04-20

## Purpose

Propstore needs a single explicit semantic pass system for every semantic
artifact family. The current code already has pass-like behavior, but it is
distributed across validators, app workflows, import normalizers, sidecar
populate functions, and runtime reasoners without a shared stage contract.

The target architecture is nanopass-shaped:

1. Name every intermediate semantic stage.
2. Represent each stage with typed objects, not loose payload dictionaries.
3. Represent every transformation or invariant check as a declared pass class.
4. Register pass classes declaratively in family-owned pass lists.
5. Run pipelines through a shared runner that validates family, stage, and order.
6. Delete old monolithic validators and implicit pass paths as their production
   callers move to the new pass system.

This is not a compatibility layer around `validate_concepts` or
`propstore.compiler.passes`. It is the replacement surface.

## Nanopass Interpretation

The nanopass paper's useful design constraint is not merely "many small
functions." It is "many small transformations over named intermediate
languages." Verification passes are normal passes; they may have the same input
and output stage. A pass declaration is therefore both executable code and a
machine-checkable statement of what invariants are supposed to hold.

For propstore, "language" means a typed semantic stage such as:

- `concept.authored`
- `concept.normalized`
- `concept.bound`
- `concept.checked`
- `claim.authored`
- `claim.normalized`
- `claim.bound`
- `claim.checked`
- `repository.checked`
- `sidecar.rows`

## Target Package Shape

Chosen long-term ownership: each semantic family owns its document schema,
identity, stages, and passes in one family package. Do not create
`propstore/families/concepts/passes/` while leaving
`propstore/families/documents/concepts.py` as a separate competing concept
owner. For each family touched by this workstream, collapse the family surface
instead of adding a parallel package.

Shared pass infrastructure:

```text
propstore/semantic_passes/
  __init__.py
  types.py
  diagnostics.py
  registry.py
  runner.py
```

Family-owned stages and pass classes:

```text
propstore/families/concepts/
  __init__.py
  documents.py
  identity.py
  stages.py
  passes/
    __init__.py
    identity.py
    forms.py
    lexical.py
    relationships.py
    parameterization.py
    cel.py
    deprecation.py

propstore/families/claims/
  __init__.py
  documents.py
  identity.py
  stages.py
  passes/
    __init__.py
    identity.py
    references.py
    contracts.py
    cel.py
    units.py
    equations.py
    algorithms.py
    stances.py

propstore/families/forms/
  __init__.py
  documents.py
  stages.py
  passes.py

propstore/families/contexts/
  __init__.py
  documents.py
  stages.py
  passes.py
```

Sidecar row compilation is sidecar-owned:

```text
propstore/sidecar/
  stages.py
  passes.py
```

Family checked stages are the input to sidecar row passes. This avoids mutual
imports between family pass modules and `propstore/sidecar/schema.py`.

The old `propstore/families/documents/*` and `propstore/families/identity/*`
modules are deleted family-by-family as their contents move into the new family
packages.

## Pass Contract

Every pass class declares its metadata. The pass registry is a list of classes,
not a string configuration file.

```python
class SemanticPass[InT, OutT](Protocol):
    family: PropstoreFamily
    name: str
    input_stage: StageId
    output_stage: StageId

    def run(self, value: InT, context: CompilationContext) -> PassResult[OutT]:
        ...
```

Verification-only passes use the same input and output stage. Transformation
passes change the output stage.

Registration remains declarative, but it must be lazy. Do not use a global
tuple literal that imports every family pass module when `propstore` or the CLI
root imports.

```python
def register_concept_pipeline(registry: PipelineRegistry) -> None:
    registry.register(ConceptNormalizePass)
    registry.register(ConceptIdentityPass)
    registry.register(ConceptFormBindingPass)
    ...
```

The runner must fail fast when:

- a pass is registered under the wrong family,
- a pass's `input_stage` does not match the current stage,
- two passes in a family declare the same `name`,
- a pipeline is requested for an unknown target stage,
- a pass returns diagnostics without a stage-typed output when output is
  required,
- a production caller asks for a checked stage but only an unchecked stage was
  produced.

The first runner is intentionally linear. No DAG scheduler, conditional pass
graph, pass discovery, optimizer, or plugin API belongs in this workstream.
Explicit lazy registration and declared order are enough.

## Shared Typed Outputs

Initial shared types:

- `StageId`
- `PassDiagnostic`
- `PassResult[T]`
- `PipelineResult[T]`
- `FamilyPipeline`
- `PipelineRegistry`

Stage IDs are per-family enum-like types, not free strings:

```python
class ConceptStage(str, Enum):
    AUTHORED = "concept.authored"
    NORMALIZED = "concept.normalized"
    BOUND = "concept.bound"
    CHECKED = "concept.checked"
```

`PassDiagnostic` is canonical for every migrated family. Old diagnostic shapes
may remain only in untouched families during intermediate slices. Once a family
migrates, its production callers must not convert back to `ValidationResult`.
`ValidationResult`, `SemanticDiagnostic`, and `WorkflowMessage` are deleted when
concepts and claims have moved.

`CompilationContext` stays in scope. Do not rename it to `SemanticContext` in
this workstream.

## Loose Transformations Inventory

This inventory is the current scope surface. A transformation is "loose" if it
changes semantic shape, binds references, derives identity, validates invariants,
or compiles storage/runtime products outside an explicit pass contract.

### Shared diagnostics and workflow reporting

Current surfaces:

- `propstore/diagnostics.py`
- `propstore/compiler/workflows.py`

Loose behavior:

- `ValidationResult` is a legacy string-list container.
- `SemanticDiagnostic` is claim-oriented and converted back into
  `ValidationResult`.
- `WorkflowMessage` is a third diagnostic/reporting shape.
- Repository validation/build orchestration manually converts between these
  surfaces.

Target:

- `PassDiagnostic` is the internal diagnostic type.
- CLI/app reports render diagnostics from pipeline results.
- For migrated families, production semantic ownership uses `PassDiagnostic`
  only.
- `ValidationResult`, `SemanticDiagnostic`, and `WorkflowMessage` are deleted
  after contexts, forms, concepts, and claims have migrated far enough that no
  production caller needs them.

### Existing compiler pass system

Current surfaces:

- `propstore/compiler/passes.py`
- `propstore/compiler/claim_checks.py`
- `propstore/compiler/ir.py`
- `propstore/compiler/context.py`
- `propstore/compiler/references.py`

Loose behavior:

- `compile_claim_files` performs normalization assumptions, binding,
  identity validation, CEL checking, contract validation, stance validation,
  and semantic checks in one function.
- `SemanticClaim.authored_claim` and `SemanticClaim.resolved_claim` are
  `dict[str, Any]`.
- Claim semantic checks are string tokens in `ClaimTypeContract`.
- Reference binding is real, but it is not represented as a declared pass.
- `ClaimCompilationBundle` is a useful typed handoff, but the pass sequence
  that produces it is implicit.

Target:

- Delete `propstore/compiler/passes.py` as a production owner once claim family
  passes replace it.
- Move claim pass classes under `propstore/families/claims/passes/`.
- Keep `CompilationContext` as the shared symbol table for this workstream.
- Replace loose claim dictionaries with typed authored/normalized/bound/checked
  claim stage objects.

### Concepts

Current surfaces:

- `propstore/validate_concepts.py`
- `propstore/core/concepts.py`
- `propstore/app/concepts.py`
- `propstore/compiler/context.py`
- `propstore/source/registry.py`
- `propstore/sidecar/concepts.py`

Loose behavior:

- `validate_concepts` owns identity, version, form, lemon, qualia,
  description-kind, relationship, CEL, parameterization, dimensional,
  canonical-claim, and deprecation checks.
- `normalize_loaded_concepts`, `parse_concept_record_document`,
  `concept_document_to_record_payload`, `rewrite_concept_payload_refs`, and
  `build_authored_concept_registry` are meaningful semantic transformations
  without pass declarations.
- `app/concepts.py` mutates concept payload dictionaries directly for add,
  rename, deprecate, link, qualia, role bundles, category values, CEL condition
  rewrites, and related claim condition rewrites.
- `source/registry.py` projects source-local concepts into canonical-looking
  dictionaries and rewrites parameterization inputs.
- `sidecar/concepts.py` compiles concepts into SQL rows, aliases,
  relationships, parameterizations, parameterization groups, form algebra, and
  FTS rows.

Target concept stages:

- `ConceptAuthoredSet`
- `ConceptNormalizedSet`
- `ConceptBoundRegistry`
- `ConceptCheckedRegistry`
- `ConceptSidecarRows`

Initial concept passes:

- `ConceptNormalizePass`
- `ConceptIdentityPass`
- `ConceptFormBindingPass`
- `ConceptLexicalInvariantPass`
- `ConceptRelationshipBindingPass`
- `ConceptCelConditionPass`
- `ConceptParameterizationPass`
- `ConceptDeprecationGraphPass`
- `ConceptSidecarRowsPass`

### Forms

Current surfaces:

- `propstore/form_utils.py`
- `propstore/compiler/workflows.py`
- `propstore/sidecar/concepts.py`
- `propstore/dimensions.py`

Loose behavior:

- Form parsing and registry construction are spread across `parse_form`,
  `load_all_forms_path`, repository workflows, and sidecar build.
- Form validation logic is duplicated in `validate_form_files` and
  repository validation/build.
- Form algebra is derived from concept parameterizations during sidecar
  population instead of from a checked concept/form stage.

Target form stages:

- `FormAuthoredSet`
- `FormNormalizedRegistry`
- `FormCheckedRegistry`

Initial form passes:

- `FormNormalizePass`
- `FormDimensionPolicyPass`
- `FormRegistryPass`
- `FormSidecarRowsPass`

### Claims

Current surfaces:

- `propstore/families/documents/claims.py`
- `propstore/claims.py`
- `propstore/compiler/passes.py`
- `propstore/compiler/claim_checks.py`
- `propstore/compiler/references.py`
- `propstore/sidecar/claims.py`
- `propstore/sidecar/claim_utils.py`
- `propstore/description_generator.py`

Loose behavior:

- Claim type contracts are declarative, but execution is not pass-class based.
- `compile_claim_files` binds concepts, target concepts, variables,
  parameters, and stance targets while also validating identity and semantics.
- `populate_claims` can accept either a semantic bundle or raw claim files,
  preserving a dual path.
- `prepare_claim_insert_row` and related sidecar helpers compile claim payloads
  into row shapes outside the pass system.
- Description generation consumes loose claim/concept dictionaries.

Target claim stages:

- `ClaimAuthoredFiles`
- `ClaimNormalizedFiles`
- `ClaimBoundBundle`
- `ClaimCheckedBundle`
- `ClaimSidecarRows`

Initial claim passes:

- `ClaimNormalizePass`
- `ClaimIdentityPass`
- `ClaimReferenceBindingPass`
- `ClaimContractPass`
- `ClaimCelConditionPass`
- `ClaimUnitCompatibilityPass`
- `ClaimEquationPass`
- `ClaimAlgorithmPass`
- `ClaimStancePass`
- `ClaimSidecarRowsPass`

### Contexts

Current surfaces:

- `propstore/context_types.py`
- `propstore/validate_contexts.py`
- `propstore/context_lifting.py`
- `propstore/sidecar/schema.py`

Loose behavior:

- `parse_context_record`, `parse_context_record_document`, and
  `loaded_contexts_to_lifting_system` are transformations without stage names.
- `validate_contexts` checks ID presence, uniqueness, and lifting-rule
  endpoints in one monolithic validator.
- Context assumptions become lifting-system inputs outside a declared pass.

Target context stages:

- `ContextAuthoredSet`
- `ContextNormalizedSet`
- `ContextBoundGraph`
- `ContextCheckedGraph`

Initial context passes:

- `ContextNormalizePass`
- `ContextIdentityPass`
- `ContextLiftingBindingPass`
- `ContextLiftingGraphPass`

### Sources and source-local artifacts

Current surfaces:

- `propstore/source/*`
- `propstore/storage/repository_import_normalization.py`
- `propstore/claim_references.py`
- `propstore/artifact_codes.py`
- `propstore/families/documents/sources.py`

Loose behavior:

- Repository import normalizers rewrite concepts, claims, and stances in a
  private ordering keyed by family.
- Source concept projection derives canonical artifact IDs and rewrites
  parameterization inputs without a stage contract.
- Claim reference indexes rewrite local/source references into canonical
  targets.
- Artifact-code attachment mutates source, claim, justification, and stance
  dictionaries together.

Target source stages:

- `SourceAuthoredBundle`
- `SourceNormalizedBundle`
- `SourceBoundBundle`
- `SourcePromotionPlan`
- `SourceArtifactCodeBundle`

Initial source passes:

- `SourceNormalizePass`
- `SourceReferenceBindingPass`
- `SourceConceptProjectionPass`
- `SourceClaimPromotionPass`
- `SourceStancePromotionPass`
- `SourceArtifactCodePass`

Source-local passes must not leak source-local-only fields into canonical
family stages. Promotion is the transformation boundary.

### Stances, justifications, micropublications

Current surfaces:

- `propstore/sidecar/claims.py`
- `propstore/claim_references.py`
- `propstore/families/documents/stances.py`
- `propstore/families/documents/sources.py`
- `propstore/families/documents/micropubs.py`

Loose behavior:

- Authored stances and justifications are validated mostly while populating the
  sidecar.
- Stance target/source resolution uses sidecar claim-reference maps rather than
  a family checked stage.
- Justification premise/conclusion resolution is embedded in SQL population.
- Micropublication lifting lives outside a general family pass shape.

Target:

- First-scope work is only to lift semantic checks out of sidecar population.
- Bind claim/context references before SQL population.
- Sidecar population consumes checked/bound family products only.
- Do not create full standalone stance/justification/micropub family pipelines
  in the first workstream unless a deletion slice requires them.

### Sidecar build

Current surfaces:

- `propstore/sidecar/build.py`
- `propstore/sidecar/concepts.py`
- `propstore/sidecar/claims.py`
- `propstore/sidecar/schema.py`
- `propstore/sidecar/rules.py`

Loose behavior:

- `build_sidecar` reloads families, builds contexts, builds concept registries,
  compiles claims, collects raw-id diagnostics, populates SQL tables, restores
  embeddings, and writes hash files.
- Populate functions perform semantic compilation as well as SQL insertion.
- `populate_claims` keeps a semantic-bundle path and a raw-claim-file path.
- Raw-id quarantine is a typed partial product, but it is not part of a declared
  pass output.

Target:

- Repository semantic pipeline produces `RepositoryCheckedBundle`.
- Sidecar pipeline consumes `RepositoryCheckedBundle` and produces
  `SidecarBuildPlan`.
- SQL population inserts rows from typed sidecar row bundles.
- Delete raw claim-file sidecar population paths.

### Grounding and ASPIC bridge

Current surfaces:

- `propstore/grounding/*`
- `propstore/aspic_bridge/*`
- `propstore/structured_projection.py`

Loose behavior:

- `grounding.grounder.ground` already behaves like a pass and returns a typed
  `GroundedRulesBundle`, but it is not registered as one.
- Translation to gunray theory, gunray evaluation, section normalization, and
  optional argument enumeration are separate conceptual passes inside one
  function.
- ASPIC bridge compilation and projection consume bundles but are not declared
  pipeline stages.

Scope decision:

- Do not include grounding or ASPIC bridge registration in the first pass-system
  workstream.
- Record these as future runtime stage-contract candidates only.
- `GroundedRulesBundle` is already a typed handoff; there is no validator
  monolith to delete here.

### World, ATMS, and worldline runtime

Current surfaces:

- `propstore/world/model.py`
- `propstore/world/bound.py`
- `propstore/world/resolution.py`
- `propstore/world/types.py`
- `propstore/worldline/*`
- `propstore/support_revision/*`

Loose behavior:

- `WorldModel.bind` constructs `BoundWorld` and queryable assumptions outside
  the pass system.
- Resolution, derived values, merge operators, render policies, ATMS labels,
  and worldline materialization each have local normalization/coercion layers.
- Worldline result types are much more typed than older surfaces, but the
  transformation from sidecar/world state to result reports is not declared as
  a pass sequence.

Target:

- Exclude runtime reasoning from this workstream.
- Treat `WorldModel.bind`, ATMS inspection, support revision, and worldline
  materialization as a later runtime stage-contract workstream after canonical,
  source, and sidecar stages are stable.

## Contract Manifest

After at least two real family pipelines exist, `propstore/contracts.py` should
emit pass contracts in addition to document schema, family, foreign-key, and
claim-type contracts. Do not make manifest output part of the first context-only
slice; otherwise the manifest may freeze the wrong abstraction.

Each emitted pass contract should include:

- `kind: semantic_pass`
- `name`
- `family`
- `input_stage`
- `output_stage`
- `class`
- `diagnostic_codes`
- `required_context`

The manifest should also include stage contracts:

- `kind: semantic_stage`
- `name`
- `family`
- `class`
- `invariants`

## Implementation Order

### Phase 1 - Substrate plus contexts

Create the minimal `propstore/semantic_passes` substrate needed for one real
family and immediately migrate contexts. The substrate must land with a
production deletion; no toy-only pass framework ships.

Exit criteria:

- `propstore/semantic_passes` exists with typed diagnostics, pass results, stage
  enums, lazy pipeline registration, and a linear runner.
- Repository validation/build call the context pipeline.
- `propstore/validate_contexts.py` is deleted.
- `propstore/families/documents/contexts.py` moves to
  `propstore/families/contexts/documents.py`.
- Context record/stage ownership moves out of `propstore/context_types.py` for
  the migrated production path.
- Context diagnostics use `PassDiagnostic`; untouched families may still use old
  diagnostic shapes until their slices move.

### Phase 2 - Forms

Move form document, registry, and validation ownership into the form family
package. Do not emit pass contracts until this second real family pipeline is
in place.

Exit criteria:

- `propstore/families/documents/forms.py` moves to
  `propstore/families/forms/documents.py`.
- Form parsing/registry stage ownership moves out of `propstore/form_utils.py`
  for the migrated production path.
- `propstore/form_utils.py::validate_form_files` is deleted or reduced to a
  non-production CLI rendering adapter; it must not own form semantics.
- Form validation duplication in `compiler/workflows.py` is gone.
- Repository validation/build call the form pipeline.
- Pass and stage contracts are emitted from `contracts.py`.

### Phase 3 - Concepts

Replace `validate_concepts` with family-owned concept passes and typed concept
stage objects.

Exit criteria:

- `propstore/validate_concepts.py` is deleted.
- `rg -F "validate_concepts"` returns zero production references.
- Concept app mutations validate by running the concept pipeline to
  `concept.checked`.
- Source concept projection uses explicit source/concept passes.
- Sidecar concept population consumes checked concept stages.

Known production callers to eliminate:

- `propstore/compiler/workflows.py`
- `propstore/app/concepts.py`

Test imports are updated after production callers move; they are not evidence
that the old module should survive.

### Phase 4 - Claims and current compiler pass cleanup

Move `propstore/compiler/passes.py` and `claim_checks.py` logic into
`propstore/families/claims/passes`.

Exit criteria:

- `propstore/compiler/passes.py` is deleted.
- `propstore/compiler/claim_checks.py` is deleted.
- `compile_claim_files` production callers use the semantic pass runner through
  the claim family pipeline, not a wrapper.
- `SemanticClaim.resolved_claim` is no longer a dict.
- Claim type contracts reference pass classes or semantic check classes, not
  string tokens.
- Claim quarantine records are produced by the claim pipeline, not by
  `sidecar/build.py`.

### Phase 5 - Source promotion/import

Move repository import normalization, source concept projection, local claim
reference rewriting, and artifact-code attachment into source-family passes.

Exit criteria:

- `propstore/storage/repository_import_normalization.py` is deleted as a
  production semantic transformation owner.
- Source-local fields are rejected at canonical boundaries.
- Promotion emits typed promotion plans before repository mutation.
- This phase does not begin until canonical concept and claim pipelines both
  produce checked bundles.

### Phase 6 - Sidecar row compilation

Separate semantic sidecar row compilation from SQL insertion.

Exit criteria:

- Sidecar build consumes `RepositoryCheckedBundle`.
- SQL populate functions insert typed row bundles.
- No populate function performs reference binding or family semantic
  validation.
- `propstore/sidecar/claims.py::populate_claims` raw claim-file branch is
  deleted.
- This phase does not begin until concepts and claims both produce checked
  bundles.

### Deferred - Runtime stage contracts

Grounding, ASPIC bridge, world binding, ATMS, support revision, and worldline
evaluation are deferred to a later runtime stage-contract plan.

## Deletion-First Rules For This Workstream

- Do not add `validate_concepts2`, `compile_claim_files2`, or parallel "new"
  APIs.
- For each family slice, define the target stage objects first, then delete or
  empty the old production owner, then fix callers against compiler/test/search
  failures.
- Do not keep raw and checked paths in sidecar population.
- Do not keep dict payload and typed stage paths in claims once the typed path
  exists.
- Do not add compatibility shims for older repository shapes unless explicitly
  required by an external compatibility target.

Deletion checklist:

- `propstore/validate_concepts.py`
- `propstore/validate_contexts.py`
- `propstore/compiler/passes.py`
- `propstore/compiler/claim_checks.py`
- `propstore/compiler/workflows.py::WorkflowMessage`
- `propstore/compiler/workflows.py::RepositoryValidationReport`
- `propstore/diagnostics.py::ValidationResult`
- `propstore/diagnostics.py::SemanticDiagnostic`
- `propstore/storage/repository_import_normalization.py`
- Raw claim-file branch of `propstore/sidecar/claims.py::populate_claims`

Each phase must remove at least one item from this list or explicitly state why
the phase is blocked. Passing tests with all old production paths still present
is not completion.

## Non-Goals

- No runtime world/ATMS pass registration.
- No grounding/ASPIC pass registration.
- No public plugin API for third-party passes.
- No compatibility support for older repository shapes.
- No generic graph optimizer or scheduler beyond linear declared pipelines.
- No broad `CompilationContext` rename.
- No manifest emission before at least two real family pipelines exist.

## Resolved Design Decisions

- `CompilationContext` stays for this workstream. Do not rename it.
- Stage IDs are per-family enum-like types.
- `PassDiagnostic` has stable machine codes from the beginning.
- Sidecar row bundles live under `propstore/sidecar/stages.py`; sidecar row
  passes live under `propstore/sidecar/passes.py`.
- Pass registration is lazy through registration functions. No eager global
  `SEMANTIC_PASS_CLASSES` tuple.
- Grounding/world/runtime stages are explicitly out of the first workstream.

## First Concrete Slice

Start with contexts only:

1. Add `propstore/semantic_passes/types.py`, `registry.py`, and `runner.py`.
2. Move `propstore/families/documents/contexts.py` to
   `propstore/families/contexts/documents.py`.
3. Move migrated context record/stage types out of `propstore/context_types.py`
   into `propstore/families/contexts/stages.py`.
4. Add `propstore/families/contexts/passes.py`.
5. Replace context validation in `compiler/workflows.py` with a context
   pipeline call.
6. Delete `propstore/validate_contexts.py`.
7. Run focused context validation tests, then `uv run pyright propstore`.

After that, move to forms. Concepts remain the first high-value large deletion
slice because `validate_concepts` is the clearest monolithic production owner.
