---
title: "Admissible and Restrained Revision"
authors: "Richard Booth, Thomas Meyer"
year: 2006
venue: "Journal of Artificial Intelligence Research 26"
doi_url: "https://doi.org/10.1613/jair.1874"
pages: "127-151"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-29T04:12:45Z"
---
# Admissible and Restrained Revision

## One-Sentence Summary
Identifies "admissible" revision as the principled subclass of Darwiche-Pearl iterated revision operators (including lexicographic and the new "restrained" revision) and provides exact representation theorems for restrained revision as the most conservative admissible operator. *(p.0)*

## Problem Addressed
The Darwiche-Pearl (1997) framework for iterated belief revision is too permissive: it admits Boutilier's "natural revision" which completely ignores the penultimate input. The paper argues that the DP arguments themselves lead to a smaller, principled class of operators ("admissible") and introduces the most conservative member of that class ("restrained revision"). *(p.0-1)*

## Key Contributions
- Definition of "admissible revision" as operators satisfying BAGM + (C1) + (C2) + (P), which excludes natural revision but includes DP's operator, lexicographic revision, and restrained revision *(p.5)*
- Introduction of "restrained revision" as the most conservative admissible operator *(p.11-12)*
- Exact axiomatic characterization of restrained revision (Theorem 2) *(p.12)*
- Proof that restrained revision = backwards revision (Papini) composed with natural revision *(p.17-18)*
- Principled framework for choosing between revision operators based on context *(p.18-20)*
- Discussion of complex epistemic states and supplementary postulates *(p.20-21)*

## Methodology
Formal analysis within the AGM/Darwiche-Pearl framework for iterated belief revision. Epistemic states are represented as total preorders on possible worlds. Revision operators are constrained by postulates and characterized via representation theorems. *(p.2-3)*

## Key Equations / Statistical Models

### AGM Postulates (reformulated for epistemic states)

$$
(E1)\ B(E * \alpha) = \text{Cn}(B(E * \alpha))
$$
Where: $E$ is an epistemic state, $*$ is a revision operator, $\alpha$ is a sentence, $B(E)$ is the belief set of $E$
*(p.2)*

$$
(E2)\ \alpha \in B(E * \alpha)
$$
*(p.2)*

$$
(E3)\ B(E * \alpha) \subseteq \text{Cn}(B(E) \cup \{\alpha\})
$$
*(p.2)*

$$
(E4)\ \text{If } \neg\alpha \notin B(E) \text{ then } B(E) \cup \{\alpha\} \subseteq B(E * \alpha)
$$
*(p.2)*

$$
(E5)\ \text{If } E = F \text{ and } \alpha \equiv \beta \text{ then } B(E * \alpha) = B(F * \beta)
$$
*(p.2)*

$$
(E6s)\ B(E * \alpha) \neq L \text{ iff } \alpha \text{ is satisfiable}
$$
*(p.3)*

### Darwiche-Pearl Postulates (semantic form)

$$
(CR1)\ \text{If } v, w \in [\alpha] \text{ then } v \preceq_E w \text{ iff } v \preceq_{E*\alpha} w
$$
*(p.4)*

$$
(CR2)\ \text{If } v, w \in [\neg\alpha] \text{ then } v \preceq_E w \text{ iff } v \preceq_{E*\alpha} w
$$
*(p.4)*

$$
(CR3)\ \text{If } v \in [\alpha], w \in [\neg\alpha] \text{ then } v \prec_E w \text{ implies } v \prec_{E*\alpha} w
$$
*(p.4)*

$$
(CR4)\ \text{If } v \in [\alpha], w \in [\neg\alpha] \text{ then } v \preceq_E w \text{ only if } v \preceq_{E*\alpha} w
$$
*(p.4)*

(CR1) states the relative ordering between $\alpha$-worlds remains unchanged after $\alpha$-revision; (CR2) same for $\neg\alpha$-worlds; (CR3) if an $\alpha$-world was strictly more plausible than a $\neg\alpha$-world before, it remains so; (CR4) requires the same for weak plausibility. *(p.4)*

### Key Postulate: Independence (P)

$$
(P)\ \text{If } \alpha \nvDash \neg\mu \text{ then } (\alpha \in B(E * \mu * \alpha) \text{ iff } \alpha \in B(E * \alpha))
$$
Where: $\mu$ is the revision input, $\alpha$ is any sentence not contradicting $\mu$
*(p.5)*

(P) requires that, after revising by $\mu$, the agent's view of any sentence $\alpha$ consistent with $\mu$ is at least as plausible as before the revision. This eliminates natural revision. *(p.5)*

### Strengthened Postulates

$$
(E5r)\ \text{If } E = F \text{ and } \alpha \equiv \beta \text{ then } E * \alpha = F * \beta
$$
*(p.3)*

$$
(E5s)\ \text{If } B(E) = B(F) \text{ then } \alpha \in B(E * \alpha + \beta) \text{ iff } \alpha \in B(F * \alpha + \beta)
$$
*(p.3)*

### Counteraction (Definition 3)

$$
s \text{ and } t \text{ counteract w.r.t. } E \text{, written } s \approx_E t, \text{ iff } \neg s \in B(E) \text{ and } \neg t \in B(E * s)
$$
Where: $s, t$ are sentences, $E$ is an epistemic state
*(p.9)*

Two sentences counteract when accepting $s$ causes $t$ to be rejected. *(p.9)*

### Restrained Revision Postulate (RR)

$$
(RR)\ \text{For } v \notin [\beta(E * \alpha)], \gamma \preceq_{E*\alpha} w \text{ iff } \begin{cases} v \preceq_E w & \text{if } v, w \in [\neg\alpha] \text{ or } v \in [\alpha] \\ v \preceq_{E*\alpha,u} w & \text{otherwise} \end{cases}
$$
*(p.11)*

(RR) says the relative ordering of valuations that are not $(\preceq_{E*\alpha})$-minimal remains unchanged, except for $\alpha$-worlds and $\neg\alpha$-worlds at the same plausibility level; these are split into two levels with the $\alpha$-worlds more plausible than the $\neg\alpha$-worlds. *(p.11-12)*

### Restrained Revision Operator Definition

$$
v \prec_q w \text{ implies } v \prec_{E*\alpha,u} w
$$
*(p.17)*

Given epistemic state $E$ and sentence $\alpha$, the restrained composite operator $\sigma_\alpha$ is defined as:

$$
E + \alpha := ((E \circ \neg\alpha) \circ \alpha)
$$
Where: $\circ$ denotes natural revision
*(p.17)*

This shows restrained revision is natural revision preceded by backwards revision (Papini). *(p.17-18)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Epistemic state | $E$ | - | - | - | 2 | Total preorder on valuations |
| Belief set | $B(E)$ | - | - | - | 2 | $\text{Cn}(\min(E, \preceq_E))$ |
| Plausibility ordering | $\preceq_E$ | - | - | - | 2 | Total preorder on worlds |
| Revision operator | $*$ | - | - | - | 2 | Maps $(E, \alpha)$ to new state |

## Methods & Implementation Details

### Operator Taxonomy (from most to least conservative)
1. **Restrained revision**: Most conservative admissible operator. Minimal changes to plausibility ordering. *(p.0, 11)*
2. **Darwiche-Pearl prototypical operator**: Intermediate admissible operator. *(p.1)*
3. **Lexicographic revision** (Nayak 1994): Least conservative admissible operator. All $\alpha$-worlds become more plausible than all $\neg\alpha$-worlds, maintaining internal ordering. *(p.8, 1)*
4. **Natural revision** (Boutilier 1996): NOT admissible. Completely ignores penultimate input. *(p.1, 6)*

### How Restrained Revision Works
- Given an epistemic state $E$ and new input $\alpha$:
  1. Apply backwards revision by $\neg\alpha$ (Papini's operator): this moves $\neg\alpha$-worlds up
  2. Apply natural revision by $\alpha$: this makes $\alpha$-worlds minimal
- The composite preserves the relative ordering of non-$\alpha$ worlds *(p.17-18)*
- The $\alpha$-worlds at the same plausibility level as $\neg\alpha$-worlds get split: $\alpha$-worlds go above, $\neg\alpha$-worlds stay *(p.11-12)*

### Postulate Relationships
- BAGM = (E1)-(E4) + (E5r) + (E6s) *(p.4)*
- DP-AGM = BAGM + (CR1)-(CR4) *(p.4)*
- Admissible = DP-AGM + (P) *(p.5, Definition 2)*
- Restrained = Admissible + (D) where (D) = stability condition *(p.11)*
- Full characterization: BAGM + (C1) + (C2) + (C1P) + (C2D) + (I) + (D) *(p.12, Theorem 2)*
- Compact: (C1) + (P) can replace (C1P), and (C2D) follows from other postulates *(p.14-15)*

### Key Propositions and Theorems
- **Proposition 1**: (E5-F) and (E6s-F) are equivalent given DP-AGM *(p.5)*
- **Proposition 2**: Under DP-AGM, $*$ satisfies (P) iff it satisfies (P') *(p.6)*
- **Proposition 3**: Counteraction characterized: $s \approx_E t$ iff there exist $v \in [s], w \in [\neg s]$ such that $v \prec_E w$ and $v \in [\neg t]$ or $w \in [t]$ *(p.9)*
- **Proposition 5**: Whenever a revision operator $*$ satisfies BAGM, $*$ satisfies (D) iff it satisfies stable *(p.11)*
- **Proposition 6**: Restrained revision satisfies (O) *(p.13)*
- **Proposition 7**: Restrained revision satisfies following property: $B(E) \cup B(E*\alpha)$ are both $E$-compatible, and $B(E) \not\subseteq B(E * \alpha * \beta)$ then follows from consistency of $B(E * \alpha * \beta)$ *(p.13)*
- **Proposition 9**: Compact syntactic representation of restrained revision *(p.14-15)*
- **Proposition 10**: Restrained revision satisfies only trivial postulate (not (CR3)) for stable epistemic states *(p.15)*
- **Proposition 11**: Restrained revision satisfies following property: (U) *(p.15)*
- **Proposition 14**: $\sigma_\alpha$ denotes restrained revision operator. Then $\sigma_\alpha = \alpha_{+,\alpha}$, i.e., restrained revision = backwards revision then natural revision *(p.18)*
- **Theorem 1**: Representation theorem for admissible operators *(p.12)*
- **Theorem 2**: BAGM + (C1), (C2), (C1P), (C2D), (I), (D) = exact characterization of restrained revision *(p.12)*
- **Theorem 3**: BAGM + (T1), (T2), (C1), (I), (D) = another exact characterization *(p.15)*

## Figures of Interest
- **Example 1 (p.5)**: Two atoms $p, q$; epistemic state showing how (E5r) strengthens (E5) — illustrates why DP-AGM needs strengthening
- **Example 2 (p.6)**: Darwiche-Pearl framework — creature that is a bird; counterexample showing natural revision ignores penultimate input
- **Example 3 (p.6)**: Similar to Example 2 but demonstrating how the postulate (D) works
- **Example 4 (p.10)**: John and Mary's murder — showing why (D) is a desirable property for iterated revision
- **Example 5 (p.18)**: Red creature — choosing between restrained and lexicographic revision based on source reliability
- **Example 6 (p.19)**: Sequence of inputs from a "fairly crude mechanism" — restrained revision more appropriate
- **Example 7 (p.19)**: Teaching a class of students — lexicographic revision more appropriate

## Results Summary
- Admissible revision is a well-motivated subclass of DP revision operators that excludes natural revision while including lexicographic and restrained revision *(p.0-1)*
- Restrained revision is uniquely characterized as the most conservative admissible operator *(p.11-12)*
- Restrained revision = backwards revision (Papini) + natural revision *(p.17-18)*
- The choice between operators depends on context: restrained for unreliable/noisy sources, lexicographic for highly reliable sources *(p.18-19)*
- For complex epistemic states, supplementary postulates are needed beyond the DP framework *(p.20-21)*

## Limitations
- The paper acknowledges that the question of which admissible operator to use in particular situations requires further research *(p.18)*
- Complex epistemic states (where an operator operates on complex epistemic states) need additional structure beyond what the paper provides *(p.20-21)*
- The paper does not provide supplementary postulates for complex epistemic states, noting this is beyond scope *(p.20)*
- The approach assumes simple epistemic states representable as total preorders on worlds *(p.2)*

## Arguments Against Prior Work
- **Against natural revision (Boutilier 1996)**: Natural revision completely ignores the penultimate input; the DP arguments themselves show this is unacceptable. (CR3) is too weak to prevent this. *(p.1, 6)*
- **Against the full DP framework as sufficient**: The DP postulates are too permissive — they admit natural revision. The framework needs the additional postulate (P) to be principled. *(p.1, 5)*
- **Against unconstrained lexicographic revision**: While admissible, lexicographic revision is the least conservative operator and makes maximal changes. It should not be the default. *(p.8, 18)*
- **Against treating "most recent is best" universally**: Lexicographic revision assumes the most recent input is always most reliable. This is inappropriate for noisy/unreliable sources. *(p.8, 18-19)*

## Design Rationale
- **Why admissibility?** The DP arguments against natural revision (penultimate input should not be completely ignored) lead directly to postulate (P), which defines admissibility. This is not an arbitrary restriction but follows from DP's own reasoning. *(p.1, 5)*
- **Why restrained revision?** As the most conservative admissible operator, it makes minimal changes to the plausibility ordering while still respecting the new input. This is appropriate when the source is unreliable or when we want to preserve as much of the prior state as possible. *(p.11, 18)*
- **Why not a single "best" operator?** Different contexts call for different operators. The paper advocates a principled approach to choosing operators based on source reliability and context. *(p.18-19)*
- **Composite operator design**: Showing restrained = backwards + natural makes it constructively implementable and connects to existing operator theory. *(p.17-18)*

## Testable Properties
- Admissible operators must satisfy (P): revising by $\mu$ then checking $\alpha$ (consistent with $\mu$) gives same result as checking $\alpha$ without the $\mu$ revision *(p.5)*
- Restrained revision must satisfy (D): stability condition — if $\alpha$ is already believed, revision by $\alpha$ is idempotent on the ordering *(p.11)*
- Restrained revision preserves relative ordering of non-minimal worlds *(p.11-12)*
- Lexicographic revision makes ALL $\alpha$-worlds more plausible than ALL $\neg\alpha$-worlds *(p.8)*
- Natural revision fails (P) — there exist cases where revising by $\mu$ then checking $\alpha$ gives different result *(p.6)*
- Restrained revision = backwards revision composed with natural revision (Proposition 14) *(p.18)*
- For any admissible operator: restrained $\preceq$ operator $\preceq$ lexicographic (in conservativeness ordering) *(p.0, 11)*

## Relevance to Project
This paper is directly relevant to propstore's argumentation and revision layers. The key question for propstore is whether ASPIC+ argumentation resolution and IC merging compose or are alternative render strategies. This paper provides:

1. **Formal revision operators** that could implement belief change when new claims enter the system
2. **The admissibility criterion** provides a principled constraint on how the system should revise its epistemic state — the penultimate input must not be completely ignored
3. **Restrained vs lexicographic choice** maps directly to propstore's render policy concept — different contexts (reliable vs unreliable sources) call for different revision strategies
4. **The composite operator construction** (backwards + natural) suggests that revision can be decomposed into simpler steps, which could be implemented as pipeline stages in the render layer
5. **The connection to AGM** via Dixon 1993 (already in the collection) means this paper bridges the argumentation world and the merging/revision world

The paper suggests that ASPIC+ argumentation and IC merging are NOT alternative render strategies but rather that argumentation provides the preference ordering while revision operators (admissible ones) implement the actual state change. They compose: argumentation determines WHAT defeats WHAT, revision operators determine HOW to update the epistemic state.

## Open Questions
- [ ] How does the admissibility criterion interact with ASPIC+ preference-based defeat?
- [ ] Can restrained revision be implemented using the ATMS label structure already in propstore?
- [ ] What is the relationship between "epistemic state as total preorder" and propstore's Subjective Logic opinions?
- [ ] Does the composite operator construction (backwards + natural) map to existing propstore pipeline stages?
- [ ] How do the supplementary postulates for complex epistemic states relate to propstore's multi-source reconciliation?

## Collection Cross-References

### Already in Collection
- [[Darwiche_1997_LogicIteratedBeliefRevision]] — foundational framework for iterated belief revision; this paper extends DP postulates with admissibility
- [[Alchourron_1985_TheoryChange]] — AGM postulates; this paper's BAGM is a reformulation for epistemic states
- [[Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic]] — epistemic entrenchment; related foundational AGM work
- [[Konieczny_2002_MergingInformationUnderConstraints]] — IC merging framework; key comparison point for whether merging and revision compose
- [[Bonanno_2010_BeliefChangeBranchingTime]] — cites this paper; branching-time belief revision extends iterated revision
- [[Baumann_2015_AGMMeetsAbstractArgumentation]] — AGM meets abstract argumentation; bridges same gap this paper addresses from the revision side
- [[Dixon_1993_ATMSandAGM]] — ATMS context switching = AGM operations; relevant for ATMS-based implementation of revision operators
- [[Spohn_1988_OrdinalConditionalFunctionsDynamic]] — cited for ordinal conditional functions; the epistemic state representation underlying all ranking-based revision operators discussed in this paper

### New Leads (Not Yet in Collection)
- Nayak (1994) — "Iterated belief change based on epistemic entrenchment" — lexicographic revision operator, the least conservative admissible operator
- Papini (2001) — "Iterated revision operations stemming from the history of an agent's observations" — backwards revision operator; restrained = backwards + natural
- Boutilier (1996) — "Iterated revision and minimal changes of conditional beliefs" — natural revision; the operator this paper argues against
- Friedman & Halpern (1999) — "Belief revision: A critique" — important critique of AGM framework limitations

### Cited By (in Collection)
- [[Bonanno_2010_BeliefChangeBranchingTime]] — cites this paper as [11] in its reference list

## Related Work Worth Reading
- Darwiche, A. & Pearl, J. (1997). On the logic of iterated belief revision. *Artificial Intelligence*, 89, 1-29. [Already referenced in collection as foundational] *(p.23)*
- Nayak, A. C. (1994). Iterated belief change based on epistemic entrenchment. *Erkenntnis*, 41. [Lexicographic revision] *(p.24)*
- Papini, O. (2001). Iterated revision operations stemming from the history of an agent's observations. In *Frontiers in belief revision*, pp. 281-303. [Backwards revision operator] *(p.24)*
- Booth, R. (2005). On the logic of iterated non-prioritised revision. In *Conditionality, Information and Inference*, pp. 86-107. [Non-prioritised extension] *(p.23)*
- Chopra, S., Ghose, A., & Meyer, T. (2003). Non-prioritised ranked belief change. *Journal of Philosophical Logic*, 32(3), 417-443. *(p.23)*
- Rott, H. (2003). Coherence and conservatism in the dynamics of belief II. *Journal of Logic and Computation*, 13(1), 111-145. [Two degrees of belief revision] *(p.24)*
- Jin, Y. & Thielscher, M. (2005). Iterated belief revision, revised. In *IJCAI 05*. *(p.23)*
- Friedman, N. & Halpern, J. Y. (1999). Belief revision: A critique. *Journal of Logic, Language and Information*, 8, 401-420. *(p.24)*
- Spohn, W. (1988). Ordinal conditional functions: A dynamic theory of epistemic states. In *Causation in Decision, Belief Change and Statistics*, Vol. 42, pp. 105-134. *(p.24)* -> NOW IN COLLECTION: [[Spohn_1988_OrdinalConditionalFunctionsDynamic]]
