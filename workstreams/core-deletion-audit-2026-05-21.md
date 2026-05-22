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

## Progress

- Files read: 18 / 51.
- Next file: `propstore/core/conditions/checked.py`.
