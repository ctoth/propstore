# Axis 3a — Argumentation Fidelity

## Summary

propstore implements an unusually faithful structured-argumentation stack around Dung 1995 and Modgil & Prakken 2018 (ASPIC+). The core modules — `propstore/dung.py`, `propstore/aspic.py`, `propstore/aspic_bridge/*.py`, `propstore/bipolar.py`, `propstore/praf/*.py` — cite paper definitions inline at the function level, track `Def N` numbers with page numbers, and are internally consistent. The ASPIC+ bridge (claim graph → rules/literals/contrariness → CSAF → Dung AF) matches the literature's intended construction chain.

Three kinds of gap appear:

1. **Known Limitations correctly declared in code and/or CLAUDE.md** — e.g. `rule_order=frozenset()` in the bridge, PrAF DP not achieving theoretical O(2^tw).
2. **Breadth gaps** — several priority-list semantics (semi-stable, ideal, stage, CF2, ranking-based, weighted-attack, value-based) are not implemented at all but the code never *claims* to. These are MISSING rather than DRIFT.
3. **One genuine theoretical-naming drift** — `propstore/preference.py` is a metadata heuristic that ships alongside the literature-faithful ASPIC+ pipeline, with a distinctive three-component strength vector that the literature does not endorse; the file documents this honestly but names the heuristic `claim_strength` and stays exported under a Modgil & Prakken docstring.

No aspirational citations were found pretending to be implementations, apart from the dialogue-game papers already flagged by the manifest scout.

Finding counts: **1 drift**, **9 missing (breadth gaps)**, **3 aspirational citations (no module)**, **2 stub-noted**.

Biggest drift: the `probabilistic_relations.py` dispatch to the treedecomp DP silently advertises Popescu & Wallner 2024 complexity guarantees that the current implementation does not deliver (documented inside `praf/treedecomp.py` as a Known Limitation, but not surfaced in CLAUDE.md).

## Fidelity verdict per paper (priority papers)

### Dung_1995_AcceptabilityArguments
- Paper's core claim: AF = (Args, Attacks); conflict-free/admissible/complete/grounded/preferred/stable defined set-theoretically via a characteristic function F(S) whose least fixpoint is grounded.
- Code implementation: `propstore/dung.py:18-37` (`ArgumentationFramework`), `:68-79` (conflict_free), `:82-96` (defends), `:99-122` (characteristic_fn), `:125-153` (admissible), `:156-179` (grounded_extension), `:199-236` (complete), `:239-259` (preferred), `:262-291` (stable).
- Match: **full** (for grounded/complete/preferred/stable).
- Notes: Defs 5 (conflict-free), 6 (admissible), 10 (complete), 8 (preferred as maximal complete), 12 (stable), 17 (F), 20+Thm 25 (grounded = lfp) are all present. `ArgumentationFramework` carries both `attacks` and `defeats` so the Modgil & Prakken 2018 Def 14 distinction is honored (conflict-free uses attacks; defense uses defeats) — explicitly commented at `dung.py:125-153`. Paper notes.md is `index` only (no notes.md file) but the paper is canonical and the code cites pages verbatim.

### Modgil_2018_GeneralAccountArgumentationPreferences (ASPIC+ "canonical Defs 1-22")
- Paper's core claim: Full ASPIC+ with preferences; elitist/democratic set comparisons; last-link/weakest-link principles; rationality postulates (Thm 14).
- Code implementation: `propstore/aspic.py:48-134` (Literal, ContrarinessFn, is_contradictory/is_contrary per Defs 1-2), `:137-162` (Rule, Def 2), `:165-246` (PremiseArg/StrictArg/DefeasibleArg, Def 5), `:252-265` (Attack kinds, Def 8), `:267-272` (KnowledgeBase K_n/K_p, Def 4), `:275-300` (PreferenceConfig, Defs 19-22), `:366-452` (transposition_closure, Def 12), `:487-503` (is_c_consistent, Def 6), `:664-758` (build_arguments, Def 5 bottom-up), `:783-964` (build_arguments_for, Def 5 top-down), `:970-1078` (compute_attacks, Def 8), `:1084-1140` (`_set_strictly_less`, Def 19), `:1143-1218` (`_strictly_weaker`, Defs 20-21), `:1221-1280` (compute_defeats, Def 9).
- Match: **full** (for the core objects and computations).
- Notes: The module enforces preference-independence of undercutting attacks and of directional-contrary attacks at `aspic.py:646-658`, matching Def 9 (p.12). Both elitist and democratic comparisons are implemented (Def 19 empty-Gamma edge cases at `aspic.py:1116-1119`). Last-link and weakest-link link modes are distinguished with the strict/firm branches the paper specifies. Rule degeneracy is handled at `aspic.py:312-333`. CLAUDE.md claim "aspic.py builds recursive arguments" VERIFIED at the two construction functions above.

### Caminada_2006_IssueReinstatementArgumentation
- Paper's core claim: Three-valued (in/out/undec) labellings in bijection with complete extensions; semi-stable semantics as labellings with minimal-undec.
- Code implementation: None in `propstore/dung.py`. Grepping `semi_stable|labell|Caminada` across `propstore/` hits only `core/labels.py` (claim-level labels, unrelated), `praf/engine.py` (semantics string dispatch), `praf/treedecomp.py` (I/O/U inside the Popescu & Wallner DP), and `calibrate.py` / `repo/merge_framework.py` (unrelated).
- Match: **missing**.
- Notes: The I/O/U labelling used inside `praf/treedecomp.py:451-600` is a *Popescu & Wallner 2024* DP artifact, not a Caminada-2006 public API. There is no standalone labelling function for a pure Dung AF, no semi-stable computation, no Ext2Lab/Lab2Ext bijection. Paper notes.md confirms semi-stable semantics is the key deliverable at `papers/Caminada_2006_IssueReinstatementArgumentation/notes.md` line 21.

### Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation
- Paper's core claim: BAF = (A, R_def, R_sup) with independent support relation; supported/indirect defeats; d/s/c-admissible; conflict-free and safe.
- Code implementation: `propstore/bipolar.py:9-20` (BipolarArgumentationFramework), `:73-122` (cayrol_derived_defeats fixpoint, Def 3), `:142-152` (set_defeats), `:155-161` (set_supports), `:164-169` (support_closed), `:172-177` (conflict_free, Def 6), `:180-190` (safe, Def 7), `:193-207` (defends, Def 5), `:210-239` (d/s/c-admissible, Defs 9-11), `:268-300` (d/s/c-preferred + stable).
- Match: **full**.
- Notes: Supported-defeat and indirect-defeat closures are computed together in `cayrol_derived_defeats` per Def 3 to a fixpoint (bipolar.py:97-120). Stable extensions computed at `:289-300`.

### Amgoud_2008_BipolarityArgumentationFrameworks
- Paper's core claim: Survey/unification of bipolar AFs; supported-defeat semantics.
- Code implementation: Shared with Cayrol 2005 — `propstore/bipolar.py` entire module.
- Match: **full** (supported-defeat aspect).
- Notes: The paper's gradual-valuation section is not separately implemented; DF-QuAD at `propstore/praf/dfquad.py` is the system's gradual-bipolar representative, citing Freedman 2025 / Rago 2016 rather than Amgoud 2008.

### Dung_2007_ComputingIdealScepticalArgumentation
- Paper's core claim: Unique maximal ideal set lying between grounded and intersection of preferred; ideal dispute trees; GB/AB/IB/Fail-dispute derivations.
- Code implementation: None. Grepping `ideal_extension|ideal_set|IB.dispute|AB.dispute|Fail.dispute|dispute.tree` returns no hits in `propstore/`.
- Match: **missing**.
- Notes: CLAUDE.md's "Known Limitations" section does not mention ideal semantics. Paper notes.md at `papers/Dung_2007_ComputingIdealScepticalArgumentation/notes.md` lines 15-29 documents the semantics and procedures.

### Dunne_2011_WeightedArgumentSystemsBasic
- Paper's core claim: Weighted Argument Systems (WAS): weights on *attacks*; inconsistency budget `beta` relaxes conflict-freeness up to total attack weight; W-grounded/W-admissible/W-preferred semantics.
- Code implementation: None for attack-weighted semantics. `propstore/praf/engine.py` implements *probabilistic* weights (existence probabilities), not the inconsistency-budget semantics.
- Match: **missing**.
- Notes: `Dunne` appears zero times in `propstore/`. WAS weights live on attacks; PrAF existence probabilities are semantically distinct (constellation vs. inconsistency-budget). Priority paper; paper notes.md at `papers/Dunne_2011_WeightedArgumentSystemsBasic/notes.md` exists (full).

### Amgoud_2013_Ranking-BasedSemanticsArgumentationFrameworks
- Paper's core claim: Axiomatic ranking-based semantics; 8 postulates; Discussion-based (Dbs) and Burden-based (Bbs) semantics.
- Code implementation: None. No `Dbs`, `Bbs`, `ranking`, `Amgoud_2013` references in `propstore/`.
- Match: **missing**.
- Notes: `praf/dfquad.py` implements one gradual family (DF-QuAD) but this is not axiomatic ranking per Amgoud 2013. CLAUDE.md cites "Amgoud & Vesic 2014" as deferred rich-PAF attack inversion but does not mention the 2013 ranking paper.

### Bonzon_2016_ComparativeStudyRanking-basedSemantics
- Paper's core claim: Comparison of five ranking-based semantics (Categoriser/Dbs/Bbs/Matt & Toni/Tuples*) against 16 properties.
- Code implementation: None.
- Match: **missing**.
- Notes: Complementary to Amgoud 2013; same verdict.

### Baroni_2019_GradualArgumentationPrinciples
- Paper's core claim: 11 principle groups for gradual argumentation over QBAFs; h-categorizer/Euler/DF-QuAD/QuAD classification.
- Code implementation: `propstore/praf/dfquad.py` (full DF-QuAD family per Freedman 2025 / Rago 2016).
- Match: **partial**.
- Notes: Only DF-QuAD is implemented from the family. h-categorizer, Euler, and QuAD (pre-DF) are not present. Paper notes.md is `full`. Principles (balance/monotonicity/etc.) are not checked in code; no principle tests exist.

### Amgoud_2011_NewApproachPreference-basedArgumentation / Amgoud_2014_RichPreference-basedArgumentationFrameworks
- Paper's core claim: Preferences at the semantics level (Amgoud 2011); rich PAFs invert defeated attacks (Amgoud 2014).
- Code implementation: The ASPIC+ core (`aspic.py:1221-1280`) follows the Modgil & Prakken 2018 Def 9 path: preferences filter attacks into defeats without inverting. No attack inversion.
- Match: **partial / missing**.
- Notes: CLAUDE.md explicitly declares "rich PAF attack inversion (Amgoud & Vesic 2014) are deferred" under Known Limitations. This is a Known Limitation, not drift.

### Bench-Capon_2003_PersuasionPracticalArgumentValue-based
- Paper's core claim: Value-based AFs (VAFs): each argument carries a value, audiences rank values, attacks succeed iff the attacker's value is not strictly less than the target's value in that audience.
- Code implementation: None. Grepping `VAF|value.based|audience|Bench.Capon` — no hits. `preference.py` is generic set-comparison, not value-based.
- Match: **missing**.
- Notes: Paper is stub in `papers/Bench-Capon_2003_PersuasionPracticalArgumentValue-based/` (metadata.json only; stub-noted per manifest). The Wallner_2024_ValueBasedReasoningInASPIC paper at `papers/Wallner_2024_ValueBasedReasoningInASPIC/` is also a cluster-3a priority — likewise not cited or implemented. Absence is real, not a stub-reading artifact.

### Popescu_2024 (three variants in manifest)
- Paper's core claim: Algorithmic advances for constellation-approach PrAFs: tree-decomposition-based DP for exact computation of extension probabilities and argument acceptance, with O(2^tw) theoretical bound on acyclic treewidth.
- Code implementation: `propstore/praf/treedecomp.py:1-41` (supports_exact_dp gate), `:50-90` (TreeDecomposition/NiceTDNode), `:315-600` (nice TD DP with I/O/U labelling), and used from `praf/engine.py:843-875` (auto-dispatch via treewidth estimate cutoff).
- Match: **partial / drift** (see Finding 1).
- Notes: The three Popescu_2024 directories are (a) `ProbabilisticArgumentationConstellation` [full notes], (b) `AlgorithmicProbabilisticArgumentationConstellation` [full notes], (c) `AdvancingAlgorithmicApproachesProbabilistic` [stub]. The "constellation" approach is confirmed by `papers/Popescu_2024_ProbabilisticArgumentationConstellation/notes.md:14-27` — this is the approach the code implements. The epistemic approach (Hunter 2017) is cited for COH rationality postulate enforcement at `praf/engine.py:261` but not used as the sampling semantics.

## Findings (drift, not missing)

### Finding 1 — PrAF tree-decomposition DP does not achieve the complexity bound it is advertised as implementing
- Severity: **medium**
- Paper source: `papers/Popescu_2024_ProbabilisticArgumentationConstellation/notes.md` lines 11-22 (tree-decomposition DP tractable for low treewidth) plus `papers/Popescu_2024_ProbabilisticArgumentationConstellation/notes.md` reference to Theorem 7.
- Code: `propstore/praf/treedecomp.py:13-17` (module docstring), `propstore/praf/engine.py:843-875` (auto-dispatch cites "Popescu & Wallner 2024").
- Drift: The module docstring at `treedecomp.py:13-17` self-declares: "The tree decomposition DP currently tracks full edge sets and forgotten arguments in table keys, giving row count O(2^|defeats| * 2^|args|). This provides zero asymptotic improvement over brute-force enumeration. Effective for AFs with treewidth <= ~15." This is honest inside the file, but the parent dispatcher at `engine.py:843-875` chooses this backend based on treewidth cutoff under the assumption the DP is more efficient than MC/enumeration for treewidth < 12. Users reading CLAUDE.md's "Technical Conventions" and seeing Popescu & Wallner 2024 cited have no signal that the implementation does not deliver the paper's asymptotic bound. The auto-path is load-bearing for correctness but not load-bearing for the paper's performance claim.
- Recommendation: Either (a) surface this Known Limitation in CLAUDE.md's "Known Limitations" section with explicit language ("treedecomp DP implemented but not yet achieving O(2^tw)"), or (b) remove the auto-dispatch path and keep exact_dp only as an opt-in strategy until the redesign lands. The in-file warning is easy to miss.

## Findings (missing — breadth gaps, not drift)

The following are all MISSING capabilities. None of them is advertised in CLAUDE.md as implemented. They are listed here so Q can see the exact gap between the priority-paper list and the code.

1. Semi-stable extensions (Caminada 2006) — no Caminada labelling API; no minimal-undec computation.
2. Ideal semantics (Dung 2007) — no ideal-extension function; no dispute-tree procedures.
3. Stage semantics — not implemented.
4. CF2 / stage2 (Baroni 2005, Gaggl 2012/2013) — not implemented.
5. Oikarinen 2010 kernel-based strong equivalence — not implemented (relevant to `repo/merge_framework.py`, which has its own semantic-merge classification but does not use kernels).
6. Weighted Argument Systems / inconsistency budget (Dunne 2011) — not implemented.
7. Ranking-based semantics (Amgoud 2013, Bonzon 2016, Matt & Toni 2008) — Dbs/Bbs/h-Categorizer/Matt-Toni not implemented.
8. Value-based AFs (Bench-Capon 2003) and Wallner 2024 value-based ASPIC — no VAF module; `preference.py` is dimension-generic, not value-indexed by audience.
9. Abstract Dialectical Frameworks (Brewka 2010/2013) — no ADF module.

For each of these, CLAUDE.md is silent. This is consistent with scoping a theoretical-foundations repo, but a scout reading the priority-paper list cannot distinguish "deferred on purpose" from "overlooked" without asking Q.

### Finding 2 — `preference.py` presents a heuristic under an ASPIC+ docstring
- Severity: **low** (file self-documents the split honestly)
- Paper source: Modgil & Prakken 2018 Def 19 (elitist/democratic set comparison) and Defs 20-21 (last-link / weakest-link) — the paper's preference ordering is derived from base orderings over *rules and premises*, not from a 3-component metadata vector.
- Code: `propstore/preference.py:27-64` (literature-faithful set comparison) plus `:67-108` (metadata_strength_vector heuristic with `[log_sample_size, inverse_uncertainty, confidence]`, and the exported alias `claim_strength`).
- Drift: The file's module docstring (`preference.py:1-17`) is up-front about the split ("This module contains two distinct layers... literature-backed set-comparison helpers... and a metadata-derived heuristic... The metadata heuristic is not a full ASPIC+ Def. 19 / Defs. 20-21 structured-argument ordering"). But the exported `claim_strength` alias at `:101-108` is used from `aspic_bridge/translate.py:20,265` to populate the ASPIC+ `premise_order` via Pareto dominance on the 3-vector (`translate.py:214-220` `_component_wise_dominates`). Callers of the bridge therefore get a preference ordering that is *not* what Modgil & Prakken 2018 Def 22 calls a "strict partial order derived from a base ordering on premises" — it is a Pareto partial order over a heuristic vector. The aspirational framing as ASPIC+-compliant is soft but it is there.
- Recommendation: Either (a) rename `claim_strength` to `metadata_strength_heuristic` everywhere (the alias is labeled "Backward-compatible" at `preference.py:101-108` but the user-facing bridge still uses the alias) and update `translate.py:20` accordingly; (b) add a Known Limitation entry to CLAUDE.md: "The ASPIC+ premise_order built by aspic_bridge is heuristic-derived from claim metadata, not elicited."

### Finding 3 — Rule ordering is always empty (CLAUDE.md claim verified, noted here for completeness)
- Severity: **none** — this is declared in CLAUDE.md.
- Paper source: Modgil & Prakken 2018 Def 22 (p.22): `rule_order` is a strict partial order over defeasible rules.
- Code: `propstore/aspic_bridge/translate.py:242-280` — `build_preference_config(defeasible_rules, ...)` takes `defeasible_rules` then `del defeasible_rules` at line 252 and returns `PreferenceConfig(rule_order=frozenset(), ...)` at line 276.
- Drift: None. CLAUDE.md explicitly declares: "Rule ordering in the bridge is always empty — only premise ordering from metadata has discriminating power." Verified.
- Recommendation: None.

## Secondary papers — cite-check table

One-line verdicts across the ~50 remaining cluster-3a papers plus known cross-cluster hits. "cite" = cited in code. "lit" = present in lit pipeline / bridge but not cited here. "absent" = no reference anywhere. "stub-noted" = paper notes.md is stub and cite-check rests on manifest summary.

| Paper | Status | Evidence |
| --- | --- | --- |
| Caminada_2007_EvaluationArgumentationFormalisms (rationality postulates) | absent | no cite in `propstore/`; rationality postulates not tested |
| Modgil_2014_ASPICFrameworkStructuredArgumentation (tutorial) | lit | ASPIC+ defs all sourced from Modgil & Prakken 2018 |
| Dauphin_2018_ASPICENDStructuredArgumentationExplanationsNaturalDeduction | absent | no cite; hypothetical-reasoning extension not implemented |
| Amgoud_2017_AcceptabilitySemanticsWeightedArgumentation | absent | no cite |
| Amgoud_2011_NewApproachPreference-basedArgumentation | absent | no cite; ASPIC+ uses Def 9 filtering, not Amgoud 2011 |
| Amgoud_2002_ReasoningModelProductionAcceptable | absent | no cite |
| Modgil_2009_ReasoningAboutPreferencesArgumentation (EAFs) | absent | no cite |
| Modgil_2011_RevisitingPreferencesArgumentation | absent | no cite (superseded by M&P 2018 in code) |
| Wallner_2024_ValueBasedReasoningInASPIC | absent | no cite; VAF not implemented |
| Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation | absent | no SCC schema |
| Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation | absent | no principle-based tests |
| Gaggl_2012 / Gaggl_2013 CF2 | absent | CF2 not implemented |
| Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation | absent | `repo/merge_framework.py` has its own classification; no kernel |
| Coste-Marquis_2005_SymmetricArgumentationFrameworks | absent | no symmetric-AF fast paths |
| Verheij_2002_ExistenceMultiplicityExtensionsDialectical | absent | no cite |
| Fan_2015_ComputingExplanationsArgumentation | absent | no related-admissibility |
| Charwat_2015_MethodsSolvingReasoningProblems | absent | stub-noted paper |
| Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation | lit | stub-noted; only Popescu 2024 actively cited for treewidth |
| Fichte_2021_Decomposition-GuidedReductionsArgumentationTreewidth | absent | no cite in `praf/treedecomp.py` (only Popescu 2024) |
| Matt_2008_Game-TheoreticMeasureArgumentStrength | absent | no LP/game-theoretic strength |
| Leite_2011_SocialAbstractArgumentation | absent | no social AF voting |
| Brewka_2010 / Brewka_2013 Abstract Dialectical Frameworks | absent | no ADF module |
| Rago_2016_DiscontinuityFreeQuAD | cite | `praf/dfquad.py` and `praf/engine.py:1392` Rago 2016 |
| Rago_2016_AdaptingDFQuADBipolarArgumentation | lit | DF-QuAD BAF mode at `engine.py:1422-1428` |
| Gabbay_2012_EquationalApproachArgumentationNetworks | absent | no equational semantics |
| Potyka_2018_ContinuousDynamicalSystemsWeighted | absent | no continuous dynamics |
| AlAnaissy_2024_ImpactMeasuresGradualArgumentation | absent | no impact measures |
| Čyras_2021_ArgumentativeXAISurvey | absent | no XAI explanation module |
| Besnard_2001_Logic-basedTheoryDeductiveArguments | cite | `aspic.py:813-817` cites Besnard & Hunter 2001 Def 6.1 for `build_arguments_for` |
| Prakken_2010_AbstractFrameworkArgumentationStructured | cite | `aspic.py:146,373,389-394` cites Prakken 2010 Def 3.4, Def 5.1 |
| Prakken_2012_ClarifyingSomeMisconceptionsASPICplusFramework | absent | no cite |
| Prakken_2012_AppreciationJohnPollock'sWork | cite-adjacent | `aspic.py:985,989,1232` cites Pollock 1987 Defs 2.4, 2.5 directly |
| Prakken_2019_ModellingAccrualArgumentsASPIC | absent | no accrual |
| Prakken_2013_FormalisationArgumentationSchemesLegalCaseBasedReasoningASPICPlus | absent | no schemes module |
| Wei_2012_DefiningStructureArgumentsAIModelsArgumentation | absent | no taxonomy |
| Walton_2015_ClassificationSystemArgumentationSchemes | absent | no schemes |
| Simari_1992_MathematicalTreatmentDefeasibleReasoning | absent | no cite |
| Thimm_2020_ApproximateReasoningASPICArgumentSampling | absent | no sampling-based ASPIC+ approximation |
| Lehtonen_2020_AnswerSetProgrammingApproach | absent | no ASP encoding |
| Lehtonen_2024_PreferentialASPIC | absent | no cite |
| Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning | absent | no cite |
| Li_2017_TwoFormsMinimalityASPIC | absent | no cite |
| Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible | absent | no cite |
| Diller_2025_GroundingRule-BasedArgumentationDatalog | cite | `aspic.py:36` cites Diller et al. 2025 Def 7 for `GroundAtom` |
| Odekerken_2023 / Odekerken_2025 / Odekerken_2022 (incomplete ASPIC+) | absent | no cite |
| Alfano_2017_EfficientComputationExtensionsDynamic | absent | no incremental recomputation |
| Boella_2009_DynamicsArgumentationSingleExtensions | absent | no cite |
| Baumann_2010_ExpandingArgumentationFrameworksEnforcing | absent | no enforcement |
| Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault (ABA) | cite-adjacent | `aspic.py:814` cites Toni 2014 ABA for backward chaining; no full ABA |
| Toni_2014_TutorialAssumption-basedArgumentation | cite | `aspic.py:814` — used as backward-chaining inspiration |
| Vreeswijk_1997_AbstractArgumentationSystems | absent | no cite |
| Stab_2016 / Mayer_2020 / Freedman_2025 (argument mining / LLM) | cite (Freedman) | Freedman 2025 cited at `praf/dfquad.py:1-10`, `engine.py:1385-1395` |
| Tang_2025_EncodingArgumentationFrameworksPropositional | absent | no fuzzy semantics |
| Niskanen_2020_ToksiaEfficientAbstractArgumentation | absent | `dung_z3.py` is Z3-SAT but does not cite µ-toksia |
| Mahmood_2025_Structure-AwareEncodingsArgumentationProperties | absent | no cite |
| Rahwan_2009_ArgumentationArtificialIntelligence | absent | reference book |
| Dunne_2009_ComplexityAbstractArgumentation | absent | no explicit complexity annotations |
| Verheij_2003_ArtificialArgumentAssistants | absent | no cite |
| Hunter_2017_ProbabilisticReasoningAbstractArgumentation | cite | `praf/engine.py:261-267,709` Hunter & Thimm 2017 COH postulate + Prop 18 |
| Hunter_2021_ProbabilisticArgumentationSurvey | lit | constellation vs. epistemic distinction implicit in choice of sampling semantics |
| Li_et_al_2012 (MC for PrAFs) | cite | `praf/engine.py:708-709,943,994,1215` Li 2012 Alg 1, Eq 5 |

## Aspirational citations (no corresponding module)

Dialogue-games (manifest scout already flagged): `Prakken_2006_FormalSystemsPersuasionDialogue`, `McBurney_2009_DialogueGamesAgentArgumentation`, `Karacapilidis_2001_ComputerSupportedArgumentationCollaborative`. Present in cluster-3a paper set, no module in `propstore/`. Not drift — propstore explicitly does not include a dialogue layer.

None of the cite-check entries above appears to be an *aspirational* citation (i.e., paper cited in code but not implemented). The citations that exist in code (Besnard 2001, Diller 2025, Prakken 2010, Pollock 1987, Toni 2014, Freedman 2025, Rago 2016, Hunter 2017, Li 2012, Popescu 2024, Modgil & Prakken 2018) all correspond to actual computations in the cited files.

## Open questions

1. **Is semi-stable / ideal / stage / CF2 deliberately deferred or overlooked?** CLAUDE.md's "Known Limitations" section mentions only rule-ordering-empty, interval dominance, semantic-merge-scope, and extended-Jøsang operators. The six unimplemented abstract-argumentation semantics on the priority list are silent absences. Q: are these planned, or explicitly out-of-scope?
2. **Value-based reasoning pathway.** Bench-Capon 2003 and Wallner 2024 are both cluster-3a priority. Neither is implemented. The generic `preference.py` metadata ordering is argued for over value-audience orderings. Q: is VAF deliberately replaced by metadata-driven preference, or is this a gap?
3. **Rich PAF vs Modgil 2018 Def 9 semantics choice.** CLAUDE.md defers "rich PAF attack inversion (Amgoud & Vesic 2014)". The code uses the attack-filtering path instead. Q: is this a permanent design choice (attack inversion changes postulate coverage) or a temporary decision?
4. **Popescu & Wallner 2024 DP redesign.** Is there a target timeline for the O(2^tw) redesign? If not, the auto-dispatch in `praf/engine.py:843-875` at least warrants a comment that current treedecomp DP is not faster than exact enumeration in the worst case.
5. **`claim_strength` heuristic vs. `metadata_strength_vector`.** The backward-compat alias still flows through the ASPIC+ bridge. Is backward compatibility required, or should the heuristic be renamed everywhere to prevent misreading it as Modgil & Prakken 2018 Def 22?
