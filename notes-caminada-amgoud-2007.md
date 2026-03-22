# Notes: Caminada & Amgoud 2007 - On the evaluation of argumentation formalisms

## Session: 2026-03-21

### GOAL
Retrieve and process paper through paper-process pipeline (retrieve, read, notes, claims).

### DONE
- Retrieved PDF from Amgoud's IRIT page (354KB, 40 pages)
- Converted to 40 page images
- Read ALL 40 pages (pages 0-39)

### FULL PAPER SUMMARY

**Paper structure:**
1. Introduction (p2-3)
2. Argumentation Process (p3-9) - formal definitions of ASPIC-like system
3. Some Problematic Examples (p9-12) - counterexamples showing issues with existing formalisms
4. Rationality Postulates (p13-15) - three postulates: closure, direct consistency, indirect consistency
5. Possible Solutions (p16-24) - two closure operators (Cl_pp and Cl_tp) plus restricted rebutting
6. Summary and Discussion (p23-24)
7. References (p25-29)
8. Appendix with proofs (p29-40)

**Core contribution:** Defines three rationality postulates for evaluating rule-based argumentation systems:
- Postulate 1 (Closure): Output closed under strict rules
- Postulate 2 (Direct Consistency): Each extension's conclusions are consistent
- Postulate 3 (Indirect Consistency): Closure of each extension's conclusions under strict rules is consistent

**Shows existing systems violate these:** ASPIC, Prakken & Sartor, Garcia & Simari all produce unintuitive results.

**Two solutions proposed:**
1. Cl_pp (propositional closure) - converts strict rules to material implications, computes classical propositional closure, converts back to rules. Works under grounded semantics only.
2. Cl_tp (transposition closure) - closes strict rules under transposition (contrapositive). Combined with restricted rebutting, satisfies all three postulates under ALL Dung semantics.

**Key theorems:**
- Theorem 1: Cl_pp + grounded semantics => all 3 postulates satisfied
- Theorem 2: Cl_tp + restricted rebutting => all 3 postulates under grounded extension
- Theorem 3: Cl_tp + restricted rebutting => closure under all Dung semantics
- Theorem 4: Cl_tp + restricted rebutting => direct and indirect consistency under all Dung semantics

**Table 2 summary (p22):**
| Rebutting type | Direct consistency | Indirect consistency | Closure |
|---|---|---|---|
| Rebut | Under any semantics | Under grounded ext | Under grounded ext |
| Restricted Rebut | Under any semantics | Under any semantics | Under any semantics |

**Discussion highlights (p23-24):**
- Rationality postulates apply not just to ASPIC but to ANY argumentation formalism using Dung semantics
- Transposition closure relates to Clark completion for logic programs
- Computational complexity: transposition generates at most n * 4^n transpositions for n strict rules (but typically much less)
- For query-based approaches (grounded/preferred), closure doesn't cause problems since you only compute what's needed

### CURRENT
- DONE: notes.md, description.md, abstract.md, citations.md all written
- DOING: Reconcile skill - forward/reverse cross-referencing
  - Forward: Dung_1995, Pollock_1987, Cayrol_2005 in collection; Prakken & Sartor 1997 and Garcia & Simari 2004 NOT in collection
  - Reverse: 5 collection papers cite Caminada: Modgil 2014, Modgil 2018, Odekerken 2023, Prakken 2010, Prakken 2012
  - Also found: Prakken_2010 paper not in index.md (may be in papers/ but not indexed)
- NEXT: Check citing papers for leads/cross-refs, write cross-reference section, then index.md update, then extract-claims
