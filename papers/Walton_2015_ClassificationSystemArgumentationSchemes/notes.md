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
Provides a hierarchical taxonomy of argumentation schemes organized by source-dependency, reasoning type, and inferential structure, with formal premise-conclusion representations for each scheme and associated critical questions, designed to support argument mining and computational argumentation tools. *(p.1)*

## Problem Addressed
Existing classifications of argumentation schemes (Kienpointner, Walton, Grennan, etc.) were fragmented and used inconsistent organizing principles, making it difficult to systematically identify, categorize, and computationally process argument types in natural language discourse. *(p.1-2)*

## Key Contributions
- A unified classification system that integrates and extends prior taxonomies (Kienpointner 1992, Walton 1996, Walton et al. 2008) *(p.1, p.22)*
- A hierarchical tree structure (Figure 4) organizing all major argumentation schemes *(p.23)*
- Formal premise-conclusion representations for each scheme with associated critical questions *(p.10-21)*
- Six desiderata for evaluating classification systems for argumentation schemes *(p.9)*
- Analysis of how schemes relate to each other (sub-scheme relationships, hybrid schemes) *(p.8, p.15-16)*
- Connection between classification and argument mining applications *(p.3)*

## Methodology
The paper surveys existing classification systems, identifies their strengths and weaknesses, proposes organizing principles (source-dependency, epistemic vs practical, rule-based vs case-based), and constructs a hierarchical taxonomy. *(p.4-6)* The system was empirically tested by having six participants classify 388 collected arguments into the proposed categories. *(p.7)*

## Classification Taxonomy (Table 1 p.22, Figure 4 p.23)

### Top-Level Division: Defeasible Argumentation Schemes

**1. Source-Based Schemes (Non-Source-Independent)** *(p.9, p.22)*
Arguments whose strength depends on the characteristics of the source.

- **Arguments from Popular Acceptance** *(p.22)*
  - Argument from popular opinion *(p.22)*
  - Argument from popular practice *(p.22)*
  - Defeasible rule-based arguments (argument from precedent, argument from example, argument from analogy) *(p.22)*

- **Ad Hominem Arguments** *(p.11-12, p.22)*
  - Direct ad hominem *(p.12, p.22)*
  - Circumstantial ad hominem *(p.12, p.22)*
  - Argument from inconsistent commitment *(p.11, p.22)*
  - Poisoning the well / ad hominem *(p.22)*
  - Poisoning the well by alleging group bias *(p.22)*

- **Arguments from Position to Know** *(p.10, p.22)*
  - Argument from expert opinion *(p.10, p.22)*
  - Argument from position to know *(p.10, p.22)*
  - Argument from witness testimony *(p.22)*

**2. Source-Independent Schemes (Epistemic Reasoning)** *(p.17, p.22)*

- **Discovery Arguments** *(p.20-21, p.22)*
  - Arguments establishing rules (argument from best explanation, argument from ignorance, argument from sign, argument from gradualism) *(p.20-21, p.22)*
  - Arguments finding entities (argument from a random sample to a population) *(p.22)*

- **Chained Arguments Connecting Rules and Cases** *(p.22)*
  - Precedent-based (precedent slippery slope argument, sorites slippery slope argument) *(p.22)*
  - Argument from verbal classification *(p.22)*

- **Applying Rules to Cases** *(p.17-19, p.22)*
  - Arguments based on cases (argument from cause to effect, argument from an established rule) *(p.17, p.22)*
  - Argument from evidence to a hypothesis *(p.22)*

**3. Practical Reasoning** *(p.13-16, p.22)*

- **Instrumental Argument from Practical Reasoning** *(p.16, p.22)*
  - Argument from action to motive *(p.22)*
  - Argument from waste (sunk costs argument) *(p.13-14, p.22)*
  - Argument from threat *(p.22)*

- **Value-Based Argument from Practical Reasoning** *(p.16, p.22)*
  - Arguments from positive or negative consequences *(p.16, p.22)*

- **Argument from Values** *(p.22)*
  - Argument from fairness *(p.22)*

**4. Schemes for Applying Rules to Cases** *(p.17-19)*
Epistemic arguments can be divided into two broad categories, depending on the relationship between the generalisation, the premises, and the conclusion. *(p.17)*

## Key Scheme Definitions

### Argument from Expert Opinion (Source-Based) *(p.10)*
- MAJOR PREMISE: Source E is an expert in subject domain S containing proposition A.
- MINOR PREMISE: E asserts that proposition A (in domain S) is true (false).
- CONCLUSION: A may plausibly be taken to be true (false).

### Argument from Position to Know *(p.10)*
- MAJOR PREMISE: Source a is in a position to know about things in a subject domain S containing proposition A.
- MINOR PREMISE: a asserts that A is true (false).
- CONCLUSION: A is true (false).

### Argument from Inconsistent Commitment *(p.11)*
- PREMISE: a is committed to proposition A (based on what a has said or what a is committed to).
- PREMISE: Other evidence shows that a is committed to not-A (the opposite/negation of A, or to something inconsistent with A).
- CONCLUSION: a's commitments are inconsistent.

### Argument from Waste (Sunk Cost) *(p.13-14)*
- PREMISE: If a stops trying to realize A now, all a's previous efforts to realize A will be wasted.
- CONCLUSION: a should continue trying to realize A.

### Argument from Commitment *(p.15)*
- PREMISE: In the past, a has been committed to A.
- CONCLUSION: a is still committed to A.

### Scheme for Practical Reasoning (Goal-Directed) *(p.16)*
- MAJOR PREMISE: I have a goal G.
- MINOR PREMISE: Carrying out this action A is a means to realize G.
- CONCLUSION: Therefore, I ought (practically speaking) to carry out this action A.

### Value-Based Practical Reasoning *(p.16)*
- PREMISE: Value V is positive as judged by agent A.
- PREMISE: If X is true/occurs, it is a reason for attracting commitment to goal G.
- CONCLUSION: V is a reason for A to commit to goal G.

### Argument from Negative Value *(p.16)*
- PREMISE: Value V is negative as judged by agent A.
- PREMISE: If X is true/occurs, it is a reason for retracting commitment to goal G.
- CONCLUSION: V is a reason for A to retract commitment to goal G.

### Argument from Established Rule *(p.17)*
- MAJOR PREMISE: If carrying out types of actions including the state of affairs A is the established rule for x, then A is the case.
- MINOR PREMISE: Carrying out types of actions including the state of affairs A is the established rule for x.
- CONCLUSION: Therefore A must carry on A.

### Argument from Precedent *(p.18)*
- PREMISE: There is a precedent with A, B, C, ..., as features, relevant for conclusion Z.
- PREMISE: This case also matches the features A, B, C, ...
- CONCLUSION: Z can be drawn.

### Analogical Following of a Precedent *(p.18)*
- MODUS PONENS: If all the conditions of a rule are fulfilled, the conclusion of the rule may be drawn.
- PREMISE: Rule R applies to facts P if case C obtains.
- CASE: In case C, condition A obtains.
- CONCLUSION: Z can be drawn.

### Argument from Correlation to Cause *(p.20)*
- PREMISE: There is a positive correlation between A and B.
- CONCLUSION: A causes B (or B causes A, or there is some common cause).

### Argument from Sign *(p.20)*
- PREMISE: A (a finding) is true in this situation.
- CONCLUSION: B is true in this situation.

### Argument from Ignorance (Lack of Evidence) *(p.21)*
- MAJOR PREMISE: If A were true, A would be known to be true.
- MINOR PREMISE: A is not known to be true.
- CONCLUSION: A is not true.

### Argument from Best Explanation (Abductive) *(p.20)*
- PREMISE: F is a finding or given set of facts.
- PREMISE: E is a satisfactory explanation of F.
- PREMISE: No alternative explanation E' given so far is as satisfactory as E.
- CONCLUSION: Therefore, E is a hypothesis.

### Argument from Example *(p.21)*
- PREMISE: In this case, the individual a has property F and also has property G.
- CONCLUSION: Rule: if x has property F, x has also has property G.

### Argument from Analogy *(p.19)*
- PREMISE: a has features f1, f2, ...fn.
- PREMISE: b has features f1, f2, ...fn.
- CONCLUSION: a and b should be treated in the same way with respect to f1, f2, ...fn.

## Desiderata for Classification Systems *(p.9)*
1. A classification system should be helpful to users for the task of attempting to identify which scheme fits a given argument *(p.9)*
2. A classification system should help users deal with borderline cases (where two or more schemes could apply) *(p.9)*
3. Should handle new schemes that are not already in the system *(p.9)*
4. A classification system should look at finer distinctions within groups *(p.9)*
5. A classification system should be more complex than a simple list (hierarchical) *(p.9)*
6. Differences in classification should reflect differences in use *(p.9)*

## Empirical Study *(p.7)*
- Six participants classified 388 collected arguments *(p.7)*
- Not fit any of the 14 schemes: the original list was supplemented with some other schemes *(p.7)*
- Study in Ontario on arguments used in election campaigns *(p.7)*
- Categories found: arguments from expert opinion, argument from sign, argument from example, argument from commitment, argument from popular opinion, argument from consequences, argument from analogy, argument from ignorance, and others *(p.7)*
- 14 argument types identified with frequencies *(p.7)*

## Survey of Prior Classification Systems

### Kienpointner (1992) *(p.4)*
- Three main directions in classification: descriptive/normative distinction, the real distinction (domain-specific vs general), and schemes as argumentation rules *(p.4)*
- Four categories: quasi-logical, based on reality, establishing reality, and discourse *(p.4)*

### Grennan (1997) *(p.4)*
- Classified schemes into four groups: quasi-logical, based on reality, establishing reality, and discourse *(p.4)*

### Walton, Reed, and Macagno (2008) *(p.4)*
- Five categories identified from Grennan and Walton's prior work, but the group "overriding" had a problematic "overriding common characteristic" *(p.4)*
- Replaced by four better categories: discovery, reasoning, argumentation, and practical reasoning *(p.4)*

### Lumer and Dove (2011) *(p.5)*
- Epistemic approach: schemes are rules for establishing an epistemic state *(p.5)*
- Practical approach: separately classified *(p.5)*

### Rahwan, Banerjee, Reed, Walton, and Abdallah (2011) *(p.5)*
- Formal description using Argument Interchange Format (AIF) *(p.5)*

### Bex and Reed (2011) *(p.5-6)*
- Three broad categories: inference schemes, conflict schemes, preference schemes *(p.6)*
- Inference schemes modeled as defeasible modus ponens or metalinguistic inference rules *(p.6)*
- Conflict schemes based on logical conflict by negation or contradiction *(p.6)*

### Macagno and Walton (2014) *(p.6)*
- Connected schemes to topical relations *(p.6)*

## Hybrid Schemes *(p.15-16)*
- The SC (sunk cost) argument is identified as a hybrid scheme: a sub-species of both argument from commitment and practical reasoning *(p.15)*
- It can be understood as a form of reasoning embedded in the scheme for the other type of argument *(p.15)*
- Argument from SC is a species of argument from commitment in which a sequence of deliberation is taking place between two choices and there is a time lapse between an earlier commitment and the time of the choice *(p.15)*

## Classifying Schemes as Sub-species *(p.8)*
- Argument from expert opinion can be classified as a subspecies of argument from position to know, since an expert is a special case of someone in a position to know *(p.8)*
- This allows hierarchical organization where specific schemes inherit properties of parent categories *(p.8)*
- Three ways to classify: according to premise dependency, according to general category, and by identifying borderline cases *(p.8)*

## Revising the Classification *(p.22, p.24)*
- The classification system originally proposed in Walton (2001, pp. 234-235) and revised in Walton et al. (2008) consisted of three main categories: reasoning arguments, source-based arguments, and arguments applying rules to cases *(p.22)*
- Under these main categories, sub-categories and individual schemes were classified *(p.22)*
- The group "overriding" was modified and replaced by four better categories *(p.22)*
- Rules-based arguments need further development connecting to legal AI, classical tradition, and recent developments *(p.22, p.24)*
- The classification is not yet complete: more sub-types need to be added *(p.24)*
- Argumentation schemes of the kind recognized in Walton, Reed and Macagno (2008) include certain classical argument forms (argument from definition, argument from genus to species, etc.) and the linguistic type of arguments called figures of speech, stemming from ancient Greek philosophy *(p.24)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of classified schemes | - | - | ~28 | - | p.22-23 | In the complete taxonomy (Table 1 + Figure 4) |
| Number of top-level categories | - | - | 4 | - | p.22 | Source-independent, source-dependent, practical reasoning, rules to cases |
| Number of desiderata | - | - | 6 | - | p.9 | Criteria for evaluating classification systems |
| Number of empirical arguments classified | - | - | 388 | - | p.7 | From Ontario election campaign study |
| Number of participants in study | - | - | 6 | - | p.7 | Who classified the arguments |
| Number of argument types identified | - | - | 14 | - | p.7 | In the empirical study |

## Figures of Interest
- **Fig 1 (p.13):** The M argument visualized using Araucaria - shows argument from inconsistent commitment with argument diagram nodes, illustrating how Medvedev's actions are inconsistent with his stated liberal commitments *(p.12-13)*
- **Fig 2 (p.14):** Argument diagram for SC (sunk cost) argument - shows how the PhD student's deliberation is structured with premises leading to the conclusion about continuing *(p.14)*
- **Fig 3 (p.15):** Two sides of the SC argument - shows conflict between argument from waste and argument from positive values, illustrating the hybrid nature of the SC scheme *(p.15)*
- **Fig 4 (p.23):** Full classification tree of argumentation schemes - the main taxonomic contribution of the paper. Hierarchical tree from top-level categories (Defeasible Argumentation Schemes splits into Practical Reasoning, Source-based Epistemic Reasoning, Non-Source-based Schemes) down to individual schemes at the leaf level *(p.23)*

## Arguments Against Prior Work

1. **Prior classifications used inconsistent organizing principles.** Kienpointner (1992) used three main directions (descriptive/normative, domain-specific/general, schemes as rules) but the categories overlapped. Grennan (1997) classified into four groups but the groupings were not mutually exclusive. *(p.4)*
2. **The "overriding" category was incoherent.** Walton, Reed, and Macagno (2008) identified five categories but the group "overriding" had a problematic "overriding common characteristic" that made the category structure unclear, requiring replacement with four better categories. *(p.4)*
3. **Flat lists fail to capture sub-scheme relationships.** Prior catalogues of schemes presented them as simple lists without hierarchical structure, failing to capture that some schemes are sub-species of others (e.g., argument from expert opinion is a subspecies of argument from position to know). *(p.8-9)*
4. **Existing classifications fail the six desiderata.** The paper identifies six criteria a classification system should satisfy (helpful for identification, handles borderline cases, accommodates new schemes, captures fine distinctions, is hierarchical not flat, reflects differences in use) and argues that no prior system fully satisfies all six. *(p.9)*
5. **Lumer and Dove's epistemic approach is too narrow.** Their approach classifies schemes only as rules for establishing epistemic states, which does not adequately handle practical reasoning schemes or source-based arguments. *(p.5)*
6. **Bex and Reed's classification serves a different purpose.** Their division into inference schemes, conflict schemes, and preference schemes is useful for formal argumentation systems but does not classify by argument type (what kind of reasoning is being used), which is what users need for identification. *(p.5-6)*
7. **The AIF approach is formal but not a classification by type.** Rahwan et al. (2011) provide a formal representation of schemes in the Argument Interchange Format, but this addresses computational encoding rather than organizing schemes by their reasoning characteristics. *(p.5)*
8. **Classical argument forms and figures of speech remain unintegrated.** Schemes from the classical Aristotelian tradition (argument from definition, argument from genus to species) and linguistic figures of speech from ancient Greek philosophy have not been systematically incorporated into modern classifications. *(p.24)*

## Design Rationale

1. **Hierarchical tree structure, not flat list.** The classification is organized as a tree (Figure 4, p.23) with multiple levels of specificity, allowing schemes to inherit properties of parent categories and making it easier to navigate from general to specific. *(p.1, p.9, p.22-23)*
2. **Source-dependency as top-level organizing principle.** The most fundamental distinction is whether an argument's strength depends on the characteristics of its source (source-based) or is independent of the source (source-independent). This reflects a deep epistemological difference in how arguments derive their force. *(p.8-9, p.22)*
3. **Practical vs. epistemic reasoning as fundamental division.** Source-independent schemes are further divided into epistemic reasoning (aimed at establishing what is true) and practical reasoning (aimed at deciding what to do). This reflects the Aristotelian distinction between theoretical and practical reason. *(p.13, p.22)*
4. **Six explicit desiderata for evaluation.** Rather than building a classification ad hoc, the paper first establishes criteria that any good classification should satisfy, then designs the system to meet them. This makes the design choices transparent and evaluable. *(p.9)*
5. **Sub-scheme inheritance.** Schemes are organized so that more specific schemes inherit the properties of their parent category. For example, argument from expert opinion inherits all the critical questions of argument from position to know, plus additional questions specific to expertise. *(p.8, p.10)*
6. **Hybrid schemes bridge categories.** Some schemes (e.g., sunk cost argument) are recognized as hybrids that combine elements of multiple categories (practical reasoning + argument from commitment). Rather than forcing them into one category, the classification acknowledges their dual nature. *(p.15-16)*
7. **Empirical grounding.** The classification was tested empirically by having six participants classify 388 collected arguments from political discourse, providing a reality check on whether the scheme types are identifiable in practice. *(p.7)*
8. **Extensibility.** The system is explicitly designed to be extended as new schemes are identified or as existing categories need further subdivision. The authors acknowledge the classification is not yet complete. *(p.24)*
9. **Connection to argument mining applications.** The classification is designed with computational argumentation in mind: automated argument mining systems need a taxonomy of argument types to classify detected arguments. *(p.3, p.24-25)*

## Results Summary
- The classification system captures most of the important schemes studied in the argumentation literature *(p.24)*
- The system is hierarchical and extensible (new schemes can be added) *(p.24)*
- Empirical testing with 388 arguments showed the system can handle real-world argument classification *(p.7)*
- Some schemes are hybrid (e.g., argument from SC combines practical reasoning and commitment) *(p.15)*
- The system distinguishes source-dependent from source-independent schemes at the top level *(p.9, p.22)*
- Modus ponens exceptions can be used to model defeasible inferences (e.g., the Tweety argument: if Tweety is a bird, Tweety flies; but Tweety is a penguin) *(p.22)*

## Limitations
- The authors acknowledge not having resources to do extensive empirical testing *(p.25)*
- The system needs to be refined as it is integrated with new developments *(p.24)*
- Classification is not yet complete - more sub-types need to be added *(p.24)*
- Some borderline cases remain difficult to classify *(p.8, p.24)*
- The paper focuses on building the classification system rather than on testing/validating it empirically at scale *(p.24-25)*
- Rules-based arguments category needs further development (connecting to legal AI, classical tradition, recent developments) *(p.22, p.24)*
- Classical argument forms (argument from definition, argument from genus to species) and figures of speech from ancient Greek philosophy are acknowledged but not fully integrated *(p.24)*

## Testable Properties
- Every argumentation scheme should have a unique premise-conclusion structure *(p.10-21)*
- Every scheme should be classifiable under exactly one branch of the taxonomy tree *(p.22-23)*
- Sub-schemes should inherit the properties of their parent category *(p.8)*
- Critical questions for each scheme should map to potential counterarguments *(p.11)*
- The classification should be exhaustive for previously catalogued schemes (Walton et al. 2008) *(p.22, p.24)*
- The six desiderata should be satisfied by any adequate classification system *(p.9)*

## Relevance to Project
This paper provides the canonical taxonomy for argumentation schemes that is directly relevant to propstore's claim/argument representation system. The hierarchical classification can inform how argument types are organized and identified in the knowledge base. The formal premise-conclusion structures for each scheme provide templates for structured claim representation. The connection to argument mining makes this directly applicable to automated argument extraction and classification. *(p.1, p.3, p.24)*

## Open Questions
- [ ] How does this taxonomy interact with ASPIC+ framework (Modgil & Prakken 2014)?
- [ ] Can the hierarchical structure be encoded as a scheme ontology for computational use?
- [ ] How do the critical questions map to attack relations in abstract argumentation?
- [ ] What is the relationship between this classification and the Argument Interchange Format?

## Related Work Worth Reading
- Walton, D., Reed, C., & Macagno, F. (2008). Argumentation schemes. Cambridge University Press. [The foundational reference for the schemes being classified] *(p.1, cited throughout)*
- Kienpointner, M. (1992). Alltagslogik. [Major prior classification system] *(p.4)*
- Rahwan, I., et al. (2011). Argumentation schemes in the Argument Interchange Format *(p.5)*
- Baroni, P., Besnard, P., Reed, C., Walton, D., & Abeldi (2013). Description of AIF *(p.5)*
- Bex, F. & Reed, C. (2011). Schemes of inference, conflict, and preference *(p.5-6)*
- Macagno, F. & Walton, D. (2014). Argumentation schemes and topical relations *(p.6)*
- Palau, R. M. & Moens, M. F. (2009). Argumentation mining (argument mining of legal texts) *(p.3)*
- Lumer, C. & Dove, I. (2011). Epistemic approach to argumentation schemes *(p.5)*
- Grennan, W. (1997). Informal logic *(p.4)*
- Atkinson, K., Bench-Capon, T. (2007). Practical reasoning and actions *(p.13)*
- Westberg (2002). Goal-directed reasoning and practical arguments *(p.13)*

## Collection Cross-References

### Already in Collection
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — cited as Modgil & Prakken (2014); ASPIC+ provides the structured argumentation framework that can instantiate the schemes classified here, modeling them as defeasible inference rules *(p.5)*
- [[Pollock_1987_DefeasibleReasoning]] — cited as Pollock (2001); Pollock's defeasible reasoning with rebutting/undercutting defeaters provides the epistemological foundation for the defeasible nature of argumentation schemes *(p.5)*
- [[Dung_1995_AcceptabilityArguments]] — not directly cited but foundational; Dung's abstract argumentation semantics underpin the evaluation of arguments constructed from these schemes
- [[Verheij_2003_ArtificialArgumentAssistants]] — cited; discusses argument assistants and the argumentation theories behind them

### New Leads (Not Yet in Collection)
- Walton, D., Reed, C., & Macagno, F. (2008) — "Argumentation schemes" — The foundational reference containing the full catalogue of 60+ schemes that this paper classifies *(cited throughout)*
- Kienpointner, M. (1992) — "Alltagslogik" — Major prior classification system with three-directional taxonomy *(p.4)*
- Rahwan, I. et al. (2011) — "Representation of argument schemes in the Argument Interchange Format" — Computational representation of schemes in AIF *(p.5)*
- Palau, R. M. & Moens, M. F. (2009) — "Argumentation mining" — Foundational paper on argument mining from legal texts *(p.3)*
- Bex, F. & Reed, C. (2011) — "Schemes of inference, conflict, and preference" — Classification into inference and conflict schemes *(p.5-6)*
- Feng, Y. & Hirst, G. (2011) — "Classifying arguments by scheme" — Automatic classification of argumentation schemes *(p.3)*
- Ashley, K. (2006) — "Case-based reasoning" — Legal argumentation technology *(p.25)*
- Atkinson, K., Bench-Capon, T., & McBurney, P. (2005) — "Arguing about cases in practical reasoning" *(p.25)*
- Green, N. (2015) — "Identifying argumentation schemes in genetics research articles" *(p.3)*
- Mochales Palau, R. & Moens, M. F. (2011) — "Argumentation mining" in Artificial Intelligence and Law *(p.3)*

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found — this paper postdates most collection papers; Modgil 2014 cites earlier Walton works but not this 2015 paper specifically)

### Conceptual Links (not citation-based)
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — **Strong.** ASPIC+ provides the formal mechanism to instantiate these argumentation schemes computationally: each scheme's premise-conclusion structure maps to a defeasible inference rule in ASPIC+, and each scheme's critical questions map to the three attack types (undermining, rebutting, undercutting). The classification here answers "what kinds of arguments exist" while ASPIC+ answers "how to construct and evaluate them formally." *(p.5)*
- [[Dung_1995_AcceptabilityArguments]] — **Moderate.** Dung's abstract framework provides the semantics for evaluating arguments built from schemes. The schemes are at a higher level of abstraction (argument types with internal structure) while Dung operates at the abstract level (arguments as atomic entities with attack relations). The classification provides the bridge between natural language arguments and abstract argumentation.
- [[Pollock_1987_DefeasibleReasoning]] — **Moderate.** Pollock's distinction between rebutting and undercutting defeaters maps to how critical questions function in argumentation schemes: some CQs attack the conclusion directly (rebutting) while others attack the inferential link (undercutting). *(p.5)*
- [[Clark_2014_Micropublications]] — **Moderate.** Micropublications model scientific claims with support/challenge relations. The argumentation schemes classified here provide a taxonomy for the types of support relations (argument from expert opinion, argument from sign, argument from analogy, etc.) that could be used to type the edges in a micropublication network.
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — **Strong.** Mayer et al. provide a computational argument mining pipeline that detects exactly the kinds of argument structures Walton classifies: evidence-to-claim support patterns in clinical trial abstracts correspond to specific scheme types in Walton's hierarchy. Walton provides the theoretical taxonomy of "what kinds of arguments exist" while Mayer provides transformer-based NLP methods for automatically detecting them in domain text, demonstrating practical realization of scheme-aware argument mining. *(p.3)*
