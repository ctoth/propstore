---
title: "Argumentative XAI: A Survey"
authors: "Kristijonas Čyras, Antonio Rago, Emanuele Albini, Pietro Baroni, Francesca Toni"
year: 2021
venue: "IJCAI 2021 Survey Track"
doi_url: "https://doi.org/10.24963/ijcai.2021/600"
---

# Argumentative XAI: A Survey

## One-Sentence Summary
Comprehensive survey of how computational argumentation frameworks are used to provide explanations in AI systems, cataloguing approaches by explanation type (intrinsic vs post-hoc), argumentation framework used, and form of explanation delivery.

## Problem Addressed
XAI approaches have proliferated but the specific role of computational argumentation — whose dialectical structure naturally aligns with explanation as a reasoning activity — has not been systematically surveyed. This paper fills that gap by cataloguing the literature on AF-based explanations and identifying open research directions. *(p.1)*

## Key Contributions
- Catalogue of AF-based explanation literature organized by explained model type and argumentation framework used *(p.1)*
- Survey of prevalent forms that AF-based explanations take (sub-graphs, dialogues, extensions, structure-based, change-based) *(p.1)*
- Taxonomy dividing approaches into intrinsic, complete post-hoc, and approximate post-hoc *(p.1)*
- Roadmap for future work covering explanation properties, computational complexity, and ML application expansion *(p.1)*

## Methodology
Literature survey organized along three dimensions: (1) the type of explanation (intrinsic vs post-hoc, with post-hoc subdivided into complete and approximate mappings), (2) the argumentation framework deployed, and (3) the form of explanation delivery. Two summary tables catalogue all surveyed works across these dimensions. *(p.1)*

## Argumentation Frameworks Surveyed

### Abstract Argumentation (AA)
AF = (Args, R⁻) where Args is a set of arguments and R⁻ ⊆ Args × Args is the attack relation. Semantics expressed through extensions E ⊆ Args satisfying dialectical constraints (conflict-freeness, admissibility, etc.). Dispute trees (DTs) provide equivalent representation of extension-based semantics and are the basis for several XAI approaches. *(p.2)*

### Bipolar Argumentation (BA)
Extends AA with a support relation R⁺ alongside attack R⁻. Various semantics reflect different support interpretations. Gradual semantics map arguments to strength values. *(p.2)*

Key variants: *(p.2)*
- **Support Argumentation (SA)**: BA with empty attack relations
- **Quantitative Bipolar Argumentation (QBA)**: incorporates intrinsic strength values τ(a) for base-score arguments
- **Tripolar Argumentation (TA)**: adds neutralizing relations
- **Generalised Argumentation (GA)**: accommodates multiple dialectical relations
- **Abstract Dialectical Frameworks (ADFs)**: allow generalised relations with user-specified acceptance conditions

### Structured Argumentation
- **ABA (Assumption-Based Argumentation)**: arguments as deductions from assumptions using rules *(p.2)*
- **ASPIC+**: arguments from strict and defeasible rules *(p.2)*
- **DeLP (Defeasible Logic Programming)**: uses dialectical trees similar to DTs *(p.2)*

### Specialized AA Instances
- **AA-CBR**: case-based reasoning with arguments as cases *(p.2)*
- **AA-ALP**: abductive logic programming deductions *(p.2)*
- **AA-LD**: logical deductions from rules *(p.2)*
- **AA-AS**: argument schemes *(p.2)*

## Types of Argumentative Explanations

### 3.1 Intrinsic Approaches *(p.3)*
Models that natively use argumentation as their reasoning mechanism:

| Domain | Work | Framework | Notes |
|--------|------|-----------|-------|
| Recommender Systems | Briguez et al. 2014 | DeLP | Movie recommendations, handles incompleteness |
| Recommender Systems | Rodríguez et al. 2017 | DeLP | Hybrid educational recommenders |
| Recommender Systems | Cocarascu et al. 2019 | QBA | Review aggregation with conversational explanations |
| Classification | Čyras et al. 2019a | AA-CBR | Case-based legislative outcome classification |
| Classification | Cocarascu et al. 2020 | AA-CBR | Binary classification with unstructured data |
| Decision Making | Amgoud and Prade 2009 | AA | Pro/con argument evaluation |
| Decision Making | Brarda et al. 2019 | AA | Multi-criteria via conditional preference rules |
| Knowledge-Based | Kökciyan et al. 2020 | AA/ASPIC+ | Domain-specific explanations |
| Planning | Oren et al. 2020 | ASPIC+ | Domain rules translated to dialogical explanations |

### 3.2 Complete Post-Hoc Approaches *(p.3-4)*
Complete (sound/faithful) mappings between existing models and AFs:

| Domain | Work | Framework | Notes |
|--------|------|-----------|-------|
| Probabilistic | Albini et al. 2020a | QBA | PageRank → QBA, competitive link effects |
| Decision Making | Zeng et al. 2018 | ABA | Decision graphs → ABA, optimal = admissible |
| Decision Making | Zhong et al. 2019 | ABA | Decision problems → equivalent ABA |
| Knowledge-Based | Arioua et al. 2015 | AA | Datalog under inconsistency-tolerant semantics |
| Planning | Fan 2018 | ABA | Planning problems → ABA counterparts |
| Planning | Čyras et al. 2019b | AA | Scheduling → AA, feasibility/efficiency explanations |
| Logic Programming | Wakaki et al. 2009 | AA-ALP | Answer sets ↔ AA-ALP exact mapping |
| Logic Programming | Schulz and Toni 2016 | ABA | Answer set membership via ABA |

### 3.3 Approximate Post-Hoc Approaches *(p.4)*
Incomplete mappings where AF approximates model behaviour:

| Domain | Work | Framework | Notes |
|--------|------|-----------|-------|
| Recommender Systems | Rago et al. 2018 | TA | Hybrid systems, collaborative filtering |
| Recommender Systems | Rago et al. 2020 | BA | Greater explanatory repertoire |
| Classification | Sendi et al. 2019 | AA | Neural network ensemble rule extraction |
| Classification | Dejl et al. 2021 | GA | Deep argumentative explanations for NNs |
| Probabilistic | Timmer et al. 2017 | SA | Bayesian network → SA framework |
| Planning | Collins et al. 2019 | ASPIC+ | Causal relationships from plans |

## Forms of AF-Based Explanations *(p.5)*

Five distinct forms identified:

1. **Sub-graph explanations**: An explanation for acceptance status is a sub-graph of the AF satisfying formal properties. Dispute trees are popular instances with theoretical guarantees (existence, correctness, relevance). Also includes paths, cycles, branches in BA/QBA/DeLP. *(p.5)*

2. **Structure-based explanations**: In structured argumentation (ABA, ASPIC+, DeLP), the logic- or argument scheme-based structure of arguments and dialectical relations acts as explanation. *(p.5)*

3. **Dialogical explanations**: Participants engage in structured, rule-guided, goal-oriented exchange of arguments. Constructed from DTs or AFs as formal games between proponent and opponent. *(p.5)*

4. **Extension-based explanations**: Explanations are extensions themselves, keeping relationships implicit. Fan and Toni (2015b) define explanations as related admissible extensions — conflict-free sets defending all attackers of the topic argument. *(p.5)*

5. **Change-based explanations**: Addition or removal of arguments and/or relations that change acceptability status of the topic argument. Indicates what AF modifications would alter the outcome. *(p.5)*

### Presentation Formats *(p.5)*
- Natural language rendering
- Visualizations
- Conversational explanations (natural fit with dialogical structure)

## Roadmap for Future Work *(p.6)*

### Properties
AF properties are well-studied but explanation properties remain understudied. Notable exceptions: fidelity (sound/complete mappings) and extension-based semantics. Desirable XAI properties like cognitive tractability, transparency, and trust need investigation, likely requiring human-user experiments. *(p.6)*

### Computational Aspects
- Intrinsic approaches need efficient reasoning systems
- Tractable membership reasoning for grounded AA extensions supports efficient intrinsic approaches
- Post-hoc approaches face extraction overhead before explanation derivation
- Systematic complexity investigation needed across AF types and explanation formats *(p.6)*

### Extending Applications
- ML represents strongest current XAI demand but AF-based explanations sparsely deployed in ML settings
- Connection opportunities: logic-based explanations as AF-based, integrating counterfactual explanations with AF approaches, relation-based counterfactuals via suitable AFs *(p.6)*

## Figures of Interest
- **Fig 1 (p.2)**: Three representations of an AA framework — (i) graph with grounded extension, (ii) dispute tree, (iii) dialogical proponent/opponent exchange
- **Fig 2 (p.3)**: Intrinsic AF-based explanation for recommender system (Briguez et al. 2014) showing DeLP dialectical trees for movie recommendations
- **Fig 3 (p.3)**: Complete post-hoc explanation for PageRank via QBA (Albini et al. 2020a) showing how link structure translates to argument graph with strength values
- **Fig 4 (p.4)**: Complete post-hoc AA-based explanation for scheduling (Čyras et al. 2019b)
- **Fig 5 (p.4)**: Approximate post-hoc AA-based explanation for recommendation via TA framework
- **Fig 6 (p.4)**: Approximate post-hoc SA framework extracted from Bayesian network Markov blanket (Timmer et al. 2017)
- **Table 1 (p.3)**: Overview of AF-based explanation approaches organized by intrinsic/complete/approximate, model category, AF type, and explanation form
- **Table 2 (p.5)**: Summary of explanation forms catalogued across all surveyed works

## Limitations
- Survey focuses on overtly argumentative approaches; does not cover all XAI methods *(p.1)*
- Does not provide empirical comparison of approaches *(p.6)*
- Properties of AF-based explanations largely understudied — most work focuses on defining explanations, not evaluating their quality *(p.6)*
- Human evaluation of argumentative explanations is sparse *(p.6)*

## Arguments Against Prior Work
- Non-argumentative XAI approaches lack the dialectical structure that matches how humans naturally reason *(p.1)*
- Existing surveys of XAI do not adequately cover argumentation-based approaches *(p.1)*
- Approximate post-hoc approaches sacrifice completeness/soundness guarantees that complete post-hoc approaches provide *(p.4)*

## Design Rationale
- Three-way taxonomy (intrinsic/complete post-hoc/approximate post-hoc) chosen because it captures the fundamental distinction in how argumentation relates to the explained model *(p.1)*
- Intrinsic = argumentation IS the model; complete post-hoc = faithful bidirectional mapping; approximate post-hoc = partial/lossy mapping *(p.1-4)*
- Five explanation forms (sub-graph, structure, dialogue, extension, change) cover all observed patterns in literature *(p.5)*

## Testable Properties
- Complete post-hoc mappings must be sound: every AF-derived explanation must correspond to a real model property *(p.3)*
- Dispute trees provide existence, correctness, and relevance guarantees for sub-graph explanations *(p.5)*
- Extension-based explanations must be conflict-free sets that defend all attackers of the topic argument *(p.5)*

## Relevance to Project
Highly relevant as a reference taxonomy for propstore's argumentation layer. The survey's classification of explanation types maps directly onto how propstore could expose its argumentation reasoning to users:
- Propstore's Dung AF and ASPIC+ layers are intrinsic argumentation; explanations could use dispute trees or dialogical forms
- The taxonomy of explanation forms (sub-graph, dialogue, extension, change) provides concrete options for rendering argumentation results
- The distinction between complete and approximate mappings is relevant for propstore's relationship between source-of-truth claims and heuristic/LLM-derived proposals
- QBA frameworks surveyed here connect to the gradual semantics work (Gabbay 2012) already in the collection

## Open Questions
- [ ] Which explanation form (sub-graph, dialogue, extension, change) is most appropriate for propstore's use case of explaining claim/stance resolution?
- [ ] Can propstore's ATMS assumption labels be surfaced as AF-based explanations?
- [ ] How do the computational complexity findings relate to propstore's scale requirements?

## Related Work Worth Reading
- **Dejl et al. 2021** — Deep argumentative explanations mapping neural networks to GA frameworks; extends argumentation-based XAI to deep learning
- **Fan and Toni 2015b** — Extension-based explanations via admissible sets; formal foundation for explanation delivery → NOW IN COLLECTION: [[Fan_2015_ComputingExplanationsArgumentation]]
- **Timmer et al. 2017** — SA framework explanations for Bayesian networks; relevant for probabilistic argumentation integration
- **Vassiliades et al. 2021** — Complementary survey on argumentation and XAI published in Knowledge Engineering Review; broader scope
- **Albini et al. 2020a** — QBA explanations for PageRank; demonstrates complete post-hoc mapping with gradual semantics

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — foundational AF = (Args, Attacks) framework; Section 2 of this survey builds directly on Dung's AA semantics
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — bipolar argumentation frameworks; Section 2 reviews BA as extension of Dung AA with support relation
- [[Besnard_2001_Logic-basedTheoryDeductiveArguments]] — deductive argumentation theory; cited as background for structured argumentation
- [[Bondarenko et al. 1997 / ABA]] — assumption-based argumentation; referenced extensively as structured argumentation framework underpinning complete post-hoc approaches
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — ASPIC+ tutorial; Section 2 references ASPIC+ as key structured argumentation framework
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — full ASPIC+ treatment with preferences; Section 2 background
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — preference-based argumentation; Amgoud and Prade 2009 (related work) cited for argumentative decision making
- [[Amgoud_2008_BipolarityArgumentationFrameworks]] — bipolarity in AFs; provides theoretical foundation for BA frameworks surveyed in Section 2
- [[Gabbay_2012_EquationalApproachArgumentationNetworks]] — equational/gradual semantics for AFs; connects to QBA gradual semantics discussed in Section 2
- [[Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation]] — principled evaluation of AF semantics; Baroni et al. 2018/2019 (related) cited for gradual argumentation properties
- [[Fan_2015_ComputingExplanationsArgumentation]] — Fan and Toni 2015b; central to survey's treatment of extension-based explanations (Section 4), defines explanations as related admissible extensions
- [[Caminada_2006_IssueReinstatementArgumentation]] — reinstatement labellings; underpins the dispute tree / extension semantics used throughout the survey
- [[Brewka_1989_PreferredSubtheoriesExtendedLogical]] — Brewka and Woltran 2010 (related) cited for Abstract Dialectical Frameworks
- [[Bonzon_2016_ComparativeStudyRanking-basedSemantics]] — ranking-based semantics; connects to gradual semantics surveyed in Section 2
- [[Rago_2016_DiscontinuityFreeQuAD]] — DF-QuAD algorithm for quantitative argumentation debates; surveyed as a QBA gradual semantics approach for decision support

### New Leads (Not Yet in Collection)
- Dejl et al. (2021) — "Argflow: A toolkit for deep argumentative explanations for neural networks" — most advanced AF-based XAI for deep learning via GA frameworks
- Timmer et al. (2017) — "A two-phase method for extracting explanatory arguments from bayesian networks" — SA framework for probabilistic model explanation
- Vassiliades et al. (2021) — "Argumentation and Explainable Artificial Intelligence: A Survey" — complementary broader-scope XAI+argumentation survey in Knowledge Engineering Review
- Miller (2019) — "Explanation in artificial intelligence: Insights from the social sciences" — social science grounding for why argumentation matches human explanation patterns
- Albini et al. (2020a) — "Pagerank as an argumentation semantics" — complete post-hoc QBA mapping for PageRank

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Halpern_2005_CausesExplanationsStructuralModel]] — Halpern's structural-model approach to causality and explanation provides a formal causality framework; this survey identifies counterfactual explanations as a key future direction for AF-based XAI integration (Section 5), and Halpern's model is a leading counterfactual formalism
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — Odekerken's work on ASPIC+ with incomplete information is directly relevant to the survey's discussion of intrinsic approaches using structured argumentation under uncertainty; the survey's roadmap calls for expanding AF-based explanations to handle incomplete settings
- [[Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible]] — LLM-ASPIC+ is a concrete realization of the survey's roadmap vision for integrating AF-based explanations with ML; the survey calls for deeper ML-argumentation integration and Fang 2025 delivers a neuro-symbolic approach using ASPIC+
