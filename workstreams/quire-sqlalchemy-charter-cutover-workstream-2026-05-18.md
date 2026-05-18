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
- Do not leave old/new dual production paths.
- Move files when the change is actually a move. Use `git mv` for same-repo
  moves.
- For cross-repo Quire/Propstore changes, preserve move intent in commit
  messages and keep source/deletion slices paired.
- Commit every intentional edit slice atomically with path-limited git
  commands in the repository being edited.
- Push Quire changes before pinning Propstore to a Quire commit.
- Never pin Propstore to a local Quire checkout.
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
5. Source vertical slice.
6. Forms and sources cleanup closure.
7. Concept/form/parameterization slice.
8. Context/lifting slice.
9. Claim model and association-object slice.
10. Relations/stances/conflicts slice.
11. Justifications and micropublications slice.
12. Rules/grounding/diagnostics/calibration/embeddings slice.
13. WorldQuery/session/graph/reasoning cutover.
14. Delete Quire projection modules.
15. Delete Propstore projection/helper leftovers.
16. Full gates, docs, and final dependency pin.

Write or run an order checker before production implementation. The checker
must prove each dependent phase appears after its prerequisites. If it fails,
repair this file before editing code.

No Propstore production cutover starts until Phases 1-4 pass in Quire. Source
is not a place to discover whether SQLAlchemy can handle metadata fields,
association objects, FTS, sessions, schema catalogs, JSON adapters, or enum
conversion. All of that is Quire's first job.

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
```

This phase does not implement anything. It proves the starting state and the
work queue. If the inventory or notes are missing, stop and restore the
authoring context before implementation.

## Mechanical Family Cutover Loop

Every Propstore family phase must use the same loop:

1. Read the family inventory entry and current family files.
2. Name the target charter/model classes in the phase notes or commit message.
3. Delete the old production projection/read-model surface first.
4. Run the smallest import/type/test command that exposes the next failures.
5. Fix only failures caused by the deletion in the current family slice.
6. Replace raw SQLite access with Quire SQLAlchemy session/model access.
7. Replace loose dict/list/row payloads with typed model objects.
8. Delete field-specific coercers once generic charter conversion covers the
   field.
9. Run the family gates.
10. Run the old-path search gates for that family.
11. Commit only that family slice.
12. Reread this workstream before selecting the next phase.

The loop is not optional. If a family cannot follow it because Quire lacks a
needed generic feature, stop and return to the Quire phase that owns that
feature. Do not create a Propstore workaround.

## Inventory Deletion Matrix

The inventory maps the cleanup to exact owner surfaces:

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `../quire/quire/projections.py` | Quire handwritten SQLite projection primitives | Quire SQLAlchemy charter engine | Delete after all consumers move |
| `../quire/quire/projection_mapping.py` | Quire object-to-row mapper | Quire SQLAlchemy mapper/session engine | Delete after all consumers move |
| `../quire/quire/derived_store.py` | Quire derived SQLite lifecycle | Quire | Keep and adapt to SQLAlchemy sessions/catalog |
| `../quire/quire/derived_runtime.py` | Quire SQLite runtime/validation | Quire | Keep and adapt to SQLAlchemy engine/session validation |
| `propstore/families/projection_catalog.py` | Propstore manual world schema assembly | Quire schema catalog over Propstore charters | Delete; replace with Propstore world charter registration through the Quire catalog |
| `propstore/families/sources/declaration.py` projection pieces | Source sidecar projection | Source charter plus Quire SQLAlchemy | Delete projection rows/tables/helpers |
| `propstore/families/concepts/projection_model.py` | Concept row mapper | Concept charter plus Quire SQLAlchemy | Delete |
| `propstore/families/concepts/declaration.py` projection/query pieces | Concept sidecar compiler/query API | Concept semantics plus model queries | Delete generic projection/query plumbing |
| `propstore/families/claims/projection_model.py` | Claim split storage/read mapper | Claim charter plus association objects | Delete |
| `propstore/families/claims/storage.py` | Loose claim row preparation/helpers | Claim semantic lowering into typed models | Delete storage-shaped helpers |
| `propstore/core/active_claims.py` row coercion | Runtime row repair | Typed `Claim` model or explicit runtime view | Delete duplicate coercion; keep only true view behavior |
| `propstore/families/relations/projection_model.py` | Relation/stance/conflict row mapper | Typed relation/stance/conflict models | Delete |
| `propstore/families/micropublications/declaration.py` projection pieces | Micropub projection/query API | Micropub charter plus association object | Delete generic projection/query plumbing |
| `propstore/families/contexts/declaration.py` projection pieces | Context/lifting projection/query API | Context charter plus lifting semantics | Delete generic projection/query plumbing |
| `propstore/families/rules/declaration.py` projection pieces | Grounding sidecar persistence | Grounding charter plus semantic persistence | Delete generic projection table plumbing |
| `propstore/families/diagnostics/declaration.py` projection pieces | Build diagnostics projection | Diagnostic charter plus typed diagnostics | Delete projection table plumbing |
| `propstore/families/embeddings/declaration.py` projection/vector pieces | Embedding sidecar/vector cache | Quire vector cache + Propstore entity policy | Delete projection/vector duplication |

The final report must account for every row in this matrix.

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

Suggested proof models:

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
- artifact family identity;
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

Type-level markers should carry storage roles without restating SQL types:

- `PrimaryKey[T]`
- `ForeignKey[T]`
- `Json[T]`
- `Indexed[T]`
- `Unique[T]`
- `SearchText[T]`
- `Vector[T]`
- `Relation[T]`
- `Association[T]`
- `SourceLocal[T]`
- `CanonicalOnly[T]`

Do not make callers type SQL column names, SQL types, JSON suffixes, or
per-field codecs when the Python type and marker determine them.

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
- open read-only sessions from derived-store handles;
- expose a typed `DerivedSession`/query context API.

Quire should own session lifecycle. Propstore should receive sessions or
semantic facades over sessions, not raw `sqlite3.Connection` objects.

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
- use or fix `sqlalchemy-fts5` for FTS5 virtual tables;
- if the extension cannot express the existing concept/claim FTS needs, stop
  Quire work and fix `sqlalchemy-fts5` first;
- do not keep Quire `FtsProjection`;
- do not re-create FTS with raw string SQL hidden in Propstore.

Vector behavior:

- keep sqlite-vec support generic in Quire;
- express vector stores as charter/index/cache declarations;
- build Quire-owned SQLAlchemy vector support before Propstore embedding
  cutover;
- do not leave vector behavior as a blocker for Propstore to work around.

Required gates:

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

Before Phase 14, the search output is an inventory of remaining old paths, not
a passing gate. It must be copied into the phase report and no Propstore
cutover may import those old paths. Phase 14 turns these same searches into
zero-hit gates.

If this gate fails, do not start Source. Fix Quire.

## Phase 5: Source Vertical Slice

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

These exact commands must pass before Phase 6:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-charter tests/test_fixture_schema_parity.py tests/test_sidecar_projection_contract.py tests/test_required_schema_completeness.py
rg -n -F -- "SourceProjectionRow" propstore tests
rg -n -F -- "SOURCE_PROJECTION" propstore tests
rg -n -F -- "quality_json" propstore tests
rg -n -F -- "derived_from_json" propstore tests
```

The first three searches are zero-hit gates outside notes/workstreams. The
`quality_json` and `derived_from_json` searches are zero-hit gates for
production Propstore code.

## Phase 6: Forms And Source Closure

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

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label forms-charter tests/test_form_algebra.py tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py
rg -n -F -- "FORM_PROJECTION" propstore tests
rg -n -F -- "FORM_ALGEBRA_PROJECTION" propstore tests
rg -n -F -- "ProjectionTable(" propstore/families/concepts propstore/families/forms tests
```

All searches are zero-hit gates outside notes/workstreams.

## Phase 7: Concept/Form/Parameterization Slice

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

All searches are zero-hit gates outside notes/workstreams.

## Phase 8: Context And Lifting Slice

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

All searches are zero-hit gates outside notes/workstreams.

## Phase 9: Claim Model And Association Objects

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

- `claim.concepts` as a read-only property or SQLAlchemy association proxy.

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

All searches are zero-hit gates outside notes/workstreams.

## Phase 10: Relations, Stances, And Conflicts

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

All searches are zero-hit gates outside notes/workstreams.

## Phase 11: Justifications And Micropublications

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
```

All searches are zero-hit gates outside notes/workstreams.

## Phase 12: Rules, Grounding, Diagnostics, Calibration, Embeddings

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

All searches are zero-hit gates outside notes/workstreams.

## Phase 13: WorldQuery, Graph, And Reasoning Cutover

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

- `WorldQuery` opens a Quire derived-store read-only SQLAlchemy session;
- family query APIs accept a session or typed repository/world context;
- graph construction consumes typed model objects;
- resolution consumes typed claims/concepts/stances/conflicts;
- app/CLI/web surfaces see no schema-layer change except better behavior.

Required gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label world-charter tests/test_world_query.py tests/test_worldline.py tests/test_graph_export.py tests/test_worldline_ic_merge_properties.py
rg -n -F -- "sqlite3.Connection" propstore/world propstore/families tests
rg -n -F -- "row_factory" propstore/world propstore/families tests
rg -n -F -- "connect_sqlite_store" propstore/world propstore/families tests
rg -n -F -- "ProjectionRow" propstore/world propstore/families tests
```

All searches are zero-hit gates outside notes/workstreams.

## Phase 14: Delete Quire Projection Modules

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

Zero production hits are permitted. Documentation hits are limited to this
workstream and historical notes.

## Phase 15: Delete Propstore Projection And Helper Leftovers

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
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world tests
```

Zero production hits are permitted. Documentation hits are limited to notes and
workstreams. External IO boundary constructors must use boundary-specific names
such as `from_yaml_payload`, `from_json_payload`, or `from_row_mapping`; the
generic `from_mapping` constructor name is deleted from core, families, world,
and tests.

## Phase 16: Final Gates

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
```

## Completion Criteria

The workstream is complete only when:

- Quire has a SQLAlchemy-backed charter/schema engine.
- Quire derived-store handles open read-only SQLAlchemy sessions.
- Quire schema catalogs describe the derived store from the same charters that
  generated the mappings.
- Quire projection modules and projection public exports are deleted.
- Propstore supplies domain charters for every sidecar family.
- Propstore no longer imports Quire projection primitives.
- Propstore has no family `projection_model.py` files.
- Propstore has no duplicate `*Row` model layer for domain objects.
- `claim.concept_links` is the primary relationship and
  `ClaimConceptLink` owns role/ordinal/binding metadata.
- Micropublication claim links, aliases, parameterizations, context lifting
  records, stances, and conflicts are typed models or association objects.
- Source-local and canonical states are explicit charter/lifecycle states.
- Manual helper/coercer families listed in the search gates are deleted or
  confined to reviewed IO boundaries.
- `WorldQuery` uses Quire sessions and typed model queries.
- App/CLI/web surfaces continue to call owner-layer APIs.
- Quire and Propstore gates pass.
- Propstore is pinned to a pushed Quire commit, never a local checkout.
