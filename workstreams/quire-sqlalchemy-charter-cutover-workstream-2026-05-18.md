# Quire SQLAlchemy Charter Cutover Workstream

Date: 2026-05-18

## Goal

Replace Propstore's duplicated projection/read-model/helper layer and Quire's
homegrown SQLite projection layer with one Quire-owned charter/schema engine
backed by SQLAlchemy.

The end state is:

- Quire owns generic typed Git artifact families, family charters, schema IR,
  Python-type-to-SQL mapping, SQLAlchemy table/mapping generation, sessions,
  derived SQLite lifecycle, schema catalog metadata, FKs, indexes, FTS/vector
  hooks, and generic query mechanics.
- Propstore owns Propstore domain charters and semantic behavior: claims,
  concepts, sources, stances, justifications, contexts, forms, rules,
  micropublications, source-local authoring, promotion, world reasoning,
  semantic validators, and policy compilation.
- Propstore has no handwritten projection-model layer, no `*Row` classes that
  duplicate domain models, no `ProjectionTable`/`ProjectionModel` usage, no
  manual optional-number/string/id coercer families, and no fake ORM.
- The queryable sidecar is a generated Quire derived store over Propstore
  charters. It can be deleted and rebuilt from Git artifacts.
- Runtime data access uses Quire-opened SQLAlchemy sessions and Propstore
  domain model classes.

## Sources Read

This workstream is based on:

- `notes/architecture-wanted-outcome-2026-05-17.md`;
- `reports/code-inventory-2026-05-17.md`;
- current Quire source around `families.py`, `derived_store.py`,
  `derived_runtime.py`, `projections.py`, and `projection_mapping.py`;
- current Propstore source around family projection declarations,
  `derived_build.py`, and `world/model.py`;
- SQLAlchemy 2.1 docs for dataclass mapping, imperative mapping, relationship
  mapping, and association object pattern.

## SQLAlchemy Capability Decision

We do not assume SQLAlchemy will do the needful. We prove it first in Quire.

The expected answer is yes for the core architecture:

- SQLAlchemy supports imperative mappings with `registry.map_imperatively`.
- Imperative mapping lets Quire generate `Table` objects from a schema IR and
  map already-defined Python classes to those tables.
- Imperative mapping avoids Declarative's reserved-name class-body collision,
  including the `metadata` field case.
- SQLAlchemy relationships cover one-to-many and many-to-one links.
- SQLAlchemy's documented association object pattern is exactly the right
  shape for join rows that carry payload columns, such as
  `ClaimConceptLink`.
- SQLAlchemy dataclass integration does not support frozen/slots mapped
  entities, so mapped domain objects must be instrumentable. Nested value
  objects remain frozen when they are not SQLAlchemy-mapped entities.
- SQLAlchemy's attrs support is imperative-only and not continuously tested by
  SQLAlchemy, so attrs is not the foundation here.

The first phases below are capability gates. If any gate fails, fix the Quire
engine or the SQLAlchemy extension before touching Propstore production paths.

## Non-Goals

- Do not move Propstore semantics into Quire.
- Do not delete source-local authoring scope.
- Do not replace Propstore projection models with `propstore.sidecar.models`,
  `models.py`, or any other parallel schema package.
- Do not use Pydantic or attrs as the core schema engine in this workstream.
  The core schema engine is Quire charters plus SQLAlchemy imperative mapping.
- Do not keep old and new projection systems in production at the same time.
- Do not pin dependencies to local paths.
- Do not preserve `ProjectionTable`, `ProjectionModel`, or `*Row` aliases for
  compatibility.
- Do not hand-roll ORM behavior that SQLAlchemy already owns.

## Execution Rules

- Execute deletion-first.
- This workstream is the control surface. Do not execute a nearby plan,
  substitute plan, spike output, implementation idea, or "equivalent" cleanup.
- Literal phase text wins over agent judgment. If the next action is not named
  by the current phase or required by a current-phase gate, stop and report the
  mismatch.
- Do not introduce a new package, abstraction, schema style, migration bridge,
  compatibility layer, or helper family during execution.
- Do not broaden from the current phase to another family because a nearby
  failure is interesting. Finish, block, or explicitly update the phase order.
- Do not use passing tests, a clean commit, a useful proof, or a partial family
  cutover as completion while old-path search gates still fail.
- Do not leave old/new dual production paths. The new Quire charter engine
  must subsume the old projection schema before any Propstore family cutover;
  family phases delete old writes and callers instead of running old and new
  read paths side by side.
- Move files when the change is actually a move. Use `git mv` for same-repo
  moves.
- For cross-repo Quire/Propstore changes, preserve move intent in commit
  messages and keep source/deletion slices paired.
- Commit every intentional edit slice atomically with path-limited git
  commands in the repository being edited.
- Push Quire changes before pinning Propstore to a Quire commit.
- Never pin Propstore to a local Quire checkout.
- Between the first Quire edit and final Propstore dependency closure,
  Propstore pins Quire to a pushed branch commit or immutable pushed commit
  SHA refreshed at the start of each Propstore phase.
- Use `uv run ...` for Python tooling.
- Run Propstore tests through `scripts/run_logged_pytest.ps1`.
- After each passing substantial test run, reread this workstream before
  choosing the next slice.
- Before implementation, mechanically check the phase order.

## Forbidden Failure Modes

These are workstream failures, not style preferences:

- executing a task that is not the current workstream phase;
- treating a spike, proof, or helper as the requested production work;
- adding wrappers/adapters/aliases instead of deleting the old production
  surface;
- changing a field name, relationship name, package boundary, or owner boundary
  without updating the workstream first;
- doing "cleanup" outside the current family slice;
- porting a caller while leaving the old callee as a production path;
- inventing a schema declaration outside Quire when the current target is the
  Quire charter engine;
- reusing Quire projection primitives after the current phase says they are
  deleted;
- claiming a helper is gone without running the named search gate;
- claiming SQLAlchemy capability without a Quire proof test that exercises the
  exact feature;
- treating this document as advisory once implementation starts.

## Dependency Order

Execute in this order:

0. Mechanical order check and current-state inventory confirmation.
1. Quire SQLAlchemy dependency and capability proof.
2. Quire charter/schema IR.
3. Quire SQLAlchemy table/mapping/session/catalog engine.
4. Quire FTS and vector implementation.
5. Build orchestration cutover.
6. Source vertical slice.
7. Forms and sources cleanup closure.
8. Concept/form/parameterization slice.
9. Context/lifting slice.
10. Claim model and association-object slice.
11. Relations/stances/conflicts slice.
12. Justifications and micropublications slice.
13. Rules/grounding/diagnostics/calibration/embeddings slice.
14. WorldQuery/session/graph/reasoning cutover.
15. Delete Quire projection modules.
16. Delete Propstore projection/helper leftovers.
17. Full gates, docs, and final dependency pin.

Write or run an order checker before production implementation. The checker
must prove each dependent phase appears after its prerequisites. If it fails,
repair this file before editing code.

No Propstore family production cutover starts until Phases 1-5 pass. Source is
not a place to discover whether SQLAlchemy can handle metadata fields,
association objects, FTS, sessions, schema catalogs, JSON adapters, enum
conversion, data parity, or build orchestration. All of that is Quire and
build-orchestration work first.

## Phase 0: Mechanical Order Check And Current-State Inventory Confirmation

Repository: Propstore for the workstream check, Quire for dependency checks.

Before any implementation edit:

- run a phase-order check over this file;
- confirm `reports/code-inventory-2026-05-17.md` still exists and is the
  controlling inventory;
- confirm `notes/architecture-wanted-outcome-2026-05-17.md` still says Quire
  owns the generic charter/schema/SQLAlchemy derived-store machinery;
- confirm the current Propstore worktree state before editing;
- confirm the current Quire worktree state before editing Quire;
- list the current Quire dependency pin in Propstore;
- list all current production imports of Quire projection primitives in
  Propstore.

Required commands:

```powershell
rg -n -F -- "ProjectionTable" propstore tests
rg -n -F -- "ProjectionModel" propstore tests
rg -n -F -- "ProjectionCodec" propstore tests
rg -n -F -- "PROPSTORE_WORLD_PROJECTION_SCHEMA" propstore tests
rg -n -F -- "quire" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
```

This phase does not implement anything. It proves the starting state and the
work queue. If the inventory or notes are missing, stop and restore the
authoring context before implementation.

The dependency check must inspect the parsed `pyproject.toml` dependency and
`[tool.uv.sources]` entries. A local path, workspace, or file URL dependency on
Quire is a hard blocker until Quire has been pushed and Propstore is pinned to
a pushed branch commit or immutable pushed commit SHA.

## Mechanical Family Cutover Loop

Every Propstore family phase must use the same loop:

1. Read the family inventory entry and current family files.
2. List every current production caller that imports or consumes the family's
   projection rows, projection models, raw SQLite selectors, or generic helper
   layer.
3. Name the target charter/model classes in the phase notes or commit message.
4. Delete the old production projection/read-model surface first.
5. Run the smallest import/type/test command that exposes the next failures.
6. Fix only failures caused by the deletion in the current family slice and
   named caller list.
7. Replace raw SQLite access with Quire SQLAlchemy session/model access.
8. Replace loose dict/list/row payloads with typed model objects.
9. Delete field-specific coercers once generic charter conversion covers the
   field.
10. Run the family gates.
11. Run the old-path search gates for that family.
12. Run the data-parity gate for that family.
13. Commit only that family slice.
14. If files moved, run `git log --diff-filter=R -1 --stat` after commit and
    verify the expected renames are visible.
15. Reread this workstream before selecting the next phase.

The loop is not optional. If a family cannot follow it because Quire lacks a
needed generic feature, stop and return to the Quire phase that owns that
feature. Do not create a Propstore workaround.

Generic SQL/helper deletion predicate:

- delete a helper when its body is a table-shaped `SELECT`, `COUNT`, `INSERT`,
  `DELETE`, row attachment, row coercion, or projection-model wrapper with no
  Propstore semantic policy;
- keep and move semantic code when it owns concept-id precedence, alias
  resolution, source-local lowering, quarantine/blocked policy, form/unit
  validation, visibility/render policy, context/lifting semantics,
  argumentation semantics, revision semantics, or authored-document identity;
- after moving kept semantics, the original helper-shaped production path is
  deleted.

Every Propstore family phase has the same data-parity obligation:

- build the sidecar from the same repository snapshot before and after the
  current phase;
- compare row counts and primary-key/key-set coverage for every table the
  phase owns;
- compare representative semantic query results for the phase owner APIs;
- explicitly list accepted column/table renames in the commit message;
- fail the phase when a row, key, diagnostic, FTS hit, vector hit, or semantic
  query result disappears. The only accepted disappearance is a table or
  helper already named as a deletion target in this workstream.

## Inventory Deletion Matrix

The inventory maps the cleanup to exact owner surfaces:

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `../quire/quire/projections.py` | Quire handwritten SQLite projection primitives | Quire SQLAlchemy charter engine | Delete after all consumers move |
| `../quire/quire/projection_mapping.py` | Quire object-to-row mapper | Quire SQLAlchemy mapper/session engine | Delete after all consumers move |
| `../quire/quire/derived_store.py` | Quire derived SQLite lifecycle | Quire | Keep and adapt to SQLAlchemy sessions/catalog |
| `../quire/quire/derived_runtime.py` | Quire SQLite runtime/validation/meta projection | Quire SQLAlchemy runtime/catalog validation | Keep runtime policy; replace projection-schema validation with SQLAlchemy catalog validation |
| `../quire/quire/families.py` | Quire artifact family registry | Quire family registry plus charter registration | Keep; compose charters with `ArtifactFamily` instead of creating a parallel family registry |
| `../quire/quire/family_store.py` | Quire document family IO | Quire document family IO | Keep; charter work must not duplicate document IO |
| `../quire/quire/artifacts.py` | Quire artifact placement/addressing | Quire artifact placement/addressing | Keep; charters reference existing artifact family identities |
| `../quire/quire/references.py` | Quire reference/FK validation | Quire reference/FK validation plus SQLAlchemy FKs | Keep; SQLAlchemy FKs are derived from the same reference specs |
| `../quire/quire/sqlite_vec_store.py` | Quire sqlite-vec persistence | Quire SQLAlchemy-backed vector cache machinery | Keep API shape where useful; replace raw connection/table plumbing with SQLAlchemy/vector extension integration |
| `propstore/derived_build.py` | Propstore sidecar build orchestration over projection tables | Propstore orchestration over Quire writable sessions and charters | Replace projection schema creation/population with charter-driven session writes |
| `propstore/derived_build_plan.py` | Propstore row-oriented build plan | Propstore typed domain-object build plan | Replace row sets with typed model/session write plans |
| `propstore/families/projection_catalog.py` | Propstore manual world schema assembly | Quire schema catalog over Propstore charters | Delete; replace with Propstore world charter registration through the Quire catalog |
| `propstore/families/sources/declaration.py` projection pieces | Source sidecar projection | Source charter plus Quire SQLAlchemy | Delete projection rows/tables/helpers |
| `propstore/source/status.py` | Source status SQL queries | Source owner query over Quire session | Replace raw SQL with model/session query |
| `propstore/source/finalize.py` and `propstore/source/promote.py` | Source promotion/finalize diagnostics into sidecar surfaces | Source subsystem plus diagnostic charter | Keep semantics; route diagnostics through typed diagnostic models |
| `propstore/form_utils.py` | Duplicate form loading/parsing facade | `propstore/families/forms/stages.py` | Delete duplicate facade after callers use the family owner |
| `propstore/families/forms/stages.py` | Form semantic stage/loading owner | Form semantic owner plus form charter | Keep; expose form model data to Quire charter without duplicating parsing |
| `propstore/families/concepts/projection_model.py` | Concept row mapper | Concept charter plus Quire SQLAlchemy | Delete |
| `propstore/families/concepts/declaration.py` projection/query pieces | Concept sidecar compiler/query API | Concept semantics plus model queries | Delete generic projection/query plumbing |
| `propstore/families/claims/projection_model.py` | Claim split storage/read mapper | Claim charter plus association objects | Delete |
| `propstore/families/claims/storage.py` storage shaping | Loose claim row preparation/helpers | Claim charter generic conversion | Delete storage-shaped helpers |
| `propstore/families/claims/storage.py` semantic conversions | Raw-id canonicalization, concept-ref resolution, unit normalization, stance-resolution conversion | Claim semantic owner modules | Move semantics to claim stages/passes/identity/relation owner modules before deleting storage-shaped remainder |
| `propstore/core/active_claims.py` row coercion | Runtime row repair | Typed `Claim` model and explicit active-claim view model | Delete projection-row coercion; keep only named active runtime view behavior |
| `propstore/core/graph_build.py` | Graph construction through projection models | Graph construction from typed model/session APIs | Replace row-model coercion with typed model reads |
| `propstore/core/analyzers.py` | Analyzer inputs through projection models | Analyzer inputs from typed graph/relation/claim models | Replace row coercion with typed model inputs |
| `propstore/core/justifications.py` | Active graph justification view | Propstore semantic justification view | Keep semantic view; delete duplicate schema/conversion role |
| `propstore/graph_export.py` | Graph export from projection model rows | Graph export from typed world/session models | Replace projection-model imports |
| `propstore/relation_analysis.py` | Stance summary through projection model rows | Stance summary from typed relation models | Replace projection-model imports |
| `propstore/parameterization_walk.py` | Parameterization traversal through row coercion | Parameterization traversal over typed models | Replace projection-model imports |
| `propstore/structured_projection.py` | Analyzer projection back to assertions | Typed assertion projection owner | Replace row-derived data assumptions |
| `propstore/families/relations/projection_model.py` | Relation/stance/conflict row mapper | Typed relation/stance/conflict models | Delete |
| `propstore/families/relations/declaration.py` projection/query pieces | Relation sidecar compiler/query API | Relation semantics plus model queries | Delete generic projection/query plumbing |
| `propstore/families/micropublications/declaration.py` projection pieces | Micropub projection/query API | Micropub charter plus association object | Delete generic projection/query plumbing |
| `propstore/families/contexts/declaration.py` projection pieces | Context/lifting projection/query API | Context charter plus lifting semantics | Delete generic projection/query plumbing |
| `propstore/families/rules/declaration.py` projection pieces | Grounding sidecar persistence | Grounding charter plus semantic persistence | Delete generic projection table plumbing |
| `propstore/families/calibration/declaration.py` | Calibration count projection/query | Calibration charter plus typed query | Delete projection table plumbing |
| `propstore/families/diagnostics/declaration.py` projection pieces | Build diagnostics projection | Diagnostic charter plus typed diagnostics | Delete projection table plumbing |
| `propstore/families/embeddings/declaration.py` projection/vector pieces | Embedding sidecar/vector cache | Quire vector cache + Propstore entity policy | Delete projection/vector duplication |
| `propstore/families/claims/sidecar_runtime.py` | Claim embedding/relation runtime over raw sidecar connection | Claim runtime over Quire session/vector APIs | Replace raw derived-store connection usage |
| `propstore/families/concepts/sidecar_runtime.py` | Concept embedding runtime over raw sidecar connection | Concept runtime over Quire session/vector APIs | Replace raw derived-store connection usage |
| `propstore/world/model.py` | Primary sidecar query facade over raw SQLite | Propstore `WorldQuery` over Quire read-only sessions | Replace raw connection/selectors with model/session queries |
| `propstore/world/queries.py` | World query helpers through projection rows | Typed world query helpers | Replace projection-model imports |
| `propstore/world/bound.py` and `propstore/world/overlay.py` | Bound/overlay worlds over projection rows | Bound/overlay worlds over typed model graph/store APIs | Replace row-model imports |
| `propstore/world/atms.py` | ATMS construction through projection rows | ATMS construction through typed graph/relation models | Replace row-model imports |
| `propstore/world/scm.py`, `propstore/world/intervention.py`, `propstore/world/resolution.py` | World reasoning consumers of row-derived graph/value data | World reasoning consumers of typed graph/value data | Replace row assumptions at world boundary |
| `propstore/worldline/resolution.py` and `propstore/worldline/argumentation.py` | Worldline materialization/capture through row models | Worldline over typed world/session models | Replace projection imports and row coercion |
| `propstore/worldline/result_types.py` | Persisted result payload constructors named `from_mapping` | Explicit document/JSON payload constructors | Rename to boundary-specific constructors; keep typed result payload validation |
| `propstore/support_revision/projection.py` and `propstore/support_revision/af_adapter.py` | Support-revision projection from row models | Support-revision over typed graph/relation models | Replace projection-model imports |
| `propstore/aspic_bridge/extract.py` and `propstore/aspic_bridge/translate.py` | ASPIC bridge through stance projection model | ASPIC bridge over typed stance/justification models | Replace projection-model imports |

The final report must account for every row in this matrix.

## Helper Classification Ledger

This ledger is part of the workstream, not commentary. During execution, only
delete, rename, or replace helpers classified here or in a phase-specific
ledger update committed before implementation.

Actions:

- `delete`: remove the helper because Quire charter/SQLAlchemy machinery owns
  the behavior.
- `replace`: remove the helper after replacing callers with SQLAlchemy
  relationships/session queries/model construction.
- `move`: preserve semantic behavior in the named owner, then delete the old
  helper-shaped path.
- `keep-boundary`: keep the behavior as explicit document/result IO, with a
  boundary-specific name.

### Claim Storage Helpers

File: `propstore/families/claims/storage.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `TypedClaimFields` | replace | Replace with `ClaimNumericPayload`, `ClaimTextPayload`, and `ClaimAlgorithmPayload`; delete the storage DTO. |
| `_optional_string` | delete | Generic nullable string conversion belongs to Quire charter conversion. |
| `_optional_float_input` | delete | Generic nullable numeric conversion belongs to Quire charter conversion. |
| `_optional_int` | delete | Generic nullable integer conversion belongs to Quire charter conversion. |
| `claim_version_id` | delete | Claim version identity comes from claim identity/domain model, not row preparation. |
| `_iter_claim_concept_link_values` | replace | Construct `ClaimConceptLink` association objects from claim contracts; delete tuple-row generation. |
| `_claim_concept_link_values_for_declaration` | replace | Construct `ClaimConceptLink` association objects from claim contracts; delete tuple-row generation. |
| `normalize_conditions_differ` | delete | Condition-difference serialization belongs to the relation/stance model JSON adapter. |
| `coerce_stance_resolution` | move | Move stance resolution validation to the relation/stance semantic owner. |
| `resolution_opinion_columns` | move | Move opinion extraction to a typed stance-resolution value object. |
| `canonicalize_claim_for_storage` | move | Split raw-id/logical/artifact identity into claim identity/source promotion owners; split concept-reference lowering into claim semantic normalization; delete the storage function. |
| `extract_numeric_claim_fields` | replace | Replace with typed claim payload construction from claim contracts. |
| `extract_typed_claim_fields` | replace | Replace with typed claim payload construction from claim contracts. |
| `resolve_equation_sympy` | move | Move equation Sympy generation to claim semantic compilation. |
| `resolve_algorithm_storage` | move | Move algorithm body/canonical AST/stage handling to claim semantic compilation. |
| `extract_deferred_stance_rows_with_diagnostics` | move | Move embedded-stance validation/quarantine semantics to relation/stance owner; replace tuple rows with `Stance` models. |
| `prepare_claim_insert_row` | delete | Replace with `Claim` model construction and SQLAlchemy session add. |
| `prepare_claim_concept_link_rows` | delete | Replace with `ClaimConceptLink` association objects and SQLAlchemy relationship persistence. |

### Active Claim Runtime Helpers

File: `propstore/core/active_claims.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `ActiveClaimVariable` | move | Keep as algorithm variable value object only if the `Claim`/algorithm payload model uses it directly; otherwise move to claim algorithm payload model. |
| `_parse_conditions` | delete | Replaced by typed checked-condition fields on `Claim`; no row JSON repair. |
| `_parse_variables` | move | Move to algorithm payload document/model boundary; delete runtime row parser. |
| `_parse_checked_conditions` | delete | Quire JSON adapter plus claim model owns checked-condition loading. |
| `_require_claim_concept_link_role` | delete | SQLAlchemy `ClaimConceptLink.role` uses typed enum validation. |
| `_coerce_claim_concept_link` | delete | `SimpleNamespace` link repair is deleted; `ClaimConceptLink` is the object. |
| `ActiveClaim.from_mapping` | delete | Projection-row construction path is deleted. |
| `ActiveClaim.to_dict` | replace | Replace with explicit view/document payload rendering that does not import `CLAIM_ROW_MODEL`. |
| `ActiveClaim.to_source_claim_payload` | keep-boundary | Keep only as source document rendering, renamed to a boundary-specific source payload renderer if still needed. |
| `coerce_active_claim` | delete | Runtime receives typed `Claim` or named active view models, not mappings. |
| `coerce_active_claims` | delete | Runtime receives typed `Claim` or named active view models, not mappings. |

### Concept Declaration Helpers

File: `propstore/families/concepts/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `ConceptRelationshipProjectionRow` | delete | Replace with typed `ConceptRelationship`/relation model. |
| `ConceptSidecarRows` | delete | Replace with typed write plan/session adds. |
| `_concept_symbol_candidates` | keep-boundary | Keep as concept semantic compilation helper if still needed by parameterization/form algebra. |
| `compile_concept_sidecar_rows` | replace | Replace with typed concept/form/alias/relationship/parameterization model construction. |
| `_compile_form_algebra_rows` | move | Move form algebra semantics to form/concept semantic owner; delete row helper. |
| `ConceptRow` | delete | Replace with `Concept` model. |
| `ConceptEmbeddingSource` | replace | Replace with typed embedding source projection over `Concept` model. |
| `ParameterizationRow` | delete | Replace with `Parameterization` model. |
| `populate_concept_sidecar_rows` | delete | Replace with SQLAlchemy session add/flush through Quire build session. |
| `ConceptSearchQuerySyntaxError` | keep-boundary | Keep as app/search error type or move to concept search owner. |
| `_is_concept_search_syntax_error` | move | Move to Quire FTS/search adapter or concept search owner. |
| `fetch_concept_search_hits` | replace | Replace raw FTS SQL with Quire/SQLAlchemy FTS query API; keep presentation mapping in app layer. |
| `fetch_concept_search_hits_from_sidecar` | delete | Direct sidecar path opening is deleted; callers use Quire sessions. |
| `select_concept_by_id` | replace | Replace with SQLAlchemy session query. |
| `select_all_concepts` | replace | Replace with SQLAlchemy session query. |
| `select_concept_embedding_sources` | replace | Replace with typed embedding source query over `Concept` model. |
| `resolve_concept_embedding_entity` | move | Move concept-handle resolution policy to concept owner; implement through session query. |
| `select_aliases_by_concept_id` | replace | Replace with `Concept.aliases` relationship query. |
| `select_concept_registry_rows` | replace | Replace with typed registry projection from `Concept` models. |
| `build_concept_logical_id_index` | move | Move logical-id precedence/index semantics to concept owner; implement over typed models. |
| `resolve_concept_alias` | move | Move alias resolution policy to concept owner; implement over `Concept.aliases`. |
| `resolve_concept_id` | move | Move id/alias/logical/canonical precedence policy to concept owner; implement over typed models. |
| `select_concept_ids_for_group` | replace | Replace with `ParameterizationGroup.members` relationship. |
| `select_parameterizations_for_output_concept` | replace | Replace with `Concept.parameterizations_as_output` relationship. |
| `select_all_parameterizations` | replace | Replace with SQLAlchemy session query. |
| `select_parameterization_group_members` | replace | Replace with `ParameterizationGroup.members` relationship. |
| `select_all_form_rows` | replace | Replace with typed `Form` model query. |
| `select_form_algebra_rows_for_output` | replace | Replace with typed `FormAlgebra` model query. |
| `select_all_form_algebra_rows` | replace | Replace with typed `FormAlgebra` model query. |
| `search_concept_ids` | replace | Replace raw FTS SQL with Quire/SQLAlchemy FTS query API. |
| `count_concepts` | replace | Replace with SQLAlchemy count query through concept owner. |
| `resolve_sidecar_concept_id` | move | Move handle-resolution policy to concept owner; delete raw sidecar helper. |

### Relation Declaration Helpers

File: `propstore/families/relations/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `RelationshipRow` | delete | Replace with typed `ConceptRelation` model. |
| `StanceRow` | delete | Replace with typed `Stance` model. |
| `ConflictRow` | delete | Replace with typed `ConflictWitness` model. |
| `_optional_numeric` | delete | Generic nullable numeric conversion belongs to Quire charter conversion or typed value object validation. |
| `compile_authored_stance_sidecar_rows` | replace | Replace with `Stance` model construction. |
| `compile_authored_stance_sidecar_rows_with_diagnostics` | move | Move stance reference validation/quarantine diagnostics to relation semantic owner; delete row output. |
| `select_stances_between` | replace | Replace with SQLAlchemy relationship/session query. |
| `select_conflicts` | replace | Replace with SQLAlchemy session query over `ConflictWitness`. |
| `select_all_relationships` | replace | Replace with SQLAlchemy session query over `ConceptRelation`. |
| `select_all_claim_stances` | replace | Replace with SQLAlchemy session query over `Stance`. |
| `select_claim_stances_with_policy` | move | Move visibility/render policy semantics to relation/world owner; implement through typed query predicates. |
| `select_explanation_stances` | move | Move explanation traversal semantics to relation/world owner; implement over `Stance` relationships. |
| `count_conflicts` | replace | Replace with SQLAlchemy count query over `ConflictWitness`. |

### Micropublication Helpers

Files: `propstore/core/micropublications.py` and
`propstore/families/micropublications/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `_parse_string_tuple` | delete | Generic row string parsing is deleted. |
| `ActiveMicropublication.from_mapping` | delete | Projection-row construction path is deleted. |
| `coerce_active_micropublication` | delete | Runtime receives typed `Micropublication`/active view models, not mappings. |
| `MicropublicationProjectionRow` | delete | Replace with `Micropublication` model. |
| `MicropublicationClaimProjectionRow` | delete | Replace with `MicropublicationClaimLink` association object. |
| `MicropublicationSidecarRows` | delete | Replace with typed write plan/session adds. |
| `compile_micropublication_sidecar_rows` | replace | Replace with typed `Micropublication`/link model construction. |
| `compile_micropublication_sidecar_rows_with_diagnostics` | move | Keep missing-claim quarantine semantics in micropublication owner; delete row output. |
| `create_micropublication_tables` | delete | Quire charter creates tables. |
| `populate_micropublications` | delete | Replace with SQLAlchemy session add/flush. |
| `select_all_micropublications` | replace | Replace with SQLAlchemy session query. |

### Grounding/Rule Helpers

File: `propstore/families/rules/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `GroundedFactProjectionRow` | delete | Replace with `GroundedFact` model. |
| `GroundedFactEmptyPredicateProjectionRow` | delete | Replace with typed empty-predicate model or `GroundedFact` state. |
| `GroundedBundleInputProjectionRow` | delete | Replace with `GroundedBundleInput` model. |
| `create_grounded_fact_table` | delete | Quire charter creates tables. |
| `populate_grounded_facts` | replace | Replace with model construction/session writes while preserving four-valued bundle semantics. |
| `_persist_bundle_inputs` | replace | Replace raw row persistence with `GroundedBundleInput` model writes. |
| `_read_bundle_inputs` | replace | Replace raw row reads with `GroundedBundleInput` model queries. |
| `_encode_bundle_input` | keep-boundary | Keep as explicit grounding document/value serialization boundary, renamed if needed. |
| `_decode_bundle_input` | keep-boundary | Keep as explicit grounding document/value serialization boundary, renamed if needed. |
| `_bundle_input_payload` | keep-boundary | Keep as grounding payload conversion, not DB row helper. |
| `_is_json_value` | keep-boundary | Keep only inside grounding payload serialization. |
| `_encode_gunray_atom` | keep-boundary | Keep as Gunray payload serialization boundary. |
| `_decode_gunray_atom` | keep-boundary | Keep as Gunray payload serialization boundary. |
| `_encode_gunray_rule` | keep-boundary | Keep as Gunray payload serialization boundary. |
| `_decode_gunray_rule` | keep-boundary | Keep as Gunray payload serialization boundary. |
| `_rule_key` | keep-boundary | Keep as deterministic grounding ordering helper. |
| `read_grounded_facts` | replace | Replace raw SQL read with typed model query and bundle assembly. |
| `read_grounded_bundle` | replace | Replace raw SQL read with typed model query and bundle assembly. |
| `build_runtime_grounded_bundle` | keep-boundary | Keep semantic bundle assembly API; internally use typed model queries. |
| `_read_source_rules` | replace | Replace raw row read with `GroundedBundleInput` query plus payload decoder. |
| `_read_source_superiority` | replace | Replace raw row read with `GroundedBundleInput` query plus payload decoder. |
| `_read_source_facts` | replace | Replace raw row read with `GroundedBundleInput` query plus payload decoder. |

### Source Helpers

File: `propstore/families/sources/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `SourceProjectionRow` | delete | Replace with `Source` model. |
| `_opinion_json` | delete | Generic typed JSON storage belongs to Quire JSON adapter. |
| `compile_source_sidecar_rows` | replace | Replace with `Source` model construction. |
| `populate_sources` | delete | Replace with SQLAlchemy session add/flush. |

### Context Helpers

File: `propstore/families/contexts/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `_nullable_text` | delete | Generic nullable text conversion belongs to Quire charter conversion. |
| `_json_or_none` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `_json_mapping` | delete | Generic JSON conversion belongs to Quire JSON adapter or typed context model field. |
| `_json_string_tuple` | delete | Generic JSON conversion belongs to Quire JSON adapter or typed context model field. |
| `create_context_tables` | delete | Quire charter creates tables. |
| `populate_contexts` | delete | Replace with SQLAlchemy session add/flush. |
| `filter_invalid_context_lifting_rows` | move | Move invalid lifting-rule filtering semantics to context/lifting semantic owner. |
| `compile_context_sidecar_rows` | replace | Replace with typed `Context`, `ContextAssumption`, and `ContextLiftingRule` model construction. |
| `compile_context_lifting_materialization_rows` | replace | Replace with typed `ContextLiftingMaterialization` model construction. |
| `load_lifting_system` | move | Keep lifting-system assembly as context owner API; implement over typed model queries. |
| `_projection_row` | delete | Projection row wrapper is deleted. |
| `_lifting_materialization_row` | delete | Projection row wrapper is deleted. |

### Diagnostics Helpers

File: `propstore/families/diagnostics/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `QuarantineDiagnostic` | keep-boundary | Keep as semantic diagnostic input value object or replace with `BuildDiagnostic`; no row coupling. |
| `Written` | replace | Replace with typed write/quarantine report not tied to projection insertion. |
| `Quarantined` | replace | Replace with typed write/quarantine report not tied to projection insertion. |
| `SourceStatusDiagnosticRow` | replace | Replace with typed source-status diagnostic view over `BuildDiagnostic`. |
| `QuarantinableWriter` | replace | Replace raw insert writer with diagnostic service using SQLAlchemy session. |
| `record_build_exception` | replace | Replace raw insert with diagnostic service/session add. |
| `record_embedding_restore_diagnostic` | replace | Replace raw insert with diagnostic service/session add. |
| `record_pass_diagnostics` | move | Keep diagnostic mapping semantics; write through diagnostic service/session. |
| `record_authoring_diagnostics` | move | Keep authoring diagnostic semantics; write through diagnostic service/session. |
| `record_quarantine_diagnostics` | move | Keep quarantine diagnostic semantics; write through diagnostic service/session. |
| `compile_promotion_blocked_diagnostic_rows` | replace | Replace projection rows with `BuildDiagnostic` model construction. |
| `has_build_diagnostics_table` | delete | Schema presence validation belongs to Quire catalog validation. |
| `select_build_diagnostics` | replace | Replace with SQLAlchemy query over `BuildDiagnostic`. |
| `select_source_status_diagnostic_rows` | replace | Replace with typed source-status diagnostic query. |
| `delete_promotion_blocked_diagnostics` | replace | Replace with SQLAlchemy delete/query scoped to `BuildDiagnostic`. |

### Embedding Helpers

File: `propstore/families/embeddings/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `_require_sqlite_vec` | move | Move extension loading policy to Quire vector backend. |
| `load_vec_extension` | move | Move extension loading policy to Quire vector backend. |
| `EmbeddingSnapshot` | keep-boundary | Keep as Propstore embedding snapshot value object. |
| `EmbeddingSnapshotReport` | keep-boundary | Keep as Propstore embedding snapshot report value object. |
| `ensure_embedding_tables` | delete | Quire vector/charter machinery creates tables. |
| `SidecarEmbeddingRegistry` | replace | Replace with Quire vector registry/session API. |
| `_SidecarEntityEmbeddingStore` | replace | Replace with Quire vector entity store over SQLAlchemy session. |
| `SidecarClaimEmbeddingStore` | replace | Replace with claim-specific adapter over Quire vector entity store. |
| `SidecarConceptEmbeddingStore` | replace | Replace with concept-specific adapter over Quire vector entity store. |
| `SidecarEmbeddingSnapshotStore` | replace | Replace with Quire vector snapshot store plus Propstore snapshot report mapping. |
| `get_registered_models` | replace | Replace with Quire vector registry query. |
| `embed_claims` | replace | Keep workflow API, but route through Quire vector/session APIs. |
| `embed_concepts` | replace | Keep workflow API, but route through Quire vector/session APIs. |
| `find_similar` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_concepts` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_agree` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_disagree` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_concepts_agree` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_concepts_disagree` | replace | Replace raw vector SQL with Quire vector query API. |
| `extract_embeddings` | replace | Replace raw snapshot extraction with Quire vector snapshot API. |
| `extract_embedding_snapshot_from_store` | replace | Replace raw sidecar opening with Quire vector snapshot API. |
| `restore_embeddings` | replace | Replace raw restore with Quire vector snapshot API. |
| `restore_embedding_snapshot` | replace | Replace raw sidecar opening with Quire vector snapshot API. |

### Calibration Helpers

File: `propstore/families/calibration/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `CalibrationCountsProjectionRow` | delete | Replace with `CalibrationCount` model. |
| `load_calibration_counts` | replace | Replace raw SQL/table-missing behavior with typed optional query over `CalibrationCount`. |

### Projection Model Helper Families

Files: `propstore/families/claims/projection_model.py`,
`propstore/families/concepts/projection_model.py`, and
`propstore/families/relations/projection_model.py`.

| Helper family | Classification | Required final owner/action |
| --- | --- | --- |
| nullable scalar codecs such as `_nullable_text`, `_nullable_int`, `_nullable_float`, `_optional_float`, `_optional_int` | delete | Quire charter conversion owns generic scalar/null handling. |
| id coercion codecs such as `_claim_id`, `_concept_id`, `_context_id`, `_justification_id` | delete | SQLAlchemy mapped model fields use typed id constructors at model/document boundaries. |
| enum value codecs such as `_role_value`, `_claim_type_value`, `_algorithm_stage_value`, `_concept_status_value`, `_exactness_value`, `_stance_type_value`, `_conflict_class_value` | delete | Enum storage adapters are generic Quire SQLAlchemy adapters. |
| JSON/render helpers such as `_logical_ids_payload`, `_logical_ids_from_value`, `_logical_ids_to_columns`, `_logical_ids_from_columns`, `_provenance_to_columns`, `_provenance_from_columns`, `_source_to_columns`, `_source_from_columns`, `_normalize_conditions_differ` | replace | Replace with typed value objects and Quire JSON adapter; semantic payload rendering moves to document/view boundaries. |
| query-plan builders such as `claim_row_query_plan`, `_edge_column`, `claim_stance_policy_query_plan` | delete | SQLAlchemy relationships/session query construction replaces projection query-plan helpers. |

## Phase 1: Quire SQLAlchemy Capability Proof

Repository: `C:\Users\Q\code\quire`.

Add SQLAlchemy as a Quire dependency. Use a normal published dependency in
`pyproject.toml`; do not use a local path.

Create proof tests in Quire before implementation:

- map a plain/dataclass domain class with a Python field named `metadata` to a
  SQL column named `metadata`;
- generate SQLAlchemy `Table` objects from a small schema IR instead of writing
  Declarative class-body mappings by hand;
- map imperatively with `registry.map_imperatively`;
- persist and load enum fields without field-specific coercer functions;
- persist and load nested JSON value objects through one generic JSON type
  adapter;
- define one-to-many and many-to-one relationships;
- define an association object with payload columns;
- open a read-only SQLAlchemy session from a derived-store handle;
- prove mapped entities are not frozen/slots while nested value objects may be
  frozen when not mapped.

Required proof models:

- `Source` with `metadata`;
- `Claim`;
- `Concept`;
- `ClaimConceptLink` with `role`, `ordinal`, `binding_name`;
- `SourceTrust` as a nested JSON value object.

Required Quire gates:

```powershell
uv run pyright
uv run pytest -vv
```

The proof is complete only when tests demonstrate the exact needed behavior.
If the proof requires handwritten row dictionaries or field-specific coercers,
the proof failed.

After this phase passes, push the Quire branch and pin Propstore to the pushed
Quire commit before editing Propstore. Refresh that pushed pin after every
later Quire phase that changes the APIs consumed by Propstore.

## Phase 2: Quire Charter/Schema IR

Repository: `C:\Users\Q\code\quire`.

Introduce the generic schema declaration layer. Target files:

- `quire/charters.py`
- `quire/schema_ir.py`
- `quire/sql_types.py`
- `quire/sqlalchemy_schema.py`
- `quire/sqlalchemy_store.py`
- `quire/schema_catalog.py`

The charter API must let a consumer define one family/object declaration with:

- Python model class;
- existing Quire `ArtifactFamily` identity;
- document codec/renderer hooks;
- lifecycle/state metadata;
- field definitions and Python types;
- primary keys;
- nullable/non-null fields;
- foreign keys;
- association objects;
- JSON value object fields;
- enum fields;
- generated/default fields;
- indexes and unique constraints;
- search fields;
- vector fields;
- source-local-only fields;
- canonical-only fields;
- semantic metadata supplied by the consumer.

The charter API composes with existing Quire APIs:

- `quire.families.ArtifactFamily` remains the document family identity and
  placement/FK owner;
- `quire.family_store.DocumentFamilyStore` remains the document IO owner;
- `quire.artifacts` remains the placement/addressing owner;
- `quire.references.ForeignKeySpec` remains the source of cross-family
  reference semantics;
- charters add derived-store model/schema/query metadata for those existing
  families and do not create a second registry.

Use SQLAlchemy-native mapping primitives for relational roles:

- primary keys are derived into SQLAlchemy `Column(..., primary_key=True)`;
- FKs are derived from Quire reference specs into SQLAlchemy `ForeignKey`;
- JSON value objects use one Quire SQLAlchemy JSON type decorator;
- relationships and association objects use SQLAlchemy `relationship`;
- search/vector/index metadata is carried through charter field metadata and
  SQLAlchemy `Column.info`.

Do not make callers type SQL column names, SQL types, JSON suffixes, or
per-field codecs when the Python type, Quire reference spec, and SQLAlchemy
mapping metadata determine them. Do not introduce a parallel `PrimaryKey[T]`,
`ForeignKey[T]`, `Json[T]`, `Relation[T]`, or similar marker type family.

The IR must be serializable into a stable schema catalog payload and hash.
That hash participates in derived-store cache identity.

## Phase 3: Quire SQLAlchemy Engine

Repository: `C:\Users\Q\code\quire`.

Build the generic SQLAlchemy engine over the charter IR:

- generate SQLAlchemy `MetaData`;
- generate `Table` objects;
- map Python classes imperatively;
- generate relationships;
- generate association object mappings;
- generate generic JSON type decorators;
- generate enum storage adapters;
- generate indexes and uniqueness constraints;
- generate FKs from family references;
- create all tables in a derived SQLite store;
- write schema catalog tables;
- validate opened stores against schema catalog and schema hash;
- expose `DerivedStoreHandle.readonly_session()` and writable build-session
  APIs;
- expose a typed `DerivedSession`/query context API.

Quire owns session lifecycle. Propstore requests sessions from Quire
derived-store handles. Propstore does not create SQLAlchemy sessions directly
and does not receive raw `sqlite3.Connection` objects.

Required Quire tests:

- generated DDL has expected tables/columns/FKs/indexes;
- generated mappings can insert/query/update/delete in a temporary SQLite DB;
- readonly sessions reject writes;
- schema catalog round-trips and detects missing tables/columns;
- source hash changes when charter shape changes;
- relationship lazy/selectin loading works for source, claim, concept, and
  claim-concept-link proof models.

## Phase 4: FTS And Vector Implementation

Repository: `C:\Users\Q\code\quire` and `C:\Users\Q\code\sqlalchemy-fts5`.

FTS belongs in SQLAlchemy extension machinery, not in Quire projection classes.

Required path:

- inspect `C:\Users\Q\code\sqlalchemy-fts5`;
- confirm `C:\Users\Q\code\sqlalchemy-fts5` exists and its tests pass;
- use or fix `sqlalchemy-fts5` for FTS5 virtual tables;
- if the extension cannot express the existing concept/claim FTS needs, stop
  Quire work and fix `sqlalchemy-fts5` first;
- do not keep Quire `FtsProjection`;
- do not re-create FTS with raw string SQL hidden in Propstore.

Vector behavior:

- keep the generic entity/snapshot API of `quire/sqlite_vec_store.py`;
- replace its raw connection/table setup with SQLAlchemy-backed vector cache
  machinery where it overlaps the charter engine;
- express vector stores as charter/index/cache declarations;
- build Quire-owned SQLAlchemy vector support before Propstore embedding
  cutover;
- do not leave vector behavior as a blocker for Propstore to work around.

Required gates:

```powershell
Set-Location C:\Users\Q\code\sqlalchemy-fts5
uv run pyright
uv run pytest -vv
Set-Location C:\Users\Q\code\quire
uv run pyright
uv run pytest -vv
```

- concept-like FTS proof query;
- claim-like FTS proof query;
- vector table create/insert/search/snapshot proof;
- no local path dependency pins.

## Quire-First Completion Gate

This gate must pass before Phase 5 starts.

Quire must have:

- SQLAlchemy dependency declared from a published package source;
- charter/schema IR;
- generated SQLAlchemy tables;
- imperative mappings;
- generated relationships;
- association object mapping;
- enum conversion;
- JSON value object conversion;
- schema catalog/hash/version validation;
- writable build sessions;
- read-only runtime sessions;
- derived-store handle integration;
- FTS through `sqlalchemy-fts5` or a fixed owned SQLAlchemy extension;
- vector create/insert/search/snapshot support;
- passing Quire type and test gates.

Required commands:

```powershell
uv run pyright
uv run pytest -vv
rg -n -F -- "ProjectionTable" quire tests
rg -n -F -- "ProjectionModel" quire tests
rg -n -F -- "FtsProjection" quire tests
rg -n -F -- "VecProjection" quire tests
```

Before Phase 15, the search output is an inventory of remaining old paths, not
a passing gate. It must be copied into the phase report and no Propstore
cutover may import those old paths. Phase 15 turns these same searches into
zero-hit gates.

If this gate fails, do not start Propstore build orchestration. Fix Quire.

## Phase 5: Build Orchestration Cutover

Repository: Propstore.

This phase converts the sidecar build path before any semantic family cutover.
It ensures family phases do not run old and new production paths together.

Target files:

- `propstore/derived_build.py`
- `propstore/derived_build_plan.py`
- `propstore/families/projection_catalog.py`

Deletion-first targets:

- direct `ProjectionSchema`/`PROPSTORE_WORLD_PROJECTION_SCHEMA` creation;
- build-plan row-set abstractions whose only purpose is projection insertion;
- raw `sqlite3.Connection` sidecar population orchestration;
- build orchestration imports of Quire projection primitives.

Replacement requirements:

- `derived_build.py` obtains a Quire writable build session from a derived-store
  handle;
- build orchestration creates tables through Quire charter/catalog APIs;
- `derived_build_plan.py` carries typed domain/model write plans instead of
  projection rows;
- schema hash/cache identity is derived from Quire schema catalog payloads;
- old projection schema creation is deleted before family phases begin.

Data-parity gate:

- build the current mainline sidecar and the charter-generated sidecar from the
  same repository snapshot;
- compare table names, primary keys, row counts, and key sets;
- record explicit column rename allowances in the phase commit message;
- fail on any dropped table/key. The only accepted drop is a table already
  named as a deletion target in the current phase.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label build-orchestration-charter tests/test_build_sidecar.py tests/test_sidecar_projection_contract.py tests/test_fixture_schema_parity.py
rg -n -F -- "PROPSTORE_WORLD_PROJECTION_SCHEMA" propstore tests
rg -n -F -- "ProjectionSchema" propstore tests
rg -n -F -- "ProjectionTable" propstore/derived_build.py propstore/derived_build_plan.py propstore/families/projection_catalog.py tests
rg -n -F -- "sqlite3.Connection" propstore/derived_build.py propstore/derived_build_plan.py tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Phase 6: Source Vertical Slice

Repositories: Quire first, then Propstore.

Source is the first Propstore proof because the inventory shows it is small:
`propstore/families/sources/declaration.py` currently owns the `source`
projection table, source projection row dataclass, opinion JSON serialization,
compilation from `SourceDocument`, and insertion into the sidecar.

Target Propstore model names:

- `Source`
- `SourceOrigin`
- `SourceTrust`

Deletion-first targets:

- `SourceProjectionRow`;
- `SOURCE_PROJECTION`;
- source-specific opinion JSON helper code that generic JSON storage replaces;
- source `sqlite3.Connection` insertion helpers.

Named caller/update surfaces:

- `propstore/derived_build.py`;
- `propstore/source/status.py`;
- `propstore/source/finalize.py`;
- `propstore/source/promote.py`;
- app and CLI source/status callers that read source sidecar status.

Implementation requirements:

- define the source charter in the source family declaration;
- derive YAML/document IO and SQLAlchemy mapping from that charter;
- store nested origin/trust data as typed JSON value objects with column names
  `origin`, `trust`, `quality`, and `derived_from`;
  no `_json` suffixes are permitted in source storage columns;
- build inserts source records through a Quire SQLAlchemy session;
- runtime reads source objects through the session.

Propstore gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-charter tests/test_fixture_schema_parity.py tests/test_sidecar_projection_contract.py
```

These exact commands must pass before Phase 7:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-charter tests/test_fixture_schema_parity.py tests/test_sidecar_projection_contract.py tests/test_required_schema_completeness.py
rg -n -F -- "SourceProjectionRow" propstore tests
rg -n -F -- "SOURCE_PROJECTION" propstore tests
rg -n -F -- "quality_json" propstore tests
rg -n -F -- "derived_from_json" propstore tests
```

The first three searches are zero-hit gates outside notes, workstreams, docs,
and reports. The
`quality_json` and `derived_from_json` searches are zero-hit gates for
production Propstore code.

## Phase 7: Forms And Source Closure

Repository: Propstore.

Forms are early because concepts depend on form metadata.

Target model names:

- `Form`
- `FormAlgebra`

Keep:

- form semantic passes;
- dimensional validation;
- Bridgman/Sympy dimensional logic;
- form document authoring shape.

Delete:

- form projection table declarations embedded in concept declaration modules;
- raw form-row dictionaries;
- selectors that only wrap generic SQL selects.

Named caller/update surfaces:

- `propstore/app/forms.py`;
- `propstore/form_utils.py`;
- `propstore/families/forms/stages.py`;
- `propstore/families/concepts/declaration.py`;
- `propstore/world/model.py`.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label forms-charter tests/test_form_algebra.py tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py
rg -n -F -- "FORM_PROJECTION" propstore tests
rg -n -F -- "FORM_ALGEBRA_PROJECTION" propstore tests
rg -n -F -- "ProjectionTable(" propstore/families/concepts propstore/families/forms tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Phase 8: Concept/Form/Parameterization Slice

Repository: Propstore.

The inventory identifies `propstore/families/concepts/declaration.py` and
`propstore/families/concepts/projection_model.py` as the main concept sidecar
boundary and duplicate row mapping layer.

Target model names:

- `Concept`
- `ConceptAlias`
- `ConceptRelationship`
- `Parameterization`
- `ParameterizationGroup`
- `FormAlgebra`

Deletion-first targets:

- `propstore/families/concepts/projection_model.py`;
- `ConceptRow`;
- `ParameterizationRow`;
- `CONCEPT_ROW_MODEL`;
- `PARAMETERIZATION_ROW_MODEL`;
- concept projection codecs;
- concept search/select/count/id-resolution helpers whose only job is generic
  SQL selection;
- `_nullable_text`, concept id/status/exactness projection codecs, and logical
  id JSON render-view helpers that generic schema conversion replaces.

Named caller/update surfaces:

- `propstore/app/concept_views.py`;
- `propstore/app/concepts/display.py`;
- `propstore/app/concepts/embedding.py`;
- `propstore/families/concepts/sidecar_runtime.py`;
- `propstore/core/graph_build.py`;
- `propstore/fragility_contributors.py`;
- `propstore/graph_export.py`;
- `propstore/parameterization_walk.py`;
- `propstore/sensitivity.py`;
- `propstore/world/model.py`;
- `propstore/world/queries.py`;
- `propstore/world/bound.py`;
- `propstore/world/overlay.py`;
- `propstore/world/atms.py`;
- `propstore/worldline/resolution.py`.

Keep as semantic owner code:

- concept normalization and identity in `stages.py`;
- concept semantic passes;
- form parameter validation;
- relationship target validation;
- parameterization dimensional checks;
- CEL registry building from typed `Concept` objects;
- concept handle/alias resolution policy.

Relationships:

- `Concept.aliases: list[ConceptAlias]`;
- `Concept.relationships: list[ConceptRelationship]`;
- `Concept.parameterizations_as_output: list[Parameterization]`;
- `Parameterization.inputs` as typed relationships or explicit link objects;
- `ParameterizationGroup.members` as typed concept membership.

FTS/search:

- FTS schema is generated through Quire/SQLAlchemy extension declarations;
- app `search_concepts` keeps presentation/report ownership;
- concept family keeps only semantic search result mapping.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label concept-charter tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py tests/test_render_time_filtering.py
```

Additional required searches:

```powershell
rg -n -F -- "propstore.families.concepts.projection_model" propstore tests
rg -n -F -- "ConceptRow" propstore tests
rg -n -F -- "ParameterizationRow" propstore tests
rg -n -F -- "CONCEPT_ROW_MODEL" propstore tests
rg -n -F -- "PARAMETERIZATION_ROW_MODEL" propstore tests
rg -n -F -- "CONCEPT_PROJECTION" propstore tests
rg -n -F -- "PARAMETERIZATION_PROJECTION" propstore tests
rg -n -F -- "_nullable_text" propstore/families/concepts tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Phase 9: Context And Lifting Slice

Repository: Propstore.

Target model names:

- `Context`
- `ContextAssumption`
- `ContextLiftingRule`
- `ContextLiftingMaterialization`

Deletion-first targets:

- context `ProjectionModel` declarations;
- context table creation helpers;
- context row dictionaries;
- selectors/loaders that merely reconstruct lifting systems from raw rows.

Named caller/update surfaces:

- `propstore/app/contexts.py`;
- `propstore/context_lifting.py`;
- `propstore/world/model.py`;
- `propstore/worldline/runner.py`;
- `propstore/worldline/argumentation.py`;
- `propstore/aspic_bridge/lifting_projection.py`.

Keep:

- context authored document schema;
- context semantic passes;
- lifting rule binding and graph validation;
- `LiftingSystem` domain behavior.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label context-charter tests/test_world_query.py tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py
rg -n -F -- "CONTEXT_TABLE" propstore tests
rg -n -F -- "CONTEXT_ASSUMPTION_TABLE" propstore tests
rg -n -F -- "CONTEXT_LIFTING_RULE_TABLE" propstore tests
rg -n -F -- "CONTEXT_LIFTING_MATERIALIZATION_TABLE" propstore tests
rg -n -F -- "ProjectionModel(" propstore/families/contexts tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Phase 10: Claim Model And Association Objects

Repository: Propstore.

This is the largest family slice. The inventory identifies:

- `propstore/families/claims/documents.py` as canonical authored claim schema;
- `propstore/families/claims/projection_model.py` as split storage/read model;
- `propstore/families/claims/storage.py` as loose-dict row preparation and
  optional helper concentration;
- `propstore/core/active_claims.py` as runtime row normalization;
- `propstore/families/claims/declaration.py` as sidecar query/population API.

Target model names:

- `Claim`
- `ClaimConceptLink`
- `ClaimNumericPayload`
- `ClaimTextPayload`
- `ClaimAlgorithmPayload`

Primary relationship:

- `claim.concept_links: list[ClaimConceptLink]`

Permitted convenience view:

- `claim.concepts` as a SQLAlchemy association proxy over
  `claim.concept_links`.

It must not be the persistence owner. Link payload data must remain visible.

Deletion-first targets:

- `propstore/families/claims/projection_model.py`;
- `CLAIM_CORE_STORAGE_MODEL`;
- `CLAIM_CONCEPT_LINK_STORAGE_MODEL`;
- `CLAIM_NUMERIC_PAYLOAD_STORAGE_MODEL`;
- `CLAIM_TEXT_PAYLOAD_STORAGE_MODEL`;
- `CLAIM_ALGORITHM_PAYLOAD_STORAGE_MODEL`;
- `CLAIM_ROW_MODEL`;
- `CLAIM_*_TABLE` projection constants;
- `ClaimSidecarRows` row-carrier fields that only aggregate projection rows;
- `_optional_float_input`, `_optional_string`, `_optional_int`;
- claim projection codecs for claim id, concept id, claim type, algorithm
  stage, logical ids, provenance, source, and concept-link role;
- `ActiveClaim` row-repair coercion that duplicates the claim charter.

Named caller/update surfaces:

- `propstore/app/claim_views.py`;
- `propstore/app/claims.py`;
- `propstore/families/claims/sidecar_runtime.py`;
- `propstore/core/activation.py`;
- `propstore/core/active_claims.py`;
- `propstore/core/graph_build.py`;
- `propstore/core/analyzers.py`;
- `propstore/claim_graph.py`;
- `propstore/defeasibility.py`;
- `propstore/fragility.py`;
- `propstore/fragility_contributors.py`;
- `propstore/graph_export.py`;
- `propstore/relation_analysis.py`;
- `propstore/structured_projection.py`;
- `propstore/support_revision/projection.py`;
- `propstore/aspic_bridge/extract.py`;
- `propstore/aspic_bridge/translate.py`;
- `propstore/world/model.py`;
- `propstore/world/bound.py`;
- `propstore/world/overlay.py`;
- `propstore/world/atms.py`;
- `propstore/world/resolution.py`;
- `propstore/worldline/resolution.py`.

Keep as semantic owner code:

- claim type contracts;
- claim semantic checks;
- raw-id quarantine policy;
- draft/blocking diagnostics;
- source-local claim support;
- artifact/version/logical identity derivation;
- CEL checking and checked-condition IR;
- Sympy/algorithm canonicalization;
- unit/form compatibility checks;
- promotion-blocked diagnostics.

Payload requirements:

- use typed payload components, not parallel row dictionaries;
- numeric/text/algorithm payloads are separate SQL tables declared once in the
  claim charter;
- generic schema code derives insert/query mapping from that declaration;
- no field-specific optional conversion helper survives.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label claim-charter tests/test_world_query.py tests/test_resolution_helpers.py tests/test_render_policy_filtering.py
```

The final claim gate must prove: build, blocked/quarantine materialization,
claim lookup, concept-link roles, visibility filters, render policy, FTS,
embedding source rows, graph construction, conflict resolution, source claim
promotion, and worldline materialization.

Additional required searches:

```powershell
rg -n -F -- "propstore.families.claims.projection_model" propstore tests
rg -n -F -- "CLAIM_CORE_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_CONCEPT_LINK_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_NUMERIC_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_TEXT_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_ALGORITHM_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "_optional_float_input" propstore tests
rg -n -F -- "_optional_string" propstore tests
rg -n -F -- "_optional_int" propstore tests
rg -n -F -- "SimpleNamespace" propstore/families/claims propstore/core tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Phase 11: Relations, Stances, And Conflicts

Repository: Propstore.

The inventory identifies `relations/projection_model.py` as a parallel
projection vocabulary for relation edge, stance rows, relationship rows, and
conflict witness rows.

Target model names:

- `Stance`
- `ConceptRelation`
- `ConflictWitness`

Delete:

- `propstore/families/relations/projection_model.py`;
- `RelationshipRow`;
- `StanceRow`;
- `ConflictRow`;
- relation projection codecs;
- `CLAIM_STANCE_STORAGE_MODEL`;
- `CONCEPT_RELATIONSHIP_STORAGE_MODEL`;
- `RELATIONSHIP_ROW_MODEL`;
- `STANCE_ROW_MODEL`;
- `CONFLICT_ROW_MODEL`;
- discriminator/query-plan objects that duplicate SQLAlchemy polymorphism or
  relationship filtering.

Named caller/update surfaces:

- `propstore/aspic_bridge/extract.py`;
- `propstore/aspic_bridge/translate.py`;
- `propstore/core/analyzers.py`;
- `propstore/core/graph_build.py`;
- `propstore/graph_export.py`;
- `propstore/relation_analysis.py`;
- `propstore/support_revision/af_adapter.py`;
- `propstore/support_revision/projection.py`;
- `propstore/world/atms.py`;
- `propstore/world/bound.py`;
- `propstore/world/overlay.py`;
- `propstore/worldline/argumentation.py`.

Keep as semantic owner code:

- authored stance document schema;
- stance target/reference validation;
- quarantine diagnostics for broken claim references;
- conflict detector output semantics;
- graph edge classification.

Design decision:

- model `relation_edge` explicitly with SQLAlchemy polymorphic mapping;
- delete the second graph vocabulary and keep graph edge classification as
  Propstore semantic behavior over the mapped relation objects.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label relations-charter tests/test_graph_export.py tests/test_world_query.py tests/test_worldline.py
rg -n -F -- "propstore.families.relations.projection_model" propstore tests
rg -n -F -- "RelationshipRow" propstore tests
rg -n -F -- "StanceRow" propstore tests
rg -n -F -- "ConflictRow" propstore tests
rg -n -F -- "CLAIM_STANCE_STORAGE_MODEL" propstore tests
rg -n -F -- "CONCEPT_RELATIONSHIP_STORAGE_MODEL" propstore tests
rg -n -F -- "RELATIONSHIP_ROW_MODEL" propstore tests
rg -n -F -- "STANCE_ROW_MODEL" propstore tests
rg -n -F -- "CONFLICT_ROW_MODEL" propstore tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Phase 12: Justifications And Micropublications

Repository: Propstore.

Target model names:

- `Justification`
- `Micropublication`
- `MicropublicationClaimLink`

Deletion-first targets:

- micropublication projection tables/models/query plans;
- micropublication `*ProjectionRow` classes;
- `ActiveMicropublication.from_mapping`;
- `coerce_active_micropublication`;
- `_parse_string_tuple`;
- justification row dictionaries;
- duplicated `CanonicalJustification` schema/conversion role.

Named caller/update surfaces:

- `propstore/core/justifications.py`;
- `propstore/core/analyzers.py`;
- `propstore/aspic_bridge/extract.py`;
- `propstore/aspic_bridge/translate.py`;
- `propstore/world/model.py`;
- `propstore/worldline/argumentation.py`.

Keep:

- authored `JustificationDocument`;
- authored `MicropublicationDocument`;
- micropublication evidence/context semantics;
- active-graph-derived justification view named as a view;
- ASPIC/world justification projection behavior.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label micropub-justification-charter tests/test_world_query.py tests/test_graph_export.py
rg -n -F -- "MicropublicationProjectionRow" propstore tests
rg -n -F -- "MicropublicationClaimProjectionRow" propstore tests
rg -n -F -- "MICROPUBLICATION_ROW_MODEL" propstore tests
rg -n -F -- "ActiveMicropublication.from_mapping" propstore tests
rg -n -F -- "coerce_active_micropublication" propstore tests
rg -n -F -- "_parse_string_tuple" propstore tests
rg -n -F -- "CanonicalJustification(" propstore tests
rg -n -F -- "from_mapping" propstore/core/justifications.py tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Phase 13: Rules, Grounding, Diagnostics, Calibration, Embeddings

Repository: Propstore.

Target model names:

- `GroundedFact`
- `GroundedBundleInput`
- `BuildDiagnostic`
- `CalibrationCount`
- `EmbeddingModel`
- `EmbeddingStatus`
- `EmbeddingVector`

Delete:

- rule projection tables based on Quire `ProjectionTable`;
- diagnostics projection table declarations;
- calibration projection table declarations;
- embedding projection declarations using `ProjectionTable`/`VecProjection`;
- raw SQLite table setup for generic schema concerns.

Named caller/update surfaces:

- `propstore/grounding/inspection.py`;
- `propstore/grounding/loading.py`;
- `propstore/families/claims/sidecar_runtime.py`;
- `propstore/families/concepts/sidecar_runtime.py`;
- `propstore/app/claims.py`;
- `propstore/app/concepts/embedding.py`;
- `propstore/app/grounding.py`;
- `propstore/world/model.py`;
- `propstore/fragility_contributors.py`.

Keep:

- grounded-rule bundle semantics;
- four-valued grounded fact sections;
- deterministic bundle input persistence;
- build diagnostic/quarantine semantics;
- embedding model identity and snapshot/restore policy;
- claim/concept embedding text source policy.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label derived-support-charter tests/test_world_query.py tests/test_opinion_schema.py tests/test_fixture_schema_parity.py tests/test_required_schema_completeness.py
rg -n -F -- "GROUNDED_FACT_PROJECTION" propstore tests
rg -n -F -- "GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION" propstore tests
rg -n -F -- "GROUNDED_BUNDLE_INPUT_PROJECTION" propstore tests
rg -n -F -- "BUILD_DIAGNOSTICS_PROJECTION" propstore tests
rg -n -F -- "CALIBRATION_COUNTS_PROJECTION" propstore tests
rg -n -F -- "EMBEDDING_MODEL_PROJECTION" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n -F -- "VecProjection" propstore/families/embeddings tests
rg -n -F -- "ProjectionTable(" propstore/families/rules propstore/families/diagnostics propstore/families/calibration propstore/families/embeddings tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Phase 14: WorldQuery, Graph, And Reasoning Cutover

Repository: Propstore.

`WorldQuery` remains Propstore's semantic read facade. It stops being a raw
SQLite facade.

Delete:

- direct `sqlite3.Connection` runtime assumptions in `WorldQuery`;
- family selectors that accept raw connections where a session/model query is
  the real abstraction;
- graph construction coercion through projection row models;
- raw SQL snippets that duplicate SQLAlchemy query construction.

Keep:

- world-facing APIs;
- cache ownership;
- condition solver/lifting caches;
- historical query behavior;
- render policy semantics;
- app facade behavior.

Target:

- `WorldQuery` requests a Quire derived-store read-only SQLAlchemy session
  from a Quire derived-store handle;
- family query APIs accept a session or typed repository/world context;
- graph construction consumes typed model objects;
- resolution consumes typed claims/concepts/stances/conflicts;
- app/CLI/web surfaces see no schema-layer change except better behavior.

Named caller/update surfaces:

- `propstore/world/model.py`;
- `propstore/world/queries.py`;
- `propstore/world/bound.py`;
- `propstore/world/overlay.py`;
- `propstore/world/atms.py`;
- `propstore/world/scm.py`;
- `propstore/world/intervention.py`;
- `propstore/world/resolution.py`;
- `propstore/core/graph_build.py`;
- `propstore/core/analyzers.py`;
- `propstore/graph_export.py`;
- `propstore/worldline/resolution.py`;
- `propstore/worldline/argumentation.py`;
- `propstore/support_revision/projection.py`;
- `propstore/support_revision/af_adapter.py`;
- `propstore/aspic_bridge/extract.py`;
- `propstore/aspic_bridge/translate.py`.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label world-charter tests/test_world_query.py tests/test_worldline.py tests/test_graph_export.py tests/test_worldline_ic_merge_properties.py
rg -n -F -- "sqlite3.Connection" propstore/world propstore/families tests
rg -n -F -- "row_factory" propstore/world propstore/families tests
rg -n -F -- "connect_sqlite_store" propstore/world propstore/families tests
rg -n -F -- "ProjectionRow" propstore/world propstore/families tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Phase 15: Delete Quire Projection Modules

Repository: Quire.

After all Propstore and Quire consumers have moved:

Delete:

- `quire/projection_mapping.py`;
- `quire/projections.py`;
- public exports for projection classes from `quire/__init__.py`;
- tests that only test deleted projection primitives.

Replace with:

- charter IR tests;
- SQLAlchemy mapping tests;
- schema catalog tests;
- FTS/vector extension tests;
- derived-store session tests.

Search gates in Quire:

```powershell
rg -n -F -- "ProjectionTable" quire tests
rg -n -F -- "ProjectionModel" quire tests
rg -n -F -- "ProjectionCodec" quire tests
rg -n -F -- "ScalarPath" quire tests
rg -n -F -- "ReferencePath" quire tests
rg -n -F -- "FtsProjection" quire tests
rg -n -F -- "VecProjection" quire tests
```

Zero production hits are permitted. Documentation hits are limited to notes,
workstreams, docs, and reports.

## Phase 16: Delete Propstore Projection And Helper Leftovers

Repository: Propstore.

Delete:

- `propstore/families/claims/projection_model.py`;
- `propstore/families/concepts/projection_model.py`;
- `propstore/families/relations/projection_model.py`;
- `propstore/families/projection_catalog.py`;
- embedded projection declarations in family declaration modules;
- row classes that duplicate domain models;
- manual select/count/insert/decode/attached-row helpers that are generic DB
  plumbing;
- manual field coercers now owned by the charter engine.

Search gates in Propstore:

```powershell
rg -n -F -- "ProjectionTable" propstore tests
rg -n -F -- "ProjectionModel" propstore tests
rg -n -F -- "ProjectionCodec" propstore tests
rg -n -F -- "ProjectionRow" propstore tests
rg -n -F -- "ScalarPath" propstore tests
rg -n -F -- "ReferencePath" propstore tests
rg -n -F -- "FtsProjection" propstore tests
rg -n -F -- "VecProjection" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "CONCEPT_ROW_MODEL" propstore tests
rg -n -F -- "STANCE_ROW_MODEL" propstore tests
rg -n -F -- "RELATIONSHIP_ROW_MODEL" propstore tests
rg -n -F -- "SOURCE_PROJECTION" propstore tests
rg -n -F -- "PROPSTORE_WORLD_PROJECTION_SCHEMA" propstore tests
rg -n -F -- "_optional_float_input" propstore tests
rg -n -F -- "_optional_string" propstore tests
rg -n -F -- "_optional_int" propstore tests
rg -n -F -- "_claim_optional_float" propstore tests
rg -n -F -- "_parse_string_tuple" propstore tests
rg -n -F -- "coerce_active_micropublication" propstore tests
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
```

Zero production hits are permitted. Documentation hits are limited to notes,
workstreams, docs, and reports. External IO boundary constructors must use
boundary-specific names such as `from_yaml_payload`, `from_json_payload`, or
`from_row_mapping`; the generic `from_mapping` constructor name is deleted from
core, families, world, worldline, support-revision, and tests.

## Phase 17: Final Gates

Quire:

```powershell
uv run pyright
uv run pytest -vv
```

Propstore:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label sqlalchemy-charter-full
```

Dependency pin:

- push Quire first;
- pin Propstore to the pushed Quire commit/tag;
- update `uv.lock`;
- no local path dependency references.

Final dependency search:

```powershell
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
```

The final dependency gate must inspect parsed `pyproject.toml` source tables.
A Quire dependency entry that resolves only from the local filesystem fails the
gate even when the string searches above miss it.

## Completion Criteria

The workstream is complete only when:

- Quire has a SQLAlchemy-backed charter/schema engine.
- Quire derived-store handles open read-only SQLAlchemy sessions.
- Quire schema catalogs describe the derived store from the same charters that
  generated the mappings.
- Quire charters compose with existing `ArtifactFamily`, document-store,
  placement, and reference/FK APIs instead of replacing them with a parallel
  registry.
- Quire projection modules and projection public exports are deleted.
- Propstore supplies domain charters for every sidecar family.
- `propstore/derived_build.py` and `propstore/derived_build_plan.py` use Quire
  writable sessions and charter catalogs, not projection schemas or raw
  sidecar row plans.
- Propstore no longer imports Quire projection primitives.
- Propstore has no family `projection_model.py` files.
- Propstore has no duplicate `*Row` model layer for domain objects.
- `claim.concept_links` is the primary relationship and
  `ClaimConceptLink` owns role/ordinal/binding metadata.
- Micropublication claim links, aliases, parameterizations, context lifting
  records, stances, and conflicts are typed models or association objects.
- Source-local and canonical states are explicit charter/lifecycle states.
- Manual helper/coercer families listed in the search gates are deleted.
  Remaining IO boundary constructors use boundary-specific names and do not use
  the generic `from_mapping` name.
- `WorldQuery` uses Quire sessions and typed model queries.
- Every matrix row has been accounted for in a commit message or final closure
  report with delete/move/keep-as-semantic-owner outcome.
- Every family cutover has a passing data-parity gate for row counts, key
  sets, representative owner-layer queries, FTS, vector, and diagnostics where
  applicable.
- App/CLI/web surfaces continue to call owner-layer APIs.
- Quire and Propstore gates pass.
- Propstore is pinned to a pushed Quire commit, never a local checkout.
