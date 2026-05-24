# Family Document And Relationship Protocol Workstream

Date: 2026-05-24

## Why This Exists

The derived-build deletion exposed another duplicated surface: family document
field lists and cross-family verification code are still hand-authored outside
the family charter.

The target is not to remove documents. Every family still has a document. The
target is to remove duplicate document definitions. A family document is
generated on demand from the family charter:

```python
family.document()
```

or the equivalent Quire family API. The document fields come from charter
fields marked as document fields. Document inclusion should be the default
unless the charter explicitly opts a field out.

## Executable Breakdown

This file is decomposed into tracked child workstreams under
`04c-family-protocol-cutover/`. Execute them in the order listed in
`04c-family-protocol-cutover/00-index.md`.

The first child is deletion fallout from the already-deleted files
`propstore/families/world_charters.py` and
`propstore/families/claims/metadata.py`. Those files stay deleted; callers move
to the real family charter/catalog owner and typed claim/world behavior.

## Actual Learnings So Far

- This file is now the architectural parent. The executable split is
  `04c-family-protocol-cutover/00-index.md`, produced from explicitly forked
  scout reports in `reports/charter-cutover-breakdown/`.
- The first executable repair is deleted-file fallout. The deleted
  `propstore/families/world_charters.py` and
  `propstore/families/claims/metadata.py` stay deleted. Their callers are
  repaired by moving world schema composition to family charter/registry owners
  and claim metadata access to typed claim/world behavior.
- `propstore.families.documents.*` and sibling `*/documents.py` files are not
  the source of truth. They are hand-authored field lists that duplicate the
  family charter target state.
- The document concept remains. The handwritten document class does not.
- Quire must provide generated msgspec document structs/codecs from
  `FamilyCharter` and `CharterField` metadata before Propstore can delete the
  handwritten family document classes cleanly.
- Field metadata is the protocol. It must carry document inclusion, storage
  participation, identity participation, references, relationships,
  artifact-code participation, indexes, and lifecycle/source-local scope.
- Cross-family behavior should not be a central view over hardcoded family
  imports. A model is already a graph chunk: relationship/reference fields
  expose related models generically.
- Artifact verification is a real capability, but the current root-level
  verifier is the wrong shape because it imports concrete document classes and
  hardcodes the claim/source/justification/stance walk.
- A generic protocol over model relationships replaces that central walk. The
  model/family supplies semantic callbacks only for named domain policy such as
  validation, canonicalization, transition guards, or display labels; callbacks
  must not carry field lists, document shape, relationship discovery, or
  storage shape.
- "Family declaration modules" are current-code files such as
  `propstore/families/<family>/declaration.py`; they are not the target
  boundary. They currently mix model shells, compile behavior, query behavior,
  and sometimes charter/schema concerns.
- Root semantic modules such as `propstore.context_lifting` can contain real
  domain behavior, but persisted context/lifting document shape belongs to the
  context family charter and generated document protocol.
- Proposal workflows are family lifecycle state machines over fields and
  placements. `propstore.proposals`, `propstore.proposals_rules`, and
  `propstore.proposals_predicates` currently hand-author promotion plans,
  copied documents, branch selection, and target refs that should come from
  proposal/canonical family metadata.
- `propstore.graph_export` is a presentation/export surface that currently
  rebuilds the semantic graph by hand. DOT/JSON rendering can stay; hardcoded
  graph discovery over concepts, claims, parameterizations, relationships, and
  stances must be replaced by generic field-relationship projection.
- `propstore.concept_ids` is real concept-authoring identity state, not random
  dead code. It allocates numeric local handles such as `concept1` and stores a
  git counter ref. The wrong part is root ownership, handwritten document
  scanning, and concept-specific storage mechanics outside the concept family
  identity/charter protocol.
- `propstore.source.claims`, `propstore.source.relations`,
  `propstore.source.claim_concepts`, `propstore.source.concepts`, and
  `propstore.source.common` contain real source-local authoring semantics, but
  they also contain handwritten document conversion, loose payload rewriting,
  source-local string rewrites, and root-level workflow ownership that should
  be source-family lifecycle metadata and transition behavior.
- `propstore.worldline.resolution` contains real worldline result semantics,
  but it also manually reassembles claim values, display ids, target values,
  input-source trees, chain fallback behavior, conflict resolution, derived
  input tracing, and trace recording that should be driven by typed
  world/worldline result protocols and family relationship metadata.

## Executable Child Split

The executable work queue is now:

1. `04c-family-protocol-cutover/01-deleted-file-fallout-repair.md`
2. `04c-family-protocol-cutover/02-quire-generated-family-protocols.md`
3. `04c-family-protocol-cutover/03-generic-family-lookup-cleanup.md`
4. `04c-family-protocol-cutover/04-family-document-deletion.md`
5. `04c-family-protocol-cutover/05-registry-contracts-batch-specs.md`
6. `04c-family-protocol-cutover/06-source-lifecycle-state-machines.md`
7. `04c-family-protocol-cutover/07-proposal-lifecycle-state-machines.md`
8. `04c-family-protocol-cutover/08-artifact-graph-verification-export.md`
9. `04c-family-protocol-cutover/09-worldline-resolution-protocol.md`
10. `04c-family-protocol-cutover/10-context-lifting-justification-views.md`
11. `04c-family-protocol-cutover/11-concept-local-id-compatibility-fixtures.md`
12. `04c-family-protocol-cutover/12-final-gates.md`

Do not execute this parent file as a loose checklist. Execute the nested index
in order.

## Target Architecture

Each family has one charter-owned contract. That contract provides:

- document type generation;
- document codecs;
- mapped model generation or mapping metadata;
- reference and relationship fields;
- identity fields;
- artifact-code fields and dependency edges;
- lifecycle/source-local/canonical scope;
- local-id/index/counter policy where the family has authoring-local handles;
- graph-node and graph-edge projection metadata;
- indexes, FTS/vector flags, and storage metadata.

Propstore family code owns:

- methods on family models;
- semantic validators;
- semantic canonicalizers;
- lifecycle/state-machine callbacks;
- local-id semantic policy when a family really has human-authored local
  handles;
- graph display labels and rendering hints that do not discover graph edges;
- artifact-code canonicalization policy over the already generated artifact
  payload;
- family-specific dependency policy only as a callback over already declared
  relationship dependency edges;
- compiler-stage behavior that turns parsed input into typed model instances.

Quire owns:

- generating document structs/codecs from the charter;
- resolving relationship/reference fields generically;
- executing lifecycle/state transitions declared by family metadata;
- reserving generic family index/counter state when a charter declares a
  monotonic local-id policy;
- projecting typed model relationship graphs into generic graph-view records;
- mapping charter fields to SQLAlchemy;
- exposing generic graph traversal over typed family relationships;
- deriving schema/catalog/cache identity from the same charter.

## Protocol Shape

The protocol is typed metadata-first. A family model participates in document
IO and artifact verification through its charter. These concepts must be
first-class typed charter attributes or typed charter-owned value objects, not
ad hoc entries in `metadata: Mapping[str, object]`:

- `CharterField.document: bool` includes or excludes a field from the generated
  document type. Inclusion defaults to true.
- `CharterField.document_name` and `CharterField.document_order` control
  document key spelling and stable output order.
- `CharterField.states` controls source-local, proposal, canonical, rejected,
  promoted, archived, and other state-conditional participation.
- `CharterField.artifact` and `CharterField.artifact_name` control artifact
  payload generation.
- `CharterField.graph_node_label` and `CharterField.graph_metadata` control
  field participation in graph projection output.
- `CharterField.local_id` and `CharterField.local_id_policy` define
  authoring-local counters such as concept numeric handles.
- `CharterField.contract_version` records document/field contract impact.
- `CharterField.parse_boundary` is allowed only for true YAML/JSON/SQLite IO
  boundary parsing.
- `CharterRelationship.artifact_dependency` marks a relationship edge as part
  of the artifact hash dependency graph.
- `CharterRelationship.graph_edge` and `CharterRelationship.graph_edge_kind`
  define exportable graph edges from the same relationship fields.
- `CharterRelationship.states` controls relationship participation by lifecycle
  state.
- `FamilyCharter.states`, `FamilyCharter.transitions`,
  `FamilyCharter.local_id_policy`, `FamilyCharter.batch_specs`, and
  `FamilyCharter.document_contract_version` define family-level state,
  lifecycle, local-id, batch-envelope, and contract behavior.

The exact API names are fixed by
`04c-family-protocol-cutover/02-quire-generated-family-protocols.md` before
implementation starts. The required property is that the information is
written once in the charter, not repeated in document structs, verification
code, model constructors, registry tables, or untyped metadata bags.

Generic operations:

- `family.document()` returns the generated document type.
- `family.document_codec()` returns the generated codec.
- `model.related()` traverses relationship/reference fields declared by the
  charter.
- `model.artifact_payload()` is generated from artifact/document fields plus a
  named family canonicalizer callback that receives typed values.
- `model.artifact_dependencies()` is generated from relationship fields marked
  as artifact dependencies plus a named family dependency callback that cannot
  introduce new undeclared edges.
- `model.artifact_code()` hashes the generated canonical payload.
- `family.transition(source_state, target_state, model)` materializes
  state-machine transitions such as proposal promotion without handwritten
  document copying. Quire runs the framework; Propstore callbacks provide
  semantic guards/materializers.
- `family.reserve_local_id(...)` reserves monotonic local handles from declared
  family identity metadata.
- `family.graph_projection(...)` emits graph nodes and edges from relationship
  metadata and model semantic methods.

The exact method names may differ, but the ownership may not: traversal and
field selection come from charter metadata, not a central handwritten view.

## Current Bad Surfaces

Delete or rewrite these as part of this workstream after Quire support exists:

- `propstore/families/documents/*.py` document field lists.
- `propstore/families/claims/documents.py`.
- `propstore/families/concepts/documents.py`.
- `propstore/families/contexts/documents.py`.
- `propstore/families/forms/documents.py`.
- `propstore/families/sameas/documents.py`.
- Root imports of concrete document classes in `propstore/artifact_codes.py`.
- Root imports of concrete document classes in
  `propstore/artifact_verification.py`.
- Concrete document class registrations in `propstore/contracts.py` that treat
  class paths as schema truth instead of resolving through family charters.
- Contract-manifest entries that name handwritten document modules after the
  generated document protocol exists.
- Payload metadata outside the charter, including claim-stage
  `metadata={"payload": ...}` and `payload_rest` field annotations.
- Constructor kwargs and compile-time object construction that effectively
  define fields for a family whose charter should own those fields.
- `propstore/proposals.py`, `propstore/proposals_rules.py`, and
  `propstore/proposals_predicates.py` promotion planners that hardcode
  proposal branches, target canonical refs, result dataclasses, path matching,
  and document-to-document field copying.
- Heuristic proposal extraction code that constructs proposal document shapes
  directly instead of asking the proposal family for its generated document and
  lifecycle placement.
- `propstore/graph_export.py::build_knowledge_graph`, `_claim_concept_id`,
  `_display_claim_id_from_store`, and hardcoded calls to `all_concepts`,
  `claims_for`, `all_parameterizations`, `all_relationships`, and
  `all_claim_stances`.
- `propstore/concept_ids.py` as a root module, including direct
  `ConceptDocument` scanning and concept-specific git counter ref mechanics.
- Root `propstore/source/*.py` helper surfaces that own source-local document
  classes, source-local-to-canonical field rewriting, proposal payload
  construction, reference normalization, and branch lifecycle mechanics outside
  the source family charters. The first deletion targets are the bad files or
  functions themselves; required semantics are recreated only in exact source
  family lifecycle/transition owners.
- `propstore/worldline/resolution.py` helper chains that duplicate world
  resolution, claim value extraction, display-id formatting, derived input
  tracing, and result/document shaping. The file is a deletion target unless
  it can be reduced to a thin worldline runner adapter over generic typed
  result protocols without owning field or relationship semantics.

## Correct Owner Placement

Target layout for family-owned code:

- `propstore/families/<family>/charter.py`: one field/schema/document/storage
  contract, including lifecycle states such as source-local, proposal,
  canonical, rejected, promoted, or archived when that family has those states.
- `propstore/families/<family>/models.py`: methods-only `FamilyModel`
  subclasses or behavior mixins; no fields.
- `propstore/families/<family>/stages.py` or domain-named modules: semantic
  compilation and validation.
- `propstore/families/<family>/identity.py` or the existing
  `propstore/families/identity/*` owner: semantic identity and artifact-code
  canonicalization policy, including local-id parsing/allocation policy when
  the family actually needs it.
- `propstore/families/<family>/views.py` or a generic Quire graph-view owner:
  graph display callbacks only; relationship discovery must still come from
  charter metadata.
- `propstore/families/registry.py`: registry composition only; it must not own
  document field lists, fallback codecs, per-family helper behavior, or schema
  facts already declared in a family charter.

Root-level modules are kept only when they are true app/service entry points or
pure cross-family algorithms over the generic protocol. They must not import
every family document class to build their own schema view.

## Proposal State-Machine Final State

Proposal artifacts are not a separate handwritten workflow family. They are a
family lifecycle state:

- stance proposals are stances in a proposal state/placement;
- rule proposals are rules in a proposal state/placement;
- predicate proposals are predicates in a proposal state/placement;
- source-local proposals are source-family or target-family records in a
  source/proposal state.

Promotion is a state transition:

1. Resolve proposal records through the proposal state placement declared by
   the family charter.
2. Validate transition guards declared by the family: conflict checks,
   already-promoted checks, required provenance, and mutation locks where a
   real concurrency policy exists.
3. Materialize canonical records through the same family document/model
   contract with transition metadata such as `promoted_from_sha`.
4. Commit through generic Quire family transaction APIs.

The promotion engine should not have one root module per proposal kind that
copies fields into another handwritten document class. If fields differ between
proposal and canonical states, that difference is represented in charter field
state metadata, not copied constructor arguments.

## Source-Local State-Machine Final State

Source authoring is real. The root-level helper shape is not.

Source branches, source-local claims, source-local concepts, source-local
justifications, source-local stances, source notes, source metadata, finalize
reports, and promotion results are lifecycle states over family records:

- source-local claim records are claim-family records in a source-local state;
- source-local concept records are concept-family records in a source-local
  state;
- source-local justifications and stances are relation/justification-family
  records in a source-local state;
- source finalize/promote is a transition from source-local state to canonical
  state;
- source-local handles are reference/index fields declared in the charter, not
  ad hoc string rewrites.

The existing source modules show the semantics that must survive:

- source branch initialization and source metadata/notes lifecycle;
- source-local claim stable identity and logical-id policy;
- source-local concept proposal matching against primary-branch concepts;
- source-local reference resolution against source and canonical indexes;
- CEL/form validation for source-local claim authoring;
- source-local concept-reference rewriting during import/promotion;
- source-local justification/stance rule validation and provenance stamping.

Deletion-first rule for this queue:

1. Delete the wrong root/file/helper surface first.
2. Let import/type/test/search failures name the missing capability.
3. Recreate only the required semantic behavior in source-family charter,
   identity, lifecycle, or transition owners.
4. Do not preserve root helper modules as compatibility shells.
5. Do not replace `SourceClaimDocument` payload patching with another dict
   normalizer.
6. Do not keep `ClaimDocument | SourceClaimDocument | Mapping[str, Any]`
   unions past the IO boundary. The transition receives typed source-local
   models and produces typed canonical models.

Correct owner examples:

- source branch placement and source-local lifecycle state: source family
  charter metadata;
- source-local claim identity: claim family identity policy scoped by source
  lifecycle state;
- source-local concept matching: concept family reference/index policy plus
  source lifecycle state;
- source-local claim-concept rewriting: transition over declared relationship
  fields;
- source-local CEL/form validation: source/claim/concept semantic validation
  callbacks over typed models;
- provenance stamping: transition metadata, not payload dict surgery.

## Worldline Resolution Final State

Worldline resolution is result projection over an already typed world graph.
It is not a second resolution engine.

The current file owns too many things:

- extracts claim scalar/text/algorithm values from `Claim` internals;
- formats claim display ids;
- chooses target/input source branches through local resolver chains;
- calls `world.resolution.resolve` directly for conflicts;
- calls `query_world.derived_value` and `world.chain_query` as fallback
  strategies;
- recursively rebuilds input-source trees;
- records trace steps while also constructing result documents.

Correct final ownership:

- claim value/display semantics live on typed claim/family model methods or
  field metadata;
- concept display semantics live on concept family model methods or field
  metadata;
- conflict resolution lives in the world resolution owner;
- derived-value input tracing lives in the generic world/parameterization graph
  protocol;
- worldline result document shape comes from the worldline family charter;
- worldline runner coordinates targets, policy, overrides, and result capture.

Deletion-first rule for this queue:

1. Delete `propstore/worldline/resolution.py` or the wrong helper family inside
   it first.
2. Use runner/import/test failures to identify the minimum required protocol.
3. Recreate missing behavior as typed worldline/world/family methods or
   generic graph projection; do not restore the resolver-chain file under a
   new name.
4. Do not add `Claim` field extraction helpers in worldline code.
5. Do not keep worldline-specific display-id lookup when model/family display
   policy can provide it.
6. Do not let result document construction duplicate fields already in the
   worldline charter.

The final worldline runner should ask typed world/worldline protocols for:

- target value for a concept under policy/overrides;
- input dependency graph for a derived value;
- trace entries from the same graph traversal;
- generated result document values from the worldline charter.

## Graph Export Final State

Graph export is presentation. It should not own the domain graph.

Kept behavior:

- a JSON/DOT export shape;
- request/report objects for the app/CLI boundary;
- rendering choices such as DOT node shapes and colors.

Deleted/replaced behavior:

- hardcoded graph discovery in `build_knowledge_graph`;
- local claim-concept selection helpers that duplicate claim relationship
  semantics;
- manual JSON decoding of relationship fields such as parameterization
  `concept_ids`;
- direct dependence on `WorldStore` methods as the graph schema.

The graph exporter receives typed graph-view records from generic family graph
projection. Family charters say which models are nodes, which relationship
fields are edges, and which fields become display labels or metadata. Bound
world/environment filtering supplies the typed model set; it does not require a
second hand-authored graph schema.

## Concept Local-ID Final State

Concept numeric IDs are useful only as an authoring-local handle policy. They
are not the concept schema owner.

If numeric `concept<N>` handles remain a product requirement:

1. Move the policy under the concept family identity owner.
2. Declare the logical-id/local-handle field in the concept charter once.
3. Declare the monotonic counter/index ref in concept family identity metadata.
4. Use a generic Quire/family reservation primitive for git-backed
   compare-and-swap counter updates.
5. Change concept mutation to call the concept family identity API instead of
   importing `propstore.concept_ids`.
6. Delete `propstore/concept_ids.py`.

If numeric handles are no longer required, delete the allocation feature
entirely and make concept creation derive identity from the family charter's
canonical identity fields. Do not keep the root module for tests only.

## Artifact Verification Final State

The current verifier is replaced by generic graph traversal:

1. Resolve the starting model through Quire family/reference APIs.
2. Ask the model/family for its generated artifact payload.
3. Traverse relationship fields marked as artifact dependencies.
4. Recompute each model's artifact code through the generated protocol.
5. Report mismatches.

The verifier may be a small CLI/app entry point, but it must not hardcode
`ClaimDocument`, `SourceDocument`, `JustificationDocument`, or `StanceDocument`
imports and must not know the family graph by hand.

## Context Lifting Placement

`propstore.context_lifting` contains real context-family semantics: lifting
rules, exceptions, decisions, materialization, and the lifting system. Those
semantics should live under the context family owner, for example
`propstore/families/contexts/lifting.py`, after the move is planned.

The context document shape does not live there. Persisted context and lifting
documents come from the context charter's generated document type.

## Required Quire Work First

This workstream is not executable until Quire can:

- generate msgspec document structs from `FamilyCharter` fields;
- default fields into document inclusion unless opted out;
- generate YAML/JSON codecs for those document structs;
- expose relationship/reference metadata for generic traversal;
- expose artifact payload/dependency metadata from fields;
- expose graph-node/edge projection metadata from fields;
- expose family local-id/index reservation metadata and a generic reservation
  primitive;
- expose lifecycle state-machine transition metadata;
- allow family semantic callbacks for canonicalization and special dependency
  policy without requiring duplicate field lists.

Add proof tests in Quire before deleting Propstore document classes.

## Deletion-First Execution Order

1. Add the missing Quire generated-document and relationship protocol.
2. Push Quire and pin Propstore to the pushed commit.
3. Pick one small family with a simple document shape.
4. Delete that family's handwritten document class file first.
5. Replace call sites with `family.document()` or the exact generated Quire
   API.
6. Use type/test/search failures as the work queue.
7. Repeat family by family.
8. Delete or rewrite `artifact_codes.py` and `artifact_verification.py` to use
   generic model relationship traversal and family artifact policy.
9. Delete or rewrite proposal promotion modules into family lifecycle
   state-machine transitions over charter fields. Do not preserve
   `StanceProposalPromotionPlan`, `RuleProposalPromotionPlan`, or
   `PredicateProposalPromotionPlan` as handwritten per-family workflow
   schemas if generic transition planning can express the same state.
10. Replace `build_knowledge_graph` with generic graph projection from family
    relationship metadata. Keep only DOT/JSON rendering and app/CLI request
    shells if still needed.
11. Move concept numeric local-id allocation under the concept family identity
    owner or delete numeric local-id allocation entirely if no longer required.
    In either case, delete `propstore/concept_ids.py`.
12. Delete root source-local helper surfaces first, then recreate source-local
    authoring and promotion semantics in source/family lifecycle-transition
    owners. Start with the smallest source file whose deletion exposes a
    bounded queue, then proceed file by file.
13. Delete `propstore/worldline/resolution.py` or its wrong helper family
    first, then recreate only required target/input/trace behavior in typed
    worldline/world/family protocols.
14. Move context-lifting semantics under the context family owner, without
    moving document shape there.
15. Remove concrete document-class registration paths from contracts and
    regenerate contract manifests through the family registry.

## Search Gates

These must be zero production hits after the workstream completes, excluding
workstreams, reports, notes, and generated historical manifests only until the
manifest regeneration phase:

```powershell
rg -n -F -- "from propstore.families.documents" propstore tests
rg -n -F -- "from propstore.families.claims.documents" propstore tests
rg -n -F -- "DocumentStruct" propstore/families propstore/source propstore/worldline propstore/support_revision propstore/core
rg -n -F -- "metadata={\"payload\"" propstore tests
rg -n -F -- "payload_rest" propstore tests
rg -n -F -- "propstore.families.documents." propstore tests
rg -n -F -- "StanceProposalPromotionPlan" propstore tests
rg -n -F -- "RuleProposalPromotionPlan" propstore tests
rg -n -F -- "PredicateProposalPromotionPlan" propstore tests
rg -n -F -- "propstore.concept_ids" propstore tests
rg -n -F -- "build_knowledge_graph" propstore tests
rg -n -F -- "_claim_concept_id" propstore tests
rg -n -F -- "ClaimDocument | SourceClaimDocument | Mapping" propstore/source propstore tests
rg -n -F -- "convert_document_value(" propstore/source propstore/families tests
rg -n -F -- "SourceClaimDocument" propstore/source propstore tests
rg -n -F -- "SourceConceptEntryDocument" propstore/source propstore tests
rg -n -F -- "SourceJustificationDocument" propstore/source propstore tests
rg -n -F -- "SourceStanceEntryDocument" propstore/source propstore tests
rg -n -F -- "propstore.worldline.resolution" propstore tests
rg -n -F -- "_claim_value" propstore/worldline propstore tests
rg -n -F -- "_resolve_claim_target" propstore/worldline propstore tests
```

Allowed remaining `DocumentStruct` hits must be generated by Quire or belong to
non-family, non-persisted semantic value objects explicitly reviewed in this
workstream. A reviewed exception is not allowed when the object is a family
document, a source-local family document, or a persisted artifact document.

## Completion Criteria

- Every family document is available through the family/charter generated
  document API.
- No handwritten family document class repeats charter fields.
- Artifact verification traverses generic relationship/reference metadata.
- Artifact code payload/dependency policy is charter-driven. Semantic family
  callbacks may canonicalize typed values or filter already declared dependency
  edges, but they must not define field lists, document shape, storage shape,
  or new undeclared dependency edges.
- Proposal promotion is a generic lifecycle/state-machine transition over
  family fields and placements, not handwritten per-family root workflow code.
- Graph export uses generic family graph projection over field relationship
  metadata. It keeps rendering but deletes the second hardcoded graph schema.
- Concept local-id allocation is either concept-family identity metadata backed
  by generic Quire reservation mechanics, or deleted completely if numeric
  handles are no longer required.
- Source-local authoring and promotion are lifecycle/state-machine transitions
  over typed family records. Root source helper modules no longer own document
  shape, payload rewriting, reference normalization, or branch workflow
  semantics.
- Worldline resolution is typed result projection over world/family protocols.
  It does not own claim field extraction, display-id lookup, conflict
  resolution, derived input tracing, or result document shape.
- `propstore.context_lifting` no longer owns persisted document shape; context
  lifting semantics are under the context family owner.
- Registry and contract code resolve document types through family charters,
  not manual class imports.
