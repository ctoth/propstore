# Quire Chained Reference Index Workstream

## Goal

Add a generic chained/fallback reference index to `../quire`, then delete
Propstore's local source-before-primary reference-resolution boilerplate.

The target architecture is:

- Quire owns ordered composition of existing `ReferenceIndex` /
  `FamilyReferenceIndex` instances.
- Propstore owns which indexes are chained, source-local lowering policy, and
  source-vs-canonical semantic boundaries.
- Propstore reference helper modules shrink by deleting generic fallback and
  trivial one-field index wrappers.

This workstream is deletion-first in Propstore. Once Quire exposes the generic
chain, delete Propstore fallback helpers before repairing callers.

This is a two-repository workstream. Quire changes land first. Propstore must
never pin Quire to a local path; pin only to a pushed tag or immutable pushed
commit SHA.

## Non-Goals

Do not move these into Quire:

- source-local handle semantics
- source promotion/finalize lowering rules
- canonical Propstore family declarations
- claim, concept, source, stance, or paper vocabulary
- compiler or sidecar semantic diagnostics

Do not add implicit global fallback lookup in Quire. The chain must be explicit
and ordered by the caller.

## Workstream Order

The phases below are topologically ordered.

1. Quire chained index tests
2. Quire chained index implementation
3. Propstore dependency pin
4. Propstore source claim fallback deletion
5. Propstore imported-handle wrapper deletion
6. Optional compiler/sidecar fallback cleanup
7. Final gates

## Phase 1 - Quire Chained Index Tests

Repository: `../quire`

Write failing tests for explicit ordered fallback resolution.

Required cases:

- first index wins when both indexes resolve a reference
- second index resolves when first misses
- missing reference returns `None` or raises the existing typed missing error,
  matching the method used
- ambiguity in the first matching index raises ambiguity and does not fall
  through silently
- `resolve(...)` preserves `ReferenceResolution.target_family`
- chain exposes the winning family/index name in resolution details if useful
- empty chains fail clearly

Property tests:

- generated disjoint indexes resolve exactly as the first index containing the
  key
- generated duplicate key in an earlier index never falls through to a later
  unambiguous match
- chain order changes results only when more than one index can resolve the key

Target tests:

- `../quire/tests/test_references.py`

Required gate:

- `uv run pytest tests/test_references.py`

## Phase 2 - Quire Chained Index Implementation

Repository: `../quire`

Add a generic explicit chain.

Candidate API:

```python
index = ChainedReferenceIndex((source_index, primary_index))
index.resolve_id("local-handle")
index.require_id("local-handle")
index.resolve("local-handle")
```

Acceptable alternative:

- `resolve_with_fallback(reference, indexes=(...))`
- `ReferenceIndex.chain(...)`

Requirements:

- no Propstore vocabulary
- no implicit global registry
- no hidden search path
- typed missing and ambiguity errors are preserved
- `resolve_id` and `require_id` behavior mirrors `FamilyReferenceIndex`
- implementation composes existing indexes instead of creating a parallel
  lookup representation when possible

Required gates:

- `uv run pytest tests/test_references.py tests/test_families.py`
- `uv run pytest`

## Phase 3 - Propstore Dependency Pin

Repository: `propstore`

Only start after Quire changes are pushed to a shared remote.

Before editing dependency metadata:

- verify the Quire reference is a pushed tag or immutable pushed commit SHA
- reject local paths, editable paths, local git paths, Windows drive paths, WSL
  paths, and `file://` URLs

Update:

- `pyproject.toml`
- `uv.lock`

Required gate:

- `uv run pyright propstore`

## Phase 4 - Propstore Source Claim Fallback Deletion

Repository: `propstore`

Delete first from `propstore/source/reference_indexes.py`:

- `resolve_source_or_primary_claim_id`

Then repair callers by constructing an explicit Quire chain at the semantic
boundary.

Known callers:

- `propstore/source/relations.py`
- source finalization checks
- source promotion planning
- tests in `tests/test_artifact_reference_resolver.py`

Rules:

- source-local indexes remain Propstore-owned
- canonical `repo.families.claims.reference_index()` remains the canonical
  family index
- the chain is explicit at the call site or at a named source subsystem boundary
- do not introduce a new Propstore fallback helper with a different name

Search gates:

- `rg -F "resolve_source_or_primary_claim_id" propstore tests` returns no refs
- `rg -F "source_or_primary" propstore tests` returns no new helper-shaped
  fallback logic

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label chained-claim-refs tests/test_artifact_reference_resolver.py tests/test_source_promote_dangling_refs.py tests/test_source_promotion_alignment.py`
- `uv run pyright propstore`

## Phase 5 - Propstore Imported-Handle Wrapper Deletion

Repository: `propstore`

Delete trivial one-field wrapper code where it only exists to build a generic
index.

Deletion candidates:

- `ImportedClaimHandle` if it carries no semantic behavior after caller repair
- `imported_claim_handle_index`
- private callback functions that return only `(record.handle,)`

Target shape:

- source import state either stores typed source claim records directly or uses a
  generic local record shape close to the source subsystem
- `FamilyReferenceIndex.from_records(...)` is called directly where a temporary
  source-local index is built
- no module-level wrapper survives solely to hide Quire API calls

Do not delete typed source-local records that encode semantic state. Delete only
generic boilerplate wrappers.

Search gates:

- `rg -F "ImportedClaimHandle" propstore tests` returns no refs unless a
  semantic record remains and is documented
- `rg -F "imported_claim_handle_index" propstore tests` returns no refs

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label imported-handle-delete tests/test_artifact_reference_resolver.py tests/test_source_claim_concept_rewrite.py tests/test_source_promotion_alignment.py`
- `uv run pyright propstore`

## Phase 6 - Optional Compiler/Sidecar Fallback Cleanup

Repository: `propstore`

Only do this if the first two Propstore phases reveal more local ordered
fallback code. Do not widen into a full reference/FK cleanup; that belongs to
`quire-reference-fk-validation-workstream-2026-05-12.md`.

Possible cleanup targets:

- compiler contexts that try source-local then canonical claim indexes
- sidecar build helpers that use fallback maps before canonical writes
- test-only helpers that duplicate chain behavior

Rules:

- delete local fallback code first
- keep semantic diagnostics in Propstore
- use Quire's chain only where ordered fallback is genuinely required
- prefer direct `FamilyReferenceIndex` where there is only one lookup scope

Required gates depend on selected deletion target. At minimum:

- `powershell -File scripts/run_logged_pytest.ps1 -Label chained-ref-optional tests/test_claim_compiler.py tests/test_build_sidecar.py tests/test_artifact_reference_resolver.py`
- `uv run pyright propstore`

## Phase 7 - Final Gates

Repository: both

Final Quire gates:

- `uv run pytest`

Final Propstore gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label chained-reference-full tests/test_artifact_reference_resolver.py tests/test_source_promote_dangling_refs.py tests/test_source_promotion_alignment.py tests/test_claim_compiler.py`
- `uv run pyright propstore`

Completion evidence:

- ordered fallback resolution exists once in Quire
- Propstore no longer owns generic source-before-primary fallback helpers
- Propstore keeps only source-local lowering semantics
- no new Propstore wrapper aliases hide the Quire chain
- no local Quire dependency pin is committed
