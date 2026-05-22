# Propstore Core Deletion Audit - 2026-05-21

Status: in progress. Scope is every tracked Python file under `propstore/core`.

## Decision Rule

Content is kept only when all are true:

- it is in the correct owner layer;
- it does not duplicate field, schema, identity, enum parsing, family lookup,
  storage-root, or reference mechanics that should come from Quire charters,
  field metadata, or family APIs;
- it does not preserve an old path through wrappers, aliases, adapters,
  fallbacks, compatibility branches, or re-export modules;
- it does not accept loose `dict`, `object`, mixed string payloads, or
  source-local handles past the IO boundary;
- its public API is typed at the semantic boundary;
- literal search does not reveal an equivalent implementation that should own
  the behavior instead.

If any condition fails, the action is delete, move, consolidate, or rewrite.

## Commit Rule

Every commit for this audit must repeat the governing principle block in the
commit message body:

- no old production surface survives through wrappers, aliases, adapters,
  fallbacks, compatibility branches, re-export modules, or renamed helpers;
- field/schema/storage/reference mechanics come from Quire charters, field
  metadata, and family APIs, not duplicated Propstore code;
- Propstore keeps semantic behavior in the correct owner layer;
- runtime APIs receive typed/domain objects, not loose `dict`, `object`, mixed
  strings, or source-local handles past the IO boundary;
- if the content fails those checks, it is deleted, moved, consolidated, or
  rewritten.

## SQLAlchemy Gate Audit Backfill

Recorded 2026-05-21 from the literal gate reports under
`workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/gate-audits/`.

This backfill tightens the core checklist. A checked read entry below does not
mean the file is acceptable as-is. If this section names a core surface, that
surface remains an active delete/move/rewrite target until its search gate is
zero-hit or its exact owner-boundary parser is named and recorded.

- `propstore/core/justifications.py`
  - New gate evidence:
    `rg -n -F -- "CanonicalJustification(" propstore tests` still has
    production/test hits, including this core file.
  - Required final state: delete the duplicate `CanonicalJustification`
    payload class/constructor path from core. Move the generated-family model
    behavior to the justification family owner and active-graph projection to
    the world/argumentation owner. No `propstore.core.justifications` re-export
    or replacement payload DTO remains.

- `propstore/core/assertions/conversion.py` and
  `propstore/core/assertions/__init__.py`
  - New gate evidence: `_from_payload` still has core production hits in the
    wave 1-E audit.
  - Required final state: no broad `_from_payload` runtime constructor remains
    in core. If source assertion parsing is real IO, place it as an explicit
    assertion/source boundary parser with hard failures and import it from the
    concrete module, not through the package initializer.

- `propstore/core/assertions/codec.py`
  - New gate effect: the canonical assertion parser may remain only as the
    canonical assertion IO boundary. It must not be used as proof that broad
    `_from_payload` or loose payload constructors are allowed elsewhere in
    core.

- `propstore/core/claim_values.py`
  - New gate effect: the helper inventory backfill treats broad payload and
    JSON repair constructors as illegal outside exact IO owners. This keeps the
    existing action strict: move claim-owned nested value objects to the claim
    owner, source-owned nested value objects to the source owner, and delete
    loose JSON/string fallback parsing from core.

- Core-wide compatibility/classification gates
  - New gate evidence: broad `legacy`, `backward compat`, `backwards compat`,
    `compat shim`, `fallback`, and `coerce_*` searches still have production
    hits outside and inside core-adjacent surfaces.
  - Required final state: each core hit is either deleted or recorded as a
    named semantic/IO owner boundary. There is no generic permission for
    compatibility wording, fallback parsing, or `coerce_*` helpers in core.

## File Checklist

- [x] `propstore/core/__init__.py`
  - Read: 2026-05-21.
  - Action: keep shallow package initializer.
  - Reason: empty `__all__` and no eager re-exports; it does not preserve old
    paths or pull runtime owners into `core`.

- [x] `propstore/core/activation.py`
  - Read: 2026-05-21.
  - Action: delete `propstore.core.activation` and create
    `propstore.world.activation`.
  - Reason: activation over compiled world graphs is world runtime
    orchestration over `WorldActivationGraph`, `Environment`, condition solvers,
    and context lifting. It is not a core semantic primitive.
  - Required follow-up: move `UnknownConceptInCEL`, `is_claim_active`,
    `claim_lifting_materializations`, and `activate_compiled_world_graph` to
    `propstore.world.activation`; update callers in `propstore.world.*` and
    tests; leave no `propstore.core.activation` module or re-export.

- [x] `propstore/core/algorithm_stage.py`
  - Read: 2026-05-21.
  - Action: keep `AlgorithmStage`; delete helper functions.
  - Delete: `to_algorithm_stage` and `coerce_algorithm_stage`.
  - Reason: both functions are helper-shaped wrappers around the `NewType`.
    `coerce_algorithm_stage` accepts `object` and reconstructs semantic meaning
    locally instead of requiring the boundary to pass `AlgorithmStage | None`.
  - Required follow-up: update all callers to construct `AlgorithmStage(value)`
    at IO/document/app boundaries and pass typed values through runtime APIs.

- [x] `propstore/core/aliases.py`
  - Read: 2026-05-21.
  - Action: delete `propstore.core.aliases` and create
    `propstore.app.concepts.aliases`.
  - Reason: the module opens repository family handles and exports a concept
    alias report. That is repository/app/family presentation behavior, not a
    core semantic primitive. It imports `Repository`,
    `parse_concept_record_document`, and identity helper code, so keeping it in
    `core` violates owner layering.
  - Required follow-up: move `AliasExportEntry` and `export_concept_aliases` to
    `propstore.app.concepts.aliases`; update `propstore.app.compiler` to import
    that owner; leave no `propstore.core.aliases` module or re-export.

- [x] `propstore/core/analyzers.py`
  - Read: 2026-05-21.
  - Action: delete from `core`; move real analyzer orchestration to the
    world/argumentation owner.
  - Reason: it builds active-world analyzer inputs, converts family records to
    graph rows, constructs Dung/bipolar/PrAF frameworks, runs claim-graph and
    PrAF analysis, wraps ASPIC backend solving, and projects analyzer results.
    That is world/argumentation runtime orchestration, not core primitive
    ownership.
  - Delete: `propstore/core/analyzers.py` as an import path.
  - Required follow-up: create the target owner only as
    `propstore/world/analyzers.py` or another explicitly chosen
    world/argumentation owner, update every caller, and leave no
    `propstore.core.analyzers` shim, alias, or package re-export.
  - Additional cleanup: remove helper-shaped local coercion inside the moved
    code, including `coerce_graph_relation_type("rebuts")` and broad
    query-claim-id normalization that accepts multiple loose collection shapes
    past the owner boundary.

- [x] `propstore/core/anytime.py`
  - Read: 2026-05-21.
  - Action: keep as a narrow core result sentinel.
  - Reason: `EnumerationExceeded` is typed, small, and does not duplicate field
    metadata, storage mechanics, family lookup, compatibility handling, or old
    import paths. It is a cross-cutting computation sentinel, not an IO parser
    or owner-specific workflow.

- [x] `propstore/core/assertions/__init__.py`
  - Read: 2026-05-21.
  - Action: delete eager re-exports from the package initializer.
  - Reason: it eagerly re-exports assertion codec, conversion, refs, and
    situated types. Low-level package `__init__.py` files are required to stay
    shallow.
  - Required follow-up: update all callers of
    `from propstore.core.assertions import ...` to import from concrete
    assertion modules. Leave `propstore/core/assertions/__init__.py` with
    package documentation only.

- [x] `propstore/core/assertions/codec.py`
  - Read: 2026-05-21.
  - Action: keep canonical assertion boundary, but consolidate duplicate
    assertion payload parsing with `conversion.py`.
  - Reason: `from_payload` is an IO/serialization boundary and hard-rejects old
    claim-shaped payloads instead of rewriting them. That part follows the
    rule. The file duplicates `_required`, `_text`, role-binding parsing,
    condition-ref parsing, and provenance-ref parsing with
    `assertions/conversion.py`.
  - Required follow-up: factor only the shared assertion payload readers into a
    narrow assertion-owned private parser module or shared private functions.
    Do not create a broad `coerce_*`/`normalize_*` helper and do not accept old
    shapes.

- [x] `propstore/core/assertions/conversion.py`
  - Read: 2026-05-21.
  - Action: keep source assertion boundary, but consolidate duplicated parser
    code with `codec.py`.
  - Reason: decoded source mappings are accepted only at the boundary and are
    immediately converted into assertion/relation domain objects. Hard failure
    for old claim-shaped payloads is correct. The duplicate private payload
    readers should be written once inside the assertion boundary.
  - Required follow-up: when consolidating, preserve the distinct canonical
    shape and source shape. The shared code may parse common typed parts only;
    it must not become an old/new shape adapter.

- [x] `propstore/core/assertions/refs.py`
  - Read: 2026-05-21.
  - Action: keep reference value objects; rewrite loose source hashing input.
  - Reason: `ContextReference`, `ConditionRef`, and `ProvenanceGraphRef` are
    core assertion identity/reference objects. They validate typed identifiers
    and do not duplicate Quire storage mechanics. The exception is
    `ConditionRef.from_sources`, which accepts `Sequence[object]` and
    stringifies arbitrary values to build identity.
  - Required follow-up: change `ConditionRef.from_sources` to accept the exact
    typed condition-source representation used by the condition owner, not
    arbitrary `object`; update callers from the resulting type errors.

- [x] `propstore/core/assertions/situated.py`
  - Read: 2026-05-21.
  - Action: keep as core assertion identity.
  - Reason: it composes typed assertion reference/domain objects and derives
    deterministic assertion IDs from the identity payload. It does not parse IO
    payloads, preserve compatibility paths, or duplicate family metadata.

- [x] `propstore/core/base_rates.py`
  - Read: 2026-05-21.
  - Action: split into exact owners and delete the core module.
  - Reason: `BaseRateProfile`, `BaseRateResolver`, and
    `construct_assertion_opinion` operate on typed assertion IDs and opinion
    domain objects. `BaseRateAssertionRecord.from_parameter_claim` accepts a
    loose `Mapping[str, object]` and hardcodes claim payload fields
    (`type`, `id`, `concept`, `value`, `unit`) inside `core`.
  - Required follow-up: move `BaseRateProfile`, `BaseRateResolved`,
    `BaseRateUnresolved`, `AssertionOpinion`, `BaseRateResolver`, and
    `construct_assertion_opinion` to `propstore.heuristic.base_rates`.
  - Required deletion: delete `BaseRateAssertionRecord.from_parameter_claim`.
    Base-rate extraction from parameter claims must be implemented at the
    claim/source document boundary with typed claim objects, not loose
    mappings.
  - Required final state: no `propstore.core.base_rates` module, no core
    re-export, and no `BaseRateAssertionRecord` loose mapping parser.

- [x] `propstore/core/claim_types.py`
  - Read: 2026-05-21.
  - Action: move claim-family vocabulary to the claim owner and delete the
    helper.
  - Delete: `coerce_claim_type`.
  - Reason: `ClaimType` is claim-family semantic vocabulary, not generic core
    infrastructure. The coercer accepts `object | None` and stringifies meaning
    locally. `VALID_CLAIM_TYPES` duplicates the enum-derived vocabulary and
    should only remain if a caller truly needs a derived constant in the claim
    owner.
  - Required follow-up: move `ClaimType` and the derived valid-value set to
    `propstore.families.claims.documents`; delete `coerce_claim_type`; update
    callers to construct `ClaimType(value)` at IO/document boundaries and pass
    typed values through runtime APIs.
  - Execution note, 2026-05-22: completed in commit `429ea38e`. The owner
    landed as `propstore.families.claims.types` so claim documents, source
    documents, claim declaration models, world/query code, and tests import the
    claim-family vocabulary directly without a top-level facade or core
    re-export. `coerce_claim_type` was deleted. Gates:
    `rg -n -F -- "propstore.core.claim_types" propstore tests` zero-hit,
    `rg -n -F -- "coerce_claim_type" propstore tests` zero-hit,
    `uv run pyright propstore` passed, and logged pytest
    `claim-type-owner-cleanup-20260522-012340.log` passed with `36 passed`.

- [x] `propstore/core/claim_values.py`
  - Read: 2026-05-21.
  - Action: move out of `core` and rewrite boundary parsing.
  - Reason: the module is claim/source nested row payload handling, not a core
    primitive. It accepts loose `object`, `Mapping[str, Any]`, JSON strings, and
    sequences; it silently returns `None` or empty tuples for malformed JSON in
    several places; and it calls source coercers inside dataclass
    `__post_init__`/payload constructors.
  - Delete/rewrite: `_parse_mapping_json`, `_parse_list_json`,
    `_opinion_from_json_payload`, `SourceOrigin.from_json_payload`,
    `SourceTrust.from_json_payload`, `ClaimSource.from_json_payload`, and
    `ClaimProvenance.from_components` cannot remain as loose core parsing.
  - Required follow-up: move claim-owned nested value objects to
    `propstore.families.claims.documents` and source-owned nested value objects
    to `propstore.families.sources.declaration`. Parse decoded JSON/YAML/SQLite
    values at the IO boundary with an exact schema and hard failures; do not
    preserve fallback-to-empty behavior.
  - Execution note, 2026-05-22: completed in commit `4b2f4353`.
    `propstore.core.claim_values` was deleted. The only production-used
    surface, `ClaimProvenance`, moved to the world resolution boundary with
    hard-failure provenance JSON parsing. Source trust/origin duplicate test
    coverage was removed because source-family documents and
    `compile_source_models` already own that path. Gates:
    `rg -n -F -- "propstore.core.claim_values" propstore tests` zero-hit,
    `rg -n -F -- "SourceTrust.from_json_payload" propstore tests` zero-hit,
    `uv run pyright propstore` passed, and logged pytest
    `claim-values-core-deletion-20260522-012829.log` passed with `25 passed`.

- [x] `propstore/core/concept_relationship_types.py`
  - Read: 2026-05-21.
  - Action: move concept-relationship vocabulary to the concept owner and delete
    the helper.
  - Delete: `coerce_concept_relationship_type`.
  - Reason: this is concept-family semantic vocabulary, not generic core
    infrastructure. The coercer accepts `object | None` and stringifies locally.
  - Required follow-up: delete the coercer first, move/consolidate
    `ConceptRelationshipType` under the concept/family owner, and update callers
    to use the enum constructor at IO/document boundaries only.
  - Execution note, 2026-05-22: completed in commit `4615997e`.
    `ConceptRelationshipType` and `VALID_CONCEPT_RELATIONSHIP_TYPES` moved to
    `propstore.families.concepts.types`, `coerce_concept_relationship_type` was
    deleted, and concept parsing now constructs `ConceptRelationshipType`
    directly at the concept boundary. Gates:
    `rg -n -F -- "propstore.core.concept_relationship_types" propstore tests`
    zero-hit,
    `rg -n -F -- "coerce_concept_relationship_type" propstore tests`
    zero-hit, `uv run pyright propstore` passed, and logged pytest
    `concept-relationship-owner-cleanup-20260522-013322.log` passed with
    `32 passed`.

- [x] `propstore/core/concept_status.py`
  - Read: 2026-05-21.
  - Action: move concept-family vocabulary to the concept owner and delete the
    helper.
  - Delete: `coerce_concept_status`.
  - Reason: concept status is concept-family semantic vocabulary, not generic
    core infrastructure. The helper accepts mixed enum/string input and hides
    boundary parsing inside runtime code.
  - Required follow-up: delete `coerce_concept_status` first, move/consolidate
    `ConceptStatus` under the concept/family owner, and update callers to use
    `ConceptStatus(value)` at IO/document boundaries only.
  - Execution note, 2026-05-22: completed in commit `29921f7f`.
    `ConceptStatus` and `VALID_CONCEPT_STATUSES` moved to
    `propstore.families.concepts.types`, `coerce_concept_status` was deleted,
    and concept record parsing now constructs `ConceptStatus` directly at the
    concept boundary. Gates:
    `rg -n -F -- "propstore.core.concept_status" propstore tests` zero-hit,
    `rg -n -F -- "coerce_concept_status" propstore tests` zero-hit,
    `uv run pyright propstore` passed, and logged pytest
    `concept-status-owner-cleanup-20260522-013559.log` passed with
    `65 passed`.

- [x] `propstore/core/conditions/__init__.py`
  - Read: 2026-05-21.
  - Action: delete eager low-level package re-export surface.
  - Reason: this initializer imports checked models, codecs, ESTree backend,
    IR, Python backend, SQL backend, solver, and Z3 backend. That violates the
    shallow package initializer rule and can pull unrelated backends into
    callers that only need one surface.
  - Required follow-up: update all `propstore.core.conditions import` callers
    to concrete-module imports. Leave `propstore/core/conditions/__init__.py`
    with package documentation only.

- [x] `propstore/core/conditions/cel_frontend.py`
  - Read: 2026-05-21.
  - Action: keep in condition owner, with type-boundary tightening.
  - Reason: this is the real CEL frontend lowering/type-checking owner for
    `ConditionIR`. It uses typed registry entries, hard-fails unsupported CEL
    nodes, and does not preserve old shapes. The remaining tightening is to
    ensure public entrypoints use the declared CEL/domain source type
    consistently rather than plain strings where the type system can carry
    `CelExpr`.
  - Required follow-up: change `condition_ir_from_cel` and
    `check_condition_ir` to accept `CelExpr`; update callers to pass `CelExpr`
    through this boundary instead of stringifying it.

- [x] `propstore/core/conditions/checked.py`
  - Read: 2026-05-21.
  - Action: keep in condition owner, with CEL source type tightening.
  - Reason: `CheckedCondition` and `CheckedConditionSet` are typed runtime
    carriers for checked condition semantics. JSON decode/encode functions are
    explicit versioned IO boundaries and hard-fail malformed payloads.
    `_normalize_checked_conditions` operates on typed `CheckedCondition`
    objects, so it is canonicalization rather than mixed-shape coercion.
  - Required follow-up: change `CheckedCondition.source` and `.sources` to carry
    `CelExpr` instead of bare `str`; keep text decoding in the versioned JSON
    boundary.

- [x] `propstore/core/conditions/codec.py`
  - Read: 2026-05-21.
  - Action: keep as condition-owned versioned JSON codec.
  - Reason: it serializes/deserializes the closed `ConditionIR` tree at an IO
    boundary, uses explicit version tags, enum constructors, and hard failures.
    It does not preserve old shapes or define broad compatibility fallbacks.
  - Required follow-up: keep as the only condition JSON codec.

- [x] `propstore/core/conditions/estree_backend.py`
  - Read: 2026-05-21.
  - Action: keep backend, but replace loose evaluation value typing with an
    explicit scalar/value alias.
  - Reason: the translation from `ConditionIR` to ESTree is owner-correct. The
    evaluator currently exposes `EstreeLiteral.value: object`,
    `bindings: Mapping[str, object]`, and returns `object`; that is a loose
    runtime boundary where the condition value type should be explicit.
  - Required follow-up: define a narrow condition evaluation value type and use
    it for ESTree literals, bindings, member evaluation, and numeric helpers.

- [x] `propstore/core/conditions/ir.py`
  - Read: 2026-05-21.
  - Action: keep closed condition IR; tighten runtime constructors to typed
    values.
  - Reason: the file defines the actual closed `ConditionIR` domain model and
    enum vocabulary for condition expressions. It does not preserve old paths.
    The tightening target is `ConditionReference.concept_id:
    ConceptId | str` and enum normalization in runtime dataclass
    `__post_init__` methods.
  - Required follow-up: make the IR runtime model require `ConceptId`,
    `ConditionValueKind`, and operator enum instances after boundary decoding;
    keep enum construction in `codec.py`/`cel_frontend.py`.

- [x] `propstore/core/conditions/python_backend.py`
  - Read: 2026-05-21.
  - Action: keep Python AST translation backend; delete duplicated production
    evaluator semantics after the shared condition value evaluator exists.
  - Reason: the backend translates closed `ConditionIR` to Python AST and
    evaluates a controlled expression. The public evaluator accepts
    `Mapping[str, object]` and returns `object`, duplicating the loose-value
    problem also present in the ESTree backend.
  - Required follow-up: introduce the same condition evaluation value type used
    by the ESTree backend. Consolidate production evaluation through one shared
    condition evaluator and keep backend-specific translation functions only.

- [x] `propstore/core/conditions/registry.py`
  - Read: 2026-05-21.
  - Action: rewrite as a typed projection from concept/family metadata, not a
    hand-maintained duplicate model.
  - Reason: `ConceptInfo` duplicates concept identity/name/kind/category fields
    in a mutable dataclass. `scope_condition_registry` accepts mixed string
    collection shapes. `synthetic_category_concept` silently filters non-string
    values. This must be a typed condition-registry projection derived from the
    concept owner/family metadata, with hard failures for invalid values.
  - Required follow-up: use `ConceptId`, immutable category tuples, and a typed
    iterable of concept IDs. Model standard synthetic bindings as explicit
    non-concept condition bindings, not fake concept metadata.

- [x] `propstore/core/conditions/solver.py`
  - Read: 2026-05-21.
  - Action: keep condition solver; tighten binding/model value types and align
    with registry rewrite.
  - Reason: this is the owner for semantic condition satisfiability,
    disjointness, equivalence, and implication over checked `ConditionIR`. The
    dynamic `z3` return objects justify localized `Any` around the solver
    backend, but public bindings currently use `Mapping[str, Any]` and internal
    caches use untyped `Any`.
  - Required follow-up: introduce the shared condition evaluation/binding value
    type and use it at public solver boundaries. After `ConceptInfo` becomes an
    immutable metadata-derived projection, remove the defensive mutable
    `replace(... category_values=list(...))` copy.

- [x] `propstore/core/conditions/sql_backend.py`
  - Read: 2026-05-21.
  - Action: keep condition SQL projection; tighten parameter value type.
  - Reason: it projects closed `ConditionIR` into parameterized SQL fragments
    and does not inline literal values. The loose part is
    `SqlConditionFragment.parameters: tuple[object, ...]`; this should use the
    same explicit condition scalar/value type as the evaluators.
  - Required follow-up: replace `object` parameters with the condition value
    alias and ensure SQL callers get identifiers from the condition owner, not
    duplicated storage metadata.

- [x] `propstore/core/conditions/z3_backend.py`
  - Read: 2026-05-21.
  - Action: keep Z3 projection backend; tighten binding/category value types
    and registry projection types.
  - Reason: localized `Any` is acceptable for `z3` AST terms because the
    upstream library is dynamically typed. It is not acceptable for domain
    binding values. `binding_constraint`, `reference_binding_constraints`,
    `_binding_constraint_for_kind`, and `z3_bindings_for_values` accept
    `object` values, and `_get_enum` accepts `tuple[str, ...] | list[str]`.
  - Required follow-up: use the shared condition value type for bindings and
    immutable category tuples from the typed registry projection.

- [x] `propstore/core/embeddings.py`
  - Read: 2026-05-21.
  - Action: move out of `core` to the embedding/heuristic/family owner.
  - Reason: the module imports claim and concept family models and prepares
    sidecar embedding text. That is embedding pipeline behavior over family
    objects, not a core semantic primitive.
  - Required follow-up: find callers, delete `propstore.core.embeddings` first,
    move the real text-preparation functions to the embedding owner, and update
    callers. No core re-export.

- [x] `propstore/core/environment.py`
  - Read: 2026-05-21.
  - Action: move world store protocols and environment runtime state out of
    `core`; rewrite loose IO parsing.
  - Reason: the file imports claim/concept/relation/micropublication family
    models and defines `WorldStore` plus many world/catalog/query protocols.
    That is world runtime and repository interface ownership, not core. The
    `Environment.from_dict` boundary accepts `object`/mapping payloads and
    silently ignores malformed assumption entries that are neither
    `AssumptionRef` nor mappings.
  - Required follow-up: move `Environment` to `propstore.world.environment`.
    Move `WorldStore` and related store protocols to `propstore.world.store`.
    Delete `propstore.core.environment`.
  - Required deletion: delete `Environment.from_dict` from runtime state. Add an
    exact IO decoder under the world/API boundary that hard-fails malformed
    assumptions.

- [x] `propstore/core/exactness_types.py`
  - Read: 2026-05-21.
  - Action: move parameterization exactness vocabulary to the concept-family
    parameterization owner and delete the helper.
  - Delete: `coerce_exactness`.
  - Reason: exactness is parameterization/concept-family semantics, not generic
    core infrastructure. The helper accepts `object | None` and stringifies
    locally.
  - Required follow-up: move `Exactness` to
    `propstore.families.concepts.documents`; update concept/parameterization
    callers to import that owner; construct the enum at IO/document boundaries
    only; leave no `propstore.core.exactness_types` module.

- [x] `propstore/core/graph_build.py`
  - Read: 2026-05-21.
  - Action: delete `propstore.core.graph_build` and create
    `propstore.world.graph_build`.
  - Reason: it builds compiled world graphs from world/repository stores,
    imports family models, parses JSON sidecar fields, performs provenance
    payload decoding, deduplicates parameterization rows in Python when store
    querying should own that, and calls graph relation coercers. This is world
    graph orchestration, not core primitive code.
  - Required follow-up: delete the core import path first, move real graph build
    behavior to `propstore.world.graph_build`, and have stores/family APIs
    supply typed rows/projections instead of parsing JSON strings and loose
    mappings in graph build code.

- [x] `propstore/core/graph_relation_types.py`
  - Read: 2026-05-21.
  - Action: consolidate graph relation vocabulary with the real relation owners
    and delete the helper.
  - Delete: `coerce_graph_relation_type`.
  - Reason: `GraphRelationType` combines concept relationship types and stance
    relation types into another enum surface. That duplicates vocabulary that
    already belongs to concept relationships and stances/relations. The helper
    accepts mixed enum/string input and locally reconstructs meaning.
  - Required follow-up: replace duplicated graph relation enum use with typed
    relation-owner values or a derived graph-edge relation projection generated
    from those owners. Delete the coercer first and update callers from the
    failures.

- [x] `propstore/core/graph_types.py`
  - Read: 2026-05-21.
  - Action: delete `propstore.core.graph_types`, create
    `propstore.world.graph`, and keep claim-specific projection in
    `propstore.families.claims.graph`.
  - Reason: `ConceptNode`, `ClaimNode`, `RelationEdge`, `ParameterizationEdge`,
    `ConflictWitness`, and `WorldActivationGraph` hand-type many fields already
    owned by claim/concept/relation/parameterization families or world runtime
    state. The module imports enum coercers, accepts loose `Mapping[str, Any]`
    payloads, parses embedded JSON, normalizes arbitrary attribute pairs, and
    has `from_dict`/`to_dict` schema definitions separate from the charters.
  - Required follow-up: move `CompiledWorldGraph`, `WorldActivationGraph`,
    `GraphDelta`, `RelationEdge`, `ParameterizationEdge`, `ConflictWitness`,
    and `ProvenanceRecord` to `propstore.world.graph`. Keep `ClaimNode` creation
    in `propstore.families.claims.graph`; create
    `propstore.families.concepts.graph` for concept graph projections and
    `propstore.families.relations.graph` for relation graph projections.
  - Required deletion: delete `_normalize_pairs`, `_require_claim_type`,
    `ProvenanceRecord.from_json_payload`, graph `from_dict` runtime parsers,
    and dataclass `__post_init__` coercion of claim/exactness/relation types.
    Runtime graph code must receive typed values; IO decoding belongs in a
    versioned graph artifact boundary.

- [x] `propstore/core/id_types.py`
  - Read: 2026-05-21.
  - Action: move `LogicalId` to the identity family owner; keep semantic ID
    aliases as the current typed surface.
  - Reason: `NewType` aliases are the current mechanism carrying semantic IDs
    through the type system. They do not parse old shapes. `LogicalId`, however,
    is identity-family behavior and payload shape, not generic core code.
  - Required follow-up: move `LogicalId` to
    `propstore.families.identity.logical_ids`. Replace direct string/NewType
    plumbing with Quire family reference/FK APIs as those APIs become available.

- [x] `propstore/core/justifications.py`
  - Read: 2026-05-21.
  - Action: delete `propstore.core.justifications`, move generated-family model
    methods to the justification family owner, and move active-graph projection
    to the world argumentation owner.
  - Reason: `Justification` is a `FamilyModel` subclass with semantic methods,
    which is the right pattern for attaching behavior to generated fields, but
    it is in the wrong owner package. `CanonicalJustification` duplicates a
    justification/argument record shape, parses loose mappings in `from_dict`,
    parses JSON fields, imports graph provenance, and
    `claim_justifications_from_active_graph` is active-world argumentation
    orchestration.
  - Required follow-up: move `Justification` to
    `propstore.families.justifications.declaration`; move
    `claim_justifications_from_active_graph` to
    `propstore.world.argumentation`; delete `CanonicalJustification.from_dict`
    and duplicated payload schema from runtime constructors; leave no core
    re-export.

- [x] `propstore/core/labels.py`
  - Read: 2026-05-21.
  - Action: keep ATMS/provenance label algebra in `core`; move CEL binding
    construction and loose environment compilation to the world condition owner.
  - Reason: `EnvironmentKey`, `NogoodSet`, `Label`, and polynomial conversion
    are core belief-space kernel behavior. But `binding_condition_to_cel`,
    `cel_to_binding`, and `compile_environment_assumptions` accept loose
    `Any`/string values, render CEL by string interpolation, and parse CEL back
    with string splitting. That is boundary/world condition handling, not core
    label algebra.
  - Required follow-up: move `binding_condition_to_cel`, `cel_to_binding`, and
    `compile_environment_assumptions` to `propstore.world.conditions`; replace
    string interpolation and string splitting with typed condition construction;
    keep `EnvironmentKey`, `NogoodSet`, `Label`, and polynomial conversion in
    `core`.

- [x] `propstore/core/lemon/__init__.py`
  - Read: 2026-05-21.
  - Action: delete eager broad re-export surface.
  - Reason: it imports and re-exports every Lemon submodule surface. That is a
    low-level package initializer doing broad eager imports. It is not an old
    compatibility shim by itself, but it violates the shallow initializer rule.
  - Required follow-up: update callers to concrete Lemon module imports. Leave
    `propstore/core/lemon/__init__.py` with package documentation only.

- [x] `propstore/core/lemon/description_kinds.py`
  - Read: 2026-05-21.
  - Action: keep Lemon domain structs; replace raw IDs with typed owner IDs.
  - Reason: `DescriptionKind`, slots, bindings, merge arguments, and causal
    assertions are semantic Lemon domain objects, not storage/family mechanics
    or compatibility wrappers. They use `DocumentStruct` for structured fields
    and validate slot bindings.
  - Required follow-up: replace bare `str` IDs such as `claim_id`,
    `description_claim_ids`, and causal description IDs with typed owner IDs.

- [x] `propstore/core/lemon/forms.py`
  - Read: 2026-05-21.
  - Action: keep as Lemon lexical form value object.
  - Reason: `LexicalForm` is a narrow domain object with field-local validation.
    `require_text` and `fold_text` are local lexical text utilities, not old
    path adapters or broad semantic coercers.
  - Required follow-up: keep `require_text` and `fold_text` as the Lemon lexical
    text utilities.

- [x] `propstore/core/lemon/proto_roles.py`
  - Read: 2026-05-21.
  - Action: keep ProtoRole domain model; tighten entailment property typing.
  - Reason: the file encodes Dowty-style proto-role domain semantics and does
    not duplicate storage/family mechanics. `GradedEntailment.property` is a
    bare `str` that is checked against enum classes in `ProtoRoleBundle` but not
    stored as the enum type.
  - Required follow-up: split `GradedEntailment` into proto-agent and
    proto-patient entailment records so the property enum type carries the
    vocabulary.

- [x] `propstore/core/lemon/qualia.py`
  - Read: 2026-05-21.
  - Action: keep Qualia domain model; rename `coerce_via_qualia`.
  - Reason: the function named `coerce_via_qualia` is not a type coercion helper;
    it implements a Pustejovsky qualia-mediated semantic operation and returns a
    `CoercedReference` domain object. It must not become an excuse for broad
    `coerce_*` helper allowance.
  - Required follow-up: rename `coerce_via_qualia` to
    `qualia_mediated_reference` and update callers.

- [x] `propstore/core/lemon/references.py`
  - Read: 2026-05-21.
  - Action: keep as Lemon ontology reference value object.
  - Reason: `OntologyReference` is narrow, typed, and validates required text.
    It does not parse loose payloads, preserve old shapes, duplicate family
    metadata, or perform compatibility bridging.
  - Required follow-up: none from deletion rules.

- [x] `propstore/core/lemon/temporal.py`
  - Read: 2026-05-21.
  - Action: keep Allen/Lemon temporal semantics; rewrite fake condition-registry
    construction and raw IDs.
  - Reason: Allen relations over description temporal anchors are real Lemon
    semantics. The implementation builds synthetic `ConceptInfo` records with
    fake `ps:concept:*` IDs solely to run the condition solver, and
    `DescriptionTemporalAnchor.claim_id` is a bare string.
  - Required follow-up: replace the fake concept registry and condition solver
    call with typed interval relation math. Use typed claim/description IDs
    instead of raw strings.

- [x] `propstore/core/lemon/types.py`
  - Read: 2026-05-21.
  - Action: keep Lemon lexical entry/sense domain model; make role bundle keys a
    typed open lexical-role value.
  - Reason: this file is semantic Lemon modeling, not storage plumbing or
    compatibility code. The main loose point is
    `role_bundles: Mapping[str, ProtoRoleBundle] | None`, where arbitrary
    string role names are validated only as non-empty text.
  - Required follow-up: define `LexicalRoleName = NewType(\"LexicalRoleName\",
    str)` or an equivalent value object and use it for `role_bundles` keys.

- [x] `propstore/core/literal_keys.py`
  - Read: 2026-05-21.
  - Action: delete `ClaimLiteralKey`; keep `IstLiteralKey` and
    `GroundLiteralKey`.
  - Reason: the file defines typed literal identity keys grounded in the ASPIC
    literature. `IstLiteralKey` carries `ContextId` and `ClaimId`, but
    `ClaimLiteralKey.claim_id` and `claim_key(claim_id: str, context_id:
    ContextId | str)` allow raw strings at the semantic boundary.
  - Required follow-up: delete `ClaimLiteralKey` from `LiteralKey` and
    `__all__`; update tests and callers to use `IstLiteralKey`; change
    `claim_key` to accept `ClaimId` and `ContextId` after boundary parsing.

- [x] `propstore/core/reasoning.py`
  - Read: 2026-05-21.
  - Action: move to world/argumentation owner and delete normalizer/alias
    compatibility surface.
  - Delete/rewrite: `normalize_reasoning_backend`,
    `normalize_argumentation_semantics`, and string alias handling such as
    `bipolar_stable`.
  - Reason: backend/semantics selection is argumentation/world runtime policy,
    not generic core. The normalize functions accept string inputs past the
    boundary, and the alias table preserves alternate spellings instead of
    requiring the enum value at the boundary. CLI value lists belong at the CLI
    presentation boundary.
  - Required follow-up: delete the core import path first, move typed enums and
    compatibility-free validation to the world/argumentation owner, and update
    CLI/app callers to parse strings at their boundary with enum constructors.

- [x] `propstore/core/relation_types.py`
  - Read: 2026-05-21.
  - Action: move/consolidate with relation and argumentation owners.
  - Reason: the file classifies attack/support relation semantics using
    `GraphRelationType`, which this audit already marks as duplicated graph
    vocabulary. These sets are argumentation relation semantics, not generic
    core constants.
  - Required follow-up: derive attack/support classification from the relation
    owner or stance vocabulary once, then update claim-graph/PrAF/ASPIC callers.

- [x] `propstore/core/relations.py`
  - Read: 2026-05-21.
  - Action: move relation concept kernel to the relation semantic owner; delete
    helper coercion and loose role values.
  - Delete: `coerce_claim_concept_link_role`.
  - Reason: the module contains real relation-concept semantics, but
    `propstore.core` is the wrong owner. Claim-concept link roles belong with
    claim/concept relation ownership. `RelationConceptRef` and `RoleDefinition`
    accept `ConceptId | str`, `RoleBinding.value` is `object`, and
    `canonicalize_binary_values` stringifies arbitrary objects.
  - Required follow-up: delete the core import path first, move the relation
    kernel under the relation owner, require typed `ConceptId` and typed role
    value/reference objects, and update callers from the resulting failures.

- [x] `propstore/core/results.py`
  - Read: 2026-05-21.
  - Action: move analyzer result records to world/argumentation owner and
    replace loose string/metadata normalization.
  - Reason: analyzer results belong to world/argumentation runtime, not generic
    core. The module imports graph label serialization, stores backend and
    semantics as bare strings, carries claim IDs as strings, accepts
    `Mapping[str, Any]` in `from_dict`, and normalizes arbitrary metadata pairs.
  - Delete/rewrite: `_normalize_strings`, `_normalize_metadata`, graph-label
    dict coupling, and `from_dict` loose payload parsing inside runtime result
    constructors.
  - Required follow-up: delete the core import path first, move typed result
    objects to the analyzer owner, use typed backend/semantics/claim IDs, and
    put serialization in an explicit artifact/API boundary.

- [x] `propstore/core/source_types.py`
  - Read: 2026-05-21.
  - Action: move source-family vocabulary to source owner and delete coercers.
  - Delete: `coerce_source_kind` and `coerce_source_origin_type`.
  - Reason: source kind/origin vocabulary belongs to the source family/semantic
    owner, not generic core. Both helpers accept `object`, branch on strings,
    and reconstruct enum meaning locally.
  - Required follow-up: delete the coercers first, move/consolidate
    `SourceKind` and `SourceOriginType` under the source owner, and update
    callers to construct enums at IO/document boundaries only.

- [x] `propstore/core/store_results.py`
  - Read: 2026-05-21.
  - Action: move world store result DTOs to world/store owner and tighten ID
    construction.
  - Reason: search/similarity hits and world store stats are world-query result
    surfaces, not core primitives. `__post_init__` constructors convert IDs from
    whatever was passed instead of requiring typed IDs at the semantic boundary.
  - Required follow-up: delete the core import path first, move the result types
    to the world/store owner, and require typed `ClaimId`/`ConceptId` after
    boundary parsing.

## Progress

- Files read: 51 / 51.
- `propstore.core` audit read pass complete.
