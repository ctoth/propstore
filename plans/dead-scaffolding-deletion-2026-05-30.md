# Dead-scaffolding deletion plan (2026-05-30)

Deletion-first removal of tests-only / write-only scaffolding in the semantic
core. **Scope is deliberately the separable half** of the graph-types/labels/
relations review: pure dead code with no production consumers. It is NOT the
relation-taxonomy consolidation (collapsing `GraphRelationType` /
`ConceptRelationshipType` / the 5-way `supports`/`rebuts`/... duplication into
the `argumentation` package) — that work is gated on re-pinning
`formal-argumentation` to its latest layout and is tracked separately.

Evidence base: `notes/scout-graph-types.md`, `notes/scout-labels.md`,
`notes/scout-relations.md`, `notes/scout-families.md`, plus direct reads of
`tests/test_relation_concept_identity.py`, `core/relations.py`, `core/labels.py`.

## Discipline

Per project delete-first rule: each chunk deletes the production symbol FIRST,
then the suite goes red on the referencing tests, then the referencing tests are
deleted/edited in the SAME commit. No shims, no deprecation aliases, no
"keep alongside." The red intermediate is expected; git holds everything.

One chunk = one commit, with explicit pathspec (`git commit -- <paths>`).
Chunks A/B/C are mutually independent and may be done in any order or parallel.
Chunk D is GATED and must not be started until its verification step passes.

## Step 0 — baseline (mandatory, before any deletion)

```
powershell -File scripts/run_logged_pytest.ps1 tests/ 2>&1 | tee logs/baseline-2026-05-30.log
uv run pyright propstore
```
Record pass/fail counts. A chunk is "done" only when the suite returns to this
baseline (same passes, zero new failures) and pyright on `propstore` is clean.

---

## Chunk A — remove relation-property / role-signature scaffolding

**File:** `propstore/core/relations.py`

**Why:** OWL-style relation-property modeling (functional/symmetric/transitive/
inverse + role signatures + role definitions) built and never wired. Zero
production callers (scout-relations.md Part A). Largest single dead-code win.

**Delete these symbols:**
- `BOOTSTRAP_RELATION_IDS`
- `RoleDefinition`
- `RoleSignature`
- `RelationPropertyKind`
- `RelationPropertyAssertion`
- `RelationPropertySet`

**KEEP (heavy production use):** `ClaimConceptLinkRole`,
`coerce_claim_concept_link_role`, `RelationConceptRef`, `RoleBinding`,
`RoleBindingSet`, and the module-private `_duplicated` (still used by
`RoleBindingSet.__post_init__`).

**Caller fixes (same commit):**
- `tests/test_relation_concept_identity.py` — drop deleted imports; delete the
  tests that exercise the deleted symbols:
  `test_bootstrap_relation_vocabulary_matches_workstream`,
  `test_role_signature_rejects_duplicate_roles`,
  `test_role_definition_requires_domain_and_range`,
  `test_role_signature_identity_includes_domain_and_range`,
  `test_role_binding_validation_rejects_missing_required_role`,
  `test_role_binding_validation_rejects_unknown_role`,
  `test_inverse_property_requires_target_relation`,
  `test_inverse_property_is_an_involution`,
  `test_symmetric_relation_canonicalizes_binary_values`,
  `test_non_symmetric_relation_preserves_binary_value_order`,
  `test_transitive_closure_contains_authored_edges`,
  and the `_published_in_signature` helper.
  **KEEP:** `test_relation_identity_is_a_concept_reference_not_a_bare_predicate`,
  `test_relation_identity_ignores_lexical_rendering_metadata`,
  `test_role_binding_set_canonicalizes_role_order` (RoleBinding/RoleBindingSet only).
- `tests/architecture/test_import_boundaries.py`, `tests/architecture/test_forbidden_symbols.py`,
  `tests/fixtures/journal.py` — **inspect first**; the earlier symbol grep
  matched these. Update only if they name a deleted symbol.

**Expected breakage:** `ImportError` in `test_relation_concept_identity.py` →
fixed by the edits above in the same commit.

---

## Chunk B — remove labels.py scaffolding

**File:** `propstore/core/labels.py`

**Why:** scaffolding with zero production importers (scout-labels.md #3/#1).

**Delete these symbols:**
- `JustificationRecord`
- `label_to_polynomial`
- `polynomial_to_label`

**Pre-deletion gate:** `grep -rn "JustificationRecord\|label_to_polynomial\|polynomial_to_label" propstore/`
must return nothing. (Scout says clean; verify, since deletion-first assumes it.)

**Caller fixes (same commit):**
- `tests/test_labelled_core.py` — remove `JustificationRecord` construction
  (lines ~222, 226) and any poly-helper use; delete the tests that exist only to
  exercise them.
- `tests/test_provenance_atms_equivalence.py` — same treatment for whichever of
  these symbols it imports.

**Expected breakage:** ImportError in the two named test files → fixed same commit.

---

## Chunk C — remove the `sameas` family

**Why:** fully registered (schema + charter) but **zero production consumers**
anywhere in `propstore/` (scout-families.md #2). The only references are two
schema-shape tests.

**Pre-deletion gate (mandatory — touches shared `registry.py`):**
`grep -rn "sameas" propstore/` and confirm every hit is either the family
declaration/registration itself or a test. No production `repo.families.sameas.*`
call site may exist. If one does, STOP — the scout was wrong, reassess.

**Delete:**
- `propstore/families/sameas/` (declaration.py, __init__.py)
- the `PropstoreFamily` enum member for sameas (registry.py)
- its entry in `PROPSTORE_FAMILY_REGISTRY` (registry.py ~632-646)
- its `world_charters()` charter entry, if present
- its sidecar table declaration, if any

**Caller fixes (same commit):**
- delete the two `sameas` schema-confirmation test files / tests.

**Risk:** medium — `registry.py` is shared infrastructure. Isolated commit,
explicit pathspec, full suite + pyright before and after.

**Note (not part of deletion):** scout also found 5 *schema-only* declaration
modules (`calibration`, `diagnostics`, `embeddings`, `meta`, `relations`) that
are sidecar tables, not registered storage families. These are NOT dead — they
back sidecar projections. Leave them. (`relations` is where the duplicate
`RelationEdge`/`ConflictWitness` names live — that belongs to the taxonomy work,
not here.)

---

## Chunk D — GATED: graph_types.py write-only fields

**Status: NOT READY.** Do not execute until the verification step below passes.

**Candidate deletions (per scout-graph-types.md, "written but never read"):**
- `ClaimNode.label` field (+ its `to_dict`/`from_dict` handling at lines
  ~431-432, ~481, and the `label_to_dict`/`label_from_dict` helpers IF they have
  no other user)
- `ClaimNode.attributes` field (+ `ClaimNode.attribute_mapping`/`attribute_value`
  IF unused) and its producer at `core/graph_build.py:223`
- `GraphDelta.then()` and `GraphDelta.is_identity` (test-only)

**Why gated — two unverified risks:**
1. `aspic_bridge/extract.py:96` calls `row.attribute_mapping()`. I have NOT
   confirmed `row`'s type. If `row` is a `ClaimNode`, then `attributes` IS read
   and must NOT be deleted. **Verify the receiver type of every
   `attribute_mapping()`/`attribute_value()` call site before touching
   `ClaimNode.attributes`.**
2. `ClaimNode.label` must not be confused with `ATMSClaimNode.label` /
   `AssertionAtom.label`, which are heavily read (all `atms.py` and
   `support_revision/` `.label` hits are those, not `ClaimNode`). Confirm no
   `.label` read resolves to a `ClaimNode` receiver.

**Verification deliverable:** a short note enumerating every `.attribute_mapping`,
`.attribute_value`, and `.label` production read and the static receiver type of
each. Only fields with zero `ClaimNode` receivers are deletable.

**Value note:** low line savings, touches core serialization + a live producer.
Lowest priority; only worth doing if the verification comes back fully clean.
`GraphDelta.then()`/`.is_identity` are independently safe (test-only) and could
be split into their own trivial commit regardless of the field question.

---

## Out of scope (taxonomy consolidation — separate, gated on package re-pin)

- Collapsing `GraphRelationType` into `{argumentation taxonomy} ∪ ConceptRelationshipType`.
- Sourcing `supports`/`rebuts`/`undercuts`/`undermines`/`supersedes`/`explains`
  from the `argumentation` package instead of 5 hand-rolled spellings.
- De-duplicating the `RelationEdge` / `ConflictWitness` names between
  `core/graph_types.py` and `families/relations/declaration.py`.

These wait until `formal-argumentation` is re-pinned to its current layout.
