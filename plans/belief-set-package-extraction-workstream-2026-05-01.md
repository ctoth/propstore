# Belief-Set Package Extraction Workstream - 2026-05-01

## Objective

Extract the reusable finite belief-set and belief-revision kernel from
propstore into a standalone Python dependency, following the direct extraction
style used for the external argumentation package.

The target architecture is:

```text
belief_set
  finite propositional language, extensional belief sets, AGM revision,
  iterated revision, epistemic entrenchment, and IC merge

propstore
  claim/source/context/storage/world projection, provenance, sidecar,
  worldline, CLI, and adapters that may consume belief_set
```

This is a test-first extraction. Existing tests move before production code.
Moved tests are the work queue.

This workstream is based on direct inspection of the current repo on
2026-05-01. Tests were not run while drafting this workstream.

## Package Name And Layout

Use:

- repository name: `belief-set`
- distribution name: `formal-belief-set`
- import package name: `belief_set`

Do not use a `src/` layout. The external repository should use the flat package
layout:

```text
belief-set/
  README.md
  CONTRIBUTING.md
  pyproject.toml
  belief_set/
    __init__.py
    agm.py
    anytime.py
    core.py
    entrenchment.py
    ic_merge.py
    iterated.py
    language.py
  tests/
```

Propstore should eventually depend on the package through a pushed immutable
remote reference:

```toml
"formal-belief-set @ git+https://github.com/ctoth/belief-set@<commit>"
```

Do not pin propstore to a local filesystem path, editable local path, local git
path, or unpublished local commit.

## Boundary

`belief_set` owns finite formal belief-set objects and algorithms:

- formula protocol and concrete finite propositional formulas
- finite worlds
- extensional `BeliefSet`
- closure/equivalence/subset helpers over finite model sets
- Spohn ordinal conditional states
- AGM-style revision and contraction over finite theories
- Darwiche-Pearl / Nayak-Spohn / Booth-Meyer iterated revision operators
- Gärdenfors-Makinson entrenchment induced by a Spohn state
- Konieczny-Pino Pérez IC merge over finite belief profiles
- bounded enumeration failure types needed by those algorithms

Propstore keeps:

- provenance graph and witness types
- source, context, claim, stance, repository, sidecar, world, worldline, and CLI
  behavior
- support-incision operational revision in `propstore.support_revision`
- adapters from propstore domain objects into formal belief-set objects, if such
  adapters are needed later
- documentation explaining how propstore uses the external package

`belief_set` must import no `propstore` modules.

## Current Source Inventory

Current package files:

```text
propstore/belief_set/__init__.py
propstore/belief_set/af_revision_adapter.py
propstore/belief_set/agm.py
propstore/belief_set/core.py
propstore/belief_set/entrenchment.py
propstore/belief_set/ic_merge.py
propstore/belief_set/iterated.py
propstore/belief_set/language.py
propstore/belief_set/README.md
```

Move to `belief_set`:

- `__init__.py`
- `agm.py`, after removing propstore provenance coupling
- `core.py`
- `entrenchment.py`
- `ic_merge.py`, after replacing `propstore.core.anytime.EnumerationExceeded`
- `iterated.py`
- `language.py`

Do not move to `belief_set`:

- `af_revision_adapter.py`

`af_revision_adapter.py` wraps `argumentation.af_revision` and
`argumentation.dung`. It is not belief-set kernel code. Either upstream that
behavior to `argumentation.af_revision` or keep a propstore adapter outside the
deleted `propstore.belief_set` path if propstore still needs it.

## Current Test Inventory

Move first, before production code:

```text
tests/test_belief_set_postulates.py
tests/test_belief_set_iterated_postulates.py
tests/test_agm_K_star_2_inconsistent_input.py
tests/test_agm_contraction_preserves_spohn_state.py
tests/test_belief_set_alphabet_growth_budget.py
tests/test_ic_merge_IC4_fairness.py
tests/test_ic_merge_Maj_Arb.py
tests/test_ic_merge_distance_cache_stale_read.py
tests/test_ic_merge_infinite_distance_handling.py
tests/remediation/phase_1_crits/test_T1_3_restrained_revise.py
tests/remediation/phase_3_ignorance/test_T3_6_ic_merge_unsat_distance.py
tests/remediation/phase_8_dos_anytime/test_T8_1_ic_merge_distance_ceiling.py
tests/remediation/phase_8_dos_anytime/test_T8_2_ic_merge_distance_memo.py
```

Split before moving:

- `tests/test_agm_postulate_audit.py`
  - move AGM, contraction, iterated, IC, and entrenchment audit cases
  - do not move AF-revision adapter cases
- `tests/remediation/phase_1_crits/test_T1_4_revision_provenance.py`
  - move only the package-owned trace/timestamp contract
  - keep propstore `Provenance` expectations in propstore only if a propstore
    adapter remains

Keep in propstore:

- `tests/test_belief_set_docs.py`
- `tests/test_af_revision_postulates.py`
- `tests/test_af_revision_no_stable_distinct_from_empty_stable.py`
- `tests/test_revision_af_adapter.py`
- `tests/test_workstream_g_done.py`
- propstore world, support-revision, CLI, app, source, repository, and
  documentation tests

## Paper Inventory

The package should carry the formal papers that specify the standalone
belief-set algorithms. Move paper directories only after the package boundary is
clear enough to decide ownership.

Primary move candidates from `./papers`:

```text
papers/Alchourron_1985_TheoryChange/
papers/Booth_2006_AdmissibleRestrainedRevision/
papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/
papers/Konieczny_2002_MergingInformationUnderConstraints/
papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/
```

Secondary move candidates, only if the package grows the corresponding formal
surface:

```text
papers/Bonanno_2007_AGMBeliefRevisionTemporalLogic/
papers/Bonanno_2010_BeliefChangeBranchingTime/
papers/Chan_2005_DistanceMeasureBoundingProbabilistic/
papers/Martins_1988_BeliefRevision/
papers/Shapiro_1998_BeliefRevisionTMS/
```

Keep in propstore unless a separate workstream moves the owning surface:

```text
papers/Baumann_2019_AGMContractionDung/
papers/Dixon_1993_ATMSandAGM/
papers/Martins_1983_MultipleBeliefSpaces/
papers/Rotstein_2008_ArgumentTheoryChangeRevision/
```

Rationale:

- Baumann and Rotstein are argumentation-revision material.
- Dixon, Martins belief spaces, and Shapiro connect belief revision to ATMS,
  contexts, or truth-maintenance architecture that propstore still owns.
- Bonanno branching-time work is not implemented by the current package
  surface.
- Chan distance bounds are relevant only if the package adds probabilistic or
  bounded-distance revision beyond current finite IC distance behavior.

## Non-Negotiable Rules

- Move tests before production code.
- Do not add compatibility modules at old `propstore.belief_set` paths.
- Do not keep old and new production paths in parallel.
- Delete the old propstore production surface during propstore cutover.
- Do not move any code that still imports propstore.
- Do not move propstore provenance into the standalone package.
- Do not move AF-revision adapter code into the standalone belief-set package.
- Do not use local dependency pins.
- Do not use a `src/` package layout.
- Use package tests and import searches as the work queue.
- Use logged pytest wrappers for propstore test runs.
- Treat paper-directory movement as an ownership decision. Do not move papers
  merely because they mention belief revision.

## Phase 0 - Baseline And Cut List

Status: pending

Record the current propstore import and documentation surface before creating
the external package.

Required searches:

```powershell
rg -n -F "propstore.belief_set" propstore tests docs README.md
rg -n -F "from propstore.belief_set" propstore tests
rg -n -F "import propstore.belief_set" propstore tests
rg -n -F "BeliefSet" propstore tests
rg -n -F "merge_belief_profile" propstore tests docs README.md
rg -n -F "SpohnEpistemicState" propstore tests docs README.md
```

Required baseline tests in propstore:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label belief-set-extraction-baseline `
  tests/test_belief_set_postulates.py `
  tests/test_belief_set_iterated_postulates.py `
  tests/test_agm_K_star_2_inconsistent_input.py `
  tests/test_agm_contraction_preserves_spohn_state.py `
  tests/test_belief_set_alphabet_growth_budget.py `
  tests/test_ic_merge_IC4_fairness.py `
  tests/test_ic_merge_Maj_Arb.py `
  tests/test_ic_merge_distance_cache_stale_read.py `
  tests/test_ic_merge_infinite_distance_handling.py `
  tests/remediation/phase_1_crits/test_T1_3_restrained_revise.py `
  tests/remediation/phase_3_ignorance/test_T3_6_ic_merge_unsat_distance.py `
  tests/remediation/phase_8_dos_anytime/test_T8_1_ic_merge_distance_ceiling.py `
  tests/remediation/phase_8_dos_anytime/test_T8_2_ic_merge_distance_memo.py
```

If baseline failures are unrelated, document them in this workstream before
cutting code. Do not treat unrelated baseline failures as extraction progress.

## Phase 1 - Create External Package Shell

Status: pending

Create the sibling repository/package using the flat layout:

```text
belief-set/
  README.md
  CONTRIBUTING.md
  pyproject.toml
  belief_set/
    __init__.py
  tests/
```

Package requirements:

- Python `>=3.11`
- runtime dependency set initially empty
- development dependencies include pytest, hypothesis, and pyright
- no dependency on propstore
- no dependency on click, linkml, dulwich, quire, gunray, bridgman, SQLite, or
  propstore sidecar modules

Acceptance in `belief-set`:

```powershell
rg -n -F "propstore" belief_set tests README.md CONTRIBUTING.md pyproject.toml
uv run pyright belief_set
uv run pytest -vv
```

The pytest run may collect zero tests at this phase. The `rg` command must
return no package dependency on propstore.

## Phase 2 - Move Existing Tests First

Status: pending

Move the formal belief-set tests into the external package before moving
production code.

Rewrite imports:

```python
from propstore.belief_set import ...
from propstore.belief_set.core import ...
from propstore.belief_set.ic_merge import ...
```

to:

```python
from belief_set import ...
from belief_set.core import ...
from belief_set.ic_merge import ...
```

Move these whole files first:

```text
tests/test_belief_set_postulates.py
tests/test_belief_set_iterated_postulates.py
tests/test_agm_K_star_2_inconsistent_input.py
tests/test_agm_contraction_preserves_spohn_state.py
tests/test_belief_set_alphabet_growth_budget.py
tests/test_ic_merge_IC4_fairness.py
tests/test_ic_merge_Maj_Arb.py
tests/test_ic_merge_distance_cache_stale_read.py
tests/test_ic_merge_infinite_distance_handling.py
tests/remediation/phase_1_crits/test_T1_3_restrained_revise.py
tests/remediation/phase_3_ignorance/test_T3_6_ic_merge_unsat_distance.py
tests/remediation/phase_8_dos_anytime/test_T8_1_ic_merge_distance_ceiling.py
tests/remediation/phase_8_dos_anytime/test_T8_2_ic_merge_distance_memo.py
```

Create split package tests from:

- `tests/test_agm_postulate_audit.py`
  - `tests/test_agm_postulate_audit.py` in `belief-set` should contain only
    belief-set, AGM, contraction, iterated, IC, and entrenchment cases
  - AF-revision cases remain outside this package
- `tests/remediation/phase_1_crits/test_T1_4_revision_provenance.py`
  - rename to `tests/test_revision_trace.py` in `belief-set`
  - assert operator, pre-image fingerprint, and real UTC timestamp behavior
  - do not assert propstore `Provenance` objects

Expected result:

- tests fail because production modules are missing
- tests do not import propstore

Acceptance in `belief-set`:

```powershell
rg -n -F "propstore" tests
uv run pytest -vv
```

The search must return no propstore imports. Pytest should fail only because
the package implementation is not moved yet or because the package trace
contract has intentionally replaced propstore provenance.

## Phase 3 - Move Language And Core

Status: pending

Move:

- `propstore/belief_set/language.py` -> `belief_set/language.py`
- `propstore/belief_set/core.py` -> `belief_set/core.py`
- the public exports needed by the already-moved tests into
  `belief_set/__init__.py`

Required edits:

- rewrite internal imports to `belief_set.*`
- keep `Formula` as the package protocol
- keep `World = frozenset[str]`
- keep extensional finite model semantics
- keep `equivalent()` but change its lazy import to `belief_set.core`

Acceptance in `belief-set`:

```powershell
rg -n -F "propstore" belief_set tests
uv run pyright belief_set
uv run pytest -vv tests/test_belief_set_postulates.py
```

Some tests may still fail because AGM, iterated revision, entrenchment, and IC
merge are not moved yet. No failure should require propstore.

## Phase 4 - Move AGM And Package-Owned Trace

Status: pending

Move:

- `propstore/belief_set/agm.py` -> `belief_set/agm.py`

Replace propstore-owned dependencies:

- remove `propstore.provenance.Provenance`
- remove `ProvenanceStatus`
- remove `ProvenanceWitness`
- replace `propstore.core.anytime.EnumerationExceeded` with
  `belief_set.anytime.EnumerationExceeded`

Add:

```text
belief_set/anytime.py
```

Target bounded-enumeration type:

```python
@dataclass(frozen=True, slots=True)
class EnumerationExceeded(Exception):
    partial_count: int
    max_candidates: int
```

Target trace:

```python
@dataclass(frozen=True, slots=True)
class RevisionTrace:
    operator: str
    pre_image_fingerprint: str
    timestamp: datetime
```

`RevisionOutcome` remains:

```python
@dataclass(frozen=True, slots=True)
class RevisionOutcome:
    belief_set: BeliefSet
    state: SpohnEpistemicState
    trace: RevisionTrace
```

Acceptance in `belief-set`:

```powershell
rg -n -F "propstore" belief_set tests
uv run pyright belief_set
uv run pytest -vv `
  tests/test_agm_K_star_2_inconsistent_input.py `
  tests/test_agm_contraction_preserves_spohn_state.py `
  tests/test_belief_set_alphabet_growth_budget.py `
  tests/test_revision_trace.py
```

## Phase 5 - Move Iterated Revision And Entrenchment

Status: pending

Move:

- `propstore/belief_set/iterated.py` -> `belief_set/iterated.py`
- `propstore/belief_set/entrenchment.py` -> `belief_set/entrenchment.py`

Required edits:

- rewrite imports to `belief_set.*`
- keep lexicographic and restrained revision returning `RevisionOutcome`
- keep Booth-Meyer restrained revision behavior pinned by the existing
  remediation test
- keep entrenchment induced by Spohn negation ranks

Acceptance in `belief-set`:

```powershell
rg -n -F "propstore" belief_set tests
uv run pyright belief_set
uv run pytest -vv `
  tests/test_belief_set_iterated_postulates.py `
  tests/test_T1_3_restrained_revise.py `
  tests/test_agm_postulate_audit.py
```

## Phase 6 - Move IC Merge

Status: pending

Move:

- `propstore/belief_set/ic_merge.py` -> `belief_set/ic_merge.py`

Required edits:

- rewrite imports to `belief_set.*`
- use `belief_set.anytime.EnumerationExceeded`
- keep `_distance_to_formula` cache behavior because existing tests pin stale
  read and memoization behavior
- keep `ICMergeProfileMemberInconsistent`
- keep `ICMergeOperator`
- keep exact model-theoretic finite IC merge behavior

Acceptance in `belief-set`:

```powershell
rg -n -F "propstore" belief_set tests
uv run pyright belief_set
uv run pytest -vv `
  tests/test_ic_merge_IC4_fairness.py `
  tests/test_ic_merge_Maj_Arb.py `
  tests/test_ic_merge_distance_cache_stale_read.py `
  tests/test_ic_merge_infinite_distance_handling.py `
  tests/test_T3_6_ic_merge_unsat_distance.py `
  tests/test_T8_1_ic_merge_distance_ceiling.py `
  tests/test_T8_2_ic_merge_distance_memo.py
```

## Phase 7 - Move Package-Owned Paper Directories

Status: pending

Move the primary formal paper directories into the external package after the
formal code and tests have converged, but before package documentation is
finalized:

```text
belief-set/papers/Alchourron_1985_TheoryChange/
belief-set/papers/Booth_2006_AdmissibleRestrainedRevision/
belief-set/papers/Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/
belief-set/papers/Konieczny_2002_MergingInformationUnderConstraints/
belief-set/papers/Spohn_1988_OrdinalConditionalFunctionsDynamic/
```

Remove the moved directories from propstore and update `papers/index.md` or any
other current propstore paper index so it no longer claims ownership of moved
paper directories.

External package documentation should cite the moved papers from package-local
paths. Propstore documentation should cite the external package or package
paper directory where the formal kernel is now owned.

Acceptance in `belief-set`:

```powershell
Get-ChildItem papers\Alchourron_1985_TheoryChange,papers\Booth_2006_AdmissibleRestrainedRevision,papers\Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic,papers\Konieczny_2002_MergingInformationUnderConstraints,papers\Spohn_1988_OrdinalConditionalFunctionsDynamic
rg -n -F "propstore" papers README.md CONTRIBUTING.md docs
```

Propstore acceptance:

```powershell
Test-Path papers\Alchourron_1985_TheoryChange
Test-Path papers\Booth_2006_AdmissibleRestrainedRevision
Test-Path papers\Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic
Test-Path papers\Konieczny_2002_MergingInformationUnderConstraints
Test-Path papers\Spohn_1988_OrdinalConditionalFunctionsDynamic
rg -n -F "Alchourron_1985_TheoryChange" papers\index.md README.md docs
rg -n -F "Booth_2006_AdmissibleRestrainedRevision" papers\index.md README.md docs
rg -n -F "Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic" papers\index.md README.md docs
rg -n -F "Konieczny_2002_MergingInformationUnderConstraints" papers\index.md README.md docs
rg -n -F "Spohn_1988_OrdinalConditionalFunctionsDynamic" papers\index.md README.md docs
```

The `Test-Path` commands for moved propstore paper directories must print
`False`. Remaining references in current propstore docs must point to the
external package or be removed; historical plans are not part of this gate.

Do not move secondary candidates in this phase. Create a later workstream if
the package grows the formal surface that owns them.

## Phase 8 - External Package Documentation And Full Gate

Status: pending

Add or complete external package documentation:

- `README.md`
- `CONTRIBUTING.md`
- optional `docs/architecture.md` if the README would become too dense

Documentation must cover:

- package purpose
- install from Git
- flat package layout
- public imports
- formula and belief-set examples
- AGM revision and contraction examples
- iterated revision examples
- IC merge example
- explicit non-goals:
  - no propstore provenance
  - no source, context, claim, stance, sidecar, storage, worldline, or CLI
  - no AF-level revision adapter
  - no compatibility imports for `propstore.belief_set`

Required full package gate:

```powershell
rg -n -F "propstore" belief_set tests README.md CONTRIBUTING.md docs
uv run pyright belief_set
uv run pytest -vv
```

Push the package to the shared remote after the full package gate passes.

## Phase 9 - Pin Propstore To The Pushed Package

Status: pending

Only after the external package is pushed, add the remote immutable dependency
to propstore:

```toml
"formal-belief-set @ git+https://github.com/ctoth/belief-set@<commit>"
```

Update the lockfile with `uv`.

Do not use:

- local filesystem paths
- editable local paths
- `file://` URLs
- local git paths
- relative paths
- Windows drive paths
- WSL paths

Acceptance in propstore:

```powershell
rg -n -F "formal-belief-set" pyproject.toml uv.lock
rg -n "formal-belief-set.*(file:|C:|\\.\\.|/Users/|/home/|wsl|editable)" pyproject.toml uv.lock
```

The second search must return no results.

## Phase 10 - Delete Old Propstore Production Surface

Status: pending

Delete:

```text
propstore/belief_set/__init__.py
propstore/belief_set/agm.py
propstore/belief_set/core.py
propstore/belief_set/entrenchment.py
propstore/belief_set/ic_merge.py
propstore/belief_set/iterated.py
propstore/belief_set/language.py
propstore/belief_set/README.md
```

Do not create compatibility modules under `propstore/belief_set`.

Handle `propstore/belief_set/af_revision_adapter.py` explicitly:

- preferred: move its behavior into `argumentation.af_revision` and delete the
  propstore file
- acceptable only if propstore still needs adapter policy: move it to a
  propstore-owned adapter path outside `propstore.belief_set`, update every
  caller, then delete `propstore/belief_set`

Update propstore tests that remain:

- tests that still exercise formal belief-set behavior should import
  `belief_set.*`, not `propstore.belief_set.*`
- tests that exercise propstore docs or adapters should stay propstore-owned
- remove moved package tests from propstore unless they are intentionally
  duplicated as dependency pin smoke tests

Acceptance in propstore:

```powershell
Test-Path propstore\belief_set
rg -n -F "from propstore.belief_set" propstore tests docs README.md
rg -n -F "import propstore.belief_set" propstore tests docs README.md
rg -n -F "propstore.belief_set" propstore tests docs README.md
```

`Test-Path` must print `False`. Searches must return no live production, test,
or current-doc imports. Historical plan mentions are allowed only outside the
listed current scopes.

## Phase 11 - Update Propstore Type And Documentation Surfaces

Status: pending

Update `pyproject.toml`:

- remove strict pyright paths under `propstore/belief_set/*`
- do not add strict paths for the external package in propstore

Update current propstore docs:

- `README.md`
- `docs/belief-set-revision.md`
- `docs/ic-merge.md`
- `docs/argumentation.md`
- `docs/atms.md`
- `docs/af-revision.md`
- `propstore/support_revision/__init__.py`

Documentation target:

- formal belief-set operations live in external `belief_set`
- propstore consumes that package only at adapter/projection boundaries, if
  needed
- support-incision remains propstore-owned and is not AGM revision
- AF revision remains argumentation-owned
- no current doc should describe `propstore.belief_set` as the live owner

Acceptance:

```powershell
rg -n -F "propstore.belief_set" README.md docs propstore
rg -n -F "belief_set.ic_merge" README.md docs propstore
rg -n -F "belief_set.agm" README.md docs propstore
rg -n -F "argumentation.af_revision" README.md docs propstore
```

The first search must return no current ownership claims. Historical plans are
not part of this current-doc gate.

## Phase 12 - Propstore Adapter And Pin Tests

Status: pending

Add only narrow propstore tests that prove propstore uses the dependency
directly and does not own the formal package.

Recommended tests:

- dependency import smoke test:
  - `from belief_set import Atom, BeliefSet, SpohnEpistemicState, revise`
- doc boundary test:
  - current docs say external `belief_set`, not `propstore.belief_set`
- no old production path test:
  - `Path("propstore/belief_set").exists()` is false

Do not reintroduce the full moved formal test suite into propstore.

Acceptance:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label belief-set-pin `
  tests/test_belief_set_docs.py
```

If new pin tests are added, include them in this logged run.

## Phase 13 - Final Verification

Status: pending

External package final verification:

```powershell
cd ..\belief-set
rg -n -F "propstore" belief_set tests README.md CONTRIBUTING.md docs
uv run pyright belief_set
uv run pytest -vv
```

Propstore final verification:

```powershell
cd ..\propstore
Test-Path propstore\belief_set
rg -n -F "from propstore.belief_set" propstore tests docs README.md
rg -n -F "import propstore.belief_set" propstore tests docs README.md
rg -n -F "propstore.belief_set" propstore tests docs README.md
rg -n -F "formal-belief-set" pyproject.toml uv.lock
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label belief-set-external-final `
  tests/test_belief_set_docs.py `
  tests/test_revision_properties.py `
  tests/test_revision_cli.py `
  tests/test_revision_operators.py `
  tests/test_revision_iterated.py `
  tests/test_revision_af_adapter.py `
  tests/test_af_revision_postulates.py `
  tests/test_af_revision_no_stable_distinct_from_empty_stable.py
```

The `Test-Path` command must print `False`.

`uv run pyright propstore` must pass or have only pre-existing unrelated
failures documented before the cutover. Do not mark the workstream complete
based only on targeted pytest passes while old production paths still exist.

## Completion Criteria

This workstream is complete only when:

1. `belief-set` exists as its own flat-layout package.
2. Existing formal belief-set tests have moved to the package.
3. The package imports no propstore modules.
4. `belief_set` owns language, core belief sets, AGM revision, iterated
   revision, entrenchment, IC merge, and bounded enumeration failures.
5. Propstore provenance is not part of the external package.
6. AF-revision adapter behavior is not part of the external package.
7. Propstore depends on a pushed immutable remote commit of
   `formal-belief-set`.
8. `propstore/belief_set` no longer exists.
9. Primary package-owned paper directories have moved to `belief-set/papers`.
10. Propstore has no live production, test, or current-doc imports from
   `propstore.belief_set`.
11. Documentation describes the new boundary accurately.
12. External package full tests pass.
13. Propstore pyright and logged targeted tests pass, or unrelated pre-existing
    failures are documented with a pre-cutover baseline.

## Known Risks

- `agm.py` currently imports propstore provenance. That must become a
  propstore-owned adapter concern or be removed from the formal trace contract.
- `agm.py` and `ic_merge.py` currently import
  `propstore.core.anytime.EnumerationExceeded`. The package needs its own
  bounded-enumeration error type.
- `test_agm_postulate_audit.py` mixes belief-set and AF-revision concerns and
  must be split.
- `af_revision_adapter.py` lives under `propstore.belief_set` today but is not
  a belief-set package surface.
- There may be no substantial propstore production callers outside the current
  `propstore.belief_set` package. If so, the propstore cutover is mainly a
  dependency, docs, and tests cutover, not an adapter migration.
- Historical plans and reviews will continue to mention `propstore.belief_set`.
  Completion searches must distinguish historical records from current
  production, tests, and docs.
