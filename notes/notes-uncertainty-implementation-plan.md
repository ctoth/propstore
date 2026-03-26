# Uncertainty Representation — Implementation Plan

## Scope

Wire the opinion algebra (Changes 1+2, done) into the existing pipeline. Implement Changes 4 → 6 → 3 → 7 → 5A. Defer 5B (full PrAF) to a future session.

## Baseline

- 1118 tests passing on master (56.79s)
- Commits: `a479c85` (opinion module), `c206928` (calibrate module)
- Impact analysis: `reports/impact-analysis-changes-3-7.md`

---

## Phase 1: Change 4 — Schema (LOW risk)

**Goal:** Add opinion columns to claim_stance table so downstream changes have somewhere to store data.

**What changes:**
- `build_sidecar.py:828-843` — add `opinion_belief REAL, opinion_disbelief REAL, opinion_uncertainty REAL, opinion_base_rate REAL` columns to CREATE TABLE
- `build_sidecar.py:187-194` — update INSERT in `_populate_stances_from_files()` to populate new columns (default to vacuous opinion values when stance YAML doesn't have them)
- `build_sidecar.py:908-912` — update INSERT in `_populate_claims()` (inline stances path)
- `tests/conftest.py:27-42` — update test schema to match
- Update test INSERT statements in: `test_argumentation_integration.py`, `test_bipolar_argumentation.py`, `test_render_time_filtering.py`

**Hard gate:** 1118 tests still passing. `pks build` succeeds. New columns appear in sidecar with vacuous defaults for existing data.

**Scout report ref:** impact-analysis-changes-3-7.md, Change 4 section.

---

## Phase 2: Change 6 — Multi-dim preferences (MEDIUM risk)

**Goal:** Make preference comparison multi-dimensional. Stop averaging orthogonal signals into one float.

**What changes:**
- `preference.py:56-87` — `claim_strength()` returns `list[float]` with separate dimensions instead of averaging into one float
- `argumentation.py:158-159` — remove `[...]` wrapping around `claim_strength()` calls (it already returns a list)
- `argumentation.py:271` — add scalar aggregation (e.g. geometric mean) for MaxSMT weight, which needs a single float
- `structured_argument.py:88` — `StructuredArgument.strength` becomes `list[float]` or keep scalar via aggregation
- `structured_argument.py:175-176` — remove `[...]` wrapping
- `tests/test_preference.py` — update `claim_strength` tests for list return, update `defeat_holds` tests

**Hard gate:** 1118 tests passing. Elitist vs democratic comparison now produces different results (verify with a test case where they diverge).

**Scout report ref:** impact-analysis-changes-3-7.md, Change 6 section. Note: `defeat_holds` already accepts `list[float]` — no change needed there.

---

## Phase 3: Change 3 — Wire into relate.py (HIGH risk)

**Goal:** Replace the fabricated `_CONFIDENCE_MAP` with `categorical_to_opinion()`. Keep backward compatibility.

**What changes:**
- `relate.py:76-83` — remove `_CONFIDENCE_MAP` dict
- `relate.py:82-83` — replace `_compute_confidence()` with call to `calibrate.categorical_to_opinion()`
- `relate.py:199-209` — update resolution dict to include opinion components (b, d, u, a) alongside scalar `confidence` (which becomes `opinion.expectation()`)
- `relate.py:464-485` — `write_stance_file()` serializes opinion data into stance YAML
- `build_sidecar.py:187-194` — read opinion components from stance YAML and populate the new schema columns from Phase 1

**Backward compatibility:** The `resolution.confidence` field in stance YAML and `claim_stance.confidence` column in SQLite continue to exist, populated with `Opinion.expectation()`. Existing consumers that read `confidence` as a float see no change. New consumers can read the full opinion.

**Hard gate:** 1118 tests passing. `pks build` succeeds. Stance YAML files contain opinion data. Sidecar claim_stance rows have populated opinion columns. `confidence` column values match `Opinion.expectation()` for all rows.

**Scout report ref:** impact-analysis-changes-3-7.md, Change 3 section.

---

## Phase 4: Change 7 — Render policy extensions (LOW risk)

**Goal:** Add new fields to RenderPolicy for opinion-aware rendering.

**What changes:**
- `world/types.py:180-196` — add to RenderPolicy:
  - `decision_criterion: str = "pignistic"` (one of: pignistic, lower_bound, upper_bound, hurwicz)
  - `pessimism_index: float = 0.5` (Hurwicz alpha, only used when criterion is "hurwicz")
  - `show_uncertainty_interval: bool = False`
- `worldline.py:55-115` — add matching fields to WorldlinePolicy, update `from_dict()`/`to_dict()`
- `world/resolution.py:210-262` — extract new fields, pass to backends. When `decision_criterion != "pignistic"`, use the opinion columns to compute bounds instead of scalar confidence.
- `cli/compiler_cmds.py` — add CLI options for new fields

**Hard gate:** 1118 tests passing. Default behavior unchanged (pignistic = expectation = existing confidence float). New criterion options produce different results when opinions have uncertainty.

**Scout report ref:** impact-analysis-changes-3-7.md, Change 7 section.

---

## Phase 5A: Change 5A — Soft threshold migration (HIGH risk)

**Goal:** Change the threshold gate from hard binary to soft. Keep threshold parameter but change semantics.

**What changes:**
- `argumentation.py:131-133` — replace hard gate with soft behavior:
  - Stances with opinion expectation < epsilon (0.01) are pruned as performance optimization
  - All other stances enter the AF regardless of confidence
  - The `confidence_threshold` parameter is preserved but deprecated (logged warning if non-default)
- `structured_argument.py:147-148` — same change
- `argumentation.py:230-232` — update `stance_summary` to report opinion statistics instead of "excluded_by_threshold" count
- `tests/test_render_time_filtering.py` — rewrite to test soft behavior (near-zero stances pruned, low-but-nonzero stances included)
- `tests/test_argumentation_integration.py:156-163` — update threshold test

**NOT in scope (deferred to 5B):**
- PrAF algorithm in dung.py
- Monte Carlo sampling for probabilistic extensions
- Tree-decomposition DP
- New ReasoningBackend.PRAF option

**Hard gate:** 1118 tests passing. Low-confidence stances (e.g. 0.3) that were previously invisible to the AF now participate. AF results may change — verify that the change is in the expected direction (more stances → more defeats → potentially different extensions).

**Scout report ref:** impact-analysis-changes-3-7.md, Change 5 section.

---

## Deferred: Change 5B — Full PrAF (future session)

Implement PrAF as a new `ReasoningBackend` option. Requires:
- New module `propstore/praf.py` with MC sampler (Li 2012, Algorithm 1) and optional tree-decomp DP (Popescu 2024)
- Integration with ATMS (environments ↔ PrAF subgraphs)
- Benchmarking at propstore scale
- Paper notes: `papers/Li_2011_*/notes.md`, `papers/Popescu_2024_*/notes.md`

---

## Execution pattern

Each phase is one coder subagent with:
1. Scout report as context (impact-analysis-changes-3-7.md)
2. Explicit file:line targets
3. Run full test suite (not just new tests)
4. Precommit + commit
5. Verify test count >= 1118 (no test deletions without replacements)

Phases are sequential — each depends on the previous. No parallelism within implementation (risk of merge conflicts on shared files).
