---
title: "Expanding Argumentation Frameworks: Enforcing and Monotonicity Results"
authors: "Ringo Baumann, Gerhard Brewka"
year: 2010
venue: "COMMA 2010, Frontiers in Artificial Intelligence and Applications, Vol. 216"
doi_url: "https://doi.org/10.3233/978-1-60750-619-5-75"
---

# Expanding Argumentation Frameworks: Enforcing and Monotonicity Results

## One-Sentence Summary
Provides formal definitions and results for how Dung argumentation frameworks can be expanded with new arguments to enforce desired extensions, including impossibility results, constructive enforcement theorems, and monotonicity guarantees for weak expansions.

## Problem Addressed
When an AF is revised by adding new arguments (which may interact with old ones), what happens to the extensions? Can we force a desired set of arguments to become an extension? Under what conditions is this possible or impossible? How do expansion operations relate to monotonicity of extensions and justification states? *(p.0-1)*

## Key Contributions
- Formal taxonomy of expansion types: normal, strong, and weak expansions *(p.3)*
- Definition of enforcement: conservative vs liberal, with or without semantics change *(p.3-4)*
- Impossibility results (Proposition 1): conditions under which normal expansions cannot enforce a desired set *(p.5)*
- Possibility results (Theorems 2-4): conditions for exchanging/eliminating/enforcing extensions *(p.6-8)*
- Constructive enforcement (Theorem 4): any conflict-free set can be enforced by adding a single new argument with appropriate attacks *(p.7-8)*
- Monotonicity results (Theorem 5, Corollary 6): weak expansions under directional semantics preserve extension cardinality and justification states *(p.9)*
- Expansion chains (Definition 7, Corollary 1): checking acceptability in the initial AF of a chain suffices *(p.10)*

## Methodology
The paper operates purely within Dung's abstract argumentation framework theory. It defines three types of expansions based on attack direction constraints, then proves possibility/impossibility theorems for enforcing desired extensions under various semantics (stable, preferred, complete, grounded, admissible). *(p.0-1)*

## Key Equations

### Definition 1: Argumentation Framework
$$
\mathcal{A} = (A, R) \text{ where } A \text{ is a non-empty finite set, } R \subseteq A \times A \text{ is a binary relation (attack)}
$$
*(p.1)*

### Definition 2: Semantics Properties
Given AF $\mathcal{A} = (A, R)$ and $B, B' \subseteq A$:
1. $(B, B') \in R_{\_+}$ iff $\exists a, b: a \in B, b \in B', (a, b) \in R$
2. $B$ is unattacked in $\mathcal{A}$: $\neg \exists a \in A \setminus B: (a, B) \in R$
3. $B$ is defended by $B'$: $\forall a \in A \setminus B': (a, B) \in R \Rightarrow (B', \{a\}) \in R$
4. $B$ is conflict-free in $\mathcal{A}$: $(B, B) \notin R$
5. $\mathcal{A}|_B$: the restriction of $\mathcal{A}$ to $B$
*(p.1)*

### Definition 3: Extension-Based Semantics
- stable: $E \in \mathcal{E}_{stb}(\mathcal{A})$ iff conflict-free and $\forall a \notin E: (E, \{a\}) \in R$
- admissible: $E \in \mathcal{E}_{ad}(\mathcal{A})$ iff conflict-free and $E$ defends all its elements
- complete: $E \in \mathcal{E}_{co}(\mathcal{A})$ iff admissible and contains all elements it defends
- preferred: $E \in \mathcal{E}_{pr}(\mathcal{A})$ iff $\subseteq$-maximal admissible
- grounded: $E \in \mathcal{E}_{gr}(\mathcal{A})$ iff $\subseteq$-minimal complete
*(p.2)*

### Definition 4: Abstract Principles
A semantics $\mathcal{S}$ satisfies:
1. admissibility
2. reinstatement
3. conflict-freeness
4. the directionality principle

iff for any argumentation framework $\mathcal{A} = \mathcal{D}_{\mathcal{A}}$, any extension $E \in \mathcal{E}_{\mathcal{S}}(\mathcal{A})$ and any unattacked set $i \in US(\mathcal{A})$ it holds that:
- $\forall a \in E: \forall b \in A: b$ attacks $a \Rightarrow B \subseteq E, (B, \{b\}) \in R$
- $\forall a: (\forall b: b$ attacks $a \Rightarrow B \subseteq E, (B, \{b\}) \in R) \Rightarrow a \in E$
- $(E, E) \notin R$
- $\mathcal{E}_{\mathcal{S}}(\mathcal{A}) = \{E|_{U'} | E' \in \mathcal{E}_{\mathcal{S}}(\mathcal{A})\}$
*(p.2)*

### Definition 5: Expansion Types
An AF $\mathcal{A}^*$ is an *expansion* of AF $\mathcal{A} = (A, R)$ iff $\mathcal{A}^* = (A \cup A^*, R \cup R^*)$ for some nonempty $A^*$ disjoint from $A$:

1. **normal** ($\mathcal{A} \prec^N \mathcal{A}^*$) iff $\forall ab\ ((a,b) \in R^* \rightarrow a \in A^* \lor b \in A^*)$
2. **strong** ($\mathcal{A} \prec^N_S \mathcal{A}^*$) iff $\mathcal{A} \prec^N \mathcal{A}^*$ and $\forall ab\ ((a,b) \in R^* \rightarrow \neg(a \in A \land b \in A^*))$
3. **weak** ($\mathcal{A} \prec^N_W \mathcal{A}^*$) iff $\mathcal{A} \prec^N \mathcal{A}^*$ and $\forall ab\ ((a,b) \in R^* \rightarrow \neg(a \in A^* \land b \in A))$

*(p.3)*

### Definition 6: Enforcement
Let $\mathcal{A} = (A, R)$ be an AF, $\mathcal{S}$ a semantics. Let $E^*$ be a *desired set* which is not an extension ($E^* \notin \mathcal{E}_{\mathcal{S}}(\mathcal{A})$). An $(\mathcal{A}, \mathcal{S})$-enforcement of $E^*$ is a pair $\mathcal{F} = (\mathcal{A}^*, \mathcal{S}^*)$ such that:
- (1) $\mathcal{A}^* = \mathcal{A}$ or $\mathcal{A} \prec^N \mathcal{A}^*$
- (2) $E^* \in \mathcal{E}_{\mathcal{S}^*}(\mathcal{A}^*)$

$\mathcal{F}$ is called:
1. *conservative* if $\mathcal{S} = \mathcal{S}^*$
2. *conservative strong* if $\mathcal{A} \prec^N_S \mathcal{A}^*$ and $\mathcal{S} = \mathcal{S}^*$
3. *conservative weak* if $\mathcal{A} \prec^N_W \mathcal{A}^*$ and $\mathcal{S} = \mathcal{S}^*$
4. *liberal* if $\mathcal{A}^* = \mathcal{A}$ and $\mathcal{S} \neq \mathcal{S}^*$
5. *liberal strong* if $\mathcal{A} \prec^N_S \mathcal{A}^*$ and $\mathcal{S} \neq \mathcal{S}^*$
6. *liberal weak* if $\mathcal{A} \prec^N_W \mathcal{A}^*$ and $\mathcal{S} \neq \mathcal{S}^*$

*(p.3-4)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Argumentation framework | $\mathcal{A} = (A, R)$ | - | - | - | 1 | Finite directed graph |
| Extension set | $\mathcal{E}_{\mathcal{S}}(\mathcal{A})$ | - | - | - | 2 | Under semantics $\mathcal{S}$ |
| Expansion | $\mathcal{A}^*$ | - | - | - | 3 | New args $A^*$ disjoint from $A$ |
| Desired set | $E^*$ | - | - | - | 3 | Set to be enforced as extension |
| Semantics | $\mathcal{S}$ | - | - | {stb, pr, co, gr, ad} | 2 | Five standard semantics considered |

## Implementation Details

### Standard Construction for Enforcement (Theorem 4)
Given a conflict-free set $C$ in AF $\mathcal{A} = (A, R)$:
1. Add one new argument $c$ to create $\mathcal{A}^* = (A \cup \{c\}, R')$ *(p.8)*
2. $R' = R \cup \{(c, a_i), (c_i, c_{j+1}), (c, a_m)\}$ — the new argument $c$ attacks every argument in $A \setminus C$ *(p.8)*
3. For all $a \in \{a_1, ..., a_n\}$ (elements of $C$): $c$ is attacked by $a$ *(p.8)*
4. $c$ attacks every possible attacker in the complement $\{A \setminus (C \cup \{c\})\}$ so $C \cup \{c\}$ is counter-attacked *(p.8)*
5. Result: $E^* = \{a_1, ..., a_n, c\}$ is the unique extension of $\mathcal{A}^*$ for **all** semantics $\sigma \in \{stb, pr, co, gr, ad\}$ *(p.8)*

### Key constraint
- The construction adds exactly ONE new argument *(p.8)*
- Only works for conflict-free desired sets *(p.7-8)*
- The enforcement is conservative strong (no semantics change needed, no attacks from old to new) *(p.8)*

### Expansion Chain Checking (Corollary 1)
- Given a weak expansion chain $C = (\mathcal{A}_0, ..., \mathcal{A}_n)$ and semantics satisfying directionality *(p.10)*
- To check acceptability of argument $a$ in the final AF $\mathcal{A}_n$: find the smallest $i$ such that $a$ appears in $\mathcal{A}_i$ *(p.10)*
- Check $a$'s acceptability in $\mathcal{A}_i$ — this determines acceptability in the whole chain *(p.10)*

## Figures of Interest
- **Fig 1 (p.3):** Normal expansion of $\mathcal{A}$ — shows original AF (solid) with new arguments (dashed circle) and allowed attack directions (dashed arrows). Illustrates that in normal expansion, attacks between $A$ and $A^*$ go in a single direction.
- **Example 6 (p.10):** Expansion chain with arguments $a_0$ through $a_5$ and additional arguments $b_i$, showing how acceptability in the shaded initial AF determines acceptability in the full chain.

## Results Summary

### Impossibility Results (Proposition 1)
For normal expansions, if $\mathcal{S}$ satisfies: *(p.5-6)*
1. admissibility and $\mathcal{S}^+ \supseteq \mathcal{A}$: $\mathcal{A}$ does not defend all its elements in $\mathcal{A}_+$ then no conservative normal enforcement exists
2. reinstatement and $\mathcal{S}^+ \supseteq \mathcal{A}$: $\mathcal{A}$ does not contain all defended elements, then no conservative enforcement exists
3. conflict-freeness and $E^* \subseteq \mathcal{A}$ is conflicting: $(c, \mathcal{A}^*) \in R$ then there is a counterexample
4. If $E^* \subseteq A$ is unattacked in $\mathcal{A}$: $E^* \notin US(\mathcal{A})$, then $E^*$ is unattacked in each normal expansion

### Possibility Results
- **Theorem 2:** Conservative (liberal) strong enforcing — exchanging arguments is possible under certain conditions *(p.6)*
- **Theorem 3:** Conservative (liberal) weak enforcing — eliminating arguments (weak expansion can block arguments from extensions) *(p.6-7)*
- **Theorem 4:** For any conflict-free set $C$, there exists a conservative strong enforcement adding exactly one argument *(p.7-8)*

### Monotonicity Results
- **Theorem 5:** For weak expansions under directional semantics: *(p.9)*
  1. $|\mathcal{E}_{\mathcal{S}}(\mathcal{A})| \leq |\mathcal{E}_{\mathcal{S}}(\mathcal{A}^*)|$ (extension count is monotone non-decreasing)
  2. $\mathcal{S}^+ \subseteq \bigcap E^* \Rightarrow E^*$ is credulously justified args persist
  3. $\mathcal{S}^+ \subseteq \bigcup E^* \Rightarrow E^*$ is skeptically justified args persist

- **Corollary 6:** *(p.9)*
  1. $\bigcap_{E \in \mathcal{E}(\mathcal{A})} E \subseteq \bigcap_{E' \in \mathcal{E}(\mathcal{A}^*)} E'$ (skeptically justified args persist)
  2. $\bigcup_{E \in \mathcal{E}(\mathcal{A})} E \subseteq \bigcup_{E' \in \mathcal{E}(\mathcal{A}^*)} E'$ (credulously justified args persist)

## Limitations
- Results are limited to Dung's abstract framework — no preference handling, no support *(p.11)*
- Only conflict-free desired sets can be enforced (not arbitrary sets) *(p.7)*
- Monotonicity results require the directionality principle, which stable and admissible semantics do not satisfy *(p.9)*
- The paper notes it cannot strengthen monotonicity to equality of extension sets *(p.9)*
- Future work mentions exploring i-maximality and several kinds of semi-expansions *(p.11)*

## Arguments Against Prior Work
- The paper notes that Cayrol et al. [5] studied a related problem (a topology of revisions with one new interaction) but their framework does not address enforcement or monotonicity *(p.11)*
- Boella et al. [2] studied the role of adding/removing arguments and attacks but did not address enforcement or establish relationships between abstract properties and enforcement possibility *(p.11)*
- Oikarinen and Woltran [14] worked on normal expansions for equivalence, not enforcement *(p.11)*

## Design Rationale
- Normal expansions are chosen because they model the natural case where old arguments' relationships are settled *(p.3)*
- Strong vs weak distinction matters because it constrains who can attack whom — strong means new args don't receive attacks from old, weak means new args don't attack old *(p.3)*
- The directionality principle is key for monotonicity because it ensures unattacked subsets are evaluated independently *(p.9)*
- Conservative enforcement (no semantics change) is preferred because it preserves the proof standard *(p.4)*

## Testable Properties
- Any conflict-free set in an AF can be enforced as an extension by adding exactly one new argument with appropriate attacks (Theorem 4) *(p.7-8)*
- For weak expansions under grounded, complete, or preferred semantics: the number of extensions can only increase or stay the same (Theorem 5) *(p.9)*
- Skeptically justified arguments remain skeptically justified after any weak expansion under directional semantics (Corollary 6) *(p.9)*
- Credulously justified arguments remain credulously justified after any weak expansion under directional semantics (Corollary 6) *(p.9)*
- In a weak expansion chain, the acceptability of argument $a$ in $\mathcal{A}_n$ is determined by its acceptability in the first AF $\mathcal{A}_i$ where it appears (Corollary 1) *(p.10)*

## Relevance to Project
Directly relevant to propstore's argumentation layer. The enforcement results tell us: (1) when adding new claims/arguments to the knowledge base, we can always construct an expansion that makes a desired conflict-free set an extension; (2) for weak expansions (adding arguments that only receive attacks), monotonicity guarantees that existing justified arguments stay justified. This matters for incremental knowledge base updates — adding new evidence should not destabilize existing conclusions under appropriate expansion types.

## Open Questions
- [ ] How does enforcement interact with ASPIC+ structured argumentation?
- [ ] Can the single-argument construction (Theorem 4) be adapted for practical use in propstore?
- [ ] What are the computational complexity implications of checking enforcement conditions?
- [ ] How do these results extend to bipolar or weighted frameworks?

## Related Work Worth Reading
- Cayrol, de Saint-Cyr, and Lagasquie-Schiex, 2008: "Revision of an argumentation system" — revision operations on AFs
- Boella, Kaci, van der Torre, 2009: "Dynamics in argumentation with single extensions" — related dynamics
- Oikarinen and Woltran, 2008: Normal expansions for equivalence checking
- Baroni and Giacomin, 2007: Principle-based evaluation (already in project corpus)
- Caminada, 2006: Reinstatement (already in project corpus)

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — foundational framework; all definitions and results in this paper operate over Dung AFs
- [[Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation]] — the abstract principles (admissibility, reinstatement, directionality) used throughout this paper come from Baroni & Giacomin's axiomatic framework
- [[Caminada_2006_IssueReinstatementArgumentation]] — semi-stable semantics referenced; the paper's Definition 4 uses reinstatement as one of the abstract principles
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — Cayrol et al.'s work on AF revision (cited as [5]) is the most directly related prior work on AF dynamics

### New Leads (Not Yet in Collection)
- Oikarinen and Woltran 2008 — "Characterizing strong equivalence for argumentation frameworks" — normal expansion concept originates from this work on equivalence checking
- Boella, Kaci, van der Torre 2009 — "Dynamics in argumentation with single extensions" — complementary perspective on what happens when arguments/attacks are added/removed → NOW IN COLLECTION: [[Boella_2009_DynamicsArgumentationSingleExtensions]]
- Rotstein et al. 2008 — "Argument theory change: Revision upon warrant" — AGM-style approach to argumentation revision → NOW IN COLLECTION: [[Rotstein_2008_ArgumentTheoryChangeRevision]]

### Supersedes or Recontextualizes
- (none — this is an original contribution, not a revision of prior collection work)

### Cited By (in Collection)
- [[Doutre_2018_ConstraintsChangesSurveyAbstract]] — cites this as [14] for the foundational definitions of expansion types (normal/strong/weak) and enforcement results

### Conceptual Links (not citation-based)
- [[Doutre_2018_ConstraintsChangesSurveyAbstract]] — Strong: Doutre & Mailly's survey places Baumann & Brewka's expansion/enforcement typology within a comprehensive taxonomy of AF dynamics operations. The survey extends the scope beyond enforcement to include revision, contraction, and control frameworks.
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — Moderate: Odekerken's stability and relevance concepts address enforcement robustness under incomplete information, complementing Baumann & Brewka's enforcement under complete information. Different problem framing but converges on the question of whether enforcement results hold when the AF changes.

### Now in Collection (previously listed as leads)
- [[Boella_2009_DynamicsArgumentationSingleExtensions]] — Studies which deletions of attacks or arguments preserve the grounded extension in single-extension frameworks. This is the closest dynamics paper to Baumann and Brewka's enforcement results, but with an invariance-under-abstraction focus rather than an enforcement/minimal-change focus.
- [[Rotstein_2008_ArgumentTheoryChangeRevision]] — Adapts AGM-style revision to structured arguments using incision and preservation constraints to make a target argument warranted. This is the structured-argument analogue of minimal-change dynamics that Baumann cites as a complementary approach.

---

**See also:** [[Baumann_2015_AGMMeetsAbstractArgumentation]] - The same authors' 2015 IJCAI paper provides the full AGM-theoretic foundation for AF expansion via "Dung logics" and kernel union, superseding this paper's operational enforcement-based framing with a postulate-based characterization.
