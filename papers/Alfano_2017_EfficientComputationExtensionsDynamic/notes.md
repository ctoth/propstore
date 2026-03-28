---
title: "Efficient Computation of Extensions for Dynamic Abstract Argumentation Frameworks: An Incremental Approach"
authors: "Gianvincenzo Alfano, Sergio Greco, Francesco Parisi"
year: 2017
venue: "IJCAI 2017"
doi_url: "https://doi.org/10.24963/ijcai.2017/8"
---

# Efficient Computation of Extensions for Dynamic Abstract Argumentation Frameworks: An Incremental Approach

## One-Sentence Summary
Provides an incremental algorithm for recomputing extensions of dynamic abstract argumentation frameworks (where arguments and attacks are added or removed) by identifying a "reduced AF" containing only the influenced arguments, achieving orders-of-magnitude speedup over from-scratch computation for grounded, preferred, stable, and complete semantics.

## Problem Addressed
Standard AF solvers recompute extensions from scratch whenever the AF changes. In dynamic settings (arguments/attacks added or removed over time), this is wasteful because small changes typically affect only a subset of arguments. Prior incremental approaches were limited to specific semantics (e.g., grounded only) or specific update types (e.g., additions only). This paper provides a general incremental approach covering multiple semantics and both additions and deletions. *(p.0)*

## Key Contributions
- An incremental technique for recomputing extensions of an updated AF based on identifying a sub-AF called "reduced AF" containing only the portion of the AF influenced by the update *(p.0)*
- Covers grounded, preferred, stable, and complete semantics *(p.0)*
- Handles both single updates and sequences of multiple updates simultaneously *(p.3-4)*
- Experimental evaluation showing orders-of-magnitude speedup over ICCMA'15 competition solvers *(p.4-5)*

## Methodology
The approach works by: (1) computing the "influenced set" of arguments whose acceptance status may change due to an update, (2) constructing a "reduced AF" that includes only the influenced arguments plus relevant context, (3) computing extensions of the reduced AF, (4) combining the result with the unchanged portion of the initial extension to obtain the extension of the updated AF. *(p.0-1)*

## Key Equations / Statistical Models

### Argumentation Semantics Criteria (Table 1)

$$
\text{cf}(S, AF) \iff \nexists\, a, b \in S : (a, b) \in R
$$
Where: cf = conflict-free, S = set of arguments, AF = (A, R), R = attack relation
*(p.1)*

$$
\text{admissible}(S, AF) \iff \text{cf}(S, AF) \land \forall a \in S : S \text{ defends } a
$$
*(p.1)*

$$
\text{complete}(S, AF) \iff \text{admissible}(S, AF) \land \forall a \in A : (S \text{ defends } a \Rightarrow a \in S)
$$
*(p.1)*

$$
\text{grounded}(S, AF) \iff S \text{ is the } \subseteq\text{-minimal complete extension}
$$
*(p.1)*

$$
\text{preferred}(S, AF) \iff S \text{ is a } \subseteq\text{-maximal complete extension}
$$
*(p.1)*

$$
\text{stable}(S, AF) \iff \text{cf}(S, AF) \land \forall a \in A \setminus S : \exists b \in S : (b, a) \in R
$$
*(p.1)*

### Labelling Notation
A labelling for an AF = (A, R) is a total function $\mathcal{L} : A \to \{in, out, undec\}$ where:
- $\mathcal{L}(a) = in$ iff $\forall b : (b,a) \in R \Rightarrow \mathcal{L}(b) = out$
- $\mathcal{L}(a) = out$ iff $\exists b : (b,a) \in R \land \mathcal{L}(b) = in$
- $\mathcal{L}(a) = undec$ means $a$ is not labelled $in$ or $out$, i.e., $\lnot\text{OCF} \land \lnot\text{CCF}$ means is rejected, while undec is neither *(p.1)*

### Influenced Set Construction

The set of arguments influenced by an update is computed as a fixpoint. For an update adding/removing attacks or arguments: *(p.2)*

For adding an argument $a$ and attacks:
$$
I = \{a\} \cup \{b \mid (a,b) \in R' \text{ or } (b,a) \in R'\} \cup \text{reachable from these via attacks}
$$
Where: $R'$ = new attacks added by the update
*(p.2)*

For removing an argument $a$:
$$
I = \{a\} \cup \{b \mid b \text{ was defended/attacked by } a\} \cup \text{transitively reachable}
$$
*(p.2)*

### Reduced AF (Definition 1)

**Definition 1 (AF for appending a set of updates).** Let $AF = (A, S)$ be an AF, and $E_\sigma$ a $\sigma$-extension for $AF$. Let $U = \{u_1, \ldots, u_m\}$ be a set of updates, and $I^+ = \{a \mid a \text{ is a new argument or target of new attack}\}$ be the set of relevant updates obtained from $U$ as follows. $AF^U$ denotes the AF obtained from $AF$ by applying $U$. *(p.3)*

$$
AF' = (A' \cup I, \{(a_1, b_1), \ldots, (a_k, b_k)\} \cup R_I)
$$
Where: $A'$ = arguments of original AF, $I$ = influenced set, $R_I$ = attacks involving influenced arguments
*(p.3)*

The reduced AF $R(AF, E_\sigma, AF^U, I)$ consists of:
- The influenced set $I$ (arguments whose status may change)
- Arguments that attack or are attacked by arguments in $I$
- All attacks among these arguments in the updated AF *(p.3)*

### Correctness Theorem

**Theorem 1.** Let $E_\sigma$ be an AF, and $AF' = (A', R')$ be an AF obtained from $AF$ by a set of updates. Let $\sigma$ be any semantics in $\{gr, pr, st, co\}$. Then for any $\sigma$-extension $\hat{E}_\sigma$ of $R(AF, E_\sigma, AF', I)$ either $\hat{E}_\sigma \cup (E_\sigma \setminus I)$ is a $\sigma$-extension of the updated $AF'$, or $\hat{E}_\sigma$ where $\hat{E}_\sigma = \emptyset$ is a $\sigma$-extension of $AF'$. *(p.3)*

### Multiple Updates (Theorem 2)

**Theorem 2.** Let $AF$ be an AF, $k = |(h, t)|$, and $E_\sigma$ is a $\sigma$-extension of $AF$. Let $U = \{u_1, \ldots, u_m\}$ be a set of updates. If $Solver_\sigma$ is sound and complete then Algorithm 1 computes $E \in \mathcal{E}_\sigma(AF_U)$ if $\mathcal{E}_\sigma(AF_U) \neq \emptyset$, otherwise it returns $\bot$. *(p.4)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of arguments | \|A\| | count | - | up to 10K+ | 4 | Benchmark AFs |
| Percentage of attacks | - | % | - | varies | 4 | Relative to |A| |
| Update percentage | S | % | 1 | 1-? | 4 | % of attacks modified in single update |
| Multiple update count | S (multiple) | count | 5/2 | varies | 4 | % for multiple updates |

## Methods & Implementation Details

### Algorithm 1: IncrExt-Alg (p.3)

```
Input: AF = (A, R), sigma (semantics), E_sigma (current extension),
       updates = {(+/-, a, b), ...} (additions/removals of args/attacks)
Output: E'_sigma (new extension of updated AF)

1. function IncrExt(AF, sigma, E_sigma, updates)
2.   Compute AF' by applying updates to AF
3.   if sigma = gr then
4.     Compute influenced set I
5.     Compute reduced AF R(AF, E_sigma, AF', I)
6.     E' = Solver_sigma(R)   // compute extension of reduced AF
7.     return E' union (E_sigma \ I)   // combine with unchanged part
8.   else  // sigma in {pr, st, co}
9.     if E_sigma is still a sigma-extension of AF' then
10.      return E_sigma   // no change needed
11.    else
12.      Compute influenced set I
13.      Compute reduced AF R(AF, E_sigma, AF', I)
14.      E' = Solver_sigma(R)
15.      if E' != empty then
16.        return E' union (E_sigma \ I)
17.      else
18.        return Solver_sigma(AF')  // fall back to from-scratch
19.    end if
```
*(p.3)*

Key insight: For grounded semantics, the algorithm always works incrementally. For preferred/stable/complete, it first checks if the existing extension is still valid (Line 4/9), and only if not does it compute the reduced AF. If the reduced AF yields no extension (e.g., the update destroyed the structure too much), it falls back to from-scratch computation (Line 7/18). *(p.3)*

### Handling Multiple Updates Simultaneously

**Definition 3 (AF for appending a set of updates).** When multiple updates are applied simultaneously, the influenced set is the union of influenced sets of individual updates, and the reduced AF incorporates all changes at once. This avoids recomputing for each update individually. *(p.3-4)*

**Theorem 3.** Correctness extends to sets of multiple updates — the algorithm produces correct extensions when given a batch of updates. *(p.4)*

### Function Solver_sigma
Uses any existing sound and complete solver for semantics $\sigma$. The paper uses the ICCMA'15 competition winners as the base solver. The key observation is that the solver only needs to run on the (typically much smaller) reduced AF rather than the full AF. *(p.3)*

## Figures of Interest
- **Fig 1 (p.1):** Four example AFs (a-d) showing different attack structures used throughout the paper. AF (a) is the running example with arguments {a,b,c,d,e} and various attacks.
- **Fig 2 (p.5):** Runtime comparison graphs — log scale plots showing run times for single and multiple updates across grounded (gr), preferred (pr), stable (st), and complete (co) semantics for three benchmark datasets (TestSetSmall, TestSetMedium/Large implied). Shows incremental approach (solid lines) consistently below from-scratch competitors (dashed lines).

## Results Summary
- Experiments on ICCMA'15 benchmark AFs with three categories: TestSetSmall (few args, many attacks), TestSetStable (many args, complex structure with SCCs), TestSetSmall1 (many complete/preferred/stable extensions) *(p.4)*
- For single updates: randomly selected an update of form $(+, a, b)$ or $(-,a,b)$; for multiple updates randomly generated a set of single updates *(p.4)*
- Used ICCMA'15 competition solver CoQuiAAS for gr/st/co, and ASPARTIX for pr *(p.4)*
- Results show the incremental approach run times were almost equal to from-scratch times for single updates on TestSetSmall, and showed increasing advantage on larger/complex AFs *(p.4-5)*
- For all four semantics, incremental technique outperforms from-scratch computation, with improvements being larger as the ratio of the update size to AF size decreases *(p.5)*
- The incremental approach is on average 1-2 orders of magnitude faster than from-scratch for single updates, with the reduced AF being about 1% of the full AF for single updates and 5% for multiple updates with about 1% of attacks updated *(p.5)*
- Considering updates that add/remove arguments does not affect efficiency *(p.5)*

## Limitations
- When the influenced set encompasses (nearly) the entire AF, the incremental advantage disappears and may add overhead *(p.5)*
- Falls back to from-scratch computation when the reduced AF does not yield a valid extension for non-grounded semantics *(p.3)*
- Results for complete semantics showed the extensions obtained are analogous to grounded (all from TestSetSmall1 only had grounded-equivalent complete extensions) *(p.5)*
- Only considers Dung AF semantics (no structured argumentation, no preferences, no support) *(p.0)*
- Only considers single-status (one extension at a time), not enumeration of all extensions *(p.1)*

## Arguments Against Prior Work
- Computational Models of Argumentation (COMMA) and ICCMA competitions focus on from-scratch computation, neglecting dynamic settings *(p.0)*
- Prior incremental work by Liao et al. (2011), Baroni et al. (2014) focused on division-based methods but did not provide general incremental algorithms *(p.0)*
- Boella et al. (2009) studied single extensions but only for additions, not deletions *(p.0)*
- Cayrol et al. (2014) and Doutre and Mailly (2018) studied change but from a different angle (characterizing change operations rather than efficient recomputation) *(p.0)*
- Bisquert et al. (2013) and Baumann and Brewka (2010) studied enforcement (making arguments accepted) rather than efficient recomputation *(p.0)*
- The approach by Liao et al. (2011) for division-based semantics, while incremental, is limited to specific semantics and does not handle arbitrary updates *(p.5)*

## Design Rationale
- The "influenced set" concept allows identifying exactly which arguments may change status, avoiding unnecessary recomputation *(p.2)*
- The reduced AF preserves enough context (attacking/defending relationships) to correctly compute the new extension without needing the full AF *(p.3)*
- Checking whether the existing extension is still valid (for preferred/stable/complete) avoids unnecessary work when updates don't affect the extension *(p.3)*
- Using existing competition solvers as black boxes means the incremental technique benefits from any improvements in base solvers *(p.3)*

## Testable Properties
- For grounded semantics: if no argument in the influenced set is in the grounded extension of the original AF, and no new argument attacks/is attacked by the grounded extension, the grounded extension is preserved *(p.2)*
- The reduced AF is always a subset of or equal to the updated AF *(p.3)*
- For any semantics sigma in {gr, pr, st, co}: E' union (E_sigma \ I) is a sigma-extension of the updated AF (when E' is a sigma-extension of the reduced AF) *(p.3)*
- The influenced set I is computable in polynomial time *(p.2)*
- For single updates, the reduced AF is typically about 1% the size of the full AF *(p.5)*
- The incremental approach never produces an incorrect extension (soundness from Theorems 1-3) *(p.3-4)*

## Relevance to Project
Directly relevant to propstore's argumentation layer. The Dung AF implementation (`dung.py`) currently recomputes extensions from scratch whenever the framework changes. This paper provides the theoretical foundation and algorithm for incremental recomputation, which would be critical for:
1. Dynamic scenarios where claims/stances are added/removed
2. ATMS-style context switching where the AF changes frequently
3. Performance optimization for large AFs
4. The world model layer where hypothetical reasoning modifies the AF

The "influenced set" concept maps naturally to propstore's needs — when a new claim arrives, only arguments reachable from that claim's argument need recomputation.

## Open Questions
- [ ] How does the influenced set interact with ASPIC+ structured arguments (where adding a premise can affect multiple arguments)?
- [ ] Can the reduced AF technique be extended to bipolar AFs (with support)?
- [ ] How does this interact with probabilistic AFs (PrAF) where argument/attack probabilities change?
- [ ] The fallback to from-scratch for non-grounded semantics — how often does this occur in practice for propstore-sized AFs?

## Related Work Worth Reading
- [Liao et al., 2011] — Division-based semantics for incremental computation (already partially covered)
- [Boella et al., 2009] — Dynamics of argumentation with single extensions (already in collection)
- [Cayrol et al., 2014] — Change in abstract argumentation frameworks (already in collection)
- [Baumann and Brewka, 2010] — Expanding argumentation frameworks (already in collection)
- [Alfano, Greco, Parisi 2019] — Extended journal version with more detail on grounded extension algorithm
- [Doutre and Mailly, 2018] — Constraints and changes survey (already in collection)
