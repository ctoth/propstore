# Process Leads Session — 2026-03-24

## GOAL
Process all New Leads from the paper collection (`--all --parallel`).

## STATUS
Wave 1 dispatched (4 parallel agents). Waiting for completion.

## LEAD EXTRACTION
Extracted leads from 42 notes.md files via grep (paper_hash.py failed — requires Python 3.10+ match syntax, project uses 3.7.9).

### Triage Summary
- **Total unique leads:** ~120 (after dedup + filtering already-in-collection)
- **Books (defer):** ~12 — Knowledge in Flux, Causality, Cognitive Carpentry, Elements of Argumentation, Argumentation Schemes, etc.
- **Old/obscure/dissertations (defer):** ~15 — pre-1980 AI memos, tech reports, dissertations
- **Already in collection:** ~8 — Gärdenfors 1988, Caminada 2007, Toni 2014, Bench-Capon 2003, Bondarenko 1997, Fazzinga 2016, McAllester 1978, Prakken 2010
- **Likely available papers:** ~85

### Processing Order (by relevance to project)

**Wave 1 (core argumentation theory) — DISPATCHED:**
1. Baroni & Giacomin 2007 — AIJ full SCC-recursiveness paper
2. Caminada 2006 — "On the Issue of Reinstatement in Argumentation"
3. Gabbay 2012 — "Equational approach to argumentation networks"
4. Simari & Loui 1992 — "A mathematical treatment of defeasible argumentation"

**Wave 2 (computational argumentation) — PENDING:**
5. Odekerken, Borg, Bex 2022 — "Stability and relevance in incomplete argumentation frameworks"
6. Lehtonen, Wallner, Jarvisalo 2020 — "An ASP approach to argumentative reasoning in ASPIC+"
7. Caminada & Verheij 2010 — "On the existence of semi-stable extensions"
8. Amgoud & Vesic 2011 — "A new approach for preference-based argumentation frameworks"

**Wave 3 (probabilistic/belief):**
9. Fazzinga et al. 2019/2020 — complexity results for probabilistic AFs
10. Smets 1990 — "The transferable belief model"
11. Malinin & Gales 2018 — "Predictive Uncertainty Estimation via Prior Networks"
12. Gal & Ghahramani 2016 — "Dropout as a Bayesian Approximation"

**Wave 4 (structured argumentation):**
13. Brewka 1989 — "Preferred Subtheories"
14. Vreeswijk 1997 — "Abstract argumentation systems"
15. Cayrol & Lagasquie-Schiex 2004 — original BAF paper
16. Pollock 2009 — "A Recursive Semantics for Defeasible Reasoning"

**Wave 5 (encodings/complexity):**
17. Besnard & Doutre 2004 — "Checking the acceptability of a set of arguments"
18. Baroni, Caminada & Giacomin 2011 — handbook chapter on argumentation semantics
19. Lampis, Mengel, Mitsou 2018 — QBF reductions
20. Fichte, Hecher, Meier 2019 — Counting complexity

**Wave 6 (NLP/argument mining):**
21. Eger et al. 2017 — "Neural end-to-end learning for computational argumentation mining"
22. Cabrio & Villata 2018 — "Five years of argument mining"
23. Kazemi et al. 2023 — "BoardGameQA"
24. Pan et al. 2023 — "Logic-LM"

**Wave 7+ (remaining likely-available):**
- de Kleer 1986 "Extending the ATMS"
- Halpern 2015 modified HP causality (arxiv)
- Eiter & Lukasiewicz 2002 tractable HP causality
- Wallner et al. 2013 SAT techniques for argumentation
- Dvořák et al. 2014 complexity-sensitive procedures
- Rapberger & Ulbricht 2022 dynamics in structured argumentation
- Gelfond & Lifschitz 1988 stable model semantics
- Clark 1978 negation as failure
- McCarthy 1980 circumscription
- Josang 2008 conditional reasoning subjective logic
- Lakshminarayanan et al. 2017 deep ensembles
- Plus ~40 more

## CURRENT STATE (update 3)

### Wave 1: COMPLETE — 4/4 succeeded
| # | Lead | Directory |
|---|------|-----------|
| 1 | Baroni & Giacomin 2007 | papers/Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation/ |
| 2 | Caminada 2006 | papers/Caminada_2006_IssueReinstatementArgumentation/ |
| 3 | Gabbay 2012 | papers/Gabbay_2012_EquationalApproachArgumentationNetworks/ |
| 4 | Simari & Loui 1992 | papers/Simari_1992_MathematicalTreatmentDefeasibleReasoning/ |

- Reconcile agent dispatched for Wave 1 papers (running in background)

### Wave 2: DISPATCHED (4 agents running)
5. Odekerken, Borg, Bex 2022 — "Stability and relevance in incomplete argumentation frameworks"
6. Lehtonen, Wallner, Järvisalo 2020 — "An ASP approach to argumentative reasoning in ASPIC+"
7. Caminada & Verheij 2010 — "On the existence of semi-stable extensions"
8. Amgoud & Vesic 2011 — "A new approach for preference-based argumentation frameworks"

### Wave 1 Reconcile: DISPATCHED (running in background)

### Wave 2 Status:
- Odekerken 2022: FAILED — agent completed prematurely, no paper directory created. Likely retrieval issue.
- Lehtonen 2020: RUNNING
- Caminada & Verheij 2010: RUNNING
- Amgoud & Vesic 2011: RUNNING (had to nudge — it restated task instead of executing, sent confirmation message)

### Wave 3 Results:
- Brewka 1989: SUCCEEDED — papers/Brewka_1989_PreferredSubtheoriesExtendedLogical/
- Vreeswijk 1997: FAILED (retrieval — PDF not available)
- Pollock 2009: NOT ATTEMPTED (user rejected agent launch)

### Final Tally: 6 succeeded, 3 failed, 1 partial out of 10 attempted
- Wave 2-3 reconcile dispatched as final agent

### DONE
- Final report written to reports/process-leads-report.md
- ~110 leads remaining for future sessions

### Waves 3-7+: PENDING (see plan below)

## OBSERVATIONS
- Chrome is available (5 existing tabs from previous sessions)
- paper_hash.py uses match/case syntax requiring Python 3.10+, project has 3.7.9 — extracted leads manually via grep
- Each subagent invokes paper-retriever → paper-reader → extract-claims
- Subagents skip reconcile and index.md update — foreman handles after each wave
- Lead extraction required reading ~900 lines of grep output across 4 reads of the persisted tool output file

## NEXT STEPS
1. Wait for Wave 1 agents to complete
2. Check results — which papers succeeded/failed
3. Run reconcile + index.md update for successful papers
4. Dispatch Wave 2 (Odekerken 2022, Lehtonen 2020, Caminada & Verheij 2010, Amgoud & Vesic 2011)
5. Continue waves until session ends naturally
