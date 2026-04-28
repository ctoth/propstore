---
title: "On the links between argumentation-based reasoning and nonmonotonic reasoning"
authors: "Zimi Li, Nir Oren, Simon Parsons"
year: 2016
venue: "arXiv preprint / September 2016 manuscript"
doi_url: "https://arxiv.org/abs/1701.03714"
---

# On the links between argumentation-based reasoning and nonmonotonic reasoning

## One-Sentence Summary
Analyzes ASPIC+ through the Kraus-Lehmann-Magidor axiom lens under two readings of consequence, showing that argument construction is cumulative but not monotonic, while justified conclusions are weaker still unless the theory is purely strict. *(p.1-9)*

## Problem Addressed
The paper asks how structured argumentation in ASPIC+ relates to classical nonmonotonic-reasoning axiom systems, and whether the resulting consequence relations line up with the rationality postulates usually used to justify argumentation formalisms. *(p.1, p.4, p.8-9)*

## Key Contributions
- Defines the ASPIC+ setup used in the analysis, including argument construction, three attack types, preferences, defeat, and induced abstract argumentation frameworks. *(p.2-3)*
- Introduces two consequence relations: `|~a` for argument constructibility and `|~j` for justified conclusions under Dung-style semantics. *(p.5-6)*
- Classifies which KLM-style axioms hold for `|~a` and `|~j` under both strict and defeasible interpretations of the meta-level consequence relation. *(p.4-8)*
- Shows `|~a` satisfies Ref, LLE, RW, Cut, CM, M, and T but fails CP, so it is cumulative monotonic but not monotonic. *(p.5-6)*
- Shows `|~j` keeps only strict LLE and RW together with Cut and CM for general theories; M, T, and CP fail for defeasible theories, while strict theories recover Ref, M, and T. *(p.6-7)*
- Connects closure under strict rules and consistency postulates to specific axiom fragments, clarifying what additional proof obligations are needed if ASPIC+ is used as a logic. *(p.8-9)*

## Formal Setup

### Argumentation System
An argumentation system is `AS = (L, R_s, R_d, n)` where `L` is a logical language closed under negation, `R_s` and `R_d` are strict and defeasible inference rules, and `n` names defeasible rules. Rules have the form `phi_1, ..., phi_n -> phi` or `phi_1, ..., phi_n => phi`. *(p.2)*

### Knowledge Base and Theory
A knowledge base is `K` with two disjoint subsets: axioms `K_n` and ordinary premises `K_p`. An argumentation theory is `AT = (AS, K)`. The paper assumes strict rules are closed under transposition in order to match ASPIC+ rationality postulates. *(p.2)*

### Arguments and Attacks
Arguments are built recursively from premises and rules. An argument can attack another by:
- undermining an ordinary premise,
- rebutting a defeasible conclusion, or
- undercutting a defeasible rule application. *(p.2-3)*

The paper uses restricted rebutting: a strict top rule cannot rebut a defeasible top rule. Preferences are represented by a binary relation `<=` over arguments and separate preference-dependent from preference-independent attacks. *(p.3)*

### Induced Abstract Framework
From a structured framework `SAF = (A, att, <=)`, the induced abstract framework is `AF = (A, Defeats)`, where `Defeats` is the attack relation filtered by successful preference comparisons. Standard Dung semantics then define extensions, and `Just(A)` denotes the set of justified conclusions obtained from an extension. *(p.3)*

## Axioms Under Study
The paper uses the KLM family:
- Ref: reflexivity `alpha |~ alpha`
- LLE: left logical equivalence
- RW: right weakening
- Cut
- CM: cautious monotonicity
- M: monotonicity
- T: transitivity
- CP: contraposition *(p.4)*

Ref, LLE, RW, Cut, and CM characterize cumulative logics; adding M yields cumulative monotonic systems. CP is stronger and turns out to be the main failure point for ASPIC+. *(p.4, p.7-8)*

## Two Consequence Relations

### Argument Construction: `|~a`
`alpha |~a beta` means that for every ASPIC+ theory whose language includes `alpha`, if `beta` is a consequence of `alpha` according to the chosen interpretation, then an argument for `beta` can be constructed in the extended theory. This ignores whether the resulting argument is ultimately justified. *(p.5)*

### Justified Conclusions: `|~j`
`alpha |~j beta` means that under the same setup, `beta` belongs to the justified conclusions of the induced argumentation framework. This is strictly stronger because it requires not just argument construction but survival through attack and defeat. *(p.6)*

## Main Results

### Results for `|~a`
- Proposition 1: `|~a` satisfies Ref, LLE, RW, Cut, and CM for both strict and defeasible theories. The proofs work by explicitly splicing chains of arguments and rule applications. *(p.5)*
- Proposition 2: `|~a` satisfies M and T for both strict and defeasible theories. The construction combines argument chains for `alpha -> beta` and `beta -> gamma` into a chain for `alpha -> gamma`. *(p.5-6)*
- Proposition 3: `|~a` does not satisfy CP; the paper gives a counterexample theory where `alpha |~a beta` holds but `not beta |~a not alpha` fails. *(p.6)*

Net effect: `|~a` is cumulative monotonic for all theories considered, but not fully monotonic in the stronger KLM sense that also requires contraposition. *(p.6-7)*

### Results for `|~j`
- Proposition 4: `|~j` implies `|~a`, so every justified consequence is constructible, but not vice versa. *(p.6)*
- Proposition 5: `|~j` does not satisfy Ref, and it also fails the defeasible versions of LLE and RW because justified conclusions can be defeated even when constructible arguments exist. *(p.6)*
- Proposition 6: `|~j` satisfies the strict version of LLE and RW, plus Cut and CM for both strict and defeasible theories. *(p.6-7)*
- Proposition 7: `|~j` does not satisfy M, T, or CP for defeasible theories. Table 2 makes clear that CP is the main blocker for cumulativity, while M and T also break once defeasible rules can be introduced. *(p.7)*
- Proposition 8: if the theory is strict, then `|~j` satisfies Ref, M, and T. In that restricted setting, `|~j` is cumulative monotonic. *(p.7)*

## Discussion and Interpretation
The paper argues that these failures are not accidents but part of why ASPIC+ is useful. Because arguments can be built without being justified, and because adding defeasible rules or premises can alter defeat status, ASPIC+ remains weaker than classical monotonic systems and even weaker than the weakest nonmonotonic logics in the KLM family. The authors treat that weakness as a feature: it allows ASPIC+ to model systems such as defeasible logic and other argumentation-oriented weak logics. *(p.7-8)*

The key design distinction is between extending a theory by adding ordinary premises versus by adding rules. LLE and RW are harmless for strict theories because strict premises and strict rules cannot be defeated, but the same moves are unsafe for defeasible theories because justified conclusions depend on attack structure, not just derivability. *(p.7-8)*

## Rationality Postulates

### Closure Under Strict Rules
Proposition 9 shows that closure under strict rules corresponds to the justified-conclusion relation satisfying RW with respect to justified conclusions. If a justified `alpha` and a strict rule `alpha -> beta` are present, closure requires justified `beta`. *(p.8)*

### Direct Consistency
Direct consistency for `|~j` means that no extension contains inconsistent arguments. The paper notes this is equivalent to an additional axiom not contained in the studied KLM fragment, so direct consistency cannot be recovered from Ref/LLE/RW/Cut/CM/M/T/CP alone. *(p.8)*

### Indirect Consistency
Proposition 10 states that, assuming direct consistency and consistency of strict rules, monotonicity plus closure under strict rules yields indirect consistency, and conversely. This makes indirect consistency a derived property once the right proof-theoretic conditions are enforced. *(p.9)*

## Implementation Details
- To reproduce the paper's first consequence relation, implement argument construction independently of acceptability, and test it against Ref/LLE/RW/Cut/CM/M/T while expecting CP to fail. *(p.5-6)*
- To reproduce the second consequence relation, compute extensions on the induced AF after filtering attacks through preferences into defeats, then collect the conclusions of the selected extension. *(p.3, p.6)*
- Restricted rebutting matters: allowing unrestricted rebut changes the property landscape, so the attack policy is part of the semantics, not a minor implementation detail. *(p.3)*
- The distinction between strict and defeasible interpretations must be explicit in code. The paper's positive results for `|~j` depend on whether newly added information is defeasible or strict. *(p.5-8)*
- Any property test suite for ASPIC+ should separate "constructible" from "justified"; collapsing them will incorrectly make ASPIC+ look stronger than it is. *(p.5-8)*

## Figures and Tables of Interest
- **Table 1**: Lists the axiom schemata analyzed in the paper. Useful as a direct checklist for property-based tests. *(p.4)*
- **Table 2**: Summarizes which axioms each consequence relation satisfies under strict versus defeasible theories. This is the paper's main implementation-facing artifact. *(p.7)*

## Relevance to Project
This paper is directly useful for propstore if ASPIC+-style reasoning is part of the design. It converts informal expectations about "what should remain true when I add rules or premises?" into a concrete regression suite. In particular, it warns against assuming justified conclusions behave like ordinary entailment once defeasible rules are present; the implementation needs separate APIs or proof statuses for constructibility and justification. *(p.5-9)*

## Open Questions
- [ ] Which of the two consequence relations should propstore expose at the API level: constructible, justified, or both?
- [ ] Does the project want restricted rebutting exactly as assumed here, or a different attack policy?
- [ ] Which rationality postulates need to be executable invariants in tests?
- [ ] Should strict-rule closure be enforced syntactically, semantically, or both?

## Collection Cross-References

### This paper cites (in collection)
- **Caminada_2007_EvaluationArgumentationFormalisms** - cited as [3]. Provides the evaluation criteria for argumentation formalisms that this paper uses as background for rationality-style analysis.
- **Dung_1995_AcceptabilityArguments** - cited as [5]. Supplies the abstract argumentation semantics used once the structured ASPIC+ theory is mapped to an induced AF.
- **Modgil_2014_ASPICFrameworkStructuredArgumentation** - cited as [13]. This is the core ASPIC+ reference whose definitions of arguments, attacks, preferences, and defeats are analyzed here.
- **McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning** - cited as [11]. One of the weak nonmonotonic logics used in the discussion of where ASPIC+ sits in the broader consequence-relation landscape.
- **Reiter_1980_DefaultReasoning** - cited as [16]. Another canonical nonmonotonic logic used for comparison in the discussion section.
- **Moore_1985_SemanticalConsiderationsNonmonotonicLogic** - cited as [14]. Used alongside circumscription and default logic as a comparison point for ASPIC+'s weakness.

### Now in Collection (previously listed as leads)
- [Nonmonotonic Reasoning, Preferential Models and Cumulative Logics](../Kraus_1990_NonmonotonicReasoningPreferentialModels/notes.md) — KLM is the foundational axiom system Li uses to classify ASPIC+. Per Li, `|~a` (argument constructibility) satisfies Ref, LLE, RW, Cut, CM, M, T but fails CP — i.e. cumulative monotonic but not fully monotonic in KLM's sense; `|~j` (justified conclusions) is weaker still unless the theory is purely strict. *(Li p.4, p.10)*

### Cited By (in Collection)
- None found by title, directory name, or author/year search at reconcile time.

### Conceptual Links
- **Prakken_2010_AbstractFrameworkArgumentationStructured** - complements this paper by explaining how structured argumentation frameworks abstract into Dung-style frameworks; Li et al. focus on which logical properties survive that abstraction.
- **Amgoud_2013_Ranking-BasedSemanticsArgumentationFrameworks** - another axiomatic analysis paper, but for ranking semantics instead of ASPIC+ consequence relations. Together they suggest a broader project pattern: treat reasoning formalisms as property bundles, not opaque algorithms.
- **Thimm_2012_ProbabilisticSemanticsAbstractArgumentation** - also asks how argumentation semantics should behave when read as a consequence-like relation; useful if propstore wants graded or probabilistic justified status on top of the binary ASPIC+ results here.
- **Li_2011_ProbabilisticArgumentationFrameworks** - shares Li and Oren authorship and offers a different axis of weakening: uncertainty over AF structure rather than weakness of the consequence relation itself.

## Related Work Worth Reading
- **Kraus, Lehmann, and Magidor 1990** - foundational axiom system for cumulative and monotonic logics. *(p.4, p.10)* → NOW IN COLLECTION: [Nonmonotonic Reasoning, Preferential Models and Cumulative Logics](../Kraus_1990_NonmonotonicReasoningPreferentialModels/notes.md)
- **Modgil and Prakken 2014** - ASPIC+ tutorial defining the base framework studied here. *(p.2-4, p.10)*
- **Dung 1995** - abstract semantics layer used after structured arguments are built. *(p.3, p.10)*
- **Li and Parsons 2015** - precursor focused on purely defeasible rules. *(p.1, p.10)*
- **Reiter 1980** and **Moore 1985** - examples of other weak nonmonotonic logics that motivate the comparison space. *(p.8-10)*
