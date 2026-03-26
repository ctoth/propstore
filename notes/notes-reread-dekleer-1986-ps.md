# Reread: de Kleer 1986 - Problem Solving with the ATMS

## Status: ALL PAGES READ. Ready to rewrite notes.md.

## Complete page mapping (0-indexed image -> journal page)
- page-000 = p.197: title, abstract, Section 1 Introduction
- page-001 = p.198: environments, labels, justifications, notation
- page-002 = p.199: Fig 1 - environment lattice for 5 assumptions
- page-003 = p.200: ATMS extensions x3 (default assumption, disjunction, nonmonotonic), Section 2 Basic Principles, 2.1 Justifications
- page-004 = p.201: too-general/too-specific labels, Section 2.2 Control
- page-005 = p.202: Section 3 Consumers - definition, 4 restrictions, basic/conjunctive consumer
- page-006 = p.203: consumer encoding a≡b, consumer type system, Section 3.1 Unouting solved
- page-007 = p.204: unouting example end, Section 4 Control
- page-008 = p.205: Section 4.1 Scheduling, before/after ordering, Section 4.2 DDB with control disjunctions, Section 4.3 Delayed justifications
- page-009 = p.206: delayed justifications impl, Section 4.4 Kernel environment, 4.5 Incremental interpretation, 4.6 Problem solver responsibility, Section 5 General Consumers
- page-010 = p.207: class consumer, conjunctive class consumer, constraint R(x,y,z) example
- page-011 = p.208: Section 5.1 Constraint consumers (R_i^{-1}), conditional constraint consumer (transistor example), Section 5.2 Implication consumer (exclusive)
- page-012 = p.209: inclusive implication consumer, environment consumer, Section 5.3 Simple constraint language (EQ, NOT, MINUS)
- page-013 = p.210: PLUS, TIMES, DIVIDE, E, AND, OR, ONEOF, ELEMENT definitions, PLUS inverse
- page-014 = p.211: AND encoding with clauses/contrapositives, AND(l,l1,l2,...) formal encoding
- page-015 = p.212: AND R_i^{-1} class consumers, TIMES detailed with zero handling, hyperresolution rule H5
- page-016 = p.213: ONEOF implementation, Section 5.4 Assertional language (AMORD)
- page-017 = p.214: assertional language continued, Section 5.5 Consequent reasoning, Section 5.6 Exclusivity of variable values (5-value system)
- page-018 = p.215: Section 6 Comparison to Other Work, 6.1 ATMS vs TMS - 3 classes of problems, parity problem intro
- page-019 = p.216: parity problem with/without control (4i vs 2^{i+2}+2^i), Section 6.2 Doyle's TMS
- page-020 = p.217: Doyle CP-justifications, contradiction handling, Section 6.3 McAllester's RUP
- page-021 = p.218: McAllester cont., RUP noticers = ATMS consumers, Section 6.4 McDermott
- page-022 = p.219: McDermott cont. - negation, data pools, erasure mechanism
- page-023 = p.220: McDermott cont. - ATMS handles contradictions/completeness/consistency, control via data pool, Section 6.5 MBR
- page-024 = p.221: MBR cont., Section 6.6 ART, Section 6.7 Theories of reasoned assumptions
- page-025 = p.222: Section 6.8 Counterfactuals (Ginsberg), Section 7 Future Research, 7.1 Parallelism, 7.2 Control issues
- page-026 = p.223: 7.3 Time and action, Acknowledgment, References 1-14
- page-027 = p.224: References 15-22

## Findings to add that existing notes missed
1. Consumer has 4 restrictions (p.202): (a) only examine data of nodes, (b) only examine antecedent nodes, (c) antecedents = exactly the consumer's antecedents, (d) no internal state/control decisions
2. Consumer type system avoids retriggering on own output (p.202)
3. Unouting problem automatically solved by consumer architecture (p.203)
4. Environment consumer: runs when new environment added to a node (p.209)
5. Conditional constraint consumer: constraint conditional on operating region (p.208) - transistor example
6. Exclusivity of variable values: non-exclusive 5-value system example (p.214)
7. Assertional language integration with AMORD (p.213-214)
8. Consequent reasoning: ATMS applies to consequent as well as antecedent reasoning (p.214)
9. Parallelism: consumers are order-insensitive, parallelizable (p.222)
10. Time/action limitation: ATMS is purely inferential, cannot model side effects (p.223)
11. Three classes of problems for ATMS vs TMS comparison (p.215)
12. Doyle's CP-justification = mechanism for recording results determined in other database state (p.217)
13. McDermott: 'assertions'='data', 'premisses'='assumptions', 'data pool'='context' (p.218)
14. MBR: origin set = label, restriction set = nogoods (p.220)
15. ART: 'extent'='label', 'constraint'=justification, 'poison'='contradiction', 'believe'=contradict competing extensions (p.221)
16. Counterfactuals: ATMS extensions correspond to Ginsberg's most similar worlds (p.222)
17. ATMS handles contradictions by simply recording them as nogoods (p.220)
18. ATMS never modifies justifications to avoid contradictions (p.219)
19. Hyperresolution rule H5 needed for detecting TIMES inconsistency with zero (p.212)
20. control{A,B} expresses preference: solutions with A found before B (p.205)
