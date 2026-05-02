# IST Workstream Phase -1 Baseline - 2026-05-01

Workstream:
`plans/context-lifting-argumentation-gunray-workstream-2026-05-02.md`

Order check:

- `uv run scripts/check_workstream_order.py plans/context-lifting-argumentation-gunray-workstream-2026-05-02.md`
- Result: pass, `phase order ok: -1 -> 0 -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8`

Propstore baseline:

- Command: `powershell -File scripts/run_logged_pytest.ps1 -Label ist-workstream-baseline tests`
- Result: fail, 3425 passed, 2 skipped, 2 failed.
- Log: `logs/test-runs/ist-workstream-baseline-20260501-233519.log`
- Failures:
  - `tests/test_doc_drift_clean.py::test_referenced_propstore_paths_exist_or_docs_are_historical`
    reports `docs\argumentation-package-boundary.md:propstore/belief_set/`.
  - `tests/test_repository_artifact_boundary_gates.py::test_non_cli_production_modules_do_not_import_cli_repository`
    raised `FileNotFoundError` for
    `propstore/storage/_ws_n2_violation_05ffe97a624e47298e6fd9d7b96a9774.py`.
- Command: `uv run pyright propstore`
- Result: fail, 2 errors.
- Pyright failures:
  - `propstore/cel_checker.py:376:31`, passing `Expr` where `_check_in_call`
    requires `Call`.
  - `propstore/cel_checker.py:379:36`, passing `Expr` where
    `_check_ternary_call` requires `Call`.

Propstore worktree context before execution:

- The worktree already had unrelated modified production and test files in CEL,
  defeasibility, activation, ATMS, and z3 condition areas.
- The worktree also already had unrelated untracked notes, reports, logs, and
  temporary directories.
- These baseline failures are recorded before Phase 0; they are not evidence
  that the IST workstream changes have passed.

Dependency baselines:

- `../argumentation` HEAD: `9917d5b52e6c4a4935a7c646e8b45278762ff3ce`
  - `uv run pytest`: pass, 750 passed, 2 skipped.
  - `uv run pyright src`: fail, 8 errors.
  - Pyright areas: `aba_asp.py`, `aspic_encoding.py`, and
    `datalog_grounding.py`.
  - Worktree status: no tracked modifications; unrelated untracked notes,
    reports, `out`, `scratch`, and `pyghidra_mcp_projects/`.
- `../gunray` HEAD: `a06da9c06a8c20262edec56f8a1f55dc1901781d`
  - `uv run pytest`: pass, 243 passed, 293 skipped, 2 deselected.
  - `uv run pyright src`: pass, 0 errors.
  - Worktree status: no tracked modifications; unrelated untracked notes,
    reports, prompts, `out`, and `pyghidra_mcp_projects/`.
- `../belief-set` HEAD: `e5b11b8265dc688807a68aec3bc2f3bd9d537cc4`
  - `uv run pytest`: pass, 157 passed.
  - `uv run pyright belief_set`: pass, 0 errors.
  - Worktree status: no tracked modifications; unrelated untracked notes and
    `pyghidra_mcp_projects/`.

Inventory counts:

- `rg -n -F "can_lift(" propstore tests docs`: 8 hits.
- `rg -n -F "LiftingException" propstore tests docs`: 8 hits.
- `rg -n -F "LiftingMaterializationStatus" propstore tests docs`: 12 hits.
- `rg -n -F "LiteralKey" propstore tests`: 46 hits.
- `rg -n -F "belief_set" propstore/context_lifting.py propstore/aspic_bridge propstore/grounding`: 0 hits.
- `rg -n -F "can_lift" propstore/cli propstore/app C:\Users\Q\code\research-papers-plugin`: 1 hit.
- `rg -n -F "from argumentation" propstore tests docs`: 269 hits.

Inventory details:

- The CLI/app/research workflow `can_lift` hit is
  `propstore/app/micropubs.py:90`.
- Production `can_lift(` call sites are currently in
  `propstore/context_lifting.py`,
  `propstore/conflict_detector/parameterization_conflicts.py`,
  `propstore/conflict_detector/context.py`, and
  `propstore/app/micropubs.py`.
- `LiftingException` production sites are currently in
  `propstore/context_lifting.py`.
- `LiftingMaterializationStatus` production sites are currently in
  `propstore/context_lifting.py`, `propstore/core/activation.py`, and
  `propstore/worldline/runner.py`.

`argumentation.__init__` import baseline:

- File: `../argumentation/src/argumentation/__init__.py`
- Line count: 87.
- Current behavior: root package eagerly imports the package module inventory
  through `from argumentation import (...)`.
- Imported module names listed there: `af_revision`, `aba`, `aba_asp`,
  `aba_sat`, `accrual`, `adf`, `approximate`, `aspic`, `aspic_encoding`,
  `aspic_incomplete`, `backends`, `bipolar`, `caf`, `dfquad`, `dung`,
  `dynamic`, `enforcement`, `epistemic`, `equational`, `gradual`,
  `gradual_principles`, `iccma`, `labelling`, `llm_surface`, `matt_toni`,
  `partial_af`, `preference`, `probabilistic`, `practical_reasoning`,
  `ranking`, `ranking_axioms`, `sat_encoding`, `semantics`, `setaf`,
  `setaf_io`, `solver_differential`, `subjective_aspic`, `vaf_completion`,
  `vaf`, and `weighted`.
