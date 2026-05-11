# WS-N: Architecture / import-linter / contract enforcement / rename discipline

**Status**: SUPERSEDED BY WS-N1 + WS-N2 per D-26. See `WS-N1-architecture-immediate.md` and `WS-N2-architecture-layered.md`. Content below is preserved for git history; do not work from it.

---

**Status (original)**: OPEN
**Depends on**: WS-K (heuristic location — moves embed/classify/relate/calibrate under `propstore/heuristic/` so the layered contract has a real Layer-3 namespace to bind)
**Blocks**: nothing — terminal workstream for the architecture-decoration tier
**Owner**: SUPERSEDED — see WS-N1 and WS-N2 per D-26.

---

## Why this workstream exists

The repository has a stated six-layer architecture (README.md:11-13) and a stated CLI/owner separation (AGENTS.md:39-46), an `import-linter` configuration, and a phase-4-layers test that shells out to `lint-imports`. Together, these look like enforcement. They are not. They are decoration.

- The four contracts in `.importlinter` are all `forbidden` (not `layered`), each over a single direction nothing currently imports. Cluster U verified: `storage->merge`, `source->heuristic`, `core.lemon->argumentation`, `worldline->support_revision` are vacuously satisfied.
- `tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py` asserts only that `lint-imports` returns 0. No test says "if a known violation existed, the linter would catch it." The linter is green for the wrong reason.
- App-layer request objects accept CLI-shaped string payloads (`*_json`, comma-separated values, `dimensionless: str`) and raise errors that name CLI flags (`--dimensions`, `--revision-atom`, `--values`). CLI ownership has leaked one layer down.
- Owner modules (`sidecar/build.py`, `provenance/__init__.py`, `contracts.py`) write to `sys.stderr` and own argv parsing. Owners should return reports; CLI should print.
- Three modules carry duplicate `_canonical_json` implementations with `default=str` (Cluster J already established that's wrong for content-hashing).
- The `# fallback`, `# backwards compatibility`, `# old data`, `_CONCEPT_STATUS_ALIASES`, `CONFIDENCE_FALLBACK`, and the dead `propstore/aspic_bridge.py` strict entry violate Q's "no old repos, iterate to perfection" rule. **Per D-3, every one comes out in this workstream — no carve-out, no aliases.**
- Two type/term names commit to stances the storage layer is forbidden from collapsing. `WorldModel` reads "singular committed view" when actual semantics support multi-extension reasoning, hypotheticals, ATMS branching. `verdict` (five docstring sites) is judicial-commitment language inside non-commitment modules. **Per D-4 and D-5, both rename via rope, no legacy alias.**

WS-N closes the gap between *stated* architecture (six layers, CLI/owner separation, no shims, non-commitment naming) and *enforced* architecture (layered contract, app-boundary gate, owner-stream gate, one-pass shim sweep, two rename passes).

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed is gone from `gaps.md` and has a green test gating it. The right column reflects the locked-in decision from `reviews/2026-04-26-claude/DECISIONS.md`.

| Finding | Source | Citation | Decided |
|---|---|---|---|
| **T0.3** | Claude REMEDIATION-PLAN | `.importlinter:5-36` | Add a negative test that injects a known violation and asserts `lint-imports` rejects it. |
| **T5.3** | Claude REMEDIATION-PLAN / Cluster U | `.importlinter:5-36` | Replace four `forbidden` contracts with one `layered` contract over the six README layers. |
| **T5.4** | Claude REMEDIATION-PLAN | `propstore/app/forms.py:48-57`, `:241-277`; `propstore/app/concepts/mutation.py:252-260`, `:1084-1097`; `propstore/app/worldlines.py:82-89`, `:367-377`; `propstore/app/world_revision.py:138-146` | App-layer request objects accept CLI-shaped payloads. Strip and retype. |
| **T5.5** | Claude REMEDIATION-PLAN | `propstore/sidecar/build.py:467-480`, `propstore/provenance/__init__.py:428`, `propstore/contracts.py:287-301` | Owner modules write to stderr or own argv parsing. Return typed reports instead. |
| **T5.6** | Claude REMEDIATION-PLAN / Cluster S | `propstore/observatory.py:34-41`, `propstore/policies.py:42-49`, `propstore/epistemic_process.py:50-57` | Three duplicate `_canonical_json` implementations collapse to one (use `quire.hashing`). |
| **T5.8 / D-3** | Claude REMEDIATION-PLAN / Cluster U | see "Shim inventory" below | **Decided: delete every shim, no carve-out, callers updated in the same pass, no aliases.** |
| **D-4** | Cluster U §"Naming"; DECISIONS.md | `propstore/world/model.py:201` (`class WorldModel(WorldStore):`); ~1019 occurrences across 133 files | **Decided: rename `WorldModel` → `WorldQuery` via rope. No legacy alias.** |
| **D-5** | Cluster U §"Naming" #3; DECISIONS.md | `propstore/grounding/grounder.py:42`, `:102`; `propstore/sidecar/rules.py:20`, `:129`, `:243` | **Decided: rename the `verdict` prose noun → `grounded classification` (and the type-style `Verdict` reference where it appears in cluster-U findings) via rope-driven textual rename. No legacy alias.** |
| **Codex #38** | `reviews/2026-04-26-codex/workstreams/ws-07-cli-architecture-and-gates.md` | `propstore/app/forms.py`, `propstore/app/concepts/mutation.py` | App request shape gate: forbid CLI-shaped names in app dataclasses. |
| **Codex #39** | `reviews/2026-04-26-codex/workstreams/ws-07-cli-architecture-and-gates.md` | `propstore/app/worldlines.py`, `propstore/app/world_revision.py` | CLI flag text gate: forbid `--flag` strings in app-layer error messages. |
| **Codex #40** | `reviews/2026-04-26-codex/workstreams/ws-07-cli-architecture-and-gates.md` | `propstore/sidecar/build.py:467-480`, `propstore/provenance/__init__.py:428`, `propstore/contracts.py:287-301` | Process-stream gate: forbid `print(..., file=sys.stderr)`, `sys.exit`, and `argparse`/`click` imports in owner modules. |

Adjacent findings closed in the same PR (cheaper here than later):

| Finding | Citation | Why included |
|---|---|---|
| Stale design briefings | `algorithms.md:13-37`, `aspic.md:13` | These name modules that don't exist (`validate_claims.py`, `conflict_detector.py` flat module, `build_sidecar.py`, `world_model.py`, `description_generator.py`, `propagation.py`, `_resolve_stance`). Move to `docs/historical/` or delete. |
| Doc internal contradiction | `docs/integration.md:38-44` says "automated — no human review required"; `:62` says "concept and claim proposals must be manually reviewed and moved." | Same review pass. |
| Doc admits silent drop | `docs/structured-argumentation.md:25` documents "Rules where premise or conclusion literals are missing… are silently dropped." | Either fix the behavior (drop with diagnostic) or stop admitting it; either way, ASPIC fidelity belongs in WS-F, but the *doc* update lands here. |
| Stub doc | `docs/epistemic-operating-system.md` (46-line stub) | Either flesh out or move to `docs/historical/`. |
| Stale boundary doc | `docs/argumentation-package-boundary.md:64` claims "the old propstore module paths are deleted" while `pyproject.toml:65` still names `propstore/aspic_bridge.py`. | Same pass. |

## Resolved decisions (formerly "Open questions for Q")

Decided in `reviews/2026-04-26-claude/DECISIONS.md`, now locked-in scope.

- **D-3 — Old-data shims**: **delete all, no carve-out**. `_CONCEPT_STATUS_ALIASES`, `DecisionValueSource.CONFIDENCE_FALLBACK` (enum value + the path that returns it), `world/types.py:1275` old-data fallback path, `classify.py:389` "fallback to whole response as forward" branch, `grounding/grounder.py:141-149` "backwards compatibility" block, `pyproject.toml:65` dead `aspic_bridge.py` strict entry — all out in one sweep, callers updated same commit, no aliases.
- **D-4 — `WorldModel` rename**: **rename to `WorldQuery` via rope**. ~1019 occurrences across 133 files (29 in `tests/test_world_model.py` alone). Single PR, mechanical rope rename, no legacy alias.
- **D-5 — `Verdict` rename**: **rename to `GroundedClassification`**. The cited references (`grounding/grounder.py:42, 102`; `sidecar/rules.py:20, 129, 243`) are docstring/prose uses of the noun `verdict` — `grep "class Verdict"` returns zero hits, so there is no class to rename. Replace the prose noun with `grounded classification` at those five sites. If a `Verdict` *symbol* surfaces during the rope pass (forgotten enum value, type alias, function-arg name), rope renames it to `GroundedClassification`/`grounded_classification`.

## Code references (verified by direct read)

### Import-linter contract surface (the decoration)

`C:\Users\Q\code\propstore\.importlinter` (repo root, not `propstore/.importlinter`) holds exactly four `forbidden` contracts: `storage→merge`, `source→heuristic`, `core.lemon→argumentation`, `worldline→support_revision`. Per Cluster U §"Import-linter contracts" verbatim: every one is *vacuously satisfied today*. The reverse direction is the actual dependency in three of four cases (`merge → storage` at `propstore/merge/structured_merge.py:18`; `heuristic → source` at `propstore/heuristic/source_trust.py:14`). `core.lemon` has zero imports of `argumentation.*`; `worldline` has zero imports of `support_revision`.

`tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py` is 21 lines, single test, asserts only `result.returncode == 0`. No companion negative test.

### Rename targets (D-4, D-5)

`propstore/world/model.py:201` — `class WorldModel(WorldStore):`. Single class. Re-exported via `propstore/world/__init__.py:2` and `propstore/__init__.py:3`. ~1019 occurrences across 133 files; `tests/test_world_model.py` alone has 29.

`verdict`-as-domain-noun appears at the five sites named in cluster U:
- `grounding/grounder.py:42` — `the storage layer never silently collapses a verdict.`
- `grounding/grounder.py:102` — `non-commitment anchor: storage never silently collapses a verdict...`
- `sidecar/rules.py:20` — `storage never silently collapses a verdict.`
- `sidecar/rules.py:129` — `an empty inner set is still a *verdict*...`
- `sidecar/rules.py:243` — `Storage never silently drops a verdict...`

`grep "class Verdict"` returns zero hits — there is no class to rename. Renaming "verdict" → "grounded classification" preserves the non-commitment promise while removing judicial framing.

### App-layer CLI-shape leakage

`propstore/app/forms.py:48-57` — `FormAddRequest` has three CLI-shaped fields: `dimensions_json`, `dimensionless: str`, `common_alternatives_json`. `:234-277` parses via `_parse_json_option(... option_name="--dimensions")` and raises `FormWorkflowError("--dimensions must decode to a JSON object")`, `option_name="--common-alternatives"`.

`propstore/app/concepts/mutation.py:252-260` — `ConceptAddRequest.values: str | None` is comma-separated. `:1084-1097` parses with `request.values.split(",")` and raises errors quoting `--values` and `--closed`.

`propstore/app/worldlines.py:82-89` — `parse_worldline_revision_atom` raises `WorldlineValidationError(f"Invalid --revision-atom JSON: {exc}")`. `:367-377` raises `"--revision-atom is required..."`, `"--revision-target is required..."`, `"--revision-operator is required..."`.

`propstore/app/world_revision.py:138-146` — raises `"--atom is required for --operation expand"`, `"--target is required for --operation contract"`, `"--atom is required for --operation revise"`.

### Owner-module process-stream and argv ownership

`propstore/contracts.py:287-301` — owner module owning argv parsing: builds `argparse.ArgumentParser`, calls `parser.parse_args(argv)`, writes via `CONTRACT_MANIFEST_PATH.write_bytes(payload)` or `print(payload.decode("utf-8"), end="")`, ends `if __name__ == "__main__": raise SystemExit(main())`.

`propstore/sidecar/build.py:467-480` — function-local `import sys` then `print("  Embedding snapshot: ...", file=sys.stderr)`.

`propstore/provenance/__init__.py:428` — `print(f"Unsupported file type: {path.suffix}", file=sys.stderr); return False`.

### Duplicate `_canonical_json` implementations

`propstore/observatory.py:34-41`, `propstore/policies.py:42-49`, `propstore/epistemic_process.py:50-57` — three byte-equivalent copies, all with `sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str`. Cluster J flagged `default=str` as wrong for content-hashing. WS-J fixes semantics; WS-N collapses call sites to `from quire.hashing import canonical_json`.

### Shim inventory (each is `git rm` work — D-3)

| Surface | File:Line | Verbatim / shape |
|---|---|---|
| `_CONCEPT_STATUS_ALIASES` | `propstore/core/concept_status.py:13-15` | `_CONCEPT_STATUS_ALIASES = {"active": ConceptStatus.ACCEPTED}`. Used in `coerce_concept_status` to silently coerce legacy `"active"` strings. No comment, no deprecation note, no doc reference. |
| `DecisionValueSource.CONFIDENCE_FALLBACK` | `propstore/world/types.py:1206` | First-class enum value. Three test files reference it. |
| Old-data fallback path | `propstore/world/types.py:1275-1281` | `# Fall back to raw confidence when opinion is missing (old data).` followed by an active branch returning `CONFIDENCE_FALLBACK`. |
| Old-data docstring concession | `propstore/world/types.py:1239` | `opinion_b/d/u/a: Opinion components (may be None for old data)`. |
| Whole-response-as-forward fallback | `propstore/classify.py:389` | `forward_raw = result.get("forward", result)  # fallback: treat whole response as forward`. |
| Backwards-compat block | `propstore/grounding/grounder.py:141-149` | Docstring: `Defaults to False for backwards compatibility — existing callers pay no argument-enumeration cost.` |
| Dead pyright-strict entry | `pyproject.toml:65` | `"propstore/aspic_bridge.py"` listed in `tool.pyright.strict` but the file does not exist (the package is `propstore/aspic_bridge/`). The strict-mode entry silently does nothing. |

AGENTS.md:21-22 ("Do not add compatibility shims, aliases, fallback readers, bridge normalizers, or dual-path glue") and Q's `feedback_no_fallbacks` memory both forbid these.

### Doc drift to clean up

- `algorithms.md:13-37` references `propstore/validate_claims.py`, `propstore/conflict_detector.py` (flat module), `propstore/build_sidecar.py`, `propstore/world_model.py`, `propstore/description_generator.py`, `propstore/propagation.py` — none exist.
- `aspic.md:13` references `_resolve_stance` in `propstore/world/resolution.py` — function name has changed to `_resolve_recency`, `_resolve_sample_size`.
- `docs/integration.md:38-44` says reconciliation "is automated — no human review required" while `:62` says "concept and claim proposals must be manually reviewed and moved." Internal contradiction.
- `docs/structured-argumentation.md:25` admits "Rules where premise or conclusion literals are missing… are silently dropped."
- `docs/epistemic-operating-system.md` is a 46-line stub.
- `docs/argumentation-package-boundary.md:64` says "the old propstore module paths are deleted" — but `pyproject.toml:65` keeps the dead path alive. Same drift the strict-entry shim records.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_import_linter_negative.py`** (new — T0.3 gate)
   - Programmatically writes a temp module under a sandboxed copy of `propstore/` that introduces a known violation: e.g. inject `import propstore.merge` into a synthetic `propstore.storage._test_violation` module.
   - Runs `lint-imports` against the sandboxed root.
   - Asserts return code is non-zero AND stdout/stderr names the violated contract.
   - **Must fail today** if sandboxed against an arbitrary cross-layer edge: the four `forbidden` contracts only catch four specific edges, so an injected `propstore.app -> propstore.cli` violation is *not* caught — confirming weakness #2 in Cluster U: the contracts are spot-checks, not a layered invariant.
   - The negative test runs once per declared contract edge AND once per layered-edge expectation (after T5.3 lands).

2. **`tests/test_layered_contract_covers_six_readme_layers.py`** (new — T5.3 gate)
   - Parses `.importlinter` via `configparser`.
   - Asserts exactly one contract of `type = layers`.
   - Asserts the layer list matches the README's six layers in order: `propstore.storage`, `propstore.source`, `propstore.heuristic`, `propstore.argumentation` / `propstore.aspic_bridge` / `propstore.world` / `propstore.belief_set` (the typed-reasoning layer), `propstore.app`, `propstore.web` / `propstore.cli`.
   - **Must fail today**: `.importlinter` has zero `layers` contracts.

3. **`tests/test_app_layer_no_cli_payloads.py`** (new — T5.4 / Codex #38 gate)
   - AST-walks `propstore/app/`.
   - For every `dataclass` whose name ends in `Request`, asserts no field name ends in `_json`, no field name is `dimensionless` of type `str`, no field name is `values` of type `str` where the dataclass also has a `form_name` or other typed sibling, and no field accepts a stringly-typed CLI option payload.
   - **Must fail today**: `FormAddRequest.dimensions_json`, `FormAddRequest.dimensionless: str`, `FormAddRequest.common_alternatives_json`, `ConceptAddRequest.values: str`, `WorldlineRevisionOptions.atom: str`-shaped paths are all violations.
   - Allow-list mechanism: a single registered exemption file with a one-line justification per entry, and the gate counts exemption entries — must shrink to zero by WS-N close.

4. **`tests/test_no_cli_flags_in_owner_errors.py`** (new — T5.4 / Codex #39 gate)
   - AST + text scan of `propstore/app/`, `propstore/source/`, `propstore/world/`, `propstore/sidecar/`, `propstore/heuristic/`, `propstore/storage/`.
   - For every string literal in an `Exception(...)`, `raise X(...)`, or returned diagnostic, fail if it contains `--<word>`.
   - **Must fail today**: every flag-named error in `app/forms.py:238`, `:249`, `:271-273`; `app/concepts/mutation.py:1086-1097`; `app/worldlines.py:88-89`, `:373-377`; `app/world_revision.py:142-146`.

5. **`tests/test_no_process_streams_in_owners.py`** (new — T5.5 / Codex #40 gate)
   - AST scan of all packages outside `propstore/cli/` and `propstore/web/` and registered script wrappers.
   - Fail on any `print(..., file=sys.stderr)`, `sys.exit(...)`, `import argparse`, `import click`.
   - **Must fail today**: `propstore/sidecar/build.py:475-480` (stderr); `propstore/provenance/__init__.py:428` (stderr); `propstore/contracts.py:287-301` (argparse + SystemExit + print).

6. **`tests/test_canonical_json_single_source.py`** (new — T5.6 gate)
   - AST-walks the repo. Counts `def _canonical_json(` definitions. Asserts there is exactly one (the one in `quire.hashing`, not local).
   - For every call site of a local `_canonical_json`, asserts the import is `from quire.hashing import canonical_json` (the public name) and the call is `canonical_json(...)`.
   - **Must fail today**: three definitions exist (`observatory.py:34`, `policies.py:42`, `epistemic_process.py:50`), all with `default=str`.

7. **`tests/test_no_old_data_shims.py`** (new — D-3 gate)
   - Static lookups for **every** named D-3 surface:
     - Symbol `_CONCEPT_STATUS_ALIASES` does not appear in `propstore/core/concept_status.py` (or anywhere in `propstore/`).
     - Symbol `CONFIDENCE_FALLBACK` does not appear in `propstore/world/types.py`. The `DecisionValueSource` enum's `__members__` does not contain a `CONFIDENCE_FALLBACK` key.
     - The literal docstring fragment `(may be None for old data)` does not appear in `propstore/world/types.py`.
     - The literal comment `# Fall back to raw confidence when opinion is missing (old data).` does not appear in `propstore/world/types.py`.
     - The literal `# fallback: treat whole response as forward` does not appear in `propstore/classify.py`.
     - The literal `for backwards compatibility — existing callers pay no argument-enumeration cost` does not appear in `propstore/grounding/grounder.py`.
     - The literal `"propstore/aspic_bridge.py"` does not appear in `pyproject.toml`.
   - Each absent → pass. Any present → fail with a one-line reason citing AGENTS.md:21-22 and the D-3 decision in DECISIONS.md.
   - **Must fail today**: all seven are present at the line numbers in the inventory above.

8. **`tests/test_worldmodel_renamed.py`** (new — D-4 gate)
   - Asserts `from propstore import WorldQuery` succeeds.
   - Asserts `WorldQuery.__module__` is `propstore.world.model` (or wherever the rope rename lands the canonical home — the test asserts the canonical module path, whatever it is, after step 9).
   - Asserts `from propstore import WorldModel` raises `ImportError`.
   - Asserts no module under `propstore/` exports a name `WorldModel` (walks `propstore.__path__`, imports each submodule, checks `vars(mod)`).
   - AST scan of `propstore/` and `tests/` for the identifier `WorldModel`: must be zero hits. (Skip strings inside `# noqa` allowlist if any survives — but the goal is zero hits.)
   - **Must fail today**: 1019 occurrences across 133 files, including `class WorldModel(WorldStore):` at `propstore/world/model.py:201` and 29 hits in `tests/test_world_model.py`. Per D-4: no legacy alias.

9. **`tests/test_verdict_renamed.py`** (new — D-5 gate)
   - Text scan of `propstore/grounding/`, `propstore/sidecar/`, `propstore/world/` source files for the lowercase noun `verdict` used as a domain term. Allowlist: occurrences inside literal citation strings (e.g. paper-section quotes that happen to contain the word in non-domain meanings — checked by hand at allowlist registration time, not auto-detected).
   - Asserts the five specific sites in the inventory above (`grounding/grounder.py:42, 102` and `sidecar/rules.py:20, 129, 243`) no longer contain the word `verdict`.
   - If a `Verdict` symbol surfaces during the rope pass — class, type alias, enum value, or dataclass field — assert it has been renamed to `GroundedClassification` (CamelCase) or `grounded_classification` (snake_case) at every binding site.
   - **Must fail today**: all five sites contain "verdict" verbatim.

10. **`tests/test_doc_drift_clean.py`** (new — adjacent finding gate)
    - Walks `algorithms.md`, `aspic.md`, `docs/integration.md`, `docs/structured-argumentation.md`, `docs/epistemic-operating-system.md`, `docs/argumentation-package-boundary.md`.
    - For each `propstore/<path>` reference in a backtick or path-shaped token, asserts the path exists in the repo OR the doc is under `docs/historical/`.
    - For `docs/integration.md` specifically: a small text check that the words "automated — no human review required" do not appear in the same file as "must be manually reviewed and moved."
    - **Must fail today**: `algorithms.md:13-37`, `aspic.md:13`, `docs/integration.md:38-44 vs :62`, `docs/argumentation-package-boundary.md:64`.

11. **`tests/test_workstream_n_done.py`** (new — gating sentinel)
    - `xfail` until WS-N closes; flips to `pass` on the final commit. Per Mechanism 2 in `REMEDIATION-PLAN.md` Part 2.

## Production change sequence

Each step lands in its own commit with a message of the form `WS-N step N — <slug>`.

### Step 1 — Negative test infrastructure (T0.3)
Land `tests/test_import_linter_negative.py` first, *before* changing any contract. Sandbox approach: copy `.importlinter` and `propstore/` into a tempdir, inject the synthetic violation, run `lint-imports`. Acceptance: synthetic violation rejected; return code != 0; contract name appears in output.

### Step 2 — Replace four `forbidden` with one `layered` (T5.3)
`.importlinter`:

```ini
[importlinter]
root_package = propstore
include_external_packages = True

[importlinter:contract:propstore-six-layers]
name = propstore six-layer architecture
type = layers
layers =
    propstore.web | propstore.cli
    propstore.app
    propstore.argumentation | propstore.aspic_bridge | propstore.world | propstore.belief_set
    propstore.heuristic
    propstore.source
    propstore.storage
containers =
    propstore
```

Run `lint-imports`. Expected fallout: every Cluster U "OBSERVED layering violations" entry surfaces. These are *real* violations the four-spot-check setup hid. They are out of scope for WS-N's *contract* work but in scope for WS-K. Acceptance: `tests/test_layered_contract_covers_six_readme_layers.py` turns green.

### Step 3 — App-layer typed requests (T5.4 / Codex #38, #39)
For each leak site:

- `FormAddRequest.dimensions_json: str | None` → `dimensions: Mapping[str, int] | None` (typed). `FormAddRequest.dimensionless: str | None` → `dimensionless: bool | None`. `FormAddRequest.common_alternatives_json: str | None` → `common_alternatives: tuple[FormAlternativeSpec, ...] | None`. JSON parsing moves to `propstore/cli/forms.py`.
- `ConceptAddRequest.values: str | None` → `values: tuple[str, ...] | None`. The `split(",")` parse moves to CLI.
- `parse_worldline_revision_atom` moves out of `propstore/app/worldlines.py` and into the CLI entry. The app-layer `WorldlineRevisionOptions.atom` becomes typed (`Mapping[str, JsonValue]`).
- `world_revision_explain` errors stop quoting `--atom`/`--target`/`--operation` and instead say `revision.atom`, `revision.target`, `operation`.

Update every CLI caller in one pass — per Q's `feedback_no_fallbacks` rule, no compatibility shim. Update web routes to construct typed app requests directly. Acceptance: `tests/test_app_layer_no_cli_payloads.py` and `tests/test_no_cli_flags_in_owner_errors.py` both turn green. Allow-list count = 0.

### Step 4 — Owner-stream typed reports (T5.5 / Codex #40)
- `propstore/sidecar/build.py:467-480`: introduce `EmbeddingSnapshotReport` (typed dataclass with model count, claim vec count, concept vec count). `build_repository` returns it. CLI renders it. Delete the `import sys` and `print(..., file=sys.stderr)`.
- `propstore/provenance/__init__.py:428`: `_stamp_path` returns a `StampResult | UnsupportedFileTypeFailure` discriminated union. CLI renders the failure to stderr.
- `propstore/contracts.py:287-301`: split into two files. `propstore/contracts.py` keeps `build_propstore_contract_manifest()` and `CONTRACT_MANIFEST_PATH` only — no `argparse`, no `print`, no `SystemExit`. `propstore/cli/commands/contracts.py` owns argv parsing, `--write` flag, and the `print` of the YAML.

Acceptance: `tests/test_no_process_streams_in_owners.py` turns green.

### Step 5 — Single canonical_json (T5.6)
Replace the three local `_canonical_json` definitions with `from quire.hashing import canonical_json`. Update call sites in `observatory.py`, `policies.py`, `epistemic_process.py`. WS-J handles the `default=str` semantic fix at the quire side; WS-N's responsibility is collapsing call sites so WS-J's fix lands once. Acceptance: `tests/test_canonical_json_single_source.py` turns green.

### Step 6 — Shim sweep (D-3 / T5.8)
Seven deletions, callers updated in the same commit per the "no old repos" rule:

1. `_CONCEPT_STATUS_ALIASES` deleted from `propstore/core/concept_status.py:13-15`. Any caller passing `"active"` updated to `"accepted"` in the same commit. If migration is required for stored data, *that* migration becomes its own gated workstream — but the runtime shim comes out unconditionally.
2. `DecisionValueSource.CONFIDENCE_FALLBACK` enum value removed from `propstore/world/types.py:1206`. The fallback path at `:1275-1281` deleted. The `apply_decision_criterion` function returns `DecisionValue(value=None, source=NO_DATA)` when opinion components are missing. Three test files asserting against `CONFIDENCE_FALLBACK` rewritten to assert `NO_DATA`, or deleted as obsolete if their reason for existing was the legacy path.
3. `propstore/world/types.py:1239` docstring `(may be None for old data)` removed; the docstring now states the precondition that opinion components are required, and the function raises if they are missing instead of synthesizing a fallback.
4. `propstore/classify.py:389` whole-response-as-forward fallback deleted. The branch that today silently treats a non-bidirectional LLM response as a forward stance now raises a typed `LLMOutputShapeUnknown` error, surfaced as a classification diagnostic rather than a synthesized `{"type":"none","strength":"weak"}` reverse.
5. `propstore/grounding/grounder.py:141-149` "for backwards compatibility" docstring block removed. The keyword default is whatever WS-K decides Block 3 of the gunray refactor lands on, but the prose comes out.
6. `pyproject.toml:65` `"propstore/aspic_bridge.py"` line removed. If the `aspic_bridge/` package should be in `tool.pyright.strict`, it goes in as `"propstore/aspic_bridge/"` or per-file entries.
7. The shim sweep runs in a single commit. No deprecation period. No `as` aliases. No `if hasattr(...)` callers.

Acceptance: `tests/test_no_old_data_shims.py` turns green.

### Step 7 — Rope-driven `WorldModel → WorldQuery` rename (D-4)
Rope is chosen because Q noted "we have rope" and its symbol-aware refactor is the only safe traversal of ~1019 occurrences across 133 files (imports, type annotations, isinstance checks, attribute accesses) without missing a docstring reference or a string literal in CLI help text.

1. Confirm `uv run python -c "import rope.base"` and clean working tree.
2. Run rope's rename refactor on `propstore/world/model.py:201`, target `WorldQuery`. Inspect preview: `tests/test_world_model.py` (29 hits), `propstore/__init__.py:3`, `propstore/world/__init__.py:2`, CLI help strings.
3. Apply. Trailing `Edit replace_all` pass covers any docstring prose / literal `"WorldModel"` strings rope leaves behind.
4. `git mv tests/test_world_model.py tests/test_world_query.py`. Rename fixture vars (`world_model_with_…` → `world_query_with_…`) via rope.
5. Update CLI help text / user-facing error messages: "world query" replaces "world model" in the `pks` surface.
6. **No legacy alias**. No `WorldModel = WorldQuery` re-export. No `from … import WorldQuery as WorldModel`. Per D-4: rope updates call sites in one pass, full stop.
7. Run `uv run pyright propstore` and `uv run lint-imports` — both must pass.

Acceptance: `tests/test_worldmodel_renamed.py` turns green; full suite has no new failures vs the WS-A baseline.

### Step 8 — `verdict` rename (D-5)
Smaller than D-4 — no `Verdict` class exists. Rope passes first; if any forgotten symbol named `Verdict` surfaces, rope renames it to `GroundedClassification`/`grounded_classification`. Then `Edit replace_all` rewrites the five docstring-noun sites:
- `silently collapses a verdict` → `silently collapses a grounded classification`
- `silently drops a verdict` → `silently drops a grounded classification`
- `is still a *verdict*` → `is still a *grounded classification*`

Allowlist file `tests/_allowlists/verdict_term.txt` (one line per remaining occurrence, one-sentence reason) for any genuinely-judicial citation context. Gate counts allowlist entries — must only shrink. **No legacy alias**.

Acceptance: `tests/test_verdict_renamed.py` turns green.

### Step 9 — Doc drift cleanup
- `algorithms.md` and `aspic.md`: move to `docs/historical/algorithms-pre-2026-04-26.md` and `docs/historical/aspic-pre-2026-04-26.md` with a one-line README pointer in each saying "see <current doc> for the current architecture." Or delete; either is acceptable.
- `docs/integration.md:38-44 vs :62`: reconcile against current code. Pick one truth.
- `docs/structured-argumentation.md:25`: change "are silently dropped" to "produce a `BridgeDiagnostic` and are excluded from the projection (tracked under WS-F)."
- `docs/epistemic-operating-system.md`: either flesh out (probably out of scope) or move to `docs/historical/`.
- `docs/argumentation-package-boundary.md:64`: re-verify after Step 6 deletes the `pyproject.toml:65` entry.

Acceptance: `tests/test_doc_drift_clean.py` turns green.

### Step 10 — Close gaps and gate
- Update `docs/gaps.md`: remove entries for the cluster-U findings; add a `# WS-N closed <sha>` line in the "Closed gaps" section.
- Flip `tests/test_workstream_n_done.py` from `xfail` to `pass`.
- Update this file's STATUS line to `CLOSED <sha>`.

## Acceptance gates

Before declaring WS-N done, ALL must hold:

- [ ] `uv run pyright propstore` — passes with 0 errors. (After Step 6, the `pyproject.toml` strict list is honest. After Steps 7-8, the renamed types resolve at every annotation site.)
- [ ] `uv run lint-imports` — passes with one `layered` contract instead of four `forbidden` contracts.
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-N tests/test_import_linter_negative.py tests/test_layered_contract_covers_six_readme_layers.py tests/test_app_layer_no_cli_payloads.py tests/test_no_cli_flags_in_owner_errors.py tests/test_no_process_streams_in_owners.py tests/test_canonical_json_single_source.py tests/test_no_old_data_shims.py tests/test_worldmodel_renamed.py tests/test_verdict_renamed.py tests/test_doc_drift_clean.py tests/test_workstream_n_done.py` — all green.
- [ ] Full suite `powershell -File scripts/run_logged_pytest.ps1` — no NEW failures vs the baseline.
- [ ] `propstore/contracts.py` no longer imports `argparse` and contains no `print(...)`.
- [ ] `propstore/sidecar/build.py` and `propstore/provenance/__init__.py` contain no `file=sys.stderr`.
- [ ] No file under `propstore/app/` raises an exception whose message contains `--<word>`.
- [ ] No file under `propstore/` contains the symbol `WorldModel` or the seven D-3 shim surfaces.
- [ ] The five cited docstring sites no longer contain the word `verdict` as a domain noun.
- [ ] `docs/gaps.md` has no open rows for the findings listed in the table at the top.
- [ ] This file's STATUS line is `CLOSED <sha>`.

## Done means done

WS-N closes when **every finding in the table at the top is closed**:

- T0.3, T5.3, T5.4, T5.5, T5.6, T5.8/D-3, D-4, D-5, Codex #38/#39/#40 — all eleven have a green test in CI.
- One `layered` contract over the six README layers; negative test catches injected violations.
- No app-layer dataclass field has a CLI-shaped name; no app-layer error names a CLI flag.
- No owner module writes to `sys.stderr` or owns argv parsing.
- One `canonical_json` definition, sourced from `quire.hashing`.
- Seven shims gone; no fallback path; no aliases.
- `WorldModel` gone from the codebase; `WorldQuery` is the only name; no re-export bridge.
- `verdict` gone from the five cited docstring sites.
- `gaps.md` updated; `tests/test_workstream_n_done.py` flipped from xfail to pass.

If any one is not true, WS-N stays OPEN.

## Papers / specs referenced

None directly. WS-N is internal infrastructure. References are project-internal: `feedback_imports_are_opinions`, `project_architecture_layers` (the `layered` contract is its mechanical encoding), `project_design_principle` (each D-3 shim collapses disagreement in storage; the D-4/D-5 renames restore non-commitment at the type/term layer).

## Cross-stream notes

- WS-N depends on WS-K because the `layered` contract requires `propstore/heuristic/` to contain the heuristic logic. With `embed.py`, `classify.py`, `relate.py`, `calibrate.py` still at the top level, Layer 3 has no real namespace. WS-K moves them; WS-N gates them.
- `test_no_old_data_shims.py` aligns with WS-J (which fixes `default=str` semantics). WS-J makes one canonical_json correct; WS-N makes there be one.
- Steps 7-8 land *after* Step 6 so the rope rename does not traverse fallback code about to be deleted. Sequencing: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10.
- `tests/test_workstream_consistency.py` (REMEDIATION-PLAN Mechanism 3) gates `STATUS: CLOSED` against `gaps.md`.

## What this WS does NOT do

- Does NOT move `embed.py`, `classify.py`, `relate.py`, `calibrate.py` under `propstore/heuristic/` (that is WS-K).
- Does NOT fix `default=str` in `quire.hashing.canonical_json` (WS-J / WS-O-qui).
- Does NOT add provenance to `propstore/storage/repository_import.py` (cluster U "imports are opinions" stays open).
- Does NOT change `derive_source_document_trust` (closed by D-8 under WS-K — function is deleted entirely, not renamed).
- Does NOT regenerate `gaps.md` line numbers.
- Does NOT change semantic-contracts.yaml runtime-enforcement question.
