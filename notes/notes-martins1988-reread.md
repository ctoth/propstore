# Martins 1988 Re-read Session

## GOAL
Re-read all 55 pages of Martins_1988_BeliefRevision and rewrite notes.md with page citations on every finding.

## Page numbering
The PDF pages (page-000.png through page-054.png) correspond to journal pages 25-79. So page-000 = p.25, page-001 = p.26, etc. Offset = 25.

## Pages read so far
- p.25 (page-000): Title page, abstract, Section 1 intro begins. Three key claims in abstract: (1) logic-based, (2) automatic dependency computation, (3) sets of assumptions not justifications.
- p.26 (page-001): Conventional approach (chronological backtracking), Stallman/Sussman dependency-directed backtracking. Belief revision definition. Five problems: inference, nonmonotonicity, dependency recording, disbelief propagation, revision of beliefs.
- p.27 (page-002): Section 1.2 Inference, 1.3 Nonmonotonicity, 1.4 Recording dependencies. Justification-based vs assumption-based.
- p.28 (page-003): Fig 1 (justification-based dependencies). Example with Man(Fred), Person(Fred), Human(Fred).
- p.29 (page-004): Fig 2 (assumption-based dependencies). Section 1.5 Disbelief propagation begins.
- p.30 (page-005): Disbelief propagation details. Three approaches: (1) Doyle/McAllester two-pass, (2) McDermott proposition labels/data pools, (3) de Kleer context/hypothesis sets.
- p.31 (page-006): Section 1.6 Revision of beliefs, 1.7 Overview of paper. SNeBR in FRANZLISP on VAX-11. Paper structure overview.
- p.32 (page-007): Section 2 The SWM System, 2.1 Introduction. SWM has syntax but no semantics. Relevance logic motivation.
- p.33 (page-008): Haack quote on formal vs informal arguments. Section 2.2 Relevance logic begins.
- p.34 (page-009): Relevance logic details. Anderson & Belnap FR system. Origin sets, rules of inference with OS tracking. Proofs as nested subproofs.

## Pages read continued
- p.35 (page-010): FR system ->I and ^I rules. Fig 3 (->I rule), Fig 4 (^I rule). Key: ->I uses set difference on OS, ^I requires same OS.
- p.36 (page-011): Fig 5 ("proof" showing paradox of implication in FR system). Section 2.3 Supported wffs begins. SWM for "perpetual proof" not theorem proving.
- p.37 (page-012): RS definition, origin tag (OT), restriction set details. Supported wff = quadruple <A, tau, alpha, rho>. Accessor functions wff(), ot(), os(), rs(). ext OT for special propositions.
- p.38 (page-013): RS minimality conditions. mu function defined. Psi function defined. Two conditions for minimal RS.
- p.39 (page-014): sigma function (remove supersets). Integral function defined. A function (OT computation). Combine predicate defined. Four guarantees of SWM rules.
- p.40 (page-015): Section 2.4 Inference rules. Hypothesis rule. Implication Introduction (->I). Modus Ponens (MP). Modus Tollens (MT).
- p.41 (page-016): Negation Introduction (neg-I). Negation Elimination (neg-E). URS rule (Updating Restriction Sets). And-Introduction (^I) - two forms. And-Elimination (^E). Or-Introduction (v-I). Or-Elimination (v-E).
- p.42 (page-017): Or-Elimination cont'd. Universal Introduction (VI). Universal Elimination (VE). Existential Introduction (EI). Existential Elimination (EE). Theorems 4, 5, Corollary 5.1 stated.
- p.43 (page-018): RS is both minimal and maximal. Section 3 Nonstandard Connectives. Section 3.1 Introduction. SNePS connectives as syntactic abbreviations. Formation rules for and-entailment, or-entailment, and-or, thresh.
- p.44 (page-019): Combination notation. Section 3.2 And-entailment. And-Entailment Introduction and Elimination rules.
- p.45 (page-020): And-Entailment Elimination cont'd. Section 3.3 Or-entailment. Or-Entailment Introduction and Elimination rules.
- p.46 (page-021): And-or definition (generalizes neg, and, or, exclusive or, nand). And-Or Introduction rule. Inferences allowed by xE (elimination).
- p.47 (page-022): And-Or Introduction and Elimination formal rules within SWM.
- p.48 (page-023): Thresh Introduction and Elimination rules. Edge cases for i=0, j=0, i=j=n.
- p.49 (page-024): Section 4 MBR The Abstract Level. Section 4.1 Contexts and belief spaces. Context = set of hypotheses determining a BS. Current context. Context consistency condition via RS checking.
- p.50 (page-025): Theorem 6 (Combine = true in non-inconsistent context). Corollary 6.1. Section 4.2 Revision of beliefs. Two levels: within current context, within strictly containing context. neg-I and URS rules.
- p.51 (page-026): URS effect on contradictions. Two cases: (1) only one contradictory wff in current BS -> revision within strictly containing context, (2) both in current BS -> revision within current context. Section 5 SNeBR begins. Five operations.
- p.52 (page-027): SNeBR operations: add hypotheses, name context, ask for nodes matching pattern, perform backward inference, perform forward inference. Section 5.2 Representation of propositions. SNePS uniqueness principle. Fig 6: SNePS nodes for "John hits Mary" and "Mary likes soup".
- p.53 (page-028): SNeBR proposition representation. Supporting nodes with os/rs/OT arcs. Fig 7: hypothesis supported wff network. Fig 8: derived (der) supported wff network.
- p.54 (page-029): Fig 8 cont'd. Contradictory propositions share network structure. SNeBR "believes" nodes whose OS is in current context. Two aspects of representation: (1) contradictory propositions, (2) multiple derivations.

## Pages read continued (batch 3)
- p.55 (page-030): Fig 9: contradictory propositions P and not-P share network structure via and-or min=0 max=0. Contradiction detection when building nodes.
- p.56 (page-031): Multiple derivations representation. Fig 10: multiple supporting nodes for same proposition C. Three derivations with different OS/RS.
- p.57 (page-032): Fig 11: propositions sharing a supporting node (same OS -> same RS by Theorem 5). Section 5.3 Representation of contexts. Context = node with "val" arcs. Fig 12 next page.
- p.58 (page-033): Fig 12: context "ct1" with val arcs to H1, H2. Section 5.4 Inference in SNeBR. Active connection graphs (acg). Bi-directional inference. Pattern matching. MULTI system (LISP-based process scheduler).
- p.59 (page-034): MULTI details: evaluator, scheduler, system primitives. One process per rule of inference. Section 5.5 Handling contradictions. Two detection conditions: (1) building contradictory nodes, (2) process data invalidates rule.
- p.60 (page-035): Section 5.6 Implementation of URS. Two traversals: first to find hypotheses, second to update RSs. os^-1 arcs for traversal. Example with Fig 9 nodes.
- p.61 (page-036): Fig 13: Network after URS application. RS update creates new rs/ers nodes. Case (2) RS simplification discussion.
- p.62 (page-037): Fig 14: Network before URS when n5 has two supporting nodes. Section 6 begins: "The Woman Freeman Will Marry" puzzle.
- p.63 (page-038): Puzzle statement (7 clues). SNePSLOG representation. wff1-5 (five women).
- p.64 (page-039): SNePSLOG encoding: wff12, wff18, wff27, wff33, wff39, wff48, wff53, wff58, wff63, wff68. Nonstandard connectives used extensively.

## Pages read continued (batch 4)
- p.65 (page-040): wff79, wff88. Fig 15 (hypotheses for puzzle). Fig 16 (hypotheses raised for ages/occupations).
- p.66 (page-041): Fig 17 (SNeBR interaction: who will Freeman marry?). Fig 18 (Freeman will marry Ada). Fig 19 (Deb is over 30). Contradiction detected.
- p.67 (page-042): Fig 20 (contradiction detected, user options). Fig 18/19 continued.
- p.68 (page-043): Fig 21 (inspecting inconsistent hypotheses). Fig 22 (adding new hypotheses age(Bea,o30), age(Deb,o30)). Interactive revision.
- p.69 (page-044): Fig 23 (resuming deduction). Fig 24 (Freeman will marry Deb). Fig 25 (returned propositions). Information sharing between BSes.
- p.70 (page-045): Section 7 Concluding Remarks. Summary of contributions. SNeBR = first assumption-based belief revision system.
- p.71 (page-046): Appendix A. Theorem 1 (mu produces minimal RS). Theorem 2 (integral produces minimal RS). Theorem 3 (supersets of inconsistent sets are inconsistent).
- p.72 (page-047): Corollary 3.1 (if A not known inconsistent, neither is any subset). Theorem 4 proof (all wffs have minimal RS by induction on rules applied).
- p.73 (page-048): Theorem 4 proof continued (URS case).
- p.74 (page-049): Lemma 1, Lemma 2. Theorem 5 proof begins (same OS -> same RS).
- p.75 (page-050): Theorem 5 proof continued. Corollary 5.1 (every OS records every known inconsistent set).
- p.76 (page-051): Theorem 6 proof (Combine = true in non-inconsistent context). Corollary 6.1.
- p.77-79 (page-052 to page-054): References (58 entries). Received August 1985, revised July 1987.

## STATUS
ALL 55 PAGES READ. Now rewriting notes.md with page citations.
