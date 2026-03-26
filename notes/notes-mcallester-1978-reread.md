# McAllester 1978 Reread Session

## GOAL
Re-read all 31 pages of McAllester_1978_ThreeValuedTMS, add page citations to notes.md.

## Progress
- Read pages 0-19 (of 0-30)
- Pages 20-30 remain (Appendix I continued, Appendix II data structures, Appendix III code)

## Page Map So Far
- p.1 (page-000): Title page, abstract - MIT AI Memo 473, May 31 1978
- p.2 (page-001): Acknowledgements + Table of Contents
- p.3 (page-002): Introduction - TMS definition, algebraic manipulator example, clause representation intro
- p.4 (page-003): Intro continued - DeMorgan, three values (true/false/unknown), assumptions, appendices overview
- p.5 (page-004): "The Algorithm" - object types (nodes, truth values, terms, clauses), CNF, terms definition, clause semantics, adding clauses and truth values
- p.6 (page-005): SET-TRUTH code, DEDUCE-CHECK code, one-step deductions only
- p.7 (page-006): NP-completeness justification for one-step restriction, "Removing Truth Values" section
- p.8 (page-007): A->B, B->C, C->B example; removal cascade; support well-foundedness
- p.9 (page-008): REMOVE-TRUTH code, "Contradictions" section begins - PSAT=0, contradictions from deductions
- p.10 (page-009): Contradiction example with 3 clauses, clause formation from contradictions
- p.11 (page-010): Figure 1 (specific example) and Figure 2 (general case) of clause formation
- p.12 (page-011): Pulsing behavior discussion, "Default Values and Backtracking" section
- p.13 (page-012): "Clause Values and Hierarchies of Assumptions" - clause validity nodes, assumption hierarchies, min-max distance heuristic
- p.14 (page-013): Continuation of min-max distance rationale (short page)
- p.15 (page-014): "Comparison with Other Work" - ARS, Doyle's TMS comparison
- p.16 (page-015): Doyle comparison continued - non-monotonic dependencies, conditional proof
- p.17 (page-016): CP mechanism not implemented, future work suggestions
- p.18 (page-017): Bibliography
- p.19 (page-018): Appendix I - User's Guide: TMS-INIT, MAKE-DEPENDENCY-NODE, SET-TRUTH
- p.20 (page-019): Appendix I continued: ADD-CLAUSE, DEFAULTS

## Key Findings Not in Current Notes
1. The algebraic manipulator example (p.3) - piecewise approximations as propositions
2. "Term" defined precisely: association of a node with a value (true when node has that value, false when opposite, unknown otherwise) (p.5)
3. OP-CLAUSES function: returns either POS-CLAUSES or NEG-CLAUSES depending on the opposite value (p.6)
4. PCONSEQ function: finds a node in the clause which has UNKNOWN truth state (p.6)
5. The example on p.8 showing why naive re-deduction after removal is problematic (A->B, B->C, C->B)
6. Contradictions can only arise from truth value addition, not clause addition alone (clarified on p.9-10)
7. The pulsing discussion (p.12): at most one or two pulses, requires complex structure
8. Assumption hierarchy via clause validity nodes with default support (p.13)
9. Doyle's CP mechanism: conditional proof as C -> (A^B -> D) condensation (p.15-16)
10. McAllester explicitly says he didn't implement CP because he had no application to justify it (p.17)
11. ADD-CLAUSE creates a clause node representing the clause's truth value (p.20)
12. DEFAULT as special reason atom in SET-TRUTH and ADD-CLAUSE (p.20)
