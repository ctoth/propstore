# Grounding Completeness Cleanup Fixed-Point Log - 2026-07-22

Target architecture:

- `RepositoryConfigDocument` owns repository-resident grounding configuration.
- `GroundedRulesBundle` is the sole typed grounding-result owner.
- The selected argument limit reaches Gunray without a loose status or result DTO.
- Later slices derive the bundle from canonical sidecar charter documents and
  fail closed at incomplete ASPIC consumers.

Forbidden surfaces:

- raw `grounded_fact` result storage and `propstore.grounding.sidecar`;
- loose string grounding status;
- CLI-local repository re-grounding;
- missing-capability substitution with `GroundedRulesBundle.empty()`;
- incomplete grounding entering ASPIC projection or committed worldlines.

Search gates:

- `rg -n "create_grounded_fact_table|populate_grounded_facts|read_grounded_facts|grounded_fact" propstore tests`
- `rg -n "def _load_grounding_repo" propstore`
- `rg -n 'build_grounded_bundle\(' propstore/cli`
- `rg -n "GroundingSurfaceState|grounding_surface_state" propstore tests`
- `rg -n "else GroundedRulesBundle.empty" propstore`
- `rg -n 'status: str = "complete"' propstore/grounding`
- `rg -n 'status="complete"|status="budget_exceeded"' propstore/grounding`
- `rg -n "def grounding_bundle" propstore/world/model.py`
- `rg -n "def load_grounded_bundle_from_sidecar" propstore`

Runtime gates:

- Each B1 slice uses its exact logged pytest command from
  `plans/unwired-and-missing-code-convergence.md`.
- Each B1 slice runs `uv run pyright propstore`; Slices 2 and 4 also run
  `uv run lint-imports`.
- Final B1 runs the combined focused suite, Pyright, import-linter, Ruff check,
  Ruff format check, and the full logged pytest suite.

## Iteration 1 - `B1 Slice 1`

Slice read:

- `propstore/repository.py`
- `propstore/grounding/bundle.py`
- `propstore/grounding/grounder.py`
- `propstore/grounding/loading.py`
- focused repository and grounding tests named by the active plan

Surfaces:

- `Repository.config -> dict[str, TaggingAuthority]`
  - Disposition: rewrite
  - Owner after cleanup: `RepositoryConfigDocument`
  - Action: return the typed document, add the positive optional budget, and add
    the commit-aware `Repository.config_at()` owner method.
  - Evidence: the current property decodes the typed document and immediately
    erases it to a one-field dict.
- `GroundedRulesBundle.status: str`
  - Disposition: rewrite
  - Owner after cleanup: `GroundingStatus` in `propstore.grounding.bundle`
  - Action: replace string construction with enum members and preserve selected
    budget plus Gunray candidate-count evidence.
  - Evidence: only `complete` and `budget_exceeded` are defined outcomes.
- `build_grounded_bundle()` dropping `max_arguments`
  - Disposition: rewrite
  - Owner after cleanup: existing `propstore.grounding.loading` workflow
  - Action: extend its owner interface and pass the value to `ground()` or the
    typed empty bundle.
  - Evidence: `ground()` already owns and accepts `max_arguments`.

Gate results:

- Pass: `powershell -File scripts/run_logged_pytest.ps1 tests/test_repository.py tests/test_uri.py tests/test_uri_authority_validation.py tests/test_grounder_budget_exceeded.py tests/test_grounder_default_returns_arguments.py tests/test_grounding_loading.py -q`
  - 44 passed in 8.53s.
  - Log: `logs/test-runs/pytest-20260722-121756.log`.
- Pass: `rg -n 'status: str = "complete"|status="complete"|status="budget_exceeded"' propstore/grounding`
  - Zero hits.
- Pass: `rg -n 'config\.get\("uri_authority"\)|def config\(self\) -> dict' propstore tests`
  - Zero hits.
- Pass: `uv run pyright propstore`
  - 0 errors, 0 warnings, 0 informations.

Commit:

- `cdc0085f refactor(grounding): type budget completeness evidence`

Next slice:

- B1 Slice 2 after every Slice 1 gate passes and this iteration is committed.

## Iteration 2 - `B1 Slice 2`

Slice read:

- `propstore/grounding/sidecar.py`
- `propstore/derived_build.py`
- `propstore/derived_schema.py`
- `propstore/families/registry.py`
- `propstore/grounding/loading.py`
- `tests/test_sidecar_grounded_facts.py`
- `tests/test_world_sidecar_grounded.py`
- focused schema, registry, pass, and manifest tests named by the active plan

Surfaces:

- `propstore.grounding.sidecar` and raw `grounded_fact` storage
  - Disposition: delete
  - Owner after cleanup: no persisted grounding result; runtime
    `GroundedRulesBundle` derives from canonical charter inputs.
  - Action: deleted the whole production file, its boundary-contract test, all
    imports/calls, and the one-line `_load_grounding_repo()` wrapper.
  - Evidence: no production reader existed and the rows could not reconstruct
    Gunray inspection.
- selected grounding build configuration
  - Disposition: move to the correct owner
  - Owner after cleanup: derived-only `GroundingBuildConfiguration` charter.
  - Action: added one singleton config row, commit-pinned resolution, cache-key
    input, registry/version changes, and regenerated manifest.
  - Evidence: sidecar-only readers require the selected limit, but status and
    result objects remain runtime bundle state.
- old raw-table build tests
  - Disposition: rewrite
  - Owner after cleanup: charter/schema and typed sidecar-loader contracts.
  - Action: replaced SQL grounded-row assertions with config-row, historical
    commit, cache identity, and full typed bundle equivalence tests.
  - Evidence: these tests represented a still-valid production capability but
    through the wrong storage representation.
- typed sidecar grounding reconstruction
  - Disposition: move to the correct owner
  - Owner after cleanup: `load_grounded_bundle_from_sidecar()` in
    `propstore.grounding.loading`.
  - Action: reconstruct canonical documents directly from charter models,
    require one config row, and build the full arguments/inspection bundle.
  - Evidence: both compiler reports and `WorldQuery` need the same
    grounding-specific typed boundary; no generic adapter or new protocol is
    needed.

Gate results:

- Pass: `uv run pks contract-manifest --write`
  - Rewrote the checked manifest from the charter registry.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 tests/test_derived_build.py tests/test_world_sidecar_grounded.py tests/test_semantic_family_registry.py tests/test_semantic_passes.py tests/test_contract_manifest.py -q`
  - 42 passed in 7.47s.
  - Log: `logs/test-runs/pytest-20260722-122509.log`.
- Pass: `rg -n "create_grounded_fact_table|populate_grounded_facts|read_grounded_facts|grounded_fact" propstore tests`
  - Zero hits.
- Pass: `rg -n "def _load_grounding_repo" propstore`
  - Zero hits.
- Pass: `rg -n "def load_grounded_bundle_from_sidecar" propstore`
  - Exactly one hit at the grounding owner.
- Pass: `uv run lint-imports`
  - 3 contracts kept, 0 broken.
- Pass: `uv run pyright propstore`
  - 0 errors, 0 warnings, 0 informations.

Commit:

- This commit: `refactor(grounding): derive bundles from canonical sidecar`

Next slice:

- B1 Slice 3 after every Slice 2 gate passes and this iteration is committed.

## Iteration 3 - `B1 Slice 3`

Slice read:

- `propstore/world/model.py`
- `propstore/compiler/workflows.py`
- `propstore/cli/compiler_cmds.py`
- `propstore/cli/grounding_cmds.py`
- `propstore/grounding/inspection.py`
- focused world, sidecar, grounding CLI, and compiler-rendering tests named by
  the active plan

Surfaces:

- missing concrete `WorldQuery.grounding_bundle()` implementation
  - Classification: already-owned capability that must use its true owner
    directly.
  - Disposition: implement the existing `GroundingBundleStore` protocol method
    and memoize the result loaded from the held typed sidecar session.
  - Evidence: both repository-backed and handle-only construction already
    converge on the same `DerivedSession`; no new protocol or adapter is needed.
- build report without the canonical grounding result
  - Classification: valid capability with the wrong representation boundary.
  - Disposition: carry `GroundedRulesBundle` directly and load it from the
    materialized sidecar through the same grounding-owned typed loader.
  - Evidence: a status DTO would duplicate the bundle's completeness evidence.
- CLI-local `load_grounding_repo()` plus `build_grounded_bundle()` path
  - Classification: valid capability in the wrong caller path.
  - Disposition: rewrite every grounding command to inspect
    `open_app_world_model(repo).grounding_bundle()` and delete the old imports
    and calls.
  - Evidence: CLI presentation must inspect the production sidecar result, not
    independently re-ground authored repository files.
- `GroundingSurfaceState` / `grounding_surface_state()` and old state tests
  - Classification: dead/test/scaffold surface after the production cutover.
  - Disposition: delete the type, function, imports, and assertions; invalid
    programs fail through the grounding owner and existing CLI failure mapper.
  - Evidence: complete versus budget-exceeded is already typed on the canonical
    bundle, while missing predicates with rules raises the owner `ValueError`.

Gate results:

- Pass: `powershell -File scripts/run_logged_pytest.ps1 tests/test_world_query.py tests/test_world_sidecar_grounded.py tests/test_cli_phase10_advanced.py tests/test_cli_compiler_rendering.py -q`
  - 65 passed in 10.53s.
  - Log: `logs/test-runs/pytest-20260722-123311.log`.
- Pass: `rg -n 'build_grounded_bundle\(' propstore/cli`
  - Zero hits.
- Pass: `rg -n "GroundingSurfaceState|grounding_surface_state" propstore tests`
  - Zero hits.
- Pass: `rg -n "def grounding_bundle" propstore/world/model.py`
  - Exactly one production implementation.
- Pass: `rg -n "def load_grounded_bundle_from_sidecar" propstore`
  - Exactly one grounding-owned typed loader implementation.
- Pending by plan until Slice 4:
  `rg -n "else GroundedRulesBundle.empty" propstore` finds only the classified
  fragility fallback at `propstore/fragility.py`; Slice 3 did not cross that
  consumer boundary.
- Pass: all other B1 deleted-result, deleted-wrapper, and loose-status searches
  returned zero hits.
- Pass: `uv run pyright propstore`
  - 0 errors, 0 warnings, 0 informations.

Commit:

- This commit: `feat(grounding): wire production bundle inspection`

Next slice:

- B1 Slice 4 only after every Slice 3 gate passes and this iteration is
  committed.

## Iteration 4 - `B1 Slice 4`

Slice read:

- `propstore/world/resolution.py`
- `propstore/worldline/argumentation.py`
- `propstore/worldline/result_types.py`
- `propstore/app/worldlines.py`
- `propstore/fragility.py`
- `propstore/fragility_types.py`
- focused resolution, worldline, hashing, fragility, and CLI tests named by the
  active plan

Surfaces:

- ASPIC projection without a completeness guard
  - Classification: valid capability with wrong representation handling.
  - Disposition: inspect the existing bundle status before projection and
    return no winner with the exact budget reason when it is incomplete.
  - Evidence: partial Gunray evidence is diagnostic input, not a complete
    structured theory.
- ASPIC worldline capture projecting an incomplete bundle
  - Classification: valid capability with wrong representation handling.
  - Disposition: return the existing typed argumentation state with exact
    `grounding_budget_exceeded` status and reason before projection.
  - Evidence: diagnostic `run_worldline()` must remain inspectable without
    treating partial grounding as accepted argumentation output.
- worldline materialization assigning and saving incomplete ASPIC results
  - Classification: wrong caller accepting an incomplete owner result.
  - Disposition: raise `WorldlineValidationError` immediately after the run and
    before assigning `definition.results` or saving.
  - Evidence: committed worldlines are complete semantic artifacts.
- fragility `else GroundedRulesBundle.empty()` fallback
  - Classification: wrong caller hiding absent/incomplete capability.
  - Disposition: delete the substitution; require `GroundingBundleStore` only
    when grounding or bridge analysis is requested.
  - Evidence: a fabricated empty bundle is indistinguishable from a complete
    empty program and falsely authorizes ranking.
- fragility result without grounding completeness evidence
  - Classification: valid capability with wrong representation.
  - Disposition: add the exact status/reason fields to the existing
    `FragilityReport`; skip grounding and bridge collectors for incomplete
    bundles while preserving other enabled families.
  - Evidence: no separate report or generic status owner is needed.

Gate results:

- Pass: `powershell -File scripts/run_logged_pytest.ps1 tests/test_resolution.py tests/test_app_worldlines.py tests/test_worldline_hash_excludes_transient_errors.py tests/test_fragility.py tests/test_cli_phase10_advanced.py -q`
  - 94 passed in 8.63s.
  - Log: `logs/test-runs/pytest-20260722-124235.log`.
- Pass: the real tiny-budget integration proof uses one committed sidecar for
  ASPIC resolution, diagnostic worldline capture, fragility completeness, and
  the no-worldline-commit materialization refusal; each reports the same exact
  owner reason.
- Pass: every B1 search gate.
  - Deleted result storage, deleted wrapper, CLI-local re-grounding, obsolete
    surface classifier, fragility empty fallback, and loose status construction
    all returned zero hits.
  - Exactly one production `WorldQuery.grounding_bundle()` and one grounding
    owner `load_grounded_bundle_from_sidecar()` remain.
- Pass: `uv run lint-imports`
  - 3 contracts kept, 0 broken.
- Pass: `uv run pyright propstore`
  - 0 errors, 0 warnings, 0 informations.

Commit:

- This commit: `fix(argumentation): fail closed on incomplete grounding`

## B1 final verification

- Pass: final combined focused gate after all four semantic commits.
  - 227 passed in 15.11s.
  - Log: `logs/test-runs/pytest-20260722-124416.log`.
- Pass: repository formatter applied to the 10 B1-touched files and left 633
  files unchanged.
- Pass: final combined focused gate after formatting.
  - 227 passed in 14.18s.
  - Log: `logs/test-runs/pytest-20260722-124608.log`.
- Pass: full logged suite after formatting.
  - 1820 passed, 1 skipped in 86.33s.
  - Log: `logs/test-runs/pytest-20260722-124640.log`.
- Pass: `uv run pyright propstore` with 0 errors.
- Pass: `uv run lint-imports` with 3 contracts kept and 0 broken.
- Pass: `uv run ruff format --check .` with all 643 files formatted.
- Blocked outside B1 scope: `uv run ruff check .` reports 72 findings in
  unrelated pre-existing review scripts, utility scripts, older revision tests,
  and a workstream note. None of the reported paths is a B1-touched file; those
  unrelated files were not mutated under B1 authority.
