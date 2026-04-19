Always run pytest through the logged pytest wrappers, which wrap `uv run pytest -vv` and tee the full output to a timestamped log file under `logs/test-runs/`.
Use `scripts/run_logged_pytest.ps1` from PowerShell and `scripts/run_logged_pytest.sh` from POSIX shells; both delegate to the portable implementation in `scripts/run_logged_pytest.py`.

Canonical usage:
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_init.py`
- `powershell -File scripts/run_logged_pytest.ps1 -Label artifact-store tests/test_artifact_store.py tests/test_import_repo.py`
- `sh ./scripts/run_logged_pytest.sh tests/test_init.py`
- `sh ./scripts/run_logged_pytest.sh --label artifact-store tests/test_artifact_store.py tests/test_import_repo.py`

For Pyright, check the package surface with `uv run pyright propstore`.
Do not use bare `uv run pyright` as the project gate; it also analyzes generated
schema, scripts, and tests that are not part of the configured package surface.

In this project:
- Prefer explicit domain objects over loose payloads.
- Decoded YAML/JSON/SQLite rows may be `dict` only at the IO boundary. Convert them immediately and do not pass them through the core semantic pipeline as domain objects.
- In the core pipeline, claims, concepts, sources, stances, justifications, and similar semantic objects should not be typed as `dict`/`Dict`.
- If a representation changes, do types first so the boundary is explicit before adding more behavior.
- When replacing a representation, interface, or identity surface, delete the old production path first and then fix every caller.
- Do not preserve old and new paths in parallel.
- Do not add compatibility shims, aliases, fallback readers, bridge normalizers, or dual-path glue unless the user explicitly says old repos or old data must be supported.
- Prefer a hard failure at the boundary over silently rewriting old input into the new shape.
- Source-local authoring state belongs only in the source subsystem.
- Canonical/master surfaces must reject source-local-only fields and shapes.
- Source-local readability metadata must not leak into canonical identity or canonical runtime paths.
- In this project, `legacy` is not implied by age or by yesterday's git state.
- Treat something as legacy only when explicitly told an older repo, older data surface, or compatibility target must be supported.
- Otherwise, delete the old path rather than carrying it forward.

When we control the stack, do the right thing:
- Prefer the full, principled implementation over a local approximation.
- Do not choose a weaker shortcut without explicitly discussing it first, proving it is better, and updating the plan.
- Go the extra mile when the stack can support the real design.
- Formalize toward the literature rather than away from it.
- Build the actual ambitious system the architecture enables, not a placeholder that merely looks finished.
- If we control the code on both sides of an interface, never write backwards-compatibility shims, adapters, aliases, fallbacks, or dual-path glue.
- Change the interface and update every caller.

CLI layer discipline:
- Treat `propstore.cli` as a presentation adapter only.
- CLI modules may declare Click commands/options, parse command strings into typed requests, call owner-layer functions, render typed results, and map typed failures to exit codes.
- CLI modules must not own compiler workflows, repository mutation semantics, source promotion/finalize/status semantics, world/ATMS/revision/argumentation query semantics, sidecar SQL policy, or concept/claim/form/context mutation logic.
- When CLI behavior needs reusable logic, move it to the architectural owner module, update every caller, and delete the CLI-owned production path.
- Owner-layer APIs extracted from CLI code should use typed request/report/failure objects or existing domain objects; they must not import Click, write to stdout/stderr, call `sys.exit`, or accept flag-shaped CLI inputs when a domain type exists.
- The root CLI entry point must register commands lazily. Asking for one command must not import unrelated command families.
- CLI command families with sibling modules should be packages. Put the Click group and shared CLI-only helpers in the package `__init__.py`; put each command family in a named sibling module inside that package.
- Keep package `__init__.py` files shallow. Do not re-export merge, reasoning, or workflow surfaces from low-level packages when that forces circular or cross-layer imports.
