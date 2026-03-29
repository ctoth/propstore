---
title: "Belief Change in Branching Time: AGM-consistency and Iterated Revision"
authors: "Giacomo Bonanno"
year: 2012
venue: "Journal of Philosophical Logic"
doi_url: "https://doi.org/10.1007/s10992-011-9202-6"
pages: "201-236"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-29T03:06:05Z"
---
# Belief Change in Branching Time: AGM-consistency and Iterated Revision

## One-Sentence Summary

Provides the formal bridge between branching-time temporal structures and AGM belief revision, proving that a frame property (PLS) is equivalent to AGM-consistency, and introduces iterated belief revision functions as ternary operations B(h, K, phi) that take informational history into account.

## Problem Addressed

The AGM theory of belief revision and Hintikka-style modal logic for static belief existed as two separate strands. No framework connected temporal branching structures (where an instant can have multiple successors representing different informational inputs) to the AGM postulates. The key question: under what conditions can the partial belief revision function induced by a branching-time frame be extended to a full AGM belief revision function?

## Key Contributions

1. **AGM-consistency equivalence (Proposition 6):** Three equivalent characterizations of AGM-consistent frames when Omega is finite: (a) every partial belief revision function extends to a full AGM function, (b) existence of a rationalizing total pre-order R, (c) the directly-verifiable frame property PLS *(p.13)*
2. **Modal axiomatization (Proposition 9):** Five axiom schemas that characterize the class of AGM-consistent branching-time belief revision frames within the modal logic of [8] *(p.17)*
3. **Iterated belief revision functions (Definition 11):** A ternary function B: H x K x Phi -> 2^Phi taking informational history h, current belief set K, and new information phi, yielding revised beliefs *(p.23)*
4. **Semantic properties for iterated revision:** REFweak (implied by AGM), REF (refinement), REFstrong (conjunction), and their modal axiom characterizations *(p.19-20)*

## Methodology

Formal mathematical analysis within branching-time temporal logic. Defines branching-time belief revision frames as tuples <T, successor, Omega, {I_t, B_t}> where T is a set of instants with branching successor relation, Omega is states, I_t is information relation, B_t is belief relation. Proves equivalences between semantic frame properties and syntactic modal axioms. All proofs in appendix.

## Key Equations / Statistical Models

### Branching-time belief revision frame (Definition 3)

A frame $\langle T, \succ, \Omega, \{I_t, B_t\}_{t \in T} \rangle$ satisfying:

1. $B_t(\omega) \subseteq I_t(\omega)$ (information is believed)
2. $B_t(\omega) \neq \emptyset$ (beliefs are consistent)
3. If $t \succ t'$, $t \succ t''$ and $I_{t'}(\omega) = I_{t''}(\omega)$ then $B_{t'}(\omega) = B_{t''}(\omega)$ (same information => same beliefs)
4. If $t \succ t'$ and $B_t(\omega) \cap I_{t'}(\omega) \neq \emptyset$ then $B_{t'}(\omega) = B_t(\omega) \cap I_{t'}(\omega)$ (Qualitative Bayes Rule)

*(p.6)*

### Initial belief set at state-instant pair

$$
K_{M,\omega,t} = \{\phi \in \Phi : B_t(\omega) \subseteq \|\phi\|_M\}
$$

Where: K is the set of formulas believed at (omega, t), B_t(omega) is the set of doxastically possible states, ||phi||_M is the truth set of phi in model M.
*(p.10)*

### Partial belief revision function

$$
B_{K_{M,\omega,t}}(\phi) = \{\psi \in \Phi : B_{t'}(\omega) \subseteq \|\psi\|_M \text{ for } t' \in \succ t \text{ with } I_{t'}(\omega) = \|\phi\|_M\}
$$

Where: the revised beliefs given information phi are the formulas true at all states doxastically possible at the successor instant where the agent is informed that phi.
*(p.10)*

### AGM-consistency equivalence property PLS (Proposition 6, part c)

For all $u_0, u_1, \ldots, u_n \in \succ t$ with $u_n = u_0$:

$$
\text{If } I_{u_{k-1}}(\omega) \cap B_{u_k}(\omega) \neq \emptyset, \forall k = 1,\ldots,n
$$
$$
\text{then } I_{u_{k-1}}(\omega) \cap B_{u_k}(\omega) = B_{u_{k-1}}(\omega) \cap I_{u_k}(\omega), \forall k = 1,\ldots,n
$$

Where: u_0 through u_n are immediate successors of t forming a cycle, I is information relation, B is belief relation.
*(p.13)*

### Rationalizability condition (Proposition 6, part b)

$$
B_t(\omega) = best_{R_{\omega,t}} I_t(\omega) \quad \text{and} \quad \forall t' \text{ with } t \succ t': B_{t'}(\omega) = best_{R_{\omega,t}} I_{t'}(\omega)
$$

Where: $best_R E = \{\omega \in E : \omega R \omega', \forall \omega' \in E\}$ selects the most plausible states according to total pre-order R.
*(p.13)*

### Iterated belief revision function (Definition 11)

$$
B: H \times \mathcal{K} \times \Phi \to 2^\Phi
$$

Where: H is the set of sequences in Phi (histories of informational inputs), K is the set of deductively closed belief sets, Phi is the propositional language. B must satisfy all 8 AGM postulates parameterized by history h.
*(p.23)*

### REFweak (Lemma 10)

$$
\text{If } I_{t_3}(\omega) = I_{t_2}(\omega) \subseteq I_{t_1}(\omega) \text{ and } B_{t_1}(\omega) \cap I_{t_2}(\omega) \neq \emptyset, \text{ then } B_{t_2}(\omega) = B_{t_3}(\omega)
$$

Where: t_1, t_3 are immediate successors of t, t_2 is immediate successor of t_1. This says: if later evidence refines earlier evidence and is compatible with revised beliefs, the two-step and one-step revisions agree.
*(p.19)*

### REFstrong

$$
\text{If } I_{t_2}(\omega) \cap I_{t_1}(\omega) \neq \emptyset \text{ and } I_{t_3}(\omega) = I_{t_2}(\omega) \cap I_{t_1}(\omega), \text{ then } B_{t_2}(\omega) = B_{t_3}(\omega)
$$

Where: strengthening of REF saying that consistent sequential information has cumulative effect.
*(p.20)*

### Iterated REFweak (Lemma 12)

$$
\text{If } \neg\psi \notin B(h, K, \phi), \text{ then } B(h\phi, B(h,K,\phi), \psi) = B(h, K, \phi \wedge \psi)
$$

Where: if psi is compatible with revised beliefs after phi, then revising further by psi equals revising once by (phi AND psi).
*(p.24)*

## Parameters

This is a pure formal theory paper with no empirical parameters.

## Methods & Implementation Details

### Branching-time frame structure *(p.6-7)*
- T is a set of instants with binary relation successor (each instant has at most one predecessor but potentially many successors)
- Omega is a finite set of states (possible worlds)
- For each instant t: I_t is the information relation, B_t is the belief relation (both binary on Omega)
- A valuation V: S -> 2^Omega maps atomic formulas to truth sets, making truth state-dependent but time-independent (this is belief revision, not belief update)

### Four frame properties (Definition 3) *(p.6)*
1. B_t(omega) subset I_t(omega) — information is believed
2. B_t(omega) non-empty — beliefs are consistent
3. Same-information-same-beliefs at sibling instants
4. Qualitative Bayes Rule (QBR): if prior beliefs intersect new information, posterior = intersection

### Modal language *(p.16)*
- Four operators: next-time box, belief B, information I, all-state A
- Information operator I restricted to Boolean (non-modal) formulas only
- Information uses equality condition: I_t(omega) = ||phi|| (not just subset — captures "informed precisely that phi")
- Truth defined at state-instant pairs (omega, t)

### Five axiom schemas for AGM-consistency (Proposition 9) *(p.17)*
1. I(phi) -> B(phi) — information is believed
2. B(phi) -> not B(not phi) — beliefs are consistent
3. Diamond(I(phi) AND B(psi)) -> Box(I(phi) -> B(psi)) — same info yields same beliefs
4a. (not B(not phi) AND B(psi)) -> Box(I(phi) -> B(psi)) — QBR consequence
4b. not B(not(phi AND not psi)) -> Box(I(phi) -> not B(psi)) — QBR consequence
5. Complex cyclic axiom characterizing PLS property *(p.17)*

### Choice-theoretic foundation *(p.29)*
- Belief revision at a state-instant pair corresponds to a choice structure <Omega, E, f> where E = {I_t(omega) : t in successors} and f(E) = B_t(omega)
- Hansson's 1968 theorem (Proposition 15): a choice function is rationalizable by a total pre-order iff it satisfies a consistency condition on cyclic sequences
- The QBR-extension lemma (Lemma 17) bridges from successor-only rationalizability to full rationalizability including the current instant

### Belief state as triple *(p.25)*
- A belief state is (h, K, b) where h is history, K is current beliefs, b(psi) = B(h, K, psi) is the one-step revision function
- Upon receiving information phi: new state is (h.phi, B(h,K,phi), b') where b'(psi) = B(h.phi, B(h,K,phi), psi)
- This answers Rott's question about how revision functions (= belief states) get revised

### Connection to Darwiche-Pearl postulates *(p.24)*
- DP2 is expressible as: if phi AND psi is inconsistent while each is consistent, then B(h.phi, B(h,K,phi), psi) = B(h, K, psi)
- REFstrong implies order-irrelevance of consistent information (property 11)

## Figures of Interest

- **Fig 1 (p.8):** Non-AGM-consistent branching-time belief revision frame with 5 states {alpha, beta, gamma, delta, epsilon}, tree T = {t0, t1, t2, t3, t4, t5}. Shows how cyclic preference reversals (alpha > beta > epsilon > alpha) violate PLS.
- **Fig 2 (p.14):** AGM-consistent frame with 4 states. Shows rationalizable belief revision where different total pre-orders rationalize different state-instant pairs, and rankings can reverse across time.
- **Fig 3 (p.20):** Locally rationalizable frame violating REF. Shows how disposition to revise can change after intermediate information, even when later information refines earlier.
- **Fig 4 (p.23):** AGM-consistent frame demonstrating history-dependence: same belief set K at two state-instant pairs but different informational histories lead to different revised beliefs upon receiving the same information.

## Results Summary

The main results are Propositions 6 and 9:
- **Proposition 6:** For finite Omega, three conditions are equivalent: AGM-consistency (extendability of partial to full AGM revision), rationalizability by a total pre-order, and the directly-verifiable frame property PLS. The equivalence of (b) and (c) holds even for infinite Omega (Remark 18). *(p.13)*
- **Proposition 9:** Five modal axiom schemas characterize the class of AGM-consistent branching-time belief revision frames. *(p.17)*
- **Lemma 10:** AGM-consistency implies REFweak (refinement of information preserves beliefs when compatible). REFweak is the only restriction AGM imposes on iterated revision. *(p.19)*
- **Lemma 12:** The iterated-function counterpart of REFweak: information phi followed by compatible psi equals one-step revision by (phi AND psi). *(p.24)*

## Limitations

- Finite Omega required for the (a)<=>(b) direction of Proposition 6 (the choice-theoretic proof uses Proposition 20 from [10] which requires finiteness). The (b)<=>(c) equivalence holds for infinite Omega. *(p.13, Remark 18)*
- Only single-agent setting. Multi-agent extension left to future work. *(p.27)*
- No integration of time uncertainty (the agent always knows what time it is). *(p.27, Footnote 32)*
- The analysis is restricted to belief revision (truth is state-dependent, time-independent). Belief update (where facts change over time) is excluded. *(p.9)*

## Arguments Against Prior Work

- **Dynamic Doxastic Logic (DDL)** uses infinitely many modal operators (one per formula phi) whereas Bonanno's logic uses only three operators (temporal, belief, information). DDL lacks an explicit temporal operator. *(p.27)*
- **Dynamic Epistemic Logic (DEL)** does not give time an explicit role, offering "very limited flexibility in terms of describing beliefs through time." *(p.27)*
- **Epistemic Temporal Logic (ETL)** models beliefs through time but gives "little structure" to the causes of belief change; information does not play an explicit role. *(p.27)*
- Board's [7] approach also uses infinitely many modal operators B_phi. *(p.27)*

## Design Rationale

- **Branching time (not linear)** because AGM postulates require comparing revised belief sets arising from *different* informational inputs, which necessitates multiple successor instants. *(p.2)*
- **Information as equality I_t(omega) = ||phi||** (not just subset) captures "informed precisely that phi" — the agent learns that phi and nothing more. This corresponds to Humberstone/Levesque's "all I know" / "only knowing." *(p.2, 9, 16)*
- **Qualitative Bayes Rule** is the qualitative analog of Bayesian updating: when prior beliefs intersect new information, posterior beliefs = intersection. This is necessary for Proposition 6. *(p.7)*
- **Ternary iterated revision B(h, K, phi)** instead of unary or binary because the same belief set K can arise from different informational histories, leading to different revision dispositions. Figure 4 demonstrates this concretely. *(p.21-23)*

## Testable Properties

- **PLS is directly verifiable on frames:** Given a branching-time belief revision frame, one can check AGM-consistency by testing PLS on all cyclic sequences of successors. *(p.13)*
- **QBR is necessary:** Any frame violating the Qualitative Bayes Rule cannot satisfy Proposition 6. *(p.12)*
- **REFweak is implied by AGM:** If a frame is AGM-consistent, then REFweak holds. A frame satisfying AGM-consistency but violating REF is possible. *(p.19)*
- **History-dependence is genuine:** Same K at different state-instant pairs with different histories can yield different revised beliefs for the same information. This is testable by constructing concrete frames. *(p.22)*
- **AGM-consistency does not constrain iterated revision beyond REFweak:** The only restriction AGM places on how epistemic states evolve is Lemma 10/12. Stronger principles (REF, REFstrong, DP2) require additional frame properties. *(p.18-19)*

## Relevance to Project

This paper is directly relevant to propstore's need for formalizing belief revision in branching contexts. The branching-time structure maps naturally to git-like version control: each branch point is an instant with multiple successors representing different informational inputs (commits). The AGM-consistency property (PLS) provides a concrete, checkable criterion for when a branching belief structure is "well-behaved" — i.e., when partial revision functions can be extended to full AGM functions. The iterated revision functions B(h, K, phi) provide the formal machinery for tracking how informational history affects revision disposition, which is exactly what propstore needs for its ATMS-backed multi-context reasoning. The connection to choice functions (Hansson 1968) and rationalizability by plausibility orderings also connects to propstore's existing plausibility/preference ordering infrastructure.

## Open Questions

- [ ] Can PLS be checked efficiently for propstore's typical frame sizes, or is the cyclic enumeration combinatorially expensive?
- [ ] How does the finite-Omega restriction interact with propstore's potentially large state spaces?
- [ ] Can the REFstrong property be enforced in propstore's branching model, or is REFweak the natural level?
- [ ] How does the ternary B(h, K, phi) map onto propstore's ATMS assumption sets and context-switching?
- [ ] Extension to multi-agent settings (multiple agents with different beliefs about the same propositions)

## Related Work Worth Reading

- **Bonanno 2007 [8]:** The foundational paper introducing branching-time belief revision frames and the modal logic. Essential prerequisite.
- **Darwiche & Pearl 1997 [13]:** Iterated belief revision postulates (DP1-DP4). Already in propstore's scope.
- **Nayak, Pagnucco & Peppas 2003 [29]:** Dynamic belief revision operators, REFstrong/"Conjunction" postulate. Detailed analysis of iterated revision principles.
- **Hansson 1968 [21]:** Choice structures and preference relations. The choice-theoretic foundation underlying rationalizability results.
- **Rott 1999 [34]:** "A revision function IS a belief state." Philosophical foundations for why iterated revision needs to track epistemic states, not just belief sets.

## Collection Cross-References

### Already in Collection
- [[Alchourron_1985_TheoryChange]] — cited as [1], the original AGM postulates paper. Bonanno's entire framework tests compatibility with these postulates.
- [[Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic]] — cited as [20], the standard AGM reference for detailed exposition of the postulates and epistemic entrenchment.
- [[Dixon_1993_ATMSandAGM]] — not directly cited but deeply relevant: Dixon proved ATMS context switching is behaviorally equivalent to AGM operations. Bonanno's branching-time frames provide the formal temporal structure that Dixon's result operates within.

### New Leads (Not Yet in Collection)
- Bonanno (2007) — "Axiomatic characterization of the AGM theory of belief revision in a temporal logic", Artificial Intelligence 171: 144-160 — the foundational predecessor to this paper, introducing branching-time belief revision frames
- Darwiche & Pearl (1997) — "On the logic of iterated belief revision", Artificial Intelligence 89: 1-29 — iterated revision postulates (DP1-DP4), expressible in Bonanno's ternary function framework
- Nayak, Pagnucco & Peppas (2003) — "Dynamic belief revision operators", Artificial Intelligence 146: 193-228 — REFstrong/Conjunction postulate analysis
- Hansson (1968) — "Choice structures and preference relations", Synthese 18: 443-458 — choice-theoretic foundation for rationalizability results
