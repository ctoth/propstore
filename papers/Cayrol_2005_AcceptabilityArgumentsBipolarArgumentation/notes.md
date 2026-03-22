---
title: "On the Acceptability of Arguments in Bipolar Argumentation Frameworks"
authors: "C. Cayrol, M.C. Lagasquie-Schiex"
year: 2005
venue: "ECSQARU 2005, LNAI 3571"
doi_url: "https://doi.org/10.1007/11518655_33"
---

# On the Acceptability of Arguments in Bipolar Argumentation Frameworks

## One-Sentence Summary
Extends Dung's abstract argumentation framework with an independent support relation alongside defeat, defining bipolar argumentation frameworks (BAFs) with new acceptability semantics (d-admissible, s-admissible, c-admissible extensions) that enforce coherence between support and defeat.

## Problem Addressed
Classical argumentation frameworks (Dung 1995) model only one kind of interaction between arguments: defeat/attack. However, arguments can also support each other (e.g., confirming a premise used by another argument). This paper addresses how to handle both defeat and support as independent, first-class relations, and how to redefine acceptability semantics accordingly.

## Key Contributions
- Formal definition of bipolar argumentation frameworks (BAFs) with independent defeat and support relations
- New interaction types: supported defeat, indirect defeat, direct defeat
- Two notions of coherence for sets of arguments: internal coherence (conflict-free) and external coherence (safe sets)
- Three new admissibility-based semantics: d-admissible, s-admissible, c-admissible
- Generalized stable and preferred extensions for BAFs
- Structural properties of extensions in acyclic BAFs (Property 4)

## Methodology
Extends Dung's abstract approach by adding a support relation to the framework tuple. Derives new types of defeat by combining support sequences with direct defeats. Defines set-level operations (set-defeat, set-support) and builds coherence and admissibility notions on top. Restricts main results to acyclic bipolar interaction graphs.

## Key Definitions

### Definition 1 (Abstract Bipolar Argumentation Framework)
A BAF is a tuple $\langle \mathcal{A}, \mathcal{R}_{def}, \mathcal{R}_{sup} \rangle$ where:
- $\mathcal{A}$ is a finite set of arguments
- $\mathcal{R}_{def} \subseteq \mathcal{A} \times \mathcal{A}$ is a defeat relation
- $\mathcal{R}_{sup} \subseteq \mathcal{A} \times \mathcal{A}$ is a support relation

Represented as a directed graph with two edge types.

### Definition 2 (Bipolar Interaction Graph)
The graph associated with a BAF has two kinds of edges: one for defeat, one for support. A leaf is an argument with no defeaters and no supporters.

### Definition 3 (Supported and Indirect Defeat)

A **supported defeat** for argument $B$ is a sequence:

$$
A_1 \mathcal{R}_1 \ldots \mathcal{R}_{n-1} A_n, \quad n \geq 3
$$

where $A_n = B$, $\forall i = 1 \ldots n-2$, $\mathcal{R}_i = \mathcal{R}_{sup}$ and $\mathcal{R}_{n-1} = \mathcal{R}_{def}$.

An **indirect defeat** for argument $B$ is a sequence:

$$
A_1 \mathcal{R}_1 \ldots \mathcal{R}_{n-1} A_n, \quad n \geq 3
$$

where $A_n = B$, $\forall i = 2 \ldots n-1$, $\mathcal{R}_i = \mathcal{R}_{sup}$ and $\mathcal{R}_1 = \mathcal{R}_{def}$.

A **direct defeat** is a simple $(A, B) \in \mathcal{R}_{def}$ (also a supported defeat of length 2 by extension).

### Definition 4 (Set-Defeat and Set-Support)
Let $S \subseteq \mathcal{A}$, $A \in \mathcal{A}$:
- $S$ **set-defeats** $A$ iff there exists a supported defeat or indirect defeat for $A$ from an element of $S$
- $S$ **set-supports** $A$ iff there exists a sequence $A_1 \mathcal{R}_1 \ldots \mathcal{R}_{n-1} A_n$, $n \geq 2$, with $\forall i = 1 \ldots n-1$, $\mathcal{R}_i = \mathcal{R}_{sup}$, $A_n = A$, and $A_1 \in S$

### Definition 5 (Defence by a Set)
$S \subseteq \mathcal{A}$ defends collectively $A \in \mathcal{A}$ iff $\forall B \in \mathcal{A}$, if $\{B\}$ set-defeats $A$ then $\exists C \in S$ such that $\{C\}$ set-defeats $B$.

### Definition 6 (Conflict-Free Set)
$S \subseteq \mathcal{A}$ is conflict-free iff $\nexists A, B \in S$ such that $\{A\}$ set-defeats $B$.

Note: This generalizes Dung's conflict-free using set-defeats rather than just direct defeat.

### Definition 7 (Safe Set)
$S \subseteq \mathcal{A}$ is safe iff $\nexists B \in \mathcal{A}$ such that $S$ set-defeats $B$ and either $S$ set-supports $B$, or $B \in S$.

Safe = no element is both set-defeated and set-supported (or member) of $S$.

### Property 1
- If $S$ is safe, then $S$ is conflict-free
- If $S$ is conflict-free and closed for $\mathcal{R}_{sup}$, then $S$ is safe

### Definition 8 (Stable Extension)
$S \subseteq \mathcal{A}$ is a stable extension iff $S$ is conflict-free and $\forall A \notin S$, $S$ set-defeats $A$.

### Definition 9 (d-Admissible Set)
$S \subseteq \mathcal{A}$ is d-admissible iff $S$ is conflict-free and $S$ defends all its elements.

### Definition 10 (s-Admissible Set)
$S \subseteq \mathcal{A}$ is s-admissible iff $S$ is safe and $S$ defends all its elements.

### Definition 11 (c-Admissible Set)
$S \subseteq \mathcal{A}$ is c-admissible iff $S$ is conflict-free, $S$ is closed for $\mathcal{R}_{sup}$, and $S$ defends all its elements.

Note: c-admissible implies s-admissible (by Property 1).

### Definition 12 (Preferred Extensions)
- A **d-preferred** extension is a maximal (for set-inclusion) d-admissible set
- A **s-preferred** extension is a maximal s-admissible set
- A **c-preferred** extension is a maximal c-admissible set

### Property 4 (Acyclic BAFs)
Let $S$ be the unique stable extension of an acyclic BAF:
1. The s-preferred extensions and c-preferred extensions are subsets of $S$
2. If $S$ is safe, there is a unique s-preferred extension which equals $S$, which is also a d-preferred extension
3. If $S$ is not safe, each s-preferred extension is included in a s-preferred extension. If $S$ is not safe, the s-preferred extensions are the subsets of $S$ which are maximal for set-inclusion and safe
4. If $S$ is safe, $\emptyset$ is safe, there is only one c-preferred extension
5. If $S$ is not safe and $\emptyset$ is safe, there is only one c-preferred extension

## Parameters

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Arguments | $\mathcal{A}$ | - | - | finite set | Set of abstract arguments |
| Defeat relation | $\mathcal{R}_{def}$ | - | - | $\subseteq \mathcal{A} \times \mathcal{A}$ | Binary relation on arguments |
| Support relation | $\mathcal{R}_{sup}$ | - | - | $\subseteq \mathcal{A} \times \mathcal{A}$ | Binary relation on arguments, independent of defeat |

## Implementation Details

### Data Structures
- BAF: directed graph with two edge types (defeat edges, support edges)
- Can be represented as two adjacency lists or a single graph with labeled edges
- Bipolar interaction graph: single directed graph merging both relations with edge labels

### Key Algorithms (Implicit)
1. **Compute supported defeats**: Find all paths where support edges lead to a final defeat edge
2. **Compute indirect defeats**: Find all paths where a defeat edge is followed by support edges
3. **Compute set-defeat**: Check if any element of S has a supported or indirect defeat path to target
4. **Compute set-support**: Check if any element of S has a pure support path to target
5. **Check conflict-free**: For all pairs in S, verify no set-defeat exists
6. **Check safe**: Verify S does not simultaneously set-defeat and set-support (or contain) any argument
7. **Check closed for R_sup**: For all A in S, if A R_sup B then B in S
8. **Compute extensions**: Enumerate maximal admissible sets under chosen semantics

### Edge Cases
- Acyclic vs. cyclic: Main results (Property 4) only hold for acyclic bipolar interaction graphs
- Empty set is always d-admissible and s-admissible (when safe), but not necessarily c-admissible
- A stable extension may not be safe (Example 3: {A, H} is unique stable extension but not s-admissible)
- Unique stable extension always exists for acyclic BAFs (by instantiating Dung with set-defeats)

## Figures of Interest
- **Fig (page 3, Example 1):** Argumentation graph for murder trial example with 5 arguments
- **Fig (page 5, Example 2):** Bipolar interaction graph with nodes A-K showing supported defeats (A-B-C-D, E-C) and indirect defeat (G-A-B-C)
- **Fig (page 6):** Diagrams illustrating internal vs external coherence violations
- **Fig (page 9, Example 4):** Argumentation system showing {A1,A2,B} as only d-preferred, s-preferred and c-preferred extension but {A1,A3} as unique s-preferred

## Results Summary
- Three levels of admissibility semantics of increasing strength: d-admissible (weakest), s-admissible, c-admissible (strongest)
- For acyclic BAFs: unique stable extension always exists; s-preferred and c-preferred are subsets of it
- When the unique stable extension is safe, it equals the unique s-preferred extension
- c-admissible sets are always s-admissible (Property 1 consequence)
- The paper focuses on acyclic frameworks; cyclic case left for future work

## Limitations
- Results restricted to acyclic bipolar argumentation frameworks
- No computational complexity analysis provided
- No algorithms given explicitly (only definitions and properties)
- Support relation semantics not fully explored (what exactly constitutes support is application-dependent)
- Cyclic frameworks and their properties left entirely to future work
- No comparison with other approaches to handling support (e.g., evidential support)

## Testable Properties
- Safe implies conflict-free (Property 1, first part)
- Conflict-free + closed for R_sup implies safe (Property 1, second part)
- c-admissible implies s-admissible
- s-admissible implies d-admissible
- Every c-preferred extension is s-admissible
- In acyclic BAFs, a unique stable extension always exists
- The s-preferred and c-preferred extensions are subsets of the unique stable extension (acyclic case)
- Empty set is always d-admissible
- If stable extension S is safe, then S is the unique s-preferred extension

## Relevance to Project
Foundational paper for bipolar argumentation. Provides the formal definitions needed to implement argumentation frameworks that handle both attack and support between arguments/claims, which is essential for modeling evidential relationships in a propositional store where claims can both conflict with and reinforce each other.

## Open Questions
- [ ] How do these semantics extend to cyclic BAFs?
- [ ] What is the computational complexity of computing the various extensions?
- [ ] How does this relate to later work on evidential support vs. deductive support?
- [ ] Connection to ASPIC+ structured argumentation with bipolar relations?

## Related Work Worth Reading
- Dung, P.M. (1995). On the acceptability of arguments. Artificial Intelligence 77, 321-357 — foundational framework this extends
- Karacapilidis, N., Papadias, D. (2001). Computer supported argumentation and collaborative decision making — support relation in argumentation
- Amgoud, L., Cayrol, C., Lagasquie-Schiex, M.C. (2004). On the bipolarity in argumentation frameworks — companion/prior work on BAFs
- Boella, G., et al. (2004). Handbook of Philosophical Logic, Volume 4 — coalitions of arguments
- Verheij, B. (2003). Artificial argument assistants — support in argumentation

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as [1]; this paper directly extends Dung's abstract argumentation framework by adding an independent support relation. All of Cayrol's definitions (conflict-free, admissible, stable, preferred) generalize Dung's originals using set-defeat in place of direct defeat.

### New Leads (Not Yet in Collection)
- Amgoud, Cayrol, Lagasquie-Schiex (2004) — "On the bipolarity in argumentation frameworks" — companion/prior work developing the bipolar argumentation concept
- Karacapilidis, N. and Papadias, D. (2001) — "Computer supported argumentation and collaborative decision making" — practical system (Hermes) with support relations
- Verheij, B. (2002) — "On the existence and multiplicity of extensions in dialectical argumentation" — relevant to extension computation

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Dung_1995_AcceptabilityArguments]] — **Strong.** Cayrol directly extends Dung's framework. Where Dung defines admissible/preferred/stable/grounded extensions over a single attack relation, Cayrol adds a support relation and derives three new admissibility levels (d-admissible, s-admissible, c-admissible) that collapse to Dung's originals when the support relation is empty. The paper instantiates Dung's framework using set-defeats to prove existence of stable extensions in acyclic BAFs.
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — **Strong.** ASPIC+ and BAFs represent two different approaches to enriching Dung's abstract framework. ASPIC+ adds internal structure to arguments (premises, rules, conclusions) while keeping Dung's single attack relation. Cayrol adds a second relation (support) while keeping arguments abstract. Both generate Dung-style frameworks at the abstract level. A full argumentation system could combine both: structured arguments (ASPIC+) with bipolar relations (Cayrol).
- [[Clark_2014_Micropublications]] — **Moderate.** Clark's micropublication model includes both support and challenge relations between scientific claims, and explicitly references Toulmin-Verheij defeasible argumentation with bipolar networks (Use Case 8). Cayrol's BAF formalization provides the abstract semantics for determining which claims are jointly acceptable in such bipolar claim-evidence networks.
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — **Strong.** Mayer's pipeline extracts exactly the structures Cayrol formalizes: bipolar argumentation frameworks with both support and attack relations between arguments. The evidence-claim-support/attack graphs mined from RCT abstracts are concrete instances of Cayrol's BAFs, and Cayrol's acceptability semantics (d-admissible, s-admissible, c-admissible) could be applied to determine which of the extracted clinical arguments are jointly acceptable.
