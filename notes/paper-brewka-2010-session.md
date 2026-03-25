# Brewka & Woltran 2010 — Paper Reader Session

**Date:** 2026-03-24
**GOAL:** Read and extract all artifacts for Brewka_2010_AbstractDialecticalFrameworks

## State
- All 10 page images read successfully
- metadata.json exists and is complete
- No notes.md, abstract.md, description.md, citations.md exist yet
- Need to write all four artifacts, then reconcile and update index.md

## Key Observations from Reading

### Core Idea
- Abstract Dialectical Frameworks (ADFs) generalize Dung AFs
- Each node has an **acceptance condition** (arbitrary propositional formula over parent nodes)
- Dung AFs are special case where acceptance condition = conjunction of negations of attackers
- Links can represent attack, support, or complex dependencies

### Definitions
- ADF D = (S, L, C) where S=statements, L=links, C=acceptance conditions
- Acceptance condition C_s is a propositional formula over par(s) = parents of s
- Three-valued interpretations: t (true), f (false), u (undecided)
- Consensus operator Gamma_D on three-valued interpretations
- Models, two-valued models, grounded model (least fixpoint of Gamma_D)

### Key Semantics
- Grounded: least fixpoint of Gamma_D operator
- Complete: fixpoints of Gamma_D
- Preferred: maximal complete (information-ordering)
- Stable: two-valued model M where the "reduced ADF" D^M has M as grounded extension
- Bipolar ADFs (BADFs): each link is either supporting or attacking (not both)
- Stable and preferred semantics need bipolar restriction

### Weighted ADFs
- Acceptance conditions represented via weights on links
- Positive weight = support, negative = attack
- Threshold parameter for acceptance
- Can model legal proof standards (preponderance, clear and convincing, beyond reasonable doubt)

### Complexity
- Grounded model computation: polynomial (for fixed formula size)
- Credulous/skeptical reasoning for preferred/stable: in complexity hierarchy

### Connections to Logic Programming
- ADFs generalize normal logic programs
- Stable models of ADF correspond to answer sets
- Well-founded model corresponds to grounded semantics

## Progress
- [x] notes.md written
- [x] abstract.md written
- [x] description.md written
- [x] citations.md written
- [x] Committed initial artifacts
- [x] index.md updated with entry
- [x] Cross-references added to Brewka 2010 notes (Cites + Cited by sections)
- [ ] Backward annotations to cited papers (Dung 1995, Cayrol 2005, Simari 1992, Caminada 2006, Prakken 2010)
- [ ] Commit reconciliation changes

## Reconciliation Findings
Papers in repo that cite Brewka 2010: Gabbay 2012, Thimm 2012, Hunter 2017, Modgil 2018, Cyras 2021, Charwat 2015, Odekerken 2023, Tang 2025, Doutre 2018
Papers Brewka 2010 cites (in repo): Dung 1995, Cayrol 2005, Bench-Capon 2003, Caminada 2006, Simari 1992, Vreeswijk 1997, Prakken 2010
- Bench-Capon 2003 and Vreeswijk 1997 have no notes.md -- skip backward annotation
- Other 5 cited papers have notes.md, need backward annotation added
- Existing cross-ref sections vary in format -- some use ### Cited by, some use bullet lists at end
