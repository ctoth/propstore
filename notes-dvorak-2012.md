# Notes: Dvorak 2012 - Fixed-Parameter Tractable Algorithms for Abstract Argumentation

## GOAL
Process paper through paper-process pipeline: retrieve, read, extract claims, write all outputs.

## DONE
- Retrieval: PDF downloaded via Sci-Hub (correct DOI: 10.1016/j.artint.2012.03.005, NOT 10.1016/j.artint.2012.07.002 as user provided)
- Page images: 37 pages converted to PNGs
- Read pages 0-31 (32 of 37 pages read)

## Key Findings So Far

### Paper Structure
- p.0: Title page, abstract. Authors: Wolfgang Dvorak, Reinhard Pichler, Stefan Woltran (TU Wien)
- p.1: Introduction - motivation for FPT algorithms for abstract argumentation
- p.2-3: Background on AFs, extensions (admissible, complete, preferred, stable, grounded, ideal)
- p.3-4: Tree-width background, directed graph parameters

### Core Contributions
1. **Negative results** (hardness): CA is NP-hard even for AFs of bounded cycle-rank (p.5-6), SA is coNP-hard even for bounded cycle-rank (p.6-7). This means cycle-rank is NOT suitable for FPT. *(p.5-7)*

2. **Hardness propagation**: Relations between directed graph measures: cycle-rank -> directed path-width -> {DAG-width, Kelly-width} -> directed tree-width. CA is NP-hard for directed path-width 1, DAG-width 2, Kelly-width 2, directed tree-width 1. SA is coNP-hard for the same parameters. *(p.10-12)*

3. **Positive results via tree-width of undirected graph**: Dynamic programming algorithm on tree decompositions for deciding credulous/skeptical acceptance under admissible, complete, preferred, stable, grounded, ideal semantics. *(p.7-8, 13-32)*

### Key Technical Details

**The meta-labelling approach** (p.7-8):
- 3-valued labelling: each argument gets label in {in, out, def}
- "in" = in the extension, "out" = not in extension and defended against, "def" = defeated (attacked by in-argument)
- A labelling C is valid for AF F=(A,R) if conditions on conflict-freeness and admissibility hold
- Algorithm works bottom-up on tree decomposition

**Definition 14** (p.13-14): X_{>t}-restricted admissible sets for F_{>=t}. For node t in tree decomposition with bag X_t, characterizes admissible sets restricted to arguments seen so far.

**Colorings** (p.14-15): Each argument labeled {in, out, def} plus a set Gamma tracking which "certificates" (attackers from in-set) are still needed. Valid colorings characterize the admissible extensions.

**Node types in nice tree decomposition** (p.13):
- LEAF, FORGET, INSERT, JOIN nodes
- Each has specific rules for computing valid colorings

**Complexity** (p.20-21):
- Time for each node is O(k * 4^k * |C|) where k = tree-width, |C| = number of colorings
- Number of colorings bounded by 3^k * 2^(k^2) per node
- Overall: exponential in tree-width but polynomial in |A|

**Extensions to other semantics**:
- Stable: add check that all arguments outside extension are attacked (p.20-21)
- Complete: characterize using vpairs (valid pairs) (p.22-24)
- Preferred: use ID-vpairs (inclusion-dominant valid pairs) (p.24-31)
- Grounded, ideal: also handled via tree decompositions

### Definitions to Track
- Definition 1: AF = (A,R) pair *(p.2)*
- Definition 2: Admissible, complete, preferred, stable, grounded extensions *(p.2-3)*
- Definition 5: Tree-width *(p.3)*
- Definition 7: Cycle-rank of directed graph *(p.5)*
- Definition 10: CNF formula -> AF reduction *(p.6)*
- Definition 12: Tree decomposition types (LEAF, FORGET, INSERT, JOIN) *(p.13)*
- Definition 14: X-restricted admissible sets *(p.13-14)*
- Definition 15: Colorings for tree nodes *(p.14-15)*
- Definition 16: Valid colorings *(p.16)*
- Definition 17: Vpairs (valid pairs for complete semantics) *(p.22)*
- Definition 19: ID-vpairs (for preferred semantics) *(p.28-29)*
- Definition 20: EQ-pairs (for ideal semantics) *(p.28-29)*

### Figures
- Fig 1: Tree decomposition of graph (p.4)
- Fig 2-4: AF constructions for hardness proofs (p.6-7)
- Fig 5: Arboreal decomposition example (p.9)
- Fig 6: Hardness propagation diagram: cycle rank -> directed path-width -> DAG-width/Kelly-width -> directed tree-width (p.11)
- Fig 7: Tree decompositions with subtrees/subframeworks (p.13)
- Fig 8: Operations on colorings (p.15-16)
- Fig 9: Computation of vcolorings example (p.17)
- Fig 10: Computation of vpairs example (p.24)
- Fig 11: Computation of ID-vpairs example (p.31)

## DONE (continued)
- All 37 pages read
- notes.md, description.md, abstract.md, citations.md written
- Reconciliation in progress:
  - Forward refs: Dung_1995 in collection, Modgil_2014 in collection. Dunne, Bodlaender, Egly/ASPARTIX NOT in collection.
  - Reverse refs found: Charwat_2015, Fichte_2021, Mahmood_2025, Niskanen_2020, Jarvisalo_2025 all cite Dvorak
  - Mahmood_2025: moved Dvorak from "New Leads" to "Now in Collection", annotated Related Work
  - Charwat_2015: already has Dvorak in "Already in Collection" but describes it as "PhD thesis" (incorrect - it's the AI journal paper, not the PhD thesis which is ref [19]). Need to fix description.
  - Fichte_2021: references Dvorak in Related Work but no Collection Cross-References section yet

## NEXT
- Fix Charwat description of this paper (it's the AI journal paper, not PhD thesis)
- Write Collection Cross-References section in this paper's notes.md
- Update index.md
- Extract claims (Step 4 of paper-process)
- Write report
