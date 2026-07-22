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
