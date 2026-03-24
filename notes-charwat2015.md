# Notes: Processing Charwat et al. 2015

## GOAL
Process "Methods for solving reasoning problems in abstract argumentation - a survey" (Charwat, Dvorak, Gaggl, Wallner, Woltran 2015) into the propstore collection.

## STATUS
- [x] Paper retrieved via fetch_paper.py (DOI: 10.1016/j.artint.2014.11.008)
- [x] PDF downloaded from sci-hub (1.2MB)
- [x] Directory: papers/Charwat_2015_MethodsSolvingReasoningProblems
- [x] metadata.json present
- [x] Converted to 36 page images in pngs/
- [ ] Read all 36 pages
- [ ] Write notes.md
- [ ] Write description.md
- [ ] Write abstract.md
- [ ] Write citations.md
- [ ] Run reconcile skill
- [ ] Update index.md
- [ ] Extract claims
- [ ] Write batch report

## OBSERVATIONS
- 36 pages total, under 50 so direct read (no chunking needed)
- Paper is a survey of computational methods for abstract argumentation
- Highly relevant to the aspic-argumentation branch work

## READING PROGRESS
Pages read: 0-23 (of 0-35)
Pages remaining: 24-35

## KEY FINDINGS SO FAR

### Structure
- Section 1: Introduction (p.0-1)
- Section 2: Background - Dung AFs, semantics, complexity (p.2-5)
- Section 3: Reduction-based approaches (p.5-10)
  - 3.1 Propositional logic (SAT-based encodings)
  - 3.2 CSP reductions
  - 3.3 ASP (answer set programming)
  - 3.4 Labelling-based approaches
- Section 4: Direct approaches (p.15-23)
  - 4.1 Labelling-based algorithms (Algorithms 3, 4)
  - 4.2 Dialogue games / game-theoretic
  - 4.3 Dynamic programming via tree decompositions

### Key Technical Content
- Definition 1 (p.2): AF = (A, R) where A = arguments, R = attack relation
- Definition 2 (p.3): Characteristic function F_F(S) = {a in A | a is defended by S}
- Definition 3 (p.3): Complete labelling with in/out/undec labels
- Definition 4 (p.4): Complexity classes for reasoning problems (Cred, Skept, Enum, etc.)
- Table 1 (p.5): Computational complexity of reasoning (NP-complete for preferred credulous, Pi2P-complete for preferred skeptical, etc.)

### Approaches Surveyed
1. **SAT-based**: Encode AF semantics as propositional formulas. ConArg system by Bistarelli & Santini.
2. **CSP-based**: Encode as constraint satisfaction. Not widely used, most solvers don't support subset maximization.
3. **ASP-based**: Two main approaches - (a) monolithic encoding using saturation, (b) meta-asp approach by ASPARTIX. ASP naturally handles enumeration.
4. **Labelling-based**: Three-valued labelling (in/out/undec). Algorithms 3 and 4 for preferred extensions.
5. **Dialogue games**: Game-theoretic proponent/opponent for credulous acceptance.
6. **Dynamic programming**: Tree decomposition of AF graph, bottom-up computation along tree. Handles treewidth-bounded instances efficiently.

### Algorithms
- Algorithm 1: SatPref (p.9) - SAT-based preferred extension enumeration
- Algorithm 2: EnumPref (p.10) - enhanced preferred enumeration
- Algorithm 3: pref-lab-? (p.17) - labelling-based preferred with candidate labelling
- Algorithm 4: pref-lab-? (p.17) - variant
- Algorithm 5: cred-prob (p.18) - credulous acceptance via labelling
- Dynamic programming algorithms using tree decompositions (p.20-23)

### Systems/Implementations Mentioned
- ASPARTIX (ASP-based)
- ConArg (SAT/CSP-based)
- CoQuiAAS (CSP-based)
- CEGARTIX (CEGAR-based)
- Prefsat, ArgSemSAT (SAT-based)
- dynPARTIX (dynamic programming)

### Complexity Results (Table 1, p.5)
- Conflict-free: verification P, credulous in NP (trivially), enumeration polynomial delay
- Admissible: credulous NP-complete, enumeration polynomial delay
- Complete: credulous NP-complete
- Grounded: all in P (unique extension)
- Preferred: credulous NP-complete, skeptical coNP-complete (for Π₂ᵖ)
- Stable: credulous NP-complete, skeptical coNP-complete
- Semi-stable: credulous Σ₂ᵖ-complete, skeptical Π₂ᵖ-complete

## PAGES 24-35 FINDINGS

### Section 4.3 continued (p.24-25): Dynamic programming
- Tree decomposition approach for computing admissible sets
- Colorings represent argument status (attack/defend/not-selected)
- Bottom-up traversal of nice tree decomposition
- Counting extensions: sufficient to count colorings at root node
- For credulous acceptance with preferred semantics: more complex, need to track partial preferred extensions

### Section 4.4 (p.25): Problems for further methods
- Ideal semantics can be computed by first finding preferred extensions then intersecting
- Stage semantics related to stable but using range instead of attack set
- Splitting approach: decompose AF into sub-frameworks F1, F2; compute independently when possible

### Section 5 (p.25-26): System comparison
- Table 2 (p.25): Systems overview - platform, language, GUI, command line, library
- Table 3 (p.26): Supported semantics and reasoning modes per system
- Systems compared: ArgSemSAT, ASPARTIX, CEGARTIX, CoQuiAAS, ConArg, Dung-O-Matic, dynPARTIX, DIAMOND, Prolog implementations
- Table 4 (p.26): Additional features (import/export, visualization, etc.)

### Section 5.1-5.9 (p.26-28): Individual system descriptions
- **ArgSemSAT**: High-performance SAT-based, handles multiple SAT solvers, won ICCMA 2015
- **ASPARTIX**: ASP-based via DLV/clingo, extensible, reference system
- **Cegartix**: CEGAR approach for preferred/semi-stable, uses Minisat
- **ConArg**: Java constraint-based, GUI, pedagogical tool
- **CoQuiAAS**: C++ compilation-based, compiles AF to CNF, fast
- **Dung-O-Matic**: Java GUI tool, dialogue games, pedagogical
- **dynPARTIX**: Dynamic programming on tree decompositions, htd library
- **Prolog implementations**: SWI-Prolog based

### Section 6 (p.28-29): Summary and future directions
- ICCMA competition (first in 2015) as benchmark venue
- Instantiation-based approaches (ASPIC+, ABA) as future direction
- Dynamic AFs (adding/removing arguments) as open problem
- Further semantics (stage, resolution-based grounded) need more solver support
- Integration of "abstract" solvers into structured argumentation systems

### Section 6.2 (p.29): Further remarks
- Splitting frameworks can improve performance
- Connection to belief revision and dynamics of AFs
- References [153-156] on expanding/changing AFs

### References (p.31-35): 156 references total

## ALL PAGES READ - OUTPUT FILES WRITTEN
- [x] notes.md written
- [x] description.md written
- [x] abstract.md written
- [x] citations.md written

## RECONCILIATION IN PROGRESS
Collection has ~40 paper directories. Key papers likely in collection that Charwat cites:
- Dung_1995_AcceptabilityArguments (ref [1])
- Modgil_2014_ASPICFrameworkStructuredArgumentation (ref [7])
- Bondarenko_1997 (ref [8])
- Dvorak_2012_FixedParameterTractableAlgorithms (ref [21])
- Cayrol_2005 (ref [23])
- Caminada_2007 (related)

Conceptual links to check:
- Järvisalo_2025_ICCMA2023 (ICCMA competition successor)
- Fichte_2021_Decomposition (tree decomposition approach)
- Mahmood_2025_Structure-Aware (encodings)
- Tang_2025_Encoding (propositional encodings)
- Niskanen_2020_Toksia (solver system)

## COMPLETED
1. [x] Write notes.md
2. [x] Write description.md
3. [x] Write abstract.md
4. [x] Write citations.md
5. [x] Run reconcile skill (7 forward refs, 5 reverse refs, 2 leads moved)
6. [x] Update index.md
7. [x] Extract claims (23 claims created, 5 concepts registered)
8. [x] Write batch report
