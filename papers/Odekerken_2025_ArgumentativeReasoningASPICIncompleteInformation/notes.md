---
title: "Argumentative Reasoning in ASPIC+ under Incomplete Information"
authors: "Daphne Odekerken, Tuomo Lehtonen, Johannes P. Wallner, Matti Järvisalo"
year: 2025
venue: "Journal of Artificial Intelligence Research 83, Article 28"
doi_url: "https://doi.org/10.1613/jair.1.18404"
pages: "282-333"
---

# Argumentative Reasoning in ASPIC+ under Incomplete Information

## One-Sentence Summary
Final JAIR version of the incomplete-information ASPIC+ line: it formalizes four grounded justification statuses, proves tight complexity results for stability and relevance, gives exact ASP and CEGAR-style algorithms, and shows the exact methods are practical on real inquiry data. *(p.1-3, p.15-28, p.29-34, p.41)*

## Problem Addressed
Most prior work on incomplete information in argumentation focused on abstract argumentation frameworks, while practical inquiry applications often need structured formalisms such as ASPIC+. The paper asks how to reason about the resilience of a literal's status when future information may still arrive, focusing on two tasks: whether the current status is stable under all future completions, and which unresolved queryables are relevant to changing that status. *(p.1-3)*

The motivating application is inquiry support in domains such as one-time trade-fraud and police investigation, where one needs both a current acceptance status and guidance on which additional information is worth gathering. *(p.1-2)*

## Key Contributions
- Formalizes incomplete ASPIC+ theories under grounded semantics using four justification statuses: `unsatisfiable`, `defended`, `out`, and `blocked`. *(p.6-8)*
- Defines future argumentation theories, `j`-stability, minimal stable future theories, and `j`-relevance for structured argumentation. *(p.8-10)*
- Proves polynomial-time decidability of justification for the grounded fragment studied here, coNP-completeness of stability, and `Sigma_2^P`-completeness of relevance. *(p.15-21)*
- Extends the analysis with additional general complexity bounds beyond the exact restricted fragment and beyond the earlier conference version. *(p.20-21)*
- Develops exact ASP encodings for justification and stability, plus CEGAR-style ASP algorithms for relevance and for finding all relevant queryables. *(p.21-30)*
- Provides empirical evidence on both a police-inspired real-world benchmark and synthetic benchmarks, showing the exact approach is practical and competitive with a prior inexact method. *(p.29-34)*
- Shows that abstract incomplete-framework notions do not directly preserve the structured notions of stability and relevance, so structured incomplete ASPIC+ needs its own analysis rather than a simple translation through IAFs. *(p.35-40)*

## Methodology
The paper starts from a grounded ASPIC+ fragment with a knowledge base, strict rules, defeasible rules, and a preference ordering interpreted via the last-link principle. It then introduces a set of queryables representing literals that may be added later to the knowledge base. Future argumentation theories are obtained by adding consistent subsets of those queryables to the axioms while leaving the rest of the theory fixed. *(p.2-4, p.8-9)*

The central move is to reformulate grounded justification, stability, and relevance in terms of rule applicability and rule defeat, rather than by explicitly constructing and inspecting all arguments. This enables a least-fixed-point characterization for justification and leads naturally to declarative ASP encodings for justification and stability, and to a CEGAR-style search procedure for relevance. *(p.11-17, p.21-29)*

The evaluation uses both real-world inquiry-style instances and synthetic instances, compares the exact ASP encodings against a prior approximate approach for stability without preferences, and reports solved counts plus mean and maximum runtimes under a 600-second time limit. *(p.29-34)*

## Formal Background Reused from ASPIC+
The paper works with an argumentation system `AS = (L, -, R, <=)` where `L` is a finite logical language, `-` is a negation/complement operation, `R` is the set of defeasible rules, and `<=` is a partial preorder on rules that is later lifted through the last-link principle. A knowledge base `X` is a consistent set of literals over `L`, and an argumentation theory is `AT = (AS, X)`. *(p.4-6)*

Arguments are either observation-based arguments for literals in the knowledge base or rule-based arguments whose top rule is a defeasible rule. The paper uses the standard ASPIC+ subargument machinery and then induces an argumentation framework whose nodes are arguments and whose defeats depend on the last-link preference ordering. *(p.4-7)*

Under grounded semantics, a literal is justified iff there is an argument for it in the grounded extension. For incomplete theories, the paper refines this into four statuses:
- `unsatisfiable`: there is no argument for the literal. *(p.8, p.16)*
- `defended`: some argument for the literal is in the grounded extension. *(p.8, p.16)*
- `out`: there is an argument for the literal, but every such argument is defeated. *(p.8, p.16)*
- `blocked`: the literal is neither unsatisfiable, defended, nor out; intuitively it has arguments but no grounded defender and also no decisive defeat of every supporting argument. *(p.8, p.16)*

## Core Definitions

### Future Argumentation Theories
Given an `AT = (AS, X)` and a set of queryables `Q`, the set `T^Q_AT` contains all future theories obtained by consistently expanding the knowledge base with subsets of `Q`. The current theory is one such future theory, and the set of allowed futures is constrained so that both a literal and its contradictory cannot be added together. *(p.8-9)*

### j-Stability
For a status `j` in `{unsatisfiable, defended, out, blocked}`, a literal `l` is `j`-stable w.r.t. `T` and `Q` iff `l` has status `j` in every future theory in `T^Q_AT`. This is the structured analogue of asking whether additional information can ever change the current status. *(p.8-10)*

### Minimal Stable Future Theories
A future theory is a minimal stable future theory for `l` and status `j` if it makes `l` `j`-stable and no strictly smaller future theory does so. These minimal futures are used to define relevance. *(p.9-10)*

### j-Relevance
A queryable `q` is `j`-relevant for `l` iff it appears in some minimal stable future theory that makes `l` `j`-stable. Intuitively, `q` is part of some minimally sufficient information package for stabilizing the status of `l`. *(p.10-11)*

### Rule-Level Justification Machinery
The main technical reformulation defines rule applicability, rule defeat, and rule defense directly over rule sets rather than over the whole argument graph. This culminates in a fixed-point operator over defended rules whose least fixed point determines the justification status of literals. *(p.11-16)*

## Key Equations

$$
\Gamma_{AT}^{Q} = \{T' \mid T' \text{ is a future argumentation theory of } AT \text{ w.r.t. } Q\}
$$

Where: `AT` is the current ASPIC+ theory, `Q` is the set of queryables, and `T'` ranges over consistent future expansions of the knowledge base by queryables. *(p.8-9)*

$$
l \text{ is } j\text{-stable w.r.t. } T,Q \iff \forall T' \in \Gamma_{AT}^{Q},\; status_{T'}(l)=j
$$

Where: `j` is one of `unsatisfiable`, `defended`, `out`, or `blocked`. This is the paper's core semantic notion of stability. *(p.8-10)*

$$
q \text{ is } j\text{-relevant for } l \iff \exists T' \text{ minimal stable-}j \text{ future theory for } l \text{ with } q \in X' \setminus X
$$

Where: `X` is the current knowledge base and `X'` is the knowledge base of a minimal stable future theory. *(p.9-10)*

$$
G(T)=lfp(def_T)
$$

Where: `def_T` is the rule-defense operator introduced for the grounded fragment, and its least fixed point determines which rules are defended and therefore which literals are `defended`, `out`, `blocked`, or `unsatisfiable`. *(p.14-16)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Time limit per instance | - | s | 600 | - | 29 | Used for all empirical runs |
| Memory limit per instance | - | GB | 32 | - | 29 | Intel Xeon Gold 6348 environment |
| Stability benchmark language size | \|L\| | literals | - | 150-5000 | 29-33 | Synthetic stability instances vary from mid-size to very large |
| Relevance benchmark language size | \|L\| | literals | - | 50-150 | 29-34 | Synthetic relevance instances use smaller languages |
| Number of real-world stability instances | - | instances | 351 | - | 31-32 | Real inquiry-style stability benchmark |
| Number of real-world relevance instances | - | instances | 351 | - | 32-34 | Real inquiry-style relevance benchmark |

## Implementation Details
- Encode the argumentation theory as ASP facts over literals, rules, rule heads/bodies, contraries, queryables, and preferences. The paper explicitly gives a compact grounding-oriented encoding of the AT. *(p.21-22)*
- Use a dedicated ASP module for justification without preferences, then extend it with an iterative preference-aware module implementing the last-link ordering for defeasible rules. *(p.22-25)*
- The rule-defense operator is implemented directly in ASP via predicates for applicable, undefeated, defeated, defended, and blocked rules/literals, instead of constructing all arguments explicitly. *(p.11-16, p.22-24)*
- Stability is decided by non-deterministically guessing a future theory and checking for a counterexample where the target literal does not have the queried status. This yields an ASP program whose answer sets witness non-stability. *(p.24-25)*
- Relevance is handled by a CEGAR-style loop. The algorithm guesses a candidate set of queryables that may witness relevance, then alternates between abstract candidate generation and concrete checking. *(p.26-29)*
- For a single queryable, the relevance encoding uses two answer-set programs: one to search for a candidate future theory and one to check whether the candidate genuinely witnesses non-stability or stability in the needed direction. *(p.26-27)*
- For the "all relevant queryables" problem, the CEGAR algorithm maintains positive discoveries `R` together with `no_subsets` and `no_supersets` constraints to prune the search space efficiently after each counterexample or witness. *(p.28-29)*
- The paper explicitly notes that the exact stability approach without preferences can be compared to a prior inexact approximate approach, but there is no similarly applicable prior exact or approximate baseline for relevance. *(p.29)*

## Figures of Interest
- **Fig. 1 (p.5):** Running one-time trade-fraud example used throughout the paper; also illustrates how observation-based and rule-based arguments interact under last-link preferences.
- **Fig. 2 (p.10):** Graph of future argumentation theories for the running example, clarifying stability and minimal stable futures.
- **Fig. 3 (p.13):** Example theory and corresponding AF used to show the correspondence between defense by rules and defense by arguments.
- **Fig. 4 (p.19):** Reduction gadget for the `Sigma_2^P`-hardness proof of relevance.
- **Table 1 (p.20):** Complexity summary, contrasting the grounded restricted fragment with general grounded ASPIC and settings beyond the grounded fragment.
- **Tables 2-6 (p.32-34, p.51):** Solved-instance counts and runtimes for stability and relevance across real and synthetic datasets.
- **Figs. 7-8 (p.33-34):** Runtime and cumulative-solved curves illustrating strong real-world performance and competitive exact stability results.
- **Figs. 9-12 (p.38-40):** Counterexamples showing that stability/relevance in corresponding incomplete abstract frameworks do not line up cleanly with the structured notions at the ASPIC+ level.

## Results Summary
- In the grounded restricted fragment studied in detail, justification is polynomial-time decidable. *(p.15-16)*
- For all four statuses, deciding `j`-stability is coNP-complete, even without preferences; the paper then recovers the same lower bound when preferences are present in the studied setting. *(p.17-18)*
- For all four statuses, deciding whether a queryable is `j`-relevant is `Sigma_2^P`-complete, again with hardness already present without preferences. *(p.18-20)*
- The paper also derives more general upper and lower bounds for broader ASPIC+ fragments and for semantics beyond the exact grounded fragment, summarized in Table 1. *(p.20-21)*
- Empirically, the exact ASP-based stability procedure performs competitively with a prior approximate approach on the real-world instances and often solves real-world cases in fractions of a second to a few seconds. *(p.29-33)*
- For relevance, all 351 real-world single-query instances are solved both with and without preferences, and a substantial portion of synthetic instances up to around `|L|=130` or higher are also solved within the time limit depending on status and preference setting. *(p.32-34, p.51)*
- The exact approach is therefore fast enough on the targeted real-world inquiry data to support online use. *(p.29, p.32-34)*

## Limitations
- The main semantic development focuses on grounded semantics, motivated by the inquiry application and its skeptical flavor. Richer semantics are discussed only through partial complexity results and future-work remarks. *(p.2-3, p.20-21, p.41)*
- Future theories only vary the knowledge base by adding queryables; they do not add new rules or new ordinary premises, which the conclusion explicitly identifies as a meaningful extension point. *(p.8-9, p.41)*
- The full relation between structured and abstract incomplete argumentation is negative rather than cleanly reducible: corresponding IAF notions do not preserve the structured notions in general. *(p.35-40)*
- The conclusion notes that once stronger preference principles or richer future-theory operations are introduced, the computational complexity is expected to rise further and likely requires new algorithmic ideas. *(p.41)*

## Arguments Against Prior Work
- Prior incomplete-information work at the abstract-AF level does not by itself solve the structured ASPIC+ problem, because the structured notions depend on argument construction and rule-level phenomena that disappear in a flat AF view. *(p.1-3, p.35-40)*
- Results about acceptance in incomplete abstract argumentation frameworks do not transfer directly to structured incomplete ASPIC+, because justified-status questions in the structured setting cannot simply be inferred from AF acceptance. *(p.20-21)*
- The paper explicitly shows counterexamples where stable-defendedness and defined-relevance at the abstract IAF level fail to capture the corresponding structured properties. *(p.37-40)*
- For stability without preferences, a previously proposed approximate approach exists, but the paper argues and demonstrates that exact ASP-based reasoning is practical enough to matter, at least on the target data. *(p.29-33)*

## Design Rationale
- **Why grounded semantics?** The inquiry application wants a single skeptical status with a strong acceptance flavor, and grounded semantics naturally supports that. *(p.2-3, p.7-8, p.41)*
- **Why rule-level fixed points instead of explicit argument enumeration?** The rule-based view makes justification polynomial-time decidable in the grounded fragment and avoids paying the full cost of explicit AF construction whenever possible. *(p.11-16, p.20-21)*
- **Why last-link preferences?** This is the preference principle used in the motivating police-inspired inquiry setting and it integrates cleanly with rule-based reasoning. *(p.2-3, p.6-7, p.24-25)*
- **Why ASP?** The problems quickly leave polynomial time once one moves from justification to stability and relevance, and ASP provides a natural declarative substrate for exact search plus iterative refinement. *(p.21-29)*
- **Why CEGAR for relevance?** Searching over many possible future queryable sets is combinatorially hard; candidate generation plus witness/counterexample refinement avoids brute-force enumeration of all subsets. *(p.26-29)*
- **Why compare against incomplete AFs at all?** The authors want to delimit exactly where abstraction is faithful and where it loses the structured signal that matters for ASPIC+ inquiry reasoning. *(p.35-40)*

## Testable Properties
- In the grounded restricted fragment, the justification status of a literal can be computed in polynomial time from the least fixed point of the rule-defense operator. *(p.15-16)*
- For each status `j` in `{unsatisfiable, defended, out, blocked}`, deciding `j`-stability is coNP-complete. *(p.17-18)*
- For each status `j` in `{unsatisfiable, defended, out, blocked}`, deciding `j`-relevance is `Sigma_2^P`-complete. *(p.18-20)*
- The ASP program for stability has an answer set exactly when a literal is **not** `j`-stable; equivalently, absence of answer sets certifies stability. *(p.24-25)*
- Algorithm 1 for single-query relevance is sound and complete: it returns `YES` exactly when the queryable is `j`-relevant for the target literal. *(p.27-28)*
- Algorithm 2 for all relevant queryables is sound and complete: it returns exactly the set of all `j`-relevant queryables for the literal. *(p.28-29)*
- Stable-defendedness in a corresponding incomplete abstract framework implies defined-stability on the structured side in one direction, but the converse fails; similarly for relevance there are counterexamples to equivalence. *(p.37-40)*

## Relevance to Project
This paper is directly relevant to any propstore workflow that wants to reason under partial evidence, ask whether a current conclusion is robust, and ask which unresolved propositions are worth investigating next. It supplies:
1. a structured-account notion of future information for ASPIC+-style reasoning,
2. exact complexity guidance for what can and cannot be expected computationally,
3. concrete ASP encodings and CEGAR procedures for stability and relevance,
4. evidence that the exact approach is fast enough for online inquiry-style use on realistic data. *(p.1-3, p.21-34)*

For project design, the most important takeaway is that "what should I ask next?" can be grounded in a formal `j`-relevance computation over structured argumentation, not only in heuristic uncertainty or abstract-AF approximations. *(p.8-10, p.26-29, p.41)*

## Open Questions
- [ ] How should the future-theory model be extended to allow new ordinary premises or new rules, rather than only new axioms/queryables? *(p.41)*
- [ ] What exact complexity and algorithmic picture emerges for richer ASPIC+ semantics beyond grounded, especially under stronger preference machinery? *(p.20-21, p.41)*
- [ ] Can the structured relevance and stability procedures be optimized further for larger synthetic instances while preserving exactness? *(p.29-34, p.41)*
- [ ] Is there a better structured abstraction than corresponding IAFs that preserves the structured notions of stability and relevance more faithfully? *(p.35-40)*

## Related Work Worth Reading
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — preliminary KR 2023 version; the JAIR paper explicitly supersedes and expands it. *(p.1-3, refs)*
- [[Lehtonen_2023_AlgorithmsPreferentialArgumentativeReasoning]] — complementary preferential ASPIC+ algorithms cited as nearby computational work. *(refs)*
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — the ASPIC+ formal baseline used throughout. *(p.2-4, refs)*
- Incomplete abstract argumentation papers by Baumeister, Rothe, and Odekerken — important foil for the structured-vs-abstract comparison section. *(p.35-40, refs)*

## Collection Cross-References

### Already in Collection
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — direct conference precursor superseded by this JAIR version. *(p.1-3, refs)*
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — foundational ASPIC+ tutorial underlying the formal setup. *(p.2-7, refs)*
- [[Lehtonen_2020_AnswerSetProgrammingApproach]] — computational ASPIC+ background that this paper extends from justification to incomplete-information stability/relevance. *(conceptual)*
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — preference machinery background for last-link ordering and rule comparison. *(p.6-7, refs)*
- [[Dung_1995_AcceptabilityArguments]] — abstract grounded semantics used after structured construction. *(p.6-8, refs)*

### New Leads (Not Yet in Collection)
- Alviano, Greco, and Parisi (2020), *Efficient Computation of Extensions for Dynamic Abstract Argumentation Frameworks: An Incremental Approach*. *(refs)*
- Odekerken, Barkema, and Woltran (2024), *Finding Relevant Updates in Incomplete Argumentation Frameworks*. *(refs)*
- Baroni et al. (2011), *An Introduction to Argumentation Semantics*. *(refs)*

### Supersedes or Recontextualizes
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — superseded as the canonical version; the JAIR paper adds general complexity results, stronger relevance algorithms, revised implementation, and broader evaluation. *(p.1-3, description.md)*

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Lehtonen_2020_AnswerSetProgrammingApproach]] — strong: both shift ASPIC+ computation away from explicit AF explosion and into direct declarative reasoning.
- [[Odekerken_2022_StabilityRelevanceIncompleteArgumentation]] — strong: abstract-AF incomplete-information precursor that this paper both builds on and criticizes as insufficient for the structured setting.
