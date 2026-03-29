---
title: "Rich preference-based argumentation frameworks"
authors: "Leila Amgoud, Srdjan Vesic"
year: 2014
venue: "International Journal of Approximate Reasoning"
doi_url: "https://doi.org/10.1016/j.ijar.2013.10.010"
pages: "585-606"
volume: "55"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-29T04:17:49Z"
---
# Rich preference-based argumentation frameworks

## One-Sentence Summary
Provides a formal framework (PAF and rich PAF) that correctly integrates preference relations over arguments into Dung-style argumentation, proving that existing approaches violate consistency and identifying the exact conditions under which preference-based defeat produces well-behaved extensions.

## Problem Addressed
Existing preference-based argumentation frameworks (Amgoud & Cayrol 2002, Bench-Capon 2003, Modgil & Prakken 2013) treat preferences incorrectly: they either (1) handle only one role of preferences (conflict resolution vs. argument comparison), (2) remove attacks in a way that produces inconsistent extensions, or (3) fail when the attack relation is not symmetric. This paper shows these failures formally and proposes a framework that handles both roles properly. *(p.0-1)*

## Key Contributions
- Formal proof that existing PAFs (which remove attacks based on preference) can produce inconsistent extensions even with consistent knowledge bases *(p.4)*
- A new "rich PAF" framework that inverts defeated attacks rather than removing them, avoiding the consistency problem *(p.4-5)*
- Proof that rich PAFs guarantee conflict-free extensions under any Dung semantics *(p.5)*
- Proof that when the preference relation is a total preorder, the rich PAF has a unique stable/preferred/grounded extension that coincides *(p.6)*
- A refinement relation for choosing between preference criteria *(p.8)*
- Coherence-based approach for handling inconsistency via sub-theories *(p.9-10)*
- Full instantiation linking propositional knowledge bases with partial preorders to rich PAFs *(p.10-13)*
- One-to-one correspondence between preferred sub-theories of a knowledge base and stable extensions of its rich PAF *(p.11-12)*

## Study Design
*Non-empirical: pure theory, formal framework, proofs.*

## Methodology
The paper builds on Dung's abstract argumentation framework (Definition 1: AF = (A, R)) and systematically extends it with preference orderings. The authors first analyze existing PAF approaches, demonstrate their failures via counterexamples, then propose a corrected framework with formal proofs of its properties. The instantiation section connects abstract argumentation to propositional knowledge bases equipped with partial preorders on formulas. *(p.0-13)*

## Key Equations / Statistical Models

### Definition 1: Argumentation Framework (Dung)
$$
\mathcal{F} = (\mathcal{A}, \mathcal{R})
$$
Where: $\mathcal{A}$ is a set of arguments, $\mathcal{R} \subseteq \mathcal{A} \times \mathcal{A}$ is an attack relation. $(a,b) \in \mathcal{R}$ means $a$ attacks $b$.
*(p.1)*

### Definition 2: Argument (propositional logic)
$$
a = (H, h)
$$
Where: $H \subseteq \Sigma$ (the support/hypotheses), $h$ is a formula (the conclusion). Conditions: (1) $H$ is consistent, (2) $H \vdash h$ (classical entailment), (3) $H$ is minimal (no proper subset entails $h$).
*(p.2)*

### Definition 3: Undercut Attack
$$
(a, b) \in \mathcal{R} \iff \exists h' \in H_b \text{ such that } h_a \equiv \neg h'
$$
Where: $a = (H_a, h_a)$ attacks $b = (H_b, h_b)$ iff the conclusion of $a$ is the negation of some hypothesis of $b$.
*(p.2)*

### Definition 4: Conflict-free
$$
\forall a, b \in S: (a,b) \notin \mathcal{R}
$$
*(p.2)*

### Definition 7: Preference-based AF (existing, shown to be flawed)
$$
\mathcal{T} = \langle \mathcal{A}, \mathcal{R}, \geq \rangle
$$
Where: $\geq$ is a (partial or total) preorder on $\mathcal{A}$. The PAF removes attack $(a,b)$ when $b > a$ (strict preference).
*(p.3)*

### Definition 8: Critical Attack
$$
(a,b) \text{ is critical} \iff (a,b) \in \mathcal{R} \text{ and } (b,a) \notin \mathcal{R}
$$
A critical attack is an asymmetric attack -- cannot be resolved by preferences. Only symmetric attacks should be subject to preference-based removal.
*(p.4)*

### Definition 9: Rich PAF
$$
\mathcal{T} = \langle \mathcal{A}, \mathcal{R}, \geq \rangle \text{ with corresponding AF } \mathcal{F}_\mathcal{T} = (\mathcal{A}, \text{Def}(\mathcal{T}))
$$
Where: $\text{Def}(\mathcal{T}) = \{(a,b) \mid (a,b) \in \mathcal{R} \text{ and } (b,a) \notin \mathcal{R}\} \cup \{(a,b) \mid (a,b) \in \mathcal{R} \text{ and } (b,a) \in \mathcal{R} \text{ and } \text{not}(b > a)\}$
The key insight: critical (asymmetric) attacks are always kept. Symmetric attacks are kept unless the attacked argument is strictly preferred.
*(p.4-5)*

### Property 1: Conflict-free Guarantee
$$
\forall \mathcal{E}_i \in \text{Ext}_x(\mathcal{F}_\mathcal{T}),\ \mathcal{E}_i \text{ is conflict-free w.r.t. } \mathcal{R}
$$
For any extension $\mathcal{E}_i$ under semantics $x$ of the rich PAF's corresponding AF $\mathcal{F}_\mathcal{T}$, $\mathcal{E}_i$ is also conflict-free with respect to the original attack relation $\mathcal{R}$.
*(p.5)*

### Definition 11: Maximal Consistent Subset
$$
\text{mc}(\Sigma) = \{S \subseteq \Sigma \mid S \text{ is consistent and } \forall S' \supset S: S' \text{ is inconsistent}\}
$$
*(p.6)*

### Definition 14: Refinement Relation
$$
\geq_2 \text{ refines } \geq_1 \iff \forall a,b: a >_1 b \implies a >_2 b
$$
A refinement relation preserves all strict preferences and may add more. Used to compare preference criteria.
*(p.7-8)*

### Definition 15: Rich PAF with Partial Preorder on Formulas
$$
\mathcal{T} = \langle \mathcal{A}, \mathcal{R}, \geq_{\mathcal{A}} \rangle \text{ where } \mathcal{A} = \text{Arg}(\Sigma)
$$
Where: arguments are built from knowledge base $\Sigma$ via Definition 2, attacks via undercut (Definition 3), and the preference $\geq_\mathcal{A}$ is lifted from a partial preorder $\geq$ on $\Sigma$'s formulas.
*(p.9)*

### Two Preference Liftings
- **Democratic relation** ($\geq_d$): $a \geq_d b$ iff for every hypothesis in $a$'s support, there exists a hypothesis in $b$'s support at least as preferred. *(p.8)*
- **Elitist relation** ($\geq_e$): $a \geq_e b$ iff for every hypothesis in $b$'s support, there exists a hypothesis in $a$'s support at least as preferred. *(p.8)*

### Definition 16: Preferred Sub-theory
$$
S \subseteq \Sigma \text{ is a preferred sub-theory iff: } (1) S \in \text{mc}(\Sigma), (2) \forall x \in \Sigma \setminus S, \exists S' \subseteq S \text{ s.t. } S' \cup \{x\} \text{ is inconsistent and } \forall y \in S': y \geq x
$$
*(p.10)*

### Definition 17: Democratic Sub-theory
$$
S \subseteq \Sigma \text{ is a democratic sub-theory iff } S \text{ is a maximal (for set inclusion) consistent subbase of } \Sigma
$$
*(p.10)*

### Definition 18: Stratified Knowledge Base
$$
\Sigma = \Sigma_1 \cup \cdots \cup \Sigma_n \text{ where } \Sigma_1 \text{ is most preferred}
$$
With total preorder: $x \geq y$ iff $\text{Level}(x) \leq \text{Level}(y)$ (lower level number = higher priority).
*(p.9)*

### Theorem 1 (Preferred Sub-theory Correspondence)
For a rich PAF $\mathcal{T}$ built over a stratified knowledge base $\Sigma$ with democratic relation $\geq_d$:
$$
\text{Ext}_s(\mathcal{F}_\mathcal{T}) = \{\text{Arg}(S) \mid S \text{ is a preferred sub-theory of } \Sigma\}
$$
The stable extensions of the rich PAF are exactly the argument sets of the preferred sub-theories. *(p.11)*

### Theorem 2 (Unique Preferred Sub-theory from Unique Democratic Sub-theory)
For a stratified knowledge base $\Sigma$: if $\mathcal{U}(\Sigma)$ is the unique democratic sub-theory, then each stable extension of $\text{Arg}(\mathcal{U}(\Sigma))$ corresponds to a preferred sub-theory, and vice versa. *(p.11-12)*

### Theorem 3 (Democratic Sub-theory Correspondence)
$$
S \text{ is a maximal consistent subset of } \mathcal{U}(\Sigma) \iff \text{Arg}(S) \text{ is a stable extension of } \text{Arg}(\mathcal{U}(\Sigma))
$$
*(p.12)*

### Theorem 4 (Full Correspondence)
The stable extensions of $\text{Arg}(\mathcal{U}(\Sigma))$ with undercut and democratic relation are exactly the stable extensions of the rich PAF, which are exactly the argument closures of the preferred sub-theories.
*(p.12-13)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Knowledge base | $\Sigma$ | — | — | Finite set of propositional formulas | 2 | Potentially inconsistent |
| Preference relation | $\geq$ | — | — | Partial or total preorder on $\mathcal{A}$ or $\Sigma$ | 3 | Strict part: $a > b$ iff $a \geq b$ and not $b \geq a$ |
| Certainty level | Level(x) | — | — | $1..n$ for stratified KB | 9 | Lower = more certain/preferred |
| Number of strata | $n$ | — | — | $\geq 1$ | 9 | In stratified KB $\Sigma = \Sigma_1 \cup \cdots \cup \Sigma_n$ |

## Methods & Implementation Details

- **Attack inversion, not removal:** The critical distinction from prior work. When $b > a$ in a symmetric attack pair $(a,b)$ and $(b,a)$, the rich PAF keeps $(a,b)$ (the attack on the preferred argument) and removes $(b,a)$. It does NOT remove both. This preserves the defeat direction. *(p.4-5)*
- **Critical attacks are untouchable:** Asymmetric attacks (where only one direction exists) are never modified by preferences. This prevents the consistency violations found in existing PAFs. *(p.4)*
- **Two-phase process for handling inconsistency in stratified KBs:** (1) compute the unique democratic sub-theory $\mathcal{U}(\Sigma)$ (the formulas surviving preference-based filtering), (2) compute maximal consistent subsets of $\mathcal{U}(\Sigma)$ to get the preferred sub-theories. *(p.10)*
- **Algorithm for computing democratic sub-theory** $\mathcal{U}(\Sigma)$ of a stratified KB: start with $\Sigma_1$ (most certain); at each level $i$, add formulas from $\Sigma_i$ that don't conflict with higher-priority formulas; if a formula $x \in \Sigma_i$ conflicts with already-included formulas, keep only formulas with certainty level $\leq i$. Formally: $\mathcal{U}(\Sigma) = \bigcup_{i=1}^{n} \text{Free}(\Sigma_i, \bigcup_{j<i} \Sigma_j)$ where $\text{Free}$ removes dominated conflicting formulas. *(p.10)*
- **Refinement as a preference-selection criterion:** Given two preference criteria that both satisfy the framework's requirements, a refinement relation (Definition 14) can determine which is "finer" — i.e., which resolves more conflicts. The democratic relation refines the elitist relation. *(p.7-8)*
- **Computing Def(T):** For each attack pair: if asymmetric, keep it; if symmetric, keep the attack where the attacker is not strictly less preferred. This is a simple filter over the original attack relation. *(p.4-5)*

## Figures of Interest
- **Fig 1 (p.2):** Argumentation framework $\mathcal{F}_2$ from Example 2 showing grounded extension.
- **Fig 2 (p.5):** Comparison of existing PAF (top) versus rich PAF (bottom) for the same knowledge base. Demonstrates that inverting rather than removing attacks yields correct extensions.
- **Fig 3 (p.12):** Preferred sub-theories of a knowledge base $\Sigma$ and their relationship to stable extensions of the rich PAF. Shows the one-to-one correspondence.
- **Fig 4 (p.13):** Summary diagram showing links between democratic sub-theories, preferred sub-theories, and stable extensions of the rich PAF.

## Results Summary
The paper proves that:
1. Existing PAFs (Definition 7) can violate conflict-freeness: extensions may contain arguments that attack each other in the original relation $\mathcal{R}$, even when the knowledge base is consistent. *(p.4)*
2. The rich PAF (Definition 9) guarantees conflict-free extensions (Property 1). *(p.5)*
3. When the preference is a total preorder and the attack relation is symmetric, the rich PAF has a unique stable = preferred = grounded extension. *(p.6)*
4. When the attack relation is symmetric and the preference is a linear order (i.e., reflexive, antisymmetric, transitive, and complete), the rich PAF has a unique stable/preferred extension, and this extension equals the grounded extension (computed in $O(n^2)$ time). *(p.6)*
5. Refinement (Definition 14) is transitive and can be used to select between preference criteria. The democratic relation refines the elitist relation. *(p.7-8)*
6. The stable extensions of the rich PAF correspond one-to-one with the preferred sub-theories of the underlying knowledge base (Theorems 1-4). *(p.11-13)*

## Limitations
- The framework handles only propositional logic with undercut attacks. Extension to first-order logic or other attack types (rebut) is not addressed. *(p.14)*
- The paper focuses on the flat (non-recursive) case; recursive argumentation frameworks are not considered. *(p.14)*
- The approach inverts attacks rather than removing them, which changes the defeat structure. The authors acknowledge this is a design choice that trades off against alternative approaches. *(p.14)*
- Only undercut is used as the attack relation in instantiation. Rebut-based attacks would require separate treatment. *(p.2)*

## Arguments Against Prior Work
- **Amgoud & Cayrol 2002 PAF:** Removing attacks based on preferences can violate conflict-freeness. Example 4 (p.5) shows a PAF where the grounded, preferred, and stable extensions contain arguments that attack each other in $\mathcal{R}$. *(p.4-5)*
- **Bench-Capon 2003 value-based AF:** Uses preferences to remove attacks but only considers one role of preferences (determining acceptable arguments), not the other (resolving conflicts). Also suffers from the same consistency problem when attacks are not symmetric. *(p.1, 14)*
- **Modgil & Prakken 2013 ASPIC+:** Their framework is an instantiation of Dung's framework with preferences handled at the rule level. The authors note it models in detail a specific case (defeasible rules) but "only one role of preferences: handling critical attacks." The approach does not handle both roles (conflict resolution AND argument comparison) in a unified way. Additionally, their completeness results apply only when conditions are met that the rich PAF approach handles more generally. *(p.14)*
- **Brewka 2013 abstract dialectical frameworks:** Preferences are defined by Cayrol, Bench-Capon, and Simari, but these only use preferences to remove attacks without considering critical vs. non-critical distinctions. *(p.14)*

## Design Rationale
- **Inversion over removal:** The key architectural choice. Removing an attack $(a,b)$ when $b > a$ is wrong because it eliminates information about conflicts. Inverting means the defeat direction changes but the conflict is still recorded. This preserves the ability to detect and handle inconsistency. *(p.4-5)*
- **Critical attacks are preserved:** Asymmetric attacks represent genuine logical conflicts (the attacker's conclusion negates a premise of the attacked argument, but not vice versa). No preference ordering should override such structural conflicts. *(p.4)*
- **Preference on formulas, lifted to arguments:** Rather than defining preferences directly on arguments (which is difficult in practice), preferences are defined on the knowledge base's formulas and lifted to arguments via democratic or elitist relations. This is more natural and connects to existing work on stratified knowledge bases. *(p.8-9)*
- **Democratic relation preferred over elitist:** The democratic relation refines the elitist relation (Property 10), meaning it resolves more conflicts while preserving all the ones the elitist relation resolves. This makes it strictly better as a preference lifting. *(p.8)*

## Testable Properties
- **P1:** For any rich PAF $\mathcal{T}$, every extension under any Dung semantics must be conflict-free w.r.t. the original attack relation $\mathcal{R}$ (not just Def($\mathcal{T}$)). *(p.5)*
- **P2:** If the preference $\geq$ is a total preorder and the attack relation is symmetric, the rich PAF must have exactly one stable extension, which equals its preferred extension and grounded extension. *(p.6)*
- **P3:** If $\mathcal{F}$ has no critical attacks (all attacks symmetric) and the preference is total, then the rich PAF's extensions equal the corresponding AF computed by the existing (flawed) PAF method. *(p.5)*
- **P4:** Refinement is transitive: if $\geq_3$ refines $\geq_2$ and $\geq_2$ refines $\geq_1$, then $\geq_3$ refines $\geq_1$. *(p.7)*
- **P5:** The democratic relation refines the elitist relation for any knowledge base. *(p.8)*
- **P6:** For a stratified knowledge base, the stable extensions of the rich PAF are exactly $\{\text{Arg}(S) \mid S \in \text{PST}(\Sigma)\}$ where PST is the set of preferred sub-theories. *(p.11)*
- **P7:** The grounded extension of the rich PAF equals the intersection of all complete extensions. *(p.16, Appendix)*
- **P8:** Def($\mathcal{T}$) = $\mathcal{R}$ when $\geq$ is empty (no preferences). The rich PAF reduces to the standard AF. *(p.5)*

## Relevance to Project
**Critical for propstore's argumentation layer.** This paper directly addresses the question of how preference orderings feed into argumentation frameworks — the exact bridge needed between IC merging (which produces preference orderings via syncretic assignments) and ASPIC+ (which computes with preferences via last-link/weakest-link).

Key implications:
1. **IC merge output as preference source:** IC merging produces total preorders over formulas. This paper's Definition 18 (stratified knowledge bases) is exactly that structure. The rich PAF instantiation (Section 5) shows how to build an argumentation framework from such a stratified base.
2. **Existing ASPIC+ preference handling is incomplete:** The paper explicitly criticizes Modgil & Prakken's approach as handling only one role of preferences. For propstore, this means the current ASPIC+ bridge may need enrichment to handle both roles.
3. **Attack inversion vs removal:** propstore's current `aspic_bridge.py` should use Def($\mathcal{T}$) (the inverted attack relation) rather than simply removing attacks where the attacker is less preferred.
4. **Democratic relation for lifting:** When lifting formula-level preferences to argument-level preferences, the democratic relation is strictly better than the elitist relation (Property 10).
5. **Correspondence theorems:** The one-to-one correspondence between preferred sub-theories and stable extensions (Theorem 1) means the argumentation layer and belief revision layer should produce equivalent results — a strong consistency check.

## Open Questions
- [ ] How does the rich PAF interact with ASPIC+'s structured argumentation? Can Def($\mathcal{T}$) be computed over ASPIC+ arguments with strict/defeasible rules?
- [ ] Does the two-phase process (democratic sub-theory + maximal consistent subsets) map onto propstore's ATMS environment structure?
- [ ] Can the refinement relation (Definition 14) be used to compare different IC merging operators' preference outputs?
- [ ] How do the correspondence theorems extend to non-stratified (partially ordered) knowledge bases?

## Related Work Worth Reading
- Amgoud, L. & Cayrol, C. (2002): Original PAF framework — the one shown to be flawed here *(ref [1])* --> NOW IN COLLECTION: [[Amgoud_2002_ReasoningModelProductionAcceptable]]
- Bench-Capon, T. (2003): Value-based argumentation frameworks *(ref [6])*
- Modgil, S. & Prakken, H. (2013): ASPIC+ with preferences *(ref [28])* --> NOW IN COLLECTION: [[Modgil_2018_GeneralAccountArgumentationPreferences]]
- Brewka, G. (2013): Abstract dialectical frameworks *(ref [7])* --> NOW IN COLLECTION: [[Brewka_2013_AbstractDialecticalFrameworksRevisited]]
- Benferhat, S. et al. (1993): Preferred sub-theories — the belief revision concept that corresponds to stable extensions *(ref [4])*
- Cayrol, C. & Lagasquie-Schiex, M.C. (2005): Bipolar argumentation *(ref [12])* --> NOW IN COLLECTION: [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]]

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — foundational AF framework (Definition 1) on which this paper builds
- [[Amgoud_2002_ReasoningModelProductionAcceptable]] — the original PAF framework by the same first author, shown here to be flawed when attacks are asymmetric
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — companion paper by same authors proposing preference handling at the semantics level (pref-stable) rather than at the attack level; this paper takes the attack-level approach but fixes the consistency bug
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — ASPIC+ with preferences; explicitly criticized here as handling only one role of preferences (critical attacks). Their Theorem 31 (stable extensions = preferred subtheories) is the same correspondence this paper proves via a different route
- [[Brewka_1989_PreferredSubtheoriesExtendedLogical]] — preferred subtheories framework; Theorems 1-4 here prove rich PAF stable extensions correspond one-to-one with Brewka's preferred subtheories
- [[Brewka_2013_AbstractDialecticalFrameworksRevisited]] — abstract dialectical frameworks; cited as another approach that uses preferences to remove attacks without distinguishing critical vs non-critical
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — bipolar argumentation with support; cited for acceptability semantics
- [[Caminada_2006_IssueReinstatementArgumentation]] — reinstatement labellings; used for extension semantics definitions
- [[Pollock_1987_DefeasibleReasoning]] — defeasible reasoning; undercut attack (Definition 3) derives from Pollock's distinction
- [[Coste-Marquis_2005_SymmetricArgumentationFrameworks]] — symmetric AFs; this paper's Property 4 shows rich PAF reduces correctly when attack relation is symmetric

### New Leads (Not Yet in Collection)
- Benferhat, Dubois & Prade (1993) — "Argumentative inference in uncertain and inconsistent knowledge bases" — preferred sub-theories concept that corresponds to rich PAF stable extensions
- Bench-Capon (2003) — "Persuasion in practical argument using value-based argumentation frameworks" — alternative preference framework using audience-relative values

### Cited By (in Collection)
- [[Thimm_2020_ApproximateReasoningASPICArgumentSampling]] — cites this paper in the context of preference-based argumentation

### Conceptual Links (not citation-based)
- [[Konieczny_2002_MergingInformationUnderConstraints]] — **Strong.** IC merging produces total preorders over interpretations via syncretic assignments. This paper's Definition 18 (stratified knowledge bases with total preorder on formulas) is exactly the output structure IC merging produces. The bridge: IC merge result -> stratified KB -> rich PAF -> stable extensions = preferred subtheories.
- [[Coste-Marquis_2007_MergingDung'sArgumentationSystems]] — **Strong.** Merging of argumentation frameworks uses distance-based operators from IC merging applied to attack relations. This paper provides the preference-handling layer that sits between merged beliefs and argumentation computation.
- [[Darwiche_1997_LogicIteratedBeliefRevision]] — **Moderate.** Iterated revision produces changing preference orderings over models. This paper's refinement relation (Definition 14) could serve as a criterion for comparing the preference orderings produced by different revision sequences.
- [[Baumann_2015_AGMMeetsAbstractArgumentation]] — **Moderate.** AGM revision applied to argumentation frameworks. This paper's correspondence theorems (stable extensions = preferred subtheories) connect the argumentation and belief revision perspectives that Baumann bridges.
