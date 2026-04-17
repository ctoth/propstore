# Paper Manifest — 2026-04-16 Code Review

Total papers: 210
Per-cluster counts: 3a=69, 3b=26, 3c=19, 3d=27, 3e=30, 7=14, Motivation=17, Unclassified=8

Notes legend: `full` = notes.md present with substantive content; `index` = entry in `papers/index.md` only (used as content source); `stub` = dir present but notes.md missing (only metadata.json / paper.pdf); `pdf-only` = only PDF on disk.

## Cluster 3a — Argumentation core

### Dung_1995_AcceptabilityArguments
- Path: `./papers/Dung_1995_AcceptabilityArguments/`
- Content: Defines abstract argumentation frameworks (arguments + attack relation) with admissible/preferred/stable/grounded/complete extensions, unifying Reiter default logic, Pollock defeasible reasoning, and logic programming NAF as special cases.
- Likely modules: `propstore/dung.py`, `propstore/dung_z3.py`
- Notes: index

### Caminada_2006_IssueReinstatementArgumentation
- Path: `./papers/Caminada_2006_IssueReinstatementArgumentation/`
- Content: Formal three-valued (in/out/undec) labelling correspondence with Dung semantics; introduces semi-stable semantics filling the gap between preferred and stable.
- Likely modules: `propstore/dung.py` (labellings)
- Notes: index

### Caminada_2007_EvaluationArgumentationFormalisms
- Path: `./papers/Caminada_2007_EvaluationArgumentationFormalisms/`
- Content: Three rationality postulates (closure, direct consistency, indirect consistency) for structured argumentation, adopted by ASPIC+.
- Likely modules: `propstore/aspic.py`, `propstore/aspic_bridge/`
- Notes: index
- Secondary: 7 Defeasible

### Modgil_2014_ASPICFrameworkStructuredArgumentation
- Path: `./papers/Modgil_2014_ASPICFrameworkStructuredArgumentation/`
- Content: Tutorial intro to ASPIC+: strict/defeasible rules, undermining/rebutting/undercutting attacks, Dung AF generation with preference-based defeat.
- Likely modules: `propstore/aspic_bridge/`, `propstore/aspic.py`
- Notes: index

### Modgil_2018_GeneralAccountArgumentationPreferences
- Path: `./papers/Modgil_2018_GeneralAccountArgumentationPreferences/`
- Content: Full ASPIC+ with preferences; attack-based conflict-free; weakest-link/last-link orderings; proofs of all four rationality postulates.
- Likely modules: `propstore/aspic_bridge/`, `propstore/preference.py`
- Notes: index

### Dauphin_2018_ASPICENDStructuredArgumentationExplanationsNaturalDeduction
- Path: `./papers/Dauphin_2018_ASPICENDStructuredArgumentationExplanationsNaturalDeduction/`
- Content: Extends ASPIC+ with hypothetical reasoning, proof by contradiction, and explanation relations (ASPIC-END); proves closure/consistency properties for EAF semantics.
- Likely modules: `propstore/aspic.py`
- Notes: index

### Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation
- Path: `./papers/Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation/`
- Content: Extends Dung AFs with independent support relation (BAFs); defines d/s/c-admissibility and supported/indirect defeat.
- Likely modules: `propstore/bipolar.py`
- Notes: index

### Amgoud_2008_BipolarityArgumentationFrameworks
- Path: `./papers/Amgoud_2008_BipolarityArgumentationFrameworks/`
- Content: Survey of bipolarity in argumentation: BAF = (A, R_def, R_sup); gradual valuation and supported-defeat semantics.
- Likely modules: `propstore/bipolar.py`
- Notes: index

### Dunne_2011_WeightedArgumentSystemsBasic
- Path: `./papers/Dunne_2011_WeightedArgumentSystemsBasic/`
- Content: Attaches positive weights to attacks; inconsistency budget reasoning under weighted grounded/admissible/preferred semantics with complexity results.
- Likely modules: `propstore/praf/` (weighted), `propstore/dung.py`
- Notes: index

### Amgoud_2013_Ranking-BasedSemanticsArgumentationFrameworks
- Path: `./papers/Amgoud_2013_Ranking-BasedSemanticsArgumentationFrameworks/`
- Content: Axiomatic ranking-based semantics: eight postulates plus Discussion-based (Dbs) and Burden-based (Bbs) semantics.
- Likely modules: `propstore/praf/`, `propstore/preference.py`
- Notes: index

### Amgoud_2017_AcceptabilitySemanticsWeightedArgumentation
- Path: `./papers/Amgoud_2017_AcceptabilitySemanticsWeightedArgumentation/`
- Content: 15-principle axiomatic foundation for weighted AGs; three novel semantics (Mbs, Cbs, h-Categorizer Hbs); formal comparison of 10 semantics.
- Likely modules: `propstore/praf/`
- Notes: index

### Bonzon_2016_ComparativeStudyRanking-basedSemantics
- Path: `./papers/Bonzon_2016_ComparativeStudyRanking-basedSemantics/`
- Content: Axiomatic comparison of five ranking-based semantics (Categoriser, Dbs, Bbs, Matt & Toni, Tuples*) against 16 properties.
- Likely modules: `propstore/praf/`
- Notes: index

### Bench-Capon_2003_PersuasionPracticalArgumentValue-based
- Path: `./papers/Bench-Capon_2003_PersuasionPracticalArgumentValue-based/`
- Content: (From metadata) Value-based argumentation frameworks (VAFs) for practical/persuasive argument, adding audience-specific value orderings to Dung AFs.
- Likely modules: `propstore/preference.py`, `propstore/dung.py`
- Notes: stub (metadata.json only)

### Amgoud_2011_NewApproachPreference-basedArgumentation
- Path: `./papers/Amgoud_2011_NewApproachPreference-basedArgumentation/`
- Content: Handles preferences at the semantics level via dominance relations on the argument powerset; bijects pref-stable extensions with Brewka preferred sub-theories.
- Likely modules: `propstore/preference.py`, `propstore/aspic_bridge/`
- Notes: index

### Amgoud_2014_RichPreference-basedArgumentationFrameworks
- Path: `./papers/Amgoud_2014_RichPreference-basedArgumentationFrameworks/`
- Content: Rich PAFs invert defeated attacks rather than removing them; stable extensions biject with preferred sub-theories of stratified KBs.
- Likely modules: `propstore/preference.py`, `propstore/conflict_detector/`
- Notes: index
- Secondary: 3c Revision

### Amgoud_2002_ReasoningModelProductionAcceptable
- Path: `./papers/Amgoud_2002_ReasoningModelProductionAcceptable/`
- Content: Original preference-based Dung extension; least-fixpoint semantics plus AND/OR dialogue-tree proof theory.
- Likely modules: `propstore/preference.py`
- Notes: index

### Modgil_2009_ReasoningAboutPreferencesArgumentation
- Path: `./papers/Modgil_2009_ReasoningAboutPreferencesArgumentation/`
- Content: Extended argumentation frameworks (EAFs) with argument-to-attack relation for defeasible meta-preferences; subsumes value-based and logic-programming approaches.
- Likely modules: `propstore/preference.py`
- Notes: index

### Modgil_2011_RevisitingPreferencesArgumentation
- Path: `./papers/Modgil_2011_RevisitingPreferencesArgumentation/`
- Content: Revises ASPIC+ so conflict-freeness is over attacks while preferences determine defeat; proves rationality postulates.
- Likely modules: `propstore/aspic_bridge/`, `propstore/preference.py`
- Notes: index

### Wallner_2024_ValueBasedReasoningInASPIC
- Path: `./papers/Wallner_2024_ValueBasedReasoningInASPIC/`
- Content: Per-agent subjective KB + defeasible rules shaped by value profile; grounded-extension intersection for collective answer.
- Likely modules: `propstore/aspic_bridge/`, `propstore/preference.py`
- Notes: index

### Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation
- Path: `./papers/Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation/`
- Content: SCC-recursive schema for argumentation semantics; introduces CF2 handling odd-length cycles.
- Likely modules: `propstore/dung.py`
- Notes: index

### Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation
- Path: `./papers/Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation/`
- Content: Principle-based evaluation of 8 semantics (grounded/complete/preferred/stable/semi-stable/ideal/CF2/prudent) against conflict-freeness, reinstatement, directionality, skepticism.
- Likely modules: `propstore/dung.py`
- Notes: index

### Baroni_2019_GradualArgumentationPrinciples
- Path: `./papers/Baroni_2019_GradualArgumentationPrinciples/`
- Content: 11 Groups of Principles for gradual argumentation over QBAFs, subsumed by balance and monotonicity meta-principles; classifies h-categorizer/Euler/DF-QuAD/QuAD families.
- Likely modules: `propstore/praf/`, `propstore/bipolar.py`
- Notes: full
- Secondary: 3b Uncertainty

### Gaggl_2012_CF2ArgumentationSemanticsRevisited
- Path: `./papers/Gaggl_2012_CF2ArgumentationSemanticsRevisited/`
- Content: (No notes.md, pngs only) Earlier CF2 revisitation — fixed-point characterization over component-defeated arguments, complexity and succinctness results.
- Likely modules: `propstore/dung.py`
- Notes: pdf-only (pngs); see 2013 version in index

### Gaggl_2013_CF2ArgumentationSemanticsRevisited
- Path: `./papers/Gaggl_2013_CF2ArgumentationSemanticsRevisited/`
- Content: Recasts CF2 from recursive SCC decomposition to fixed-point characterization; proves CF2 is uniquely maximal succinct and strong equivalence collapses to syntactic.
- Likely modules: `propstore/dung.py`
- Notes: index

### Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation
- Path: `./papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/`
- Content: Kernel operators characterizing strong equivalence for Dung AFs across all major semantics (a-kernel for stable/preferred; a*-kernel for admissible/complete).
- Likely modules: `propstore/dung.py`, `propstore/repo/` (merge classification)
- Notes: index

### Coste-Marquis_2005_SymmetricArgumentationFrameworks
- Path: `./papers/Coste-Marquis_2005_SymmetricArgumentationFrameworks/`
- Content: Symmetric attack AFs: preferred/stable/naive coincide; grounded = unattacked args (linear time); coNP/NP-completeness for set-acceptability.
- Likely modules: `propstore/dung.py`
- Notes: index

### Verheij_2002_ExistenceMultiplicityExtensionsDialectical
- Path: `./papers/Verheij_2002_ExistenceMultiplicityExtensionsDialectical/`
- Content: Dialectical justification in DEFLOG; determines existence and count of stable extensions; translates to Dung AFs, default logic, LP.
- Likely modules: `propstore/dung.py`
- Notes: index

### Dung_2007_ComputingIdealScepticalArgumentation
- Path: `./papers/Dung_2007_ComputingIdealScepticalArgumentation/`
- Content: Ideal dispute trees and AB/IB/Fail-dispute derivations for ideal sceptical semantics in AA and ABA; sound generally, complete for p-acyclic finite ABA.
- Likely modules: `propstore/dung.py`, `propstore/aspic.py`
- Notes: index
- Secondary: 7 Defeasible

### Fan_2015_ComputingExplanationsArgumentation
- Path: `./papers/Fan_2015_ComputingExplanationsArgumentation/`
- Content: "Related admissibility" semantics filtering irrelevant admissible arguments; minimal/compact/maximal explanation types via dispute forests for AA and ABA.
- Likely modules: `propstore/dung.py`, `propstore/aspic.py`
- Notes: index

### Charwat_2015_MethodsSolvingReasoningProblems
- Path: `./papers/Charwat_2015_MethodsSolvingReasoningProblems/`
- Content: (No notes.md) Survey of methods (ASP, SAT, DB-style, dedicated procedures) for solving abstract argumentation reasoning problems. [Inferred from title + tag in cluster definition.]
- Likely modules: `propstore/dung.py`, `propstore/dung_z3.py`
- Notes: stub (claims.yaml, abstract.md, description.md present; no notes.md)

### Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation
- Path: `./papers/Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation/`
- Content: (No notes.md; paper.pdf + pngs) FPT algorithms for abstract argumentation parameterized by treewidth.
- Likely modules: `propstore/praf/treedecomp/` (if present), `propstore/dung.py`
- Notes: pdf-only

### Fichte_2021_Decomposition-GuidedReductionsArgumentationTreewidth
- Path: `./papers/Fichte_2021_Decomposition-GuidedReductionsArgumentationTreewidth/`
- Content: Decomposition-guided reductions for argumentation leveraging treewidth; enables FPT algorithms for complexity-theoretically hard argumentation problems.
- Likely modules: `propstore/praf/` (treedecomp DP)
- Notes: full

### Matt_2008_Game-TheoreticMeasureArgumentStrength
- Path: `./papers/Matt_2008_Game-TheoreticMeasureArgumentStrength/`
- Content: Game-theoretic argument strength via two-person zero-sum game (proponent admissible sets vs opponent attacking sets); LP-computable value in [0,1].
- Likely modules: `propstore/praf/`
- Notes: index
- Secondary: 3b Uncertainty

### Leite_2011_SocialAbstractArgumentation
- Path: `./papers/Leite_2011_SocialAbstractArgumentation/`
- Content: Social Abstract Argumentation Frameworks adding per-argument pos/neg votes; algebraic semantics over Dung AFs.
- Likely modules: `propstore/praf/`
- Notes: index

### Brewka_2010_AbstractDialecticalFrameworks
- Path: `./papers/Brewka_2010_AbstractDialecticalFrameworks/`
- Content: Abstract Dialectical Frameworks (ADFs) generalizing Dung with per-node propositional acceptance conditions; BADFs for stable/preferred.
- Likely modules: `propstore/dung.py`, `propstore/bipolar.py`
- Notes: index

### Brewka_2013_AbstractDialecticalFrameworksRevisited
- Path: `./papers/Brewka_2013_AbstractDialecticalFrameworksRevisited/`
- Content: Preferred/stable ADF semantics over three-valued interpretations for arbitrary ADFs; static + dynamic preferences; DIAMOND ASP implementation.
- Likely modules: `propstore/dung.py`
- Notes: index

### Rago_2016_DiscontinuityFreeQuAD
- Path: `./papers/Rago_2016_DiscontinuityFreeQuAD/`
- Content: QuAD frameworks and DF-QuAD discontinuity-free strength aggregation for bipolar argumentation with base scores; fixes QuAD discontinuities.
- Likely modules: `propstore/bipolar.py`, `propstore/praf/` (df-quad)
- Notes: index

### Rago_2016_AdaptingDFQuADBipolarArgumentation
- Path: `./papers/Rago_2016_AdaptingDFQuADBipolarArgumentation/`
- Content: Adapts DF-QuAD to BAFs without base scores (default 0.5); continuity proven; equivalence with QuAD at base=0.5.
- Likely modules: `propstore/bipolar.py`
- Notes: index

### Gabbay_2012_EquationalApproachArgumentationNetworks
- Path: `./papers/Gabbay_2012_EquationalApproachArgumentationNetworks/`
- Content: Equational semantics: argument values in [0,1] via four equation families (Eq_inverse/max/geometrical/suspect); Eq_max = Caminada complete labellings.
- Likely modules: `propstore/praf/`, `propstore/dung.py`
- Notes: index

### Potyka_2018_ContinuousDynamicalSystemsWeighted
- Path: `./papers/Potyka_2018_ContinuousDynamicalSystemsWeighted/`
- Content: Quadratic energy continuous dynamical systems approach to weighted bipolar argumentation; convergence for acyclic graphs; outperforms DF-QuAD/Euler on cyclic.
- Likely modules: `propstore/praf/`, `propstore/bipolar.py`
- Notes: index

### AlAnaissy_2024_ImpactMeasuresGradualArgumentation
- Path: `./papers/AlAnaissy_2024_ImpactMeasuresGradualArgumentation/`
- Content: Revised removal-based impact (ImpS^rev) and Shapley-value impact (ImpSh) for QBAFs with nine desirable principles.
- Likely modules: `propstore/praf/`
- Notes: index

### Čyras_2021_ArgumentativeXAISurvey
- Path: `./papers/Čyras_2021_ArgumentativeXAISurvey/`
- Content: Survey of argumentation-based XAI cataloguing explanation types, frameworks (AA/BA/QBA/ABA/ASPIC+/DeLP) and forms.
- Likely modules: `propstore/aspic.py`, `propstore/dung.py`
- Notes: index

### Besnard_2001_Logic-basedTheoryDeductiveArguments
- Path: `./papers/Besnard_2001_Logic-basedTheoryDeductiveArguments/`
- Content: Logic-based argumentation: arguments as minimal consistent subsets of a KB; canonical undercuts; argument trees and structures.
- Likely modules: `propstore/aspic.py`
- Notes: index

### Prakken_2010_AbstractFrameworkArgumentationStructured
- Path: `./papers/Prakken_2010_AbstractFrameworkArgumentationStructured/`
- Content: Original ASPIC framework: strict/defeasible rules instantiating Dung AFs; rationality postulates under conditions.
- Likely modules: `propstore/aspic_bridge/`, `propstore/aspic.py`
- Notes: full

### Prakken_2012_ClarifyingSomeMisconceptionsASPICplusFramework
- Path: `./papers/Prakken_2012_ClarifyingSomeMisconceptionsASPICplusFramework/`
- Content: (No notes.md) Clarifies common misconceptions about ASPIC+ (strict vs defeasible, restricted vs unrestricted rebuttal, etc.).
- Likely modules: `propstore/aspic_bridge/`
- Notes: pdf-only (pngs)

### Prakken_2012_AppreciationJohnPollock'sWork
- Path: `./papers/Prakken_2012_AppreciationJohnPollock'sWork/`
- Content: Appreciation and critical survey of Pollock's defeasible reasoning (inference graphs, undercutting/rebutting, argument strength, self-defeat).
- Likely modules: `propstore/aspic.py`
- Notes: index

### Prakken_2019_ModellingAccrualArgumentsASPIC
- Path: `./papers/Prakken_2019_ModellingAccrualArgumentsASPIC/`
- Content: Inference-based accrual in ASPIC+: accrual as property of argument sets; defeat via labelling-relative set preferences.
- Likely modules: `propstore/aspic_bridge/`
- Notes: index

### Prakken_2013_FormalisationArgumentationSchemesLegalCaseBasedReasoningASPICPlus
- Path: `./papers/Prakken_2013_FormalisationArgumentationSchemesLegalCaseBasedReasoningASPICPlus/`
- Content: CATO-style legal case-based reasoning reconstructed as ASPIC+ schemes over factors/precedential comparisons.
- Likely modules: `propstore/aspic_bridge/`
- Notes: index

### Prakken_2006_FormalSystemsPersuasionDialogue
- Path: `./papers/Prakken_2006_FormalSystemsPersuasionDialogue/`
- Content: Formal specification framework for persuasion dialogue systems; comparison of nine systems by speech acts, commitment rules, turntaking.
- Likely modules: (no obvious module — dialogue layer not in `propstore/`)
- Notes: index

### Wei_2012_DefiningStructureArgumentsAIModelsArgumentation
- Path: `./papers/Wei_2012_DefiningStructureArgumentsAIModelsArgumentation/`
- Content: ASPIC+ formalization of informal-logic taxonomy of argument structures (serial/convergent/divergent/linked); unit I vs II arguments.
- Likely modules: `propstore/aspic.py`
- Notes: index

### Walton_2015_ClassificationSystemArgumentationSchemes
- Path: `./papers/Walton_2015_ClassificationSystemArgumentationSchemes/`
- Content: Hierarchical classification of argumentation schemes by source-dependency/epistemic-vs-practical/rule-vs-case; ~28 schemes validated on 388 political arguments.
- Likely modules: `propstore/aspic.py`, `propstore/claims.py`
- Notes: index

### Simari_1992_MathematicalTreatmentDefeasibleReasoning
- Path: `./papers/Simari_1992_MathematicalTreatmentDefeasibleReasoning/`
- Content: Defeasible argumentation combining Poole specificity with Pollock warrant; dialectical justification converging to unique stable set.
- Likely modules: `propstore/aspic.py`
- Notes: index

### Thimm_2020_ApproximateReasoningASPICArgumentSampling
- Path: `./papers/Thimm_2020_ApproximateReasoningASPICArgumentSampling/`
- Content: randI and randD sampling-based approximation algorithms for ASPIC+ reasoning; 99%+ accuracy on random/mined/MaxSAT benchmarks.
- Likely modules: `propstore/aspic_bridge/`, `propstore/aspic.py`
- Notes: index

### Lehtonen_2020_AnswerSetProgrammingApproach
- Path: `./papers/Lehtonen_2020_AnswerSetProgrammingApproach/`
- Content: ASP-based direct computation of ASPIC+ semantics via σ-assumptions; complexity results up to Π₂ᴾ-skeptical preferred.
- Likely modules: `propstore/aspic_bridge/`
- Notes: index

### Lehtonen_2024_PreferentialASPIC
- Path: `./papers/Lehtonen_2024_PreferentialASPIC/`
- Content: Preferential ASPIC+ under last-link: rephrasing over defeasible elements; complexity matches abstract AFs; ASP encodings for elitist/democratic lifting.
- Likely modules: `propstore/aspic_bridge/`, `propstore/preference.py`
- Notes: full

### Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning
- Path: `./papers/Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning/`
- Content: ASPIC+ as nonmonotonic consequence: cumulative but not monotonic at argument level; property checklist for entailment implementations.
- Likely modules: `propstore/aspic.py`
- Notes: index

### Li_2017_TwoFormsMinimalityASPIC
- Path: `./papers/Li_2017_TwoFormsMinimalityASPIC/`
- Content: Distinguishes ASPIC+'s weak "everything used" minimality from closure-based minimality; canonical minimal argument characterization.
- Likely modules: `propstore/aspic.py`
- Notes: index

### Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible
- Path: `./papers/Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible/`
- Content: LLM-ASPIC+: LLM extraction + ASPIC+ grounded extension; 67.1% on BoardGameQA vs 51.3% pure LLM CoT.
- Likely modules: `propstore/aspic_bridge/`, `propstore/classify.py`
- Notes: index
- Secondary: 7 Defeasible

### Diller_2025_GroundingRule-BasedArgumentationDatalog
- Path: `./papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/`
- Content: First-order ASPIC+ → Datalog grounding procedure; non-approximated predicate detection; ANGRY prototype.
- Likely modules: `propstore/aspic_bridge/`, `propstore/compiler/`
- Notes: index
- Secondary: 7 Defeasible

### Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation
- Path: `./papers/Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation/`
- Content: Incomplete-information ASPIC+: four justification statuses; stability/relevance decision problems; ASP implementation in Clingo.
- Likely modules: `propstore/aspic_bridge/`, `propstore/aspic.py`
- Notes: index

### Odekerken_2025_ArgumentativeReasoningASPICIncompleteInformation
- Path: `./papers/Odekerken_2025_ArgumentativeReasoningASPICIncompleteInformation/`
- Content: JAIR final of incomplete-ASPIC+ line: general complexity bounds, rule-set reformulation, ASP + CEGAR algorithms, larger eval.
- Likely modules: `propstore/aspic_bridge/`
- Notes: index

### Odekerken_2022_StabilityRelevanceIncompleteArgumentation
- Path: `./papers/Odekerken_2022_StabilityRelevanceIncompleteArgumentation/`
- Content: (stub) Earlier paper on stability/relevance for incomplete abstract argumentation — companion to Odekerken 2023/2025 ASPIC+ line.
- Likely modules: `propstore/aspic_bridge/`
- Notes: stub (metadata.json only)

### Alfano_2017_EfficientComputationExtensionsDynamic
- Path: `./papers/Alfano_2017_EfficientComputationExtensionsDynamic/`
- Content: Incremental recomputation of Dung extensions via reduced AF restricted to update-influenced arguments; 1-2 orders of magnitude speedup on ICCMA'15.
- Likely modules: `propstore/dung.py`
- Notes: index

### Boella_2009_DynamicsArgumentationSingleExtensions
- Path: `./papers/Boella_2009_DynamicsArgumentationSingleExtensions/`
- Content: Principle-based evaluation of attack/argument abstraction under grounded semantics; label-sensitive preservation conditions.
- Likely modules: `propstore/dung.py`, `propstore/revision/`
- Notes: index

### Baumann_2010_ExpandingArgumentationFrameworksEnforcing
- Path: `./papers/Baumann_2010_ExpandingArgumentationFrameworksEnforcing/`
- Content: Normal/strong/weak expansions on Dung AFs; any conflict-free set enforceable by adding one argument; extension-count monotonicity.
- Likely modules: `propstore/dung.py`, `propstore/revision/`
- Notes: index
- Secondary: 3c Revision

### Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault
- Path: `./papers/Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault/`
- Content: (From metadata) Seminal ABA paper (Bondarenko/Dung/Kowalski/Toni): abstract argumentation-theoretic approach to default reasoning.
- Likely modules: `propstore/aspic.py` (ABA semantics)
- Notes: stub (metadata.json + paper.pdf only)
- Secondary: 7 Defeasible

### Toni_2014_TutorialAssumption-basedArgumentation
- Path: `./papers/Toni_2014_TutorialAssumption-basedArgumentation/`
- Content: (No notes.md) Tutorial introduction to Assumption-Based Argumentation (ABA) — contraries, support, admissible/preferred/grounded/complete extensions.
- Likely modules: `propstore/aspic.py`
- Notes: stub (metadata.json only)
- Secondary: 7 Defeasible

### Vreeswijk_1997_AbstractArgumentationSystems
- Path: `./papers/Vreeswijk_1997_AbstractArgumentationSystems/`
- Content: (No notes.md) Vreeswijk's abstract argumentation systems with defeasible inference rules, argument strength, and conclusive force — precursor to ASPIC+.
- Likely modules: `propstore/aspic.py`
- Notes: stub (metadata.json only)

### McBurney_2009_DialogueGamesAgentArgumentation
- Path: `./papers/McBurney_2009_DialogueGamesAgentArgumentation/`
- Content: Survey of formal dialogue games: locutions, commitment stores, denotational/operational semantics, strategic pragmatics.
- Likely modules: (no dialogue module)
- Notes: index

### Karacapilidis_2001_ComputerSupportedArgumentationCollaborative
- Path: `./papers/Karacapilidis_2001_ComputerSupportedArgumentationCollaborative/`
- Content: HERMES web-based CSCW system integrating IBIS argumentation with multi-criteria weighting and quantitative proof standards.
- Likely modules: (no obvious module)
- Notes: index

### Stab_2016_ParsingArgumentationStructuresPersuasive
- Path: `./papers/Stab_2016_ParsingArgumentationStructuresPersuasive/`
- Content: End-to-end argument-mining pipeline on persuasive essays; ILP-joint model enforcing tree constraints over sequence labeling + SVM.
- Likely modules: `propstore/classify.py`, `propstore/relate.py`
- Notes: index

### Mayer_2020_Transformer-BasedArgumentMiningHealthcare
- Path: `./papers/Mayer_2020_Transformer-BasedArgumentMiningHealthcare/`
- Content: Transformer-based argument-mining pipeline on 500 RCT abstracts; SciBERT/RoBERTa+GRU+CRF for components; macro-F1 0.87/0.68.
- Likely modules: `propstore/classify.py`, `propstore/embed.py`
- Notes: index

### Freedman_2025_ArgumentativeLLMsClaimVerification
- Path: `./papers/Freedman_2025_ArgumentativeLLMsClaimVerification/`
- Content: ArgLLMs: LLM-generated pro/con arguments + DF-QuAD QBAF; proves base score monotonicity and argument-relation contestability.
- Likely modules: `propstore/praf/`, `propstore/bipolar.py`, `propstore/classify.py`
- Notes: index
- Secondary: Motivation

### Tang_2025_EncodingArgumentationFrameworksPropositional
- Path: `./papers/Tang_2025_EncodingArgumentationFrameworksPropositional/`
- Content: Encoding Dung AFs into multi-valued and fuzzy propositional logic systems; new Lukasiewicz-based fuzzy semantics Eq^L.
- Likely modules: `propstore/dung.py`, `propstore/dung_z3.py`
- Notes: full

### Niskanen_2020_ToksiaEfficientAbstractArgumentation
- Path: `./papers/Niskanen_2020_ToksiaEfficientAbstractArgumentation/`
- Content: µ-toksia SAT-based abstract argumentation reasoner; ICCMA 2019 first place in all main-track tasks; supports dynamic AA.
- Likely modules: `propstore/dung.py`, `propstore/dung_z3.py`
- Notes: full

### Mahmood_2025_Structure-AwareEncodingsArgumentationProperties
- Path: `./papers/Mahmood_2025_Structure-AwareEncodingsArgumentationProperties/`
- Content: (No notes.md) Structure-aware encodings of argumentation properties — follow-up on decomposition/treewidth lineage.
- Likely modules: `propstore/praf/`, `propstore/dung.py`
- Notes: stub (abstract.md, claims.yaml, description.md, paper.pdf, pngs)

### Rahwan_2009_ArgumentationArtificialIntelligence
- Path: `./papers/Rahwan_2009_ArgumentationArtificialIntelligence/`
- Content: (No notes.md) Standard reference handbook "Argumentation in Artificial Intelligence" (Rahwan & Simari eds.).
- Likely modules: (reference overall; no single module)
- Notes: stub (metadata.json + paper.pdf)

### Dunne_2009_ComplexityAbstractArgumentation
- Path: `./papers/Dunne_2009_ComplexityAbstractArgumentation/`
- Content: Computational properties of argument systems under graph-theoretic constraints; Dunne & Wooldridge complexity results (foundational for ICCMA).
- Likely modules: `propstore/dung.py`
- Notes: full

### Verheij_2003_ArtificialArgumentAssistants
- Path: `./papers/Verheij_2003_ArtificialArgumentAssistants/`
- Content: (No notes.md) Design of interactive argument-assistant systems (ArguMed etc.) for user-guided defeasible reasoning.
- Likely modules: (no obvious module)
- Notes: pdf-only

## Cluster 3b — Uncertainty

### Josang_2001_LogicUncertainProbabilities
- Path: `./papers/Josang_2001_LogicUncertainProbabilities/`
- Content: Subjective logic: opinion (b, d, u, a) with b+d+u=1; AND/OR/NOT + discounting + consensus; bijection to Beta PDF.
- Likely modules: `propstore/opinion.py`
- Notes: index

### Josang_2010_CumulativeAveragingFusionBeliefs
- Path: `./papers/Josang_2010_CumulativeAveragingFusionBeliefs/`
- Content: Multiplicative product of multinomial opinions; Assumed Belief Mass vs Assumed Uncertainty redistribution.
- Likely modules: `propstore/opinion.py`
- Notes: index

### Kaplan_2015_PartialObservableUpdateSubjectiveLogic
- Path: `./papers/Kaplan_2015_PartialObservableUpdateSubjectiveLogic/`
- Content: Subjective Logic updates from partially observable evidence via likelihood + Dirichlet moment-matching; trust via likelihood ratios.
- Likely modules: `propstore/opinion.py`, `propstore/calibrate.py`
- Notes: index

### vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic
- Path: `./papers/vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic/`
- Content: Corrected N-source SL fusion operators: WBF, CCF, BCF; WBF = confidence-weighted average of Dirichlet hyper-probabilities.
- Likely modules: `propstore/opinion.py`
- Notes: index

### Margoni_2024_SubjectiveLogicMetaAnalysis
- Path: `./papers/Margoni_2024_SubjectiveLogicMetaAnalysis/`
- Content: SL as meta-analysis: findings as binomial opinions fused via WBF preserving second-order uncertainty; 67 infant-prosociality findings.
- Likely modules: `propstore/opinion.py`, `propstore/calibrate.py`
- Notes: index
- Secondary: Motivation

### Vasilakes_2025_SubjectiveLogicEncodings
- Path: `./papers/Vasilakes_2025_SubjectiveLogicEncodings/`
- Content: Subjective Logic Encodings (SLEs) for annotator labels; CBF + trust discounting; KL-divergence loss on Dirichlet targets.
- Likely modules: `propstore/opinion.py`, `propstore/calibrate.py`
- Notes: index

### Shafer_1976_MathematicalTheoryEvidence
- Path: `./papers/Shafer_1976_MathematicalTheoryEvidence/`
- Content: Foundational DS monograph: belief functions, Dempster's rule, simple/separable support, weight of evidence, compatible frames.
- Likely modules: `propstore/opinion.py`
- Notes: index

### Shenoy_1990_AxiomsProbabilityBelief-functionPropagation
- Path: `./papers/Shenoy_1990_AxiomsProbabilityBelief-functionPropagation/`
- Content: Three axioms on valuation systems necessary/sufficient for local computation of marginals via hypertree message-passing.
- Likely modules: `propstore/propagation.py`, `propstore/opinion.py`
- Notes: index

### Sensoy_2018_EvidentialDeepLearningQuantifyClassification
- Path: `./papers/Sensoy_2018_EvidentialDeepLearningQuantifyClassification/`
- Content: Replaces softmax with Dirichlet parameters; per-class evidence yields uncertainty mass separating epistemic ignorance from aleatoric.
- Likely modules: `propstore/calibrate.py`, `propstore/opinion.py`
- Notes: index

### Sensoy_2018_EvidentialDeepLearningQuantify
- Path: `./papers/Sensoy_2018_EvidentialDeepLearningQuantify/`
- Content: (No notes.md; same authors same year) Likely the NeurIPS poster/preprint twin of the classification paper above.
- Likely modules: `propstore/calibrate.py`, `propstore/opinion.py`
- Notes: stub (metadata.json + paper.pdf)

### Walley_1996_InferencesMultinomialDataLearning
- Path: `./papers/Walley_1996_InferencesMultinomialDataLearning/`
- Content: Imprecise Dirichlet Model (IDM): vacuous upper/lower probs parameterized by s; satisfies embedding/symmetry/representation invariance.
- Likely modules: `propstore/opinion.py`, `propstore/calibrate.py`
- Notes: index

### Guo_2017_CalibrationModernNeuralNetworks
- Path: `./papers/Guo_2017_CalibrationModernNeuralNetworks/`
- Content: Modern NNs poorly calibrated (overconfident); temperature scaling (single param) reduces ECE from 3-15% to <2%.
- Likely modules: `propstore/calibrate.py`
- Notes: index

### Denoeux_2018_Decision-MakingBeliefFunctionsReview
- Path: `./papers/Denoeux_2018_Decision-MakingBeliefFunctionsReview/`
- Content: Survey of DS decision criteria (Hurwicz, pignistic, OWA, maximality, E-admissibility, Shafer goals); all reduce to MEU on Bayesian bf.
- Likely modules: `propstore/world/` (apply_decision_criterion)
- Notes: index

### Gardenfors_1982_UnreliableProbabilitiesRiskTaking
- Path: `./papers/Gardenfors_1982_UnreliableProbabilitiesRiskTaking/`
- Content: Epistemic reliability as second-order measure over distribution sets; MMEU resolves Ellsberg and Popper paradoxes.
- Likely modules: `propstore/opinion.py`, `propstore/world/`
- Notes: index

### Howard_1966_InformationValueTheory
- Path: `./papers/Howard_1966_InformationValueTheory/`
- Content: Value-of-information theory: clairvoyance as upper bound; non-additivity of joint EVPI.
- Likely modules: `propstore/sensitivity.py`, `propstore/world/`
- Notes: index

### Hunter_2017_ProbabilisticReasoningAbstractArgumentation
- Path: `./papers/Hunter_2017_ProbabilisticReasoningAbstractArgumentation/`
- Content: Epistemic prob arg: probability functions over argument sets constrained by attack-graph postulates (COH, FOU, RAT, ...); maxent propagation.
- Likely modules: `propstore/praf/`
- Notes: index

### Hunter_2021_ProbabilisticArgumentationSurvey
- Path: `./papers/Hunter_2021_ProbabilisticArgumentationSurvey/`
- Content: Survey separating epistemic vs constellation approaches; rationality postulates (COH, RAT, FOU, TRU, OPT).
- Likely modules: `propstore/praf/`
- Notes: index

### Li_2011_ProbabilisticArgumentationFrameworks
- Path: `./papers/Li_2011_ProbabilisticArgumentationFrameworks/`
- Content: PrAFs: independent probabilities on arg/defeat existence; constellations with exact exponential + Monte Carlo with Agresti-Coull bounds.
- Likely modules: `propstore/praf/`
- Notes: index

### Thimm_2012_ProbabilisticSemanticsAbstractArgumentation
- Path: `./papers/Thimm_2012_ProbabilisticSemanticsAbstractArgumentation/`
- Content: Probabilistic semantics for Dung AFs; four rationality postulates from complete labellings; maxent as unique principled selection.
- Likely modules: `propstore/praf/`
- Notes: index

### Popescu_2024_ProbabilisticArgumentationConstellation
- Path: `./papers/Popescu_2024_ProbabilisticArgumentationConstellation/`
- Content: First exact tree-decomposition DP for PrAF constellation approach; #·P/#·NP-completeness; FPT on bounded treewidth.
- Likely modules: `propstore/praf/` (treedecomp DP)
- Notes: index

### Popescu_2024_AlgorithmicProbabilisticArgumentationConstellation
- Path: `./papers/Popescu_2024_AlgorithmicProbabilisticArgumentationConstellation/`
- Content: Exact DP algorithms for extension and acceptability probabilities in PrAFs parameterized by primal graph treewidth (KR 2024 extended version).
- Likely modules: `propstore/praf/` (treedecomp DP)
- Notes: full

### Popescu_2024_AdvancingAlgorithmicApproachesProbabilistic
- Path: `./papers/Popescu_2024_AdvancingAlgorithmicApproachesProbabilistic/`
- Content: (No notes.md) Popescu & Wallner follow-up/companion to the KR 2024 paper above; advancing algorithmic approaches under constellation.
- Likely modules: `propstore/praf/`
- Notes: stub (metadata.json + paper.pdf)

### Potyka_2019_PolynomialTimeEpistemicProbabilistic
- Path: `./papers/Potyka_2019_PolynomialTimeEpistemicProbabilistic/`
- Content: Polynomial-time fragment of epistemic probabilistic argumentation via linear atomic constraints on P(A); ProBabble library.
- Likely modules: `propstore/praf/`
- Notes: index

### Riveret_2017_LabellingFrameworkProbabilisticArgumentation
- Path: `./papers/Riveret_2017_LabellingFrameworkProbabilisticArgumentation/`
- Content: Probabilistic Labelling Frames (PLFs) with {ON,OFF}×{IN,OUT,UN} label sets; subsumes constellations and epistemic approaches.
- Likely modules: `propstore/praf/`, `propstore/world/atms.py`
- Notes: index
- Secondary: 3e Reasoning infra

### Coupé_2002_PropertiesSensitivityAnalysisBayesian
- Path: `./papers/Coupé_2002_PropertiesSensitivityAnalysisBayesian/`
- Content: BN posterior is a linear fractional function of any single CPT parameter; sensitivity set reduces sweep to 2-3 evaluations.
- Likely modules: `propstore/sensitivity.py`
- Notes: index

### Chan_2005_DistanceMeasureBoundingProbabilistic
- Path: `./papers/Chan_2005_DistanceMeasureBoundingProbabilistic/`
- Content: CD-distance = log range of probability ratios; tight bounds on odds-ratio change; Jeffrey's rule and Pearl virtual evidence minimize CD.
- Likely modules: `propstore/sensitivity.py`, `propstore/revision/`
- Notes: index

### Ballester-Ripoll_2024_GlobalSensitivityAnalysisBayesianNetworks
- Path: `./papers/Ballester-Ripoll_2024_GlobalSensitivityAnalysisBayesianNetworks/`
- Content: Global variance-based SA for BN parameters via Sobol indices with low-rank tensor-train decomposition; OAT correlates <0.51.
- Likely modules: `propstore/sensitivity.py`
- Notes: index

## Cluster 3c — Revision

### Alchourron_1985_TheoryChange
- Path: `./papers/Alchourron_1985_TheoryChange/`
- Content: AGM postulates for contraction/revision; partial meet contraction; Levi/Harper identities; representation theorem for transitively relational.
- Likely modules: `propstore/revision/`, `propstore/world/atms.py`
- Notes: index

### Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic
- Path: `./papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/`
- Content: Epistemic entrenchment as total preorder; representation theorem bijecting AGM contraction with 5-postulate entrenchment; O(n!) orderings for n atoms.
- Likely modules: `propstore/revision/`, `propstore/fragility.py`
- Notes: index

### Darwiche_1997_LogicIteratedBeliefRevision
- Path: `./papers/Darwiche_1997_LogicIteratedBeliefRevision/`
- Content: Four iterated-revision postulates C1-C4 beyond AGM; representation via pre-order preservation (CR1-CR4); OCF-based concrete operator.
- Likely modules: `propstore/revision/`
- Notes: index

### Spohn_1988_OrdinalConditionalFunctionsDynamic
- Path: `./papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/`
- Content: Ordinal conditional functions (kappa-functions) as qualitative epistemic states; A_n-conditionalization; independence properties.
- Likely modules: `propstore/revision/`
- Notes: index

### Booth_2006_AdmissibleRestrainedRevision
- Path: `./papers/Booth_2006_AdmissibleRestrainedRevision/`
- Content: Admissible iterated revision subclass excluding natural revision; introduces restrained revision (most conservative) with axiomatization.
- Likely modules: `propstore/revision/`
- Notes: index

### Konieczny_2002_MergingInformationUnderConstraints
- Path: `./papers/Konieczny_2002_MergingInformationUnderConstraints/`
- Content: IC merging postulates IC0-IC8; representation via distance-based pre-orders; Sigma/Max/GMax operator families.
- Likely modules: `propstore/revision/`, `propstore/repo/` (IC merge)
- Notes: index

### Coste-Marquis_2007_MergingDung'sArgumentationSystems
- Path: `./papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/`
- Content: Distance-based merging of Dung AFs lifted from IC merging; Partial AFs with three-valued attacks; sum/max/leximax aggregation.
- Likely modules: `propstore/revision/`, `propstore/repo/`
- Notes: index
- Secondary: 3a Argumentation

### Baumann_2015_AGMMeetsAbstractArgumentation
- Path: `./papers/Baumann_2015_AGMMeetsAbstractArgumentation/`
- Content: AGM expansion and revision for Dung AFs via Dung logics (ordinary = strong equivalence); expansion = kernel union; faithful-assignment revision.
- Likely modules: `propstore/revision/`
- Notes: index

### Baumann_2019_AGMContractionDung
- Path: `./papers/Baumann_2019_AGMContractionDung/`
- Content: AGM-style contraction for Dung AFs using Dung logics; proves Harper Identity fails; dropping recovery restores well-behaved operators.
- Likely modules: `propstore/revision/`
- Notes: full

### Diller_2015_ExtensionBasedBeliefRevision
- Path: `./papers/Diller_2015_ExtensionBasedBeliefRevision/`
- Content: Extension-based AGM revision for Dung AFs; works at extension level rather than model level; generic for stable/semi-stable/stage/sub-stable.
- Likely modules: `propstore/revision/`
- Notes: full

### Cayrol_2014_ChangeAbstractArgumentationFrameworks
- Path: `./papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/`
- Content: Taxonomy of adding one argument to a Dung AF; seven structural + three status properties with N/S conditions under grounded/preferred.
- Likely modules: `propstore/revision/`, `propstore/dung.py`
- Notes: full

### Doutre_2018_ConstraintsChangesSurveyAbstract
- Path: `./papers/Doutre_2018_ConstraintsChangesSurveyAbstract/`
- Content: Survey of dynamic constraint-enforcement approaches on abstract AFs; classifies 20+ by constraint/change/quality axes.
- Likely modules: `propstore/revision/`
- Notes: index

### Rotstein_2008_ArgumentTheoryChangeRevision
- Path: `./papers/Rotstein_2008_ArgumentTheoryChangeRevision/`
- Content: Argument Theory Change: AGM-style revision for structured args with active/inactive status; warrant-prioritized incision-based operator.
- Likely modules: `propstore/revision/`, `propstore/aspic.py`
- Notes: index

### Bonanno_2007_AGMBeliefRevisionTemporalLogic
- Path: `./papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/`
- Content: Axiomatization of AGM K*1-K*8 within branching-time temporal logic; Qualitative Bayes Rule; requires Backward Uniqueness (fails on DAGs).
- Likely modules: `propstore/revision/`, `propstore/worldline/`
- Notes: index

### Bonanno_2010_BeliefChangeBranchingTime
- Path: `./papers/Bonanno_2010_BeliefChangeBranchingTime/`
- Content: AGM-consistency of branching-time belief-revision frames ≡ rationalizability by total pre-order ≡ PLS frame property.
- Likely modules: `propstore/revision/`, `propstore/worldline/`
- Notes: index

### Dixon_1993_ATMSandAGM
- Path: `./papers/Dixon_1993_ATMSandAGM/`
- Content: ATMS context switching ≡ AGM expansion+contraction given entrenchment from justifications; ATMS→AGM translation correct.
- Likely modules: `propstore/revision/`, `propstore/world/atms.py`
- Notes: index
- Secondary: 3e Reasoning infra

### Shapiro_1998_BeliefRevisionTMS
- Path: `./papers/Shapiro_1998_BeliefRevisionTMS/`
- Content: Survey of TMS (JTMS/LTMS/ATMS/SNeBR) vs AGM traditions; proposes AGM-compliant SNePSwD-based TMS.
- Likely modules: `propstore/revision/`, `propstore/world/atms.py`
- Notes: index
- Secondary: 3e Reasoning infra

### Greenberg_2009_CitationDistortions
- Path: `./papers/Greenberg_2009_CitationDistortions/`
- Content: Empirical citation-distortion taxonomy (bias/amplification/invention) on β-amyloid IBM case; 242 papers, 675 citations.
- Likely modules: `propstore/provenance.py`, `propstore/stances.py`
- Notes: index
- Secondary: Motivation

### Ginsberg_1985_Counterfactuals
- Path: `./papers/Ginsberg_1985_Counterfactuals/`
- Content: Three-valued counterfactual framework equivalent to Lewis possible worlds; context via sublanguage selection; subsumes min-fault diagnosis.
- Likely modules: `propstore/world/`, `propstore/revision/`
- Notes: index
- Secondary: 3e Reasoning infra

## Cluster 3d — Semantic substrate

### McCarthy_1993_FormalizingContext
- Path: `./papers/McCarthy_1993_FormalizingContext/`
- Content: Contexts as first-class logical objects via ist(c, p); lifting rules; nonmonotonic inheritance via abnormality; relative decontextualization.
- Likely modules: `propstore/context_hierarchy.py`, `propstore/context_types.py`
- Notes: index

### McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning
- Path: `./papers/McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning/`
- Content: Circumscription sentence schema formalizing "only provably required"; predicate + domain circumscription with minimal-model soundness.
- Likely modules: `propstore/context_hierarchy.py`
- Notes: index
- Secondary: 3e Reasoning infra

### Guha_1991_ContextsFormalization
- Path: `./papers/Guha_1991_ContextsFormalization/`
- Content: (No notes.md, chunks/pngs) Guha's foundational CYC contexts formalization: lifting, reification, microtheories.
- Likely modules: `propstore/context_hierarchy.py`
- Notes: pdf-only

### Guha_1991_ContextsFormalizationApplications
- Path: `./papers/Guha_1991_ContextsFormalizationApplications/`
- Content: (No notes.md, chunks/pngs) Applications companion paper: contexts in practice (CYC microtheories) — see `papers/notes/microtheories-paper.md` for extracted analysis.
- Likely modules: `propstore/context_hierarchy.py`
- Notes: pdf-only

### Kallem_2006_Microtheories
- Path: `./papers/Kallem_2006_Microtheories/`
- Content: CYC's microtheory system: named contexts scoping assertion visibility; contradictory viewpoints coexist; Matthew/Luke Christmas example.
- Likely modules: `propstore/context_hierarchy.py`, `propstore/repo/`
- Notes: index

### Ghidini_2001_LocalModelsSemanticsContextual
- Path: `./papers/Ghidini_2001_LocalModelsSemanticsContextual/`
- Content: Local Models Semantics: families of local Tarskian models with compatibility relations; Multi-Context proof theory with bridge rules.
- Likely modules: `propstore/context_hierarchy.py`, `propstore/context_types.py`
- Notes: index

### Fillmore_1982_FrameSemantics
- Path: `./papers/Fillmore_1982_FrameSemantics/`
- Content: Frame semantics: word meanings via structured background knowledge (frames); commercial transaction frame, BACHELOR, LAND/GROUND.
- Likely modules: `propstore/core/` (concepts/frames), `propstore/cel_registry.py`
- Notes: index

### Baker_1998_BerkeleyFrameNet
- Path: `./papers/Baker_1998_BerkeleyFrameNet/`
- Content: Berkeley FrameNet: corpus-based lexicographic database organized around frames; ~5000 lexical units with FE/PT/GF annotations.
- Likely modules: `propstore/core/` (concepts)
- Notes: index

### Narayanan_2014_BridgingTextKnowledgeFrames
- Path: `./papers/Narayanan_2014_BridgingTextKnowledgeFrames/`
- Content: FrameNet as bridge between text and structured knowledge; 95.9% IE precision; cross-lingual metaphor analysis.
- Likely modules: `propstore/core/`, `propstore/classify.py`
- Notes: index

### Pustejovsky_1991_GenerativeLexicon
- Path: `./papers/Pustejovsky_1991_GenerativeLexicon/`
- Content: Generative Lexicon: argument/event/qualia/inheritance structure; type coercion and cocompositionality derive context-dependent senses.
- Likely modules: `propstore/core/` (concepts)
- Notes: index

### Pustejovsky_2013_DynamicEventStructureHabitat
- Path: `./papers/Pustejovsky_2013_DynamicEventStructureHabitat/`
- Content: Dynamic Event Structure + Habitat Theory: DITL over qualia-structured record types; scale-typed attributes (nominal/ordinal/interval/ratio).
- Likely modules: `propstore/core/`, `propstore/worldline/`
- Notes: index

### Dowty_1991_ThematicProtoRoles
- Path: `./papers/Dowty_1991_ThematicProtoRoles/`
- Content: Proto-Agent/Proto-Patient cluster concepts defined by independent entailments; Argument Selection Principle by counting properties.
- Likely modules: `propstore/core/`, `propstore/classify.py`
- Notes: index

### Wein_2023_CrossLinguisticAMR
- Path: `./papers/Wein_2023_CrossLinguisticAMR/`
- Content: Systematic cross-lingual AMR evaluation; divergence schema by cause and type; AMR Smatch outperforms BERTscore on human similarity.
- Likely modules: `propstore/core/`, `propstore/relate.py`
- Notes: index

### Buitelaar_2011_OntologyLexicalizationLemon
- Path: `./papers/Buitelaar_2011_OntologyLexicalizationLemon/`
- Content: lemon: RDF lexicon-ontology linking model with lexical entry/form/sense primitives and opt-in morphology/phrase/syntax-semantics modules.
- Likely modules: `propstore/core/`, `propstore/identity.py`
- Notes: index

### Gruber_1993_OntologyDesignPrinciples
- Path: `./papers/Gruber_1993_OntologyDesignPrinciples/`
- Content: (No notes.md) Gruber's classic ontology design principles (clarity, coherence, extendibility, minimal encoding bias, minimal ontological commitment).
- Likely modules: `propstore/core/`, `propstore/validate_concepts.py`
- Notes: pdf-only

### Clark_2014_MicropublicationsSemanticModel
- Path: `./papers/Clark_2014_MicropublicationsSemanticModel/`
- Content: Micropublications semantic model MP=(A, mp, c, A_c, Phi, R); OWL + Open Annotation; Similarity Groups/Holotypes.
- Likely modules: `propstore/claims.py`, `propstore/provenance.py`, `propstore/claim_graph.py`
- Notes: index

### Clark_2014_Micropublications
- Path: `./papers/Clark_2014_Micropublications/`
- Content: Companion/duplicate directory for the Clark 2014 Micropublications paper with a shorter notes.md.
- Likely modules: `propstore/claims.py`
- Notes: full (likely duplicate of SemanticModel dir)

### Groth_2010_AnatomyNanopublication
- Path: `./papers/Groth_2010_AnatomyNanopublication/`
- Content: Nanopublication model: minimal citable assertions + provenance + attribution; layered ontology over RDF named graphs.
- Likely modules: `propstore/claims.py`, `propstore/provenance.py`
- Notes: index

### Buneman_2001_CharacterizationDataProvenance
- Path: `./papers/Buneman_2001_CharacterizationDataProvenance/`
- Content: (From metadata) Buneman/Khanna/Tan "Why and Where": characterization of data provenance distinguishing why-provenance and where-provenance.
- Likely modules: `propstore/provenance.py`
- Notes: stub (metadata.json only)

### Carroll_2005_NamedGraphsProvenanceTrust
- Path: `./papers/Carroll_2005_NamedGraphsProvenanceTrust/`
- Content: (From metadata) Named Graphs extending RDF for provenance/trust: assertion + meta-statements about graphs themselves.
- Likely modules: `propstore/provenance.py`, `propstore/repo/`
- Notes: stub (metadata.json only)

### Green_2007_ProvenanceSemirings
- Path: `./papers/Green_2007_ProvenanceSemirings/`
- Content: Semiring-based provenance: K-annotated tuples; provenance polynomials N[X] as universal model; subsumes lineage/why-prov/bag/Boolean.
- Likely modules: `propstore/provenance.py`
- Notes: index

### Juty_2020_UniquePersistentResolvableIdentifiers
- Path: `./papers/Juty_2020_UniquePersistentResolvableIdentifiers/`
- Content: Survey of persistent identifiers (DOI, ARK, identifiers.org, PURL); individual registration vs namespace-level resolution patterns.
- Likely modules: `propstore/uri.py`, `propstore/identity.py`
- Notes: index

### Kuhn_2014_TrustyURIs
- Path: `./papers/Kuhn_2014_TrustyURIs/`
- Content: Trusty URIs embedding cryptographic hashes at RDF graph level; serialization-invariant; Java/Perl/Python implementations.
- Likely modules: `propstore/uri.py`, `propstore/sidecar/`
- Notes: index

### Kuhn_2015_DigitalArtifactsVerifiable
- Path: `./papers/Kuhn_2015_DigitalArtifactsVerifiable/`
- Content: Trusty URIs with SHA-256; FA byte-level + RA RDF-graph-level modules; evaluated on 1B+ nanopublication triples.
- Likely modules: `propstore/uri.py`, `propstore/sidecar/`
- Notes: index

### Kuhn_2017_ReliableGranularReferences
- Path: `./papers/Kuhn_2017_ReliableGranularReferences/`
- Content: Trusty-URI nanopublications with granular/verifiable/persistent refs; incremental versioning; decentralized-server retrieval.
- Likely modules: `propstore/uri.py`, `propstore/sidecar/`
- Notes: index

### Wilkinson_2016_FAIRGuidingPrinciplesScientific
- Path: `./papers/Wilkinson_2016_FAIRGuidingPrinciplesScientific/`
- Content: FAIR principles (Findable, Accessible, Interoperable, Reusable) with 15 measurable sub-principles; machine-actionability emphasis.
- Likely modules: `propstore/uri.py`, `propstore/provenance.py`
- Notes: index

### Raad_2019_SameAsProblemSurvey
- Path: `./papers/Raad_2019_SameAsProblemSurvey/`
- Content: Survey of owl:sameAs identity problem; detection (terminological/semantic/network/content-based) and relaxed identity alternatives.
- Likely modules: `propstore/identity.py`
- Notes: index

### Halpin_2010_OwlSameAsIsntSame
- Path: `./papers/Halpin_2010_OwlSameAsIsntSame/`
- Content: Systematic misuse of owl:sameAs; Similarity Ontology with 8 graded identity properties; MT experiment showing ~50% misuse rate.
- Likely modules: `propstore/identity.py`
- Notes: index

### Beek_2018_SameAs.ccClosure500MOwl
- Path: `./papers/Beek_2018_SameAs.ccClosure500MOwl/`
- Content: sameAs.cc: 558M owl:sameAs statements, 49M closure sets via union-find; largest set (177k) conflates Einstein with countries and the empty string.
- Likely modules: `propstore/identity.py`
- Notes: index

### Melo_2013_NotQuiteSameIdentity
- Path: `./papers/Melo_2013_NotQuiteSameIdentity/`
- Content: Strict vs near-identity on Linked Data; erroneous owl:sameAs repair is NP-hard (min multicut); LP relaxation + Hungarian at Web scale.
- Likely modules: `propstore/identity.py`
- Notes: index

## Cluster 3e — Reasoning infra

### Doyle_1979_TruthMaintenanceSystem
- Path: `./papers/Doyle_1979_TruthMaintenanceSystem/`
- Content: Original TMS: SL/CP justifications; seven-step truth-maintenance algorithm; dependency-directed backtracking with nogoods.
- Likely modules: `propstore/world/atms.py`, `propstore/world/`
- Notes: index

### deKleer_1986_AssumptionBasedTMS
- Path: `./papers/deKleer_1986_AssumptionBasedTMS/`
- Content: ATMS: every datum labelled with minimal assumption environments; four label invariants (consistency/soundness/completeness/minimality).
- Likely modules: `propstore/world/atms.py`
- Notes: index

### deKleer_1986_ProblemSolvingATMS
- Path: `./papers/deKleer_1986_ProblemSolvingATMS/`
- Content: Problem-solving on top of ATMS: consumer architecture, simplest-label-first scheduling, PLUS/TIMES/AND/OR/ONEOF constraint language.
- Likely modules: `propstore/world/atms.py`
- Notes: index

### deKleer_1984_QualitativePhysicsConfluences
- Path: `./papers/deKleer_1984_QualitativePhysicsConfluences/`
- Content: Qualitative physics via confluences over {+,0,-}; ENVISION program; no-function-in-structure, locality, mythical causality.
- Likely modules: `propstore/world/` (context ontology)
- Notes: index

### Forbus_1993_BuildingProblemSolvers
- Path: `./papers/Forbus_1993_BuildingProblemSolvers/`
- Content: BPS textbook: full Common Lisp implementations of JTMS/LTMS/ATMS, TRE/FTRE, TCON/ATCON, TGIZMO, TGDE, WALTZER.
- Likely modules: `propstore/world/atms.py`
- Notes: index

### Falkenhainer_1987_BeliefMaintenanceSystem
- Path: `./papers/Falkenhainer_1987_BeliefMaintenanceSystem/`
- Content: BMS generalizing JTMS to continuous DS-theoretic beliefs; hard/invertible support links; threshold queries.
- Likely modules: `propstore/world/atms.py`, `propstore/opinion.py`
- Notes: index
- Secondary: 3b Uncertainty

### McAllester_1978_ThreeValuedTMS
- Path: `./papers/McAllester_1978_ThreeValuedTMS/`
- Content: Three-valued (T/F/unknown) TMS with disjunctive clauses; clause-based contradiction generating new clauses; the "RUP" system.
- Likely modules: `propstore/world/atms.py`
- Notes: index

### McDermott_1983_ContextsDataDependencies
- Path: `./papers/McDermott_1983_ContextsDataDependencies/`
- Content: Unifies data pools (contexts) and data dependencies via Boolean labels over beads; ~0.3 ms/node on 1983 hardware.
- Likely modules: `propstore/world/atms.py`, `propstore/context_hierarchy.py`
- Notes: index
- Secondary: 3d Semantic

### Mason_1989_DATMSFrameworkDistributedAssumption
- Path: `./papers/Mason_1989_DATMSFrameworkDistributedAssumption/`
- Content: Distributed ATMS: per-agent local ATMS with message passing; Fact-ID = <id:agent>; four fact operators; configurable contradiction propagation.
- Likely modules: `propstore/world/atms.py`, `propstore/repo/`
- Notes: index

### Martins_1983_MultipleBeliefSpaces
- Path: `./papers/Martins_1983_MultipleBeliefSpaces/`
- Content: MBR on SWM+SNePS representing multiple agents' contradictory beliefs via contexts/belief spaces; restriction-set contradiction handling.
- Likely modules: `propstore/world/atms.py`
- Notes: index

### Martins_1988_BeliefRevision
- Path: `./papers/Martins_1988_BeliefRevision/`
- Content: SWM relevance logic with origin/restriction sets auto-tracking propositional dependencies; MBR belief-revision model.
- Likely modules: `propstore/world/atms.py`, `propstore/revision/`
- Notes: index
- Secondary: 3c Revision

### Moore_1985_SemanticalConsiderationsNonmonotonicLogic
- Path: `./papers/Moore_1985_SemanticalConsiderationsNonmonotonicLogic/`
- Content: Autoepistemic logic with possible-worlds semantics (sound+complete); distinguishes default from autoepistemic reasoning.
- Likely modules: (no direct module — semantic-substrate bridge)
- Notes: index

### Reiter_1980_DefaultReasoning
- Path: `./papers/Reiter_1980_DefaultReasoning/`
- Content: Default logic: defaults (prereq/justif/conseq); normal defaults guaranteed extensions; top-down linear resolution proof theory.
- Likely modules: `propstore/aspic.py`, `propstore/world/atms.py`
- Notes: index
- Secondary: 7 Defeasible

### Pollock_1987_DefeasibleReasoning
- Path: `./papers/Pollock_1987_DefeasibleReasoning/`
- Content: Prima facie vs conclusive reasons; rebutting vs undercutting defeaters; warrant via iterative defeat/reinstatement; OSCAR implementation.
- Likely modules: `propstore/aspic.py`, `propstore/conflict_detector/`
- Notes: index
- Secondary: 7 Defeasible

### Halpern_2005_CausesExplanationsStructuralModel
- Path: `./papers/Halpern_2005_CausesExplanationsStructuralModel/`
- Content: Structural-model actual causation (AC1-AC3) with contingent interventions; handles preemption/overdetermination.
- Likely modules: `propstore/world/`, `propstore/sensitivity.py`
- Notes: index

### Halpern_2000_CausesExplanationsStructural-ModelApproach
- Path: `./papers/Halpern_2000_CausesExplanationsStructural-ModelApproach/`
- Content: Earlier/companion version of the Halpern-Pearl structural-model causation paper; AC1-AC3 definition of actual causation.
- Likely modules: `propstore/world/`, `propstore/sensitivity.py`
- Notes: full

### Pearl_2000_CausalityModelsReasoningInference
- Path: `./papers/Pearl_2000_CausalityModelsReasoningInference/`
- Content: Pearl's monograph: structural causal models, do-calculus, backdoor/frontdoor criteria, counterfactual reasoning; foundational for Halpern-Pearl.
- Likely modules: `propstore/world/`, `propstore/sensitivity.py`
- Notes: full

### Moura_2008_Z3EfficientSMTSolver
- Path: `./papers/Moura_2008_Z3EfficientSMTSolver/`
- Content: Z3 SMT solver: DPLL-SAT + theory solvers (linear arith, bit-vectors, arrays, tuples) + E-matching quantifier instantiation.
- Likely modules: `propstore/z3_conditions.py`, `propstore/dung_z3.py`, `propstore/cel_checker.py`
- Notes: index

### Moura_2008_ProofsRefutationsZ3
- Path: `./papers/Moura_2008_ProofsRefutationsZ3/`
- Content: Z3 proof-producing + model-producing internals; implicit quotation; modular natural-deduction proof terms.
- Likely modules: `propstore/z3_conditions.py`
- Notes: index

### Bjorner_2014_MaximalSatisfactionZ3
- Path: `./papers/Bjorner_2014_MaximalSatisfactionZ3/`
- Content: νZ optimization module for Z3: weighted MaxSMT, linear-arith optimization, lexicographic/Pareto/box multi-objective strategies.
- Likely modules: `propstore/z3_conditions.py`
- Notes: full

### Sebastiani_2015_OptiMathSATToolOptimizationModulo
- Path: `./papers/Sebastiani_2015_OptiMathSATToolOptimizationModulo/`
- Content: OptiMathSAT OMT: lex/Pareto/minmax multi-objective over linear arith, bit-vectors, partial weighted MaxSMT.
- Likely modules: `propstore/z3_conditions.py`
- Notes: index

### Docef_2023_UsingZ3VerifyInferencesFragmentsLinearLogic
- Path: `./papers/Docef_2023_UsingZ3VerifyInferencesFragmentsLinearLogic/`
- Content: Reusable Z3 template for verifying Gentzen-style inference rules in fragments of linear logic (MLL+Mix, MILL).
- Likely modules: `propstore/z3_conditions.py`
- Notes: index

### Horowitz_2021_EpiPen
- Path: `./papers/Horowitz_2021_EpiPen/`
- Content: EpiPEn Python DSL encoding epistemic puzzles as FO knowledge-state transitions with Z3; public announcements, simultaneous-action blocks.
- Likely modules: `propstore/z3_conditions.py`
- Notes: index

### Cousot_1977_AbstractInterpretation
- Path: `./papers/Cousot_1977_AbstractInterpretation/`
- Content: (No notes.md; paper.pdf only) Cousot & Cousot foundational abstract interpretation: Galois connections, widening/narrowing, fixed-point approximation.
- Likely modules: `propstore/cel_checker.py`, `propstore/cel_types.py`
- Notes: pdf-only

### Kennedy_1997_RelationalParametricityUnitsMeasure
- Path: `./papers/Kennedy_1997_RelationalParametricityUnitsMeasure/`
- Content: (No notes.md) Relational parametricity for units of measure; dimensional polymorphism as a free theorem.
- Likely modules: `propstore/unit_dimensions.py`, `propstore/cel_types.py`
- Notes: stub (metadata.json + paper.pdf)

### Knuth_1970_SimpleWordProblems
- Path: `./papers/Knuth_1970_SimpleWordProblems/`
- Content: Knuth-Bendix completion algorithm for deciding equational word problems; confluent+terminating TRS construction.
- Likely modules: `propstore/cel_checker.py`, `propstore/equation_comparison.py`
- Notes: index

### Sarkar_2004_Nanopass
- Path: `./papers/Sarkar_2004_Nanopass/`
- Content: (No notes.md) Dipanwita Sarkar nanopass compiler framework: small, typed IR transformations for educational compilers.
- Likely modules: `propstore/compiler/`
- Notes: stub (metadata.json + paper.pdf)

### Pierce_2002_TypesProgrammingLanguages
- Path: `./papers/Pierce_2002_TypesProgrammingLanguages/`
- Content: (No notes.md) Pierce's TAPL textbook: type systems, subtyping, polymorphism, recursive/dependent types — foundational reference.
- Likely modules: `propstore/cel_types.py`, `propstore/cel_checker.py`
- Notes: stub (metadata.json + paper.pdf)

### Eskandari_2016_OnlineStreamingFeatureSelection
- Path: `./papers/Eskandari_2016_OnlineStreamingFeatureSelection/`
- Content: (From metadata) Online streaming feature selection under rough-set framework — likely for incremental classification/embedding pipelines.
- Likely modules: `propstore/embed.py`, `propstore/classify.py`
- Notes: stub (metadata.json only)

### Järvisalo_2025_ICCMA20235thInternational
- Path: `./papers/Järvisalo_2025_ICCMA20235thInternational/`
- Content: ICCMA 2023 competition overview: formalisms (AF, ABA), tracks, benchmarks, solver implementations and empirical rankings.
- Likely modules: `propstore/dung.py`, `propstore/aspic_bridge/`
- Notes: full
- Secondary: 3a Argumentation

## Cluster 7 — Defeasible / Datalog

### Antoniou_2007_DefeasibleReasoningSemanticWeb
- Path: `./papers/Antoniou_2007_DefeasibleReasoningSemanticWeb/`
- Content: DR-Prolog: defeasible theories → logic programs under WFS via XSB; ambiguity blocking/propagating; RDF/RDFS/OWL integration.
- Likely modules: `propstore/aspic.py`, `propstore/compiler/`
- Notes: index

### Bozzato_2018_ContextKnowledgeJustifiableExceptions
- Path: `./papers/Bozzato_2018_ContextKnowledgeJustifiableExceptions/`
- Content: Contextualized Knowledge Repositories (CKRs) with defeasible axioms; justified exceptions via clashing assumption sets; datalog translation.
- Likely modules: `propstore/context_hierarchy.py`, `propstore/aspic.py`
- Notes: index
- Secondary: 3d Semantic

### Bozzato_2020_DatalogDefeasibleDLLite
- Path: `./papers/Bozzato_2020_DatalogDefeasibleDLLite/`
- Content: Datalog translation for DL-Lite_R KBs with defeasible axioms under CKR "justifiable exception" semantics; NLogSpace/coNP complexity.
- Likely modules: `propstore/aspic.py`, `propstore/compiler/`
- Notes: index

### Brewka_1989_PreferredSubtheoriesExtendedLogical
- Path: `./papers/Brewka_1989_PreferredSubtheoriesExtendedLogical/`
- Content: Preferred maximal consistent subsets (preferred subtheories); Prioritized Default Logic (PDL) equivalent to layered Reiter default logic.
- Likely modules: `propstore/aspic.py`, `propstore/preference.py`
- Notes: index
- Secondary: 3a Argumentation

### Deagustini_2013_RelationalDatabasesDefeasibleArgumentation
- Path: `./papers/Deagustini_2013_RelationalDatabasesDefeasibleArgumentation/`
- Content: DB-DeLP: connects DeLP to relational DBs via Target Connections + Data Source Retrieval Functions; linear scaling in DB size.
- Likely modules: `propstore/aspic.py`
- Notes: index

### Garcia_2004_DefeasibleLogicProgramming
- Path: `./papers/Garcia_2004_DefeasibleLogicProgramming/`
- Content: DeLP: logic programming + defeasible argumentation; dialectical trees; four-valued answers (YES/NO/UNDECIDED/UNKNOWN).
- Likely modules: `propstore/aspic.py`
- Notes: index

### Goldszmidt_1992_DefeasibleStrictConsistency
- Path: `./papers/Goldszmidt_1992_DefeasibleStrictConsistency/`
- Content: Polynomial-time tolerance-based consistency procedure for mixed defeasible/strict KBs; equivalent to System Z.
- Likely modules: `propstore/conflict_detector/`
- Notes: index

### Maher_2021_DefeasibleReasoningDatalog
- Path: `./papers/Maher_2021_DefeasibleReasoningDatalog/`
- Content: Compiles defeasible logic D(1,1) into Datalog-with-negation via metaprogram + unfold/fold; proven correct + linear-size.
- Likely modules: `propstore/compiler/`, `propstore/aspic.py`
- Notes: index

### Morris_2020_DefeasibleDisjunctiveDatalog
- Path: `./papers/Morris_2020_DefeasibleDisjunctiveDatalog/`
- Content: Rational/Lexicographic/Relevant Closure for Disjunctive Datalog; LM-rationality results; Datalog+ compound terms.
- Likely modules: `propstore/compiler/`
- Notes: index

## Motivation

### Aarts_2015_EstimatingReproducibilityPsychologicalScience
- Path: `./papers/Aarts_2015_EstimatingReproducibilityPsychologicalScience/`
- Content: First large-scale systematic replication of 100 psych studies; 36% significant; replication ES ~half originals.
- Likely modules: (motivation/base-rates)
- Notes: index

### Altmejd_2019_PredictingReplicabilitySocialScience
- Path: `./papers/Altmejd_2019_PredictingReplicabilitySocialScience/`
- Content: ML on 131 replications from 4 projects; 70% accuracy (AUC 0.77) predicting binary replication from basic stats features.
- Likely modules: `propstore/calibrate.py`
- Notes: index

### Begley_2012_DrugDevelopmentRaiseStandards
- Path: `./papers/Begley_2012_DrugDevelopmentRaiseStandards/`
- Content: Amgen 6/53 (11%) preclinical cancer reproduction; identifies cell-line/animal-model/publication-incentive causes.
- Likely modules: (motivation)
- Notes: index

### Border_2019_NoSupportHistoricalCandidate
- Path: `./papers/Border_2019_NoSupportHistoricalCandidate/`
- Content: Preregistered test of 18 candidate depression genes on N≤443,264; no support for any candidate or GxE interaction.
- Likely modules: (motivation — large-sample defeats small-sample)
- Notes: index

### Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments
- Path: `./papers/Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments/`
- Content: 18 experimental-econ replications AER/QJE 2011-2014; 61% replicate; mean ES 66% of originals.
- Likely modules: (motivation)
- Notes: index

### Camerer_2018_EvaluatingReplicabilitySocialScience
- Path: `./papers/Camerer_2018_EvaluatingReplicabilitySocialScience/`
- Content: 21 Nature/Science social-science replications 2010-2015; 62% replicate; prediction markets rho=0.842.
- Likely modules: (motivation — calibration priors)
- Notes: index

### Dreber_2015_PredictionMarketsEstimateReproducibility
- Path: `./papers/Dreber_2015_PredictionMarketsEstimateReproducibility/`
- Content: Prediction markets among psych researchers forecast replication; 71% accuracy; well-calibrated probabilities.
- Likely modules: (motivation)
- Notes: full

### Errington_2021_InvestigatingReplicabilityPreclinicalCancer
- Path: `./papers/Errington_2021_InvestigatingReplicabilityPreclinicalCancer/`
- Content: Reproducibility Project: Cancer Biology — 50 experiments, 23 papers; replication ES ~85% smaller; 3-82% replication rate by criterion.
- Likely modules: (motivation)
- Notes: index

### Freedman_2025_ArgumentativeLLMsClaimVerification (listed primary under 3a — noted here as Motivation adjacent)
- see 3a entry

### Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction
- Path: `./papers/Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction/`
- Content: Pooled 103-study replication forecasting; markets 73%, surveys 71%; p<0.005 replicates 76% vs 18% for weaker.
- Likely modules: `propstore/calibrate.py`
- Notes: index

### Ioannidis_2005_WhyMostPublishedResearch
- Path: `./papers/Ioannidis_2005_WhyMostPublishedResearch/`
- Content: Bayesian PPV model of research findings; six corollaries; most claimed findings likely false under typical designs.
- Likely modules: (motivation — base rates)
- Notes: index

### Klein_2018_ManyLabs2Investigating
- Path: `./papers/Klein_2018_ManyLabs2Investigating/`
- Content: Many Labs 2: 28 findings, 125 samples, 36 countries, N=15,305; 54% replicate; variation attributable to effect, not sample.
- Likely modules: (motivation)
- Notes: index

### Nosek_2020_WhatIsReplication
- Path: `./papers/Nosek_2020_WhatIsReplication/`
- Content: Redefines replication as "any study whose outcome would be diagnostic evidence about a prior claim."
- Likely modules: (motivation/foundational definition)
- Notes: full

### Raff_2021_QuantifyingReproducibleMLResearch
- Path: `./papers/Raff_2021_QuantifyingReproducibleMLResearch/`
- Content: Cox PH + XGBoost survival analysis of 255 ML papers' reproducibility; Cix readability and pseudo-code strongest predictors.
- Likely modules: (motivation)
- Notes: index

### Yang_2020_EstimatingDeepReplicabilityScientific
- Path: `./papers/Yang_2020_EstimatingDeepReplicabilityScientific/`
- Content: ML model combining word2vec narrative features + reported stats; 0.65-0.78 accuracy; text features outperform stats.
- Likely modules: `propstore/calibrate.py`, `propstore/embed.py`
- Notes: index

### Swanson_1986_UndiscoveredPublicKnowledge
- Path: `./papers/Swanson_1986_UndiscoveredPublicKnowledge/`
- Content: (No notes.md) Swanson's classic "undiscovered public knowledge": A→B and B→C implicit in disjoint literatures yield novel A→C hypotheses (Raynaud/fish-oil).
- Likely modules: (motivation — literature-based discovery)
- Notes: stub (metadata.json + paper.pdf)

### Swanson_1996_UndiscoveredPublicKnowledgeTenYearUpdate
- Path: `./papers/Swanson_1996_UndiscoveredPublicKnowledgeTenYearUpdate/`
- Content: (No notes.md) Ten-year update on ABC model of literature-based discovery; magnesium/migraine and other validated hypotheses.
- Likely modules: (motivation)
- Notes: stub (metadata.json + paper.pdf)

## Unclassified

### Greenberg_2009_CitationDistortions
- Note: Classified under 3c Revision above because its taxonomy maps to stance validation and provenance revision. Secondary: Motivation. Not truly unclassified — placed in 3c.

### Horowitz_2021_EpiPen
- Classified under 3e Reasoning infra (Z3-based DSL) but epistemic logic / modal reasoning is adjacent to argumentation. Left in 3e.

### Karacapilidis_2001_ComputerSupportedArgumentationCollaborative
- Classified under 3a (argumentation core) but is more of a systems/CSCW paper than formal theory — no clean module fit in `propstore/`.

### McBurney_2009_DialogueGamesAgentArgumentation
- Classified under 3a but no dialogue-system module exists in `propstore/` — may be aspirational/background only.

### Prakken_2006_FormalSystemsPersuasionDialogue
- Same as above — dialogue-game paper with no dialogue module in `propstore/`.

### Rahwan_2009_ArgumentationArtificialIntelligence
- Handbook reference; no single module; classified under 3a as background.

### Verheij_2003_ArtificialArgumentAssistants
- Classified under 3a as background (argument-assistant systems); no UI/assistant module in `propstore/`.

### Eskandari_2016_OnlineStreamingFeatureSelection
- Classified under 3e but only metadata present and relevance to propstore is unclear. Possibly only relevant to a feature-selection pipeline for `embed.py` or `classify.py` — flag for review.

## Surprises

1. **Clark_2014 appears in two directories** — `Clark_2014_Micropublications/` and `Clark_2014_MicropublicationsSemanticModel/`. Both contain notes.md. Directly duplicates the same paper.
2. **Popescu_2024 appears three times** — `Popescu_2024_ProbabilisticArgumentationConstellation`, `Popescu_2024_AdvancingAlgorithmicApproachesProbabilistic`, `Popescu_2024_AlgorithmicProbabilisticArgumentationConstellation`. The first two share one notes.md (via index only) and one is stub; the KR 2024 content appears under multiple names.
3. **Sensoy_2018 appears twice** — `Sensoy_2018_EvidentialDeepLearningQuantify` (stub) and `Sensoy_2018_EvidentialDeepLearningQuantifyClassification` (index entry). Likely preprint vs final/classification variant of the same paper.
4. **Gaggl_2012 / Gaggl_2013** — 2012 dir has no notes, 2013 dir has index entry. Appears the 2012 directory is an earlier-year duplicate of the same paper (index says "Published 2013").
5. **Eskandari_2016_OnlineStreamingFeatureSelection** — only metadata, no paper.pdf and no notes.md; unclear how this relates to any cluster. Feels out-of-domain for propstore; flag for removal or relevance review.
6. **Halpern_2000 vs Halpern_2005** — both directories present for what appears to be the same Halpern-Pearl Part I paper (notes.md in 2000 dir has 2005 metadata). Index lists only 2005; 2000 dir is the one with notes.
7. **Rahwan_2009_ArgumentationArtificialIntelligence** — a full edited handbook stub-present on disk but not in index, and no obvious module — it's a reference anchor, not a load-bearing citation.
8. **Halpern_2000 has notes that claim Halpern_2005 metadata** — the 2000-labelled directory's notes.md says "year: 2005, journal: British Journal for the Philosophy of Science 56(4), 843-887" — the dirname and notes.md disagree.

## Stub / missing notes flagged for future processing

The following papers on disk have no `notes.md` (only metadata.json and/or paper.pdf/pngs) and should be prioritized for paper-process runs:

- `Bench-Capon_2003_PersuasionPracticalArgumentValue-based` (metadata.json only) — foundational VAF paper
- `Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault` (metadata.json + paper.pdf) — seminal ABA
- `Buneman_2001_CharacterizationDataProvenance` (metadata.json only) — foundational provenance
- `Carroll_2005_NamedGraphsProvenanceTrust` (metadata.json only) — named graphs foundational
- `Charwat_2015_MethodsSolvingReasoningProblems` (no notes.md; abstract/claims/description present) — methods survey
- `Cousot_1977_AbstractInterpretation` (paper.pdf only) — foundational
- `Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation` (paper.pdf + pngs) — FPT foundational
- `Eskandari_2016_OnlineStreamingFeatureSelection` (metadata.json only) — relevance unclear
- `Gaggl_2012_CF2ArgumentationSemanticsRevisited` (pngs only) — possibly duplicate of 2013
- `Gruber_1993_OntologyDesignPrinciples` (paper.pdf + pngs) — foundational ontology principles
- `Guha_1991_ContextsFormalization` (paper.pdf + pngs + chunks) — foundational contexts
- `Guha_1991_ContextsFormalizationApplications` (paper.pdf + pngs + chunks) — foundational contexts
- `Kennedy_1997_RelationalParametricityUnitsMeasure` (metadata.json + paper.pdf) — units of measure
- `Mahmood_2025_Structure-AwareEncodingsArgumentationProperties` (abstract/claims/description present; no notes.md)
- `Odekerken_2022_StabilityRelevanceIncompleteArgumentation` (metadata.json only) — earlier Odekerken paper
- `Pierce_2002_TypesProgrammingLanguages` (metadata.json + paper.pdf) — TAPL textbook
- `Popescu_2024_AdvancingAlgorithmicApproachesProbabilistic` (metadata.json + paper.pdf) — companion paper
- `Prakken_2012_ClarifyingSomeMisconceptionsASPICplusFramework` (paper.pdf + pngs)
- `Rahwan_2009_ArgumentationArtificialIntelligence` (metadata.json + paper.pdf) — handbook
- `Sarkar_2004_Nanopass` (metadata.json + paper.pdf)
- `Sensoy_2018_EvidentialDeepLearningQuantify` (metadata.json + paper.pdf) — probable duplicate
- `Swanson_1986_UndiscoveredPublicKnowledge` (metadata.json + paper.pdf)
- `Swanson_1996_UndiscoveredPublicKnowledgeTenYearUpdate` (metadata.json + paper.pdf)
- `Toni_2014_TutorialAssumption-basedArgumentation` (metadata.json only) — ABA tutorial
- `Verheij_2003_ArtificialArgumentAssistants` (paper.pdf + pngs)
- `Vreeswijk_1997_AbstractArgumentationSystems` (metadata.json only) — foundational structured arg
