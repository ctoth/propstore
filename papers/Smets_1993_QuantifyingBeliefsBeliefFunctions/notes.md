---
title: "Quantifying Beliefs by Belief Functions: An Axiomatic Justification"
authors: "Philippe Smets"
year: 1993
venue: "International Joint Conference on Artificial Intelligence (IJCAI-93), Vol. 1, pp. 598-603"
affiliation: "IRIDIA, Universite Libre de Bruxelles, 50 av. Roosevelt, CP 194-6, B-1050 Brussels, Belgium"
doi_url: null
url: "https://www.ijcai.org/Proceedings/93-1/Papers/084.pdf"
pages: "598-603"
note: "Short version of IRIDIA technical report Smets (1992b). Full proofs and discussion in the longer report."
produced_by:
  agent: "claude-opus-4.7-1m"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-28T07:25:41Z"
---
# Quantifying Beliefs by Belief Functions: An Axiomatic Justification

## One-Sentence Summary
Smets presents an axiom system over a generic point-valued "credibility function" Cr that, when a closure axiom is added, forces Cr to be a Dempster-Shafer belief function — providing an axiomatic justification for the credal level of the Transferable Belief Model (TBM). *(p.598)*

## Problem Addressed
Many non-additive measures of belief have been proposed (belief, plausibility, possibility, necessity, lower/upper probability) but no axiomatic argument distinguishes among them. Smets asks: **what is the minimal set of intuitive properties on a generic "credibility" function that uniquely picks out belief functions** as the right structure for quantifying degrees of belief at the credal level (separated from the betting/decision level)? *(p.598)*

## Key Contributions
- A propositional/algebraic setup distinguishing **frame of discernment** Omega, **propositional space** (Omega, R) where R is a Boolean algebra of subsets, and **doxastic equivalence** relative to an evidential corpus EC^Y_t. *(p.598-599)*
- **Axiom A1** (equi-credibility of doxastically equivalent propositions). *(p.599)*
- **Axiom R1** (impact of uninformative refinement) and **Axiom R2** (factorization on irrelevant atoms). *(p.600)*
- A trichotomy theorem: from R1 + R2 the credibility function is forced into one of three forms — belief, plausibility, or possibility. *(p.601)*
- **Axioms M1, M2, M3** governing conditioning (Cr_A); derivation of two extremal solutions (minimal = unnormalized Dempster, maximal = its dual) plus a partially-renormalized intermediate, with theorems 3 and 4 nailing down structure. *(p.601-602)*
- **Closure axiom**: every credibility function on r+1 atoms can be obtained by refinement-conditioning-simplex-combinations from credibility functions on r atoms; closure forces B_r = E_r, i.e., **every credibility function is a belief function**. *(p.603)*
- Demonstration that probability functions cannot satisfy A1 and R1 simultaneously — i.e., probability theory is *incompatible* with the joint axiomatization for total ignorance, motivating the departure to belief functions. *(p.600)*
- Identification of unnormalized Dempster's rule of conditioning as the unique conditioning rule satisfying both **homomorphism** and **preservation** properties (probability-style revision). *(p.602)*

## Methodology
Pure axiomatic / representation-theorem methodology over finite Boolean algebras. Define a generic "credibility space" (Omega, R, Cr); accumulate axioms motivated by what beliefs should do under uninformative algebra changes (coarsening/refinement) and under conditioning on new evidence; show that the axioms force a specific algebraic form. Proofs are deferred to the technical report Smets (1992b).

## Setup and Notation *(p.598-599)*

- **Propositional language** L with finite generators {p_1, ..., p_n}, propositional connectives, and a model-theoretic truth assignment.
- **Worlds**: every truth assignment defines a world. Omega is the set of all worlds (frame of discernment).
- **Subsets of worlds**: for any proposition X, [[X]] subset Omega is the set of worlds in which X is true.
- For A subset Omega, f_A is any proposition such that [[f_A]] = A, so A = [[f_A]], empty = [[bottom]], Omega = [[top]].
- **Actual world** omega_bar in Omega; Cr(A) quantifies agent Y's belief at time t that omega_bar in A.
- **Logical equivalence** A == B iff [[A]] = [[B]].
- **Evidential corpus** EC^Y_t at time t. [[EC^Y_t]] is the set of worlds compatible with EC^Y_t. Worlds outside this set are "impossible for Y at time t."
- **Doxastic equivalence**: A =_dox B iff [[EC^Y_t]] cap [[A]] = [[EC^Y_t]] cap [[B]]. (Logical equivalence forces doxastic equivalence; the converse fails.)
- For A subset Omega, Abar = [[EC^Y_t]] \ A.
- **Partition** Pi of Omega -> Boolean algebra R built from subsets unions of partition cells. The pair (Omega, R) is a **propositional space**; cells are the **atoms** of R.

## Credibility Function *(p.599)*

A credibility function Cr: R -> [0,1] is point-valued, uniquely determined by (EC^Y_t, Y, t), monotone for inclusion, with Cr(empty) = 0 lower bound and Cr(Omega) upper bound. The triple (Omega, R, Cr) is a **credibility space**, indexed by EC^Y_t.

Smets proves elsewhere (Smets 1990b) that the set of credibility functions on a propositional space is **convex**: if Cr_1 and Cr_2 are credibility functions, then alpha*Cr_1 + (1-alpha)*Cr_2 (alpha in [0,1]) is too. He also derives the **pignistic transformation** (Cr -> a probability function used for decision making) and shows probability functions are credibility functions (Smets 1992b).

## Axiom A1 — Equi-credibility of doxastically equivalent propositions *(p.599)*

> Suppose two credibility spaces (Omega, R_i, Cr_i), i = 1,2 induced by EC^Y_t. Let A_1 in R_1, A_2 in R_2. Let f_{A_1} and f_{A_2} be any propositions identifying A_1 and A_2. If f_{A_1} =_dox f_{A_2}, then Cr_1(A_1) = Cr_2(A_2).

Justification: doxastically equivalent propositions are equally credible (Kyburg, 1987a). A1 lets the granularity of the algebra be irrelevant when the evidential corpus is fixed.

## Coarsening *(p.599)*

A mapping C: R -> R' is a **coarsening** if it sends one or several atoms of R into one atom of R', and each atom of R lands in exactly one atom of R'. C(omega) is the atom of R' that omega lands in; C(A) = union {C(omega): omega in A}. C^{-1}(A') is the union of atoms of R sent to A'.

**Theorem 1** *(p.599)*: Let (Omega, R', Cr')_{EC^Y_t} be derived from (Omega, R, Cr)_{EC^Y_t} through an uninformative coarsening C. Then for A' in R': Cr'(A') = Cr(C^{-1}(A')).

Consequence: the granularity of the algebra is irrelevant for credibility — the only constraint is that each atom of R is included in one atom of R' and each atom of R' contains at least one atom of R.

## Refinement *(p.599-600)*

Mapping R: (Omega, R) -> (Omega', R') such that each atom of R maps to one or several atoms of R' and each atom of R' is the image of exactly one atom of R. Without loss of generality Omega = Omega' = Omega*, denoted such after re-mapping.

**Worked example (Paul's age)**: Omega = [0, infinity); atoms omega_1 = [0, 20), omega_2 = [20, 40), omega_3 = [40, infinity) of R. Cr quantifies Y's beliefs over R based on EC^Y_t. Let P_1, P_2, P_3 be three propositions Y does not know (only that exactly one is true). Refinement R sends omega_1 -> omega_1, omega_2 -> omega_2, omega_3 -> {X_1, X_2, X_3} where X_i = "omega_3 and P_i". Y knows nothing about which P_i obtains.

The uninformativeness of R means Cr'(omega_1 cup X_1) = Cr'(omega_1 cup X_2) = Cr'(omega_1 cup X_3). Iterating with a different uninformative refinement R'' (omega_3 -> {Y_1, Y_2}, with f_{Y_1} =_dox f_{X_1}, f_{Y_2} =_dox f_{X_2 cup X_3}) and applying A1 gives Cr'(omega_1 cup X) constant for all X subset R(omega_3).

## Axiom R1 *(p.600)*

> Let (Omega, R, Cr)_{EC^Y_t} be a credibility space, R a refinement (Omega, R) -> (Omega', R'). Let omega be a given atom of R, B in R' with B cap R(omega) = empty, X_i (i = 1, ..., n) the atoms of R' included in R(omega). Let (Omega', R', Cr')_{EC^Y_t} be the credibility space induced from (Omega, R, Cr) by R. Then:
> Cr'(B cup X_i) = Cr'(B cup X_j) for all i, j in {1, ..., n}.

**Theorem 2** *(p.600)*: Under R1, for any omega in Omega, B in R' with B cap R(omega) = empty, Cr'(B cup X) is constant for all X subset R(omega).

## Axiom R2 *(p.600)*

> Let (Omega, R, Cr)_{EC^Y_t} be the credibility space based on EC^Y_t. Let R be a uninformative refinement (Omega, R) -> (Omega', R'). Let A in R, omega_i (i = 1, ..., n) be n different atoms of R with A cap omega_i = empty. Let X_i be any element of R' strictly included in R(omega_i). Then there is a function g such that:
> Cr'(R(A) cup X_1 cup ... cup X_n) = g({Cr(A cup B): B in R, B subset omega_1 cup ... cup omega_n})

Simplified form: Cr'(R(A) cup X_1 cup ... cup X_n) does not depend on Cr(X) when X cap (A cup omega_1 cup ... cup omega_n) = empty. Same nature as A1: irrelevant credibilities should not interfere with relevant ones.

## Trichotomy theorem (consequence of R1 + R2) *(p.601)*

From R1 and R2, Cr' must satisfy one of three relations:

1. Cr'(R(A) cup X_1 cup ... cup X_n) = Cr(A) — **belief function** case.
2. Cr'(R(A) cup X_1 cup ... cup X_n) = Cr(A cup omega_1 cup ... cup omega_n) — **plausibility function** case.
3. Cr'(R(A) cup X_1 cup ... cup X_n) = max(Cr(A), Cr(omega_1), ..., Cr(omega_n)) — does not satisfy the conditioning axioms; finds use in **possibility theory**.

## Updating / Conditioning *(p.601-602)*

Y expands EC^Y_t by adding evidence Ev_A compatible with EC^Y_t implying that all worlds in Abar are impossible (i.e., omega_bar is not in Abar). Equivalently f_{Abar} == bottom. Cr_A is the conditional credibility function after adding Ev_A.

### Axiom M1 *(p.601)*
> Let (Omega, R, Cr)_{EC^Y_t} be a credibility space based on EC^Y_t. Let Ev_A be evidence compatible with EC^Y_t implying that f_{Abar} == bottom. Let (Omega, R, Cr_A)_{EC^Y_t cup {Ev_A}} be the credibility space based on EC^Y_t cup {Ev_A}. Then Cr_A depends only on Cr and A.

Iterated conditioning argument: learning f_A == top then f_B == top, or learning them in the opposite order, or learning f_{A cap B} == top directly should yield the same final beliefs. This fixes the mathematical structure of conditioning.

### Theorem 3 *(p.601)*
There is a function f such that Cr_A satisfies:
1. Cr_A(B) = 0 for all B subset Abar, B in R; and for all B in R
2. Cr_A(B) = Cr_A(B cap A)
3. Cr_A(B) = f(Cr(B cap A), Cr(Bbar cap A), Cr(Abar), Cr(A), Cr((B cap A) cup A), Cr((Bbar cap A) cup A), Cr(Omega))

(The page-3 line "Cr((BcapA) cup A)" appears garbled in the OCR; it is the standard set of arguments needed to fix the conditioning by inclusion-exclusion-style relations.)

### Theorem 4 *(p.601)*
Let (Omega, R, Cr)_{EC^Y_t} be the credibility space based on EC^Y_t. Let R be an uninformative refinement (Omega, R) -> (Omega', R') such that each atom of R is mapped onto itself in R', except one atom omega of R refined into omega_1 and omega_2 by R. Let Cr' be derived from Cr on R' by R. Suppose conditioning of Cr' on omega_2bar:
> for all A in R, Cr'_{omega_2bar}(R(A) cap omega_2bar) = Cr(A).

(Refining one atom and conditioning on the bar leaves the original credibility unchanged on the unaltered part — confirms that "the Q story becomes irrelevant" in the worked example.)

### Axiom M2 — non-degenerated solutions *(p.601)*
> Cr_A(B) is not constant for all A in R.

### Axiom M3 — additivity preservation *(p.601)*
> If the credibility function Cr is additive, then additivity is preserved after conditioning.

### Theorem 5 — minimal and maximal solutions *(p.601-602)*

Let {omega_1, ..., omega_n} be the atoms of R; R uninformative refinement to (Omega', R'); I subset {1, ..., n}; X_i subset R(omega_i) for i in I; A in R with omega_i cap A = empty for all i in I. The refinement and conditioning admit only two solutions:

**Minimal solution** *(p.602)*:
$$
Cr_A(B) = \frac{Cr(B \cup \bar{A}) - Cr(\bar{A})}{Cr(\Omega) - Cr(\bar{A})} Cr_A(A)
$$
$$
Cr'(R(A) \cup \bigcup_{i \in I} X_i) = Cr(A)
$$

**Maximal solution** *(p.602)*:
$$
Cr_A(B) = \frac{Cr(A \cap B)}{Cr(A)} Cr_A(A)
$$
$$
Cr'(R(A) \cup \bigcup_{i \in I} X_i) = Cr(A \cup \bigcup_{i \in I} \omega_i)
$$

The qualification as minimal/maximal comes from the inequality (forced by monotonicity for inclusion and A1):
$$
Cr(A) \le Cr'\!\left(R(A) \cup \bigcup_{i \in I} X_i\right) \le Cr\!\left(A \cup \bigcup_{i \in I} \omega_i\right)
$$
*(p.602)*

The two solutions are **dual** via the co-credibility function:
$$
CoCr(A) = Cr(\Omega) - Cr(\bar{A})
$$
A credibility function satisfying the minimal solution induces a co-credibility satisfying the maximal solution and vice versa. Hence in practice there is one credibility function (the other is its dual) — the same duality as belief vs plausibility. *(p.602)*

### Three particular cases of Cr_A(A) *(p.602)*

1. **Cr_A(A) = 1** -> normalized Dempster's rule of conditioning (TBM under closed-world assumption).
2. **Cr_A(A) = Cr(Omega) - Cr(Abar)** (minimal) and Cr_A(A) = Cr(A) (maximal) -> unnormalized Dempster's rule (TBM under open-world assumption).
3. **Cr_A(A) = Cr(Omega)** -> partially renormalized Dempster's rule. Fits the idea that initial belief on Omega is preserved by proportional reallocation of belief on Abar.

If initially Cr is a probability and Cr_A(A) = 1, both solutions of theorem 5 collapse and equal Bayesian conditioning. *(p.602)*

### Gardenfors's compelling properties: homomorphism and preservation *(p.602)*

> **Homomorphism**: If Cr(Abar) < Cr(Omega) and Cr = p*Cr' + (1-p)*Cr'' with p in [0,1], then Cr_A = p*Cr'_A + (1-p)*Cr''_A.
>
> **Preservation**: If Cr(Abar) < Cr(Omega) and Cr(B) = Cr(Omega), then Cr_A(B) = Cr_A(A).

- Homomorphism is satisfied **only by unnormalized Dempster's rule** (it fails as soon as a normalization factor is introduced through division).
- Preservation is satisfied by both the minimal and maximal solutions.
- **Probability theory cannot satisfy both simultaneously** -> rejection of probability functions for quantifying beliefs at the credal level.
- Both are satisfied in TBM with unnormalized Dempster conditioning (Smets and Kennes, 1990); the precondition Cr(Abar) < Cr(Omega) can even be relaxed, but if Cr(Abar) = Cr(Omega), then Cr_A(B) = 0 for all B in R, including Cr_A(Omega) = 0 — a state of complete contradiction (analogous to logic with a contradiction). Studied in Smets (1992c). *(p.602)*

## From credibility to belief functions: The Closure Axiom *(p.603)*

For a propositional space (Omega, R), the only relevant info defining the set of credibility functions on R is r = |R| (number of atoms). Write E_r for the set of credibility functions on an algebra with r atoms satisfying the minimal solution of theorem 5. Let I_Omega be the **vacuous credibility function**: I_Omega(X) = 0 for all X subset Omega, X != Omega, and I_Omega(Omega) = 1.

Let B_r be the set of belief functions on an algebra with r atoms. B_r is closed under conditioning. Furthermore all elements of B_r can be generated from the vacuous credibility function I_Omega in B_r by appropriate conditioning and **simplex combinations** (a simplex combination is a convex combination except the weights may sum to a value in [0, 1] instead of exactly 1).

Let R_r be the set of refinements R_i: (Omega, R) -> (Omega', R') with |R| = r, |R'| = r+1 (one atom of R refined into two atoms of R'). For Cr in E_r, R_i in R_r, let R_i(Cr) in E_{r+1} be the credibility function defined on R' after applying R_i via the minimal solution of theorem 5.

Let Ext(E_r) be the set of credibility functions on R' obtainable by **convex combinations** of credibility functions generated on R' from elements of E_r via refinement operators in R_r. Let D(Ext(E_r)) be the closure of Ext(E_r) under conditioning (minimal solution) and simplex combinations. Formally:

$$
\mathrm{Ext}(\mathcal{E}_r) = \left\{ Cr : Cr \in \mathcal{E}_{r+1},\ Cr = \sum_i \alpha_i R_i(Cr_i),\ Cr_i \in \mathcal{E}_r,\ R_i \in \mathcal{R}_r,\ \alpha_i \ge 0,\ \sum_i \alpha_i = 1 \right\}
$$

$$
\mathcal{D}(\mathrm{Ext}(\mathcal{E}_r)) = \left\{ Cr : Cr \in \mathcal{E}_{r+1},\ Cr = \sum_i \alpha_i Cr_{i, A_i},\ \alpha_i \ge 0,\ \sum_i \alpha_i = 1,\ Cr_{i, A_i}\ \text{is the (minimal) conditioning on } A_i \in \mathcal{R}'\ \text{of } Cr_i \in \mathcal{D}(\mathrm{Ext}(\mathcal{E}_r)) \right\}
$$

**Closure Axiom** *(p.603)*:
> E_{r+1} = D(Ext(E_r))

I.e., every credibility function on r+1 atoms is obtainable by refinement, conditioning (minimal solution), and simplex combinations from credibility functions on r atoms.

### Theorem 6 *(p.603)*

1. **B_r = E_r** — every credibility function in E_r (those satisfying the minimal solution of theorem 5) is a belief function.
2. Credibility functions satisfying the **minimal** solution for conditioning and refinement are belief functions.
3. Credibility functions satisfying the **maximal** solution for conditioning and refinement are plausibility functions.

This is the **central representation theorem**: under the axiom system (A1, R1, R2, M1, M2, M3, Closure), credibility functions are forced to be belief functions.

## Conclusions of paper *(p.603)*

- The axioms determine that beliefs at the credal level are quantified by belief functions.
- All axioms hold in probability theory **except** that homomorphism and preservation cannot be jointly satisfied — so the axioms reject probability theory as a model for credal-level beliefs.
- Probability functions are special cases of normalized belief functions.

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of atoms in algebra | r | — | — | finite (>=1) | 603 | Indexes B_r and E_r families |
| Vacuous credibility | I_Omega | — | I_Omega(Omega)=1, else 0 | — | 603 | Total ignorance, identity of E_r |
| Convex combination weight | alpha | — | — | [0, 1] with sum_i alpha_i = 1 | 603 | Convex (simplex) combination |
| Simplex combination weight | alpha | — | — | alpha_i >= 0, sum_i alpha_i in [0, 1] | 603 | Distinct from convex combo |
| Conditioning weight | p | — | — | [0, 1] | 602 | Used in homomorphism statement |
| Pignistic transformation | BetP | — | derived from Cr | probability | 599 | Smets 1990b — used for decision-making |

## Key Equations / Statistical Models

Doxastic equivalence:
$$
A \equiv_{\mathrm{dox}} B \iff [\![EC^Y_t]\!] \cap [\![A]\!] = [\![EC^Y_t]\!] \cap [\![B]\!]
$$
Where: [[X]] is the set of worlds satisfying X, EC^Y_t is the evidential corpus of agent Y at time t. *(p.599)*

Theorem 1 (uninformative coarsening):
$$
Cr'(A') = Cr(C^{-1}(A'))
$$
Where: C is an uninformative coarsening, A' is an element of the coarsened algebra R'. *(p.599)*

Trichotomy after R1 + R2:
$$
Cr'(R(A) \cup X_1 \cup \dots \cup X_n) = Cr(A) \quad \text{(belief)}
$$
$$
Cr'(R(A) \cup X_1 \cup \dots \cup X_n) = Cr(A \cup \omega_1 \cup \dots \cup \omega_n) \quad \text{(plausibility)}
$$
$$
Cr'(R(A) \cup X_1 \cup \dots \cup X_n) = \max(Cr(A), Cr(\omega_1), \dots, Cr(\omega_n)) \quad \text{(possibility)}
$$
*(p.601)*

Minimal conditioning solution:
$$
Cr_A(B) = \frac{Cr(B \cup \bar{A}) - Cr(\bar{A})}{Cr(\Omega) - Cr(\bar{A})} \cdot Cr_A(A)
$$
Where: Abar = Omega \ A, Cr_A(A) parameterizes the family of minimal solutions. *(p.602)*

Maximal conditioning solution:
$$
Cr_A(B) = \frac{Cr(A \cap B)}{Cr(A)} \cdot Cr_A(A)
$$
*(p.602)*

Co-credibility duality:
$$
CoCr(A) = Cr(\Omega) - Cr(\bar{A})
$$
*(p.602)*

Inclusion bound (monotonicity + A1):
$$
Cr(A) \le Cr'\!\left(R(A) \cup \bigcup_{i \in I} X_i\right) \le Cr\!\left(A \cup \bigcup_{i \in I} \omega_i\right)
$$
*(p.602)*

Closure axiom:
$$
\mathcal{E}_{r+1} = \mathcal{D}(\mathrm{Ext}(\mathcal{E}_r))
$$
*(p.603)*

## Methods & Implementation Details
- Algebraic / axiomatic derivation, not algorithmic. *(p.598)*
- Worked illustrative example (Paul's age) at p.600 demonstrates uninformative refinement.
- Three "particular cases" of conditioning (p.602) map directly onto: normalized Dempster (closed world TBM), unnormalized Dempster (open world TBM), and partially renormalized Dempster.
- Implementation guidance: when implementing TBM at the credal level, use unnormalized Dempster conditioning to satisfy both homomorphism and preservation; use the pignistic transformation to derive a probability for decision-making (separating credal from pignistic level).

## Figures of Interest
- No figures. Six pages of dense theoretical text. The Paul's age scenario on p.600 is the only worked example.

## Results Summary
- Under axioms A1, R1, R2, M1, M2, M3, and the Closure Axiom, the credibility function on a finite Boolean algebra is exactly a Dempster-Shafer belief function. Plausibility functions are the dual case (maximal solution); possibility functions arise from a third branch that is incompatible with the conditioning axioms. *(p.601-603)*
- Probability functions cannot satisfy A1 and R1 simultaneously; hence probability is rejected as a credal-level belief representation. *(p.600, 603)*
- Unnormalized Dempster's rule is uniquely characterized by Gardenfors's homomorphism and preservation. *(p.602)*

## Limitations
- "Short version" — full proofs deferred to Smets (1992b) IRIDIA tech report. *(p.598)*
- Restricted to **finite** Boolean algebras (atoms enumerable). *(p.599, 603)*
- Closure Axiom acknowledged as **not provable**: "We cannot prove it, but we feel it can be postulated. We feel reasonable to assume that any credibility function in E_{r+1} could be derived from some credibility functions in E_r through refinement, conditioning and simplex combinations." *(p.603)*
- Some axioms (e.g., R2) require non-trivial proofs not included; "the gain is not worth the needed proof" for deriving R2 from A1. *(p.601)*
- Acknowledges that some readers may find specific axioms unreasonable — defends them by noting most are satisfied in probability theory (except the joint homomorphism + preservation). *(p.603)*

## Arguments Against Prior Work
- **Probability theory cannot accommodate uninformative refinement under axiom A1** — once a refinement happens, classical probability needs additional information about the distribution among new atoms (often equidistribution), thereby updating EC^Y_t and violating uninformativeness. *(p.600)*
- **Probability theory cannot satisfy homomorphism + preservation jointly** — Gardenfors (1988) noted this for revision; Smets uses it to reject probability at the credal level. *(p.602)*
- **Possibility theory's max-rule** does not satisfy the conditioning axioms — third branch of the trichotomy is excluded. *(p.601)*
- **Normalized Dempster's rule** fails homomorphism due to its renormalization factor — argument for unnormalized form (TBM open-world). *(p.602)*

## Design Rationale
- **Credal level vs pignistic level separation**: belief functions live at the credal level (where beliefs are entertained); pignistic transformation produces probabilities only when decision-making requires it (Smets 1990b). *(p.599)*
- **Uninformative coarsening / refinement** axioms preserve doxastic content: changes in algebra granularity should not change beliefs unless the evidential corpus changes. *(p.599-600)*
- **Iterated conditioning consistency** (M1) — order-independence of evidence accumulation forces the mathematical structure. *(p.601)*
- **Closure axiom** is justified pragmatically: it cannot be proven but is "reasonable" — every belief function can be built from the vacuous one by refinement + conditioning + simplex combinations. *(p.603)*
- **Open-world TBM (unnormalized Dempster)** is preferred because it (a) keeps homomorphism and preservation, (b) admits the contradiction state Cr_A(Omega) = 0 analogous to logical contradiction. *(p.602)*

## Testable Properties
- A1 implies coarsening invariance: Cr'(A') = Cr(C^{-1}(A')). *(p.599)*
- Theorem 2: under R1, Cr'(B cup X) is constant over all X subset R(omega) when B cap R(omega) = empty. *(p.600)*
- Theorem 5 minimal solution: $Cr_A(B) = \frac{Cr(B \cup \bar{A}) - Cr(\bar{A})}{Cr(\Omega) - Cr(\bar{A})} Cr_A(A)$. *(p.602)*
- Theorem 5 inclusion bound: $Cr(A) \le Cr'(R(A) \cup \bigcup X_i) \le Cr(A \cup \bigcup \omega_i)$. *(p.602)*
- Co-credibility duality: $CoCr(A) = Cr(\Omega) - Cr(\bar{A})$ swaps minimal and maximal solutions. *(p.602)*
- Theorem 6: B_r = E_r — every credibility function satisfying minimal solution is a belief function. *(p.603)*
- Probability functions cannot satisfy A1 and R1 simultaneously. *(p.600)*
- Unnormalized Dempster conditioning is the unique conditioning rule satisfying both homomorphism and preservation. *(p.602)*
- If Cr(Abar) = Cr(Omega), unnormalized Dempster gives Cr_A(Omega) = 0 (contradiction state). *(p.602)*

## Relevance to Project
This paper is direct foundational material for propstore's argumentation/reasoning layer, specifically:

- **Subjective logic / belief functions / TBM** as alternatives to or complements of probability for representing belief with provenance type `vacuous` (Jøsang 2001's vacuous opinions correspond to Smets's vacuous credibility I_Omega). The closure axiom shows how the vacuous belief function is the *generator* of all belief functions through refinement and conditioning.
- **Honest ignorance over fabricated confidence**: I_Omega is the formal counterpart of "I don't know" — it is the unit element from which all other belief states are constructed. This validates propstore's design principle that vacuous opinions are a first-class type.
- **Conditioning rules**: the trichotomy (normalized / unnormalized / partially renormalized Dempster) maps onto choices in the ATMS / world layer (`propstore.world`) and gives axiomatic guidance for which conditioning rule to use depending on whether the world is closed (normalized) or open (unnormalized — preferred for open-world reasoning, which fits propstore's lazy-until-render discipline).
- **Algebra-independence**: A1 and R1 mean credibility doesn't depend on choice of granularity. This is the formal counterpart of propstore's lemon/OntoLex separation — concept identity is invariant under granularity changes in the lexical entries.
- **Rejection of probability at the credal level**: justifies propstore's typed-provenance distinction between `measured`/`calibrated`/`stated`/`defaulted`/`vacuous` rather than collapsing everything to probability.
- **TBM separation of credal and pignistic levels**: directly maps to propstore's "lazy until rendering" architecture — beliefs accumulate at the credal level (storage), pignistic transformation happens at render time only when a decision must be made.

## Open Questions
- [ ] Smets (1992b) IRIDIA technical report contains full proofs — is it worth retrieving for the propstore claims extraction?
- [ ] Does propstore want to enforce homomorphism + preservation in its merge layer? If yes, this dictates unnormalized Dempster as the merge rule.
- [ ] How does Smets's pignistic transformation (here cited as Smets 1990b) interact with subjective-logic projection (Jøsang 2001)? Both target a probability for decision-making but from different starting axioms.
- [ ] Closure Axiom is unproven by Smets — is there a model in propstore's storage where it could be tested or violated?

## Collection Cross-References

### Already in Collection
- [A Mathematical Theory of Evidence](../Shafer_1976_MathematicalTheoryEvidence/notes.md) — Smets cites Shafer (1976) as the source of belief functions; the present paper provides the axiomatic justification for treating Cr as a belief function in Shafer's sense.
- [Revisions of Knowledge Systems Using Epistemic Entrenchment](../Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/notes.md) — Smets imports Gardenfors (1988)'s **homomorphism** and **preservation** properties of revision and uses them to reject probability theory at the credal level (only unnormalized Dempster's rule satisfies both jointly).
- [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) — The canonical TBM paper. Smets and Kennes (1990) is cited throughout; this 1993 paper is the axiomatic justification of the credal level used in TBM and explicitly motivates the unnormalized open-world conditioning that TBM adopts.
- [The Combination of Evidence in the Transferable Belief Model](../Smets_1990_CombinationEvidenceTransferableBelief/notes.md) — Smets (1990a), IEEE TPAMI 12:447-458. Cited for the axiomatic justification of Dempster's rule of combination and for the pignistic transformation BetP referenced at p.599 and p.602; supplies the credal/pignistic level split that this credibility-function axiomatization presupposes.
- `papers/Smets_1991_TransferableBeliefModel/` (notes pending) — Smets (1991) varieties-of-ignorance / earlier TBM exposition. Cited as the cumulative TBM build-up.
- `papers/Smets_1992_NatureUnnormalizedBeliefsEncountered/` (notes pending) — Smets (1992a) — analysis of Cr(Omega) < 1 / unnormalized beliefs / contradiction state. Directly cited at p.602 for the meaning of `Cr_A(Omega) = 0`.
- [Belief Functions: The Disjunctive Rule of Combination and the Generalized Bayesian Theorem](../Smets_1993_BeliefFunctionsDisjunctiveRule/notes.md) — Smets (1993) IJAR paper on the disjunctive rule and GBT — companion 1993 paper, distinct from this axiomatic-justification IJCAI paper. Provides the operator-level DRC/GBT machinery whose credal-level foundation is axiomatized here.

### New Leads (Not Yet in Collection)
- Smets P. (1992b) "An axiomatic justification for the use of belief function to quantify beliefs" — IRIDIA TR/IRIDIA/92 — full proofs of the theorems summarized in the IJCAI version. Worth retrieving if propstore wants to formalize the axioms.
- Smets P. (1990b) "Constructing the pignistic probability function in a context of uncertainty" — UAI 5, pp. 29-40 — the credal-to-pignistic projection used at decision time. Directly relevant to propstore's render-time policy.
- Smets P. (1992c) "The concept of distinct evidence" — IPMU 92, pp. 789-794 — analysis of distinctness of evidence, cited as Smets (1992c) for combination semantics.
- Klawonn F. and Schwecke E. (1992) "On the axiomatic justification of Dempster's rule of combination" — Int. J. Intel. Systems 7:469-478 — companion axiomatic justification specifically for Dempster's combination rule (this paper axiomatizes the credibility function itself).
- Klawonn F. and Smets Ph. (1992) "The dynamics of belief in TBM and specialization-generalization matrices" — UAI 92 — TBM dynamics, specialization-generalization matrices.
- Kennes R. (1991) "Evidential Reasoning in a Categorial Perspective" — UAI 91 — categorial-perspective conjunction/disjunction of belief functions.
- Kyburg H. (1987a) "Objective probabilities" — IJCAI-87, pp. 902-904 — invoked for axiom A1's motivation (doxastically equivalent propositions are equally credible).
- Ruspini E.H. (1986) "The logical foundations of evidential reasoning" — SRI Technical Note 408 — logical foundations cited in support of the doxastic equivalence framework.
- Smith C.A.B. (1961) "Consistency in statistical inference and decision" — J. Roy. Statist. Soc. B 23:1-37 — foundational consistency conditions for inference and decision; relevant for the credal/pignistic split.

### Supersedes or Recontextualizes
- (none — this paper provides foundational axiomatic justification rather than supersession)

### Conceptual Links (not citation-based)
**Belief-function and uncertainty-representation foundations:**
- [A Logic for Uncertain Probabilities](../Josang_2001_LogicUncertainProbabilities/notes.md) — Jøsang's vacuous opinion (b=d=0, u=1) is the subjective-logic counterpart of Smets's vacuous credibility I_Omega. Both are first-class representations of "I don't know." Smets's closure axiom (every belief function generated from I_Omega via refinement+conditioning+simplex combinations) parallels Jøsang's construction of opinions from vacuous via accumulation of evidence.
- [Subjective Logic: A Formalism for Reasoning Under Uncertainty](../Josang_2016_SubjectiveLogic/notes.md) — Jøsang's monograph extends the same vacuous-as-first-class principle and formalizes a probability projection from opinions to probabilities; analogous to Smets's pignistic transformation (cited here as Smets 1990b) but built on a different algebraic substrate.
- [Decision-Making with Belief Functions: a Review](../Denoeux_2018_Decision-MakingBeliefFunctionsReview/notes.md) — Denoeux reviews the decision rules built on belief functions, including the pignistic transformation Smets axiomatizes elsewhere. The credal/pignistic distinction this 1993 paper presupposes is one of Denoeux's organizing themes.
- [Inferences from Multinomial Data: Learning About a Bag of Marbles](../Walley_1996_InferencesMultinomialDataLearning/notes.md) — Walley's IDM is an alternative imprecise-probability formalism that also treats ignorance non-numerically; tension with Smets is whether to use lower/upper probabilities (Walley) or belief/plausibility (Smets) — the trichotomy in this paper (p.601) shows belief and plausibility are duals while max-rule is incompatible with the conditioning axioms.
- [An Axiomatic Framework for Bayesian and Belief-function Propagation](../Shenoy_1990_AxiomsProbabilityBelief-functionPropagation/notes.md) — Shenoy axiomatizes propagation/combination operators across Bayesian and belief-function frameworks; this paper axiomatizes the credibility *function* itself. They are complementary: Shenoy fixes the operator algebra, Smets fixes the underlying point-valued measure.

**AGM and revision dynamics:**
- [Revisions of Knowledge Systems Using Epistemic Entrenchment](../Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/notes.md) — already a citation; the link is also conceptual: Gardenfors's homomorphism/preservation axioms used here to reject probability are part of the AGM revision tradition that propstore.belief_set implements.
- [On the Logic of Theory Change: Partial Meet Contraction and Revision Functions](../Alchourron_1985_TheoryChange/notes.md) — AGM revision; conditioning in Smets (M1, M2, M3) is the credibility-level analogue of AGM revision. The order-independence M1 invokes (learn A then B = learn B then A = learn A∩B) is structurally related to AGM's success and consistency postulates.
- [On the Logic of Iterated Belief Revision](../Darwiche_1997_LogicIteratedBeliefRevision/notes.md) — Darwiche-Pearl iterated revision; Smets's iterated-conditioning argument for M1 is the belief-function analogue and parallels propstore's iterated revision in `propstore.belief_set`.

### Cited By (in Collection)
- [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) — Smets and Kennes cite this 1993 IJCAI paper as ref [49] "An axiomatic justification for the use of belief function to quantify beliefs" — the promised foundational axiomatization for the credal level of TBM.

## Related Work Worth Reading
- **Smets and Kennes (1990) "The Transferable Belief Model"** — the canonical TBM paper (already in propstore as `papers/Smets_Kennes_1994_TransferableBeliefModel/`). This 1993 paper is the axiomatic justification for that model.
- **Smets (1992b) IRIDIA TR** — full proofs of the present paper's theorems.
- **Smets (1990a)** — combination of evidence / Dempster's rule justification, IEEE PAMI 12:447-458.
- **Smets (1990b)** — pignistic transformation, in UAI 5.
- **Smets (1991) "The Transferable Belief Model"** — already in propstore as `papers/Smets_1991_TransferableBeliefModel/`.
- **Klawonn and Schwecke (1992)** — On the axiomatic justification of Dempster's rule of combination, Int. J. Intel. Systems 7:469-478.
- **Klawonn and Smets (1992)** — Dynamics of belief in TBM and specialization-generalization matrices, in UAI 92.
- **Gardenfors (1988) "Knowledge in Flux"** — homomorphism and preservation properties of revision.
- **Shafer (1976)** — Mathematical Theory of Evidence (already in propstore as `papers/Shafer_1976_MathematicalTheoryEvidence/`).
- **Kyburg (1987a)** — objective probabilities, IJCAI-87, pp. 902-904.
- **Ruspini (1986)** — logical foundations of evidential reasoning, SRI tech note 408.
- **Smith (1961)** — consistency in statistical inference and decision, J. Roy. Statist. Soc. B 23:1-37.

---

**See also (cited-by):** [The Nature of the Unnormalized Beliefs Encountered in the Transferable Belief Model](../Smets_1992_NatureUnnormalizedBeliefsEncountered/notes.md) - Smets 1992 supplies the open-world interpretation of m(empty) > 0 and the homomorphism-under-refinement uniqueness argument for unnormalized conditioning. The two papers are companions: 1992 justifies the unnormalized form, 1993 axiomatizes belief quantification given that form.
