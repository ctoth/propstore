---
title: "The Dynamic of Belief in the Transferable Belief Model and Specialization-Generalization Matrices"
authors: "Frank Klawonn, Philippe Smets"
year: 1992
venue: "Proceedings of the Eighth Conference on Uncertainty in Artificial Intelligence (UAI-92), pp. 130-137"
doi_url: "https://doi.org/10.1016/B978-1-4832-8287-9.50022-0"
pages: "130-137"
note: "Directory name uses 2013, the arXiv posting year (arXiv:1303.5408); the paper was published at UAI 1992. Page citations below use the printed proceedings page numbers 130-137 (PDF pages 1-8)."
---

# The Dynamic of Belief in the Transferable Belief Model and Specialization-Generalization Matrices

## One-Sentence Summary
Models every belief expansion in the Transferable Belief Model (TBM) as a column-stochastic "specialization matrix" that moves basic belief mass from each set to its subsets, and proves (i) unnormalized Dempster conditioning is the least committed specialization that zeroes plausibility of the excluded set, and (ii) the Dempsterian specialization matrices (those that implement unnormalized Dempster combination) are exactly the largest commuting family that contains the conditioning matrices; the disjunctive dual uses "generalization" matrices. *(p.130, p.133-136)*

## Problem Addressed
Dempster's rules of conditioning and combination have been criticised (Levi 1983, Kyburg 1987, Pearl 1990, Voorbraacht 1991), mostly by reading Dempster-Shafer theory as upper/lower probability. The TBM is built without probability so those criticisms do not apply, but there remains the question of *why* the two Dempster rules should be used. This paper supplies that justification from non-probabilistic requirements: minimal commitment and commutativity of expansions. *(p.130)*

## Key Contributions
- Formal notion of an evidential corpus (EC), equivalence of corpora, compatibility, vacuous evidence, and distinctness of evidence. *(p.132)*
- Definition of a specialization matrix S with coefficients s(A,B) giving the proportion of m(A) that flows to B subset of A; specialization m = m0·S. *(p.132-133)*
- Construction of the C-conditioning specialization matrix S_C and of the Dempsterian specialization matrix S_m that implements m' ⊕ m. *(p.133)*
- Theorem 1: unnormalized Dempster conditioning is the least committed specialization making pl'(C̄)=0. *(p.133-134)*
- Lemma 1: conditioning specialization matrices are idempotent. *(p.134)*
- Theorem 2: any specialization matrix commuting with every conditioning matrix is Dempsterian. Theorem 3: Dempsterian matrices commute. Together: Σ_D is the largest commuting family containing Σ_cond. *(p.134)*
- Spectral note: S_m = T Λ T^{-1} with eigenvalues the commonalities q(A). *(p.134-135)*
- Theorem 4: among all specializations that never yield something less committed than m0, S_{m0} gives the least committed result — a second minimal-commitment characterization of Dempster's combination. *(p.135)*
- Extension to contraction (de-specialization = matrix inverse) and to disjunctive combination via generalization matrices; a table of dual relations. *(p.135-136)*

## Methodology
Axiomatic/algebraic. Belief states are bba vectors over 2^Ω; updates are linear operators (matrices) indexed by pairs of subsets. Properties (least commitment, commutativity) are imposed on the operator set and the Dempster rules are derived as unique/optimal solutions. Proofs are direct sum manipulations. *(p.132-135)*

## Background Definitions (TBM) *(p.130-131)*
- Ω: finite frame of discernment; at most one element is the actual state of affairs. *(p.130-131)*
- A unitary amount of belief is distributed over subsets of Ω. m(A), the basic belief mass (bbm), is the part of belief supporting A and not any strict subset of A, "due to lack of information". *(p.131)*
- No normalization: m(∅) may be positive and bel(Ω), pl(Ω) may be less than one (Smets 1992). The conclusions still apply when normalization is introduced. *(p.131)*
- Vacuous belief function: bel(A)=0 for all A≠Ω, bel(Ω)=1; vacuous bba m(Ω)=1; vacuous plausibility pl(A)=1 for all A≠∅. Represents total ignorance. *(p.131)*
- bba, bel, pl and q are in one-to-one correspondence (Shafer 1976). *(p.131)*

$$
\sum_{A \subseteq \Omega} m(A) = 1
$$
Where m: 2^Ω → [0,1] is the basic belief assignment (bba), m(A) ≥ 0. *(p.131)*

$$
bel(A) = \sum_{\emptyset \neq X \subseteq A} m(X)
$$
Where bel(A) is the degree of belief; ∅ excluded. *(p.131)*

$$
pl(A) = bel(\Omega) - bel(\bar{A}) = \sum_{X \cap A \neq \emptyset} m(X)
$$
Where pl(A) is the degree of plausibility, the maximal belief that might support A. *(p.131)*

$$
q(A) = \sum_{A \subseteq B} m(B)
$$
Where q: 2^Ω → [0,1] is the commonality function; "no practical interpretation" but useful for Dempster combination. *(p.131)*

## Principle of Minimal Commitment *(p.131-132)*
- Motivating example: Ω={a,b,c}; You know only bel_Me({a})=.3 and bel_Me({b,c})=.5. Applying "no more support than justified" gives m_You({a})=.3, m_You({b,c})=.5, m_You({a,b,c})=.2; this is the belief function giving the smallest degree of belief to every subset among those compatible with the constraints. *(p.131)*
- Degrees of belief are degrees of "justified" support; the principle is "at the core of the TBM". *(p.131)*
- Definition with unnormalized belief functions is based on plausibility: if pl1(A) ≤ pl2(A) for all A, pl2 is "not more committed" than pl1 (less committed if at least one strict inequality). Extended to bba and bel. The least committed belief function on Ω is the vacuous one. *(p.131)*

$$
pl_1(A) \le pl_2(A) \quad \forall A \subseteq \Omega
$$
*(p.131)*

$$
bel_1(A) + m_1(\emptyset) \ge bel_2(A) + m_2(\emptyset) \quad \forall A \subseteq \Omega
$$
Where this is the same ordering expressed with belief functions (pl1 more committed than pl2). *(p.131)*

- Partial order ⊑ on belief functions (Yager 1986, Dubois and Prade 1986): pl1 ⊑ pl2 means pl1 equals or is more committed than pl2; same notation for m and bel. *(p.131)*
- The principle: select the least committed belief function in a set of equally justified ones; a form of skepticism / uncommitment / conservatism, close in spirit to maximum entropy (Dubois and Prade 1987, Hsia 1991, Smets 1991c). *(p.131-132)*

## Evidential Corpus and Expansion *(p.132)*
- EC: the set of all Your evidence at a given time (cf. Levi 1980). *(p.132)*
- EC1 and EC2 equivalent (relative to Ω) iff for every piece of evidence E, EC1∪E and EC2∪E induce the same bba on Ω. *(p.132)*
- E compatible with EC iff EC∪E ⊭ ⊥. *(p.132)*
- E vacuous (relative to Ω) iff EC and EC∪E are equivalent for every EC; a tautology is a typical vacuous evidence. *(p.132)*
- Expansion: adding to EC an evidence compatible with EC (Gardenfors 1988), i.e. adding a belief without retracting old ones. Represented in the TBM by two rules: Dempster's rule of conditioning and Dempster's rule of combination. *(p.130, p.132)*
- E distinct from EC iff there is no non-vacuous evidence F with E ⊨ F and EC ⊨ F; otherwise F would be shared evidence and the beliefs would result from common underlying evidence. *(p.132)*

### Unnormalized Dempster conditioning *(p.132)*
Learning all elements of Ā are impossible transfers m(X) to X∩A.

$$
m_A(B) = \sum_{\emptyset \neq Y \subseteq \bar{A}} m(B \cup Y) \quad \text{for } B \subseteq A, \; 0 \text{ otherwise}
$$
*(p.132)* (As printed the sum index excludes Y=∅; read literally this omits m(B) itself. Since conditioning must keep m(B) for B ⊆ A, the intended range is presumably Y ⊆ Ā including ∅ — flagged as a likely typesetting slip, not verified against another source.)

$$
bel_A(B) = bel(B \cup \bar{A}) - bel(\bar{A}) \quad \text{for } B \subseteq \Omega
$$
*(p.132)*

### Dempster's rule of combination (unnormalized) *(p.132)*
For E distinct from EC, m0 induced by EC, m1 by E; m01 induced by EC∪E (Shafer 1976).

$$
m_{01} = m_0 \oplus m_1
$$
*(p.132)*

$$
m_{01}(A) = \sum_{Y \cap Z = \emptyset,\; Y, Z \subseteq \bar{A}} m_0(A \cup Y)\, m_1(A \cup Z) \quad \forall A \subseteq \Omega
$$
*(p.132)*

$$
q_{01}(A) = q_0(A)\, q_1(A) \quad \forall A \subseteq \Omega
$$
*(p.132)*

- Prior justifications: Nguyen and Smets (1991) show Bel(A|B) is the minimal commitment solution for the belief of the conditional object A|B (Goodman, Nguyen et al. 1991; Goodman, Gupta et al. 1991). For combination: Smets (1990), Klawonn and Schwecke (1990), Dubois and Prade (1986), Hajek (1992) give algebraic requirement sets. This paper adds a justification from commutative specialization. *(p.132)*

## Specialization Matrices *(p.132-133)*
- New evidence E added to EC redistributes the initial m0: the bbm m(A) is distributed among subsets of A. s(A,B) ∈ [0,1] is the proportion of m(A) flowing into B ⊆ A. *(p.132)*

$$
\sum_{B \subseteq A} s(A,B) = 1 \quad \forall A \subseteq \Omega
$$
*(p.132)*

- s(A,B)=0 for all B ⊄ A. The matrix S of coefficients s(A,B), A,B ⊆ Ω, is a specialization matrix (Yager 1986, Dubois and Prade 1986, Kruse and Schwecke 1990, Moral 1985, Delgado and Moral 1987). *(p.132-133)*

$$
m(A) = \sum_{X \subseteq \Omega} s(X,A)\, m_0(X)
$$
Where m = m0·S is the specialization of m0 by S. *(p.133)*

- Any specialization of m0 is at least as committed as m0 (Yager 1986): m0·S ⊑ m0 for every bba m0 and every specialization matrix S. *(p.133)*
- Σ: set of specialization matrices on Ω. *(p.133)*

### C-conditioning matrix *(p.133)*

$$
s_C(A,B) = 1 \text{ if } B = A \cap C, \; 0 \text{ otherwise}
$$
Where m_C = m·S_C is m conditioned on C by Dempster's rule. Σ_cond ⊆ Σ is the set of C-conditioning matrices, C ⊆ Ω. *(p.133)*

### Dempsterian specialization matrix *(p.133)*

$$
s_m(A,B) = m_A(B) \quad \forall A, B \subseteq \Omega
$$
Where m_A is m conditioned on A by Dempster's rule of conditioning. *(p.133)*

$$
s_m(\Omega, B) = m(B) \quad \forall B \subseteq \Omega
$$
*(p.133)*

$$
s_m(A,B) = \sum_{X \subseteq \bar{A}} s_m(\Omega, B \cup X) \quad \forall B \subseteq A, \; 0 \text{ otherwise}
$$
*(p.133)*

- For a bba m': m' ⊕ m = m'·S_m. Commutativity of m'·S_m is not obvious but holds: m'·S_m = m·S_{m'}. S_m is the Dempsterian specialization matrix associated with m; Σ_D ⊆ Σ is the set of Dempsterian matrices. *(p.133)*
- If m(C)=1 (bba corresponding to conditioning on C) then S_C = S_m, so Σ_cond ⊆ Σ_D. *(p.133)*
- Design claim: expansion by specialization is "one of the fundamental ideas" of the dynamic TBM; m(X) is belief supporting X and no strict subset that can be transferred to subsets if further information justifies it; "therefore we can accept that every expansion is defined by a specialization matrix". *(p.133)*

## Main Results *(p.133-135)*

### Theorem 1 (Dempster's rule of conditioning) *(p.133-134)*
Let C ⊆ Ω and Σ* = {S ∈ Σ | ∀m: if m' = m·S then pl'(C̄) = 0}. Let S_C be the C-conditioning matrix (s_C(A,B)=1 if B=A∩C, else 0). Then S_C ∈ Σ* and m·S_C is the least committed bba among m·S for S ∈ Σ*:

$$
m \cdot S_C \sqsubseteq m \cdot S \quad \forall S \in \Sigma^*
$$
*(p.133)* (As printed the relation is "m·S_C ⊑ m·S"; given ⊑ means "equal or more committed", the proof's conclusion pl_C(D) ≥ pl'(D) actually shows m·S ⊑ m·S_C, i.e. m·S_C least committed, matching the theorem's prose.)

Proof sketch: 0 = pl'(C̄) = Σ_{B∩C̄≠∅} Σ_{B⊆A} m(A)s(A,B) for all m, so s(A,B)=0 whenever B ⊄ C. Then pl'(D) = Σ_{A∩D∩C≠∅} m(A) Σ_{B⊆A∩C, B∩D≠∅} s(A,B) ≤ Σ_{A∩D∩C≠∅} m(A) = pl_C(D). Hence pl_C(D) ≥ pl'(D) for all D, so pl_C is least committed. *(p.134)*

### Lemma 1 *(p.134)*
The specialization matrices S ∈ Σ_cond are idempotent (since Dempster conditioning is idempotent). *(p.134)*

### Theorem 2 (Dempster's rule of combination) *(p.134)*
Let S1 ∈ Σ such that for all C ⊆ Ω: S1·S_C = S_C·S1 with S_C ∈ Σ_cond. Then S1 ∈ Σ_D.

Proof: s_{1,C}(A,B) = Σ_D s1(A,D) s_C(D,B) = Σ_{X⊆C̄∩A} s1(A,B∪X) if B ⊆ C, else 0. s_{C,1}(A,B) = Σ_D s_C(A,D) s1(D,B) = s1(A∩C,B). Equating: s1(A∩C,B) = Σ_{X⊆C̄∩A} s1(A,B∪X) if B⊆C, else 0. Setting A=Ω gives s1(C,B) = Σ_{X⊆C̄} s1(Ω,B∪X) if B⊆C, else 0 — the Dempsterian form with m = s1(Ω,·). *(p.134)*

### Theorem 3 *(p.134)*
If S_{m1}, S_{m2} ∈ Σ_D then S_{m1}·S_{m2} = S_{m2}·S_{m1}. Proof by associativity and commutativity of ⊕: m0·S_{m1}·S_{m2} = m0⊕m1⊕m2 = m0⊕m2⊕m1 = m0·S_{m2}·S_{m1}. *(p.134)*

Consequence (stated p.134): Σ_D is the largest set of specialization matrices that commute among themselves and include Σ_cond.

### Spectral note *(p.134-135)*
T transforms a bba into its commonality function:

$$
t_{A,B} = 1 \text{ if } B \subseteq A \subseteq \Omega, \; 0 \text{ otherwise}
$$
*(p.134)*

- Claims (stated "it can be shown", no proof given): (1) commonalities q(A), A ⊆ Ω, are the diagonal elements and the eigenvalues of S_m; (2) the lines (rows) of T^{-1} are the eigenvectors of S_m (row eigenvector t: tS = λt). *(p.134)*

$$
S_m = T \Lambda T^{-1}
$$
Where Λ is diagonal with λ_{A,A} = q(A). Useful when m(Ω)=0, where generalized inverses can help. *(p.135)*

### Theorem 4 (second characterization of combination) *(p.135)*
Setting: My EC induces m0; I want S to combine any new evidence distinct from EC, i.e. specialize any new m. Let

$$
\Sigma_0 = \{ S \in \Sigma \mid \forall m : m \cdot S \sqsubseteq m_0 \}
$$
*(p.135)*

Then S_{m0} ∈ Σ_0 and for all S ∈ Σ_0 and all m: m·S ⊑ m·S_{m0}. I.e. Dempster combination gives the least committed result among operators guaranteed to be at least as committed as m0. *(p.135)*

Proof sketch: S_{m0} ∈ Σ_0 since m·S_{m0} = m⊕m0 ⊑ m0. For S ∈ Σ_0, define m_S^(A)(B) = s(A,B) with plausibility pl_S^(A). With m(A)=1, m·S = m_S^(A) ⊑ m0, so m_S^(A) = m_S^(A)(·|A) ⊑ m0(·|A) = m_{S0}^(A) (*). For arbitrary m, pl'(A) = Σ_{C∩A≠∅} m(C) pl_S^(C)(A) ≤ Σ_{C∩A≠∅} m(C) pl_{S0}^(C)(A) = pl''(A), where pl'' is the plausibility of m0·S0 (as printed; context implies m·S0). *(p.135)*

## Contraction and Disjunctive Combination *(p.135-136)*
- Contraction: eliminating a belief from EC. Specialization matrices are replaced by de-specialization matrices, the matrix inverses of specialization matrices. Unlike specializations, they must not be applied to any bba, only to a subset of bbas that depends on the matrix: one cannot eliminate evidence that was never added. *(p.135)*
- Retraction as special conjunctive combination: from EC containing only distinct E and F, eliminating E means adding "eliminate E"; compute bel_F from bel_{E and F} and bel_E; easy with commonalities: *(p.135)*

$$
q_F(A) = \frac{q_{E \wedge F}(A)}{q_E(A)} \quad \forall A \subseteq \Omega
$$
*(p.135)*

- Disjunctive combination (Smets 1991c): with vacuous ECo and known bel_E, bel_F, You can add only "E or F". The product m_E(A) m_F(B) is transferred to A∪B in m_{E or F}, and *(p.135)*

$$
bel_{E \vee F}(A) = bel_E(A)\, bel_F(A) \quad \forall A \subseteq \Omega
$$
*(p.135)*

- Generalization matrix G: dual of specialization; stochastic matrix with g(A,B)=0 for all A ⊄ B ⊆ Ω; bbm m(A) is distributed among supersets of A. *(p.135)*
- Enlargement: dual of conditioning. If m' is the enlargement on A of m, then conditioning m' on any X∪Y with X ⊆ Ā and Y ⊆ A gives the same result whatever Y ⊆ A; elements of A become "indiscernible" (no subset of A gets support not given to the whole A). *(p.135-136)*

### Table of dual relations *(p.136)*

| Evidence combination | Conjunctive | Disjunctive |
|---|---|---|
| from bel_E and bel_F | bel_{E and F} | bel_{E or F} |
| expansion matrices | specialization | generalization |
| retraction matrices | de-specialization | de-generalization |
| single fact | conditioning / de-conditioning | enlargement / de-enlargement |
| combination | conjunctive rule | disjunctive rule |

- Dual and inverse relations are in one-to-one correspondence: to any de-specialization matrix corresponds a generalization matrix and vice versa, so there are two processes, not four; which to use depends on context. *(p.136)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Example bel_Me({a}) | bel_Me({a}) | - | 0.3 | - | 131 | Minimal commitment example, Ω={a,b,c} |
| Example bel_Me({b,c}) | bel_Me({b,c}) | - | 0.5 | - | 131 | Same example |
| Resulting m_You({a}) | m_You({a}) | - | 0.3 | - | 131 | Least committed solution |
| Resulting m_You({b,c}) | m_You({b,c}) | - | 0.5 | - | 131 | Least committed solution |
| Resulting m_You(Ω) | m_You({a,b,c}) | - | 0.2 | - | 131 | Residual mass to Ω |
| Specialization coefficient | s(A,B) | - | - | 0-1 | 132 | Rows sum to 1; zero unless B ⊆ A |
| Generalization coefficient | g(A,B) | - | - | 0-1 | 135 | Stochastic; zero unless A ⊆ B |

## Methods & Implementation Details
- Represent a bba as a vector of length 2^|Ω| indexed by subsets; a specialization is a 2^|Ω| × 2^|Ω| row-stochastic matrix with support only on B ⊆ A; update is row-vector times matrix: m = m0·S. *(p.132-133)*
- Conditioning on C: S_C maps each A deterministically to A∩C (possibly ∅, since unnormalized). *(p.133)*
- Combination with m: build S_m row by row: row A is m conditioned on A, i.e. s_m(A,B) = Σ_{X⊆Ā} m(B∪X) for B ⊆ A. Then m'⊕m = m'·S_m. *(p.133)*
- Commonality transform T (t_{A,B}=1 iff B ⊆ A) diagonalizes S_m with eigenvalues q(A); combination is pointwise product in commonality space, so retraction is pointwise division (when q_E(A) ≠ 0). *(p.132, p.134-135)*
- De-specialization (inverse) is only valid on bbas that are in the image of the corresponding specialization. *(p.135)*

## Figures of Interest
- **Table (p.136):** dual relations between conjunctive/specialization and disjunctive/generalization processes.

## Results Summary
Under three assumptions — (1) expansion of EC by E maps prior m0 to a posterior that is a specialization of m0; (2) if E says Ā is impossible then pl1(Ā)=0 and the least committed such specialization is Dempster conditioning; (3) results of expanding by two pieces of evidence are independent of order, so expansion matrices including conditioning ones commute — the only commuting specialization family yields Dempster's rule of combination. *(p.136)*

## Limitations
- Restricted to finite frames Ω. *(p.130)*
- Distinctness of evidence is assumed for combination; no treatment of overlapping/shared evidence beyond the definition. *(p.132)*
- Contraction/de-specialization is only sketched; domain of applicability of inverse matrices is not characterized. *(p.135)*
- Spectral claims (eigenvalues = commonalities, eigenvectors = rows of T^{-1}) are stated without proof; singular case m(Ω)=0 deferred to generalized inverses. *(p.134-135)*
- Disjunctive results are cited from Smets 1991c, not proved here. *(p.135)*

## Arguments Against Prior Work
- Most criticisms of Dempster's rules (Levi 1983, Kyburg 1987, Pearl 1990, Voorbraacht 1991) arise from reading Dempster-Shafer theory as upper/lower probability; the TBM uses no probability concept, so they do not apply. *(p.130)*
- Even so, prior work had not explained why the rules should be used; earlier justifications were algebraic requirement sets (Smets 1990, Klawonn and Schwecke 1990, Dubois and Prade 1986, Hajek 1992) or conditional-object minimal commitment (Nguyen and Smets 1991). *(p.130, p.132)*

## Design Rationale
- Masses only flow to subsets on expansion because m(X) is uncommitted support for X that further information can refine; hence every expansion is a specialization. *(p.133)*
- Commutativity is required because expansion by two pieces of evidence should not depend on order; classically required for any expansion operator (Gardenfors 1988). *(p.133)*
- Least commitment (never more support than justified) selects among equally justified updates; analogous to maximum entropy. *(p.131-132)*
- No normalization: m(∅) > 0 allowed; results also hold with normalization. *(p.131)*

## Testable Properties
- For any bba m0 and specialization S, m0·S ⊑ m0 (pl does not increase). *(p.133)*
- Each row of a specialization matrix sums to 1 and s(A,B)=0 for B ⊄ A. *(p.132)*
- m'⊕m = m'·S_m = m·S_{m'}. *(p.133)*
- If m(C)=1 then S_m = S_C. *(p.133)*
- After m·S_C, pl(C̄)=0, and for any S with that property and every D, pl_{m·S}(D) ≤ pl_{m·S_C}(D). *(p.133-134)*
- S_C·S_C = S_C (idempotence). *(p.134)*
- Any S commuting with every S_C equals S_m with m = s(Ω,·). *(p.134)*
- S_{m1} S_{m2} = S_{m2} S_{m1}. *(p.134)*
- diag(S_m) = q and S_m = T diag(q) T^{-1}. *(p.134-135)*
- q_{01} = q_0 q_1 pointwise; q_F = q_{E∧F}/q_E. *(p.132, p.135)*
- bel_{E∨F}(A) = bel_E(A)·bel_F(A). *(p.135)*
- For S with m·S ⊑ m0 for all m, m·S ⊑ m·S_{m0}. *(p.135)*

## Relevance to Project
propstore stores rival evidence without collapsing it and resolves at render time with subjective-logic/belief-function machinery. This paper gives a principled reason for using unnormalized Dempster conditioning and conjunctive combination as the default expansion operators: they are the least committed and the only order-independent specializations. Order independence matters directly for a lazy store where evidence arrives in arbitrary order. The commonality-space view gives a simple implementation (pointwise product) and a clean retraction (pointwise division), relevant to removing a source's contribution without recomputing. The unnormalized m(∅) aligns with the honest-ignorance discipline already grounded in Smets 1992 (`Smets_1992_NatureUnnormalizedBeliefsEncountered`). The conjunctive/disjunctive duality matches the choice between combining distinct reliable sources (conjunctive) and "at least one source is right" (disjunctive).

## Open Questions
- [ ] Exact range of Y in the printed m_A(B) formula (p.132) — the ∅≠Y restriction looks like a typo.
- [ ] Direction of ⊑ in the displayed conclusion of Theorem 1 (p.133) vs. its proof (p.134).
- [ ] Characterization of the admissible domain of de-specialization matrices (p.135).

## Related Work Worth Reading
- Smets 1990, "The combination of evidence in the transferable belief model", IEEE PAMI 12:447-458 (already in collection as `Smets_1990_CombinationEvidenceTransferableBelief`).
- Smets 1992, "The nature of the unnormalized beliefs encountered in the transferable belief model" (in collection as `Smets_1992_NatureUnnormalizedBeliefsEncountered`).
- Smets 1991c, "Belief functions: the disjunctive rule of combination and the generalized Bayesian theorem" (later published 1993; collection has `Smets_1993_BeliefFunctionsDisjunctiveRule`).
- Yager 1986, "The entailment principle for Dempster-Shafer granules".
- Dubois and Prade 1986, "A set theoretical view of belief functions".
- Kruse and Schwecke 1990, "Specialization: a new concept for uncertainty handling with belief functions".
- Gardenfors 1988, Knowledge in Flux.
- Klawonn and Schwecke 1990, "On the axiomatic justification of Dempster's rule of combination".

## Collection Cross-References

### Already in Collection
- [A Mathematical Theory of Evidence](../Shafer_1976_MathematicalTheoryEvidence/notes.md) - cited for the one-to-one correspondence of bba, bel, pl and q and for combining distinct evidential corpora *(p.131-132)*
- [The Combination of Evidence in the Transferable Belief Model](../Smets_1990_CombinationEvidenceTransferableBelief/notes.md) - cited as an earlier algebraic requirement-set justification of Dempster's rule, which this paper replaces with least commitment plus commutativity *(p.130, p.132)*
- [The Nature of the Unnormalized Beliefs Encountered in the Transferable Belief Model](../Smets_1992_NatureUnnormalizedBeliefsEncountered/notes.md) - same UAI-92 volume; cited for working without normalization (m(empty) > 0 allowed) *(p.131)*
- [Belief Functions: The Disjunctive Rule of Combination and the Generalized Bayesian Theorem](../Smets_1993_BeliefFunctionsDisjunctiveRule/notes.md) - the 1993 journal version of the cited Smets 1991c technical report; source of the disjunctive-combination results used for generalization matrices *(p.135)*
- [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) - the 1994 journal version of the cited Smets and Kennes 1990 technical report, named as where the TBM was developed *(p.130)*

### New Leads (Not Yet in Collection)
- Kruse and Schwecke (1990) - "Specialization: a new concept for uncertainty handling with belief functions" - origin of specialization for belief functions
- Klawonn and Schwecke (1990) - "On the axiomatic justification of Dempster's rule of combination" - companion axiomatic justification
- Yager (1986) - "The entailment principle for Dempster-Shafer granules" - specializations are at least as committed
- Gardenfors (1988) - "Knowledge in Flux" - the expansion/contraction framework whose commutativity requirement this paper adopts
- Dubois and Prade (1986) - "A set theoretical view of belief functions" - earlier algebraic justification
- Nguyen and Smets (1991) - "On Dynamics of Cautious Belief and Conditional Objects" - conditional-object minimal-commitment derivation of conditioning
- Hsia (1991) - "Characterizing Belief with Minimum Commitment"
- Pearl (1990) - "Reasoning with Belief Functions: an Analysis of Compatibility" - one of the criticisms the TBM sidesteps

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [The Nature of the Unnormalized Beliefs Encountered in the Transferable Belief Model](../Smets_1992_NatureUnnormalizedBeliefsEncountered/notes.md) - cites this for the algebraic conditioning derivation (Smets 1992 p.295)
- [Belief Functions: The Disjunctive Rule of Combination and the Generalized Bayesian Theorem](../Smets_1993_BeliefFunctionsDisjunctiveRule/notes.md) - cites this as ref [20] for minimal-commitment specialization-generalization
- [Quantifying Beliefs by Belief Functions: An Axiomatic Justification](../Smets_1993_QuantifyingBeliefsBeliefFunctions/notes.md) - lists this as TBM dynamics via specialization-generalization matrices
- [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) - cites this as ref [20]

### Conceptual Links (not citation-based)
- [The Geometry of Uncertainty: The Geometry of Imprecise Probabilities](../Cuzzolin_2021_GeometryUncertaintyGeometryImprecise/notes.md) - Moderate. Cuzzolin's reasoning chapter (chapters/chapter-03-reasoning.md) surveys the nested family of belief-function conditioning operators and quotes the result that "Dempster's rule of conditioning corresponds essentially to the least committed specialisation, whereas Dempster's rule of combination results from commutativity requirements" (attributed there to Klawonn-Schwecke, refs [974, 975]); that is this paper's abstract-level claim. Whether ref [975] is this paper could not be checked from the chapter notes.
