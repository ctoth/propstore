---
title: "Encoding Argumentation Frameworks to Propositional Logic Systems"
authors: "Shuai Tang, Jiachao Wu, Ning Zhou"
year: 2025
venue: "arXiv preprint"
doi_url: "https://doi.org/10.48550/arXiv.2503.07351"
---

# Encoding Argumentation Frameworks to Propositional Logic Systems

## One-Sentence Summary
Provides a general methodology for encoding Dung's argumentation frameworks into multi-valued and fuzzy propositional logic systems, establishing exact model correspondences between classical AF semantics and encoded semantics, and proposing a new Lukasiewicz-based fuzzy semantics Eq^L.

## Problem Addressed
Prior work (Besnard & Doutre) encoded AFs into classical 2-valued propositional logic (PL2) for model checking. This paper asks: can we generalize this encoding to 3-valued logic (PL3) and fuzzy logic (PL[0,1]), and what argumentation semantics do the resulting encodings correspond to? *(p.2)*

## Key Contributions
- Establishes that the normal encoding ec1 with Kleene's PL3^K captures stable semantics, and ec1 with Lukasiewicz's PL3^L captures complete semantics *(p.12-14)*
- Shows that Gabbay's real equational semantics Eq^R_max and Eq^R_inverse correspond to fuzzy encoded semantics with Godel PL^G[0,1] and Product PL^P[0,1] respectively *(p.23-24)*
- Proposes a new fuzzy encoded semantics Eq^L associated with Lukasiewicz's PL^L[0,1] *(p.24-26)*
- Proves that every continuous encoded equational system is a Gabbay real equational system *(p.21)*
- Introduces the property of decreasing monotonicity for encoded equational functions, which is not required by Gabbay's framework but is naturally satisfied by the encoding *(p.19-20)*
- Establishes relationships between complete semantics and fuzzy encoded semantics via 1/2-idempotent t-norms *(p.27-29)*

## Methodology
The paper defines two encoding maps from AFs to propositional logic formulas:
1. **Normal encoding** ec1: maps each argument to a biconditional with the negation of its attackers
2. **Regular encoding** ec2: maps each argument to an implication (defense condition) conjoined with a biconditional (reinstatement condition)

These encodings are then evaluated under different propositional logic systems (PL2, PL3^K, PL3^L, PL[0,1] variants) and the resulting model sets are compared to known AF semantics. *(p.10-11)*

## Key Equations

### Normal Encoding ec1

$$
ec_1(AF) = \bigwedge_{a \in A} \left( a \leftrightarrow \bigwedge_{(b,a) \in R} \neg b \right)
$$
Where: A is the set of arguments, R is the attack relation, the conjunction over an empty set of attackers is top (true).
*(p.11)*

### Regular Encoding ec2

$$
ec_2(AF) = \bigwedge_{a \in A} \left( \left( a \to \bigwedge_{(b,a) \in R} \neg b \right) \wedge \left( a \leftrightarrow \bigwedge_{(b,a) \in R} \bigvee_{(c,b) \in R} c \right) \right)
$$
Where: the first conjunct is the defense condition (if accepted, attackers must be out), the second is reinstatement (accepted iff all attackers are counter-attacked).
*(p.11)*

### Complete Labelling (3-valued)

$$
lab(a) = \begin{cases} 1 & \text{iff } \nexists(b,a) \in R \text{ or } \forall b_i((b_i,a) \in R) : lab(b_i) = 0 \\ 0 & \text{iff } \exists b_j((b_j,a) \in R) : lab(b_j) = 1 \\ \frac{1}{2} & \text{otherwise} \end{cases}
$$
Where: 1 = in (accepted), 0 = out (rejected), 1/2 = undecided.
*(p.4)*

### Fuzzy Normal Encoded Equational System (general)

$$
\|a\| = \begin{cases} 1, & \nexists c((c,a) \in R) \\ N(\|b_1\|) * N(\|b_2\|) * \cdots * N(\|b_k\|), & \text{otherwise} \end{cases}
$$
Where: N is a negation function on [0,1], * is a t-norm, {b_1,...,b_k} are all attackers of a.
*(p.19)*

### Eq^R_inverse (Product logic)

$$
\|a\| = \begin{cases} 1, & \nexists c((c,a) \in R) \\ \prod_{i=1}^{k_a}(1 - \|b_i\|), & \text{otherwise} \end{cases}
$$
Where: {b_1,...,b_{k_a}} are all attackers of a.
*(p.9)*

### Eq^R_max (Godel logic)

$$
\|a\| = \begin{cases} 1, & \nexists c((c,a) \in R) \\ 1 - \max_{i=1}^{k_a} \|b_i\|, & \text{otherwise} \end{cases}
$$
Where: {b_1,...,b_{k_a}} are all attackers of a.
*(p.9)*

### New: Eq^L (Lukasiewicz logic)

$$
\|a\| = \begin{cases} 1, & \nexists c((c,a) \in R) \\ 0, & \sum_{i=1}^{k} \|b_i\| \geqslant 1 \\ 1 - \sum_{i=1}^{k} \|b_i\|, & \sum_{i=1}^{k} \|b_i\| < 1 \end{cases}
$$
Where: {b_1,...,b_k} are all attackers of a. An argument is totally defeated (value 0) when the sum of attacker values reaches 1.
*(p.25)*

### Encoded Equational Function h^{ec1}

$$
h^{ec_1}(x_1, x_2, \ldots, x_k) = N(x_1) * N(x_2) * \cdots * N(x_k)
$$
Where: N is a negation, * is a t-norm, x_i are attacker values.
*(p.19)*

### Binarization T2

$$
T_2(lab_{num})(a) = lab_2(a) = \begin{cases} 1 & lab_{num}(a) = 1 \\ 0 & lab_{num}(a) \neq 1 \end{cases}
$$
*(p.10)*

### Ternarization T_com

$$
T_{\text{com}}(lab_{num})(a) = \begin{cases} 1 & \text{iff } lab_{num}(a) = 1 \\ 0 & \text{iff } \exists b_i((b_i,a) \in R) : T_{\text{com}}(lab_{num})(b_i) = lab_{num}(b_i) = 1 \\ \frac{1}{2} & \text{otherwise} \end{cases}
$$
*(p.10)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Argument value | \|\|a\|\| | - | - | {0,1} for PL2; {0,1/2,1} for PL3; [0,1] for fuzzy | 5 | Truth value assigned to argument a |
| Negation (standard) | N(x) | - | 1-x | [0,1]->[0,1] | 6 | Standard negation: N(x) = 1-x |
| Godel t-norm | T_G(x,y) | - | min{x,y} | [0,1] | 6 | Minimum conjunction |
| Lukasiewicz t-norm | T_L(x,y) | - | max{0,x+y-1} | [0,1] | 6 | Bounded sum conjunction |
| Product t-norm | T_P(x,y) | - | x*y | [0,1] | 6 | Multiplicative conjunction |
| Kleene implication | =>^K | - | - | {0,1/2,1} | 5 | Table 1 |
| Lukasiewicz implication | =>^L | - | - | {0,1/2,1} | 5 | Table 2 |

## Implementation Details
- The encoding ec1 is simpler than ec2 but suffices for both stable (via PL3^K) and complete (via PL3^L) semantics *(p.14)*
- For computational implementation, the choice of PLS determines which semantics you compute: switching logic systems gives different semantics from the same formula *(p.14)*
- The ternarization function T_com converts any numerical labelling into a complete labelling; this is how fuzzy models connect back to classical semantics *(p.10)*
- A model of ec2(AF) in PL3^L may NOT be a model under complete semantics (Example 1, p.16), but its ternarization always is *(p.17)*
- The encoded equational function h^{ec1} always satisfies decreasing monotonicity (Theorem 8), which Gabbay's real equational functions do not necessarily satisfy *(p.19-20)*
- Eq^R_geometrical cannot be derived from any PL*[0,1] encoding (Example 2, p.22-23) because the induced operation is not a t-norm *(p.23)*

## Figures of Interest
- **Table 1 (p.6):** Truth-value table for Kleene implication =>^K in PL3^K
- **Table 2 (p.6):** Truth-value table for Lukasiewicz implication =>^L in PL3^L

## Results Summary
The paper establishes a systematic correspondence table: *(p.29-30)*
- Stable semantics <=> ec1 + PL3^K (Theorem 1)
- Complete semantics <=> ec1 + PL3^L (Theorem 2)
- Complete semantics => ec2 + PL3^K (Theorem 3-4, via T2 and T_com)
- Complete semantics <=> ec2 + PL3^L (Theorem 5-6, via T_com)
- Eq^R_max <=> ec1 + PL^G[0,1] (Theorem 13)
- Eq^R_inverse <=> ec1 + PL^P[0,1] (Theorem 14)
- Eq^L <=> ec1 + PL^L[0,1] (Theorem 15, NEW)
- Complete semantics <=> Eq^{ec1} with 1/2-idempotent zero-divisor-free t-norm (Corollary 10)

## Limitations
- Only finitary AFs are considered (each argument has finitely many attackers) *(p.3)*
- Only the normal encoding ec1 is used for fuzzy extensions; ec2 is not explored in the fuzzy domain *(p.18)*
- The paper does not address weighted AFs or bipolar AFs *(p.30)*
- No computational complexity analysis of model checking in the different PLSs *(p.30)*
- Eq^R_geometrical is shown NOT to be derivable from any PL*[0,1] encoding, indicating limits of the approach *(p.22-23)*

## Arguments Against Prior Work
- Besnard and Doutre's model checking approach [29] only handled PL2, limiting it to stable and complete semantics in the 2-valued case *(p.2)*
- Gabbay's real equational approach [12] does not require decreasing monotonicity, which the authors argue is an essential property for argumentation semantics (value of argument should decrease as attacker values increase) *(p.19)*
- Prior encoding work [29, 30] only gave encodings for specific semantics without a general methodology unifying them *(p.2)*

## Design Rationale
- ec1 is preferred over ec2 because it is simpler and, with the right PLS, already captures complete semantics *(p.14)*
- The choice of t-norm determines which equational semantics emerges: Godel gives Eq^R_max, Product gives Eq^R_inverse, Lukasiewicz gives the new Eq^L *(p.23-26)*
- Decreasing monotonicity is introduced as a desirable property because it captures the intuition that an argument's value should decrease as its attackers' values increase *(p.19)*

## Testable Properties
- For ec1+PL3^K: model set equals stable extensions (Theorem 1) *(p.12)*
- For ec1+PL3^L: model set equals complete extensions (Theorem 2) *(p.13)*
- h^{ec1} is symmetric in its arguments (Theorem 9c) *(p.20)*
- h^{ec1}(0,...,0) = 1 and h^{ec1}(x1,...,1,...,xk) = 0 (Theorem 9a,b) *(p.20)*
- h^{ec1} is non-increasing in each variable (Theorem 8) *(p.19)*
- Under Eq^L: if sum of attacker values >= 1 then argument value = 0 *(p.25)*
- Under Eq^L: if sum of attacker values < 1 then argument value = 1 - sum *(p.25)*
- Every continuous encoded equational system is a Gabbay real equational system (Theorem 12) *(p.21)*

## Relevance to Project
Directly relevant to the propstore's argumentation framework implementation. The paper provides:
1. Alternative computational methods for AF semantics via propositional logic model checking
2. A theoretical foundation for extending beyond classical {in, out, undecided} to graded/fuzzy acceptance values
3. The new Eq^L semantics could be useful for representing partial/graded acceptance of arguments
4. Connections between Gabbay's equational approach and standard logic systems, which may inform implementation choices

## Open Questions
- [ ] How does Eq^L compare empirically to Eq^G and Eq^P on real argumentation problems?
- [ ] Can ec2 be extended to fuzzy logics to capture additional semantics?
- [ ] What is the computational complexity of model checking ec1(AF) in PL^L[0,1]?
- [ ] Can the encoding methodology be extended to bipolar or weighted AFs?

## Related Work Worth Reading
- [12] Gabbay, D. M.: Equational approach to argumentation networks. Argum. & Comput. 3(2-3), 87-142 (2012) - foundational equational semantics
- [29] Besnard, P., Doutre, S.: Checking the acceptability of a set of arguments. NMR, pp. 59-64 (2004) - original model checking approach
- [30] Besnard, P., Doutre, S., Herzig, A.: Encoding argument graphs to logic. ISMIS, pp. 345-354 (2014) - extended encoding
- [11] Gabbay, D. M.: Introducing equational semantics for argumentation networks. ECSQARU, pp. 19-35 (2011)
- [48] Baroni, P., Caminada, M. W. A., Giacomin, U.: An introduction to argumentation semantics. Knowledge Engineering Review 26(4), 365-410 (2011) - survey of AF semantics

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as [1], the foundational paper defining all the argumentation framework semantics (stable, complete, preferred, grounded, admissible) that this paper encodes into propositional logic systems
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — cited as [6], extends Dung's framework with support relations; Tang's conclusion mentions extending the encoding methodology to bipolar AFs as future work

### New Leads (Not Yet in Collection)
- Gabbay (2012) — "Equational approach to argumentation networks" Argum. & Comput. 3(2-3), 87-142 — cited as [12], foundational for the equational semantics (Eq^R_max, Eq^R_inverse) that Tang proves correspond to Godel and Product fuzzy logic encodings
- Besnard & Doutre (2004) — "Checking the acceptability of a set of arguments" NMR pp. 59-64 — cited as [29], the original model checking approach encoding AFs as PL2 formulas that Tang generalizes to PL3 and PL[0,1]
- Baroni, Caminada & Giacomin (2011) — "An introduction to argumentation semantics" Knowledge Engineering Review 26(4), 365-410 — cited as [48], comprehensive survey of labelling-based semantics used throughout Tang's paper

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Mahmood_2025_Structure-AwareEncodingsArgumentationProperties]] — **Strong.** Both papers encode Dung's AF semantics into propositional logic formulas, starting from the same Besnard-Doutre baseline. Mahmood focuses on structure-aware SAT encodings that preserve clique-width for computational efficiency; Tang focuses on generalizing the encoding to multi-valued and fuzzy logics to establish semantic correspondences. They are complementary: Tang shows WHAT semantics different logics capture; Mahmood shows HOW to compute those semantics efficiently.
- [[Niskanen_2020_ToksiaEfficientAbstractArgumentation]] — **Strong.** mu-toksia uses SAT-based encodings of AF semantics (the computational implementation side of the same encoding approach). Tang's work provides the theoretical foundation showing that switching the underlying logic system yields different semantics from the same formula, which could inform choices of SAT encoding strategy.
- [[Dung_1995_AcceptabilityArguments]] — **Strong.** Tang's entire paper is about encoding Dung's semantics into logic systems. The key theoretical result is that Dung's stable semantics = ec1 + Kleene PL3, and Dung's complete semantics = ec1 + Lukasiewicz PL3 --- providing a precise logical characterization of Dung's abstract definitions.
