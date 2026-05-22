# Core Fixed-Point Iterations - 2026-05-21

Target architecture:

- Core files import concrete owner modules directly.
- Checked condition runtime paths use checked IR and hard failures instead of
  reparsing old condition sources through fallback branches.
- Semantic/runtime APIs keep typed domain objects past the IO boundary.

Forbidden surfaces:

- Package-level convenience imports that preserve broad re-export surfaces.
- Fallback, retry, compatibility, normalize, coerce, or old-shape branches that
  keep an obsolete production path alive.
- Hand-reparsed condition sources where checked IR should already carry the
  type and registry contract.

Search gates:

- `rg -n -F -- "from propstore.core.assertions import" propstore/core/activation.py`
- `rg -n -F -- "_retry_with_standard_bindings" propstore/core/activation.py`
- `rg -n -F -- "except Z3TranslationError" propstore/core/activation.py`
- `rg -n -F -- "claim_conditions.sources" propstore/core/activation.py`

Runtime gates:

- `powershell -File scripts/run_logged_pytest.ps1 tests/test_condition_runtime_no_reparse.py tests/remediation/phase_3_ignorance/test_T3_5_activation_unknown_cel.py`
- `uv run pyright propstore`

## Iteration 1 - `propstore/core/__init__.py`

Slice files read:

- `propstore/core/__init__.py`
- `propstore/context_lifting.py` as the caller exposed by the slice gate

Actions executed:

- `propstore/core/__init__.py`
  - Decision: `keep`.
  - Final owner: `propstore.core`.
  - Edit: none. The file is already a shallow package initializer with no
    eager imports and empty `__all__`.
  - Reason: package initializer does not preserve old production surfaces or
    pull unrelated runtime owners into core.
  - Gate: `rg -n -- "^(from|import)\s" propstore/core/__init__.py` is zero-hit.

- `from propstore.core import assertions as _assertions` in
  `propstore/context_lifting.py`
  - Decision: `delete`.
  - Final owner: concrete assertion reference module.
  - Edit: replaced the package-level import with
    `from propstore.core.assertions.refs import ContextReference` and updated
    typed uses.
  - Reason: package-level import kept a broad core convenience/re-export path
    alive. Callers must import the exact owner module.
  - Gate:
    `rg -n -- "propstore\.core import|from propstore\.core import" propstore tests`
    is zero-hit after the edit.

Gate results:

- Pass: no eager imports in `propstore/core/__init__.py`.
- Pass: `__all__` is empty.
- Pass: no `from propstore.core import ...` or `propstore.core import` callers
  remain under `propstore tests`.

Derived file disposition:

- `propstore/core/__init__.py`: `keep-file`.
- `propstore/context_lifting.py`: `split-file`; only the package-import surface
  was deleted in this iteration.

Next slice:

- Continue with the next tracked core file after
  `propstore/core/__init__.py`.

## Iteration 2 - `propstore/core/activation.py`

Slice files read:

- `propstore/core/activation.py`
- `propstore/core/assertions/__init__.py` as the re-export package used by the
  slice
- `propstore/core/conditions/registry.py` as the synthetic binding owner used by
  the slice
- `propstore/core/conditions/checked.py` and
  `propstore/core/conditions/solver.py` as the checked-condition/solver
  contracts for the fallback branch
- Activation and runtime condition tests that cover the slice gates

Actions executed:

- `from propstore.core.assertions import ContextReference` inside
  `claim_lifting_materializations`
  - Decision: `delete`.
  - Final owner: `propstore.core.assertions.refs`.
  - Edit: replaced the package-level assertion import with
    `from propstore.core.assertions.refs import ContextReference`.
  - Reason: the package import preserved a broad assertion re-export path.
    Callers must import the exact owner module.
  - Gate:
    `rg -n -F -- "from propstore.core.assertions import" propstore/core/activation.py`
    is zero-hit after the edit.

- `_retry_with_standard_bindings`
  - Decision: `delete`.
  - Final owner: none.
  - Edit: removed the helper.
  - Reason: `is_claim_active` already constructs a query solver with standard
    and environment bindings before asking the solver. Retrying after a solver
    translation error preserved a fallback path instead of honoring the checked
    condition registry contract.
  - Gate:
    `rg -n -F -- "_retry_with_standard_bindings" propstore/core/activation.py`
    is zero-hit after the edit.

- `except Z3TranslationError` branch in `is_claim_active`
  - Decision: `delete`.
  - Final owner: checked-condition solver hard failure.
  - Edit: removed the catch-and-reparse branch.
  - Reason: checked conditions already carry IR and registry fingerprint. A
    translation or fingerprint mismatch must surface from `ConditionSolver`
    instead of reparsing `claim_conditions.sources` under a new registry.
  - Gates:
    `rg -n -F -- "except Z3TranslationError" propstore/core/activation.py` and
    `rg -n -F -- "claim_conditions.sources" propstore/core/activation.py` are
    zero-hit after the edit.

- `tests/remediation/phase_3_ignorance/test_T3_5_activation_unknown_cel.py`
  fallback expectation
  - Decision: `rewrite`.
  - Final owner: activation boundary tests.
  - Edit: kept `UnknownConceptInCEL` coverage for unchecked environment
    assumptions and added a hard-failure assertion for checked-condition
    registry mismatch.
  - Reason: the previous test expected a mismatched checked condition to be
    reparsed into an unknown-concept error. The target contract is that checked
    IR registry mismatch surfaces from `ConditionSolver`; activation does not
    reinterpret it through an old fallback path.

Gate results:

- Pass: broad assertion package import gate is zero-hit.
- Pass: activation retry helper gate is zero-hit.
- Pass: `Z3TranslationError` fallback branch gate is zero-hit.
- Pass: claim-condition source reparse gate is zero-hit.
- Pass:
  `powershell -File scripts/run_logged_pytest.ps1 tests/test_condition_runtime_no_reparse.py tests/remediation/phase_3_ignorance/test_T3_5_activation_unknown_cel.py`
  completed with 5 passed. Log:
  `logs/test-runs/pytest-20260521-223824.log`.
- Pass: `uv run pyright propstore` completed with 0 errors, 0 warnings, 0
  informations.

Derived file disposition:

- `propstore/core/activation.py`: `rewrite`; fallback/reparse and broad import
  surfaces were deleted, activation ownership remains in core.

Next slice:

- Continue with `propstore/core/algorithm_stage.py`.

## Iteration 3 - `propstore/core/algorithm_stage.py`

Slice files read:

- `propstore/core/algorithm_stage.py`
- `propstore/world/queries.py` as the owner-layer caller of the stage filter
- `propstore/app/world.py` as the app request boundary
- `propstore/cli/world/query.py` as the CLI string parsing boundary
- `tests/test_algorithm_stage_types.py` and owner/CLI algorithm tests

Actions executed:

- `to_algorithm_stage`
  - Decision: `delete`.
  - Final owner: `AlgorithmStage` type constructor.
  - Edit: removed the helper and updated tests to use `AlgorithmStage(...)`
    directly.
  - Reason: the helper duplicated what the type already carries.
  - Gate: `rg -n -F -- "to_algorithm_stage" propstore tests` is zero-hit
    after the edit.

- `coerce_algorithm_stage`
  - Decision: `delete`.
  - Final owner: CLI request parsing and typed request objects.
  - Edit: removed the helper, changed `WorldAlgorithmsRequest.stage` and
    `AppWorldAlgorithmsRequest.stage` to `AlgorithmStage | None`, and converted
    the CLI `--stage` string with `AlgorithmStage(stage)` at the presentation
    boundary.
  - Reason: owner-layer world queries should receive the typed stage value, not
    coerce loose objects at runtime.
  - Gate: `rg -n -F -- "coerce_algorithm_stage" propstore tests` is zero-hit
    after the edit.

Gate results:

- Pass: old helper gates for `to_algorithm_stage` and
  `coerce_algorithm_stage` are zero-hit.
- Pass: `uv run pyright propstore` completed with 0 errors, 0 warnings, 0
  informations.
- Pass:
  `powershell -File scripts/run_logged_pytest.ps1 tests/test_algorithm_stage_types.py`
  completed with 3 passed. Log:
  `logs/test-runs/pytest-20260521-224127.log`.
- Pass:
  `powershell -File scripts/run_logged_pytest.ps1 tests/test_cli.py::TestWorldOwnerReports::test_owner_algorithms_report_empty_when_none tests/test_cli.py::TestWorldOwnerReports::test_world_algorithms_cli_reports_empty_inventory`
  completed with 2 passed. Log:
  `logs/test-runs/pytest-20260521-224158.log`.

Derived file disposition:

- `propstore/core/algorithm_stage.py`: `rewrite`; the file now contains only
  the branded semantic type.
- `propstore/world/queries.py`: `rewrite`; stage filter consumes typed request
  data directly.
- `propstore/app/world.py`: `rewrite`; app request carries the typed stage.
- `propstore/cli/world/query.py`: `rewrite`; CLI parses command text into the
  typed request.

Next slice:

- Continue with `propstore/core/aliases.py`.

## Iteration 4 - `propstore/core/aliases.py`

Slice files read:

- `propstore/core/aliases.py`
- `propstore/app/compiler.py` as the only production caller
- `propstore/families/concepts/stages.py` as the typed concept-record owner
- `propstore/families/identity/logical_ids.py` as the old dict helper used by
  the slice
- Alias export CLI and git-backend tests

Actions executed:

- `propstore/core/aliases.py`
  - Decision: `delete`.
  - Final owner: `propstore.app.compiler`.
  - Edit: removed the core module.
  - Reason: alias export is repository-bound app/compiler workflow code, not a
    core semantic type. Keeping it in core forced core to import repository and
    family-stage surfaces.
  - Gates: `Test-Path propstore/core/aliases.py` is false and
    `rg -n -F -- "propstore.core.aliases" propstore tests` is zero-hit after
    the edit.

- `export_concept_aliases`
  - Decision: `move`.
  - Final owner: `propstore.app.compiler.export_aliases`.
  - Edit: removed the extra helper and implemented the export loop directly in
    the app owner.
  - Reason: the public owner API is already `export_aliases`; a second core
    helper was only a misplaced wrapper.
  - Gate: `rg -n -F -- "export_concept_aliases" propstore tests` is zero-hit
    after the edit.

- Alias export payload inspection
  - Decision: `rewrite`.
  - Final owner: typed `ConceptRecord`.
  - Edit: app export now uses `parse_concept_record_document`,
    `record.primary_logical_id`, `record.canonical_name`, and
    `record.aliases` directly.
  - Reason: the old code converted the typed concept record back to a payload
    dict and then used a dict-shaped logical-id helper.

Gate results:

- Pass: deleted-file gate for `propstore/core/aliases.py`.
- Pass: old import gate for `propstore.core.aliases` is zero-hit.
- Pass: old helper gate for `export_concept_aliases` is zero-hit.
- Pass: `uv run pyright propstore` completed with 0 errors, 0 warnings, 0
  informations.
- Pass:
  `powershell -File scripts/run_logged_pytest.ps1 tests/test_cli.py::TestExportAliases::test_export_aliases_json tests/test_cli.py::TestExportAliases::test_export_aliases_text tests/test_git_backend.py::test_export_aliases_reads_git_head_not_worktree`
  completed with 3 passed. Log:
  `logs/test-runs/pytest-20260521-224402.log`.

Derived file disposition:

- `propstore/core/aliases.py`: `delete-file`.
- `propstore/app/compiler.py`: `rewrite`; owns the repository-bound alias export
  workflow and uses typed concept records.

Next slice:

- Continue with `propstore/core/analyzers.py`.

## Iteration 5 - `propstore/core/analyzers.py`

Moved argumentation analyzer orchestration to `propstore/argumentation.py`; deleted old `propstore.core.analyzers` path and updated callers.
Gates: old path zero-hit, deleted file absent, pyright pass, focused argumentation tests pass (`logs/test-runs/pytest-20260521-225159.log`).
Next: `propstore/core/anytime.py`.

## Iteration 6 - `propstore/core/anytime.py`

Kept `EnumerationExceeded`: it is the typed bounded-enumeration sentinel, not a shim/coercer/wrapper.
Gates: direct uses only, pyright pass, anytime enumeration tests pass (`logs/test-runs/pytest-20260521-225324.log`).
Next: `propstore/core/assertions/__init__.py`.
