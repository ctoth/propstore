# Workstream CLI Layer Discipline

Date: 2026-04-17
Status: IN PROGRESS
Depends on: `disciplines.md`, `judgment-rubric.md`
Blocks: none
Review context: layer discipline from `../axis-2-layer-discipline.md` and the
standing architecture in `../../../CLAUDE.md`.

## What triggered this

The CLI package had become an application and domain layer by accumulation.
`propstore/cli/compiler_cmds.py` was roughly 100 KB and hosted compiler
workflow orchestration, world query behavior, revision operation plumbing,
ATMS interrogation, graph export, sensitivity, fragility, and consistency
checking. Other CLI modules had similar drift at smaller scale: concept
mutation logic in `propstore/cli/concept.py`, log classification in
`propstore/cli/__init__.py`, source status SQL in `propstore/cli/source.py`,
worldline definition construction in `propstore/cli/worldline_cmds.py`, and
grounding inspection in `propstore/cli/grounding_cmds.py`.

I read every file under `propstore/cli/` on 2026-04-17 before creating this
workstream:

- `__init__.py`
- `claim.py`
- `compiler_cmds.py`
- `concept.py`
- `context.py`
- `form.py`
- `grounding_cmds.py`
- `helpers.py`
- `init.py`
- `merge_cmds.py`
- `micropub.py`
- `repository_import_cmd.py`
- `source.py`
- `verify.py`
- `worldline_cmds.py`

## Target discipline

The CLI package is a presentation adapter. It may:

- declare Click groups, commands, options, and arguments;
- parse command-line strings into typed request objects;
- call owner-layer functions;
- render typed result objects;
- translate typed failures into Click exceptions or exit codes.

The CLI package must not own:

- compiler/build/validation workflows;
- repository mutation semantics;
- source promotion/finalize/status semantics;
- world, ATMS, revision, fragility, sensitivity, graph, or argumentation
  query semantics;
- concept identity mutation logic;
- sidecar SQL access policy;
- reusable formatting that a non-CLI caller would reasonably need.

## Owner API contract

Each extraction must publish the same shape before the CLI caller is changed:

- frozen request dataclass when the operation has more than one domain input;
- frozen report/result dataclass for successful behavior;
- typed failure class or sum type for expected failures;
- renderer function in CLI when the output is command-specific text;
- direct owner-layer test for behavior plus CLI output test for rendering.

Owner modules must not import `click`, call `sys.exit`, or write to stdout or
stderr. Owner modules must not accept Click-shaped flag names when a domain
object already exists. For render workflows, CLI may construct a `RenderPolicy`
from command flags; owner functions accept the policy rather than rebuilding it.

World/render workflows should not hide `WorldModel` lifecycle behind generic
helpers. A world query owner function should take an existing `WorldModel` or
`BoundWorld` plus a typed request. Repository/compiler/storage workflows may
take `Repository` because their job is to orchestrate repository state.

## Target module map

| Current CLI responsibility | Owner module |
|---|---|
| `pks validate`, `pks build` orchestration | `propstore.compiler.workflows` |
| raw read-only sidecar query policy | `propstore.sidecar.query` |
| concept alias export | `propstore.core.aliases` |
| world status/query/bind/explain/derive/resolve/chain/hypothetical | `propstore.world.queries` or narrower `propstore.world.*_workflows` modules |
| ATMS status/context/futures/stability/relevance/interventions/next-query | `propstore.world.atms_workflows` |
| revision-base/expand/contract/revise/iterated surfaces | `propstore.support_revision.workflows` or `propstore.world.revision_workflows` |
| argumentation extension computation | `propstore.world.argumentation_workflows` |
| sensitivity/fragility/export-graph/check-consistency | existing owner modules plus thin workflow functions where needed |
| concept add/alias/rename/deprecate/link/qualia/proto-role/add-value | `propstore.core.concept_workflows` or artifact-family-specific concept services |
| concept search/embed/similar | `propstore.core.concept_search` / `propstore.embed` request-result functions |
| claim show/validate/conflicts/compare/embed/similar/relate | `propstore.claims.workflows` plus existing `compiler`, `conflict_detector`, `embed`, `relate` |
| context/form add/list/show/remove/validate | owner workflow modules in `propstore.contexts` / `propstore.forms` or existing typed artifact helpers |
| source CLI status and auto-finalize wrapper | `propstore.source.status` / `propstore.source` return objects |
| worldline create/run/show/list/diff/refresh/delete request handling | `propstore.worldline.workflows` |
| log/diff/show/checkout repository-history presentation data | `propstore.storage.history` / `propstore.storage.checkout` |
| grounding status/show/query/arguments inspection | `propstore.grounding.inspection` |
| init seed construction | `propstore.bootstrap` or `propstore.repository_init` |
| micropub iteration/find/lift query | `propstore.micropubs` / context lifting owner modules |

## Phase structure

### Phase CLI-1 - Compiler and sidecar extraction

- Move repository validation/build orchestration from
  `propstore/cli/compiler_cmds.py` to `propstore/compiler/workflows.py`.
- Move raw sidecar query execution to `propstore/sidecar/query.py`.
- Move concept alias export to `propstore/core/aliases.py`.
- Keep the CLI text output stable.
- Run targeted CLI/build/query/export-alias tests through the logged wrapper.

Status 2026-04-17: first slice landed.

- Added `propstore.compiler.workflows` with typed validation/build reports,
  messages, and failures.
- Added `propstore.sidecar.query` with typed read-only SQL result/failure.
- Added `propstore.core.aliases` with typed alias export entries.
- Reduced `propstore/cli/compiler_cmds.py` by moving `validate`, `build`,
  `query`, and `export-aliases` behavior to owner modules while keeping CLI
  rendering stable.
- Verification:
  - `logs/test-runs/cli-layer-20260417-165300.log` - 161 passed.
  - `logs/test-runs/cli-layer-build-20260417-165335.log` - 203 passed.
  - `logs/test-runs/cli-layer-smoke-20260417-165522.log` - 11 passed.
  - `uv run pyright propstore/compiler/workflows.py propstore/sidecar/query.py propstore/core/aliases.py` - 0 errors.

Observed debt: `propstore/cli/compiler_cmds.py` still has pre-existing pyright
errors unrelated to this first extraction. They remain in the old CLI/world
surface and should be retired as the corresponding logic moves.

### Phase CLI-2 - World query extraction

- Extract render-policy construction, target resolution, value formatting, and
  world status/query/bind/explain/algorithms/derive/resolve/chain/hypothetical
  workflows into `propstore.world` owner modules.
- CLI commands construct requests and render typed reports only.
- Delete the old production path in `compiler_cmds.py` as each workflow moves.

Status 2026-04-17: `pks world status` slice landed.

- Added `propstore.world.queries` with `WorldStatusRequest`,
  `WorldStatusReport`, `WorldQueryError`, and `get_world_status`.
- Kept lifecycle flag parsing / `RenderPolicy` construction in the CLI; the
  owner API accepts the policy.
- Added owner-layer assertions for default and all-flags status counts, paired
  with existing CLI output assertions.
- Verification:
  - `logs/test-runs/cli-layer-world-status-20260417-170155.log` - 6 passed.
  - `uv run pyright propstore/world/queries.py propstore/compiler/workflows.py propstore/sidecar/query.py propstore/core/aliases.py` - 0 errors.

Status 2026-04-17: `pks world query` slice landed.

- Added `WorldConceptQueryRequest`, `WorldConceptQueryReport`, typed claim and
  diagnostic rows, and `query_world_concept`.
- Added owner-layer assertions for default policy filtering and all-flags
  diagnostic visibility, paired with existing CLI output assertions.
- Preserved SI value display through the owner report because canonical-unit
  lookup depends on world/concept metadata.
- Verification:
  - `logs/test-runs/cli-layer-world-query-20260417-170802.log` - 9 passed.
  - `uv run pyright propstore/world/queries.py` - 0 errors.

Status 2026-04-17: `pks world bind` slice landed.

- Added `WorldBindRequest`, typed bind reports, and `query_bound_world`.
- CLI parsing remains in `compiler_cmds.py`; binding/query behavior moved to
  `propstore.world.queries`.
- Added owner-layer assertion for bound SI-value display, paired with existing
  CLI output assertions.
- Verification:
  - `logs/test-runs/cli-layer-world-bind-20260417-171012.log` - 5 passed.
  - `uv run pyright propstore/world/queries.py` - 0 errors.

Status 2026-04-17: `pks world explain` and `pks world algorithms` slice landed.

- Added `WorldExplainRequest`, `WorldExplainReport`, typed stance lines,
  `UnknownClaimError`, and `explain_world_claim`.
- Added `WorldAlgorithmsRequest`, `WorldAlgorithmsReport`, typed algorithm
  rows, and `list_world_algorithms`.
- Replaced CLI-owned claim lookup, stance-chain traversal, algorithm filtering,
  and algorithm row shaping with owner-layer reports; CLI now only opens the
  `WorldModel`, maps expected failures, and renders text.
- Tightened tests to use `WorldModel` as a context manager and added explicit
  CLI-output tests for both commands.
- Verification:
  - `logs/test-runs/cli-layer-world-explain-algorithms-20260417-171434.log` - 9 passed.
  - `uv run pyright propstore/world/queries.py` - 0 errors.

Status 2026-04-17: `pks world derive` and `pks world hypothetical` slice landed.

- Added `WorldDeriveRequest`, `WorldDeriveReport`, and `derive_world_value`.
- Added typed hypothetical synthetic-claim specs, change lines, reports, and
  `diff_hypothetical_world`.
- Replaced CLI-owned world binding, derivation, synthetic-claim construction,
  claim removal resolution, and hypothetical diff shaping with owner-layer
  reports. The CLI remains responsible for parsing raw JSON from `--add` and
  rendering text.
- Added direct owner tests for derive status and removed-claim hypothetical
  changes, and expanded the CLI lifecycle regression coverage to include
  `world derive`.
- Verification:
  - `logs/test-runs/cli-layer-world-derive-hypothetical-20260417-171913.log` - 12 passed.
  - `uv run pyright propstore/world/queries.py` - 0 errors.

Status 2026-04-17: `pks world resolve` and `pks world chain` slice landed.

- Added `WorldResolveRequest`, `WorldResolveReport`, typed acceptance
  probability lines, `WorldResolveError`, and `resolve_world_value`.
- Added `WorldChainRequest`, typed target/step/report objects, and
  `query_world_chain`.
- Replaced CLI-owned resolution execution, winner display lookup, chain query
  execution, concept label lookup, and chain step shaping with owner-layer
  reports. CLI still constructs the `RenderPolicy` from command flags and
  renders text.
- Added owner-layer tests for resolved values and direct-claim chain steps,
  plus CLI output coverage for `world chain`.
- Verification:
  - `logs/test-runs/cli-layer-world-resolve-chain-20260417-172224.log` - 15 passed.
  - `uv run pyright propstore/world/queries.py` - 0 errors.

Status 2026-04-17: `pks world export-graph` slice landed.

- Added `GraphExportRequest`, `GraphExportReport`, and
  `export_knowledge_graph` to `propstore.graph_export`, next to the graph
  model and DOT/JSON serializers it already owns.
- Replaced CLI-owned graph binding and graph construction with the owner
  report. CLI now chooses the requested textual format and handles optional
  file output.
- Added direct owner-layer graph export coverage while retaining the existing
  CLI JSON-output regression.
- Verification:
  - `logs/test-runs/cli-layer-world-graph-export-20260417-172446.log` - 16 passed.
  - `uv run pyright propstore/graph_export.py` - 0 errors.

Status 2026-04-17: `pks world check-consistency` slice landed.

- Added `propstore.world.consistency` with `WorldConsistencyRequest`,
  `WorldConsistencyReport`, typed conflict lines, and
  `check_world_consistency`.
- Replaced CLI-owned bound conflict detection and transitive conflict registry
  construction with the owner module. The owner now uses typed row coercion
  instead of the previous CLI-local `dict(row)` handling.
- Added owner tests for both bound and transitive no-conflict paths, paired
  with CLI output assertions for both command modes.
- Verification:
  - `logs/test-runs/cli-layer-world-consistency-20260417-172716.log` - 19 passed.
  - `uv run pyright propstore/world/consistency.py` - 0 errors.

Status 2026-04-17: `pks world sensitivity` slice landed.

- Added `SensitivityRequest`, `SensitivityReport`, and `query_sensitivity` to
  `propstore.sensitivity`, next to the existing derivative analysis logic.
- Replaced CLI-owned target resolution and world binding with the owner
  request/report wrapper. CLI now renders either the unavailable-analysis
  message or the existing text/JSON sensitivity output.
- Added owner coverage for the unavailable-analysis path and CLI output
  coverage for the same command surface.
- Verification:
  - `logs/test-runs/cli-layer-world-sensitivity-20260417-172902.log` - 21 passed.
  - `uv run pyright propstore/sensitivity.py` - 0 errors.

Status 2026-04-17: `pks world fragility` slice landed.

- Added `FragilityRequest` and `query_fragility` to `propstore.fragility`,
  next to the existing fragility ranking orchestrator.
- Replaced CLI-owned world binding and fragility option plumbing with the
  owner request. CLI now renders the existing text/JSON report only.
- Added owner coverage for the all-families-skipped empty report, paired with
  the existing fragility CLI output regressions.
- Verification:
  - `logs/test-runs/cli-layer-world-fragility-20260417-173131.log` - 25 passed.
  - `uv run pyright propstore/fragility.py` - 0 errors.

Status 2026-04-17: world-query CLI helper cleanup landed.

- Removed stale CLI-local value/SI formatting and display-id helpers after
  their behavior moved to owner modules.
- Verification:
  - `logs/test-runs/cli-layer-world-cleanup-20260417-173247.log` - 22 passed.

### Phase CLI-3 - ATMS and revision extraction

- Move ATMS inspection workflows into `propstore.world.atms_workflows`.
- Move support-revision command behavior into the support revision/world owner
  layer.
- Preserve ATMS/revision tests while replacing CLI-owned orchestration with
  owner-layer result objects.

Status 2026-04-17: support revision workflow slice landed.

- Added `propstore.support_revision.workflows` with `RevisionWorldRequest`,
  `IteratedRevisionReport`, and owner functions for revision base,
  entrenchment, expand, contract, revise, explain, epistemic state, and
  iterated revise.
- Replaced CLI-owned revision world binding and revision operation
  orchestration with owner workflow calls. CLI keeps JSON argument parsing and
  text rendering.
- Added direct workflow tests beside the existing revision CLI coverage.
- Verification:
  - `logs/test-runs/cli-layer-revision-workflows-20260417-173524.log` - 11 passed.
  - `uv run pyright propstore/support_revision/workflows.py` - 0 errors.

Status 2026-04-17: ATMS binding/lifecycle slice landed.

- Added `propstore.world.atms_workflows` with `ATMSBindRequest` and
  `bind_atms_world`, so ATMS reasoning policy and context binding live outside
  the CLI.
- Replaced the remaining direct `WorldModel(repo)` / manual `wm.close()` ATMS
  helper in `compiler_cmds.py` with a context-managed CLI wrapper around
  `open_world_model`.
- Added direct owner coverage for ATMS policy/context binding and retained the
  ATMS CLI regression tests for status, context, verify, futures, why-out,
  stability, relevance, interventions, and next-query surfaces.
- Verification:
  - `logs/test-runs/cli-layer-atms-lifecycle-20260417-174021.log` - 4 passed.
  - `uv run pyright propstore/world/atms_workflows.py` - 0 errors.

### Phase CLI-4 - Concept, claim, source, form, context extraction

- Move concept mutations behind typed owner-layer functions.
- Move claim validation/conflict/compare/embedding/relation request handling
  behind typed owner-layer functions.
- Move source status SQL and auto-finalize reporting into `propstore.source`.
- Move form/context mutation and validation behavior out of CLI modules.

Status 2026-04-17: claim show/compare slice landed.

- Added claim owner APIs in `propstore.claims` for `show_claim` and
  `compare_algorithm_claims`, with typed request/report/failure objects.
- Replaced direct `WorldModel` lifecycle and claim/algorithm row shaping in
  `propstore.cli.claim` for `claim show` and `claim compare`.
- Added owner tests for SI display data and non-algorithm comparison failure,
  paired with existing CLI `claim show` output tests.
- Verification:
  - `logs/test-runs/cli-layer-claim-show-compare-20260417-174436.log` - 5 passed.
  - `uv run pyright propstore/claims.py` - 0 errors.

Status 2026-04-17: form show slice landed.

- Added `show_form`, `FormShowReport`, algebra line types, and
  `FormNotFoundError` to `propstore.form_utils`.
- Replaced CLI-owned form YAML lookup, conversion report source loading, and
  sidecar algebra lookup with the owner report. CLI now renders the sections.
- Added owner coverage for YAML/conversion reporting, paired with existing
  form conversion and algebra CLI tests.
- Verification:
  - `logs/test-runs/cli-layer-form-show-20260417-174758.log` - 6 passed.
  - `uv run pyright propstore/form_utils.py` - 0 errors.

Status 2026-04-17: form workflow slice landed.

- Extended `propstore.form_utils` with typed list, add, remove, and validate
  reports plus workflow failures.
- Moved form dimension filtering, JSON option parsing, document construction,
  artifact save/delete/sync, form-reference checks, and validation report
  assembly out of `propstore.cli.form`.
- Added owner and CLI coverage for add/list/validate/remove, malformed JSON,
  missing forms, dry-run rendering, and dimension-filtered listing.
- Verification:
  - `logs/test-runs/cli-layer-form-workflows-20260417-181620.log` - 4 passed.
  - `uv run pyright propstore/form_utils.py propstore/cli/form.py` - 0 errors.

Status 2026-04-17: source status slice landed.

- Added `propstore.source.status` with typed source-status states, rows, and
  diagnostic reports.
- Moved source promotion-status sidecar queries and diagnostic correlation out
  of `propstore.cli.source`; CLI now renders the returned report state.
- Added direct owner coverage for blocked-row reports and missing-sidecar
  reports, paired with the existing source status CLI coverage.
- Verification:
  - `logs/test-runs/cli-layer-source-status-20260417-175844.log` - 5 passed.
  - `uv run pyright propstore/source/status.py propstore/cli/source.py` - 0 errors.

Status 2026-04-17: context workflow slice landed.

- Added `propstore.context_workflows` with typed add requests, add reports,
  list rows, and workflow failures.
- Moved context parameter parsing, duplicate detection, document construction,
  artifact save/sync, and list item projection out of `propstore.cli.context`.
- Added owner coverage for structured writes, duplicate detection, malformed
  parameters, dry-run behavior, and list rendering. Existing context CLI
  integration checks remain green.
- Verification:
  - `logs/test-runs/cli-layer-context-workflows-20260417-181014.log` - 5 passed.
  - `uv run pyright propstore/context_workflows.py propstore/cli/context.py` - 0 errors.

### Phase CLI-5 - Worldline, grounding, micropub, history extraction

- Move worldline definition/request construction and materialization reporting
  into `propstore.worldline.workflows`.
- Move grounding inspection into `propstore.grounding.inspection`.
- Move micropublication traversal and lift query behavior out of CLI.
- Move log classification/merge summary/diff/show/checkout report generation
  into storage/repository owner modules.

Status 2026-04-17: worldline model lifecycle slice landed.

- Replaced direct `WorldModel(repo)` construction and manual `close()` handling
  in worldline materialization and freshness checks with the shared
  `open_world_model` lifecycle helper.
- Verified no direct `WorldModel(repo)` construction remains under
  `propstore/cli` except the helper boundary itself.
- Verification:
  - `logs/test-runs/cli-layer-worldline-lifecycle-20260417-175153.log` - 3 passed.
  - `rg -n -F "WorldModel(repo)" propstore\cli` - only
    `propstore\cli\helpers.py:173`.

Status 2026-04-17: grounding inspection slice landed.

- Added `propstore.grounding.inspection` with typed surface, status, show,
  query, and arguments reports plus typed inspection failures.
- Moved grounding authoring-surface classification, bundle loading, grounded
  rule projection, argument projection, and atom parsing out of
  `propstore.cli.grounding_cmds`.
- Added owner coverage for ready and invalid grounding surfaces, rule/section
  projection, argument projection, and typed query parsing. Existing CLI demo
  grounding output tests remain green.
- Verification:
  - `logs/test-runs/cli-layer-grounding-inspection-20260417-175618.log` - 7 passed.
  - `uv run pyright propstore/grounding/inspection.py propstore/cli/grounding_cmds.py` - 0 errors.

Status 2026-04-17: micropub report slice landed.

- Added `propstore.micropubs` with typed lookup failures, entry reports, and
  lift reports.
- Moved micropublication bundle lookup, artifact traversal, and context-lift
  checks out of `propstore.cli.micropub`.
- Added owner coverage for bundle lookup, entry lookup, liftable and
  not-liftable reports, plus CLI coverage for bundle/show/lift rendering.
- Verification:
  - `logs/test-runs/cli-layer-micropub-reports-20260417-180144.log` - 3 passed.
  - `uv run pyright propstore/micropubs.py propstore/cli/micropub.py` - 0 errors.

Status 2026-04-17: log history report slice landed.

- Added `propstore.repository_history` with typed log reports, log records,
  merge summaries, operation classification, and branch-not-found failures.
- Moved `pks log` operation classification, merge-manifest summary loading,
  branch resolution, and structured record assembly out of `propstore.cli`.
- Added owner coverage for structured log reports, missing branch failures, and
  operation classification. Existing log CLI text/YAML tests remain green.
- Fixed the merge-commit helper to import `ArtifactRepository`, the actual
  artifact repository API used to prepare merge artifacts.
- Verification:
  - `logs/test-runs/cli-layer-log-history-20260417-180653.log` - 10 passed.
  - `uv run pyright propstore/repository_history.py propstore/cli/__init__.py` - 0 errors.

Status 2026-04-17: diff/show/checkout history slice landed.

- Extended `propstore.repository_history` with typed file-change, commit-show,
  and checkout reports plus commit-not-found and no-concepts failures.
- Moved root `pks diff`, `pks show`, and `pks checkout` snapshot querying and
  sidecar checkout decisions out of `propstore.cli.__init__`.
- Added owner coverage for diff/show reports and checkout missing-commit
  failure, paired with existing CLI diff/show/checkout regression tests.
- Verification:
  - `logs/test-runs/cli-layer-history-commands-20260417-181837.log` - 5 passed.
  - `uv run pyright propstore/repository_history.py propstore/cli/__init__.py` - 0 errors.

Status 2026-04-17: proposal promotion slice landed.

- Added typed stance proposal promotion plans, items, and results to
  `propstore.proposals`.
- Moved top-level `pks promote` proposal branch discovery, requested-file
  selection, target path calculation, artifact promotion, and sync semantics
  out of `propstore.cli.__init__`.
- Added owner coverage for promotion planning, missing proposal branch reports,
  and master promotion. Existing promote CLI registration, help, commit, and
  commit-failure atomicity regressions remain green.
- Verification:
  - `logs/test-runs/cli-layer-proposal-promotion-20260417-185006.log` - 7 passed.
  - `uv run pyright propstore/proposals.py propstore/cli/__init__.py` - 0 errors.

Status 2026-04-17: claim embedding and relation slice landed.

- Added typed claim embedding, similarity, and relation request/report surfaces
  to `propstore.claims`.
- Moved sidecar connection lifecycle, vec extension loading, registered-model
  selection, embedding dispatch, similarity search selection, relation
  classification, and stance proposal commits out of `propstore.cli.claim`.
- Added owner coverage for embedding progress/connection ownership, default
  similarity model selection, single-claim proposal commits, and all-claims
  summary reporting. Existing CLI connection-leak and proposal-branch
  regressions remain green.
- Verification:
  - `logs/test-runs/cli-layer-claim-workflows-20260417-185735.log` - 6 passed.
  - `uv run pyright propstore/claims.py propstore/cli/claim.py` - 0 errors.

Status 2026-04-17: concept sidecar workflow slice landed.

- Added a typed `propstore.concepts` owner surface for user-facing concept
  sidecar search, concept embedding, and concept similarity workflows.
- Moved sidecar presence checks, SQLite connection lifecycle, concept-handle
  resolution, registered-model selection, embedding dispatch, and similarity
  query selection out of `propstore.cli.concept`.
- Added owner coverage for search query ownership, embedding progress and
  connection ownership, and similarity default-model resolution. Existing
  `concept search` CLI regressions remain green.
- Verification:
  - `logs/test-runs/cli-layer-concept-workflows-20260417-190335.log` - 7 passed.
  - `uv run pyright propstore/concepts.py propstore/cli/concept.py` - 0 errors.

Status 2026-04-17: claim WorldModel lifecycle follow-up landed.

- Added repo-level claim show/compare wrappers that use `WorldModel` directly
  as a context manager in the claim owner layer.
- Removed `open_world_model` ownership from `pks claim show` and
  `pks claim compare`; those commands now render owner reports and map typed
  owner failures.
- Added owner coverage for missing-sidecar wrapper failures while keeping the
  existing claim show CLI regressions green.
- Verification:
  - `logs/test-runs/cli-layer-claim-worldmodel-20260417-190628.log` - 10 passed.
  - `uv run pyright propstore/claims.py propstore/cli/claim.py` - 0 errors.

Status 2026-04-17: project initialization slice landed.

- Added `propstore.project_init` as the owner for repository bootstrap,
  packaged form/concept seed loading, typed seed artifact rendering, and the
  initial seed commit.
- Reduced `propstore.cli.init` to target-directory resolution, owner failure
  mapping, and output rendering.
- Added owner coverage for fresh initialization and already-initialized
  reporting. Existing init CLI and git-backed initialization regressions remain
  green.
- Verification:
  - `logs/test-runs/cli-layer-project-init-20260417-190937.log` - 15 passed.
  - `uv run pyright propstore/project_init.py propstore/cli/init.py` - 0 errors.

Status 2026-04-17: init package experiment reverted.

- Restored `propstore.cli.init` as a flat command module. Single-command
  modules do not need package directories.
- Kept the project initialization owner extraction in `propstore.project_init`;
  only the CLI adapter layout changed back.
- Verification:
  - `logs/test-runs/cli-init-flat-20260417-191616.log` - 15 passed.
  - `uv run pyright propstore/cli/init.py propstore/cli/__init__.py` - 0 errors.

Status 2026-04-17: world CLI split landed.

- Moved the `pks world` command group and its CLI-only render helpers from
  `propstore.cli.compiler_cmds` to flat module `propstore.cli.world_cmds`.
- Reduced `propstore.cli.compiler_cmds` to compiler-facing top-level commands:
  `validate`, `build`, raw sidecar `query`, and `export-aliases`.
- Updated root CLI registration so `world` is imported from
  `propstore.cli.world_cmds`.
- Added a layout guard preventing `@world.command` handlers from returning to
  `compiler_cmds.py`.
- Verification:
  - `logs/test-runs/cli-world-split-20260417-192812.log` - 47 passed.
  - `logs/test-runs/cli-world-split-revision-extensions-20260417-193018.log` - 15 passed.
  - `logs/test-runs/cli-world-layout-20260417-193048.log` - 1 passed.
  - `uv run pyright propstore/cli/compiler_cmds.py propstore/cli/world_cmds.py propstore/cli/__init__.py` - 0 errors.

### Phase CLI-6 - Discipline capture and enforcement

- Update `AGENTS.md` and `CLAUDE.md` with the CLI adapter discipline.
- Add tests or architectural checks that prevent large workflow logic from
  returning to `propstore.cli` where practical.
- Update `docs/cli-reference.md` only if command behavior changes. The default
  target is no behavior change.

## Exit criteria

- `propstore/cli/*.py` files contain Click declarations, argument parsing,
  owner-layer calls, rendering, and failure mapping only.
- Every moved behavior has one owner-layer function with typed request/result
  objects or typed failures.
- Every extracted command has a stable output-contract test. Existing
  `CliRunner` assertions count where they cover the exact command text; larger
  extractions should add snapshot-style fixtures before moving behavior.
- Every extracted command has at least one owner-layer behavior test that does
  not call the CLI.
- No compatibility shim, alias path, fallback reader, or old/new dual path is
  introduced.
- The command surface remains stable unless explicitly changed in this
  workstream document.
- `AGENTS.md` and `CLAUDE.md` include the CLI adapter discipline.
- Targeted CLI tests pass after each phase.
- Full logged `tests/` run is green before the workstream is declared complete,
  unless Q explicitly defers the full-suite verification.

## Red flags

- Moving code from `propstore.cli` into a generic dumping-ground module.
- Adding a `*_workflows.py` file without naming its request, report/result, and
  failure types in the module docstring or nearby type definitions.
- Returning untyped dicts from new owner-layer APIs where a domain object is
  practical.
- Keeping old and new production paths alive in parallel.
- Adding a facade that still lets CLI-only code own the real behavior.
- Treating formatting as logic. Presentation can stay in CLI; policy,
  selection, mutation, and query semantics cannot.

## Review checks

- `rg -n -F "import click" propstore` finds no owner-module imports introduced
  by this workstream.
- `rg -n -F "sys.exit" propstore` finds no owner-module exits introduced by
  this workstream.
- New owner-layer APIs return dataclasses or existing domain objects, not loose
  dicts, unless the owner module is explicitly at an IO boundary.
- Render workflows accept `RenderPolicy`; they do not reconstruct it from CLI
  flag-shaped inputs.
- Each phase reports both the CLI-output tests and owner-layer tests that
  passed.
