# Argumentation Package Extraction Workstream - 2026-04-18

## Objective

Extract the reusable finite argumentation kernel from propstore into a Python
package named `argumentation`, while keeping propstore's claim, stance, source,
context, sidecar, worldline, and CLI adapters in propstore.

The target is not a transition layer. The target is one ownership boundary:

```text
argumentation
  finite formal argumentation objects and algorithms

propstore
  scientific-claim storage, compilation, projection, policy, and CLI
```

The extraction starts with the surfaces that are already clean:

- `propstore.aspic`
- `propstore.dung`
- `propstore.bipolar`

Everything else moves only after its propstore-specific dependencies are
removed.

This workstream is based on direct inspection of the current repo and a Claude
design-review/adversarial-review pass on 2026-04-18. Tests were not run while
drafting this workstream.

## Decision

Use:

- GitHub repo / distribution name: `argumentation`
- import package name: `argumentation`

Do not use a branded/metaphorical package name. The package should stay
citation-anchored and literal.

Initial public imports should look like:

```python
from argumentation.dung import ArgumentationFramework, grounded_extension
from argumentation.aspic import Literal, Rule, build_arguments, compute_attacks
from argumentation.bipolar import BipolarArgumentationFramework
```

Propstore adapters should import the formal kernel:

```python
from argumentation.aspic import ArgumentationSystem, KnowledgeBase
from argumentation.dung import ArgumentationFramework
```

## Non-Negotiable Rules

- `argumentation` must import no `propstore` modules.
- Propstore must not keep compatibility import shims or old-path modules that
  forward to the new package.
- Move one formal surface at a time.
- Delete the old production import surface first in each slice, then use search,
  type-check, and tests as the work queue.
- Do not extract a module that still imports propstore.
- Do not carry old and new paths in parallel.
- Do not move store-facing adapters into `argumentation`.
- Do not move provenance, CEL, sidecar, world, worldline, CLI, or source
  workflows into `argumentation`.
- If a slice cannot converge without a compatibility bridge, revert that slice
  and record the blocker.

## Current Boundary

Clean formal kernel candidates:

- `propstore/aspic.py`
  - ASPIC+ literals, rules, arguments, attacks, defeats, CSAF construction.
  - Runtime code is intended to be leaf formal logic.
- `propstore/dung.py`
  - Dung AF dataclass and grounded, complete, preferred, stable semantics.
  - No propstore domain concepts.
- `propstore/bipolar.py`
  - Cayrol-style bipolar argumentation framework and semantics.
  - No propstore domain concepts.

Near-kernel but blocked:

- `propstore/dung_z3.py`
  - Blocked by `propstore.z3_conditions`.
  - Move only after solver-result/timeout plumbing is local to
    `argumentation` or generic enough to extract without CEL.
- `propstore/preference.py`
  - Split-brained by design.
  - Generic strict-order and set-comparison helpers can move.
  - `metadata_strength_vector(ActiveClaim)` must stay in propstore.
- `propstore/praf/*`
  - The store-facing engine imports propstore row, provenance, opinion, stance,
    and analyzer surfaces.
  - Do not move as part of the initial package.
- `propstore/belief_set/*`
  - Formal-adjacent, but coupled to propstore provenance and current revision
    surfaces.
  - Do not move until the argumentation kernel extraction is complete.

Propstore-owned adapters:

- `propstore/aspic_bridge/`
- `propstore/claim_graph.py`
- `propstore/structured_projection.py`
- `propstore/defeasibility.py`
- `propstore/core/analyzers.py`
- `propstore/praf/projection.py`
- `propstore/worldline/`
- `propstore/storage/`
- `propstore/cli/`

## Target Package Scope

Extracted `argumentation` package:

```text
argumentation/
  README.md
  pyproject.toml
  src/
    argumentation/
      __init__.py
      dung.py
      dung_z3.py
      aspic.py
      bipolar.py
      preference.py
      solver.py
  tests/
    test_dung.py
    test_aspic.py
    test_bipolar_argumentation.py
    test_bipolar_semantics.py
    test_dung_z3.py
    test_dung_backend_differential.py
    test_backward_chaining.py
    test_preference.py
```

Potential future packages or later workstreams:

- subjective logic / calibration
- probabilistic argumentation
- belief revision and IC merge

Those are not part of the initial `argumentation` extraction unless their
propstore dependencies have first been removed.

## Documentation Artifacts

The extraction is not complete until these documents exist and are accurate:

1. `argumentation/README.md`
   - package purpose
   - install instructions
   - supported formal systems
   - examples for Dung, ASPIC+, and bipolar AFs
   - explicit non-goals
   - citation list
2. `argumentation/CONTRIBUTING.md`
   - tests, formatting, type checks, citation discipline
   - rule that the package cannot import propstore
3. `argumentation/docs/architecture.md`
   - formal kernel boundary
   - backend policy
   - optional Z3 backend design, once added
4. `propstore/aspic_bridge/README.md`
   - explains that this package is the propstore adapter from claims,
     justifications, stances, and grounded bundles into `argumentation.aspic`.
5. `docs/argumentation-package-boundary.md`
   - propstore-side architectural boundary and execution checklist.
6. Update `README.md`, `docs/argumentation.md`,
   `docs/structured-argumentation.md`, and `docs/bipolar-argumentation.md`
   after imports move.

## Phase 0 - Boundary Documentation

Status: completed

Add the propstore-side planning and documentation artifacts before changing code.

Required files:

- `plans/argumentation-package-extraction-workstream-2026-04-18.md`
- `docs/argumentation-package-boundary.md`
- `docs/argumentation-package-readme.md`

Acceptance:

```powershell
rg -n -F "argumentation-package-boundary" README.md docs plans
rg -n -F "from argumentation.dung import *" propstore
```

The second search must return no compatibility shim in production code.

## Phase 1 - Create The External Package

Status: completed

Create a sibling GitHub repo/package named `argumentation`.

Target files:

```text
argumentation/
  README.md
  CONTRIBUTING.md
  pyproject.toml
  src/argumentation/__init__.py
  src/argumentation/dung.py
  src/argumentation/aspic.py
  src/argumentation/bipolar.py
  tests/
```

Move the three clean modules and their kernel tests into the external package:

- `propstore/dung.py` -> `argumentation.dung`
- `propstore/aspic.py` -> `argumentation.aspic`
- `propstore/bipolar.py` -> `argumentation.bipolar`
- kernel tests for Dung, ASPIC+, and bipolar semantics

Package requirements:

- Python `>=3.11`
- no runtime dependency on propstore
- no dependency on Click, Quire, Gunray, Bridgman, LinkML, Dulwich, SQLite, CEL,
  or propstore sidecar modules
- `z3-solver` is not required in the initial package
- no license file or license metadata is added in this workstream

Initial package docs:

- `README.md`
- `CONTRIBUTING.md`
- `docs/architecture.md`

Acceptance in the `argumentation` repo:

```powershell
uv run pyright src
uv run pytest -vv
rg -n -F "from propstore" src tests
rg -n -F "import propstore" src tests
```

The `rg` commands must return no package-code or test dependency on propstore.

## Phase 2 - Cut Propstore Over To The External Package

Status: completed

Add the new package dependency to propstore:

```toml
"argumentation @ git+https://github.com/ctoth/argumentation@<commit>"
```

Delete the old production files:

- `propstore/dung.py`
- `propstore/aspic.py`
- `propstore/bipolar.py`
- `propstore/dung_z3.py`

Then update every caller to import directly from `argumentation.*`.

Required import target:

```python
from argumentation.dung import ArgumentationFramework
from argumentation.aspic import Literal, Rule
from argumentation.bipolar import BipolarArgumentationFramework
```

Do not create compatibility modules at the old paths.

Acceptance:

```powershell
rg -n -F "from propstore.dung" propstore tests docs
rg -n -F "from propstore.aspic" propstore tests docs
rg -n -F "from propstore.bipolar" propstore tests docs
rg -n -F "import propstore.dung" propstore tests docs
rg -n -F "import propstore.aspic" propstore tests docs
rg -n -F "import propstore.bipolar" propstore tests docs
rg -n -F "propstore/dung.py" README.md docs
rg -n -F "propstore/aspic.py" README.md docs
rg -n -F "propstore/bipolar.py" README.md docs
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-external `
  tests/test_dung.py `
  tests/test_aspic.py `
  tests/test_bipolar_argumentation.py `
  tests/test_bipolar_semantics.py `
  tests/test_aspic_bridge.py `
  tests/test_structured_projection.py `
  tests/test_core_analyzers.py
```

All old-path import searches must return no live production/test imports.
Historical mentions in plans/reviews are allowed only when the search is
broadened beyond the listed scopes.

## Phase 3 - Keep Tests Split By Ownership

Status: completed

Maintain two test groups after the cutover:

- formal kernel tests in the `argumentation` repo
- propstore adapter/projection tests in propstore

Kernel tests should import only `argumentation.*`.
Adapter tests may import propstore domain modules and `argumentation.*`.

Required classification:

- Kernel, moved to `argumentation`:
  - `test_dung.py`
  - `test_dung_backend_differential.py`, after `dung_z3` moves or after the
    differential test is narrowed to brute-force behavior
  - `test_aspic.py`
  - `test_backward_chaining.py` if it only uses formal ASPIC inputs
  - `test_bipolar_argumentation.py`
  - `test_bipolar_semantics.py`
- Adapter, kept in propstore:
  - `tests/test_aspic_bridge.py`
  - `tests/test_aspic_bridge_grounded.py`
  - `tests/test_aspic_bridge_review_v2.py`
  - `tests/test_structured_projection.py`
  - claim graph, worldline, storage, and PrAF integration tests

Acceptance in `argumentation`:

```powershell
rg -n -F "propstore.core" tests
rg -n -F "propstore." tests
uv run pytest -vv
```

Acceptance in propstore:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-adapters `
  tests/test_aspic_bridge.py `
  tests/test_aspic_bridge_grounded.py `
  tests/test_aspic_bridge_review_v2.py `
  tests/test_structured_projection.py
```

## Phase 4 - Add Propstore Adapter READMEs

Status: completed

Add or update propstore-local README files for the adapter surfaces that remain:

```text
propstore/aspic_bridge/README.md
propstore/praf/README.md
propstore/belief_set/README.md
```

Each README must state:

- what propstore-specific data it owns
- which `argumentation` modules it consumes
- why it is not part of the formal kernel package
- main entry points
- relevant docs/workstream links

The `aspic_bridge` README can be added before the code move because that
boundary is already clear.

Acceptance:

```powershell
Get-ChildItem propstore\aspic_bridge\README.md,propstore\praf\README.md,propstore\belief_set\README.md
rg -n -F "argumentation" propstore\aspic_bridge\README.md propstore\praf\README.md propstore\belief_set\README.md
```

## Phase 5 - Extract Z3 Dung Backend

Status: completed

Move `dung_z3` only after decoupling it from `propstore.z3_conditions`.

Target choices:

1. Implement a small solver-result wrapper inside `argumentation.dung_z3`.
2. Or create `argumentation.solver` with a minimal `SolverSat`,
   `SolverUnsat`, `SolverUnknown`, and `Z3UnknownError`.

Do not import `propstore.z3_conditions`.
Do not move CEL condition solving.

Acceptance in `argumentation`:

```powershell
rg -n -F "propstore" src/argumentation/dung_z3.py tests/test_dung_z3.py
uv run pytest -vv tests/test_dung_z3.py tests/test_dung_backend_differential.py
```

Acceptance in propstore:

```powershell
rg -n -F "propstore.dung_z3" propstore tests docs
powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-z3 tests/test_dung_z3.py tests/test_dung_backend_differential.py
```

## Phase 6 - Split Generic Preference Helpers

Status: completed

Split `propstore.preference`:

- move generic formal helpers into `argumentation.preference`
- keep propstore metadata heuristics in `propstore.preference`

Move:

- `strict_partial_order_closure`
- `strictly_weaker`
- `defeat_holds`, if its string attack-type surface is kept generic

Keep:

- `metadata_strength_vector`
- `claim_strength`
- anything importing `ActiveClaim`

Acceptance:

```powershell
rg -n -F "from propstore.core.active_claims" argumentation
rg -n -F "metadata_strength_vector" argumentation
powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-preference tests/test_aspic_bridge.py tests/test_core_analyzers.py
```

The first two searches must return no results.

## Phase 7 - Update Documentation And READMEs

Status: completed

Required propstore documentation updates:

- `README.md`
  - dependency table includes `argumentation`
  - reasoning backend table points to external formal kernel plus propstore
    adapters
- `docs/argumentation.md`
  - explains external kernel versus propstore projection layer
- `docs/structured-argumentation.md`
  - replaces `propstore/aspic.py` references with `argumentation.aspic`
  - keeps `propstore.aspic_bridge` as the adapter
- `docs/bipolar-argumentation.md`
  - replaces `propstore/bipolar.py` references with `argumentation.bipolar`
- `docs/probabilistic-argumentation.md`
  - explains that PrAF remains propstore-owned for now

Required external package documentation:

- `README.md`
- `CONTRIBUTING.md`
- `docs/architecture.md`
- API examples for Dung, ASPIC+, bipolar
- citation section
- explicit non-goals

Acceptance:

```powershell
rg -n -F "propstore/aspic.py" README.md docs
rg -n -F "propstore/dung.py" README.md docs
rg -n -F "propstore/bipolar.py" README.md docs
rg -n -F "argumentation.aspic" README.md docs
rg -n -F "argumentation.dung" README.md docs
rg -n -F "argumentation.bipolar" README.md docs
```

Old path searches should return only historical workstream text, not current
architecture docs.

## Phase 8 - Reconsider Adjacent Packages

Status: completed

This phase was evaluated after the initial package was external and the
focused propstore adapter tests passed against it.

Evaluate separately:

- `subjective-logic`
- `probabilistic-argumentation`
- `belief-revision`

For each candidate, require the same proof:

- no propstore imports
- no provenance coupling unless provenance is modeled as a local protocol
- clear package name
- tests move with the package
- propstore keeps only adapters

Evaluation result:

- `subjective-logic`: not extracted. `propstore/opinion.py` imports propstore
  provenance, so the package proof is not satisfied.
- `probabilistic-argumentation`: not extracted. `propstore/praf/*` imports
  propstore opinions, provenance, row types, analyzers, and world-store
  surfaces.
- `belief-revision`: not extracted. `propstore/belief_set/*` still imports
  propstore provenance and is coupled to propstore belief-set package surfaces.

## Completion Criteria

This workstream is complete only when:

1. `argumentation` exists as its own package/repo.
2. `argumentation` contains Dung, ASPIC+, and bipolar formal kernels.
3. `argumentation` imports no propstore modules.
4. propstore imports formal kernels from `argumentation`.
5. old production import paths no longer exist.
6. propstore keeps bridge/projection/policy/storage/CLI ownership.
7. package and propstore READMEs describe the boundary accurately.
8. focused kernel and adapter tests pass through logged pytest wrappers.
9. `uv run pyright propstore` passes or has only pre-existing documented
   unrelated failures.

## Known Risks

- Direct test imports from old paths are numerous and will make the first cut
  noisy.
- `aspic.py` contains a `TYPE_CHECKING` reference to Dung; update it in the same
  slice that moves Dung.
- `dung.py` currently lazy-imports `propstore.dung_z3`; leave Z3 disabled or
  temporarily remove backend routing until Phase 5. Do not route to old
  propstore code from the new package.
- Documentation currently describes `propstore/aspic.py`, `propstore/dung.py`,
  and `propstore/bipolar.py` as the implementation locations.
- PrAF, belief revision, and opinion code are tempting but not yet clean
  package contents.
