# Cluster N: compiler + importing + sources + semantic_passes + repository

Reviewer: claude (review-cluster-N, wave 2). Date: 2026-04-26.

## Scope

Files reviewed (all paths under `C:\Users\Q\code\propstore\`):

- `propstore\compiler\__init__.py`, `context.py`, `ir.py`, `references.py`, `workflows.py`
- `propstore\importing\machinery.py` (only file in `importing/`)
- `propstore\semantic_passes\__init__.py`, `types.py`, `registry.py`, `runner.py`, `diagnostics.py`
- `propstore\source\__init__.py`, `stages.py`, `common.py`, `registry.py`, `concepts.py`, `claims.py`,
  `relations.py`, `passes.py`, `alignment.py`, `finalize.py`, `promote.py`, `status.py`
- `propstore\repository.py`
- `propstore\epistemic_process.py`

Note: the dispatch prompt referenced `propstore/sources/`. That directory does not exist — only the
singular `propstore/source/` exists. Treated the singular path as the intended target.

`active_claims.py` does not exist anywhere in `propstore/`; `tests/test_active_claims.py` exists but
no module by that name in core, so cross-link is moot.

## Pipeline ordering and pass dependencies

### Pipeline framework (semantic_passes)

The pipeline framework in `semantic_passes/` is intentionally minimal: a single linear chain of
passes per family, no fixpoint, no recovery. `registry.py:65-94` validates that pass `input_stage`
== previous `output_stage` and that the chain reaches `target_stage`. `runner.py:14-71` runs them
linearly and bails on the first pass that produces `output is None` *with errors*. This is sound for
the current data model (one stage class per family) but several fragility points are worth flagging:

1. **Single linear pipeline per family is a hard constraint (`registry.py:74-80`).** A pass’s
   `input_stage` must equal the previous pass’s `output_stage`. There is no support for branching,
   for re-running a pass after later analysis, or for fixpoint computation. Several callers (e.g.
   `compiler.workflows.build_repository`) call `build_compilation_context_from_loaded` twice
   because the second call needs `claim_files` data that is only available after partial pipeline
   work — that pattern is not expressible inside the pipeline runner, so it leaks into the caller.

2. **Pipeline returns no diagnostics from the runner itself if a pass raises.** `runner.py:43`
   constructs `pass_class()` and calls `result = pass_instance.run(...)`. Any exception escapes
   unwrapped. There is no `try/except` around `pass_instance.run`, so a pass that calls into
   external YAML decoding (`source/passes.py::SourceImportNormalizePass.run`) will raise a
   `DocumentSchemaError` straight through the runner instead of becoming a diagnostic. This is
   inconsistent with the rest of the system, where `compiler/workflows.py` catches
   `DocumentSchemaError` and converts it to a `_workflow_diagnostic`.

3. **`source/passes.py::SourceImportNormalizePass` is the *only* registered pass for the SOURCES
   family**, and it always succeeds (`return PassResult(output=...)`). The pipeline registry
   indirection is therefore zero-value: `run_source_import_pipeline` allocates a fresh
   `PipelineRegistry`, registers one pass, and runs it. This is mostly harmless, but it means the
   `semantic_passes` framework is currently over-engineered for what it does.

### Compiler workflows ordering

`compiler/workflows.py::build_repository` (lines 362-631) has several ordering problems:

1. **`build_compilation_context_from_loaded` is called twice** (lines 513 and 531) and the first
   result is silently discarded except as input to `_enforce_cel_structural_invariants`. The first
   call uses `claim_files=None` (line 513-517 omits claim_files); the second uses
   `claim_files=files`. The `cel_registry` is identical between the two (it derives only from
   `concepts`), but the `claim_lookup` is empty in the first and populated in the second.
   `_enforce_cel_structural_invariants` only reads `cel_registry`, so the extra build is wasted
   work, but a future maintainer who added claim-aware CEL validation here would silently get the
   empty lookup version. Mark this as a latent footgun.

2. **`validate_repository` builds compilation context only inside the `if files:` branch
   (`workflows.py:281`).** If there are concepts but zero claim files, the CEL structural-invariant
   check (`workflows.py:330-340`) only runs when `concept_result.output` is a
   `ConceptCheckedRegistry` — fine — but uses a *third* freshly-built compilation context (line
   331-335). The same context-building call now appears in three different shapes within one
   workflow.

3. **`build_repository` line 562-576 builds the sidecar BEFORE constructing the WorldModel**, then
   immediately opens the sidecar via `WorldModel(repo)` to count claims. If `build_sidecar`
   silently returns an empty/incomplete artifact, the build report will say `rebuilt=True` with
   `claim_count=0, conflict_count=0, phi_node_count=0`. The `FileNotFoundError` fallback at
   line 609-616 also reports zero conflicts and zero phi nodes whenever the sidecar is missing —
   the only signal a caller has that something went wrong is `claim_count` derived from a payload
   walk that re-counts raw claims. This is silent failure dressed up as success; see Bugs HIGH-1.

4. **`validate_repository` runs concept_pipeline (line 268) before claim_pipeline (line 282)** but
   passes the *raw, unvalidated* claim files into `build_claim_reference_lookup` (line 272). If
   any of those claim files is malformed, `claim_file_claims()` may itself raise, propagating an
   uncaught exception out of validation. This is a missing-pass-dependency bug: claim validation
   should occur (or at least claim files should be schema-checked) before they are used to
   populate cross-family reference lookups.

5. **The compilation pipeline sequencing is hardcoded in `workflows.py`, not declared in the
   `semantic_passes` registry.** The order forms→concepts→contexts→claims→sidecar lives entirely
   in imperative Python, so the pass-dependency framework that the codebase invested in
   (`semantic_passes/`) is bypassed for the most important pipeline. If a pass were inserted in
   the wrong place during a future refactor, no static guard catches it — the family registry
   ordering check (`registry.py:74-80`) does not apply because none of these are registered.

### Source-branch promote ordering

`source/promote.py::promote_source_branch`:

1. **Sidecar mirror rows for blocked claims are written *before* the git transaction
   commits** (lines 840-847, then 849 starts the transact). The comment at lines 831-839 argues
   this is safe because blocked claims do not enter master. This is mostly correct, but the
   sidecar write is *not* inside any transactional boundary at all (see Repository transaction
   safety section below). If the process is killed between lines 847 and the end of the transact
   block, sidecar rows for claims with the now-stale `source_branch` value persist forever — the
   sidecar build assumes it is regenerable, but only if you know to rebuild it.

2. **`_compute_blocked_claim_artifact_ids` runs both `source_claim_index` and the resolver, but
   `concept_resolution` is required first** (line 605 then 610-624). If `resolve_source_concept_promotions`
   raises (e.g. on the `ValueError` at line 284-286 of `promote.py` for unresolved
   parameterization concepts), the function aborts and no sidecar mirror is written even though
   the user might have expected at least the failure diagnostics to be persisted. There is no
   error recovery — concept-resolution failures are non-restartable from the caller’s point of
   view because no diagnostics are surfaced through the structured `PassDiagnostic` channel.

3. **`promote.py:888 `transaction.commit_sha` is read AFTER the `with` block exits** (line 887:
   `sha = transaction.commit_sha`). This relies on the transact context manager binding
   `commit_sha` to its yielded value during `__exit__`, and on the `transaction` Python local
   surviving the `with` block. Both are true in CPython, but the read pattern is unusual — if
   the context manager raises during `__exit__`, `transaction.commit_sha` may be `None` or
   stale, and the subsequent `if sha is None: raise` (line 888-889) is the only check.

## Determinism / content-addressing

### Compiler IR

The `compiler/ir.py` dataclasses are all `frozen=True`. Good. They use `tuple` for sequence fields
(`concept_refs`, `variable_refs`, etc.) which is hashable and ordered — also good for determinism.

### CompilationContext

`compiler/context.py:36-46` uses `MappingProxyType` to expose immutable views, but the underlying
dicts are still owned by the constructing function. Concretely:

- `_freeze_mapping(data)` (line 48-49) calls `dict(data)` first, then wraps it. So callers cannot
  mutate after the fact.
- `_build_context_from_concepts` (line 56-87) creates fresh dicts and passes them to
  `MappingProxyType`. Safe.
- However, the `claim_lookup` returned by `build_claim_reference_lookup` (`compiler/references.py:36-48`)
  is wrapped in `MappingProxyType` over a *fresh* `dict(lookup)`. Safe.

So the "frozen" contract is honored. Determinism here is not a current concern, but the
architecture invites future drift — a future contributor who adds a method like
`CompilationContext.with_extra_concept(...)` and forgets to deep-copy will share state.

### Content-addressing

`importing/machinery.py` uses content-addressing in two places:

1. **`_digest(value)` (line 652-660)** uses `json.dumps(..., sort_keys=True, separators=...,
   ensure_ascii=True, default=str)` and SHA-256, taking the first **32 hex chars** (16 bytes).
   This is fine for its uses (URI suffixes for provenance graphs, equivalence-witness ids), but
   16 bytes of collision resistance is borderline for a global graph identifier. If propstore is
   ever stitched to a larger system, two distinct `ImportMetadata` payloads colliding on 128-bit
   hashes is well into "won't happen in our lifetime" but worth flagging.

2. **`default=str`** in the JSON encoder means non-JSON-serializable values are stringified.
   `repr()`-form output is not stable across Python versions for some types (e.g. `Path`,
   `datetime`). `_digest` is called on `metadata.identity_payload()` (line 282-297) which is
   already nested tuples of strings/None and the *result of recursive `identity_payload()` on
   nested records*. As long as those `identity_payload()` methods produce only strings/tuples/None,
   determinism holds. There is no test in `test_import_machinery.py` that asserts cross-platform
   hash stability.

### Repository

`repository.py:181-187`: `_write_bootstrap_manifest` uses `json.dumps(..., sort_keys=True,
separators=(",", ":"))`. Deterministic. Good.

### Epistemic process

`epistemic_process.py:50-61` `_canonical_json` uses `sort_keys=True`, `separators=(",", ":")`,
`ensure_ascii=True`, `default=str`. Same `default=str` caveat as importing. Identity is computed
as `_hash(self._content_payload())` and then `plan_id = "urn:propstore:...:{hash[:32]}"` —
again 16 bytes of collision resistance.

The `_check_recorded_identity` helper (line 644-655) verifies that `plan_id` and `content_hash`
in a deserialized payload match what `__post_init__` recomputed. Good defensive check. But it
checks `data.get("plan_id") or data.get("job_id")` (line 650) — if a payload has *both* fields,
only `plan_id` is checked, and a wrong `job_id` would pass through silently.

`ProcessCompletionRecord.from_dict` (line 460-474) checks `content_hash` directly without using
`_check_recorded_identity`, which is inconsistent with `InvestigationPlan`/`InterventionPlan`/
`ProcessJob`. `EpistemicProcessManager.from_dict` (line 530-547) also has its own ad-hoc check.
Three different code paths for the same invariant. See Bugs MED-3.

### Sidecar build determinism

`compiler/workflows.py::build_repository` calls `build_sidecar(...)` (line 563) but I did not
audit `propstore.sidecar.build` (out of scope). The build report's `rebuilt: bool` flag is
returned directly from `build_sidecar`, so determinism of the sidecar artifact depends on that
module — **not verified by this review.**

## Trust-boundary discipline at import

### Import machinery (`importing/machinery.py`)

This module is *exemplary* on provenance discipline. Every authored surface field that flows into
an assertion carries explicit metadata:

- `AuthoredAssertionSurface` (line 64-178) requires `source_id`, `source_version_id`,
  `source_content_hash`, `import_run_id`, `importer_id`, `imported_at`, `external_statement_id`,
  `external_statement_locator`, `mapping_policy_id`, `condition_registry_fingerprint` — all
  validated as URIs or non-empty strings in `__post_init__`.
- `_require_uri` (line 638-642) enforces that every URI-typed field starts with one of
  `urn:`, `ni://`, `http://`, `https://`. Strict.
- `ImportCompiler.compile` (line 435-456) bundles all metadata into `ImportMetadata`, mints a
  `ProvenanceGraphRef` from a content hash of the metadata, and attaches it to the
  `SituatedAssertion`. There is no path that produces a `SituatedAssertion` without a
  `provenance_ref`.
- `EquivalenceWitnessStore` (line 493-583) explicitly refuses to do sameAs-style identity
  closure (line 553-554: `identity_for` returns the input id unchanged) and demands a
  `mapping_policy_id` on every recorded witness.

This is the layer the global memory note `feedback_imports_are_opinions.md` is enforcing, and
it is enforced.

### Source-branch ingest paths

The `propstore/source/` ingest paths *bypass* this discipline. Specifically:

1. **`source/claims.py::commit_source_claims_batch` (line 186-251)** stamps the batch with
   `produced_by=ExtractionProvenanceDocument(reader=..., method=..., timestamp=...)` only when
   `reader is not None` (line 230-239). If a caller does not pass `reader`, the batch lands on
   the source branch with **no provenance metadata** about who imported it or when.

2. **The `timestamp` uses `datetime.utcnow()` (line 237)** — `datetime.utcnow()` is deprecated
   in Python 3.12+ and returns naive datetimes. This appears in three places:
   `source/claims.py:237`, `source/relations.py:78` and `:137`. See Bugs MED-1.

3. **Concept ingest (`source/concepts.py::commit_source_concepts_batch`)** has *no* provenance
   metadata at all. There is no `ExtractionProvenanceDocument` analog on
   `SourceConceptsDocument` — the document is decoded, normalized, and written. The concept
   normalize step (`normalize_source_concepts_document`, line 32-70) does not stamp who
   normalized it or against which primary-branch state.

4. **`primary_branch_concept_match` is called inside the normalize step** (line 45-48), which
   means: the primary-branch concept registry at *normalize time* is baked into the
   `registry_match` field on the source-branch entry. If the primary branch advances between
   normalize and finalize, the source branch carries a stale registry match. There is no
   recorded `primary_branch_commit` on the entry, so the staleness is invisible. See Bugs MED-2.

5. **`source/finalize.py` micropub composition (line 47-97) accepts `claim.context` as a
   string** and wraps it in `{"id": claim.context}` (line 76). There is no validation that the
   context id refers to an existing context; the structural CEL invariant check
   (`compiler/workflows.py::_enforce_cel_structural_invariants`) does not run at finalize.
   A source branch can therefore reach a `status: ready` finalize report with claims pinned to
   a context that does not (and may never) exist.

### Importing pipeline `source/passes.py`

`SourceImportNormalizePass` runs `_normalize_semantic_import_writes` which *rewrites concept
references* in claim payloads (line 253). The rewrites use `state.concept_ref_map` populated by
the concept-batch normalizer (line 224). This map is built from `concept_reference_keys` over the
*just-normalized* concept payload — but if two imported concepts happen to normalize to the same
canonical key (e.g. two external sources defined "Voltage" with different definitions), the map
silently overwrites (line 224 uses `state.concept_ref_map[str(reference_key)] = artifact_id`,
no collision check). The second concept wins. This is a silent data-loss path during import.

`_normalize_claim_batch` line 256-259 *does* warn on ambiguous local handles via
`state.warnings.append`, but the concept-ref-map collision is silent.

## Repository transaction safety

### Repository class

`repository.py:29-168` is intentionally thin: it locates the knowledge directory, exposes
`families`/`snapshot`/`git`/`config` as `cached_property`. There is no explicit lock acquisition
in `Repository` itself.

### Transact via families

The transactional boundary is `repo.families.transact(message=...)` — a context manager defined
in `quire.family_store.DocumentFamilyStore` (out of scope). All actual write paths funnel through
this. Used at:

- `propstore\source\finalize.py:166` — finalize writes
- `propstore\source\promote.py:849` — promotion writes
- `propstore\proposals.py:132,183` — proposal writes
- `propstore\app\concepts\mutation.py:1328` — concept mutations
- `propstore\demo\reasoning_demo.py:27,171` — demo

Issues:

1. **`finalize.py:244` and `promote.py:887` read `transaction.commit_sha` *after* the `with`
   block.** This relies on the context manager keeping the transaction object alive (it does in
   CPython by virtue of the `as` binding) and on the manager populating `commit_sha` during
   `__exit__`. The pattern is fragile: if `__exit__` is amended to detach state on exit (a
   common cleanup pattern), both call sites break silently. There is no test that demonstrates
   the value remains valid post-exit.

2. **No lock contention discipline visible at the repository layer.** `concept_ids.py:9, 149`
   imports `dulwich.file.FileLocked` and catches it for the concept-id counter file, but for
   every other write (concepts, claims, micropubs, etc.) there is no application-layer lock. If
   two concurrent `pks` invocations call `commit_source_claims_batch` against the same source
   branch, the underlying git operations may race. Whether `quire.family_store` provides
   serialization is not visible from this scope, but I see *no* repository-level `with
   repo.lock():` guard anywhere.

3. **Sidecar SQLite writes in `promote.py::_write_promotion_blocked_sidecar_rows` (line 422-575)
   open their own connection and commit independently of any git transaction.** The comment
   block at lines 484-494 even documents a prior bug ("Bug 4 (v0.3.2)") where FK constraints
   were violated, with the fix being to delete child rows first. The fact that this complexity
   has been reverse-engineered into this function rather than handled by a `claim_core`
   `ON DELETE CASCADE` definition is itself a code-smell. The sidecar transaction is *not*
   coordinated with the git transaction at all — the sidecar commits at line 573, then the git
   `with repo.families.transact(...)` block runs at line 849. If git transact fails, the
   sidecar mirror rows persist for claims that were never actually promoted.

4. **`repository.py::find` (line 126-158) walks ancestor directories** looking for a
   `knowledge/` directory. It also recognises `start` itself as a repository root if `start` is
   a git store with a propstore bootstrap manifest. This dual-search means tests or scripts
   that run inside `tmp_path` directories may unexpectedly resolve to a parent's
   `knowledge/` — there is no fence preventing the walk from escaping a sandbox.
   `RepositoryNotFound` is only raised if no propstore is found *anywhere* upward.

5. **`repository.py::write_bootstrap_manifest` (line 122-123) is unguarded.** Calling it twice
   writes the manifest twice (the `git.write_blob_ref` for `PROPSTORE_BOOTSTRAP_REF` overwrites
   any existing value). The semantic of this ref is "this is a propstore repo"; overwriting it
   with new metadata silently changes `seed_commit`. There is no check that an existing
   manifest has a compatible format version before being overwritten.

### EpistemicProcessManager — no ordering guarantee on completions

`epistemic_process.py::EpistemicProcessManager.from_dict` (line 529-547) sorts queued jobs by
`queue_position` but completions only by `job_id`. The `replay()` method (line 596-620) iterates
queued jobs by `queue_position` and validates that completions reference queued jobs, but there
is no check that completions are in *causal* order — a completion record may reference a
snapshot hash that does not exist in the journal. Replay reports `errors=()` even if the
underlying snapshot chain is broken, because it never examines the snapshots themselves.

`complete()` (line 567-594) refuses to overwrite an existing completion only if it is
*different* (`existing == record`, line 586-588). Idempotent re-completion with the same
payload is silently allowed. This is intentional but worth noting: a buggy caller that reissues
the completion call cannot detect the duplicate from the return value.

## Bugs (HIGH/MED/LOW)

### HIGH

1. **`compiler/workflows.py::build_repository` silently reports
   `rebuilt=True, conflict_count=0, claim_count=0` when the sidecar is missing after build**
   (line 609-616). The `FileNotFoundError` catch swallows the error; the only signal in the
   returned `RepositoryBuildReport` is that `claim_count` is computed by walking raw payloads.
   A genuine build failure (sidecar not produced) is indistinguishable from "no claims in
   repo" plus "no conflicts". Failure modes should surface as diagnostics at minimum.

2. **`source/passes.py::_normalize_concept_batch` silently overwrites concept-reference-map
   entries on collision** (line 224). Two imported concepts with overlapping reference keys
   produce a map where only the second wins. No warning. Down-stream
   `_rewrite_claim_concept_refs` then rewrites claim refs to the surviving artifact id, so
   the loss propagates into normalized claim payloads. Compare with the sibling
   `_normalize_claim_batch` (line 256-259), which warns on ambiguous handles.

3. **`source/promote.py::_write_promotion_blocked_sidecar_rows` performs a multi-table
   SQLite write outside any transaction the rest of the system can roll back** (line 449-575).
   Sidecar `conn.commit()` runs at line 573, *then* the git `with repo.families.transact(...)`
   block runs at line 849. If the git transact raises, sidecar mirror rows remain for claims
   that were never promoted, and there is no compensating delete. The comment at lines 831-839
   asserts sidecar-ahead-of-git is "safe" because blocked claims do not flow into master, but
   safety relies on the sidecar being regenerable — yet nothing in promote triggers a sidecar
   rebuild after a failed transact.

4. **`compiler/workflows.py::validate_repository` passes raw, unvalidated claim files to
   `build_claim_reference_lookup`** (line 272). If a claim file is malformed at the
   `claim_file_claims()` level (not at schema decode level), the validation pipeline raises
   straight through, defeating the diagnostic-collection purpose of the validator.

### MED

1. **`datetime.utcnow()` deprecated usage** at `source/claims.py:237`,
   `source/relations.py:78`, `source/relations.py:137`. Returns naive datetime; deprecated in
   Python 3.12. Should be `datetime.now(timezone.utc)`.

2. **Source-branch normalization bakes in the *current* primary-branch concept registry**
   without recording the primary-branch commit it consulted. `source/concepts.py:45-48` calls
   `primary_branch_concept_match` which reads `repo.snapshot.branch_head(primary)`. If primary
   advances between normalize and promote, the source's `registry_match` is stale. There is no
   `primary_branch_commit` field on `SourceConceptEntryDocument` to detect this. (This is a
   form of TOCTOU on registry state.)

3. **`epistemic_process.py` has three different identity-check paths** — `_check_recorded_identity`
   (line 644-655) for plans/jobs, ad-hoc check inside `ProcessCompletionRecord.from_dict`
   (line 471-473), and another inside `EpistemicProcessManager.from_dict` (line 544-546).
   `_check_recorded_identity` only verifies `data.get("plan_id") or data.get("job_id")` — if
   both keys are present, only `plan_id` wins (line 650).

4. **`semantic_passes/runner.py` does not catch exceptions raised by passes** (line 44). A pass
   that raises (e.g. `DocumentSchemaError`) propagates uncaught, bypassing the
   `PipelineResult.diagnostics` channel. This is inconsistent with how `compiler/workflows.py`
   catches `DocumentSchemaError` and converts to a structured diagnostic.

5. **`importing/machinery.py::_digest` truncates SHA-256 to 32 hex chars (128 bits)** for
   global URIs (provenance graphs, equivalence witnesses). Acceptable for current scale but
   not future-proof, and there is no test asserting cross-platform hash stability of
   `identity_payload()` outputs.

6. **`source/finalize.py` does not validate that `claim.context` resolves to an existing
   context** before producing a `status: ready` finalize report (line 220-242). The same
   structural CEL invariant check that compiler workflows enforce (`compiler/workflows.py:115-209`)
   is not invoked at finalize time. A source branch can be marked ready and yet fail at
   compile / promote / build time.

### LOW

1. **`compiler/workflows.py::build_repository` builds `compilation_context` twice** (lines 513,
   531) and discards the first except for the structural-invariant check. Wasted work and
   latent footgun for future maintainers.

2. **`semantic_passes/__init__.py` is empty except for a docstring.** No public re-exports — every
   user must import from `semantic_passes.types` / `.registry` / `.runner` directly. Not a bug,
   but inconsistent with `compiler/__init__.py` style.

3. **`source/promote.py:887` reads `transaction.commit_sha` after `with` block exits.** Works in
   CPython by Python's `with ... as transaction:` binding lifetime, but unusual. Same pattern
   in `source/finalize.py:244-246`.

4. **`source/relations.py::commit_source_stance_proposal` (line 218-229) chains two `convert_document_value`
   calls** to add `strength` then `note`. If both are provided, the value is round-tripped
   through document conversion twice. Functionally correct but inefficient and creates two
   `source` strings (`f"{branch}:stances proposal"` line 221 and 226) pointing at the same
   logical operation — debugging traceability suffers.

5. **`repository.py::find` walks ancestors without a sandbox fence** (line 142-154). Tests
   running inside a temp directory may inadvertently resolve to a parent's propstore.

6. **`source/finalize.py::finalize_source_branch` reads `transaction.commit_sha` twice**
   (lines 244, 246) instead of binding it to a local. Minor.

7. **`source/promote.py:887` `transaction` is referenced after `with` block exits.** CPython
   binding survives — fine — but the more idiomatic pattern is to capture inside the block.

8. **`compiler/workflows.py::build_repository` uses `defaultdict` and `Counter`-style logic via
   imports inside a `try` block** (line 580-608). This means the import latency is paid every
   build; not a bug but odd.

## Open questions for Q

1. **Pass framework usage.** The `semantic_passes/` substrate is currently only used by
   `source/passes.py` (one pass) and exposed via `compiler/workflows.py` family pipelines
   (`run_form_pipeline`, `run_concept_pipeline`, `run_claim_pipeline`, `run_context_pipeline`)
   that I did not read in this scope. Is the long-term intent that *all* compilation pipelines
   migrate into the registry framework, or is the registry only for source-branch import?
   Right now the most important pipeline (concept→claim→sidecar build) is hardcoded imperative
   Python in `workflows.py`, bypassing the framework entirely.

2. **Repository locking discipline.** Is there a higher-level lock that wraps git operations
   (e.g. inside `quire.family_store.DocumentFamilyStore.transact`)? If not, two concurrent
   `pks` invocations against the same repo can race — the only application-level lock I see is
   on the concept-id counter file (`concept_ids.py:149`). This is in scope to flag but I cannot
   confirm without reading `quire`.

3. **Sidecar-vs-git transactional coordination.** Should the sidecar mirror writes in
   `promote.py::_write_promotion_blocked_sidecar_rows` be deferred until after the git
   transaction lands, with rollback on failure? The current order (sidecar first, git second)
   was an explicit choice (see comment at promote.py:831-839), but the failure mode (sidecar
   carries blocked rows for a never-actually-promoted batch) is real.

4. **`primary_branch_commit` recording on source-branch entries.** Should
   `SourceConceptEntryDocument.registry_match` carry the primary commit it was matched
   against, so finalize/promote can detect staleness? Currently the staleness is invisible.

5. **`EquivalenceWitnessStore` (`importing/machinery.py:493-583`) is in-memory only.** No
   persistence path exists in this scope. Where does the witness store integrate with the
   repository? Is there a planned family for it?

6. **`source/passes.py` collision discipline on `concept_ref_map`.** Should
   `_normalize_concept_batch` warn (or error) on key collisions the way
   `_normalize_claim_batch` warns on ambiguous handles? Right now the second concept silently
   wins.
