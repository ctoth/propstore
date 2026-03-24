# Re-read Session 2026-03-22 (argumentation papers batch)

## Goal
Re-read 6 papers from page images, rewrite notes.md with (p.N) citations on every finding, add "Arguments Against Prior Work" and "Design Rationale" sections if missing.

## Papers to process (in order) - THIS AGENT'S BATCH
1. Clark_2014_Micropublications - ALL 33 pages read. Adding missing sections.
2. Modgil_2014_ASPICFrameworkStructuredArgumentation - TODO
3. Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation - TODO
4. Walton_2015_ClassificationSystemArgumentationSchemes - TODO
5. Prakken_2012_AppreciationJohnPollock'sWork - TODO
6. Greenberg_2009_CitationDistortions - TODO

## Clark 2014 - COMPLETE READ
- 33 pages (000-032), all read
- Existing notes very thorough with page citations
- Missing sections: Arguments Against Prior Work, Design Rationale
- Key arguments against prior work: SWAN/Nanopub/BEL lack claim networks + empirical evidence (p.3), linear docs from 1665 can't support machine verification (p.5), citation distortion undetectable (p.4,27)
- Design rationale: Toulmin-Verheij grounding (p.5,9), complexity spectrum (p.10,13), backward-compatible (p.3,30), avoids ontological status (p.20), holotype normalization (p.19-20)

## Clark 2014 - DONE
- Added "Arguments Against Prior Work" (6 items) and "Design Rationale" (8 items) sections

## Modgil 2014 - IN PROGRESS
- 34 pages total, read pages 0-5 so far
- Page 1 is blank (T&F terms page)
- Existing notes are very thorough with page citations
- Missing sections: Arguments Against Prior Work, Design Rationale
- Arguments against prior work found so far:
  - p.31 (page-002): Dung's abstract AFs treat arguments as atomic with no internal structure
  - p.31-32: Real argumentation requires structured arguments with different attack types
  - p.32 (page-003): Earlier structured argumentation approaches lack rationality postulates (consistency, closure)
  - p.32: Caminada & Amgoud 2007 showed existing formalisms violate rationality postulates
  - p.33 (page-003): Need to distinguish strict vs defeasible rules, necessary vs ordinary premises
  - p.33-34 (page-003/004): Three types of attack needed (undermining, rebutting, undercutting) - prior work conflated these
  - p.34 (page-004): Pollock's system lacked explicit preferences; Vreeswijk lacked undermining
  - p.34 (page-004): Whether deductive inference step itself is an attack point is debatable
- Design rationale found so far:
  - p.31: Two key ideas - (1) conflicts resolved via preferences, (2) some premises only presumptive
  - p.32: Bridge between abstract and structured argumentation
  - p.33-34: Three distinct attack types each with different preference behavior
  - p.34: Undercutting always succeeds regardless of preferences (design choice)
  - p.35: Separation of argumentation system (rules) from knowledge base (premises)
- Read pages 6-23 now (pp.37-52)
- Additional arguments against prior work:
  - p.39-40: Preferences needed to resolve which attacks succeed as defeats; prior work lacked this
  - p.44: Last-link vs weakest-link debate - context-dependent, no single right answer
  - p.45-46: Caminada & Amgoud 2007 showed consistency violations without transposition closure
  - p.47-48: Classical logic approaches (Besnard & Hunter) lack defeasible rules and undercutting
  - p.48: "Others (mainly logicians) take a more standard logic approach" - domain-specific defeasible rules vs logic-based
  - p.50: Pollock's formalized defeasible rules lack meta-variables; ASPIC+ generalizes with schemes
  - p.50-51: Walton argument schemes need formal grounding that prior scheme theory didn't provide
- Additional design rationale:
  - p.39-40: Undercutting always defeats regardless of preferences (principled choice, see Modgil & Prakken 2013)
  - p.42-44: Two ordering principles (last-link, weakest-link) for different domains (legal vs epistemic)
  - p.45-46: Transposition closure requirement ensures consistency
  - p.46-47: Two approaches to classical logic (simple materialized implications vs sophisticated full logic)
  - p.50-51: Argument schemes as defeasible rules with critical questions mapping to three attack types
  - p.53: Connection to Toulmin model (data=premises, warrant=defeasible rule, backing=support, rebuttal=attack)
- Still need pages 24-33

## Modgil 2014 - DONE
- All 34 pages read (pages 0-33)
- Added "Arguments Against Prior Work" (8 items) and "Design Rationale" (9 items) sections
- Section 6 (pp.59-60) key for relationships: Dung, ABA, Besnard & Hunter, Carneades, Pollock, Vreeswijk

## Cayrol 2005 - ALL 12 PAGES READ
- Arguments against prior work found:
  - p.378: Most existing frameworks only have one kind of interaction (defeat)
  - p.378: Support between arguments exists in practice but is not modeled
  - p.379: Bipolar preferences in cognitive psychology suggest two independent evaluations (positive/negative)
  - p.381: In Dung's framework, defence is the only implicit form of support; real support is independent
  - p.381: Classical frameworks conflate support-via-defence with direct support
  - p.384: Conflict-free in Dung's sense is insufficient for bipolarity - need internal + external coherence
  - p.385: Stable extensions can be unsafe - they may simultaneously defeat and support the same argument
- Design rationale found:
  - p.378: Support and defeat as independent, first-class relations
  - p.382: Abstract approach - no internal structure, just relations (following Dung's methodology)
  - p.383: Supported defeat and indirect defeat as derived interaction types
  - p.384: Two-level coherence: internal (conflict-free via set-defeat) and external (safe = no defeat+support of same arg)
  - p.385: Safe set captures external coherence; Property 1 bridges safe and conflict-free
  - p.386: Three-level admissibility hierarchy: d-admissible < s-admissible < c-admissible
  - p.386: c-admissible = conflict-free + closed for R_sup + defends elements (strongest requirement)
  - p.387: Restriction to acyclic frameworks for clean existence/uniqueness results
  - p.388: Conclusion emphasizes independent support/defeat as key design choice

## Cayrol 2005 - DONE
- Added "Arguments Against Prior Work" (6 items) and "Design Rationale" (7 items)

## Walton 2015 - IN PROGRESS
- 28 pages total, read pages 0-17 so far (pp.1-17)
- Read all existing notes (324 lines) - thorough with page citations
- Missing sections: Arguments Against Prior Work, Design Rationale
- Arguments against prior work found:
  - p.1-2: Existing classifications fragmented and inconsistent (Kienpointner, Grennan, Walton earlier)
  - p.4: Kienpointner's three-direction classification had inconsistent organizing principles
  - p.4: Grennan's four categories had problematic "overriding common characteristic"
  - p.4: Walton et al. 2008 replaced "overriding" with better categories but still incomplete
  - p.5: Lumer & Dove epistemic approach limited to establishing epistemic states
  - p.5-6: Bex & Reed (2011) classification into inference/conflict/preference useful but different purpose
  - p.6: Rahwan et al. AIF approach is formal but doesn't classify by type
  - p.8: Sub-scheme relationships not captured by flat lists
  - p.9: Six desiderata that prior systems fail to fully satisfy
- Design rationale found:
  - p.1: Hierarchical taxonomy (tree structure) not flat list
  - p.8: Source-dependency as top-level organizing principle
  - p.9: Six explicit desiderata for evaluating classification systems
  - p.8: Sub-scheme inheritance (expert opinion is subspecies of position to know)
  - p.13: Practical vs epistemic reasoning as fundamental division
  - p.15: Hybrid schemes (sunk cost) can bridge categories
  - p.17: Epistemic arguments divided by relationship between generalization, premises, and conclusion
- Still need pages 18-27

## Walton 2015 - DONE
- All 28 pages read, added Arguments Against Prior Work (8 items) + Design Rationale (9 items)

## Prakken 2012 - IN PROGRESS
- 20 pages total, read pages 0-5 so far
- Read all existing notes (293 lines) - thorough with page citations
- Missing sections: Arguments Against Prior Work, Design Rationale
- This is a survey/appreciation paper, so "arguments against prior work" = critiques of Pollock's system
- Key critiques found so far (pp.1-5):
  - p.2: Pollock worked in isolation from mainstream AI argumentation community
  - p.3: Non-monotonic reasoning community didn't appreciate argumentation-based approach
  - p.3: Dung 1995 abstract framework was more influential despite Pollock's earlier work
  - p.4: Pollock's formalism is complex - not easy for outsiders to grasp
- Design rationale of Pollock's system (as identified by Prakken/Horty):
  - p.2: Defeasible reasoning is essential and omnipresent in cognitive life
  - p.4: Inference graphs not trees (subargument sharing)
  - p.4-5: Four defeasible inference rules grounded in epistemology
- Still need pages 6-19

## Prakken 2012 - DONE
- All 20 pages read, added Arguments Against Prior Work (8 items) + Design Rationale (9 items)

## Greenberg 2009 - ALL 14 PAGES READ, writing sections now

## Status
- Writing Greenberg 2009 sections - LAST PAPER

---

## SECOND AGENT BATCH (papers assigned to a different worker)

### Paper 1: Dung 1995 - DONE
- All 37 pages read, added Arguments Against Prior Work (7 items) + Design Rationale (8 items)

### Paper 2: deKleer 1984 - DONE
- Read key pages, added Arguments Against Prior Work (8 items) + Design Rationale (10 items)

### Paper 3: Martins 1988 - DONE
- Read key pages (intro, SWM section, conclusion), added both sections (8+8 items)

### Paper 4: Reiter 1980 - DONE
- Read pages 0-8 + conclusion, added both sections (6+8 items)

### Paper 5: Pollock 1987 - DONE
- Read pages 0-5, added Arguments Against Prior Work (6 items) + Design Rationale (8 items)

### Paper 6: Modgil 2018 - DONE
- Read pages 0-7 + references, added Arguments Against Prior Work (8 items) + Design Rationale (9 items)

### ALL 6 PAPERS COMPLETE
