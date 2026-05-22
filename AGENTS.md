Pytest and Pyright:
- Run tests through the logged wrappers, not bare pytest:
  `powershell -File scripts/run_logged_pytest.ps1 ...` or
  `sh ./scripts/run_logged_pytest.sh ...`.
- Check package typing with `uv run pyright propstore`; do not use bare
  `uv run pyright` as the project gate.

Propstore architecture:
- Prefer explicit typed domain objects. Decoded YAML/JSON/SQLite rows may be
  `dict` only at IO boundaries and must not flow through core semantic code.
- Claims, concepts, sources, stances, justifications, and related semantic
  objects must not be represented as loose `dict`, `Dict`, `object`, or
  source-local handles past their boundary.
- Put each fact in one owner: Quire charters/field metadata/family APIs for
  schema, field, storage, registry, reference, and placement mechanics;
  Propstore family/domain owners for semantic behavior.
- Delete old production paths first. Do not keep old/new paths in parallel, and
  do not replace deleted helpers with aliases, shims, adapters, fallback
  readers, bridge normalizers, repeated field lists, per-field kwargs builders,
  or local type-narrowing blocks.
- `legacy` is not implied by age. Support old repos/data only when explicitly
  requested; otherwise fail hard at the boundary and delete the old path.
- Source-local authoring state belongs only in the source subsystem. Canonical
  surfaces must reject source-local-only fields/shapes, and source-local
  readability metadata must not leak into canonical identity/runtime paths.

Tooling discipline:
- Use `uv` for Python commands.
- Use `apply_patch` for manual edits.
- For multi-file Python symbol renames, symbol moves, or import-updating
  refactors, use the repo Rope workflow (`scripts/rope_rename.py`) or explicit
  `apply_patch` edits. Do not write ad hoc rewrite scripts or broad
  text-replacement scripts.
- If a small semantic change creates a broad/noisy diff, stop immediately and
  report the mismatch before making another edit.

CLI boundary:
- `propstore.cli` is presentation only: Click commands/options, typed request
  construction, owner-layer calls, rendering, and exit-code mapping.
- CLI modules must not own compiler workflows, repository mutation semantics,
  source promotion/finalize/status semantics, world/ATMS/revision/argumentation
  query semantics, sidecar SQL policy, or concept/claim/form/context mutation
  logic.
- Move reusable behavior to the owner layer with typed request/report/failure
  objects; owner APIs must not import Click, print, call `sys.exit`, or accept
  flag-shaped CLI inputs when a domain type exists.
- Root CLI registration must stay lazy, and package `__init__.py` files must
  stay shallow.

Worldline boundary:
- Worldline journals are Propstore semantic artifacts, not Quire storage
  concepts and not CLI-owned workflows.
- Journal capture/projection belongs in worldline/app/support-revision owner
  layers; durable journal state belongs in committed worldline artifacts, not
  process-local branch metadata.
