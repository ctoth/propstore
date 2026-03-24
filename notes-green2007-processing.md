# Processing: Green 2007 - Provenance Semirings

## GOAL
Process paper through full paper-process pipeline: retrieve, read, extract claims, report.

## DONE
- Retrieved PDF via sci-hub (325KB, 10 pages)
- Paper directory: papers/Green_2007_ProvenanceSemirings/
- Page images created (page-000 through page-009)
- Read ALL 10 pages

## Key Findings (all pages)

### Paper Overview
- Authors: Todd J. Green, Grigoris Karvounarakis, Val Tannen (UPenn)
- Venue: PODS 2007
- DOI: 10.1145/1265530.1265535

### Core Contribution
- Algebraic approach to data provenance using semirings
- Unifies lineage, why-provenance, and provenance polynomials
- N[X] (provenance polynomials) is the most general — all others are homomorphic images
- Extends to Datalog via omega-continuous semirings and formal power series

### Key Concepts
- **K-relations**: tuples map to elements of semiring K, finite support
- **Positive algebra ops**: union→sum, join→product, projection→sum, selection→0/1
- **N[X]**: free commutative semiring = provenance polynomials (most informative)
- **Lineage** (Lin(X)): Boolean expressions
- **Why-provenance** (Why(X)): sets of sets
- **Bag semantics** (N): multiplicity counting
- Proposition 3.5: semantics preserved by semiring homomorphisms

### Datalog Extension (Sections 6-8)
- omega-continuous semirings for fixpoint semantics
- Formal power series N_inf[[X]] for recursive queries
- Algorithm "All Trees": computes provenance for Datalog derivations
- Algorithm "Absorptive Monomial Coefficient": handles idempotent semirings
- Section 8: incomplete/probabilistic databases as application

### Section 9: Query Containment
- Containment for conjunctive queries with provenance
- Distributive lattice K: containment iff K-containment for each valuation

### Relevance to propstore
HIGH — provenance polynomials track how source claims combine into derived conclusions.
The semiring homomorphism property means compute once in N[X], project to any coarser notion.

## NEXT
- Write notes.md, description.md, abstract.md, citations.md
- Update index.md
- Run reconcile, extract claims
- Write report
