# Values, PrAF, and stale-gap research checkpoint

## Current findings

- The controlling research prompt has been read in full.
- The active branch is `master`.
- The pre-existing worktree contains unrelated untracked `pyghidra_mcp_projects/` artifacts; this research will not touch them.
- Relevant current-code surfaces have been inventoried across claim families, compiler, grounding, PrAF, ASPIC, ATMS, world/worldline, analyzers, CLI, and their tests.
- Canonical `Claim.value` and its charter-derived sidecar row remain `float | None` (`propstore/families/claims.py`), and source `SourceClaimDocument.value` is also `float | None` (`propstore/families/sources.py`).
- Source promotion rebuilds canonical claims and runs them through the shared claim semantic pipeline; it does not introduce a broader scalar representation.
- Runtime `ActiveClaim.value`, `ResolvedResult.value`, and `SyntheticClaim.value` accept `float | str | None`, while world bindings accept `str | int | float | bool`; this already exposes a representation mismatch between authoring/storage and runtime.
- `world.model._as_scalar` currently stringifies booleans and normalizes integers to floats for chain/value projection, despite bindings preserving bool/int in `Environment`.
- Claim validation runs type contracts, CEL conditions, and context checks but has no scalar-kind/value-form compatibility check; source-only bounds validation assumes every claim value is numeric.
- The world value resolver already compares direct string values for equality/conflict (`float | str | None`), while excluding booleans and restricting parameterization derivation/known-value collection to numeric values. Thus categorical direct resolution exists at runtime, but authoring cannot reach it.
- `ValueResult` exposes status and claims rather than a scalar field; `DerivedResult` remains numeric-only by design, whereas `ResolvedResult` is `float | str | None`.
- Grounding already owns a `GroundedRulesBundle` with `status` (`complete` or `budget_exceeded`) and `budget_reason`; `build_grounded_bundle` calls the real grounding owner and can request argument enumeration.
- PrAF's own COH iteration cap is separate: hard mode raises `COHDivergenceError`, while `soft=True` returns `EnforceCohResult(converged=False, iterations, max_violation)`. This is not gunray argument-enumeration status.
- The analyzer PrAF path delegates acceptance computation to the argumentation package and maps its query/strategy/sample/interval fields into analyzer details; its handling of package-level budget/partial status still needs exact caller verification.
- `ground()` already accepts `max_arguments`, catches `gunray.EnumerationExceeded`, and returns partial arguments/inspection with `status="budget_exceeded"`; focused tests cover it.
- `build_grounded_bundle()` does not accept or pass `max_arguments`, so repository build, CLI, ASPIC construction, and analyzer flows cannot set that budget through their normal owner path. The old statement that the low-level path is wholly absent is stale, but the production propagation gap is real.
- Grounded-fact sidecar population writes only marking sections; it does not persist grounding status, budget reason, partial arguments, or inspection. CLI argument/status rendering likewise does not surface the bundle's budget fields.
- ASPIC `project_grounded_rules` accepts a bundle whenever `grounding_inspection` exists and ignores `bundle.status`/`budget_reason`; therefore a partial gunray inspection can be treated as a complete ASPIC theory.
- ASPIC full-build and `ClaimQueryResult` types contain arguments/attacks/defeats but no completeness or budget status. Goal-directed ASPIC has a separate `max_depth` bound whose result type also does not say whether depth cut off exploration.
- `analyze_praf` currently copies package query/strategy/sample/confidence-interval metadata but does not expose a generic result status; exact package return fields still need inspection.
- Canonical `AnalyzerResult` has no explicit status/completeness/budget field; the only possible carrier today is untyped metadata. ASPIC maps its package `status` into extensions/metadata only indirectly, while PrAF does not map any status field.
- The pinned `formal-argumentation` and `gunray` package sources are installed under `.venv/Lib/site-packages`; they are current dependency code and can be inspected directly for exact result contracts.
- Installed `PrAFResult` has probabilities, strategy/downgrade, sample count, CI half-width, semantics, query selectors, and strategy metadata, but no status or convergence field.
- PrAF Monte Carlo stops either when its CI target is met or at a hardcoded 100,000-sample safety cap. It returns the same `PrAFResult` in both cases, so callers cannot distinguish a converged estimate from a capped partial estimate. This is the actual PrAF status gap.
- Exact enumeration and exact DP/paper-TD are separate strategies; their potentially expensive computation is not represented by the gunray budget or the COH iteration result.
- ATMS build ceilings already return inspectable partial state on the engine (`fixpoint_reached=False`, `iterations_run`, warning); dedicated tests cover it. This is separate from ATMS future-query subset budgets, which raise counted `BudgetExhausted` rather than return a guessed verdict.
- `WorldlineArgumentationState` and `ATMSEngine.to_worldline_state()` omit the engine build-completeness fields, so a partial ATMS build can still be serialized as ordinary ATMS state.
- ATMS categorical rejection behavior already exists (`PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE`); its skipped end-to-end test is legitimately blocked only by float-only claim authoring, not by missing ATMS behavior.
- `tests/test_resolution.py` still says the ATMS engine is deferred and skips an empty placeholder, even though current production ATMS engine and resolution code exist; that skip description is stale/invalid and should be deleted or replaced only if a concrete uncovered behavior is identified.
- The three skipped fragility classes are stale placeholders: ground-fact, grounded-rule, and bridge-undercut collectors are implemented and the repository has real predicate/rule authoring plus grounding/loading. A missing historical complement encoder is not proof those production paths are absent; current code explicitly uses typed grounded projection and a no-complement decode.
- `propstore/aspic_bridge/projection.py` says the store-reading `build_aspic_projection` entrypoint is deferred, but the function is implemented later in that same file and used by world/worldline resolution. The comment is invalid.
- `tests/test_world_query.py` still labels embedding similarity deferred to Phase 10, but backed `WorldQuery.similar_*` behavior and CLI end-to-end tests exist in `tests/test_embed_similar.py` and `tests/test_cli_embed.py`. The `pytest.importorskip("sqlite_vec")` gates remain valid because embeddings are an optional dependency, not missing production code.
- ATMS claim resolution is implemented in `world/resolution.py` via `HasATMSEngine` and the bound-world engine; only a non-bound view raises `NotImplementedError`. This makes the old "engine lands later" skip unequivocally stale.
- Source claim CLI and proposal APIs parse/accept only floats. Hypothetical/worldline synthetic values already accept strings in owner types, but canonical claim storage still cannot persist them; runtime trace/value carriers generally use `float | str | None`, excluding bool as a distinct result value.
- `WorldlineArgumentationState` already has a generic `status` field, but ATMS state construction leaves it unset despite engine fixpoint metadata, and PrAF capture currently uses samples/CI without a convergence status from the package.
- A scalar charter cutover affects source/canonical structs, charter-derived SQL/schema, source CLI/import contracts, promotion, active/conflict view types, and app claim view types. Direct display, hashing, grounding fact extraction, runtime equality, and worldline targets are already largely scalar-safe.
- Numeric-only consumers must stay separate and explicitly reject/bypass nonnumeric values: dimensional/value comparison, parameterization conflict derivation, propagation, sensitivity, algorithm known-value evaluation, assignment-selection merge, numeric bounds/uncertainty, and derived-result types.
- Boolean is especially inconsistent: environment/rule grounded scalars preserve it, runtime claim/result types exclude it, value resolvers explicitly reject it, and some chain code stringifies it. A user decision is needed on whether canonical bool remains distinct and whether integers are preserved or normalized as floats.
- The standalone `schema/claim.linkml.yaml` and generated `_resources/schemas/claim.schema.json` also declare numeric-only `value`, but current Python references only the generator; production claim decoding/storage is owned by the Quire `Claim` charter and its derived sidecar. Any cutover should decide whether these standalone artifacts remain supported contracts or are retired.

## State

- Research is read-only except for this authorized checkpoint note and the requested final report.
- Markdown plans, notes, reports, memory, and historical summaries are excluded as evidence.
- Ward is out of scope and will not be invoked or inspected.

## Blocker

- No research blocker remains. The actor-local notes checkpoint is being satisfied by this file under explicit parent authorization.

## Next action

- Finish exact line-evidence tracing through validation/compiler/sidecar/value comparison, then separately map gunray grounding, ASPIC, PrAF, and ATMS budget/status paths and revalidate all relevant skips/comments before writing `docs/reports/values-praf-stale-gaps.md`.
