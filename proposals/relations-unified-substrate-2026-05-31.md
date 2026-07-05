# Unified relation-instance substrate — design (2026-05-31)

Supersedes the binding/identity portions of
`proposals/relations-as-concepts-2026-05-31.md`. Synthesizes: the three census
reports (`reports/relations-binding-provenance-census.md`,
`reports/relations-assertion-identity-purpose.md`,
`reports/relations-one-binding-feasibility.md`), the migration facts
(`reports/relations-unification-migration-facts.md`,
`reports/relations-merge-commit-id-resolution.md`), and the Codex design consult
(`reports/relations-unification-codex.md`). Codex's design is adopted with one
correction (migration is cheaper than Codex feared — see §7).

## The 1 thing

There are **three** parallel spellings of "a relation/predicate applied to typed
arguments," differing only in filler type:
- `RoleBinding.value: object` (situated assertions; concept-id OR JSON blob)
- `GroundAtom`/`GroundLiteralKey` = (predicate, tuple[`Scalar`]) (grounding/ASPIC+)
- `SlotBinding` with `OntologyReference` fillers (lemon description-kinds)

Replace all three at the propstore boundary with **one** typed relation instance
over **one** tagged value type. A relation is a concept; its role signature is the
concept sense's `DescriptionKind`; `RelationConceptRef` is a concept FK. The
content-addressed merge behaviour of `assertion_id` (identical proposition →
identical id → one ATMS atom, multiple `source_claims`) is preserved; attribution
stays out of identity (Clark separation).

## 0. The atom: ONE proposition kind, two analysis states (literature-confirmed)

The projector spike (`reports/relations-phase2-projector-spike.md`) found ~4 of 9
claim types (`observation`, `mechanism`, `comparison`, `limitation`) are
prose+ABOUT, not relation-shaped. The literature
(`reports/relations-prose-ontology.md`) settles what they ARE: a prose statement
is the **surface form of a proposition whose logical form has not been extracted**,
NOT a terminal kind. Hobbs 1985 separates content `p'(e,…)` from assertion;
OntoLex separates `writtenRep` from `sense.reference`; Clark's `Statement` is
explicitly analyzable with a formalization upgrade path — no paper grounds an
irreducible text kind.

Therefore there is **one** semantic atom — the proposition — in one of two
**analysis states**, not two co-equal kinds (your "0,1,many" holds):

```
SemanticAtom = RelationInstance | UnanalyzedProposition

@dataclass(frozen=True, slots=True)
class UnanalyzedProposition:
    surface_text: str                       # the verbatim statement (no data loss)
    about: tuple[RelationValue, ...]         # the ABOUT concepts/refs that ARE known
    # structure is honestly typed PENDING; provenance records "not yet analyzed"
```

- `RelationInstance` is the **analyzed** state (structured relation + typed fillers).
- `UnanalyzedProposition` is the **pending** state: surface text preserved, ABOUT
  links kept, structure marked unknown. This is **honest ignorance about FORM** —
  the exact mirror of a vacuous Jøsang opinion's honest ignorance about VALUE. It
  neither fabricates a one-role `states(...)` relation (which Hobbs says the logical
  form must be *derived*, not assumed) nor blesses prose as terminal truth.
- It is **transient and upgradeable**: when analysis later derives the logical form,
  an `UnanalyzedProposition` is upgraded *into* a `RelationInstance`. Prose is a
  typed IOU the system is invited to resolve, not a permanent category.

Consequence: a prose-dominant claim projects to an `UnanalyzedProposition`, NEVER a
`TextAtom`-as-kind and NEVER a manufactured relation. The name
`UnanalyzedProposition` is **our coinage** (the *concept* is grounded — Hobbs,
McCarthy, Clark, Dowty — but no paper names the state). Caution: `comparison` has
no logical-form grounding in the collection and `limitation` rests on analogy to
McCarthy `ist` only — their relation signatures are weaker-grounded than
`observe`/`cause` and should be authored with that noted.

## 1. Unified value type (`propstore/core/relation_values.py`)

A closed tagged union — **no untyped map/list variant**, so it cannot decay into a
new blob:

```
RelationValue = ConceptValue | FamilyRefValue | ScalarValue | TextValue | CelValue
              | TimepointValue | ListValue | RelationInstanceValue
```
- `ConceptValue(reference: OntologyReference)` — identity = URI only; label is render metadata.
- `FamilyRefValue(family: {"claim","context","condition","assumption","justification"}, id)` —
  **distinct from a scalar string** so a claim-id / context-id / free-text with the
  same spelling never collide. Family set is **literature-derived**
  (`reports/relations-reference-kind-ontology.md`): claim (Clark/Groth/Hobbs),
  context (McCarthy ist/Bozzato), assumption (Dixon ATMS/Doyle), condition (Hobbs
  reified eventuality), justification (Clark supports/challenges, Dixon (A,c)).
  `policy` PRUNED — no literature grounding as a referent (Carroll's trust policy
  is a render-time operator, not a referent). `stance`/`proposition` added only if
  the family registry stores them distinctly. micropub/provenance-graph EXCLUDED by
  citation (reduce to principal claim; provenance stays in git notes per Clark
  separation). The value-vs-reference split itself is literature-principled (Hobbs
  1985 transparent/opaque arguments + `p'(e,…)` nominalization).
- `ScalarValue(str|int|float|bool)` — exactly the ASPIC `Scalar` vocabulary. NOT a
  catch-all for concepts/ids/CEL/time, and **NOT a home for prose**.
- `TextValue(text: str)` — a genuine text-valued **role filler / attribute** within
  an *analyzed* proposition (e.g. a `notes`/`label` attribute on a structured
  claim). Distinct from `ScalarValue(str)` (a scalar string is an enum/operator/
  token; a `TextValue` is honest prose) — prose is never absorbed into a scalar.
  **NARROWED (literature verdict, §0):** `TextValue` is NOT the home for a
  whole-proposition prose `statement`. A prose statement is an *unanalyzed
  proposition* (see §0), not a text-valued filler — so `TextValue` covers only the
  residual text attributes that sit *beside* real structure, never a proposition's
  entire content.
- `CelValue(expression: CelExpr)` — wraps the existing branded CEL source.
- `TimepointValue(lexical: str)` — separate from `ScalarValue(float)`; `KindType.TIMEPOINT`
  is semantically distinct from `QUANTITY` (CLAUDE.md), not dimensional.
- `ListValue(items, ordered: bool)` — repeated fillers without duplicate roles.
  **Multiplicity is preserved by default**: `ordered=True` (a sequence) is the
  default; `ordered=False` is opt-in set-semantics and canonicalizes by item
  payload — and even then preserves duplicate count (a multiset, not a set) so no
  distinction is silently dropped (adversary fix, principle: non-commitment).
  Reject cycles at construction.
- `RelationInstanceValue(instance)` — nested structured fillers; **must name a
  relation concept and pass a `DescriptionKind` signature** (the guardrail against
  a recursive blob).

## 2. One relation instance + generalized signature

```
RelationInstance(relation: RelationConceptRef, bindings: tuple[RelationBinding, ...])
RelationBinding(role: str, value: RelationValue)        # one binding per role; repetition -> ListValue
```
Replaces `RelationConceptRef + RoleBindingSet`, `GroundAtom` (at the propstore
boundary), and lemon `SlotBinding`. `SlotBinding.provenance` is **deleted** — the
census found it set-but-never-read; provenance lives on the instance/claim.

The lemon signature generalizes `ParticipantSlot.type_constraint: OntologyReference`
to a tagged `value_constraint: SlotValueConstraint`
(`ConceptConstraint | FamilyRefConstraint | ScalarConstraint | KindConstraint |
CelConstraint | TimepointConstraint | ListConstraint | RelationInstanceConstraint`).
`validate_slot_bindings` checks the tagged value against the tagged constraint
(bool-before-int; `KindConstraint` bridges to `KindType`). **`CATEGORY` membership
is GRADED, not crisp** (Dowty 1991 Def. 34 — categories are entailment clusters):
the check reports degree/fit, it does not assert crisp in/out membership that the
data does not support (adversary fix, principle: honest ignorance).

## 3. Identity canonicalization (fixes a latent bug)

`assertion_id` = SHA over `(relation.identity_key(), sorted (role, canonical_value),
context, condition)`. `canonical_value` is **tagged** per variant (e.g.
`ScalarValue(1)`→`("scalar","int","1")`, `ScalarValue("1")`→`("scalar","str","1")`,
`TextValue("x")`→`("text","x")` (distinct from `("scalar","str","x")`),
`ConceptValue`→`("concept",uri)`, floats via RFC8785, reject NaN/Inf, bool before int).

This fixes a **real present-day defect**: today's `RoleBinding.identity_payload`
uses `str(value)`, so `"1"` vs `1`, `"True"` vs `True`, and concept-id-vs-free-text
**already collide**. Merge behaviour is preserved (same relation instance + context
+ condition → same id; claim-id/provenance excluded).

## 4. Convergence per construction site
- **Situated assertion**: holds `RelationInstance`; codec serializes **tagged**
  values (current `str(value)` loses type — must change).
- **`merge/merge_claims.py`, `support_revision/projection.py`**: the synthetic
  `f"ps:relation:claim:{type}"` dies; both call ONE per-claim-**family** projector
  returning (per §0) `RelationInstance | UnanalyzedProposition` for claims, plus a
  parameterization atom for `equation`-shaped claims. The `content` JSON blob is
  **decomposed by analysis state**, never merely deleted:
  - **Relation-shaped claims** (e.g. `measurement` — spike-proven): each field →
    its typed filler (concept/numeric → `ConceptValue`/`ScalarValue`, `conditions`
    → `CelValue`); residual text *attributes* → `TextValue`; equation/parameter/
    variable/fit → parameterization owner path. Unknown subject → `FamilyRefValue`
    to the source claim (§9.1), never `ps:concept:unscoped`.
  - **Prose-dominant claims** (`observation`/`mechanism`/`comparison`/`limitation`):
    project to an **`UnanalyzedProposition`** (surface text + ABOUT links + pending
    structure), NEVER a manufactured `states(...)` relation and NEVER a
    `TextAtom`-as-kind. Upgradeable to a `RelationInstance` when analysis derives
    the logical form.
  The `UnanalyzedProposition` is a STORED, queryable atom (sidecar row + "pending
  analysis" provenance), never a dropped row — render filters, the build does not
  gate (Design checklist).
- **`importing/machinery.py`**: `SurfaceRoleBinding(role,value:str)` → a typed
  `SurfaceRelationBinding` carrying a tagged value payload. A bare untyped string is
  **admitted with a `shape-unknown` diagnostic** (NOT rejected/dropped) — the data
  reaches the sidecar carrying its uncertainty, render filters on the diagnostic.
  No shape-guessing (no concept-vs-text-vs-number inference), but no build-time gate
  either (Design checklist: nothing prevents data reaching the sidecar).
- **`policies.py`**: hard-coded relation ids → `RelationConceptRef` concept FKs;
  config scalars/operators/enums → `ScalarValue`. A value is `ConceptValue` only if
  the policy schema says it references a concept.
- **Grounding**: do NOT replace the external `argumentation.GroundAtom` (scalar-only,
  owned upstream). Add adapters `relation_instance_to_ground_atom` /
  `ground_atom_to_relation_instance(registry)` with a **strict representability
  check**; delete the `_scalar_value` stringify fallback (`grounding/facts.py:321-324`).
  The `PredicateRegistry` becomes the grounding view of the same constraint vocab.

## 5. Honesty / non-commitment checkpoints
- No `ps:concept:unscoped` fake subject; unknown subject = absence+diagnostic or source-claim ref.
- No guessing concept-vs-text-vs-number for bare import strings — require typed payload.
- No equation/parameter/fit stored as relation JSON — route to parameterization owner.
- No pre-merge of `measurement`/`observation`/`parameter` in storage — distinct authored relations; render policy may unify.
- No `TimepointValue`→`ScalarValue(float)` normalization in storage.
- No grounding stringify fallback — unrepresentable value = error at the boundary.

## 6. What dies / survives (updated kill list)
- **Dies**: `RoleDefinition`, `RoleSignature` (superseded by `DescriptionKind`/
  `ParticipantSlot`); `BOOTSTRAP_RELATION_IDS` string; the two `f"ps:relation:claim:"`
  f-strings; `SlotBinding.provenance` field; `_scalar_value` stringify fallback;
  the `ps:concept:unscoped` fabrication.
- **Transforms (not deleted)**: `RoleBinding`/`RoleBindingSet` → `RelationBinding`/
  `RelationInstance` (renamed+typed, not removed — they do real work); `SlotBinding`
  → folded into `RelationBinding`; `ParticipantSlot.type_constraint` → `value_constraint`.
- **Survives**: `ClaimConceptLinkRole`; `RelationConceptRef` (→ concept FK, renamed
  `RelationRef` via rope); the content-addressed identity + merge semantics; the
  external `GroundAtom` (behind adapters).
- **New (added)**: the `RelationValue` tagged union (`relation_values.py`); the
  `SemanticAtom = RelationInstance | UnanalyzedProposition` atom model (§0). The
  `content` JSON blob dies by **decomposition** (relation-shaped) or **honest
  unanalyzed-state** (prose-dominant) — never silently.
- **Phase-2 (unchanged, deferred)**: relation properties (functional/symmetric/transitive/inverse).

## 7. Migration — CHEAP (correcting Codex's pessimism)

Codex assumed persisted records must be rewritten. The migration scouts show the
identity is **derived, not source**:
- `assertion_id` is a computed `@property`, never stored; ATMS rebuilt in-memory each run.
- `relation_edge`/`conflict_witness`/snapshots are `.derived/` — rebuilt by `pks build`,
  keyed on `derived_store_content_hash` (fed by `_WORLD_CONTRACT_VERSION` /
  `PROPSTORE_WORLD_SCHEMA_VERSION`, already at v6).
- Merge-commit baked ids are **write-only history** — a scheme change leaves them as
  harmless stale strings (no raise, no re-derive-reject; worst case a silent lookup miss).

**Therefore the migration = bump the world contract version → content-hash miss →
full rebuild from git source.** No record rewriting, no old/new dual readers
(delete-first). Stale snapshots hard-fail on load and regenerate. One scheme in
production.

(Separate pre-existing bug to file: merge bakes a `ps:assertion:` id into a field
validated `^ps:claim:...$`, already tripping a build diagnostic today —
`reports/relations-merge-commit-id-resolution.md`.)

## 8. Phased plan + gates (spike already green: commit 14ec4318)

Each phase: TDD, `run_logged_pytest`, `pyright propstore`, commit with pathspec, report hash.

- **P-A Value type**: add `relation_values.py` (the tagged union) + canonicalization
  + property tests (round-trip, no-collision: `"1"`≠`1`, concept≠text). No call-site
  changes. Gate: new module green, suite at baseline.
- **P-B Signature generalization**: `ParticipantSlot.value_constraint` + tagged
  `validate_slot_bindings`; keep `published_in` spike passing. Gate: spike + validation tests.
- **P-C Atom + situated assertion**: `RelationInstance`/`RelationBinding` and the
  `SemanticAtom = RelationInstance | UnanalyzedProposition` union (§0);
  `SituatedAssertion` holds a `SemanticAtom`; codec serializes tagged values; bump
  contract version. Gate: identity round-trip + merge-collision tests + an
  `UnanalyzedProposition` round-trip; full rebuild green.
- **P-D Claim projector**: per-claim-family `project_claim_to_semantic_atom`
  returning `RelationInstance | UnanalyzedProposition | parameterization`
  (measurement → relation, spike-proven; observation/mechanism/comparison/limitation
  → `UnanalyzedProposition`; equation → parameterization). Delete both f-strings +
  the `unscoped` fabrication; migrate `merge_claims` + `support_revision/projection`.
  Gate: vanish greps `ps:relation:claim:` → 0; prose claim → `UnanalyzedProposition`
  (not a manufactured relation) test; equation → parameterization test.
- **P-E Importing + policies**: typed surface binding + diagnostics; policies → FKs/scalars.
- **P-F Grounding adapters**: `relation_instance ↔ ground_atom` + representability;
  delete `_scalar_value` fallback.
- **P-G Deletions**: `RoleDefinition`/`RoleSignature`/`BOOTSTRAP_RELATION_IDS`/
  `SlotBinding.provenance`; update arch guard (`RoleBindingSet(())` assertion); update
  remaining tests. Gate: full vanish scoreboard at target; `core/relations.py` reduced
  (verifier reads it); arch guards green.

## 9. Decisions (resolved 2026-05-31)
1. **Unknown subject → dangling pointer (DECIDED).** Emit a `FamilyRefValue`
   referencing the source claim. Never absence-only, never `ps:concept:unscoped`.
   The reference is honest ("subject is whatever this claim is about") and keeps the
   binding present for identity.
2. **`FamilyRefValue` family set → LITERATURE-DERIVED (RESOLVED).** Per
   `reports/relations-reference-kind-ontology.md`: **`{claim, context, condition,
   assumption, justification}`** (+ `stance`/`proposition` iff stored distinctly in
   the family registry). `policy` PRUNED (no grounding; render-time operator).
   micropub/provenance-graph excluded by citation. The value-vs-reference split is
   itself literature-principled (Hobbs 1985). Two cautions folded in: (a)
   `KindConstraint`/`CATEGORY` must heed Dowty 1991 graded-cluster membership, not
   crisp equality; (b) `ListValue` and CEL surface syntax are structural primitives
   with NO paper citation — kept, but not claimed as grounded.
3. **Rename → YES, via `rope` (DECIDED).** `RelationConceptRef → RelationRef`,
   `RoleBinding → RelationBinding`, `RoleBindingSet → RelationInstance`. Use `rope`
   for safe cross-codebase renames (not hand find-replace). Fold into the relevant
   phase (P-C for the instance/binding rename; the `RelationConceptRef→RelationRef`
   rename rides P-B/P-C).

## 10. Next gate
Adversary review against the non-commitment / honest-ignorance principles BEFORE
any P-A code. The design's biggest risk is the strict-no-fallback discipline (no
scalar stringify, no unscoped concept, no shape-guessing) silently degrading into
fabrication under implementation pressure — exactly what the adversary should hunt.
