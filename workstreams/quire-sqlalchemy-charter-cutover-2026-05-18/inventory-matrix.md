# Inventory Deletion Matrix

Date: 2026-05-18

## Refactor Zen

This workstream succeeds only if the refactor removes duplicate structure and
makes the project smaller, clearer, and more beautiful. Field and schema shape
is written once in Quire charters or in the exact Propstore semantic owner; do
not restate it in helper families, casts, kwargs builders, row DTOs, projection
models, or model-layer normalizers. After an IO boundary has parsed input, the
type system carries meaning: no generic coercion, loose mapping repair, shim,
adapter, alias, compatibility bridge, or old/new dual path is allowed. Delete
the old production surface first; compiler, type, test, and search failures are
the work queue. If a bridge feels necessary, stop and move parsing/validation
to the owning boundary or add the missing Quire generic capability.

This matrix is executable inventory for the Quire SQLAlchemy charter cutover. Every implementation child workstream must read the rows it owns before editing code, execute the listed action, and account for the row in a commit message or final closure report.

## Matrix Rules

- `Current owner` names the production surface that owns the behavior now.
- `Final owner` names the only production owner allowed after the cutover.
- `Action` is mandatory for the owning child workstream.
- `Child workstream owner file` is the file that owns execution and closure for the row.
- Rows assigned to `13-final-deletion-gates.md` are final deletion closures after all consumers have moved.
- Rows assigned to semantic family workstreams must follow the global family cutover loop in `00-index.md`.
- No row is complete until its old-path search gate passes outside notes, workstreams, docs, and reports.

| Inventory surface | Current owner | Final owner | Action | Child workstream owner file |
| --- | --- | --- | --- | --- |
| `../quire/quire/projections.py` | Quire handwritten SQLite projection primitives | Quire SQLAlchemy charter engine | Delete after all consumers move. | `13-final-deletion-gates.md` |
| `../quire/quire/projection_mapping.py` | Quire object-to-row mapper | Quire SQLAlchemy mapper/session engine | Delete after all consumers move. | `13-final-deletion-gates.md` |
| `../quire/quire/derived_store.py` | Quire derived SQLite lifecycle | Quire SQLAlchemy derived-store lifecycle | Keep and adapt to SQLAlchemy sessions/catalog. | `02-quire-sqlalchemy-engine.md` |
| `../quire/quire/derived_runtime.py` | Quire SQLite runtime/validation/meta projection | Quire SQLAlchemy runtime/catalog validation | Keep runtime policy; replace projection-schema validation with SQLAlchemy catalog validation. | `02-quire-sqlalchemy-engine.md` |
| `../quire/quire/families.py` | Quire artifact family registry | Quire family registry plus charter registration | Keep; compose charters with `ArtifactFamily` instead of creating a parallel family registry. | `01-quire-capability-and-charter.md` |
| `../quire/quire/family_store.py` | Quire document family IO | Quire document family IO | Keep; charter work must not duplicate document IO. | `01-quire-capability-and-charter.md` |
| `../quire/quire/artifacts.py` | Quire artifact placement/addressing | Quire artifact placement/addressing | Keep; charters reference existing artifact family identities. | `01-quire-capability-and-charter.md` |
| `../quire/quire/references.py` | Quire reference/FK validation | Quire reference/FK validation plus SQLAlchemy FKs | Keep; derive SQLAlchemy FKs from the same reference specs. | `01-quire-capability-and-charter.md` |
| `../quire/quire/sqlite_vec_store.py` | Quire sqlite-vec persistence | Quire SQLAlchemy-backed vector cache machinery | Keep the generic entity/snapshot API; replace raw connection/table plumbing with SQLAlchemy/vector extension integration. | `03-quire-fts-vector.md` |
| `propstore/derived_build.py` | Propstore sidecar build orchestration over projection tables | Propstore orchestration over Quire writable sessions and charters | Replace projection schema creation/population with charter-driven session writes. | `04-propstore-build-orchestration.md` |
| `propstore/derived_build_plan.py` | Propstore row-oriented build plan | Propstore typed domain-object build plan | Replace row sets with typed model/session write plans. | `04-propstore-build-orchestration.md` |
| `propstore/families/projection_catalog.py` | Propstore manual world schema assembly | Quire schema catalog over Propstore charters | Delete; replace with Propstore world charter registration through the Quire catalog. | `04-propstore-build-orchestration.md` |
| `propstore/families/sources/declaration.py` projection pieces | Source sidecar projection | Source charter plus Quire SQLAlchemy | Delete projection rows/tables/helpers. | `05-source-and-diagnostics.md` |
| `propstore/core/claim_values.py` source/trust mapping constructors | Generic source/trust payload constructors named `from_mapping` | Explicit source document/JSON payload constructors | Rename to boundary-specific constructors; keep typed value validation. | `05-source-and-diagnostics.md` |
| `propstore/source/status.py` | Source status SQL queries | Source owner query over Quire session | Replace raw SQL with model/session query. | `05-source-and-diagnostics.md` |
| `propstore/source/finalize.py` and `propstore/source/promote.py` | Source promotion/finalize diagnostics into sidecar surfaces | Source subsystem plus diagnostic charter | Keep semantics; route diagnostics through typed diagnostic models. | `05-source-and-diagnostics.md` |
| `propstore/form_utils.py` | Duplicate form loading/parsing facade | `propstore/families/forms/stages.py` | Delete duplicate facade after callers use the family owner. | `06-forms-concepts-parameterizations.md` |
| `propstore/families/forms/stages.py` | Form semantic stage/loading owner | Form parsing/validation module plus form charter | Keep; expose form model data to Quire charter without duplicating parsing. | `06-forms-concepts-parameterizations.md` |
| `propstore/families/concepts/projection_model.py` | Concept row mapper | Concept charter plus Quire SQLAlchemy | Delete. | `06-forms-concepts-parameterizations.md` |
| `propstore/families/concepts/declaration.py` projection/query pieces | Concept sidecar compiler/query API | Concept semantics plus model queries | Delete generic projection/query plumbing. | `06-forms-concepts-parameterizations.md` |
| `propstore/families/claims/projection_model.py` claim-owned symbols | Claim split storage/read mapper plus co-located justification residual | Claim charter plus association objects | Delete claim-owned symbols; leave only `JUSTIFICATION_STORAGE_MODEL` residual for Phase 10. | `08-claims-active-claims.md` |
| `propstore/families/claims/declaration.py` projection compiler/populator paths | Claim sidecar compiler, raw projection-row writes, claim diagnostic row writes | Claim model construction, typed write plans, Quire sessions, and diagnostic model construction | Delete `compile_claim_sidecar_rows`, `populate_claims`, claim-family `ProjectionRow` usage, and claim-family `BUILD_DIAGNOSTICS_PROJECTION` writes. | `08-claims-active-claims.md` |
| `propstore/families/claims/storage.py` storage shaping | Loose claim row preparation/helpers | Claim charter generic conversion | Delete storage-shaped helpers. | `08-claims-active-claims.md` |
| `propstore/families/claims/storage.py` semantic conversions | Raw-id canonicalization, concept-ref resolution, unit normalization, stance-resolution conversion | `propstore/families/identity/claims.py`, `propstore/source/claims.py`, `propstore/families/claims/references.py`, `propstore/families/claims/stages.py`, `propstore/families/relations/declaration.py`, and `propstore/families/diagnostics/declaration.py` | Move each semantic to its exact named owner before deleting storage-shaped remainder. | `08-claims-active-claims.md` |
| `propstore/families/claims/stages.py` sidecar row carriers | Stage bundle classes containing `ProjectionRow` sidecar carriers | Claim semantic stage bundles plus typed write plans | Delete `*SidecarRows`; keep `ClaimCheckedBundle` only as semantic compiler-stage bundle. | `08-claims-active-claims.md` |
| `propstore/core/active_claims.py` row coercion | Runtime row repair | Typed `Claim` model plus query-state filters | Delete projection-row coercion and the parallel active claim object family. | `08-claims-active-claims.md` |
| `propstore/core/graph_build.py` | Graph construction through projection models | Graph construction from typed model/session APIs | Replace row-model coercion with typed model reads. | `12-world-query-graph-reasoning.md` |
| `propstore/core/graph_types.py` provenance mapping constructors | Generic graph provenance payload constructors named `from_mapping` | Explicit graph/provenance payload constructors | Rename to boundary-specific constructors; keep graph provenance validation. | `12-world-query-graph-reasoning.md` |
| `propstore/core/analyzers.py` | Analyzer inputs through projection models | Analyzer inputs from typed graph/relation/claim models | Replace row coercion with typed model inputs. | `12-world-query-graph-reasoning.md` |
| `propstore/core/justifications.py` | Active graph justification view | Propstore semantic justification view | Keep semantic view; delete duplicate schema/conversion role. | `10-micropublications-justifications.md` |
| `propstore/families/claims/projection_model.py` justification residual | `JUSTIFICATION_STORAGE_MODEL` co-located in the old claim projection module | `Justification` charter plus owner APIs | Delete `JUSTIFICATION_STORAGE_MODEL` and the residual file after Phase 8 deletes claim-owned symbols. | `10-micropublications-justifications.md` |
| `propstore/graph_export.py` | Graph export from projection model rows | Graph export from typed world/session models | Replace projection-model imports. | `12-world-query-graph-reasoning.md` |
| `propstore/relation_analysis.py` | Stance summary through projection model rows | Stance summary from typed relation models | Replace projection-model imports. | `09-relations-stances-conflicts.md` |
| `propstore/parameterization_walk.py` | Parameterization traversal through row coercion | Parameterization traversal over typed models | Replace projection-model imports. | `06-forms-concepts-parameterizations.md` |
| `propstore/structured_projection.py` | Analyzer projection back to assertions | Typed assertion projection owner | Replace row-derived data assumptions. | `12-world-query-graph-reasoning.md` |
| `propstore/families/relations/projection_model.py` | Relation/stance/conflict row mapper | Typed relation/stance/conflict models | Delete. | `09-relations-stances-conflicts.md` |
| `propstore/families/relations/declaration.py` projection/query pieces | Relation sidecar compiler/query API | Relation semantics plus model queries | Delete generic projection/query plumbing. | `09-relations-stances-conflicts.md` |
| `propstore/families/micropublications/declaration.py` projection pieces | Micropub projection/query API | Micropub charter plus association object | Delete generic projection/query plumbing. | `10-micropublications-justifications.md` |
| `propstore/families/contexts/declaration.py` projection pieces | Context/lifting projection/query API | Context charter plus lifting semantics | Delete generic projection/query plumbing. | `07-contexts-lifting.md` |
| `propstore/families/rules/declaration.py` projection pieces | Grounding sidecar persistence | Grounding charter plus semantic persistence | Delete generic projection table plumbing. | `11-rules-grounding-calibration-embeddings.md` |
| `propstore/families/calibration/declaration.py` | Calibration count projection/query | Calibration charter plus typed query | Delete projection table plumbing. | `11-rules-grounding-calibration-embeddings.md` |
| `propstore/families/diagnostics/declaration.py` projection pieces | Build diagnostics projection | Diagnostic charter plus typed diagnostics | Delete projection table plumbing. | `05-source-and-diagnostics.md` |
| `propstore/families/embeddings/declaration.py` projection/vector pieces | Embedding sidecar/vector cache | Quire vector cache plus Propstore entity policy | Delete projection/vector duplication. | `11-rules-grounding-calibration-embeddings.md` |
| `propstore/families/claims/sidecar_runtime.py` | Claim embedding/relation runtime over raw sidecar connection | Claim runtime over Quire session/vector APIs | Replace raw derived-store connection usage. | `11-rules-grounding-calibration-embeddings.md` |
| `propstore/families/concepts/sidecar_runtime.py` | Concept embedding runtime over raw sidecar connection | Concept runtime over Quire session/vector APIs | Replace raw derived-store connection usage. | `11-rules-grounding-calibration-embeddings.md` |
| `propstore/world/model.py` | Primary sidecar query facade over raw SQLite | Propstore `WorldQuery` over Quire read-only sessions | Replace raw connection/selectors with model/session queries. | `12-world-query-graph-reasoning.md` |
| `propstore/world/queries.py` | World query helpers through projection rows | Typed world query helpers | Replace projection-model imports. | `12-world-query-graph-reasoning.md` |
| `propstore/world/queries.py` active report naming | `WorldBindActiveReport` active-object spelling | `WorldBindActivationReport` | Rename to `WorldBindActivationReport` and update callers. | `12-world-query-graph-reasoning.md` |
| `propstore/world/bound.py` and `propstore/world/overlay.py` | Bound/overlay worlds over projection rows | Bound/overlay worlds over typed model graph/store APIs | Replace row-model imports. | `12-world-query-graph-reasoning.md` |
| `propstore/world/atms.py` | ATMS construction through projection rows | ATMS construction through typed graph/relation models | Replace row-model imports. | `12-world-query-graph-reasoning.md` |
| `propstore/world/scm.py`, `propstore/world/intervention.py`, `propstore/world/resolution.py` | World reasoning consumers of row-derived graph/value data | World reasoning consumers of typed graph/value data | Replace row assumptions at world boundary. | `12-world-query-graph-reasoning.md` |
| `propstore/worldline/resolution.py` and `propstore/worldline/argumentation.py` | Worldline materialization/capture through row models | Worldline over typed world/session models | Replace projection imports and row coercion. | `12-world-query-graph-reasoning.md` |
| `propstore/worldline/result_types.py` | Persisted result payload constructors named `from_mapping` | Explicit document/JSON payload constructors | Rename to boundary-specific constructors; keep typed result payload validation. | `12-world-query-graph-reasoning.md` |
| `propstore/support_revision/projection.py` and `propstore/support_revision/af_adapter.py` | Support-revision projection from row models | Support-revision over typed graph/relation models | Replace projection-model imports. | `12-world-query-graph-reasoning.md` |
| `propstore/support_revision/state.py`, `history.py`, `snapshot_types.py`, and `explanation_types.py` | Support-revision persisted payload constructors named `from_mapping` | Explicit document/JSON payload constructors | Rename to boundary-specific constructors; keep typed revision payload validation. | `12-world-query-graph-reasoning.md` |
| `propstore/aspic_bridge/extract.py` and `propstore/aspic_bridge/translate.py` | ASPIC bridge through stance projection model | ASPIC bridge over typed stance/justification models | Replace projection-model imports. | `12-world-query-graph-reasoning.md` |

## Closure Checklist

Before the full cutover is complete:

1. Every row above has a commit message or final closure report entry naming the final outcome.
2. Every `Delete` action has a zero-hit search gate outside notes, workstreams, docs, and reports.
3. Every `Replace` action has caller updates and parity results in the owning child workstream report.
4. Every `Keep` action has confirmation that the kept code no longer owns generic projection/read-model plumbing.
5. Every `Move` action preserves semantic behavior in the named final owner and deletes the old helper-shaped production path.
