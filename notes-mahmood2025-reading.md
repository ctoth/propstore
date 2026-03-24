# Reading: Mahmood 2025 — Structure-Aware Encodings of Argumentation Properties for Clique-width

## Paper Info
- Authors: Yasir Mahmood, Markus Hecher, Johanna Groven, Johannes K. Fichte
- Venue: AAAI 2026 (accepted)
- 33 pages, read pages 0-11 so far

## Key Concept
The paper designs **directed decomposition-guided (DDG) reductions** from argumentation problems to (Q)SAT that **linearly preserve clique-width**. This means the SAT encoding's structural complexity doesn't blow up relative to the input AF.

## Core Technical Approach

### k-expressions and Clique-width
- Clique-width is a graph parameter more general than treewidth — can be small for dense graphs
- A k-expression builds a graph using k colors via operations: create vertex, disjoint union, relabeling, edge introduce
- The directed incidence clique-width of an AF F is denoted dcw(G_d(F))

### SAT Encodings by Semantics (pages 6-12)

**Stable Extensions (p.7, Formulas 1-4):**
- Variables: x_c for each color c (whether color is in extension)
- Formula 1: initial create — x_c for root color
- Formula 2: disjoint union — propagate
- Formula 3: relabeling — propagate
- Formula 4: edge introduce — conflict-freeness (if c attacks c', then ¬(x_c ∧ x_{c'}))
- Also need d_c^v auxiliary variables: "every non-extension argument of color c up to operation is attacked by the extension"

**Admissible Extensions (p.9, Formulas 10-15):**
- Reuse conflict-freeness from stable
- Add attack variable a: "whether some non-extension color remains attacking"
- Formula 10-11: initial/union propagation
- Formula 12: edge introduce — track attacks
- Formula 13-14: handle not-initial cases
- Formula 15: root constraint — no color remains attacking

**Complete Extensions (p.10, Formulas 16-24):**
- Additionally need d_c^O variables — whether argument could have been included
- Formulas 16-20: propagate "defended or not" information along k-expression
- Formulas 21-24: at root, encode that no argument is incorrectly left out

**Preferred Extensions (p.12, Formulas 25-31):**
- Construct CNF φ_pref using starred variables for "sub-larger extension candidates"
- Formula 25-29: encode admissible extension via starred vars
- Formula 30-31: find admissible extension that is subset-maximal
- Uses QBF (quantified Boolean formula): ∀ free variables, the QBF evaluates to false if there's no larger admissible extension
- Convert QBF → DNF matrix → CNF via Lemma 14

**Semi-Stable Extensions (p.12):**
- Need to maximize range of arguments
- CNF φ_semist constructed

## Complexity Results
- Proposition 5: QSATs on directed incidence clique-width k, quantifier depth d, size s can be solved in time exp(t · (1 + O(k)) · poly(s)) — fixed-parameter tractable in clique-width

## Key Theorems So Far
- Theorem 7 (stable): DDG reduction R_stable is correct, bijective correspondence between stable extensions and satisfying assignments
- Theorem 8 (CW-Awareness): SAT instance linearly preserves clique-width
- Theorem 10 (admissible): Correct DDG reduction
- Theorem 12 (complete): Correct DDG reduction
- Theorem 14 (preferred): Correct, uses QBF with 2 ∀-quantifiers
- Theorem 16 (semi-stable): Correct

## Pages 12-14: Lower Bounds and Conclusion

**Theorem 19 (Runtime-UBs, p.13):** For AF of size n with directed clique-width k, problem σ can be solved in time:
- 2^O(k) · poly(s) for σ ∈ {stab, adm, comp}
- 2^O(k²) · poly(s) for σ ∈ {pref, semSt, stage}

**Lower bounds (p.14):**
- Corollary 22 (Stable/Complete): Under ETH, cannot decide for AF F=(A,R) of directed clique-width k in time 2^o(k) · poly(|A|+|R|)
- Proposition 23 (Preferred/Semi-Stable/Stage): Under ETH, cannot decide in time 2^o(k²) · poly(|A|+|R|)
- These lower bounds match the upper bounds — the DDG reductions are essentially optimal

**Section 3.3 Credulous/Skeptical Reasoning (p.13):**
- To solve credulous acceptance: add variable x_σ for argument a, conjoin with formula, check SAT
- To solve skeptical acceptance: add ¬x_σ, flip answer

**Section 5 Conclusion (p.14-15):**
- DDG reductions efficiently encode KRR formalisms to (Q)SAT while respecting clique-width
- Applicable to abductive reasoning, logic-based argumentation, ASP, and more
- Solutions bijectively preserved → enumeration complexity transfers too

## Pages 15-18: References
47 references total. Key citations include:
- [9] Charwat et al. 2015 — Methods survey (already in our research)
- [19] Dung 1995 — foundational (already in collection)
- [22] Dvořák et al. 2010 — dynamic programming for argumentation on treewidth
- [23] Dvořák et al. 2012 — fixed-parameter tractable algorithms for abstract argumentation
- [24] Fichte et al. 2021 — disposition-guided reductions for argumentation
- [25] Fichte, Hecher, Pfandler — lower bounds for QBFs of bounded treewidth
- [38] Niskanen & Järvisalo — µ-toksia: efficient abstract argumentation reasoner
- [44] Rahwan 2009 — Argumentation in AI

## Pages 18-30: Detailed Examples and Proofs
- Section 6 (p.18-20): Detailed worked examples for admissible, complete, preferred extensions using the AF from Example 2 — shows step-by-step formula construction along k-expression parse tree
- Section 7 (p.20-30): Full formal proofs of all theorems (correctness + CW-awareness)
  - Theorem 7 proof (stable): bijective correspondence between stable extensions and satisfying assignments via bottom-up construction on k-expression
  - Theorem 8 proof (CW-awareness): shows SAT instance construction adds ≤ 11k+2 colors, so linear overhead
  - Theorem 10 proof (admissible): correctness via careful case analysis on attack variables
  - Theorem 12/13 proofs (complete): adds "defended" variables, 11k+2 still linear
  - Theorem 15 proof (preferred): uses QBF with starred variables, correctness via maximality argument
  - Lemma 27 (p.29): Meta result on DNF matrices — for QBF with inner-most ∀ quantifier, can construct model-preserving DNF matrix with dcw(φ') ≤ 2·dcw(Q(ψ))

## Pages 30-32: Still need to read (remaining proofs)

## Summary for Implementation
The paper's practical value for propstore is the **simple SAT encoding formulas (1)-(9) for stable/admissible** which don't require the clique-width machinery at all. The clique-width analysis proves these encodings are structurally efficient, but the encodings themselves are straightforward Boolean formulas over argument variables. For preferred extensions, the iterative CEGAR approach (not in this paper, but referenced) is more practical than the QBF encoding.
