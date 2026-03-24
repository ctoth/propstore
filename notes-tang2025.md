# Notes: Tang 2025 - Encoding Argumentation Frameworks to Propositional Logic Systems

## GOAL
Process paper https://arxiv.org/abs/2503.07351 through full paper-process pipeline.

## STATUS
- Retrieval: DONE - papers/Tang_2025_EncodingArgumentationFrameworksPropositional/
- PDF to images: DONE - 37 pages
- Reading: IN PROGRESS - read pages 0-9

## Key Findings So Far (pages 0-9)

### Paper Identity
- Title: "Encoding argumentation frameworks to propositional logic systems"
- Authors: Shuai Tang, Jiachao Wu, Ning Zhou
- Affiliation: Shandong Normal University, Jinan, China
- Year: 2025 (arxiv:2503.07351v2, 18 Aug 2025)
- Keywords: argumentation framework, general encoding methodology, propositional logic system, triangular norm

### Abstract Summary
Generalizes encoding of AFs beyond classical 2-valued PL2 to:
- 3-valued propositional logic (PL3) using Kleene's and Lukasiewicz's systems
- Fuzzy propositional logic (PL[0,1])
Two encodings: normal encoding (ec1) and regular encoding (ec2)
Establishes model relationships between Dung's semantics and encoded semantics.
Proposes new fuzzy encoded semantics (Eq^L) with Lukasiewicz PL[0,1].

### Section 2: Preliminaries (pp.3-9)
- Def 1: AF = (A, R) standard Dung framework
- Def 2-3: Universe of AFs, finitary
- Def 4: Extension-based semantics as function ES: AF -> 2^(2^A)
- Def 5-7: Labellings (numerical, 2-valued, 3-valued, complete labelling)
- Def 7: Complete labelling with lab: A -> {1, 0, 1/2}
- Def 8: PLS = (L, S) - propositional logic system with language and structure
- Def 9-10: Assignments and models in PLS
- Def 11-12: Negation, t-norms (Godel TG, Lukasiewicz TL, Product TP)
- Def 13-14: Fuzzy implication, residual implication
- Key t-norms: Godel min{x,y}, Lukasiewicz max{0,x+y-1}, Product x*y
- Section 2.3: Model checking approach (Besnard/Doutre [29])
  - Encodes conflict-free, stable, admissible, complete as PL2 formulas
- Section 2.4: Real equational approach (Gabbay [12])
  - Def 15-17: Real equational functions, equational argumentation networks
  - Eq_inverse^R and Eq_max^R specific equational systems

### Section 3: General Encoding Methodology (p.10)
- Def 18: Numerical labelling types (2-valued, 3-valued, [0,1]-valued)
- Def 19: Binarization T2: LABnum -> LAB2
- Def 20: Ternarization Tcom: LABnum -> LAB3
- Def 21: Encoding ec: AF -> F_PL (maps AF to formulas)
- Two key encodings: ec1 (normal) and ec2 (regular) - definitions coming

## Section 3: General Encoding Methodology (pp.10-11)
- Def 21: Encoding ec: AF -> F_PL
- **Normal encoding ec1**: ec1(AF) = AND_{a in A} (a <-> AND_{(b,a) in R} not-b)
  - Corresponds to stable semantics formula from Besnard/Doutre
- **Regular encoding ec2**: ec2(AF) = AND_{a in A} ((a -> AND_{(b,a) in R} not-b) AND (a <-> AND_{(b,a) in R} OR_{(c,b) in R} c))
  - Corresponds to complete semantics formula
- Def 22-23: Assignments and models in encoded framework
- Def 24-25: Encoded semantics, fuzzy normal/continuous/strict encoded semantics
- Def 26-27: Translating (models of tr(AF) in PLS = models of AF under semantics), translatable semantics

## Section 4: Encoding AFs to PL3s (pp.12-17)
- 4.1: Normal encoding ec1 to PL3
  - **Theorem 1**: Assignment is model of AF under stable semantics iff model of ec1(AF) in PL3^K
  - **Corollary 1**: Stable semantics is translatable by ec1 and PL3^K
  - **Theorem 2**: Assignment is model of AF under complete semantics iff model of ec1(AF) in PL3^L
  - **Corollary 2**: Complete semantics is translatable by ec1 and PL3^L
  - Key insight: ec1 alone suffices for complete semantics with the right PLS (Lukasiewicz PL3)
- 4.2: Regular encoding ec2 to PL3
  - **Theorem 3**: Model of AF under complete => T2 is model of ec2(AF) in PL3^K
  - **Theorem 4**: Model of ec2(AF) in PL3^K => Tcom is model under complete semantics
  - **Theorem 5**: Each model of AF under complete semantics is model of ec2(AF) in PL3^L
  - **Theorem 6**: If model of ec2(AF) in PL3^L, then Tcom is model under complete semantics
  - Example 1: Shows ec2(AF) model in PL3^L may NOT be a model under complete semantics

## Section 5: Encoding AFs to PL[0,1]s (pp.18-20)
- 5.1: Encoding AFs to general PL[0,1]s
  - 5.1.1: Fuzzy normal encoded semantics
    - **Theorem 7**: Assignment is model of ec1(AF) in PL[0,1] iff solution of equational system Eq^{ec1}
    - Eq^{ec1}: ||a|| = N(||b1||) * N(||b2||) * ... * N(||bk||) where b1..bk attack a
    - Def 28-29: Encoded equational system, encoded equational function h^{ec1}, decreasing monotonicity
    - **Theorem 8**: h^{ec1} satisfies decreasing monotonicity
    - **Remark 4**: Real equational system Eq^R may NOT satisfy decreasing monotonicity (distinguishing feature)
    - **Theorem 9**: h^{ec1} satisfies boundary conditions and symmetry
  - 5.1.2: Continuous fuzzy normal encoded semantics (started, reading continues)

## Section 5 continued (pp.20-29)

### 5.1.2 Continuous fuzzy normal encoded semantics (pp.20-22)
- Def 30-31: Continuous/strict encoded equational systems
- **Theorem 10**: Model of ec1(AF) in PL*[0,1] iff solution of Eq*_{ec1}
- **Theorem 11**: Model of ec1(AF) in PL**[0,1] iff solution of Eq**_{ec1}
- **Theorem 12**: Each continuous encoded equational system Eq*_{ec1} is a Gabbay real equational system
- **Corollary 3-5**: Strict systems also real equational; models in PL*[0,1] and PL**[0,1] are real equational extensions
- Example 2: Eq^R_geometrical cannot be derived from ec1(AF) model in any PL*[0,1] (because the induced t-norm is not actually a t-norm)

### 5.2 Encoding AFs to specific PL[0,1]s (pp.23-29)
- 5.2.1: Encoding to PL^G[0,1] and PL^P[0,1]
  - **Theorem 13**: Model of AF under Eq^R_max iff model of ec1(AF) in PL^G[0,1]
  - **Corollary 6**: Eq^R_max translatable by ec1 and PL^G[0,1] (denoted Eq^G)
  - **Theorem 14**: Model of AF under Eq^R_inverse iff model of ec1(AF) in PL^P[0,1]
  - **Corollary 7**: Eq^R_inverse translatable by ec1 and PL^P[0,1] (denoted Eq^P)
- 5.2.2: Encoding to PL^L[0,1] - **NEW CONTRIBUTION**
  - Proposes Eq^L: ||a|| = {1 if no attackers, 0 if sum of attacker values >= 1, 1-sum(||bi||) if sum < 1}
  - **Theorem 15**: Model of ec1(AF) in PL^L[0,1] iff solution of Eq^L
  - **Corollary 8**: Eq^L is a fuzzy normal encoded equational system associated with PL^L[0,1]
  - **Corollary 9**: Eq^L is a real equational system

### 5.3 Relationships between complete semantics and fuzzy encoded semantics (pp.27-29)
- Uses 1/2-idempotent t-norms (Def 32) and zero-divisor-free t-norms
- **Theorem 16**: For encoded semantics Eq^{ec1}_circled-times with idempotent t-norm, model => Tcom is model under complete semantics
- **Theorem 17**: For Eq^{ec1}_circled-dot with 1/2-idempotent t-norm, model under complete semantics => model under Eq^{ec1}_circled-dot
- **Corollary 10**: Set of complete models = set of Tcom of models under Eq^{ec1}_circled-dot (for 1/2-idempotent zero-divisor-free t-norm with standard negation and R-implication)

## Section 6: Conclusion (pp.29-30)
- Advances encoding methodology by exploring AF-PLS connections
- Key results: stable <==> ec1+PL3^K; complete <==> ec1+PL3^L
- For fuzzy: Eq^R_max <==> ec1+PL^G; Eq^R_inverse <==> ec1+PL^P
- New: Eq^L proposed via ec1+PL^L (Lukasiewicz fuzzy logic)
- Future: higher-level AFs, bipolar AFs, encoding with support relations

## Appendix A: Proofs of model equivalence for complete semantics (pp.30-32)
- Theorem 18: ec2(AF) model in PL2 => model under complete semantics
- Theorem 19: Model under complete semantics => binarized is model of ec2(AF) in PL2

## References (pp.32-37)
- 57 references total
- Key: [1] Dung 1995, [12] Gabbay 2012 equational approach, [29] Besnard/Doutre model checking

## ALL PAGES READ - OUTPUT FILES WRITTEN

## DONE
- notes.md written
- description.md written
- abstract.md written
- citations.md written

## Reconciliation Findings
- Forward refs in collection: Dung_1995, Cayrol_2005
- No reverse citations found (Tang 2025 is new, no collection papers cite it)
- Conceptual links:
  - Mahmood_2025 (Strong) - also encodes AFs to propositional formulas (SAT), different purpose (complexity) but same Besnard-Doutre starting point
  - Niskanen_2020 (Strong) - SAT-based AF reasoner, uses propositional encodings computationally
  - Dung_1995 (Strong) - foundational paper whose semantics Tang encodes
  - Caminada_2007 (Moderate) - evaluation of argumentation formalisms

## COMPLETED
- Cross-references written in Tang notes.md
- Backward annotations added to Mahmood, Niskanen, Dung
- index.md updated
- 8 new concepts registered (propositional_logic_system, normal_encoding, regular_encoding, t_norm, encoded_semantics, equational_semantics, translatable_semantics, complete_labelling)
- 19 claims extracted in claims.yaml (2 equation, 10 observation, 1 mechanism, 1 comparison, 3 limitation, 2 other observation)
