# Integration Plan Execution Notes
**Date:** 2026-03-17
**Goal:** Implement propstore + research-papers-plugin integration plan (Phases 0-7)

## Status
- Phase 0: Design Spikes — COMPLETE (3 claims.yaml files + report)
- Phase 1: Form Dimensions — COMPLETE (21 tests pass, 515 total, commits b84f0cf..31619ad)
- Phase 2: Package Rename — NOT STARTED
- Phase 3: Claim Notes Field — NOT STARTED
- Phase 4: Generator Script — NOT STARTED
- Phase 5: Extract-claims Skill — NOT STARTED
- Phase 6: Migration Tooling — NOT STARTED
- Phase 7: READMEs — NOT STARTED

## Baseline
- 494 tests, ALL PASSING on clean master (2026-03-17)
- 188 warnings (conflict_detector parameterization — pre-existing)

## Phase 0 Scout Findings (report: reports/phase0-scout-report.md)
- Claim schema: 5 types (parameter, equation, observation, model, measurement)
- Form schema: name, dimensionless, unit_symbol, qudt, base, parameters, common_alternatives, note
- 368 paper dirs in qlatt, 100+ with notes.md
- 3 diverse papers selected: Klatt_1980 (params), Fant_1985 (equations), Henrich_2003 (measurements)
- 11 form definitions exist in qlatt
- No claims.yaml files exist yet
- Schema gaps flagged: parameter table grouping, piecewise equations, measurement value/unit requirements
