# Quire Reference and FK Validation Workstream

## Goal

Move generic artifact reference indexing and foreign-key validation into
`../quire`, then delete Propstore's ad hoc storage-reference maps and update
every caller to use the Quire storage system properly.

The target architecture is:

- Quire owns declarative per-family reference keys, generic reference indexes,
  typed missing/ambiguous reference failures, and mandatory foreign-key
  validation for family writes and transactions.
- Propstore owns source-local authoring semantics, source-local handle lowering,
  semantic family declarations, compiler workflows, source promotion, sidecar
  policy, and runtime world/sidecar query indexes.
- Canonical Propstore artifact writes must go through Quire family FK
  validation. Propstore must not keep parallel production resolver maps for
  canonical storage identity.

This is a two-repository workstream. Changes to `../quire` must land first.
Propstore dependency pins must never point at local filesystem paths. If
Propstore needs a Quire update, push Quire first and pin Propstore to a pushed
remote tag or immutable pushed commit SHA.

## Non-Goals

Do not add these:

- implicit ordered scopes, search paths, preload-style resolution, or global
  fallback lookup in Quire
- source-local handles in canonical family reference declarations
- Propstore vocabulary or source-promotion policy in Quire
- compatibility shims, old/new dual paths, alias modules, or fallback readers
- per-type Propstore wrapper functions around a generic Quire reference index
- runtime sidecar or world-query replacement for `WorldQuery.resolve_*`
- local dependency pins between Propstore and Quire

Source-local handles remain semantically separate. Propstore may build an
explicit temporary source-local index while lowering source authoring records,
but canonical artifacts must be validated by Quire's family reference and FK
surface after lowering.

## Workstream Order

The phases below are topologically ordered. Do not start a phase until its
dependencies are complete. Each implementation phase starts with failing tests,
keeps the old production surface deleted before caller repair where the phase is
a replacement, and ends with the listed search and test gates.

1. Quire RED tests for declarative reference keys
2. Quire generic family reference index
3. Quire family declaration metadata
4. Quire mandatory FK validation
5. Quire documentation and contract gates
6. Propstore Quire dependency pin
7. Propstore canonical family declarations
8. Propstore claim-reference deletion
9. Propstore compiler reference deletion
10. Propstore sidecar reference-map deletion
11. Propstore concept registry map deletion
12. Propstore docs and contributor guidance
13. Final cross-repository gates

## Phase 1 - Quire RED Tests for Declarative Reference Keys

Repository: `../quire`

Write failing tests first. Do not implement production code until these tests
fail for the missing behavior.

Add tests for:

- `ReferenceKey.field("artifact_id")`
- `ReferenceKey.field("logical_ids[].value")`
- `ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]")`
- callback-supplied keys for consumer-specific extraction
- missing optional fields producing no key, not an empty-string key
- duplicate keys for the same artifact id deduplicating cleanly
- duplicate keys for different artifact ids raising a typed ambiguity error
- malformed path specs failing at declaration time

Hypothesis properties:

- for any generated unique artifact ids and unique aliases, every emitted key
  resolves to exactly the artifact id that emitted it
- for any generated duplicate alias assigned to two different ids, index build
  raises `AmbiguousReferenceError`
- extraction is order-independent: shuffling input records does not change
  successful lookup results or ambiguity failures
- missing optional nested lists never creates a resolvable key

Target test files:

- `tests/test_references.py`
- `tests/test_families.py` if family declarations already have the closest
  contract tests

Required gate:

- `uv run pytest tests/test_references.py tests/test_families.py`

## Phase 2 - Quire Generic Family Reference Index

Repository: `../quire`

Add the smallest generic surface that satisfies Phase 1.

Target public shape:

```python
index = FamilyReferenceIndex.from_records(
    records,
    artifact_id=lambda record: record.artifact_id,
    keys=(
        ReferenceKey.field("artifact_id"),
        ReferenceKey.field("logical_ids[].value"),
        ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
        lambda record: record.extra_aliases,
    ),
)

artifact_id = index.require_id("claim:local-handle")
maybe_id = index.resolve_id("claim:local-handle")
```

Add:

- `ReferenceKey`
- `FamilyReferenceIndex`
- `MissingReferenceError`
- `AmbiguousReferenceError`

Rules:

- errors are typed and inspectable; Propstore must not parse strings
- ambiguity is detected at index-build time
- callback keys are explicit and local to the caller
- Quire does not know about Propstore claims, concepts, sources, or handles
- the index maps references to artifact ids, not loaded artifact objects

Hypothesis properties:

- `require_id(key)` returns the same value as `resolve_id(key)` when the key is
  present and unambiguous
- `require_id(key)` raises `MissingReferenceError` for absent keys
- identical repeated aliases on the same artifact never create false ambiguity
- every ambiguity error identifies the key and conflicting artifact ids

Required gates:

- `uv run pytest tests/test_references.py`
- `uv run pytest tests/test_families.py`

## Phase 3 - Quire Family Declaration Metadata

Repository: `../quire`

Extend family declarations so references are part of the family contract, not a
consumer-side convention.

Target shape:

```python
FamilyDefinition(
    name="claims",
    artifact_family=CLAIM_FAMILY,
    identity_field="artifact_id",
    reference_keys=(
        ReferenceKey.field("artifact_id"),
        ReferenceKey.field("logical_ids[].value"),
        ReferenceKey.format("{namespace}:{value}", from_field="logical_ids[]"),
    ),
    foreign_keys=(...),
)
```

Requirements:

- cheap families remain cheap to declare
- default identity can be explicit, such as `identity_field="id"`
- a family with no aliases can use only the identity field
- declarations expose a bound way to build that family's reference index from a
  snapshot or loaded records
- declaration validation rejects invalid field paths and invalid FK references
  before the first write

Hypothesis properties:

- for any declared identity field and generated records with unique identities,
  the default identity key resolves every record
- adding extra reference keys can only add resolvable keys or introduce typed
  ambiguity; it must not change identity-key resolution
- declaration serialization or contract inspection preserves reference-key and
  FK metadata

Required gates:

- `uv run pytest tests/test_references.py tests/test_families.py tests/test_family_store.py`
- `uv run pytest`

## Phase 4 - Quire Mandatory FK Validation

Repository: `../quire`

Make FK validation mandatory on family writes and transactions. Validation must
use declared target-family reference indexes, not consumer-provided ad hoc maps.

Required behavior:

- saving an artifact with a required FK to a missing target fails before commit
- saving an artifact with an optional missing FK fails when the field is present
- saving an artifact with an omitted optional FK succeeds
- saving an artifact with an ambiguous target key fails before commit
- a transaction that writes a target and a dependent artifact in the same batch
  succeeds when the post-transaction snapshot is valid
- deleting or replacing a target that would leave existing dependents dangling
  fails before commit
- validation sees the post-transaction state, not operation order inside the
  transaction
- failures raise Quire typed errors directly

Hypothesis properties:

- generated valid dependency graphs commit successfully
- generated missing target references fail with `MissingReferenceError` or a
  typed FK wrapper that preserves the Quire reference error
- generated duplicate target aliases fail with `AmbiguousReferenceError`
- generated add/update/delete transactions are accepted exactly when the final
  graph satisfies all declared FKs
- operation order inside a transaction does not affect validation outcome

Target test files:

- `tests/test_foreign_keys.py`
- `tests/test_family_store.py`
- `tests/test_families.py`

Required gates:

- `uv run pytest tests/test_references.py tests/test_foreign_keys.py tests/test_family_store.py tests/test_families.py`
- `uv run pytest`

## Phase 5 - Quire Documentation and Contract Gates

Repository: `../quire`

Update docs after the behavior exists.

Docs:

- `README.md`: add a "References and foreign keys" section showing declarative
  family references, `FamilyReferenceIndex`, and mandatory FK validation
- `AGENTS.md` and `CLAUDE.md`: add one sentence stating that storage artifact
  identity and cross-family references belong in Quire family declarations and
  FK validation, not ad hoc consumer maps

Search gates:

- no Quire docs describe FK validation as optional
- no Quire tests rely on string parsing for reference or FK errors
- no Quire code imports Propstore or mentions Propstore domain vocabulary outside
  consumer-neutral examples

Required gates:

- `uv run pytest`

## Phase 6 - Propstore Quire Dependency Pin

Repository: `propstore`

Only start this after the Quire changes are pushed to a shared remote.

Before editing dependency metadata:

- verify the intended Quire reference is a pushed tag or immutable pushed commit
  SHA
- reject any local path, editable path, local git path, Windows drive path, WSL
  path, or `file://` reference

Update:

- Propstore dependency metadata and lockfile, if Quire is pinned there

Required gate:

- `uv run pyright propstore`

## Phase 7 - Propstore Canonical Family Declarations

Repository: `propstore`

Declare canonical reference keys and FKs on Propstore families through Quire.
This phase does not delete old callers yet; it makes the target path available.

Families to validate:

- claims
- concepts
- concept forms
- contexts
- sources
- stances
- justifications
- micropublications
- any remaining semantic family with `foreign_keys` or `*_id` references

Rules:

- canonical family declarations include canonical artifact ids and canonical
  aliases only
- source-local handles do not appear in canonical family declarations
- Propstore semantic FK declarations stay in Propstore, but Quire enforces them
  generically

Hypothesis tests:

- generated canonical artifacts with valid references pass Quire validation
- generated canonical artifacts with missing references fail at write time
- generated source-local-only handle fields are rejected from canonical surfaces
  when present there
- generated duplicate canonical aliases fail with Quire ambiguity errors

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label quire-family-refs tests/test_semantic_family_registry.py`
- `uv run pyright propstore`

## Phase 8 - Propstore Claim-Reference Deletion

Repository: `propstore`

Delete first:

- `propstore/claim_references.py`

Then use failures and literal references as the work queue.

Known callers to update:

- `propstore/source/__init__.py`
- `propstore/source/relations.py`
- `propstore/source/finalize.py`
- `propstore/source/promote.py`
- `propstore/source/stages.py`
- tests importing `ClaimReferenceIndex`, `ClaimReferenceResolver`, or
  `ImportedClaimHandleIndex`

Target replacement:

- source workflows build an explicit temporary source-local
  `FamilyReferenceIndex.from_records(...)` for authoring handles
- source finalization lowers source-local handles into canonical artifact ids
- canonical writes rely on Quire FK validation
- missing or ambiguous canonical references raise Quire errors directly unless a
  Propstore semantic boundary needs to attach source-location context

Remove these names completely:

- `ClaimReferenceIndex`
- `ClaimReferenceResolver`
- `ImportedClaimHandleIndex`
- `build_source_claim_reference_index`
- `load_source_claim_reference_index`
- `load_primary_branch_claim_reference_index`

Hypothesis tests:

- generated source-local handles lower to canonical claim artifact ids when
  source relations are valid
- generated dangling source-local references fail before promotion
- generated duplicate imported handles fail with Quire ambiguity
- generated canonical references written by promotion satisfy Quire FK validation

Search gates:

- `rg -F "propstore.claim_references" propstore tests` returns no refs
- `rg -F "ClaimReferenceIndex" propstore tests` returns no refs
- `rg -F "ClaimReferenceResolver" propstore tests` returns no refs
- `rg -F "ImportedClaimHandleIndex" propstore tests` returns no refs

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label source-refs tests/test_artifact_reference_resolver.py tests/test_source_relations.py tests/test_source_promote_dangling_refs.py tests/test_source_promotion_alignment.py`
- `uv run pyright propstore`

## Phase 9 - Propstore Compiler Reference Deletion

Repository: `propstore`

Delete old production lookup helpers before caller repair.

Delete or replace:

- `propstore/compiler/references.py::build_claim_reference_lookup`
- `propstore/compiler/references.py::foreign_keys_from_context`
- `propstore/compiler/references.py::concept_exists`
- `propstore/compiler/references.py::claim_exists`
- `propstore/compiler/references.py::resolve_claim_reference`
- `propstore/compiler/references.py::resolve_concept_reference`

Relocate any non-reference semantic helper, such as concept-form lookup, to the
owning compiler/context module instead of keeping `compiler/references.py` alive
as a mixed-purpose storage resolver.

Target replacement:

- `CompilationContext` receives or builds Quire family reference indexes for
  canonical claims and concepts
- compiler checks call Quire `require_id` or `resolve_id`
- FK extraction comes from Quire family declarations, not a Propstore duplicate
  table

Hypothesis tests:

- generated compiler contexts resolve every declared canonical claim/concept
  alias through Quire indexes
- generated dangling compiler references fail with the Quire missing-reference
  error path
- generated duplicate aliases fail with Quire ambiguity
- compiler FK checks agree with Quire FK validation for generated artifacts

Search gates:

- `rg -F "build_claim_reference_lookup" propstore tests` returns no refs
- `rg -F "foreign_keys_from_context" propstore tests` returns no refs
- `rg -F "concept_exists" propstore tests` returns no production refs
- `rg -F "claim_exists" propstore tests` returns no production refs

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label compiler-refs tests/test_claim_compiler.py tests/test_semantic_family_registry.py`
- `uv run pyright propstore`

## Phase 10 - Propstore Sidecar Reference-Map Deletion

Repository: `propstore`

Delete production-side ad hoc claim reference maps used during sidecar builds.
This does not replace runtime world-query indexes.

Delete or replace:

- `propstore/sidecar/claim_utils.py::collect_claim_reference_map`
- `propstore/sidecar/claim_utils.py::resolve_claim_reference`
- `claim_reference_map` parameters in sidecar build passes
- `valid_claims = set(claim_reference_map.values())` style validation

Target replacement:

- sidecar build code receives or builds a Quire claim `FamilyReferenceIndex`
  from canonical loaded claim artifacts
- sidecar passes use index resolution for storage references
- sidecar runtime query indexes remain sidecar-owned

Hypothesis tests:

- generated sidecar inputs resolve all canonical claim references through Quire
- generated dangling claim references fail before sidecar facts are written
- generated duplicate aliases fail with Quire ambiguity
- the set of valid canonical claim ids is derived from the index or loaded
  canonical records, not a duplicate map

Search gates:

- `rg -F "collect_claim_reference_map" propstore tests` returns no refs
- `rg -F "resolve_claim_reference" propstore\\sidecar tests` returns no refs
- `rg -F "claim_reference_map" propstore\\sidecar tests` returns no refs

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label sidecar-refs tests/test_build_sidecar.py tests/test_sidecar_grounded_facts.py tests/test_sidecar.py`
- `uv run pyright propstore`

## Phase 11 - Propstore Concept Registry Map Deletion

Repository: `propstore`

Replace storage identity maps in source concept registration with Quire
reference indexes and explicit source-local lowering.

Delete or replace:

- `handle_to_artifact`
- `local_handle_to_artifact`
- `ConceptAliasCollisionError` when it only duplicates Quire ambiguity
- source registry canonical alias maps that duplicate Quire family indexes

Known areas:

- `propstore/source/registry.py`
- `propstore/app/concepts/mutation.py`
- any source concept tests that assert bespoke alias collision errors

Target replacement:

- canonical concept aliases resolve through Quire concept family indexes
- source-local concept handles lower through an explicit temporary source-local
  index before canonical writes
- canonical writes rely on Quire FK validation and ambiguity errors

Hypothesis tests:

- generated source-local concept handles lower to canonical concept ids
- generated duplicate canonical concept aliases fail with Quire ambiguity
- generated source-local-only fields are rejected from canonical concept writes
- generated concept mutation requests cannot create dangling canonical FKs

Search gates:

- `rg -F "ConceptAliasCollisionError" propstore tests` returns no refs unless a
  remaining semantic collision is documented and not storage identity
- `rg -F "handle_to_artifact" propstore tests` returns no refs
- `rg -F "local_handle_to_artifact" propstore tests` returns no refs

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label concept-refs tests/test_source_registry.py tests/test_concept_mutation.py tests/test_semantic_family_registry.py`
- `uv run pyright propstore`

## Phase 12 - Propstore Docs and Contributor Guidance

Repository: `propstore`

Update docs after production code uses the new path.

Docs:

- `AGENTS.md`: add one sentence stating that storage artifact identity and
  cross-family references must use Quire family reference/FK APIs, while
  source-local handles are lowered explicitly inside the source subsystem before
  canonical writes
- `CLAUDE.md`: add the same operational rule if the file exists
- any contributor or architecture doc that still recommends resolver maps,
  `whatever_id` scans, or hand-rolled FK validation

Search gates:

- `rg -F "ClaimReferenceIndex" AGENTS.md CLAUDE.md docs propstore tests` returns
  no stale guidance
- `rg -F "claim_reference_map" AGENTS.md CLAUDE.md docs propstore tests` returns
  no stale guidance
- docs do not describe FK validation as optional or caller-owned

Required gates:

- `uv run pyright propstore`

## Phase 13 - Final Cross-Repository Gates

Repositories: `../quire`, `propstore`

Quire gates:

- `uv run pytest`

Propstore gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label reference-fk-full`
- `uv run pyright propstore`

Final Propstore search gates:

- `rg -F "propstore.claim_references" propstore tests`
- `rg -F "ClaimReferenceIndex" propstore tests`
- `rg -F "ClaimReferenceResolver" propstore tests`
- `rg -F "ImportedClaimHandleIndex" propstore tests`
- `rg -F "build_source_claim_reference_index" propstore tests`
- `rg -F "load_source_claim_reference_index" propstore tests`
- `rg -F "load_primary_branch_claim_reference_index" propstore tests`
- `rg -F "collect_claim_reference_map" propstore tests`
- `rg -F "claim_reference_map" propstore tests`
- `rg -F "foreign_keys_from_context" propstore tests`

Completion evidence:

- every canonical Propstore family write with declared FKs is validated by Quire
- source-local handles are lowered before canonical writes and never appear in
  canonical family reference declarations
- old Propstore storage resolver surfaces are deleted, not wrapped
- Quire docs explain references and mandatory FK validation
- Propstore contributor docs tell future work to use Quire reference/FK APIs
- no committed dependency points at a local Quire checkout
