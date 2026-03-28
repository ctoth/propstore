---
title: "A reasoning model based on the production of acceptable arguments"
authors: "Leila Amgoud, Claudette Cayrol"
year: 2002
venue: "Annals of Mathematics and Artificial Intelligence"
doi_url: "https://doi.org/10.1023/A:1014490210693"
pages: "197-215"
produced_by:
  agent: "gpt-5-codex"
  skill: "paper-reader"
  timestamp: "2026-03-28T07:56:55Z"
---
# A reasoning model based on the production of acceptable arguments

## One-Sentence Summary
Refines Dung-style abstract argumentation with explicit preference orderings over arguments, defining acceptability as the combination of self-defence by preference and defence by other arguments, then proves an equivalent AND/OR dialogue-tree proof theory for deciding membership in the resulting acceptable set. *(p.0, p.5-16)*

## Problem Addressed
Dung's acceptability semantics uses only the defeat graph and ignores the quality or strength of arguments, so it can reject a stronger argument merely because it is defeated by an acceptable but weaker argument, or accept a weaker argument because it is defended by other acceptable arguments. The paper aims to integrate preferences between arguments without collapsing them into the defeat relation, so that acceptability reflects both direct comparative strength and dialectical defence. *(p.1-4)*

## Key Contributions
- Defines a general preference-based argumentation framework that combines a defeat relation with a preorder over arguments instead of using defeat alone. *(p.1, p.5-7)*
- Introduces two complementary notions of defence: individual defence by being preferred to one's defeaters, and joint defence by being defended by other arguments. *(p.1, p.7-8)*
- Gives a revised acceptability semantics whose acceptable set is a least-fixpoint construction extending Dung's characteristic-function approach. *(p.3, p.8-9)*
- Instantiates the framework for inconsistency handling with rebut and undercut defeat relations over minimal consistent arguments from a propositional base. *(p.3-4, p.9)*
- Develops a dialogue-game proof theory using AND/OR trees and proves that probable acceptability exactly coincides with semantic acceptability. *(p.10-16)*

## Study Design (empirical papers)

Non-empirical theoretical paper. *(p.0-18)*

## Methodology
The paper starts from Dung's abstract argumentation framework, where arguments are abstract objects linked by a defeasibility relation, and extends it with a preference preorder over arguments. It then redefines attack, self-defence, collective defence, rejected arguments, and acceptable arguments in the combined framework. The semantic side is paired with a proof-theoretic side: dialogues between `PRO` and `OPP` are organized as AND/OR trees, candidate solution subtrees encode successful defence strategies, and complete winning trees characterize provably acceptable arguments. *(p.2-16)*

### Basic Abstract Framework
An argumentation framework is a pair of a set of arguments and a defeasibility relation. Three status classes are induced: acceptable arguments, rejected arguments defeated by acceptable ones, and arguments in abeyance that are neither accepted nor rejected. *(p.2-3)*

### Logic-Based Instantiation
For a propositional knowledge base `Σ`, an argument is a pair `(H, h)` where `H` is a minimal consistent support proving conclusion `h`. The paper uses two concrete defeat relations:
- `rebut`: one argument's conclusion is the negation of the other's conclusion. *(p.4)*
- `undercut`: one argument's conclusion negates a premise occurring in the other's support. *(p.4)*

### Preference Layer
Preferences are preorders on supports or arguments, typically induced by priorities on beliefs. The paper emphasizes explicit priorities and gives an elitist-lifting construction from stratified belief bases to preferences over supports, then lifts those support preferences to preferences over arguments. *(p.5-6)*

### Preference-Based Semantics
The key move is to define attack after consulting preference: an argument `B` attacks `A` only if `B` defeats `A` and `A` is not strictly preferred to `B`. Acceptability then proceeds in two stages:
- `C_{R,Pref}`: arguments that defend themselves against all defeaters by preference alone. *(p.7-8)*
- `Acc_{R,Pref}`: arguments in `C_{R,Pref}` plus those defended, directly or indirectly, by arguments already accepted. *(p.8-9)*

### Proof Theory
The proof theory simplifies membership checking by using strict defence and indirect defence, then encodes a defence search as a dialogue tree. `PRO` nodes are AND nodes because all defeaters must be answered; `OPP` nodes are OR nodes because one successful line of defence is enough. Winning solution subtrees correspond exactly to acceptable arguments. *(p.10-16)*

## Key Equations / Statistical Models

$$
\langle A, R \rangle
$$
Argumentation framework with argument set `A` and defeasibility relation `R \subseteq A \times A`; `A \, R \, B` means argument `A` defeats argument `B`. *(p.2)*

$$
C_R = \{A \in \mathcal{A} \mid \nexists B \in \mathcal{A} \text{ such that } B \, R \, A\}
$$
The class of acceptable arguments under the most cautious direct-defeat view: arguments with no defeaters. *(p.2)*

$$
Rej_R = \{A \in \mathcal{A} \mid \exists B \in C_R \text{ such that } B \, R \, A\}
$$
Rejected arguments are those defeated by an acceptable argument. *(p.3)*

$$
Ab_R = \mathcal{A} \setminus (C_R \cup Rej_R)
$$
Arguments in abeyance are neither acceptable nor rejected. *(p.3)*

$$
A \text{ is defended by } S \iff \forall B \in \mathcal{A},\, (B \, R \, A \Rightarrow \exists C \in S \text{ such that } C \, R \, B)
$$
Dung-style joint defence: every defeater of `A` is itself defeated by some member of `S`. *(p.3)*

$$
\mathcal{F}(S) = \{A \in \mathcal{A} \mid A \text{ is defended by } S\}
$$
Characteristic function returning the arguments acceptable with respect to defending set `S`. *(p.3)*

$$
Acc_R = \operatorname{lfp}(\mathcal{F})
$$
The acceptable arguments in the basic framework are the least fixpoint of the characteristic function. *(p.3)*

$$
(H, h)
$$
Argument built from knowledge base `\Sigma`, where `H \subseteq \Sigma` is consistent, `H \vdash h`, and `H` is minimal by set inclusion. *(p.4)*

$$
(H_1, h_1) \text{ rebuts } (H_2, h_2) \iff h_1 = \neg h_2
$$
Rebuttal defeat relation for logic-based arguments. *(p.4)*

$$
(H_1, h_1) \text{ undercuts } (H_2, h_2) \iff \exists h \in H_2 \text{ such that } h = \neg h_1
$$
Undercut defeat relation: the attack targets a premise in the opposing support. *(p.4)*

$$
\langle \mathcal{A}, R, Pref \rangle
$$
Preference-based argumentation framework, where `Pref` is a partial or complete preorder on arguments. *(p.6)*

$$
B \text{ attacks } A \iff B \, R \, A \text{ and } \neg(A \gg_{Pref} B)
$$
Defeat becomes an effective attack only when `A` is not strictly preferred to `B`. *(p.7)*

$$
A \text{ defends itself w.r.t. } Pref \iff B \, R \, A \Rightarrow A \gg_{Pref} B
$$
Individual defence: an argument can survive by outranking each direct defeater. *(p.7)*

$$
A \text{ is defended by } S \text{ w.r.t. } Pref \iff \forall B,\,(B \, R \, A \wedge \neg(A \gg_{Pref} B)) \Rightarrow \exists C \in S \text{ such that } C \, R \, B \wedge \neg(B \gg_{Pref} C)
$$
Joint defence in the preference-based framework only needs to answer defeaters not already neutralized by preference, and the defender itself must not be strictly outranked by the defeater. *(p.8)*

$$
\mathcal{F}(\varnothing) = C_{R,Pref}
$$
Applying the characteristic function to the empty set yields the set of arguments that defend themselves by preference. *(p.8)*

$$
Acc_{R,Pref} = \bigcup_{i \ge 0} \mathcal{F}^i(\varnothing) = C_{R,Pref} \cup \left[\bigcup_{i \ge 1} \mathcal{F}^i(C_{R,Pref})\right]
$$
Acceptable arguments in a finite preference-based framework are obtained by iterative closure from the self-defended core. *(p.8)*

$$
B \text{ indirectly attacks } A \iff \exists A_0,\ldots,A_{2n+1} \text{ with } A=A_0,\; B=A_{2n+1},\; \forall i<2n,\; A_{i+1} \text{ attacks } A_i
$$
Indirect attack is an odd-length attack chain. *(p.10-11)*

$$
B \text{ indirectly defends } A \iff \exists A_0,\ldots,A_{2n} \text{ with } A=A_0,\; B=A_{2n},\; \forall i<2n,\; A_{i+1} \text{ attacks } A_i
$$
Indirect defence is an even-length attack chain ending in `B`. *(p.11)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Argument set | `A` | - | finite set of arguments | - | 2 | Underlying universe of arguments in the abstract framework. |
| Defeasibility relation | `R` | - | binary relation on `A` | subset of `A × A` | 2 | Raw defeat relation before preferences are consulted. |
| Characteristic function | `\mathcal{F}` | - | defence-closure operator | maps `2^A -> 2^A` | 3 | Used for least-fixpoint computation of acceptable arguments. |
| Support set of an argument | `H` | - | minimal consistent subset of `\Sigma` | `H \subseteq \Sigma` | 4 | Carries the premises used to derive a conclusion. |
| Conclusion of an argument | `h` | formula | proposition proved from `H` | - | 4 | The claim established by the support set. |
| Preference preorder | `Pref` | - | partial or complete preorder | reflexive and transitive relation | 5-6 | Encodes comparative strength between supports or arguments. |
| Strict preference relation | `\gg_{Pref}` | - | induced from `Pref` | asymmetric part of preorder | 6 | Determines when a defeater is neutralized by superiority. |
| Self-defended core | `C_{R,Pref}` | set | arguments preferred to all direct defeaters | - | 7-8 | Individual-defence component of acceptability. |
| Acceptable set | `Acc_{R,Pref}` | set | least fixpoint generated from `C_{R,Pref}` | - | 8 | Final accepted arguments after iterated collective defence. |
| Dialogue move | `Move_i = (Player_i, Arg_i)` | - | sequence element in proof theory | - | 12 | `Player_i` alternates between `PRO` and `OPP`. |

## Effect Sizes / Key Quantitative Results

Non-empirical theoretical paper; no empirical effect-size table is reported. *(p.0-18)*

## Methods & Implementation Details
- The framework keeps defeat and preference independent, then derives effective attacks from both instead of rewriting the defeat graph up front. *(p.7)*
- Status computation still uses Dung's least-fixpoint architecture, but starts from a non-empty seed `C_{R,Pref}` of self-defending arguments. *(p.7-8)*
- Rebut and undercut are the two concrete defeat relations proposed for knowledge-base arguments. *(p.4)*
- Preferences over arguments are obtained from preferences over supports, with explicit priorities on beliefs highlighted as the practically important case. *(p.5-6)*
- In the elitist instantiation over a stratified base `\Sigma = \Sigma_1 \cup \cdots \cup \Sigma_n`, stronger supports are those containing better-ranked beliefs. *(p.6)*
- `Proposition 3.1` proves that the direct acceptable set `C_R` from the non-preference framework is included in `C_{R,Pref}`; adding preferences only enlarges the individually acceptable core. *(p.7)*
- `Definition 4.1` uses strict defence rather than general defence in the proof theory: to answer a defeater `B`, defender `C` must attack `B` without being attacked back by `B`. *(p.10)*
- `Proposition 4.1` shows that every acceptable argument is strictly defended by the whole acceptable set, which justifies the proof-theoretic simplification. *(p.10)*
- `Proposition 4.2` proves every acceptable argument is indirectly defended against all defeaters by acceptable arguments. *(p.11)*
- `Proposition 4.3` proves every rejected argument is indirectly attacked by some member of `C_{R,Pref}`. *(p.11)*
- A dialogue begins with `PRO` asserting the target argument; `OPP` replies with attackers, and later `PRO` replies with strict attackers of the immediately previous `OPP` move. `PRO` cannot repeat its own previous arguments in the same dialogue. *(p.12)*
- A dialogue tree is interpreted as an AND/OR tree: `PRO` nodes are AND because all defeaters must be countered; `OPP` nodes are OR because one successful line of defence suffices. *(p.13)*
- Candidate subtrees keep all edges under every AND node and exactly one edge under every OR node. A solution subtree is a candidate subtree in which all branches are won by `PRO`. *(p.14)*
- `Definition 4.7` requires completeness: for every `PRO` move, the children in the dialogue tree must be exactly all defeaters of the current argument. *(p.15)*

## Figures of Interest
- **Fig. 1 (p.13):** Dialogue tree for Example 4.2, illustrating a case where `PRO` wins by maintaining successful replies to every defeater of the root.
- **Fig. 2 (p.14):** Dialogue tree for Example 4.4, showing that `PRO` may end the whole dialogue while still losing local branches, motivating the need for solution subtrees rather than a naive "last move wins everywhere" criterion.
- **Fig. 3 (p.14):** Two candidate subtrees (`S_1`, `S_2`) extracted from the dialogue tree of Fig. 2; used to define solution subtrees formally.

## Results Summary
- The basic Dung framework partitions arguments into acceptable, rejected, and abeyance classes, but this is too coarse when argument strength matters. *(p.2-4)*
- In the preference-based framework, an argument is acceptable if it is not defeated or if it defends itself against its defeaters by preference, and arguments defended by acceptable arguments are then added by fixpoint iteration. *(p.7-9)*
- The preferred-argument semantics strictly generalizes the individual direct-acceptability view: `C_R \subseteq C_{R,Pref}`. *(p.7)*
- Example 3.2 demonstrates why purely individual defence is too weak: an argument may fail self-defence against a stronger defeater yet still be acceptable because another acceptable argument defeats that defeater. *(p.7-8)*
- Example 3.3 shows the framework handling inconsistency under both rebut and undercut, with acceptability depending on both priority structure and chains of defence. *(p.9-10)*
- `Proposition 4.4` proves that if `PRO` wins a dialogue then its last move belongs to `C_{R,Pref}`. *(p.13)*
- `Proposition 4.5` proves every leaf in a solution subtree belongs to `C_{R,Pref}` and indirectly defends the `PRO` arguments on its branch. *(p.14)*
- `Proposition 4.6` establishes the main equivalence theorem: an argument is provably acceptable exactly when it belongs to `Acc_{R,Pref}`. *(p.15)*

## Limitations
- The framework assumes a finite preference-based argumentation framework so that the iterative fixpoint definition is well-behaved. *(p.8)*
- The belief-level preference orderings emphasized in the paper are total preorders; the conclusion notes that contextual preferences require a later extension. *(p.5, p.16)*
- The proof theory is designed for membership testing of a single argument rather than computing the entire acceptable set directly. *(p.10)*
- The paper does not provide complexity bounds for the proof theory or the fixpoint procedure. *(p.10-16)*
- The framework remains abstract: it specifies rebut and undercut instances for inconsistency handling but does not integrate richer structured-argument notions like subarguments, strict rules, or explicit premise vulnerabilities. *(p.4, p.16)*

## Arguments Against Prior Work
- Dung's notion of acceptability ignores argument quality and can therefore accept weaker arguments or reject stronger ones purely because of defeat structure. *(p.4)*
- Earlier preference-based frameworks distinguished preference relations between arguments but did not provide a general unified abstract framework combining defeat and preferences at the semantic level. *(p.1-2)*
- Prakken and Sartor's prioritized setting is criticized as less direct because it embeds priorities inside the definition of defeat, adds a negation-by-failure style language, and masks the simpler interaction between preference and defence. *(p.1-2, p.10)*
- Existing negotiation/dialogue proposals make use of argumentation protocols, but largely do not address how generated and interpreted arguments fit into the negotiation process; the paper positions its dialogue proof theory as a better bridge between semantics and dialogue. *(p.16)*

## Design Rationale
- Keep `R` and `Pref` independent so preference does not erase conflict information; it only determines whether a defeater is effective as an attack. *(p.7)*
- Combine individual defence and joint defence because neither alone is sufficient: self-defence captures direct superiority, while collective defence captures dialectical support from other accepted arguments. *(p.1, p.7-8)*
- Seed the fixpoint with self-defending arguments `C_{R,Pref}` because this retains the intuition that some arguments are acceptable purely by their own strength. *(p.7-8)*
- Use strict defence in the proof theory because `Proposition 4.1` shows this restricted notion is enough for acceptable arguments, making the dialogue calculus operationally simpler. *(p.10)*
- Model proof search as AND/OR trees because defence obligations are asymmetric: `PRO` must answer every defeater, while `OPP` only needs one effective challenge on a branch. *(p.12-14)*

## Testable Properties
- If an argument has no defeaters, it belongs to `C_R` and therefore is acceptable in the cautious basic semantics. *(p.2-3)*
- `C_R \subseteq C_{R,Pref}`: adding preferences cannot remove already directly acceptable arguments from the individual-defence core. *(p.7)*
- `\mathcal{F}(\varnothing) = C_{R,Pref}` in the preference-based framework. *(p.8)*
- `Acc_{R,Pref}` is the least fixpoint generated by iterating `\mathcal{F}` from the empty set. *(p.8)*
- Every acceptable argument is strictly defended by `Acc_{R,Pref}`. *(p.10)*
- Every acceptable argument is indirectly defended against all its defeaters by acceptable arguments. *(p.11)*
- Every rejected argument is indirectly attacked by some argument in `C_{R,Pref}`. *(p.11)*
- If `PRO` wins a dialogue tree, the tree has a solution subtree and every leaf of that solution subtree belongs to `C_{R,Pref}`. *(p.13-14)*
- An argument is provably acceptable if and only if it belongs to `Acc_{R,Pref}`. *(p.15)*

## Relevance to Project
This paper is directly relevant to propstore's preference-sensitive argumentation layer because it is the original abstract preference-based argumentation framework that later work, especially Amgoud and Vesic (2011), critiques. Its central design move is useful for implementation: do not destroy defeats when a preference exists; instead, keep conflict structure intact and let preference determine whether a defeater counts as an effective attack. The dialogue-tree proof theory is also relevant for explanation and interactive inspection, since it gives a constructive witness for why a claim is acceptable. *(p.1, p.7-16)*

## Open Questions
- [ ] How should this paper's self-defence core `C_{R,Pref}` be reconciled with structured argument frameworks like ASPIC+ that distinguish rebut, undermine, and undercut more finely?
- [ ] Does propstore want the exact `Acc_{R,Pref}` fixpoint or only the proof-theoretic explanation layer built from dialogue trees?
- [ ] How should contextual preferences from the paper's cited extension be represented in propstore's stance and provenance model?
- [ ] Which parts of Amgoud and Vesic's 2011 critique target this paper's attack definition specifically, and which target the broader attack-removal family?

## Related Work Worth Reading
- Dung 1995, "On the acceptability of arguments and its fundamental role in non-monotonic reasoning, logic programming and n-person games." *(p.17-18)*
- Elvang-Goransson et al. 1993, "Dialectic reasoning with inconsistent information." *(p.18)*
- Prakken and Sartor 1996/1997/1998 on legal reasoning, dynamic priorities, and argumentation with prioritized logic. *(p.17-18)*
- Simari and Loui 1992, "A mathematical treatment of defeasible reasoning and its implementation." *(p.18)*
- Amgoud, Parsons, and Maudet 2000, "Modelling dialogues using argumentation," for the dialogue setting the proof theory points toward. *(p.17)*
- Amgoud, Parsons, and Prade 2000, "A dialogue framework based on argumentation," which the conclusion cites as fitting negotiation contexts. *(p.17)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as [11]; provides the characteristic-function and least-fixpoint acceptability semantics that this paper extends with an explicit preference layer.
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] — cited as [21]; the logic-based rebut/undercut tradition this paper uses for its concrete argument instantiation over inconsistent knowledge bases.
- [[Vreeswijk_1997_AbstractArgumentationSystems]] — cited as [23]; another abstract defeasible framework in the background literature for comparing argument-status semantics.

### New Leads (Not Yet in Collection)
- Amgoud and Cayrol (1998) — "On the acceptability of arguments in preference-based argumentation framework" — immediate predecessor that isolates the preference-based acceptability idea this paper generalizes.
- Amgoud, Parsons, and Perrussel (2000) — "An argumentation framework based on contextual preferences" — follow-on extension explicitly named in the conclusion as the path beyond total preorders.
- Amgoud, Parsons, and Maudet (2000) — "Modelling dialogues using argumentation" — dialogue setting that motivates the paper's proof-theoretic game view.
- Prakken and Sartor (1996/1997/1998) — prioritized legal-argumentation models this paper criticizes for baking priority handling into defeat.

### Cited By (in Collection)
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — critiques this paper as the original preference-based attack-removal approach and argues that removing attacks loses essential conflict information.
- [[Amgoud_2008_BipolarityArgumentationFrameworks]] — cites it as [AC02b] when surveying extensions of Dung AFs that enrich conflict handling beyond plain defeat.
- [[Caminada_2007_EvaluationArgumentationFormalisms]] — uses it as one of the preference-sensitive formalisms whose behavior is evaluated against rationality postulates.
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — cites it as an earlier abstract preference-based approach that motivates richer structured defeat relations.
- [[Brewka_2010_AbstractDialecticalFrameworks]] — cites it as a Dung-style extension that ADFs aim to generalize and subsume.

### Conceptual Links (not citation-based)
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — Strong. Same preference-based setting, but the 2011 paper attacks this model's attack-removal design directly and replaces it with a semantics-level dominance relation to preserve conflicts.
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — Moderate. Later preference theory that similarly insists preferences should determine winners of conflicts without erasing the underlying attack relation.
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — Moderate. Moves from abstract preference-based acceptability to structured arguments with explicit undermine/rebut/undercut defeat and orderings.
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — Moderate. Extends Dung in a different direction by adding support relations, but shares the same motivation of not forcing richer argument interaction into plain attack deletion.
- [[Prakken_2006_FormalSystemsPersuasionDialogue]] — Moderate. Connects to the dialogue-tree proof theory here by treating argumentative interaction as an operational protocol rather than only a semantic fixpoint.
