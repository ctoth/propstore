---
title: "A classification system for argumentation schemes"
authors: "Douglas Walton, Fabrizio Macagno"
year: 2015
venue: "Argument & Computation"
doi_url: "https://doi.org/10.1080/19462166.2015.1123772"
pages: 28
---

# A Classification System for Argumentation Schemes

## One-Sentence Summary
Provides a hierarchical taxonomy of argumentation schemes organized by source-dependency, reasoning type, and inferential structure, with formal premise-conclusion representations for each scheme and associated critical questions, designed to support argument mining and computational argumentation tools.

## Problem Addressed
Existing classifications of argumentation schemes (Kienpointner, Walton, Grennan, etc.) were fragmented and used inconsistent organizing principles, making it difficult to systematically identify, categorize, and computationally process argument types in natural language discourse.

## Key Contributions
- A unified classification system that integrates and extends prior taxonomies (Kienpointner 1992, Walton 1996, Walton et al. 2008)
- A hierarchical tree structure (Figure 4) organizing all major argumentation schemes
- Formal premise-conclusion representations for each scheme with associated critical questions
- Six desiderata for evaluating classification systems for argumentation schemes
- Analysis of how schemes relate to each other (sub-scheme relationships, hybrid schemes)
- Connection between classification and argument mining applications

## Methodology
The paper surveys existing classification systems, identifies their strengths and weaknesses, proposes organizing principles (source-dependency, epistemic vs practical, rule-based vs case-based), and constructs a hierarchical taxonomy. The system was empirically tested by having six participants classify 388 collected arguments into the proposed categories.

## Classification Taxonomy (Table 1, Figure 4)

### Top-Level Division: Defeasible Argumentation Schemes

**1. Source-Based Schemes (Non-Source-Independent)**
Arguments whose strength depends on the characteristics of the source.

- **Arguments from Popular Acceptance**
  - Argument from popular opinion
  - Argument from popular practice
  - Defeasible rule-based arguments (argument from precedent, argument from example, argument from analogy)

- **Ad Hominem Arguments**
  - Direct ad hominem
  - Circumstantial ad hominem
  - Argument from inconsistent commitment
  - Poisoning the well / ad hominem
  - Poisoning the well by alleging group bias

- **Arguments from Position to Know**
  - Argument from expert opinion
  - Argument from position to know
  - Argument from witness testimony

**2. Source-Independent Schemes (Epistemic Reasoning)**

- **Discovery Arguments**
  - Arguments establishing rules (argument from best explanation, argument from ignorance, argument from sign, argument from gradualism)
  - Arguments finding entities (argument from a random sample to a population)

- **Chained Arguments Connecting Rules and Cases**
  - Precedent-based (precedent slippery slope argument, sorites slippery slope argument)
  - Argument from verbal classification

- **Applying Rules to Cases**
  - Arguments based on cases (argument from cause to effect, argument from an established rule)
  - Argument from evidence to a hypothesis

**3. Practical Reasoning**

- **Instrumental Argument from Practical Reasoning**
  - Argument from action to motive
  - Argument from waste (sunk costs argument)
  - Argument from threat

- **Value-Based Argument from Practical Reasoning**
  - Arguments from positive or negative consequences

- **Argument from Values**
  - Argument from fairness

## Key Scheme Definitions

### Argument from Expert Opinion (Source-Based)
- MAJOR PREMISE: Source E is an expert in subject domain S containing proposition A.
- MINOR PREMISE: E asserts that proposition A (in domain S) is true (false).
- CONCLUSION: A may plausibly be taken to be true (false).

### Argument from Position to Know
- MAJOR PREMISE: Source a is in a position to know about things in a subject domain S containing proposition A.
- MINOR PREMISE: a asserts that A is true (false).
- CONCLUSION: A is true (false).

### Argument from Inconsistent Commitment
- PREMISE: a is committed to proposition A (based on what a has said or what a is committed to).
- PREMISE: Other evidence shows that a is committed to not-A (the opposite/negation of A, or to something inconsistent with A).
- CONCLUSION: a's commitments are inconsistent.

### Argument from Waste (Sunk Cost)
- PREMISE: If a stops trying to realize A now, all a's previous efforts to realize A will be wasted.
- CONCLUSION: a should continue trying to realize A.

### Argument from Commitment
- PREMISE: In the past, a has been committed to A.
- CONCLUSION: a is still committed to A.

### Scheme for Practical Reasoning (Goal-Directed)
- MAJOR PREMISE: I have a goal G.
- MINOR PREMISE: Carrying out this action A is a means to realize G.
- CONCLUSION: Therefore, I ought (practically speaking) to carry out this action A.

### Value-Based Practical Reasoning
- PREMISE: Value V is positive as judged by agent A.
- PREMISE: If X is true/occurs, it is a reason for attracting commitment to goal G.
- CONCLUSION: V is a reason for A to commit to goal G.

### Argument from Negative Value
- PREMISE: Value V is negative as judged by agent A.
- PREMISE: If X is true/occurs, it is a reason for retracting commitment to goal G.
- CONCLUSION: V is a reason for A to retract commitment to goal G.

### Argument from Established Rule
- MAJOR PREMISE: If carrying out types of actions including the state of affairs A is the established rule for x, then A is the case.
- MINOR PREMISE: Carrying out types of actions including the state of affairs A is the established rule for x.
- CONCLUSION: Therefore A must carry on A.

### Argument from Precedent
- PREMISE: There is a precedent with A, B, C, ..., as features, relevant for conclusion Z.
- PREMISE: This case also matches the features A, B, C, ...
- CONCLUSION: Z can be drawn.

### Analogical Following of a Precedent
- MODUS PONENS: If all the conditions of a rule are fulfilled, the conclusion of the rule may be drawn.
- PREMISE: Rule R applies to facts P if case C obtains.
- CASE: In case C, condition A obtains.
- CONCLUSION: Z can be drawn.

### Argument from Correlation to Cause
- PREMISE: There is a positive correlation between A and B.
- CONCLUSION: A causes B (or B causes A, or there is some common cause).

### Argument from Sign
- PREMISE: A (a finding) is true in this situation.
- CONCLUSION: B is true in this situation.

### Argument from Ignorance (Lack of Evidence)
- MAJOR PREMISE: If A were true, A would be known to be true.
- MINOR PREMISE: A is not known to be true.
- CONCLUSION: A is not true.

### Argument from Best Explanation (Abductive)
- PREMISE: F is a finding or given set of facts.
- PREMISE: E is a satisfactory explanation of F.
- PREMISE: No alternative explanation E' given so far is as satisfactory as E.
- CONCLUSION: Therefore, E is a hypothesis.

### Argument from Example
- PREMISE: In this case, the individual a has property F and also has property G.
- CONCLUSION: Rule: if x has property F, x has also has property G.

### Argument from Analogy
- PREMISE: a has features f1, f2, ...fn.
- PREMISE: b has features f1, f2, ...fn.
- CONCLUSION: a and b should be treated in the same way with respect to f1, f2, ...fn.

## Desiderata for Classification Systems
1. A classification system should be helpful to users for the task of attempting to identify which scheme fits a given argument
2. A classification system should help users deal with borderline cases (where two or more schemes could apply)
3. Should handle new schemes that are not already in the system
4. A classification system should look at finer distinctions within groups
5. A classification system should be more complex than a simple list (hierarchical)
6. Differences in classification should reflect differences in use

## Empirical Study
- Six participants classified 388 collected arguments
- Not fit any of the 14 schemes: the original list was supplemented with some other schemes
- Study in Ontario on arguments used in election campaigns
- Categories found: arguments from expert opinion, argument from sign, argument from example, argument from commitment, argument from popular opinion, argument from consequences, argument from analogy, argument from ignorance, and others
- 14 argument types identified with frequencies

## Parameters

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Number of classified schemes | - | - | ~28 | - | In the complete taxonomy (Table 1 + Figure 4) |
| Number of top-level categories | - | - | 4 | - | Source-independent, source-dependent, practical reasoning, rules to cases |
| Number of desiderata | - | - | 6 | - | Criteria for evaluating classification systems |
| Number of empirical arguments classified | - | - | 388 | - | From Ontario election campaign study |
| Number of participants in study | - | - | 6 | - | Who classified the arguments |

## Figures of Interest
- **Fig 1 (page 13):** The M argument visualized using Araucaria - shows argument from inconsistent commitment with argument diagram nodes
- **Fig 2 (page 14):** Argument diagram for SC (sunk cost) argument
- **Fig 3 (page 15):** Two sides of the SC argument - shows conflict between argument from waste and argument from positive values
- **Fig 4 (page 23):** Full classification tree of argumentation schemes - the main taxonomic contribution of the paper. Hierarchical tree from top-level categories down to individual schemes

## Results Summary
- The classification system captures most of the important schemes studied in the argumentation literature
- The system is hierarchical and extensible (new schemes can be added)
- Empirical testing with 388 arguments showed the system can handle real-world argument classification
- Some schemes are hybrid (e.g., argument from SC combines practical reasoning and commitment)
- The system distinguishes source-dependent from source-independent schemes at the top level

## Limitations
- The authors acknowledge not having resources to do extensive empirical testing
- The system needs to be refined as it is integrated with new developments
- Classification is not yet complete - more sub-types need to be added
- Some borderline cases remain difficult to classify
- The paper focuses on building the classification system rather than on testing/validating it empirically at scale
- Rules-based arguments category needs further development (connecting to legal AI, classical tradition, recent developments)

## Testable Properties
- Every argumentation scheme should have a unique premise-conclusion structure
- Every scheme should be classifiable under exactly one branch of the taxonomy tree
- Sub-schemes should inherit the properties of their parent category
- Critical questions for each scheme should map to potential counterarguments
- The classification should be exhaustive for previously catalogued schemes (Walton et al. 2008)

## Relevance to Project
This paper provides the canonical taxonomy for argumentation schemes that is directly relevant to propstore's claim/argument representation system. The hierarchical classification can inform how argument types are organized and identified in the knowledge base. The formal premise-conclusion structures for each scheme provide templates for structured claim representation. The connection to argument mining makes this directly applicable to automated argument extraction and classification.

## Open Questions
- [ ] How does this taxonomy interact with ASPIC+ framework (Modgil & Prakken 2014)?
- [ ] Can the hierarchical structure be encoded as a scheme ontology for computational use?
- [ ] How do the critical questions map to attack relations in abstract argumentation?
- [ ] What is the relationship between this classification and the Argument Interchange Format?

## Related Work Worth Reading
- Walton, D., Reed, C., & Macagno, F. (2008). Argumentation schemes. Cambridge University Press. [The foundational reference for the schemes being classified]
- Kienpointner, M. (1992). Alltagslogik. [Major prior classification system]
- Rahwan, I., et al. (2011). Argumentation schemes in the Argument Interchange Format
- Baroni, P., Besnard, P., Reed, C., Walton, D., & Abeldi (2013). Description of AIF
- Bex, F. & Reed, C. (2011). Schemes of inference, conflict, and preference
- Macagno, F. & Walton, D. (2014). Argumentation schemes and topical relations
- Palau, R. M. & Moens, M. F. (2009). Argumentation mining (argument mining of legal texts)

## Collection Cross-References

### Already in Collection
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — cited as Modgil & Prakken (2014); ASPIC+ provides the structured argumentation framework that can instantiate the schemes classified here, modeling them as defeasible inference rules
- [[Pollock_1987_DefeasibleReasoning]] — cited as Pollock (2001); Pollock's defeasible reasoning with rebutting/undercutting defeaters provides the epistemological foundation for the defeasible nature of argumentation schemes
- [[Dung_1995_AcceptabilityArguments]] — not directly cited but foundational; Dung's abstract argumentation semantics underpin the evaluation of arguments constructed from these schemes
- [[Verheij_2003_ArtificialArgumentAssistants]] — cited; discusses argument assistants and the argumentation theories behind them

### New Leads (Not Yet in Collection)
- Walton, D., Reed, C., & Macagno, F. (2008) — "Argumentation schemes" — The foundational reference containing the full catalogue of 60+ schemes that this paper classifies
- Kienpointner, M. (1992) — "Alltagslogik" — Major prior classification system with three-directional taxonomy
- Rahwan, I. et al. (2011) — "Representation of argument schemes in the Argument Interchange Format" — Computational representation of schemes in AIF
- Palau, R. M. & Moens, M. F. (2009) — "Argumentation mining" — Foundational paper on argument mining from legal texts
- Bex, F. & Reed, C. (2011) — "Schemes of inference, conflict, and preference" — Classification into inference and conflict schemes

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found — this paper postdates most collection papers; Modgil 2014 cites earlier Walton works but not this 2015 paper specifically)

### Conceptual Links (not citation-based)
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — **Strong.** ASPIC+ provides the formal mechanism to instantiate these argumentation schemes computationally: each scheme's premise-conclusion structure maps to a defeasible inference rule in ASPIC+, and each scheme's critical questions map to the three attack types (undermining, rebutting, undercutting). The classification here answers "what kinds of arguments exist" while ASPIC+ answers "how to construct and evaluate them formally."
- [[Dung_1995_AcceptabilityArguments]] — **Moderate.** Dung's abstract framework provides the semantics for evaluating arguments built from schemes. The schemes are at a higher level of abstraction (argument types with internal structure) while Dung operates at the abstract level (arguments as atomic entities with attack relations). The classification provides the bridge between natural language arguments and abstract argumentation.
- [[Pollock_1987_DefeasibleReasoning]] — **Moderate.** Pollock's distinction between rebutting and undercutting defeaters maps to how critical questions function in argumentation schemes: some CQs attack the conclusion directly (rebutting) while others attack the inferential link (undercutting).
- [[Clark_2014_Micropublications]] — **Moderate.** Micropublications model scientific claims with support/challenge relations. The argumentation schemes classified here provide a taxonomy for the types of support relations (argument from expert opinion, argument from sign, argument from analogy, etc.) that could be used to type the edges in a micropublication network.
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — **Strong.** Mayer et al. provide a computational argument mining pipeline that detects exactly the kinds of argument structures Walton classifies: evidence-to-claim support patterns in clinical trial abstracts correspond to specific scheme types in Walton's hierarchy. Walton provides the theoretical taxonomy of "what kinds of arguments exist" while Mayer provides transformer-based NLP methods for automatically detecting them in domain text, demonstrating practical realization of scheme-aware argument mining.
