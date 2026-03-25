# Paper: Besnard & Hunter 2001 — A logic-based theory of deductive arguments

## 2026-03-24

### GOAL
Retrieve and process Besnard & Hunter 2001 "A logic-based theory of deductive arguments" from Artificial Intelligence journal.

### OBSERVATIONS
- search_papers.py hung with zero output after 20+ seconds — likely network or API issue
- Known DOI: 10.1016/S0004-3702(01)00077-5 (Elsevier/AI journal)
- Will try fetch_paper.py directly with DOI

### DONE
- Retrieved PDF via university mirror (fiit.stuba.sk), 33 pages, 244KB
- Paper directory: papers/Besnard_2001_Logic-basedTheoryDeductiveArguments/
- Metadata resolved via Semantic Scholar, DOI: 10.1016/S0004-3702(01)00071-6
- Converted to 33 page images (page-000 to page-032)
- Read pages 0-15 (paper pages 203-218)

### KEY CONTENT OBSERVED SO FAR
- **Definition 3.1 (p.2/205):** Argument = pair <Phi, alpha> where Phi consistent, Phi |- alpha, Phi minimal subset of Delta satisfying (2)
- **Definition 3.3 (p.3/206):** "more conservative" ordering on arguments
- **Theorem 3.5 (p.3/206):** Relationship between conservative ordering and logical implication
- **Theorem 3.6 (p.3/206):** Being more conservative defines pre-ordering; minimal/maximal arguments
- **Theorem 3.7 (p.4/207):** Normal form arguments; finitely many arguments per consequent
- **Definition 3.8 (p.5/208):** Equivalent arguments
- **Section 4 - Defeaters, rebuttals, undercuts (p.6/209):**
  - Definition 4.1: Defeater — <Psi, beta> defeats <Phi, alpha> when beta |- neg(phi1 ^ ... ^ phin) for some phi_i in Phi
  - Definition 4.3: Undercut — special defeater where consequent negates conjunction of support elements
  - Definition 4.5: Rebuttal — defeater where beta <-> neg(alpha) is tautology
  - Theorem 4.6: Every rebuttal is a defeater
  - Theorem 4.7: When alpha v beta is tautology and support elements entail each phi, rebuttal relationship holds
- **Section 5 - Canonical undercuts (p.10-12/213-215):**
  - Definition 5.1: Maximally conservative undercut
  - Definition 5.3: Canonical undercut — maximally conservative undercut using canonical enumeration
  - Theorem 5.8: For each defeater, there exists a canonical undercut that is more conservative
- **Section 6 - Argument trees (p.12-13/215-216):**
  - Definition 6.1: Argument tree — tree of arguments where children are canonical undercuts
  - Theorem 6.5: Argument trees are finite
  - Theorem 6.6: If Delta consistent, all argument trees have exactly one node
- **Section 7 - Duplicates (p.14/217):**
  - Definition 7.1: Duplicate undercuts
  - Theorem 7.1: Systematic generation of duplicates from maximally conservative undercuts

### STUCK
- Nothing blocked, continuing to read remaining pages (16-32)

### NEXT
- Read pages 16-32
- Write notes.md, abstract.md, description.md, citations.md
- Run reconcile, update index.md
- Extract claims
