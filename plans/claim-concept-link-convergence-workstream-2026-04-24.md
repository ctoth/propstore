# Claim-Concept Link Convergence Workstream

Date: 2026-04-24
Status: active

Grounded in current repo review of:

- `propstore/families/claims/documents.py`
- `propstore/families/claims/passes/checks.py`
- `propstore/core/row_types.py`
- `propstore/core/active_claims.py`
- `propstore/sidecar/schema.py`
- `propstore/sidecar/claim_utils.py`
- `propstore/world/model.py`
- `propstore/app/claim_views.py`
- `plans/semantic-contract.md`
- `plans/semantic-carrier-convergence-workstream-2026-04-13.md`
- `proposals/epistemic-operating-system-synthesis-2026-04-21.md`
- `docs/lemon-concepts.md`
- `propstore/core/lemon/description_kinds.py`
- `propstore/core/lemon/types.py`

## Goal

Delete the false singular claim concept surface and replace it with explicit,
typed claim-concept links.

This is a direct cutover. We control the whole stack. There are no old/new
parallel production paths, compatibility shims, bridge normalizers, or fallback
readers.

The target end state is:

- canonical claim artifacts do not use a generic singular `concept` field
- compiled rows do not use a generic singular `concept_id` field as the claim
  ownership surface
- concept-bearing claim semantics are represented as explicit typed links
- the claim type contract declares which authored fields produce which link
  roles
- concept-facing query and inventory surfaces consume links, not ad hoc
  per-claim-type conditionals
- output ownership, target ownership, aboutness, and input dependency are not
  collapsed into one slot

## Thesis

The generic singular claim `concept` was always the collapse.

It falsely combines at least four distinct relations:

- the claim is about these concepts
- the claim outputs a value for this concept
- the claim targets this concept for measurement
- the claim depends on these concepts as inputs

That collapse violates propstore's current semantic direction:

- source artifacts are authoritative and sidecars are projections
- closed vocabularies should be explicit enums
- runtime semantic carriers should not be anonymous strings or overloaded
  nullable columns
- the operating-system target is relation plus role bindings, not loose
  predicate-like shortcuts

This workstream therefore treats the singular claim concept surface as wrong,
not as legacy compatibility that needs to be preserved.

## Important Distinction: Closed Claim-Link Roles vs Open Relation Roles

This workstream introduces a closed enum for claim-to-concept link roles.

It does **not** close the future relation participant role vocabulary.

These are different layers:

- claim-concept link roles are a small closed compiler/runtime vocabulary about
  how a claim touches a concept
- relation participant roles are open, relation-defined slots such as `cause`,
  `effect`, `whole`, `part`, `subtype`, and `supertype`

The semantic OS proposal wants open `RoleSignature` and `role_bindings`.
That remains correct. This workstream does not replace it.

Instead, this workstream fixes the existing claim artifact and sidecar shape so
it stops lying before the larger situated-assertion substrate lands.

## Closed Enum

Add a canonical closed vocabulary:

```python
class ClaimConceptLinkRole(StrEnum):
    ABOUT = "about"
    OUTPUT = "output"
    TARGET = "target"
    INPUT = "input"
```

This belongs in a canonical owner module under `propstore/core/`.

Reason:

- the semantic-carrier workstream already established that closed vocabularies
  become `Enum`/`StrEnum`
- these four values are runtime-meaningful and finite
- they should not remain bare strings in authored contracts, sidecar rows, or
  query surfaces

## Current Wrong Surface

The current system already shows the mismatch clearly:

- claim documents support both `concept` and `concepts`
- claim type contracts already know which fields contain concept references
- validation already consumes that contract centrally
- sidecar compilation collapses authored concept-bearing surfaces into singular
  `concept_id` and optional `target_concept`
- runtime claim rows preserve the collapse
- concept-facing query paths use the collapsed row shape
- presenter surfaces then guess

That is why valid observation, comparison, limitation, mechanism, and equation
claims look broken in inventories even when the authored claim is correct.

## Target Architecture

### 1. Authored Claim Surface

Delete generic singular `concept` from canonical claim documents.

Canonical claim concept semantics become:

- `concepts`: concept refs for aboutness
- `target_concept`: explicit target concept where the claim type requires a
  dedicated target field
- `variables[*].concept`: input concept refs
- any future explicit output field when a claim type needs one

Claim types that truly have one semantic output concept must name that role
explicitly. Do not reintroduce generic `concept` under a friendlier spelling.

### 2. Claim Type Contract Surface

Replace the current concept-reference declaration with an explicit link
declaration.

Current contract shape answers:

- where is the concept reference stored
- is it scalar/list/bindings

Target contract shape must also answer:

- what link role does this field produce

Example:

```python
@dataclass(frozen=True)
class ClaimConceptLinkDeclaration:
    field: str
    role: ClaimConceptLinkRole
    source: str
    target_family: str = "concept"
    message_subject: str | None = None
```

Then each `ClaimTypeContract` declares explicit link semantics instead of only
field locations.

### 3. Compiled Sidecar Surface

Add a normalized claim-concept link table and make it the sole production
surface for claim-concept association.

Target table:

- `claim_id`
- `concept_id`
- `role`
- `ordinal`
- `binding_name` nullable

`ordinal` preserves authored order where it matters.
`binding_name` lets variable/input links retain authored names without pushing
that burden into the claim core row.

Delete generic claim ownership from `claim_core`:

- remove `concept_id`
- keep `target_concept` only if it survives as a claim-type-specific field
  during intermediate slices; final target is for it to become a link too

Do not replace `concept_id` with `concept_ids_json`. That would preserve the
same collapse in blob form.

### 4. Runtime Row Surface

`ClaimRow` must no longer pretend a claim has one concept.

Target direction:

- `ClaimRow` drops generic `concept_id`
- `ClaimRow` may keep typed claim-type-specific fields if still needed during
  migration, but the stable ownership surface is `ClaimConceptLinkRow`
- world/model query helpers resolve link rows and expose typed link collections
  or role-aware helper methods

### 5. Query Surface

Concept-facing runtime queries must be link-based.

That means:

- inventory/search by concept use link membership
- claim ownership/attribution logic uses role semantics, not first-non-null
  field hacks
- algorithm, measurement, observation, equation, and model claims all reach the
  same concept-facing surfaces through explicit links

### 6. Presentation Surface

CLI/web presenters stay dumb.

They consume precomputed typed summaries from the app layer. They do not inspect
claim-type-specific fields to reconstruct semantics.

## Initial Role Mapping

The starting mapping for current claim types is:

- parameter -> explicit output concept link
- algorithm -> explicit output concept link
- measurement -> target concept link
- observation -> about links from `concepts`
- mechanism -> about links from `concepts`
- comparison -> about links from `concepts`
- limitation -> about links from `concepts`
- equation -> input links from `variables[*].concept`
- model -> input links from `parameters[*].concept`

If a claim type truly needs both aboutness and output ownership, declare both.
Do not force one field to stand in for the other.

## Step 0

Step 0 is deletion of the singular claim concept surface.

This is not a late cleanup step. It is the opening cut.

Delete first:

- canonical `ClaimDocument.concept`
- canonical `AtomicPropositionDocument.concept`
- generic singular concept use in claim-type contracts
- `TypedClaimFields.concept_id`
- `ClaimRow.concept_id`
- `claim_core.concept_id`
- concept-facing query semantics that treat singular `concept_id` as the claim
  ownership key

After deletion, use the resulting failures as the migration queue.

Forbidden failure mode:

- add `concept_links` while keeping generic `concept` and `concept_id` alive as
  production ownership surfaces

## Execution Order

### Phase 0: Red Tests And Boundary Inventory

Add failing tests first.

Required proofs:

1. observation/comparison/mechanism/limitation claims with `concepts` round-trip
   through compile and query without singular ownership loss
2. equation variable concepts are queryable as input-linked concepts
3. concept-facing claim queries are role-aware, not singular-column-based
4. claim inventory/search can render concept memberships from typed links
5. no canonical claim artifact accepts generic singular `concept`
6. no compiled runtime claim row exposes generic singular `concept_id`

Inventory every production caller of:

- `claim["concept"]`
- `claim.concept_id`
- `core.concept_id` on `claim_core`
- `claims_for(concept_id)` semantics that assume one owning concept

### Phase 1: Contract Cutover

1. Add `ClaimConceptLinkRole`
2. replace `ClaimFieldReferenceDeclaration` with
   `ClaimConceptLinkDeclaration`
3. update `ClaimTypeContract`
4. move current claim types to explicit link-role declarations
5. make contract manifest output include the role
6. fail canonical claim decode/validation when singular `concept` appears

Exit criteria:

- canonical claim contracts no longer declare generic singular concept
- link role is explicit and typed in the contract surface
- old generic contract path is deleted

### Phase 2: Authored Claim Model Cutover

1. delete singular `concept` from canonical claim documents
2. update claim file parsing and payload emission
3. update validation and source/canonical boundaries
4. reject old singular authored shape loudly

Exit criteria:

- canonical claim documents no longer carry singular `concept`
- authored boundary failures are loud and typed

### Phase 3: Sidecar Link Table Cutover

1. add `claim_concept_link`
2. compile link rows from claim contracts
3. delete `claim_core.concept_id`
4. stop deriving claim ownership from the old core column
5. update build/invalidation and any affected indexes

Exit criteria:

- sidecar concept association is link-table-based
- generic `claim_core.concept_id` is gone

### Phase 4: Runtime Row And Query Cutover

1. delete `ClaimRow.concept_id`
2. add typed link row objects and world/model readers
3. rewrite `claims_for` and related concept-facing helpers to use links
4. update `ActiveClaim` and query/runtime callers

Exit criteria:

- runtime concept-facing access is role-aware
- no production runtime path depends on singular claim concept ownership

### Phase 5: Presenter/App Cutover

1. update app claim/concept views to consume links
2. update CLI/web reporting
3. delete presenter heuristics introduced only to compensate for the collapse

Exit criteria:

- app summaries consume typed link semantics
- CLI/web inventory is truthful without ad hoc recovery logic

### Phase 6: Cleanup Gates

Delete every remaining production reference to the old surface:

- `rg -F "\"concept\"" ...` must not find canonical claim concept ownership code
- `rg -F "concept_id" ...` must not find generic claim ownership code
- no helper named around "primary concept" or similar should survive unless it
  is truly claim-type-specific and justified

## Test Plan

Focused suites will likely include:

- `tests/test_validate_claims.py`
- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`
- `tests/test_claim_views.py`
- `tests/test_concept_views.py`
- `tests/test_web_claim_index_routes.py`

Add architectural tests that fail if:

- canonical claims reintroduce generic singular `concept`
- runtime rows reintroduce generic singular `concept_id`
- sidecar schema reintroduces generic claim concept ownership on `claim_core`

Use the logged pytest wrapper for every pytest run.

## Deletion-First Rules For This Workstream

- do not add `primary_concept`, `owner_concept`, `claim_concept`, or any other
  renamed singular wrapper as a compatibility bridge
- do not add `concept_ids_json` as a blob replacement for the deleted surface
- do not keep old and new ownership/query paths in parallel
- do not preserve silent authored compatibility for singular `concept`
- do not let the presenter layer infer semantics the contract/compiler should
  carry explicitly

## Non-Goals

- this workstream does not implement the full situated-assertion substrate
- this workstream does not close future open relation participant roles
- this workstream does not redesign the whole proposition/evidence ontology
- this workstream does not introduce ORM ownership of semantic truth

## Definition Of Done

This workstream is complete only when all of the following are true:

- canonical claim artifacts have no generic singular `concept`
- claim type contracts declare typed concept link roles
- sidecar storage uses a normalized claim-concept link surface
- `claim_core` has no generic concept ownership column
- runtime claim rows have no generic singular concept ownership field
- concept-facing query semantics are link-based and role-aware
- presenter surfaces use typed summaries built from links
- tests and architectural guards prevent reintroduction of the collapse

## First Concrete Slice

Start with Phase 1 and Phase 2 together as one deletion-first cut:

1. add `ClaimConceptLinkRole`
2. replace contract declarations with explicit link-role declarations
3. delete singular `concept` from canonical claim documents
4. update every claim type contract to the new declarations
5. make canonical authored decode/validation fail on singular `concept`

That first slice proves the semantic direction before touching sidecar storage.
