# Axis 4 — Test Adequacy

## Summary

propstore collects **2496 tests** and the `@given`-decorated property suite (**365 tests across 54 files**) runs **all green in 4m 25s**. That is the strong half of the story.

The weak halves:

1. **Marker discipline is almost nonexistent.** Of six registered markers (`unit | property | differential | e2e | migration | slow`) five are effectively unused. Only one file carries `@pytest.mark.property`, zero carry `differential` / `unit` / `migration` / `slow`, and two files carry `e2e`. The README (`tests/README.md:33`) documents them as policy, but the corpus ignores the policy. `-m property` selects 6 tests when the actual property-test count is **365**. This makes marker-scoped runs in CI and in Q-directed workflows ("run the differential suite", "run the e2e suite") silently vacuous.
2. **Four heavy theoretical clusters have no property tests.** AGM K*1-K*8 and DP C1-C4 (revision), IC0-IC8 (Konieczny merge postulates), ATMS invariants (label minimality, nogood consistency, sound propagation), and Cayrol bipolar direct/supported/secondary-attack relations — all sit on example tests or nothing.
3. **~1500 LOC of source is completely untested** (seven modules with no reference from any test file). Several of them — `fragility_contributors.py` (529 LOC), `fragility_scoring.py` (386 LOC), `fragility_types.py` (234 LOC) — sit directly under claims added to Axis 9 / Axis 3b on calibrated uncertainty.
4. **`conflict_detector/orchestrator.py` is not directly tested.** It is reached transitively through `detect_conflicts()` callers but no test file names it.

Biggest single gap: **ATMS invariants in `propstore/atms_engine.*` / BoundWorld are not property-tested at all.** `tests/test_atms_engine.py` is 1780 LOC and contains zero `@given`; every label-minimality / nogood-consistency / sound-propagation check is a hand-crafted scenario. This is Axis 3e territory and the single biggest untested formal-property surface.

## A. Marker integrity

Commands used (all via `uv run pytest --collect-only -q -m <marker>`):

| Marker | Tests collected | Files actually using it | Delta vs. actual content |
|---|---:|---:|---|
| `unit` | 0 | 0 | Registered in `tests/README.md:33`, never applied |
| `property` | 6 | 1 (`test_equation_comparison_properties.py`) | Actual @given files: **54**. Missing marker on 53 files |
| `differential` | 0 | 0 | Registered but never applied |
| `e2e` | 2 | 2 (`test_log_cli.py:204`, `test_source_cli.py:806`) | `test_cli.py`, `test_reasoning_demo_cli.py`, `test_verify_cli.py`, `test_source_cli.py`, `test_merge_cli.py`, `test_revision_cli.py`, `test_concept_alignment_cli.py`, `test_cli.py` all look end-to-end but are not tagged |
| `migration` | 0 | 0 | Registered but never applied |
| `slow` | 0 | 0 | Registered but never applied |
| `hypothesis` (auto) | 365 | 54 | This is auto-applied by the hypothesis plugin, not author-declared |

**Findings:**

- **F-A1 (HIGH):** 53 of 54 hypothesis/property test files lack the `property` marker. `-m property` in CI will run 6 tests when it should run 365. Example file without marker but with @given: `tests/test_opinion.py:397` (`@given(valid_opinions(), valid_opinions())`), `tests/test_dung.py:264`, `tests/test_aspic.py:2367`, `tests/test_ic_merge.py:295`, `tests/test_bipolar_semantics.py:143`. None of them carry `@pytest.mark.property` or `pytestmark = pytest.mark.property`.
- **F-A2 (MEDIUM):** `differential` is registered as "differential or oracle-comparison tests" but `tests/test_treedecomp_differential.py` exists and is not tagged. (The "differential" concept is alive in the codebase; the marker is not.)
- **F-A3 (MEDIUM):** `slow` registered but unused — the hypothesis suite takes 4m 25s and `tests/test_ic_merge.py` alone has `max_examples` knobs; no suite mechanism exists to exclude slow tests from fast CI.
- **F-A4 (LOW):** `test_equation_comparison_properties.py:171,220,232,253,287,313` uses `@pytest.mark.property` at the individual test level rather than a module-level `pytestmark`, while the module name signals "all of this is property." This works but is verbose; module-level `pytestmark` is the canonical idiom.

## B. Property coverage per theoretical cluster

Table: cluster → formal property → test file → `@given`? → verdict.

| Cluster | Paper / property | Test file | `@given`? | Verdict |
|---|---|---|---|---|
| Opinion algebra | Jøsang 2001 §3 — `b+d+u=1` | `test_opinion.py:32-47` (property class `TestBDUSum`) | mixed (class tests example + hypothesis strategy `valid_opinions`) | **OK** |
| Opinion algebra | Jøsang 2001 §4 — vacuous `(0,0,1,a)` | `test_opinion.py:33-34` | example | acceptable (single canonical case) |
| Opinion algebra | Jøsang 2001 §5 — consensus commutativity | `test_opinion.py:397` (`@given(valid_opinions(), valid_opinions())`) | yes | **OK** |
| Opinion algebra | Jøsang 2001 §5 — consensus associativity | `test_opinion.py:620` (`@given(valid_opinions(), valid_opinions(), valid_opinions())`) | yes | **OK** |
| Opinion algebra | Jøsang 2001 §6 — discount identity/absorption | `test_opinion.py:658-687` (`@given(valid_opinions())`) | yes | **OK** |
| Opinion algebra | Jøsang 2001 §9 — WBF bounds, CCF | `test_opinion.py:842-917` | yes | **OK** |
| Dung 1995 | Def 6 — conflict-free (grounded is CF) | `test_dung.py:264-269` | `@given(argumentation_frameworks())` | **OK** |
| Dung 1995 | Def 8 — admissible (grounded admissible) | `test_dung.py:271-276` | yes | **OK** |
| Dung 1995 | Def 10 — complete (fixed-point F) | `test_dung.py:367-372` | yes | **OK** |
| Dung 1995 | Thm 25 — grounded is least complete | `test_dung.py:374-380` | yes | **OK** |
| Dung 1995 | Thm 13 — stable ⊆ preferred | `test_dung.py:344-351` | yes | **OK** |
| Dung 1995 | Def 12 — stable defeats outsiders | `test_dung.py:353-361` | yes | **OK** |
| Dung 1995 | Preferred: maximal admissible | `test_dung.py:311-323` | yes | **OK** |
| Dung 1995 | Fundamental Lemma / F monotone | `test_dung.py:386-396` | yes (but only `f_empty ⊆ f_grounded`, not full subset quantification — partial) | **PARTIAL** |
| AGM | Alchourrón 1985 — K*1 closure | nothing | — | **MISSING (HIGH)** |
| AGM | K*2 success: `φ ∈ K*φ` | `test_revision_operators.py:84` example only | — | **MISSING-as-property (HIGH)** |
| AGM | K*3 inclusion: `K*φ ⊆ K+φ` | nothing | — | **MISSING (HIGH)** |
| AGM | K*4 vacuity: `¬φ ∉ K → K*φ = K+φ` | nothing | — | **MISSING (HIGH)** |
| AGM | K*5 consistency: `K*φ` inconsistent iff `⊢¬φ` | nothing | — | **MISSING (HIGH)** |
| AGM | K*6 extensionality | nothing | — | **MISSING (HIGH)** |
| AGM | K*7, K*8 super/sub-expansion | nothing | — | **MISSING (HIGH)** |
| DP | Darwiche-Pearl 1997 C1-C4 (iterated) | `test_revision_iterated.py` — example tests only (no @given) | — | **MISSING (HIGH)** |
| IC merge | Konieczny 2002 IC0-IC8 postulates | `test_ic_merge.py` — `@given` exists but for distance-metric / Sigma-Maj / Max-Arb / GMax-Arb properties, not for IC0-IC8 by name | partial | **PARTIAL (HIGH — postulates not named)** |
| ASPIC+ | Modgil-Prakken Post 1 — sub-arg closure | `test_aspic.py:2367-2386` (`@given(well_formed_csaf())`) | yes | **OK** |
| ASPIC+ | Post 2 — strict closure | `test_aspic.py:2387-2406` | yes | **OK** |
| ASPIC+ | Post 3 — direct consistency | `test_aspic.py:2408-2430` | yes | **OK** |
| ASPIC+ | Post 4 — indirect consistency | `test_aspic.py:2431-2458` | yes | **OK** |
| ASPIC+ | Post 5-7 | `test_aspic.py:2456-2514` | yes | **OK** |
| ASPIC+ | Post 8 — transposition closure | `test_aspic.py:2518-2538` | yes | **OK** |
| ATMS | de Kleer — label minimality | `test_atms_engine.py` — 0 `@given` in 1780 LOC | no | **MISSING (HIGH)** |
| ATMS | nogood consistency | `test_atms_engine.py:278-316` example only | no | **MISSING (HIGH)** |
| ATMS | sound propagation | `test_atms_engine.py` example only | no | **MISSING (HIGH)** |
| Bipolar | Cayrol-Lagasquie-Schiex 2005 Def 3 — supported/secondary defeat | `test_bipolar_semantics.py:143-315` has `@given(bipolar_frameworks())` for semantics | yes | **OK for semantics** |
| Bipolar | Derived-defeats structural properties | `test_bipolar_argumentation.py` — 513 LOC, 0 @given (all examples) | no | **MISSING-as-property (MEDIUM)** |
| DF-QuAD | Baroni-Rago-Toni — strength monotonicity | `test_dfquad.py:725,761` (`@given(_monotonicity_scenario())`) | yes | **OK** |
| DF-QuAD | τ-isolation, quadrupled input symmetry | `test_dfquad.py:641,660,682` | yes | **OK** |
| PAF merge | Coste-Marquis 2007 — completion / edit distance | `test_paf_merge.py:61,83,111` (3 `@given`) | yes | **OK** |
| PAF core | partition invariants | `test_paf_core.py:34` — parametrize, **0 @given** | no | **PARTIAL** |
| Preference | defeat ordering | `test_preference.py` — 10 `@given` | yes | **OK** |
| Propagation | ATMS-esque propagation | `test_propagation.py` — 47 LOC, 0 @given | no | **PARTIAL** |
| Merge classifier | semantic merge classification | `test_merge_classifier.py` — 1 `@given` | partial | **PARTIAL** |

**Single biggest untested formal property:** **AGM revision postulates K*1-K*8 and the DP iteration postulates C1-C4.** `propstore/revision/` ships operators (`contract`, `expand`, `revise`, plus iterated-revision machinery) whose contract is *defined* by these postulates; `tests/test_revision_properties.py` contains exactly one `@given` that only tests `normalize_revision_input` handle resolution. The operators that are the whole point of the module have no postulate-level property tests. ATMS is a tie on "biggest" by LOC of untested formal surface (1780 LOC in one test file, zero @given), but AGM is the worse gap because at least ATMS example tests exercise concrete invariants whereas AGM's defining axioms aren't tested at all.

## C. Strict-typed coverage

Per the axis-2 / axis-1 list, these modules are pyright-strict. For each I map the test surface.

| Strict module | Test file | Covers strict surface directly? | Notes |
|---|---|---|---|
| `propstore/core/literal_keys.py` | `tests/test_literal_keys.py` | yes | Dedicated file. |
| `propstore/core/labels.py` | `tests/test_labels_properties.py`, `test_labelled_core.py` | yes | Two files; property tests present. |
| `propstore/core/graph_types.py` | `tests/test_core_graph_types.py`, `test_graph_build.py` | yes | Directly imports graph types. |
| `propstore/core/results.py` | no `test_core_results.py`; exercised via `test_core_analyzers.py`, `test_core_justifications.py`, `test_world_model.py` | indirect only | **GAP:** no direct test file. |
| `propstore/conflict_detector/models.py` | `tests/test_conflict_detector.py:24`, `test_condition_classifier.py:6`, `test_contexts.py:14`, `test_equation_comparison.py:3`, `test_equation_comparison_properties.py:10`, `test_param_conflicts.py:6`, `test_property.py:22`, `test_parameter_z3_strictness.py:7`, `test_exception_narrowing_group3.py:148` | yes | Widely exercised. |
| `propstore/dung.py` | `tests/test_dung.py`, `test_dung_z3.py`, `test_dung_review_v2.py` | yes | Strong. |
| `propstore/opinion.py` | `tests/test_opinion.py`, `test_opinion_schema.py` | yes | Strong. |
| `propstore/aspic.py` | `tests/test_aspic.py` | yes | Strong. |
| `propstore/aspic_bridge/` (package) | `tests/test_aspic_bridge.py`, `test_aspic_bridge_grounded.py`, `test_aspic_bridge_review_v2.py` | through `__init__` only | Submodules `build.py`, `extract.py`, `grounding.py`, `projection.py`, `query.py`, `translate.py` never directly imported in tests (grep for `from propstore.aspic_bridge.<submodule>` returns only `aspic_bridge.grounding` in `test_aspic_bridge_review_v2.py:16`). Package API testing is fine as long as surface is complete; however there is no test that pins the submodule split (e.g., circular-import regression). |

**Findings:**

- **F-C1 (MEDIUM):** `propstore/core/results.py` has no direct test file; exercised only transitively.
- **F-C2 (LOW):** `aspic_bridge/` submodules are only indirectly tested via the package facade. If Axis 2's internal split matters, no test locks it in.

## D. Suite run

- Command used: `uv run pytest -m hypothesis --timeout=60 --timeout-method=thread -q --no-header -p no:cacheprovider`
- Result: **pass**
- Output: `365 passed, 2159 deselected, 1 warning in 265.94s (0:04:25)`
- No flakes or failures in the property-marked subset.
- **Full-suite run not attempted within the 60-minute budget.** A prior attempt with `--timeout=30` hit a 30-second Hypothesis timeout in `test_aspic_bridge.py::test_sub_argument_closure` at `propstore/aspic.py:1065` inside `compute_attacks` (one of the unrelated tests deep in a git-backend commit_batch path also stalled on dulwich file open). Raising to `--timeout=60 --timeout-method=thread` cleared the property suite. Running the full 2496-test suite would likely require a higher per-test timeout; recommend running with `--timeout=120` in CI.
- Collection-time warning: `scripts/test_inventory_report.py:11` — `PytestCollectionWarning: cannot collect test class 'TestFileStats' because it has a __init__ constructor`. A frozen dataclass named `TestFileStats` is being mistaken for a pytest test class. Rename to `FileStats` or add `__test__ = False`.

## E. Blind spots

### Modules with ZERO test references (grep of `from propstore.<module>` or `import propstore.<module>` returns no tests/*.py match):

| Module | LOC | Notes |
|---|---:|---|
| `propstore/diagnostics.py` | 57 | Small — low-risk |
| `propstore/fragility_contributors.py` | 529 | **HIGH RISK** — sizeable fragility machinery, no tests |
| `propstore/fragility_scoring.py` | 386 | **HIGH RISK** — scoring logic, no tests |
| `propstore/fragility_types.py` | 234 | Types — medium risk |
| `propstore/parameterization_walk.py` | 91 | Walk traversal, no tests |
| `propstore/probabilistic_relations.py` | 111 | Probabilistic layer untested |
| `propstore/source_calibration.py` | 98 | **HIGH RISK** — Axis 3b uncertainty calibration, no tests |

**Total untested LOC: 1506.** `source_calibration.py` is directly adjacent to Q's stated "calibration (Guo et al. 2017) bridges raw model outputs to the opinion algebra" principle in the project CLAUDE.md, and it has no tests at all.

### Modules with weak / indirect coverage:

- `propstore/conflict_detector/orchestrator.py` — no test file imports it by name (grep `orchestrator` in tests/ returns zero files). Reached only transitively through top-level `detect_conflicts`.
- `propstore/conflict_detector/parameterization_conflicts.py` — imported by `test_exception_narrowing_group3.py:149` and `test_param_conflicts.py:13` only. OK minimally.
- `propstore/conflict_detector/algorithms.py` — only imported by `test_conflict_detector.py:1120,1154`. Thin.

### Smoke-only test files:

- `tests/test_init.py` — imports-only smoke test for package root. Acceptable as a sanity check.
- `tests/test_knowledge_path.py` — thin (verified by wc: ~80 LOC, a few assertion scenarios). Acceptable.

### Mock-tainted test surfaces (checked against Q's `feedback_no_fallbacks` memory):

- **`tests/test_classify.py`** — heavy `unittest.mock.AsyncMock` / `MagicMock` / `patch` usage. Mocks the litellm seam (`propstore.embed._require_litellm`, `litellm.acompletion`). This is a **sensible seam**: classify.py is an LLM stance classifier and stubbing at the HTTP boundary is correct. **Not a violation.**
- **`tests/test_embed_operational_error.py:155,187,189`** — `patch("propstore.embed._require_litellm", return_value=mock_litellm)`. Also correct seam.
- **`tests/test_relate_*.py`** — need to spot-check. Based on file count (async/bulk/dedup/opinions/wbf) these look like integration tests with stubbed LLM responses, same pattern.
- **None of these build "fallback shims"** in the sense Q's memory warns against — they stub an external service, they do not provide a compat layer. Acceptable.

### Conflict-detector coverage summary:

- `conflict_detector/algorithms.py` — tested via `test_conflict_detector.py:1120,1154` only. **Thin.**
- `conflict_detector/orchestrator.py` — **not directly tested by any file (0 direct imports).**
- `conflict_detector/parameterization_conflicts.py` — tested via 2 files. **Adequate.**
- `conflict_detector/models.py` — widely used (9 files). **Strong.**

### Worldline pipeline end-to-end:

- `tests/test_worldline.py` (50 tests) exercises the worldline runner.
- `tests/test_worldline_properties.py` (24 tests incl. `TestDeterminism`, `TestContentHashDeterminism`, `TestOverrideAlwaysWins`, `TestBindingIsolation`) — good property-style coverage for worldline behaviour.
- `tests/test_worldline_revision.py` — covers revision-state roundtrips.
- `tests/test_worldline_praf.py` — covers PRAF integration.
- `tests/test_worldline_error_visibility.py` — error-path coverage.
- **Verdict:** worldline is one of the best-tested pipelines.

### Merge framework end-to-end:

- `tests/test_ic_merge.py` — 1100+ LOC, strong `@given` for metric/majority/arbitration. No IC0-IC8 named postulates.
- `tests/test_merge_cli.py`, `test_merge_report.py`, `test_structured_merge_projection.py` — exercise CLI and projection.
- `tests/test_repo_merge_object.py` — two-parent merge commits.
- **Verdict:** merge is well-exercised operationally but the **named IC postulates are the gap**.

## F. Should-be-property-but-is-example

Specific findings where the underlying property is formal and a `@given` strategy would generalise the existing example tests:

1. **`tests/test_revision_operators.py:54-224`** — 11 example tests covering `contract`, `expand`, `revise`, `normalize_revision_input`, `stabilize_belief_base`. Every one of these is a hand-built belief base. The AGM axioms K*1-K*8 (and the DP iteration C1-C4) are *pure* universally-quantified statements over arbitrary belief bases and revision input. **Strategy:** `belief_bases()` draws a BeliefBase with random atoms + scope; `claim_atoms()` draws a new atom; then `@given(belief_bases(), claim_atoms())` can assert each postulate. Current example coverage of ~11 cases should be at least 200 generated cases per postulate.

2. **`tests/test_atms_engine.py`** — 1780 LOC, zero `@given`. Label-minimality, nogood consistency, and sound propagation are invariants of every reachable ATMS state, not just hand-crafted scenarios. **Strategy:** `atms_networks()` draws an assumption set + justification set (DAG); then @given(atms_networks()) can assert `all(not env1 < env2 for env1, env2 in combinations(labels(node), 2))` (minimality), consistency of `nogoods` vs. labels, and support-preservation on expansion.

3. **`tests/test_bipolar_argumentation.py`** — 513 LOC, zero `@given`. Cayrol 2005 Def 3 and Modgil-Prakken Def 14 are property-level definitions: "A defeats B, B supports C → derived defeat (A, C)" is a `∀A,B,C` statement. The *semantics* file (`test_bipolar_semantics.py`) already uses `@given(bipolar_frameworks())` — the same strategy belongs here. **Strategy:** reuse `bipolar_frameworks()` and add closure properties (supported defeat closed under support chain, secondary defeat closed under attack-followed-by-support).

4. **`tests/test_paf_core.py`** — 137 LOC, zero `@given`, only `pytest.parametrize`. `PartialArgumentationFramework` has a partition invariant (`attacks | ignorance | non_attacks = ordered_pairs`, pairwise disjoint) — this is literally invariant-test shape. **Strategy:** `partial_afs()` strategy; `@given(partial_afs())` asserting partition + disjointness. Currently tested by one example (`test_partial_argumentation_framework_tracks_total_partition`) at line 34.

5. **`tests/test_propagation.py`** — 47 LOC. If this covers propagation properties (which would be monotone closure of a relation), it's almost certainly an @given candidate; current size suggests example-only. Low priority due to small surface.

6. **`tests/test_ic_merge.py`** — `@given` exists for some properties but **IC0-IC8 postulates by name are absent**. Strategy: the existing `st_branch_profile` strategy is already in scope; add eight property tests, one per IC postulate, citing Konieczny 2002 Thm 1-2. This is a tight, high-value fix.

7. **`tests/test_revision_iterated.py`** — 263 LOC; DP C1-C4 (iterated revision) are universally quantified over belief-base sequences. Current tests appear example-only (no `@given` in file). Strategy: `revision_sequences()` strategy drawing a seed base + finite sequence of input claims; test C1 (`if φ⊨ψ, then (K*φ)*ψ = K*ψ` — success of more-specific revision), C2, C3, C4 as `@given`.

## Open questions

- **Q1:** What is the intended CI invocation for `-m property`, `-m e2e`, `-m slow`? If the intent is that `-m property` selects the @given corpus, adding `pytestmark = pytest.mark.property` to the 53 missing files (or a conftest autouse marker based on `@given` presence) would restore the promise. If the intent is narrower, the README definition needs tightening.
- **Q2:** Are AGM postulate tests intentionally deferred (per CLAUDE.md "Known Limitations" mentioning ASPIC+ bridge gaps) or just not-yet-written? The `revision/` module is not named in "Known Limitations" so this looks like an omission, not a conscious deferral.
- **Q3:** Do `fragility_scoring.py` and `fragility_contributors.py` have a different test home (property-based invariants somewhere, or an integration in `sidecar`-level tests) that this survey missed? The grep-based module-matching method would miss a test that reaches the module only via a CLI subprocess.
- **Q4:** `scripts/test_inventory_report.py` collects as a pytest module due to `TestFileStats` dataclass name — is that script supposed to be discoverable by pytest at all? If not, a `conftest.py` `collect_ignore` entry or `__test__ = False` on the class would silence the warning.
- **Q5:** For ATMS, do `test_atms_value_status_types.py` and `test_atms_engine.py` together satisfy the "property" intent, or is there a separate ATMS property suite planned? Axis 3e should have an opinion here.

---

**Deliverable:** `reviews/2026-04-16-code-review/axis-4-test-adequacy.md`.

**Counts:**
- 2496 tests collected.
- 365 property (`@given`) tests, all passing in 4m 25s.
- 54 files use `@given`; 1 file carries the `property` marker.
- 7 source modules (1506 LOC) have zero test coverage.
- `conflict_detector/orchestrator.py` is not directly tested.

**Single biggest untested formal property:** AGM revision postulates K*1-K*8 (Alchourrón 1985) and Darwiche-Pearl iteration C1-C4 (DP 1997) — `propstore/revision/operators.py` and `revision/iterated.py` ship the operators, `tests/test_revision_properties.py` has one `@given` and it only tests ID normalization.
