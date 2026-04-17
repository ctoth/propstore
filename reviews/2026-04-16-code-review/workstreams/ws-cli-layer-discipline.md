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

### Phase CLI-5 - Worldline, grounding, micropub, history extraction

- Move worldline definition/request construction and materialization reporting
  into `propstore.worldline.workflows`.
- Move grounding inspection into `propstore.grounding.inspection`.
- Move micropublication traversal and lift query behavior out of CLI.
- Move log classification/merge summary/diff/show/checkout report generation
  into storage/repository owner modules.

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
