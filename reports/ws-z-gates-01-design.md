# WS-Z-gates Phase 1 — Design Scout Report

Date: 2026-04-16
Workstream: `reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md`
Source findings: `reviews/2026-04-16-code-review/axis-1-principle-adherence.md` Findings 3.1, 3.2, 3.3
Author: scout subagent (read-only, no code modified)

This report maps current state and proposes shape only. Implementation is for the coder pass.

---

## A. Current sidecar schema state

### Tables that exist today

From `propstore/sidecar/schema.py` (full file read):

- `meta` (key TEXT PK, schema_version INTEGER) — created in `create_meta_table` / `write_schema_metadata` at `propstore/sidecar/schema.py:14-36`. `SCHEMA_VERSION = 2` at line 10.
- `source` — `propstore/sidecar/schema.py:41-53`
- `concept` — `propstore/sidecar/schema.py:55-75`
- `alias` — `propstore/sidecar/schema.py:77-82`
- `relationship` — `propstore/sidecar/schema.py:84-92`
- `parameterization` — `propstore/sidecar/schema.py:94-102`
- `parameterization_group` — `propstore/sidecar/schema.py:104-108`
- `relation_edge` — `propstore/sidecar/schema.py:110-137`
- `form` — `propstore/sidecar/schema.py:139-145`
- `form_algebra` — `propstore/sidecar/schema.py:147-156`
- `context`, `context_assumption`, `context_exclusion` — `propstore/sidecar/schema.py:172-199`
- `claim_core` — `propstore/sidecar/schema.py:242-260`
- `claim_numeric_payload` — `propstore/sidecar/schema.py:262-275`
- `claim_text_payload` — `propstore/sidecar/schema.py:277-292`
- `claim_algorithm_payload` (note: already has its own `stage` column for algorithm sub-stage, unrelated to draft/final lifecycle) — `propstore/sidecar/schema.py:294-301`
- `conflict_witness` — `propstore/sidecar/schema.py:303-314`
- `justification` — `propstore/sidecar/schema.py:316-325`
- `calibration_counts` — `propstore/sidecar/schema.py:327-333`
- `claim_fts` (FTS5 virtual) — `propstore/sidecar/schema.py:335-340`

Plus indexes at `propstore/sidecar/schema.py:158-168, 196-198, 342-347`.

### `build_diagnostics` table

**Does not exist today.** No `diagnostics`/`build_diagnostics` table is created anywhere in `schema.py`. Need to add one.

Proposed shape (concrete SQL — coder may translate to msgspec/dataclass for the loader path; SQLite literal kept here so the populator side is obvious):

```sql
CREATE TABLE build_diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id TEXT,                          -- nullable: not all diagnostics belong to a claim
    source_kind TEXT NOT NULL,              -- 'claim' | 'source' | 'concept' | 'context' | 'justification' | 'stance'
    source_ref TEXT,                        -- e.g. filename, source slug, claim id
    diagnostic_kind TEXT NOT NULL,          -- 'raw_id_input' | 'draft_stage' | 'promotion_blocked' | 'finalize_error' | ...
    severity TEXT NOT NULL,                 -- 'error' | 'warning' | 'info'
    blocking INTEGER NOT NULL,              -- 1 if the row this attaches to is quarantined; 0 if informational
    message TEXT NOT NULL,
    file TEXT,                              -- source filename (nullable)
    detail_json TEXT                        -- optional structured payload (e.g., reference targets that failed)
);
CREATE INDEX idx_build_diagnostics_claim ON build_diagnostics(claim_id);
CREATE INDEX idx_build_diagnostics_kind ON build_diagnostics(diagnostic_kind);
CREATE INDEX idx_build_diagnostics_source ON build_diagnostics(source_kind, source_ref);
```

Rationale notes:
- `claim_id` nullable because some diagnostics aren't claim-scoped (e.g., a parse failure on a stances file with no resolvable claim).
- `source_kind`/`source_ref` lets non-claim quarantine rows (sources blocked from promotion, drafts at file level) attach without forcing a synthetic claim id.
- `diagnostic_kind` enumerates the categories the workstream calls out so the render layer can filter cleanly.
- `blocking` lets the same table carry both "this row was quarantined" and "this row was warned about" without separate tables.
- `detail_json` keeps the structured payloads (e.g., stance target lists) without proliferating columns.

### Current claim row shape and required new fields

`claim_core` columns today (`propstore/sidecar/schema.py:242-260`): `id`, `primary_logical_id`, `logical_ids_json`, `version_id`, `content_hash`, `seq`, `type`, `concept_id`, `target_concept`, `source_slug`, `source_paper`, `provenance_page`, `provenance_json`, `context_id`, `premise_kind`, `branch`.

**Fields the workstream requires growing:**

- `build_status TEXT NOT NULL DEFAULT 'ingested'` — domain `Literal["ingested", "blocked"]`. Set to `'blocked'` when the claim ingested only because we relaxed the gate; render policy hides blocked by default.
- `stage TEXT` — file-level stage marker (`'draft' | 'final' | NULL`). Distinct from `claim_algorithm_payload.stage` (which is an algorithm-internal phase like "excitation"). Sourced from `claim_file_stage(normalized_file)` in `propstore/claims.py:66`.
- `promotion_status TEXT` — `Literal["promoted", "blocked", NULL]`. NULL on direct primary-branch claims; `'blocked'` on claims that stayed on a source branch because finalize had errors; `'promoted'` once they've crossed.

Proposed additions to `claim_core`:

```sql
build_status TEXT NOT NULL DEFAULT 'ingested',  -- 'ingested' | 'blocked'
stage TEXT,                                     -- file-level: 'draft' | 'final' | NULL
promotion_status TEXT                           -- 'promoted' | 'blocked' | NULL
```

Plus indexes:

```sql
CREATE INDEX idx_claim_core_build_status ON claim_core(build_status);
CREATE INDEX idx_claim_core_stage ON claim_core(stage);
CREATE INDEX idx_claim_core_promotion_status ON claim_core(promotion_status);
```

The diagnostic-row foreign-key linkage flows the other direction: `build_diagnostics.claim_id` references `claim_core.id` for blocked claims; lookup via `WHERE claim_core.build_status='blocked' AND build_diagnostics.claim_id = claim_core.id` is the canonical "what's wrong with this row" join.

---

## B. Three-gate-site code shape

### B.1 `propstore/sidecar/build.py:75-82, 148` — `_raise_on_raw_id_claim_inputs`

**Current shape:**

```python
# propstore/sidecar/build.py:75-82
def _raise_on_raw_id_claim_inputs(claim_bundle: ClaimCompilationBundle) -> None:
    raw_id_errors = [
        diagnostic.message
        for diagnostic in claim_bundle.diagnostics
        if diagnostic.is_error and "raw 'id' input" in diagnostic.message
    ]
    if raw_id_errors:
        raise ValueError("\n".join(raw_id_errors))
```

Called unconditionally at `propstore/sidecar/build.py:148`:
```python
if claim_bundle is not None:
    _raise_on_raw_id_claim_inputs(claim_bundle)
```

The diagnostics it filters on are emitted by `propstore/compiler/passes.py:329-339` inside `compile_claim_files` when `claim.id` is a raw string but `claim.artifact_id` was not produced. Diagnostic message text matched: `"claim uses raw 'id' input without canonical identity fields"`.

**Callers (grep results):**

- `propstore/sidecar/build.py:148` — sole call site. (`Grep` for `_raise_on_raw_id_claim_inputs` returned only the def at line 75 and the call at 148.)
- No external test imports the function directly; tests assert via the propagated `ValueError` from `build_sidecar`.

**Tests that exercise the gate behaviour:**

- `tests/test_build_sidecar.py:1130` — `with pytest.raises(ValueError, match="raw 'id' input"): build_sidecar(...)`.
- `tests/test_claim_compiler.py:233` — `assert any("raw 'id' input" in message for message in messages)` against `bundle.diagnostics` (this tests the diagnostic emission, not the gate; should survive unchanged).

**Proposed refactor (shape):**

- Rename `_raise_on_raw_id_claim_inputs` → `_collect_raw_id_diagnostics(claim_bundle) -> list[BuildDiagnosticRow]` returning a typed row per offender (with claim filename, attempted id, message). No exceptions.
- The build pipeline keeps the per-file traversal in `populate_claims` (`propstore/sidecar/claims.py`), but augmented to: (a) skip *just* the offending claim's normal insert, (b) write a stub `claim_core` row with `build_status='blocked'`, (c) write a `build_diagnostics` row with `diagnostic_kind='raw_id_input'`, `blocking=1`, `claim_id=<stub id>`.
- Question to confirm during implementation (axis-1 open question 4): the offending claim has no canonical id — a synthetic id (e.g., hash of filename+raw_id+seq) is needed to satisfy the `claim_core.id PRIMARY KEY` constraint while still letting render-time filters surface the row.
- Callers to update:
  - `tests/test_build_sidecar.py:1130` — must change from `pytest.raises(...)` to asserting that the build succeeded AND that a `build_diagnostics` row exists with `diagnostic_kind='raw_id_input'` AND that all *other* claims still ingested.
  - No other call sites need updates.

### B.2 `propstore/compiler/passes.py:289-307` — draft drop

**Current shape:**

```python
# propstore/compiler/passes.py:289-307
if claim_file_stage(normalized_file) == "draft":
    file_diagnostics.append(
        SemanticDiagnostic(
            level="error",
            filename=normalized_file.filename,
            message=(
                "draft artifacts are not accepted in the final claim validation path"
            ),
        )
    )
    diagnostics.extend(file_diagnostics)
    semantic_files.append(
        SemanticClaimFile(
            loaded_entry=original_file,
            normalized_entry=normalized_file,
            claims=tuple(),
        )
    )
    continue
```

`claim_file_stage` defined at `propstore/claims.py:66`.

**Callers of `claim_file_stage`:**
- `propstore/compiler/passes.py:289` — only call site.
- Schema description at `propstore/_resources/schemas/claim.schema.json:715-716` documents the rejection behavior: "Optional file-level processing stage marker used to reject draft claim files from the canonical validation path."
- Test reference at `tests/test_algorithm_stage_types.py:33` — orthogonal (algorithm stage column, NOT file-level draft). Keep as-is.

**Tests that exercise the gate behaviour:**

- `tests/test_validate_claims.py:707-733` (`TestDraftArtifactBoundary.test_draft_claim_file_rejected_from_final_validation`) — asserts `not result.ok` and that an error message containing "draft artifacts are not accepted" surfaces.

**Proposed refactor (shape):**

- The early-return for `stage == "draft"` is deleted entirely.
- Drafts traverse the normal binding path. A `SemanticDiagnostic` is *still* emitted, but `level="info"` (or new `level="draft"`) — informational, not blocking. Per the workstream: "the SemanticDiagnostic survives but downgrades from `error` to `info`."
- Each `SemanticClaimFile` for a draft contains the actual semantic claims (not `tuple()`).
- The downstream `populate_claims` writes draft claims with `claim_core.stage='draft'`. Optionally writes a `build_diagnostics` row per file with `diagnostic_kind='draft_stage'`, `blocking=0`, `severity='info'`.
- `propstore/_resources/schemas/claim.schema.json:716` description updates to: "Optional file-level processing stage marker used for render-policy filtering (drafts hidden by default)."
- Callers to update:
  - `tests/test_validate_claims.py:707-733` — must invert: assert `result.ok`, assert claims are present in the output, optionally assert diagnostic presence at `info` level.

### B.3 `propstore/source/promote.py:186-188` — all-or-nothing promotion

**Current shape:**

```python
# propstore/source/promote.py:185-188
def promote_source_branch(repo: Repository, source_name: str) -> str:
    report = load_finalize_report(repo, source_name)
    if report is None or report.status != "ready":
        raise ValueError(f"Source {source_name!r} must be finalized successfully before promotion")
```

`report.status` is computed at `propstore/source/finalize.py:147-149`: `"ready"` iff `not claim_errors and not justification_errors and not stance_errors`, else `"blocked"`. The error lists are computed at `finalize.py:52-77`.

**Callers (grep results):**
- `propstore/cli/source.py:31` import; `propstore/cli/source.py:351` — `pks source promote <name>` wraps the function and translates `ValueError` to `click.ClickException`.
- `propstore/source/__init__.py:36` re-exports.
- `tests/test_source_promotion_alignment.py:32, 207` — happy-path test; report status is constructed as `"ready"` in the fixture (`tests/test_source_promotion_alignment.py:96`).

**Tests that exercise the gate behaviour:**

- `tests/test_source_promotion_alignment.py:176-207` (`test_promote_source_branch_writes_canonical_artifact_families`) — happy path only.
- **No existing test asserts that the all-or-nothing rejection happens.** That's a gap; the workstream's exit criteria require a test for partial promotion (P valid + Q invalid case).

**Proposed refactor (shape):**

- Remove the `report.status != "ready"` early return. Instead, for each claim/justification/stance, decide individually whether it can promote based on the per-item error membership computed in `finalize`.
- `finalize_source_branch` already produces `claim_reference_errors`, `justification_reference_errors`, `stance_reference_errors` — these become the per-item allow/block lists rather than threshold inputs.
- `promote_source_branch` iterates: a valid claim flows through `attach_source_artifact_codes` and `transaction.save` as today; a blocked claim is skipped on the primary branch but a `build_diagnostics` row with `source_kind='claim'`, `source_ref=<source_branch>:<claim_id>`, `diagnostic_kind='promotion_blocked'`, `blocking=1` is written. Also a `claim_core` mirror row with `promotion_status='blocked'`, `branch=<source_branch_name>` so the render layer surfaces it via `pks query`.
- The blocked claims stay on the source branch (no movement) — promotion is render-layer-visible only via the diagnostic + the claim row's `promotion_status`.
- Promote command output reports both counts. CLI exit code: `0` if anything promoted; `1` only if all items blocked.
- Callers to update:
  - `propstore/cli/source.py:345-354` — replace single ClickException path with success/partial/total-failure messaging; preserve ValueError → ClickException for *unrecoverable* errors (e.g., source doesn't exist), distinguish from per-claim block.
  - `tests/test_source_promotion_alignment.py:176-207` — must continue passing (happy path unchanged).
  - **NEW** test: source with mix of valid + invalid claims; assert the valid ones land on primary branch, the invalid ones do not, the diagnostic rows exist, and a re-promote after fix promotes the previously-blocked item.

---

## C. Existing `RenderPolicy`

### Current location and fields

`propstore/world/types.py:778-872` — `RenderPolicy` is a `@dataclass(frozen=True)`. Re-exported via `propstore/__init__.py` (per `docs/python-api.md:337`).

Existing fields (with defaults):
- `reasoning_backend: ReasoningBackend = ReasoningBackend.CLAIM_GRAPH`
- `strategy: ResolutionStrategy | None = None`
- `semantics: ArgumentationSemantics = ArgumentationSemantics.GROUNDED`
- `comparison: str = "elitist"`
- `link: str = "last"`
- `decision_criterion: str = "pignistic"`
- `pessimism_index: float = 0.5`
- `show_uncertainty_interval: bool = False`
- `praf_strategy: str = "auto"`
- `praf_mc_epsilon: float = 0.01`
- `praf_mc_confidence: float = 0.95`
- `praf_treewidth_cutoff: int = 12`
- `praf_mc_seed: int | None = None`
- `merge_operator: MergeOperator = MergeOperator.SIGMA`
- `branch_filter: tuple[str, ...] | None = None`
- `branch_weights: Mapping[str, float] | None = None`
- `integrity_constraints: tuple[IntegrityConstraint, ...] = ()`
- `future_queryables: tuple[str, ...] = ()`
- `future_limit: int | None = None`
- `overrides: Mapping[str, str] = {}`
- `concept_strategies: Mapping[str, ResolutionStrategy] = {}`

Plus `from_dict` at `propstore/world/types.py:874-943` and `to_dict` at `propstore/world/types.py:945-995` for serialization.

### Render-layer code consuming `RenderPolicy`

Tests show consumption in: `tests/test_world_model.py`, `tests/test_ic_merge.py`, `tests/test_render_policy_opinions.py`, `tests/test_praf_integration.py`, `tests/test_init.py`, `tests/test_worldline.py`, `tests/test_atms_engine.py`, `tests/test_resolution_helpers.py`, `tests/test_revision_phase1.py`, `tests/test_worldline_error_visibility.py`, `tests/test_semantic_core_phase0.py`, `tests/test_render_time_filtering.py`, `tests/test_render_contracts.py`. Source code consumption is across `propstore/world/`, `propstore/render/` paths (full grep saved at the persistence target listed during scout). Naming convention is consistent: snake_case fields, defaults that preserve pre-policy behavior, and `from_dict`/`to_dict` round-trip.

### Proposed additional fields

Following the existing convention (snake_case, defaults that preserve "current default render"):

```python
# Visibility flags for build/lifecycle status surfaces.
# Default values match the design-checklist intent: don't show problems by default;
# allow opt-in for diagnostic views.
include_drafts: bool = False              # show claim_core rows with stage='draft'
include_blocked: bool = False             # show claim_core rows with build_status='blocked'
                                          # (and rows with promotion_status='blocked')
show_quarantined: bool = False            # show build_diagnostics rows in render output
                                          # (alias-style flag — same underlying storage as include_blocked
                                          #  but specifically toggles diagnostic visibility in formatted output)
```

Open question for the coder: spec lists `--include-drafts`, `--include-blocked`, `--show-quarantined` as three CLI flags; whether they map 1-to-1 to three RenderPolicy booleans, or whether `include_blocked` subsumes `show_quarantined`, depends on whether we want diagnostic *rows* visible alongside the claim row (`show_quarantined=True`) or merely the blocked claim itself surfaced (`include_blocked=True`). The shape above keeps them separate; collapse if the workstream coder prefers.

`from_dict` / `to_dict` need three new lines each, following the omit-when-default pattern at `propstore/world/types.py:947-994`.

---

## D. CLI surface

### Where flags attach

`propstore/cli/__init__.py:44-58` defines the root `cli` group. Subcommands are added at `propstore/cli/__init__.py:61-76`. Per-command flags are the convention (no global `--include-drafts`).

The relevant existing surfaces:
- `pks query <SQL>` at `propstore/cli/compiler_cmds.py:383-412` — accepts a raw SQL string; sets `PRAGMA query_only=ON`. Current shape has no row-level filter flags. Adding `--include-drafts` etc. here is awkward because the user controls the SQL; a flag can only modify which rows the user *sees*, not which they query.
- `pks world ...` at `propstore/cli/compiler_cmds.py:453-2228` — many subcommands (`status`, `query`, `bind`, `explain`, `algorithms`, `derive`, `resolve`, `extensions`, `hypothetical`, `chain`, `export-graph`, `sensitivity`, `fragility`, `check-consistency`, `revision-*`, `atms-*`). These are the *render-layer* surfaces — they construct a `RenderPolicy` (often via `--policy-json` or world-binding flags) and apply it.
- `pks source promote <name>` at `propstore/cli/source.py:345-354` — needs partial-promotion result reporting.
- `pks source ...` group has no `status` subcommand currently; the workstream proposes one.

### Proposed minimal CLI extension

Per-command flags (matching the existing `is_flag=True` boolean convention used at `propstore/cli/compiler_cmds.py:208`, `propstore/cli/form.py:258`, etc.):

1. **`pks query` SQL surface:** for raw SQL it makes most sense to leave as-is — the user can already write `WHERE build_status='ingested' AND stage IS NOT 'draft'` themselves. *However,* a thin convenience wrapper subcommand `pks list-claims` (or extend `pks claim list` if it exists in `cli/claim.py`) with `--include-drafts/--include-blocked/--show-quarantined` flags is more discoverable. Coder check: does `pks claim` already have a list subcommand? If yes, add flags there.

2. **`pks world ...` subcommands:** the world subcommands that materially involve claim visibility — `world status`, `world query`, `world resolve`, `world chain`, `world derive` — should accept the same three flags, plumbed through to a `RenderPolicy` constructor. Today these subcommands construct `RenderPolicy` from a `--policy-json` option (verify in coder pass — the `_bind_world` helper at `propstore/cli/compiler_cmds.py:87` is the entry point); the new flags are CLI sugar over the same RenderPolicy.

3. **`pks source promote`:** no new flag needed; output text changes to report `Promoted N of M claims (K blocked)`. Add optional `--strict` flag to preserve the old "fail if anything blocked" behavior (off by default).

4. **`pks source status <name>` (NEW subcommand):** lists per-claim promotion status by reading `build_diagnostics WHERE source_kind='claim' AND source_ref LIKE '<source_branch>:%'` plus `claim_core WHERE branch=<source_branch>`. Output: claim id, status, blocking diagnostic message. Naming follows existing `pks source` pattern (`add-claim`, `add-justification`, `add-stance`, `finalize`, `promote`, `sync`, `stamp-provenance` at `propstore/cli/source.py:301-389`).

Flag-naming convention (`--include-drafts`, `--include-blocked`, `--show-quarantined`) matches existing project style: kebab-case, descriptive verb-noun, boolean default false.

---

## E. Test coverage of the affected sites

### Existing tests per gate site

**Site B.1 (raw-id gate):**
- `tests/test_build_sidecar.py:1130` — gate behavior (the `pytest.raises`).
- `tests/test_claim_compiler.py:233` — diagnostic emission (orthogonal, keeps).

**Site B.2 (draft drop):**
- `tests/test_validate_claims.py:707-733` (`TestDraftArtifactBoundary.test_draft_claim_file_rejected_from_final_validation`) — gate behavior (asserts `result.ok` is False).
- `tests/test_algorithm_stage_types.py:33` — orthogonal (algorithm stage column).

**Site B.3 (promote):**
- `tests/test_source_promotion_alignment.py:176-207` — happy-path only.

**RenderPolicy:**
- 13 test files (`tests/test_world_model.py`, `tests/test_ic_merge.py`, `tests/test_render_policy_opinions.py`, `tests/test_praf_integration.py`, `tests/test_init.py`, `tests/test_worldline.py`, `tests/test_atms_engine.py`, `tests/test_resolution_helpers.py`, `tests/test_revision_phase1.py`, `tests/test_worldline_error_visibility.py`, `tests/test_semantic_core_phase0.py`, `tests/test_render_time_filtering.py`, `tests/test_render_contracts.py`) — none currently exercise visibility flags for drafts/blocked/quarantined (they don't exist yet).

### Tests that WILL need updating

- `tests/test_build_sidecar.py:1130` — must invert. New assertion: build succeeds; sidecar has a `build_diagnostics` row with `diagnostic_kind='raw_id_input'`; the broken claim has `build_status='blocked'`; all other claims ingested normally.
- `tests/test_validate_claims.py:707-733` — must invert. New assertion: `result.ok` is True (or downgrade to non-error level); the draft claim is present in the validated output; the draft annotation rides along.
- `tests/test_render_policy_opinions.py` (and possibly `tests/test_render_contracts.py`) — verify default `RenderPolicy()` still produces existing default behavior; add tests for the new boolean defaults.

### NEW tests needed (per workstream exit criteria)

Property-style (Hypothesis `@given` per `disciplines.md` rule 9 and CLAUDE.md feedback_hypothesis_property_tests):

1. **Raw-id quarantine property:** `@given(strategies.lists(claim_strategy()), st.integers(min_value=0))` — for any tree with N valid + 1 raw-id-broken claim, the sidecar contains N+1 rows; the broken row has `build_status='blocked'`; valid rows are ingested.
2. **Draft visibility property:** for any (M non-draft, K draft), `pks query` with default policy returns M; with `--include-drafts` returns M+K; sidecar contains M+K rows regardless.
3. **Partial-promote property:** for any source with (P valid, Q invalid) claims, `promote` lands P on primary; Q stay with `promotion_status='blocked'`; subsequent promote after fixing one of Q lands that one.
4. **RenderPolicy invariance:** identical sidecar state, two policy configurations → two distinct render outputs but identical underlying claim_core rows.
5. **`pks source status` correctness:** lists exactly the `promotion_status='blocked'` rows for the named source, with the matching diagnostic messages.

The `disciplines.md` "tests as postulates" rule applies — these properties are the workstream's correctness postulates; encode as Hypothesis strategies, not as one-off example tests.

---

## F. Migration concern

### Local knowledge tree

`knowledge/` exists at `C:/Users/Q/code/propstore/knowledge/` with subtrees: `claims/`, `concepts/`, `contexts/`, `forms/`, `justifications/`, `predicates/`, `rules/`, `sidecar/`, `sources/`, `stances/`, `worldlines/`. The `sidecar/` subtree holds the compiled SQLite. After schema changes land, this sidecar will mismatch the new tables and columns.

Any other local repos managed by `pks` (paper-process knowledge stores under `pyghidra_mcp_projects/`, etc.) face the same staleness.

### Existing migration mechanism

**There is no incremental migration path.** Reading `propstore/sidecar/build.py`:
- `propstore/sidecar/build.py:101-107` — `hash_path = sidecar_path.with_suffix(".hash")`. If the hash matches and `force=False`, build is a no-op.
- `propstore/sidecar/build.py:186-187` — `if sidecar_path.exists(): sidecar_path.unlink()`. Build *always* unlinks and rebuilds from scratch when invoked.
- `propstore/sidecar/schema.py:10` — `SCHEMA_VERSION = 2`, written via `write_schema_metadata` to the `meta` table. Nothing currently reads this version back to gate migration.
- CLI: `pks build --force` (`propstore/cli/compiler_cmds.py:208`) bypasses the hash check and rebuilds.

**Implication for this workstream:** schema additions (new `build_diagnostics` table, new `claim_core` columns) require:
1. Bumping `SCHEMA_VERSION` to 3 (`propstore/sidecar/schema.py:10`).
2. Adding `CREATE TABLE build_diagnostics` and the new columns to `create_tables` / `create_claim_tables`.
3. Documenting in release notes that users must re-run `pks build --force` after pulling. Per `disciplines.md` rule 6 ("No backward-compat shims") and CLAUDE.md feedback_no_fallbacks, no migration code is needed — the rebuild-from-scratch path handles it. Q's local repos rebuild on next `pks build`.

If at some point an `ALTER TABLE`-style migration becomes necessary, that's out of scope for this workstream.

---

## Drift / discrepancies between spec and code

1. **Workstream phrasing "RenderPolicy per `propstore/__init__.py` re-exports — verify what's there":** verified — `RenderPolicy` is in `propstore/world/types.py:778`, re-exported via `propstore/__init__.py` (referenced in `docs/python-api.md:337`). Extension-not-parallel-invent is the right call.

2. **Workstream says "the schema description currently says drafts are 'rejected'; update to 'marked for render-policy filtering.'":** verified at `propstore/_resources/schemas/claim.schema.json:716`. Exact current text: `"Optional file-level processing stage marker used to reject draft claim files from the canonical validation path."` Replacement should follow the workstream's wording.

3. **Workstream calls out three sites; review's Finding 3.3 calls promote a MED, not the same as 3.1's CRIT.** Finding 3.3 also notes promote is "philosophically consistent with 'explicit user migration'" — the workstream still chooses to relax it because the *data on the source branch is not queryable from primary's sidecar*. The render-time-policy fix is the cleaner discipline: do partial promote, mark blocked rows, surface them. **No drift — the workstream is consistent with the finding's recommendation.**

4. **`pks query` is raw SQL (`propstore/cli/compiler_cmds.py:386`); the workstream casually says `pks query --include-drafts`.** That flag does not naturally fit a SQL passthrough subcommand. Either:
   - Add the flag to other render-layer subcommands (`pks world status`, `pks world query`, etc.) — these already construct RenderPolicy.
   - Add a new convenience subcommand (`pks claim list` or similar) where the flag has clear meaning.
   The workstream's "minimal CLI extension" framing leaves room for the coder to choose, but a literal `pks query --include-drafts` is incompatible with the current subcommand. **Flagged as a small spec-vs-code mismatch needing the coder to choose between the two designs above.**

5. **`tests/test_source_promotion_alignment.py` only covers happy path** — there is no existing test that asserts the all-or-nothing rejection. So the workstream's "tests asserting the raise must change" doesn't apply to site B.3; instead, a NEW test for partial promotion is needed and there is no removal step.

6. **`claim_algorithm_payload.stage` already exists** as an algorithm-internal phase column (`propstore/sidecar/schema.py:299`) and `tests/test_algorithm_stage_types.py:33` covers it. The new file-level `stage` on `claim_core` is a different concept; care needed in naming and documentation so the two don't collide.

---

## Summary of artifact requirements

Per the workstream's exit criteria, the implementation phases will need to produce:

- 1 schema bump (`SCHEMA_VERSION` → 3) + 1 new table + 3 new columns on `claim_core`.
- 1 refactored function (`_raise_on_raw_id_claim_inputs` → `_collect_raw_id_diagnostics`) + populator-level handling for blocked claim stub rows.
- 1 deleted early-return (passes.py:289-307 draft drop).
- 1 partial-promote loop (promote.py:185-).
- 1 new RenderPolicy fields (3 booleans) + from_dict/to_dict updates.
- 1 new CLI subcommand (`pks source status`) + new flags on world-layer subcommands.
- 5 new property tests; 2 inverted existing tests; 1 schema-description string update.
- Documentation updates: CLAUDE.md "Known Limitations" cleanup, `docs/gaps.md` closures, `docs/conflict-detection.md` if it discusses build-time gating, citation-as-claim discipline references on the new code paths.

All references in this report point to read-time observations of `master` HEAD `2d27708` (per `git log` shown in the conversation environment).
