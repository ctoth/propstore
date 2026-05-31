# Phase-2 SPIKE — does the claim projector decompose HONESTLY? (2026-05-31)

**Spike (additive, no production type touched, nothing wired in).** Prototype lives
in `tests/test_projector_spike.py` (green: `6 passed`, `pyright propstore` and
`pyright tests/test_projector_spike.py` both `0 errors`). It builds a minimal
`RelationValue` union + a `DescriptionKind` signature + a per-claim-family
`project_claim_to_fillers`, and decomposes two REAL-shaped claims — a structured
`measurement` and a free-text `observation` — using the ACTUAL field shapes from
`propstore/families/claims/declaration.py`.

**Sources read (not paraphrased):** the design proposal
`proposals/relations-unified-substrate-2026-05-31.md` (§1 value union incl.
`TextValue`, §4 projector, §5 honesty checkpoints); the three reports
(`relations-one-binding-feasibility.md`, `relations-unified-substrate-adversary.md`,
`relations-reference-kind-ontology.md`); and the source —
`families/claims/declaration.py` (the `ClaimTypeContract`s at lines 208-287 and the
`AtomicPropositionDocument` fields at 407-434), `cel_types.py` (`CelExpr` is a
branded `str`), `core/conditions/registry.py` (`KindType`), and the existing
projector `support_revision/projection.py:156-189`.

**The authored field set per claim type (the ground truth for both decompositions),
from `CLAIM_TYPE_CONTRACTS`:**
- `MEASUREMENT` — required `target_concept` + `measure`; `value_group`
  (`value`/`lower_bound`/`upper_bound`/`uncertainty`/`sample_size`/`confidence`);
  `unit_policy`; concept-link `target_concept → TARGET`. **`measure` is NOT a
  concept link** — it is a free-string measurement-kind token. Real instance
  (`tests/test_description_generator.py:153`): `target_concept="concept2",
  measure="jnd_absolute", value=0.05, unit="ratio"`.
- `OBSERVATION` — required `statement` (prose); nonempty `concepts`; concept-link
  `concepts → ABOUT`. **No `value_group`, no other structured role.** Real instance
  (`tests/test_concept_views.py:281`): `statement="Observed at concept1"` + concepts.

The current projector flattens everything after `subject` into ONE
`RoleBinding("content", <whole JSON blob string>)` (`projection.py:164`,
`merge_claims.py:87`) and fabricates `ps:concept:unscoped` for an unknown subject
(`projection.py:176`). That blob is exactly what this spike tries to replace with
typed fillers.

---

## Finding 1 — `measurement` decomposition (field → filler → honest?)

Every authored measurement field found an honest typed home. No field was forced
into the wrong kind, none was dropped, and **no JSON blob and no `TextValue` was
produced.** Asserted in `test_measurement_decomposes_to_typed_fillers`.

| field | value (real) | filler kind | honest? |
|---|---|---|---|
| `target_concept` | `ps:concept:open_quotient` | `ConceptValue` (concept FK) | **yes** |
| `measure` | `"jnd_absolute"` | `ScalarValue(str)` — enum-like token | **yes** (token, not prose, not a concept link) |
| `value` | `0.05` | `ScalarValue(float)` QUANTITY | **yes** |
| `lower_bound` | `0.04` | `ScalarValue(float)` QUANTITY | **yes** |
| `upper_bound` | `0.06` | `ScalarValue(float)` QUANTITY | **yes** |
| `uncertainty` | `0.01` | `ScalarValue(float)` QUANTITY | **yes** |
| `sample_size` | `42` | `ScalarValue(int)` QUANTITY | **yes** |
| `confidence` | `0.9` | `ScalarValue(float)` QUANTITY | **yes** |
| `uncertainty_type` | `"sd"` | `ScalarValue(str)` — enum-like token | **yes** (label token) |
| `unit` | `"ratio"` | `ScalarValue(str)` — unit token | **yes-ish** (see note) |
| `conditions` | `voice_quality == 'modal'` | `CelValue` (`ListValue[CelValue]` if >1) | **yes** |

`validate_against_signature(instance, MEASUREMENT_SIGNATURE)` returns `[]` — every
filler's kind matches its slot's declared `value_kind`, and both required roles
(`target`, `measure`) are present.

**Two honesty calls worth recording, both defensible:**
- `measure` and `uncertainty_type` are `ScalarValue(str)` **tokens**, not
  `TextValue`. This is honest under the design's own definition: a scalar string
  is "an enum/operator/token", a `TextValue` is prose (proposal §1). `"jnd_absolute"`
  and `"sd"` are closed-vocabulary tokens, not free prose. They are NOT cast from
  non-scalar data — they are already string tokens in the source.
- `unit="ratio"` is the one mild wrinkle: there is no `KindType.UNIT`, and unit
  algebra lives in `propstore.dimensions`. The honest filler is the unit string
  token (`ScalarValue(str)`); the dimensional meaning is owned elsewhere. No fake
  type was invented. (This is "yes-ish" only because a future `unit`-aware value
  kind could be more expressive — but the spike did not fabricate one.)

**Verdict on Finding 1: `measurement` decomposes honestly. No forced cast, no
no-home field, no blob. The design holds for structured claims.**

---

## Finding 2 — `observation` decomposition (is it relation-shaped at all?)

`observation`'s authored contract has exactly one structured role: `concepts →
ABOUT`. Its required field is `statement`, which is **prose** — and that prose is
*the whole proposition*, not a filler of some multi-role relation. There is no
subject/predicate/object decomposition to recover; the observation *is* the
sentence "Listeners reliably perceived breathiness increasing with open quotient…".

So: putting that prose into a `TextValue` and then into a one-role relation
(`relation=ps:relation:observation`, single binding `statement → TextValue`) would
be **a one-field blob wearing a type** — a fake relation signature the data does not
have. The `TextValue` itself is honest (it is genuinely prose, never
`ScalarValue(str)` — asserted in
`test_observation_is_not_relation_shaped_returns_text_atom`), but wrapping it in a
manufactured single-role `RelationInstance` is not.

The prototype therefore returns a **`NonRelationAtom`** (a `TextAtom`): a stored
artifact carrying `content: TextValue(statement)`, `about: tuple[ConceptValue]`
(the ABOUT concepts — the one real structured role), and `aux` for the other prose
fields (`notes`, `methodology`), each also `TextValue`, never `ScalarValue`. The
projector explicitly does **not** manufacture a `RelationInstance`
(`test_observation_text_is_not_castable_to_a_one_role_relation`).

This atom is a **stored, queryable artifact carrying the content verbatim** —
`result.content.text == doc.statement` is asserted — not a dropped row (satisfies
adversary risk #3 and Design checklist items 1/3/4: data reaches the sidecar, no
build-time gate).

**Verdict on Finding 2: `observation` is NOT relation-shaped. Its proposition is
irreducible prose ABOUT some concepts. `TextValue`-in-a-fake-one-role-relation is a
blob wearing a type; the honest representation is a distinct non-relation atom.**

---

## Finding 3 — the verdict on the fourth wall

**The design needs a non-relation `TextAtom` branch BEFORE P-A is wired into the
projector.** Evidence: the two claims sit on opposite sides of a real boundary.

- `measurement` (and structured kinds generally — `parameter`, `equation`-with-
  variables, the numeric value-group claims) decompose into a genuine
  `RelationInstance` over typed fillers. The unified-substrate design holds for them
  exactly as written.
- `observation` (and, by the same contract shape, `mechanism`, `comparison`,
  `limitation` — all four have `required=("statement",)`, `nonempty=("concepts",)`,
  `concept_link=ABOUT` only) are **text assertions, not relation instances.** They
  have one ABOUT role and an irreducible-prose proposition. Forcing them into a
  `RelationInstance` reintroduces precisely the blob-wearing-a-type fabrication the
  closed value union was built to prevent.

This is a *finding, not a failure*: "observation is not relation-shaped" is the
honest answer the spike was built to surface. The proposal's `project_claim_to_*`
(§4) already says it returns "a `RelationInstance` for relation-shaped claims, or a
parameterization/diagnostic atom for non-relation claims" — this spike makes that
fork concrete and shows the second branch is **load-bearing for an entire family of
prose claims (≈4 of the 9 claim types), not an edge case.** The branch must be a
first-class `NonRelationAtom`/`TextAtom` (a text assertion ABOUT concepts), distinct
from a `RelationInstance`, and it must be a stored queryable artifact.

The crucial honesty point the spike protects: **`TextValue` is the honest home for
prose, but it does not make `observation` a relation.** A `TextValue` is a legitimate
*role filler* (e.g. a `note` slot inside an otherwise-structured relation), and it is
the *content* of a `TextAtom` — but a relation whose *only* filler is the whole
proposition as `TextValue` is not a relation, it is a `TextAtom`. The substrate needs
both shapes.

**Recommendation: add the non-relation atom branch to the design before P-A code.**
Concretely: P-A's value union stays as designed (including `TextValue`), but the
projector contract (P-D) must return `RelationInstance | NonRelationAtom`, and
`NonRelationAtom` must be a real stored atom kind — not a `RelationInstance` with a
fabricated single `statement` role. Proceed to P-A for the *value type* as designed;
do NOT let the projector force prose-dominant claims into `RelationInstance`.

---

## Finding 4 — tagged identity distinguishes what `str(value)` collapsed

The present-day `RoleBinding.identity_payload` uses `str(value)`, so
`str(1) == str("1") == "1"` — a real collision. Three concrete cases the prototype's
tagged `canonical_value` keeps distinct (asserted green):

- `ScalarValue(1)` → `("scalar","int","1")` **≠** `ScalarValue("1")` →
  `("scalar","str","1")` (`test_tagged_identity_distinguishes_scalar_string_from_scalar_int`),
  while `str(1) == str("1")` is demonstrated in the same test as the collapse it fixes.
- For the same spelling `"open_quotient"`: `ConceptValue` →
  `("concept","open_quotient")`, `ScalarValue` → `("scalar","str","open_quotient")`,
  `TextValue` → `("text","open_quotient")` — all three distinct
  (`test_tagged_identity_distinguishes_prose_from_concept_and_token`), where today
  all three `str()` to the same key and collide.
- Two measurements identical except `value` (`0.05` vs `0.06`) get distinct
  `instance_identity` hashes (`test_two_measurements_differing_only_in_value…`),
  confirming the content hash is sensitive to the typed filler, not to a blob string.

**Verdict on Finding 4: yes — tagged canonicalization recovers distinctions the old
`str(value)` blob silently merged (scalar-int vs scalar-str; concept vs token vs
prose).**

---

## Summary verdict

- **Finding 1:** `measurement` decomposes fully into honest typed fillers — no
  forced cast, no no-home field, no blob, no prose. Design holds for structured claims.
- **Finding 2:** `observation` is prose-dominant with a single ABOUT role; its
  proposition is irreducible prose. `TextValue`-in-a-one-role-relation is a blob
  wearing a type.
- **Finding 3 (the fourth wall):** **the design needs a non-relation `TextAtom`
  branch before P-A is wired in.** `measurement → RelationInstance`,
  `observation → NonRelationAtom`. The branch covers ~4 of 9 claim types
  (observation/mechanism/comparison/limitation share the prose+ABOUT contract), so
  it is load-bearing, not an edge case. Proceed to P-A for the *value type* (incl.
  `TextValue`) as designed; the *projector* (P-D) must return
  `RelationInstance | NonRelationAtom` and must not force prose claims into a relation.
- **Finding 4:** tagged identity distinguishes `"1"` vs `1`, and concept vs token vs
  prose — fixing a present-day `str(value)` collision.

**Deliverables.** Prototype: `tests/test_projector_spike.py` (green, `6 passed`;
`pyright propstore` 0 errors; `pyright` on the spike file 0 errors). Report: this
file.

**Commit:** the two new paths (`tests/test_projector_spike.py`,
`reports/relations-phase2-projector-spike.md`) were committed together on `master`
as the single commit whose subject begins "Phase-2 projector spike: measurement
decomposes typed, observation is a TextAtom" (`git log --oneline -1 --
tests/test_projector_spike.py`). Because the hash is filled in by amending that
same commit, a literal hash here would always be one amend stale; the commit
subject is the stable locator. As of this writing `HEAD` = `c34125da`.
