# Condition Registry Convergence Plan

Date: 2026-07-21
Status: implementation and fixed-point closeout complete; final convergence gates pending
Control surface: `protocols:cleanup-refactor`

This plan supersedes only the still-open CEL-registry ownership work in:

- `plans/cel-registry-hardening-workstream-2026-04-14.md`
- `plans/cel-subsystem-unification-plan-2026-04-08.md` phase U1
- `plans/cel-typed-expression-workstream-2026-04-16.md` registry ownership questions
- `plans/concept-canonical-typing-workstream-2026-04-09.md` cluster C

Those plans describe historical types and files. This plan is based on the
current `Concept` charter, condition-ir package API, semantic passes, compiler,
world, and source-promotion code. It does not change the scope or ordering of
`plans/unwired-and-missing-code-convergence.md`.

## Literal requested outcome

1. A condition registry is keyed by an authored CEL symbol, never by a concept
   URI/id.
2. `ConceptInfo.id` remains the stable `Concept.concept_id` embedded in checked
   condition IR.
3. Missing or dangling form information never fabricates `KindType.CATEGORY`.
4. Category vocabulary/openness is explicit typed per-concept data and survives
   source proposal promotion.
5. `Concept` remains a canonical data object; no condition-ir conversion,
   registry-building, or form-registry methods are added to it.
6. The checked concept semantic pass owns condition binding validation, form
   resolution, and condition-ir projection.
7. `propstore/cel_registry.py` and the duplicate registry/lowering helpers in
   `propstore/claim_conditions.py` are deleted. They are not renamed, wrapped,
   aliased, or recreated elsewhere.
8. Compiler, world, and source workflows use their real typed owners directly.

## Resolved contracts

### Concept naming

- `Concept.concept_id` is stable identity, for example
  `ps:concept:fundamental_frequency`.
- `Concept.canonical_name` is the authored CEL identifier, for example
  `fundamental_frequency`.
- `Concept.lexical_entry.canonical_form.written_rep` is the human lexical form,
  for example `Fundamental frequency`.
- A canonical name is valid only when `cel_parser.parse(name)` returns one
  `cel_parser.Ident` with the same name. The parser owns the grammar; Propstore
  will not duplicate it with a regex or normalization helper.
- Duplicate canonical names are concept-pass errors. Last-write-wins is
  forbidden.
- Existing persisted repositories are not silently rewritten. Invalid existing
  names fail at the semantic boundary and require an explicit, separately
  authorized repository migration. Checked-in project seeds and test fixtures
  are corrected in this workstream.

### Condition kind resolution

- A concept enters the condition registry only when
  `lexical_entry.physical_dimension_form` resolves to a `FormDefinition`.
- No lexical entry or no form link means the concept is not condition-bindable;
  it is omitted without inventing a kind.
- A dangling form link retains the existing `concept.form.dangling` warning and
  is omitted from the condition registry.
- A claim condition that names an omitted concept receives condition-ir's
  existing undefined-concept diagnostic.
- Category and structural condition concepts must explicitly link the existing
  `category` and `structural` forms respectively.

### Category metadata

- Category values and openness vary by concept, so they do not belong in the
  global `FormDefinition.parameters` dictionary.
- Add explicit canonical `Concept` fields:
  - `category_values: tuple[str, ...] = ()`
  - `category_extensible: bool = True`
- The fields are consumed only when the resolved form kind is
  `KindType.CATEGORY`. Non-default category metadata (`category_values` is
  non-empty or `category_extensible` is `False`) on another kind is a concept
  semantic-pass error.
- Source promotion maps
  `SourceConceptFormParametersDocument.values/extensible` into those canonical
  fields. `None` means the canonical defaults above.
- `SourceConceptFormParametersDocument.construction`, `note`, and `reference`
  remain source-authoring metadata; they do not affect condition typing and are
  not copied into the canonical Concept by this plan.

## Target ownership

### `propstore/families/concepts.py`

Owns only the canonical stored concept fields, including typed category
metadata. It does not import condition-ir or cel-parser and gains no registry or
conversion methods.

### `propstore/families/concepts_passes.py`

`ConceptCheckPass` owns:

- CEL-symbol validation of `canonical_name` by direct cel-parser use;
- duplicate id and duplicate canonical-name detection;
- linked-form resolution;
- category-metadata/kind consistency checks;
- the canonical-name-keyed `Mapping[str, condition_ir.ConceptInfo]` exposed on
  `ConceptCheckedRegistry`.

The pass stores the original canonical `Concept` objects in `by_id`; it creates
no Propstore mirror of `ConceptInfo`.

### `propstore/compiler/context.py`

Compilation context construction consumes `ConceptCheckedRegistry`. It does not
revalidate concepts or rebuild condition metadata from `LoadedConcept`.
`CompilationContext.condition_registry` replaces the misleading
`CompilationContext.cel_registry` field. The authored `concepts_by_id` map comes
directly from `ConceptCheckedRegistry.by_id`.

### `propstore/claim_conditions.py`

Owns claim-level checking, checked-condition serialization, satisfiability, and
disjointness. It does not construct `ConceptInfo` or registries.

### World and source workflows

- `WorldQuery.condition_solver()` runs the existing concept pass over its
  canonical `Concept` and `FormDefinition` values and gives the checked
  registry directly to condition-ir's `ConditionSolver`.
- Source claim validation runs the canonical concept pass for primary-branch
  concepts, then adds source-local proposed bindings from their typed source
  documents. It uses condition-ir types/functions directly and does not route
  source-local documents through canonical `Concept` conversion.
- Source promotion constructs a complete canonical `Concept` with a
  `LexicalEntry`, `LexicalForm`, `LexicalSense`, self-owned
  `OntologyReference(uri=concept_id)`, the authored form link, and typed category
  metadata. This follows the existing project-seed construction pattern.

## Forbidden surfaces

The following must not exist at completion:

- `propstore/cel_registry.py`
- `concept_kind`
- `concept_info_from_concept`
- `build_canonical_cel_registry`
- `propstore.claim_conditions.lower_concept`
- `propstore.claim_conditions.condition_registry`
- any `{info.id: info}` condition-registry construction
- any absent/dangling-form fallback to `KindType.CATEGORY`
- reads of `FormDefinition.parameters["extensible"]` or `values` for condition
  semantics
- `canonical_name=seed.name` in project initialization
- source promotion that constructs a flat `Concept` while dropping the authored
  form or category metadata
- a replacement builder/helper/adapter with the same Concept + form-registry
  inputs and registry output as the deleted module
- simultaneous old/new registry production paths

## Accountability and record

Before the first source edit:

1. Run `git status --short --branch` and record the exact branch and relevant
   tracked state.
2. Create `notes-condition-registry-convergence.md` from the cleanup-refactor
   fixed-point template.
3. Keep that notes file uncommitted and update it after every gate and commit.
4. Preserve the pre-existing `pyghidra_mcp_projects/` path and all unrelated
   user changes.
5. Each source slice ends as either one committed kept change or a full Git
   restore of that slice before the next source slice begins.
6. Stage only the exact paths recorded for the active slice.

### Plan activation

After the user approves execution and before Slice 1:

- [x] Commit this plan alone as:

  ```text
  docs(conditions): plan condition registry convergence
  ```

- [x] Create the uncommitted fixed-point record and record the post-plan-commit
  Git state there.
- [x] Reread this plan and begin with the first unchecked Slice 1 item.

Verified planning baseline on 2026-07-21:

- focused logged suite: 57 passed in 6.85 seconds;
- log: `logs/test-runs/cel-registry-plan-baseline-20260721-145843.log`;
- `uv run pyright propstore`: 0 errors;
- `uv run lint-imports`: 3 contracts kept;
- full `uv run ruff check propstore tests` has 53 pre-existing unrelated F401
  failures, so it is not a valid clean baseline. Each slice instead runs Ruff
  over only its changed Python paths. The unrelated failures are not repaired in
  this workstream.

## Slice 1 - Canonical CEL-symbol contract

Decision changed: what authored name CEL resolves.

Active production boundary:

- `propstore/app/project_init.py`
- `propstore/families/concepts_passes.py`
- `propstore/source/concepts.py`

Execution order:

- [x] Delete the old producer assignment `canonical_name=seed.name`; replace it
   directly with `canonical_name=seed.ref`. Keep `seed.name` only in the lexical
   form and ontology-reference label.
- [x] In `ConceptCheckPass`, use `cel_parser.parse`/`Ident` directly to reject a
   non-identifier canonical name and reject duplicate canonical names. Add
   diagnostic codes `concept.canonical_name.invalid` and
   `concept.canonical_name.duplicate`.
- [x] At the source authoring boundary, validate `proposed_name` by the same direct
   parser operation before it can become a future canonical name. Do not
   normalize an invalid name into a valid one.
- [x] Classify and repair fixtures exposed by those changes. A display phrase in
   `canonical_name` is a valid concept with the wrong representation; retain its
   human phrase only in `LexicalForm.written_rep` and give it an explicit CEL
   symbol.
- [x] Prove a concept with id `ps:concept:frequency`, canonical name `frequency`,
   and lexical written form `Fundamental frequency` preserves all three values.

Runtime gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label condition-registry-s1 tests/test_family_passes.py tests/test_app_project_init.py tests/test_source_authoring_p82.py tests/test_app_aliases.py tests/test_concept_views.py -q
uv run ruff check propstore/app/project_init.py propstore/families/concepts_passes.py propstore/source/concepts.py tests/test_family_passes.py tests/test_app_project_init.py tests/test_source_authoring_p82.py tests/test_app_aliases.py tests/test_concept_views.py
uv run pyright propstore
```

Search gate:

```powershell
rg -n "canonical_name=seed\.name" propstore tests
```

Expected result: zero hits.

Result (2026-07-21): 55 focused tests passed; changed-path Ruff and package
Pyright passed; the search gate had zero hits. Kept commit `35b18e88`.

Commit:

```text
refactor(concepts): make canonical names CEL symbols
```

## Slice 2 - Preserve form and category semantics through promotion

Decision changed: whether source-authored condition typing survives canonical
promotion.

Active production boundary:

- `propstore/families/concepts.py`
- `propstore/families/registry.py`
- `propstore/source/promote.py`
- charter-derived contract manifest

Execution order:

- [x] Add the two typed category fields to `Concept` and bump the concept charter
   contract version from `2026.06.28` to `2026.07.21`.
- [x] Bump `PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION` from `2026.07.21.1`
   to `2026.07.21.2`; the concept charter change also changes the derived
   `family-registry:propstore` contract body.
- [x] Delete the flat promoted-Concept construction that drops form data.
- [x] Rebuild that exact caller path with the already-owned lemon objects, carrying
   proposed name, definition, form, values, and extensibility into the canonical
   `Concept`. Do not add a constructor helper or alternate Concept type.
- [x] Add a source proposal -> promotion -> canonical reload proof for a closed
   category and a quantity concept.
- [x] Regenerate the checked-in manifest with the existing owner command:

   ```powershell
   uv run pks contract-manifest --write
   ```

Runtime gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label condition-registry-s2 tests/test_source_promote_p83b.py tests/test_source_finalize_p83a.py tests/test_cli_source_p101.py tests/test_lemon_concept_charter.py tests/test_concept_skeleton.py tests/test_contract_manifest.py -q
uv run ruff check propstore/families/concepts.py propstore/families/registry.py propstore/source/promote.py tests/test_source_promote_p83b.py tests/test_source_finalize_p83a.py tests/test_cli_source_p101.py tests/test_lemon_concept_charter.py tests/test_concept_skeleton.py tests/test_contract_manifest.py
uv run pyright propstore
```

Required proof:

- promoted `lexical_entry.physical_dimension_form` equals the source form;
- promoted closed-category values and `category_extensible=False` survive save
  and load;
- no source-local handle or source-only document type enters the canonical
  Concept charter.

Result (2026-07-21): 89 focused tests passed; changed-path Ruff, package
Pyright, manifest regeneration, and contract compatibility passed. The closed
category and quantity promotion/reload proofs passed. Kept commit `faa6851e`.

Commit:

```text
refactor(source): preserve promoted concept semantics
```

## Slice 3 - Delete the old registry surface and cut callers to the checked owner

Decision changed: which owner constructs condition-ir's registry.

This is one atomic cutover. Do not stop or commit while any production caller
still depends on the deleted surfaces.

Execution order:

- [x] Delete `propstore/cel_registry.py` in full.
- [x] Delete `lower_concept` and `condition_registry` from
   `propstore/claim_conditions.py`.
- [x] Delete `tests/test_cel_registry.py`; move surviving behavioral assertions to
   the actual owner tests rather than preserving an obsolete module contract.
- [x] Extend `ConceptCheckedRegistry` and `ConceptCheckPass` with the direct
   condition-ir projection described above. Do not introduce a replacement
   builder function.
- [x] Delete `build_authored_concept_registry` and
   `build_compilation_context_from_loaded`. Make compilation context consume the
   already-checked concept registry and rename its field to
   `condition_registry`.
- [x] Update compiler workflows to pass `concept_result.output`, not the original
   loaded concepts, into compilation-context construction.
- [x] Update source promotion revalidation to run the concept pass before the
   claim pass.
- [x] Update source claim CEL validation to combine the checked primary registry
   with source-local typed `ConceptInfo` values keyed by proposed/local CEL name.
- [x] Update `WorldQuery.condition_solver()` to run the concept pass over its
   canonical concepts/forms and use `ConceptCheckedRegistry.condition_registry`
   directly. Preserve synthetic bindings by calling condition-ir's package API
   directly at the caller that requests them.
- [x] Classify every import/type/test breakage before editing it. Allowed
    dispositions are direct use of `ConceptCheckedRegistry`, direct use of
    condition-ir at a true source/runtime boundary, or deletion of an obsolete
    caller/test.
- [x] Continue the fixed-point loop until every forbidden search is clean before
    committing.

Focused runtime gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label condition-registry-s3 tests/test_family_passes.py tests/test_compilation_context.py tests/test_claim_conditions.py tests/test_compiler_workflows.py tests/test_source_promote_p83b.py tests/test_source_authoring_p82.py tests/test_conflict_detector.py tests/test_world_query.py tests/test_world_keystone.py -q
uv run pyright propstore
uv run lint-imports
```

Run Ruff on the exact changed Python paths recorded in the fixed-point log.

Required behavioral proofs:

1. Registry key `frequency` maps to a `ConceptInfo` whose id is
   `ps:concept:frequency`.
2. CEL `frequency > 10` checks and lowers to that stable concept id.
3. The concept URI is not accepted as CEL source syntax.
4. Explicit category form produces `KindType.CATEGORY` with authored values and
   openness.
5. Missing form produces no registry entry.
6. Dangling form produces `concept.form.dangling` and no registry entry.
7. Duplicate or invalid canonical names prevent a checked concept registry.
8. Compiler, source validation/promotion, and world solver observe the same
   canonical condition metadata for the same canonical concepts.

Search gates:

```powershell
rg -n 'propstore\.cel_registry|build_canonical_cel_registry|concept_info_from_concept|concept_kind|lower_concept' propstore tests
rg -n 'cc\.condition_registry|claim_conditions\.condition_registry|from propstore\.claim_conditions import condition_registry' propstore tests
rg -n '\{info\.id: info|registry\[info\.id\]' propstore tests
rg -n 'parameters\.get\("extensible"\)|parameters\.get\("values"\)' propstore tests
rg -n 'defaults? to .*CATEGORY|dangling.*CATEGORY|missing.*CATEGORY' propstore tests
rg -n 'build_compilation_context_from_loaded|build_authored_concept_registry' propstore tests
```

Expected result: zero production hits. Any test/document hit must be either
deleted as an obsolete contract or recorded with a precise non-production
disposition before the slice commits.

Result (2026-07-21): 159 focused tests passed; package Pyright, all import
contracts, and changed-path Ruff passed; all six searches had zero hits. All
eight behavioral proofs passed through the checked owner paths. Kept commit
`f68d2209`.

Commit:

```text
refactor(conditions): derive registries from checked concepts
```

## Slice 4 - Fixed-point closeout and historical-plan status

This slice changes records, not architecture.

- [x] Rerun every search gate from all slices.
- [x] Update the four historical CEL/concept plan files named at the top with a
   dated note that their remaining registry ownership work is superseded by
   this completed plan. Do not rewrite their historical records.
- [x] Update this plan's status and every checkbox/result only after the evidence
   exists.
- [x] Update `notes-condition-registry-convergence.md` with commits, logs, exact
   residual hits, and the next action or fixed-point completion.

Result (2026-07-21): all seven prior search gates have zero hits, the four
historical plans carry dated supersession notes, and the uncommitted
fixed-point record names the commits, logs, zero residual hits, and next action.
Final convergence gates remain pending and are not reported as complete.

Commit:

```text
docs(conditions): close obsolete registry workstreams
```

## Final convergence gates

Run in this order:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label condition-registry-focused tests/test_family_passes.py tests/test_compilation_context.py tests/test_claim_conditions.py tests/test_compiler_workflows.py tests/test_source_authoring_p82.py tests/test_source_promote_p83b.py tests/test_source_finalize_p83a.py tests/test_cli_source_p101.py tests/test_app_project_init.py tests/test_conflict_detector.py tests/test_world_query.py tests/test_world_keystone.py tests/test_contract_manifest.py -q
uv run pyright propstore
uv run lint-imports
powershell -File scripts/run_logged_pytest.ps1 -Label condition-registry-full
```

Then rerun Ruff only over the union of Python paths changed by this plan.

The plan is complete only when:

- the plan activation commit and all four source/record slices are committed in
  order;
- the required behavioral proofs pass through production paths;
- every forbidden search gate reaches fixed point;
- old and new registry production paths do not coexist;
- the full logged suite, package Pyright gate, and import-linter gate pass;
- the contract manifest matches the charter-derived output;
- unrelated pre-existing worktree paths remain untouched;
- the uncommitted fixed-point record names all evidence and commits;
- every item above is complete or explicitly deferred by the user.
