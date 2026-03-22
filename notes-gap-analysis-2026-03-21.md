# Paper Collection Gap Analysis — 2026-03-21

## Current Collection (26 papers)
See papers/index.md for full list.

## All New Leads from notes.md files (deduplicated)

### Cited by multiple papers (highest signal):
1. **Stallman & Sussman (1977)** — "Forward reasoning and dependency-directed backtracking" — cited by deKleer ATMS, Doyle TMS, McAllester RUP, McDermott contexts
2. **Gardenfors & Makinson (1988)** — "Revisions of Knowledge Systems Using Epistemic Entrenchment" — cited by Alchourron, Dixon (EE1-EE5 axioms central to ATMS-AGM bridge)
3. **Caminada & Amgoud (2007)** — "On the evaluation of argumentation formalisms" — cited by Modgil 2014, Modgil 2018 (rationality postulates ASPIC+ satisfies)
4. **Prakken (2010)** — "An abstract framework for argumentation with structured arguments" — cited by Modgil 2014, Modgil 2018 (original ASPIC+ paper)
5. **de Kleer (1986)** — "Extending the ATMS" — cited by deKleer ATMS, deKleer ProblemSolving (default reasoning, disjunction)
6. **McDermott & Doyle (1978)** — "Non-monotonic Logic I" — cited by Doyle, Reiter

### Cited once but high relevance:
7. **Bondarenko, Toni & Kowalski (1993/1997)** — ABA framework — Dung cites this
8. **Toni (2014)** — "A tutorial on assumption-based argumentation" — companion to ASPIC+ tutorial
9. **Brewka (1989)** — "Preferred subtheories" — formally connected to ASPIC+ via Theorem 31
10. **Stab & Gurevych (2017)** — "Parsing argumentation structures in persuasive essays" — baseline for Mayer 2020
11. **Baroni, Caminada & Giacomin (2011)** — handbook chapter on argumentation semantics
12. **Odekerken, Borg & Bex (2022)** — "Stability and relevance in incomplete argumentation frameworks" — companion to collected 2023 paper
13. **Bench-Capon (2003)** — "Persuasion in practical argument using value-based argumentation frameworks"
14. **Cravo & Martins (1993)** — "SNePSwD" — extends SNeBR with AGM entrenchment

### Books (not retrievable as papers):
- Gardenfors (1988) — "Knowledge in Flux"
- Lewis (1973) — "Counterfactuals"
- Anderson & Belnap (1975) — "Entailment"
- Pollock (1995) — "Cognitive Carpentry"
- Walton, Reed & Macagno (2008) — "Argumentation Schemes"
- Shafer (1976) — "A Mathematical Theory of Evidence"

### Lower priority / harder to find:
- Pollock (2009b) — recursive semantics for defeasible reasoning
- Amgoud, Cayrol, Lagasquie-Schiex (2004) — bipolar argumentation precursor
- Rahwan et al. (2011) — AIF representation
- Various 1970s AI memos

## Retrieval Plan

### Batch 1 — Core argumentation theory gaps (highest priority):
1. Caminada & Amgoud (2007) — rationality postulates
2. Prakken (2010) — original ASPIC+
3. Toni (2014) — ABA tutorial
4. Brewka (1989) — preferred subtheories

### Batch 2 — Belief revision / TMS gaps:
5. Gardenfors & Makinson (1988) — epistemic entrenchment
6. de Kleer (1986) — "Extending the ATMS"

### Batch 3 — Argument mining / modern:
7. Stab & Gurevych (2017) — parsing argumentation structures
8. Baroni, Caminada & Giacomin (2011) — argumentation semantics handbook chapter

### Batch 4 — After web search identifies additional gaps

## Dispatch Status (2026-03-21)

8 parallel subagents dispatched via `paper-process` skill. Status:

| # | Paper | Agent | Status |
|---|-------|-------|--------|
| 1 | Caminada & Amgoud (2007) — rationality postulates | caminada2007 | RUNNING |
| 2 | Prakken (2010) — original ASPIC+ | prakken2010 | RUNNING |
| 3 | Gardenfors & Makinson (1988) — epistemic entrenchment | gardenfors1988 | FAILED — no open-access PDF (old TARK proceedings) |
| 4 | Toni (2014) — ABA tutorial | toni2014 | RUNNING |
| 5 | Brewka (1989) — preferred subtheories | brewka1989 | RUNNING |
| 6 | Bondarenko et al (1997) — canonical ABA | bondarenko1997 | FAILED — Elsevier paywall, DOI: 10.1016/S0004-3702(97)00015-5 |
| 7 | Stab & Gurevych (2017) — argumentation parsing | stab2017 | RUNNING |
| 8 | Bench-Capon (2003) — value-based argumentation | benchcapon2003 | RUNNING |

### Failed retrievals needing manual PDF download:
- `papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/paper.pdf`
- `papers/Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault/paper.pdf` — get from sci-hub: 10.1016/S0004-3702(97)00015-5

### Web search findings:
- Collection gaps are well-identified by existing New Leads sections
- No major thematic holes beyond what the leads already captured
- Modgil & D'Agostino (2020) "A fully rational account of structured argumentation under resource bounds" is a potential future addition

### Next steps:
- Wait for remaining 6 agents to complete
- Read their reports to confirm success
- Manually download the 2 paywalled PDFs, then re-run paper-reader on them
- After all papers are in, run reconcile --all to cross-reference
