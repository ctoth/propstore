# Paper Processing: Cayrol 2014 - Change in Abstract Argumentation Frameworks

**Date:** 2026-03-24

## GOAL
Process Cayrol, Dupin de Saint-Cyr & Lagasquie-Schiex (2014) "Change in Abstract Argumentation Frameworks: Adding an Argument" (JAIR 2014, DOI 10.1613/jair.2965) through the paper-process pipeline.

## STATUS
- [x] Step 1: Paper retrieved (arxiv 1401.3838, 334KB PDF, 36 pages)
- [x] Step 2: All 36 pages read
- [x] Step 3: notes.md written
- [x] Step 4: description.md written
- [x] Step 5: abstract.md written
- [x] Step 6: citations.md written
- [ ] Step 7: Reconcile
- [ ] Step 8: Update index.md
- [ ] Step 9: Extract claims

## FILES
- papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/paper.pdf
- papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/metadata.json
- papers/Cayrol_2014_ChangeAbstractArgumentationFrameworks/pngs/ (36 page images)

## KEY FINDINGS SO FAR (pages 0-11)

### Paper Structure
- Section 1: Introduction
- Section 2: Basic Concepts in Argumentation Frameworks (Dung AF definitions)
- Section 3: Change in Argumentation (the core contribution)
  - 3.1: Definition of change operations
  - 3.2: Structural properties (decisive, restrictive, questioning, destructive, expansive, conservative, altering)
  - 3.3: Status-based properties (monotony)

### Core Definitions
- **Definition 7 (Change operation):** Four types of change on AF (A,R):
  1. Adding one interaction between existing args
  2. Removing one existing interaction
  3. Adding one new argument Z (not in A) with interactions Z_r
  4. Removing one argument Z in A with all its interactions

- **Structural properties** (Definition 8-14): decisive, restrictive, questioning, destructive, expansive, conservative, altering - all based on comparing extension sets before/after change

- **Table 2** (p.11): Summarizes which structural properties can co-occur for different extension set configurations

- **Status-based properties** (Section 3.3): Monotony - arguments accepted before change remain accepted after

### Key Notation
- G = attack graph, G' = modified attack graph
- E = set of extensions of G, E' = set of extensions of G'
- Change operation: G -> G' with Z and Z_r (interactions)

## NEXT
Continue reading pages 12-35, then write all output files.
