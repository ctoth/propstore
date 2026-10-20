# Code wiring audit

## Scope

- Read-only audit requested on 2026-07-17.
- Evidence source is current Python implementation and tests only; plans, reports,
  existing notes, and memory are excluded.
- No production or test code has been changed.

## Current repository state

- Branch: `master`, two commits ahead of `origin/master` at audit start.
- Pre-existing untracked path: `pyghidra_mcp_projects/`.
- This handoff file was added only because the repository checkpoint required an
  accepted `notes-*.md` update before continuing.

## Findings so far

- The root CLI is a lazy registry in `propstore/cli/__init__.py`; world, worldline,
  source, proposal, predicate, rule, and read-view command families are registered.
- The old skipped ATMS-resolution test is stale as a wiring indicator: production
  resolution dispatches to `_resolve_atms_support`, and `BoundWorld` exposes
  `atms_engine()` through the required protocol.
- ASPIC projection is no longer merely a pure projection fragment:
  `build_aspic_projection` reads stances/justifications and is called by world
  resolution and worldline argumentation capture.
- Predicate authoring has a complete owner API in
  `propstore/grounding/authoring.py` (`add/list/show/remove`), but production CLI
  adapters bypass it for reads and use a separate proposal path for declaration;
  `remove_predicate` has no production caller found so far.
- The claim charter stores `value` as `float | None`, while `ActiveClaim` permits
  `float | str | None`; the skipped categorical-provider test says the ATMS
  rejection behavior exists but cannot be driven through canonical authoring.
- PrAF analysis and resolution are wired, but the skipped enumeration-budget test
  identifies no Propstore consumer path for the upstream argument-enumeration
  budget/result status.
- Fragility has implemented grounding-family collectors, but their end-to-end
  skip markers are stale as a broad wiring claim: the build loads canonical
  predicates/rules/superiorities/claims/concepts, grounds them, stores grounded
  facts, and the CLI fragility path calls the grounding and bridge collectors.
- The embedding/NLI relation stack is largely implemented in
  `propstore/heuristic/classify.py` and `propstore/heuristic/relate.py`, including
  async bidirectional classification, pair discovery, deduplication, calibration,
  and batch orchestration. It has no production caller and no concrete production
  implementation of `ClaimRelationStore`; the only implementation found is a test
  stand-in.
- Predicate LLM extraction is implemented and tested in
  `propstore/heuristic/predicate_extraction.py` but has no CLI/app/source caller.
  Rule extraction does have a CLI adapter, but its real no-fixture LLM boundary is
  still `_llm_call`, which always raises; only fixture-driven execution works.
- The web repository overview is deliberately incomplete in production code:
  provenance summary, recent activity, and notable conflicts are returned as
  hard-coded `NOT_IMPLEMENTED` sections even though history, conflict, and
  provenance primitives exist elsewhere.
- Semantic neighborhoods implement only claim focus. Concept/source/worldline
  focus raises immediately; even claim focus hard-codes assumption traversal and
  policy alternatives as unavailable and claim provenance as missing rather than
  connecting ATMS/provenance/policy subsystems.
- PrAF construction, analysis, world resolution, and worldline capture are wired.
  What is absent is budget-result propagation: `AnalyzerResult` has no explicit
  status/partial-result field, and `analyze_praf` does not accept or surface an
  argument-enumeration budget.

## Next action

- The preliminary audit has been delivered. The user has now requested formal
  planning and revalidation of every candidate, including checking whether any
  supposedly missing capability already exists under another owner.
- Use the `protocols:researcher` workflow: create bounded research prompts,
  dispatch independent researcher actors without inherited context, collect
  code-backed reports under `docs/reports/`, then synthesize one repo-local plan.
- Research groups: relation/classification/calibration/predicate extraction;
  verification/web/neighborhood/secondary owner surfaces; canonical value
  representation/PrAF budget/stale deferred markers.
- No implementation is authorized in this phase. Only research prompts, reports,
  this required handoff, and the final plan are in scope.

## Research dispatch status

- Ward is not installed and, by explicit user instruction, must not be invoked,
  inspected, configured, or treated as a dependency.
- Three isolated research actors have been dispatched from the physical prompts:
  relation/calibration/extraction; verification/views/owners; and canonical
  values/PrAF/stale gaps.
- Each actor is restricted to its requested `docs/reports/*.md` artifact and must
  revalidate preliminary audit claims against current code and tests.
- Current blocker: none after this centrally handled checkpoint update.
- Next action: collect all three code-backed reports, synthesize their agreements
  and disagreements, then write one implementation plan with invalid/already-built
  items removed and dependency-ordered slices and gates.

## Research completion checkpoint

- All three requested reports now exist under `docs/reports/` and are based on
  current code/tests rather than plans or historical notes.
- Relation research confirmed existing production similarity and complete
  stance/predicate/rule proposal owners; missing work is the typed relation
  orchestration edge, calibration authorities/injection, classifier-to-proposal
  recording, and real extraction model calls.
- Verification/view research completed its owner/caller map and is ready for
  synthesis; direct mutation surfaces must be rejected where source-owned paths
  already own the capability.
- Value/status research separated canonical scalar authoring/storage from already
  scalar-capable runtime code, and separated grounding, ASPIC, PrAF, and ATMS
  completeness/budget mechanisms rather than treating them as one gap.
- Current blocker: the initial combined report read was truncated by the output
  window. This is not a research blocker; each report will be read individually.
- Next action: read each completed report in full, reconcile recommendations and
  open decisions, then create the single repo-local implementation plan requested
  by the user.

## Execution kickoff checkpoint

- The user selected the most important planned work for execution. The selected
  capability is canonical scalar value convergence because it is the foundation
  for categorical and boolean canonical authoring and the existing ATMS/runtime
  scalar consumers.
- The repo-local plan remains the execution control surface. Its Phase 0 stale-
  premise corrections must be completed before Workstream A feature changes.
- `protocols:cleanup-refactor` is the active deletion-first control surface for
  Phase 0 and all resulting caller classification and disposition work.
- Ward is explicitly prohibited and remains entirely out of scope.
- Current blocker: none. The cleanup protocol read was truncated and is being
  completed in bounded chunks before branch inspection or source mutation.
- Next action: finish reading the cleanup protocol through EOF, then verify Git
  branch/dirty state and begin the first bounded Phase 0 vertical slice.

## Phase 0 iteration 1 checkpoint - ATMS resolution scaffold

- Git accountability baseline: `master` is three commits ahead of
  `origin/master`; tracked files are clean. The active convergence plan is
  untracked, and the unrelated untracked `pyghidra_mcp_projects/` tree will not
  be touched.
- Active slice: the skipped `test_atms_support_resolution` symbol at the end of
  `tests/test_resolution.py` and the production dispatch it claims is absent.
- Ownership classification: the skipped symbol is dead test scaffold. Its
  stated prerequisite is invalid because `propstore.world.resolution` already
  owns `_resolve_atms_support()` and dispatches the ATMS backend through it.
- Disposition: delete the skipped scaffold. A real replacement test is justified
  because current tests cover ATMS engine support and `BoundWorld.value_of()`,
  but no test drives `resolve()` through `ReasoningBackend.ATMS` and asserts its
  winner/reason result.
- Target owner: the existing `resolve()` plus `BoundWorld`/`ATMSEngine` path;
  no helper, adapter, alias, or replacement production surface is needed.
- Current blocker: none.
- Next action: commit the accepted execution plan as the Git control ledger,
  then rewrite this one test symbol to exercise the existing production path,
  run its focused logged gate, and commit the kept slice before continuing.

## Phase 0 iteration 1 result - ATMS resolution scaffold

- The convergence plan was committed alone as `c866d8d5` so it is now the Git-
  tracked execution ledger.
- The attempted real replacement test proved the winner-dispatch premise wrong:
  `BoundWorld.value_of()` applies ATMS support before `resolve()`, so the real
  fixture becomes `DETERMINED` and never enters resolution dispatch. The failed
  focused run is recorded at
  `logs/test-runs/pytest-20260717-152500.log`.
- Disposition finalized as **delete**: the skipped test scaffold and stale module
  prose were removed; the experimental import and test body were fully removed.
- Search gate passed with zero hits for the stale skip reason, test name, and
  deferred ATMS strategy wording.
- Runtime gate passed: all 24 tests in `tests/test_resolution.py` passed through
  the logged wrapper. Evidence:
  `logs/test-runs/pytest-20260717-152550.log`.
- Kept reduction committed as `7447d07f` (`Delete obsolete ATMS resolution
  scaffold`).
- Current blocker: none.
- Next action: reread the plan, then open the bounded ASPIC prose slice that
  incorrectly says `build_aspic_projection` is absent; classify and correct only
  that invalid premise, gate it, and commit it before continuing.

## Phase 0 iteration 2 result - ASPIC projection prose

- Active surface: the `propstore.aspic_bridge.projection` module docstring.
- Classification: production-module documentation in the correct owner file;
  the described entrypoint already exists in that same file and is consumed by
  resolution and worldline owners.
- Disposition: **rewrite** the false deferred/absent description to state the
  existing store and active-graph behavior. No production symbol or caller was
  added, deleted, moved, or wrapped.
- Search gate passed with zero stale deferred-entrypoint phrases.
- Runtime gate passed: the store-backed projection, resolution dispatch, and
  revision adapter tests all passed (4 tests). Evidence:
  `logs/test-runs/pytest-20260717-152803.log`.
- The tracked plan item is checked and the slice is committed as `cc816e86`
  (`Correct stale ASPIC projection premise`).
- Current blocker: none.
- Next action: reread the plan and inspect the bounded relation prose that claims
  reverse distances survive classification; prove current forward/reverse data
  flow, correct the false premise only, gate it, and commit the slice.

## Phase 0 iteration 3 result - directional distance prose

- Active surface: the module-level contract in
  `propstore.heuristic.relate`.
- Proven flow: pair deduplication retains forward and reverse distances and both
  enter the reference-distance pool, but `relate_all_async()` passes only
  `forward_dist` to `classify_stance_async()`, which supplies it to both generated
  directions. Direction-specific perspective ids remain distinct.
- Classification: wrong production prose in the correct orchestration owner.
  Disposition: **rewrite** the prose only; Workstream C remains responsible for
  changing the typed classifier data flow later.
- Search evidence retains the visible production edge
  `embedding_distance=forward_dist` and removes the false survival claim.
- Runtime gate passed: deduplication, directional LLM calls, and perspective
  isolation all passed (10 tests). Evidence:
  `logs/test-runs/pytest-20260717-152943.log`.
- The tracked plan item is checked and the slice is committed as `ebb01286`
  (`State current directional distance flow`).
- Current blocker: none.
- Next action: reread the plan and open the grounding/fragility prose slice;
  prove the current non-empty authoring/build path, correct only false claims,
  gate it, and commit before touching the placeholder-test slice.

## Phase 0 iteration 4 result - grounding and fragility prose

- Active surfaces: the module contract and predicate-decode docstring in
  `propstore.fragility_contributors`.
- Proven owner path: `load_grounding_repo()` reads typed authored families,
  `build_grounded_bundle()` produces non-empty sections and arguments, and
  `rank_fragility()` consumes the store's grounded bundle.
- Classification: wrong production prose in the existing collector owner.
  Disposition: **rewrite** the false absence/deferred claims while preserving the
  real limitation that undecorated section predicate ids use a positive-only
  decode because the complement encoder is absent.
- Search gate passed with no false non-empty-grounding deferred phrases in the
  production module.
- Runtime gate passed: all 3 grounding-loading tests, including a non-empty
  authored bundle, passed. Evidence:
  `logs/test-runs/pytest-20260717-153134.log`.
- The tracked plan item is checked and the slice is committed as `a982c8b8`
  (`Correct grounded fragility authoring premise`).
- Current blocker: none.
- Next action: drive each existing grounding/bridge fragility collector from a
  real non-empty production bundle, then delete the three skipped placeholder
  classes, run focused fragility/grounding gates, and commit that slice.

## Phase 0 iteration 5 result - fragility collector coverage

- Broken surfaces: the three skipped empty grounding, grounded-rule, and bridge-
  undercut test classes plus their obsolete module note.
- Classification: dead test scaffolds for capabilities already owned by the
  typed grounding and fragility collector modules. Disposition: **delete** the
  scaffolds, then **rewrite** coverage to call the existing owners directly.
- A real non-empty bundle built by `ground()` from typed `DefeasibleRule` values,
  facts, and a proper defeater now drives
  `collect_ground_fact_interventions()`,
  `collect_grounded_rule_interventions()`, and
  `collect_bridge_undercut_interventions()`.
- Search gate passed with zero old class names, deferred authoring messages, or
  nonexistent `families.documents.rules` references in the test module.
- Focused gate passed first (1 test), then the complete fragility and grounding-
  loading gate passed (30 tests). Evidence:
  `logs/test-runs/pytest-20260717-153350.log` and
  `logs/test-runs/pytest-20260717-153414.log`.
- The tracked plan item is checked and the slice is committed as `99d04118`
  (`Replace grounded fragility placeholders`).
- Current blocker: none.
- Next action: reread the plan and locate stale embedding-deferred labels; retain
  only genuine optional `sqlite_vec` skips, run focused embedding gates, and
  commit that bounded cleanup slice.

## Phase 0 iteration 6 result - embedding labels

- Active surfaces: the `tests/test_world_query.py` module contract and embedding
  section label.
- Classification: stale test prose around valid honest-empty cases. The indexed
  production path already has separate optional-dependency coverage.
- Disposition: **rewrite** the two deferred labels to distinguish a fixture with
  no index from indexed behavior. The three genuine
  `pytest.importorskip("sqlite_vec")` gates remain unchanged in CLI, similarity,
  and web tests.
- Search gate passed with zero embedding-deferred labels and confirmed all three
  optional gates still exist.
- Runtime gate passed: honest-empty world queries and indexed embedding behavior
  passed (9 tests). Evidence:
  `logs/test-runs/pytest-20260717-153535.log`.
- The tracked plan item is checked and the slice is committed as `e4ab130b`
  (`Remove stale embedding deferral labels`).
- Current blocker: none.
- Next action: reread the plan and inspect the PrAF/grounding skipped-test text;
  prove the owner-side budget behavior that exists, name only the missing
  Propstore propagation seam, gate it, and commit the final Phase 0 item.

## Phase 0 iteration 7 result and Workstream A blocker

- Proven owner behavior: `ground()` already captures argument-enumeration
  overflow as a `GroundedRulesBundle` with `status="budget_exceeded"`, partial
  arguments, inspection, and reason. The focused owner test passes.
- Missing seam: `build_grounded_bundle()` and production build/analysis callers
  do not accept `max_arguments`, and Propstore analysis/PrAF-facing results do
  not expose the incomplete bundle status.
- Classification: the skip is a valid future production-boundary contract, but
  its reason/docstring/sentinel text misstated the missing edge. Disposition:
  **rewrite** those descriptions and keep the skip.
- Runtime gate passed with the owner budget test passing and the future contract
  remaining skipped. Evidence:
  `logs/test-runs/pytest-20260717-153722.log`.
- The Phase 0 package type gate passed: `uv run pyright propstore` reported 0
  errors and 0 warnings.
- The final Phase 0 item is checked and committed as `d818c34a` (`Name the
  grounding budget propagation seam`). All seven Phase 0 items are now checked.
- Current blocker: Workstream A1 begins with `Resolve Q1`, and the plan explicitly
  states this semantic authority is not safe to infer. Required user decisions:
  the exact canonical scalar set; tagged JSON versus discriminator plus typed
  columns; and whether standalone LinkML/JSON schemas remain supported contracts.
- Next action after user direction: encode the approved Q1 contract as the first
  Workstream A vertical slice, beginning with source-to-world round-trip tests.

## Q1 recommendation review checkpoint

- The user requested recommendations and rationale for all three Q1 decisions;
  this review is read-only and Ward remains out of scope.
- Current source and canonical claim owners both declare `value: float | None`,
  while existing runtime/domain paths already accept string values and grounding
  terms already preserve `str | int | float | bool`.
- Recommended scalar set is `str | bool | int | float`, with `None` representing
  absence. Boolean must be tested before integer in any runtime narrowing because
  Python `bool` subclasses `int`; direct-value paths must preserve integer rather
  than normalize it to float.
- Quire maps ordinary multi-type unions to a TEXT column by default, which cannot
  itself prove round-trip scalar identity. A Quire-owned JSON boundary stores and
  decodes the annotated type through its charter-derived column and avoids a
  second hand-maintained discriminator/typed-column schema.
- No production or test consumer was found for the packaged standalone claim JSON
  schema. The LinkML source still declares claim `value` as numeric-only, is a
  manually maintained second claim schema, and generates the packaged JSON file.
  Current source decoding, charters, sidecar validation, and contract manifests
  derive from typed owners instead.
- Current recommendation direction: four JSON scalar classes; one Quire-owned
  type-preserving JSON column rather than discriminator plus four nullable typed
  columns; retire the standalone Claim LinkML/JSON schema unless an external
  consumer can be named.
- Current blocker: none for answering the recommendation question. The actual A1
  implementation remains blocked until the user chooses the contract.
- Next action: finish checking whether sidecar SQL performs value-specific queries,
  then present the three recommendations, tradeoffs, and implementation effect.

## Q1 decision approved for capture

- The user approved the recommended scalar/storage/schema package and explicitly
  instructed that it be captured now.
- Approved Propstore semantic contract: `str | bool | signed-int64 | finite-
  float64`; `None` means absence. Boolean is not an integer for validation or
  runtime routing.
- Approved owner split: Propstore owns scalar semantics; Quire owns a generic
  charter-derived MessagePack BLOB codec. Present values are encoded; absence is
  SQL `NULL`.
- MessagePack bytes are derived sidecar projection state and must not become
  artifact identity or hash input.
- The standalone Claim LinkML source and generated/package JSON schemas are to be
  retired as supported contracts. CBOR is reserved only for a future durable
  external wire format; Protobuf and ASN.1 are rejected for this boundary.
- Current blocker: none.
- Next action: finish reading `protocols:spec-updating`, verify branch/dirty state,
  replace Q1's open decision block in the tracked convergence plan with this dated
  decision, verify the scoped diff, and commit it.

## Q1 decision capture result

- `protocols:spec-updating` was read but could not be applied cleanly: it mandates
  Ward-mediated review actors, while Ward is explicitly prohibited, and it is
  designed for formal spec-directory changes rather than this approved execution-
  plan decision. No Ward, subagent, Gemini, or substitute review path was used.
- The existing Q1 recommendation/open-question block was replaced with the dated
  2026-07-18 decision covering scalar widths, finite floats, owner boundaries,
  MessagePack BLOB/SQL NULL storage, identity exclusions, forbidden parallel
  representations, Claim schema retirement, and the CBOR/Protobuf/ASN.1
  disposition.
- Only the existing `Resolve Q1` checkbox was checked. No A1 implementation item
  was marked complete.
- The scoped markdown diff passed `git diff --check` and was committed as
  `85701896` (`Decide canonical scalar storage contract`).
- Current blocker: none for decision capture.
- Next action under the active plan: begin A1 with source-to-world scalar round-
  trip tests, then change source/canonical claim values and the Quire-owned codec
  in their required owner order.
