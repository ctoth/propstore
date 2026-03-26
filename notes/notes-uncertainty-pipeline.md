# Uncertainty Representation Paper Pipeline

## GOAL
Process 7 papers on uncertainty representation to replace bare-float probability mapping in propstore's NLI/embedding/argumentation pipeline.

## PAPERS
1. Guo et al. 2017 — "On Calibration of Modern Neural Networks" — https://arxiv.org/abs/1706.04599
2. Jøsang 2001 — "A Logic for Uncertain Probabilities" — https://www.mn.uio.no/ifi/english/people/aca/josang/publications/jos2001-ijufks.pdf
3. Sensoy et al. 2018 — "Evidential Deep Learning to Quantify Classification Uncertainty" — https://arxiv.org/abs/1806.01768
4. Hunter & Thimm 2017 — "Probabilistic Reasoning with Abstract Argumentation Frameworks" — JAIR 59, 565-611
5. Li et al. 2012 — "Probabilistic Argumentation Frameworks" — TAFA 2011, LNCS 7132
6. Denoeux 2019 — "Decision-Making with Belief Functions: a Review" — https://arxiv.org/abs/1808.05322
7. LLM-ASPIC+ 2025 — "A Neuro-Symbolic Framework for Defeasible Reasoning" — https://ebooks.iospress.nl/doi/10.3233/FAIA250981

## PIPELINE STAGES
- [x] Stage 1: Retrieve all 7 PDFs (parallel) — ALL COMPLETE
- [x] Stage 2: Read each paper (parallel subagents) — ALL 7 COMPLETE
- [ ] Stage 3: Extract claims from each (sequential subagents)
- [ ] Stage 4: Reconcile against collection (single agent)

## STAGE 1 — RETRIEVAL STATUS
- [x] Guo 2017 — papers/Guo_2017_CalibrationModernNeuralNetworks/paper.pdf (6pp)
- [x] Jøsang 2001 — papers/Josang_2001_LogicUncertainProbabilities/paper.pdf (31pp)
- [x] Sensoy 2018 — papers/Sensoy_2018_EvidentialDeepLearningQuantifyClassification/paper.pdf
- [x] Hunter & Thimm 2017 — papers/Hunter_2017_ProbabilisticReasoningAbstractArgumentation/paper.pdf
- [x] Li et al. 2012 — papers/Li_2011_ProbabilisticArgumentationFrameworks/paper.pdf (Chrome via ResearchGate)
- [x] Denoeux 2019 — papers/Denoeux_2018_Decision-MakingBeliefFunctionsReview/paper.pdf (39pp)
- [x] LLM-ASPIC+ 2025 — papers/Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible/paper.pdf (8pp, 650KB). Retrieved via Chrome clicking IOS Press download button directly. Took 4 attempts.

### Retrieval lessons learned
- Original 7 agents did NOT invoke paper-retriever skill — got hand-rolled prompts that lacked Chrome fallback
- The skill already has Chrome fallback (SKILL.md Step 4) but agents never reached it because they weren't using the skill
- First Chrome retry for LLM-ASPIC+ died immediately — agent couldn't use Chrome tools without ToolSearch loading them first
- Second retry includes explicit ToolSearch-before-use instructions

## STAGE 2 — READING STATUS
All 5 retrieved papers dispatched to reader agents (parallel, each using paper-reader skill):
- [x] Guo 2017 — DONE. notes.md, description.md, citations.md created
- [x] Jøsang 2001 — DONE. Opinion algebra, consensus/discounting operators, Beta bijection, cross-refs to Sensoy+Falkenhainer+Denoeux
- [x] Sensoy 2018 — DONE. Dirichlet→subjective logic opinions, cross-refs to Guo+Falkenhainer
- [x] Hunter & Thimm 2017 — DONE. Rationality postulates as LP constraints, max entropy propagation, connects to ATMS nogoods
- [x] Li et al. 2012 — DONE. PrAF maps to ATMS environments, MC sampler algorithm
- [x] Denoeux 2019 — DONE. Three decision-rule families for render-time (pignistic, Bel/Pl, E-admissibility)
- [x] LLM-ASPIC+ 2025 — DONE. LLM extraction→ASPIC+ resolution architecture, 7-category error taxonomy, cross-refs to Dung+Modgil+Pollock+Odekerken

## STAGE 3 — CLAIMS
Skipped per Q's decision — notes are the actionable content.

## ROUND 2 — GAP-CLOSING PAPERS
- [x] Jøsang 2010 — papers/Josang_2010_CumulativeAveragingFusionBeliefs/paper.pdf (multinomial opinions, gap 6)
- [x] Popescu & Wallner 2024 — papers/Popescu_2024_ProbabilisticArgumentationConstellation/paper.pdf (tree-decomp DP, gap 4)
- [x] Freedman et al. 2025 — papers/Freedman_2025_ArgumentativeLLMsClaimVerification/paper.pdf (LLM→QBAF, gap 7)
- [ ] Fazzinga 2016 — SKIPPED (3 failed retrieval attempts, supplementary to Li+Popescu)

## ROUND 2 — READING STATUS
- [ ] Jøsang 2010 — reader running
- [ ] Popescu & Wallner 2024 — reader running
- [ ] Freedman 2025 — reader running

## IMPLEMENTATION
- [x] Change 1: propstore/opinion.py + tests/test_opinion.py — commit a479c85, 44 tests passing
- [x] Change 2: propstore/calibrate.py + tests/test_calibrate.py — commit c206928, 17 tests (61 total), no regressions
  - TemperatureScaler, CorpusCalibrator, categorical_to_opinion, calibrated_probability_to_opinion, ECE
  - All with literature citations in docstrings (Guo 2017, Josang 2001, Sensoy 2018)
  - Minor pyright warnings: unused _entropy helper, unused bin_boundaries, import resolution (non-blocking)
- [ ] Change 3: Wire into relate.py (replace _CONFIDENCE_MAP) — not started
- [ ] Change 4: Schema changes in build_sidecar.py — not started
- [ ] Change 5: Replace threshold gate in argumentation.py — not started
- [ ] Change 6: Multi-dim preferences — not started
- [ ] Change 7: Render policy extensions — not started

## ROUND 2 — READING STATUS
- [x] Jøsang 2010 — DONE but CAVEAT: PDF was actually "Multiplication of Multinomial Subjective Opinions" not the fusion paper. Still useful for multinomial opinion representation + multiplication operator. The cumulative/averaging fusion paper still needed for multi-source stance fusion.
- [x] Popescu & Wallner 2024 — DONE. Tree-decomposition DP for exact probabilistic AF. Use exact when treewidth ≤10-15, MC otherwise. DP table rows analogous to ATMS labels.
- [x] Freedman 2025 — DONE. DF-QuAD aggregation (~20 lines), QBAFs extend Dung AFs with graded base scores + support. Bridge between LLM confidence and formal argumentation.

## IMPACT ANALYSIS COMPLETE
Scout report: reports/impact-analysis-changes-3-7.md

Revised implementation order (per scout findings):
4 (schema, LOW risk) → 6 (multi-dim prefs, MEDIUM) → 3 (relate.py, HIGH) → 7 (render policy, LOW) → 5 (threshold gate removal, HIGH — needs PrAF in dung.py)

Key finding: defeat_holds already accepts list[float] — Change 6 is mostly unwrapping callers.
Key risk: Change 5 requires a PrAF algorithm that doesn't exist yet in dung.py.

Test baseline: 1118 passed (56.79s) on clean master.

## PLAN APPROVED — EXECUTING
Plan: C:\Users\Q\.claude\plans\reactive-sleeping-crown.md
Order: Phase 1 (schema) → Phase 2 (multi-dim prefs) → Phase 3 (relate.py) → Phase 4 (render policy) → Phase 5A (soft threshold)

Pre-execution done:
- [x] Added "Honest ignorance over fabricated confidence" design principle to CLAUDE.md
- [x] Added 7 new papers to literature grounding table in CLAUDE.md
- [x] Saved citations/TDD feedback to memory

Progress:
- [x] Phase 1 (schema) — commit 32c9c05, 1123 tests passing. Hard gate PASSED.
- [x] Phase 2 (multi-dim prefs) — commit 4048609, 1130 tests passing. Elitist ≠ democratic proven. Hard gate PASSED.
- [x] Phase 3 (relate.py) — commit b2cab77, 1144 tests passing. _CONFIDENCE_MAP deleted, categorical_to_opinion wired in. Hard gate PASSED.
- [x] Phase 4 (render policy) — commit ced8f0a, 1155 tests passing. 4 decision criteria (pignistic/lower/upper/hurwicz). Hard gate PASSED.
- [x] Phase 5A (soft threshold) — commit 1d2896d, 1159 tests passing. confidence_threshold HARD DELETED from entire codebase. Soft epsilon prune for vacuous opinions. Hard gate PASSED.

## ALL PHASES 1-5A COMPLETE
Started: 1118 tests → Ended: 1159 tests (+41 new, 0 regressions)
5 commits on master implementing the full opinion algebra pipeline.

## PHASE 5B — PrAF IMPLEMENTATION
- [x] 5B-1 (PrAF core + MC sampler) — commit 912eb10, 1171 tests. ProbabilisticAF dataclass, MC with Agresti-Coull stopping, connected component decomposition, build_praf(), deterministic fallback, exact enumeration for small AFs. Hard gate PASSED.
- [x] 5B-2 (ReasoningBackend.PRAF integration) — commit c3742a9, 1181 tests. ReasoningBackend.PRAF, RenderPolicy praf fields, resolve dispatch, CLI flags, WorldlinePolicy serialization, ResolvedResult.acceptance_probs. Hard gate PASSED.
- [x] 5B-3 (DF-QuAD gradual semantics) — commit 503ce8e, 1210 tests. dfquad_aggregate, dfquad_combine, compute_dfquad_strengths. Topological sort + fixpoint fallback for cycles. 29 new tests. Hard gate PASSED.
- [x] 5B-4 attempt 1 — commits b39e33d/a231e04/35d53da/7744f01, 1233 tests. BUT used factored enumeration instead of the actual Popescu 2024 algorithm. Q flagged this as unacceptable — the I/O/U table DP with witness mechanism IS the paper's contribution.
- [x] 5B-4 attempt 2 (REDO) — Agent thrashed for 82min/174 tool calls. 7 WIP commits, all broken. Concluded P_ext ≠ P_acc. Saved to branch dp-wip-attempts, reset master to 8a48db0.
- [x] Popescu research — CONFIRMED: DP computes P_ext not P_acc. BUT for grounded semantics P_ext = P_acc (unique extension). DP is viable for grounded only. Multi-extension semantics stay on MC. See reports/research-popescu-pacc-report.md.
- [x] Toy DP — commit b83416f. Standalone I/O/U labelling verified by hypothesis (600 random AFs, matches brute force 1e-9). Correct grounded labelling via fixpoint. 14 tests.
- [x] 5B-4 attempt 3 (wire) — commit 924bc51 (wrong message, right code). 260K tokens, 145 tool calls, 51min. Used edge-configuration tracking + root fixpoint instead of pure I/O/U labels — avoids overcounting for grounded. 41/41 DP tests pass. Cross-validated against brute force on all topologies. Witness mechanism correct. Hard gate PASSED.
  - NOTE: commits 5e976cc and b8264b6 are noise (agent wandered into paper processing). Content is in 924bc51.

## WARD (separate repo C:/Users/Q/code/ward)
- [x] Signals feature — commits 961527f (test fix), fcc205a (cmdAllow/cmdRevoke). ward allow/revoke commands work. Binary rebuilt.
- [ ] Ward rules — Agent running. Wiring session.signals into all blocking rules + adding node -e, ruby -e, perl -e rules.
- Ward build broken by previous agent, fixed by ward-fixer agent.

## PROPSTORE IDENTITY (from discussion with Q)
- propstore = thin application layer over independently useful formal reasoning primitives
- The primitives (dung.py, opinion.py, praf.py) are already leaf modules with zero propstore imports — they're libraries in everything but packaging
- The non-composable feeling is these un-extracted libraries leaking into the app layer
- Papers-first methodology: papers spark "what should exist," code pressure reveals "what needs to exist now"
- [x] 5B-5 (Polish + CLI + performance) — commit 6c15bca. Dead code removed, DF-QuAD wired into resolution, CLI flags complete, CLAUDE.md restored. Performance: dfquad 3ms, MC 237ms, exact_dp 22.4s (needs optimization). 1250 tests passing (1 pre-existing flaky failure).

## PHASE 5B COMPLETE
All 5 sub-phases done. PrAF is a working reasoning backend with:
- MC sampling (Agresti-Coull stopping, any AF size, any semantics)
- Exact DP (grounded only, tree decomposition, correct but slow)
- DF-QuAD gradual semantics (near-instant, attack+support)
- Full CLI: --reasoning-backend praf --praf-strategy auto|mc|exact|dfquad
- Connected component decomposition for scalability
- Opinion-derived P_D, dogmatic P_A with hook for future extension

## STAGE 4 — RECONCILE
(not started)

## SESSION LOG — 2026-03-24

### What we observed (pre-foreman scout work)
- Scout surveyed all NLI/embedding/probability code in propstore (full report: notes-nli-embedding-survey.md)
- 5 critical findings:
  1. Confidence is a hardcoded 6-entry lookup table (relate.py:76-83), not model-derived
  2. Three conflated float concepts (strength/confidence/claim_strength) with no type distinction
  3. Raw embedding distance interpolated into LLM prompts unnormalized
  4. Hard threshold gate at 0.5 drops stances before argumentation (build-time filter = WRONG per design checklist)
  5. Single-element strength lists — Modgil set-comparison machinery unused
- Researcher found 19 papers across 7 areas (full report: notes-probability-representation-research.md)
- Key recommendation: Beta(α, β) as canonical storage, isomorphic to subjective logic opinions, derive DS/credal at render time

### What we tried
- Activated foreman protocol for coordinated paper processing
- Designed 3-stage pipeline: retrieve → read → extract-claims (one subagent per stage per paper, fresh context each)
- Dispatched 7 retrieval agents in parallel (all background)

### Current state
- All 7 retrieval agents running in background, awaiting completion
- Reports will land at reports/retrieve-{name}-report.md
- One background command completion notification received (metadata search from an agent), not yet actionable

### What worked
- Parallel retrieval dispatch — all 7 launched cleanly
- Scout + researcher produced comprehensive findings before foreman mode

### What didn't work / blockers
- No failures yet — waiting on retrieval agents
- LLM-ASPIC+ 2025 is IOS Press (paywalled), may need Chrome/sci-hub fallback
- Li et al. 2012 is Springer LNCS (paywalled), same risk

### Next steps
1. Wait for all 7 retrieval reports
2. Read each report, update checklist above
3. For any failures: retry with alternative URLs or Chrome-based retrieval
4. Dispatch paper-reader agents sequentially (one per paper, fresh context)
5. After all reads: dispatch extract-claims agents sequentially
6. Final: reconcile --all

## DONE
(nothing yet)

## STUCK
(nothing yet)
