# Semantic Artifact Family Cutover Workstream

Date: 2026-05-11

## Goal

Make canonical Propstore storage represent semantic artifacts, not aggregate
authoring files.

Source-local authoring may remain batch-shaped. Canonical/master artifacts must
be artifact-shaped:

- one claim artifact
- one stance artifact
- one justification artifact
- one micropublication artifact
- one same-as assertion artifact
- one rule artifact if rules require independent identity

This is a direct cutover. We control the stack, so do not preserve old and new
canonical storage paths in parallel. If a current canonical family stores many
semantic objects inside one file, delete that production surface for the family
being cut over and update every caller to the new artifact family.

## Why This Workstream Exists

Propstore currently has several "file document" families whose storage unit does
not match the semantic artifact unit. The result is that identity, verification,
sidecar compilation, and proposal promotion have to reason about entries inside
bucket files.

The clearest case is stances:

- `SourceStancesDocument` is a source-local batch containing many source stance
  entries.
- `StanceFileDocument` is a canonical/proposal bucket keyed by `source_claim`.
- `StanceEntryDocument` is the actual semantic edge.
- `artifact_code` is stamped on entries inside the bucket.
- Runtime sidecar compilation flattens the bucket into `relation_edge` rows.

That means the canonical family artifact is the bucket, while the semantic
artifact is an entry in the bucket. The same pattern appears in other families.

This workstream makes that mismatch impossible in canonical storage.

## Current Aggregate Surfaces

### Source-Local Authoring Batches

These may remain batch-shaped because their job is authoring, ingestion, and
paper/source review:

- `claims.yaml` as `SourceClaimsDocument`
- `justifications.yaml` as `SourceJustificationsDocument`
- `stances.yaml` as `SourceStancesDocument`
- source concepts and source micropubs where they are source-branch working
  state

These are source subsystem state, not canonical semantic identity.

### Canonical Or Proposal Aggregates To Remove

These are suspect because they are canonical/proposal family artifacts that hold
many semantic entries:

- `ClaimsFileDocument` with `claims: tuple[ClaimDocument, ...]`
- `StanceFileDocument` with `stances: tuple[StanceEntryDocument, ...]`
- `SourceJustificationsDocument` reused as canonical `JUSTIFICATIONS_FILE_FAMILY`
- `MicropublicationsFileDocument` with many `MicropublicationDocument` entries
- `SameAsFileDocument` with many `SameAsAssertionDocument` entries
- `RulesFileDocument` if individual rules need independent identity

Some files may represent intentional sets. Each case must be decided by the
semantic unit, not by current YAML layout.

## Target Architecture

### 1. Source Batches Are Not Canonical Artifacts

Source-local files are authoring inputs and source-branch working state. They
may group related objects for human review and ingestion efficiency.

Promotion/finalize converts source batch entries into canonical semantic
artifacts. It must not carry the source batch shape forward into master.

### 2. Canonical Families Store Semantic Artifacts

Each canonical semantic unit gets its own family document and ref:

- `ClaimDocument` under a claim artifact ref
- `StanceDocument` under a stance artifact ref
- `JustificationDocument` under a justification artifact ref
- `MicropublicationDocument` under a micropub artifact ref
- `SameAsAssertionDocument` under a same-as assertion artifact ref

The family artifact is the semantic artifact.

### 3. Quire Provides Generic Artifact Machinery

Quire should provide generic, schema-blind artifact identity infrastructure:

- typed document coerce/render/payload through `ArtifactFamily`
- canonical JSON encoding and hashing
- optional family identity policy hooks
- field exclusion from local identity payloads
- optional document stamping/rebuilding hook

Quire must not know Propstore semantics:

- no `ps:claim:` or `ps:concept:` grammar
- no stance target rules
- no source finalize or promote semantics
- no sidecar or worldline behavior
- no claim/justification/stance closure verification

### 4. Propstore Families Own Semantic Identity

Propstore declares family-specific identity:

- artifact id derivation
- version id derivation
- canonical payload construction
- excluded fields
- logical id fields
- source-local-only fields
- cross-family references

Identity and canonical payload functions live beside the document model or in a
close family identity module. They must accept typed family documents, not loose
payload dictionaries.

### 5. Sidecar Compiles From Semantic Artifacts

Sidecar builders iterate canonical semantic artifact families directly:

- claim artifacts produce `claim_core`
- stance artifacts produce `relation_edge`
- justification artifacts produce `justification`
- micropub artifacts produce micropub rows

No canonical path should open an aggregate bucket only to flatten entries.

## Non-Goals

- Do not redesign source-local paper authoring formats unless needed for the
  canonical cutover.
- Do not preserve compatibility with old canonical aggregate files unless the
  user explicitly creates an old-repo compatibility requirement.
- Do not add fallback readers for old and new master layouts.
- Do not hide aggregate entries behind `JsonObject` or `dict[str, Any]`.
- Do not create per-family wrapper aliases around old aggregate helpers.
- Do not move Propstore semantic policy into Quire.

## Dependency Order

Execute in this order. Do not start a dependent phase until its prerequisite
phase is complete or explicitly deferred.

1. Quire identity hook assessment
2. Propstore semantic-artifact target model
3. Stance canonical cutover
4. Justification canonical cutover
5. Micropublication canonical cutover
6. Claim canonical cutover
7. Same-as assertion cutover
8. Rule/predicate decision and cutover if needed
9. Artifact-code and verification cleanup
10. Contract, manifest, and documentation closure

## Phase 1: Quire Identity Hook Assessment

Goal: decide what belongs in Quire before changing Propstore family storage.

Tasks:

- Read Quire `ArtifactFamily`, `FamilyDefinition`, `DocumentFamilyStore`, and
  document codec surfaces.
- Add a Quire design note for generic identity hooks if missing:
  - document payload provider
  - canonical payload provider
  - identity field exclusion
  - hash function
  - optional stamp/rebuild callback
- Decide whether the first Propstore cutover can use existing Quire hooks or
  needs a small Quire extension first.
- If Quire changes are needed, implement them in Quire first and pin Propstore
  only to a pushed remote commit or tag. Never pin to a local path.

Gate:

- Written decision: "existing Quire hooks are sufficient" or "Quire identity
  hook extension landed and is available from a pushed remote ref."

## Phase 2: Propstore Semantic-Artifact Target Model

Goal: define the target family model before touching production storage.

Tasks:

- Add or update typed document models for semantic units:
  - canonical `StanceDocument`
  - canonical `JustificationDocument`
  - canonical `MicropublicationDocument`
  - canonical `SameAsAssertionDocument`
  - eventual one-claim `ClaimDocument` family shape
- Add ref types for each semantic artifact:
  - `StanceRef`
  - `JustificationRef`
  - `MicropublicationRef`
  - `SameAsAssertionRef`
  - claim ref if current `ClaimsFileRef` remains file-shaped
- Define placement policies for one artifact per semantic object.
- Define identity policy for each target family.
- Define foreign keys from family documents to referenced families.
- Add red tests for registry presence and absence of aggregate canonical
  family use.

Gate:

- Target model tests fail before implementation and pass after registry/model
  declarations exist.
- No production caller has been dual-wired yet.

## Phase 3: Stance Canonical Cutover

Goal: make each canonical/proposal stance a first-class artifact.

Delete-first target:

- Delete canonical/proposal production use of `StanceFileDocument` as a bucket.
- Delete grouping-by-`source_claim` canonical promotion as production behavior.

Tasks:

- Add `StanceDocument` as the canonical stance artifact document.
- Add `StanceRef`, with identity derived from stance semantic content or an
  explicit durable stance artifact id.
- Replace `STANCE_FILE_FAMILY` with a one-stance artifact family.
- Replace `PROPOSAL_STANCE_FAMILY` with one proposal artifact per stance.
- Keep `SourceStancesDocument` only as source-local batch input.
- Update `source.promote` to promote every source stance entry to one canonical
  stance artifact.
- Update source finalize artifact-code stamping to stamp source-local stance
  entries without creating canonical buckets.
- Update proposal commit/promotion to write and promote individual stance
  artifacts.
- Update sidecar compilation to iterate stance artifacts directly.
- Update worldline stance dependency keys to use stance artifact identity where
  available.
- Delete bucket-specific naming helpers such as proposal filename by
  `source_claim` unless retained only for source-local batch import.

Tests first:

- Canonical stance family stores one stance per artifact.
- No `StanceFileDocument` is used by canonical/proposal production paths.
- Source `stances.yaml` batch import still writes source-local state.
- Promotion of a source with N stances creates N canonical stance artifacts.
- Proposal classification creates one proposal artifact per stance.
- Sidecar relation rows are unchanged for an equivalent input.
- World/ASPIC/PRAF stance behavior remains unchanged.

Gate:

- `rg -n "StanceFileDocument|StanceFileRef" propstore` shows no canonical or
  proposal production use. Source-local tests or deleted compatibility tests
  may be updated accordingly.
- `uv run pyright propstore` passes.
- Logged targeted tests for source relations, proposals, sidecar, world query,
  ASPIC bridge, and worldline argumentation pass.

## Phase 4: Justification Canonical Cutover

Goal: make every canonical justification a first-class artifact.

Tasks:

- Add canonical `JustificationDocument` and `JustificationRef`.
- Stop using `SourceJustificationsDocument` as canonical
  `JUSTIFICATIONS_FILE_FAMILY`.
- Keep `SourceJustificationsDocument` as source-local batch state.
- Promote each source justification entry to one canonical justification
  artifact.
- Update artifact-code verification to load justification artifacts directly.
- Update sidecar compilation and ASPIC extraction to iterate justification
  artifacts directly.
- Define canonical identity:
  - conclusion claim
  - premises, sorted only if order is semantically irrelevant
  - rule kind and strength
  - attack target
  - provenance fields if they are identity-relevant

Tests first:

- Promotion of N valid justifications creates N canonical justification
  artifacts.
- Invalid/blocked justifications remain source-local and do not create
  canonical artifacts.
- Premise-order identity behavior is explicitly tested.
- ASPIC and sidecar justification behavior remains unchanged.

Gate:

- No canonical production path stores justification entries inside a file
  aggregate.
- Pyright and targeted logged tests pass.

## Phase 5: Micropublication Canonical Cutover

Goal: make each micropublication a first-class artifact.

Tasks:

- Add `MicropublicationRef` and one-micropub canonical family if absent.
- Stop using `MicropublicationsFileDocument` as canonical storage.
- Keep source-local composition as a batch operation if useful.
- Finalize writes individual micropub artifacts.
- Sidecar/runtime readers iterate micropub artifacts directly.
- Identity remains based on micropub semantic payload, not file position.

Tests first:

- Source finalize creating N micropubs creates N micropub artifacts.
- Existing micropub artifact id/version fixtures remain stable unless the
  target identity intentionally changes.
- No canonical micropub aggregate file remains in production.

Gate:

- Pyright and targeted micropub/source finalize tests pass.

## Phase 6: Claim Canonical Cutover

Goal: make each canonical claim a first-class artifact.

This is the highest-blast-radius phase and must run after smaller relation
families prove the pattern.

Tasks:

- Replace `ClaimsFileDocument` as canonical storage with one claim artifact per
  claim.
- Keep source-local `SourceClaimsDocument` or paper `claims.yaml` as authoring
  batch input only.
- Define claim family placement by durable `artifact_id`.
- Keep `logical_ids`, `artifact_id`, and `version_id` semantics explicit.
- Update compiler, sidecar, merge, world model, validation, concept views, and
  source promotion to iterate claim artifacts directly.
- Delete claim-file iteration as canonical production path.

Tests first:

- Repository import writes one claim artifact per claim.
- Source promotion writes one claim artifact per promoted source claim.
- Claim version identity fixtures remain stable unless intentionally changed.
- Existing world query behavior remains unchanged.

Gate:

- No canonical production path depends on `ClaimsFileDocument` as a storage
  bucket.
- Full package Pyright passes.
- Broad logged source/compiler/sidecar/world tests pass.

## Phase 7: Same-As Assertion Cutover

Goal: decide and implement whether each same-as assertion is an artifact.

Tasks:

- Determine whether `SameAsFileDocument` represents an intentional assertion
  set or accidental aggregate storage.
- If accidental, add `SameAsAssertionRef` and canonical assertion family.
- Update import, sidecar, and validation to iterate assertion artifacts.
- Delete aggregate canonical storage path.

Gate:

- Written decision plus implementation if cutover is required.

## Phase 8: Rule And Predicate Decision

Goal: decide whether rule and predicate files are intentional sets or accidental
aggregates.

Tasks:

- For rules, determine whether individual `RuleDocument`s need independent
  identity, promotion, validation, or provenance.
- For predicates, determine whether declarations are a schema file or
  independent semantic artifacts.
- If a family is an intentional set, document the reason in the family
  registry contract metadata.
- If a family is accidental aggregate storage, cut it over like stances and
  justifications.

Gate:

- Every remaining aggregate family has an explicit decision: intentional set or
  cut over.

## Phase 9: Artifact-Code And Verification Cleanup

Goal: remove loose payload mutation and align artifact-code verification with
semantic artifacts.

Tasks:

- Delete `attach_source_artifact_codes` as a dict-mutating API.
- Replace it with typed source finalize/promotion operations.
- Ensure source-local artifact-code stamping uses typed source documents.
- Ensure canonical verification loads first-class artifacts directly:
  - source artifact
  - claim artifacts
  - justification artifacts
  - stance artifacts
- Keep source-centered claim-tree verification in Propstore, not Quire.
- Keep canonical JSON/hash primitives generic in Quire.

Tests first:

- Source finalize artifact-code fixtures remain stable unless deliberately
  changed.
- Verification detects claim/stance/justification mismatches through the new
  family storage.
- No production artifact-code function accepts `dict[str, Any]`,
  `dict[str, object]`, or raw `JsonObject` when a typed document exists.

Gate:

- `rg -n "attach_source_artifact_codes|dict\\[str, Any\\]|dict\\[str, object\\]" propstore/artifact_codes.py propstore/source`
  shows no production loose-payload artifact-code path.
- Pyright and targeted verification tests pass.

## Phase 10: Contracts, Manifest, And Docs

Goal: make the new family architecture enforceable.

Tasks:

- Update semantic family contracts.
- Update checked-in contract manifests with required version bumps.
- Document source-local batch families versus canonical semantic artifact
  families.
- Add tests that prevent accidental reintroduction of aggregate canonical
  artifacts.
- Update CLI/help text where user-visible paths change.

Gate:

- Contract manifest tests pass.
- Full relevant test suite passes.
- Documentation clearly states that source-local batches are not canonical
  artifact identity.

## Definition Of Done

The workstream is complete only when:

- Every canonical semantic family stores one semantic artifact per family
  artifact, or has an explicit documented "intentional set" decision.
- Source-local batch files remain source-local and do not define canonical
  identity.
- Sidecar compilation reads semantic artifacts directly.
- Artifact-code and version-id functions operate on typed family documents.
- Quire owns only generic artifact/document/hash mechanics.
- Propstore owns semantic identity and cross-family verification.
- No production path stamps artifact codes into entries hidden inside canonical
  aggregate bucket files.

## Execution Rules

- Work one family at a time.
- Start with stances.
- Delete the old production surface first for the family being cut over.
- Use compiler, Pyright, tests, and search failures as the work queue.
- Do not preserve old and new canonical layouts in parallel.
- Do not introduce fallback readers unless the user explicitly creates an old
  repository compatibility requirement.
- Do not commit generated diagnostics unless explicitly requested.
- Use logged pytest wrappers for tests.

## Expected Targeted Test Gates

Run focused gates after each family slice:

- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label stance-cutover tests/test_source_relations.py tests/test_promote_stance_proposals_idempotency.py tests/test_plan_stance_proposal_promotion_typo_path.py tests/test_world_query.py tests/test_ws_f_aspic_bridge.py`
- `powershell -File scripts/run_logged_pytest.ps1 -Label artifact-code tests/test_verify_cli.py tests/test_source_promote_properties.py`
- Add or adjust family-specific gates as cutovers move to claims,
  justifications, micropubs, same-as, and rules.

Full-suite runs are required before declaring the entire workstream complete.

## Open Design Questions

- Should Quire support aggregate-entry artifact families, or should Propstore
  canonical storage use one physical file per semantic artifact?
- For stance identity, should the durable `artifact_id` be derived from semantic
  content, from a logical handle, or from source-local provenance plus target?
- Which stance fields are identity-relevant versus metadata?
- Are `RulesFileDocument` and `PredicatesFileDocument` intentional sets?
- Should artifact-code verification remain source-centered after canonical
  claim/stance/justification storage becomes artifact-shaped, or should it be
  split into per-artifact verification plus source-closure verification?

