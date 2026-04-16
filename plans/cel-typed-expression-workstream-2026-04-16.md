# CEL Typed Expression Workstream

Date: 2026-04-16
Status: completed
Builds on completed CEL cleanup tracks:

- `plans/cel-subsystem-unification-plan-2026-04-08.md`
- `plans/cel-registry-hardening-workstream-2026-04-14.md`
- `plans/semantic-carrier-convergence-workstream-2026-04-13.md`

## Goal

Make CEL expressions explicit semantic carriers instead of anonymous strings.

## Completion

Implemented on 2026-04-16.

Primary commits:

- `2d1166c` - `refactor(cel): add typed expression carriers`
- `d1f7c54` - `refactor(cel): cache checked z3 conditions`
- `88a7ced` - `refactor(cel): carry branded expressions through runtime`

Lifecycle documentation:

- `docs/cel-typed-expressions.md`

Target outcome:

1. Raw authored CEL text is branded as CEL source, not generic `str`.
2. Validated CEL is a real domain object with a constructor-backed invariant.
3. Runtime CEL paths consume checked or compiled CEL instead of reparsing loose
   strings wherever the caller already crossed a validation boundary.
4. CEL condition sets have a typed normalized representation.
5. The type system prevents accidental mixing of CEL, prose, SymPy formulas,
   SQL fragments, labels, and other string-valued domains.

This is a typing and boundary workstream. It does not redesign CEL syntax,
category semantics, registry construction, or the Z3 backend except where
small API changes are required to carry typed CEL objects through the existing
semantics.

## Baseline Assumption

This workstream assumes the earlier CEL unification and CEL registry hardening
tracks have already landed in production code.

In particular, this plan assumes:

- CEL registry projection already lives outside `propstore/cel_checker.py`
- canonical CEL projection is typed over `ConceptRecord`
- store/world CEL projection is typed over `ConceptRow`
- duplicate canonical names and duplicate concept IDs fail at registry
  construction
- no production caller outside CEL projection code manually constructs
  `ConceptInfo`
- Z3-backed CEL semantics are the production runtime semantics

If an older plan document still reports one of those workstreams as active,
treat that as stale plan metadata unless current code review proves otherwise.

## Why This Exists

CEL is currently treated as plain text across several production surfaces:

- claim document `conditions`
- concept relationship and parameterization `conditions`
- queryable assumptions
- activation bindings and effective assumptions
- conflict classification condition lists
- IC-merge integrity constraints
- Z3 parse and condition-set caches

But CEL is not free text. It has a grammar, type system, registry-dependent
name resolution, category semantics, runtime satisfiability semantics, and
condition-set normalization rules.

Keeping CEL as `str` loses all of that information at the type boundary. It
also lets unchecked strings reach runtime paths that should only accept CEL
known to have parsed and type-checked against the relevant registry.

## Core Decision

Use two different carriers:

1. `CelExpr` as a `NewType` over `str` for raw authored CEL source.
2. `CheckedCelExpr` as a frozen structured object for CEL that has parsed and
   type-checked against a specific CEL registry.

Do not use `NewType("CheckedCelExpr", str)` for validated CEL. A checked CEL
value has an invariant that must be created by validation, and the object needs
to carry enough context to keep that invariant honest.

## Type Model

### `CelExpr`

Raw authored CEL source.

Shape:

```python
CelExpr = NewType("CelExpr", str)
```

Meaning:

- this value is intended to be CEL
- no parse or type-checking guarantee is implied
- IO boundaries, CLI parsing, YAML decoding, and SQLite decoding may construct
  it from text

Allowed operations:

- serialize to string
- normalize condition sets by source text
- pass into parser/checker APIs

Forbidden implication:

- `CelExpr` does not mean valid CEL

### `ParsedCelExpr`

Optional intermediate object for syntax-valid CEL.

Shape:

```python
@dataclass(frozen=True)
class ParsedCelExpr:
    source: CelExpr
    ast: ASTNode
```

This type is useful if parser and checker APIs are separated. It is not
required if `CheckedCelExpr` construction parses internally.

### `CheckedCelExpr`

CEL source that parsed and type-checked against one registry identity.

Shape:

```python
@dataclass(frozen=True)
class CheckedCelExpr:
    source: CelExpr
    ast: ASTNode
    registry_fingerprint: CelRegistryFingerprint
    warnings: tuple[CelError, ...] = ()
```

Meaning:

- `source` parsed successfully
- all hard type errors were absent under the referenced registry
- warnings may remain available for diagnostics
- the checked value is only valid relative to the registry fingerprint it
  carries

Important rule:

- CEL validity is registry-relative. `valid_from >= 100` is valid only if
  `valid_from` is present and numeric/timepoint-like in the checked registry.

### `CheckedCelConditionSet`

Normalized checked condition conjunction.

Shape:

```python
@dataclass(frozen=True)
class CheckedCelConditionSet:
    conditions: tuple[CheckedCelExpr, ...]
    registry_fingerprint: CelRegistryFingerprint
```

Meaning:

- all member expressions were checked against the same registry fingerprint
- ordering is canonical
- duplicate source expressions are removed if condition-set semantics remain
  conjunction-only

This type should replace loose `list[str]`, `tuple[str, ...]`, and JSON-loaded
condition arrays in runtime paths after the validation boundary.

### `CompiledCelCondition`

Optional backend-specific runtime object.

Shape:

```python
@dataclass(frozen=True)
class CompiledCelCondition:
    checked: CheckedCelExpr
    backend: Literal["z3"]
    translated: object
```

This should remain inside the CEL runtime/backend module. Callers should not
depend on Z3 object shapes.

## Registry Identity

Validated CEL must carry a registry identity, not just a boolean "valid" flag.

Introduce an explicit type:

```python
CelRegistryFingerprint = NewType("CelRegistryFingerprint", str)
```

The fingerprint must change when any CEL-relevant registry fact changes:

- canonical name set
- concept IDs behind those names
- kind
- category values
- category openness
- synthetic binding definitions included in the registry

The first implementation may compute this from sorted `ConceptInfo` facts. It
does not need to be cryptographically important, but it must be deterministic
and complete for CEL semantics.

## Ownership

### New or Existing Module

Likely new module:

- `propstore/cel_types.py`

Owns:

- `CelExpr`
- `CelRegistryFingerprint`
- `ParsedCelExpr`
- `CheckedCelExpr`
- `CheckedCelConditionSet`
- constructor/coercion helpers that do not require checker internals

### Checker

`propstore/cel_checker.py`

Owns:

- tokenization
- parsing
- `ASTNode` and AST subclasses unless later split out
- `CelError`
- type-checking
- checked-expression construction if keeping construction close to checker

Preferred public APIs:

```python
def parse_cel(expr: CelExpr) -> ParsedCelExpr
def check_cel_expression(expr: CelExpr, registry: CelRegistry) -> tuple[CelError, ...]
def check_cel_expr(expr: CelExpr, registry: CelRegistry) -> CheckedCelExpr
def check_cel_condition_set(
    conditions: Sequence[CelExpr],
    registry: CelRegistry,
) -> CheckedCelConditionSet
```

### Z3 Backend

`propstore/z3_conditions.py`

Owns:

- checked-CEL-to-Z3 translation
- compiled condition cache
- condition-set cache
- satisfaction/disjointness/equivalence APIs

Preferred direction:

- runtime APIs accept `CheckedCelExpr` or `CheckedCelConditionSet`
- boundary APIs may accept `CelExpr` only when they explicitly validate before
  use

### Documents And IO

Authored YAML, JSON payloads, CLI arguments, and SQLite rows remain text at the
wire format.

Boundary decode should convert:

- `str -> CelExpr`
- `list[str] -> tuple[CelExpr, ...]`

Serialization should convert:

- `CelExpr -> str`
- `CheckedCelExpr.source -> str`

Do not serialize AST objects, Z3 objects, or checked-expression internals into
authored documents.

## Architectural Rules

1. No dual production paths.
   Once a surface is converted to typed CEL, update every production caller and
   delete the old loose-string path.

2. A checked type must be impossible to create accidentally.
   It must come from a checker/validator function, not from a public alias over
   `str`.

3. `CelExpr` is not validation.
   It is only a raw-source brand.

4. Registry-relative validity must be explicit.
   Do not create a global "valid CEL" type that hides the registry dependency.

5. Runtime consumers should ask for the strongest type they need.
   If a function requires a checked expression, type it that way.

6. IO boundaries may remain textual, but core semantic paths should not.

7. Keep warning semantics explicit.
   A checked expression may carry warnings; callers decide whether warnings are
   lint-only or fatal in their boundary.

8. Do not use compatibility shims to keep accepting both `str` and typed CEL in
   production APIs we control.

## Initial Target Surfaces

Convert in this order:

1. CEL checker and type definitions.
2. Claim and concept document condition fields at decoded boundary.
3. Compiler validation outputs for claim/concept conditions.
4. Z3 condition solver APIs and caches.
5. Activation condition extraction and binding/effective-assumption paths.
6. Conflict classification condition inputs.
7. IC-merge integrity constraints.
8. Queryable assumptions and ATMS future-analysis paths.
9. CLI parsing and display/report surfaces.
10. Docs and examples.

## Execution Sequence

### Phase T0: Freeze The Intended Type Boundary In Tests

Commit message:

- `test(cel): freeze typed expression boundary`

Work:

- add focused tests that raw CEL is represented as `CelExpr`
- add tests that checked CEL is produced only by checker construction
- add tests that checked CEL carries an AST and registry fingerprint
- add tests that checking the same source against different registries produces
  distinct fingerprints or fails as appropriate
- add tests that condition-set normalization preserves checked registry identity

Target suites:

- `tests/test_cel_checker.py`
- `tests/test_z3_conditions.py`
- add `tests/test_cel_types.py` if the type module is separate

Stop condition:

- the raw-vs-checked contract is expressed before converting production
  callers

### Phase T1: Add CEL Carrier Types

Commit message:

- `refactor(cel): add typed cel expression carriers`

Work:

- add `propstore/cel_types.py`
- define `CelExpr`, `CelRegistryFingerprint`, `ParsedCelExpr`,
  `CheckedCelExpr`, and `CheckedCelConditionSet`
- add helper constructors for raw source coercion and condition-set
  normalization
- keep the first slice minimal: no runtime path conversion yet unless required
  by tests

Acceptance:

- no production behavior changes
- type definitions and pure helpers are covered by tests

### Phase T2: Make Checker Produce Checked CEL

Commit message:

- `refactor(cel): return checked cel expressions from checker`

Work:

- update `parse_cel` or add a typed wrapper that returns `ParsedCelExpr`
- add `check_cel_expr(...) -> CheckedCelExpr`
- add `check_cel_condition_set(...) -> CheckedCelConditionSet`
- compute deterministic registry fingerprints from CEL registry facts
- keep `check_cel_expression(...)` only if still needed by callers during this
  phase, then remove or reduce it before closeout

Acceptance:

- checker construction is the only production way to obtain
  `CheckedCelExpr`
- hard errors prevent construction
- warnings are preserved on the checked object

### Phase T3: Convert Compiler And Validation Boundaries

Commit message:

- `refactor(cel): type checked conditions in compiler validation`

Work:

- convert claim `conditions` from raw decoded strings to `CelExpr` at document
  or compiler boundary
- validate claim conditions into checked condition sets during compilation
- validate concept relationship and parameterization conditions into checked
  condition sets during concept validation or registry-aware compilation
- preserve authored serialization as plain text

Acceptance:

- compiler validation no longer passes arbitrary `str` into CEL checker
- diagnostics still report source text and warning/error messages
- authored YAML payload shape is unchanged

### Phase T4: Convert Z3 Solver To Checked CEL

Commit message:

- `refactor(cel): make z3 solver consume checked expressions`

Work:

- update solver cache keys to use `CheckedCelExpr`/source plus registry
  fingerprint as appropriate
- update disjointness/equivalence/satisfaction APIs to accept
  `CheckedCelConditionSet` where callers have already validated
- keep any raw-source convenience function private to CEL boundary code
- delete production string-parse paths after callers are updated

Acceptance:

- Z3 runtime paths do not parse unchecked `str` from core callers
- cache identity is registry-aware
- existing CEL semantics tests remain green

### Phase T5: Convert Runtime Condition Users

Commit message:

- `refactor(cel): carry checked conditions through runtime paths`

Work:

- convert activation claim-condition extraction
- convert environment effective assumptions and binding-derived conditions
- convert conflict classification condition inputs
- convert IC-merge CEL integrity constraints
- convert queryable assumptions and ATMS future-analysis queryables

Acceptance:

- core runtime APIs no longer traffic in `list[str]` or `tuple[str, ...]` for
  CEL condition semantics
- string conversion is limited to IO/display boundaries
- no production dual acceptance of both raw strings and checked CEL remains

### Phase T6: Tighten Public APIs And Delete Loose Paths

Commit message:

- `refactor(cel): delete loose string cel runtime paths`

Work:

- remove temporary raw-string checker/solver overloads
- update type annotations across CEL-facing modules
- remove now-unused helper coercions
- search for remaining production `conditions: list[str]`,
  `conditions: tuple[str, ...]`, `cel: str`, and CEL-specific `Sequence[str]`
  surfaces
- keep raw `str` only at documented IO/display edges

Acceptance:

- production CEL runtime paths require `CelExpr`, `CheckedCelExpr`, or
  `CheckedCelConditionSet`
- no checked-CEL object can be constructed without validation

### Phase T7: Docs And Closeout

Commit message:

- `docs(cel): document typed cel expression lifecycle`

Work:

- document the lifecycle:
  - authored text
  - `CelExpr`
  - `CheckedCelExpr`
  - condition set
  - backend compilation
- update Python API docs for CEL-related types
- update CLI/docs only where user-visible behavior or error wording changes
- update related workstream docs if this plan completes or supersedes items

Acceptance:

- docs describe typed CEL as the production contract
- all phase checkboxes are complete or explicitly deferred by user direction

## Test Discipline

All pytest runs must go through the project wrapper:

```powershell
powershell -File scripts/run_logged_pytest.ps1 tests/test_cel_checker.py
```

Targeted suites:

- `tests/test_cel_checker.py`
- `tests/test_z3_conditions.py`
- `tests/test_condition_classifier.py`
- `tests/test_conflict_detector.py`
- `tests/test_ic_merge.py`
- `tests/test_atms_engine.py`
- `tests/test_claim_compiler.py`
- `tests/test_temporal_conditions.py`

Full-suite closeout:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label cel-typed-expression-full
```

## Search Closeout

Before declaring this workstream complete, search production code for:

```powershell
rg -n -F "cel: str" propstore
rg -n -F "conditions: tuple[str" propstore
rg -n -F "conditions: list[str" propstore
rg -n -F "Sequence[str]" propstore
rg -n -F "check_cel_expression(" propstore
rg -n -F "parse_cel(" propstore
```

Each remaining hit must be either:

- an IO/display boundary,
- a test-only helper,
- generic non-CEL string handling,
- or explicitly converted before closeout.

## Non-Goals

- changing CEL syntax
- replacing the current recursive-descent parser
- changing open/closed category semantics
- changing concept registry projection ownership
- serializing checked CEL into authored YAML
- exposing Z3 objects outside the CEL backend

## Open Design Questions

1. Should `ParsedCelExpr` be public, or should parsing remain an internal step
   of checked-expression construction?
2. Should warnings live on `CheckedCelExpr`, or should validation return a
   separate `CheckedCelResult` containing `checked` plus warnings?
3. Should registry fingerprinting live in `propstore/cel_types.py`,
   `propstore/cel_registry.py`, or the checker module?
4. Should queryable assumptions store only checked CEL after construction, or
   retain raw `CelExpr` plus a checked value generated in a specific world
   context?
5. Should binding-derived conditions be represented as checked CEL source, or
   as structured binding constraints that compile to CEL only for display?
