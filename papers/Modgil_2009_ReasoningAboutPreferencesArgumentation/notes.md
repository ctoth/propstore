---
title: "Reasoning about preferences in argumentation frameworks"
authors: "Sanjay Modgil"
year: 2009
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/j.artint.2009.02.001"
produced_by:
  agent: "gpt-5-codex"
  skill: "paper-reader"
  timestamp: "2026-03-28T08:11:01Z"
---
# Reasoning about preferences in argumentation frameworks

## One-Sentence Summary
Extends Dung's abstract argumentation framework with explicit arguments about preferences between attacks, so object-level arguments and meta-level preference arguments can be evaluated in one abstract framework under grounded, complete, preferred, and stable semantics. *(p.901-903)*

## Problem Addressed
Dung frameworks can represent conflicting arguments abstractly, but they do not themselves explain when one symmetric attack should succeed because one argument is preferred to another. Existing preference-aware approaches typically assume the preference relation is fixed in advance, while in realistic reasoning the preference information is often defeasible, conflicting, and itself in need of argumentation. The paper therefore asks how to represent reasoning not only with preferences but also about preferences while preserving Dung's abstract machinery. *(p.901-903)*

## Key Contributions
1. Introduces the **extended argumentation framework (EAF)**, adding a meta-level relation from arguments to attacks so one argument can challenge whether another attack succeeds. *(p.904-905)*
2. Redefines **acceptability** so justified arguments require reinstatement not only of arguments, but also of the attacks used to defend them. *(p.906-907)*
3. Shows that many extensional results familiar from Dung still hold for EAFs, including existence of preferred extensions, admissibility properties, and stable-implies-preferred. *(p.907-909)*
4. Identifies two important subclasses, **bounded hierarchical EAFs** and **preference symmetric EAFs**, whose characteristic functions are monotonic and therefore support constructive grounded-extension computation. *(p.910-914)*
5. Encodes **value-based argumentation** and **argument-based logic programming with defeasible priorities (ALP-DP)** inside the EAF framework, yielding a unified semantics-level treatment of preference reasoning. *(p.910-919)*

## Study Design (empirical papers)

Non-empirical theoretical paper. *(p.901-934)*

## Methodology
The paper starts from Dung's abstract framework and introduces a new relation that lets an argument attack an attack rather than an argument directly. It then defines defeat relative to a set of accepted arguments, develops a recursive notion of reinstatement for defended attacks, and lifts Dung's standard semantics to the resulting structure. After establishing general semantic results, it studies two structurally restricted subclasses where the characteristic function becomes monotonic, then demonstrates the framework's expressiveness by instantiating value-based argumentation and ALP-DP. *(p.903-920)*

## Key Equations / Statistical Models

$$
F_{AF}(S) = \{A \mid A \text{ is acceptable w.r.t. } S\}
$$
Characteristic function for a Dung framework. *(p.904)*

$$
A \text{ defeats}_S B \iff (A,B)\in R \land \neg \exists C \in S \text{ such that } (C,(A,B)) \in D
$$
An attack succeeds in an EAF exactly when no accepted argument in $S$ defense-attacks that attack. *(p.906)*

$$
F_{\Delta}(S) = \{A \mid A \text{ is acceptable w.r.t. } S\}
$$
Characteristic function for an EAF, defined over conflict-free subsets. *(p.909)*

$$
F^0 = \emptyset,\qquad F^{i+1} = F(F^i)
$$
Iterative construction used for grounded semantics when the characteristic function is monotonic, including bounded hierarchical EAFs and preference symmetric EAFs. *(p.909-910, p.913-914)*

$$
R' \succ R \iff \exists r \in R \text{ such that } \forall r' \in R',\ r \prec_C r'
$$
Rule-set comparison used in the ALP-DP instantiation: the rules supporting one argument are better than the other's when every alternative replacement beats at least one rule in the inferior set under priority argument $C$. *(p.916)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Argument set | Args | - | - | - | 904-905 | Base set of arguments in Dung AFs and EAFs |
| Attack relation | R | - | - | - | 904-905 | Binary attack relation between arguments |
| Attack-on-attack relation | D | - | - | - | 905 | Relation from an argument to a specific attack |
| Characteristic function | F | - | - | - | 904, 909 | Maps a candidate extension to its acceptable arguments |
| Preferred extension criterion | - | maximal admissible | - | - | 904, 908 | Same maximal-admissibility criterion as Dung |
| Grounded extension seed | $F^0$ | - | $\emptyset$ | - | 909, 914 | Starting point for constructive grounded computation |
| Value assignment | val | - | - | - | 910 | Maps each argument to a promoted value in VAFs |
| Audience/value ordering | P | - | total order | - | 910 | Total ordering over values in avAFs |
| Strict rule set | S | - | - | - | 914 | Strict rules in ALP-DP theories |
| Defeasible rule set | D | - | - | - | 914 | Defeasible rules in ALP-DP theories |

## Effect Sizes / Key Quantitative Results

This paper is purely theoretical and reports no empirical effect sizes or benchmark metrics. *(p.901-934)*

## Methods & Implementation Details
- **Dung base layer:** Start from $AF=(Args,R)$ with conflict-free, admissible, preferred, complete, stable, and grounded semantics defined exactly as in Dung's 1995 framework. *(p.904)*
- **EAF data model:** Represent an extended framework as $\Delta=(Args,R,D)$ where $D \subseteq Args \times R$, and contradictory preference arguments attacking opposite directions must themselves attack each other. *(p.905)*
- **Defeat evaluation:** An attack $(A,B)$ succeeds relative to a candidate set $S$ only when no accepted argument in $S$ attacks that attack. This makes defeat set-relative rather than globally fixed. *(p.906)*
- **Conflict-freeness:** A set is conflict-free in an EAF when no member defeats another member relative to the set, not merely when no raw attack edge exists. *(p.906)*
- **Acceptability via reinstated attacks:** To defend $A$ against an attacker $B$, it is not enough to have some $C$ attacking $B$; the attack from $C$ to $B$ must itself survive all counterattacks through a recursively defined reinstatement set. *(p.906-907)*
- **Extensional semantics:** Admissible, preferred, complete, and stable extensions are defined over EAFs by reusing Dung's set-theoretic templates once EAF acceptability is in place. *(p.908)*
- **General grounded caveat:** The EAF characteristic function is not monotonic in general, so a least fixed point is not guaranteed without additional restrictions such as finitariness plus structural subclass assumptions. *(p.909)*
- **Bounded hierarchical EAFs:** Partition arguments by meta-level so only level $i$ arguments attack attacks in level $i-1$; under this restriction the characteristic function is monotonic. *(p.910)*
- **Preference symmetric EAFs:** Restrict attacked attacks to those between symmetric attackers. This recovers a simpler acceptability condition and again yields a monotonic characteristic function. *(p.912-914)*
- **VAF instantiation:** Encode value preferences as level-2 arguments over values and optional audience arguments at level 3, so value-based argumentation becomes a hierarchical EAF. *(p.910-912)*
- **ALP-DP instantiation:** Build arguments from named strict and defeasible logic-program rules; conclusion-conclusion attacks and undercuts become EAF attacks, while priority arguments attack only those conclusion-conclusion attacks whose supporting defeasible rules they overrule. *(p.914-919)*

## Figures of Interest
- **Fig. 1 (p.904):** Minimal Dung framework used to review standard acceptability and semantics.
- **Fig. 2 (p.905):** Stepwise weather-forecast example showing how meta-level preference arguments attack object-level attacks.
- **Fig. 3 (p.905):** Final EAF for the weather example; the clearest visual summary of the framework's core idea.
- **Fig. 5 (p.907):** Counterexamples motivating the recursive reinstatement-set definition of acceptability.
- **Fig. 6 (p.911-912):** Encoding of value orderings and arguments about audiences inside a hierarchical EAF.
- **Fig. 8 (p.918):** EAF instantiations for ALP-DP examples, showing how undercuts and preference arguments interact.
- **Fig. 9 (p.925):** Appendix proof diagram characterizing when reinstatement fails in a preference symmetric EAF.

## Results Summary
The paper proves that EAFs preserve the abstract style of Dung while supporting defeasible preference reasoning at the meta-level. Preferred extensions always exist, stable extensions remain preferred, and admissibility enjoys a Dung-style fundamental lemma. The paper also shows that grounded computation is constructive only for restricted subclasses: bounded hierarchical EAFs and preference symmetric EAFs have monotonic characteristic functions, unlike arbitrary EAFs. Finally, the formal encodings of VAFs and ALP-DP show that the framework subsumes important earlier preference formalisms without hard-coding one single preference mechanism. *(p.907-920)*

## Limitations
- The general EAF characteristic function is **not monotonic**, so least-fixed-point grounded semantics are not available in full generality. *(p.909)*
- Grounded semantics in EAFs can diverge from the set of skeptically justified arguments under preferred semantics; the paper's own Example 4 shows this explicitly. *(p.909)*
- The hierarchical restriction is deliberately strong: it forbids arbitrary cross-level interaction and may be too rigid for some applications. *(p.912)*
- ALP-DP grounded semantics coincide with the EAF account only under a **priority-finitary** restriction; a finitary ALP-DP theory need not otherwise produce a finitary EAF. *(p.919)*

## Arguments Against Prior Work
- Existing preference-handling approaches often assume a fixed preference relation or simply remove dispreferred attacks, which cannot represent defeasible, conflicting preferences that must themselves be debated. *(p.901-903)*
- Modeling attack on attack by directly making a preference argument attack one of the object-level arguments is incorrect, because if that preference argument is later defeated, the original attack should be reinstated. *(p.904)*
- The acceptability condition used in earlier preference-based frameworks is too weak for EAFs because it can count an argument as defended without ensuring the defending attacks themselves are reinstated. *(p.906-907)*
- Prakken and Sartor's ALP-DP semantics provide only grounded status and a stronger acceptability notion that does not support Dung-style admissible and preferred semantics; the EAF instantiation is proposed as a repair. *(p.916-920)*

## Design Rationale
- Preferences are represented as **arguments** rather than external metadata so they can be attacked, supported, and evaluated with the same semantics as ordinary arguments. *(p.902-905)*
- The new primitive is an argument-to-attack relation instead of a direct preference-weighted defeat edge, because the paper wants to preserve Dung's abstract graph orientation while making attack success contingent on meta-level reasoning. *(p.904-905)*
- Reinstatement is defined over attacks rather than just arguments because meta-level preference disputes can recursively determine whether a first-order defense is actually available. *(p.906-907)*
- Hierarchical and preference symmetric restrictions are introduced not as arbitrary subclasses but because they recover monotonicity and hence constructive grounded semantics. *(p.910-914)*
- The ALP-DP encoding treats undercuts as preference-independent defeats, reflecting the intuition that attacking the applicability of a rule is categorically different from preferring one rebuttal over another. *(p.916-918)*

## Testable Properties
- If $A$ defeats$_S$ $B$, then for every $S' \subseteq S$, $A$ also defeats$_{S'}$ $B$. *(p.906)*
- Every stable extension of an EAF is a preferred extension, but not conversely. *(p.908)*
- In a bounded hierarchical EAF, the characteristic function is monotonic on conflict-free sets. *(p.910)*
- In a preference symmetric EAF, every argument inside a conflict-free set is ps-acceptable with respect to that set. *(p.913)*
- The grounded extension of a finitary preference symmetric EAF is obtained by iterating the characteristic function from $\emptyset$. *(p.913-914)*
- In the ALP-DP instantiation, if argument $A$ undercuts $B$, then $A$ defeats $B$ for every candidate set $S$; preference arguments cannot block undercuts. *(p.917-918)*
- Every subargument of an acceptable ALP-DP argument is itself acceptable in the corresponding EAF semantics. *(p.918, p.927-928)*
- For priority-finitary ALP-DP theories, the grounded extension of the original ALP-DP account matches the grounded extension of the instantiated EAF modulo composite priority arguments. *(p.919)*

## Relevance to Project
This paper is directly relevant to propstore's preference layer because it formalizes the exact issue the project faces: preferences should not merely rank outcomes externally, they must be represented as defeasible claims that can be challenged and reinstated. The paper also gives a clean semantics-level distinction between preference-dependent and preference-independent defeat, which is central for implementing robust argument resolution, especially when combining object-level claims, provenance-based preferences, and explicit reasons for those preferences. *(p.901-920)*

## Open Questions
- [ ] Which propstore conflicts should be modeled as preference-symmetric disputes versus asymmetric undercuts? *(p.912-918)*
- [ ] Does the project's intended preference language fit better with hierarchical EAFs, or does it need the full non-monotonic generality of unrestricted EAFs? *(p.909-914)*
- [ ] How should composite priority arguments be normalized in implementation so grounded computation matches Proposition 17 cleanly? *(p.919)*

## Related Work Worth Reading
- Dung (1995), "On the acceptability of arguments and its fundamental role in nonmonotonic reasoning, logic programming and n-person games" — the base semantics reused throughout. *(p.903-904, p.933)*
- Bench-Capon (2003), "Persuasion in practical argument using value-based argumentation frameworks" — the fixed-value-ordering approach that this paper generalizes. *(p.901-902, p.932)*
- Kakas and Moraitis (2003), "Argumentation based decision making for autonomous agents" — a logic-programming preference framework that the paper reconstructs in EAF form. *(p.903, p.919-920, p.932)*
- Prakken and Sartor (1997), "Argument-based extended logic programming with defeasible priorities" — the ALP-DP formalism instantiated in Section 7. *(p.903, p.914-920, p.934)*
- Prakken (2010), "An abstract framework for argumentation with structured arguments" — the structured-argumentation successor that moves from abstract EAFs to internal argument structure. *(collection context)*
- Modgil and Prakken (2014, 2018) — later ASPIC+ treatments that absorb the central lessons here into structured argumentation. *(collection context)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as [19]; the entire EAF construction is presented as an extension of Dung's abstract semantics.
- [[Amgoud_2002_ReasoningModelProductionAcceptable]] — cited as [3]; an earlier preference-based framework that assumes preferences externally rather than arguing about them inside the AF.
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — cited as the structured-argument successor that internalizes attacks and defeat types beyond the abstract EAF level.

### New Leads (Not Yet in Collection)
- Kakas and Moraitis (2003) — "Argumentation based decision making for autonomous agents" — decision-making formalism reconstructed within hierarchical EAFs.
- Modgil (2007) — "An abstract theory of argumentation that accommodates defeasible reasoning about preferences" — immediate precursor to the full EAF account.
- Prakken and Sartor (1997) — "Argument-based extended logic programming with defeasible priorities" — core ALP-DP formalism instantiated here.

### Cited By (in Collection)
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — cites and critiques this paper as another attack-removal approach that mishandles asymmetric conflicts.
- [[Modgil_2011_RevisitingPreferencesArgumentation]] — explicitly cites it as the unrestricted-rebut and asymmetric-attack predecessor that motivates the 2011 correction.
- [[Dunne_2011_WeightedArgumentSystemsBasic]] — cites it as the main EAF comparison point when contrasting weighted attacks with attacks on attacks.
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — cites it as part of the line of work leading to the later general account of preferences.

### Conceptual Links (not citation-based)
- [[Modgil_2011_RevisitingPreferencesArgumentation]] — Strong. Direct sequel that keeps the meta-level preference machinery but shifts conflict-freeness back to raw attacks instead of defeats.
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — Strong. Later, fuller preference account that absorbs this paper's EAF ideas into a broader structured-argumentation setting.
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — Moderate. EAFs reason about attacks on attacks at the abstract level; Prakken 2010 moves the same preference-sensitive issues into explicitly structured arguments.
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — Moderate. Competing answer to the same problem of how preferences should affect abstract argumentation semantics.
- [[Dunne_2011_WeightedArgumentSystemsBasic]] — Moderate. Alternative quantitative route for weakening attacks, using weights and budgets instead of meta-level arguments about the attacks.
