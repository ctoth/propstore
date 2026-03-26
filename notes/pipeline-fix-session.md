# Pipeline Fix Session

Date: 2026-03-25

## GOAL
Close propstore's broken pipeline loops: wire opinions, conflicts, decision criteria, preferences, COH, and PRAF worldline state.

## STATUS
- Plan approved at `~/.claude/plans/cheerful-jingling-waffle.md`
- 6 phases, foreman protocol, TDD (red agent then green agent per phase)
- Phases 1,2,3 independent; 4,5,6 sequential after those

## DONE
- Deep code read (notes/code-deep-read.md)
- Paper requirements read (notes/paper-requirements-deep-read.md)
- Infrastructure read (notes/infrastructure-deep-read.md)
- Wiring survey (notes/wiring-survey.md)
- Problem recheck after recent commits

## VERIFIED STATE (post-recheck)
- P0 vacuous pruning: FIXED (2a9013e)
- P1 inert opinions: STILL BROKEN (relate.py:196 no calibration)
- P2 conflicts disconnected: STILL BROKEN (argumentation.py:117 only stances_between)
- P3 decision criteria: STILL BROKEN (resolution.py:330 unused locals)
- P6 preferences: STILL BROKEN (preference.py:75 variable-length vectors)
- P7 P_A/tau: FIXED (e61342e)
- P8 PRAF worldline: STILL BROKEN (no branch in worldline_runner.py)
- P9 COH: NOT IMPLEMENTED

## PROGRESS

### Phase 3: Preferences — COMPLETE
- Red: commit 8128cf3 (5 failing, 3 passing)
- Green: commit 98468ba (all 1331 pass, 1 deselected pre-existing)
- claim_strength() now returns fixed 3-element [log_sample_size, inv_uncertainty, confidence]
- Neutral defaults: [0.0, 1.0, 0.5]
- Test fixtures updated in 4 files to provide all 3 metadata dimensions
- Pyright: SQLiteArgumentationStore missing `conflicts()` — pre-existing, will fix in Phase 2

### Phase 2: Conflicts→AF — COMPLETE
- Red: commit 82fd646 (4 failing, 1 passing)
- Green: commit 304c3e3 (all 1336 pass, 1 deselected pre-existing)
- Conflicts loaded from store.conflicts() in _collect_claim_graph_relations()
- Three-tier precedence: attack stances skip, non-attack stances block direction, orphan pairs synthesized
- Synthetic stances: rebuts, vacuous opinions (b=0, d=0, u=1, a=0.5)
- PHI_NODE/CONTEXT_PHI_NODE/COMPATIBLE correctly skipped
- Also fixed: Cayrol self-loop filter, Opinion.uncertainty property alias
- Note: pyright shows ProbabilisticAF/Opinion undefined in argumentation.py — lazy imports, not runtime errors

### Phase 4: Decision Criteria — COMPLETE
- Red: commit 0bab0a4 (2 failing, 3 passing)
- Green: commit b098be5 (all 1341 pass, 1 deselected pre-existing)
- apply_decision_criterion() wired as tiebreaker in _resolve_praf()
- Reads claim opinion components (b,d,u,a) when acceptance probs tie
- lower_bound/hurwicz/upper_bound now break ties per Denoeux 2019
- Pignistic ties remain ties (backward compat)
- Dead _decision_criterion locals removed from resolve()

### Phase 5: COH Constraint — COMPLETE
- Red: commit 63056aa (5 failing, 17 pre-existing pass)
- Green: commit 4150527 (22 praf tests pass, 18 integration pass)
- enforce_coh() added to praf.py
- Proportional scaling, iterative convergence (max 100 iters)
- Self-attacks enforce P(A) <= 0.5
- Inverts from_probability formula for correct expectation targeting
- Hypothesis property test confirms COH on random PrAFs

### Phase 6: Worldline PRAF State — COMPLETE
- Red: commit 89cf75a (2 failing, 29 pre-existing pass)
- Green: commit c500f45 (all pass)
- Added elif reasoning_backend=="praf" branch in worldline_runner.py
- Captures acceptance_probs, strategy_used, samples, semantics

## SUMMARY: 5 of 6 phases complete
- Phase 3 (preferences): DONE — 98468ba
- Phase 2 (conflicts→AF): DONE — 304c3e3
- Phase 4 (decision criteria): DONE — b098be5
- Phase 5 (COH): DONE — 4150527
- Phase 6 (worldline PRAF): DONE — c500f45
- Phase 1 (opinions): REMAINING — needs CorpusCalibrator wiring + calibration_counts schema

### Phase 1: Real Opinions — COMPLETE
- Red: commit c047d58 (5 failing, 2 guard pass)
- Green: commit 38152e0 (all 1355 pass, 1 deselected pre-existing)
- _classify_stance_async now accepts reference_distances and calibration_counts
- CorpusCalibrator fused with categorical opinion via consensus_pair (Josang 2001 Theorem 7)
- load_calibration_counts() added to calibrate.py
- calibration_counts table added to sidecar schema (starts empty — honest ignorance)
- Dogmatic opinion fusion guarded against division by zero

## ALL 6 PHASES COMPLETE

| Phase | Problem | Red Commit | Green Commit | Tests Added |
|-------|---------|------------|--------------|-------------|
| 3 | Preference incommensurability | 8128cf3 | 98468ba | 8 |
| 2 | Conflicts disconnected from AF | 82fd646 | 304c3e3 | 5 |
| 4 | Decision criteria dead code | 0bab0a4 | b098be5 | 5 |
| 5 | COH constraint unenforced | 63056aa | 4150527 | 5 |
| 6 | PRAF worldline state missing | 89cf75a | c500f45 | 2 |
| 1 | Inert opinion pipeline | c047d58 | 38152e0 | 7 |
| **Total** | | | | **32** |

Final test count: 1355 passed, 1 deselected (pre-existing hypothesis flake)

## FILES
- Plan: ~/.claude/plans/cheerful-jingling-waffle.md
- Notes: notes/code-deep-read.md, notes/paper-requirements-deep-read.md, notes/infrastructure-deep-read.md, notes/wiring-survey.md
