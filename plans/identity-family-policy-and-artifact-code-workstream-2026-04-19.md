# Identity Family Policy And Artifact Code Workstream

Date: 2026-04-19

## Goal

Make Propstore identity a first-class semantic family concern without moving
Propstore domain semantics into Quire.

This workstream replaces the top-level `propstore.identity` grab bag with
family-owned identity policy. It also separates durable object identity from
artifact-code verification so `artifact_id`, `logical_ids`, `version_id`, and
`artifact_code` do not continue to look like one layer.

This is a direct cutover. We control both sides of the interface, so there are
no compatibility shims, import aliases, fallback readers, old/new dual paths,
or long-lived transition surfaces.

## Current Problems

- `propstore.identity` mixes unrelated layers:
  - logical-id grammar and formatting
  - claim/concept artifact-id derivation
  - claim/concept content-version hashing
  - claim-file import normalization and stance target rewriting
  - concept lexical-entry and ontology-reference scaffolding
- `propstore.families.registry` declares document families, placement, import
  metadata, and foreign keys, but identity policy is still computed by callers
  that import `propstore.identity`.
- Claim and concept document schemas carry `artifact_id`, `logical_ids`, and
  `version_id`, but the family definitions do not declare how those fields are
  derived, normalized, or verified.
- Source finalize and promote workflows use `propstore.artifact_codes`, which
  computes verification hashes over a source-centered claim tree. That is not
  the same as single-document content identity.
- Deterministic JSON SHA-256 hashing is reimplemented in multiple places:
  `propstore.identity`, `propstore.artifact_codes`, and source/micropub
  helpers.
- Several downstream systems depend on identity but import it indirectly:
  compiler passes, sidecar builders, source workflows, concept CLI commands,
  merge reporting, and validation.

## Target Architecture

Propstore owns semantic identity. Quire owns only generic document-family
infrastructure and schema-blind deterministic hashing.

The target boundary is:

```text
propstore family identity policy
        |
        v
propstore family registry and document callbacks
        |
        v
quire DocumentFamilyStore / deterministic hash helpers
```

`propstore.families` becomes the identity control surface for Propstore
semantic families.

Each identity-bearing family declares:

- stable family name
- document type
- placement
- import participation
- foreign keys
- content identity policy, where applicable
- import normalization policy, where applicable
- reference rewrite policy, where applicable
- verification policy only when the verification is local to that family

Cross-family verification stays outside generic family identity policy.

## Identity Surfaces

Propstore must keep these identities distinct:

- `artifact_id`: durable object identity for a first-class Propstore object.
- `logical_ids`: namespaced source/user-facing handles for that object.
- `version_id`: immutable content identity for one canonical document payload.
- `artifact_code`: verification/provenance code over a source-centered closure
  of source, claim, justification, stance, and origin evidence.

Only the first three belong to per-family content identity policy.

`artifact_code` remains a Propstore verification surface. It is intentionally
not a generic Quire artifact-family identity.

## Propstore Module Shape

Delete `propstore.identity` as a production module.

Move logical-id primitives to a Propstore-owned family identity module:

- `propstore.families.identity.logical_ids`
- `LogicalId` formatting helpers
- namespace/value normalization
- claim/concept artifact-id regexes
- `parse_claim_id`
- `format_logical_id`
- primary logical-id helpers

Move claim identity to claim-owned modules:

- claim artifact-id derivation
- claim canonical payload construction
- claim `version_id` computation
- claim-file ingest normalization
- local claim-handle to artifact-id mapping
- in-file stance target rewriting

Move concept identity to concept-owned modules:

- concept artifact-id derivation
- concept canonical payload construction
- concept `version_id` computation
- canonical concept payload normalization
- lexical-entry scaffolding
- ontology-reference scaffolding
- `propstore` logical-handle preservation
- concept reference-key enumeration

Keep source, promotion, and verification code in Propstore workflow modules:

- source claim normalization remains source-owned.
- source concept promotion remains source-owned.
- source finalize and promote continue to call Propstore artifact-code
  composers.
- sidecar blocked-claim mirror rows remain sidecar/source workflow behavior.

## Quire Infrastructure

Quire should provide only generic primitives:

- A deterministic payload hashing helper:
  - sorted keys
  - compact JSON separators
  - UTF-8 bytes
  - `ensure_ascii=False`
  - `sha256:<hex>` output
- A schema-blind canonical JSON byte encoder reusable by Propstore identity and
  artifact-code code.
- Optional typed handle helpers such as a generic `LogicalHandle(namespace,
  value)` if this does not import Propstore naming rules.
- Optional single-document content identity hooks on `ArtifactFamily` or a
  sibling declaration type, but only for local document identity:
  - canonical payload for one document
  - content `version_id` for one document
  - optional artifact-id derivation from a caller-supplied handle

Quire must not provide:

- claim/concept normalization
- stance target rewriting
- concept lexical-entry scaffolding
- source finalize or promote semantics
- source-origin file lookup
- sidecar writes
- ATMS/world verification
- artifact-code tree walking
- any knowledge of `ps:claim:` or `ps:concept:` URI conventions

If the optional Quire content identity hooks force Quire to understand
cross-family relationships, skip those hooks and keep the family identity
policy entirely in Propstore.

## Artifact Codes

`propstore.artifact_codes` is not durable identity. It is verification over a
source-centered evidence closure.

Keep these composers in Propstore:

- `source_artifact_code`
- `justification_artifact_code`
- `stance_artifact_code`
- `claim_artifact_code`
- `attach_source_artifact_codes`
- `verify_claim_tree`

Only the schema-blind hash helper under those functions should move to Quire.

The following semantics must remain Propstore-owned:

- justifications are indexed by `conclusion`
- justification premises are sorted before hashing
- stances are indexed by `source_claim`
- claim artifact codes include source, justification, and stance codes
- source origin verification looks for paper bytes using Propstore repository
  conventions
- verification may consult the sidecar and `WorldModel`
- promote recomputes artifact codes after filtering blocked claims,
  justifications, stances, and concept rewrites

## Tests First

Add failing tests before implementation:

1. `propstore.identity` is absent as an importable production module.
2. Claim identity functions are reachable only through claim family identity
   modules or the claim family policy.
3. Concept identity functions are reachable only through concept family identity
   modules or the concept family policy.
4. `PROPSTORE_FAMILY_REGISTRY` exposes identity policy metadata for claims and
   concepts.
5. Claim and concept family contracts include stable identity callback
   identifiers or stable Propstore identity policy contract bodies.
6. Fixed claim and concept payload fixtures keep exact existing `version_id`
   outputs.
7. Existing source finalize artifact-code fixtures keep exact existing
   `artifact_code` outputs.
8. `artifact_code` composers do not move to Quire and do not appear as Quire
   artifact-family identity hooks.
9. Source finalize and promote still recompute artifact codes through
   Propstore-owned composers.
10. Sidecar claim/concept utilities no longer import from `propstore.identity`.
11. Compiler, validation, merge, CLI, and source workflows no longer import from
   `propstore.identity`.
12. Quire tests cover deterministic hash helper behavior independently of
   Propstore.

Golden tests must pin byte-equivalent behavior for:

- claim canonical payload hashing
- concept canonical payload hashing
- claim artifact-code roll-up with sorted justification and stance codes
- source artifact-code stripping of existing `artifact_code`
- concept logical-id preservation of the `propstore` handle

## Execution Phases

### Phase 1: Quire Hash Primitive

- Add a schema-blind deterministic JSON hash helper to Quire.
- Add Quire tests for stable ordering, compact encoding, Unicode behavior, and
  `sha256:<hex>` formatting.
- Replace only duplicated schema-blind hash implementations in Propstore with
  the Quire helper.
- Do not move Propstore composers or canonicalizers.

### Phase 2: Propstore Identity Types

- Add Propstore-owned family identity modules for logical IDs and content IDs.
- Move logical-id grammar, formatting, and normalization out of
  `propstore.identity`.
- Update every caller of logical-id helpers.
- Delete the old logical-id functions from `propstore.identity` rather than
  re-exporting them.

### Phase 3: Claim Family Identity

- Move claim artifact-id derivation, canonicalization, and `version_id`
  computation into claim-owned identity code.
- Move claim-file import normalization and stance target rewriting into
  claim-family import policy code.
- Wire the claim family declaration to the claim identity policy.
- Update compiler, sidecar, validation, source, merge, demo, and CLI callers.
- Keep exact hash outputs unchanged.

### Phase 4: Concept Family Identity

- Move concept artifact-id derivation, canonicalization, and `version_id`
  computation into concept-owned identity code.
- Move canonical concept payload normalization into concept-family policy code.
- Preserve lexical-entry scaffolding, ontology-reference scaffolding, and
  `propstore` logical handle behavior.
- Wire the concept family declaration to the concept identity policy.
- Update concept CLI, source alignment, source promotion, validation, sidecar,
  demo, and tests.
- Keep exact hash outputs unchanged.

### Phase 5: Registry And Contracts

- Extend Propstore family contract bodies to include identity policy facts and
  stable callback identifiers.
- Bump family contract versions for changed family bodies.
- Regenerate the checked-in semantic contract manifest only after tests prove
  the new body shape.
- Ensure identity policy is discoverable from the family registry, not from a
  standalone global module.

### Phase 6: Artifact-Code Boundary

- Rename or document `propstore.artifact_codes` as verification/provenance
  code, not durable identity.
- Keep artifact-code composers in Propstore.
- Make source finalize and promote use the shared Quire hash primitive only for
  the schema-blind hash operation.
- Add architectural tests that prevent artifact-code composers from moving into
  Quire or into single-document family identity hooks.

### Phase 7: Delete `propstore.identity`

- Remove the module.
- Use search failures as the work queue.
- Update all production and test imports to the new family-owned surfaces.
- Add an architectural test that `importlib.util.find_spec("propstore.identity")`
  is `None`.

### Phase 8: Verification

Run Quire tests:

- `uv run pytest tests`

Run Propstore targeted tests through the logged wrapper:

- `powershell -File scripts/run_logged_pytest.ps1 -Label identity-family tests/test_artifact_identity_policy.py tests/test_verify_cli.py tests/test_semantic_family_registry.py`
- Add any new identity-family tests to this command as they are created.

Run broader Propstore checks through the logged wrapper:

- source finalize/promote tests
- compiler/sidecar tests that cover claim and concept identity
- full logged suite

## Definition Of Done

- `propstore.identity` is deleted.
- Claim identity is owned by the claim family surface.
- Concept identity is owned by the concept family surface.
- Logical-id grammar and formatting are owned by Propstore family identity
  modules.
- The family registry exposes identity policy facts for identity-bearing
  families.
- Contract manifests include identity policy facts and remain current.
- Quire provides only schema-blind deterministic hashing and optional
  single-document identity plumbing.
- Quire does not import Propstore and does not know Propstore semantic fields.
- `artifact_code` composers remain in Propstore and are clearly separate from
  `artifact_id`, `logical_ids`, and `version_id`.
- Source finalize and promote preserve existing artifact-code behavior.
- Golden tests prove hash stability for claim and concept `version_id`.
- Golden tests prove artifact-code stability.
- All production imports of `propstore.identity` are gone.
- Targeted tests pass through the logged pytest wrapper.
- The full logged suite is attempted.

## Stop Conditions

Stop and reassess if:

- Quire needs to import Propstore.
- Quire identity hooks require claim, concept, stance, source, sidecar, or
  artifact-code semantics.
- Moving identity code changes existing claim or concept `version_id` outputs
  without an explicit decision to re-key stored data.
- Moving hash helpers changes existing artifact-code outputs.
- Artifact-code verification starts depending on generic Quire family identity.
- Source promotion cannot recompute artifact codes after filtering and concept
  rewrites under the new structure.
