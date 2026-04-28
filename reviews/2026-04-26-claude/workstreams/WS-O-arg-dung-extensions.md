# WS-O-arg-dung-extensions: argumentation pkg coverage — variant Dung extensions + Caminada labelling-as-semantics operational

**Status**: CLOSED 00076004
**Depends on**: WS-O-arg-argumentation-pkg (the existing-bugs sub-stream; bug fixes land first so coverage work is built on a clean kernel)
**Blocks**: none
**Owner**: Codex implementation owner + human reviewer required
**Repo**: `../argumentation` (per D-15: fix upstream, propstore pin bumps after release)

---

## Why this workstream exists

Cluster-P (`reviews/2026-04-26-claude/cluster-P-argumentation-pkg.md`) inventoried
extension-semantics coverage in `argumentation/src/argumentation/dung.py` and
identified named-but-absent semantics the package's own bibliography commits it
to: eager (Caminada 2007), stage / stage2 (Gaggl 2012, 2013), prudent admissibility,
and a non-trivially-broken semi-stable. In parallel, `labelling.py` ships only as
a passive container — `from_extension`, `from_dict`, no operational solver — even
though Caminada 2006 (labelling-as-semantics) is in the package's bibliography.

D-16 (Group B) commits to implementing all of these. D-15 commits to doing it
upstream in `../argumentation` with propstore pinning each release. This is
Group B. Groups A (ABA+/ADF) and C (VAF + ranking) can run in parallel with
this stream after WS-O-arg kernel fixes land; Group D (gradual) waits on Group C
because it consumes `RankingResult`. Group-B changes land together because every Group-B semantics
is defined as a filter on complete extensions or a max-range/CF property, and
each has a textbook labelling characterisation that becomes available the moment
`labelling.py` gains operational predicates.

## Architecture decision (locked) — Option A: labelling-only, no Z3 dung-semantics backend

Per Codex finding 2.17 in `DECISIONS.md` and Q's `feedback_no_fallbacks.md`:
this WS commits to **one** architecture for Dung extension semantics. The
labelling-backed solver is the only path. The Z3-based dung-semantics path
(`argumentation/src/argumentation/dung_z3.py` and any `solve_with_z3`-style
entry points reachable from the dung kernel) is **deleted**, not retained as a
"second backend". Rationale:

1. No-fallbacks rule: when a new path replaces an old one, the old one leaves
   in the same PR. No `backend='z3'` knob, no compatibility shim.
2. The previous draft of this WS contained an explicit contradiction — it said
   "Do NOT keep the old brute paths as fallbacks" and then "The z3 path stays
   for `complete`/`preferred`/`stable`." Two architectures cannot both be the
   architecture. Option A resolves this by deleting the Z3 path.
3. The Z3-backed *condition reasoning* module in propstore (Bridgman /
   equation-condition work, NOT `argumentation/dung_z3.py`) is a different
   concern — propositional condition reasoning, not extension-semantics
   enumeration. That module stays. Only the Z3 path inside the dung-semantics
   solver is removed.
4. If a future workload genuinely needs SAT/SMT for Dung enumeration, that
   becomes a successor WS with its own justified contract: single backend
   selection point, identical public contract enforced by tests, explicit
   caller selection. Until then: labelling-backed only.

Decision **locked**. Re-introducing a Z3 path requires a new WS that justifies
it from scratch — not weakening the deletion here.

## Review findings covered

This workstream closes ALL of the following from cluster-P. "Done means done":
each row has a green test in `argumentation/tests/`, paper-cited, and the
cluster-P table at the top of cluster-P-argumentation-pkg.md gets the
corresponding "implemented" cell flipped.

| Finding | Source | Cluster-P citation | Description |
|---|---|---|---|
| **P-cov-1** | cluster-P §"Dung extension semantics coverage matrix" | `dung.py:88` | `eager (Caminada 2007)` row absent. Per Caminada 2007, eager extension is the unique semi-stable extension; if multiple semi-stable, eager is their intersection that is also admissible. Not implemented. |
| **P-cov-2** | cluster-P §"Missing features the literature reaches further on" | bibliography | `stage2 (Gaggl 2012/2013)` not implemented. Stage2 is the SCC-recursive variant of stage that resolves CF2's odd-cycle pathologies while staying max-range. |
| **P-cov-3** | cluster-P §"Dung extension semantics coverage matrix" | `dung.py:88` | `prudent / strongly admissible` row absent. Prudent semantics (Coste-Marquis-Devred-Marquis 2005) restricts admissibility to *prudent attack* — argument set is prudent-conflict-free under the ancestral attack relation. |
| **P-cov-4** | cluster-P §"Dung extension semantics coverage matrix" | `dung.py:363` | `semi-stable` ships as brute (range-max over complete) but only "hint" tested. Need paper-faithful first-failing test pinning Caminada 2006/2017 worked example, plus Baroni 2007 principle suite. |
| **P-cov-5** | cluster-P §"Bipolar / weighted / ranking / gradual / ADF / ABA coverage" | `bipolar.py` | `Bipolar grounded` and `bipolar complete` missing. Cayrol 2005 / Amgoud 2008 give the bipolar characteristic function; only d/s/c preferred + stable ship. |
| **P-cov-6** | cluster-P open-question 5; §"Missing features" | `labelling.py:1-127` | Caminada 2006 labelling-as-semantics is shipped passive only. No `legally_in`/`legally_out`, no admissible-/complete-/grounded-/preferred-/stable-labelling characterisation, no operational labelling-based solver. |
| **Codex-2.17** | DECISIONS.md round 2 §2.17 | this file (previous draft) | Z3 dung-semantics path retained alongside labelling-backed solver — contradicts no-fallbacks rule. Resolution: delete the Z3 dung-semantics path entirely. |

Adjacent finding closed in the same PR series because the substrate shift
makes it cheaper here than later:

| Finding | Why included |
|---|---|
| `dung.py:363` semi-stable: brute-only (no labelling solver, no SAT path) | While we're touching semi-stable for paper-faithful tests, it gets routed through the new operational labelling solver. The previously-discussed "extend `dung_z3.py` with Lehtonen 2020 semi-stable encoding" item is **removed** under Option A. |
| Stage brute-only at `dung.py:378` | Same — paper-faithful test pin, and the semantics is rerouted through operational labelling. No SAT/z3 encoding is added. |

## Decision authority

- **D-15** (`reviews/2026-04-26-claude/DECISIONS.md:158-163`): each item ships as
  a PR in `../argumentation`. propstore-side pin updates after each. No
  propstore wrappers.
- **D-16** (`DECISIONS.md:165-177`): all four groups implemented; this WS is
  Group B; runs in parallel with Groups A/C after WS-O-arg, while Group D waits
  on Group C's `RankingResult` contract.
- **Codex 2.17** (`DECISIONS.md` round 2, finding 2.17 list): deletion-first.
  Pick one architecture; delete the other. This WS picks Option A
  (labelling-only).

## Code references (verified by direct read of `../argumentation`)

### Dung kernel — current state
- `dung.py:53` — `_AUTO_BACKEND_MAX_ARGS = 12` (brute↔z3 threshold).
  **Removed** under Option A; labelling solver is unconditional.
- `dung.py:196-237` — `grounded_extension` lfp of F (Dung 1995 Def 25). Works.
- `dung.py:239-277` — `complete_extensions` brute checks
  `characteristic_fn(s) == s` AND `admissible(s)` per subset (cluster-P bug
  #14, efficiency only). The `dung_z3.py` backend at `:187` is **deleted**;
  the brute path is **replaced** by labelling projection in Step 1.
- `dung.py:279-301` — `preferred_extensions`: replaced by labelling projection;
  z3 reroute removed.
- `dung.py:302-338` — `stable_extensions`: three backends collapse to the
  single labelling-derived path; brute and z3 deleted.
- `dung.py:363-377` — `semi_stable_extensions` brute max-range over complete.
  Step 2 lands paper-faithful pin and routes through labelling. **No z3
  semi-stable encoding is added.**
- `dung.py:378-411` — `stage_extensions` brute max-range over CF; routes
  through labelling in Step 4. No z3 encoding.
- `dung.py:468-522, :523-541` — `naive_extensions`, `cf2_extensions`
  untouched.
- `dung.py:543-585` — `ideal_extension` (bug-bearing; WS-O-arg-argumentation-pkg).
- `dung_z3.py` (full module) — **deleted** in Step 1 with every importer
  reference. Any non-extension-semantics helper inside it (none identified;
  verify in Step 0) gets relocated before deletion.

### Labelling — current state (passive container)
- `labelling.py:1-127` (verify in Step 0). Ships `Labelling` dataclass
  (`inn`/`out`/`und`) and `from_extension(extension, framework)` — backwards
  (Caminada solves via labelling *first*, derives extension *second*). No
  `legally_in`/`legally_out` predicates; no `complete_labellings`,
  `grounded_labelling`, `preferred_labellings`, `stable_labellings`,
  `semi_stable_labellings` as solvers.

Central refactor: promote `labelling.py` to operational solver; semi-stable,
eager, stage2 are defined over labellings as the papers define them.

### Bipolar kernel — current state
- `bipolar.py:100-149` — Cayrol derived defeats to fixpoint. Works.
- `bipolar.py:200-275` — `d_admissible`/`s_admissible`/`c_admissible` per
  Cayrol Defs 9-11. Works.
- `bipolar.py:278-320` — `_maximal_sets`; d/s/c preferred + stable ship.
- **MISSING**: bipolar grounded (lfp of bipolar characteristic function),
  bipolar complete (fixed points). Cluster-P P-cov-5.

## Papers — primary sources for paper-faithful tests

Read each paper's `papers/<dir>/notes.md` BEFORE writing any test. Paper-faithful
= first failing test encodes a worked example transcribed verbatim from the
paper's figures with page reference in the test docstring.

| Paper dir | Role for this WS | What we extract |
|---|---|---|
| `Caminada_2006_IssueReinstatementArgumentation` | Labelling foundations | Defs of legally-in/out, complete labelling, characterisation theorems for grounded/preferred/stable/admissible labellings. Worked examples. |
| `Caminada_2007_EvaluationArgumentationFormalisms` | Eager | Definition: unique eager extension; computation as semi-stable when unique, otherwise specific intersection rule. Worked example (Caminada's "floating reinstatement" framework). |
| `Gaggl_2012_CF2ArgumentationSemanticsRevisited` | Stage2 motivation | Why CF2 has pathologies; stage2 as SCC-recursive max-range refinement. |
| `Gaggl_2013_CF2ArgumentationSemanticsRevisited` | Stage2 definition | Full SCC-recursive stage2 algorithm. Worked examples. |
| `Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation` | Bipolar grounded/complete | Bipolar characteristic function `F_BAF` definition; lfp = bipolar grounded; fixed points = bipolar complete. |
| `Amgoud_2008_BipolarityArgumentationFrameworks` | Bipolar refinement | Distinct support modes (deductive/necessary/evidence-based) — for this WS we ship the Cayrol abstract version; document the Amgoud distinction in module docstring as deferred. |
| `Verheij_2002_ExistenceMultiplicityExtensionsDialectical` | Stage existence/multiplicity | Stage extensions always exist (because conflict-free always exists); used to design tests that pin the existence guarantee. |
| `Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation` | Principle-based test suite | The 12+ principles (admissibility, conflict-freeness, reinstatement, weak/strong reinstatement, directionality, I-maximality, allowing abstention, language-independence, ...). Each new semantics ships with the principle suite as its acceptance test. |
| (additional, for prudent) `Coste-Marquis_2005_PrudentSemantics` | Prudent definition | Prudent indirect conflict as odd-length directed attack paths; grounded prudent extension by `F^p_AF` iteration from the empty set. |

If `Coste-Marquis_2005_PrudentSemantics/notes.md` is absent at WS start,
retrieve via `/research-papers:paper-retriever` and run paper-reader BEFORE
writing the prudent test. Exact deliverable: `papers/<dir>/notes.md` with
worked examples extracted.

## First failing tests — write these BEFORE any production change

Each of the following tests is paper-faithful, names the paper and page in the
docstring, encodes a worked example from the paper, and MUST fail at the time
of writing. Tests live in `argumentation/tests/` (per D-15: upstream).

### 1. `tests/test_labelling_operational.py` (new)

Substrate test. Without operational labelling, every WS semantics reduces to
extension enumeration and loses the labelling speed-up.

- `test_legally_in_predicate_caminada_2006_def_X`: small AF from Caminada
  2006 running example; assert `labelling.legally_in(a)` per paper (IN iff
  every attacker is OUT).
- `test_legally_out_predicate`: symmetric.
- `test_complete_labelling_definition`: complete iff every IN is legally-in
  and every OUT legally-out.
- `test_complete_labellings_match_complete_extensions`: bijection per
  Caminada 2006 Theorem.
- `test_grounded_labelling_unique`: exists, unique; IN equals
  `grounded_extension(af)`.
- `test_preferred_labelling_max_in`: complete labellings with maximal IN.
- `test_stable_labelling_no_undecided`: empty UNDEC; IN equals stable
  extension.
- **All must fail today**: `labelling.py` lacks `legally_in`/`legally_out`
  and any solver.

### 2. `tests/test_no_z3_backend.py` (new — Codex 2.17 deletion gate)

Deletion-side gate. Asserts no Z3-based dung-semantics solver exists in
propstore or argumentation after Step 1 lands.

- `test_no_z3_dung_module_in_argumentation`: `import argumentation.dung_z3`
  raises `ModuleNotFoundError`.
- `test_no_z3_solver_grep_argumentation`: AST-walk
  `argumentation/src/argumentation/`; zero occurrences of `solve_with_z3`,
  `_solve_with_z3`, `z3_{complete,preferred,stable,semi_stable}_extensions`,
  `_AUTO_BACKEND_MAX_ARGS`; zero `import z3`/`from z3 import` in the
  dung-semantics surface (`dung.py`, `bipolar.py`, `labelling.py`,
  `aspic_*`, `semantics.py`).
- `test_no_z3_solver_grep_propstore`: AST-walk `propstore/`; zero
  occurrences of any z3-based dung-semantics solver name outside an
  explicit single-element allowlist constant declared in the test, naming
  the propstore Bridgman / condition-reasoning module (different purpose:
  propositional condition reasoning, not extension semantics).
- **All must fail today**: `dung_z3.py` exists; `_AUTO_BACKEND_MAX_ARGS`
  referenced at `dung.py:53`; allowlist constant absent.

Stays green forever. Standing assertion that Option A holds.

### 3. `tests/test_semi_stable_paper_faithful.py` (new)

Cluster-P notes semi-stable ships brute-only with a "hint" test. Replace
"hint" with paper-faithful pin.

- `test_caminada_2006_floating_reinstatement_semi_stable`: encode the framework
  from Caminada 2006 Figure 4 (or wherever the floating-reinstatement example
  is, transcribed from the paper PDF). Compute semi-stable extensions. Assert
  the exact set of extensions matches the paper's claimed result.
- `test_semi_stable_via_labelling_only_path`: solve via the new operational
  labelling (max-range over complete labellings — minimum UNDEC) and confirm
  the result. Hypothesis-generated AF strategy across small AFs. Assert the
  result matches a brute-force reference enumeration written into the test
  itself (independent of the production path) so the labelling implementation
  is pinned to the paper's definition. There is no second-backend
  cross-check, because there is no second backend.
- **First test must fail** because no transcribed worked example exists today.
- **Second must fail** because the labelling-as-semantics path does not exist.

### 4. `tests/test_eager_extension.py` (new)

- `test_eager_unique_when_semi_stable_unique_caminada_2007`: Caminada 2007
  worked example where exactly one semi-stable extension exists. Eager equals
  semi-stable.
- `test_eager_intersection_admissible_when_multiple_semi_stable`: Caminada 2007
  worked example with multiple semi-stable. Eager extension is the largest
  admissible subset of their intersection (paper-cited definition; transcribe
  exactly from notes.md, not from second-hand sources).
- `test_eager_existence_uniqueness`: eager always exists and is unique.
  Hypothesis @given over small AFs (≤ 8 args). Marker
  `@pytest.mark.property`.
- **All must fail today**: no `eager_extension` function exists.

### 5. `tests/test_stage2_extensions.py` (new)

- `test_stage2_gaggl_2013_running_example`: AF from Gaggl 2013 §X "running
  example" verbatim. Compute stage2; assert exact match with paper's claimed
  result.
- `test_stage2_collapses_to_stage_when_no_odd_cycles`: on AFs without odd
  cycles, stage2 = stage. Hypothesis property.
- `test_stage2_resolves_cf2_pathology`: Gaggl 2012 specific framework where
  CF2 produces undesired result; stage2 produces the corrected result.
- **All must fail today**: no `stage2_extensions` function exists.

### 6. `tests/test_prudent_semantics.py` (new)

- `test_prudent_conflict_free_coste_marquis_2005`: AF where naive
  conflict-freeness and prudent conflict-freeness diverge (because prudent
  uses the ancestral closure of attack, not direct attack). Worked example
  transcribed from Coste-Marquis 2005 paper.
- `test_prudent_admissible_subset_of_admissible`: prudent admissible ⊆
  admissible. Hypothesis property.
- `test_prudent_preferred_extension_existence`: prudent preferred extensions
  always exist (a single one if AF is prudent-conflict-free at empty set,
  always at least the empty set otherwise).
- **All must fail today**: no prudent module / functions.

### 7. `tests/test_bipolar_grounded_complete.py` (new)

- `test_bipolar_grounded_lfp_cayrol_2005`: bipolar AF from Cayrol 2005
  worked example; bipolar grounded extension equals lfp of bipolar
  characteristic function.
- `test_bipolar_complete_fixed_points`: bipolar complete extensions are
  exactly fixed points of the bipolar characteristic function. Hypothesis
  property.
- `test_bipolar_grounded_unique`: bipolar grounded is unique and minimal
  bipolar complete. Hypothesis property.
- **All must fail today**: `bipolar.py` has no grounded / complete entry
  points (per cluster-P P-cov-5).

### 8. `tests/test_baroni_2007_principle_suite.py` (new)

Principle-based acceptance harness. Parametrize (semantics, principle) pairs
per Baroni 2007 and assert. Extract applicability from
`papers/Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation/notes.md`:

| Principle | Applies to (this WS) |
|---|---|
| Conflict-freeness | semi-stable, eager, stage, stage2, prudent, bipolar grounded/complete |
| Admissibility | semi-stable, eager, prudent (vs prudent attack) |
| I-maximality | preferred, semi-stable, eager (when unique), stage, stage2 |
| Reinstatement | complete, semi-stable, eager |
| Directionality | grounded, ideal, eager (Caminada 2007) |
| Allowing abstention | semi-stable (no), eager (yes), stage (no) |
| Language independence | all |

Each row: parameterised test, small AF or Hypothesis draw, assert principle
holds. **Tests must fail today** for every (eager, *), (stage2, *),
(prudent, *), (bipolar grounded, *) row.

### 9. Paired sentinels — upstream + propstore (per Codex 2.18)

Per Codex 2.18 (already applied to WS-O-arg-argumentation-pkg), every
upstream WS needs **two** sentinels with explicit closure conditions. A
propstore commit cannot flip an upstream test; an upstream commit cannot
prove the propstore pin contains the fix. Both directions are required.

**9a. `argumentation/tests/test_workstream_o_arg_dung_extensions_done.py`**
(new — upstream sentinel; lives in the **argumentation** repo)

- `xfail` until tests 1-8 above are all green in the argumentation repo
  and Steps 1-7 have shipped upstream.
- Asserts the upstream behaviour shipped: `from argumentation import
  labelling`; `labelling.legally_in`, `labelling.legally_out`,
  `labelling.complete_labellings`, `labelling.grounded_labelling`,
  `labelling.preferred_labellings`, `labelling.stable_labellings`,
  `labelling.semi_stable_labellings`, `labelling.eager_labelling`,
  `labelling.stage2_labellings` all importable; `eager_extension`,
  `stage2_extensions`, `prudent_*` exposed on the dung surface;
  `bipolar_grounded_extension`, `bipolar_complete_extensions` exposed on
  bipolar; `import argumentation.dung_z3` raises `ModuleNotFoundError`
  (Option A deletion gate); `_AUTO_BACKEND_MAX_ARGS` absent.
- **Closure condition**: turns green when the final upstream PR (Step 7
  — Baroni 2007 principle suite) merges to argumentation's default
  branch. Closes in the **argumentation repo**. Independent of any
  propstore-side change. Mirrors WS-A's pattern.

**9b. `propstore/tests/architecture/test_argumentation_pin_dung_extensions.py`**
(new — propstore sentinel; lives in **propstore**)

- Imports the public API surface from the pinned `argumentation` package:
  `from argumentation import labelling`; `from argumentation.labelling
  import legally_in, legally_out, complete_labellings,
  grounded_labelling, preferred_labellings, stable_labellings,
  semi_stable_labellings, eager_labelling, stage2_labellings`; new dung
  surface (`eager_extension`, `stage2_extensions`, `prudent_*`); new
  bipolar surface (`bipolar_grounded_extension`,
  `bipolar_complete_extensions`).
- Exercises one paper-faithful behavioural assertion per major addition,
  observable from propstore (no reaching into argumentation internals):
  - Operational labelling: build a small AF; call
    `complete_labellings(af)` and assert each result satisfies
    `legally_in`/`legally_out` per Caminada 2006.
  - Semi-stable: paper-faithful Caminada 2006 floating-reinstatement
    fixture; assert pinned extension set.
  - Eager: Caminada 2007 multi-semi-stable fixture; assert pinned eager
    extension equals the largest admissible subset of the intersection.
  - Stage2: Gaggl 2013 running example; assert pinned stage2 extensions.
  - Prudent: Coste-Marquis 2005 fixture where naive and prudent
    conflict-freeness diverge; assert prudent extension differs.
  - Bipolar grounded: Cayrol 2005 fixture; assert pinned bipolar
    grounded extension.
  - Z3 deletion (Option A standing assertion, observable from propstore):
    `from argumentation import dung_z3` raises `ModuleNotFoundError`;
    AST-walk `propstore/` and assert no propstore module imports any
    argumentation Z3 dung-semantics symbol outside the documented
    Bridgman/condition-reasoning allowlist constant.
- Asserts `propstore/pyproject.toml`'s argumentation pin string equals
  or post-dates the recorded post-Step-7 argumentation commit (resolved
  via a recorded commit string in this WS or via git metadata).
- **Closure condition**: turns green when `propstore/pyproject.toml`'s
  argumentation pin advances to a commit that contains all Step 1-7
  fixes AND every behavioural assertion above passes against that
  pinned dependency. Closes in **propstore** when the pin bumps and the
  propstore suite re-runs clean.

The two-sentinel discipline ensures that a fix is genuinely reflected in
propstore behavior, not merely in upstream source. A propstore PR cannot
mark this WS closed by editing only the upstream sentinel (which lives
in a different repo); the propstore-side pin bump and 9b turning green
is the closure event for propstore.

## Production change sequence (in `../argumentation`)

Each step is one PR. Each PR has its first failing test landed in the same
commit as the implementation, with the test predating the implementation in
the worktree (TDD discipline per Q's `feedback_tdd_and_paper_checks.md`).

### Step 0 — Read source and papers
- Read `labelling.py` in full to confirm cluster-P's "passive container"
  claim; narrow scope if predicates already exist.
- Read `dung_z3.py` in full; catalogue every exported symbol and every
  importer for Step 1 deletion plan.
- Read each paper notes.md; transcribe one worked example per paper into
  `notes/WS-O-arg-dung-extensions.md` in the argumentation repo.
- DECISION POINT: if `Coste-Marquis_2005_PrudentSemantics/notes.md` is
  missing, retrieve+read before continuing.

Acceptance: notes file written with page-cited worked examples; full
`dung_z3.py` inventory recorded.

### Step 1 — Operational `labelling.py` AND deletion of the Z3 dung-semantics path

Foundational refactor + deletion that locks Option A. Both happen in the same
PR series — adding the new path while leaving the old one standing would
violate the no-fallbacks rule on every commit between them.

**Add (labelling-backed solver):**
- `Labelling.legally_in(arg) -> bool`, `Labelling.legally_out(arg) -> bool`
  per Caminada 2006.
- Module-level solvers: `complete_labellings`, `grounded_labelling`,
  `preferred_labellings`, `stable_labellings`.
- Implement via Caminada 2006 algorithm: start all-IN, iteratively re-label
  IN→OUT/UNDEC when attackers aren't all OUT, to fixed point. Preferred =
  search maximal-IN; stable = filter complete labellings with empty UNDEC.

**Reroute extension functions to delegate:**
- `complete_extensions`/`grounded_extension`/`preferred_extensions`/
  `stable_extensions` BECOME thin wrappers calling `*_labellings(af)` and
  projecting IN-sets. Solve via labelling first, derive extension second.
- Previous brute paths inside `dung.py` are deleted in the same commit.

**Delete the Z3 dung-semantics path (Option A; Codex 2.17):**
- Delete `argumentation/src/argumentation/dung_z3.py` entirely.
- Delete every `dung_z3` import from `dung.py`.
- Delete `_AUTO_BACKEND_MAX_ARGS` at `dung.py:53` and every branch reading it.
- Delete every `solve_with_z3`-style helper, every
  `if size > _AUTO_BACKEND_MAX_ARGS` branch, every `backend='z3'` keyword
  path, every Z3-conditional in `complete_extensions`/`preferred_extensions`/
  `stable_extensions`/`semi_stable_extensions`.
- If any helper inside `dung_z3.py` has non-extension-semantics use (none
  identified; verify Step 0 inventory), relocate before deletion.
- Update every caller of any deleted symbol in one pass per
  `feedback_update_callers.md`. No shims, no aliases, no `try: import`
  guards. Grep `argumentation/`, `propstore/`, and the test corpus.
- Delete tests existing solely to exercise the Z3 dung-semantics path. Keep
  abstract contract tests — they retarget automatically.

Acceptance for Step 1:
- `tests/test_labelling_operational.py` green.
- `tests/test_no_z3_backend.py` green (deletion gate).
- `dung_z3.py` does not exist; `_AUTO_BACKEND_MAX_ARGS` absent everywhere;
  `import argumentation.dung_z3` raises `ModuleNotFoundError`.

### Step 2 — Semi-stable paper-faithful via labelling

- Reroute `semi_stable_extensions` to compute via
  `semi_stable_labellings(af)`: max-range (i.e., minimal-UNDEC) complete
  labellings, then project. Definition is paper-cited
  (Caminada-Verheij 2017, Caminada 2006).
- Add `semi_stable_labellings(af)` solver. Implementation is over labellings
  only — no SAT/SMT encoding is added under Option A. If, in a future
  successor WS, scaling demands an SMT path, that successor designs a
  single-backend selection point with explicit caller selection and
  re-justifies the architecture.

Acceptance: `tests/test_semi_stable_paper_faithful.py` green; brute path
deleted; `tests/test_no_z3_backend.py` continues to pass.

### Step 3 — Eager (Caminada 2007)

- New module surface (in `dung.py` for cohesion, or new
  `eager.py` if size warrants — judgment call; cluster-P's existing semantics
  cohabit `dung.py`).
- `eager_extension(af) -> frozenset[str]`. Per Caminada 2007: compute
  semi-stable; if unique, return; else return the largest admissible subset
  of their intersection. Use `is_admissible` already in `dung.py:140-194`.
- Add `eager_labelling(af) -> Labelling` for the labelling path (Caminada
  2007 also gives the labelling characterisation).

Acceptance: `tests/test_eager_extension.py` green.

### Step 4 — Stage2 (Gaggl 2013)

- New `stage2_extensions(af)`. SCC-recursive structure mirrors
  `cf2_extensions` at `dung.py:523-541`. The recursion is: for each SCC in
  topological order, compute stage extensions of the SCC restricted by the
  outcomes from earlier SCCs; combine.
- Reuse the existing SCC machinery at `dung.py:413` (recursive Tarjan; note
  cluster-P bug #13 — recursion-limit risk; out of scope for this WS unless
  tests trigger it, in which case this WS picks up the iterative variant).
- `stage2_labellings(af)` for the labelling path.

Acceptance: `tests/test_stage2_extensions.py` green.

### Step 5 — Prudent (Coste-Marquis-Devred-Marquis 2005)

- New `prudent.py` module (or `dung.py` extension). Smaller than the others.
- `ancestral_attacks(af)` computes the transitive closure of attack as
  defined in the paper (an attack of `a` on `b` includes any attack-path
  ending at `b`).
- `is_prudent_conflict_free(af, s)` uses ancestral attack instead of direct.
- `prudent_admissible(af, s)`, `prudent_preferred_extensions(af)`,
  `prudent_grounded_extension(af)` per the paper.
- Decision: do NOT shadow the existing `is_conflict_free` / `is_admissible`.
  Prudent variants are separate functions. Callers opt in.

Acceptance: `tests/test_prudent_semantics.py` green.

### Step 6 — Bipolar grounded / complete (Cayrol 2005)

- Extend `bipolar.py`. Add `BipolarArgumentationFramework.characteristic_fn(s)`
  per Cayrol's bipolar definition (an argument is acceptable iff it is
  defended by `s` against derived defeats AND is supported by `s` w.r.t.
  abstract supports — exact form per `Cayrol_2005_*/notes.md`).
- `bipolar_grounded_extension(baf)` = lfp.
- `bipolar_complete_extensions(baf)` = fixed points filtered by bipolar
  admissibility.
- Document the deferred Amgoud 2008 distinction (deductive / necessary /
  evidence-based support modes) in module docstring with paper citation.

Acceptance: `tests/test_bipolar_grounded_complete.py` green.

### Step 7 — Baroni 2007 principle suite

Land the principle-based parametric test harness covering every (semantics,
applicable principle) row. Failures here surface paper-spec divergence in
any of the new semantics. If a principle fails, fix the semantics
implementation; do not weaken the principle test.

Acceptance: `tests/test_baroni_2007_principle_suite.py` green.

### Step 8 — propstore-side pin bump (paired sentinels per Codex 2.18)

After upstream PRs ship and a release tag exists:

Upstream side (argumentation):
- Confirm tests 1-8 above are green in the argumentation repo.
- Flip `argumentation/tests/test_workstream_o_arg_dung_extensions_done.py`
  (9a) from `xfail` to `pass`. This test lives in the **argumentation**
  repo and closes upstream behaviour.

Propstore side:
- Bump the `argumentation` pin in `pyproject.toml`.
- Re-run propstore's full suite; no NEW failures vs WS-A baseline
  (`logs/test-runs/pytest-20260426-154852.log`).
- Run `tests/test_no_z3_backend.py` against the propstore tree; the
  documented Z3-condition module is the sole allowlisted Z3 importer.
- Update any propstore caller of `labelling` / changed extension signatures
  / deleted Z3 symbols per `feedback_update_callers.md` (no shims).
- Flip `propstore/tests/architecture/test_argumentation_pin_dung_extensions.py`
  (9b) from `xfail` to `pass`. This test lives in **propstore** and
  closes the pin / observable-behaviour gate.
- Update this WS file's STATUS line to `CLOSED <propstore-sha>`.

Acceptance: pin updated; full suite green; both sentinels (9a upstream,
9b propstore) green in their respective repos; propstore-side
no-Z3-backend assertion green. Per Codex 2.18, the propstore commit
cannot flip the upstream test (different repo); the upstream commit
cannot prove the propstore pin contains the fix. Both directions are
required.

## Acceptance gates

ALL must hold before WS done:

- [ ] `../argumentation` tagged release contains every Step 1-7 change.
- [ ] Every test in §"First failing tests" green; brute paths for
      semi-stable/stage deleted; no shims/fallbacks.
- [ ] `dung_z3.py` does not exist; no `import z3` for dung-semantics use;
      `_AUTO_BACKEND_MAX_ARGS` absent.
- [ ] `tests/test_no_z3_backend.py` green in `../argumentation` AND propstore
      (allowlist arm).
- [ ] propstore `pyproject.toml` pin advanced; full suite (`scripts/run_logged_pytest.ps1`)
      no NEW failures vs WS-A baseline.
- [ ] Upstream sentinel `argumentation/tests/test_workstream_o_arg_dung_extensions_done.py`
      (9a) green in the argumentation repo.
- [ ] Propstore sentinel `propstore/tests/architecture/test_argumentation_pin_dung_extensions.py`
      (9b) green in propstore against the bumped pin.
- [ ] cluster-P P-cov-1..6 closed; open-question 5 answered; Codex 2.17 closed.
- [ ] WS-O-arg-dung property-based gates from `PROPERTY-BASED-TDD.md` are included in upstream tests or a named companion run.
- [ ] `STATUS` flipped to `CLOSED <sha>`.

## Done means done

WS done when **every findings-table row is closed**:

- Caminada labelling is OPERATIONAL: complete/grounded/preferred/stable/
  semi-stable/eager extension functions delegate to labelling solvers.
- Semi-stable, eager, stage2, prudent, bipolar grounded, bipolar complete
  have paper-faithful first-failing tests with page-cited worked examples.
- Each semantics passes the Baroni 2007 principle suite for applicable
  principles.
- Z3 dung-semantics backend fully deleted: no `dung_z3.py`, no
  `_AUTO_BACKEND_MAX_ARGS`, no `solve_with_z3` helpers, no `backend='z3'`
  parameter, no `import z3` in any dung-semantics surface.
  `tests/test_no_z3_backend.py` is the standing assertion this remains true.
- propstore pin bumped; tests green; propstore-side no-Z3-backend arm green.
- Sentinel test flipped.

If any row is not closed the WS stays OPEN. No "we'll keep `dung_z3.py` for
one more cycle." Either in scope and closed, or removed from this WS file
(moved to a successor) before declaring done.

## Discipline reminders

- **Read papers first** (`feedback_citations_and_tdd.md`): cite at docstring
  and inline levels; tests first; don't infer algorithms from Wikipedia.
- **No fallbacks** (`feedback_no_fallbacks.md`): brute paths AND Z3 backend
  deleted in the same PR as labelling-as-solver lands. No standby code.
- **Hypothesis property tests** (`feedback_hypothesis_property_tests.md`):
  every "for all AF, semantics satisfies principle X" becomes `@given` over
  small AFs with `@pytest.mark.property`.
- **Imports are opinions** (`feedback_imports_are_opinions.md`): the kernel
  computes what FOLLOWS from defeasible inputs; this WS adds machinery, does
  not privilege any semantics. Propstore-side bridge defaults stay explicit
  caller choice.

## Cross-stream notes

- **Sequenced after WS-O-arg-argumentation-pkg.** Cluster-P bug #1
  (`ideal_extension` non-admissible union) and bug #14 (complete-extension
  efficiency) live in `dung.py`. WS-O-arg-argumentation-pkg merges first;
  this WS rebases.
- **Parallel with WS-O-arg-aba-adf** after argumentation-pkg lands —
  different modules, no coupling.
- **Parallel with WS-O-arg-vaf-ranking** after argumentation-pkg lands —
  different modules, no coupling.
- **NOT parallel with WS-O-arg-gradual** — gradual depends on
  WS-O-arg-vaf-ranking shipping `RankingResult` (Codex 2.22). This WS does
  not block gradual but the gradual stream waits on vaf-ranking, not on
  this WS.
- **propstore-side consumer impact**: dispatcher key additions are
  backwards-compatible. The `labelling.py` refactor preserves
  `Labelling.from_extension` (useful utility; no longer privileged). The Z3
  deletion is the most invasive: any propstore caller reaching into
  `argumentation.dung_z3` (verify zero hits via Step 0 inventory) retargets
  to labelling in the same PR. Per the propstore-side allowlist test, the
  only remaining propstore Z3 importer post-WS is the documented
  Z3-condition module (propositional condition reasoning, not extension
  semantics).
- **Caminada labelling unblocks future work**: cluster-N's
  argumentation-as-trust-calibration pipeline (D-8) renders labellings more
  naturally than extensions; stage2 unblocks callers hitting CF2 odd-cycle
  issues.

## What this WS does NOT do

- Does NOT fix existing bugs in `dung.py` / `aspic_encoding.py` /
  `bipolar.py` (WS-O-arg-argumentation-pkg).
- Does NOT add ABA, ADF, ASPIC+ (WS-O-arg-aba-adf), VAF/ranking
  (WS-O-arg-vaf-ranking), DF-QuAD/Matt-Toni (WS-O-arg-gradual).
- Does NOT touch the probabilistic stack — out of scope for cluster-P.
- Does NOT implement Amgoud 2008 support modes — Cayrol 2005 abstract
  support stays; Amgoud refinement deferred (module docstring).
- Does NOT implement resolution-based grounded (Baroni-Giacomin 2008) or
  strongly admissible (Caminada 2014). Successors only.
- Does NOT change propstore bridges except the pin bump and Z3-deletion
  retargeting.
- Does NOT add an SMT/SAT backend for Dung extension semantics. Option A
  locked; future SMT scaling needs a successor WS.
- Does NOT touch the propstore Z3-condition module (Bridgman / equation
  conditions) — the one allowlisted Z3 importer.

## Papers / specs referenced (verbatim from `papers/`)

- `papers/Caminada_2006_IssueReinstatementArgumentation/notes.md` — labelling
  foundations.
- `papers/Caminada_2007_EvaluationArgumentationFormalisms/notes.md` — eager.
- `papers/Gaggl_2012_CF2ArgumentationSemanticsRevisited/notes.md`
- `papers/Gaggl_2013_CF2ArgumentationSemanticsRevisited/notes.md`
- `papers/Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation/notes.md`
- `papers/Amgoud_2008_BipolarityArgumentationFrameworks/notes.md`
- `papers/Verheij_2002_ExistenceMultiplicityExtensionsDialectical/notes.md`
- `papers/Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation/notes.md`
- `papers/Coste-Marquis_2005_PrudentSemantics/notes.md` — retrieve if absent
  before Step 5.

Each test docstring cites the paper and the specific page/figure/example
number transcribed.
