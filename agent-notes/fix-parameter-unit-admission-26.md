# Parameter unit admission (#26)

## Goal

Execute the declared PARAMETER UnitFormCompatibilityCheck using checked concept/form evidence. Quarantine incompatible or unavailable required evidence, retain authored claims and provenance, and prevent an invalid rival parameter from crashing build-time comparison. No issue closure, external comments, merge, Ward, or unrelated refactor.

## State

Isolated branch `fix/parameter-unit-admission-26`, based on merged master `9048dbeb7de19d7ca69affa9817a6d7c7c1641ac`. No overlapping open validation PR. Existing algorithm/equation owner pins stay unchanged. Dependencies synced with the locked graph. Implemented the marker dispatch, checked-evidence resolution, owned unit compatibility and admitted-only comparison. Initial regression run: 10 failed/4 passed, including the exact kg-to-N build exception. First green run: 14 passed. Expanded valid controls plus existing scalar contract tests: 34 passed. Logs are under logs/test-runs/parameter-unit-*.

## Smallest design and evidence

Approximately 100 production lines plus focused tests: dispatch the existing unit marker, resolve the output's form through CompilationContext/FormCheckedRegistry, delegate compatibility to propstore.dimensions (Pint and form-declared conversions), and feed only ClaimCheckedBundle.checked_claims to derived conflict comparison. No conversion of authored values/units, parallel claim validator, or new storage representation.

The prior real repository reproduction admitted force parameters `1 N` and `1 kg`; validate reported OK, then build raised ValueError from dimensions.normalize_to_si during rival comparison. claim_contracts.py currently records UnitFormCompatibilityCheck as deferred. derived_build_plan._compile_conflicts currently uses RepositoryCheckedBundle.claims, which explicitly includes blocked claims.

Read current contract, form/claim pass, dimensions unit owner, value comparison, checked IR, docs/units-and-forms.md and docs/data-model.md. Visually read Kennedy (1997), original rendered page 2, sections 2.1–2.3: force M L T^-2, newton kg m s^-2, invalid cross-dimensional comparisons, compatible unit scales. Old documentation's retired module names/heuristics are not current implementation authority. Non-quantity forms retain scalar policies; missing checked evidence cannot be assumed dimensionless.

## Decisions and why

Required units apply to physical quantities; known category/boolean/structural forms have no numeric-unit obligation. Dimensionless quantities use the declared `1` default without mutating stored claims. Checked form canonical units and declared conversions supply conversion evidence; bare allowed-unit labels do not prove compatibility. Unknown/missing evidence gets an explicit diagnostic, not deferred success. The real compiler regression includes valid N and kN controls and incompatible kg with a rival, and checks provenance/ref preservation.

## Surprises

Blocking the claim alone does not protect the build: conflict comparison currently consumes blocked claims as well. The fix must correct that caller's input to the existing admitted claim view while retaining the complete projection set.

Dimensionless scaled units require normalization against `1` even when no unit_symbol is authored on the form; otherwise 100 percent versus 1 produces a false conflict. Corrected the existing normalization owner and comparison predicate, with a real build regression. Form extra_units use the existing Pint registration owner. Added malformed-unit controls reproduced TokenError (`N / (`) and Pint parser AssertionError (`N**`); the unit owner now returns incompatibility for these expected parse failures. The boundary run before that correction was 2 failed/22 passed.

## Next step

Publish the focused draft and read full hosted CI, correct any real integration failures without weakening the required unit evidence, and obtain independent review. Return exact head and eligibility to parent without merging.
