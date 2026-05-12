# Typed Source Promotion Cleanup Workstream

Date: 2026-05-12

## Goal

Delete the remaining boilerplate left after the semantic-artifact cutovers by
making source import, source finalize, source promotion, and proposal promotion
build typed domain artifacts directly instead of moving canonical semantic
objects through loose payload dictionaries.

This is a TDD, deletion-first workstream. Source-local batch files remain
source-local authoring state. Canonical/master artifacts remain one semantic
artifact per family artifact.

## Target Architecture

The source subsystem has three explicit typed boundaries:

- source-local authoring batches:
  - `SourceClaimsDocument`
  - `SourceJustificationsDocument`
  - `SourceStancesDocument`
  - source-local `MicropublicationsFileDocument`
- typed promotion planning:
  - `ClaimDocument`
  - `StanceDocument`
  - `JustificationDocument`
  - `MicropublicationDocument`
  - `ConceptDocument`
  - `SourceDocument`
- typed canonical writes through `repo.families.<family>.save(...)`

Concept-reference rewriting is one shared source/promotion policy, not two
parallel helper families.

Proposal promotion has one shared transaction skeleton for "planned artifact to
canonical artifact" writes. Rule, predicate, and stance modules still own their
domain selection, validation, and document construction.

## Non-Goals

- Do not delete source-local batch files such as `claims.yaml`, `stances.yaml`,
  `justifications.yaml`, or `micropubs.yaml`.
- Do not add generic CRUD wrappers around rules, predicates, forms, contexts,
  or concepts.
- Do not move Propstore semantic policy into Quire.
- Do not replace payload-dict code with wrapper-shaped aliases that preserve
  the same loose boundary.
- Do not broaden this into another canonical family cutover.
- Do not preserve old and new production paths in parallel.

## Execution Rules

- Work deletion-first.
- Add or update tests that fail against the old loose-payload or duplicated
  helper surface before each production slice.
- Delete the old production helper first, then use type, search, and test
  failures as the work queue.
- Commit every intentional edit slice atomically with path-limited git
  commands.
- After every commit, reread this workstream before choosing the next edit
  slice.
- After every passing substantial targeted test run, reread this workstream
  before choosing the next edit slice.
- Use logged pytest wrappers for tests.
- Run Python tooling through `uv`.
- Do not report completion while old production helpers coexist with the new
  typed path unless this workstream explicitly marks that old helper as a
  source-local authoring boundary.

## Dependency Order

Execute in this order:

1. Workstream order check
2. Shared typed claim concept-reference rewrite policy
3. Typed source-import claim normalization
4. Typed source-finalize micropub composition
5. Typed source-promotion plan builder
6. Shared proposal-promotion transaction skeleton
7. Search, contract, documentation, and full-suite closure

Before implementation, make this dependency order mechanically executable:
write or run an order check that proves each dependent phase appears after its
prerequisites. If the check fails, repair this workstream before editing
production code.

## Phase 1: Workstream Order Check

Goal: prove this checklist is mechanically executable before production edits.

Tasks:

- Add or run a reusable order check over this workstream's dependency order.
- Verify phases appear in the exact dependency order above.
- Commit the order check or documented order repair before touching production
  code if a new reusable check is needed.

Gate:

- The order check passes for this workstream.

## Phase 2: Shared Typed Claim Concept-Reference Rewrite Policy

Goal: delete duplicated source/promotion claim concept rewrite logic.

Delete-first targets:

- Delete `_place_promoted_singular_concept` from `propstore/source/promote.py`.
- Delete `_place_rewritten_singular_concept` from `propstore/source/passes.py`.
- Delete the duplicate claim-reference rewrite implementation from one of:
  - `propstore/source/promote.py`
  - `propstore/source/passes.py`

Target shape:

- Add one owner-layer helper in the source subsystem that accepts a typed
  source or canonical claim document plus a concept-ref resolver.
- The helper returns a typed canonical `ClaimDocument` or a normalized canonical
  claim payload only at the IO boundary required by existing identity code.
- The old source-local `concept` field is placed by one policy:
  - parameter and algorithm claims use `output_concept`
  - measurement claims use `target_concept`
  - other claims use `concepts`

Tests first:

- Add a unit test proving source import and source promotion use identical
  placement for source-local `concept`.
- Add a regression test for parameter, algorithm, measurement, and observation
  claim kinds.
- Add a deletion test that the two old placement helpers no longer exist.
- Add a source import test proving unresolved concept handles still warn or
  fail exactly as before.
- Add a source promotion test proving unresolved concept handles still fail
  before writing master artifacts.

Gate:

- `rg -n "_place_promoted_singular_concept|_place_rewritten_singular_concept" propstore tests`
  has no hits except deletion tests if needed.
- Logged source import and source promotion targeted tests pass.
- `uv run pyright propstore` passes.

## Phase 3: Typed Source-Import Claim Normalization

Goal: keep repository import normalization typed after YAML decode.

Delete-first targets:

- Delete loose claim payload rewriting from `_normalize_claim_batch` in
  `propstore/source/passes.py`.
- Delete source-import-only claim concept rewrite code that duplicates the
  shared policy from Phase 2.

Target shape:

- Decode YAML at the IO boundary.
- Convert immediately to the relevant typed document.
- Normalize to one typed `ClaimDocument`.
- Return `PlannedSemanticWrite` carrying the typed document.
- Reject aggregate canonical claim imports before typed conversion, with the
  existing hard failure.

Tests first:

- Importing one canonical claim artifact produces one planned claim write with
  the typed `ClaimDocument` document type.
- Importing aggregate `claims: [...]` still fails loudly.
- Concept-reference rewriting still updates variables, parameters,
  `target_concept`, and `concepts`.
- The local-handle ambiguity warning behavior is unchanged.

Gate:

- `rg -n "def _rewrite_claim_payload_concept_refs|def _rewrite_claim_concept_refs" propstore/source/passes.py`
  has no production hits.
- Logged repository import tests pass.
- `uv run pyright propstore` passes.

## Phase 4: Typed Source-Finalize Micropub Composition

Goal: construct source-local micropubs as typed documents without dict-stamping
boilerplate.

Delete-first targets:

- Delete `_stamp_micropub_identity(payload: dict[str, object])`.
- Delete dict-first micropub composition inside `_compose_source_micropubs`.

Target shape:

- `_compose_source_micropubs` builds typed `MicropublicationDocument` entries.
- Artifact id and version id stamping use typed micropub identity helpers.
- The returned source-local `MicropublicationsFileDocument` may remain a batch
  because it is source-local authoring state.

Tests first:

- Finalizing a source with contextual claims creates source-local micropubs with
  stable artifact ids and version ids.
- Missing claim context still fails before micropub write.
- Existing source finalize artifact-code fixtures remain stable unless the
  typed canonical payload deliberately changes.
- A deletion test proves `_stamp_micropub_identity` is gone.

Gate:

- `rg -n "_stamp_micropub_identity|payload: dict\\[str, object\\].*micropub|micropubs: list\\[dict" propstore/source/finalize.py`
  has no production hits.
- Logged source finalize and artifact-code tests pass.
- `uv run pyright propstore` passes.

## Phase 5: Typed Source-Promotion Plan Builder

Goal: replace source promotion's dict conveyor belt with a typed promotion
plan builder.

Delete-first targets:

- Delete `promoted_stances: list[dict[str, Any]]`.
- Delete `filtered_justifications_payload`.
- Delete `normalized_promoted_claims: list[JsonValue]`.
- Delete promotion-plan `JsonObject`/`JsonValue` typing from
  `propstore/source/promote.py`.
- Delete promotion-time loops that convert typed source entries to payload dicts
  only to convert them back into typed canonical documents.

Target shape:

- `propstore/source/promote.py` assembles typed promotion documents. It must not
  expose `JsonObject`, `JsonValue`, or similar payload aliases in the plan
  builder.
- The remaining claim payload normalization required by canonical claim identity
  lives behind the source claim-concept/claim-normalization helper and returns a
  typed `ClaimDocument`.
- Add typed promotion-plan assembly functions that return:
  - `dict[ClaimRef, ClaimDocument]`
  - `dict[StanceRef, StanceDocument]`
  - `dict[JustificationRef, JustificationDocument]`
  - `dict[MicropublicationRef, MicropublicationDocument]`
  - `dict[ConceptFileRef, ConceptDocument]`
- Keep all existing promotion policy:
  - blocked claims stay blocked
  - stances are promoted only when source claim and target resolve
  - justifications are promoted only when conclusion and premises resolve
  - micropubs are promoted only when all claims are valid promoted claims
  - canonical artifact-code stamping still happens before write
- Keep source-centered closure verification in Propstore.

Tests first:

- Unit tests for the typed plan builder cover valid claims, blocked claims,
  stances, justifications, micropubs, and concept promotion.
- Source promotion produces the same committed canonical artifact families as
  before for a representative source.
- Blocked-claim diagnostics and blocked sidecar behavior are unchanged.
- Artifact-code verification still detects claim, stance, and justification
  mismatches through typed family documents.
- Deletion tests prove the old dict conveyor variables are gone.

Gate:

- `rg -n "promoted_stances: list\\[dict|filtered_justifications_payload|normalized_promoted_claims|valid_justification_entries: list\\[dict" propstore/source/promote.py`
  has no hits.
- `rg -n "JsonObject|JsonValue" propstore/source/promote.py`
  has no hits.
- `rg -n "dict\\[str, Any\\]|dict\\[str, object\\]" propstore/source/promote.py`
  shows only IO-boundary or explicitly documented source-local payload use.
- Logged source promotion, source promote property, verify, build, and world
  tests pass.
- `uv run pyright propstore` passes.

## Phase 6: Shared Proposal-Promotion Transaction Skeleton

Goal: remove repeated transaction boilerplate without hiding domain policy.

Delete-first targets:

- Delete duplicated transaction loops in:
  - `promote_stance_proposals`
  - `promote_predicate_proposals`
  - `promote_rule_proposals`

Target shape:

- Add one small helper for committing a sequence of already-validated planned
  canonical artifacts in one family transaction.
- The helper must not know rule, predicate, or stance semantics.
- Rule and predicate modules still own:
  - proposal branch selection
  - item selection
  - idempotence checks
  - conflict validation
  - document construction
- Stance module still owns stance-specific already-promoted behavior and force
  semantics.

Tests first:

- Stance proposal promotion still supports selective promotion and `force`.
- Predicate proposal promotion still rejects duplicate/conflicting predicate
  declarations.
- Rule proposal promotion still rejects undeclared predicates and arity
  mismatches through the existing owner validation.
- A unit test covers the shared helper committing multiple refs atomically.
- A deletion/search test proves the repeated transaction loop body is gone from
  proposal modules.

Gate:

- Logged proposal, predicate proposal, rule proposal, and CLI proposal tests
  pass.
- `uv run pyright propstore` passes.

## Phase 7: Search, Contract, Documentation, And Full-Suite Closure

Goal: make the cleanup enforceable.

Tasks:

- Add or update architecture tests preventing reintroduction of the deleted
  duplicated source rewrite helpers.
- Document the source-local batch versus typed promotion-plan boundary if docs
  currently imply source promotion is payload-dict based.
- Run final search gates.
- Run package Pyright.
- Run the full logged pytest suite.
- Ensure tracked git status is clean.

Final gates:

- `rg -n "_place_promoted_singular_concept|_place_rewritten_singular_concept|_stamp_micropub_identity" propstore tests`
  has no production hits.
- `rg -n "promoted_stances: list\\[dict|filtered_justifications_payload|normalized_promoted_claims|valid_justification_entries: list\\[dict" propstore/source/promote.py`
  has no hits.
- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label typed-source-promotion-cleanup-final`
- `git status --short --untracked-files=no` is clean.

## Definition Of Done

This workstream is complete only when:

- Source import and source promotion share one claim concept-reference rewrite
  policy.
- Source import converts decoded YAML into typed documents before semantic
  pipeline work continues.
- Source finalize builds micropub entries as typed documents.
- Source promotion builds canonical claim, stance, justification, micropub,
  concept, and source documents through a typed promotion plan.
- Proposal promotion uses a shared transaction skeleton only after owner modules
  have built and validated typed planned artifacts.
- No generic CRUD wrapper has been added around rule, predicate, form, context,
  or concept owner workflows.
- Source-local batch files remain source-local and do not define canonical
  identity.
- Full Pyright and full logged pytest pass.
