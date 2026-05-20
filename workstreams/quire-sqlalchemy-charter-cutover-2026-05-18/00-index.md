# Quire SQLAlchemy Charter Cutover Index

Date: 2026-05-18

This directory splits `workstreams/quire-sqlalchemy-charter-cutover-workstream-2026-05-18.md` into executable child workstreams. This file is the global control surface. Child workstreams must preserve this ordering and cannot weaken these rules.

## Target Architecture

Replace Propstore's duplicated projection/read-model/helper layer and Quire's handwritten SQLite projection layer with one Quire-owned charter/schema engine backed by SQLAlchemy.

Final state:

- Quire owns generic typed Git artifact families, family charters, schema IR, Python-type-to-SQL mapping, SQLAlchemy table/mapping generation, sessions, derived SQLite lifecycle, schema catalog metadata, FKs, indexes, FTS/vector hooks, and generic query mechanics.
- Propstore owns Propstore domain charters and semantic behavior: claims, concepts, sources, stances, justifications, contexts, forms, rules, micropublications, source-local authoring, promotion, world reasoning, semantic validators, and policy compilation.
- Propstore has no handwritten projection-model layer, no `*Row` classes that duplicate domain models, no `ProjectionTable`/`ProjectionModel` usage, no manual optional-number/string/id coercer families, and no fake ORM.
- The queryable sidecar is a generated Quire derived store over Propstore charters. It can be deleted and rebuilt from Git artifacts.
- Runtime data access uses Quire-opened SQLAlchemy sessions and Propstore domain model classes.

## Sources Read

This split is based on:

- `workstreams/quire-sqlalchemy-charter-cutover-workstream-2026-05-18.md`;
- `notes/architecture-wanted-outcome-2026-05-17.md`;
- `reports/code-inventory-2026-05-17.md`;
- current Quire source around `families.py`, `derived_store.py`, `derived_runtime.py`, `projections.py`, and `projection_mapping.py`;
- current Propstore source around family projection declarations, `derived_build.py`, and `world/model.py`;
- SQLAlchemy 2.1 docs for dataclass mapping, imperative mapping, relationship mapping, and association object pattern.

## SQLAlchemy Capability Decision

SQLAlchemy is a required capability gate, not an assumption. Prove the exact architecture in Quire before touching Propstore production paths.

Expected capabilities:

- SQLAlchemy supports imperative mappings with `registry.map_imperatively`.
- Imperative mapping lets Quire generate `Table` objects from a schema IR and map already-defined Python classes to those tables.
- Imperative mapping avoids Declarative's reserved-name class-body collision, including the `metadata` field case.
- SQLAlchemy relationships cover one-to-many and many-to-one links.
- SQLAlchemy's association object pattern is the persistence shape for join rows with payload columns, including `ClaimConceptLink`.
- SQLAlchemy dataclass integration does not support frozen/slots mapped entities, so mapped domain objects must be instrumentable. Nested value objects remain frozen when they are not SQLAlchemy-mapped entities.
- SQLAlchemy attrs support is imperative-only and not the foundation here.

If any capability gate fails, fix Quire or the SQLAlchemy extension first. Do not create a Propstore workaround.

## Non-Goals

- Do not move Propstore semantics into Quire.
- Do not delete source-local authoring scope.
- Do not replace Propstore projection models with `propstore.sidecar.models`, `models.py`, or any other parallel schema package.
- Do not use Pydantic or attrs as the core schema engine. The core schema engine is Quire charters plus SQLAlchemy imperative mapping.
- Do not keep old and new projection systems in production at the same time.
- Do not pin dependencies to local paths.
- Do not preserve `ProjectionTable`, `ProjectionModel`, or `*Row` aliases for compatibility.
- Do not hand-roll ORM behavior that SQLAlchemy already owns.

## Global Execution Rules

- Execute deletion-first.
- This directory is the control surface. Do not execute a nearby plan, substitute plan, spike output, implementation idea, or equivalent cleanup.
- Literal phase text wins over agent judgment. If the next action is not named by the current phase or required by a current-phase gate, stop and report the mismatch.
- Do not introduce a new package, abstraction, schema style, migration bridge, compatibility layer, or helper family during execution.
- Do not broaden from the current phase to another family because a nearby failure is interesting. Finish, block, or update the phase order before continuing.
- Do not use passing tests, a clean commit, a useful proof, or a partial family cutover as completion while old-path search gates still fail.
- Do not leave old/new dual production paths. The Quire charter engine must subsume the old projection schema before any Propstore family cutover. Family phases delete old writes and callers instead of running old and new read paths side by side.
- Move files when the change is actually a move. Use `git mv` for same-repo moves.
- Use Rope for Python symbol renames, symbol moves, and import-updating refactors
  when the target is a project-wide Python API such as a model, resolver,
  protocol, or graph type. Run the relevant `rg` gates after Rope to catch
  string references, tests, docs, and any dynamic imports Rope cannot see.
- For cross-repo Quire/Propstore changes, preserve move intent in commit messages and keep source/deletion slices paired.
- Commit every intentional edit slice atomically with path-limited git commands in the repository being edited.
- Push Quire changes before pinning Propstore to a Quire commit.
- Use `uv run ...` for Python tooling.
- Run Propstore tests through `scripts/run_logged_pytest.ps1`.
- After each passing substantial test run, reread this index and the active child workstream before choosing the next slice.
- Before implementation, mechanically check the phase order.

## Forbidden Failure Modes

These are workstream failures:

- executing a task that is not the current workstream phase;
- treating a spike, proof, or helper as the requested production work;
- adding wrappers/adapters/aliases instead of deleting the old production surface;
- changing a field name, relationship name, package boundary, or owner boundary without updating the workstream first;
- doing cleanup outside the current family slice;
- porting a caller while leaving the old callee as a production path;
- inventing a schema declaration outside Quire when the current target is the Quire charter engine;
- reusing Quire projection primitives after the current phase says they are deleted;
- claiming a helper is gone without running the named search gate;
- claiming SQLAlchemy capability without a Quire proof test that exercises the exact feature;
- treating this index, `inventory-matrix.md`, or the active child workstream as advisory once implementation starts.

## Child Workstream Files

Sibling files:

- `00-index.md`: global target architecture, rules, phase order, dependency rules, parity/search rules, and completion criteria.
- `inventory-matrix.md`: full inventory deletion matrix with current owner, final owner, required action, and child workstream owner file.
- `01-quire-capability-and-charter.md`: Quire dependency, SQLAlchemy capability proof, and charter/schema IR.
- `02-quire-sqlalchemy-engine.md`: Quire SQLAlchemy table/mapping/session/catalog engine.
- `03-quire-fts-vector.md`: FTS and vector implementation in Quire and `sqlalchemy-fts5`.
- `04-propstore-build-orchestration.md`: Propstore build orchestration cutover.
- `05-source-and-diagnostics.md`: source model/charter vertical slice and diagnostic model cutover.
- `06-forms-concepts-parameterizations.md`: forms, concepts, aliases, relationships, and parameterizations.
- `07-contexts-lifting.md`: context and lifting slice.
- `08-claims-active-claims.md`: claim model, association objects, and active-claim runtime.
- `09-relations-stances-conflicts.md`: relations, stances, and conflicts slice.
- `10-micropublications-justifications.md`: justifications and micropublications slice.
- `11-rules-grounding-calibration-embeddings.md`: rules, grounding, calibration, embeddings, and vector runtimes.
- `12-world-query-graph-reasoning.md`: WorldQuery, session, graph, and reasoning cutover.
- `13-final-deletion-gates.md`: delete Quire projection modules, delete Propstore projection/helper leftovers, final gates, docs, and dependency pin.

## Phase Order

Execute in this exact order:

| Phase | Child workstream file | Gate to proceed |
| --- | --- | --- |
| 0. Mechanical order check and current-state inventory confirmation | `00-index.md` and `inventory-matrix.md` | Phase 0 checklist below is complete; order checker passes; inventory, architecture note, worktree state, Quire pin, and old-path imports are listed. |
| 1-2. Quire SQLAlchemy capability proof and charter/schema IR | `01-quire-capability-and-charter.md` | Quire proof tests pass; charter/schema IR composes with existing family/document/placement/reference APIs. |
| 3. Quire SQLAlchemy table/mapping/session/catalog engine | `02-quire-sqlalchemy-engine.md` | Generated DDL, mapping, sessions, relationships, schema catalog, and hash tests pass. |
| 4. Quire FTS and vector implementation | `03-quire-fts-vector.md` | `sqlalchemy-fts5` and Quire FTS/vector gates pass with no local dependency pins. |
| Quire-first completion gate | `03-quire-fts-vector.md` | Quire has the full SQLAlchemy charter engine before Propstore build orchestration starts. |
| 5. Build orchestration cutover | `04-propstore-build-orchestration.md` | Propstore build path uses Quire writable sessions and charter catalogs, with data parity. |
| 6. Source and diagnostics slice | `05-source-and-diagnostics.md` | Source projection rows/tables/helpers and diagnostic projection tables are deleted; parity passes. |
| 7-8. Forms, concepts, and parameterizations slice | `06-forms-concepts-parameterizations.md` | Duplicate form facade and concept/form/parameterization projection surfaces are deleted; parity passes. |
| 9. Context/lifting slice | `07-contexts-lifting.md` | Context/lifting projection surfaces are deleted and parity passes. |
| 10. Claim model and association-object slice | `08-claims-active-claims.md` | Claim split row models/helpers and active-claim row coercion are deleted; claim parity passes. |
| 11. Relations/stances/conflicts slice | `09-relations-stances-conflicts.md` | Relation/stance/conflict row models are deleted and parity passes. |
| 12. Justifications and micropublications slice | `10-micropublications-justifications.md` | Micropublication/justification projection surfaces are deleted and parity passes. |
| 13. Rules/grounding/calibration/embeddings slice | `11-rules-grounding-calibration-embeddings.md` | Support families use typed models and Quire vector APIs. |
| 14. WorldQuery/session/graph/reasoning cutover | `12-world-query-graph-reasoning.md` | WorldQuery uses Quire sessions and typed model queries. |
| 15-17. Final deletion gates and dependency pin | `13-final-deletion-gates.md` | Quire projection modules and Propstore projection/helper leftovers are deleted; full gates pass; Propstore is pinned to a pushed Quire commit/tag. |

## Phase 0: Mechanical Order Check And Current-State Inventory Confirmation

Repository: Propstore for the workstream check, Quire for dependency checks.

Before any implementation edit:

1. Create or update `scripts/check_workstream_order.py`.
2. The checker reads `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/00-index.md`, extracts the Phase Order table, extracts prerequisite file references from every child workstream, and fails when a child depends on a later phase.
3. Run the checker:

```powershell
uv run scripts/check_workstream_order.py workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/00-index.md
```

4. Confirm `reports/code-inventory-2026-05-17.md` still exists and is the controlling inventory.
5. Confirm `notes/architecture-wanted-outcome-2026-05-17.md` still says Quire owns generic charter/schema/SQLAlchemy derived-store machinery.
6. Capture the current Propstore worktree state.
7. Capture the current Quire worktree state before editing Quire.
8. List the current Quire dependency pin in Propstore.
9. List every current production import of Quire projection primitives in Propstore.

Required Phase 0 searches:

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

This phase proves the starting state and the work queue. Missing inventory, missing architecture note, a dirty task-owned worktree, a local Quire dependency pin, or a failing order checker blocks implementation.

No Propstore family production cutover starts until Phases 1-5 pass. Source is not a place to discover whether SQLAlchemy can handle metadata fields, association objects, FTS, sessions, schema catalogs, JSON adapters, enum conversion, data parity, or build orchestration. All of that is Quire and build-orchestration work first.

## Global Dependency Pin Rule

- Add SQLAlchemy as a normal published Quire dependency.
- Never pin Propstore to a local Quire checkout.
- Push Quire changes before pinning Propstore to a Quire commit.
- Between the first Quire edit and final Propstore dependency closure, Propstore pins Quire to a pushed branch commit or immutable pushed commit SHA refreshed at the start of each Propstore phase.
- The dependency check must inspect parsed `pyproject.toml` dependencies and `[tool.uv.sources]` entries.
- A local path, workspace, or file URL dependency on Quire is a hard blocker until Quire has been pushed and Propstore is pinned to a pushed branch commit or immutable pushed commit SHA.
- The final dependency gate fails if a Quire dependency entry resolves only from the local filesystem, even when string searches miss it.

Required dependency searches:

```powershell
rg -n -F -- "quire" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
```

## Global Family Cutover Loop

Every Propstore family phase uses this loop:

1. Read the family inventory entry in `inventory-matrix.md` and the current family files.
2. List every current production caller that imports or consumes the family's projection rows, projection models, raw SQLite selectors, or generic helper layer.
3. Name the target charter/model classes in the phase notes or commit message.
4. Delete the old production projection/read-model surface first.
5. Run the smallest import/type/test command that exposes the next failures.
6. Fix only failures caused by the deletion in the current family slice and named caller list.
7. Replace raw SQLite access with Quire SQLAlchemy session/model access.
8. Replace loose dict/list/row payloads with typed model objects.
9. Delete field-specific coercers once generic charter conversion covers the field.
10. Run the family gates.
11. Run the old-path search gates for that family.
12. Run the data-parity gate for that family.
13. Commit only that family slice.
14. If files moved, run `git log --diff-filter=R -1 --stat` after commit and verify the expected renames are visible.
15. Reread this index and the active child workstream before selecting the next phase.

If a family cannot follow this loop because Quire lacks a needed generic feature, stop and return to the Quire phase that owns that feature. Do not create a Propstore workaround.

## Global Helper Deletion Predicate

- Delete a helper when its body is a table-shaped `SELECT`, `COUNT`, `INSERT`, `DELETE`, row attachment, row coercion, or projection-model wrapper with no Propstore semantic policy.
- Keep and move semantic code when it owns concept-id precedence, alias resolution, source-local lowering, quarantine/blocked policy, form/unit validation, visibility/render policy, context/lifting semantics, argumentation semantics, revision semantics, or authored-document identity.
- After moving kept semantics, delete the original helper-shaped production path.

## Global Parity Rules

Every Propstore family phase has this data-parity obligation:

- The parity harness is `scripts/compare_sqlalchemy_charter_parity.py`.
- Phase 4 creates the harness before Propstore family cutovers begin.
- Phase 4 is not complete until the harness exists, has a targeted test or
  fixture-run proving row-count, key-set, FTS/vector, diagnostic, and semantic
  query comparison failures are reported, and the harness command shape below
  works for at least one owner slug.
- Every Propstore phase writes its parity report under `reports/sqlalchemy-charter-parity/<phase-slug>.json`.
- Standard command shape:

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --before <old-sidecar.sqlite> --after <new-sidecar.sqlite> --owner <phase-slug> --out reports/sqlalchemy-charter-parity/<phase-slug>.json
```

- build the sidecar from the same repository snapshot before and after the current phase;
- compare row counts and primary-key/key-set coverage for every table the phase owns;
- compare representative semantic query results for the phase owner APIs;
- explicitly list accepted column/table renames in the commit message;
- fail the phase when a row, key, diagnostic, FTS hit, vector hit, or semantic query result disappears. The only accepted disappearance is a table or helper already named as a deletion target in the active workstream.

The build-orchestration cutover must additionally compare table names, primary keys, row counts, and key sets between the current mainline sidecar and the charter-generated sidecar from the same repository snapshot.

## Global Search Rules

- All child workstream search gates are zero-hit gates outside notes, workstreams, docs, and reports unless the child says the search is an inventory-only pre-deletion report.
- Before Phase 15, Quire searches for `ProjectionTable`, `ProjectionModel`, `FtsProjection`, and `VecProjection` are remaining-old-path inventory. Copy the output into the phase report and do not let Propstore cutovers import those paths.
- Phase 15 turns Quire projection searches into zero-hit gates.
- Phase 16 turns Propstore projection/helper searches into zero-hit gates.
- Remaining IO boundary constructors must use boundary-specific names such as `from_yaml_payload`, `from_json_payload`, or `from_row_mapping`; the generic `from_mapping` constructor name is deleted from core, families, world, worldline, support-revision, and tests.

Initial old-path searches:

```powershell
rg -n -F -- "ProjectionTable" propstore tests
rg -n -F -- "ProjectionModel" propstore tests
rg -n -F -- "ProjectionCodec" propstore tests
rg -n -F -- "PROPSTORE_WORLD_PROJECTION_SCHEMA" propstore tests
```

Final Quire searches:

```powershell
rg -n -F -- "ProjectionTable" quire tests
rg -n -F -- "ProjectionSchema" quire tests
rg -n -F -- "ProjectionIndex" quire tests
rg -n -F -- "ProjectionColumn" quire tests
rg -n -F -- "ProjectionSelectedColumn" quire tests
rg -n -F -- "ProjectionModel" quire tests
rg -n -F -- "ProjectionCodec" quire tests
rg -n -F -- "ScalarPath" quire tests
rg -n -F -- "ReferencePath" quire tests
rg -n -F -- "FtsProjection" quire tests
rg -n -F -- "VecProjection" quire tests
```

Final Propstore searches:

```powershell
rg -n -F -- "ProjectionTable" propstore tests
rg -n -F -- "ProjectionSchema" propstore tests
rg -n -F -- "ProjectionIndex" propstore tests
rg -n -F -- "ProjectionColumn" propstore tests
rg -n -F -- "ProjectionSelectedColumn" propstore tests
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
rg -n -F -- "CONCEPT_FTS_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_VEC_PROJECTION" propstore tests
rg -n -F -- "CONTEXT_SCHEMA" propstore tests
rg -n -F -- "PROPSTORE_WORLD_PROJECTION_SCHEMA" propstore tests
rg -n -F -- "TEXT_CODEC" propstore/families/contexts tests
rg -n -F -- "PARAMETERS_CODEC" propstore/families/contexts tests
rg -n -F -- "CONDITIONS_CODEC" propstore/families/contexts tests
rg -n -F -- "PROVENANCE_CODEC" propstore/families/contexts tests
rg -n -F -- "AUTOINCREMENT_CODEC" propstore/families/contexts tests
rg -n -F -- "_optional_float_input" propstore tests
rg -n -F -- "_optional_string" propstore tests
rg -n -F -- "_optional_int" propstore tests
rg -n -F -- "_claim_optional_float" propstore tests
rg -n -F -- "_parse_string_tuple" propstore tests
rg -n -F -- "coerce_active_micropublication" propstore tests
rg -n -- "class Active[A-Z]|\\bActive[A-Z][A-Za-z0-9_]*\\b" propstore tests
rg -n -F -- "WorldBindActiveReport" propstore tests
rg -n -F -- "ClaimSidecarRows" propstore tests
rg -n -F -- "RawIdQuarantineSidecarRows" propstore tests
rg -n -F -- "PromotionBlockedSidecarRows" propstore tests
rg -n -F -- "SidecarClaimRelationStore" propstore tests
rg -n -F -- "find_similar_claim_rows" propstore tests
rg -n -F -- "find_similar_concept_rows" propstore tests
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
```

## Full Gates

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

Final dependency search:

```powershell
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
```

## Completion Criteria

The directory workstream is complete only when:

- Quire has a SQLAlchemy-backed charter/schema engine.
- Quire derived-store handles open read-only SQLAlchemy sessions.
- Quire schema catalogs describe the derived store from the same charters that generated the mappings.
- Quire charters compose with existing `ArtifactFamily`, document-store, placement, and reference/FK APIs instead of replacing them with a parallel registry.
- Quire projection modules and projection public exports are deleted.
- Propstore supplies domain charters for every sidecar family.
- `propstore/derived_build.py` and `propstore/derived_build_plan.py` use Quire writable sessions and charter catalogs, not projection schemas or raw sidecar row plans.
- Propstore no longer imports Quire projection primitives.
- Propstore has no family `projection_model.py` files.
- Propstore has no duplicate `*Row` model layer for domain objects.
- `claim.concept_links` is the primary relationship and `ClaimConceptLink` owns role/ordinal/binding metadata.
- Micropublication claim links, aliases, parameterizations, context lifting records, stances, and conflicts are typed models or association objects.
- Source-local and canonical states are explicit charter/lifecycle states.
- Manual helper/coercer families listed in search gates are deleted.
- Remaining IO boundary constructors use boundary-specific names and do not use the generic `from_mapping` name.
- No PascalCase `Active*` production/report/model type remains.
- `WorldQuery` uses Quire sessions and typed model queries.
- Every row in `inventory-matrix.md` has been accounted for in a commit message or final closure report with delete/move/keep-as-semantic-owner outcome.
- Every family cutover has a passing data-parity gate for row counts, key sets, representative owner-layer queries, FTS, vector, and diagnostics where applicable.
- App/CLI/web surfaces continue to call owner-layer APIs.
- Quire and Propstore gates pass.
- Propstore is pinned to a pushed Quire commit, never a local checkout.
