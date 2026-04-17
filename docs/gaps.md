# Known Gaps — propstore

This file is the source of truth for gaps between propstore's rhetoric / cited papers / intended behavior and the current implementation. Replaces CLAUDE.md's old "Known Limitations" section, which the 2026-04-16 code review (`reviews/2026-04-16-code-review/axis-6-limitation-honesty.md`) found to be materially inaccurate.

## Discipline

- Every gap has a severity, a citation (axis finding, paper, or observation source), and a plan (workstream, or explicit "not planned").
- Gaps are only added when *observed* (by a reviewer, an agent, or a test failure).
- Gaps are only removed when a test proves closure — the commit that closes a gap also deletes its entry here, and the commit message references the gap entry.
- New workstreams grep this file for relevant gaps; closures happen atomically with implementation.

## Open gaps

### CRIT / structural

- **`_DEFAULT_BASE_RATES` fabricates a "corpus frequency prior" without a corpus.** `propstore/calibrate.py:211-217` hard-codes `{"strong": 0.7, "moderate": 0.5, "weak": 0.3, "none": 0.1}` and feeds them into `Opinion.vacuous(a=...)` as the base-rate slot for every uncalibrated LLM classification. The one signal subjective logic reserves for honest prior ignorance is silently filled with category-keyed guesses. Citation: axis-1 Finding 2.1; axis-6 item 9. Plan: WS-Z-types phase 4.

- **`praf/engine.py` `p_arg_from_claim` / `p_relation_from_stance` fallback to `Opinion.dogmatic_true()`.** `propstore/praf/engine.py:155-157, 197-199, 245-253` — when a claim has no structured fields, or when a stance has no opinion/confidence data, the hook returns maximum-certainty dogmatic true (or dogmatic_false on `confidence <= 1e-12`). Every unrated claim or stance becomes dogmatic; the "backward compat" comment on line 252 acknowledges the hack. Citation: axis-1 Finding 2.2; axis-5 Findings 1.1, 1.2, 1.5. Plan: WS-Z-types phase 5.

### HIGH

- **`fragility_scoring.imps_rev` fabricates dogmatic opinions for every argument and defeat.** `propstore/fragility_scoring.py:366-367` initializes `p_args = {a: Opinion.dogmatic_true() for a in ...}` and `p_defeats` likewise before running the sensitivity analysis sold as measuring "fragility under uncertainty." Citation: axis-1 Finding 2.3; axis-6 item 8; axis-5 Category 1. Plan: WS-Z-types (bundled with 2.2 consumer update).

- **`source_calibration.derive_source_trust` silently defaults `prior_base_rate=0.5` without provenance.** `propstore/source_calibration.py:39, 65, 94-97` stores a float `prior_base_rate` on `SourceTrustDocument` that could mean "we derived this from a chain query" or "we had nothing and used 0.5" — no provenance field distinguishes. The finalize report's `calibration.fallback_to_default_base_rate` boolean lives on a separate document. Citation: axis-1 Finding 2.4. Plan: WS-Z-types phase 6 + WS-A P1.

- **Z3 three-valued results collapse to `bool` everywhere.** `propstore/z3_conditions.py:442-444, 459-463, 481, 489` map `solver.check() == z3.sat/unsat/unknown` into two-valued returns. Every downstream conflict-class decision, context-activation decision, and assignment-selection merge validity check silently maps unknown to a plausible-looking Boolean outcome. No timeouts are ever set (`timeout|set_param|set_option` → zero hits across `propstore/`). Citation: axis-5 Findings 2.1-2.3; axis-6 item 4. Plan: WS-Z-types phases 1-2.

- **`condition_classifier.py` silently maps Z3 `unknown` to `ConflictClass.OVERLAP`.** `propstore/condition_classifier.py:32-36` falls through to OVERLAP when neither `are_equivalent` nor `are_disjoint` returned True — but those returns already collapsed `unknown` to False. Every Z3 timeout anywhere in the system becomes a fabricated OVERLAP conflict record. `ConflictClass` enum has no `UNDECIDABLE` variant. Citation: axis-5 Finding 2.4 (most dangerous single site). Plan: WS-Z-types phases 1-2.

- **CLAUDE.md "Pignistic" claim names Denoeux but implements Jøsang.** `propstore/world/types.py:1064-1066` is labeled `"pignistic"` and cites Denoeux p.17-18, but the implemented formula is Jøsang `b + a·u`; Denoeux's binomial BetP is `b + u/2`. Diverges whenever `a ≠ 0.5`. Citation: axis-6 declared-limitation 2 status "materially false"; axis-3b F2. Plan: WS-Z-types (axis-3b docket).

- **`opinion.wbf()` is algebraically aCBF, not WBF.** `propstore/opinion.py` implementation has three structural divergences from the van der Heijden 2018 WBF formula; worked example drifts 0.175 absolute on uncertainty. Commit `c7a9215` self-acknowledges the open bug. Citation: axis-6 declared-limitation 4 "materially false"; axis-3b F1. Plan: WS-Z-types (axis-3b docket).

- **AGM revision is AGM in name only.** `propstore/revision/` is 1663 LOC with zero literature citations in source and zero K*1-K*8 / C1-C4 / EE1-EE5 / P*1-P*6 / A*1-A*6 tests. "Entrenchment" is a weighted-support-count total order, not Gärdenfors entrenchment. Recovery (K*6) is not even syntactically expressible. Citation: axis-6 item 1; axis-3c. Plan: WS-B (belief-set layer).

- **AF revision (Baumann/Diller/Cayrol) absent entirely.** `propstore/revision/af_adapter.py` does not implement AF revision — it projects an active-claim subset of a store. No module implements Baumann 2015 expansion kernels, Diller 2015 extension-based revision, or Cayrol 2014 change operators. Citation: axis-6 item 2; axis-3c. Plan: WS-B (belief-set layer).

- **Defeasibility priority information unconditionally dropped.** `propstore/grounding/translator.py:171-178` hard-codes `superiority=[]`; `propstore/aspic_bridge/translate.py:275-280` hard-codes `rule_order=frozenset()`. Priority data flows in from rule files and is dropped on the floor twice before reaching the ASPIC+ layer. CLAUDE.md's "rule ordering always empty" understates: the drop is systematic across the whole subsystem. Citation: axis-6 item 6; axis-7; axis-9. Plan: WS-C (defeasibility).

- **LLM "none" stance writes structurally invalid opinion.** `propstore/classify.py:148-161` writes `(0.0, 0.0, 0.0, 0.5)` on `"type": "none"`. `b+d+u = 0 ≠ 1.0` violates `Opinion.__post_init__`. Persists as a dict bypassing validation; downstream `p_relation_from_stance` reads the fields. Citation: axis-5 Finding 1.3; axis-1 Finding 2.6 (structural S3); axis-6 item 7. Plan: WS-A P1 (structural S3 collapse to `opinion: OpinionDocument | None`).

- **Sidecar claim SI normalization silently writes non-SI values to `_si` columns.** `propstore/sidecar/claim_utils.py:596-606` — on `ValueError`/`TypeError` from `normalize_to_si`, the code writes `value_si = typed_fields.value` (i.e., the unnormalized value). Downstream queries trust the `_si` suffix. Citation: axis-5 Finding 3.1. Plan: not yet scheduled (axis-5 docket).

### MED

- **`SourceTrustDocument` lacks a `prior_base_rate_status` field.** `propstore/artifacts/documents/sources.py:43-55` — `b, d, u, a` are required floats with no `status` tag; readers cannot distinguish "we intentionally recorded vacuous" from "we put zeros because we had nothing else." Citation: axis-1 Finding 2.5 (structural S2). Plan: WS-A P1 (structural S2).

- **`dedup_pairs` collapses mirror pairs without provenance.** `propstore/relate.py:67-74` — when `(A,B,0.3)` and `(B,A,0.4)` both exist, keeps the cheaper pair and throws away the other. Silent collapse of two rival evidence records at pair-selection time instead of render time. Citation: axis-1 Finding 1.2. Plan: not yet scheduled.

- **`finalize_source_branch` mutates authored payloads in place.** `propstore/source/finalize.py:96-140` — finalize saves `SOURCE_*_FAMILY` updated documents, overwriting the originals on the source branch. If the user re-runs extract-claims before promote, the finalized layer gets clobbered. The branch preserves one stance (latest finalize), not rival authored-vs-finalized. Citation: axis-1 Finding 1.3. Plan: not yet scheduled.

- **Probabilistic argumentation treewidth bound doesn't deliver.** `propstore/praf/treedecomp.py:13-17` self-documents row count as `O(2^|defeats| * 2^|args|)`, not the Popescu & Wallner 2024 `O(2^tw)` bound the engine dispatch assumes. Queries the engine considers cheap may be exponentially expensive. Citation: axis-6 item 5; axis-3a. Plan: WS-C or independent.

- **Preference heuristic is not Modgil-Prakken.** `propstore/preference.py` uses Pareto dominance on a 3-vector; Modgil-Prakken 2018 Def 22 is a strict partial order from a base ordering over premises. File self-documents the split but the heuristic flows into the bridge unlabeled. Citation: axis-6 item 11; axis-3a. Plan: WS-C (defeasibility).

- **Oikarinen strong-equivalence kernels are absent.** No production module implements Oikarinen 2010 `a`/`a*`/`c` kernels or kernel-based strong-equivalence checks for Dung AFs. Phase 5 of the paper-grounded test-suite workstream searched for a production surface and recorded the absence in `reports/paper-grounded-oikarinen-kernel-gap-2026-04-16.md`; no placeholder tests were added. Citation: axis-3a item 5; paper manifest `Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation`; `plans/paper-grounded-test-suite-workstream-2026-04-16.md` Phase 5. Plan: future argumentation strong-equivalence implementation workstream.

- **`pks world chain` accepts lifecycle flags but does not behaviorally filter.** Phase-4 flagged: `chain` accepts `--include-drafts` / `--include-blocked` / `--show-quarantined` for CLI symmetry but `chain_query` reads parameterizations and relationship state rather than a filtered claim set — the constructed `_lifecycle_policy` sits unused. Citation: phase-4 coder report (`reports/ws-z-gates-04-renderpolicy-cli.md` deviation 2; flag 2). Plan: future workstream when chain-query materially consumes claim sets.

- **CLAUDE.md references `aspic_bridge.py` as a file, but it is now a package.** CLAUDE.md lines 35, 45; README.md; `docs/argumentation.md:30`; `docs/data-model.md:332`; `agent-papers.md`; `EXPLORATION_NOTES.txt` all still reference `aspic_bridge.py`. The file does not exist; `aspic_bridge/` does. Citation: axis-9 Findings A.3, E.2, E.3, E.4. Plan: CLAUDE.md rewrite (phase beyond WS-Z-gates).

- **`aspic.py` cites "Modgil & Prakken 2018 Def 1 (p.8)" for contrariness — wrong number, wrong page, wrong content.** `propstore/aspic.py:55, 74, 91-93` — Def 1 is on page 4 (Dung acceptability); contrariness is Def 2, page 8. Same phantom citation repeated three times. Citation: axis-9 Findings B.1, C.1 (most-damaging single drift). Plan: citation-discipline cleanup (not yet scheduled).

- **`artifacts/documents/rules.py:120` cites Def 13 for last-link.** Modgil & Prakken 2018 Def 13 is defeat-based conflict-free (which the paper argues *against*). Last-link is Def 20 (p.21). Citation: axis-9 Findings B.2, C.2. Plan: citation-discipline cleanup.

### LOW / NOTE

- **10 pyright errors remain in `propstore/source/common.py` after the phase-4 fix.** Commit `5a47bfa` addressed `cli/source.py:33`; the broader `propstore.artifacts` `__getattr__` lazy-dispatch pattern still produces "Object of type 'object' is not callable" errors across other `SOURCE_*_FAMILY` constants and identity helpers. Citation: phase-4 coder report (flag 1). Plan: follow-up typing workstream.

- **Test markers lie about content.** 54 files use `@given`; only 1 carries the `property` pytest marker. `-m property` runs 6 tests when 365 property tests exist. Citation: axis-6 item 13; axis-4. Plan: test-marker audit (not yet scheduled).

- **Seven production modules with zero test references.** 1506 LOC in `diagnostics.py`, `fragility_contributors.py`, `fragility_scoring.py`, `fragility_types.py`, `parameterization_walk.py`, `probabilistic_relations.py`, `source_calibration.py`; plus `conflict_detector/orchestrator.py`. Citation: axis-6 item 14; axis-4. Plan: test-coverage workstream.

- **`papers/index.md` is 21% incomplete.** 44 paper directories have no index entry (Pearl 2000, Pierce 2002, Cousot 1977, Clark 2014, Guha 1991, Halpern 2000 among them); 25 directories have no `notes.md` at all (Toni 2014, Clark 2014, Guha 1991, etc. — cited in code but unverifiable). Citation: axis-9 Category D. Plan: papers-index backfill workstream.

- **CLAUDE.md "Defs 1-22" shorthand for Modgil & Prakken 2018.** Paper extends through Def 23+; Def 1 is plain Dung AFs, not ASPIC+. Citation: axis-9 Finding A.4. Plan: CLAUDE.md rewrite.

- **CLAUDE.md TIMEPOINT claim points at wrong file.** Line 16 semantic claim is correct but the implicit pointer (prompt says check `cel_types.py`) is wrong — `KindType` lives in `propstore/cel_checker.py:38`. Citation: axis-9 Finding A.1. Plan: CLAUDE.md rewrite.

- **Citation-pattern drift across codebase.** `aspic.py`, `world/types.py` (Denoeux→Jøsang), `revision/*.py` (AGM names, not AGM), `wbf()` (WBF name, aCBF computation) all cite papers for authority while implementing something different. Citation: axis-6 item 15; axis-9 cross-cutting. Plan: citation-as-claim CI lint (per disciplines.md rule 1) + workstream-specific closures.

- **`Opinion` invariant `b+d+u=1.0` vs `ResolutionDocument` four independent optional scalars.** `ResolutionDocument` at `propstore/artifacts/documents/claims.py:137-168` permits `(0.0, 0.0, 0.0, 0.5)` (invalid opinion, not None). Structural fix: collapse to `opinion: OpinionDocument | None`. Citation: axis-1 Finding 2.6 (structural S3). Plan: WS-A P1 (structural S3).

## Closed gaps (reference only — kept for traceability)

### Closed 2026-04-17 (WS-B Phase 4)
- axis-3c / axis-6 item 3 — `propstore/world/ic_merge.py` claimed IC-merge lineage while enumerating only `product(observed_values)` assignments. Closed by renaming that production surface to `propstore/world/assignment_selection_merge.py`, migrating callers/tests/docs to `ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE`, and implementing true Konieczny-Pino Perez model-theoretic IC merge over all `mu`-models in `propstore/belief_set/ic_merge.py`. Evidence: `tests/test_assignment_selection_merge.py`, `tests/test_resolution_helpers.py`, `tests/test_render_contracts.py`, and `tests/test_belief_set_postulates.py`.

### Closed 2026-04-17 (WS-A Phase 4)
- axis-3d / axis-6 item 3 — semantic substrate remained incomplete at contexts and micropublications. Closed by WS-A Phase 4: `context_hierarchy.py` was replaced by `context_lifting.py`; `ClaimDocument.context` is required; nested `ist(c, p)` proposition documents exist; source finalize/promote emits canonical `micropubs/{source}.yaml`; sidecar `micropublication` and `micropublication_claim` tables materialize bundles; `WorldModel.all_micropublications()` returns typed `ActiveMicropublication` records; `EnvironmentKey` includes `context_ids`; ATMS seeds context nodes and micropublication nodes. Evidence: `docs/contexts-and-micropubs.md`, `tests/test_context_lifting_phase4.py`, `tests/test_micropublications_phase4.py`, `tests/test_labels_properties.py`, and `tests/test_atms_engine.py`.

### Closed 2026-04-16 (this commit)
- axis-1 Finding 3.1 — raw-id claim quarantine. Closed by commit `67fccc1` (WS-Z-gates phase 3).
- axis-1 Finding 3.2 — compiler draft filter. Closed by commit `5bb948d` (WS-Z-gates phase 3).
- axis-1 Finding 3.3 — source promote all-or-nothing. Closed by commits `8923b9f` + `c263db6` (WS-Z-gates phases 3 + 4).
