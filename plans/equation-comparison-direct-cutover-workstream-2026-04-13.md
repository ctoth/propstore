# Equation Comparison Direct Cutover Workstream

Date: 2026-04-13
Status: proposed

Grounded in current repo review of:

- [propstore/equation_comparison.py](/C:/Users/Q/code/propstore/propstore/equation_comparison.py)
- [propstore/conflict_detector/equations.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/equations.py)
- [propstore/conflict_detector/collectors.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/collectors.py)
- [propstore/conflict_detector/models.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/models.py)
- [tests/test_equation_comparison.py](/C:/Users/Q/code/propstore/tests/test_equation_comparison.py)
- [tests/test_conflict_detector.py](/C:/Users/Q/code/propstore/tests/test_conflict_detector.py)
- [docs/conflict-detection.md](/C:/Users/Q/code/propstore/docs/conflict-detection.md)
- [docs/algorithm-comparison.md](/C:/Users/Q/code/propstore/docs/algorithm-comparison.md)
- [pyproject.toml](/C:/Users/Q/code/propstore/pyproject.toml)

## Goal

Replace the current unsafe, stringly, silently-failing SymPy parsing path in
`propstore.equation_comparison` with a strict, typed, deterministic equation
comparison subsystem that:

- never hands raw equation strings to SymPy parsing
- operates on typed `ConflictClaim` inputs, not dict-or-attr duck typing
- returns explicit comparison outcomes, not `None`
- uses deterministic canonicalization rather than `simplify()`
- caches parse and canonicalization results
- surfaces unsupported or malformed equations honestly to the caller
- adds a renaming-invariant structural signature for future analogical reasoning

This is a direct cutover. We control the stack, so there will be no
backwards-compatibility layer for the old `parse_expr` path.

## Why This Workstream Exists

The current implementation in
[propstore/equation_comparison.py](/C:/Users/Q/code/propstore/propstore/equation_comparison.py)
has five architectural problems:

1. it passes raw strings into `sympy.parse_expr`, which is not a safe boundary
   for untrusted input
2. it uses `simplify()` as the canonicalizer, which is heuristic and
   non-deterministic for our purposes
3. it imports SymPy inside every call and does no caching
4. it collapses many distinct failure modes to `None`, and the caller silently
   skips those pairs
5. it still carries generic dict-or-attr compatibility helpers even though the
   production path already normalizes equation claims to `ConflictClaim`

The current tests mostly pin "does not obviously explode" behavior. They do not
define a real typed contract for parse results, unsupported surfaces, or
comparison outcomes.

## Verified Constraints

The plan is shaped by the repo as it exists today.

Verified observations:

- production equation conflict detection only calls
  `canonicalize_equation(claim)` from
  [propstore/conflict_detector/equations.py](/C:/Users/Q/code/propstore/propstore/conflict_detector/equations.py)
- production equation claims are already normalized to typed
  `ConflictClaim` and `ConflictClaimVariable`
- `hypothesis` is already available in the dev dependency group
- `lark` is not currently a dependency
- the authored equation corpus is broader than plain arithmetic:
  it includes arithmetic formulas, function calls like `log(...)`, and also
  many symbolic surfaces such as `Piecewise`, `And`, `Or`, quantified/set
  notations, optimization notation, and other non-algebraic forms

This means the right architecture is:

- define a supported comparison subset explicitly
- compare only that subset
- mark everything else as `unsupported_surface`

It is not acceptable to pretend a tiny grammar can honestly compare the entire
current corpus.

## Scope

Primary production files:

- `propstore/equation_comparison.py`
- `propstore/conflict_detector/equations.py`
- `propstore/conflict_detector/collectors.py`
- `propstore/conflict_detector/models.py`
- `pyproject.toml`

Primary tests and docs:

- `tests/test_equation_comparison.py`
- `tests/test_conflict_detector.py`
- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`
- `tests/test_graph_export.py`
- `docs/conflict-detection.md`
- `docs/algorithm-comparison.md`

Likely new files:

- `propstore/equation_parser.py`
- `propstore/equation_types.py`
- `tests/test_equation_comparison_properties.py`

## Non-goals

- Do not broaden this into a whole-math-system redesign.
- Do not attempt arbitrary SymPy-language support.
- Do not preserve old and new parsing paths in parallel.
- Do not add regex hardening to the current `parse_expr` path as an
  intermediate production solution.
- Do not claim unsupported equations are comparable.
- Do not use raw dict payloads in the equation-comparison core after the typed
  cutover.

## Target Architecture

## Supported comparison language

The new comparison subsystem supports a strict equation language for algebraic
comparison:

- numbers
- named symbols drawn from declared equation variables
- binary operators: `+`, `-`, `*`, `/`, `^`
- unary `+` and `-`
- parentheses
- equality with exactly one relational operator
- a small explicit function allowlist

Initial function allowlist:

- `log`
- `ln`
- `exp`
- `sqrt`

We may extend the allowlist only when a concrete authored equation in the repo
requires it and the function is safe and deterministic to represent in the AST.

Out of scope for initial comparison support:

- inequalities
- chained equalities
- boolean connectives
- quantifiers
- piecewise expressions
- set-builder notation
- optimization syntax
- arbitrary SymPy constructors
- comprehensions or iterable notation

Those equations must fail explicitly as `unsupported_surface`.

## Parser boundary

Use a grammar-driven parser, preferably `lark`, for the supported language.

Rules:

- raw authored text is parsed into our own AST
- symbol resolution happens against declared `ConflictClaimVariable` bindings
- unknown symbols are hard failures
- duplicate or malformed relation tokens are hard failures
- SymPy never parses raw user strings

## Typed surfaces

Introduce explicit types for the equation subsystem.

Minimum typed objects:

- `EquationSymbolBinding`
- `EquationAst`
- `EquationSide`
- `EquationComparisonResult`
- `EquationNormalizationResult`
- `EquationFailure`
- `EquationFailureCode`

Minimum failure codes:

- `missing_variables`
- `missing_equation_text`
- `invalid_relation`
- `unknown_symbol`
- `parse_error`
- `unsupported_surface`
- `sympy_unavailable`

Result rules:

- successful normalization returns a canonical expression string and structured
  metadata
- failed normalization returns a typed failure with code and detail
- pair comparison returns an explicit outcome, not `str | None`

## Canonicalization

Canonicalization is deterministic and expression-class aware.

Baseline rule:

- normalize an equation to a canonical representation of `lhs - rhs`

Preferred pipeline:

1. convert our AST to SymPy expressions programmatically
2. build `diff = lhs - rhs`
3. use deterministic transforms such as:
   - `expand()`
   - `cancel()`
   - where needed, `cancel(expand(diff))`
4. serialize from the resulting SymPy expression

Do not use `simplify()` in the production canonicalization path.

## Structural signature

Keep concept-based grouping, but add a second structural signature derived from
the safe AST.

Required properties:

- independent of local symbol names
- stable under alpha-renaming
- cheap to hash and compare

Use:

- current concept-based signature for equation conflict grouping
- new structural signature for clustering and future analogical discovery

Do not switch conflict grouping to the structural signature in this workstream.

## Performance

Add:

- module-level lazy SymPy import
- cached safe parsing
- cached normalization

Suggested cache keys:

- normalized equation source text
- ordered symbol binding tuple
- normalization mode if more than one deterministic pipeline exists

## Error visibility

The conflict detector must stop silently treating parse failure as "nothing to
see here."

Required behavior:

- successful comparison still suppresses equivalent pairs
- failed normalization becomes explicit diagnostic information
- unsupported equations are visible as unsupported, not silently dropped

Exact reporting sink may be:

- typed diagnostics returned from comparison helpers and consumed by
  `conflict_detector/equations.py`
- build-time warnings
- stored sidecar text fields

The execution phase should choose the narrowest honest sink that integrates
cleanly with the current conflict detector.

## Direct-deletion rules

- delete `_claim_field` and `_variable_field`
- delete the raw `parse_expr` production path
- delete `simplify()`-based canonicalization
- delete `str | None` equation-normalization returns
- delete implicit fallback from malformed `sympy` to `expression` if the input
  is unsupported or invalid

No compatibility shim. Change the interface and update every caller.

## Commit Plan

The workstream should land as a sequence of small direct commits. The exact
count can move slightly, but the intended commit boundaries are:

### Commit 1: `test(equations): define strict typed comparison contract`

Add red tests for:

- typed failure codes instead of `None`
- explicit rejection of `==`, `<=`, `>=`, and chained `=`
- explicit unsupported classification for non-algebraic surfaces
- conflict detector behavior when comparison cannot proceed

### Commit 2: `refactor(equations): cut to typed claim and result surfaces`

Add the typed result objects and update callers/tests to use them.

Delete:

- dict-or-attr helpers
- generic `object` claim inputs in the core equation helpers

### Commit 3: `feat(equations): add safe grammar parser for algebra subset`

Add:

- `lark` dependency
- grammar
- AST builder
- symbol binding validation

Delete:

- raw SymPy parsing path

### Commit 4: `feat(equations): deterministic canonicalization without simplify`

Add:

- programmatic AST-to-SymPy conversion
- deterministic canonicalization pipeline

Delete:

- `simplify()` canonicalization
- `evaluate=False` divergence between paths

### Commit 5: `perf(equations): lazy-load sympy and cache normalization`

Add:

- lazy SymPy sentinel import
- parse and normalization caches
- targeted performance regression tests where practical

### Commit 6: `feat(conflicts): surface equation diagnostics honestly`

Update:

- `propstore/conflict_detector/equations.py`

So that:

- failed normalization is visible and typed
- equivalent normalized equations still suppress conflicts
- non-equivalent normalized equations still classify conditions normally

### Commit 7: `feat(equations): add alpha-invariant structure signatures`

Add:

- structural signature generation
- tests for renaming invariance

### Commit 8: `docs(equations): document strict supported subset and cutover`

Update docs to reflect:

- supported language
- unsupported surfaces
- deterministic canonicalization
- explicit diagnostics instead of silent skipping

## Execution Discipline

For each slice in this workstream:

1. add or update the failing tests first
2. run the red tests and keep the log
3. change types first
4. change behavior
5. delete the replaced production path in the same slice
6. run focused pytest
7. rerun the nearest broader suite
8. reread this workstream before choosing the next slice

Project rules:

- use `uv`, not bare `python`, `pip`, or `pytest`
- run pytest as `uv run pytest -vv`
- tee logs under `logs/test-runs/`
- assume PowerShell command syntax

## Phase Plan

### Phase 0: Baseline and Surface Inventory

Tasks:

1. run `uv sync --upgrade`
2. capture a focused baseline for current equation tests
3. inventory every production and test import of `canonicalize_equation` and
   `equation_signature`
4. inventory authored equation surfaces that fall outside the initial safe
   algebra subset

Suggested gate:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
uv run pytest -vv tests/test_equation_comparison.py tests/test_conflict_detector.py | Tee-Object -FilePath "logs/test-runs/$ts-equation-baseline.txt"
```

Exit criteria:

- baseline log exists
- unsupported authored-surface categories are enumerated

### Phase 1: Define the Contract in Tests

Tasks:

1. replace "None or exception is acceptable" tests with strict result-contract
   tests
2. add tests for exact failure-code classification
3. add conflict-detector tests that pin behavior for unsupported and malformed
   equations
4. add red tests for canonicalization consistency across all accepted inputs

Required new examples:

- `x = 2*y`
- `x == 2*y`
- `x <= 2*y`
- `a = b = c`
- `Eq(x, 2*y)` no longer accepted as executable input
- symbolic boolean/quantified surfaces classified as unsupported

Exit criteria:

- red tests define the strict contract
- no test still encodes "exception or None is fine"

### Phase 2: Cut to Typed Core Surfaces

Tasks:

1. add explicit equation result and failure dataclasses
2. change `equation_signature()` to accept `ConflictClaim`
3. change normalization helpers to accept typed `ConflictClaim`
4. delete `_claim_field` and `_variable_field`
5. update all callers and tests

Exit criteria:

- no equation core helper accepts untyped `object`
- no dict-or-attr helper remains in production code

### Phase 3: Add the Safe Parser

Tasks:

1. add `lark` to runtime dependencies
2. add grammar and AST builder for the supported subset
3. bind declared symbols to concepts through typed symbol bindings
4. reject unsupported syntax explicitly
5. delete all production uses of `sympy.parse_expr`

Required behavior:

- no raw equation string is ever parsed by SymPy
- unsupported surfaces are typed failures, not crashes

Exit criteria:

- `parse_expr` is gone from `propstore.equation_comparison`
- supported equations parse into our AST
- unsupported equations fail explicitly

### Phase 4: Deterministic Canonicalization

Tasks:

1. convert our AST to SymPy expressions programmatically
2. implement deterministic canonicalization of `lhs - rhs`
3. unify normalization across all accepted inputs
4. delete `simplify()` and the old explicit-`sympy` path divergence

Required tests:

- algebraically identical supported inputs normalize identically
- normalization is idempotent
- accepted inputs do not depend on `evaluate=False` quirks

Exit criteria:

- `simplify()` is no longer used in equation comparison
- accepted inputs share one canonicalization path

### Phase 5: Lazy Import and Caching

Tasks:

1. add module-level lazy SymPy loading
2. cache parsing and normalization
3. add focused tests for cache-safe deterministic behavior
4. verify no caller-visible behavior change from caching

Exit criteria:

- SymPy import no longer happens per call
- repeat normalization of the same equation is cached

### Phase 6: Honest Conflict-Detector Integration

Tasks:

1. replace silent `None` skipping in
   `propstore/conflict_detector/equations.py`
2. thread typed equation diagnostics into the pairwise comparison path
3. preserve current conflict semantics for successfully compared equations
4. make unsupported or malformed equations visible

Required tests:

- successful equivalent equations still do not emit conflict records
- successful non-equivalent equations still emit classified conflict records
- unsupported equations do not masquerade as compatibility

Exit criteria:

- the conflict detector no longer treats parser failure as silent success

### Phase 7: Structural Signature Layer

Tasks:

1. add AST-derived structural signature generation
2. add renaming-invariance tests
3. keep structural signature separate from current conflict grouping

Required tests:

- renaming symbols without changing structure preserves structural signature
- changing structure changes structural signature

Exit criteria:

- structural signatures exist and are tested
- production conflict grouping still uses the current concept signature

### Phase 8: Docs and Broader Validation

Tasks:

1. update equation-comparison docs and conflict-detection docs
2. document the supported comparison subset explicitly
3. document unsupported surfaces explicitly
4. rerun focused suites
5. rerun broader affected suites
6. rerun full pytest suite

Suggested targeted gate:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
uv run pytest -vv tests/test_equation_comparison.py tests/test_equation_comparison_properties.py tests/test_conflict_detector.py tests/test_build_sidecar.py tests/test_world_model.py tests/test_graph_export.py | Tee-Object -FilePath "logs/test-runs/$ts-equation-targeted.txt"
```

Suggested final gate:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
uv run pytest -vv | Tee-Object -FilePath "logs/test-runs/$ts-full-suite-equation-cutover.txt"
```

Exit criteria:

- docs match the new subsystem
- targeted suites are green
- full suite is green

## TDD Plan

The workstream is explicitly test-driven.

Per slice:

- write red tests first
- run the narrowest red command
- implement the smallest coherent production change
- run focused green tests
- then run the next broader safety net

Suggested red/green command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
uv run pytest -vv tests/test_equation_comparison.py -k "<slice selector>" | Tee-Object -FilePath "logs/test-runs/$ts-equation-slice.txt"
```

## Hypothesis Plan

Add a dedicated property file:

- `tests/test_equation_comparison_properties.py`

Required property families:

### Property A: Round-trip stability

Generate supported ASTs, pretty-print them, reparse them, and assert structural
equivalence.

### Property B: Canonicalization idempotence

For generated supported equations:

- normalize once
- normalize the canonical form again
- assert the canonical form is unchanged

### Property C: Alpha-renaming invariance

Generate supported equations and rename symbols while preserving declared
bindings. Assert:

- structural signature is unchanged
- canonicalization remains equivalent when concept bindings are preserved

### Property D: Equivalent rewrite invariance

Generate polynomial and rational forms plus equivalent rewrites, such as:

- operand commutation for `+` and `*`
- distributive rewrites
- factored versus expanded rational forms

Assert:

- canonical forms are equal

### Property E: Failure honesty

Generate token strings containing unsupported relation patterns or unsupported
operators and assert:

- normalization returns a typed failure
- failure code is one of the explicit rejected-surface codes

### Property F: Conflict classification symmetry

Generate pairs of successfully comparable equation claims and assert conflict
classification is symmetric under claim order.

Rules for property tests:

- keep strategies inside the supported language
- add a separate unsupported-language strategy for rejection properties
- do not use Hypothesis to generate arbitrary SymPy syntax

## Test Plan

Minimum targeted suites during execution:

- `tests/test_equation_comparison.py`
- `tests/test_equation_comparison_properties.py`
- `tests/test_conflict_detector.py`
- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`
- `tests/test_graph_export.py`

Likely broader supporting suites:

- `tests/test_validate_claims.py`
- `tests/test_sympy_generator.py`

Mandatory new regression coverage:

- explicit typed failures for malformed relations
- explicit typed failures for unsupported symbolic surfaces
- deterministic canonicalization of supported algebra
- lazy import and cache correctness
- conflict detector no longer silently skipping failed equation comparisons
- structural signatures stable under alpha-renaming

## Completion Criteria

This workstream is complete only when all of the following are true:

- raw SymPy parsing of authored equation strings is gone
- equation comparison accepts typed `ConflictClaim` inputs only
- equation normalization returns typed results, not `None`
- deterministic canonicalization has replaced `simplify()`
- lazy import and caching are in place
- unsupported or malformed equations are surfaced honestly
- a structural signature exists for alpha-invariant equation shape
- docs describe the supported subset and explicit unsupported cases
- focused suites are green
- full suite is green with logged output

## Explicitly Forbidden End States

- keeping `parse_expr` in the production equation comparison path
- wrapping `parse_expr` in more regexes and calling it "safe"
- supporting both typed-result and `None`-return paths in production
- letting the conflict detector silently skip malformed equations
- claiming comparison support for authored surfaces we still classify as
  unsupported
- preserving the current dict-or-attr helper path "for flexibility"
