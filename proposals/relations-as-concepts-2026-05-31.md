# Relations as concepts — design (2026-05-31)

## The core insight

**A relation is a concept whose lexical sense carries a role signature.**

No new family. No new `KindType`. No discriminator flag. A relation concept is
just a concept whose OntoLex sense declares named role slots with domain/range —
the structure itself makes it a relation. `RelationConceptRef` stops being a bare
string wrapper and becomes an ordinary **concept FK**, resolved against the
concepts family exactly the way a claim already references a concept.

This is the thing the codebase was reaching for. Evidence it was always the
target:
- `core/relations.py` docstring (Buitelaar 2011, Cimiano 2016): *"Relation
  identity therefore lives at the ontology/concept reference."*
- `RelationConceptRef.identity_key()` returns `("relation_concept", concept_id)`
  and carries `lexical_sense_id` / `description_kind_id` — OntoLex grounding with
  nowhere to point, because the sense/description-kind weren't addressable.
- `BOOTSTRAP_RELATION_IDS` lists `relation_concept`, `role`, `role_domain`,
  `role_range`, `has_role` — a vocabulary meant to be **concepts** that define
  relations, never materialized.
- The concept sense already holds `description_kind` **participant slots** and
  Dowty `role_bundles` — role structure already lives at the sense.

The dead `RoleSignature`/`RoleDefinition`/`RelationProperty*` types were the
in-memory projection of authored role/property content. They had no storage
anchor, so they floated, unused, and read as cruft. Design B builds the anchor.

## What inverts the earlier deletion plan

**Choosing this design rewrites Chunk A — it does NOT simply cancel it.** The
split is now sharp, because the role-signature half is superseded by the lemon
layer while the property half has no lemon equivalent:
- `RoleDefinition`, `RoleSignature`, `validate_bindings`, AND `RoleBinding` /
  `RoleBindingSet` → **deleted as duplicates of the lemon `DescriptionKind` /
  `ParticipantSlot` / `SlotBinding` layer** (see §1), after the situated-
  assertion path migrates onto the lemon types. This is a *bigger* deletion than
  the original Chunk A (it also removes the currently-"live" RoleBinding(Set)),
  but it happens only after the migration, not before.
- `RelationPropertyKind` (functional/symmetric/transitive/inverse),
  `RelationPropertyAssertion`, `RelationPropertySet` (transitive_closure,
  symmetric canonicalization) → **kept and anchored.** No lemon equivalent
  exists (the lemon layer has only account-sensitive *causal* closure,
  `causal_transitivity_allowed`, not a generic property algebra). These become
  the OWL relation-property layer projected from authored relation-property
  content. (Decision 2.)
- The two `RelationConceptRef` lemon fields → wired, not deleted.
- `BOOTSTRAP_RELATION_IDS` → still dies as a *string constant*, but its members
  are reborn as authored bootstrap relation **concepts**.

So the original Chunk A "delete the role/property scaffolding" was directionally
half-right: the *role* types do die (as lemon duplicates), the *property* types
do not (they get a home). Just not on the original timeline — the role deletion
waits for the lemon migration.

Chunks **B** (labels scaffolding: `JustificationRecord`, poly helpers) and **C**
(`sameas` family) are untouched by this decision — still pure dead code, still
deletable independently. Only Chunk A is coupled to the relations design.

## The design, in five pieces

### 1. Relation concepts (authored, in the concepts family) — RESOLVED

A relation is authored through the existing `pks source propose-concept` path
into the concepts source family, promoted to canonical with the standard id
lowering (`derive_concept_artifact_id` → `ps:concept:<sha256>`). What makes it a
relation: its sense's **`description_kind` is its role signature**.

**The home already exists and is richer than the dead types.**
`LexicalSense.description_kind` is already a field (`core/lemon/types.py:22`).
`DescriptionKind(name, reference, slots)` + `ParticipantSlot(name,
type_constraint, proto_role_bundle)` (`core/lemon/description_kinds.py`) already
express the full signature:
- slot `name` = role name
- slot `type_constraint: OntologyReference` = role **range**
- the kind's `reference` = the relation identity = role **domain**
- `validate_slot_bindings` checks presence **and type** (stronger than the dead
  `validate_bindings`, which only checked presence)
- `SlotBinding(slot, value, value_type, provenance)` / `DescriptionClaim` carry
  **provenance per binding** and feed the Dung-backed `MergeArgument`
  coreference machinery.

Consequence: the `core/relations.py` role layer is a weaker, unprovenanced
**duplicate** of the lemon layer. It is NOT revived — it is **superseded**:
- `RoleDefinition` → `ParticipantSlot`
- `RoleSignature` → `DescriptionKind`
- `RoleBinding` / `RoleBindingSet` → `SlotBinding` (tuple) / `DescriptionClaim`
- `validate_bindings` → `validate_slot_bindings`

Nothing new is added to the concept sense. The work is to migrate the
situated-assertion representation off the bare role types onto the lemon
description-kind types, then delete the role layer.

### 2. `RelationConceptRef` → concept FamilyReference (FK)

Replace the bare `ConceptId | str` with a typed concept reference using the same
machinery claims already use: `ForeignKeySpec(... target_family=concepts ...)`
declared via `charter_field(foreign_key=...)`, resolved through
`FamilyReferenceIndex.resolve_id()`. The reference is validated wherever a
relation instance crosses a canonical write boundary.

The two grounding fields become real: `lexical_sense_id` /
`description_kind_id` point into the referenced concept's embedded sense and
description-kind — once those carry addressable identity (they're embedded
sub-objects today; this design gives them stable ids within the concept).

Identity vs. stance split (matters for the non-commitment principle):
- The **FK itself** (does this relation concept exist) is identity — a hard
  reference, fine to validate strictly.
- The **role signature / properties** (what roles, what domain/range, is it
  transitive) are *contestable authored content with provenance*. A relation may
  carry rival signatures; the render layer resolves. Do NOT model the signature
  as one canonical hard field that forces a single answer — author it as
  content, project + resolve at render time. (Design checklist #3: no gate
  before render.)

### 3. Claim types are relations

`f"ps:relation:claim:{claim_type}"` (merge_claims.py:83,
support_revision/projection.py:158) is the synthetic string path. It dies.

Each `ClaimType` maps to an authored relation concept (e.g. the `measurement`
relation with role slots `{subject, value, ...}`). The mapping is authored or
derived through a single typed resolver, not two hand-spelled f-strings. The
situated-assertion lowering then resolves the relation by FK and **validates the
`RoleBindingSet` against the relation's authored role signature** — the claim's
`{subject, content}` bindings type-check against stored structure instead of
being minted untyped.

Honest-ignorance rule: a `ClaimType` with no authored relation concept yields a
**diagnostic**, not a silently minted `ps:relation:claim:*` string. "I don't
know this relation" is a valid signal.

### 4. Argumentation relations come from the `argumentation` package

This closes the earlier taxonomy thread. `supports` / `rebuts` / `undercuts` /
`undermines` are ASPIC+/bipolar-AF vocabulary owned by `formal-argumentation`
(already a hard dependency). They are relation **identities imported from
upstream**, not re-declared as propstore `StrEnum` members. propstore authors
its *own* relations (published_in, measurement, …) as concepts; it imports the
argumentation relations' identity from the package. One source per name.

This remains gated on the `argumentation` re-pin (its layout moved). The
relations-as-concepts work in pieces 1–3 does **not** need the re-pin and can
proceed first; piece 4 lands when the package is re-pinned.

### 5. Relation properties (functional / symmetric / transitive / inverse)

`RelationPropertySet` already implements `transitive_closure` and symmetric
canonicalization correctly. Under this design they project from authored
relation-property content on the relation concept. **Scope decision:** include
properties in the first cut, or land relations + role signatures first and add
properties (and their reasoning) as phase 2? They're separable.

## Migration shape (additive-first, then delete-first)

Unlike a pure cleanup, this is feature work, so the *opening* is additive — you
cannot delete the synthetic path until its replacement (authored relation
concepts) exists to resolve against.

1. **Author the bootstrap + claim-type relation concepts** (knowledge data, not
   code): the real relations from `BOOTSTRAP_RELATION_IDS` plus one relation
   concept per `ClaimType`, each with a role signature. These are the FK targets.
2. **Give embedded senses / description-kinds addressable identity** so the
   lemon FK fields have something to point at. (Confirm scope from §1 first.)
3. **Flip `RelationConceptRef` to a concept FK**; update the ~5 construction
   sites to resolve against the concepts family. Revive `RoleSignature`/
   `RoleDefinition` as the projection of authored signature content; wire
   `validate_bindings` into the situated-assertion build.
4. **Delete the synthetic string path** (delete-first now applies): remove the
   two `f"ps:relation:claim:{...}"` sites; the projection breaks; fix by
   resolving `ClaimType → relation concept FK`. Missing → diagnostic.
5. **(gated) Argumentation relations from the package** once `formal-argumentation`
   is re-pinned.
6. **(optional phase 2) Relation properties** projected from authored content.

## Decisions

1. **Role-signature home — RESOLVED (read 2026-05-31).** It is the existing
   `LexicalSense.description_kind` (`DescriptionKind` + `ParticipantSlot`).
   Slots carry the range via `type_constraint`; domain is the kind's
   `reference`. The `relations.py` role layer is superseded, not extended. See
   §1.
2. **Relation properties — IN SCOPE NOW (Q, leaning yes).** `RelationPropertyKind`
   / `RelationPropertyAssertion` / `RelationPropertySet` are kept and anchored to
   authored relation-property content; no lemon equivalent exists, so this is the
   one genuinely-new surface. Includes the property *reasoning*
   (transitive_closure, symmetric canonicalization, inverse involution).

3. **Claim-type → relation is a RESOLVER, not a 1:1 table.** Read of `ClaimType`
   (`families/claims/types.py`): `parameter, equation, observation, mechanism,
   comparison, limitation, model, measurement, algorithm, unknown`. They fracture
   four ways:

   - **Split (one type → many relations):**
     - `mechanism` → causal relations keyed by `CausalAccount`
       (stated/counterfactual/statistical/mechanistic). The system *already*
       refuses a unified causal primitive (`causal_transitivity_allowed` is
       account-sensitive). Reuse `CausalConnectionAssertion`. Not one relation.
     - `comparison` → carries a comparator. Model the comparator as a **role
       filler** (one relation, comparator slot) rather than a relation per
       operator, to avoid relation explosion — but note `supersedes`-style
       comparators bleed into the argumentation vocabulary owned upstream.
   - **Not a relation (wrong shape):**
     - `equation` → output + *variadic* inputs + formula = a **parameterization**
       (`ParameterizationEdge`), a sibling of relations, not a fixed-slot role
       signature. Keep on the parameterization path; do not force a
       `DescriptionKind`.
     - `unknown` → no relation; honest ignorance; already out of
       `VALID_CLAIM_TYPES`.
   - **Possible merge (many types → one relation):**
     - `measurement` / `observation` / `parameter` may share `{subject, value,
       conditions}` and differ only by typed provenance method
       (`measured`/`stated`/…). Candidate to denormalize to one relation +
       provenance discriminator — OR keep separate if slots genuinely differ
       (instrument/conditions vs parameter-name). **Needs a read of real claim
       content before deciding** — do not pre-commit.
   - **Clean 1:1:** `model`, `algorithm`, `limitation` → binary
     `{subject, object}` relations.

   Consequence: there is no `ClaimType → relation` table to author 1:1. There is
   a typed **resolver** that splits `mechanism`, routes `equation` to
   parameterization, returns a diagnostic for `unknown`, and (pending the content
   read) possibly merges the value-bearing trio. The `f"ps:relation:claim:{...}"`
   string assumed 1:1 and is wrong for `mechanism` and `equation` specifically.

   **Merge sub-question — RESOLVED by the non-commitment principle (read
   2026-05-31).** `knowledge/claims/` is empty in the source repo and `ClaimNode`
   is a single generic shape tagged by `claim_type` — there is no authored
   per-type role structure to compare, so "do their signatures coincide" is not
   a fact in the data; it's a forward choice. The core design principle decides
   it: pre-merging `measurement`/`observation`/`parameter` into one relation at
   author time **collapses a distinction in storage**, which the non-commitment
   discipline forbids absent an explicit migration request. **Default: author
   them as three distinct relations.** Render-time policy may treat them
   uniformly; storage must not pre-merge. Split-now/merge-at-render is
   reversible; merge-at-author is not.

## Net effect on the deletion plan

- Chunk A: **cancelled / inverted** (scaffolding re-homed, not deleted; only the
  `BOOTSTRAP_RELATION_IDS` string constant and possibly the property types if
  deferred get touched).
- Chunk B, Chunk C: **proceed independently** — unrelated dead code.
- Chunk D: unchanged (still gated on the `attribute_mapping`/`label` receiver
  verification).
