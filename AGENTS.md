Always run pytest through `scripts/run_logged_pytest.ps1`, which wraps `uv run pytest -vv` and tees the full output to a timestamped log file under `logs/test-runs/`.

Canonical usage:
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_init.py`
- `powershell -File scripts/run_logged_pytest.ps1 -Label artifact-store tests/test_artifact_store.py tests/test_import_repo.py`

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
