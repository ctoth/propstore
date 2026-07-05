# Relations-as-concepts — control surface / tracking inventory

Design: `proposals/relations-as-concepts-2026-05-31.md`. Notes:
`notes/relations-as-concepts.md`. Every touch-point is a checkbox. Nothing ships
unchecked. Line numbers captured 2026-05-31 (re-grep before editing; they drift).

**Strategy: spike first, then mechanical fan-out.**
Phase 1 proves the whole spine end-to-end on ONE tiny relation (`published_in`,
2 roles paper/venue). Only once that round-trips green do we walk the Phase 2
inventory site-by-site. The inventory is the map; the spike is the proof; the
checkboxes are the tracking.

**In scope:** the relation spine (FK + role-signature-as-description-kind +
claim-type resolver + role-layer deletion).
**Phase 2 (deferred):** relation properties (functional/symmetric/transitive/
inverse) — `RelationPropertyKind`/`RelationPropertyAssertion`/`RelationPropertySet`
STAY untouched until then.
**Deferred:** argumentation relations from `formal-argumentation` (gated on
re-pin); the full per-claim-type author-set beyond the spike.

---

## Phase 0 — baseline & guards (do first, once)

- [ ] Run clean baseline: `powershell -File scripts/run_logged_pytest.ps1 tests/` → record pass/fail to `logs/`
- [ ] `uv run pyright propstore` clean — record baseline
- [x] READ `test_forbidden_symbols.py` guards — ALLIES of the design:
  - `:133 test_relation_concept_ref_is_not_a_string_alias` forbids `RelationConceptRef` being `NewType`/`str` alias → our FK keeps it structured → guard PROTECTS us, stays green.
  - `:116 test_relations_does_not_name_relation_identity_as_predicate` forbids hardcoded predicate Names in relations.py (AST Name/Attr only, not string literals) → deleting `BOOTSTRAP_RELATION_IDS` keeps it green.
- [x] READ `test_import_boundaries.py:80-88` — only ONE break: `assert relations.RoleBindingSet(())` (`:88`) fails when `RoleBindingSet` is deleted. The `RelationConceptRef("supports").identity_key()` assertion (`:84`) survives (type still takes an id). Action: drop the `RoleBindingSet` assertion in Phase 2.F.

## Phase 1 — SPIKE: `published_in` end-to-end (one tiny object)

- [ ] Author `published_in` as a relation **concept** (existing `pks source propose-concept` path)
- [ ] Attach its role signature via the EXISTING description-kind authoring: `set_concept_description_kind` (`app/concepts/mutation.py:1450`) / CLI `description_kind_cmd` (`cli/concept/mutation.py:318`), slots `paper`, `venue` with `type_constraint`
- [ ] Build ONE `SituatedAssertion` that references `published_in` **by concept FK** (resolve via `FamilyReferenceIndex.resolve_id`) instead of a bare string
- [ ] Validate its bindings against the description-kind (`validate_slot_bindings`) at build time
- [ ] Round-trip through the codec (`core/assertions/codec.py`) — serialize + deserialize, identity stable
- [ ] GATE: spike green (FK resolves, validation runs, round-trip stable) before any Phase 2 edit

---

## Phase 2 — FAN-OUT (mechanical; walk every site)

### A. Author the relation concepts (resolver, NOT 1:1 — see design §Decision 3)
Reuses existing description-kind authoring. One checkbox per relation concept.
- [ ] Clean 1:1: `model`, `algorithm`, `limitation` — binary `{subject, object}`
- [ ] Value-bearing trio (author SEPARATE per non-commitment): `measurement`, `observation`, `parameter`
- [ ] `comparison` — one relation, comparator as a role slot
- [ ] `mechanism` — SPLIT into account-keyed causal relations; reuse `CausalConnectionAssertion` (`core/lemon/description_kinds.py:126`) + `CausalAccount`
- [ ] `equation` — NOT a relation: route to parameterization (`ParameterizationEdge`); resolver returns "parameterization", not a relation FK
- [ ] `unknown` — resolver returns a diagnostic, mints nothing
- [ ] Bootstrap relations that are real (from old `BOOTSTRAP_RELATION_IDS`): `subtype_of`, `instance_of`, `published_in`, `base_rate_for`, `calibrates`, `condition_applies`, `contextualizes` — author as concepts (the meta ones `role`/`role_domain`/`role_range`/`has_role`/`relation_concept` are subsumed by the lemon description-kind model; confirm none still needed as concepts)

### B. `RelationConceptRef` → concept FamilyReference (FK)
- [ ] Add `ForeignKeySpec(target_family=concepts)` via `charter_field(foreign_key=...)` wherever a relation ref is persisted at a canonical-write boundary
- [ ] Replace the bare `ConceptId | str` field with the typed concept reference; resolve via `FamilyReferenceIndex.resolve_id()`
- [ ] Wire the two previously-dead lemon fields `lexical_sense_id` / `description_kind_id` to point into the referenced concept's sense / description-kind (needs addressable identity for embedded senses)
- [ ] Missing-referent → diagnostic (honest ignorance), never a minted string

### C. Migrate situated-assertion representation onto the lemon layer
`RoleBinding`/`RoleBindingSet` (bare) → `SlotBinding`/`DescriptionClaim` (typed + provenance).
- [ ] `core/assertions/situated.py:30` — `role_bindings: RoleBindingSet` → lemon `SlotBinding` tuple / `DescriptionClaim`; update `identity_payload` (`:48-49`)
- [ ] `core/assertions/codec.py` — `:29` field, `:66-69` to_assertion, `:78-81` serialize, `:105-122` `_relation_ref`/`_role_binding_set`/`_role_binding` decoders
- [ ] Bindings validated against the relation concept's description-kind at assertion build

### D. Claim-type resolver (kill the f-strings)
- [ ] Write ONE typed resolver `ClaimType → relation FK | parameterization | diagnostic`
- [ ] DELETE f-string `support_revision/projection.py:158` `RelationConceptRef(f"ps:relation:claim:{claim_type}")`
- [ ] DELETE f-string `merge_claims.py:83` `RelationConceptRef(f"ps:relation:claim:{...}")`
- [ ] (delete-first: remove the f-strings, let projection break, fix via resolver)

### E. Update every construction call site
Relation ref + role bindings + SituatedAssertion construction:
- [ ] `importing/machinery.py:387-390` (`RelationConceptRef(surface.relation_id)` + bindings), `:448-450` (SituatedAssertion), `:317-324` (the `.relation`/`.role_bindings` readers), `:35/85/171/425` (`SurfaceRoleBinding` — lower into lemon bindings)
- [ ] `policies.py:424-427` (SituatedAssertion + ref + bindings)
- [ ] `merge/merge_claims.py:82-87` (SituatedAssertion + ref + bindings)
- [ ] `support_revision/projection.py:59`, `:156-158` (`_relation_ref`), `:161-166` (`_role_bindings`)
- [ ] `support_revision/state.py:29-36` (`AssertionAtom` holds SituatedAssertion — type tighten if signature changes)

### F. Update / delete tests
- [ ] `tests/fixtures/journal.py:27-91` — migrate ref + bindings to FK + lemon
- [ ] `tests/test_situated_assertions.py:14-102` — migrate
- [ ] `tests/test_situated_assertion_codec.py:15-94` — migrate
- [ ] `tests/test_import_machinery.py:13-138` — `SurfaceRoleBinding` path
- [ ] `tests/test_relation_concept_identity.py` — KEEP the 3 identity tests (`:44`, `:58`, `:166-179`); DELETE the role-signature/property tests (see deletion plan Chunk A list)
- [ ] `tests/architecture/test_import_boundaries.py:84-88` — rewrite assertions (RoleBindingSet gone)
- [ ] `tests/architecture/test_forbidden_symbols.py:140` — update/retarget the AST guard

### G. Delete the superseded role layer (`core/relations.py`) — AFTER C/E/F green
- [ ] DELETE `RoleDefinition` (`:135`), `RoleSignature` (`:167`), `validate_bindings` (`:188`)
- [ ] DELETE `RoleBinding` (`:91`), `RoleBindingSet` (`:110`) — once no consumer remains
- [ ] DELETE `BOOTSTRAP_RELATION_IDS` (`:26`) string constant
- [ ] KEEP `ClaimConceptLinkRef`/`ClaimConceptLinkRole`, `_duplicated` (still used elsewhere?), and `RelationConceptRef` (now FK)
- [ ] KEEP (Phase 2) `RelationPropertyKind`/`RelationPropertyAssertion`/`RelationPropertySet` — untouched until properties phase
- [ ] Final: `core/relations.py` holds only `ClaimConceptLinkRole` + `RelationConceptRef`(+property types pending phase 2)

---

## Reuse (already built — do NOT rebuild)
- Description-kind authoring: `cli/concept/mutation.py:318`, `app/concepts/mutation.py:1450` + `ConceptDescriptionKindRequest:313`, `project_init.py:_seed_description_kind`
- Concept doc carries `description_kind`: `families/concepts/declaration.py:76`
- Slot validation pass: `families/concepts/passes.py:197-210`
- Lemon types: `core/lemon/description_kinds.py` (`DescriptionKind`/`ParticipantSlot`/`SlotBinding`/`DescriptionClaim`/`validate_slot_bindings`)
- FK API: `ForeignKeySpec` + `charter_field(foreign_key=...)` + `FamilyReferenceIndex.resolve_id()` (recipe in `notes/scout-authored-family-recipe.md`)

## Deferred (explicit — do not silently drop)
- [ ] PHASE 2: relation properties (functional/symmetric/transitive/inverse) + reasoning
- [ ] GATED: argumentation relations imported from `formal-argumentation` (after re-pin)
- [ ] Per-claim-type author-set beyond spike (folded into A above, but real-content read for measurement/observation/parameter slot shapes still pending)
