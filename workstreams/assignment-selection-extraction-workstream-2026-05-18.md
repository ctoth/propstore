# Assignment Selection Extraction Workstream

Date: 2026-05-18

## Goal

Extract assignment-selection merge into its own package and repository under
`ctoth`, using `../argumentation` as the package model.

Propstore should stop owning the assignment-selection algorithm. Propstore
should only adapt Propstore world/render policy data into the extracted package
model, call the package solver, and map the package result back into Propstore
resolution output.

## Current Inventory

The production implementation is currently split across these Propstore files:

- `propstore/world/assignment_selection_merge.py`
  - owns `claim_distance`;
  - owns observed candidate enumeration;
  - owns assignment/source distance scoring;
  - owns sigma, max, and gmax selection;
  - owns candidate tiebreak ordering;
  - owns `assignment_satisfies_mu`;
  - owns Propstore CEL constraint compilation through
    `check_condition_ir`, `scope_condition_registry`, and `ConditionSolver`;
  - imports assignment-selection model types from `propstore.world.types`.
- `propstore/world/types.py`
  - owns generic assignment-selection algorithm types:
    `MergeOperator`, `normalize_merge_operator`, `MergeAssignment`,
    `MergeSource`, `MergeAssignmentScore`, `AssignmentSelectionProblem`,
    and `AssignmentSelectionResult`;
  - owns Propstore render-policy constraint declarations:
    `IntegrityConstraintKind`, `IntegrityConstraint`,
    `integrity_constraint_from_dict`, and `integrity_constraint_to_dict`;
  - owns `RenderPolicy`, which carries Propstore policy declarations that are
    later compiled into runtime assignment-selection constraints.
- `propstore/world/resolution.py`
  - owns Propstore-specific active-claim filtering;
  - builds grouped source assignments from `ActiveClaim` rows;
  - derives automatic range and category constraints from Propstore concepts;
  - enriches CEL policy constraints with Propstore concept registries;
  - calls `solve_assignment_selection_merge` and maps winners back to a
    winning Propstore claim id.

The tests are currently:

- `tests/test_assignment_selection_merge.py`
  - contains the main algorithm contract and property tests;
  - contains CEL/Z3 integration tests;
  - contains current public API protection tests proving the solver is not
    exported from `propstore.storage`;
  - contains scalar oracle helpers used only by tests.
- `tests/remediation/phase_8_dos_anytime/test_T8_1_assignment_candidates_ceiling.py`
  - covers the candidate-enumeration ceiling path.
- `tests/test_resolution_helpers.py`
  - covers Propstore resolution integration and policy translation.
- `tests/test_render_contracts.py` and `tests/test_mapping_boundary_failures.py`
  - cover `RenderPolicy` and `IntegrityConstraint` mapping behavior.
- `tests/test_worldline_ic_merge_properties.py`
  - protects the separate generated IC-merge path from calling assignment
    selection.

## Target Architecture

Create a new GitHub repository:

- GitHub repo: `ctoth/assignment-selection`
- Python distribution: `assignment-selection`
- import package: `assignment_selection`
- local checkout while developing: `C:\Users\Q\code\assignment-selection`

The new package owns the pure assignment-selection domain and algorithms:

```python
class MergeOperator(StrEnum):
    SIGMA = "sigma"
    MAX = "max"
    GMAX = "gmax"


@dataclass(frozen=True)
class Assignment:
    values: Mapping[str, object]


@dataclass(frozen=True)
class SourceAssignment:
    source_id: str
    assignment: Assignment
    weight: float = 1.0


@dataclass(frozen=True)
class Constraint:
    concept_ids: tuple[str, ...]
    holds: Callable[[Assignment], bool]
    description: str | None = None


@dataclass(frozen=True)
class Problem:
    concept_ids: tuple[str, ...]
    sources: tuple[SourceAssignment, ...]
    constraints: tuple[Constraint, ...] = ()
    operator: MergeOperator = MergeOperator.SIGMA


@dataclass(frozen=True)
class CandidateScore:
    assignment: Assignment
    score: float | tuple[float, ...]


@dataclass(frozen=True)
class Result:
    winners: tuple[Assignment, ...]
    scored_candidates: tuple[CandidateScore, ...]
    admissible_count: int
    total_candidate_count: int
    reason: str | None = None
```

Names can be refined inside the new repo before Propstore pins it, but the
semantic boundary is fixed: the package owns assignments, source assignments,
runtime constraints, candidate enumeration, distance, scoring, and the solver.

The package does not import Propstore. The package does not import CEL,
`ConditionSolver`, `WorldStore`, `ActiveClaim`, `RenderPolicy`, or
`ConceptInfo`.

Propstore owns the Propstore adapter:

- `IntegrityConstraintKind`, `IntegrityConstraint`,
  `integrity_constraint_from_dict`, and `integrity_constraint_to_dict` stay in
  Propstore because they are Propstore render-policy declarations and include
  Propstore CEL policy data.
- Propstore compiles each `IntegrityConstraint` into an
  `assignment_selection.Constraint`.
- Propstore range and category policy declarations compile to typed runtime
  package constraints.
- Propstore CEL policy declarations compile through Propstore
  `check_condition_ir`, `scope_condition_registry`, and `ConditionSolver`, then
  pass a runtime predicate into the package.
- Propstore `ActiveClaim` rows are converted to package `SourceAssignment`
  objects at the resolution boundary.
- Propstore maps package `Result.winners` back to the winning active claim.

## Non-Goals

- Do not extract Propstore `WorldStore`, `ActiveClaim`, render policy,
  concept-row loading, CEL registry building, or resolution result mapping into
  `assignment-selection`.
- Do not keep `propstore.world.assignment_selection_merge` as a compatibility
  import path.
- Do not re-export package model classes from `propstore.world.types`.
- Do not pin Propstore to a local `assignment-selection` checkout.
- Do not move the unrelated artifact-level IC merge in
  `propstore/merge/merge_classifier.py`.
- Do not change the generated worldline IC-merge path except to update imports
  in tests that assert it stays separate.

## Execution Rules

- Work test-first and deletion-first.
- Move files when the change is actually a move. Use `git mv` for same-repo
  moves so Git sees the rename instead of a delete plus unrelated add.
- For cross-repository extraction, preserve the move intent explicitly: create
  the destination package file from the source file content, delete the
  Propstore-owned source path in the same extraction slice, and document the
  source path in the package commit message. Do not hand-retype moved code as
  an untraceable rewrite when a mechanical move is available.
- If replacing an interface, delete the old production surface first, then use
  type, search, and test failures as the work queue.
- Commit every intentional edit slice atomically with path-limited git
  commands.
- After every commit, reread this workstream before choosing the next slice.
- After every passing substantial targeted test run, reread this workstream
  before choosing the next slice.
- Use `uv run ...` for Python tooling.
- Use Propstore logged pytest wrappers for Propstore tests.
- Push `assignment-selection` changes first, then pin Propstore to a pushed
  immutable commit SHA or tag. Never pin to a local path or editable dependency.

## Dependency Order

Execute in this order:

1. New Repo Existence Check And Creation
2. Package Skeleton From Argumentation Pattern
3. Package Red Tests
4. Package Deletion-First Implementation
5. Propstore Red Tests
6. Propstore Adapter Replacement
7. Propstore Dependency Pin
8. Search Gates
9. Verification Gates

Before implementation, make this dependency order mechanically executable:
write or run an order check proving each dependent phase appears after its
prerequisites. If the order check fails, repair this workstream before editing
production code.

## Phase 1: New Repo Existence Check And Creation

From `C:\Users\Q\code\propstore`, verify the local target path and GitHub repo:

```powershell
Test-Path C:\Users\Q\code\assignment-selection
gh repo view ctoth/assignment-selection
```

If the local path exists, inspect it before writing. If the remote repo exists,
use it. If neither exists, create the remote and clone it:

```powershell
gh repo create ctoth/assignment-selection --public --clone=false --description "Assignment-selection merge algorithms and constraint models"
git clone https://github.com/ctoth/assignment-selection.git C:\Users\Q\code\assignment-selection
```

Repository creation is part of this workstream. Do not create a shadow copy of
Propstore. Do not initialize the package inside the Propstore repository.

## Phase 2: Package Skeleton From Argumentation Pattern

In `C:\Users\Q\code\assignment-selection`, create a normal `src/` Hatch
package patterned after `C:\Users\Q\code\argumentation`:

- `pyproject.toml`
- `README.md`
- `src/assignment_selection/__init__.py`
- `src/assignment_selection/model.py`
- `src/assignment_selection/solver.py`
- `tests/`

The `pyproject.toml` must use the same broad shape as `../argumentation`:

- `[project] name = "assignment-selection"`
- `requires-python = ">=3.11"`
- Hatchling build backend
- `[tool.hatch.build.targets.wheel] packages = ["src/assignment_selection"]`
- `[tool.pyright] include = ["src"]`
- `[tool.pytest.ini_options] testpaths = ["tests"]`
- dev dependencies include `pytest`, `pytest-timeout`, `hypothesis`, and
  `pyright`

The initial package public API should export the package-owned names from the
target architecture. It should not export Propstore-specific aliases.

## Phase 3: Package Red Tests

Move the pure algorithm tests out of Propstore and into
`C:\Users\Q\code\assignment-selection\tests`.

Use `git mv` only for test files whose ownership fully transfers to the new
package. If only part of a Propstore test file moves, copy the whole file into
the new package test suite, then edit both files: delete Propstore-only cases
from the package copy, and delete package-owned pure algorithm cases from the
original Propstore file so it remains the smaller Propstore adapter test file.
Do not move a mixed-ownership file and recreate the original from memory.

The package test suite owns:

- distance behavior for numeric and non-numeric values;
- candidate enumeration and candidate ceiling behavior;
- assignment/source distance;
- sigma, max, and gmax scoring;
- deterministic tiebreak behavior;
- no-admissible-assignment behavior;
- custom runtime predicate constraints;
- range and category runtime constraints;
- property tests for renamed concepts;
- property tests that every reported winner satisfies all constraints;
- property tests that reversing source order does not change winner sets when
  weights and assignments are equal.

Do not copy Propstore CEL registry tests into the package. Those remain
Propstore adapter tests because CEL compilation is Propstore-owned.

Run package red tests with:

```powershell
uv run pytest -vv
```

The expected red state is import failure or missing implementation inside the
new package. Red due to Propstore imports inside package tests is not accepted;
the package tests must target only `assignment_selection`.

## Phase 4: Package Deletion-First Implementation

Delete the algorithm ownership from Propstore before copying it into the new
package:

- delete `propstore/world/assignment_selection_merge.py`;
- remove package-owned model definitions from `propstore/world/types.py`:
  `MergeOperator`, `normalize_merge_operator`, `MergeAssignment`,
  `MergeSource`, `MergeAssignmentScore`, `AssignmentSelectionProblem`, and
  `AssignmentSelectionResult`;
- keep Propstore `IntegrityConstraintKind` and `IntegrityConstraint` in
  `propstore/world/types.py`.

Then implement the package from the failures. Preserve move intent where the
old file body becomes the new package body:

- move `claim_distance` to `assignment_selection.solver`;
- move candidate enumeration to `assignment_selection.solver`;
- move assignment distance and score sorting to `assignment_selection.solver`;
- move sigma, max, and gmax behavior to `assignment_selection.solver`;
- move problem/result validation into `assignment_selection.model`;
- use typed runtime constraints instead of Propstore metadata bags.

The package implementation must not import `propstore`.

Package gates:

```powershell
uv run pyright
uv run pytest -vv
```

Commit the package implementation in `C:\Users\Q\code\assignment-selection`.
Push the package commit:

```powershell
git push origin HEAD
git rev-parse HEAD
```

The SHA printed by `git rev-parse HEAD` is the only SHA allowed in the
Propstore dependency pin.

## Phase 5: Propstore Red Tests

Back in `C:\Users\Q\code\propstore`, add or update Propstore tests before
rewiring production code.

Propstore tests own:

- `RenderPolicy` serialization and mapping for `IntegrityConstraint`;
- automatic range/category constraint derivation from Propstore concepts;
- CEL policy constraints compiled through Propstore `ConditionSolver`;
- active claim grouping into package source assignments;
- duplicate source/concept rejection in the Propstore adapter;
- branch filtering and branch weights;
- mapping package winners back to exactly one winning claim id;
- no-admissible-assignment reason propagation;
- public API protection: `propstore.storage` does not export assignment
  selection solver or package model classes;
- old path protection: importing `propstore.world.assignment_selection_merge`
  fails.

Run targeted red Propstore tests through the logged wrapper:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label assignment-selection-red tests/test_resolution_helpers.py tests/test_render_contracts.py tests/test_mapping_boundary_failures.py
```

## Phase 6: Propstore Adapter Replacement

Create the Propstore adapter module:

- `propstore/world/assignment_selection_policy.py`

This module owns only Propstore-specific translation:

- `_concept_integrity_constraints`
- `_filtered_assignment_selection_claim_rows`
- `_integrity_constraint_concept_ids`
- `_cel_registry_for_concepts`
- `_enriched_policy_integrity_constraints`
- `_compile_integrity_constraint`
- `build_assignment_selection_problem`
- `resolve_assignment_selection_merge`

Move these responsibilities out of `propstore/world/resolution.py` or leave
`resolution.py` with only a thin call into this module. The adapter may import
`assignment_selection`. The adapter may import Propstore CEL and world types.
The package must not import the adapter.

Update `propstore/world/resolution.py` so the
`ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE` path calls the adapter and no
longer imports `propstore.world.assignment_selection_merge`.

Update tests to import package-owned algorithm types from
`assignment_selection`, not from `propstore.world.types`.

## Phase 7: Propstore Dependency Pin

After the package commit is pushed, pin Propstore to the pushed immutable SHA.

Add a direct dependency in `pyproject.toml` following the current
`formal-argumentation` pattern:

```toml
"assignment-selection @ git+https://github.com/ctoth/assignment-selection.git@<pushed-sha>",
```

Then update the lockfile:

```powershell
uv lock
```

Do not use a local path, editable install, local Git URL, Windows path, WSL
path, or `file://` URL.

## Phase 8: Search Gates

These searches must pass before the workstream is complete:

```powershell
rg -n -F -- "propstore.world.assignment_selection_merge" propstore tests
rg -n -F -- "from propstore.world.types import MergeOperator" propstore tests
rg -n -F -- "from propstore.world.types import MergeAssignment" propstore tests
rg -n -F -- "AssignmentSelectionProblem" propstore tests
rg -n -F -- "AssignmentSelectionResult" propstore tests
rg -n -F -- "solve_assignment_selection_merge" propstore tests
rg -n -F -- "_eval_cel_constraint_z3" propstore tests
rg -n -F -- "_scalar_assignment_selection_merge" propstore tests
rg -n -F -- "assignment-selection @ file" pyproject.toml uv.lock
rg -n -F -- "assignment-selection @ .." pyproject.toml uv.lock
rg -n -F -- "assignment-selection @ C:" pyproject.toml uv.lock
```

Allowed hits:

- `AssignmentSelectionProblem`, `AssignmentSelectionResult`, and solver names
  may appear in `workstreams/` and package dependency metadata only.
- `solve_assignment_selection_merge` may appear in the new
  `assignment-selection` repository.
- `IntegrityConstraint` hits remain allowed in Propstore because those are
  Propstore render-policy declarations.
- `ResolutionStrategy.ASSIGNMENT_SELECTION_MERGE` remains in Propstore because
  it is a Propstore strategy selector.

No production Propstore file may define or import the deleted solver module.
No Propstore test may import package-owned types from `propstore.world.types`.

## Phase 9: Verification Gates

Run package gates in `C:\Users\Q\code\assignment-selection`:

```powershell
uv run pyright
uv run pytest -vv
```

Run Propstore package-surface type checking:

```powershell
uv run pyright propstore
```

Run targeted Propstore tests through the logged wrapper:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label assignment-selection tests/test_resolution_helpers.py tests/test_render_contracts.py tests/test_mapping_boundary_failures.py tests/test_worldline_ic_merge_properties.py
```

Run the moved or remaining assignment-selection Propstore tests through the
logged wrapper only when they still exist as Propstore adapter tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label assignment-selection-adapter tests/test_assignment_selection_merge.py tests/remediation/phase_8_dos_anytime/test_T8_1_assignment_candidates_ceiling.py
```

If `tests/test_assignment_selection_merge.py` is fully deleted from Propstore,
replace that command with the exact adapter test file that now owns CEL and
resolution integration.

Run the full Propstore suite through the logged wrapper:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label assignment-selection-full
```

## Completion Criteria

This workstream is complete only when all of these are true:

- `ctoth/assignment-selection` exists.
- `C:\Users\Q\code\assignment-selection` is a normal `src/` Hatch package
  patterned after `../argumentation`.
- The package owns assignment-selection model types, runtime constraints,
  candidate enumeration, distance, sigma/max/gmax scoring, tiebreaking, and
  solver behavior.
- The package test suite owns the pure algorithm and property tests.
- The package has passing `uv run pyright` and `uv run pytest -vv`.
- The package commit has been pushed to GitHub.
- Propstore pins `assignment-selection` to the pushed immutable Git SHA in
  `pyproject.toml` and `uv.lock`.
- Propstore has no `propstore.world.assignment_selection_merge` production
  path.
- Propstore `world.types` no longer defines or re-exports package-owned
  assignment-selection model types.
- Propstore keeps `IntegrityConstraint` as a Propstore render-policy
  declaration and compiles it into package runtime constraints at the adapter
  boundary.
- Propstore assignment-selection resolution works through the adapter.
- Search gates pass with only the allowed hits.
- `uv run pyright propstore` passes.
- Required logged Propstore pytest gates pass.
