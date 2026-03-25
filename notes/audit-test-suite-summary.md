# Test Suite Audit — 2026-03-24

## Summary

- **Collected:** 1251 tests
- **Passed:** 1249
- **Failed:** 2
- **Skipped:** 0
- **Warnings:** 0
- **Duration:** 224.35s (3m44s)

## Failures

### 1. `test_form_dimensions.py::TestDimensionsPropertyBased::test_invalid_dimension_keys_rejected`

**Root cause: Schema gap.** The test generates keys like `'A\n'` (letter followed by newline) and expects the JSON schema to reject them. The schema's `additionalProperties` pattern for dimension keys does not reject keys containing `\n`. The filter in the `@given` decorator considers `'A\n'` invalid (because `\n` is not alphanumeric or underscore), but the JSON schema accepts it — so `pytest.raises(ValidationError)` fails because no error is raised.

This is either a schema bug (dimensions pattern should anchor against whitespace/control characters) or a test bug (the test's filter is stricter than the schema intends). Most likely a **schema bug** — dimension keys containing newlines should not be valid.

**File:** `C:/Users/Q/code/propstore/tests/test_form_dimensions.py:383-399`

### 2. `test_form_dimensions.py::TestDimensionsPropertyBased::test_forms_with_same_dimensions_compatible`

**Root cause: Flaky timing.** Hypothesis generated dimensions `{'M': -1, 'N': -1, 'T': -3}` and the first run took 642ms, exceeding the default 200ms deadline. On retry it took 26ms. This is a cold-start penalty (first call to `load_form` is slow, likely due to schema loading or import overhead).

**Fix:** Add `deadline=None` or `deadline=timedelta(seconds=2)` to the `@settings` decorator.

**File:** `C:/Users/Q/code/propstore/tests/test_form_dimensions.py:401-424`

## Observations

- No tests are skipped — full coverage is being exercised.
- No pytest warnings were emitted.
- Both failures are in the same property-based test class using Hypothesis. The rest of the suite (1249 tests) is solid.
- No tautological tests were observed from the verbose output — test names accurately describe specific behaviors being validated (e.g., `test_rebut_blocked_when_weaker`, `test_z3_detects_numeric_overlap`, `test_override_propagates_to_derivation`). The test structure uses meaningful assertion patterns rather than trivially-true checks.
