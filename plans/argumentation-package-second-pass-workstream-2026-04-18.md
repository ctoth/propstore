# Argumentation Package Second-Pass Workstream - 2026-04-18

## Objective

Finish extracting the remaining reusable formal argumentation kernels from
propstore into the external `argumentation` package, and polish the public
argumentation API so propstore consumes one coherent formal package rather than
several scattered propstore-local kernels.

The target architecture is direct:

```text
argumentation
  Dung AFs, ASPIC+, bipolar AFs, partial AFs, AF-level revision,
  probabilistic / quantitative AF kernels, generic semantics dispatch

propstore
  claim/source/context/storage/world projection, provenance, calibration,
  opinions, sidecar, worldline, CLI, and adapters into argumentation
```

This is not a transition plan. Each slice deletes the old propstore production
surface, updates every caller to the new `argumentation.*` surface, and moves
the owning tests with the code.

## Starting Point

The first extraction workstream already moved:

- `argumentation.dung`
- `argumentation.dung_z3`
- `argumentation.aspic`
- `argumentation.bipolar`
- `argumentation.preference`
- `argumentation.solver`

Propstore already imports those modules directly. No compatibility modules at
`propstore.dung`, `propstore.aspic`, `propstore.bipolar`, or
`propstore.dung_z3` should be recreated.

Remaining formal-adjacent code inspected on 2026-04-18:

- `propstore/storage/merge_framework.py`
- `propstore/storage/paf_queries.py`
- `propstore/storage/paf_merge.py`
- `propstore/belief_set/af_revision.py`
- `propstore/praf/components.py`
- `propstore/praf/treedecomp.py`
- `propstore/praf/dfquad.py`
- pure parts of `propstore/praf/engine.py`
- generic dispatch currently open-coded in `propstore/core/analyzers.py` and
  partial-AF query helpers

I did not run tests while drafting this workstream.

## Non-Negotiable Rules

- `argumentation` must import no `propstore` modules.
- Propstore must not keep old-path production shims, wrapper modules, alias
  modules, or fallback import paths for moved kernels.
- Delete the old propstore production surface first in each slice, then use
  search, type-check, and tests as the work queue.
- Move tests with the code they actually specify.
- Do not move propstore projection, provenance, opinion, calibration, sidecar,
  world, worldline, storage commit, or CLI code into `argumentation`.
- Do not move code that still imports propstore.
- If a kernel needs a propstore type only as a small interface, replace it with
  an argumentation-owned protocol or value object before moving.
- If a slice cannot converge without compatibility glue, fully revert that
  slice and record the blocker.
- Use logged pytest wrappers for propstore test runs.

## Target Package Scope

After this workstream, the external package should include:

```text
argumentation/
  src/argumentation/
    partial_af.py
    af_revision.py
    probabilistic.py
    semantics.py
```

Public imports should look like:

```python
from argumentation.partial_af import PartialArgumentationFramework
from argumentation.partial_af import enumerate_completions
from argumentation.partial_af import sum_merge_frameworks

from argumentation.af_revision import ExtensionRevisionState
from argumentation.af_revision import diller_2015_revise_by_framework

from argumentation.probabilistic import ProbabilisticArgumentationFramework
from argumentation.probabilistic import compute_probabilistic_acceptance

from argumentation.semantics import extensions
from argumentation.semantics import accepted_arguments
```

Propstore should import those surfaces directly where it needs them. Propstore
should not re-export them as propstore-owned formal APIs.

## Propstore-Owned Surfaces

These stay in propstore:

- `propstore/claim_graph.py`
- `propstore/structured_projection.py`
- `propstore/aspic_bridge/`
- `propstore/core/analyzers.py`
- `propstore/defeasibility.py`
- `propstore/fragility_scoring.py`
- `propstore/fragility_contributors.py`
- `propstore/praf/projection.py`
- claim-to-probability and stance-to-probability calibration
- `propstore/opinion.py`
- `propstore/provenance/`
- `propstore/support_revision/`
- `propstore/belief_set/agm.py`
- `propstore/belief_set/iterated.py`
- `propstore/belief_set/ic_merge.py`
- `propstore/world/`
- `propstore/worldline/`
- `propstore/storage/merge_commit.py`
- CLI modules

## Phase 0 - Baseline And Cut List

Status: pending

Record the exact current import surface before moving code.

Required searches:

```powershell
rg -n -F "propstore.storage.merge_framework" propstore tests docs
rg -n -F "propstore.storage.paf_queries" propstore tests docs
rg -n -F "propstore.storage.paf_merge" propstore tests docs
rg -n -F "propstore.belief_set.af_revision" propstore tests docs
rg -n -F "propstore.praf" propstore tests docs
rg -n -F "compute_praf_acceptance" propstore tests docs
```

Required baseline tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-second-pass-baseline `
  tests/test_paf_core.py `
  tests/test_paf_queries.py `
  tests/test_paf_merge.py `
  tests/test_af_revision_postulates.py `
  tests/test_dfquad.py `
  tests/test_treedecomp.py `
  tests/test_treedecomp_differential.py `
  tests/test_praf.py `
  tests/test_praf_integration.py
```

If baseline failures are unrelated to this workstream, document them in the
workstream before cutting code. Do not treat a failing unrelated baseline as
proof that the extraction is complete.

## Phase 1 - Extract Partial Argumentation Frameworks

Status: pending

Move the pure partial-AF kernel out of propstore storage.

Move to `argumentation.partial_af`:

- `PairState`
- `PartialArgumentationFramework`
- `enumerate_paf_completions`, renamed to `enumerate_completions`
- `merge_framework_edit_distance`
- `consensual_expand`
- `sum_merge_frameworks`
- `max_merge_frameworks`
- `leximax_merge_frameworks`
- skeptical and credulous completion-based queries

Delete from propstore:

- `propstore/storage/merge_framework.py`
- `propstore/storage/paf_queries.py`
- `propstore/storage/paf_merge.py`

Move or split tests:

- `tests/test_paf_core.py` -> `argumentation/tests/test_partial_af.py`
- `tests/test_paf_queries.py` -> `argumentation/tests/test_partial_af_queries.py`
- `tests/test_paf_merge.py` -> `argumentation/tests/test_partial_af_merge.py`

Update propstore callers to import from `argumentation.partial_af`.

Acceptance in `argumentation`:

```powershell
rg -n -F "propstore" src tests
uv run pyright src
uv run pytest -vv tests/test_partial_af.py tests/test_partial_af_queries.py tests/test_partial_af_merge.py
```

Acceptance in propstore:

```powershell
rg -n -F "propstore.storage.merge_framework" propstore tests docs
rg -n -F "propstore.storage.paf_queries" propstore tests docs
rg -n -F "propstore.storage.paf_merge" propstore tests docs
rg -n -F "enumerate_paf_completions" propstore tests docs
powershell -File scripts/run_logged_pytest.ps1 -Label partial-af-cutover `
  tests/test_repo_merge_object.py `
  tests/test_structured_merge_projection.py `
  tests/test_merge_cli.py `
  tests/test_merge_report.py
```

The old path searches must return no live production or test imports.

## Phase 2 - Extract AF-Level Revision

Status: pending

Move AF-level revision into `argumentation.af_revision`.

Current blocker:

- `propstore/belief_set/af_revision.py` imports
  `propstore.belief_set.language.Formula`.

Target replacement:

```python
class ExtensionConstraint(Protocol):
    def atoms(self) -> frozenset[str]: ...
    def evaluate(self, extension: frozenset[str]) -> bool: ...
```

Move to `argumentation.af_revision`:

- `AFChangeKind`
- `ExtensionConstraint`
- `ExtensionRevisionState`
- `ExtensionRevisionResult`
- `baumann_2015_kernel_union_expand`
- `diller_2015_revise_by_formula`
- `diller_2015_revise_by_framework`
- `cayrol_2014_classify_grounded_argument_addition`

Delete from propstore:

- `propstore/belief_set/af_revision.py`

Update callers and tests to import from `argumentation.af_revision`.

Move or split tests:

- pure AF-revision portions of `tests/test_af_revision_postulates.py` move to
  `argumentation/tests/test_af_revision.py`
- any tests asserting propstore `belief_set.language` integration stay in
  propstore and adapt a propstore formula into the `ExtensionConstraint`
  protocol

Acceptance in `argumentation`:

```powershell
rg -n -F "propstore" src tests
uv run pyright src
uv run pytest -vv tests/test_af_revision.py
```

Acceptance in propstore:

```powershell
rg -n -F "propstore.belief_set.af_revision" propstore tests docs
rg -n -F "from propstore.belief_set import AFChangeKind" propstore tests docs
powershell -File scripts/run_logged_pytest.ps1 -Label af-revision-cutover `
  tests/test_af_revision_postulates.py `
  tests/test_worldline_revision.py `
  tests/test_revision_af_adapter.py
```

## Phase 3 - Extract Probabilistic And Quantitative AF Kernel

Status: pending

Extract a pure probabilistic argumentation kernel without propstore opinions,
provenance, rows, or calibration.

Target `argumentation.probabilistic` model:

```python
@dataclass(frozen=True)
class ProbabilisticArgumentationFramework:
    framework: ArgumentationFramework
    argument_probabilities: Mapping[str, float]
    direct_defeat_probabilities: Mapping[tuple[str, str], float]
    attack_probabilities: Mapping[tuple[str, str], float] | None = None
    supports: frozenset[tuple[str, str]] = frozenset()
    support_probabilities: Mapping[tuple[str, str], float] | None = None
    base_defeats: frozenset[tuple[str, str]] | None = None
```

The kernel accepts probabilities, not `Opinion` objects. Propstore is
responsible for converting opinions to expectations before constructing the
kernel object.

Move to `argumentation.probabilistic`:

- probabilistic AF value object
- probabilistic result type
- connected-component decomposition
- exact enumeration
- Monte Carlo sampling with Agresti-Coull stopping
- exact DP / tree decomposition for the supported grounded defeat-only domain
- DF-QuAD / QBAF strength functions
- strategy normalization for the pure kernel

Keep in propstore:

- `NoCalibration`
- `p_arg_from_claim`
- `p_relation_from_stance`
- opinion payload decoding
- provenance creation
- row coercion
- `propstore/praf/projection.py`
- analyzer/worldline integration

Delete or empty as production kernel surfaces:

- pure computation ownership in `propstore/praf/engine.py`
- `propstore/praf/components.py`
- `propstore/praf/treedecomp.py`
- `propstore/praf/dfquad.py`

Propstore `build_praf_from_shared_input` should become an adapter that returns
`argumentation.probabilistic.ProbabilisticArgumentationFramework` plus
propstore-owned omission/calibration metadata. `analyze_praf` should call
`argumentation.probabilistic.compute_probabilistic_acceptance` directly.

Move or split tests:

- pure parts of `tests/test_dfquad.py`
- pure parts of `tests/test_treedecomp.py`
- pure parts of `tests/test_treedecomp_differential.py`
- pure parts of `tests/test_praf.py`

Keep in propstore:

- `tests/test_praf_integration.py`
- tests that use `propstore.opinion.Opinion`
- tests that use propstore stances, claim rows, analyzers, stores, or
  worldline result capture

Acceptance in `argumentation`:

```powershell
rg -n -F "propstore" src tests
uv run pyright src
uv run pytest -vv `
  tests/test_probabilistic.py `
  tests/test_dfquad.py `
  tests/test_treedecomp.py `
  tests/test_treedecomp_differential.py
```

Acceptance in propstore:

```powershell
rg -n -F "from propstore.praf.dfquad" propstore tests docs
rg -n -F "from propstore.praf.treedecomp" propstore tests docs
rg -n -F "from propstore.praf.components" propstore tests docs
rg -n -F "compute_praf_acceptance" propstore tests docs
powershell -File scripts/run_logged_pytest.ps1 -Label probabilistic-af-cutover `
  tests/test_praf_integration.py `
  tests/test_worldline_praf.py `
  tests/test_core_analyzers.py `
  tests/test_dfquad.py `
  tests/test_praf.py
```

The `compute_praf_acceptance` search must return no propstore-owned production
entry point. Propstore callers should use the argumentation function name
directly after building the pure kernel object.

## Phase 4 - Add Generic Semantics API Polish

Status: pending

Add `argumentation.semantics` as a convenience API over the formal kernels.

Target API:

```python
def extensions(framework: object, *, semantics: str) -> tuple[frozenset[str], ...]: ...

def accepted_arguments(
    framework: object,
    *,
    semantics: str,
    mode: str = "credulous",
) -> frozenset[str]: ...
```

Required behavior:

- Dung:
  - `grounded`
  - `complete`
  - `preferred`
  - `stable`
- Bipolar:
  - `d-preferred`
  - `s-preferred`
  - `c-preferred`
  - `bipolar-stable`
- Partial AF:
  - completion-based grounded/preferred/stable
  - `mode="skeptical"` and `mode="credulous"`

This module is allowed to dispatch over argumentation-owned dataclasses only.
It must not know about propstore backends, claims, analyzers, `AnalyzerResult`,
worldline state, or CLI semantics validation.

Update `argumentation.partial_af` internals to reuse the dispatch where it
reduces duplication. Update propstore only where generic set-returning
semantics are currently open-coded and the replacement does not pull propstore
policy into `argumentation`.

Acceptance in `argumentation`:

```powershell
rg -n -F "propstore" src tests
uv run pyright src
uv run pytest -vv tests/test_semantics.py tests/test_partial_af_queries.py tests/test_dung.py tests/test_bipolar_semantics.py
```

Acceptance in propstore:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-semantics-polish `
  tests/test_core_analyzers.py `
  tests/test_argumentation_integration.py `
  tests/test_structured_projection.py `
  tests/test_paf_queries.py
```

## Phase 5 - Documentation And Dependency Pin

Status: pending

Update external package documentation:

- `argumentation/README.md`
- `argumentation/docs/architecture.md`
- `argumentation/CONTRIBUTING.md`

Documentation must cover:

- partial AFs and completions
- AF revision
- probabilistic AFs
- DF-QuAD / QBAF gradual semantics
- generic semantics dispatch
- explicit non-goals:
  - no propstore provenance
  - no source calibration
  - no subjective-logic opinion calculus
  - no storage or CLI ownership

Update propstore documentation:

- `README.md`
- `docs/argumentation.md`
- `docs/probabilistic-argumentation.md`
- `docs/af-revision.md`
- `docs/semantic-merge.md`
- `docs/argumentation-package-boundary.md`

Update propstore dependency pin:

```toml
"argumentation @ git+https://github.com/ctoth/argumentation@<new-commit>"
```

Acceptance:

```powershell
rg -n -F "propstore/storage/merge_framework.py" README.md docs plans
rg -n -F "propstore/praf/dfquad.py" README.md docs
rg -n -F "propstore/belief_set/af_revision.py" README.md docs
rg -n -F "argumentation.partial_af" README.md docs
rg -n -F "argumentation.af_revision" README.md docs
rg -n -F "argumentation.probabilistic" README.md docs
rg -n -F "argumentation.semantics" README.md docs
```

Old path mentions are allowed only in historical plans, not current
architecture docs.

## Phase 6 - Final Boundary Verification

Status: pending

External package verification:

```powershell
cd ..\argumentation
rg -n -F "propstore" src tests README.md docs
uv run pyright src
uv run pytest -vv
```

Propstore boundary verification:

```powershell
cd ..\propstore
Test-Path propstore\storage\merge_framework.py
Test-Path propstore\storage\paf_queries.py
Test-Path propstore\storage\paf_merge.py
Test-Path propstore\belief_set\af_revision.py
Test-Path propstore\praf\components.py
Test-Path propstore\praf\treedecomp.py
Test-Path propstore\praf\dfquad.py
rg -n -F "propstore.storage.merge_framework" propstore tests docs
rg -n -F "propstore.storage.paf_queries" propstore tests docs
rg -n -F "propstore.storage.paf_merge" propstore tests docs
rg -n -F "propstore.belief_set.af_revision" propstore tests docs
rg -n -F "from propstore.praf.dfquad" propstore tests docs
rg -n -F "from propstore.praf.treedecomp" propstore tests docs
rg -n -F "from propstore.praf.components" propstore tests docs
rg -n -F "compute_praf_acceptance" propstore tests docs
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-second-pass-final `
  tests/test_core_analyzers.py `
  tests/test_argumentation_integration.py `
  tests/test_structured_projection.py `
  tests/test_structured_merge_projection.py `
  tests/test_praf.py `
  tests/test_praf_integration.py `
  tests/test_worldline_praf.py `
  tests/test_worldline.py `
  tests/test_revision_af_adapter.py `
  tests/test_worldline_revision.py
```

The `Test-Path` checks for deleted files must print `False`.

`uv run pyright propstore` must pass or have only unrelated failures that are
documented with a pre-cutover baseline. Do not mark this workstream complete
based only on targeted pytest passes while old production paths still exist.

## Completion Criteria

This workstream is complete only when:

1. `argumentation.partial_af` owns partial-AF completions, queries, and merge
   operators.
2. `argumentation.af_revision` owns AF-level revision.
3. `argumentation.probabilistic` owns pure probabilistic and quantitative AF
   algorithms.
4. `argumentation.semantics` provides the generic dispatch polish.
5. `argumentation` imports no propstore modules.
6. Propstore imports all moved formal kernels from `argumentation.*`.
7. Old propstore production paths for moved kernels do not exist.
8. Tests are split by ownership: formal tests in `argumentation`, adapter and
   projection tests in propstore.
9. Documentation describes the new boundary accurately.
10. The final verification commands have been run and recorded.

## Known Risks

- The PrAF slice is the largest risk because the current model mixes pure
  probability algorithms with `Opinion`, provenance, claim rows, and omission
  metadata.
- `tests/test_praf.py` and `tests/test_dfquad.py` likely need splitting rather
  than wholesale movement.
- `propstore/core/analyzers.py` should stay propstore-owned even if it calls
  `argumentation.semantics`; it owns `AnalyzerResult`, claim projections,
  backend names, and propstore policy validation.
- AF revision has a small formula dependency. Moving the whole belief-set
  package to solve that dependency would be the wrong cut.
- Historical plan files will continue to mention old propstore paths. Completion
  searches must distinguish historical notes from current production/docs.
