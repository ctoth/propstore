# WS-O-gun-garcia: gunray defeasibility rewrite — Garcia 2004 generalized specificity properly

**Status**: OPEN
**Depends on**: `WS-O-gun-gunray` (existing-bug fixes and `EnumerationExceeded` wire-up must merge first; this WS is a much larger semantic rewrite that builds on the post-bugfix code)
**Blocks**: WS-K (argumentation pipeline benefits from Garcia-correct defeasibility — the source-trust argumentation-replaces-heuristic decision in D-8 leans on a paper-faithful defeater taxonomy and presumption handling); secondary downstream effect on WS-O-arg-bugs (clean DeLP semantics make the cluster-P HIGH bugs in argumentation more diagnosable because the gunray shape is no longer a moving target).
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)
**Spawned by**: D-17 (DECISIONS.md). Q's pushback on the original "split sections vs Antoniou vs Garcia" question chose the **full Garcia rewrite** as the highest-fidelity path to the cluster-B preferred reference.

---

## Why this workstream exists separately from WS-O-gun-gunray

WS-O-gun-gunray handles defects with paper-faithful intent already in code — `build_arguments` perf, `disagrees` cache, MED-2 mark memoization, MED-6 superiority validation, `anytime.EnumerationExceeded` wire-up per D-18. Those fixes preserve the current semantic contract.

This WS replaces the **semantic contract itself**:

- The four-section projection `{definitely, defeasibly, not_defeasibly, undecided}` is propstore-derived; `not_defeasibly` folds in a `defeater_touches` rule with no Garcia 04 backing (cluster-R MED-4). Cluster B flagged this gap from the consumer side: `RuleDocument.kind` collapses proper/blocking defeaters (D4); `StanceType` has no §4.1/§4.2 analog (M2); §6 default negation has no representation distinct from strong negation (M3); §6.2 presumptions lack the §6.3 comparison adjustment (M4).
- The KLM postulate suite from Kraus 1990 is named in CITATIONS only as the source of the `Or` postulate that closure.py implements. The full postulate set is not a property suite anywhere in `gunray/tests/`.
- `preference.GeneralizedSpecificity` has paper-cited code, but no test pins the §3.4 worked example — the canonical fingerprint for any Garcia-faithful implementation.

Per Q's no-fallback-shims rule (D-3, `feedback_no_fallbacks`), the rewrite replaces `not_defeasibly`'s shape, not preserves it.

## Scope: gunray + propstore (coordinated PRs)

Per Codex 2.26, schema-closure of the Garcia-faithful defeater distinction cannot complete from gunray-only work. Garcia §4.1/§4.2 require typed `RuleDocument` fields (`proper_defeater` vs `blocking_defeater`) on the propstore side, and that schema lives in propstore, not gunray. This WS therefore ships as **two coordinated PRs**:

- **PR-1 (gunray-side)**: steps 1–7 below. Implements the runtime semantic rewrite, surfaces proper-vs-blocking at `DialecticalNode`, replaces the section dict, ships KLM postulate property suite, splits Policy.
- **PR-2 (propstore-side)**: step 8 below. Widens `RuleDocument` to carry the proper/blocking distinction as a typed field, migrates `StanceType`, drops the `not_defeasibly` consumer surface, updates `propstore/grounding/grounder.py` and `propstore/grounding/inspection.py`. Pinned to PR-1's gunray release.

The schema widening is **in scope for this WS**. It is not deferred to WS-K or WS-N. Cluster-B M2 (StanceType analog) closes here.

## Review findings covered

This WS closes the following findings. "Done means done": every row has a green test gating it, and the symptom is gone from `gaps.md` (or its gunray-side equivalent in `../gunray/notes/`).

| Finding | Source | Citation | Description |
|---|---|---|---|
| **Cluster-R MED-4** | `reviews/2026-04-26-claude/cluster-R-gunray.md:350-368` | `gunray/src/gunray/defeasible.py:196-229` | `not_defeasibly` semantics is propstore-derived not Garcia 2004; the `defeater_touches` clause has no paper backing. |
| **Cluster-B D4** | `reviews/2026-04-26-claude/cluster-B-semantic-layer.md:71-72` | `propstore/families/documents/rules.py:88-91` | `RuleDocument.kind` does not distinguish proper-vs-blocking defeaters; Garcia 04 §4 (Defs 4.1, 4.2) requires the distinction at runtime AND at schema time. Acceptable argumentation lines (Def 4.7 condition 4) require the runtime distinction. Closes here via PR-2 schema widening. |
| **Cluster-B M1** | `reviews/2026-04-26-claude/cluster-B-semantic-layer.md:88-90` | `propstore/grounding/grounder.py:128-134` | Propstore has no specificity surface — delegates everything to gunray. After the rewrite the specificity comparison must be inspectable from the propstore side. |
| **Cluster-B M2** | `reviews/2026-04-26-claude/cluster-B-semantic-layer.md:91-92` | `propstore/stances.py:8` | `StanceType` enum has no proper-vs-blocking analog; rule kind collapses both. Closed when (a) gunray exposes the distinction at the `GroundDefeasibleRule` level (PR-1) *and* (b) the propstore schema is widened to carry it through (PR-2). Both ship in this WS. |
| **Cluster-B M3** | `reviews/2026-04-26-claude/cluster-B-semantic-layer.md:93-94` | `propstore/families/documents/rules.py` (RuleDocument body schema) | `not L` (default negation) absent from schema; only `~L` (strong negation) representable. Garcia 04 §6.1 requires both. Gunray-side: `parser.py` and `types.Rule.negative_body` already carry `not`-style atoms via `negation_semantics`; the rewrite must surface this as a separate-from-strong concept in the dialectical pipeline (PR-1) and at the propstore body schema (PR-2). |
| **Cluster-B M4** | `reviews/2026-04-26-claude/cluster-B-semantic-layer.md:95-96` | `propstore/families/documents/rules.py` | §6.2 presumptions: defeasible rules with empty body are syntactically allowed (`schema.DefeasibleTheory.presumptions` has its own slot per `gunray/CITATIONS.md:23`) but no separate priority handling and no §6.3 comparison-criterion adjustment. Closed when presumptions get correct specificity treatment per §6.3. |
| **CITATIONS gap** | `gunray/CITATIONS.md:41-45` | KLM 1990 cited only via Morris/Ross/Meyer 2020 restatement (the `Or` postulate). | The full KLM postulate suite (cumulativity, left logical equivalence, right weakening, reflexivity, cut, cautious monotonicity, `Or`) is the foundation of the proper-vs-blocking distinction and the rational-closure semantics. After this WS, every postulate has a green Hypothesis property test. |
| **Garcia §3.4 worked example** | `papers/Garcia_2004_DefeasibleLogicProgramming/notes.md:79-104` | none in `gunray/tests/` today | No test pins the §3.4 worked example as the canonical fingerprint. Closed when the example exists exactly in `tests/test_specificity.py` (or a new `tests/test_garcia_section_3_4.py`) and other tests reference it as the reference shape. |
| **`not_defeasibly` rename** | derived from MED-4 | `gunray/src/gunray/defeasible.py:196-235`, `propstore/grounding/grounder.py:237-287` | `not_defeasibly` becomes either two named sections (`defeated`, `probed`) per cluster-R Open Question 1, or is replaced entirely by the Garcia 04 YES/NO/UNDECIDED/UNKNOWN four-valued surface (Def 5.3). **Decision noted below** — see "Naming the four-section dict". Per Codex re-review #12, field names are paper-faithful: `yes`, `no`, `undecided`, `unknown` — NOT the propstore-derived `definitely`. |

Adjacent findings cheaper to close in the same rewrite (cluster-R LOW-7, the Policy enum mixing dialectical and closure concerns, is a refactor target. The KLM closure path is unaffected by Garcia 04, but separating Policy into `MarkingPolicy` and `ClosurePolicy` makes the Garcia-rewrite surface cleaner because the marking-side becomes the only thing the dialectical pipeline cares about):

| Finding | Citation | Why included |
|---|---|---|
| Cluster-R LOW-7 | `cluster-R-gunray.md:466-475`, `gunray/src/gunray/schema.py` `Policy` | Splitting Policy is a small refactor with zero-cost tests; doing it together with the dialectical-pipeline rewrite keeps the call surface coherent. |
| Cluster-R MED-7 | `cluster-R-gunray.md:394-405` | Strict-only fast path drops the full argument view. The Garcia-faithful rewrite must populate trace `arguments` for trivial single-rule strict arguments per `Argument(rules=frozenset(), conclusion=h)`. The fast path becomes consistent with the argument pipeline. |

Out of scope (lifted to other WS):

- Cluster-B B6 / B19 (msgspec `__post_init__` validation) — schema-validation drift, lives in WS-N.
- Cluster-B P3 (grounded atoms losing claim provenance) — propstore boundary problem, lives in WS-K and WS-M. The gunray-side change here makes provenance threading easier but does not implement it.
- Cluster-R HIGH-1 / HIGH-2 (build_arguments / disagrees performance) — performance pathology, lives in WS-O-gun-gunray. The Garcia rewrite does not regress them and may benefit from the refactor opportunity, but the perf fix is its own commit chain.

## Code references (verified by direct read)

### `not_defeasibly` machinery (being replaced)
- `gunray/src/gunray/defeasible.py:118-252` — `_evaluate_via_argument_pipeline`. Builds `warranted`, `defeater_probed` (lines 178-180), projects via four-clause section logic (lines 196-229). `not_defeasibly` is `(no AND NOT strict) OR defeater_touches`; the `defeater_touches` clause (lines 216-217, 223-224) is the propstore-specific Nute/Antoniou reading being replaced.
- `gunray/src/gunray/defeasible.py:159-160` — `_is_defeater_argument`: any rule with `kind == "defeater"` excludes the argument from `warranted`.
- `gunray/src/gunray/defeasible.py:280-301` — `_evaluate_strict_only_theory_with_trace`: strict-only fast path, only `definitely` and `defeasibly`.
- `propstore/grounding/grounder.py:237-287` — propstore-side normaliser ensuring all four keys present even when empty.

### Preference machinery (preserve and extend)
- `gunray/src/gunray/preference.py:63-191` — `GeneralizedSpecificity`. Simari/Loui Lemma 2.4 / Garcia Def 3.5 with `An(T)`. Empty-rules guard (lines 129-130) returns `False`. The rewrite must verify against §3.5–3.6 and §6.3, not just Lemma 2.4.
- `gunray/src/gunray/preference.py:193-291` — `SuperiorityPreference`. Floyd-Warshall over `(stronger_id, weaker_id)` pairs.
- `gunray/src/gunray/preference.py:294-401` — `CompositePreference`. First-criterion-to-fire composition.

### Dialectical machinery (Defs 4.1/4.2/4.7/5.1/5.3)
- `gunray/src/gunray/dialectic.py` — `proper_defeater`, `blocking_defeater`, `_defeat_kind`, `_expand` conds 2/3/4, `build_tree`, `mark`, `explain`. Cluster-R verdict says Defs 4.1/4.2 are correct here. The rewrite extends, does not replace. Block-on-block ban (`_expand` line 354-355) confirmed correct.

### Schema and parser surfaces
- `gunray/src/gunray/schema.py` — `DefeasibleTheory` already carries `presumptions` as a separate slot (validated empty-body, plumbed as defeasible kind per `CITATIONS.md:23`). Rewrite preserves the slot; §6.3 adjustment surfaces in `GeneralizedSpecificity`.
- `gunray/src/gunray/types.py` — `Rule.negative_body` already represents `not L` at the type level; the dialectical pipeline does not currently treat `not L` differently from `~L`.
- `propstore/families/documents/rules.py:88-91` — `RuleDocument.kind: Literal["strict", "defeasible", "defeater"]`. The defeater value collapses proper and blocking. PR-2 widens this to distinguish.
- `propstore/stances.py:8` — `StanceType` enum. PR-2 adds proper/blocking analog.

### Paper anchors (read these into the rewrite)

- **Garcia 2004** `notes.md:79-104` — Defs 3.5 (generalized specificity), 4.1 (proper defeater), 4.2 (blocking defeater), 4.7 (acceptable argumentation line including block-on-block ban). `notes.md:124-131` — Def 5.3 four-valued YES/NO/UNDECIDED/UNKNOWN; **no `not_defeasibly`**, **no `definitely`** — the four field names are exactly `yes`, `no`, `undecided`, `unknown` per the paper (Codex re-review #12). `notes.md:192-202` — §6.1 default negation, §6.2 presumptions, §6.3 specificity-with-presumptions.
- **Simari 1992** — predecessor; Lemma 2.4 antecedent-only syntactic check is the canonical obligation for `GeneralizedSpecificity`.
- **Pollock 1987** — foundational: prima facie reasons, undercutting vs rebutting. Garcia's proper/blocking echoes this but with strictly-preferred-vs-incomparable.
- **Antoniou 2007** — DR-Prolog ambiguity-blocking vs propagating. Propagating stays out-of-contract per `gunray/CITATIONS.md:106-113`. Antoniou's defeater-kind reading drove `not_defeasibly`'s current shape and is what's being replaced.
- **Maher 2021** — alternative compilation route, not taken per `CITATIONS.md:98-102`. Used here only for stratification-hint cross-checks.
- **Bozzato 2018** — context-aware extension; downstream consumer that benefits from a clean Garcia surface. Not modified here.
- **Diller 2025** — already partial in `grounding.py:_simplify_strict_fact_grounding`. Cluster-R LOW-1 CITATIONS miscategorisation gets corrected in step 9; the simplification itself is unchanged.
- **Kraus 1990** — newly retrieved. KLM postulates: reflexivity, left logical equivalence, right weakening, cut, cautious monotonicity, `Or`. Each becomes a Hypothesis property test.
- **Lehmann 1989** — newly retrieved. Dirname `_1989` is S2 metadata; content is the 1992 paper. Rational closure construction; relevant to the closure-vs-marking Policy split (cluster-R LOW-7).

## First failing tests (write these first; they MUST fail before any production change)

The §3.4 worked-example test is the *first* test. Everything else hangs off it. Per Codex 2.24, **TDD discipline is in force throughout this WS**: every step in the production change sequence begins with the relevant test failing for the reason the step is about to fix, and ends with that targeted test passing. Tests run continuously throughout the rewrite — not deferred to acceptance.

1. **`tests/test_garcia_section_3_4.py`** (new — first failing test for this WS)
   - Constructs the §3.4 worked example verbatim from `papers/Garcia_2004_DefeasibleLogicProgramming/notes.md`. The example involves `flies(X) -< bird(X)` and `~flies(X) -< chicken(X)` plus background facts about Tina, Tweety, Opus, etc. (see `notes.md:79-85`).
   - Asserts each step of Def 3.5 generalized-specificity comparison matches the paper's stated outcome literally.
   - Asserts `prefers(<{r_chicken_no_fly}, ~flies(tina)>, <{r_bird_fly}, flies(tina)>)` is `True` because the chicken antecedents activate the bird argument's antecedents but not vice versa.
   - Tests every literal that the paper resolves, in the order the paper resolves them. Each assertion cites the paragraph and figure number of the paper.
   - **Must fail today**: today's `GeneralizedSpecificity` may compute the right answer (the test for it in `test_specificity.py` passes), but it has not been pinned against the §3.4 worked example as a unit. The fingerprint test does not exist.

2. **`tests/test_proper_vs_blocking_defeater.py`** (new)
   - Constructs three minimal theories:
     - **Theory A**: two arguments where one is strictly preferred → exactly proper defeater per Def 4.1.
     - **Theory B**: two arguments where neither is strictly preferred → exactly blocking defeater per Def 4.2.
     - **Theory C**: a chain `A1` blocks `A2` blocks `A3` → forbidden by Def 4.7 condition 4.
   - Asserts `dialectic._defeat_kind(...)` returns `"proper"`, `"blocking"`, and the chain in C is rejected by `_expand`.
   - Asserts each defeater kind is **observable from outside `dialectic.py`** — that is, `DialecticalNode` exposes `defeater_kind: Literal["proper", "blocking", "root"]` so callers can inspect the marking discipline. Today this is recoverable from `_defeat_kind` only via private call.
   - **Must fail today**: cluster-B D4 — the kind is not exposed at the `DialecticalNode` level for downstream consumers. (Verify by reading `gunray/src/gunray/dialectic.py:DialecticalNode:191-200`.)

3. **`tests/test_garcia_default_negation.py`** (new)
   - Constructs a §6.1 default-negation example: `r1: a -< b, not c` and `r2: c -< d` with facts `b, d`. Argument for `a` exists only if `c` is not warranted; argument for `c` exists from `r2`.
   - Asserts default-negated body literals attack as `not L` (negation as failure), distinct from strong-negation `~L` attack.
   - Asserts the four-valued projection treats `a` correctly: `a` is **not** warranted because `c` is warranted via `r2`.
   - **Must fail today**: the dialectical pipeline does not separately treat `not L` body literals — they collapse to the same `negative_body` slot used by the Datalog evaluator's stratified-negation path. Garcia §6.1 specifically distinguishes these in the *argumentation* layer.

4. **`tests/test_garcia_presumptions.py`** (new)
   - Constructs §6.2 presumption examples: `h -< true` (presumption shorthand for empty-body defeasible rule). At least three presumptions interacting via §6.3's adjusted specificity criterion.
   - Asserts presumption-vs-presumption comparison handles the §6.3 case correctly (presumption-based arguments use no evidence, so vanilla Lemma 2.4 collapses; §6.3 prescribes the alternative comparison).
   - Asserts presumption arguments participate in dialectical trees as expected (they can both attack and be attacked, they can be warranted, etc.).
   - **Must fail today**: `GeneralizedSpecificity._covers` (line 180-183) returns `True` for vacuous coverage with the comment "Vacuous coverage is valid only after the empty-rule incomparability guard in `prefers`." The §6.3 adjustment is not implemented.

5. **`tests/test_klm_postulates.py`** (new)
   - For each KLM postulate from Kraus 1990 (reflexivity, left logical equivalence, right weakening, cut, cautious monotonicity, `Or`), a Hypothesis `@given` property test that generates random small theories and asserts the postulate holds for the warranted-set under the Garcia 04 four-valued projection.
   - Properties to encode (state explicitly so the test author cannot drift):
     - **Reflexivity**: every `α` warrants `α` if `α` is a fact in `Π`.
     - **Left logical equivalence (LLE)**: if `α ≡ β` under `Π`, the warranted-set conditioned on `α` equals that conditioned on `β`.
     - **Right weakening (RW)**: if `α |~ β` (defeasibly entails) and `Π ⊨ β → γ`, then `α |~ γ`.
     - **Cut**: if `α |~ β` and `α ∧ β |~ γ`, then `α |~ γ`.
     - **Cautious monotonicity (CM)**: if `α |~ β` and `α |~ γ`, then `α ∧ β |~ γ`.
     - **`Or`**: if `α |~ γ` and `β |~ γ`, then `α ∨ β |~ γ`.
   - Each property is a `@given` Hypothesis test marked with `@pytest.mark.property` (per WS-A's discipline).
   - **Must fail today**: no KLM postulate property tests exist. Lehmann 1989 / 1992 rational closure is implemented for closure.py only; the dialectical-tree path has no postulate verification at all.

6. **`tests/test_section_naming_replacement.py`** (new — gates the rename of `not_defeasibly`)
   - Asserts that `DefeasibleModel.sections` does *not* contain a `not_defeasibly` key.
   - Asserts that `DefeasibleModel.sections` is a `GarciaSections` value with exactly the Garcia 04 Def 5.3 surface: `yes` (warranted), `no` (complement warranted), `undecided` (some argument exists for atom or complement, neither warranted), and `unknown` (no argument exists for atom or complement). **No `not_defeasibly`.** **No `defeater_touches` synthetic atoms.** **No `defeasibly` field — that name is gone.** **No `definitely` field — per Codex re-review #12, the paper's four field names are `yes`, `no`, `undecided`, `unknown`; the propstore-derived `definitely` name is rejected as paper-unfaithful.**
   - Defeater-kind argument participation is captured separately on the trace (a new field, e.g. `DefeasibleTrace.defeater_arguments`) — it is observable but does not pollute the section dict.
   - **Must fail today**: every existing call site that reads `model.sections["not_defeasibly"]` must be migrated. Per Q's "no fallback shims" rule (D-3, `feedback_no_fallbacks`, `feedback_update_callers`), the migration is mechanical and total — no aliases.

7. **`tests/test_strict_only_argument_view.py`** (new — closes cluster-R MED-7)
   - Constructs a strict-only theory and calls `evaluate_with_trace`.
   - Asserts `trace.arguments` is non-empty; specifically, contains `Argument(rules=frozenset(), conclusion=h)` for every strict consequence.
   - Asserts `trace.markings[h] == "U"` for every such atom (Proposition 5.1 — strictly derived atoms are warranted).
   - Asserts that for the strict-only fast path the Garcia Def 5.3 surface satisfies: every Π-strict consequence appears in `GarciaSections.yes`; `GarciaSections.no` and `GarciaSections.undecided` are empty; `GarciaSections.unknown` contains every literal in the Herbrand base for which no argument exists (i.e., everything not derivable from Π). The strict-only invariant is paper-faithful: `yes ⊇ Π-strict consequences`, and atoms with no argument fall to `unknown` per Garcia Def 5.3 — NOT to a propstore-derived `definitely` field. There is no `defeasibly` field and no `definitely` field to compare against — both names are dead per Codex re-review #12.
   - **Must fail today**: `_evaluate_strict_only_theory_with_trace` does not populate `trace.arguments`, and the section invariant cannot be expressed against the new field names because they do not exist yet.

8. **`tests/test_propstore_rule_kind_widened.py`** (new — propstore-side, gates PR-2)
   - Constructs a `RuleDocument` with `kind="proper_defeater"` and another with `kind="blocking_defeater"`. Asserts both round-trip through msgspec validation.
   - Asserts the legacy `kind="defeater"` value is **rejected** at validation time (not silently coerced; per `feedback_no_fallbacks`).
   - Asserts `propstore/stances.py` `StanceType` exposes the proper/blocking analog and that the family-document layer surfaces it through `propstore/grounding/inspection.py:format_ground_rule`.
   - **Must fail today**: `RuleDocument.kind` is `Literal["strict", "defeasible", "defeater"]` (no proper/blocking) and `StanceType` has no analog.

9. **`tests/test_workstream_o_gun_garcia_done.py`** (new — gating sentinel)
   - `xfail` until WS-O-gun-garcia closes; flips to `pass` on the final commit.

## Production change sequence

Each step lands in its own commit `WS-O-gun-garcia step N — <slug>`. Steps 1–7 are gunray-side (PR-1); step 8 is propstore-side (PR-2), pinned to the gunray release that ships PR-1; step 9 is docs and seal across both repos.

**TDD discipline (per Codex 2.24)**: every step starts with the relevant test failing and ends with that test passing. Tests run continuously on every step — `uv run pytest <targeted-test>` after writing it (failing), then again after the production change (passing). The full suite runs on each commit; the acceptance gate at the end is a re-run, not a first run. There is no "do not run tests during the rewrite" period.

### Step 1 — Surface proper-vs-blocking distinction at DialecticalNode

The `kind="defeater"` rule kind stays in gunray. Garcia §4 defeaters exist at the *argument-pair* level and are computed at runtime by `_defeat_kind`. What's missing is exposure of that classification to consumers.

Changes:
- Add `defeater_kind: Literal["proper", "blocking", "root"]` to `DialecticalNode`, populated during `build_tree` from `_defeat_kind`.
- Expose `dialectic.classify_defeat(attacker, target, theory, criterion) -> Literal["proper", "blocking", "none"]` as a public function.

Acceptance: `tests/test_proper_vs_blocking_defeater.py` was failing at step start (the `defeater_kind` attribute did not exist on `DialecticalNode`) and turns green at step end. `uv run pytest tests/test_proper_vs_blocking_defeater.py` is run before the production edit (RED) and after (GREEN); both runs are recorded in the commit message.

### Step 2 — Replace the four-section projection with Garcia 04 Def 5.3 surface

Drop the `not_defeasibly` key from `DefeasibleModel.sections`. The new surface is the Garcia Def 5.3 four-valued surface, **paper-faithfully named** (per Codex re-review #12):
- `yes`: warranted-atoms (`mark(tree) == "U"`).
- `no`: atoms whose complement is warranted.
- `undecided`: atoms with arguments but no warrant on either side.
- `unknown`: atoms with no argument for either the atom or its complement (Def 5.3 UNKNOWN).

The `defeater_touches` clause is gone. Atoms touched by defeater-kind arguments are recorded on `DefeasibleTrace.defeater_probed_atoms: frozenset[GroundAtom]` and are *also* classified into `yes`/`no`/`undecided`/`unknown` per the standard rules. There is no longer a synthetic "defeater_touches → not_defeasibly" rule.

`DefeasibleModel.sections` is replaced with a typed view:

```python
@dataclass(frozen=True, slots=True)
class GarciaSections:
    yes: ModelFacts
    no: ModelFacts
    undecided: ModelFacts
    unknown: ModelFacts
```

The four field names mirror Garcia Def 5.3 (YES/NO/UNDECIDED/UNKNOWN) exactly. The previously-considered `definitely` name (a propstore-derived Π-strict refinement of `yes`) is **rejected** per Codex re-review #12 as paper-unfaithful. Π-strict information remains observable as a property over `yes` (e.g. `trace.strict_consequences` or `model.strict_subset()`), not as a separate section field.

By construction `yes`, `no`, `undecided`, `unknown` partition the Herbrand base relevant to the theory; no atom appears in two sections. No `defeasibly` field exists; the previous `defeasibly` name is gone in favour of `yes`.

Per `feedback_no_fallbacks`: no `not_defeasibly` alias, no `defeasibly` alias, no `definitely` alias, no compatibility property. The propstore-side migration in PR-2 (step 8) updates every call site.

Acceptance: `tests/test_section_naming_replacement.py` was failing at step start (the `GarciaSections` type did not exist; the section dict still had `not_defeasibly`) and turns green at step end. RED → GREEN recorded in commit.

### Step 3 — Default negation in extended DeLP (§6.1)

Today `types.Rule.negative_body` carries `not L` literals; the Datalog evaluator handles them via stratified negation, but the dialectical pipeline does not.

- `arguments.build_arguments` treats `not L` body literals as additional attack points: an argument for a rule with `not L` in body is conditioned on `L` not being warranted; if `L` later becomes warranted, the argument is defeated.
- `dialectic._expand` adds default-negation acceptability: a default-negated body atom is a sub-target that subsequent counter-arguments may attack at, distinct from strong-negation `~L` rebut.

Acceptance: `tests/test_garcia_default_negation.py` was failing at step start (default-negation literals collapsed to strong-negation in the dialectical pipeline) and turns green at step end. RED → GREEN recorded.

### Step 4 — Presumptions per §6.2 with §6.3 specificity adjustment

The presumption schema slot exists; the §6.3 specificity adjustment does not. `GeneralizedSpecificity.prefers` short-circuits when either side has empty rules (`preference.py:129-130`). Presumption arguments have *non-empty rules* (the presumption rules) but *empty antecedent set* `An(T)`.

Garcia §6.3:
- Two presumption-only arguments compare via §6.3's alternative criterion when antecedent comparison vacuously holds in both directions.
- A presumption-only and an antecedent-bearing argument are incomparable under specificity unless rule-priority breaks the tie.

`GeneralizedSpecificity` distinguishes three cases: both `An(T)` empty AND both rule sets non-empty → §6.3 alternative; one empty / one non-empty → incomparable; both non-empty → vanilla Lemma 2.4.

Acceptance: `tests/test_garcia_presumptions.py` was failing at step start (vacuous-coverage behaviour produced wrong results on §6.2 examples) and turns green at step end. RED → GREEN recorded.

### Step 5 — KLM postulate property suite

Author `tests/test_klm_postulates.py` as Hypothesis `@given` properties over small random theories. This is the safety net for steps 1–4 and runs continuously alongside them.

Not every KLM postulate is a DeLP theorem. The suite codifies which hold. For postulates DeLP does not satisfy generally, the test is `@pytest.mark.xfail(strict=True)` with the reason citing the Garcia section that explains why.

Acceptance: `tests/test_klm_postulates.py` was empty at step start (no KLM property file existed) and turns green (mix of `pass` and `xfail(strict=True)` per postulate) at step end. The targeted test run before authoring fails with `collected 0 items`; after authoring it runs the property suite. RED → GREEN recorded.

### Step 6 — Strict-only fast path emits the trivial argument view

Cluster-R MED-7. `_evaluate_strict_only_theory_with_trace` populates `trace.arguments` with `Argument(rules=frozenset(), conclusion=h)` for every strict consequence, and sets `trace.markings[h] = "U"` for each.

The fast-path invariant on the new section type is: every strict consequence appears in `yes`; `no == undecided == frozenset()`; and every literal in the Herbrand base with no argument appears in `unknown`. There is no `defeasibly` field and no `definitely` field — those idioms from the pre-rewrite code are gone.

Acceptance: `tests/test_strict_only_argument_view.py` was failing at step start (`trace.arguments` was empty for the strict-only path) and turns green at step end. The strict-consequence-in-`yes` and no-argument-in-`unknown` invariants are asserted in the same test. RED → GREEN recorded.

### Step 7 — Split Policy enum (cluster-R LOW-7)

`schema.Policy` becomes:

```python
class MarkingPolicy(StrEnum):
    BLOCKING = "blocking"
    # PROPAGATING is out-of-contract (CITATIONS:106-113); enum value reserved for future Antoniou variant if Q reverses D-?

class ClosurePolicy(StrEnum):
    RATIONAL = "rational"
    LEXICOGRAPHIC = "lexicographic"
    RELEVANT = "relevant"
```

`adapter.evaluate` takes both as separate keyword arguments. The dispatcher routes to the closure engine if `closure_policy` is set; otherwise to the dialectical-tree pipeline with `marking_policy`. Both being set raises `ValueError` (these are alternatives, not composable per gunray's current architecture).

Per `feedback_no_fallbacks`: no string alias for the old `Policy` enum values. Every caller updates in one pass.

Acceptance: a new `tests/test_policy_split.py` was failing at step start (the split enums did not exist) and turns green at step end, asserting both-set rejection and routing semantics. Existing closure and dialectical-path tests still pass; no regressions in the targeted-test run before the commit lands. RED → GREEN recorded.

### Step 8 — Propstore-side schema widening and migration (PR-2)

This is the propstore-side coordinated step. PR-1 (steps 1–7) lands first in gunray; PR-2 lands in propstore pinned to the new gunray release.

Schema-side changes (cluster-B D4 / M2 / M3 closure):

- `propstore/families/documents/rules.py`: widen `RuleDocument.kind` to `Literal["strict", "defeasible", "proper_defeater", "blocking_defeater"]`. The legacy `"defeater"` value is **removed**, not aliased; per `feedback_no_fallbacks`, msgspec validation rejects it. Authoring paths that previously emitted `"defeater"` are updated to compute proper-vs-blocking from the new gunray runtime classification at promote time.
- `propstore/families/documents/rules.py` (RuleDocument body schema): add a body-literal kind distinguishing `not L` (default negation) from `~L` (strong negation), surfacing the §6.1 distinction at the schema level. Cluster-B M3 closes.
- `propstore/stances.py`: `StanceType` gains proper-vs-blocking analogs. The propstore stance machinery wraps gunray's defeater_kind. Cluster-B M2 closes.

Consumer-side migration:

- `propstore/grounding/grounder.py:237-287` (the four-section normaliser) updates: drop the `not_defeasibly` key entirely; project the new `GarciaSections` view through to consumers; surface `defeater_probed_atoms` from the trace.
- Audit every `model.sections["not_defeasibly"]` reference in propstore. Each becomes `model.sections.no`, `model.sections.undecided`, a defeater-probed-atoms read from the trace, or is deleted.
- `propstore/grounding/inspection.py:format_ground_rule` updates to surface the proper-vs-blocking distinction in render output (cluster-B M2 propstore-side).
- `propstore` `pyproject.toml` pin updates to the new gunray version published by PR-1.

Migration tests run continuously: `tests/test_grounding_grounder.py`, `tests/test_defeasible_conformance_tranche.py`, `tests/test_propstore_rule_kind_widened.py`. The propstore CI runs against the new gunray pin; no caller may reference the old `not_defeasibly` shape or the old `kind="defeater"` value.

Acceptance: `tests/test_propstore_rule_kind_widened.py` was failing at step start (legacy `kind="defeater"` was accepted; no proper/blocking values existed) and turns green at step end. The full propstore test suite passes against the new gunray pin. `Grep -r "not_defeasibly" propstore` returns zero matches. `Grep -rn '"defeater"' propstore/families` shows only paper-citation strings, no schema literal values.

### Step 9 — Documentation and seal

- Update `gunray/CITATIONS.md`: Kraus 1990 promoted from "informational" to "load-bearing" with section reference to `tests/test_klm_postulates.py`. Lehmann 1989 (rational closure) cited at `closure.py` since it's the actual algorithm source. Antoniou 2007 stays in "out-of-contract" but with a note that the propstore-derived `not_defeasibly`-via-defeater-touches reading has been removed.
- Update `gunray/ARCHITECTURE.md`: document the new `GarciaSections` shape (fields `yes`, `no`, `undecided`, `unknown` — explicitly note `defeasibly` and `definitely` are no longer field names), the `defeater_kind` field on `DialecticalNode`, the §6.1 default-negation argumentation handling, the §6.3 presumption specificity adjustment.
- Update `gunray/notes/b2_defeater_participation.md`: mark the old Nute/Antoniou reading as superseded; record the rationale.
- Update `propstore/families/documents/rules.py` docstring and any `propstore/ARCHITECTURE.md`-equivalent docs to reflect the widened `RuleDocument.kind` and the §6.1 body-literal-kind addition.
- Flip `tests/test_workstream_o_gun_garcia_done.py` from `xfail` to `pass`.
- Update `reviews/2026-04-26-claude/workstreams/WS-O-gun-garcia.md` STATUS to `CLOSED <gunray-sha> + <propstore-sha>` (two SHAs, since the work spans two repos).
- Update `docs/gaps.md` (propstore-side) and `gunray/notes/gaps.md` (gunray-side) to remove the rows listed above.

Acceptance: sentinel test passes; gaps files updated in both repos; CITATIONS reflects the new state; both PRs reference each other in their commit messages.

## Acceptance gates

Before declaring WS-O-gun-garcia done, ALL must hold:

- [ ] `uv run pyright src/gunray` (in `../gunray`) — passes with 0 errors.
- [ ] `uv run pyright propstore` — passes with 0 errors against the new gunray pin.
- [ ] All tests listed above turn green:
  - `tests/test_garcia_section_3_4.py`
  - `tests/test_proper_vs_blocking_defeater.py`
  - `tests/test_garcia_default_negation.py`
  - `tests/test_garcia_presumptions.py`
  - `tests/test_klm_postulates.py` (mix of pass and `xfail(strict=True)` per postulate)
  - `tests/test_section_naming_replacement.py`
  - `tests/test_strict_only_argument_view.py`
  - `tests/test_policy_split.py`
  - `tests/test_propstore_rule_kind_widened.py`
  - `tests/test_workstream_o_gun_garcia_done.py` (gating sentinel — flips from `xfail` to `pass`).
- [ ] Existing gunray tests still pass: `tests/test_specificity.py`, `tests/test_superiority.py`, `tests/test_dialectic.py`, `tests/test_defeasible_evaluator.py`, `tests/test_presumptions.py`, `tests/test_explain.py`, `tests/test_conformance.py`. The §3.4 worked-example test references `test_specificity.py` for the existing equivalence-class properties.
- [ ] Existing propstore grounding tests still pass: `tests/test_grounding_translator.py`, `tests/test_grounding_grounder.py`, `tests/test_defeasible_conformance_tranche.py`. The latter changes section-name expectations (`not_defeasibly` → `no`) and is updated in step 8.
- [ ] No `not_defeasibly` reference remains in `propstore/` or `gunray/src/` — `Grep -r "not_defeasibly" propstore gunray/src` returns zero matches.
- [ ] No `defeasibly` field-name reference remains in either tree — that vocabulary is gone post-rewrite. (Paper citations and prose mentions are fine; field/dict-key references are not.)
- [ ] No `definitely` field-name reference remains in either tree — strict consequences are trace metadata or a property over `yes`, not a section.
- [ ] No legacy `RuleDocument.kind == "defeater"` literal remains in propstore source — only `"proper_defeater"` and `"blocking_defeater"` are valid.
- [ ] `gunray/CITATIONS.md` reflects KLM 1990 promotion and Lehmann 1989 inclusion.
- [ ] `gunray/ARCHITECTURE.md` documents the new section shape and the §6.1 / §6.3 extensions.
- [ ] `gunray/notes/b2_defeater_participation.md` records the supersession of the propstore-derived defeater-touches rule.
- [ ] WS-O-gun-garcia property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged gunray/propstore test runs or a named companion run.
- [ ] `docs/gaps.md` (propstore) and `gunray/notes/gaps.md` (gunray) have no open rows for the findings table at the top.

## Done means done

This workstream is done when **every finding in the table at the top is closed**, not when "most" are closed.

- Cluster-R MED-4: the `not_defeasibly` section is gone. Every consumer of `model.sections` uses `yes`/`no`/`undecided`/`unknown` per Garcia 04 Def 5.3. The `defeasibly` and `definitely` field names are gone too; strict consequences remain observable as trace metadata or a property over `yes`.
- Cluster-B D4: gunray-side `DialecticalNode.defeater_kind` is observable; `dialectic.classify_defeat` is public; the proper-vs-blocking distinction is testable from the propstore boundary; AND propstore `RuleDocument.kind` carries the typed proper/blocking distinction at the schema level.
- Cluster-B M1: propstore-side specificity inspection — covered structurally (the new gunray `GeneralizedSpecificity` exposes a `compare` API that returns the comparison rationale per §3.5; `propstore/grounding/inspection.py` surfaces it for render).
- Cluster-B M2: gunray-side proper-vs-blocking distinction is exposed; propstore `StanceType` carries the typed analog. Both PR-1 and PR-2 ship.
- Cluster-B M3: §6.1 default negation has its own argumentation-pipeline behaviour (PR-1) and its own body-literal kind in the propstore schema (PR-2).
- Cluster-B M4: §6.2 presumptions get the §6.3 specificity adjustment.
- KLM postulate suite from Kraus 1990: every postulate has a Hypothesis property test that either passes or `xfail(strict=True)`s with a paper-cited reason.
- Garcia §3.4 worked example pinned exactly in `tests/test_garcia_section_3_4.py`.
- The gating sentinel test `tests/test_workstream_o_gun_garcia_done.py` has flipped from `xfail` to `pass`.

If any one of those is not true, WS-O-gun-garcia stays OPEN.

## Naming the four-section dict

Cluster-R Open Question 1 ("split `not_defeasibly` into `defeated` and `probed`, or keep conflated?") is resolved by **not splitting and not keeping** — the field is removed entirely. The Garcia 04 Def 5.3 surface is the authoritative shape: `yes` (warranted), `no` (complement warranted), `undecided` (some argument exists, neither warranted), `unknown` (no argument exists for atom or complement). Defeater-probed atoms are observable on the trace (`DefeasibleTrace.defeater_probed_atoms`) for callers that genuinely need that view. The pre-rewrite `defeasibly` field name is gone; `yes` subsumes it. The propstore-derived `definitely` field name is gone; Π-strict consequences remain trace metadata or a property over `yes`.

If a future propstore consumer turns out to need the `defeater_probed`-as-section view back, it can re-introduce a propstore-side projection from `trace.defeater_probed_atoms`. Per the project principle on `imports_are_opinions`: every imported KB row is a defeasible claim with provenance, and a synthetic section that conflates "warrant fails" with "defeater rule probed" violates the non-commitment discipline (cluster-B P1).

## TDD execution discipline

Per Codex 2.24, this WS runs tests continuously throughout the rewrite. Every step in the production change sequence:

1. Begins with the targeted test failing for the reason the step is about to fix (`uv run pytest <test>` shows RED).
2. Ends with that test passing (`uv run pytest <test>` shows GREEN).
3. Both runs are recorded in the step's commit message as evidence the failing-then-passing transition happened.

The full suite runs on every commit. The acceptance gate at the end of the WS is a re-run of already-green tests — not a first-time test invocation. Production state under `knowledge/` and `sidecar/` is not modified by tests; tests construct their own fixtures.

## Cross-stream notes

- This WS depends on **WS-O-gun-gunray** completing first. The existing-bug fixes (HIGH-1 build_arguments perf, HIGH-2 disagrees cache, MED-2 mark memoization, MED-6 superiority validation, anytime EnumerationExceeded wire-up per D-18) land in WS-O-gun-gunray. The Garcia rewrite operates on the post-bugfix code.
- This WS unblocks **WS-K** (heuristic-discipline). Per D-8 the trust-calibration argumentation pipeline replaces `derive_source_document_trust`; that pipeline depends on a clean Garcia-faithful surface for the per-source rule firings. The proposal_source_trust family design was dropped per D-8; what remains is the meta-paper rule extraction (WS-K2) and the argumentation-pipeline output, both of which need clean DeLP semantics.
- This WS interacts with **WS-O-arg-bugs** (the cluster-P HIGH bugs in `argumentation`) only via the dialectical-tree shape — both gunray and argumentation expose dialectical surfaces, but they are independent kernels per D-15. No code shared.
- This WS does **not** change Bozzato 2018 / Diller 2025 / Maher 2021 affordances at the propstore boundary. Those gaps (cluster-B M5–M9) are tracked in their own workstreams. The rewrite leaves the door open: cleaner Garcia semantics make Bozzato-style override-with-justification rules easier to integrate later.

## Scope honesty

Per D-16's scope-honesty note applied here: this is a major rewrite of gunray's core semantic surface plus propstore schema widening and migration. Honest estimate:

- Steps 1–4: ~3–5 weeks focused engineering with deep paper-reading.
- Step 5 (KLM property suite): ~1 week — each postulate small, but verifying which DeLP satisfies requires Kraus 1990 alongside Garcia 04.
- Step 6: ~1 day. Step 7: ~2 days.
- Step 8 (propstore schema widening + consumer migration): ~1.5 weeks. Schema widening is in scope here, not deferred.
- Step 9: ~2 days.

Total: **5.5–9 weeks across two coordinated PRs**. Per `feedback_tdd_and_paper_checks`: coder+reviewer per chunk, paper §-checks each phase. The §3.4 worked-example test is the foreman-level quality gate — regression there blocks the next step.

## What this WS does NOT do

- Does NOT change `closure.py` — KLM closure for the propositional fragment stays as-is. The KLM property suite tests the dialectical path; closure path is already covered by `test_closure_faithfulness.py`.
- Does NOT implement Antoniou 2007 ambiguity-propagating semantics — stays out-of-contract per `CITATIONS.md:106-113`.
- Does NOT implement Maher 2021 metaprogram compilation — stays "considered, not taken".
- Does NOT change `_simplify_strict_fact_grounding`. Cluster-R LOW-1 CITATIONS update is in step 9 docs only.
- Does NOT add Pollock undercutting/rebutting as a named API. Garcia proper/blocking is canonical per `CITATIONS.md`; Pollock is read for foundational understanding only.
- Does NOT remove `kind="defeater"` from the gunray rule schema — gunray rules keep the runtime `defeater` kind classified at the argument-pair level via `_defeat_kind`. The propstore-side `RuleDocument.kind` does widen to proper/blocking (PR-2) because that distinction is required at the persistence boundary by Cluster-B D4.

## Cross-checks before the first commit

Before the first commit, the implementer must:

1. Read Garcia 2004 notes.md end to end — every Definition, every figure caption.
2. Read Simari 1992 Lemma 2.4 and Def 2.6.
3. Read Kraus 1990 (paper directly if notes.md sparse) for postulate definitions.
4. Read Pollock 1987 for rebutting/undercutting context; Lehmann 1989/1992 for rational closure (note `_1989` dirname is S2 metadata; content is 1992).
5. Reread `gunray/src/gunray/{dialectic,defeasible,preference,arguments}.py` line by line.
6. Reread `propstore/families/documents/rules.py`, `propstore/stances.py`, `propstore/grounding/grounder.py`, `propstore/grounding/inspection.py` line by line — schema-side touch surface for PR-2.
7. Run existing `tests/test_{specificity,dialectic,presumptions}.py` on master and write baseline to `logs/test-runs/pre-WS-O-gun-garcia.log`. Run propstore baseline likewise to `logs/test-runs/pre-WS-O-gun-garcia-propstore.log`.
8. Author `tests/test_garcia_section_3_4.py` as the first failing test. No production change until that test exists, fails, and the failure mode matches prediction. Run it and record the failure output.

Paper-vs-code discrepancies escalate to a decision point per the global protocol — not silently resolved by reading either side selectively.
