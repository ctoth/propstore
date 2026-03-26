# Phase 3: Wire Opinion Algebra into relate.py

## GOAL
Replace fabricated _CONFIDENCE_MAP in relate.py with categorical_to_opinion() from calibrate.py, wire opinion fields through to sidecar.

## OBSERVATIONS

### Current state of relate.py
- `_CONFIDENCE_MAP` at lines 76-79: hardcoded lookup (pass_number, strength) -> float
- `_compute_confidence()` at lines 82-83: lookup wrapper
- `_classify_stance_async()` at lines 111-219: calls `_compute_confidence` at line 199, builds resolution dict at lines 203-210
- `write_stance_file()` at lines 464-485: writes stance dicts to YAML as-is
- No import of calibrate module currently

### Current state of build_sidecar.py
- `_populate_stances_from_files()` at lines 143-199: ALREADY has opinion columns in INSERT (lines 191-197)
- The schema ALREADY has opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate columns (from Phase 1)
- It reads `res.get("opinion_belief")` etc from the resolution dict

### What this means
- build_sidecar.py is ALREADY wired for opinion columns -- just needs the resolution dict from relate.py to contain them
- The main work is in relate.py: replace _CONFIDENCE_MAP/_compute_confidence with categorical_to_opinion call, add opinion fields to resolution dict

### calibrate.py
- `categorical_to_opinion(category, pass_number, calibration_counts=None)` -> Opinion
- Without calibration_counts: returns vacuous opinion with base_rate from _DEFAULT_BASE_RATES
- With calibration_counts: returns evidence-based opinion

### opinion.py
- `Opinion(b, d, u, a)` frozen dataclass
- `Opinion.vacuous(a=0.5)` -> (0, 0, 1, a)
- `Opinion.expectation()` -> b + a * u

### "none" stance handling
- Line 198-201 in relate.py: when stance_type == "none", confidence = 0.0
- Need to preserve this: none stances get 0.0 confidence

## DONE
- Read all 9 required files
- Understand the full data flow
- Tests written in tests/test_relate_opinions.py (14 tests, 2 fail as expected)
- Async tests use asyncio.run() pattern (no pytest-asyncio available)
- build_sidecar.py ALREADY has opinion columns in schema AND INSERT -- no changes needed
- conftest.py ALREADY has opinion columns in test schema -- no changes needed
- Added import of categorical_to_opinion to relate.py

## IN PROGRESS
- Replacing _CONFIDENCE_MAP and _compute_confidence in relate.py
- Need to: delete map+function, update _classify_stance_async to call categorical_to_opinion, add opinion fields to resolution dict

## NEXT
1. Delete _CONFIDENCE_MAP and _compute_confidence, add replacement comment
2. Update _classify_stance_async (around line 198-210)
3. Run tests -- all 14 should pass
4. Run full test suite (>= 1130)
5. Precommit + commit
6. Write report
