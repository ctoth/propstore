# Equation Equivalence Extraction Workstream - 2026-05-17

Status: executable.

Goal: extract equation parsing, equation comparison, SymPy equation generation,
and their pure tests from Propstore into sibling repository `../eq-equiv`, then
make Propstore depend on the pushed immutable Git SHA.

The extraction is deletion-first. A Propstore module that re-exports,
wraps, aliases, or forwards the old `propstore.equation_*` or
`propstore.sympy_generator` surfaces is not an extraction.

## Current Evidence

Read-only discovery on 2026-05-17 found:

- `../eq-equiv` exists, is a Git repository on `master`, and has no files other
  than `.git`.
- `../eq-equiv` has no remote.
- `../ast-equiv` is a populated sibling repository with package
  `ast_equiv`, Hatch metadata, `README.md`, `LICENSE`, `uv.lock`, pytest tests,
  and a GitHub remote at `git@github.com:ctoth/ast-equiv.git`.
- `gh` is installed and authenticated as GitHub account `ctoth`.
- Propstore currently pins `ast-equiv` by immutable Git SHA in
  `pyproject.toml`.
- Propstore equation production surfaces are:
  - `propstore/equation_parser.py`
  - `propstore/equation_comparison.py`
  - equation/SymPy generation portions of `propstore/sympy_generator.py`
- Propstore equation callers include:
  - `propstore/conflict_detector/equations.py`
  - `propstore/conflict_detector/collectors.py`
  - `propstore/families/claims/storage.py`
  - `propstore/families/claims/passes/checks.py`
- Pure or mostly pure equation tests include:
  - `tests/test_equation_comparison.py`
  - `tests/test_equation_comparison_properties.py`
  - `tests/test_equation_orientation.py`
  - `tests/test_log_product_under_positive_reals.py`
  - `tests/test_exp_sum_under_reals.py`
  - `tests/test_sqrt_square_under_nonnegative_reals.py`
  - `tests/test_sympy_generator.py`
  - `tests/test_sympy_generator_no_lhs_drop.py`
- Propstore integration equation tests include:
  - `tests/test_equation_conflict_status.py`
  - `tests/test_equation_signature_role_invariance.py`
  - equation assertions inside `tests/test_bridgman_pi_signal_propagation.py`
  - the conflict-detector property currently embedded in
    `tests/test_equation_comparison_properties.py`

## Target State

`../eq-equiv` owns:

- equation expression AST dataclasses;
- equation symbol binding dataclasses;
- equation parser and renderer;
- equation failure/status/result dataclasses and enums;
- domain assumptions;
- equation normalization and comparison;
- concept-set grouping/signature helper over generic equation inputs;
- SymPy RHS and two-sided equation generation;
- symbol warning helper;
- all pure unit tests and Hypothesis/property tests for those surfaces;
- repository metadata, README, pyproject, lockfile, CI, license, and typing
  marker.

Propstore owns only:

- adapting `ConflictClaim` and `ConflictClaimVariable` to `eq_equiv` input
  types;
- conflict-detector integration behavior;
- claim storage/validation decisions about when to call equation generation;
- logged test wrappers and Propstore-specific integration gates.

Propstore must not contain:

- `propstore/equation_parser.py`;
- `propstore/equation_comparison.py`;
- `propstore/sympy_generator.py`;
- imports of `propstore.equation_comparison`;
- imports of `propstore.equation_parser`;
- imports of `propstore.sympy_generator`;
- duplicate pure equation tests that were moved to `../eq-equiv`.

## Target `eq-equiv` Layout

Create these files:

```text
../eq-equiv/
  .github/workflows/ci.yml
  .gitignore
  LICENSE
  README.md
  pyproject.toml
  uv.lock
  eq_equiv/
    __init__.py
    comparison.py
    parser.py
    sympy_generation.py
    py.typed
  tests/
    __init__.py
    test_comparison.py
    test_comparison_properties.py
    test_domain_assumptions.py
    test_orientation.py
    test_parser.py
    test_sympy_generation.py
```

`pyproject.toml` requirements:

- project name: `eq-equiv`;
- package: `eq_equiv`;
- Python: `>=3.11`;
- runtime dependencies: `lark>=1.2.2`, `sympy>=1.14.0`;
- dev dependencies: `pytest`, `hypothesis`, `pyright`;
- pytest marker: `property`;
- pyright include: `eq_equiv`;
- Hatch wheel package: `eq_equiv`.

CI must run:

```powershell
uv sync --all-extras --dev
uv run pytest
uv run pyright eq_equiv
```

## Public API

`eq_equiv.__init__` exports:

- `BinaryExpr`
- `DomainAssumption`
- `EquationClaimInput`
- `EquationComparison`
- `EquationComparisonStatus`
- `EquationExpr`
- `EquationFailure`
- `EquationFailureCode`
- `EquationNormalization`
- `EquationSymbolBinding`
- `FunctionExpr`
- `Integer`
- `NonNegative`
- `NumberExpr`
- `ParsedEquation`
- `Positive`
- `Real`
- `SymbolExpr`
- `SympyEquationGenerationResult`
- `SympyGenerationResult`
- `UnaryExpr`
- `canonicalize_equation`
- `check_symbols`
- `compare_equation_claims`
- `equation_signature`
- `generate_sympy_equation`
- `generate_sympy_rhs`
- `generate_sympy_rhs_with_error`
- `normalized_number_token`
- `parse_equation`
- `render_equation`
- `split_equation_relation`
- `structural_signature`

`EquationClaimInput` is the library-owned input shape:

```python
@dataclass(frozen=True)
class EquationClaimInput:
    expression: str | None = None
    sympy: str | None = None
    variables: tuple[EquationSymbolBinding, ...] = ()
```

The comparison layer accepts only `EquationClaimInput`. It must not import or
type-check against Propstore classes.

## Non-Goals

- Do not improve the algebraic decision procedure during extraction.
- Do not add backwards-compatible Propstore modules.
- Do not create a local path dependency in Propstore.
- Do not pin Propstore to an unpushed local commit.
- Do not duplicate pure tests in both repositories.
- Do not move Propstore conflict detection into `eq-equiv`.
- Do not move Bridgman dimensional checking into `eq-equiv`.
- Do not change claim artifact identity or storage schema beyond imports and
  generated SymPy values.

## Phase 0: Preflight

Repository: `propstore`.

Run:

```powershell
git status --short --branch
git status --short -- workstreams/eq-equiv-extraction-workstream-2026-05-17.md
rg -n -F "propstore.equation_comparison" propstore tests
rg -n -F "propstore.equation_parser" propstore tests
rg -n -F "propstore.sympy_generator" propstore tests
rg -n -F "equation_comparison" pyproject.toml README.md propstore tests
rg -n -F "equation_parser" propstore tests
rg -n -F "sympy_generator" propstore tests
rg -n -F 'file://' pyproject.toml uv.lock
rg -n -F 'path = "../' pyproject.toml uv.lock
rg -n -F 'editable = true' pyproject.toml uv.lock
```

Repository: `../eq-equiv`.

Run:

```powershell
git status --short --branch
git remote -v
Get-ChildItem -Force -Name
```

Required result:

- Propstore tracked dirty files are not touched by this workstream unless they
  are explicitly listed in later phases.
- `../eq-equiv` is the implementation repository.
- `../eq-equiv` has no remote before publication.
- no local dependency pins exist in Propstore dependency metadata.

## Phase 1: Build `eq-equiv` Package Skeleton

Repository: `../eq-equiv`.

Create:

- package directory `eq_equiv`;
- test directory `tests`;
- `.github/workflows/ci.yml`;
- `.gitignore`;
- `LICENSE`;
- `README.md`;
- `pyproject.toml`;
- `uv.lock`;
- `eq_equiv/py.typed`.

README must document:

- what the package does;
- supported equation surface;
- comparison outcomes: `EQUIVALENT`, `DIFFERENT`, `INCOMPARABLE`, `UNKNOWN`;
- domain assumptions and why unrestricted domain-sensitive identities return
  `UNKNOWN`;
- SymPy RHS generation versus two-sided equation generation;
- minimal API examples.

Gate:

```powershell
Push-Location ..\eq-equiv
uv sync --all-extras --dev
uv run pytest
uv run pyright eq_equiv
Pop-Location
```

Required result:

- package imports cleanly;
- CI file exists and runs pytest plus pyright;
- Hypothesis is available in the dev environment.

## Phase 2: Move Parser And Pure Parser Tests

Repository: `../eq-equiv` and `propstore`.

Delete first from Propstore:

- `propstore/equation_parser.py`.

Move into `../eq-equiv`:

- parser AST dataclasses;
- `EquationFailureCode`;
- `EquationFailure`;
- `EquationSymbolBinding`;
- parser grammar;
- `parse_equation`;
- `split_equation_relation`;
- `render_equation`;
- `normalized_number_token`;
- expression `structural_signature`.

Move pure parser tests from Propstore into `../eq-equiv/tests/`, including the
render/parse Hypothesis property tests from
`tests/test_equation_comparison_properties.py`.

Old-path gate in Propstore:

```powershell
rg -n -F "from propstore.equation_parser" propstore tests
rg -n -F "import propstore.equation_parser" propstore tests
rg -n -F "propstore.equation_parser" propstore tests
```

Required final hits: none.

Eq-equiv gate:

```powershell
Push-Location ..\eq-equiv
uv run pytest tests/test_parser.py tests/test_comparison_properties.py
uv run pyright eq_equiv
Pop-Location
```

## Phase 3: Move Comparison And Domain Tests

Repository: `../eq-equiv` and `propstore`.

Delete first from Propstore:

- `propstore/equation_comparison.py`.

Move into `../eq-equiv`:

- `EquationNormalization`;
- `EquationComparisonStatus`;
- `EquationComparison`;
- `DomainAssumption`, `Real`, `Positive`, `NonNegative`, `Integer`;
- normalization/cache logic;
- SymPy conversion and residual simplification;
- `canonicalize_equation`;
- `compare_equation_claims`;
- `equation_signature`.

Change the input contract to `EquationClaimInput`. Do not import Propstore under
`TYPE_CHECKING` or at runtime.

Move pure comparison tests from Propstore into `../eq-equiv/tests/`:

- pure parts of `tests/test_equation_comparison.py`;
- pure parts of `tests/test_equation_comparison_properties.py`;
- `tests/test_equation_orientation.py`;
- `tests/test_log_product_under_positive_reals.py`;
- `tests/test_exp_sum_under_reals.py`;
- `tests/test_sqrt_square_under_nonnegative_reals.py`.

Do not move Propstore conflict-detector tests into `eq-equiv`.

Old-path gate in Propstore:

```powershell
rg -n -F "from propstore.equation_comparison" propstore tests
rg -n -F "import propstore.equation_comparison" propstore tests
rg -n -F "propstore.equation_comparison" propstore tests
```

Required final hits: none.

Eq-equiv gates:

```powershell
Push-Location ..\eq-equiv
uv run pytest tests/test_comparison.py tests/test_comparison_properties.py tests/test_orientation.py tests/test_domain_assumptions.py
uv run pyright eq_equiv
Pop-Location
```

## Phase 4: Move SymPy Generation Surface And Tests

Repository: `../eq-equiv` and `propstore`.

Delete first from Propstore:

- `propstore/sympy_generator.py`.

Move into `../eq-equiv/sympy_generation.py`:

- `SympyGenerationResult`;
- `SympyEquationGenerationResult`;
- `generate_sympy_rhs_with_error`;
- `generate_sympy_rhs`;
- `generate_sympy_equation`;
- `check_symbols`;
- local-dict construction and constants/builtin handling.

Move tests:

- `tests/test_sympy_generator.py` to
  `../eq-equiv/tests/test_sympy_generation.py`;
- `tests/test_sympy_generator_no_lhs_drop.py` to
  `../eq-equiv/tests/test_sympy_generation.py` or a sibling pure test file.

Old-path gate in Propstore:

```powershell
rg -n -F "from propstore.sympy_generator" propstore tests
rg -n -F "import propstore.sympy_generator" propstore tests
rg -n -F "propstore.sympy_generator" propstore tests
```

Required final hits: none.

Eq-equiv gates:

```powershell
Push-Location ..\eq-equiv
uv run pytest tests/test_sympy_generation.py
uv run pyright eq_equiv
Pop-Location
```

## Phase 5: Propstore Adapter And Integration Tests

Repository: `propstore`.

Add Propstore-owned adapter code at the conflict-detector boundary. Acceptable
location:

- `propstore/conflict_detector/equation_inputs.py`

Owned responsibilities:

- convert `ConflictClaim` to `eq_equiv.EquationClaimInput`;
- convert `ConflictClaimVariable` to `eq_equiv.EquationSymbolBinding`;
- expose only Propstore integration helpers needed by conflict detection.

Update callers:

- `propstore/conflict_detector/equations.py`;
- `propstore/conflict_detector/collectors.py`;
- `propstore/families/claims/storage.py`;
- `propstore/families/claims/passes/checks.py`;
- tests that are genuinely Propstore integration tests.

Retain or create Propstore integration tests for:

- conflict detector skips equivalent orientations;
- conflict detector reports proven difference;
- conflict detector reports `UNKNOWN` for undecidable domain-sensitive pairs;
- equation signature ignores author-dependent role choice;
- Bridgman pi diagnostics do not make equations equivalent;
- claim storage/validation still calls RHS SymPy generation correctly.

Do not retain duplicate pure parser/comparison/generation tests in Propstore.

Propstore old-path gates:

```powershell
rg -n -F "propstore.equation_comparison" propstore tests
rg -n -F "propstore.equation_parser" propstore tests
rg -n -F "propstore.sympy_generator" propstore tests
rg -n -F "from eq_equiv import" ../eq-equiv
rg -n -F "propstore." ../eq-equiv/eq_equiv ../eq-equiv/tests
```

Expected result:

- first three commands: no hits;
- fourth command may have hits only in `../eq-equiv` tests or docs if examples
  require it; production code should import internally by package-relative
  modules;
- fifth command: no hits.

Propstore gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label eq-equiv-adapter tests/test_equation_conflict_status.py tests/test_equation_signature_role_invariance.py tests/test_bridgman_pi_signal_propagation.py tests/test_claim_roundtrip_fixtures.py
```

## Phase 6: Eq-Equiv Final Verification And Commit

Repository: `../eq-equiv`.

Run:

```powershell
git status --short --branch
uv run pytest
uv run pyright eq_equiv
git status --short
```

Then commit only intended `eq-equiv` source, tests, metadata, README, CI,
license, and lockfile.

Required result:

- all pure tests, including Hypothesis-backed property tests, live in
  `../eq-equiv`;
- `uv run pytest` runs Hypothesis tests as part of the normal suite;
- `uv run pyright eq_equiv` passes;
- no Propstore imports exist in `../eq-equiv/eq_equiv` or `../eq-equiv/tests`;
- generated diagnostics or caches are not committed.

## Phase 7: Publish Eq-Equiv With `gh`

Repository: `../eq-equiv`.

Create and push the remote:

```powershell
gh repo create ctoth/eq-equiv --public --source . --remote origin --push
git rev-parse HEAD
git remote -v
```

Record the pushed SHA exactly.

Required result:

- GitHub repository `ctoth/eq-equiv` exists;
- `origin` points to the GitHub repository;
- the recorded SHA is present on the remote;
- Propstore will pin to this immutable pushed SHA, not to a local path or
  unpushed commit.

## Phase 8: Pin Propstore To Eq-Equiv

Repository: `propstore`.

Before editing dependency metadata:

```powershell
rg -n -F 'file://' pyproject.toml uv.lock
rg -n -F 'path = "../' pyproject.toml uv.lock
rg -n -F 'editable = true' pyproject.toml uv.lock
```

All commands must return no local dependency pin hits.

Update:

- `pyproject.toml`
- `uv.lock`

Add:

```text
eq-equiv @ git+https://github.com/ctoth/eq-equiv@<pushed-sha>
```

Remove direct Propstore runtime dependencies only if no remaining Propstore
production code imports them directly:

- `lark`
- `sympy`

Search before removal:

```powershell
rg -n -F "import lark" propstore tests
rg -n -F "from lark" propstore tests
rg -n -F "import sympy" propstore tests
rg -n -F "from sympy" propstore tests
```

Gate:

```powershell
uv sync
uv run pyright propstore
```

## Phase 9: Propstore Test Movement Cleanup

Repository: `propstore`.

Delete moved pure test files or pure moved test bodies from Propstore.

Required deletions:

- pure parser/comparison/generation tests no longer live under `tests/`;
- Hypothesis parser/comparison tests no longer live under Propstore;
- only Propstore-specific adapter/integration tests remain.

No-duplication gates:

```powershell
rg -n -F "test_render_parse_round_trip" tests
rg -n -F "test_canonicalization_is_idempotent" tests
rg -n -F "test_structural_signature_is_invariant_under_alpha_renaming" tests
rg -n -F "test_equivalent_rewrites_normalize_identically" tests
rg -n -F "TestGenerateSympyRhs" tests
rg -n -F "test_equation_generator_preserves_distinct_left_hand_sides" tests
```

Expected result:

- no Propstore hits for pure moved test names;
- equivalent tests exist in `../eq-equiv/tests`.

Verification:

```powershell
Push-Location ..\eq-equiv
uv run pytest
uv run pyright eq_equiv
Pop-Location

uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label eq-equiv-propstore-targeted tests/test_equation_conflict_status.py tests/test_equation_signature_role_invariance.py tests/test_bridgman_pi_signal_propagation.py tests/test_claim_roundtrip_fixtures.py tests/test_conflict_detector.py
```

## Phase 10: Documentation And Metadata Sweep

Repository: `propstore`.

Update:

- `README.md` dependency table to include `eq-equiv`;
- any docs that describe equation comparison as Propstore-owned;
- any architecture or workstream done tests that pin old module ownership.

Old ownership gates:

```powershell
rg -n -F "propstore.equation_comparison" README.md docs propstore tests
rg -n -F "propstore.equation_parser" README.md docs propstore tests
rg -n -F "propstore.sympy_generator" README.md docs propstore tests
rg -n -F "equation_comparison.py" README.md docs propstore tests
rg -n -F "equation_parser.py" README.md docs propstore tests
rg -n -F "sympy_generator.py" README.md docs propstore tests
```

Expected result:

- no stale ownership references;
- references to `eq-equiv` describe it as the owner of equation parsing,
  comparison, and SymPy generation.

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label eq-equiv-docs tests/test_ws_o_ast_integration.py tests/test_workstream_p_done.py tests/test_conflict_detector.py
```

## Final Gates

Run all gates from a clean tracked-file base except task-owned commits.

Repository: `../eq-equiv`:

```powershell
git status --short --branch
uv run pytest
uv run pyright eq_equiv
git ls-remote origin HEAD
```

Repository: `propstore`:

```powershell
git status --short --branch
rg -n -F "propstore.equation_comparison" propstore tests README.md docs
rg -n -F "propstore.equation_parser" propstore tests README.md docs
rg -n -F "propstore.sympy_generator" propstore tests README.md docs
rg -n -F "from propstore.equation_comparison" propstore tests
rg -n -F "from propstore.equation_parser" propstore tests
rg -n -F "from propstore.sympy_generator" propstore tests
rg -n -F 'file://' pyproject.toml uv.lock
rg -n -F 'path = "../' pyproject.toml uv.lock
rg -n -F 'editable = true' pyproject.toml uv.lock
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label eq-equiv-final-targeted tests/test_equation_conflict_status.py tests/test_equation_signature_role_invariance.py tests/test_bridgman_pi_signal_propagation.py tests/test_claim_roundtrip_fixtures.py tests/test_conflict_detector.py tests/test_algorithm_sympy_tier_not_conflict.py
powershell -File scripts/run_logged_pytest.ps1 -Label eq-equiv-final-full
```

Expected final search results:

- no `propstore.equation_comparison` hits;
- no `propstore.equation_parser` hits;
- no `propstore.sympy_generator` hits;
- no local dependency pins;
- Propstore dependency points to
  `git+https://github.com/ctoth/eq-equiv@<pushed-sha>`.

## Completion Definition

This workstream is complete only when:

- `../eq-equiv` exists as a populated, pushed GitHub repository;
- `../eq-equiv` has README, license, pyproject, lockfile, CI, `py.typed`, source,
  and tests;
- `../eq-equiv` CI runs pytest, including Hypothesis tests, and pyright;
- parser, comparison, domain-assumption, and SymPy generation pure tests are
  moved from Propstore to `../eq-equiv`;
- Propstore retains only adapter/integration tests for equation behavior;
- no moved pure test remains duplicated in Propstore;
- `propstore/equation_parser.py` is deleted;
- `propstore/equation_comparison.py` is deleted;
- `propstore/sympy_generator.py` is deleted;
- Propstore callers use `eq_equiv` through explicit adapter or direct imported
  public APIs as appropriate;
- `../eq-equiv` has no Propstore imports;
- Propstore pins `eq-equiv` to an immutable pushed GitHub SHA;
- no local path, file URL, or editable dependency pin exists;
- all final Eq-equiv and Propstore gates pass.
