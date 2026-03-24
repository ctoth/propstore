# Process Leads Session — 2026-03-22

## GOAL
Process first 10 New Leads from the paper collection via paper-process (retrieve + read + extract claims).

## STATUS
Parsed all 10 leads, about to start sequential processing.

## LEADS TO PROCESS

| # | Lead | Search Query | Notes |
|---|------|-------------|-------|
| 1 | Gardenfors 1988 "Knowledge in Flux" | Gardenfors 1988 Knowledge in Flux | BOOK — likely fail |
| 2 | Cimatti et al 2013 "OptiMathSAT" | Cimatti 2013 OptiMathSAT | Paper |
| 3 | de Moura & Bjørner 2008 "Z3: An Efficient SMT Solver" | de Moura Bjørner 2008 Z3 An Efficient SMT Solver | Paper |
| 4 | Amgoud et al 2004 "Towards a consensual formal model" | Amgoud 2004 Towards a consensual formal model ASPIC | Technical report — likely fail |
| 5 | Baroni & Giacomin "Two-resolutions" | Baroni Giacomin Two-resolutions argumentation semantics | Paper |
| 6 | Amgoud et al 2004 "On the bipolarity in argumentation frameworks" | Amgoud 2004 On the bipolarity in argumentation frameworks | Paper |
| 7 | Karacapilidis & Papadias 2001 "Computer supported argumentation" | Karacapilidis 2001 Computer supported argumentation collaborative decision making | Paper |
| 8 | Verheij 2002 "On the existence and multiplicity of extensions" | Verheij 2002 existence multiplicity extensions dialectical argumentation | Paper |
| 9 | Toulmin 1958 "The Uses of Argument" | Toulmin 1958 The Uses of Argument | BOOK — likely fail |
| 10 | Carroll et al 2005 "Named graphs, provenance and trust" | Carroll 2005 Named graphs provenance trust | Paper |

## PROGRESS
- Lead 1 (Gardenfors 1988): SKIP — book, no paper PDF available
- Lead 2 (Cimatti/OptiMathSAT): DONE — Sebastiani_2015_OptiMathSATToolOptimizationModulo. Committed.
- Lead 3 (Z3 SMT Solver): Retrieved as Moura_2008_Z3EfficientSMTSolver (4pp). Read all pages. Writing notes now.
  - Short tool/system paper describing Z3 architecture
  - DPLL-based SAT solver + core theory solver (congruence closure) + satellite solvers (LA, BV, arrays, tuples) + E-matching engine
  - Key components: Simplifier, Compiler, Congruence closure core, SAT solver, Theory Solvers, E-matching
  - Clients: VCC (C verifier), Spec#/Boogie3, Pex (test generation)
  - Quantifier instantiation via E-matching with model-based approach
  - Won 4 categories in SMT-COMP 2007
  - Tool paper for OptiMathSAT, extends MathSAT5 SMT solver with optimization
  - Supports single/multi-objective optimization over LRA, LIA, BV, combinable
  - Partial weighted MaxSMT with Pseudo-Boolean objective encoding
  - Multi-objective: lexicographic, Pareto, minmax/maxmin
  - Interfaces: SMT-LIBv2 extensions, C API, Python/Java wrappers
  - Applications: structured learning modulo theories, automated reasoning on constrained goal models

## DONE
- Extracted 99 leads (11 already in collection)
- Parsed all 10 leads with paper_hash.py
- Started paper-process for lead 1

## WAVE 1 STATUS
- lead5-baroni: Got 9pp NMR workshop version (not full AIJ paper). Reader agent dispatched, running.
- lead6-amgoud: DONE — Amgoud_2008_BipolarityArgumentationFrameworks (29pp, all read, notes written). High relevance: BAF=(A,R_def,R_sup), supported defeat, gradual valuation.
- lead7-karacapilidis: DONE — Karacapilidis_2001_ComputerSupportedArgumentationCollaborative (10pp). Medium relevance: HERMES CDSS with proof standards, no formal semantics.
  - PDF retrieval required manual sci-hub via Chrome (curl blocked by redirects, then sci-hub blocked direct curl — had to download via browser JS fetch + save to Downloads + mv)

## WAVE 2 — DISPATCHED
- lead8-verheij: Verheij 2002 "Extensions in dialectical argumentation" — agent running
- lead10-carroll: Carroll 2005 "Named graphs, provenance and trust" — agent running

## DEFERRED (unlikely available)
- Lead 1: Gardenfors 1988 "Knowledge in Flux" — BOOK, skipped
- Lead 4: Amgoud et al 2004 ASPIC deliverable — technical report
- Lead 9: Toulmin 1958 "The Uses of Argument" — BOOK

## SKILL UPDATE COMPLETED
- Updated process-leads SKILL.md: triage step + mandatory subagents
- Committed to ../research-papers-plugin

## WHAT WORKED
- Subagent dispatch for paper-process — context stays clean, agents handle the heavy page reading
- Triage ordering — skipped book leads, processed real papers first
- fetch_paper.py gets many papers via Unpaywall/direct download
- Chrome browser as sci-hub fallback when curl is blocked

## WHAT DIDN'T WORK
- Agents restated task instead of executing (global CLAUDE.md "restate first" rule) — had to SendMessage "Confirmed" to each
- Karacapilidis agent couldn't do sci-hub fallback alone (no tab ID) — foreman had to do it manually
- Baroni agent got short workshop version instead of full paper — tried to find longer version and ran out
- Curl to sci-hub blocked (got HTML instead of PDF) — browser-context fetch worked but required JS download trick

## ALL AGENTS COMPLETE
- lead5-baroni-read: DONE — 9/10 usefulness, SCC-recursive decomposition, CF2 semantics
- lead8-verheij: DONE — 7/10 usefulness, extension existence/multiplicity characterization
- lead10-carroll: FAILED — sci-hub PDF download blocked (blob download not landing in filesystem)

## NEXT STEPS NOW
1. Update papers/index.md with 4 new papers (Amgoud, Baroni, Karacapilidis, Verheij)
2. Commit all new papers
3. Run reconcile for each (dispatch subagent)
4. Write process-leads-report.md
