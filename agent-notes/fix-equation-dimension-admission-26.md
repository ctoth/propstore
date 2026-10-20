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

## Independent review and remaining owner blockers
- Independent full-diff/two-pass review completed at aa5d2ff5 and parser 5dd5da9;
  both review gates printed complete. That consumer head passed hosted CI with
  2091 tests and 4 skips. Output binding/implicit equality correction confirmed.
- Verified review's malformed m.attribute=m case through a stored claim: it
  escaped as AttributeError. Added it to expected parse failures and regression.
- Verified functional Eq(F,F) was reduced to True in parser; owner 43942105
  now disables evaluation during constructors and supplies an optional RHS
  output symbol. Hosted owner run 39510944625: 37 passed, typing zero errors.
- Consumer uses that owner API directly, with no raw SymPy constructors/imports
  or partial-typed symbol.name access. Corrected focused suite: 22 passed
  (16.28s), dimension-review-corrections-20261020-165110.log.
- Remaining reproduced substrate bugs (not merge-eligible): r=2^m accepts a
  mass-dimensional exponent when the base is dimensionless; F=0 is diagnosed
  as mismatch although Kennedy p.3 requires polymorphic zero. Stored repros:
  task-3/dimension-review-repro-_n3tdq19 and -xjevdzif. Bridgman owns these
  algebra rules; no consumer-side exception or replacement algebra was added.
- Bridgman remote master 3acb3c0 has an independent Rust rewrite; current consumer
  pin remains 5eb6118b/Python 0.2.0. Do not silently pull that rewrite into this
  focused validation draft. Parent must integrate the dimensional owner work.
- Next: exact-head CI and independent delta re-review; report eligibility and
  the concrete owner blockers. No PR/body/comment/issue mutation or merge.
- At 988264bc, hosted CI passed 2132 tests/4 skips. Delta review verified
  malformed input and functional Eq corrections, but reproduced one caller bug:
  __claim_output__(m) was shadowed by the synthetic output alias when reparsing.
- Fix the cause: both parses use only the authored symbol_names tuple; the
  synthetic output remains a dimensional binding and constructor argument.
  Expected parse exceptions are typed at both calls. Red log
  dimension-generated-alias-red-20261020-165900.log; all 23 focused cases now
  pass (15.00s), dimension-generated-alias-green-20261020-165943.log.
- Consumer package typing: 15 errors, comprising the prior 14 unchanged merge
  file errors and one newly reached unannotated Bridgman verify_expr input.
  Do not hide it with a consumer protocol, adapter, stub, or suppression.
- Continued under parent direction: integrated actual #332 merge
  3d15f12926a8f523ef425a6b11c6e75e8bddefd8 without rewriting branch history.
  Dependency acceptance file now has 37 cases. Old exact pins yielded 12 failed,
  25 passed (25.88s), log dimension-owner-boundaries-red-20261020-171648.log.
- Bridgman maintenance draft #14 corrects dimensional exponents, proven
  polymorphic zero, exact rational exponent trees and verify_expr annotation.
  Base remains the exact old Python 0.2 pin; no Rust rewrite adopted.
- Parser #2 rejects authored conditional/short-circuit/Piecewise and
  list/tuple/attribute selection before SymPy can erase operands. Unsupported
  syntax is quarantined as expression.invalid, including missing-symbol erasure.
- Exact new pins: owner 4caa723209444b7bcc2c0359a2fd2bd7188da31e and parser
  f05af3d49b0ed1bfa592bba4bd4f879e9c4e1141. Both owner CI runs are green;
  independent review and consumer final acceptance remain in progress.
- At 34caccec, all 37 focused cases passed; hosted CI39514238771 passed
  2175 tests/4 skips against the actual #332 merge. Package typing is now clean
  (zero errors), resolving both the 14 baseline errors and owner boundary error.
- Additional real authored case F = (lambda x: 0)(m+t) still erased the invalid
  argument and was admitted; failing regression is retained in log
  dimension-lambda-erasure-red-20261020-172729.log. Parser now rejects Lambda
  before evaluation at 2fc8674524b473d36761ec36836b711dc7189624. Add both invalid
  argument and unknown argument cases. Exact owner 4caa723 remains unchanged;
  refresh the parser pin and rerun the expanded 39-case consumer acceptance.
- Final expanded acceptance: 39 passed (26.98s), including both stored Lambda
  claims and authored/provenance retention. Log
  dimension-lambda-erasure-green-20261020-173044.log. Parser final hosted
  CI39515289950 passed 50 tests with typing zero. Owner review gate passed at
  exact 4caa723; parent retains final merge decision. Publish this final pin,
  obtain exact-head consumer CI/review, and do not merge or mark ready.
