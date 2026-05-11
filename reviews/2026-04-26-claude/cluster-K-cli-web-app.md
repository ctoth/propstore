# Cluster K: CLI, web, app, demo surface

## Scope

Files read in full or in pertinent sections (every absolute path is to the source tree at `C:/Users/Q/code/propstore/`):

- `main.py`
- `propstore/cli/__init__.py`, `helpers.py`, `web.py`, `init.py`, `materialize.py`, `sidecar.py`, `observatory.py`
- `propstore/cli/output/{__init__.py,console.py}`
- `propstore/cli/claim/{__init__.py,display.py}`, `propstore/cli/concept/{__init__.py,mutation.py}`
- `propstore/cli/world/{__init__.py,query.py,analysis.py,atms.py,revision.py}` (heads + key segments)
- `propstore/cli/source/{__init__.py,authoring.py,batch.py,lifecycle.py}`
- `propstore/web/{app.py,routing.py,html.py,requests.py,serialization.py,static/web.css}`
- `propstore/app/...` (header signatures only, via Grep)
- `propstore/observatory.py`, `propstore/policies.py`, `propstore/contracts.py`, `propstore/contract_manifests/semantic-contracts.yaml` (existence + index)
- `propstore/demo/reasoning_demo.py`
- `propstore/sidecar/{query.py,sqlite.py}`
- `README.md`, `docs/cli-reference.md` (top index), `docs/application-layer-and-undo.md`
- `tests/test_cli_web.py`, `tests/test_app_rendering.py`, `tests/test_web_accessibility.py` (preface), `tests/test_contract_manifest.py`

Out of read budget but in scope (acknowledge gaps): the deeper bodies of `world/{atms,reasoning,revision,analysis}.py` past header pass, `cli/worldline/*.py`, `cli/concept/{alignment,display,embedding}.py`, `cli/claim/{analysis,embedding,relation,validation}.py`, `cli/source/proposal.py`, `cli/predicate/`, `cli/rule/`, `cli/context.py`, `cli/form.py`, `cli/grounding_cmds.py`, `cli/history_cmds.py`, `cli/merge_cmds.py`, `cli/repository_import_cmd.py`, `cli/verify.py`, `cli/micropub.py`, `cli/proposal.py`, `cli/compiler_cmds.py`, full `cli-reference.md`/`python-api.md`/`integration.md`, `propstore-web-gui-vamp-2026-04-19.md`. The findings below cite only files I directly read; everything outside that read set I list as an open question rather than a claim.

## CLI bugs and UX issues

### 1. Missing `pks promote` top-level command (README claim → code drift) [HIGH]

`README.md:166` documents:

```
uv run pks -C knowledge promote
```

`propstore/cli/__init__.py:13-45` lists every top-level command. There is no `promote` entry. Only `pks proposal promote ...` and `pks source promote <name>` exist (`propstore/cli/source/lifecycle.py:75`, `propstore/cli/proposal.py` per command catalog). Running the documented invocation will fail with a "no such command" error, and Click will not auto-suggest because the alias map is single-entry (`{"forms": "form"}`).

### 2. README documents non-existent `pks world` flat aliases [HIGH]

The README block at `README.md:198-208` documents:

```
pks world atms-status ...
pks world atms-interventions ...
pks world revision-base
pks world revise --atom ...
pks world iterated-revise --atom ...
```

Reality (from Bash grep over `propstore/cli/world/*.py`):

- `world atms` is a subgroup; subcommands are `world atms status`, `world atms interventions`, etc. (`propstore/cli/world/atms.py:36, 50, 344`). There is no `world atms-status` flat command.
- `world revision` is a subgroup with `base`, `revise`, `iterated-revise` subcommands (`propstore/cli/world/revision.py:37, 142, 241, 320`). There is no `world revise` or `world iterated-revise` flat command.

Anyone copy-pasting these from the README hits "no such command" on every line. This is the single highest-priority drift in the README because the affected commands are the centerpieces of three full README sections (ATMS, revision).

### 3. `docs/application-layer-and-undo.md` describes a package that does not exist [HIGH]

`docs/application-layer-and-undo.md:5-8` declares "Propstore gets a real application layer at `propstore.application`. The CLI is a presentation adapter over that layer." It then specifies `pks undo`, `pks undo --mine`, `pks undo --preview`, `pks redo`, `refs/propstore/command-journal`, `CommandEnvelope`, `UndoPlan` enum, RestoreTreeUndo merge semantics, dependency tracking, etc.

Reality:

- `ls propstore/application` → no such directory.
- `propstore/cli/__init__.py:13-45` does not register `undo` or `redo`. Grep over `propstore/cli/` for `undo|redo` returns zero matches.
- The "Command Semantics Matrix" maps every existing command to an undo plan, so the docs imply undo is operational. None of it is.

This document should either be moved to `proposals/` or annotated as "unimplemented design" at the top. As-published it actively misleads agents/users about what exists.

### 4. `pks web` exposes `0.0.0.0` with no auth, no token, no CSP [HIGH]

`propstore/cli/web.py:11-34`:

- `--host` accepts any string, default `127.0.0.1`. Test (`tests/test_cli_web.py:40-50`) asserts that `--host 0.0.0.0` works.
- `propstore/web/app.py` and `propstore/web/routing.py` register zero authentication middleware, no CSP/X-Frame-Options/X-Content-Type-Options headers, no rate limit.
- All routes are GET, so CSRF surface is small, but a knowledge corpus exposed on `0.0.0.0` allows anyone on the LAN to enumerate every claim, neighborhood, source paper title, machine ID, and provenance fact. The README and CLI flag give no warning.

Recommendation: at minimum, when `host` resolves to non-loopback, emit a warning about the lack of auth before calling `uvicorn.run`. Long term, gate non-loopback behind an explicit `--insecure` opt-in flag.

### 5. `pks sidecar query` accepts arbitrary SQL [MED]

`propstore/cli/sidecar.py:18-36` and `propstore/sidecar/query.py:21-43`. Read-only is enforced via `PRAGMA query_only=ON`, so `INSERT/UPDATE/DELETE/PRAGMA writable_schema=ON` should fail. ATTACH still works but writes against the attached DB are also blocked under `query_only`. This is acceptable for a local CLI tool.

However: `cursor.fetchall()` happens unbounded — a `SELECT * FROM claim_core CROSS JOIN claim_core` will allocate the world. There is no `LIMIT` injection or row cap. For a debugging surface this is fine; for any web-exposed equivalent it would be lethal.

### 6. `pks source stamp-provenance` deprecated yet still mutates files [MED]

`propstore/cli/source/lifecycle.py:188-221`. Marked DEPRECATED in the docstring, emits a deprecation warning on stderr, then continues to mutate the file. This is the worst of both worlds: anyone who relies on the deprecation warning being a soft veto will silently keep producing mutations. Either the command should error out (recommended once callers are updated) or the warning text should explicitly say "this still mutates".

Additional smell: this `@source.command` is registered without `@click.pass_obj`. Every other `source.*` command takes `obj: dict` first. The function signature is `def stamp_provenance(name, file_path, agent, skill_name, status_value, plugin_version)` — works because the function genuinely doesn't need a Repository, but the inconsistency is bait for refactor errors.

### 7. `pks claim rename` rewrites CEL across files but is silently atomic [MED]

`propstore/cli/concept/mutation.py:162-186` (`rename`) and the underlying `rename_concept` app function. Docstring says "rewrites CEL condition expressions in every other concept and every claim file that references the old name". CLI surface offers `--dry-run` but no preview/diff output described in the help. For a blind user (Q's stated scenario) operating via screen reader, the lack of an upfront list of affected files is a real ergonomic defect — the user has to commit to invoking and trust the after-report. The command's `_render_mutation_report` (line 43) iterates `report.lines` but I did not verify those lines enumerate touched paths; this needs follow-up.

### 8. CLI exit codes are inconsistent across modules [MED]

`propstore/cli/helpers.py:64-83` defines `EXIT_OK=0`, `EXIT_ERROR=1`, `EXIT_VALIDATION=2` and a `PropstoreClickError` that respects an explicit code. But:

- `propstore/cli/observatory.py:54-61` uses `click.ClickException` directly (exit code 1) for both invalid JSON and invalid scenarios — neither is distinguishable.
- `propstore/cli/source/lifecycle.py:58-59, 70, 102, 183` all wrap `ValueError` in `click.ClickException` (exit code 1), losing the validation/runtime distinction.
- `propstore/cli/world/query.py:144, 207` use `fail(...)` which defaults to `EXIT_ERROR=1` even for "Unknown concept" / "Unknown claim" — these are arguably user-input validation errors and should be `EXIT_VALIDATION=2` (which the helper module defines but does not use here).
- `propstore/cli/world/atms.py:121` uses `exit_with_code(EXIT_VALIDATION)` for ATMS verify failure — that is a *consistency check failure*, not user input validation. Same constant, very different semantic. The helper names should be reviewed; `EXIT_VALIDATION` currently bridges "input invalid" and "data inconsistent".

Net: exit codes are not a contract. Scripts cannot reliably distinguish "your input was wrong" from "your data is inconsistent" from "internal error".

### 9. `pks world bind` argument parsing silently drops middle bindings without `=` [MED]

`propstore/cli/world/__init__.py:22-35` (`parse_world_binding_args`):

```python
return parsed, remaining[-1] if remaining else None
```

If a user runs `pks world bind domain=example pitch task=speech other_concept`, only `other_concept` is treated as the concept filter; `pitch` is silently discarded into the void. Same applies to `world hypothetical`, `world chain`, `world export-graph`, `world sensitivity` — they all reuse this parser (`propstore/cli/world/analysis.py:113, 175, 215, 245`). The parser should at least raise on multiple non-`=` tokens.

### 10. `pks world bind` accepts empty value via `key=` [LOW]

`propstore/cli/world/__init__.py:22-35`: rejects empty key but accepts empty value. `partition("=")` on `"k="` yields `("k", "=", "")`. Bound to `parsed["k"] = ""`. Whether downstream treats `""` as "any" or "this literal empty string" depends on the binding consumer, which I did not trace. Flagging.

### 11. `_LazyCLIGroup.get_command` raises `TypeError` on misregistered command [LOW]

`propstore/cli/__init__.py:80-82`: if a developer typos the attribute, the user gets an opaque `TypeError`, not a Click error. Defensive but never user-facing under correct registration. Low priority — flag.

### 12. `pks observatory run` fixture loader has no schema [MED]

`propstore/cli/observatory.py:51-61`. Reads JSON, hands to `EvaluationScenario.from_dict`. No JSON Schema, no friendly error pinpointing which field; user gets `ValueError` text from msgspec/dataclass. Acceptable for an internal harness, but `--fixture` is documented in `cli-reference.md` (per index pass) so users may try this.

### 13. `_render_text` for observatory loses falsification details [LOW]

`propstore/cli/observatory.py:64-75`: text format only emits "pass"/"fail" and the operator/policy. The actual `falsification_ids` are dropped. JSON has them. A failing scenario in text mode tells the operator nothing actionable — they have to re-run with `--format json`.

### 14. `pks materialize` silently allows arbitrary directory targets [MED]

`propstore/cli/materialize.py:14`: `directory` has no `path_type` validation beyond `file_okay=False`. Passing `--clean` plus a typo target (e.g. `pks materialize ../`) could remove "stale" files outside the intended path. I did not trace `materialize_repository` to verify the safety boundary, but the CLI does not pre-validate that `directory` is inside the repo root or even non-existent. Worth checking `propstore/app/materialize.py`.

### 15. `pks init` resolves `directory` against ctx-stored `start` only when present [LOW]

`propstore/cli/init.py:25-27`. If `obj is None` (which only happens when nothing populated ctx.obj), code defaults to `{}`. But `cli` callback always populates `ctx.obj`, so `obj is None` is dead — unless a downstream tester invokes `init` outside the parent group. Defensive but the comment in `propstore/cli/__init__.py:101-104` tells the reader why this branch exists; OK.

## Web/app correctness and accessibility

### 16. `templates/` directory is empty; HTML is f-string concatenation in `html.py` [LOW]

`propstore/web/templates/` is empty (verified via `ls`). `propstore/web/html.py` builds HTML by string interpolation with `html.escape(quote=True)` (`html.py:559-560`) routed through `_text(...)` everywhere. Escaping looks correct on every interpolation I checked (`_text(...)` is called on every dynamic value including `href` strings). `quote(claim_id, safe="")` is also URL-quoted before embedding (`html.py:46, 75, 108, 222, 238, 267, 282, 506, 530`). No raw f-strings of user data into href slots.

This is a defensible choice for a small read-only UI; just delete the empty `templates/` directory or note it as future state. The presence of the empty dir is misleading.

### 17. Render-policy float params have no range validation [HIGH]

`propstore/web/requests.py:15-30, 58-69`. `pessimism_index`, `praf_epsilon`, `praf_confidence` are converted with bare `float(value)`. There is no range check. A request with `?pessimism_index=999` or `?praf_confidence=-1` is accepted at the web layer and passed on. NaN/inf strings — `float("nan")` succeeds in Python. The downstream `build_render_policy` may catch some of these via `RenderPolicyValidationError` (test in `tests/test_app_rendering.py:67` only checks "Unknown reasoning_backend"), but rejecting at the trust boundary would be cleaner and the error message better.

Recommendation: in `_float_param`, accept a `lo`/`hi` and reject out-of-range / NaN / inf with `WebQueryParseError`. `pessimism_index` and `praf_confidence` should be `[0, 1]`; `praf_epsilon` should be `(0, 1)`.

### 18. `_repo_from_request` re-walks the filesystem on every request [MED]

`propstore/web/routing.py:424-426`:

```python
def _repo_from_request(request: Request) -> Repository:
    start = request.app.state.repository_root
    return Repository.find(start)
```

Every request constructs a new Repository. On Windows this incurs at minimum a parent-directory walk plus a sidecar/git open per request. For a UI this is fine; for any concurrent traffic it will become a hot path. More importantly, `Repository.find` may have side effects (sidecar connection caching, etc.) that I did not verify; if so, repeated construction could leak handles.

### 19. Web error responses do not set `Content-Security-Policy` or any security headers [MED]

`propstore/web/routing.py:454-508`. Error responses are `HTMLResponse` / `JSONResponse` with no header customization. FastAPI defaults are minimal. For a localhost-only tool this is OK; for the `--host 0.0.0.0` case (finding 4) this matters.

### 20. Accessibility: solid bones, missing affordances [MED]

`propstore/web/html.py` builds HTML with:

- `<html lang="en">` — good (`html.py:320`).
- `<main>` landmark, `<section aria-labelledby=…>`, `<th scope="col">`, `<dl>` for key/value summary — all good.
- `_link_table` enforces correct cell count or raises `ValueError` (`html.py:473-475`).

What is missing from a screen-reader perspective (Q is blind, so this matters):

- **No skip-link.** `_page` (`html.py:318-332`) writes `<body><main>...` directly. There is no `<a href="#main-content" class="skip-link">Skip to content</a>`. JAWS/NVDA users land on the document root and have to walk every header to reach the table. Add a skip-link that targets `<main id="main-content">`.
- **No `aria-current` on the focused claim/concept link.** When navigating from the index to a claim, returning to the index gives no indication of "where I was". A persistent breadcrumb or `aria-current="page"` annotation would help.
- **Tables lack `<caption>`.** `_table` and `_link_table` (`html.py:449-481`) emit `<thead>` only. A caption summarizing "Claim inventory, 47 rows" would orient screen-reader users immediately.
- **Empty tables emit a single bogus row** (`html.py:451, 466-468`) with `"none"` and `"not applicable"` filler. This is not announced as an empty state — it reads like real data. Better: emit `<p>No claims match the current filter.</p>` instead of a fake table row.
- **Filter values rendered as `dt`/`dd`.** A user cannot tell from the markup whether `Query: none` means "no query was supplied" or "the literal string 'none'". The filter section should distinguish, e.g. `<dd><em>(no filter)</em></dd>`.
- **`_state_label` strips underscores for display** (`html.py:551-552`) but not for ARIA. State `"build_blocked"` becomes `"build blocked"` in the visible cell — fine. But the underlying status appears in many places (`status.state`, `value_summary.state`, etc.) and the same string is used for both `aria-labelledby` ids and human display. Mostly harmless, just noting the dual use.
- **No focus-visible styling on table rows.** `web.css:77-80` only handles `a:focus-visible`. Rows are not focusable, but there is no clear visual cue when navigating links inside a row.
- **`color-scheme: light` only** (`web.css:6`). No `prefers-color-scheme: dark` block. A blind user does not care, but a low-vision user does.

Severity: MED collectively. Each item alone is LOW; together they are the difference between "technically passes WCAG landmark checks" and "actually pleasant for a blind user."

### 21. `to_json_compatible` raises on plain dict, but reports use them [LOW → potential HIGH]

`propstore/web/serialization.py:17-36` lists supported types: `None, bool, int, float, str, Enum, Path, tuple|list, dataclass`. **Plain `dict` raises `WebSerializationError`.** The route handlers feed dataclass reports through this serializer. Reports built by `propstore/app/...` are dataclasses, so the common case works. But:

- `propstore/observatory.py:296-312` declares `operator_summaries: Mapping[str, OperatorFamilySummary]` and `__post_init__` stores it as a `dict`. If observatory results were ever returned through the web layer (they aren't today, per the route table at `propstore/web/routing.py:84-170`), serialization would explode at runtime.
- Any future field of type `dict[str, X]` on any app report will silently fail in production rather than at design time. Add a unit test that introspects every dataclass field type used by routed reports and asserts `dict` doesn't appear, or extend the serializer to handle `dict` (recursively, with str keys).

### 22. `Repository.find(None)` behavior at request time is undefined here [LOW]

`propstore/web/routing.py:424-426`. If the user starts the server outside any propstore tree, every request raises whatever `Repository.find` raises. The error path goes through `_EXPECTED_WEB_ERRORS` which does NOT include the Repository lookup error type, so it propagates as a 500 with a stack trace. Better: catch at startup and refuse to serve, or render a 503 with an explanation.

## Contract enforcement reality

`propstore/contracts.py` and `propstore/contract_manifests/semantic-contracts.yaml` are governed exclusively at test time:

- `tests/test_contract_manifest.py:128-132` asserts `build_propstore_contract_manifest().to_yaml() == checked-in-bytes`.
- `tests/test_contract_manifest.py:135-152` runs `git show HEAD:semantic-contracts.yaml` and calls `quire.contracts.check_contract_manifest(previous, current)` — this gates version bumps in CI.
- No runtime code path imports `CONTRACT_MANIFEST_PATH` or `build_propstore_contract_manifest` outside the test (verified by Grep). The manifest is documentation that fails CI when out of sync; it does not enforce behavior at compile or query time.

Implication: a developer can change a `Family.contract_version` and a behavior-affecting field in the same commit. The test will catch the mismatch (good), but no invariant prevents an artifact written under v1 from being read under v2. That story lives in `quire`, not here. Outside this cluster's scope to verify.

`docs/application-layer-and-undo.md` says contract enforcement should also include `expected_head` checks, dependency tracking, and conflict classification. None of that exists yet. Treat the manifest as "schema fingerprint", not as "behavioral contract".

## README/docs vs code drift

Confirmed and severity-ranked:

| Drift | Location | Reality | Severity |
|---|---|---|---|
| `pks promote` documented as top-level | `README.md:166` | Only `pks proposal promote` and `pks source promote` exist | HIGH |
| `pks world atms-status` / `atms-interventions` | `README.md:198-200` | Subcommands under `pks world atms` group | HIGH |
| `pks world revision-base` / `revise` / `iterated-revise` | `README.md:206-208` | Subcommands under `pks world revision` group | HIGH |
| `pks import-repo` | `docs/cli-reference.md:109` (per index) | Command is registered as `import-repository` (`propstore/cli/__init__.py:23-27`); the `import-repo` shortcut does not exist | HIGH |
| Application layer + undo described as built | `docs/application-layer-and-undo.md` | `propstore.application` package missing, no `pks undo`/`redo` | HIGH |
| `forms` alias documented? | `propstore/cli/__init__.py:47-49` | Only one alias, `forms → form`. README never references this | LOW |
| Demo path `.tmp-reasoning-demo/knowledge` | `README.md:117-126` | Requires `scripts/materialize_reasoning_demo.py`; `.tmp-reasoning-demo/` is untracked per `git status` and likely not pre-built. New users will hit "no such repo" if they skip step 1 | LOW |

## Demo failure modes

`propstore/demo/reasoning_demo.py`:

- Imports `propstore.app.project_init._seed_form_documents` (line 19). Leading underscore = private API. The demo reaches into private app-layer surface; any internal refactor of `project_init` without touching the demo will break it silently (the demo is only exercised via the script and by `test_web_demo_fixture.py` per the test directory listing).
- `materialize_reasoning_demo` calls `Repository.init(root)` unconditionally (line 24, via `_initialize_repo`). If `root` already exists as a propstore repo the behavior depends on `Repository.init` — not verified. The README/script README implies `--force` wipes; the demo function itself has no `--force` parameter.
- `repo.git is None` check (line 38) raises `RuntimeError`, not a Click exception. Fine because this is a script entry, but the wrapping `scripts/materialize_reasoning_demo.py` may not translate it into a useful exit code. Did not read that script.
- Hardcoded text payloads use literal artifact ids and concept names. There is no version-pinning of the form schema the demo expects; if `_seed_form_documents` evolves, the demo's claims may stop validating.

## Observatory metrics correctness

`propstore/observatory.py`:

- `EvaluationScenario.__post_init__` (line 132) sorts and dedupes `falsification_ids`: `tuple(sorted(_strings(self.falsification_ids)))`. `len(falsification_ids)` is therefore the **unique** falsification count, not the raw count. If the same falsification id is observed twice (e.g. one rule fired twice), the metric undercounts. `OperatorFamilySummary.falsification_count = sum(len(item.falsification_ids) for item in items)` (line 365) inherits the undercount.
- `ScenarioEvaluation.from_scenario` (line 194-202) is a pure shovel: it copies `replay_result_hash` and `falsification_ids` from the scenario to the result. **The "evaluator" performs no evaluation.** A scenario file declares its own "did I pass" via `falsification_ids`. The harness has no notion of running the operators against fixtures and computing falsification ids itself. This is observatory-as-documentation, not observatory-as-test. Whether that is intended is a question for Q.
- `_check_hash` (line 376-379) only verifies `content_hash` if it is present in the input dict. Inputs without `content_hash` are accepted silently. For an audit trail this is acceptable; for tamper-evident scenarios it is not.
- `OperatorFamilySummary.__post_init__` (line 261) sorts `replay_result_hashes`. The summary therefore loses any per-scenario ordering — fine for an opaque summary, but downstream consumers cannot zip `scenario_results` against `replay_result_hashes` reliably.
- `ObservatoryReport.to_dict` walks `operator_summaries` via `sorted(self.operator_summaries.items())` (line 348) — good, deterministic.

Severity: the falsification-undercount and pure-shovel design are both MED-impact correctness questions. Neither is a bug if "falsification id" is defined as "kind of falsification" rather than "occurrence count" — but the names suggest occurrence counts.

## Permission boundary issues

- `propstore/cli/web.py:32-34` writes nothing; serves only. Good.
- `pks materialize` writes loose files into `directory`; `--clean` deletes "stale" ones. CLI does no path-containment check (finding 14). The actual safety probably lives in `propstore/app/materialize.py` — flag for cluster covering app/.
- `pks sidecar query` is read-only via `query_only=ON`. Good.
- `pks source stamp-provenance` writes to a user-supplied `--file` outside the repo without a containment check. Flagged in finding 6 as deprecated; while it lives, it is the only CLI surface with arbitrary external write.
- `_LazyRepository` (`propstore/cli/__init__.py:52-65`) defers Repository construction until first attribute access. Fine, but means errors in `Repository.find` surface in surprising places (e.g. inside command bodies, not at CLI parse time). Affects exit-code uniformity.

## User-input validation at the trust boundary

CLI:

- `parse_kv_pairs` and `parse_world_binding_args`: see findings 9-10.
- `_coerce_cli_scalar` (`helpers.py:38-59`) silently coerces `"1.0e10000"` via `float(value)` to `inf` without warning. Users who pass numeric strings expecting strings get inf/nan in the dict. Limited blast radius (only when `coerce=True` is opted into) but worth flagging.
- `pks observatory run`: see finding 12.
- `pks world hypothetical --add` (`propstore/cli/world/analysis.py:104, 119`) parses arbitrary JSON via `_parse_hypothetical_add` (not read but referenced). User can inject any structure; downstream validation depends on app layer. Did not trace.
- `pks world revision`: `_parse_revision_atom_json` (`propstore/cli/world/revision.py:63-70`) checks the top-level is a dict; otherwise raises ClickException. Does not validate field types; downstream will catch.

Web (all `GET`):

- `claim_id` and `concept_id` are path params with no length cap, no regex. URL-quoted on the way out (`html.py`); fine for HTML safety. The risk is downstream: a 500-character claim_id may hit DB query limits or sidecar code paths not designed for it. No DOS protection.
- `q` (free-text search) is unbounded in length. `limit` is clamped 1–500. Good.
- Render policy floats: see finding 17.

## Bugs (HIGH/MED/LOW)

### HIGH

- H1: README documents `pks promote`, `pks world atms-status`, `pks world revision-base`, `pks world revise`, `pks world iterated-revise`. None exist. (`README.md:166, 198-208`)
- H2: `docs/application-layer-and-undo.md` describes a `propstore.application` package and `pks undo`/`redo` workflow that is entirely unimplemented. Doc should be tagged "proposal" or moved.
- H3: `pks web --host 0.0.0.0` exposes a no-auth read-only knowledge browser to the LAN. No warning, no opt-in flag, no security headers. (`propstore/cli/web.py:11-46`, `propstore/web/app.py`)
- H4: Render-policy floats on web routes (`pessimism_index`, `praf_epsilon`, `praf_confidence`) accept any float including NaN/inf and out-of-range values. (`propstore/web/requests.py:58-69`)

### MED

- M1: Inconsistent exit codes — `EXIT_VALIDATION` defined but underused; many user-input errors land on `EXIT_ERROR=1`. (`propstore/cli/helpers.py`, callers across CLI)
- M2: `parse_world_binding_args` silently drops middle non-`=` tokens. (`propstore/cli/world/__init__.py:22-35`)
- M3: `pks source stamp-provenance` deprecated yet still mutates files; warning is non-fatal. Inconsistent `pass_obj` decoration. (`propstore/cli/source/lifecycle.py:188-221`)
- M4: `_repo_from_request` re-runs `Repository.find` per HTTP request. Possible handle leak / hot path. (`propstore/web/routing.py:424-426`)
- M5: Web error responses set no security headers. Combined with H3, lethal off loopback. (`propstore/web/routing.py:454-508`)
- M6: A11y gaps: no skip-link, no `<caption>`, empty-table rendered as bogus row, no `aria-current`. (`propstore/web/html.py:318, 449-481`)
- M7: `pks materialize` `directory` arg has no containment check; `--clean` deletes inside whatever path is given. (`propstore/cli/materialize.py:14-37`)
- M8: Observatory `falsification_count` deduplicates ids, undercounting if the harness ever produces multi-occurrence ids. The "evaluator" performs no actual evaluation — pure shovel from scenario to result. (`propstore/observatory.py:132, 194-202, 365`)
- M9: `to_json_compatible` does not handle `dict`; future report fields with `dict` shapes will explode at runtime instead of build time. (`propstore/web/serialization.py:17-36`)
- M10: `pks observatory run --fixture` schema errors surface as raw `ValueError` text; no guidance on which field. (`propstore/cli/observatory.py:51-61`)

### LOW

- L1: `pks world bind key=` accepts empty value silently. (`propstore/cli/world/__init__.py:22-35`)
- L2: `pks observatory run --format text` drops falsification ids; users must re-run with `--format json`. (`propstore/cli/observatory.py:64-75`)
- L3: Empty `propstore/web/templates/` directory is misleading (HTML is f-string composed in `html.py`).
- L4: `_coerce_cli_scalar` silently turns numeric overflow into inf. (`propstore/cli/helpers.py:38-59`)
- L5: `_LazyCLIGroup.get_command` raises `TypeError` on misregistration rather than a Click error. (`propstore/cli/__init__.py:80-82`)
- L6: Demo reaches into private `_seed_form_documents`. (`propstore/demo/reasoning_demo.py:19`)
- L7: `RuntimeError` in demo for missing git is not converted to a Click failure. Fine because demo is not Click-mounted, but worth noting if it ever is. (`propstore/demo/reasoning_demo.py:38-39`)
- L8: `propstore/cli/__init__.py` builds `_COMMANDS` as a plain dict; no validation that all attributes resolve at startup. Lazy resolution defers errors. Defensive but trade-off.

## Open questions for Q

1. **Application layer & undo doc**: is `docs/application-layer-and-undo.md` an aspirational design (in which case it should move to `proposals/` or be top-banner-tagged "unimplemented"), or is implementation in flight on a branch I cannot see?
2. **README drift severity**: do you want me to enumerate the exact README lines that need rewriting, or open a separate doc-fix PR? The five HIGH-severity README claims are plausibly all from a stale revision before the `world atms` and `world revision` subgroups were introduced.
3. **`pks web --host 0.0.0.0`**: should non-loopback bind require an explicit `--insecure` flag? Or is the assumption "users only run this on localhost" load-bearing? The current state is "easy to footgun".
4. **Observatory semantics**: is `falsification_ids` meant to be a set of distinct falsification kinds, or an occurrence list? Today it is normalized to a set; the count is therefore unique-count, not occurrence-count. If the latter is intended, `__post_init__` needs to stop sorting/deduping.
5. **`pks sidecar query`**: any appetite for adding an automatic `LIMIT` cap or a `--max-rows` flag? Current code happily fetches a cross-join into memory.
6. **A11y baseline**: Q is blind, so I called out the missing skip-link, table caption, empty-state handling, and `aria-current`. Is there a list of accepted a11y deviations, or do you want every WCAG 2.1 AA gap surfaced?
7. **`pks world bind` parser**: should multiple non-`=` tokens be a hard error, or do you want positional concept after bindings to remain "first one wins" (currently last one wins, silently)?
8. **Contract manifest**: is the test-only enforcement intentional, or is there an expectation that runtime code consults the manifest for compatibility checks (e.g. when reading older sidecars)?
9. **`pks source stamp-provenance`**: ready to delete, or still depended on by an external workflow?
10. **Demo private import**: should `_seed_form_documents` be promoted to public app surface, or should the demo be rewritten to use the public `init_source`/transaction path?
