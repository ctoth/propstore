---
title: "Merging Information Under Constraints: A Logical Framework"
authors: "Sebastien Konieczny, Ramon Pino Perez"
year: 2002
venue: "Journal of Logic and Computation"
doi_url: "https://doi.org/10.1093/logcom/12.5.773"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-29T03:15:26Z"
---
# Merging Information Under Constraints: A Logical Framework

## One-Sentence Summary
Provides a complete axiomatic framework (postulates IC0-IC8) for merging multiple belief bases under integrity constraints, with representation theorems linking operators to distance-based semantics on interpretations, distinguishing majority, arbitration, and quasi-merging operators.

## Problem Addressed
Multiple sources of information (expert systems, databases, sensor networks) need to be combined into a single coherent result, even when sources conflict. Prior work either handled only two sources (belief revision) or ignored integrity constraints. This paper provides the first comprehensive logical characterization of merging operators for any number of sources under integrity constraints, with representation theorems connecting postulates to semantic constructions. *(p.1-2)*

## Key Contributions
- Complete set of postulates (IC0-IC8) characterizing IC merging operators, with representation theorem via syncretic assignments *(p.4-8)*
- Distinction between majority operators (IC0-IC8 + Maj), arbitration operators (IC0-IC8 + Arb), and quasi-merging operators (IC0-IC3 + IC7-IC8) *(p.4-6)*
- Three concrete operator families: Sigma (sum-based majority), Max (max-based quasi-merging), GMax (lexicographic arbitration) *(p.12-18)*
- Proof that IC merging generalizes Katsuno-Mendelzon belief revision *(p.19-22)*
- Proof that Liberatore-Schaerf commutative revision operators are a special case *(p.25-30)*
- Connection to pure merging (no constraints), Lin-Mendelzon majority merging, and Revesz model-fitting operators *(p.23-32)*

## Methodology
The paper works in propositional logic over a finite language. Belief bases are propositional formulas; a belief set (multi-set of belief bases) Psi = {phi_1, ..., phi_n} represents multiple sources. An integrity constraint mu restricts admissible merged results. The paper:
1. Defines postulates that any reasonable IC merging operator should satisfy
2. Defines syncretic assignments (semantic counterpart) mapping belief sets to pre-orders on interpretations
3. Proves representation theorems: an operator satisfies the postulates iff it can be represented by a syncretic assignment
4. Provides concrete distance-based operator families and proves they satisfy the postulates

## Key Equations / Statistical Models

### Distance between interpretation and belief base

$$
d(I, \varphi) = \min_{J \models \varphi} d(I, J)
$$
Where: $I, J$ are interpretations (possible worlds), $\varphi$ is a belief base, $d: \mathcal{W} \times \mathcal{W} \to \mathbb{N}$ is a distance between interpretations satisfying $d(I,J) = d(J,I)$ and $d(I,J) = 0$ iff $I = J$. *(p.12)*

### Distance between two belief bases

$$
d(\varphi, \varphi') = \min_{I \models \varphi, J \models \varphi'} d(I, J)
$$
*(p.12)*

### Sigma-distance (majority merging)

$$
d_{\Sigma}(I, \Psi) = \sum_{\varphi \in \Psi} d(I, \varphi)
$$
Where: $\Psi$ is a belief set (multi-set of belief bases). *(p.12)*

### Sigma pre-order

$$
I \leq_{\Psi}^{\Sigma} J \text{ iff } d_{\Sigma}(I, \Psi) \leq d_{\Sigma}(J, \Psi)
$$
*(p.12)*

### Sigma operator

$$
mod(\triangle_{\mu}^{\Sigma}(\Psi)) = \min(mod(\mu), \leq_{\Psi}^{\Sigma})
$$
Where: $mod(\cdot)$ returns the set of models, $\min(S, \leq)$ returns the minimal elements of $S$ under $\leq$. *(p.12)*

### Max-distance (quasi-merging/arbitration)

$$
d_{Max}(I, \Psi) = \max_{\varphi \in \Psi} d(I, \varphi)
$$
*(p.15)*

### Max pre-order and operator

$$
I \leq_{\Psi}^{Max} J \text{ iff } d_{Max}(I, \Psi) \leq d_{Max}(J, \Psi)
$$

$$
mod(\triangle_{\mu}^{Max}(\Psi)) = \min(mod(\mu), \leq_{\Psi}^{Max})
$$
*(p.15)*

### GMax-distance (lexicographic arbitration)

$$
d_{GMax}(I, \Psi) = L_I^{\Psi} \text{ (sorted distance vector)}
$$
Where: for $\Psi = \{\varphi_1 \ldots \varphi_n\}$, build list $(d_1^I \ldots d_n^I)$ where $d_j^I = d(I, \varphi_j)$, sort in descending order to get $L_I^{\Psi}$. *(p.17)*

### GMax pre-order and operator

$$
I \leq_{\Psi}^{GMax} J \text{ iff } L_I^{\Psi} \leq_{lex} L_J^{\Psi}
$$

$$
mod(\triangle_{\mu}^{GMax}(\Psi)) = \min(mod(\mu), \leq_{\Psi}^{GMax})
$$
Where: $\leq_{lex}$ is lexicographic order on sequences of integers. *(p.17)*

### Revision from merging (Theorem 5.5)

$$
mod(\varphi \circ \mu) = \min(mod(\mu), \leq_{\varphi})
$$
Where: if $\triangle$ is an IC merging operator satisfying (IC0-IC3), the revision operator $\circ$ defined as $\varphi \circ \mu = \triangle_{\mu}(\{\varphi\})$ satisfies KM postulates (R1-R6). *(p.20-21)*

### Merging from revision (Definition 5.4 + Theorem 5.5)

Given a revision operator $\circ$, build the merging method:

$$
f_{\circ}^{\Psi}(I) = \sum_{j} f_{\circ}^{\varphi_j}(I)
$$
Where: $f_{\circ}^{\varphi}(I)$ is the level at which interpretation $I$ appears in the $\leq_{\varphi}$ pre-order (the faithful assignment corresponding to revision $\circ$). The merging operator is:

$$
mod(\triangle_{\mu}^{\circ}(\Psi)) = \min(mod(\mu), \leq_{\Psi}^{\circ})
$$
This satisfies (IC0-IC3), (IC5-IC6) but not necessarily condition 4 of syncretic assignments without additional symmetry. *(p.21-22)*

### Symmetry condition for merging from revision

$$
f_{\circ}^{\varphi}(I) = f_{\circ}^{\varphi'}(J) \text{ for any belief bases } \varphi \text{ and } \varphi'
$$
*(Sym) condition required so that the merging operator built from revision satisfies full IC postulates. *(p.21)*

### Distance-based revision operator (Proposition 5.8)

$$
\varphi \circ \mu = (\varphi \lor \mu) \lor (\varphi \land \mu)
$$
A revision operator $\circ$ is said to be derived from a distance $d$ iff: (a) $d$ is a distance, (b) property (6.6) is satisfied, (c) $mod(\varphi \circ \mu) = min(mod(\mu), \leq_{\varphi})$. In this case the Sigma and Grosse methods give the operators $\triangle^{\Sigma}$ and $\triangle^{GMax}$. *(p.22-23)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of belief bases | n | - | - | >= 1 | p.3 | Size of belief set Psi |
| Propositional language | L | - | - | finite | p.3 | Finite set of propositional letters |
| Interpretations | W | - | - | 2^|L| | p.3 | Set of all interpretations |
| Distance function | d | N | - | >= 0 | p.12 | d: W x W -> N, symmetric, d(I,J)=0 iff I=J |

## Methods & Implementation Details

### IC Merging Postulates (Definition 3.1) *(p.4-5)*
An operator $\triangle$ is an IC merging operator iff it satisfies:

- **(IC0)** $\triangle_{\mu}(\Psi) \vdash \mu$ — result satisfies integrity constraint *(p.4)*
- **(IC1)** If $\mu$ is consistent, then $\triangle_{\mu}(\Psi)$ is consistent *(p.4)*
- **(IC2)** If $\bigwedge \Psi$ is consistent with $\mu$, then $\triangle_{\mu}(\Psi) \leftrightarrow \bigwedge \Psi \wedge \mu$ — if sources agree and are compatible with constraint, take conjunction *(p.4)*
- **(IC3)** If $\Psi_1 \leftrightarrow \Psi_2$, then $\triangle_{\mu}(\Psi_1) \leftrightarrow \triangle_{\mu}(\Psi_2)$ — syntax independence *(p.4)*
- **(IC4)** If $\varphi_1 \vdash \mu$ and $\varphi_2 \vdash \mu$, then $\triangle_{\mu}(\varphi_1 \sqcup \varphi_2) \not\vdash \neg\varphi_1$ — fairness, one source cannot be completely ignored *(p.4)*
- **(IC5)** $\triangle_{\mu}(\Psi_1) \wedge \triangle_{\mu}(\Psi_2) \vdash \triangle_{\mu}(\Psi_1 \sqcup \Psi_2)$ — if result is compatible with both sub-merges, it's in the full merge *(p.4)*
- **(IC6)** If $\triangle_{\mu}(\Psi_1) \wedge \triangle_{\mu}(\Psi_2)$ is consistent, then $\triangle_{\mu}(\Psi_1 \sqcup \Psi_2) \vdash \triangle_{\mu}(\Psi_1) \wedge \triangle_{\mu}(\Psi_2)$ *(p.4)*
- **(IC7)** $\triangle_{\mu_1}(\Psi) \wedge \mu_2 \vdash \triangle_{\mu_1 \wedge \mu_2}(\Psi)$ — constraint monotonicity *(p.4)*
- **(IC8)** If $\triangle_{\mu_1}(\Psi) \wedge \mu_2$ is consistent, then $\triangle_{\mu_1 \wedge \mu_2}(\Psi) \vdash \triangle_{\mu_1}(\Psi)$ *(p.4)*

### Additional postulates:

- **(Maj)** $\exists n\ \triangle_{\mu}(\Psi_1 \sqcup \Psi_2^n) \vdash \triangle_{\mu}(\Psi_2)$ — majority: a sufficiently large group can impose its view *(p.5)*
- **(Arb)** $\triangle(\varphi_1) \leftrightarrow \triangle(\varphi_2)$ and $\triangle_{\bot}(\varphi_1 \sqcup \varphi_2) \leftrightarrow \bot$ and $\top \not\vdash \top$ implies $\triangle(\varphi_1 \sqcup \varphi_2) \leftrightarrow \triangle(\varphi_1)$ — arbitration: fair operator, no group can dominate *(p.5)*
- **(Iteration)** $\lim_{n \to \infty} \triangle_{\mu}^n(\Psi, \varphi) = \varphi$ — iterated merging converges to the merged result *(p.5)*

### Taxonomy of operator types *(p.5)*
- **IC merging operator:** satisfies IC0-IC8
- **IC majority merging operator:** IC0-IC8 + (Maj)
- **IC arbitration operator:** IC0-IC8 + (Arb)
- **IC quasi-merging operator:** IC0-IC3 + IC7-IC8 (drops IC4-IC6)

### Syncretic Assignments (Definition 3.6) *(p.6-7)*
A syncretic assignment maps each belief set $\Psi$ to a total pre-order $\leq_{\Psi}$ over interpretations such that:
1. If $I \models \Psi$ and $J \models \Psi$, then $I \approx_{\Psi} J$ (models of all bases are equally preferred)
2. If $I \models \Psi$ and $J \not\models \Psi$, then $I <_{\Psi} J$ (models beat non-models)
3. If $\Psi_1 \leftrightarrow \Psi_2$, then $\leq_{\Psi_1} = \leq_{\Psi_2}$ (syntax independence)
4. For singletons: $I \models \varphi$ and $J \not\models \varphi$ implies $I <_{\{\varphi\}} J$ *(p.6)*
5. (For majority): $I <_{\Psi_1} J$ and $I \leq_{\Psi_2} J$ implies $I <_{\Psi_1 \sqcup \Psi_2} J$ *(p.7)*

Conditions 5-8 correspond to IC5-IC8 on operators. Fair syncretic assignments add symmetry for arbitration.

### Representation Theorems
- **Theorem 3.7:** $\triangle$ is an IC merging operator iff there exists a syncretic assignment such that $mod(\triangle_{\mu}(\Psi)) = \min(mod(\mu), \leq_{\Psi})$ *(p.7)*
- **Theorem 3.11:** $\triangle$ is an IC quasi-merging operator iff represented by a majority syncretic assignment *(p.10)*
- **Theorem 3.13:** $\triangle$ is an IC majority merging operator iff represented by a majority syncretic assignment *(p.10)*
- **Theorem 3.15:** $\triangle$ is an IC arbitration operator iff represented by a fair syncretic assignment *(p.11)*

### Operator hierarchy
- $\triangle^{GMax}(\Psi) \vdash \triangle^{Max}(\Psi)$ (GMax refines Max) — Remark 4.10 *(p.17)*
- $\triangle^{\Sigma}$ is a majority merging operator — Theorem 4.2 *(p.13)*
- $\triangle^{Max}$ is a quasi-merging operator — Theorem 4.6 *(p.15)*
- $\triangle^{GMax}$ is an arbitration operator — Theorem 4.14 *(p.18)*
- $\triangle^{\Sigma}$ satisfies triangle inequality (Theorem 4.3): if $d$ satisfies triangle inequality, then $d_{\Sigma}$ does too *(p.13)*

### Connection to belief revision (Section 5) *(p.19-22)*
- **Theorem 5.3:** If $\triangle$ is an IC merging operator satisfying (IC0-IC3), then the operator $\circ$ defined as $\varphi \circ \mu = \triangle_{\mu}(\{\varphi\})$ is a KM revision operator (satisfies R1-R6) *(p.20)*
- **Theorem 5.5:** If $\triangle$ is an IC merging operator, the operator $\circ_{\triangle}$ associated with $\triangle$ satisfies (LS1-LS5) and the commutative revision from $\triangle$ satisfies (LS1-LS5, LS7) *(p.21)*

### Connection to Liberatore-Schaerf (Section 6.2) *(p.25-30)*
- Commutative revision operators $\diamond$ defined from IC merging: $\varphi_1 \diamond \varphi_2 = \triangle_{\top}(\varphi_1 \sqcup \varphi_2)$ *(p.25)*
- LS postulates (LS1-LS7) shown to be special cases *(p.25-26)*
- Representation theorem 6.8 for commutative revision operators via faithful assignments *(p.27)*
- Theorem 6.11: representation of commutative revision operators as IC merging operators on 2-element belief sets *(p.30)*

### Connection to Lin-Mendelzon (Section 6.3) *(p.31)*
- Lin and Mendelzon's "kind of merging operator" is a majority merging operator in this framework
- Their postulates (LM1-LM5) map to IC postulates *(p.31)*

### Connection to Revesz model-fitting (Section 6.4) *(p.31-32)*
- Revesz's model-fitting operators map into the framework *(p.31)*
- Definition 6.14: model-fitting operators use total pre-orders over sets of interpretations *(p.31-32)*
- Theorem 6.15: model-fitting operators satisfying certain conditions are IC merging *(p.32)*
- $\triangle^{GMax}$ family operators are model-fitting operators *(p.32)*

## Figures of Interest
- **Table 1 (p.14):** Worked example of $\triangle^{\Sigma}$ operator on 4-voter building committee scenario (16 interpretations, distances to each belief base, sum distance)
- **Table 2 (p.17):** Same example with $\triangle^{Max}$ operator (max distance)
- **Table 3 (p.19):** Same example with $\triangle^{GMax}$ operator (sorted distance vectors with lexicographic comparison)

## Results Summary
The paper establishes a complete axiomatic framework for belief merging under integrity constraints. The key hierarchy is:
- **Majority** ($\triangle^{\Sigma}$): sum of distances — democratic, large groups can override minorities *(p.12-14)*
- **Quasi-merging** ($\triangle^{Max}$): max distance — more egalitarian but can't distinguish between some cases *(p.15-16)*
- **Arbitration** ($\triangle^{GMax}$): lexicographic max — no group can dominate, requires approval of all members *(p.17-19)*

The building committee example (p.14-19) shows concretely how the three operators produce different results: $\triangle^{\Sigma}$ gives majority rule (build all three items), $\triangle^{Max}$ gives more interpretations (multiple tied options), $\triangle^{GMax}$ gives a fair compromise (build tennis court or car park, don't increase rent).

## Limitations
- Limited to finite propositional language *(p.3)*
- Only considers propositional belief bases, not first-order *(p.3)*
- Does not address computational complexity of the operators *(p.32)*
- Does not address whether $\triangle^{\Sigma}$ and $\triangle^{GMax}$ built from the same distance are always disjoint classes *(p.33)*
- Open question: are all IC merging operators built from a distance? *(p.33)*
- Open question: relationship between postulates (Maj) and (Arb) — are they jointly satisfiable? *(p.33)*
- Does not address iterated merging beyond the convergence postulate *(p.5)*

## Arguments Against Prior Work
- Liberatore and Schaerf's commutative revision operators handle only two sources, which is a major limitation; their operators are shown to be a special case of the IC framework *(p.2, p.25)*
- Pure merging (without integrity constraints) is too restrictive — real scenarios always have constraints *(p.1-2)*
- Simple majority is not always appropriate — the building committee example shows arbitration may be needed when unanimous approval is required *(p.19)*

## Design Rationale
- Multi-sets (not sets) of belief bases are used because the same belief base contributed by multiple sources should count multiple times — this is essential for majority behavior *(p.3)*
- Integrity constraints are separate from belief bases because they represent hard requirements that the merged result must satisfy, not preferences *(p.1-2)*
- The postulate-based approach (rather than directly defining operators) allows characterizing whole classes of operators and proving they are the only ones satisfying natural properties *(p.4)*
- Syncretic assignments provide semantic transparency: each operator has a clear interpretation in terms of preference orderings on possible worlds *(p.6-7)*

## Implementation Notes For Propstore
- `mu` is a hard admissibility filter over whole interpretations/models, not a local score tweak or tie-breaker. The operator first restricts to `mod(mu)` and only then takes the minimal elements under the assignment-induced preorder *(p.4, p.7, p.12, p.15, p.17)*.
- A concept-local scalar merge like `profile: branch -> value` can be a useful adaptation, but by itself it does **not** match the paper's semantic object. The paper merges belief multisets into sets of admissible interpretations, not isolated scalar winners.
- Therefore a per-concept predicate such as "value is in range" is only a **restricted adaptation** of `mu`. The literature-faithful target is an assignment-level constraint over one jointly merged result, potentially spanning multiple concepts.
- For code claims, the safe rule is: do not cite IC0-IC8 for an unconstrained scalar wrapper. Those postulates are proved for operators of the form `mod(Delta_mu(Psi)) = min(mod(mu), <=_Psi)`, where `mu` is real and the compared objects are interpretations.

## Testable Properties
- IC0: merged result must entail the integrity constraint *(p.4)*
- IC1: if the constraint is consistent, the merged result is consistent *(p.4)*
- IC2: if all sources agree and are compatible with constraint, result is their conjunction *(p.4)*
- IC4: no single source's beliefs are completely overridden when both are individually consistent with the constraint *(p.4)*
- Sigma operator satisfies triangle inequality when base distance does *(p.13)*
- GMax refines Max: $mod(\triangle^{GMax}_{\mu}(\Psi)) \subseteq mod(\triangle^{Max}_{\mu}(\Psi))$ *(p.17)*
- Singleton reduction: $\triangle_{\mu}(\{\varphi\})$ produces a KM revision operator *(p.20)*
- Majority property: for any $\Psi_1, \Psi_2$, there exists $n$ such that $\triangle_{\mu}(\Psi_1 \sqcup \Psi_2^n) \vdash \triangle_{\mu}(\Psi_2)$ for majority operators *(p.5)*

## Relevance to Project
This is a foundational paper for the propstore belief merging layer. The IC postulates (IC0-IC8) define correctness criteria for any merging operation in the system. The distance-based semantics connect directly to the existing opinion algebra (Subjective Logic distances could serve as the base distance function d). The distinction between majority vs arbitration operators maps to different conflict resolution policies in the render layer. The representation theorems via syncretic assignments provide the formal bridge between axiomatic and constructive definitions of merging — essential for verifying that any implemented operator is principled.

Key connections:
- IC postulates are to merging what AGM postulates are to revision — correctness criteria
- The Sigma/Max/GMax hierarchy maps to different degrees of minority protection in multi-source merging
- Integration with ASPIC+: merged belief bases could serve as knowledge bases for argumentation
- The connection to belief revision (Section 5) shows how single-agent and multi-agent operations unify

## Open Questions
- [ ] How do IC postulates interact with the opinion algebra (Josang 2001)?
- [ ] Can Subjective Logic fusion operators be characterized as IC merging operators?
- [ ] What is the computational complexity of Sigma, Max, GMax operators?
- [ ] How does iterated merging interact with ATMS assumption management?
- [ ] Can the distance function d be derived from the opinion space metric?

## Related Work Worth Reading
- Konieczny & Pino Perez 1999 [22] — Pure merging without integrity constraints (precursor)
- Liberatore & Schaerf 1998 [24, 25] — Commutative revision operators (shown to be special case)
- Katsuno & Mendelzon 1991 [18] — Belief revision postulates (KM, shown to be special case of IC merging)
- Lin & Mendelzon 1999 [27] — Integration of weighted belief bases
- Revesz 1997 [31, 32] — Model-fitting operators
- Dalal 1988 [8] — Distance-based revision (Dalal distance used in examples)
- Everaere et al. [9] — Combination of prioritized belief bases (extension of this work)

## Collection Cross-References

### Already in Collection
- [[Alchourron_1985_TheoryChange]] — cited as [1]; AGM postulates are the correctness criteria that IC merging postulates generalize from single-agent revision to multi-source merging
- [[Coste-Marquis_2007_MergingDung'sArgumentationSystems]] — directly builds on this paper; lifts IC merging operators to Dung argumentation frameworks using distance-based semantics on partial AFs

### New Leads (Not Yet in Collection)
- Katsuno & Mendelzon 1992 [18] — "Propositional knowledge base revision and minimal change" — KM revision postulates shown to be special case of IC merging
- Liberatore & Schaerf 1998 [24, 25] — "Arbitration" — commutative revision operators as IC merging special case
- Dalal 1988 [8] — distance-based revision using Hamming distance, used in all examples
- Konieczny & Pino Perez 1998 [22] — pure merging precursor paper (no integrity constraints)

### Supersedes or Recontextualizes
- (none in collection)

### Cited By (in Collection)
- [[Coste-Marquis_2007_MergingDung'sArgumentationSystems]] — cites this as the foundational IC merging framework that it lifts to argumentation frameworks
- [[Doutre_2018_ConstraintsChangesSurveyAbstract]] — cites this in the context of dynamics and change in abstract argumentation
- [[Bonzon_2016_ComparativeStudyRanking-basedSemantics]] — references merging operators
- [[Baumann_2015_AGMMeetsAbstractArgumentation]] — cites in connection with AGM and argumentation
- [[Matt_2008_Game-TheoreticMeasureArgumentStrength]] — references in citations
- [[Hunter_2017_ProbabilisticReasoningAbstractArgumentation]] — references in citations

### Conceptual Links (not citation-based)
- [[Gardenfors_1988_RevisionsKnowledgeSystemsEpistemic]] — epistemic entrenchment provides an alternative semantic construction for belief revision; IC merging's syncretic assignments generalize faithful assignments from the same tradition
- [[Alchourron_1985_TheoryChange]] — IC postulates are explicitly designed as the multi-source generalization of AGM; the representation theorem structure (postulates <-> semantic construction) mirrors AGM's partial meet characterization
