# ASPIC completeness planning notes - 2026-07-22

## Current findings

- B2 is distinct from B1: B1 already prevents incomplete grounding from
  entering ASPIC. B2 owns incompleteness produced by ASPIC computation itself.
- The package-owned `build_arguments_for(..., max_depth=10)` currently returns
  an ordinary `frozenset[Argument]`. When recursion exceeds `max_depth`, it
  returns an empty set at that branch, so callers cannot distinguish exhaustion
  from a genuinely argument-free branch.
- Propstore's `ClaimQueryResult` consequently carries arguments, attacks, and
  defeats but no completeness evidence.
- The package-owned `ASPICQueryResult` already has solver statuses such as
  `success`, `unavailable_backend`, `backend_error`, and `protocol_error`.
  `analyze_aspic_backend()` currently stores this as generic metadata under
  `package_status` and emits an empty extension tuple for every non-success.
- `AnalyzerResult` has no typed ASPIC status/failure field; its generic metadata
  is therefore the only current carrier for solver status.
- Production world resolution and worldline capture use the materialized ASPIC
  projection path. They can interpret an empty/absent extension as an ordinary
  semantic outcome unless backend computation status is carried separately.
- The formal-argumentation dependency is pinned to Git revision
  `3ff70f3d824a27fc03eb50d3dc128e9c2dc14e05`; package-owner changes must land
  there first and Propstore must then repin deliberately.

## Intended B2 outcome

- Package goal-directed construction returns explicit max-depth completeness
  evidence without treating normal finite cycle rejection as exhaustion.
- Propstore carries package solver status on the existing typed analyzer result
  surface rather than burying it in generic metadata or adding a generic
  cross-backend status.
- World resolution and worldline capture fail closed on ASPIC partial/failed
  computation, while diagnostic surfaces may preserve partial evidence with an
  explicit backend-specific reason.

## State and blocker

- State: explanation/research only; no B2 plan mutation or implementation has
  begun.
- Blocker: the current three-line B2 plan does not yet settle the exact package
  result type/status vocabulary or the exact typed `AnalyzerResult` field
  shape. Those choices should be specified before execution.

## Next action

- Explain the current failure modes and proposed package-first propagation to
  the user. If the user elects to plan B2, inspect the sibling argumentation
  repository at the pinned revision/current head and settle exact types,
  statuses, propagation fields, tests, commits, and repin order.

## Design-settlement update

- Directly read the rendered page images for Modgil and Prakken, printed
  pp. 36-37 (`pngs/page-007.png` and `pngs/page-008.png`). Definition 3.6
  constructs ASPIC+ arguments recursively from knowledge-base premises and
  inference rules as finite argument trees. A bounded prefix is not the
  defined full argument set.
- Directly read the rendered page images for Thimm, printed pp. 5-7
  (`pngs/page-004.png` through `pngs/page-006.png`). The paper explicitly
  separates approximate argument construction (a bounded subgraph) from the
  unchanged abstract semantics subsequently run on that subgraph. Exact
  semantics over a partial construction remains an approximate answer.
- The sibling package checkout is at `099db662aaa5adb38282724f8a6a38f037eb5646`;
  Propstore's pin `3ff70f3d824a27fc03eb50d3dc128e9c2dc14e05` is its ancestor.
  The ASPIC source and relevant tests have no committed diff between that pin
  and current HEAD, so the examined live source matches the pin.
- The sibling checkout is substantially dirty (`AGENTS.md` modified, one test
  deleted, and many untracked records/artifacts). It is evidence only and must
  not be edited. Package implementation needs a separately verified clean
  worktree/branch rooted at the exact chosen base.
- Package source confirms `build_arguments_for()` has explicit cycle detection
  (`in_progress`) in addition to `max_depth`; `depth > max_depth` silently
  returns an empty set. The current depth-limit test therefore conflates a
  truncated search with complete absence of arguments.

## Updated state and blocker

- The semantic decision is settled: reaching any depth cutoff makes the whole
  goal-directed construction incomplete, even when partial arguments exist and
  exact Dung semantics later succeeds.
- The exact API names, Propstore carrier field, production disposition, and
  executable gates still need to be written into the tracked plan before code
  implementation.

## Updated next action

- Inspect the narrow Propstore analyzer/world/worldline definitions and all
  package callers, then write one exact B2 execution contract into
  `plans/unwired-and-missing-code-convergence.md`. Do not edit either codebase
  yet.

## Settled B2 contract

- Package goal-directed construction will use
  `ArgumentBuildStatus(StrEnum)` with `COMPLETE = "complete"` and
  `MAX_DEPTH_EXHAUSTED = "max_depth_exhausted"`, plus frozen
  `ArgumentBuildResult(arguments, status, max_depth, cutoff_literals)`.
- `build_arguments_for()` itself changes return type; there is no compatibility
  wrapper or parallel legacy function. Its default becomes unbounded
  (`max_depth: int | None = None`) because explicit cycle detection already
  terminates finite grounded theories. Explicit negative limits are rejected;
  zero remains a valid diagnostic bound. Any reached cutoff makes the whole
  result `MAX_DEPTH_EXHAUSTED`, while finite cycle rejection remains complete.
- Package solver status will be owned as `ASPICQueryStatus(StrEnum)` with the
  exact existing vocabulary `SUCCESS`, `UNAVAILABLE_BACKEND`, `BACKEND_ERROR`,
  and `PROTOCOL_ERROR`. `ASPICQueryResult.status` and every producer/test use
  enum members instead of loose strings.
- Propstore `ClaimQueryResult` carries the package-owned build result directly
  as `construction: ArgumentBuildResult`; it derives its existing views from
  `construction.arguments` and does not copy status/evidence into another DTO.
- Propstore `AnalyzerResult` gains exactly
  `aspic_query_status: ASPICQueryStatus | None = None`.
  `analyze_aspic_backend()` always populates it, removes `package_status` from
  generic metadata, compares enum identity, and preserves detailed backend
  reason as diagnostic metadata.
- The optional solver analyzer and production materialized projection are not
  unified through a new helper/adapter. Production ASPIC uses exhaustive
  `build_arguments()` and its semantics function has no partial-success result:
  a returned empty extension is legitimate, while an exception is failure.
  Resolution already propagates such exceptions. Worldline diagnostics capture
  them as `status="error"`; committed materialization must replace its narrow
  grounding-only check with refusal of any non-`None` argumentation status or
  error before assigning/saving results.
- The package implementation must use a new clean worktree at
  `C:\Users\Q\code\argumentation-b2` from verified commit
  `099db662aaa5adb38282724f8a6a38f037eb5646`; that path does not currently
  exist. The dirty primary package checkout remains untouched.

## Current state

- Propstore is on `master`, eight commits ahead of `origin/master`, with only
  unrelated untracked `pyghidra_mcp_projects/`; the notes file remains
  uncommitted/ignored.
- No B2 code has been edited. The next authorized mutation is the tracked plan
  update containing exact classifications, slices, commands, commit order, and
  gates.

## Planning completion

- `plans/unwired-and-missing-code-convergence.md` now contains the settled B2
  exact execution contract: literature basis, package worktree authority,
  exact result/status types, propagation fields, production-path disposition,
  deletion-first classifications, four ordered commits, exact focused/full
  commands, and search gates.
- The production decision explicitly rejects a new shared adapter. Optional
  encoded-solver analysis remains separate from exhaustive materialized
  world/worldline analysis.
- The plan also settles the previously dropped successful multi-extension
  worldline path and distinguishes a legitimate zero-extension result from an
  exception or construction cutoff.
- No implementation has begun. Next action, only after user authorization, is
  B2 Slice 1 exactly as written: load `protocols:cleanup-refactor`, reverify the
  package base/worktree facts, create the clean package worktree and package
  execution record, then perform the package result cutover.

## Execution update - B2 Slice 1

- User authorized full B2 execution.
- Loaded `protocols:cleanup-refactor` as the active deletion-first control
  surface.
- Reverified the package base, pin ancestry, relevant no-diff claim, dirty
  primary checkout, absent branch, and absent worktree.
- Created clean worktree `C:\Users\Q\code\argumentation-b2` on branch
  `b2-aspic-completeness` at
  `099db662aaa5adb38282724f8a6a38f037eb5646`; the dirty primary package checkout
  remains untouched.
- Created the package tracked record
  `plans/aspic-completeness-fixed-point-log.md`.
- Replaced the bare `build_arguments_for()` set return with the planned typed
  result, removed the silent default cap, added explicit cutoff evidence, and
  rewrote all package callers directly without a compatibility surface.
- Added the planned unbounded, bounded-empty, bounded-partial, attacker-cutoff,
  sufficient-bound, deterministic-cutoff, negative-bound, and finite-cycle
  tests. The focused suite passes 28 tests.
- The planned package-wide Pyright gate exposed one pre-existing, unrelated
  error in unchanged `src/argumentation/solving/solver.py:831`: inferred kwargs
  value types exclude the existing `engine: str`. The tracked plan now records
  a separate atomic gate-repair slice and commit; Slice 1 uses changed-owner
  Pyright and the full package gate remains mandatory after that repair.

Current state:
- Slice 1 source and package execution record are uncommitted in the clean
  package worktree.
- Propstore has only the tracked plan update plus unrelated untracked
  `pyghidra_mcp_projects/`; this notes file remains uncommitted/ignored.

Next action:
- Run the corrected Slice 1 owner Pyright and exact Ruff/format gates, update the
  package record, and commit exactly
  `feat(aspic): expose bounded construction status` before Slice 2.

## Execution update - Slice 1 committed / Slice 2 active

- Slice 1 passed 28 focused tests, changed-owner Pyright, focused Ruff, format,
  search gates, and staged-diff checks.
- Committed Slice 1 in the clean package worktree as
  `063910e feat(aspic): expose bounded construction status`.
- Reread the controlling plan after the passing substantial test run and moved
  only then to Slice 2.
- Slice 2 classification is active: `ASPICQueryResult.status: str` is valid
  package-owned capability with the wrong representation; every producer and
  boundary assertion is being rewritten to the package enum. ABA remains out of
  scope.
- Added `ASPICQueryStatus` with the four planned members, changed the package
  result/failure signature, replaced every source producer, and added the enum
  to `__all__`. Source searches show no remaining ASPIC status string producer.
- `tests/test_aspic_encodings.py` now imports the owner enum and uses identity
  assertions for its existing status cases. The differential tests and an
  explicit backend-error assertion still remain before the Slice 2 gate.

Current state:
- Package worktree has the Slice 1 ledger hash update plus uncommitted Slice 2
  edits in `aspic_encoding.py` and its first test file.
- No Propstore source has been changed; the dirty primary package checkout and
  `pyghidra_mcp_projects/` remain untouched.

Next action:
- Finish all Slice 2 enum assertions, add direct backend-error coverage if the
  current tests do not already prove it, then run the exact focused gates and
  commit `refactor(aspic): type query execution status`.

## Execution update - Slice 2 ready to commit

- Completed every solver-status producer and assertion cutover to
  `ASPICQueryStatus`; no parallel string constants or ABA changes were added.
- Added direct `BACKEND_ERROR` process-failure coverage. All four enum families
  now have identity assertions.
- Focused ASPIC encoding/differential suite passes 21 tests after formatting.
- Changed-owner Pyright reports zero errors; focused Ruff and format checks pass.
- Source/test search finds zero literal constructor statuses for the four old
  values.
- `tests/structured/aspic/test_aspic_encodings.py` is tracked and checked out as
  CRLF (`i/crlf w/crlf`). Plain `git diff --check` reports its existing carriage
  returns as whitespace on changed lines. The package ledger records that
  baseline, and the equivalent check with `core.whitespace=...cr-at-eol` passes
  without rewriting the whole file's line endings.

Current state:
- Slice 2 owns only `aspic_encoding.py`, its two planned tests, and the package
  ledger update. It is not staged or committed yet.

Next action:
- Stage exactly those four paths, validate the staged diff with the repository's
  existing CRLF treated as EOL, and commit exactly
  `refactor(aspic): type query execution status`.

## Execution update - Slice 2 committed / solver formatting isolated

- Committed Slice 2 as
  `25483a5 refactor(aspic): type query execution status`.
- The separate package Pyright repair initially touched one annotation and one
  dead import, but its required format check proved `solver.py` was wholly
  unformatted and would create a broad mechanical diff.
- Reported the mismatch before further source edits and corrected the tracked
  plan to preserve Git accountability: mechanical formatting/dead-import
  deletion first, then the one-line annotation in the next commit.
- Restored the annotation to baseline, retained only the proven-dead import
  deletion, formatted `solver.py`, and ran the isolated gates.
- Solver routing suite passes 45 tests; focused Ruff and format checks pass.
- Package Pyright reports exactly the one expected pre-existing mapping error,
  moved by formatting from line 831 to line 835, with no additional errors.

Current state:
- The clean package worktree contains an uncommitted mechanical solver-format
  slice plus its ledger update. No Pyright repair is hidden in that diff.

Next action:
- Inspect and stage only `solver.py` plus the package ledger, commit exactly
  `style(solving): format solver module`, then reapply the one-line annotation
  as the separate `fix(solving): type SAT finder kwargs` slice.

## Execution update - package repair commits complete

- Committed the isolated formatting/dead-import prerequisite as
  `51786f7 style(solving): format solver module`.
- Reapplied only `shared: dict[str, object]`, yielding a one-line solver source
  diff. Solver routing passed 45 tests; package-wide Pyright then reported zero
  errors; focused Ruff and format checks passed.
- Committed the narrow repair as
  `5233a27 fix(solving): type SAT finder kwargs`.
- Package history now contains, in order:
  `063910e` bounded construction result,
  `25483a5` typed solver status,
  `51786f7` isolated formatting prerequisite, and
  `5233a27` one-line Pyright repair.

Current state:
- The next required action is the package full gate. The package execution
  record's final commit hash will be updated after the gate and carried into the
  first Propstore commit with the new pin only if required by the plan; no
  package source slice is left uncommitted.

Next action:
- Run, separately and exactly, package full pytest, package-wide Pyright,
  repository Ruff, and repository format check; then record the exact repin HEAD.
## 2026-07-22 checkpoint - package full gate after Probe 7 deletion

- The user explicitly authorized deletion of the obsolete intentionally red
  Probe 7 contract.
- The Propstore B2 plan now classifies that edge as `dead/test/scaffold surface`
  and requires deletion without implementing, aliasing, skipping, or replacing
  the nonexistent diagnostic owner.
- In clean package worktree `C:\Users\Q\code\argumentation-b2`, the current
  uncommitted slice contains only the tracked fixed-point-log update and deletion
  of `tests/structured/aba/test_aba_cadical2_eager_arc_contract.py`.
- The deletion removed the collection failure. Exact package gate
  `uv run pytest -q` completed with 3156 passed, 4 skipped, 1 xfailed, and 9
  failed in 416.97 seconds.
- Six failures are stale monkeypatch edges in
  `tests/structured/aba/test_aba.py` targeting the deleted unused solver alias
  `sat_aba_support_extensions`; do not restore that alias.
- One failure is the page-image provenance contract because the clean worktree
  lacks the referenced paper PNG files.
- Two failures require the optional vendored CaDiCaL 2.2.1 batch binary at
  `tools/solvers/cadical-2.2.1/cadical.exe`.
- Next action: finish classifying the stale monkeypatch edge and the two missing
  environment artifacts, then correct the plan before any further package
  mutation. Complete and commit the Probe 7 deletion slice before starting a
  separate caller-rewrite slice.

## 2026-07-22 checkpoint - Probe 7 committed, caller repair active

- The obsolete Probe 7 contract deletion and tracked package execution record
  were committed in the clean package worktree as
  `d1d5d7d test(aba): delete obsolete Probe 7 contract`.
- The next atomic slice rewrites the two stale monkeypatch dependency edges in
  `tests/structured/aba/test_aba.py` from the deleted solver alias to the true
  owner `argumentation.structured.aba.aba_sat.support_extensions`.
- No production alias or import was restored.
- Exact focused gate `uv run pytest tests/structured/aba/test_aba.py -q` passes:
  30 passed in 3.54 seconds.
- The 13 required ignored page images and the ignored CaDiCaL 2.2.1 binary were
  verified present in the primary package checkout; they will be copied only to
  matching ignored paths in the clean worktree for the final package gate.
- Next action: reread the B2 plan, run focused Ruff and format checks, update the
  tracked package execution record, and commit the caller repair before setting
  up ignored full-gate artifacts.

## 2026-07-22 checkpoint - caller repair ready to commit

- Ruff exposed 13 pre-existing formatting hunks in
  `tests/structured/aba/test_aba.py`; the plan was corrected before mutation so
  mechanical and semantic changes remained separate.
- Whole-file test formatting was committed as
  `4333ebb style(aba): format solver tests`. Its exact intermediate test result
  was recorded: six known stale monkeypatch failures and 24 passes; Ruff and
  format gates passed.
- The next slice reapplied only the two monkeypatch target rewrites to
  `argumentation.structured.aba.aba_sat.support_extensions`.
- Exact focused gates now pass: 30 ABA tests, Ruff check, and Ruff format check.
- Next action: update the tracked package execution record, commit exactly as
  `test(aba): patch enumeration owner directly`, then copy only the verified
  ignored page images and CaDiCaL binary into the clean worktree for the final
  package gates.

## 2026-07-22 checkpoint - final package test has one runtime failure

- Caller repair was committed as
  `fd7e274 test(aba): patch enumeration owner directly`.
- The five required ignored paper-image directories and the ignored CaDiCaL
  executable were copied from the primary checkout into matching ignored paths
  in the clean worktree; all 13 page paths and the executable exist, and tracked
  status remains clean.
- Exact full gate `uv run pytest -q` now reports 3164 passed, 4 skipped,
  1 xfailed, and 1 failed in 425.40 seconds.
- The sole failure is
  `test_engine_override_matches_oracle[cadical221-batch]`: the executable exits
  with Windows status 3221225785 (`0xC0000135`, runtime DLL not found).
- This is an environment input failure, not a solver assertion failure. The
  recorded package experiment already notes that the MinGW runtime directory
  must be on `PATH` for this executable.
- Next action: identify the exact existing MinGW runtime directory from current
  environment/records, correct the plan before altering the gate environment,
  and rerun the isolated engine test before repeating the full package gate.

## 2026-07-22 checkpoint - package tests and Pyright green, Ruff baseline red

- Correction: Windows status 3221225785 is `0xC0000139`
  (`STATUS_ENTRYPOINT_NOT_FOUND`), not a missing-DLL status. The executable was
  loading an incompatible MinGW runtime from the ambient path.
- With only `C:\Users\Q\scoop\apps\mingw-winlibs\current\bin` prepended to the
  test process's `PATH`, the isolated engine contract passes: 7 tests.
- The exact package-wide test gate under that process-local environment passes:
  3165 passed, 4 skipped, 1 xfailed in 451.79 seconds.
- Exact package-wide Pyright passes: zero errors, warnings, or information.
- Exact `uv run ruff check .` is baseline-red with 19 findings spread across
  unrelated scripts, dynamics, probabilistic code, ABA decomposition, and test
  modules. Thirteen are reported auto-fixable; six require explicit edits or
  scoped noqa placement.
- No Ruff repair has been made yet. The caller-repair commit remains the latest
  clean package commit, with ignored gate artifacts present only in the clean
  worktree.
- Next action: classify the 19 Ruff findings and correct the B2 plan into
  separate atomic repair slices before editing; then run package-wide Ruff and
  format gates again.

## 2026-07-22 checkpoint - package formatted, Ruff slices settled

- Repository-wide Ruff formatting changed the exact 198 files named by the
  gate and was committed separately as `807d734 style: format package`.
- Formatting-only gates passed: full suite 3165 passed, 4 skipped, 1 xfailed;
  package Pyright zero errors; all 294 Python files formatted.
- Ruff still reports exactly 19 non-format findings. The B2 plan now contains
  three exact atomic repair slices:
  1. Production owners: named local ranking callable, move the Dung import to
     the import block, and delete two dead ABA-decomposition imports.
  2. Test owners: move one valid import, delete ten dead imports, and remove two
     inert `f` prefixes.
  3. Script/tool IO boundaries: line-scoped E402 annotations on two imports that
     must follow repository-root `sys.path` setup.
- No Ruff repair edit has been made yet; package worktree is clean at the
  formatting commit, apart from ignored full-gate artifacts.
- Next action: execute production-owner slice, run its exact focused tests,
  Pyright, Ruff, and format checks, update the tracked fixed-point log, and
  commit before starting the test-owner slice.

## 2026-07-22 checkpoint - production Ruff repair committed

- Production-owner Ruff repair is committed as
  `ff6e138 fix: repair production Ruff violations`.
- It contains only the named local default-ranking callable, movement of the
  existing Dung import into its module import block, deletion of two dead ABA
  decomposition imports, and the tracked execution record.
- Exact focused gates passed: 34 tests, package Pyright zero errors, focused
  Ruff check, and focused Ruff format check.
- The test-owner slice is now active. The first edit moved
  `cayrol_derived_defeats` into the existing top-level bipolar import block and
  removed its late module import; no other test-owner file is edited yet.
- Next action: perform only the remaining planned dead-import and inert-prefix
  deletions in the seven named test modules, then run the exact eight-module
  focused test/Ruff/format gates before committing.

## 2026-07-22 checkpoint - test Ruff repair committed

- Test-owner Ruff repair is committed as
  `ccf4e0b test: repair Ruff violations`.
- It contains one valid import moved into its top-level block, deletion of ten
  Ruff-proven dead imports, deletion of two inert `f` prefixes, and the tracked
  execution record.
- Exact focused gates passed: 137 tests across the eight named modules, focused
  Ruff check, and focused Ruff format check.
- The package worktree is clean at the start of the final Ruff slice.
- Next action: add only line-scoped `# noqa: E402` annotations to the two
  direct-execution imports that must follow repository-root `sys.path` setup,
  run focused Ruff/format gates, update the package log, and commit exactly as
  `chore: mark bootstrap imports`.

## 2026-07-22 checkpoint - package fixed point complete

- The final bootstrap-boundary commit, including the package fixed-point log,
  is `eb816ee chore: mark bootstrap imports`.
- Exact post-amend package gates all pass on that commit:
  - full suite: 3165 passed, 4 skipped, 1 xfailed in 505.38 seconds;
  - package Pyright: zero errors;
  - package Ruff check: pass;
  - package Ruff format check: all 294 files formatted.
- Package tracked worktree is expected clean; the copied paper page images and
  CaDiCaL executable remain ignored gate-only inputs.
- `eb816ee` is the exact B2 Propstore repin target under the current plan.
- Next action: verify package status/HEAD, create the tracked Propstore B2
  execution record, then address the required reachability of `eb816ee` before
  changing the Propstore git dependency and running `uv lock`.

## 2026-07-22 checkpoint - publication redirected to primary `main`

- The user confirmed the actual package target branch is `main`, stashed the
  primary package checkout, directed use of it, and directed deletion of the
  temporary clean clone.
- `C:\Users\Q\code\argumentation-b2-main` was removed to the Windows Recycle
  Bin and no longer exists.
- Primary package checkout evidence:
  - branch: `main`;
  - HEAD and `origin/main`: `099db662aaa5adb38282724f8a6a38f037eb5646`;
  - tracked files: clean;
  - numerous user-owned untracked logs, notes, prompts, reports, paper state,
    and scripts remain and must be preserved.
- The plan now uses the primary checkout for a no-ff merge of
  `b2-aspic-completeness`, verifies the merge tree equals gated branch commit
  `eb816ee`, then pushes `origin/main`.
- Next action: verify the B2 changed-path set has zero overlap with every
  user-owned untracked path. If zero, merge without touching or staging any
  untracked file; otherwise stop before the merge.

## 2026-07-22 checkpoint - package merged and published

- The B2 changed-path set contained 209 tracked paths; the primary package
  checkout contained 437 user-owned untracked paths; exact case-insensitive
  overlap was zero.
- `b2-aspic-completeness` was merged into primary `main` with an explicit no-ff
  merge commit: `978b10edb8eaf106f64cd760cfeedce1c3cbb237`.
- The merge tree hash is `f23ce11bee5f4a2fa08b0818c92c2ffcbd4ccbfb`,
  exactly equal to gated branch commit `eb816ee`'s tree hash.
- `git push origin main` succeeded, and `git ls-remote` verifies
  `origin/main` exactly at `978b10edb8eaf106f64cd760cfeedce1c3cbb237`.
- All primary-package untracked paths were preserved; no untracked file was
  staged or touched.
- Next action: create the tracked Propstore fixed-point record, pin the formal
  argumentation dependency to `978b10e`, run `uv lock`, and verify the lock
  resolves that exact revision before editing Propstore semantic callers.

## 2026-07-22 checkpoint - Propstore Slice 3 repin complete

- The tracked Propstore execution record now exists at
  `plans/aspic-completeness-fixed-point-log.md`.
- `pyproject.toml` pins formal-argumentation to published merge commit
  `978b10edb8eaf106f64cd760cfeedce1c3cbb237`; `uv lock` completed and both
  formal-argumentation entries in `uv.lock` resolve that exact revision.
- The old pin `3ff70f3d824a27fc03eb50d3dc128e9c2dc14e05` has no remaining hit in either
  dependency file.
- Current deletion-first dispositions are unchanged from the controlling plan:
  `query_claim()` is a valid capability consuming the wrong result
  representation and must consume `ArgumentBuildResult.arguments` while
  returning the same construction result; analyzer `package_status` is valid
  backend control evidence in generic metadata and must move to the typed
  `AnalyzerResult.aspic_query_status` field.
- No Propstore production or test source has been edited yet. The unrelated
  untracked `pyghidra_mcp_projects/` path remains untouched, and this notes file
  remains uncommitted.
- Next action: edit only the three Slice 3 owner modules and their three focused
  test modules, then run the exact logged pytest, Pyright, import-lint, and
  focused Ruff gates before committing the slice.

## 2026-07-22 checkpoint - Slice 3 gates pass, search assertion remains

- The Slice 3 owner and focused test changes are implemented without a helper,
  adapter, compatibility wrapper, or parallel metadata control path.
- Exact gates passed on the current semantic code: logged focused pytest
  reported 38 passed; package Pyright reported zero errors; all three import
  contracts were kept; focused Ruff check and Ruff format check passed.
- The intended pre-commit B2 search exposed one test-only hit: the new negative
  assertion spells the deleted metadata key literally, so the required future
  zero-hit search cannot yet pass even though production no longer emits it.
- The unrelated untracked `pyghidra_mcp_projects/` remains untouched, and this
  notes file remains uncommitted.
- Next action: rewrite only that negative assertion so it still proves the key
  is absent without retaining the forbidden literal, rerun the affected focused
  gates and search, update the tracked execution record, and commit Slice 3 with
  the exact required subject.

## 2026-07-22 checkpoint - Slice 3 committed, Slice 4 classified

- Propstore Slice 3 is committed as
  `31939b79 feat(aspic): propagate computation status` after the corrected tree
  passed 38 logged tests, package Pyright, all import contracts, focused Ruff,
  focused format, and the three Propstore zero-hit B2 searches.
- Slice 4 production reading confirms `_resolve_structured_argumentation()` has
  no exception conversion: a semantics exception already escapes, so the named
  resolution work is a regression test only.
- `_capture_aspic()` currently accepts only the grounded `frozenset` shape and
  returns `None` for all list shapes. This is a valid capability with a wrong
  caller disposition: consume both existing successful result shapes directly,
  map every extension to claim ids, and populate existing typed state fields.
- The runner already records `status="error"` and the typed argumentation error
  marker after capture failure, but omits the reasoning backend. The required
  edit is only to populate the existing backend field from policy.
- `materialize_worldline()` still checks only the grounding status string. This
  is the planned incomplete-consumer disposition: replace it with the existing
  state fields' fail-closed invariant before assigning results or saving.
- No Slice 4 source or test file has been edited. The unrelated untracked
  `pyghidra_mcp_projects/` remains untouched, and this notes file remains
  uncommitted.
- Next action: implement those three exact production edits and the four named
  regression families, then run the exact Slice 4 logged and static gates.

## 2026-07-22 checkpoint - Slice 4 implementation gated through Ruff

- `_capture_aspic()` now normalizes grounded, multiple-extension, and legitimate
  zero-extension successful results into the existing worldline state fields;
  no helper, adapter, or alternate production path was added.
- Argumentation capture failures now retain the selected backend together with
  existing typed status/error evidence, and materialization fails closed on any
  existing argumentation status or error before assigning results or saving.
- The four named regression families are implemented, including proof that
  resolution semantics exceptions escape and that grounding exhaustion and
  captured ASPIC failure cannot create a materialization commit.
- Final focused logged pytest reports 55 passed in 8.32 seconds at
  `logs/test-runs/pytest-20260722-171802.log`.
- `uv run pyright propstore` reports zero errors after explicitly typing the
  zero-extension claim set; all three import contracts are kept; package-wide
  Ruff check passes.
- The unrelated untracked `pyghidra_mcp_projects/` remains untouched, and this
  notes file remains uncommitted.
- Next action: run package-wide Ruff format check, rerun every B2 zero-hit
  search on the final tree, update the tracked execution ledger, and commit
  Slice 4 with the exact required subject.

## 2026-07-22 checkpoint - B2 complete

- The combined B2 gate passed 93 tests; final Pyright, import contracts, Ruff,
  and format gates passed; the full logged Propstore suite passed 1830 tests
  with 1 skipped in 87.87 seconds.
- Propstore commits are `31939b79 feat(aspic): propagate computation status`
  and `da0b48b4 fix(worldline): refuse incomplete argumentation results`.
- The tracked fixed-point ledger contains the final gate evidence, and all
  three B2 checklist items in the active plan are marked complete.
- Formal-argumentation `origin/main` is exactly
  `978b10edb8eaf106f64cd760cfeedce1c3cbb237`; Propstore remains pinned and
  locked to that revision. The gated package branch tip remains `eb816ee`.
- The temporary `argumentation-b2-main` clone does not exist. The ignored B2
  notes remain uncommitted. The unrelated untracked
  `pyghidra_mcp_projects/` remains untouched.
- No B2 blocker or unchecked execution item remains. No Propstore push was
  performed because the user authorized the package merge/push, not a
  Propstore push.
