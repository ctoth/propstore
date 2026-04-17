# Axis 9 — Documentation Drift

## Summary

The CLAUDE.md architecture description has meaningful drift against the actual code layout (wrong files named for TIMEPOINT, wrong location for ATMS/IC-merge operators, stale `aspic_bridge.py` references after the module was split into a package). The most systematic drift is in paper citations: Modgil & Prakken (2018) is cited by the wrong definition number in multiple docstrings in `aspic.py` and `artifacts/documents/rules.py`, in a pattern that looks like a single author referring to the paper from memory and off-by-one-ing the definitions. The papers/index.md manifest is also out of sync — 44 paper directories have no index entry, and 25 paper directories have no `notes.md` at all. Category C (paper citation drift) is the most damaging category because it erodes the literature-grounding claim the project stakes its authority on.

Finding counts (unique findings, positive "note" findings included):
- Crit: 2 (both on the same Modgil Def-1 mislocation, one in Category B and one in Category C)
- High: 4 (A.2 ATMS/IC-merge mislocation; B.2 last-link Def 13; D orphan index entries; D missing notes.md)
- Med: 7 (A.1 TIMEPOINT file pointer; A.3 stale aspic_bridge.py; B.6 missing revision docstring; C.6 Diller 2025 Def 7; D small notes.md spot-check; E.2 README aspic_bridge.py; E.3 docs/argumentation.md)
- Low: 5 (A.4 Defs 1-22 hand-wave; B.7 thin orchestrator docstring; B.8 Run 6/7 shorthand; E.1 Layer 2 naming; E.4 docs/data-model.md)
- Note (positive): 7 (A.5 Jøsang p.8 vacuous; A.6 Known-Limitations accurate; B.3 dung.py citations; B.4 opinion.py citations; B.5 build_arguments_for Def 5; C.3/C.4/C.5 Jøsang/Dung/Modgil Def 14; E.5 pks build command)

## Findings by category

### Category A — CLAUDE.md vs code

#### Finding A.1 — TIMEPOINT pointed at wrong file
- Severity: med
- CLAUDE.md claim (line 16): "`KindType.TIMEPOINT` maps to `z3.Real` (same as QUANTITY) but is semantically distinct — not valid for parameterization or dimensional algebra."
- Directive to verify in task prompt: "check `propstore/cel_types.py`, `propstore/z3_conditions.py`, and wherever TIMEPOINT is used."
- Code reality: `cel_types.py` contains only `CelExpr`, `CheckedCelExpr`, `CheckedCelConditionSet` branded carriers — no `KindType` at all. `KindType.TIMEPOINT` is defined at `propstore/cel_checker.py:38`.
- Drift: CLAUDE.md implicitly routes readers to the wrong file when they try to verify the TIMEPOINT claim.
- Recommendation: Update CLAUDE.md (and similar prose in any internal guide) to name `cel_checker.py` as the home of `KindType`, or rename the pointed-to file. The underlying semantic claim is correct — TIMEPOINT and QUANTITY both land on `z3.Real` via `z3_conditions.py:134`, and `parameterization_groups.py` / `parameterization_walk.py` reference neither kind.

#### Finding A.2 — `propstore/repo/` described as owning ATMS/ASPIC+ bridge and IC merge operators
- Severity: high
- CLAUDE.md claim (line 15): "`propstore/repo/` provides git-backed storage with branch isolation, semantic merge classification, two-parent merge commits, branch reasoning (ATMS/ASPIC+ bridge), and IC merge operators."
- Code reality:
  - `propstore/repo/` is 12 modules covering branch/merge/git plumbing (`branch.py`, `git_backend.py`, `merge_claims.py`, `merge_classifier.py`, `merge_commit.py`, `merge_framework.py`, `merge_report.py`, `paf_merge.py`, `paf_queries.py`, `repo_import.py`, `snapshot.py`, `structured_merge.py`).
  - Grepping `propstore/repo/` for `atms|aspic` returns zero matches.
  - ATMS engine actually lives in `propstore/world/atms.py`.
  - ASPIC+ bridge lives in `propstore/aspic_bridge/` (its own top-level package).
  - IC-merge operators live in `propstore/world/ic_merge.py`.
  - `propstore/repo/` imports nothing from `world.ic_merge`.
- Drift: CLAUDE.md attributes three capabilities to `propstore/repo/` that are entirely owned by `propstore/world/` and `propstore/aspic_bridge/`. A reader chasing "how does branch reasoning via ATMS actually work" would find nothing in the location they were told to look.
- Recommendation: Rewrite the `propstore/repo/` line to reflect its actual role (branch plumbing, semantic-merge classification, two-parent commits) and move the ATMS / ASPIC+-bridge / IC-merge attribution into the description of the Concept/semantic and Argumentation layers.

#### Finding A.3 — `aspic_bridge.py` cited as a file, but it is now a package
- Severity: med
- CLAUDE.md claim (line 35): "ASPIC+ bridge (`aspic_bridge.py` translates claims/stances to formal ASPIC+ types, `aspic.py` builds recursive arguments)"
- CLAUDE.md claim (line 45): "The claim graph routes through `aspic_bridge.py` → `aspic.py` ..."
- Code reality: no `propstore/aspic_bridge.py` file exists. `propstore/aspic_bridge/` is a package with `__init__.py`, `build.py`, `extract.py`, `grounding.py`, `projection.py`, `query.py`, `translate.py`.
- Drift: CLAUDE.md, README.md, `docs/argumentation.md`, `docs/data-model.md`, `agent-papers.md`, and `EXPLORATION_NOTES.txt` all still reference the legacy `aspic_bridge.py` file. The package was extracted but six docs were left stale.
- Recommendation: Search-and-replace `aspic_bridge.py` → `aspic_bridge/` (or to the specific module inside the package) across all top-level docs. The surviving docstring at `docs/argumentation.md:30` pointing `query_claim()` to `propstore/aspic_bridge.py` literally sends readers to a non-existent file.

#### Finding A.4 — Modgil & Prakken "Defs 1-22" shorthand is inaccurate
- Severity: low
- CLAUDE.md claim (line 45): "recursive argument construction (Modgil & Prakken 2018 Defs 1-22)"
- Code reality: Modgil & Prakken 2018 extends through Def 23 at minimum (per `papers/Modgil_2018_GeneralAccountArgumentationPreferences/notes.md:86` "Def 23, p.23"). The actual ASPIC+ argument construction uses specific definitions: Def 2 (AS tuple), Def 5 (arguments), Def 8 (attack types), Def 9 (defeat), Def 14 (attack-based conflict-free), Defs 18-21 (preference orderings).
- Drift: "Defs 1-22" is a vague hand-wave that overstates how much of the paper the code implements and understates where it stops. Def 1 is actually about plain Dung AFs, not ASPIC+ at all.
- Recommendation: Replace with an accurate list such as "Def 2 (AS), Def 5 (arguments), Defs 8-9 (attack/defeat), Def 14 (conflict-free), Defs 18-21 (preferences)".

#### Finding A.5 — Honest-ignorance claim pointing at Jøsang 2001 p.8 for vacuous opinions
- Severity: note (positive — this one is correct)
- CLAUDE.md claim (line 24): "Vacuous opinions (Jøsang 2001, p.8) represent total ignorance honestly."
- Paper evidence: `papers/Josang_2001_LogicUncertainProbabilities/notes.md:218` — "Special opinions: vacuous = (0, 0, 1, a), absolute_true = (1, 0, 0, a), absolute_false = (0, 1, 0, a) *(p.8)*" and line 240: "Start with vacuous opinion (0, 0, 1, a) for any proposition without evidence *(p.8)*".
- Match: yes.

#### Finding A.6 — Known-Limitations list is accurate
- Severity: note (positive)
- Each "not yet implemented" claim in CLAUDE.md lines 45-51 was cross-checked and still holds:
  - `interval_dominance` has zero matches in `propstore/` — confirmed deferred.
  - `apply_decision_criterion` at `world/types.py:1031` handles pignistic / lower_bound / upper_bound / hurwicz only — matches the claim.
  - Konieczny IC0-IC8 semantics are deferred per `world/ic_merge.py:1-12` module docstring.
  - `Amgoud` and `Vesic` both return zero matches in `propstore/praf/` (and in `propstore/` overall) — attack-inversion deferred.
  - `deduction`, `comultiplication`, `abduction` have no definitions in `opinion.py`; only core consensus/wbf/ccf/fuse/discount are present.
- The Known-Limitations section is one of the least-drifted parts of CLAUDE.md — keep it but monitor.

### Category B — Docstring vs behavior

#### Finding B.1 — `aspic.py:55` cites "Def 1 (p.8)" for the contrariness function — wrong number AND wrong content
- Severity: crit
- File:line: `propstore/aspic.py:55-57` (Literal), `propstore/aspic.py:74` (Literal.contrary), `propstore/aspic.py:91-93` (ContrarinessFn)
- Docstring says (Literal, lines 55-57): "Modgil & Prakken 2018, Def 1 (p.8): L is a logical language closed under the contrariness function — every formula's contraries/contradictories are also in L."
- Paper reality (pulled from `papers/Modgil_2018_GeneralAccountArgumentationPreferences/pngs/page-003.png`):
  - **Definition 1 is on page 4, not page 8.** It is Dung's acceptability/admissibility ("Let (A, C) be a AF. For any X ∈ A, X is acceptable with respect to some S ⊆ A iff ∀Y s.t. (Y, X) ∈ C implies ∃Z ∈ S s.t. (Z, Y) ∈ C..."). It says nothing about L, languages, or contrariness.
  - The contrariness function is part of **Definition 2 on page 8** (ASPIC+ argumentation system `AS = (L, -, R, n)`, verified via `pngs/page-007.png`).
- Drift: Both number and page are wrong, and the quoted content does not appear under Def 1 anywhere in the paper. The same phantom "Def 1 (p.8)" citation is repeated on lines 74 (Literal.contrary) and 91-93 (ContrarinessFn), propagating the error across three docstrings.
- Recommendation: Change to "Modgil & Prakken 2018, Def 2 (p.8)" and adjust the quoted wording (the paper does not claim closure under contrariness as stated — it just defines the mapping and requires each φ ∈ L to have at least one contradictory).

#### Finding B.2 — `artifacts/documents/rules.py:120` cites Def 13 for last-link comparisons
- Severity: high
- File:line: `propstore/artifacts/documents/rules.py:120`
- Docstring says: "implicit preference information relevant to structured-argumentation last-link comparisons (Modgil & Prakken 2018 Def 13)."
- Paper reality (`papers/Modgil_2018_GeneralAccountArgumentationPreferences/notes.md:73-77`): Def 20 (p.21) is the last-link principle. Def 13 (p.14) is defeat-based conflict-free (which Modgil & Prakken 2018 explicitly argues against in favor of Def 14).
- Drift: Citation points to the exact wrong definition — one that is about an unrelated topic the paper moves away from. Future readers who chase the citation will arrive at defeat-based conflict-free, not last-link preference.
- Recommendation: Change to "Modgil & Prakken 2018 Def 20 (p.21)".

#### Finding B.3 — `dung.py` citations accurate
- Severity: note (positive)
- File:line: `propstore/dung.py:32, 72, 135-136`
- Docstring says: "Modgil & Prakken 2018 Def 14: conflict-free uses attacks, not defeats" and "Defense is checked against defeats (Dung 1995 Def 6)."
- Paper evidence: `Modgil_2018.../notes.md:45` "attack-based conflict-free (Def 14, p.14)"; `Dung_1995.../notes.md:48` "Definition 6: Acceptability and Admissibility *(p.326)*".
- Match: yes. `dung.py` is a good example of load-bearing citations done right.

#### Finding B.4 — `opinion.py` Jøsang citations all match
- Severity: note (positive)
- All six explicit citations in `opinion.py` verified against `papers/Josang_2001_LogicUncertainProbabilities/notes.md`:
  - Def 6 p.5 expectation — opinion.py:72 — notes.md:46-52 — match.
  - Def 12 p.20-21 opinion→evidence — opinion.py:82 — notes.md:128-138 — match.
  - Theorem 6 p.18 negation — opinion.py:95 — notes.md:112 — match.
  - Theorem 3 p.14 conjunction — opinion.py:99 — notes.md:67 — match.
  - Theorem 4 p.14-15 disjunction — opinion.py:107 — notes.md:84 — match.
  - Def 10 p.9 ordering — opinion.py:127, 132 — notes.md:230 ("Opinion ordering *(p.9)*") — match.
  - Def 16 p.30 uncertainty maximization — opinion.py:158 — notes.md:190 — match.
- `opinion.py` is the gold standard for citation discipline in this codebase.

#### Finding B.5 — `aspic.py:797` build_arguments_for Def 5 citation matches
- Severity: note (positive)
- File:line: `propstore/aspic.py:797`
- Docstring says: "Modgil & Prakken 2018, Def 5 (pp.9-10): same argument structure as build_arguments(), but constructed top-down."
- Paper evidence: notes.md:41 "Construct arguments recursively from premises and rules (Def 5, p.9)". Match.

#### Finding B.6 — `revision/operators.py` has no module docstring
- Severity: med
- File:line: `propstore/revision/operators.py:1` (module-level)
- Current state: file begins with `from __future__ import annotations`. Zero module docstring. This is a load-bearing module (belief-base revision operators) in the revision pipeline.
- Drift: Not strictly drift (no doc to be wrong), but a gap that breaks the CLAUDE.md "cite at both docstring and inline levels" convention and the project's own `feedback_citations_and_tdd.md` memory entry.
- Recommendation: Add a module docstring citing Alchourrón-Gärdenfors-Makinson 1985 / Darwiche & Pearl 1997 theorems the module implements.

#### Finding B.7 — `conflict_detector/orchestrator.py` module docstring is one line
- Severity: low
- File:line: `propstore/conflict_detector/orchestrator.py:1`
- Current state: `"""Top-level conflict detection orchestration."""` and nothing else.
- Drift: Minimal doc for a load-bearing module that composes five conflict detectors (algorithm, equation, measurement, parameter, parameterization). No citation to relevant theory, no description of ordering/interaction semantics.
- Recommendation: Expand to 5-10 lines explaining the pipeline, the synthetic-concept injection at lines 34-59 (which is not obvious), and which conflict detectors are applied in what order.

#### Finding B.8 — `world/atms.py` module docstring has self-serial-numbered references
- Severity: low
- File:line: `propstore/world/atms.py:1-13`
- Docstring says: "Run 6 adds bounded stability and relevance analysis, and Run 7 adds bounded additive intervention planning..."
- Drift: "Run 6" and "Run 7" are internal workstream identifiers. A future maintainer reading this has no way to know what a "Run" is, how many there are, or whether more exist. The numbers are also likely to rot — Run 8/9/10 features may already exist.
- Recommendation: Remove the "Run N" shorthand and describe the capabilities directly. "Run 6" / "Run 7" are the transitional-implementation references that CLAUDE.md explicitly discourages.

### Category C — Paper citations

#### Finding C.1 — Modgil & Prakken 2018 "Def 1 (p.8)" is not Def 1, not p.8, and not what the quote says
- Docstring says: `aspic.py:55-57`, `:74`, `:91-93` — "Modgil & Prakken 2018, Def 1 (p.8): L is a logical language closed under the contrariness function"
- Paper says (via `pngs/page-003.png` and `pngs/page-007.png`): Def 1 is on p.4 and defines Dung-AF acceptability; Def 2 on p.8 defines the ASPIC+ argumentation system tuple. There is no definition anywhere in the paper that says "L is a logical language closed under the contrariness function". The closest is Def 2 which gives the signature `-: L → 2^L` and requires "each φ ∈ L has at least one contradictory".
- Match: no.
- Severity: crit.

#### Finding C.2 — Modgil & Prakken 2018 Def 13 cited for last-link
- Docstring says: `artifacts/documents/rules.py:120` — "last-link comparisons (Modgil & Prakken 2018 Def 13)"
- Paper says: `Modgil_2018.../notes.md:73` — "Last-link principle (Def 20) ... *(Def 20, p.21)*". Def 13 is defeat-based conflict-free.
- Match: no.
- Severity: high.

#### Finding C.3 — Jøsang 2001 Def 6, Def 10, Def 12, Def 16, Thms 3/4/6 all match
- Docstrings say: citations in `opinion.py` at lines 72, 82, 95, 99, 107, 127-136, 158-160.
- Paper says: `papers/Josang_2001_LogicUncertainProbabilities/notes.md` lines 46-52 (Def 6), 67 (Thm 3), 84 (Thm 4), 112 (Thm 6), 128-138 (Def 12), 190-199 (Def 16), 230 (Def 10).
- Match: yes (all six).
- Severity: note (positive).

#### Finding C.4 — Dung 1995 Def 6 for "defense is checked against defeats"
- Docstring says: `propstore/dung.py:136` — "Defense is checked against defeats (Dung 1995 Def 6)."
- Paper says: `Dung_1995.../notes.md:48` — "Definition 6: Acceptability and Admissibility *(p.326)*" — defines acceptability as defense via counter-attack.
- Match: yes.
- Severity: note (positive).

#### Finding C.5 — Modgil & Prakken 2018 Def 14 for attack-based conflict-free
- Docstring says: `propstore/dung.py:32, 72, 135`, `propstore/dung_z3.py:38` — "Modgil & Prakken 2018 Def 14: conflict-free uses attacks, not defeats".
- Paper says: `Modgil_2018.../notes.md:21, 45, 50` — "Revised conflict-free definition: Replaces defeat-based conflict-free (Def 13, p.14) with attack-based conflict-free (Def 14, p.14)".
- Match: yes.
- Severity: note (positive).

#### Finding C.6 — Diller 2025 Def 7 cited as "fact base is a finite set of ground atoms"
- Docstring says: `propstore/grounding/grounder.py:18-21` — "Section 3 (Definition 7, p.3): the fact base is a finite set of ground atoms".
- Paper says: `papers/Diller_2025_GroundingRule-BasedArgumentationDatalog/notes.md:62` — "Definition 7: Datalog Program *(p.3)*". Def 7 is the Datalog program, not the fact base. The fact base is at best Def 6 — but notes.md skips from Def 5 to Def 7, so Def 6 is not extracted.
- Match: partial — page number is right but the definition name and content do not match the notes. Cannot fully adjudicate because notes.md has no Def 6 entry.
- Severity: med — pending PDF reading to determine whether Def 6 (if it exists) is the fact base or the citation genuinely should be a different number.
- Recommendation: Have someone read the Diller 2025 PDF to determine the actual definition of fact base, or update grounder.py to cite what the paper actually says.

### Category D — papers/index.md vs filesystem

Summary:
- 210 paper directories exist under `papers/` (excluding `index.md`, `reports/`, `tagged/`, `tags.yaml`).
- 166 `## <Paper>` section headers in `index.md`.
- **44 paper directories have no index entry.**
- **0 index entries point to missing directories.**
- 183 of the 210 paper directories have a `notes.md` file.
- **25 paper directories have no notes.md at all.**

#### Orphan paper directories in `papers/` with no index entry (44)

```
Baroni_2019_GradualArgumentationPrinciples
Baumann_2019_AGMContractionDung
Bench-Capon_2003_PersuasionPracticalArgumentValue-based
Bjorner_2014_MaximalSatisfactionZ3
Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault
Buneman_2001_CharacterizationDataProvenance
Carroll_2005_NamedGraphsProvenanceTrust
Cayrol_2014_ChangeAbstractArgumentationFrameworks
Charwat_2015_MethodsSolvingReasoningProblems
Clark_2014_Micropublications
Cousot_1977_AbstractInterpretation
Diller_2015_ExtensionBasedBeliefRevision
Dreber_2015_PredictionMarketsEstimateReproducibility
Dunne_2009_ComplexityAbstractArgumentation
Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation
Eskandari_2016_OnlineStreamingFeatureSelection
Fichte_2021_Decomposition-GuidedReductionsArgumentationTreewidth
Gaggl_2012_CF2ArgumentationSemanticsRevisited
Gruber_1993_OntologyDesignPrinciples
Guha_1991_ContextsFormalization
Guha_1991_ContextsFormalizationApplications
Halpern_2000_CausesExplanationsStructural-ModelApproach
Järvisalo_2025_ICCMA20235thInternational
Kennedy_1997_RelationalParametricityUnitsMeasure
Lehtonen_2024_PreferentialASPIC
Mahmood_2025_Structure-AwareEncodingsArgumentationProperties
Niskanen_2020_ToksiaEfficientAbstractArgumentation
Nosek_2020_WhatIsReplication
Odekerken_2022_StabilityRelevanceIncompleteArgumentation
Pearl_2000_CausalityModelsReasoningInference
Pierce_2002_TypesProgrammingLanguages
Popescu_2024_AdvancingAlgorithmicApproachesProbabilistic
Popescu_2024_AlgorithmicProbabilisticArgumentationConstellation
Prakken_2010_AbstractFrameworkArgumentationStructured
Prakken_2012_ClarifyingSomeMisconceptionsASPICplusFramework
Rahwan_2009_ArgumentationArtificialIntelligence
Sarkar_2004_Nanopass
Sensoy_2018_EvidentialDeepLearningQuantify
Swanson_1986_UndiscoveredPublicKnowledge
Swanson_1996_UndiscoveredPublicKnowledgeTenYearUpdate
Tang_2025_EncodingArgumentationFrameworksPropositional
Toni_2014_TutorialAssumption-basedArgumentation
Verheij_2003_ArtificialArgumentAssistants
Vreeswijk_1997_AbstractArgumentationSystems
```

Severity: high. This breaks the CLAUDE.md invariant (line 41): "See `papers/index.md` for the full collection with descriptions and tags." The index is ~21% incomplete. Pearl 2000 (Causality), Pierce 2002 (Types and PL), Cousot 1977 (Abstract Interpretation), Clark 2014 (Micropublications), Guha 1991 (Contexts formalization), and Halpern 2000 (Causes) are all foundational references for this codebase and all silently missing from the index.

#### Orphan index entries with no matching directory (0)

None. (This is good — no one has index-entry ghosts pointing at deleted papers.)

#### Paper directories with no notes.md (25)

```
Bench-Capon_2003_PersuasionPracticalArgumentValue-based
Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault
Buneman_2001_CharacterizationDataProvenance
Carroll_2005_NamedGraphsProvenanceTrust
Charwat_2015_MethodsSolvingReasoningProblems
Cousot_1977_AbstractInterpretation
Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation
Eskandari_2016_OnlineStreamingFeatureSelection
Gaggl_2012_CF2ArgumentationSemanticsRevisited
Gruber_1993_OntologyDesignPrinciples
Guha_1991_ContextsFormalization
Guha_1991_ContextsFormalizationApplications
Kennedy_1997_RelationalParametricityUnitsMeasure
Knuth_1970_SimpleWordProblems
Mahmood_2025_Structure-AwareEncodingsArgumentationProperties
Odekerken_2022_StabilityRelevanceIncompleteArgumentation
Pierce_2002_TypesProgrammingLanguages
Popescu_2024_AdvancingAlgorithmicApproachesProbabilistic
Prakken_2012_ClarifyingSomeMisconceptionsASPICplusFramework
Rahwan_2009_ArgumentationArtificialIntelligence
Sarkar_2004_Nanopass
Sensoy_2018_EvidentialDeepLearningQuantify
Swanson_1986_UndiscoveredPublicKnowledge
Swanson_1996_UndiscoveredPublicKnowledgeTenYearUpdate
Toni_2014_TutorialAssumption-basedArgumentation
Verheij_2003_ArtificialArgumentAssistants
Vreeswijk_1997_AbstractArgumentationSystems
```

(Knuth_1970 contains only `metadata.json` and `paper.pdf` — it is essentially a stub.)

Severity: high. Per `research-papers:paper-reader` skill design and the project's citation-discipline memory entries, every paper that appears in the collection is supposed to carry an extracted `notes.md` so future citers can verify claims. Twenty-five papers cannot be verified this way. For Toni 2014 specifically, `aspic.py:814` cites "Toni (2014): ABA backward chaining" — there is no notes.md for Toni_2014_TutorialAssumption-basedArgumentation to cross-check against.

#### Small (likely-stub) notes.md files (under 100 lines)

```
 58 Lehtonen_2024_PreferentialASPIC/notes.md
 72 Diller_2015_ExtensionBasedBeliefRevision/notes.md
 76 Brewka_1989_PreferredSubtheoriesExtendedLogical/notes.md
 81 Baumann_2019_AGMContractionDung/notes.md
 88 Amgoud_2017_AcceptabilitySemanticsWeightedArgumentation/notes.md
 89 Ghidini_2001_LocalModelsSemanticsContextual/notes.md
 92 Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/notes.md
 94 Gabbay_2012_EquationalApproachArgumentationNetworks/notes.md
```

Severity: low-med. These are short but may still be complete depending on paper size. Flag only for spot-check.

### Category E — README / convention drift

#### Finding E.1 — README.md architecture diagram uses different layer numbering than CLAUDE.md
- Severity: low
- README.md claim (lines 9-17): 6 layers numbered Layer 1..6 from bottom ("Source Storage") to top ("Agent Workflow").
- CLAUDE.md claim (lines 30-37): 6 layers numbered 1..6 from bottom ("Source-of-truth storage") to top ("Agent workflow layer").
- Drift: The numbers align on this check (both 1 = storage, 6 = agent). But CLAUDE.md names Layer 2 "Concept/semantic layer" while README calls it "Theory / Typing". These names are doing different work — Concept/semantic has specific theoretical grounding (Fillmore, Pustejovsky, McCarthy, Buitelaar) that "Theory / Typing" discards. A reader who reads README first and CLAUDE.md second gets a substantially different sense of what Layer 2 is for.
- Recommendation: Reconcile the Layer 2 name. The CLAUDE.md framing is more load-bearing — README should adopt "Concept/semantic" and acknowledge the typing/CEL subsystem as implementation detail.

#### Finding E.2 — README table cites `aspic_bridge.py` as a key file (line 75)
- Severity: med (same underlying drift as A.3)
- README says: "`aspic_bridge.py`, `aspic.py`" in the "Key files" column for the `aspic` reasoning backend.
- Reality: `aspic_bridge.py` does not exist; `aspic_bridge/` package does.
- Recommendation: Same as A.3.

#### Finding E.3 — `docs/argumentation.md:30` points query_claim at a non-existent file
- Severity: med
- docs/argumentation.md says: "use `query_claim()` from `propstore/aspic_bridge.py`"
- Reality: `query_claim` is defined at `propstore/aspic_bridge/query.py:65`.
- Recommendation: Update to `propstore/aspic_bridge/query.py`.

#### Finding E.4 — `docs/data-model.md:332` same drift
- Severity: low
- docs/data-model.md says: "ASPIC+ rules via the bridge in `aspic_bridge.py`"
- Reality: bridge lives in the `aspic_bridge/` package, specifically `aspic_bridge/translate.py` for claims→literals / rules.
- Recommendation: Update.

#### Finding E.5 — `uv run pks build` verified
- Severity: note (positive)
- CLAUDE.md says (line 58): "Build: `uv run pks build`"
- Reality: `pks build` is registered in `propstore/cli/__init__.py:68` (`cli.add_command(build)`), with the implementation at `propstore/cli/compiler_cmds.py:210`.
- Match: yes.

## Hot-zones map

Drift density ranked highest to lowest:

1. **papers/index.md** — 44 orphan directories = 21% of the collection silently missing from the published index. (Category D)
2. **papers/*/notes.md absence** — 25 directories with no notes, breaking the verifiability chain for citations like Toni 2014 (cited in aspic.py), Pierce 2002, Pearl 2000, Clark 2014, Guha 1991. (Category D)
3. **aspic.py** — three docstrings (Literal, Literal.contrary, ContrarinessFn) all share the same incorrect "Def 1 (p.8)" citation. (Category B/C)
4. **CLAUDE.md lines 15, 35, 45** — mislocates ATMS/ASPIC-bridge/IC-merge (should point to `world/` and `aspic_bridge/`, not `repo/`), stale `aspic_bridge.py` file reference × 2. (Category A)
5. **README.md + docs/argumentation.md + docs/data-model.md + agent-papers.md + EXPLORATION_NOTES.txt** — shared stale `aspic_bridge.py` reference.
6. **artifacts/documents/rules.py:120** — Modgil 2018 Def 13 cited where Def 20 is meant.

## Most damaging drift

**Finding B.1 / C.1 — `aspic.py:55, 74, 91-93` cites Modgil & Prakken (2018) Def 1 (p.8) for the contrariness function.**

The paper's Definition 1 is on page 4 and is about Dung-AF acceptability — it has nothing to do with contrariness or languages. The content the docstring quotes is from Definition 2 (p.8), not Definition 1. This is the most damaging drift because:

1. It is in `aspic.py`, a load-bearing leaf module with zero internal imports that establishes the foundational ASPIC+ types the rest of the system composes.
2. The error is repeated three times in the same module, so a grepping maintainer sees a pattern and treats it as ground truth.
3. It cites the paper by name + definition + page, which invokes academic authority — the worst kind of wrong citation, because readers assume "they looked it up". But Def 1 says the opposite of what the docstring attributes to it.
4. This is exactly the failure mode CLAUDE.md warns about: "code is citing literature to add authority to something the literature doesn't say."
5. A future maintainer refactoring `Literal.contrary` who consults Def 1 to understand the invariant would read about `acceptability w.r.t. S` and be thoroughly confused about why the docstring cited it.

The fix is one line in three places: change "Def 1 (p.8)" to "Def 2 (p.8)" and adjust the quoted text.

## Open questions

- Diller 2025 Def 6 (fact base) — notes.md skips from Def 5 to Def 7, so I could not verify whether `grounder.py:18-21`'s citation ("Definition 7, p.3: the fact base is a finite set of ground atoms") aligns with Def 6 or is simply pointing at the wrong number. Needs a direct read of the Diller 2025 PDF. (Category C.6)
- Bonanno 2007 claim 9 "Backward Uniqueness" cited in `propstore/repo/branch.py:7-8`. Not spot-checked — paper has a notes.md but I did not open it.
- Darwiche & Pearl 1997 C1-C4 cited in `propstore/repo/branch.py:9-10`. Not spot-checked.
- Cayrol 2005 "derived defeats with fixpoint" cited in README.md:81. Notes.md exists (`papers/Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation/`) but not spot-checked.
- Sensoy 2018 cited in README.md:83 for evidence-to-opinion mapping — no notes.md exists for Sensoy_2018_EvidentialDeepLearningQuantify (in the 25-orphan list above). Cannot verify.
- Li et al. 2012 cited in README.md:76 for "Agresti-Coull stopping". I did not locate the Li 2012 paper in the collection; the name is ambiguous (two Li 20xx papers exist, neither 2012).
- Toni 2014 cited in `aspic.py:814` for "ABA backward chaining from claims to assumptions" — Toni_2014_TutorialAssumption-basedArgumentation has no notes.md (see Category D stubs). Unverifiable as-is.
- CLAUDE.md line 31 cites "(Fillmore 1982), generative lexicon theory (Pustejovsky 1991), context formalization (McCarthy 1993), ontology lexicalization (lemon/Buitelaar 2011), and micropublication structure (Clark 2014)." — Clark 2014 has a directory but no notes.md. McCarthy 1993 appears to exist under a different slug. Fillmore 1982, Pustejovsky 1991, Buitelaar 2011 were not spot-checked.
- Run 6 / Run 7 in `world/atms.py` docstring — the "Run" numbering scheme is not defined anywhere a fresh reader would find it. If more Runs have been added since that docstring was written, this is silent drift.
