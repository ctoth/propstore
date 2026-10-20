# Equation dimension admission (#26)

## Goal
Execute the remaining equation dimension obligation at the claim CHECKED
boundary through Bridgman, retaining authored claims and provenance.

## State
- Isolated branch fix/equation-dimension-admission-26 at master
  3a7726a65e332290fbfe0f4b6e646402971a6551. No overlapping open validation PR.
- Current validate_claim appends DimensionalConsistencyCheck to deferred_checks;
  ClaimCheckPass discards that obligation. verify_form_algebra has only direct
  test callers and conflates missing dimensions with a proven mismatch.
- Kennedy 1997, original rendered paper p. 2: additions/comparisons require
  equal dimensions; products and quotients compose base-dimension powers.

## Decisions and why
- Smallest complete slice: execute the declared equation check once with the
  existing checked form registry/concept bindings and Bridgman symbolic owner.
  Preserve unavailable inputs separately from negative algebra evidence.
- Existing human-to-sympy generation simplifies expressions, so dimensional
  execution must retain authored operations rather than check a simplified RHS.
  Inspect/use its parser owner; do not create an equation parser in Propstore.
- No Ward path, merge-family changes, storage filtering, or source mutation.

## Cleanup dispositions
- verify_form_algebra: dead/test scaffold, delete; generic algebra stays Bridgman.
- FormDefinition and form family file: keep canonical charter/storage owner.
- Raw form mapping at compilation-context entry: rewrite to checked registry
  owner, including repository and promotion callers; no parallel validator.
- Search gate: no verify_form_algebra references or deferred dimension success.
- Runtime gate: real claim pipeline plus validate/build artifact retention,
  distinct missing-evidence/mismatch dispositions, valid formulas still admitted.

## Next step
- Structurally valid regression fails at CHECKED: F=m*t yields no blocked claim
  with force M L T^-2, mass M, time T. Log
  equation-dimension-red-complete-fixture-20261020-162135.log.
- Removed only the test-only boolean facade and its four direct assertions.
  Its charter/storage file remains; generic algebra remains Bridgman.
- Added typed dimensional diagnostics, threaded the exact FormCheckedRegistry
  through repository/context/promotion callers, and consumed it once per claim.
- Parser-owner prerequisite draft: propstore/human-to-sympy#2,
  5dd5da9da95a5895e21e1671e14bb26da92d1c60. CI run 39508090612 passed all 35
  tests and package typing (zero errors). Initial return-type error corrected.
- Consumer focused regressions: 16 passed (35.37s), including canceled invalid
  addition, dimensional/default quantity forms, missing evidence, raw registry
  rejection, invalid-form abort, validate/build claim and provenance retention.
  Log equation-dimension-focused-20261020-163019.log.
- Publish focused draft; use real hosted full CI, then independent review.
  No merge authorized until parent integrates review. Issue #26 stays open.
- Initial draft #331 at 0038f8e7 passed hosted full CI run 39508825076.
- Self-check against world/queries.py derive_parameterizations exposed another
  real input: full m=m with output_concept=force and a mass-bound m passed.
  Red log dimension-output-red-20261020-163454.log. The output must have a used
  concept/symbol binding for a full equality. Do not compare its form with the
  RHS alone: human_to_sympy.numeric.evaluate_numeric solves implicit equalities
  for the output symbol, so F/m=a is valid even though its RHS is acceleration.
  Preserve one Bridgman check of the authored full relation. The missing output
  binding is unavailable evidence, not a proved dimensional mismatch.
- The implicit equation preservation and output-binding correction passed all
  18 then-current focused cases (16.82s), log
  dimension-output-binding-green-20261020-163824.log. Added explicit cases for
  full equalities without output annotations and bare RHS without output evidence.
