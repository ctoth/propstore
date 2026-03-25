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

## NEXT
- Establish test baseline
- Execute Phase 3 (preferences) first — smallest, cleanest, no dependencies
- Then Phase 2 (conflicts→AF)
- Then Phase 1 (opinions)
- Then Phase 4 (decision criteria)
- Then Phase 5 (COH)
- Then Phase 6 (worldline PRAF)

## FILES
- Plan: ~/.claude/plans/cheerful-jingling-waffle.md
- Notes: notes/code-deep-read.md, notes/paper-requirements-deep-read.md, notes/infrastructure-deep-read.md, notes/wiring-survey.md
