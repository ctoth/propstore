# Notes: Walton & Macagno 2015 Paper Processing

## Task
Process paper: Walton, D. and Macagno, F. (2015). "A classification system for argumentation schemes." Argument & Computation, 6(3), 219-245.
DOI: https://doi.org/10.1080/19462166.2015.1123772

## Steps
1. Retrieve paper via fetch_paper.py (may need sci-hub fallback)
2. Read and extract notes via paper-reader skill
3. No cleanup needed (source is URL, not local file)
4. Extract claims via extract-claims skill
5. Write report to ./reports/lead-Walton-Macagno-2015-report.md

## Current State
- Step 1 DONE: PDF retrieved from sci-hub (1.3MB, 28 pages)
- PNGs converted: 28 page images in pngs/ directory
- Reading pages: read pages 0-6 so far

## Key Observations from Pages 0-6
- Page 0: Cover/citation page from Taylor & Francis
- Page 1: Title, authors (Douglas Walton, Fabrizio Macagno), abstract. Paper classifies argumentation schemes and outlines how the classification system can be used for building argument mining tools. Published in Argument & Computation, 6(3), 219-245, 2015 (published online 2016).
- Page 2: Section 1 "Why argumentation schemes are important" - schemes can be classified in different ways depending on the purpose. The paper's classification system will determine criteria for classifying schemes and is adapted from existing systems.
- Page 3: Section 2 "Argument mining" - computational uses of argumentation schemes. Argument mining extracts argumentative structures from text. Schemes used to identify/classify argument types. References to Palau & Moens 2009, Mochales & Moens 2011 on legal texts.
- Page 4: Section 3 "A survey of recent classification systems" - Reviews Kienpointner (1992), Grennan (1997), Walton (1996), Walton et al. (2008). Kienpointner's taxonomy has 3 first directions: descriptive-normative, abstract-concrete, individual schemes vs classes. Also discusses Perelman & Olbrechts-Tyteca, Hastings.
- Page 5: Continues survey. Discusses Lumer & Dove (2011), Macagno & Rivas (2021 probably 2014), Rahwan et al. (2011), and Baroni, Besnard, Reed, Walton, Abeldi (2013) on Argument Interchange Format.
- Page 6: Discusses Bex & Reed (2011) on classification into 3 broad categories. Distinction between inference schemes (defeasible modus ponens, rule-based) and conflict schemes (negation/contradiction). Also mentions schemes that can be modeled as conditional generalizations.
- Page 7: Section 4 "Ways and desiderata for classifying schemes". Two ways: (1) by premise dependency (e.g. argument from expert opinion depends on source being expert), (2) by general category. Also discusses the "ad hominem" scheme and its sub-categories. Lists 6 desiderata for a classification system.
- Page 8: Continues desiderata. Lists 6 criteria for classification systems: (1) helpful for identifying schemes, (2) helps users deal with borderline cases, (3) should handle new schemes, (4) look at finer distinctions, (5) more complex = more useful, (6) differences in classification should reflect differences in use.
- Page 9: Section 5 "Schemes for source-based arguments". Distinguishes practical vs epistemic arguments. Argument from position to know (expert opinion). Major Premise, Minor Premise, Conclusion structure.
- Page 10: Section 5 continued. Argument from expert opinion detailed with premise/conclusion structure. Discusses critical questions and how they map to counterarguments. Difference between argument from position to know and argument from expert opinion.
- Page 11: Argument from inconsistent commitment. Premise structure provided. Discusses circumstantial ad hominem as related.
- Page 12: Figure 1 showing argument visualization using Araucaria. Section 6 "Schemes for practical reasoning" begins. Argument from waste (sunk cost).
- Page 13: Figure 2. Argument diagram for SC argument. Argumentation scheme for argument from waste with premise/conclusion structure.
- Page 14: Figure 3. Two sides of argument from SC. Argumentation scheme for argument from commitment detailed. Argument from positive/negative values.
- Page 15: Argument from SC can be classified as species of argument from commitment. Discusses goal-directed practical reasoning. Value-based practical reasoning with 16 critical questions.
- Page 16: Value-based scheme detailed. Argument from positive consequences, argument from negative consequences. Can be hybrid schemes.
- Page 17: Section 7 "Schemes for applying rules to cases". Epistemic arguments divided into two broad categories. Argument from established rule. Analogical Following of a Precedent. Modus ponens patterns.
- Page 18: Argument from precedent vs argument from analogy. Carrying out types of actions. Two inference patterns from established rule.
- Page 19: Argument from precedent related to argument from analogy. Case-based reasoning from analogy.
- Page 20: Section 8 "Discovery arguments". Arguments from correlation, sign, and best explanation. Argument from a finding/group of facts.
- Page 21: Argument from ignorance (lack of evidence). Knowledge-based systems connection. Negative argument from ignorance.
- Page 22: TABLE 1 - Summary of classification of schemes. Major taxonomy:
  - Source-independent: (1) Argument establishing rules, (2) Arguments dealing with exceptions, (3) Arguments from ignorance
  - Source-dependent: (1) Arguments from position to know, (2) Arguments from position to know + expertise, (3) Argument from position to know to commitment
  - Practical reasoning: (1) Instrumental argument from goal, (2) Argument from values, (3) Argument from commitment
  - Rules to cases: (1) Classical arguments connecting, (2) Precedent-based, (3) Discovery arguments
  Each category has sub-schemes listed.

## Reading Progress
- All 28 pages read.
- Pages 23-27: Figure 4 (full classification tree), conclusion, references.

## Files Written So Far
- notes.md - DONE
- description.md - DONE
- abstract.md - DONE
- citations.md - DONE
- pngs/ - DONE (28 pages)

## Remaining Steps
- Step 7: Reconcile (cross-reference against collection) - IN PROGRESS
- Step 8: Update papers/index.md
- Step 3 (paper-process): Skip (source was URL, no cleanup)
- Step 4 (paper-process): Extract claims
- Step 5 (paper-process): Write report
