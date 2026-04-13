# Test Suite Improvement Workstream

Date: 2026-04-13
Status: proposed

## Goal

Improve the test suite on three axes at once:

- raise semantic protection where important properties are currently untested
- reduce low-signal and redundant tests that mainly pin wiring, migration, or
  implementation trivia
- make the suite measurable so we can prove improvement instead of guessing

This is not a "more tests" plan. It is a signal-density plan.

## Validated Basis

This plan is based on direct inspection of the current repo and test suite.

Verified observations:

- `tests/` contains `130` test files.
- `propstore/` contains `387` Python files.
- the repo has `2401` collected tests
- the latest complete same-day full-suite log on disk is:
  `logs/test-runs/full-suite-literal-identity-final-20260413-015249.log`
- that run finished green in `378.97s`
- `54` test files use Hypothesis/stateful/differential patterns
- there is no current `pytest-cov` usage or coverage configuration in
  `pyproject.toml`

Concrete weak-signal examples found during inspection:

- duplicated monkeypatched CLI acceptance for
  `world extensions --backend aspic` in
  `tests/test_aspic_bridge.py` and `tests/test_structured_projection.py`
- cutover-era delegation tests in `tests/test_aspic_bridge.py`
- backend-wiring tests in `tests/test_worldline.py` that assert old paths do not
  run rather than asserting enduring behavior contracts
- heavy dict/SQLite scaffolding concentrated in `tests/conftest.py`
- several very large example-heavy files without comparable property/stateful
  depth, especially:
  - `tests/test_world_model.py`
  - `tests/test_git_backend.py`
  - `tests/test_atms_engine.py`
  - `tests/test_cli.py`
  - `tests/test_source_cli.py`

Concrete strong patterns already present and worth expanding:

- `tests/test_git_properties.py`
- `tests/test_treedecomp_differential.py`
- `tests/test_worldline_properties.py`
- `tests/test_verify_cli.py`

## Principles

- Prefer durable semantic contracts over migration-era wiring assertions.
- Prefer property, differential, metamorphic, and stateful tests over long lists
  of examples when the surface admits them.
- Keep raw `dict` and raw SQLite rows at explicit IO boundaries; use typed or
  named builders for core semantic tests.
- If we control both sides of a surface, do not keep old/new test paths in
  parallel after the cutover is complete.
- Delete low-signal tests only when an equal-or-stronger contract replaces them,
  or when mutation/fault-injection shows they do not pull their weight.

## Success Criteria

This workstream is complete only when all of the following are true:

1. coverage reporting exists and is part of routine test evaluation
2. suspect low-signal surfaces have been triaged with proof, not vibes
3. duplicate migration/cutover tests have been removed or consolidated
4. major semantic engines have stronger property/differential coverage than they
   do today
5. at least one minimally mocked end-to-end path exists for each major product
   surface:
   - source flow
   - sidecar build
   - repo/git flow
   - worldline/render/verify flow
6. suite taxonomy markers exist so future tests can be added intentionally

## Non-goals

- Do not optimize for a bigger raw test count.
- Do not preserve migration/cutover tests once the migration is over.
- Do not rewrite the whole suite before getting measurement in place.
- Do not treat green test runs as evidence that a test is useful.

## Execution Discipline

For every slice in this workstream:

1. measure or prove the weakness first
2. if deleting tests, identify the replacement contract or mutation evidence
3. make the narrowest coherent change
4. run the focused suite with
   `uv run pytest -vv ... 2>&1 | Tee-Object -FilePath logs/test-runs/<name>.log`
5. after each substantial green run, reread this workstream before picking the
   next slice

Do not remove a test because it is ugly. Remove it only if it is redundant,
obsolete, or weaker than the replacement we are adding.

## Tooling Decisions

These are the pinned defaults for this workstream.

### Coverage and Runtime Measurement

Use:

- `pytest-cov`
- pytest `--durations`

Planned dependency change:

- add `pytest-cov>=6.0` to the `dev` dependency group in `pyproject.toml`

Baseline command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase0-coverage-baseline-$ts.log"
$xml = "logs/test-runs/phase0-coverage-baseline-$ts.xml"
$html = "logs/test-runs/phase0-coverage-html-$ts"
uv run pytest -vv --cov=propstore --cov-report=term-missing --cov-report=xml:$xml --cov-report=html:$html --durations=25 2>&1 | Tee-Object -FilePath $log
```

Focused command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/<slice-name>-$ts.log"
uv run pytest -vv <targeted tests...> --durations=10 2>&1 | Tee-Object -FilePath $log
```

### Low-Signal Proof Method

For the initial suspect tranche, the default proof method is targeted fault
injection/manual mutation inside the local repo, not full-suite mutation
testing.

Reason:

- it is Windows-friendly
- it is precise enough for duplicated wiring tests
- it avoids blocking the workstream on mutation-tool ergonomics

Allowed escalation:

- if a suspect surface remains ambiguous after duplicate comparison and targeted
  fault injection, use a selective mutation tool trial on that one file group
- do not broaden to repo-wide mutation until the selective path proves useful

### Phase-Close Artifacts

Every phase-close run must leave named artifacts under `logs/test-runs/`.

Required artifact families:

- `phase0-coverage-baseline-<timestamp>.log`
- `phase0-coverage-baseline-<timestamp>.xml`
- `phase0-coverage-html-<timestamp>/`
- `phase1-low-signal-ledger-<timestamp>.md`
- `phase2-cutover-consolidation-<timestamp>.log`
- `phase3-semantic-replacements-<timestamp>.log`
- `phase4a-world-model-<timestamp>.log`
- `phase4b-git-backend-<timestamp>.log`
- `phase4c-cli-source-cli-<timestamp>.log`
- `phase4d-atms-worldline-cli-<timestamp>.log`
- `phase5-builders-refactor-<timestamp>.log`
- `phase6-e2e-ratchet-<timestamp>.log`
- `phase7-guardrails-<timestamp>.log`

## Live Status Ledger

Update this ledger as execution proceeds. Every suspect tranche and every phase
must end in an explicit terminal state rather than drifting.

### Phase Ledger

| Phase | Summary | Status | Evidence | Notes |
|---|---|---|---|---|
| 0 | coverage + markers baseline | completed | `logs/test-runs/phase0-coverage-baseline-xdist-plain-20260413-134049.xml`; `logs/test-runs/phase0-inventory-report-20260413-141300.txt` | markers and `pytest-cov` landed; usable XML/HTML coverage artifacts and inventory summary now exist even though `xdist` remained noisy at the tail of one later rerun |
| 1 | low-signal triage ledger | completed | `logs/test-runs/phase2-cutover-consolidation-rerun-20260413-135057.log` | initial suspect tranche classified below |
| 2 | cutover/wiring consolidation | completed | `logs/test-runs/phase2-cutover-consolidation-rerun-20260413-135057.log` | duplicate ASPIC CLI acceptance removed; cutover-only delegation block removed |
| 3 | semantic replacement contracts | completed | `logs/test-runs/phase2-cutover-consolidation-rerun-20260413-135057.log` | obsolete projection assumption replaced; worldline tests moved from negative path assertions to kept behavior contracts |
| 4A | world_model property tranche | completed | `logs/test-runs/phase4a-world-model-20260413-141918.log` | added irrelevant-claim invariance, overlay conflict-order invariance, and stronger sidecar schema hard-failure coverage |
| 4B | git_backend/repo tranche | completed | `logs/test-runs/phase4b-git-backend-20260413-143128.log` | added CLI-vs-report differential coverage and fixed merge-commit materialization so the advertised `claims/merged.yaml` path always exists |
| 4C | cli/source_cli tranche | completed | `logs/test-runs/phase4c-cli-source-cli-20260413-143732.log` | replaced a survival-style observation proposal smoke test with a full source init/finalize/promote/build/verify flow and hardened source form fixtures for real authored-flow execution |
| 4D | atms/worldline cli tranche | completed | `logs/test-runs/phase4d-atms-worldline-cli-20260413-144222.log` | added a worldline run/show/list cross-command consistency contract on persisted materializations |
| 5 | typed builders + fixture refactor | completed | `logs/test-runs/phase5-builders-refactor-20260413-145145.log` | introduced named source semantic builders and rewrote core source relation tests to use them instead of anonymous inline payload dicts |
| 6 | minimally mocked e2e ratchet | completed | `logs/test-runs/phase6-e2e-ratchet-20260413-144336.log` | added a real authored source->build->verify->worldline flow and a real worldline create/run->log history flow, both without monkeypatching core product paths |
| 7 | structural guardrails | pending | | |

### Suspect Surface Ledger

| Surface | Reason | Proof Method | Decision | Replacement / Keep Surface | Evidence | Notes |
|---|---|---|---|---|---|---|
| `tests/test_aspic_bridge.py` backend acceptance block | duplicates neighboring CLI/backend contract | direct duplicate comparison + call-site inspection | delete as redundant | keep `tests/test_structured_projection.py::test_world_extensions_cli_accepts_aspic_backend` | `logs/test-runs/phase2-cutover-consolidation-rerun-20260413-135057.log` | CLI command imports `build_structured_projection` from the structured layer |
| `tests/test_structured_projection.py` backend acceptance block | closest test to actual CLI call site | direct duplicate comparison + call-site inspection | keep | `tests/test_structured_projection.py::test_world_extensions_cli_accepts_aspic_backend` | `logs/test-runs/phase2-cutover-consolidation-rerun-20260413-135057.log` | retained as the owning CLI/backend acceptance contract |
| `tests/test_aspic_bridge.py` Phase-5 cutover delegation block | migration-era call-routing contract | direct duplicate comparison + replacement contract proof | delete as obsolete | keep direct `BuildAspicProjection` contract tests plus structured projection behavior tests | `logs/test-runs/phase2-cutover-consolidation-rerun-20260413-135057.log` | cutover is complete; the old/new dual path is no longer a product surface |
| `tests/test_worldline.py` old-path/bridge-threading blocks | asserts implementation path more than product behavior | direct duplicate comparison + replacement contract proof | replace then delete | keep graph-backed projection contract tests and stable materialization tests | `logs/test-runs/phase2-cutover-consolidation-rerun-20260413-135057.log` | removed negative "old path must not run" assertions and duplicate ASPIC threading checks |
| `tests/test_cli.py` survival-style `CliRunner` cluster | likely weak assertions on command success only | selective duplicate review + targeted fault injection | keep for Phase 4C | phase 4C authored-flow replacements | | not yet executed |
| `tests/test_source_cli.py` survival-style `CliRunner` cluster | likely weak assertions on command success only | selective duplicate review + targeted fault injection | keep for Phase 4C | phase 4C authored-flow replacements | | not yet executed |

## Phase 0: Measurement First

Purpose:
establish objective visibility before changing the suite.

Tasks:

1. add coverage tooling and commit to the reporting surface
   - `pytest-cov` with terminal, XML, and HTML outputs
2. add suite taxonomy markers in pytest config
   - `unit`
   - `property`
   - `differential`
   - `e2e`
   - `migration`
   - `slow`
3. produce a baseline report for:
   - file coverage
   - changed-line blind spots for the largest product areas
   - runtime distribution by test file
4. add a small script or documented command that can emit:
   - top slow files
   - files with many tests but poor coverage
   - product modules with no obvious direct test file

Pinned outputs:

- full baseline coverage run using the command in `Tooling Decisions`
- marker configuration in `pyproject.toml`
- one checked-in or documented command surface for post-run summaries

Phase-close command:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase0-coverage-baseline-$ts.log"
$xml = "logs/test-runs/phase0-coverage-baseline-$ts.xml"
$html = "logs/test-runs/phase0-coverage-html-$ts"
uv run pytest -vv --cov=propstore --cov-report=term-missing --cov-report=xml:$xml --cov-report=html:$html --durations=25 2>&1 | Tee-Object -FilePath $log
```

Exit criteria:

- coverage report exists
- markers are enforced
- a baseline measurement artifact is saved under `logs/test-runs/`

## Phase 1: Low-Signal Triage Ledger

Purpose:
turn "I suspect this is useless" into an explicit ledger.

Create a tracked ledger with one row per suspect surface:

- file or test block
- reason for suspicion
- proof method
- decision
- replacement surface if removed

Initial suspect tranche:

- duplicated backend-acceptance tests in
  `tests/test_aspic_bridge.py` and `tests/test_structured_projection.py`
- Phase-5 cutover delegation tests in `tests/test_aspic_bridge.py`
- backend-wiring tests in `tests/test_worldline.py`
- large `CliRunner` surfaces in `tests/test_cli.py` and `tests/test_source_cli.py`
- simple `exit_code == 0` tests that assert little beyond command survival

Pinned proof order:

1. direct duplicate comparison against stronger neighboring tests
2. targeted fault injection/manual mutation in the touched production surface
3. proving that a migration/cutover condition is no longer part of the product
   contract
4. selective mutation-tool trial only if the first three do not settle the case

Required artifact:

- update the `Suspect Surface Ledger` in this file or a phase-specific exported
  copy under `logs/test-runs/phase1-low-signal-ledger-<timestamp>.md`

Exit criteria:

- each suspect test surface is classified as:
  - keep
  - consolidate
  - replace then delete
  - delete as obsolete

## Phase 2: Delete Or Consolidate Migration-Era Tests

Purpose:
remove tests that no longer protect the actual product.

Tasks:

1. collapse duplicated monkeypatched CLI acceptance tests so one contract owns
   each command/backend combination
2. remove cutover/delegation tests once an externally visible behavior contract
   covers the same surface
3. remove tests that only assert "old path should not run" when the observable
   result contract is stronger
4. move any remaining migration-only tests behind a `migration` marker or delete
   them if the migration is complete

Priority files:

- `tests/test_aspic_bridge.py`
- `tests/test_structured_projection.py`
- `tests/test_worldline.py`

Phase-close command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase2-cutover-consolidation-$ts.log"
uv run pytest -vv tests/test_aspic_bridge.py tests/test_structured_projection.py tests/test_worldline.py 2>&1 | Tee-Object -FilePath $log
```

Exit criteria:

- no active production surface depends on cutover-only tests for protection
- duplicate backend wiring tests are reduced materially

## Phase 3: Replace Weak Wiring Tests With Strong Semantic Contracts

Purpose:
trade internal-path assertions for externally meaningful contracts.

Tasks:

1. add deterministic oracle tests for backend equivalence on overlapping
   semantics surfaces
2. add metamorphic tests such as:
   - input order invariance
   - irrelevant-claim invariance
   - repeated-query/history independence
   - rebuild idempotence
   - roundtrip stability
3. where practical, compare public routes against trusted internal or brute-force
   oracles rather than asserting a call graph

Initial target surfaces:

- `worldline`
- `structured_projection`
- `aspic_bridge`
- `verify`
- `repo merge/report/projection` summaries

Phase-close command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase3-semantic-replacements-$ts.log"
uv run pytest -vv tests/test_aspic_bridge.py tests/test_structured_projection.py tests/test_worldline.py tests/test_verify_cli.py 2>&1 | Tee-Object -FilePath $log
```

Exit criteria:

- deleted wiring tests are replaced by equal-or-stronger semantic checks

## Phase 4A: World Model Property Tranche

Purpose:
improve the largest semantic example-heavy file first.

Target file:

- `tests/test_world_model.py`

Required additions:

- binding order invariance beyond current spot checks
- irrelevant concept/claim injection invariance
- sidecar schema/version rejection as a boundary hard-failure family
- value derivation history independence
- conflict detection permutation invariance

Phase-close command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase4a-world-model-$ts.log"
uv run pytest -vv tests/test_world_model.py tests/test_worldline_properties.py 2>&1 | Tee-Object -FilePath $log
```

Exit criteria:

- at least one meaningful new property/metamorphic slice is kept
- existing spot checks are either strengthened or shown sufficient by proof

## Phase 4B: Git Backend And Repo Stateful Tranche

Purpose:
raise the protection on repo/public-route semantics.

Target files:

- `tests/test_git_backend.py`
- repo-related merge/report/projection tests

Required additions:

- strengthen alignment with `test_git_properties.py` stateful model
- more public-route differential checks between worktree state and git state
- branch/history operations expressed as state transitions, not only examples

Phase-close command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase4b-git-backend-$ts.log"
uv run pytest -vv tests/test_git_properties.py tests/test_git_backend.py tests/test_repo_branch.py tests/test_merge_cli.py tests/test_merge_report.py 2>&1 | Tee-Object -FilePath $log
```

Exit criteria:

- stateful or differential protection is increased on at least one repo public
  route that was previously example-only

## Phase 4C: CLI And Source CLI Tranche

Purpose:
reduce low-signal command-survival testing and replace it with stronger
authored-flow contracts.

Target files:

- `tests/test_cli.py`
- `tests/test_source_cli.py`
- `tests/test_source_propose.py`

Required additions:

- fewer pure monkeypatch tests
- more authored-repo flows:
  init/propose/finalize/promote/build/query/verify
- explicit output contract tests where the text is part of the product surface
- avoid survival-only tests unless command success itself is the contract

Phase-close command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase4c-cli-source-cli-$ts.log"
uv run pytest -vv tests/test_cli.py tests/test_source_cli.py tests/test_source_propose.py tests/test_verify_cli.py 2>&1 | Tee-Object -FilePath $log
```

Exit criteria:

- at least one low-signal CLI cluster is replaced by a stronger authored-flow
  contract

## Phase 4D: ATMS And Worldline CLI Tranche

Purpose:
strengthen backend/result contracts for reasoning-facing CLI surfaces.

Target files:

- `tests/test_atms_engine.py`
- `tests/test_worldline.py`
- `tests/test_worldline_properties.py`
- nearby reasoning CLI tests

Required additions:

- backend result contracts
- serialization/result-schema contracts
- cross-command consistency where two commands expose the same underlying state

Phase-close command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase4d-atms-worldline-cli-$ts.log"
uv run pytest -vv tests/test_atms_engine.py tests/test_worldline.py tests/test_worldline_properties.py tests/test_verify_cli.py 2>&1 | Tee-Object -FilePath $log
```

Exit criteria:

- at least one backend/wiring-heavy cluster is replaced by a stronger public
  result contract

## Phase 5: Typed Test Builders And Fixture Refactor

Purpose:
stop letting raw dict payloads dominate core semantic tests.

Tasks:

1. introduce typed or named test builders for claims, concepts, stances,
   justifications, worldline definitions, and repo states
2. keep raw YAML/JSON/SQLite fixtures only at explicit boundary tests
3. split oversized helpers in `tests/conftest.py` by subsystem if needed
4. replace anonymous inline dict construction in core semantic tests where it
   obscures the contract

Benefits:

- clearer tests
- fewer accidental invalid states
- easier property-strategy composition
- closer alignment with the project rule that core semantics should not live as
  loose dict payloads

Exit criteria:

- new semantic tests default to builders/domain objects rather than raw dicts
- `tests/conftest.py` stops growing as the universal bag of ad hoc helpers

Phase-close command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase5-builders-refactor-$ts.log"
uv run pytest -vv tests/test_world_model.py tests/test_worldline.py tests/test_build_sidecar.py tests/test_source_relations.py 2>&1 | Tee-Object -FilePath $log
```

## Phase 6: End-to-End Minimal-Mocking Coverage

Purpose:
ensure each major workflow has at least one real path with minimal mocking.

Required flows:

1. source authoring:
   `source init -> propose -> finalize -> promote`
2. sidecar build:
   authored repo -> build -> SQLite assertions through public readers where
   possible
3. verify flow:
   authored source/repo state -> `verify` commands -> structured output checks
4. worldline flow:
   authored knowledge -> build -> worldline run -> persisted/rendered result
5. repo/git flow:
   repo mutations -> history/log/branch/report surfaces

Rules:

- mocking is allowed only to isolate external services or truly expensive
  dependencies
- if a command family only passes through monkeypatched fakes, it does not count
  as e2e coverage

Exit criteria:

- each listed flow has a minimally mocked passing test path

Phase-close command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase6-e2e-ratchet-$ts.log"
uv run pytest -vv tests/test_source_cli.py tests/test_verify_cli.py tests/test_worldline.py tests/test_git_backend.py 2>&1 | Tee-Object -FilePath $log
```

## Phase 7: Suite Structure And Ongoing Guardrails

Purpose:
keep the suite from degrading again.

Tasks:

1. split giant mixed-purpose files where the split improves ownership and
   readability
2. document test-style guidance:
   - when to use property tests
   - when to use differential tests
   - when CLI tests are appropriate
   - when monkeypatching is acceptable
3. add a review rule for new tests:
   - if a test asserts internal call routing, justify why the observable
     contract is insufficient
4. optionally add a lightweight CI check that lists newly added `migration`
   tests so they do not accumulate unnoticed

Exit criteria:

- future test additions are guided by explicit rules instead of local habit

Phase-close command shape:

```powershell
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
$log = "logs/test-runs/phase7-guardrails-$ts.log"
uv run pytest -vv tests 2>&1 | Tee-Object -FilePath $log
```

## Recommended Slice Order

Do the work in this order:

1. Phase 0 measurement
2. Phase 1 low-signal ledger
3. Phase 2 consolidation of duplicated cutover/wiring tests
4. Phase 3 semantic replacement contracts for those deletions
5. Phase 4A world_model tranche
6. Phase 4B git_backend/repo tranche
7. Phase 4C cli/source_cli tranche
8. Phase 4D atms/worldline cli tranche
9. Phase 5 typed builder refactor
10. Phase 6 minimally mocked e2e ratchet
11. Phase 7 guardrails

## First Three Concrete Slices

### Slice A: coverage + markers

- update `pyproject.toml`
- add the tooling
- capture baseline logs

### Slice B: aspic/structured/worldline low-signal tranche

- build the suspect ledger
- consolidate duplicate CLI/backend acceptance tests
- replace the removed wiring checks with behavior contracts

### Slice C: world_model property tranche

- add 2-4 high-value metamorphic properties
- keep each property tied to a real semantic risk:
  dependency soundness, permutation invariance, irrelevant-input invariance,
  history independence

## Completion Standard

This workstream is not complete when the suite is merely green.

It is complete when we can point to:

- measured visibility
- fewer obsolete and redundant tests
- stronger semantic invariants on the core reasoning surfaces
- more real end-to-end protection with less mock-driven noise
