# Unit Phase 0: Replace hand-rolled conversion with pint

## GOAL
Replace hand-rolled UnitConversion/normalize_to_si/from_si with pint library, keeping function signatures identical.

## DONE
- Read prompt file and understood requirements
- Baseline: 16 existing tests pass in test_form_utils.py
- Step 1: Added pint dependency (v0.25.3) via `uv add pint`
- Step 2 (partial): Added two new RED tests:
  - test_pint_normalize_si_prefixes_automatic: THz -> Hz (THz not in common_alternatives)
  - test_pint_normalize_compound_unit: kPa -> Pa (kPa not in common_alternatives)

## FILES
- `propstore/form_utils.py` — contains normalize_to_si, from_si, UnitConversion (to be modified)
- `tests/test_form_utils.py` — test file (new tests added)
- `propstore/_resources/forms/frequency.yaml` — has kHz/MHz/GHz but NOT THz
- `propstore/_resources/forms/pressure.yaml` — has atm/bar/psi but NOT kPa

## NEXT
- Run RED tests to confirm they fail with current hand-rolled code
- Step 3: Replace internals with pint
- Step 4: Run full suite
- Step 5: Commit
- Write report to reports/unit-phase0-pint-report.md
