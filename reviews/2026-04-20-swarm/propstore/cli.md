# CLI Adapter Review — 2026-04-20

Scope: `C:\Users\Q\code\propstore\propstore\cli\` (root + subpackages concept, output, source, world, worldline).

All CLI modules read. Owner-layer click-discipline sweep performed via grep of `propstore\propstore\`: no `import click` outside `propstore.cli`, no `sys.exit` anywhere in the package, no `print(`, `sys.stdout`, `sys.stderr` inside `propstore\app`. Owner-layer click discipline appears clean at the import level.

Remaining verification gap: have not confirmed that `propstore.app.*` modules never return Click-coupled types or that the owner-layer request objects in `propstore.app.world`, `propstore.app.world_atms`, `propstore.app.world_reasoning`, `propstore.app.world_revision`, `propstore.app.worldlines` are all free of flag-string handling; shallow reading of CLI callsites suggests they accept typed domain values (strategy strings are `Choice`-validated in CLI before construction, but some are passed as raw strings like `strategy: str | None` — see observations).

## Adapter Discipline Violations (each with quoted rule)

### AV-1 — `propstore/cli/__init__.py:104-107`
Rule: "The root CLI entry point stays lazy: registering or asking for one command must not import unrelated command families."
After defining `_LazyCLIGroup` (which correctly defers sibling imports in `get_command`), the module post-mutates `cli.commands` with stub `click.Command(name, help=spec[2])` entries. These stubs have no callback, no options, and shadow the lazy resolution when anything reads `cli.commands[name]` directly. Structurally preserves laziness; semantically a footgun that can silently break Click introspection or tests. Severity: Medium. Fix: delete the `cli.commands.update({...})` block and rely entirely on `_LazyCLIGroup.get_command` for resolution.

### AV-2 — `propstore/cli/concept/__init__.py:14-17`
Rule: "CLI command families with sibling modules are PACKAGES: the package `__init__.py` owns the Click group and shared CLI-only helpers, and each command family lives in a named sibling module inside that package."
Concept `__init__.py` eagerly imports `alignment`, `display`, `embedding`, `mutation` as siblings. Standard split-module Click pattern — within the letter of the rule, but forces `propstore.app.concepts` to load any time `pks concept` is invoked regardless of which subcommand actually runs. Severity: Low (design choice, rule-compliant).

### AV-3 — `propstore/cli/source/__init__.py:14-17`
Same pattern as AV-2 for source. Severity: Low.

### AV-4 — `propstore/cli/world/__init__.py:23-27`
Same pattern for world — analysis, atms, query, reasoning, revision all loaded on any `pks world ...`. Severity: Low.

### AV-5 — `propstore/cli/worldline/__init__.py:96-99`
Same pattern for worldline — display, materialize, mutation. Severity: Low.

### AV-6 — `propstore/cli/concept/mutation.py:103-107`
Rule: "They [CLI] must not own … concept/claim/form/context mutation logic."
`pks concept add` reads `repo.families.forms.iter()` directly to populate an interactive "Available forms" prompt. An owner-layer `list_form_items(repo)` already exists in `propstore.app.forms` and is used by `pks form list`. CLI is reaching into Repository.families storage for prompt rendering. Severity: Low. Fix: call `list_form_items(repo)` and extract names; do not traverse `repo.families.*`.

### AV-7 — `propstore/cli/world/__init__.py:11-13`
Rule: "CLI is presentation adapter, NOT owner layer."
The `@world` group has `@click.pass_obj` + `obj: dict` parameter but body is `pass`. Obj unused. Not a violation; style drift. Severity: None.

### AV-8 — `propstore/cli/worldline/__init__.py:36-92`
Rule: "Package `__init__.py` files stay shallow."
The worldline package `__init__.py` defines `_REASONING_OPTIONS` (11 click options) and `_REVISION_OPTIONS` (5 click options) plus two decorator helpers `_apply_reasoning_options` / `_apply_revision_options`. These are CLI-only helpers legitimately shared between `create` and `run`, matching the rule: "the package __init__.py owns the Click group and shared CLI-only helpers." But the helpers also `import` `propstore.app.worldlines` values (`reasoning_backend_values()`, `argumentation_semantics_values()`) at module load time — any `pks worldline` invocation loads the full worldlines app layer before the user asks for even `--help`. Severity: Low.

### AV-9 — `propstore/cli/world/analysis.py:206-208`
`Path(output_file).write_text(output)` — CLI writes a file. Presentation output, borderline OK; does not violate any explicit rule but the serialization policy (DOT vs JSON via `report.graph.to_dot()` / `report.graph.to_json()`) lives in the graph object (owner), so CLI is just choosing + writing. Severity: None.

### AV-10 — `propstore/cli/init.py:26-28`
CLI computes `root = start / directory if start is not None else Path(directory)`. Path composition policy for the `-C` + positional arg — acceptable request construction. Severity: None.

## Eager Import Violations

Audit: no owner-layer module in `propstore/app/` imports `click` (verified by grep `^import click|^from click`). No module outside `propstore.cli` imports `click`. No `propstore.app.*` imports `propstore.cli.*`.

Observed eager imports within CLI (all are family-local, triggered only after the lazy root registry has selected a family):

- `propstore/cli/__init__.py:9` — `import click` at root: required.
- `propstore/cli/claim.py:16-39` — top-level import of 16 symbols from `propstore.app.claims`. Loads only when `pks claim` is dispatched. OK.
- `propstore/cli/concept/{alignment,display,embedding,mutation}.py` — top-level import of `propstore.app.concepts`. Loads via `concept/__init__.py` on any `pks concept`. OK in spirit.
- `propstore/cli/concept/embedding.py:23-30, 84-91` — deferred imports *inside* function bodies. This would be a good optimization if `mutation.py` and `alignment.py` and `display.py` did not already eagerly pull `propstore.app.concepts`. Given they do, the lazy imports in `embedding.py` buy nothing. Severity: None (cosmetic).
- `propstore/cli/source/*.py` — top-level imports of `propstore.app.sources`. Same family-local pattern.
- `propstore/cli/world/*.py` — top-level imports of `propstore.app.world`, `propstore.app.world_atms`, `propstore.app.world_reasoning`, `propstore.app.world_revision`.
- `propstore/cli/worldline/__init__.py:8-13` — imports from `propstore.app.worldlines` at module load.
- `propstore/cli/worldline/*.py` — top-level app imports.

No cross-family leakage observed. No `propstore.storage` / `propstore.compiler` / `propstore.aspic_bridge` / `propstore.world` / `propstore.belief_set` imports from CLI (all go via `propstore.app.*`).

## Owner-Layer Work in CLI

### OL-1 — `propstore/cli/proposal_cmds.py:40-44`
Rule: "CLI MUST NOT own: … source promotion/finalize/status semantics."
```
result = promote_proposals(repo, plan)
for item in plan.items:
    emit_success(f"  Promoted: {item.filename}")
emit_success(f"\n{result.moved} file(s) promoted.")
```
The CLI iterates `plan.items` (the *planned* items) not `result.<promoted_items>` — if the owner promoted a subset, the CLI falsely reports every planned item as "Promoted:". `result.moved` may disagree with the line count. Severity: Medium. Fix: have owner return the actual promoted items; CLI should iterate `result.promoted_items`.

### OL-2 — `propstore/cli/concept/mutation.py:103-107`
Duplicate of AV-6. CLI reaches `repo.families.forms.iter()` directly.

### OL-3 — `propstore/cli/world/reasoning.py:347-382`
`_claim_label` and `_group_by_type` contain claim-type-specific formatting logic: truncation at 60 chars, ellipsis, branching on `parameter`/`equation`/`observation`/`limitation`/`mechanism`/`comparison`, fallback to `concept_name` / `statement` / `description`. This is presentation, but the claim-type vocabulary is a first-class domain concept. If the set of claim types grows or types are renamed, the CLI silently falls through to `f"{claim_id} ({claim_type})"`. Consider exposing a `claim.display_label()` method from the owner (or a `WorldExtensionsClaimLine.display_label()` helper). Severity: Low (presentation drift risk).

### OL-4 — `propstore/cli/worldline/materialize.py:30-44, 91-107`
`_parse_revision_conflicts` parses `atom_id=target,target,...` strings into a dict, and `_coerce_override_values` does string-to-float coercion. Both are CLI-side scalar-parsing before building typed request objects. Acceptable as request construction. Severity: None.

### OL-5 — `propstore/cli/world/analysis.py:32-72`
`_parse_hypothetical_add` JSON-validates the `--add` payload and constructs `WorldHypotheticalSyntheticClaimSpec`. This is CLI-side request parsing — permitted. Note: line 60 accepts `str | int | float` but rejects `bool` via `isinstance(value, bool)` short-circuit. OK.

### OL-6 — `propstore/cli/world/revision.py:63-70`
`_parse_revision_atom_json` parses JSON then passes the raw dict straight to `AppRevisionExpandRequest(atom=...)`. The owner request object accepts a `dict` rather than a typed atom spec. This is a flag-shaped CLI input surviving into the owner layer — mild violation of: "Owner-layer APIs extracted from CLI code use typed request/report/failure objects or existing domain objects. They do not … accept flag-shaped CLI inputs when a domain type exists." Severity: Medium if a typed `RevisionAtomSpec` exists; Low if not. Inspect `propstore.app.world_revision.AppRevisionExpandRequest.atom` type declaration to confirm.

### OL-7 — `propstore/cli/worldline/__init__.py:16-26`
`_parse_kv_args` calls owner-side `coerce_worldline_cli_value`, which suggests the owner provides a helper specifically for CLI scalar coercion. That helper lives in `propstore.app.worldlines`. If `coerce_worldline_cli_value` is used only by the CLI and nowhere else, it is an owner-layer function that exists solely to serve CLI flag-shaped inputs — arguably owner-layer accepting CLI-shaped inputs. Severity: Low. Verify whether other call sites use it; if not, move the coercion to CLI.

## Bugs & Silent Failures

### B-1 — `propstore/cli/proposal_cmds.py:41-44`
See OL-1. Iterating the plan rather than the result. Severity: Medium.

### B-2 — `propstore/cli/history_cmds.py:118-120`
`show_cmd`: on `CommitNotFoundError` emits to stdout and returns with exit 0. Scripting tools see success on a nonexistent commit. Severity: Medium. Fix: `fail(f"Commit not found: {commit}")`.

### B-3 — `propstore/cli/history_cmds.py:151-155`
`checkout_cmd`: same pattern — `CommitNotFoundError` and `CommitHasNoConceptsError` both return with exit 0 after stdout error. Severity: Medium.

### B-4 — `propstore/cli/micropub.py:69`
`exit_with_code(1)` uses hard-coded int instead of `EXIT_ERROR` constant. Severity: Low (drift).

### B-5 — `propstore/cli/world/atms.py:111`
`exit_with_code(2)` hard-coded. Should use `EXIT_VALIDATION`. Severity: Low.

### B-6 — `propstore/cli/world/reasoning.py:274`
`fail(exc, exit_code=2)` hard-coded `2`. Severity: Low.

### B-7 — `propstore/cli/claim.py:266-269`
Progress lambda:
```
(lambda model_name, done, total: emit(f"  {done}/{total}", nl=False) if done % batch_size == 0 else None)
```
`nl=False` means no newline is ever emitted — output runs together onto one line. `done % batch_size == 0` skips the final chunk unless `done` is an exact multiple of `batch_size`. Severity: Low (cosmetic); misleading progress.

### B-8 — `propstore/cli/claim.py:329`
`def relate(obj, claim_id, relate_all_flag, model, embedding_model, top_k, concurrency):` — missing type annotations. Drift from rest of module. Severity: Low.

### B-9 — `propstore/cli/claim.py:360-388`
`--all` and positional `claim_id` not mutually exclusive. The `relate_all_flag` branch at line 377 wins over the claim-specific branch when both are set (guarded by `not relate_all_flag` at 360). Ambiguous user contract. Severity: Low.

### B-10 — `propstore/cli/__init__.py:95-96`
```
if ctx.resilient_parsing or any(arg in {"--help", "-h"} for arg in sys.argv[1:]):
    return
```
Inspects raw `sys.argv` rather than Click context. Breaks if a subcommand has a positional argument literally named "--help". Also: if `--help` appears after a `--` separator it still triggers. Fragile. Severity: Low.

### B-11 — `propstore/cli/__init__.py:87-91`
Root `-C/--directory` option uses `click.Path(exists=True, ...)`. If the user gives a new path for `init`, Click rejects before init runs. Breaks `pks -C new_knowledge init new_knowledge`. Severity: Low (UX).

### B-12 — `propstore/cli/world/analysis.py:206-208`
`Path(output_file).write_text(output)` — no encoding, no error handling, silently overwrites. Severity: Low-Medium.

### B-13 — `propstore/cli/world/analysis.py:58-71`
`value=float(value) if isinstance(value, int | float) else value` — ints coerce to float, strings pass through. But the field type on `WorldHypotheticalSyntheticClaimSpec.value` is not visible from CLI; inconsistent typing could break downstream assumption of numeric values. Severity: Low.

### B-14 — `propstore/cli/source/lifecycle.py:167-193` (`stamp-provenance`)
Missing `@click.pass_obj` and no `obj` parameter. Works because owner function doesn't need `repo`. Docstring says "DEPRECATED" but no runtime deprecation warning is emitted; users running the command never learn it's deprecated. Severity: Low (deprecation hygiene).

### B-15 — `propstore/cli/source/proposal.py:25-26`
`pks source propose-concept NAME --name CONCEPT_NAME --definition ...` has two "name" concepts (positional source-branch name, `--name` concept_name). UX-confusing; easy to swap. Severity: Low.

### B-16 — `propstore/cli/concept/mutation.py:108-109`
```
if definition is None or form_name is None:
    raise click.ClickException("definition and form are required")
```
Unreachable — `click.prompt` returns a string or aborts. Dead defensive code. Severity: None.

### B-17 — `propstore/cli/worldline/display.py:69, 71`
Non-ASCII warning glyphs `⚠` and `✓` in emitted strings. Windows consoles without UTF-8 support will fail to render. Since `rich.console.Console` is used with `force_terminal=False`, it should render as plain text — but the raw characters may still encode-error on some platforms. Severity: Low.

### B-18 — `propstore/cli/worldline/materialize.py:243-259`
`worldline_refresh` uses `ctx.invoke(worldline_run, name=name, bindings=(), overrides=(), targets=(), strategy=None, ...)` with a fixed set of defaults. The defaults hard-code `semantics="grounded"`, `praf_strategy="auto"`, etc. — duplicating the `@click.option(..., default=...)` values from `worldline_run`. If the option defaults change, `refresh` drifts silently. Severity: Medium (maintenance bomb).

### B-19 — `propstore/cli/worldline/__init__.py:21-22`
```
for r in remaining:
    emit_warning(f"WARNING: ignoring argument without '=': {r}")
```
Silent warning only — argument is accepted. Scripts that mistype a positional may not detect the problem. Severity: Low.

### B-20 — `propstore/cli/world/analysis.py:39-41`
`except json.JSONDecodeError as exc: raise click.ClickException(f"invalid --add JSON: {exc.msg}")` — emits `exc.msg` only, dropping line/col context. `str(exc)` would include position. Severity: Low.

### B-21 — `propstore/cli/concept/display.py:117-121`
On `UnknownConceptError`, special-case prefix `align:` produces "Concept alignment '...' not found", otherwise "Concept '...' not found". Both via `click.ClickException` (exit 1). Inconsistent with surrounding code that uses `fail()` helper. Severity: None.

### B-22 — `propstore/cli/world/reasoning.py:274`
`fail(exc, exit_code=2)` — takes an exception but `PropstoreClickError.__init__` does `super().__init__(str(message))`, coercing to string. Fine, but `WorldExtensionsUnsupportedBackend` message content depends on owner-side `__str__`. Severity: None.

### B-23 — `propstore/cli/init.py:29`
`Path(directory)` if `start is None` — yields a relative path. `initialize_project(root)` may resolve relative paths unpredictably depending on CWD. Verify owner handles it; if not, CLI should resolve to absolute here. Severity: Low.

### B-24 — `propstore/cli/world/atms.py:361-362`
```
emit("bounded additive plans over declared queryables")
emit("not revision/contraction")
```
Two bare-info `emit` calls emit unconditional diagnostic text BEFORE attempting the owner call. If the owner raises `WorldAtmsValidationError`, these two lines still print, then the exception renders. Confusing partial output. Severity: Low.

### B-25 — `propstore/cli/world/atms.py:418-419`
Same pattern in `next-query`: `emit("derived from bounded additive intervention plans")` emitted unconditionally before the owner call. Severity: Low.

### B-26 — `propstore/cli/claim.py:266-269`
The conditional lambda assignment uses a nested ternary:
```
on_progress=(
    (lambda model_name, done, total: emit(...) if done % batch_size == 0 else None)
    if model == "all"
    else (lambda model_name, done, total: emit(...))
),
```
Two distinct callback shapes for the same parameter; easy to break. Severity: Low.

### B-27 — `propstore/cli/compiler_cmds.py:40-43, 66-71`
No `return` statement between `emit_error(exc.summary)` and `exit_with_code(EXIT_VALIDATION)`. Since `exit_with_code` raises `click.exceptions.Exit`, control does not fall through. Fine at runtime; brittle if someone changes `exit_with_code` behavior. Severity: None.

## Dead Code / Drift

### DC-1 — `propstore/cli/output/errors.py`
`emit_prefixed_error` is defined but NOT re-exported from `output/__init__.py`, and grep shows no callers outside the reviews/ dir. Dead module. Severity: None (cleanup candidate).

### DC-2 — `propstore/cli/world/__init__.py:10-13`
`@world.command` group uses `@click.pass_obj` but body is `pass` — obj parameter unused. Severity: None.

### DC-3 — `propstore/cli/source/lifecycle.py:167-193`
`stamp-provenance` marked DEPRECATED in docstring but still functional with no deprecation warning emitted. Severity: Low.

### DC-4 — `propstore/cli/concept/mutation.py:108-109`
Unreachable defensive check after `click.prompt(...)`. Severity: None.

### DC-5 — `propstore/cli/__init__.py:104-107`
Stub placeholder loop populates `cli.commands` with useless Command objects. See AV-1. Severity: Medium.

### DC-6 — `propstore/cli/worldline/materialize.py:91-107`
`_coerce_override_values` contains a dead branch: `if isinstance(value, bool): ... continue` then `if isinstance(value, int | float): ... continue`. Since `bool` is a subclass of `int`, the bool branch must come first (and does). But after `_parse_kv_args` + `coerce_worldline_cli_value`, the returned value type space is limited; the final `override_dict[key] = str(value)` fallback is likely unreachable unless `coerce_worldline_cli_value` can return arbitrary types. Severity: None.

### DC-7 — `propstore/cli/worldline/materialize.py:243-259`
`worldline_refresh` duplicates default values across click option definitions and `ctx.invoke` call. If defaults change in one place, silent drift. Severity: Medium. Fix: build a `WorldlineRunRequest` from zero-flag input and call owner directly, or have `worldline_run` dispatch to a helper that accepts sensible defaults.

### DC-8 — `propstore/cli/worldline/__init__.py:31-32`
`@worldline` group callback body is empty (docstring only). `@click.pass_obj` decoration yields unused `obj`. Severity: None.

### DC-9 — `propstore/cli/helpers.py:10-35` (`parse_kv_pairs`)
Used by `propstore/cli/worldline/__init__.py:_parse_kv_args`. Grep to confirm other callers — if none, the helper may be over-engineered for a single caller. Severity: None.

## Positive Observations

- Root `__init__.py` uses a proper lazy registry (`_LazyCLIGroup`) with `get_command` deferring sibling imports. Core adapter discipline preserved.
- `propstore/cli/helpers.py` centralizes exit codes (`EXIT_OK`, `EXIT_ERROR`, `EXIT_VALIDATION`), a `PropstoreClickError`, and consistent `fail()` / `exit_with_code()` helpers.
- `propstore/cli/output/*` is clean, small, CLI-only presentation. `emit_yaml` delegates to `quire.documents.render_yaml_value`.
- Verified (grep): NO `import click` anywhere in `propstore/` outside `propstore/cli/`. Owner-layer click discipline clean.
- Verified (grep): NO `sys.exit` anywhere in `propstore/`. Owner-layer exit discipline clean.
- Verified (grep): NO `print(`, `sys.stdout`, `sys.stderr` in `propstore/app/`. Owner-layer output discipline clean.
- Verified: `propstore.app.*` modules are not imported by the CLI from cross-family modules (no CLI source.py importing `propstore.app.world`, no CLI world.py importing `propstore.app.concepts`).
- All top-level CLI commands observed construct typed `propstore.app.<family>.XxxRequest` objects and call typed owner-layer functions. No raw SQL, no direct storage mutation, no argumentation computation inside CLI.
- Owner exception types (`ClaimSidecarMissingError`, `UnknownClaimError`, `WorldResolveError`, `WorldAtmsValidationError`, `WorldRevisionValidationError`, `WorldExtensionsUnsupportedBackend`, `FormReferencedError`, `FormNotFoundError`, `ConceptMutationError`, `ConceptValidationError`, `ConceptSidecarMissingError`, `ClaimEmbeddingModelError`, `ClaimWorkflowError`, etc.) are caught at the CLI boundary and translated to `ClickException` / `fail()`. Clean separation.
- Revision, worldline, and world command families cleanly use `@click.pass_obj` and thread the lazy `_LazyRepository` through without reaching into storage internals.
- `propstore/cli/claim.py` uses `on_progress=` callbacks to decouple progress rendering from owner-layer execution — correct adapter pattern.
- CLI-local rendering helpers (`propstore/cli/worldline/rendering.py`, `propstore/cli/world/reasoning.py:_claim_label`) are CLI-only and import from `propstore.worldline.definition`/`result_types` — domain value types, not controllers.

## Unfinished Verification

- Whether `AppRevisionExpandRequest.atom` / `AppRevisionReviseRequest.atom` / `AppRevisionExplainRequest.atom` accept `dict` or a typed atom spec — if typed, CLI's `_parse_revision_atom_json` is laundering a flag-shaped dict into the owner.
- Whether `coerce_worldline_cli_value` is owner-layer API serving non-CLI callers or CLI-only plumbing misplaced in the owner.
- Whether `parse_world_binding_args` (owner-layer helper imported in four CLI world modules) accepts raw CLI `args: tuple[str, ...]` — if so, owner is accepting flag-shaped input. Needs source-level confirmation.
