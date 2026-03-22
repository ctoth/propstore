# McDermott 1983 Reread Session Notes

## GOAL
Reread all 10 pages of McDermott 1983, add page citations to every claim in notes.md, add any missed findings.

## STATUS
- All 10 pages read. Paper pages are 237-246 (page-000=p.237, page-009=p.246).
- Ready to rewrite notes.md with citations.

## Page-by-page content mapping

- **p.237 (page-000):** Title, abstract, Section I intro. Data pools defined. Conniver/QA4 context. Bead = natural number, data pool = pair (b,S). Copy/push operations.
- **p.238 (page-001):** Fig.1 tree of data pools. Examples of pool operations. Labels as Boolean expressions. Reagan/McMorrow example. Labels stored in DNF.
- **p.239 (page-002):** Section I-B Data Dependencies. Fig.2 chess example. Fig.3 non-monotonic dependency. Justification = (in-justifiers, out-justifiers, justificand). Consistent/well-founded definitions.
- **p.240 (page-003):** Fig.4 data pool label as justification. Fig.5 dependency simulation. Fig.6 deductive chaining. Synthesis of pools and dependencies. Signal functions between KR and DD levels.
- **p.241 (page-004):** Fig.7 labeled network. Fig.8 circular network. Fig.9 network fragment. Section II combining pools+deps. Labels as Boolean combinations. Consistency/well-foundedness redefined for Boolean labels. Subsumption defined. Label equations A=b1 V ~B, B=b2 V ~A.
- **p.242 (page-005):** Fig.10 odd loops. Fig.11 large labels. Solving B=b2, A=b1 V ~b2. Odd loop constraint. A=f(A) monotonic solution A=C. Algorithm: pick A=E, substitute. Halting proof. Complexity n^2 worst case. McAllester exponential label growth. Labels can grow with depth of well-founded support.
- **p.243 (page-006):** Fig.12 worked example. Section II-B Deductive Chaining. Section III Actual Algorithm. Description of Lisp implementation. Forward sweep, *UNKNOWN marking, provisional labels. Subsumption optimization. Blocking beads and latent assertions.
- **p.244 (page-007):** Section III-B Timing. Benchmark: 200 nodes, DEC 2060, ILISP. 0.3ms per node, 3 CONSes per node, 606 CONSes total, 0.1ms per CONS for GC. Table of benchmark results. Section III-C Other optimizations discussion. Comparison with Doyle's algorithm.
- **p.245 (page-008):** Section IV Applications. Chronological backtracking. DUCK language. Chronsets for temporal reasoning. Temporal intervals. Gated lists for heuristics.
- **p.246 (page-009):** References. Also contains beginning of next paper (Vere 1983) which is not part of this paper.

## Key findings to add (missed in existing notes)
- Fig.6 (p.240) showing deductive chaining across data pools - not mentioned in figures
- Fig.12 (p.243) worked example details - forward sweep ordering
- The DUCK language application (p.245)
- Chronset temporal reasoning details (p.245)
- Gated lists mechanism (p.245)
- Comparison with Doyle's algorithm specifics (p.244)
- Signal functions definition on p.240
- 606 total CONSes, 39 reclaimed (p.244)
- The subsumption relation formal definition (p.241)
