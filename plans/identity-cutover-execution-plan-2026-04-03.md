# Identity Cutover Execution Plan

**Date:** 2026-04-03
**Depends on:** `proposals/identity-architecture-plan-2026-04-03.md`
**Scope:** full clean-break execution roadmap for propstore identity replacement
**Status:** Draft

---

## Goal

Replace propstore's current raw-local-ID model with a literature-backed identity architecture built around:

1. `artifact_id`
2. namespaced `logical_id`
3. `version_id`
4. explicit identity relations

This is a clean break.

It is **not**:

- a migration architecture
- a dual-stack period
- a compatibility shim
- a flag-gated old/new semantic split

The repository should end this plan with one identity model, not two.
The old repository should be deleted after the new canonical repository is validated.

---

## Non-Negotiable Rules

1. There is no compatibility layer.
2. There is no long-lived mixed semantic period.
3. Raw local YAML `id` stops being the storage identity key.
4. `artifact_id` becomes the durable storage key for first-class objects.
5. Imported source-local handles survive only as namespaced `logical_id`s.
6. `version_id` is immutable and content-derived.
7. Cross-source sameness is never assumed by default.
8. Identity collapse is explicit, reviewable, and relation-based.
9. Every slice must leave the repo in a coherent measurable state.
10. We work one target surface at a time until it is finished.

---

## User-Facing Outcome

This plan is not complete until user-visible identity behavior is settled.

### Default UX

Users should usually see:

- a short label or statement excerpt
- one stable human-facing `logical_id`

Users should **not** usually see:

- raw UUID-like `artifact_id`
- raw `version_id`

### Advanced UX

Detailed inspect/provenance/debug views should show:

- `logical_id`
- `artifact_id`
- `version_id`
- provenance
- identity relations such as:
  - `same_as_candidate`
  - `same_as_in_context`
  - `supersedes`
  - `version_of`

### Examples

Normal claim display:

- `Aarts_2015:claim1`
- `Replication rate in sampled psychology studies is ...`

Detailed claim display:

- `Logical ID: Aarts_2015:claim1`
- `Artifact ID: ps:claim:01JZ...`
- `Version ID: sha256:...`
- `Source: Aarts_2015_EstimatingReproducibilityPsychologicalScience`

### UX Rule

`logical_id` is the everyday handle.

`artifact_id` is the durable internal anchor.

`version_id` is the immutable provenance/debug anchor.

---

## Current Problems To Eliminate

1. imported papers reuse local IDs like `claim1`
2. merge logic keys on raw local claim IDs
3. different IDs for the same semantics never meet
4. non-claim references break when IDs are rewritten or disambiguated
5. concepts and related first-class objects lack durable object identity
6. users currently have no coherent identity story across import, merge, inspection, and reconciliation

---

## Identity Contract

### `artifact_id`

Required on every durable first-class object:

- claims
- concepts
- justifications / rules
- stance records if persisted as first-class objects
- contexts
- worldlines
- source/paper records

Properties:

- globally unique inside propstore
- durable across import, branch, merge, and canonical repository lifetime
- opaque
- never reused

### `logical_id`

Required whenever an object has a source-facing or user-facing handle.

Properties:

- namespaced
- human-usable
- may have multiple entries per object
- old raw local IDs survive only here, never as storage identity

### `version_id`

Required on every first-class object whose content can change.

Properties:

- immutable
- derived from canonical content
- changes whenever canonical content changes
- suitable for verification and deduplication

### Identity Relations

Initial required relation vocabulary:

- `same_as_candidate`
- `same_as_in_context`
- `supersedes`
- `derived_from`
- `version_of`
- `duplicate_artifact_of`
- `source_asserts_same_as`

---

## Execution Order

This order is strict.

1. identity schema contract
2. canonical serialization and `version_id`
3. new canonical repository bootstrap
4. claim cutover
5. claim reference cutover
6. concept cutover
7. import cutover
8. merge cutover
9. relation-object cutover
10. reconciliation/query/UX surfaces
11. final deletion of obsolete identity code and old repository

No later step is allowed to depend on old identity semantics surviving.

---

## Step 1: Identity Schema Contract

Primary files:

- schema files under `schema/`
- packaged schemas under `propstore/_resources/schemas/`
- validators that enforce first-class object structure

Tasks:

1. Define required fields for each first-class object kind:
   - `artifact_id`
   - `logical_ids`
   - `version_id`
   - identity relation surface where applicable
2. Decide exact field names and cardinalities.
3. Define which objects are first-class now vs deferred.
4. Remove schema assumptions that raw local `id` is the durable storage key.

Acceptance:

- one written schema contract exists
- no schema ambiguity remains on whether `id` means local handle or durable identity

---

## Step 2: Canonical Serialization And `version_id`

Primary files:

- serializers / validators
- merge/import code that computes object sameness or change

Tasks:

1. Define canonical content for each object kind.
2. Define which fields are inside `version_id` and which are excluded.
3. Ensure provenance treatment is explicit:
   - included when it changes object identity
   - excluded when it is only storage metadata
4. Implement deterministic serialization for hashing.

Acceptance:

- the same semantic object serializes identically across machines
- `version_id` behavior is fully specified

---

## Step 3: New Canonical Repository Bootstrap

Primary files:

- repository bootstrap/init surfaces
- import/bootstrap tooling
- docs specifying canonical repository location/contract

Tasks:

1. Create a new canonical repository under the new identity schema.
2. Decide what content is imported or regenerated into it.
3. Ensure no part of the old repository remains canonical after bootstrap.
4. Treat the old repository as disposable once validation is complete.

Acceptance:

- a new canonical repository exists under the new identity model
- no in-place conversion of the old repository is required

---

## Step 4: Claim Cutover

This is the first mandatory target surface.

Primary files:

- claim schema
- claim validators
- claim load/store helpers
- merge/import code touching claims

Tasks:

1. Add `artifact_id`, `logical_ids`, and `version_id` to claims.
2. Stop treating raw local `id` as the claim identity key.
3. Decide whether raw `id` survives at all or is subsumed into `logical_ids`.
4. Rewrite claim indexing and lookup APIs around durable identity.

Acceptance:

- claims have one durable object identity surface
- raw local IDs no longer drive merge behavior

---

## Step 5: Claim Reference Cutover

Primary files:

- inline claim stance handling
- stance file handling
- any cross-claim references in loaders/validators/CLI

Tasks:

1. Rewrite cross-claim references to target durable identities.
2. Preserve source-facing handles only as display or import metadata.
3. Ensure merge-time disambiguation no longer breaks targets.
4. Add a single normalized reference contract.

Acceptance:

- no claim relation points at unstable raw local IDs
- no merge path can create dangling references through ID rewriting

---

## Step 6: Concept Cutover

Primary files:

- concept schema
- concept validators
- concept CLI and helper functions
- import and merge surfaces touching concepts

Tasks:

1. Add `artifact_id`, `logical_ids`, and `version_id` to concepts.
2. Stop relying on filename and local `conceptN` as durable identity.
3. Separate aliases from identity.
4. Normalize concept references from claims and parameterizations.

Acceptance:

- concept identity is no longer filename-driven
- alias handling no longer masquerades as identity

---

## Step 7: Import Cutover

Primary files:

- `propstore/repo/repo_import.py`
- paper import flows
- any import-adjacent rewriting helpers

Tasks:

1. Replace raw overlay import with identity-aware import.
2. Mint `artifact_id` for imported first-class objects.
3. Derive namespaced `logical_id` from source handles.
4. Derive `version_id` from canonical content.
5. Rewrite internal references during import.
6. Apply deletes so import is a true snapshot replacement.

Namespace priority:

1. stable paper slug
2. source repo slug
3. explicit external namespace if present

Acceptance:

- imported `claim1` never enters the repo as an unscoped storage identity
- repeated imports converge by snapshot semantics, not overlay accumulation

---

## Step 8: Merge Cutover

Primary files:

- `propstore/repo/merge_classifier.py`
- `propstore/repo/merge_commit.py`
- `propstore/repo/merge_report.py`
- structured merge consumers as needed

Tasks:

1. Stop keying merge on raw local IDs.
2. Define exact precedence of merge surfaces:
   - same `artifact_id`
   - same `logical_id`
   - same semantic candidate
   - contradiction without identity
3. Preserve noncommitment:
   - no silent cross-source collapse
   - explicit relation output where identity is candidate-level only
4. Rewrite storage merge materialization accordingly.

Acceptance:

- unrelated local `claim1`s do not collide
- same-semantic but differently named claims can be surfaced as candidates without forced fusion

---

## Step 9: Relation-Object Cutover

Primary files:

- stance storage and helpers
- any other persisted relation objects

Tasks:

1. Decide which relations become first-class objects.
2. Give first-class persisted relation objects their own `artifact_id`.
3. Normalize their targets around durable object identity.
4. Remove storage assumptions that relations are just weak inline decorations.

Acceptance:

- persisted relation surfaces are identity-safe

---

## Step 10: Reconciliation And UX Surfaces

Primary files:

- CLI inspect/show/query commands
- merge/report surfaces
- future UI/report docs

Tasks:

1. Make `logical_id` the default visible handle.
2. Make `artifact_id` and `version_id` visible only in detailed/provenance/debug contexts.
3. Add side-by-side reconciliation views for candidate identity.
4. Add explicit rendering of identity relations.
5. Ensure user-facing outputs never require UUID literacy for ordinary work.

Acceptance:

- a user can work effectively using `logical_id`
- detailed identity internals are still available when needed

---

## Step 11: Deletion Pass

Primary files:

- all remaining identity helpers, validators, and merge/import code tied to old semantics

Tasks:

1. Remove obsolete raw-local-ID identity assumptions.
2. Remove dead helper code and fallback branches.
3. Remove any documentation that describes the old identity model as live.
4. Delete the old repository after the new canonical repository is validated.
5. Verify there is exactly one identity architecture left.

Acceptance:

- old identity semantics are gone from production code

---

## Testing Discipline

Every substantial slice must:

1. write RED tests first
2. make the smallest GREEN change
3. run targeted tests as `uv run pytest -vv`
4. tee output to `logs/test-runs/`
5. reread this plan before selecting the next slice
6. keep work on exactly one target surface until that surface is finished

---

## Required UX Decisions Before Coding Reaches Step 9

These must be settled early, not improvised late:

1. format of generated `artifact_id`
2. format of generated propstore-native `logical_id`
3. whether legacy raw `id` remains as a field at all
4. CLI default display shape for claims and concepts
5. inspect/debug display shape for identity details

Recommended default:

- claim list/show:
  - short label
  - `logical_id`
- claim inspect:
  - `logical_id`
  - `artifact_id`
  - `version_id`
  - provenance
  - identity relations

---

## Completion Criteria

This plan is complete only when:

1. first-class objects have the new identity surfaces
2. import and merge no longer depend on raw local IDs
3. references no longer break under ID rewriting or merge
4. user-facing claim/concept handling is coherent and stable
5. obsolete identity code is deleted
6. the old repository is deleted
7. there is no compatibility path left in production

---

## Immediate Next Slice

Start with the claim surface only.

Specifically:

1. finalize claim identity schema
2. define canonical claim serialization for `version_id`
3. define bootstrap rules for claims entering the new canonical repository
4. define claim reference target contract

Do not widen to concepts or UX implementation until the claim surface is closed.
