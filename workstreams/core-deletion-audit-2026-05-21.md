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

## File Checklist

- [x] `propstore/core/__init__.py`
  - Read: 2026-05-21.
  - Action: keep shallow package initializer.
  - Reason: empty `__all__` and no eager re-exports; it does not preserve old
    paths or pull runtime owners into `core`.

- [x] `propstore/core/activation.py`
  - Read: 2026-05-21.
  - Action: rewrite/move candidate.
  - Reason: activation over compiled world graphs is real behavior, but it is
    world runtime orchestration over `CompiledWorldGraph`, `Environment`,
    condition solvers, and context lifting. It should be audited against the
    world owner boundary before being kept in `core`.
  - Required follow-up: decide whether the semantic primitive is only
    condition-activation math or whether the whole module belongs under
    `propstore.world`. If moved, delete the old `propstore.core.activation`
    import path first and update callers; no re-export module.

- [x] `propstore/core/algorithm_stage.py`
  - Read: 2026-05-21.
  - Action: delete helper functions; keep only the branded type if stage remains
    a Propstore semantic primitive.
  - Delete: `to_algorithm_stage` and `coerce_algorithm_stage`.
  - Reason: both functions are helper-shaped wrappers around the `NewType`.
    `coerce_algorithm_stage` accepts `object` and reconstructs semantic meaning
    locally instead of requiring the boundary to pass `AlgorithmStage | None`.
  - Required follow-up: update all callers to construct `AlgorithmStage(value)`
    at IO/document/app boundaries and pass typed values through runtime APIs.

- [x] `propstore/core/aliases.py`
  - Read: 2026-05-21.
  - Action: move or delete from `core`.
  - Reason: the module opens repository family handles and exports a concept
    alias report. That is repository/app/family presentation behavior, not a
    core semantic primitive. It imports `Repository`,
    `parse_concept_record_document`, and identity helper code, so keeping it in
    `core` violates owner layering.
  - Required follow-up: find callers. If the export is still used, move it to
    the concept app/family owner and delete the `propstore.core.aliases` import
    path first; no core re-export.

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
  - Action: consolidate package API or remove eager re-exports after caller
    audit.
  - Reason: it eagerly re-exports assertion codec, conversion, refs, and
    situated types. This is not an old-path shim by itself, but low-level
    package `__init__.py` files are required to stay shallow. If callers only
    need concrete modules, delete these re-exports and update imports directly.
  - Required follow-up: search callers of `propstore.core.assertions import`.
    If re-export use is broad convenience only, delete the re-export surface;
    if kept, prove it does not pull owner workflows or create circular imports.

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
  - Action: split. Keep typed resolver/value objects; move or delete source
    claim payload parsing from `core`.
  - Reason: `BaseRateProfile`, `BaseRateResolver`, and
    `construct_assertion_opinion` operate on typed assertion IDs and opinion
    domain objects. `BaseRateAssertionRecord.from_parameter_claim` accepts a
    loose `Mapping[str, object]` and hardcodes claim payload fields
    (`type`, `id`, `concept`, `value`, `unit`) inside `core`.
  - Delete/move: `BaseRateAssertionRecord.from_parameter_claim` cannot remain
    in `core`; it belongs at the source/family/document boundary or should be
    replaced by a typed parameter-claim/domain object supplied by that owner.
  - Required follow-up: search callers, delete the loose mapping entrypoint
    first, then update callers to pass typed claim/domain objects.

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
  - Required follow-up: delete `coerce_claim_type` first. Move or consolidate
    `ClaimType` under the claim family/semantic owner, then update callers to
    construct `ClaimType(value)` at IO/document boundaries and pass typed values
    through runtime APIs.

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
  - Required follow-up: move typed claim/source value objects to the claim or
    source owner. Parse decoded JSON/YAML/SQLite values at the IO boundary with
    an exact schema and hard failures; do not preserve fallback-to-empty
    behavior.

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

- [x] `propstore/core/conditions/__init__.py`
  - Read: 2026-05-21.
  - Action: delete eager low-level package re-export surface unless caller audit
    proves it is the intentional condition package API.
  - Reason: this initializer imports checked models, codecs, ESTree backend,
    IR, Python backend, SQL backend, solver, and Z3 backend. That violates the
    shallow package initializer rule and can pull unrelated backends into
    callers that only need one surface.
  - Required follow-up: search all `propstore.core.conditions import` callers.
    Prefer concrete-module imports. If a package API remains, it must be narrow
    and must not import every backend eagerly.

- [x] `propstore/core/conditions/cel_frontend.py`
  - Read: 2026-05-21.
  - Action: keep in condition owner, with type-boundary tightening.
  - Reason: this is the real CEL frontend lowering/type-checking owner for
    `ConditionIR`. It uses typed registry entries, hard-fails unsupported CEL
    nodes, and does not preserve old shapes. The remaining tightening is to
    ensure public entrypoints use the declared CEL/domain source type
    consistently rather than plain strings where the type system can carry
    `CelExpr`.
  - Required follow-up: audit callers of `condition_ir_from_cel` and
    `check_condition_ir`; if they already have `CelExpr`, pass it through as a
    typed value instead of stringifying before this boundary.

- [x] `propstore/core/conditions/checked.py`
  - Read: 2026-05-21.
  - Action: keep in condition owner, with CEL source type tightening.
  - Reason: `CheckedCondition` and `CheckedConditionSet` are typed runtime
    carriers for checked condition semantics. JSON decode/encode functions are
    explicit versioned IO boundaries and hard-fail malformed payloads.
    `_normalize_checked_conditions` operates on typed `CheckedCondition`
    objects, so it is canonicalization rather than mixed-shape coercion.
  - Required follow-up: consider carrying `CelExpr` instead of bare `str` for
    `CheckedCondition.source` and `.sources` if the type exists at all callers.

- [x] `propstore/core/conditions/codec.py`
  - Read: 2026-05-21.
  - Action: keep as condition-owned versioned JSON codec.
  - Reason: it serializes/deserializes the closed `ConditionIR` tree at an IO
    boundary, uses explicit version tags, enum constructors, and hard failures.
    It does not preserve old shapes or define broad compatibility fallbacks.
  - Required follow-up: none from deletion rules unless duplicate condition
    JSON parsing appears elsewhere during the remaining audit.

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
  - Action: keep only if it remains an explicit backend; tighten value typing
    and consolidate evaluator semantics with ESTree where duplication appears.
  - Reason: the backend translates closed `ConditionIR` to Python AST and
    evaluates a controlled expression. The public evaluator accepts
    `Mapping[str, object]` and returns `object`, duplicating the loose-value
    problem also present in the ESTree backend.
  - Required follow-up: introduce the same condition evaluation value type used
    by the ESTree backend. If both evaluators implement the same runtime
    semantics for production callers, consolidate the production evaluator and
    keep backend-specific translation only where needed.

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
    iterable of concept IDs. Ensure standard synthetic bindings remain
    explicitly non-concept condition bindings instead of fake concept metadata
    unless the concept owner declares them.

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
  - Delete/move: store protocols belong under the world/repository owner.
    `Environment` belongs with the world/condition runtime owner unless a
    smaller typed condition-environment primitive is extracted.
  - Required follow-up: delete the core import path first, update callers to the
    world owner, and replace `from_dict` with an exact IO-boundary decoder that
    hard-fails malformed assumptions.

- [x] `propstore/core/exactness_types.py`
  - Read: 2026-05-21.
  - Action: move parameterization exactness vocabulary to the parameterization or
    concept-family owner and delete the helper.
  - Delete: `coerce_exactness`.
  - Reason: exactness is parameterization/concept-family semantics, not generic
    core infrastructure. The helper accepts `object | None` and stringifies
    locally.
  - Required follow-up: delete `coerce_exactness` first, move/consolidate
    `Exactness` under the semantic owner, and update callers to construct the
    enum at IO/document boundaries only.

- [x] `propstore/core/graph_build.py`
  - Read: 2026-05-21.
  - Action: move out of `core` to world graph/build owner and rewrite from typed
    family projections.
  - Reason: it builds compiled world graphs from world/repository stores,
    imports family models, parses JSON sidecar fields, performs provenance
    payload decoding, deduplicates parameterization rows in Python when store
    querying should own that, and calls graph relation coercers. This is world
    graph orchestration, not core primitive code.
  - Delete/move: `build_compiled_world_graph` and its helpers cannot remain in
    `core`.
  - Required follow-up: delete the core import path first, move real graph build
    behavior to the world/family graph owner, and have stores/family APIs supply
    typed rows/projections instead of parsing JSON strings and loose mappings in
    graph build code.

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
  - Action: rewrite/move; delete duplicated family field models and helper
    normalization/coercion from `core`.
  - Reason: `ConceptNode`, `ClaimNode`, `RelationEdge`, `ParameterizationEdge`,
    `ConflictWitness`, and `WorldActivationGraph` hand-type many fields already
    owned by claim/concept/relation/parameterization families or world runtime
    state. The module imports enum coercers, accepts loose `Mapping[str, Any]`
    payloads, parses embedded JSON, normalizes arbitrary attribute pairs, and
    has `from_dict`/`to_dict` schema definitions separate from the charters.
  - Delete/rewrite: `_normalize_pairs`, `_require_claim_type`,
    `ProvenanceRecord.from_json_payload`, graph `from_dict` methods, and
    dataclass `__post_init__` coercion of claim/exactness/relation types.
  - Required follow-up: define the graph projection once from the family/world
    owners or generated field metadata. Runtime graph code must receive typed
    `ClaimType`, relation type, `Exactness`, `ConceptId`, `ClaimId`, and
    `Environment` objects; IO decoding belongs at a versioned graph artifact
    boundary, not inside semantic dataclass constructors.

- [x] `propstore/core/id_types.py`
  - Read: 2026-05-21.
  - Action: keep semantic ID aliases only until replaced by Quire/family
    reference types; move logical identity record to identity owner if still
    needed.
  - Reason: `NewType` aliases are the current mechanism carrying semantic IDs
    through the type system. They do not parse old shapes. `LogicalId`, however,
    is identity-family behavior and payload shape, not generic core code.
  - Required follow-up: as Quire family reference/FK APIs become the canonical
    reference mechanism, replace direct string/NewType plumbing with those
    typed references. Move or delete `LogicalId` from `core` after caller audit.

- [x] `propstore/core/justifications.py`
  - Read: 2026-05-21.
  - Action: move out of `core` and rewrite duplicated justification/graph
    payload handling.
  - Reason: `Justification` is a `FamilyModel` subclass with semantic methods,
    which is the right pattern for attaching behavior to generated fields, but
    it is in the wrong owner package. `CanonicalJustification` duplicates a
    justification/argument record shape, parses loose mappings in `from_dict`,
    parses JSON fields, imports graph provenance, and
    `claim_justifications_from_active_graph` is active-world argumentation
    orchestration.
  - Delete/move: the family model subclass belongs under the justification
    family owner. Active-graph justification projection belongs under the
    world/argumentation owner. `CanonicalJustification.from_dict` and duplicated
    payload schema should be replaced by the owner boundary.
  - Required follow-up: delete `propstore.core.justifications` first, move the
    real behavior to the owner modules, and update callers; no core re-export.

- [x] `propstore/core/labels.py`
  - Read: 2026-05-21.
  - Action: split. Keep ATMS/provenance label algebra; move/rewrite CEL binding
    parsing and loose environment compilation.
  - Reason: `EnvironmentKey`, `NogoodSet`, `Label`, and polynomial conversion
    are core belief-space kernel behavior. But `binding_condition_to_cel`,
    `cel_to_binding`, and `compile_environment_assumptions` accept loose
    `Any`/string values, render CEL by string interpolation, and parse CEL back
    with string splitting. That is boundary/world condition handling, not core
    label algebra.
  - Delete/rewrite: `cel_to_binding` string parsing and `binding_condition_to_cel`
    interpolation must be replaced by typed condition construction at the
    world/condition boundary. `compile_environment_assumptions` should receive
    typed bindings/assumptions, not `Mapping[str, Any]`.
  - Required follow-up: keep only the label algebra in `core`; move binding/CEL
    conversion to the world/condition owner and use the shared condition value
    type.

- [x] `propstore/core/lemon/__init__.py`
  - Read: 2026-05-21.
  - Action: delete eager broad re-export surface unless caller audit proves this
    is the intentional Lemon package API.
  - Reason: it imports and re-exports every Lemon submodule surface. That is a
    low-level package initializer doing broad eager imports. It is not an old
    compatibility shim by itself, but it violates the shallow initializer rule.
  - Required follow-up: search callers. Prefer concrete Lemon module imports,
    or keep only a narrow public Lemon API that does not pull all submodules
    eagerly.

- [x] `propstore/core/lemon/description_kinds.py`
  - Read: 2026-05-21.
  - Action: keep Lemon domain structs; tighten identity/reference IDs if owner
    types exist.
  - Reason: `DescriptionKind`, slots, bindings, merge arguments, and causal
    assertions are semantic Lemon domain objects, not storage/family mechanics
    or compatibility wrappers. They use `DocumentStruct` for structured fields
    and validate slot bindings.
  - Required follow-up: replace bare `str` IDs such as `claim_id`,
    `description_claim_ids`, and causal description IDs with typed owner IDs
    once those are available, rather than carrying raw strings through the
    semantic pipeline.

- [x] `propstore/core/lemon/forms.py`
  - Read: 2026-05-21.
  - Action: keep as Lemon lexical form value object.
  - Reason: `LexicalForm` is a narrow domain object with field-local validation.
    `require_text` and `fold_text` are local lexical text utilities, not old
    path adapters or broad semantic coercers.
  - Required follow-up: none from deletion rules unless duplicate lexical text
    normalization appears elsewhere in the Lemon audit.

- [x] `propstore/core/lemon/proto_roles.py`
  - Read: 2026-05-21.
  - Action: keep ProtoRole domain model; tighten entailment property typing.
  - Reason: the file encodes Dowty-style proto-role domain semantics and does
    not duplicate storage/family mechanics. `GradedEntailment.property` is a
    bare `str` that is checked against enum classes in `ProtoRoleBundle` but not
    stored as the enum type.
  - Required follow-up: make proto-agent and proto-patient entailment property
    types explicit at construction or split the entailment records by owner role
    so the type system carries the vocabulary.

- [x] `propstore/core/lemon/qualia.py`
  - Read: 2026-05-21.
  - Action: keep Qualia domain model; review `coerce_via_qualia` naming under
    search gates.
  - Reason: the function named `coerce_via_qualia` is not a type coercion helper;
    it implements a Pustejovsky qualia-mediated semantic operation and returns a
    `CoercedReference` domain object. It must not become an excuse for broad
    `coerce_*` helper allowance.
  - Required follow-up: either document this as an explicit domain exception in
    the old-symbol search gate or rename to a non-helper-shaped domain verb such
    as `qualia_mediated_reference` and update callers.

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
  - Required follow-up: replace the fake concept registry with either typed
    interval relation math or explicit non-concept condition bindings from the
    condition owner. Use typed claim/description IDs instead of raw strings.

- [x] `propstore/core/lemon/types.py`
  - Read: 2026-05-21.
  - Action: keep Lemon lexical entry/sense domain model; tighten role bundle
    collection typing if needed.
  - Reason: this file is semantic Lemon modeling, not storage plumbing or
    compatibility code. The main loose point is
    `role_bundles: Mapping[str, ProtoRoleBundle] | None`, where arbitrary
    string role names are validated only as non-empty text.
  - Required follow-up: if role names are a known vocabulary, carry that
    vocabulary in the type. If they are intentionally open lexical roles, keep
    the text validation and document the openness.

- [x] `propstore/core/literal_keys.py`
  - Read: 2026-05-21.
  - Action: keep ASPIC literal key domain objects; delete raw string claim-key
    surface.
  - Reason: the file defines typed literal identity keys grounded in the ASPIC
    literature. `IstLiteralKey` carries `ContextId` and `ClaimId`, but
    `ClaimLiteralKey.claim_id` and `claim_key(claim_id: str, context_id:
    ContextId | str)` allow raw strings at the semantic boundary.
  - Required follow-up: remove unused `ClaimLiteralKey` if caller audit confirms
    `IstLiteralKey` is the canonical claim literal. Change `claim_key` to accept
    `ClaimId` and `ContextId` after boundary parsing.

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
