# Unwired and Missing Code Convergence Plan

## Objective

Converge the code that is substantially implemented but unreachable, complete
the genuinely missing representation and result-status seams, and remove stale
claims of missing functionality without creating parallel owners.

This plan is based on current production code and tests, recorded in:

- `docs/reports/relation-calibration-extraction.md`
- `docs/reports/verification-views-owners.md`
- `docs/reports/values-praf-stale-gaps.md`

The reports are research evidence. This file is the execution control surface.

## Non-negotiable boundaries

- Use existing `WorldQuery`/world read APIs for similarity and semantic reads;
  do not create another embedding store or relation-store adapter hierarchy.
- Use existing stance, predicate, and rule proposal/promotion owners; do not add
  another proposal writer or write classifier output directly to canonical
  stances/rules/predicates.
- Keep source-branch state in the source subsystem and canonical semantic state
  in canonical families/micropublications.
- Do not productionize the test-only `FormRepository`, `ContextRepository`, or
  dead `RuleRepository`; production storage is `Repository.families`.
- Do not add direct canonical rule mutation or direct source-derived
  micropublication mutation. Their existing proposal/finalize/promotion paths
  remain authoritative.
- Keep direct scalar values distinct from numeric derivation. Category/boolean
  values must not leak into dimensional algebra, sensitivity, parameterization,
  or numeric conflict math.
- Treat grounding, ASPIC, PrAF, and ATMS completeness as separate owner-specific
  contracts. Do not invent a generic status adapter before the owner results are
  correct.
- All Python tests run through `scripts/run_logged_pytest.ps1`; the package type
  gate is `uv run pyright propstore`.
- For each deletion-first slice, load and follow `protocols:cleanup-refactor`
  before mutation, classify every broken dependency edge, and commit or fully
  revert the slice before starting the next source slice.

## Decisions required before affected phases

These are real semantic authorities missing from code. They are not safe to infer
during implementation.

### Q1. Canonical claim scalar

Decision — 2026-07-18:

- Propstore's canonical scalar API is `str | bool | int | float`, with `None`
  representing absence. Integers are signed 64-bit values. Floats are finite
  IEEE-754 binary64 values. Boolean remains distinct from integer, and integer is
  never silently converted to float.
- Propstore owns those scalar semantics. Quire owns the generic charter-derived
  storage mechanism: each present value is MessagePack-encoded into one BLOB
  column, while absence is SQL `NULL`. Encoded MessagePack `nil` is not a second
  spelling of absence.
- The MessagePack bytes are derived sidecar projection state. They are not input
  to artifact identity, content hashes, or canonical Git document serialization.
  Domain and authoring APIs continue to expose native scalar values, not a
  wrapper, payload, or codec DTO.
- No discriminator-plus-typed-column representation, Propstore-local codec
  adapter, or parallel scalar storage path is permitted.
- The standalone Claim LinkML source and its generated/package JSON schemas are
  retired as supported contracts. This decision is specific to the Claim schema;
  it does not automatically retire unrelated schema resources.
- CBOR is reserved for a future durable external binary wire contract if one is
  explicitly required. Protobuf and ASN.1 are rejected for this boundary because
  their schema/code-generation and encoding-profile ownership is disproportionate
  to one derived scalar column.

### Q2. Incomplete reasoning policy

Decision confirmed 2026-07-22: resolution and committed worldline
materialization fail closed on incomplete computation for grounding, ASPIC,
PrAF, and ATMS. Diagnostic and inspection surfaces may display partial evidence
only when the backend-specific partial status is explicit. No partial or failed
result may be rendered, persisted, or used to select a winner as though it were
complete.

### Q3. Calibration authority

No persisted human-judgment authority currently exists.

Decision required:

- the identity and storage owner for labeled judgments;
- whether category priors are measured from that corpus or supplied as explicit
  provenance-bearing policy;
- version dimensions for model, prompt, pass, and category.

No production calibration-count producer may be built before this is decided.

### Q4. Durable LLM evidence

Decision required: whether stance/predicate/rule proposals retain raw prompts and
responses, only hashes/call ids plus model metadata, or a separately retained
evidence artifact. This affects privacy, reproducibility, and proposal schemas.

### Q5. View semantics

Decision required before the named optional surfaces:

- what makes a conflict “notable”;
- which provenance aggregates belong on the repository overview;
- source focus identity (`SourceRef.name`, canonical source URI, or explicit
  resolution of both) and whether a source neighborhood shows branch-local,
  canonical, or two-part state;
- whether form/context/lifting-rule mutation is allowed after initialization and
  its deletion/reference/proposal policy;
- whether micropublication lift means all claims, principal claim, or bundle-node
  support.

## Phase 0 — Correct invalid premises before feature work

Purpose: ensure later work is not justified by stale skips or descriptions.

- [x] Delete the obsolete skipped ATMS resolution placeholder; add a real test
  only if a specific uncovered behavior is identified.
- [x] Correct ASPIC module prose that says `build_aspic_projection` is absent.
- [x] Correct relation prose claiming reverse distances survive classification.
- [x] Correct grounding/fragility prose claiming non-empty grounding authoring is
  absent.
- [x] Replace or delete the three empty fragility placeholder test classes only
  after driving the existing collectors with a real non-empty production bundle.
- [x] Remove stale “embedding deferred” labels while retaining genuine optional
  `sqlite_vec` dependency skips.
- [x] Rewrite the PrAF/grounding skipped-test description so it names the actual
  missing propagation seam rather than claiming low-level budget capture is absent.

Gate:

- The changed tests either execute meaningful production paths or are deleted;
  no skip remains whose stated prerequisite already exists.
- Focused logged tests for ATMS resolution, ASPIC projection, fragility, grounding,
  and embeddings pass.
- `uv run pyright propstore` passes.

## Workstream A — Canonical scalar value convergence

This is the foundational representation change. Complete it before the categorical
ATMS test or any consumer-specific workaround.

### A1. Prove and encode the scalar contract

- [x] Resolve Q1.
- [x] Add source-to-world round-trip tests for string category, boolean, integer,
  float, and absent value.
- [x] Change `SourceClaimDocument.value` and canonical `Claim.value` together.
- [x] Make the Quire charter-derived SQL representation preserve scalar type.
- [x] Update source decode/CLI/import contracts and promotion without introducing
  a second claim representation.
- [x] Regenerate supported external schemas or explicitly retire them, per Q1.

Required vertical gate:

`source decode -> source save/load -> promotion -> canonical save/load -> sidecar -> WorldQuery`

must preserve both scalar value and runtime type for all selected scalar classes.

### A2. Form-aware authoring validation

- [x] Numeric forms retain current bounds, unit, uncertainty, and confidence rules.
- [x] Closed category forms reject values outside their authored vocabulary.
- [x] Extensible category forms accept new category values.
- [x] Boolean forms accept booleans and reject textual lookalikes such as
  `"true"`.
- [x] Category/boolean values never enter numeric bounds or dimensional checks.

### A3. Direct runtime consumers

- [x] Preserve scalar identity in direct resolution and presentation; remove bool
  stringification and unintended int-to-float conversion from direct-value paths.
- [x] Keep equation/parameterization, sensitivity, dimensional comparison,
  parameterization conflicts, and assignment-selection explicitly numeric.
- [x] Preserve typed grounding constants and worldline results.
- [x] Drive a real authored categorical provider through the bound world and
  unskip the existing ATMS incompatibility test, reusing the already-implemented
  visible rejection node.

Workstream A gate:

- Focused source, charter, sidecar, world-value, worldline, grounding, and ATMS
  tests pass through the logged wrapper.
- Numeric derivation behavior is unchanged for numeric inputs and explicitly
  rejects nonnumeric inputs.
- `uv run pyright propstore` passes.

Completion evidence — 2026-07-21:

- Quire commit `9f9d9ff` provides the generic charter-derived MessagePack storage
  codec; Propstore pins that exact revision in `pyproject.toml` and `uv.lock`.
- The required source-to-world vertical path preserves string, bool, int, float,
  and absence with exact runtime types. The final focused logged gate passed 141
  tests: `logs/test-runs/canonical-scalar-final-focused-20260721-190836.log`.
- The final committed-HEAD full logged suite passed 1812 tests with one skip:
  `logs/test-runs/canonical-scalar-final-head-20260721-191841.log`. The skip is
  `test_praf_argument_enumeration_budget_surfaces_partial_result`, which belongs
  to the still-unchecked Workstream B PrAF completeness seam, not Workstream A.
- Package Pyright reports 0 errors; all three import-linter contracts are kept;
  Ruff reports all 644 Python files formatted. Deleted-surface, duplicate-alias,
  retired-schema/dependency, and categorical-ATMS placeholder searches are at
  zero matches.

## Workstream B — Reasoning completeness propagation

Q2 is resolved above. Keep each backend isolated from the others; within B1,
execute the four atomic slices below in order and commit each kept slice before
starting the next.

### B1. Grounding

- [x] Make `GroundedRulesBundle` the sole grounding-result owner. Its typed,
  backend-specific result carries status, the selected `max_arguments`, partial
  arguments and inspection, Gunray's candidate count, and the budget reason.
- [x] Make `grounding_max_arguments` positive optional repository configuration
  in `propstore.yaml`; read it from the requested commit for historical builds,
  include it in the world-sidecar content hash, and project that exact value as
  a typed derived-only grounding-configuration charter for sidecar-only readers.
- [x] Delete the production-unread raw `grounded_fact` table and the
  `propstore.grounding.sidecar` create/populate/read API. Do not replace them
  with another result table, status table, Gunray codec/DTO, alias, wrapper, or
  fallback reader.
- [x] Derive and memoize the full bundle in production
  `WorldQuery.grounding_bundle()` from the canonical checked predicate, rule,
  superiority, claim, concept, and grounding-configuration sidecar documents.
  Repo-backed and derived-store-only readers must use the same path.
- [x] Preserve the canonical bundle through build reports and grounding CLI
  inspection. CLI query output must not call an atom absent when grounding is
  incomplete.
- [x] Prevent a budget-exceeded bundle from entering ASPIC projection,
  resolution, or committed worldline materialization as a complete theory.
- [x] Delete fragility's missing-capability substitution of
  `GroundedRulesBundle.empty()` and report grounding incompleteness explicitly
  on that diagnostic surface.

B1 completion audit — 2026-07-22:

- All seven implementation requirements and all four ordered semantic commits
  are complete. The combined focused suite passes 227 tests, the full suite
  passes 1820 with one skip, all B1 searches pass, Pyright is clean, all import
  contracts are kept, and repository-wide Ruff and formatting checks pass.
- The user-authorized repository-wide Ruff cleanup is committed as `7cd565a4`.
  After that cleanup, the exact B1 final focused gate passes 227 tests, the full
  logged suite passes 1820 with one skip, `uv run pyright propstore` reports no
  errors, all three import contracts are kept, all nine B1 search gates match
  their required outcomes, `uv run ruff check .` passes, and
  `uv run ruff format --check .` reports all 640 remaining Python files
  formatted. No B1 completion gate remains unchecked.

Confirmed storage correction:

- The earlier instruction to persist status beside grounded rows is superseded.
  The raw rows have no production reader and cannot reconstruct the
  `gunray.GroundingInspection` ASPIC requires. Persisting them and then
  re-running Gunray would create two authorities for one result.
- The durable authority is the canonical checked sidecar documents plus the
  commit-pinned typed grounding configuration. The complete runtime bundle is a
  deterministic projection of those inputs. No grounding result/status is
  stored separately.
- `RenderPolicy` is not the budget owner, and `BuildDiagnostic` is not the
  grounding-configuration owner.

Deletion-first classifications:

- `GroundedRulesBundle.status: str`: valid capability with wrong
  representation; rewrite it at the existing bundle owner to a
  grounding-specific enum.
- `build_grounded_bundle()` dropping `max_arguments`: already-owned capability
  with an incomplete owner interface; extend the owner and thread the value.
- raw `grounded_fact` storage and its create/populate/read functions:
  IO-boundary carrier with no production reader and insufficient information
  for ASPIC; delete the file/table/callers/tests first.
- `derived_build._load_grounding_repo()`: wrong one-line wrapper; delete it with
  the old build path.
- CLI-local repository load and re-grounding: valid capability in the wrong
  caller path; rewrite the CLI to inspect `WorldQuery.grounding_bundle()`.
- `GroundingSurfaceState` / `grounding_surface_state()`: dead surface after the
  CLI stops inspecting the authored repository directly; delete the type,
  function, imports, and old state tests rather than retaining an uncalled
  second classifier. An invalid rules-without-predicates repository continues
  to fail at `build_grounded_bundle()` and the CLI maps that owner failure to a
  nonzero presentation error.
- `GroundingBundleStore`: valid optional structural capability; keep it and add
  the missing production implementer without widening `WorldStore`.
- fragility's empty-bundle fallback: wrong caller hiding absent/incomplete
  capability; delete it.
- production-empty `ConceptRelations.relationships`: valid capability with no
  canonical relation owner. Record it as a separate gap and do not invent a
  concept-relation family in B1.

#### B1 exact execution contract — settled 2026-07-22

No B1 naming, ownership, signature, persistence, or failure-policy decision is
left implicit. Execute these exact contracts; if current code makes any one of
them impossible, amend this plan before editing a substitute.

Artifacts and version changes:

- Create the tracked execution record at
  `plans/grounding-completeness-fixed-point-log.md`. For every broken dependency
  edge record the deleted surface, caller, required classification, disposition,
  focused gate, kept commit, and next slice. Do not create a second log.
- Create `propstore/families/grounding.py` containing the sole derived config
  charter `GroundingBuildConfiguration`:
  `key=name=placement="grounding_build_configuration"`,
  `contract_version="2026.07.22"`,
  `identity_field="configuration_id"`, and fields
  `configuration_id: Annotated[str, charter_field(primary_key=True)]` plus
  `max_arguments: int | None = None`. The build projects exactly one row whose
  `configuration_id` is `"grounding"`.
- Add that charter to `_CHARTER_MODELS`, add
  `PropstoreFamily.GROUNDING_BUILD_CONFIGURATION =
  "grounding_build_configuration"`, and add the family name to
  `_COMPUTED_FAMILIES` so it is never scanned as authored content.
- Set `PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION` to
  `contract_version("2026.07.22")`, set the new charter contract version above,
  and bump `WORLD_SIDECAR_SCHEMA_VERSION` from `1` to `2`.
- Regenerate the checked manifest with the existing exact command
  `uv run pks contract-manifest --write`; do not hand-edit
  `propstore/_resources/contract_manifests/semantic-contracts.yaml`.

Repository configuration API:

- `RepositoryConfigDocument` has exactly
  `uri_authority: str | None = None` and
  `grounding_max_arguments: int | None = None`. Its `__post_init__` rejects zero
  and negative values with
  `ValueError("grounding_max_arguments must be positive")`.
- Add
  `Repository.config_at(self, commit: str | None = None) ->
  RepositoryConfigDocument`. It calls the existing
  `GitStore.read_file(REPOSITORY_CONFIG_PATH, commit=commit)`, returns an empty
  `RepositoryConfigDocument()` when the file is absent, and raises the same
  explicit non-git historical-read error pattern as `Repository.tree()` when a
  non-`None` commit is requested without Git.
- `Repository.config` remains a cached HEAD property but now returns
  `RepositoryConfigDocument` by calling `config_at()`. `uri_authority` reads and
  parses `self.config.uri_authority`; no dict, alias, or compatibility accessor
  remains.

Grounding result API:

- In `propstore/grounding/bundle.py`, add exactly
  `GroundingStatus(StrEnum)` with `COMPLETE = "complete"` and
  `BUDGET_EXCEEDED = "budget_exceeded"`.
- `GroundedRulesBundle` has the exact completeness fields
  `status: GroundingStatus = GroundingStatus.COMPLETE`,
  `budget_reason: str | None = None`,
  `max_arguments: int | None = None`, and
  `partial_candidate_count: int | None = None`. Keep `arguments` and
  `grounding_inspection` as Gunray-owned typed values; add no result DTO.
- `GroundedRulesBundle.empty(*, max_arguments: int | None = None)` preserves the
  selected limit even for an empty complete program.
- `ground()` records `max_arguments` on complete output. On
  `gunray.EnumerationExceeded`, it records
  `GroundingStatus.BUDGET_EXCEEDED`, `exc.reason`, `exc.max_arguments`, and
  `exc.partial_count`; `partial_candidate_count` deliberately does not claim to
  equal `len(exc.partial_arguments)` because Gunray also uses it for head-only
  binding candidates.
- `build_grounded_bundle(repo, *, commit=None, return_arguments=False,
  max_arguments: int | None = None)` passes the limit to `ground()` and to
  `GroundedRulesBundle.empty()`. The sidecar loader below always requests
  `return_arguments=True`, so every production bundle is inspection- and
  arguments-complete when its status is complete.

Sidecar hash, projection, and typed load boundary:

- Extend both `world_sidecar_hash_inputs()` and `world_sidecar_hash()` with the
  keyword `grounding_max_arguments: int | None = None`. Add exactly
  `"grounding_config": {"max_arguments": grounding_max_arguments}` to the
  inspectable inputs and the hashed `extra_inputs`.
- `materialize_world_sidecar()` resolves
  `repo.config_at(resolved_commit).grounding_max_arguments` once, passes that
  exact value to the hash and `_build_sidecar_file()`, and the builder projects
  `GroundingBuildConfiguration(configuration_id="grounding",
  max_arguments=grounding_max_arguments)` through `_project_documents()`.
- Add exactly
  `load_grounded_bundle_from_sidecar(session: DerivedSession) ->
  GroundedRulesBundle` to `propstore/grounding/loading.py`. This is the only new
  loader API. It directly reconstructs canonical `Predicate`,
  `DefeasibleRule`, `RuleSuperiority`, checked `Claim`, and `Concept` documents
  from their charter models; lowers each `Concept` only to the existing typed
  `ConceptRelations`; requires exactly one `GroundingBuildConfiguration` row;
  builds one `GroundingRepo`; and calls `build_grounded_bundle(...,
  return_arguments=True, max_arguments=config.max_arguments)`. Neither loose
  row dicts nor a second `load_grounding_repo_from_*` function crosses this
  boundary.

Production consumers and report fields:

- `WorldQuery.grounding_bundle()` is a method, preserving the existing
  `GroundingBundleStore` protocol. It memoizes one result in
  `self._grounding_bundle: GroundedRulesBundle | None` and calls
  `load_grounded_bundle_from_sidecar(self._session)` for both construction
  modes.
- Add exactly
  `grounding_bundle: GroundedRulesBundle | None = None` to
  `RepositoryBuildReport`. After materialization, `build_repository()` opens a
  Quire `readonly_session` over `handle.path` with
  `build_world_sidecar_schema()` and obtains this field through the same typed
  loader. Do not change `materialize_world_sidecar()`'s `(handle, built)` return
  contract and do not import `WorldQuery` into the compiler.
- Build presentation renders `bundle.status.value`, `bundle.max_arguments`
  (`"unbounded"` for `None`), and, when budget-exceeded,
  `bundle.budget_reason`, `bundle.partial_candidate_count`, and
  `len(bundle.arguments)`. It reads the bundle; it does not introduce a build
  status report.
- Grounding CLI commands open the production world through
  `open_app_world_model(repo)` and use only `world.grounding_bundle()`.
  `status`, `show`, and `arguments` label a budget-exceeded bundle before
  rendering partial evidence. `query` emits an incomplete result containing
  the exact status and reason and must not emit `status: absent`. The command
  boundary catches `ValueError` from an invalid grounding program and calls the
  existing `fail(str(exc))` presentation mapper. Delete `GroundingSurfaceState`
  and `grounding_surface_state()` after this cutover.

Fail-closed fields and behavior:

- ASPIC resolution compares `bundle.status is GroundingStatus.COMPLETE` before
  projection. A budget-exceeded bundle returns no winner and uses
  `bundle.budget_reason` as the existing `ResolvedResult.reason` path.
- Add `reason: str | None = None` beside `status` on the existing
  `WorldlineArgumentationState`. ASPIC capture returns
  `WorldlineArgumentationState(backend="aspic",
  status="grounding_budget_exceeded", reason=bundle.budget_reason)` without
  projection. `materialize_worldline()` checks that exact status immediately
  after `run_worldline()` and raises
  `WorldlineValidationError(result.argumentation.reason or
  result.argumentation.status)` before assigning `definition.results` or
  calling `save()`.
- Add exactly `grounding_status: GroundingStatus | None = None` and
  `grounding_budget_reason: str | None = None` to `FragilityReport`. When either
  grounding or bridge analysis is requested, absence of `GroundingBundleStore`
  raises `TypeError("grounding or bridge fragility requires a grounded bundle-capable store")`.
  A budget-exceeded bundle sets both report fields and skips the grounding and
  bridge collectors while preserving enabled ATMS/discovery/conflict results.
  When neither family is requested both fields remain `None`; a complete
  requested bundle records `GroundingStatus.COMPLETE` and a `None` reason.

Exact file/test disposition:

- Delete `propstore/grounding/sidecar.py` and
  `tests/test_sidecar_grounded_facts.py` in Slice 2. Rewrite
  `tests/test_world_sidecar_grounded.py` to prove the typed config-row and
  full-bundle sidecar path; do not leave raw-SQL grounded-fact assertions.
- Extend `tests/test_repository.py`, `tests/test_uri.py`, and
  `tests/test_uri_authority_validation.py` for the typed current/historical
  config and positive-budget contract; extend
  `tests/test_grounder_budget_exceeded.py` and
  `tests/test_grounding_loading.py` for enum identity and exact evidence.
- Extend `tests/test_derived_build.py`,
  `tests/test_semantic_family_registry.py`, `tests/test_semantic_passes.py`, and
  `tests/test_contract_manifest.py` for the charter, cache input, schema/version,
  and manifest changes.
- Extend `tests/test_world_query.py`, `tests/test_cli_phase10_advanced.py`, and
  `tests/test_cli_compiler_rendering.py` for both reader modes and complete versus
  partial rendering. Replace the old `none/invalid/ready` CLI assertions; the
  invalid-program case now asserts the owner error and nonzero exit.
- Extend `tests/test_resolution.py`, `tests/test_app_worldlines.py`,
  `tests/test_worldline_hash_excludes_transient_errors.py`, and
  `tests/test_fragility.py` for the exact fail-closed behavior and report fields.
  `tests/test_praf_argument_enumeration_budget.py` remains deferred to B3: B1
  propagates grounding completeness into ASPIC, not PrAF convergence status.

#### B1 Slice 1 — typed, commit-pinned budget and bundle evidence

1. Verify branch/tracked state and create a tracked cleanup-refactor fixed-point
   log under `plans/`; keep `notes-*.md` handoffs uncommitted.
2. Make `RepositoryConfigDocument` the typed return of `Repository.config`
   instead of erasing it to a dict; add optional positive
   `grounding_max_arguments`.
3. Add only the commit-aware repository-config read required by
   `materialize_world_sidecar(commit=...)`; HEAD access remains the property.
4. Replace loose bundle status with a grounding-specific enum. Preserve the
   selected maximum and Gunray's `partial_count` under a name that identifies it
   as a candidate count rather than assuming it equals
   `len(partial_arguments)`.
5. Thread `max_arguments` through `build_grounded_bundle()` into `ground()` and
   preserve reason, partial arguments, inspection, and candidate count.
6. Run
   `powershell -File scripts/run_logged_pytest.ps1 tests/test_repository.py tests/test_uri.py tests/test_uri_authority_validation.py tests/test_grounder_budget_exceeded.py tests/test_grounder_default_returns_arguments.py tests/test_grounding_loading.py -q`,
   then the applicable B1 searches and `uv run pyright propstore`. Update and
   include the fixed-point log, then commit exactly as
   `refactor(grounding): type budget completeness evidence` before Slice 2.

#### B1 Slice 2 — delete duplicate result storage and project canonical inputs

1. Delete `propstore/grounding/sidecar.py`, its derived-build imports/calls, and
   its raw-table contract tests before adding the replacement path.
2. Classify each deletion failure; never restore a table/helper/reader merely to
   repair an import or test.
3. Add one derived-only charter for selected grounding build configuration and
   add it to the computed-family projection set. It carries configuration only,
   never status, sections, arguments, or inspection.
4. Resolve the config from the same requested commit for the sidecar hash and
   builder. Hash only the grounding budget field in addition to existing inputs.
5. Bump `WORLD_SIDECAR_SCHEMA_VERSION` for the sidecar-shape change.
6. Add the typed sidecar load boundary over canonical predicates, rules,
   superiorities, checked claims, concepts, and grounding configuration. Loose
   rows/dicts must not cross the boundary.
7. Prove a built sidecar and a derived-store-only session produce the same full
   bundle from claim-derived facts. Concept-relation facts are explicitly not
   evidence for B1 because their production input is a separate gap.
8. Run `uv run pks contract-manifest --write`, then
   `powershell -File scripts/run_logged_pytest.ps1 tests/test_derived_build.py tests/test_world_sidecar_grounded.py tests/test_semantic_family_registry.py tests/test_semantic_passes.py tests/test_contract_manifest.py -q`,
   the applicable B1 deletion searches, `uv run lint-imports`, and
   `uv run pyright propstore`. Update and include the fixed-point log, then
   commit exactly as
   `refactor(grounding): derive bundles from canonical sidecar` before Slice 3.

#### B1 Slice 3 — production WorldQuery, build report, and inspection CLI

1. Implement and per-instance memoize `WorldQuery.grounding_bundle()` through
   the typed sidecar load boundary for both repo-backed and handle-only readers.
2. Carry the canonical bundle on `RepositoryBuildReport`; do not create a
   parallel status DTO. Build output renders exact status, selected budget,
   reason, and partial candidate/argument counts.
3. Rewrite `pks grounding status/show/query/arguments` to inspect the
   `WorldQuery` bundle and label incomplete evidence before rendering it.
4. Delete the CLI-local load/re-ground path; old and new paths must not coexist.
5. Prove both `WorldQuery` construction modes return complete output by default
   and `budget_exceeded` under a committed tiny configuration.
6. Run
   `powershell -File scripts/run_logged_pytest.ps1 tests/test_world_query.py tests/test_world_sidecar_grounded.py tests/test_cli_phase10_advanced.py tests/test_cli_compiler_rendering.py -q`,
   the applicable B1 searches, and `uv run pyright propstore`. Update and
   include the fixed-point log, then commit exactly as
   `feat(grounding): wire production bundle inspection` before Slice 4.

#### B1 Slice 4 — fail-closed ASPIC consumers and honest diagnostics

1. ASPIC resolution inspects completeness before projection. Incomplete
   grounding produces no winner and leaves `ResolvedResult` conflicted with the
   exact grounding reason.
2. ASPIC worldline capture does not project partial grounding; diagnostic
   `run_worldline()` returns an explicit `grounding_budget_exceeded` state.
3. `materialize_worldline()` detects that state and raises the existing app
   validation failure before assigning or saving results.
4. Delete fragility's empty-bundle fallback. When grounding/bridge diagnostics
   are requested, require the capability and carry explicit grounding status
   and reason on `FragilityReport`; never rank an incomplete bundle as complete
   empty output.
5. Prove one tiny-budget sidecar is visible as partial in diagnostics, refused
   by ASPIC resolution, refused without a worldline commit, and never reported
   complete by fragility.
6. Run
   `powershell -File scripts/run_logged_pytest.ps1 tests/test_resolution.py tests/test_app_worldlines.py tests/test_worldline_hash_excludes_transient_errors.py tests/test_fragility.py tests/test_cli_phase10_advanced.py -q`,
   every B1 search, `uv run lint-imports`, and `uv run pyright propstore`.
   Update and include the fixed-point log, then commit exactly as
   `fix(argumentation): fail closed on incomplete grounding`.

Gate: a deliberately tiny budget yields visible partial arguments and
`budget_exceeded` at every production boundary; no caller renders it as complete.

B1 search gates:

- `rg -n "create_grounded_fact_table|populate_grounded_facts|read_grounded_facts|grounded_fact" propstore tests`
  returns zero hits.
- `rg -n "def _load_grounding_repo" propstore` returns zero hits.
- `rg -n 'build_grounded_bundle\(' propstore/cli` returns zero hits.
- `rg -n "GroundingSurfaceState|grounding_surface_state" propstore tests`
  returns zero hits.
- `rg -n "else GroundedRulesBundle.empty" propstore` returns zero hits.
- `rg -n 'status: str = "complete"' propstore/grounding` returns zero hits.
- `rg -n 'status="complete"|status="budget_exceeded"' propstore/grounding`
  returns zero hits; construction uses `GroundingStatus` members.
- `rg -n "def grounding_bundle" propstore/world/model.py` finds the one
  production implementation.
- `rg -n "def load_grounded_bundle_from_sidecar" propstore` finds the one
  grounding-owned typed loader implementation.

B1 final focused gate:

`powershell -File scripts/run_logged_pytest.ps1 tests/test_repository.py tests/test_uri.py tests/test_uri_authority_validation.py tests/test_grounder_budget_exceeded.py tests/test_grounder_default_returns_arguments.py tests/test_grounding_loading.py tests/test_derived_build.py tests/test_world_sidecar_grounded.py tests/test_semantic_family_registry.py tests/test_semantic_passes.py tests/test_contract_manifest.py tests/test_world_query.py tests/test_resolution.py tests/test_app_worldlines.py tests/test_worldline_hash_excludes_transient_errors.py tests/test_fragility.py tests/test_cli_phase10_advanced.py tests/test_cli_compiler_rendering.py -q`

Then run `uv run pyright propstore`, `uv run lint-imports`,
`uv run ruff check .`, `uv run ruff format --check .`, and the full logged suite
with `powershell -File scripts/run_logged_pytest.ps1 -q`. After every substantial
passing test run, reread this plan and continue to the next unchecked B1 item.

### B2. ASPIC

- The grounding-to-ASPIC completeness handoff is owned and completed only by B1
  Slice 4; B2 must not add a second grounding status or repeat that cutover.
- [ ] Add an explicit completeness result for goal-directed `max_depth` exhaustion.
- [ ] Promote optional solver `package_status` from generic metadata into the
  existing typed analyzer result surface.
- [ ] Verify world and worldline never convert failed/partial ASPIC computation
  into an empty successful extension.

### B3. PrAF owner package and Propstore propagation

- [ ] Change the argumentation package owner to accept caller-supplied
  `max_samples` and return explicit convergence/cap status.
- [ ] Propagate that owner result through `AnalyzerResult`, resolution, CLI, and
  worldline without conflating it with COH convergence.
- [ ] Distinguish epsilon met, sample cap hit, exact strategy, Monte Carlo strategy,
  and automatic downgrade.

### B4. ATMS

- [ ] Carry build `fixpoint_reached`, iteration count, and warnings into existing
  worldline argumentation results.
- [ ] Make ATMS resolution refuse an unqualified winner or mark it incomplete when
  the build did not reach a fixpoint, per Q2.
- [ ] Keep future-query `BudgetExhausted(examined, total)` separate; do not replace
  it with build-fixpoint status.

Workstream B gate:

- Owner-focused logged suites distinguish complete, partial/capped, and failed
  outcomes for each backend.
- No generic result status obscures backend-specific cause or evidence.
- `uv run pyright propstore` passes in Propstore and the changed owner package.

## Workstream C — Relation classification to proposal workflow

Do not create a new embedding or proposal owner.

### C1. Typed classifier convergence

- [ ] Delete the reachable loose-dictionary stance result path.
- [ ] Make one typed proposal-ready result carry source/target ids, `StanceType`,
  model/call provenance, direction-specific distance, optional opinion, and
  unresolved-calibration detail.
- [ ] Normalize errors to typed `ABSTAIN`; do not persist a non-vocabulary
  `"error"` stance.
- [ ] Pass distinct forward and reverse embedding distances to their corresponding
  classifier calls.

Gate:

`powershell -File scripts/run_logged_pytest.ps1 tests/test_classify.py tests/test_classify_forward_reverse_independent.py tests/test_classify_no_silent_fallback.py tests/test_relate_perspective_isolation.py tests/test_relate_wbf.py -q`

### C2. Relation reads over existing world owners

- [ ] Replace `ClaimRelationStore` with direct use of existing world query/store
  capabilities unless a concrete remaining owner proves the protocol necessary.
- [ ] Project canonical claims to `RelatableClaim` at the heuristic boundary.
- [ ] Derive source attribution from canonical micropublication membership; do not
  add claim-local provenance.
- [ ] Bound candidate selection and retain the existing vector-store owner.

### C3. Calibration inputs

- [ ] Resolve Q3.
- [ ] Add the chosen labeled-judgment owner and reproducible calibration-count
  computation in the derived-build owner.
- [ ] Add the provenance-bearing category-prior provider.
- [ ] Load counts/priors in the production relation workflow and pass them through
  to typed classification.
- [ ] Keep absent authority explicit as unresolved; never invent defaults.

### C4. Record proposals

- [ ] Resolve Q4 for durable evidence fields.
- [ ] Record each directional typed result through existing
  `commit_stance_proposal()`.
- [ ] Preserve `pks proposal promote` as the only canonical acceptance step.
- [ ] Add a thin bounded CLI/app entry point only after the owner path passes.

Required vertical gate:

Built sidecar + real `WorldQuery` + deterministic model-boundary response -> two
typed directional stance proposals on `proposal/stances`, with distinct distances,
honest calibration state, and no canonical stance mutation.

Then run the logged stance-proposal/CLI suites and `uv run pyright propstore`.

## Workstream D — Predicate and rule extraction completion

### D1. Shared requirements without a new client abstraction

- [ ] Resolve repository paper inputs from the selected `Repository`, never the
  process working directory.
- [ ] Resolve Q4 for durable model evidence.
- [ ] Use lazy LiteLLM calls at each heuristic owner boundary; do not introduce a
  new interface/helper solely to share two small calls.
- [ ] Preserve current typed decoding, rejection, proposal transactions, and
  promotion owners.

### D2. Predicate extraction

- [ ] Replace the raising predicate `_llm_call` with the real model boundary.
- [ ] Add one production adapter. Recommended command:
  `pks proposal propose-predicates`, parallel to `propose-rules`; do not also add
  `pks predicate extract`.
- [ ] Keep manual `pks predicate declare` and existing promotion unchanged.

Gate: command -> model boundary -> typed decode -> existing predicate proposal
owner, with no canonical predicate write; logged predicate lifecycle suites pass.

### D3. Rule extraction

- [ ] Replace only the raising rule `_llm_call` boundary.
- [ ] Keep predicate admission, typed rejections, fixture injection used by tests,
  proposal transaction, and selective promotion unchanged.

Gate: command -> model boundary -> typed admitted/rejected results -> existing rule
proposal owner; logged rule extraction/promotion suites pass.

## Workstream E — Provenance, verification, and views

### E1. Typed indexing foundation

- [ ] Add a source-owner index that enumerates `SourceRef` values and resolves
  source identity and promoted source-claim artifact ids without exposing branch
  parsing to app code.
- [ ] Add one typed claim-provenance index over canonical micropublications.
- [ ] Preserve multiple sources and distinguish unbundled claims from source-less
  claims; do not collapse to a single source.

Gate: one source, multiple sources for one claim, unbundled claim, unknown source,
and source enumeration are covered by focused tests.

### E2. Verification composition

- [ ] Add a typed app request/report combining existing source artifact/origin
  verification with existing world/ATMS claim status.
- [ ] Keep storage verification world-free; composition belongs in app code.
- [ ] Add thin CLI adapters only after the app owner passes.

Gate: mismatched, unstamped, missing-origin, unknown-claim, no-label, and supported
claim cases pass alongside existing tree verification.

### E3. Correct existing views

- [ ] Replace hard-coded missing claim/concept provenance with the canonical
  micropublication index.
- [ ] Replace unavailable claim assumptions with existing bound-world ATMS support.
- [ ] Preserve render-policy visibility and honest unbundled/vacuous states.

### E4. Repository overview

- [ ] Reuse `build_log_report`, `world.conflicts`, and the provenance index.
- [ ] Replace prose-only placeholders with typed activity, provenance, and conflict
  rows.
- [ ] Do not implement conflict ranking or provenance aggregates until Q5 selects
  their semantics; unranked factual rows/counts may land first.

### E5. Neighborhoods

- [ ] Implement concept focus as an app projection over existing world/concept
  view inputs.
- [ ] Implement worldline focus as an app projection over existing definition,
  result dependency, and journal inputs.
- [ ] Implement source focus only after Q5 selects identity and branch/canonical
  scope; keep it in a source-aware app owner, not `WorldQuery`.
- [ ] Add CLI/web adapters only after each app projection passes focused tests.

Workstream E gate:

- Logged verification, app-view, neighborhood, web, history, source, and worldline
  suites pass.
- `uv run pyright propstore` passes.

## Workstream F — Owner-surface disposition

These are explicit dispositions, not an automatic feature backlog.

### Existing behavior to keep

- [ ] Form `show` remains on its existing app owner.
- [ ] Rule and source-derived micropublication mutation remain proposal/source
  owned; no direct mutation commands are added.
- [ ] Test-only alternate repositories remain non-production until deletion-first
  cleanup separately proves they are dead and deletes them.

### Valid missing read owners

- [ ] Add typed app list/show owners for contexts, rules, and micropublications,
  then move CLI presentation to those owners without changing behavior.

### Decision-blocked mutations

- [ ] Form mutation: blocked on Q5 reference/deletion/proposal policy.
- [ ] Context/lifting-rule mutation: blocked on Q5 authoring and reference policy.
- [ ] Micropublication lift inspection: blocked on Q5 bundle-lift semantics.

These blocked items are not plan failures and must not be replaced by direct
family writes.

## Final convergence gate

- [ ] Every implemented phase ends in a focused production-path test, a committed
  kept slice, and the named logged suites.
- [ ] Full logged pytest suite passes.
- [ ] `uv run pyright propstore` passes.
- [ ] No old/new production path coexistence remains for typed classifier results,
  source/provenance indexing, or result-completeness propagation.
- [ ] No stale skip/comment claims a capability is missing when it is production
  wired.
- [ ] Every decision-blocked item remains visibly deferred rather than replaced by
  an inferred policy.
- [ ] Review the plan from top to bottom and verify every phase is complete or
  explicitly deferred by the user before declaring convergence complete.
