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

- This commit: `refactor(grounding): type budget completeness evidence`

Next slice:

- B1 Slice 2 after every Slice 1 gate passes and this iteration is committed.
