# Grounding completeness planning record

## Scope and control surfaces

- Planning-only research for item 1 in `notes-propstore-followup-audit.md`.
- Active plan: `plans/unwired-and-missing-code-convergence.md`, Q2 and
  Workstream B1 plus only the necessary grounding-to-ASPIC handoff.
- No production implementation is authorized in this pass.
- The `protocols:researcher` evidence discipline is in use without Ward because
  the user's standing instruction forbids Ward.

## Current findings

- The audit premise is still live. Production `WorldQuery` does not implement
  `GroundingBundleStore.grounding_bundle()`; the only implementation found is a
  test double in `tests/test_resolution.py`.
- `grounding.grounder.ground(...)` already accepts `max_arguments` and converts
  `gunray.EnumerationExceeded` into a `GroundedRulesBundle` containing
  `status="budget_exceeded"`, `budget_reason`, partial arguments, and partial
  grounding inspection.
- `grounding.loading.build_grounded_bundle(...)` is the first loss point: it has
  no `max_arguments` parameter and therefore cannot pass a production budget to
  `ground(...)`.
- `derived_build._build_sidecar_file(...)` builds a bundle but persists only its
  four marking sections in the raw `grounded_fact` table. Status, reason,
  arguments, inspection, and the chosen budget are not persisted.
- `pks grounding status/show/query/arguments` each rebuild directly from the
  repository. None accepts a budget; none renders `status` or `budget_reason`.
- Runtime ASPIC resolution and worldline ASPIC capture require the optional
  `GroundingBundleStore` protocol. Both call `grounding_bundle()` and currently
  inspect no completeness field before treating the bundle as a complete theory.
- Fragility silently substitutes `GroundedRulesBundle.empty()` when the store
  lacks the protocol, hiding the missing production capability.
- `WorldQuery` may be constructed from a `Repository`, or from a
  `DerivedStoreHandle` with no repository. A repository-only implementation of
  `grounding_bundle()` would therefore leave a valid production construction
  path unable to satisfy its advertised capability.
- The sidecar already contains the canonical predicate, defeasible-rule,
  superiority, claim, and concept charters needed to rebuild `GroundingRepo`.
  It does not currently expose grounding-specific typed selectors for them.
- The sidecar content hash does not include a grounding budget. If a build-time
  budget affects persisted output, that budget must be part of the cache key.
- The world-sidecar schema version is currently `1`; adding a grounding build
  status/config table is an incompatible sidecar-shape change and requires a
  version bump.
- `GroundedRulesBundle.status` is currently a loose string even though the only
  defined outcomes are `complete` and `budget_exceeded`. Propstore's existing
  `core.anytime` sentinels intentionally do not mirror owner-package enumeration
  failures, so they are not the owner for Gunray grounding completeness.
- `WorldStore` does not include `grounding_bundle()`. The capability remains an
  optional world-layer protocol used only by ASPIC resolution, ASPIC worldline
  capture, and fragility; making it an umbrella-store requirement would broaden
  the contract beyond the active B1 slice.
- ASPIC resolution already has a fail-closed result channel: no winner leaves the
  `ResolvedResult` conflicted with an explicit `reason`. It does not require a new
  generic result type for B1.
- Worldline rendering already has a typed `WorldlineCaptureError.ARGUMENTATION`
  marker and catches argumentation exceptions in `run_worldline()`. The durable
  commit boundary is `app.worldlines.materialize_worldline()`, which currently
  saves that error-marked result without qualification. Q2 therefore needs two
  distinct dispositions: diagnostic rendering may return the typed error state;
  materialization must inspect it and refuse the save.
- `BuildDiagnostic` describes compiler/quarantine diagnostics and does not own a
  grounding computation's deterministic configuration/outcome. Reusing it as
  the grounding build record would conflate two different facts.

## Observations

- Persisting only status/reason is insufficient for `WorldQuery`: ASPIC needs a
  full bundle with source rules/facts/superiority and Gunray inspection.
- Hand-serializing Gunray arguments or inspection would create a new codec/DTO
  surface and conflict with the repository's typed-owner rules.
- A minimal sidecar grounding record must carry at least the selected
  `max_arguments`, the resulting status, reason, and partial-argument count.
  The full ASPIC-ready bundle can then be deterministically reconstructed from
  canonical charter rows using the recorded budget instead of serializing
  Gunray internals.
- The likely simpler owner path is to persist the grounding build configuration
  and outcome beside grounded rows, then rebuild the full typed bundle from the
  canonical charter rows at the `WorldQuery` load boundary using that same
  budget. This still needs proof against cache identity, deterministic rebuild,
  and sidecar-only readers before it can enter an executable plan.
- Q2 remains unresolved. The active recommendation is fail-closed for resolution
  and committed worldline materialization, while diagnostic/inspection surfaces
  may display explicitly labeled partial evidence.
- The world-sidecar content hash currently includes schema/pass/family versions
  and build-time config, but not the grounding budget. The exact chosen budget
  must be included in `world_sidecar_hash_inputs()` and `world_sidecar_hash()` so
  two budgets cannot alias the same derived artifact.
- A transient `pks build --max-arguments` value is not sufficient by itself.
  Ordinary later `WorldQuery(repo)` construction recomputes the sidecar hash
  without remembering that flag and would select/build the default-budget
  artifact instead. A budget intended to define the repository's current
  sidecar must therefore be recoverable from repository-resident content.
- `RenderPolicy` is not the budget owner: it varies per render after the sidecar
  is selected, so placing the grounding build limit there could make the stored
  grounded rows and runtime bundle describe different computations.
- Production `load_grounding_repo()` currently creates each `ConceptRelations`
  with no relationships. Consequently an authored
  `derived_from="concept.relation:..."` predicate cannot mine repository facts,
  even though direct `GroundingRepo` tests can supply them. This is an adjacent
  production-input gap; it must be named separately rather than silently folded
  into completeness propagation.
- A read-only external architectural critique independently confirmed the
  repository-resident budget/cache-identity problem and recommended rebuilding
  the ASPIC-ready bundle from canonical sidecar charters. It also proposed
  deleting eager `grounded_fact` persistence. Direct search then confirmed the
  raw rows have no production reader, while Quire's metadata table was proven
  incapable of holding arbitrary configuration. The corrected recommendation is
  deletion plus a typed derived-only grounding-config charter, pending the
  user's explicit amendment of B1.

## State

- Read-only research complete; no production or test files changed.
- Worktree began clean except unrelated untracked `pyghidra_mcp_projects/`, which
  remains untouched.
- No implementation slice has started.
- The external critique was read-only and modified no repository files.

## Blocker

- Q2 still requires the user's explicit policy confirmation before an
  implementation plan can be literally executable. The code now proves the
  exact choice: incomplete ASPIC resolution stays conflicted with a reason;
  diagnostic worldline rendering records a typed argumentation error; committed
  worldline materialization raises and does not save.
- The draft selects typed, commit-pinned `propstore.yaml` configuration as the
  durable budget source. Execution still awaits the user's decision-gate
  confirmation; no transient CLI/render budget or code-only fixed ceiling is
  proposed.

## Next action

- The user confirmed both decision gates on 2026-07-22. The decisions and the
  four-slice B1 execution control surface have been promoted into
  `plans/unwired-and-missing-code-convergence.md`.
- No implementation is authorized by the confirmation alone. Await an explicit
  instruction to execute B1; when received, reread the active plan, create the
  tracked cleanup-refactor fixed-point log, and execute Slice 1 first.

## Corrected target architecture

The durable authority is:

1. canonical checked predicate/rule/superiority/claim/concept charter rows in the
   world sidecar; and
2. one typed, derived-only grounding configuration row carrying the
   commit-pinned `max_arguments` selected from `propstore.yaml`.

`WorldQuery.grounding_bundle()` derives and memoizes the one canonical
`GroundedRulesBundle` from those inputs. No Gunray argument or inspection DTO is
serialized. No second status result is persisted. Build/report/CLI/runtime
surfaces receive that same bundle or its exact backend-specific fields.

This corrects the earlier storage hypothesis. Persisting `grounded_fact` rows
and a build-status row while re-running Gunray to recover
`GroundingInspection` would create two authorities for one grounding result.
The raw grounded rows have no production reader, cannot reconstruct the ASPIC
input, and are therefore a deletion candidate rather than the home for more
metadata.

The repository config is the durable budget source because a transient CLI or
render-policy value cannot be recovered when a later `WorldQuery(repo)`
recomputes the content-addressed sidecar key. Historical sidecars must load the
config blob at the requested commit, never the cached HEAD config.

## Decision gates — confirmed 2026-07-22

The user confirmed both:

1. Q2: resolution and committed worldline materialization fail closed for
   incomplete grounding, ASPIC, PrAF, and ATMS computations; diagnostic and
   inspection surfaces may expose partial evidence only with an explicit
   backend-specific partial status.
2. Correct B1's storage line from "persist status beside grounded rows" to:
   delete the production-unread raw grounded-row projection; project the
   commit-pinned grounding budget as typed sidecar configuration; derive status,
   reason, partial evidence, and marking sections from the canonical bundle.

Recorded answer to both gates: yes.

## Cleanup-refactor control surface

Target architecture:

- `GroundedRulesBundle` is the sole grounding-result owner.
- `RepositoryConfigDocument` owns the authored per-repository argument budget.
- a derived-only charter row projects that exact budget for sidecar-only readers.
- `WorldQuery` owns the production bundle capability.
- consumers branch on the bundle's backend-specific completeness before ASPIC.

Forbidden surfaces after convergence:

- raw `grounded_fact` table and `propstore.grounding.sidecar` reader/writer API;
- persisted duplicate grounding status or Gunray DTO/codec;
- loose string grounding status;
- transient build/render budget that is absent from the sidecar cache key;
- raw-authored claims at build time paired with checked claims at runtime;
- CLI-local re-grounding;
- `GroundedRulesBundle.empty()` as a fallback for a missing production
  capability;
- incomplete grounding entering ASPIC projection or a committed worldline.

Required record during execution:

- create a tracked fixed-point log under `plans/` before the first production
  edit; record each disposition, search/runtime gate, commit, and next slice.
- keep this `notes-*.md` handoff uncommitted.

## Surface classifications and dispositions

- `GroundedRulesBundle.status: str`
  - Classification: valid capability with wrong representation.
  - Disposition: rewrite at its existing owner to a grounding-specific enum;
    add exact `max_arguments` and Gunray candidate-count evidence. Do not reuse
    Propstore's unrelated `core.anytime` sentinels.
- `build_grounded_bundle()` dropping `max_arguments`
  - Classification: already-owned capability using an incomplete owner
    interface.
  - Disposition: extend the true grounding owner and thread the exact value.
- raw `grounded_fact` storage plus `create/populate/read_grounded_facts`
  - Classification: IO-boundary carrier whose tests pin a boundary but whose
    capability has no production reader and cannot supply the ASPIC-required
    `GroundingInspection`.
  - Disposition: delete the file/table/imports/tests first; do not recreate it
    under another name. Replace its intended production capability with direct
    derivation of the typed bundle from canonical sidecar charters.
- `derived_build._load_grounding_repo()`
  - Classification: wrong one-line caller wrapper around the existing owner.
  - Disposition: delete with the old build path.
- grounding CLI calls to `load_grounding_repo()` / `build_grounded_bundle()`
  - Classification: valid capability in the wrong caller path.
  - Disposition: rewrite the CLI to use the production `WorldQuery` bundle and
    render only; no CLI-owned grounding workflow.
- `GroundingBundleStore`
  - Classification: valid optional structural capability used by alternate
    stores/test doubles.
  - Disposition: keep; give it the missing production implementer. Do not widen
    the umbrella `WorldStore` protocol.
- fragility's `else GroundedRulesBundle.empty()`
  - Classification: wrong caller that hides an absent/incomplete capability.
  - Disposition: delete the fallback; expose explicit grounding completeness on
    the diagnostic report when grounding/bridge analysis is requested.
- `BuildDiagnostic`
  - Classification: already-owned compiler/quarantine diagnostic family.
  - Disposition: keep unchanged; deterministic grounding configuration is not a
    diagnostic.
- `RenderPolicy`
  - Classification: render-time policy, not build configuration.
  - Disposition: keep unchanged.
- production-empty `ConceptRelations.relationships`
  - Classification: valid capability with no canonical relation owner.
  - Disposition: explicitly exclude from B1 and record as a separate gap. Do not
    invent a concept-relation family while implementing completeness.

## Ordered executable draft

### Slice 1 - Typed, commit-pinned budget and bundle evidence

1. Verify branch and tracked state; create the tracked fixed-point log.
2. Make `RepositoryConfigDocument` the typed return of `Repository.config`
   instead of erasing it to a dict; add optional positive
   `grounding_max_arguments`.
3. Add the narrow commit-aware repository config read needed by
   `materialize_world_sidecar(commit=...)`; keep HEAD access as the property.
4. Replace loose bundle status with a grounding-specific enum and add the exact
   selected maximum plus Gunray's `partial_count` under a name that says it is a
   candidate count, not necessarily `len(partial_arguments)`.
5. Thread `max_arguments` through `build_grounded_bundle()` into `ground()` and
   preserve exception reason, partial arguments, inspection, and candidate
   count.
6. Run focused repository/config/grounder/loading tests, search gates, Pyright,
   then commit the kept slice before proceeding.

### Slice 2 - Delete the duplicate storage result; project canonical inputs

1. Delete `propstore/grounding/sidecar.py`, its derived-build imports/calls, and
   raw-table contract tests before adding replacement code.
2. Classify every deletion failure using the required caller categories. Do not
   restore a table/helper/reader to satisfy an import or test.
3. Add one derived-only charter document for the selected grounding build
   configuration, and add it to the computed-family projection set. It carries
   configuration only, never status, sections, arguments, or inspection.
4. Resolve config from the same requested commit for both sidecar hash and
   builder; hash only the grounding budget field (plus existing inputs).
5. Bump `WORLD_SIDECAR_SCHEMA_VERSION` because the sidecar shape changes.
6. Add the typed sidecar load boundary that gathers predicates, rules,
   superiorities, checked claims, concepts, and grounding config directly as
   canonical documents. It must not return loose rows/dicts.
7. Prove a built sidecar and a derived-store-only session produce the same full
   bundle from claim-derived facts; explicitly do not use concept-relation facts
   as evidence.
8. Run focused sidecar/cache/schema tests, deletion search gates, import-linter,
   Pyright, then commit.

### Slice 3 - Production WorldQuery, build report, and inspection CLI

1. Implement and per-instance memoize `WorldQuery.grounding_bundle()` using the
   typed sidecar load boundary. Both repo-backed and derived-store-only
   constructors must work.
2. Carry the canonical bundle on `RepositoryBuildReport` rather than inventing a
   parallel build-status DTO. The build CLI renders exact status, selected
   budget, reason, and partial candidate/argument counts.
3. Rewrite `pks grounding status/show/query/arguments` to inspect the
   `WorldQuery` bundle. On incomplete grounding, `query` must not render an atom
   as absent; every command labels the partial status before showing evidence.
4. Delete the CLI-local repository load/re-ground path; do not keep both paths.
5. Prove repo-backed and handle-only `WorldQuery` return a complete bundle under
   the default and a budget-exceeded bundle under a committed tiny config.
6. Run focused WorldQuery/build/grounding-CLI tests, search gates, Pyright, then
   commit.

### Slice 4 - Fail-closed ASPIC consumers and honest diagnostics

1. In ASPIC resolution, inspect the bundle before projection. An incomplete
   bundle produces no winner and leaves `ResolvedResult` conflicted with the
   exact grounding reason.
2. In ASPIC worldline capture, do not project partial grounding. Return an ASPIC
   argumentation state explicitly marked `grounding_budget_exceeded`.
3. In `materialize_worldline()`, detect that exact incomplete ASPIC state and
   raise the existing app validation failure before assigning/saving results.
   Diagnostic `run_worldline()` remains allowed to return the explicit state.
4. Delete fragility's empty-bundle fallback. When grounding/bridge diagnostics
   are requested, require the capability and carry explicit grounding status and
   reason on `FragilityReport`; never rank an incomplete bundle as a complete
   empty result.
5. Prove the same tiny-budget sidecar is: visible as partial in diagnostics,
   refused by ASPIC resolution, refused without a worldline commit, and never
   reported as complete by fragility.
6. Run focused resolution/worldline/fragility/CLI tests, search gates,
   import-linter, Pyright, then commit.

## Search gates

- `rg -n "create_grounded_fact_table|populate_grounded_facts|read_grounded_facts|grounded_fact" propstore tests`
  must be zero.
- `rg -n "def _load_grounding_repo" propstore` must be zero.
- `rg -n "build_grounded_bundle\\(" propstore/cli` must be zero.
- `rg -n "else GroundedRulesBundle.empty" propstore` must be zero.
- `rg -n "status: str = \\"complete\\"" propstore/grounding` must be zero.
- `rg -n "def grounding_bundle" propstore/world/model.py` must find the one
  production implementation.

## Runtime gates

Per-slice tests use the logged wrapper. The final focused command is:

`powershell -File scripts/run_logged_pytest.ps1 tests/test_repository.py tests/test_uri.py tests/test_uri_authority_validation.py tests/test_grounder_budget_exceeded.py tests/test_grounding_loading.py tests/test_derived_build.py tests/test_world_sidecar_grounded.py tests/test_world_query.py tests/test_resolution.py tests/test_app_worldlines.py tests/test_worldline_hash_excludes_transient_errors.py tests/test_fragility.py tests/test_cli_phase10_advanced.py tests/test_cli_compiler_rendering.py -q`

Then run, in order:

1. `uv run pyright propstore`
2. `uv run lint-imports`
3. `uv run ruff check .`
4. `uv run ruff format --check .`
5. `powershell -File scripts/run_logged_pytest.ps1 -q`

After every substantial passing test run and the full-suite run, reread the
active plan and continue to the next unchecked item. Final completion also
requires zero forbidden-surface hits, four committed slices, and every B1 item
checked or explicitly amended by the user.

## Verified baseline

- Focused logged baseline: 110 passed in 13.90s.
- Log: `logs/test-runs/pytest-20260721-232639.log`.
- No production/test source was changed during research.

## Exact-plan checkpoint — 2026-07-22

### Findings

- Quire already exposes the needed commit-aware read as
  `GitStore.read_file(path, commit=...)`; no tree adapter is needed for
  historical `propstore.yaml` configuration.
- `Repository.config` currently erases `RepositoryConfigDocument` into
  `dict[str, TaggingAuthority]`. The exact correction can remain at the
  repository owner: `config_at(commit)` decodes the document and the cached
  `config` property calls `config_at(None)`; `uri_authority` parses the typed
  document field.
- Derived-only sidecar families are ordinary charter classes explicitly added
  to `_CHARTER_MODELS` and `_COMPUTED_FAMILIES`. `BuildDiagnostic`,
  `ConflictProjection`, and `CalibrationCount` confirm that a grounding config
  row should be its own no-`semantic`, no-FK charter rather than metadata or a
  diagnostic.
- The typed sidecar session is `quire.sqlalchemy_store.DerivedSession`, and
  `propstore.world.queries` is the existing owner for charter-to-document
  selectors. `WorldQuery` already owns and holds that session.
- Gunray's `EnumerationExceeded.partial_count` defaults to the number of
  partial arguments, but head-only binding exhaustion sets it to the number of
  candidate bindings. The Propstore field therefore must be named
  `partial_candidate_count`, not argument count.
- `RepositoryBuildReport` can carry the canonical
  `GroundedRulesBundle` directly; `FragilityReport` currently has no grounding
  completeness fields and fragility currently substitutes an empty bundle for
  a missing capability.

### Observations

- A selector collection plus one typed `GroundingRepo` assembly function at
  the world-query boundary is sufficient for sidecar-only readers; a generic
  adapter or serialized Gunray DTO would duplicate existing owners.
- The registry contract version and `WORLD_SIDECAR_SCHEMA_VERSION` must both
  change when the grounding configuration charter is added.
- `GroundingBundleStore` already exists as the optional structural capability;
  no new interface is warranted.

### State

- Planning research remains read-only with respect to production and tests.
- The active tracked plan is still modified but uncommitted.
- This `notes-*.md` checkpoint remains uncommitted as required.
- Ward and subagents were not used.

### Blocker

- No user decision is currently missing. The remaining planning work is to
  settle exact symbol names, report fields, failure behavior, and test/file
  gates from current code, then amend the active plan only.

### Next action

- Inspect the exact Gunray exception contract, worldline result/materialization
  types, CLI rendering, and existing test owners; choose one literal name and
  signature for every remaining item; amend and mechanically validate the
  active plan without implementing it.

## Exact-plan checkpoint 2 — 2026-07-22

### Findings

- All formerly unnamed B1 artifacts now have exact plan contracts:
  `plans/grounding-completeness-fixed-point-log.md`,
  `Repository.config_at()`, `GroundingStatus`,
  `GroundingBuildConfiguration`,
  `load_grounded_bundle_from_sidecar()`, the canonical build-report bundle,
  and the two grounding fields on `FragilityReport`.
- The derived charter is fixed as family
  `grounding_build_configuration`, singleton id `grounding`, with only
  `max_arguments`; status and Gunray result objects are not persisted.
- The loader is fixed as one grounding-owned function accepting Quire's
  `DerivedSession`. Both `WorldQuery` and `build_repository()` use it; no new
  interface and no compiler-to-`WorldQuery` dependency are introduced.
- The worldline incomplete state uses the existing argumentation result with
  exact status `grounding_budget_exceeded` plus a new `reason` field, and the
  app materialization boundary rejects it before assignment or save.
- The obsolete `GroundingSurfaceState` classifier is dead after the production
  CLI cutover and is explicitly deleted. Invalid rules-without-predicates
  remains an owner error, mapped to a nonzero CLI result.
- Each of the four slices now has an exact logged test command, search/type
  gates, fixed-point-log update, and commit subject.

### Observations

- Every existing path named by the focused gates exists.
- `uv run pks contract-manifest --help` confirms the planned exact
  `uv run pks contract-manifest --write` command and options are current.
- `git diff --check` passes for the plan amendment.

### State

- Only `plans/unwired-and-missing-code-convergence.md` is tracked-modified.
- `pyghidra_mcp_projects/` remains unrelated and untouched.
- Production and test files remain unchanged; no implementation or commits
  occurred.
- The active plan contains the settled execution contract and exact slice
  commands.

### Blocker

- No external decision is missing. The final audit must only remove any
  internal contradiction between the detailed B1 contract and the later B2
  wording before the plan can be called execution-ready.

### Next action

- Reconcile the later B2 grounding-handoff checkbox with the now-exact B1 Slice
  4 ownership, rerun plan-only diff/status checks, and report the plan ready for
  explicit execution authorization.

## Execution checkpoint — B1 Slice 1

### Findings

- `RepositoryConfigDocument` now owns both `uri_authority` and positive optional
  `grounding_max_arguments`; `Repository.config_at(commit)` reads the exact Git
  revision and the cached `config` property returns the typed document.
- `GroundedRulesBundle.status` is now `GroundingStatus`; the bundle preserves
  `max_arguments` and Gunray's independent `partial_candidate_count`.
- `build_grounded_bundle()` now passes the selected limit to both `ground()` and
  the typed empty bundle.

### Observations

- Exact Slice 1 logged test gate: 44 passed in 8.53s.
- Log: `logs/test-runs/pytest-20260722-121756.log`.
- Loose grounding status construction searches and the old config-dict access
  searches are zero-hit.
- `uv run pyright propstore`: 0 errors, 0 warnings, 0 informations.

### State

- B1 Slice 1 implementation and focused tests are complete but not yet
  committed.
- The tracked fixed-point log exists at the exact planned path.
- No Slice 2 deletion or replacement work has begun.
- The ignored planning note remains uncommitted; unrelated
  `pyghidra_mcp_projects/` remains untouched.

### Blocker

- None.

### Next action

- Update the tracked fixed-point log with Slice 1 gate evidence, audit/stage only
  the intended Slice 1 paths, commit exactly
  `refactor(grounding): type budget completeness evidence`, reread the plan, and
  begin Slice 2 deletion-first.

## Execution checkpoint — B1 Slice 2 in progress

### Findings

- Slice 1 was committed as `cdc0085f` with the exact planned subject.
- `propstore/grounding/sidecar.py` and
  `tests/test_sidecar_grounded_facts.py` are deleted.
- The derived-build import/call path and `_load_grounding_repo()` wrapper that
  existed only for raw result storage are deleted; Pyright remained clean after
  deletion.
- `GroundingBuildConfiguration` now exists as the sole derived-only config
  charter and is registered/computed with schema version 2.
- The sidecar hash now includes only the selected grounding maximum, resolved
  from the requested commit.
- `load_grounded_bundle_from_sidecar(DerivedSession)` is the sole new typed
  loader and reconstructs the full runtime bundle from canonical charter rows.

### Observations

- After production deletion, remaining `grounded_fact` references were only the
  two old test surfaces identified by the plan.
- `tests/test_world_sidecar_grounded.py` has been rewritten to compare the full
  sidecar-only bundle against the repository grounding owner rather than raw
  SQL rows.

### State

- Slice 2 implementation is in progress and uncommitted.
- Contract manifest regeneration, focused Slice 2 tests, deletion searches,
  import-linter, and Pyright remain to run.
- Unrelated `pyghidra_mcp_projects/` remains untouched.

### Blocker

- None.

### Next action

- Rewrite the remaining derived-build raw-table assertion into charter/config
  and cache tests, add registry/manifest assertions, format, regenerate the
  manifest, run the exact Slice 2 gates, update the tracked ledger, and commit.
## 2026-07-22 Slice 3 start checkpoint

- Current state: Slice 1 is committed as `cdc0085f`; Slice 2 is committed as
  `75fa7895`. Tracked state was clean on `master` before Slice 3; unrelated
  untracked `pyghidra_mcp_projects/` remains untouched.
- Finding: `WorldQuery` opens one typed `DerivedSession` but does not yet own or
  memoize a grounding bundle. The exact owner cutover is to call
  `load_grounded_bundle_from_sidecar(self._session)` from the one production
  `grounding_bundle()` method for both repository and handle-only construction.
- Finding: `RepositoryBuildReport` does not yet carry the canonical bundle, and
  `build_repository()` currently stops after sidecar materialization. It must
  open that sidecar with `readonly_session(..., build_world_sidecar_schema())`
  and load the same bundle without importing `WorldQuery` or changing the
  materialization return contract.
- Finding: `propstore/cli/grounding_cmds.py` still owns the forbidden authored
  repository load/re-ground path and uses the obsolete
  `GroundingSurfaceState`. The broken edge is classified as valid capability in
  the wrong caller path; disposition is to rewrite each command to inspect
  `open_app_world_model(repo).grounding_bundle()`. The state type/function and
  their old tests are dead/test surface and must be deleted.
- Blocker: none. No source edit for Slice 3 has been made yet.
- Next action: inspect the focused WorldQuery/build/CLI tests, then implement the
  exact Slice 3 owner cutover and delete the old CLI/state surfaces before
  running the named Slice 3 gate.

## 2026-07-22 Slice 3 focused-gate checkpoint

- Current state: the Slice 3 production cutover is implemented but not yet
  committed. `WorldQuery.grounding_bundle()` uses and memoizes the typed sidecar
  loader for both construction modes; `RepositoryBuildReport` carries that same
  bundle; build and grounding CLI rendering expose completeness evidence.
- Deletion state: CLI-local `load_grounding_repo()` / `build_grounded_bundle()`
  calls are gone, and `GroundingSurfaceState` / `grounding_surface_state()` plus
  their obsolete tests are deleted.
- Evidence: the exact focused command passed 65 tests in 10.53s. Log:
  `logs/test-runs/pytest-20260722-123311.log`.
- Observation: tiny committed `grounding_max_arguments: 1` configurations now
  produce `budget_exceeded` through both repository-backed and handle-only
  `WorldQuery` readers. CLI `query` renders an incomplete status/reason and does
  not render the atom absent.
- Blocker: none.
- Next action: reread the active plan as required after the substantial passing
  run, then run the Slice 3 search gates and `uv run pyright propstore`, update
  the tracked fixed-point log, and commit the exact Slice 3 commit if all gates
  pass.

## 2026-07-22 Slice 4 start checkpoint

- Current state: Slice 3 is committed as `ea1597af feat(grounding): wire
  production bundle inspection`; tracked state was clean before Slice 4 and the
  unrelated untracked directory remains untouched.
- Finding: ASPIC resolution currently calls `build_aspic_projection()` after
  loading the bundle without checking `GroundingStatus`. It must return no
  winner and the bundle's exact reason before projection when incomplete.
- Finding: ASPIC worldline capture likewise projects immediately. The settled
  diagnostic path is the existing `WorldlineArgumentationState` with backend
  `aspic`, status `grounding_budget_exceeded`, and the new adjacent `reason`
  field.
- Finding: `materialize_worldline()` currently assigns and saves every
  `run_worldline()` result. It must raise `WorldlineValidationError` on that
  exact status before assignment or save.
- Finding: fragility still substitutes `GroundedRulesBundle.empty()` when the
  store lacks grounding capability. That fallback must be deleted; grounding or
  bridge analysis requires `GroundingBundleStore`, and an incomplete real bundle
  records status/reason while skipping only those two collectors.
- Blocker: none. The tracked fixed-point log contains all Slice 4 edge
  classifications and dispositions; no Slice 4 source edit has been made.
- Next action: add the exact completeness guard to ASPIC resolution, then apply
  the corresponding worldline and fragility owner changes and focused tests.

## 2026-07-22 Slice 4 gate-repair checkpoint

- Current state: all Slice 4 production changes and focused proofs are present
  but uncommitted. The first gate had six failures: five tests depended on the
  now-deleted implicit empty grounding capability, and one asserted an unrelated
  worldline value-status spelling. Those broken test edges were classified and
  rewritten without restoring the fallback.
- Evidence: the second exact focused run passed 93 of 94 tests. Log:
  `logs/test-runs/pytest-20260722-124155.log`.
- Remaining failure: production correctly raises
  `WorldlineValidationError("argument enumeration budget exceeded: 1 candidates produced of 1 allowed")`.
  The test regex incorrectly expected `argument enumeration exceeded`, omitting
  the actual owner word `budget`.
- Observation: the same committed tiny-budget sidecar now yields an incomplete
  `ResolvedResult`, diagnostic ASPIC worldline state, and fragility report with
  the same exact reason; materialization raises before a commit.
- Blocker: none.
- Next action: correct only the stale test regex to the exact owner wording, then
  rerun the complete named Slice 4 gate.

## 2026-07-22 B1 final-gate checkpoint

- Current state: all four B1 slices are committed. Slice 4 is `4362e3e1`; the
  final combined focused gate passed 227 tests in 15.11s. Log:
  `logs/test-runs/pytest-20260722-124416.log`.
- Pass: Pyright has 0 errors; import-linter keeps all 3 contracts.
- Formatting finding: `uv run ruff format --check .` identified exactly 10
  B1-touched files with mixed/newline formatting from the applied edits.
  `uv run ruff format .` reformatted those 10 and left 633 unchanged; the
  repository-wide format check now passes all 643 files.
- Ruff-check finding: `uv run ruff check .` still fails with 72 findings in
  unrelated pre-existing review scripts, utility scripts, older revision tests,
  and a workstream note. None of the reported paths is a B1-touched file.
- Blocker: the plan's repository-wide Ruff-check gate cannot become green
  without broadening beyond B1 into unrelated existing lint debt. No such files
  have been changed.
- Next action: rerun the combined focused gate against the mechanical formatting
  diff, commit that verified formatting slice, then run the plan's full logged
  suite. After all in-scope gates are exhausted, request exact direction on the
  unrelated Ruff-check gate if it remains the sole blocker.

## 2026-07-22 Repository-wide Ruff cleanup checkpoint

- Authority: the user explicitly directed `let's resolve ruff first`, making
  the repository-wide Ruff gate the active accountable slice before the B1
  final completion audit resumes.
- Starting ledger: branch `master`; tracked worktree clean at `15d8acb9`; only
  unrelated untracked `pyghidra_mcp_projects/` present and untouched.
- Reproduced finding: `uv run ruff check .` reported 72 errors. Ruff's safe
  `--fix` pass repaired 61 mechanical unused-import, unused-variable, and
  unnecessary-f-string findings across 14 files. The resulting diff is 5
  insertions and 71 deletions; `git diff --check` passes.
- Remaining state: 11 errors are unresolved: four `normalize` references in
  `scripts/check_workstream_order.py`; `_write_json` and
  `_world_behavior_comparison` references in
  `scripts/compare_sqlalchemy_charter_parity.py`; `_role_for_field` and
  `build_rows` references in `scripts/generate_typed_metadata_owner_ledger.py`;
  `main` in `scripts/generate_ws_k2_corpus.py`; and unused `alias_targets` in
  `scripts/seed_tags.py`.
- Observation: most undefined symbols were removed by commit `61d8783a`
  (`Delete payload-containing functions`) while their callers remained. They
  must not be restored merely to make imports or Ruff pass; each broken
  dependency edge needs its intended capability and current usefulness checked.
- Blocker: none yet. The semantic disposition of each undefined edge is still
  being established from current code and history.
- Next action: inspect the exact deletion patches and current script purposes,
  classify each edge as dead script/caller or valid capability needing a typed
  rewrite, then make only the justified repairs and rerun Ruff.

## 2026-07-22 Ruff cleanup ownership gate

Target architecture:
- Live repository gates contain no undefined names and use their actual current
  owners. Historical one-shot generators and parity adapters whose owner APIs
  were deleted do not remain as broken executable scripts.

Forbidden surfaces:
- Restored payload helpers, loose semantic payload builders, missing-symbol
  shims, and scripts that advertise execution through already-deleted owners.

Slice boundary:
- The five scripts containing the 11 post-autofix Ruff findings, plus the
  already-applied safe Ruff edits elsewhere.

Dispositions:
- `scripts/check_workstream_order.py` / deleted `normalize` edge: valid local
  checker capability. Rewrite the legacy caller around locally paired raw and
  normalized titles; do not restore the deleted helper.
- `scripts/compare_sqlalchemy_charter_parity.py`: dead historical harness.
  Its behavior extractor and tests were deleted in `61d8783a`; its current
  builder still imports the nonexistent `write_repository_world_store`; the
  remaining workstream record says its Phase 14 gate was completed in May.
  Delete the whole broken script rather than restoring `_write_json`, behavior
  payload extraction, or compatibility transforms.
- `scripts/generate_typed_metadata_owner_ledger.py`: dead one-shot scaffold.
  There are no current callers; its loose-dict row builder and role classifier
  were deliberately deleted, while the durable generated ledger already
  exists. Delete the remaining file rather than recreate those surfaces.
- `scripts/generate_ws_k2_corpus.py`: dead one-shot scaffold. There are no
  current callers; its raw YAML payload writer was deliberately deleted and
  only constants plus an undefined `main` remain. Delete the remaining file.
- `scripts/seed_tags.py` / `alias_targets`: live IO utility with an unused local
  value. Delete only the unused assignment; keep the owner behavior unchanged.

Search gates:
- `rg` for the three deleted script paths outside historical request reports.
- `rg` for the deleted undefined names in remaining Python files.
- `uv run ruff check .`.

Runtime gates:
- Run the current split-workstream order command documented by the workstream.
- Run an isolated legacy checker fixture through the script without writing a
  reusable helper.
- Run `uv run ruff format --check .`, the focused affected tests, and the full
  B1 gates after committing this cleanup slice.

Current blocker:
- None.

Next action:
- Apply the recorded deletions and two narrow caller rewrites, then run the
  search and Ruff gates before any commit.

## 2026-07-22 Ruff cleanup verification

- Applied dispositions: deleted the three recorded dead scripts; rewrote the
  live legacy workstream checker with local raw/normalized title pairs; removed
  the unused tag-seeder assignment; retained Ruff's 61 safe mechanical fixes.
- Search pass: no remaining Python hit for `normalize(`, `_write_json`,
  `_world_behavior_comparison`, `_role_for_field`, `build_rows`, or
  `generate_ws_k2_corpus`; no Python/TOML/YAML caller references any deleted
  script path.
- Gate pass: `uv run ruff check .` reports `All checks passed!`.
- Gate pass: `uv run ruff format --check .` reports all 640 remaining Python
  files formatted.
- Runtime pass: the documented split-workstream checker command and an existing
  legacy `Dependency Order` workstream both return `workstream order ok`.
- Focused pass: 63 affected revision/worldline tests passed in 12.05s. Log:
  `logs/test-runs/ruff-cleanup-20260722-130910.log`.
- Diff state: 18 tracked paths, 19 insertions and 1,417 deletions;
  `git diff --check` passes. The unrelated untracked
  `pyghidra_mcp_projects/` remains untouched.
- Blocker: none.
- Next action: commit this verified Ruff cleanup as one accountable slice, then
  resume the exact B1 final focused, type, import, Ruff, format, and full-suite
  gate sequence from the controlling plan.

Ruff cleanup commit:
- `7cd565a4 chore: resolve repository-wide Ruff findings`
- Next slice: B1 final completion audit only; no further Ruff-cleanup source
  work remains unless a named final gate exposes new breakage.

## 2026-07-22 B1 final completion audit

- Exact combined focused gate: 227 passed in 20.33s. Log:
  `logs/test-runs/pytest-20260722-131104.log`.
- Package typing: `uv run pyright propstore` reports 0 errors.
- Imports: `uv run lint-imports` keeps all 3 contracts.
- Repository lint: `uv run ruff check .` passes.
- Repository formatting: `uv run ruff format --check .` reports all 640
  remaining Python files formatted.
- Exact full logged suite: 1820 passed, 1 skipped in 94.97s. Log:
  `logs/test-runs/pytest-20260722-131215.log`.
- Exact B1 searches: all seven forbidden-surface searches return zero hits;
  exactly one `WorldQuery.grounding_bundle()` and one
  `load_grounded_bundle_from_sidecar()` implementation remain.
- Durable reconciliation: the controlling plan and grounding fixed-point log
  now state that no B1 completion gate remains unchecked.
- Worktree: no tracked source changes remain after `7cd565a4`; the two current
  tracked edits are documentation-only final-audit reconciliation. Unrelated
  untracked `pyghidra_mcp_projects/` remains untouched.
- Blocker: none.
- Next action: commit the two tracked plan/log reconciliations, verify the final
  ledger, and mark the B1 objective complete.
