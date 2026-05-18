# Code Inventory - 2026-05-17

Workflow actually used: live repository inventory by direct file reads and command output. This report is being updated as files are read. The local `quire/` directory in the checkout was empty when inspected; Quire evidence below is from the installed package under `.venv/Lib/site-packages/quire`, while `pyproject.toml` pins Quire to a remote Git revision.

## Scope And Current Evidence

Requested outcome source: `notes/inventory-wanted-outcome-2026-05-17.md`.

The wanted outcome is a complete, evidence-backed inventory of Propstore and Quire before more cleanup work. The inventory must identify current types, models, families, projections, query surfaces, storage surfaces, DAO-like helpers, semantic objects, authored artifact schemas, derived-world objects, and boundaries, so deletion decisions are based on what exists and who owns it.

## Session File Read Log

- `notes/inventory-wanted-outcome-2026-05-17.md`: defines the inventory objective and explicitly says cleanup decisions come after knowing current ownership and duplication.
- `pyproject.toml`: package is `propstore` 0.3.3, exports CLI script `pks = "propstore.cli:cli"`, builds only `propstore`, and depends on `quire`, `formal-belief-set`, `formal-argumentation`, `gunray`, `bridgman`, `eq-equiv`, `ast-equiv`, `human-to-sympy`, `cel-parser`, `linkml`, `msgspec`, `pint`, `fastapi`, and related runtime packages. `[tool.uv.sources]` pins `quire` to `https://github.com/ctoth/quire` at `1343248a218577cb2f63f338c06a02145dd8bf40`.
- `propstore/families/registry.py`: owns `PropstoreFamily`, semantic family names, contract versions, family definitions, placement policy selection, identity policies, reference keys, source/proposal branches, and semantic metadata such as `importable` and `import_order`.
- `propstore/repository.py`: owns the `Repository` object, repository bootstrap format, repository discovery/init, binding to Quire `DocumentFamilyStore`, derived-store root, tree abstraction, GitStore policy, and mutation guard.
- `.venv/Lib/site-packages/quire/families.py`: Quire owns generic `FamilyIdentityPolicy`, `FamilyDeclaration`, `FamilyDefinition`, and `FamilyRegistry`, including contract validation, metadata lookup, registry selection, storage root lookup, and registry binding.
- `.venv/Lib/site-packages/quire/artifacts.py`: Quire owns artifact addressing, branch placement policies, path locators, ref codecs, scan contracts, placement errors, and path-backed artifact locator mechanics.
- `.venv/Lib/site-packages/quire/family_store.py`: Quire owns generic document family load/save/scan/prepare/transaction mechanics over an abstract document store backend.
- `.venv/Lib/site-packages/quire/projections.py`: Quire owns projection column/field/table/index/foreign-key/schema declarations and SQLite DDL/row encode-decode mechanics.
- `.venv/Lib/site-packages/quire/projection_mapping.py`: Quire owns generic row-to-object projection mapping types including projection codecs, bindings, components, metadata, attached rows, joins, discriminators, query plans, and projection models.
- `.venv/Lib/site-packages/quire/derived_store.py`: Quire owns derived-store materialization, cache keys, temp/lock/final SQLite file layout, content hashes, dependency pins, GC reports, and readonly handles.
- `.venv/Lib/site-packages/quire/references.py`: Quire owns generic reference keys, family reference indexes, ambiguous/missing-reference failures, foreign-key specs, and foreign-key validation.
- `.venv/Lib/site-packages/quire/contracts.py`: Quire owns contract manifests, contract entries, compatibility markers, and contract comparison reports.
- `.venv/Lib/site-packages/quire/documents/__init__.py`: Quire exports the document codec/schema/batch surface: `DocumentStruct`, document conversion, decode/encode/render helpers, batch specs, loaded documents, YAML/JSON/text codecs.
- `propstore/derived_build.py`: Propstore owns world sidecar orchestration, sidecar hash inputs, family/pass version inputs, dependency pins, source branch tip inclusion, SQLite sidecar population, and Propstore world projection schema use.
- `propstore/source/promote.py`: Propstore source subsystem owns source-branch promotion, source-local to canonical lowering, promoted claim validation, blocked-claim promotion records, source trust calibration at promotion time, and canonical artifact writes.
- `propstore/core/environment.py`: core owns `Environment` plus store protocols that define the world/query boundary: stance, claim, concept, relationship, explanation, justification, conflict, parameterization, micropublication, condition solver, compiled graph, and full `WorldStore`.
- `propstore/world/model.py`: world owns `WorldQuery`, the read-only reasoner over compiled sidecars, schema validation, lazy Z3/CEL/grounding/lifting caches, historical query sidecars, and SQLite-backed query implementations.
- `propstore/semantic_passes/types.py`: semantic pass layer owns `PassDiagnostic`, `PassResult`, `PipelineResult`, `SemanticPass`, and `FamilyPipeline`.
- `propstore/families/claims/documents.py`: canonical claim schema file; defines typed claim documents, claim type contracts, concept link declarations, value/unit policies, semantic check declarations, claim logical/source/provenance/fit/binding/opinion/resolution/stance/proposition documents, and `ClaimDocument`.
- `propstore/families/concepts/documents.py`: canonical concept schema file; defines logical IDs, aliases, relationships, form parameters, parameterization relationships, ontology references, lexical forms/senses/entries, `ConceptDocument`, and `ConceptIdScanDocument`.
- `propstore/families/claims/projection_model.py`: Propstore claim family owns claim-specific projection mapping from SQLite rows to active claim/domain views, using Quire projection mapping primitives.
- `propstore/families/contexts/documents.py`: authored context schema file; defines context references, context structure with CEL assumptions/parameters/perspective, context lifting rules with source/target/conditions/mode/justification, and `ContextDocument`.
- `propstore/families/forms/documents.py`: authored form schema file; defines form alternatives, extra unit declarations, and `FormDocument` fields for dimensions, base/unit/QUDT metadata, parameters, alternatives, kind/note, extra units, and min/max bounds.

## Top-Level Shape

Propstore is the semantic application package. The top-level package directories observed are:

- `app`: typed application/service layer request/report APIs.
- `aspic_bridge`: bridges active Propstore data into ASPIC/formal argumentation surfaces.
- `cli`: Click presentation adapter layer.
- `compiler`: repository validation/build workflow types and compilation context.
- `conflict_detector`: equation, parameterization, measurement, and algorithm conflict detection.
- `core`: semantic domain objects and protocol boundaries shared below world/app.
- `families`: authored artifact families, document schemas, identity, sidecar projection declarations, and family-specific semantic passes.
- `grounding`: grounded rule/fact bundle loading, translation, inspection, and grounder integration.
- `heuristic`: embedding, calibration, classification, extraction, relation heuristics.
- `importing`: repository import stages, machinery, normalizers.
- `merge`: structured merge, merge reports, commits, classifiers, witnesses.
- `praf`: probabilistic argumentation projection/engine.
- `provenance`: provenance records, supports, variables, nogoods, polynomial provenance, PROV-O/trusty surfaces.
- `semantic_passes`: generic pass registry, runner, and typed pass results.
- `source`: source branch lifecycle and source-local authoring/promotion state.
- `source_trust_argumentation`: source trust calibration by argumentation.
- `storage`: Git policy and repository snapshot surfaces.
- `support_revision`: belief-set/support revision adapters, histories, workflows, explanations, and state.
- `web`: HTML/web presentation helpers.
- `world`: derived-world query, resolution, ATMS, SCM, overlay, intervention, consistency, and replay surfaces.
- `worldline`: worldline definitions, journal/capture/result/revision types, interfaces, and resolution.

Quire is the generic storage substrate. The checkout-local `quire/` directory had no files at inspection time. The installed package files observed are `artifacts.py`, `canonical.py`, `contracts.py`, `derived_runtime.py`, `derived_store.py`, `families.py`, `family_store.py`, `git_store.py`, `hashing.py`, `notes.py`, `projection_mapping.py`, `projections.py`, `references.py`, `refs.py`, `sqlite_vec_store.py`, `tree_path.py`, `versions.py`, and `documents/*`.

## Family Registry And Artifact Surfaces

`PropstoreFamily` currently declares these family keys:

- Canonical/importable semantic families: `claims`, `concepts`, `contexts`, `forms`, `predicates`, `rules`, `rule_superiority`, `stances`, `sameas`, `worldlines`.
- Canonical non-import-order families observed in the registry: `sources`, `micropubs`, `justifications`.
- Source-local authoring families: `source_documents`, `source_notes`, `source_metadata`, `source_concepts`, `source_claims`, `source_micropubs`, `source_justifications`, `source_stances`, `source_finalize_reports`.
- Proposal/merge families: `proposal_stances`, `proposal_predicates`, `proposal_rules`, `concept_alignments`, `merge_manifests`.

Ownership boundary:

- Propstore owns the family enum, semantic metadata, contract version constants, family-specific document types, identity policy selection, and semantic import order.
- Quire owns the generic `FamilyRegistry`, `FamilyDefinition`, `ArtifactFamily`, placement policy classes, path/ref mechanics, and document family store mechanics.

Placement patterns observed in `propstore/families/registry.py`:

- Canonical primary-branch YAML families use Quire placements such as `FlatYamlPlacement`, `HashScatteredYamlPlacement`, `NestedFlatYamlPlacement`, `SingletonFilePlacement`, `SubdirFixedFilePlacement`, and `TemplateFilePlacement`.
- Source-local families use fixed source-branch files such as `source.yaml`, `notes.md`, `metadata.json`, `concepts.yaml`, `claims.yaml`, `micropubs.yaml`, `justifications.yaml`, `stances.yaml`, plus source finalize report templates under `merge/finalize/{stem}.yaml`.
- Branch ownership is encoded with Quire `BranchPlacement`: primary, current, source template, and proposal branches.

## Authored Document Schemas

Propstore authored artifact schemas are typed with Quire `DocumentStruct` and related msgspec-backed conversion.

Canonical claim schema includes:

- claim type contracts and semantic checks (`UnitFormCompatibilityCheck`, `SympyGenerationCheck`, `DimensionalConsistencyCheck`, `AlgorithmParseCheck`, `AlgorithmUnboundNamesCheck`);
- logical/source/provenance/fit/binding/opinion/resolution/stance documents;
- atomic and IST proposition document variants;
- `ClaimDocument` as the canonical claim document.

Canonical concept schema includes:

- `ConceptLogicalIdDocument`, `ConceptAliasDocument`, `ConceptRelationshipDocument`;
- `ConceptFormParametersDocument`, `ParameterizationRelationshipDocument`;
- ontology and lexical documents;
- `ConceptDocument`;
- `ConceptIdScanDocument` for scan-oriented concept-id reads.

Other authored schema families identified from file listings/search output include contexts, worldlines, stances, predicates, sources, source-local claims/concepts/stances/justifications, source alignments, micropublications, forms, same-as assertions, rules, justifications, and merge manifests.

Context schema details from `propstore/families/contexts/documents.py`:

- `ContextReferenceDocument` is a single-id reference payload.
- `ContextStructureDocument` owns context assumptions as CEL expressions, string parameters, and optional perspective.
- `LiftingRuleDocument` owns author-authored context lifting edges: `id`, `source`, `target`, CEL `conditions`, `LiftingMode`, and optional justification.
- `ContextDocument` owns the authored context artifact: `id`, `name`, optional description, structure, and lifting rules.

Form schema details from `propstore/families/forms/documents.py`:

- `FormAlternativeDocument` represents alternate units/conversions with unit, type, multiplier, offset, base, divisor, and reference.
- `FormExtraUnitDocument` declares additional unit symbols with dimension exponents.
- `FormDocument` owns a form's identity and dimensional metadata: `name`, `dimensionless`, optional base/unit symbol/QUDT, arbitrary parameters, common and delta alternatives, kind/note, dimensions, extra units, and numeric bounds.

## Projection And Derived-World Surfaces

Quire projection substrate:

- `ProjectionColumn`, `ProjectionField`, field factories, `ProjectionForeignKey`, `ProjectionIndex`, `ProjectionRow`, runtime catalog entries, `ProjectionTable`, `ProjectionSchema`, and schema errors live in Quire.
- Projection mapping types such as `ProjectionCodec`, `ProjectionBinding`, `ProjectionComponent`, `ProjectionMetadata`, `ProjectionAttachedRows`, `ProjectionSelectedColumn`, `ProjectionJoin`, `ProjectionDiscriminator`, `ProjectionQueryPlan`, and `ProjectionModel` live in Quire.

Propstore projection declarations observed:

- `CALIBRATION_COUNTS_PROJECTION`
- `SOURCE_PROJECTION`
- `GROUNDED_FACT_PROJECTION`
- `GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION`
- `GROUNDED_BUNDLE_INPUT_PROJECTION`
- `MICROPUBLICATION_PROJECTION`
- `MICROPUBLICATION_CLAIM_PROJECTION`
- `RELATION_EDGE_TABLE`
- `BUILD_DIAGNOSTICS_PROJECTION`
- `CONCEPT_PROJECTION`
- `FORM_PROJECTION`
- `FORM_ALGEBRA_PROJECTION`
- `ALIAS_PROJECTION`
- `PARAMETERIZATION_GROUP_PROJECTION`
- `PARAMETERIZATION_PROJECTION`
- `RELATIONSHIP_PROJECTION`

Claim projections are more extensive and are owned by `propstore/families/claims/projection_model.py` plus `propstore/families/claims/declaration.py`; they map claim rows, payload variants, source/provenance fields, concept links, conditions, authored justifications, stances, conflicts, and blocked/quarantine facts into active runtime views.

World sidecar ownership:

- Propstore owns the world sidecar build workflow and domain population in `propstore/derived_build.py`.
- Quire owns derived-store caching/materialization and SQLite runtime helpers.
- `WorldQuery` opens the derived sidecar read-only through Quire `DerivedStoreHandle`, validates Propstore's projection schema, and exposes world/query behavior.

## Query Surfaces

Core boundary:

- `propstore/core/environment.py` defines `WorldStore` and narrower store protocols. These protocols are the boundary between domain logic and concrete sidecar/query implementations.

World query:

- `propstore/world/model.py` implements `WorldQuery(WorldStore)` over SQLite sidecars.
- `propstore/world/queries.py` owns typed request/report query APIs for status, concept queries, bind, explain, algorithms, derive, hypothetical diff, resolve, and chain.
- `propstore/world/types.py` owns runtime result objects and protocols for values, derived results, ATMS reports, resolution strategy/operator, assignment selection, synthetic claims, claim views, chains, render policies, decision values, and belief-space protocols.

Application query:

- `propstore/app/*` exposes typed request/report adapters for CLI/web-facing workflows: claims, claim views, concepts, contexts, forms, rules, predicates, sources, repository overview/history/import, materialize, merge, world, world ATMS/reasoning/revision, worldlines, rendering, observatory, grounding, and neighborhoods.

## Source And Canonical Boundary

Source-local authoring state is isolated in source families and source subsystem modules:

- source-local documents and side files are separate registry families;
- `propstore/source/promote.py` lowers source-local concepts/claims/justifications/stances/micropublications into canonical artifacts;
- promotion validates the canonical claim view before commit and records blocked claims/diagnostics where promotion cannot proceed for an item.

Canonical families are declared separately in the family registry and use canonical identity policies, reference keys, and foreign keys.

## Storage Surfaces

Propstore storage ownership:

- `Repository` locates a propstore knowledge repository, binds the family registry to a Quire `DocumentFamilyStore`, exposes `families`, `snapshot`, `tree`, `derived_stores`, `git`, `require_git`, and `mutation_guard`.
- `PROPSTORE_REPOSITORY_FORMAT_VERSION` is currently `2026.04.store-only-init`.
- `REPOSITORY_CONFIG_PATH` is `propstore.yaml`.
- derived stores live under `.propstore/derived-stores` inside the repository root.

Quire storage ownership:

- `DocumentFamilyStore` owns generic address/ref/load/exists/handle/iter/save/transaction mechanics over a backend.
- `GitStore` is the backend dependency used by Propstore repositories.
- `DerivedStoreManager` owns cache key layout, locks, temp SQLite file placement, final SQLite placement, and GC.
- `references.py` owns generic FK/reference validation and family reference indexes.
- `contracts.py` owns contract manifests and contract comparison.
- `documents/*` owns conversion/codecs/batch loading.

## Known Dirty State At Inventory Start

Before creating this report, `git status --short` showed an existing tracked modification in `propstore/conflict_detector/equation_inputs.py` and multiple unrelated untracked files/directories. This report path was clean before creation. The existing modification was not read or changed as part of the initial report creation.

## Open Inventory Gaps

These are not completion claims; they are the remaining inventory work:

- enumerate each Propstore family document schema file beyond claims and concepts;
- enumerate every sidecar table declared in claim and relation projection model files;
- inventory DAO-like helpers: all `select_*`, `populate_*`, `resolve_*`, `count_*`, `load_*`, and `build_*_index` functions that operate as storage/query adapters;
- inventory all semantic pass pipelines by family and stage;
- inventory CLI modules only as presentation adapters and identify any owner-layer leakage;
- inventory source subsystem lifecycle/status/batch/common/reference-index surfaces;
- inventory worldline journal/revision/result interfaces and their boundary with world/app/support-revision;
- inventory conflict detector, grounding, ASPIC bridge, PR-AF, support revision, merge, import, heuristic, provenance, and web surfaces;
- validate Quire evidence against the pinned remote revision if required by the final inventory standard; current Quire evidence is from the installed package.
