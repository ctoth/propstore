---
title: "Axiomatic Characterization of the AGM Theory of Belief Revision in a Temporal Logic"
authors: "Giacomo Bonanno"
year: 2007
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/j.artint.2006.12.001"
pages: "144-160"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-29T04:19:11Z"
---
# Axiomatic Characterization of the AGM Theory of Belief Revision in a Temporal Logic

## One-Sentence Summary
Provides a complete axiomatic characterization of the AGM belief revision postulates within a branching-time temporal logic, showing that the basic postulates (K*1-K*6) correspond to logic L_b and the full postulates (K*1-K*8) correspond to logic L_AGM, both interpreted over temporal belief revision frames with the Qualitative Bayes Rule as the core semantic property.

## Problem Addressed
The literature treats static beliefs (via modal logic with Kripke semantics) and belief change (via AGM theory with belief sets) as separate frameworks with different formalisms. There is no unified logic that captures both the doxastic state and its evolution over time in response to information. *(p.1)*

## Key Contributions
- Defines temporal belief revision frames combining branching-time structure with belief and information operators *(p.3)*
- Introduces the Qualitative Bayes Rule (QBR) as the core semantic property governing how beliefs update in response to information *(p.8)*
- Provides logic L_b that axiomatically characterizes AGM postulates K*1-K*6 (basic revision) *(p.9, Proposition 7)*
- Provides logic L_AGM that axiomatically characterizes the full set of AGM postulates K*1-K*8 *(p.17, Proposition 12)*
- Shows that the branching-time frame structure naturally captures both single-shot and iterated revision *(p.21)*
- Proves soundness of both logics with respect to their respective frame classes *(p.6, Proposition 4)*

## Methodology
The paper defines a modal logic with five operators (next-time, inverse next-time, belief, information, all-state) interpreted over temporal belief revision frames. It then proves representation theorems: the axioms of the logic exactly characterize the class of frames satisfying the AGM postulates, in the sense that (A) every frame validates the logic iff it satisfies the corresponding frame conditions, and (B) for every AGM-compliant revision function, there exists a model in the frame class that realizes it.

## Key Equations / Statistical Models

### Temporal Belief Revision Frame (Definition 1)

$$
\langle T, \rightarrowtail, \Omega, \{\mathcal{B}_t\}_{t \in T}, \{\mathcal{I}_t\}_{t \in T} \rangle
$$
Where: $T$ = set of instants (time points), $\rightarrowtail$ = successor relation on $T$ (injective), $\Omega$ = set of states, $\mathcal{B}_t$ = belief relation at time $t$ ($\mathcal{B}_t \subseteq \Omega \times \Omega$), $\mathcal{I}_t$ = information relation at time $t$ ($\mathcal{I}_t \subseteq \Omega \times \Omega$)
*(p.3)*

### Frame Properties (Definition 1)

$$
\text{(i) uniqueness: if } t_1 \rightarrowtail t_2 \text{ and } t_1 \rightarrowtail t_3 \text{ then } t_2 = t_3
$$
$$
\text{(ii) acyclicity: if } (t_1, ..., t_n) \text{ is a sequence with } t_i \rightarrowtail t_{i+1} \text{ then } t_1 \neq t_n
$$
$$
\text{(iii) for every } t = 1, ..., n-1, t_i \text{ has at most a unique immediate successor}
$$
Where: property (i) means each instant has at most one immediate successor (forward determinism), property (ii) prevents cycles
*(p.3)*

### Qualitative Bayes Rule (QBR)

$$
\text{if } t_1 \rightarrowtail t_2 \text{ and } \mathcal{B}_{t_1}(\omega) \cap \mathcal{I}_{t_2}(\omega) \neq \varnothing \text{ then } \mathcal{B}_{t_2}(\omega) = \mathcal{B}_{t_1}(\omega) \cap \mathcal{I}_{t_2}(\omega)
$$
Where: $\mathcal{B}_t(\omega)$ = set of states considered possible (believed) at state $\omega$ and time $t$, $\mathcal{I}_t(\omega)$ = set of states compatible with information received at time $t$
*(p.8)*

### Truth Conditions for Modal Operators

$$
(\omega, t) \models B\phi \quad \text{iff} \quad \mathcal{B}_t(\omega) \subseteq \lceil\phi\rceil_t
$$
$$
(\omega, t) \models I\phi \quad \text{iff} \quad \mathcal{I}_t(\omega) = \lceil\phi\rceil_t
$$
$$
(\omega, t) \models A\phi \quad \text{iff} \quad \lceil\phi\rceil_t = \Omega
$$
Where: $\lceil\phi\rceil_t = \{\omega \in \Omega : (\omega,t) \models \phi\}$ is the truth set of $\phi$ at time $t$. Note the equality (not subset) condition for $I$ -- information determines the truth set exactly.
*(p.5)*

### Logic L_b (Basic AGM Characterization)

$$
\mathbb{L}_b = \mathbb{L}_0 + A + ND + NA + WC
$$
Where: $\mathbb{L}_0$ = base temporal logic, the four added axiom schemas are:

- $A$ (Acceptance): $I\phi \to B\phi$ -- if informed that $\phi$, believe $\phi$ *(p.7)*
- $ND$ (No Drop): $\neg(I\phi \wedge B\psi) \to \bigcirc(I\phi \to \neg B\psi)$ -- if not currently informed of $\phi$ and believing $\psi$, then at next instant when informed of $\phi$, don't believe $\psi$ (unless forced) *(p.7)*
- $NA$ (No Add): $\neg B\neg(\phi \wedge \neg\psi) \to \bigcirc(I\phi \to \neg B\psi)$ -- if $\phi \wedge \neg\psi$ is not disbelieved, then at the next instant when informed of $\phi$, don't add $\psi$ *(p.8)*
- $WC$ (Weak Consistency): $(I\phi \wedge \neg A\neg\phi) \to (B\psi \to \neg B\neg\psi)$ -- if informed of consistent information, beliefs are consistent *(p.8)*

*(p.7-8)*

### Logic L_AGM (Full AGM Characterization)

$$
\mathbb{L}_{AGM} = \mathbb{L}_b + K7 + K8
$$
Where the two additional axiom schemas are:

- $K7$: $\bigcirc(I\phi \wedge B\psi) \to \bigcirc(\neg I(\phi \wedge \psi) \vee B(\phi \to \psi))$ *(p.9)*
- $K8$: $\bigcirc(I(\phi \wedge \psi) \wedge B(\phi \to \psi)) \to \bigcirc(I\phi \wedge \psi \to B\psi)$ *(p.9)*

*(p.9)*

### CAR Frame Condition (Definition 8)

$$
\text{if } t_1 \rightarrowtail t_2, t_1 \rightarrowtail t_3, \mathcal{I}_{t_2}(\omega) \subseteq \mathcal{I}_{t_3}(\omega) \text{ and } \mathcal{I}_{t_2}(\omega) \cap \mathcal{B}_{t_1}(\omega) \neq \varnothing
$$
$$
\text{then } \mathcal{B}_{t_2}(\omega) = \mathcal{B}_{t_3}(\omega) \cap \mathcal{I}_{t_2}(\omega)
$$
*(p.10)*

### Backward Uniqueness Axiom

$$
\Diamond^{-1}\phi \to \bigcirc^{-1}\phi \quad (BU)
$$
Where: $\Diamond^{-1}\phi \stackrel{def}{=} \neg\bigcirc^{-1}\neg\phi$ means "at some previous instant $\phi$", and the axiom forces at most one predecessor per instant.
*(p.5)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Set of instants | T | - | - | finite or infinite | 3 | Time points in the frame |
| Set of states | Omega | - | - | non-empty | 3 | Possible worlds |
| Successor relation | -> | - | - | injective, acyclic | 3 | Forward time step |
| Belief relation | B_t | - | - | B_t(w) subset of Omega | 3 | Per-state, per-time belief set |
| Information relation | I_t | - | - | I_t(w) subset of Omega | 3 | Per-state, per-time information set |

## Methods & Implementation Details
- The language has five modal operators: next-time (circle), inverse (circle^-1), belief B, information I, all-state A *(p.4)*
- Boolean formulas (Phi^B) are the modal-free fragment; their truth value depends only on state, not time *(p.6, Proposition 5)*
- AGM revision is restricted to Boolean formulas as informational inputs *(p.6)*
- The base logic L_0 includes: all propositional tautologies, axiom K for all operators, temporal axioms O_1 (phi -> circle diamond^{-1} phi) and O_2 (phi -> circle^{-1} diamond phi), Backward Uniqueness BU, S5 axioms for A, inclusion axiom Incl_B (A phi -> B phi), axioms I_1 and I_2 for information operator *(p.5-6)*
- Rules of inference: Modus Ponens, Necessitation for A/circle/circle^{-1} (but NOT for I -- necessitation for I is not validity-preserving) *(p.6)*
- The Qualitative Bayes Rule is the SEMANTIC counterpart of AGM revision: when prior beliefs and new information are compatible, revised beliefs = prior beliefs intersected with information *(p.8)*
- L_b-frame properties (Definition 6): (1) QBR holds, (2) beliefs are subset of information-compatible states (B_t(w) subset I_t(w)), (3) if information is non-empty then beliefs are non-empty *(p.8)*
- L_AGM-frame additionally requires CAR (Definition 8) *(p.10)*
- Proof of Proposition 11 constructs two-instant models {t_1, t_2} with Omega = M_K (models of the belief set K) *(p.12-15)*
- Proof of Proposition 12 constructs multi-instant models for iterated revision using a linear chain t_1 -> t_2 -> ... -> t_n *(p.17-21)*

## Figures of Interest
- No figures in this paper.

## Results Summary
- Proposition 7 (p.9): L_b is sound with respect to L_b-frames. Every theorem of L_b is valid in every L_b-model.
- Proposition 11 (p.12): L_b provides an axiomatic characterization of AGM postulates K*1-K*6. For any consistent deductively closed set K and Boolean formula phi, K*_phi satisfies K*1-K*6 iff there exists an L_b-model realizing the revision.
- Proposition 12 (p.17): L_AGM provides an axiomatic characterization of the full set of AGM postulates K*1-K*8. Both directions proved: (A) AGM-compliant revision implies L_AGM-model existence, (B) L_AGM-models satisfy AGM postulates.
- Section 5 (p.23): Related work discussion. Comparison with Kraus and Lehmann [14] who use knowledge operator and next-time but not branching time. Comparison with Friedman and Halpern [10] who use branching-time but without information operator. *(p.23)*

## Limitations
- Completeness is not addressed; the paper notes it is "not relevant for the results" and is dealt with in a separate paper *(p.6, footnote 3)*
- Only belief REVISION is treated, not belief UPDATE (where the world itself changes over time) *(p.4)*
- The temporal frames require Backward Uniqueness (BU): each instant has at most one predecessor. This rules out DAG-like structures with merge points *(p.3, p.5)*
- The information operator I has non-standard semantics (equality, not subset): I_t(w) = [phi]_t rather than I_t(w) subset [phi]_t. This means information fully determines the set of compatible states *(p.5)*
- The paper acknowledges that "axiomatic characterization" is perhaps better called "axiomatic representation" or "axiomatic counterpart" *(p.23, footnote 5)*

## Arguments Against Prior Work
- Criticizes the lack of uniformity between how static beliefs and belief change are modeled in the literature: static beliefs use modal logic/Kripke semantics, while belief change uses AGM theory with belief sets -- two different formalisms for related phenomena *(p.1)*
- Notes that Kraus and Lehmann [14] use a knowledge operator rather than belief, and their setup considers only one revision step, not iterated revision *(p.23)*
- Notes that Friedman and Halpern [10] do not have an explicit information operator, instead building belief change into the branching-time structure directly *(p.23)*

## Design Rationale
- Branching-time temporal logic chosen because belief revision "deals with the interaction of belief and information over time" -- branching time naturally captures the multiplicity of possible future information *(p.1)*
- Five operators chosen to separate concerns: temporal (circle, circle^{-1}), doxastic (B), informational (I), and universal (A) *(p.4)*
- The "all state" operator A is needed to capture the non-normality of I (necessitation is not valid for I) *(p.4)*
- QBR chosen as the bridge between probabilistic (Bayesian) and qualitative (AGM) revision: in a probabilistic setting, QBR reduces to standard Bayesian conditioning on the support of the probability measure *(p.8)*
- Backward Uniqueness axiom justified by the interpretation that each instant has a unique history *(p.3)*
- Boolean formula restriction on information inputs justified because "belief revision" (not "belief update") means the world doesn't change, only beliefs about it do -- so informational input should be state-dependent only *(p.4, p.6)*

## Testable Properties
- If B_t(w) cap I_{t+1}(w) != empty, then B_{t+1}(w) = B_t(w) cap I_{t+1}(w) (QBR must hold) *(p.8)*
- B_t(w) subset I_t(w) for all w, t (beliefs must be consistent with information) *(p.8)*
- If I_t(w) != empty then B_t(w) != empty (non-vacuous information implies non-vacuous beliefs) *(p.8)*
- Backward Uniqueness: each instant has at most one predecessor *(p.3)*
- Forward branching: each instant has at most one IMMEDIATE successor (property (i) of Definition 1), but can have MULTIPLE successors reachable via different paths *(p.3)*
- For L_AGM frames: CAR condition must hold -- when information at t_2 is a subset of information at t_3 and is compatible with prior beliefs, revised beliefs at t_2 equal the intersection of revised beliefs at t_3 with information at t_2 *(p.10)*

## Relevance to Project
This paper is critical for evaluating whether the AGM theory of belief revision can be mapped onto git's commit graph structure for propstore's branching-time belief revision. The key finding is that Bonanno's temporal frames REQUIRE Backward Uniqueness (each instant has at most one predecessor), which means the temporal structure is tree-like forward but LINEAR backward. Git's commit graph is a DAG where merge commits have MULTIPLE predecessors, violating BU. This means:

1. The direct AGM-temporal-logic mapping DOES NOT hold on git DAGs without modification.
2. At merge commits (multiple predecessors), the QBR would need to be generalized -- which predecessor's beliefs to intersect with the new information?
3. The PLS (plausibility ordering) frame condition from Bonanno 2012 inherits this BU constraint since it builds on this 2007 framework.
4. Any mapping of AGM to git would need to either (a) linearize the DAG (pick one predecessor path), (b) generalize QBR to handle multiple predecessors (belief merging, not just revision), or (c) work at the branch level rather than the commit level.

## Open Questions
- [ ] Does the Bonanno 2012 paper relax the Backward Uniqueness constraint in any way?
- [ ] Can QBR be generalized to multiple predecessors (belief merging)?
- [ ] What is the relationship between the CAR condition and plausibility orderings in Bonanno 2012?
- [ ] Is completeness of L_b and L_AGM proven in the companion paper mentioned in footnote 3?

## Collection Cross-References

### Already in Collection
- [[Alchourron_1985_TheoryChange]] — this paper axiomatically characterizes the AGM postulates defined there
- [[Bonanno_2010_BeliefChangeBranchingTime]] — the direct successor to this paper; extends the framework to prove AGM-consistency equivalence with PLS and total pre-order rationalizability
- [[Darwiche_1997_LogicIteratedBeliefRevision]] — this paper's iterated revision (Section 4, Proposition 12) relates to DP postulates; Bonanno 2010 shows how the ternary revision function subsumes Darwiche-Pearl
- [[Dixon_1993_ATMSandAGM]] — Dixon's ATMS-AGM bridge uses the same AGM postulates K*1-K*8 that this paper characterizes axiomatically
- [[Gardenfors_1988_RevisionsKnowledgeSystemsEpistemic]] — epistemic entrenchment ordering relates to the plausibility structure implicit in this paper's QBR-based frames

### New Leads (Not Yet in Collection)
- Kraus and Lehmann (1988) — "Knowledge, belief and time", Theoretical Computer Science 58: 155-174 — alternative temporal approach using knowledge operator, compared in Section 5
- Friedman and Halpern (1994/2000) — Belief revision using branching time without explicit information operator — compared in Section 5
- Segerberg (1995) — "Belief revision from the point of view of doxastic logic", Bulletin of the IGPL 3: 535-553 — doxastic logic approach to revision

### Cited By (in Collection)
- [[Bonanno_2010_BeliefChangeBranchingTime]] — cites this as the foundational predecessor introducing branching-time belief revision frames and the modal logic

### Conceptual Links (not citation-based)
- [[Baumann_2015_AGMMeetsAbstractArgumentation]] — both papers bridge AGM revision with another formalism (temporal logic here, Dung frameworks there); together they suggest a three-way correspondence: temporal frames <-> AGM postulates <-> Dung AF dynamics
- [[Shapiro_1998_BeliefRevisionTMS]] — Shapiro surveys TMS vs AGM traditions; this paper's temporal logic characterization provides the formal link that Shapiro's survey identifies as missing between the two traditions
- [[Rotstein_2008_ArgumentTheoryChangeRevision]] — Rotstein's warrant-prioritized revision adapts AGM to structured arguments; this paper's QBR provides the semantic foundation for what "revision" means formally

## Related Work Worth Reading
- [1] Alchourron, Gardenfors, Makinson 1985 - Original AGM theory. Journal of Symbolic Logic 50: 510-530. *(already in collection as aspirational reference)*
- [10] Friedman and Halpern 2000 - Belief revision in the situation calculus using plausibility measures on formulas. Uses branching time but no explicit information operator. *(p.23)*
- [14] Kraus and Lehmann 1988 - Knowledge, belief and time. Theoretical Computer Science 58: 155-174. Uses knowledge operator with next-time but not branching time. *(p.23)*
- [9] van Ditmarsch, B. 2005 - Prolegomena to dynamic logic for belief revision. Synthese 147: 229-275. Dynamic epistemic logic approach. *(p.23)*
- [17] Nayak, Pagnucco, Peppas 2003 - Dynamic belief revision operators. Artificial Intelligence 146: 193-228. *(p.26)*
- [19] Segerberg 1995 - Belief revision from the point of view of doxastic logic. Bulletin of the IGPL 3: 535-553. *(p.27)*
- [2] Battigalli and Bonanno 1997 - The logic of belief persistence. Economics and Philosophy 13: 39-59. *(p.25)*
