# Pipeline Redesign Execution Plan

**Date:** 2026-04-05
**Scope:** `propstore` plus `research-papers-plugin` pipeline redesign, authored and tracked from the `propstore` repo
**Status:** Proposed
**Repos:**
- `C:/Users/Q/code/propstore`
- `C:/Users/Q/code/research-papers-plugin`

---

## Goal

Make the paper pipeline genuinely propstore-first without breaking current repo contracts on the way there.

End state:

1. per-paper ingestion gets immediate validation feedback after each `pks source add-*`
2. per-paper promotion is possible for unambiguous new concepts, without requiring a collection-wide ceremony
3. `paper-process` becomes a pure skill orchestrator
4. `paper-reader` stays a paper-reading skill, not a propstore mutation skill
5. collection ingestion becomes incremental, with sidecar build deferred to the end

This is an execution plan, not a design sketch. It is not complete until all listed slices are either finished or explicitly deferred.

---

## Non-Negotiable Rules

1. Work one slice at a time.
2. Do not mix `propstore` and plugin code changes in the same commit.
3. Every slice is test-driven:
   - write the failing test or contract check first
   - run the narrowest relevant test target
   - implement the smallest coherent fix
   - rerun the same target
   - run the broader slice suite
   - commit immediately if green
4. Every pytest invocation must be `uv run pytest -vv` and must tee full output to `logs/test-runs/`.
5. Do not put `pks source` commands into `paper-reader`.
6. Do not deprecate `sync_propstore_source.py` until tests no longer rely on it.
7. Do not declare the plan complete while old and new orchestration contracts both remain active unless the plan explicitly says they coexist.

---

## Current Reality Check

The redesign must respect the current codebase, not the imagined one.

Confirmed constraints:

- `propstore/cli/source.py` already has `add-concepts`, `add-claim`, `add-justification`, `add-stance`, `finalize`, and `promote`.
- `finalize_source_branch()` already writes `merge/finalize/<source>.yaml` and is advisory-friendly if invoked from the caller.
- `promote_source_branch()` still blocks on unresolved promoted concept mappings for source-local concepts that are not linked to master concepts.
- `paper-reader` is currently contract-tested to stay out of propstore ingestion.
- plugin tests currently use `sync_propstore_source.py` as a contract proxy, so immediate removal is not justified.

Implication:

- auto-finalize is a valid early slice
- per-paper promotion requires a real `propstore` change, not just plugin skill rewrites
- orchestration boundaries must be changed deliberately and test-first

---

## Required Test Logging

Use timestamped logs for every pytest run.

PowerShell pattern:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv <target> 2>&1 | Tee-Object "logs/test-runs/$ts-<label>.log"
```

Examples:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_source_claims.py 2>&1 | Tee-Object "logs/test-runs/$ts-source-claims.log"
```

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv plugins/research-papers/tests/test_source_workflow_contracts.py 2>&1 | Tee-Object "logs/test-runs/$ts-plugin-workflow-contracts.log"
```

---

## Commit Discipline

Commit after every green slice. No squashing during execution.

Expected commit sequence:

1. `propstore: auto-finalize source add commands`
2. `propstore: promote unique source-local concepts`
3. `plugin: add source bootstrap and promote skills`
4. `plugin: make register-concepts notes-first`
5. `plugin: harden extract-claims verification loop`
6. `plugin: make paper-process a pure orchestrator`
7. `plugin: add ingest-new-papers without breaking reader wrapper`
8. `plugin: simplify ingest-collection around per-paper promotion`
9. `plugin: deprecate sync helper after test migration`

If a slice needs to split further to stay green and reviewable, do so, but still commit immediately after the slice-level acceptance tests pass.

---

## Slice 1: Advisory Auto-Finalize After Source Adds

**Repo:** `C:/Users/Q/code/propstore`

**Files likely touched:**
- `propstore/cli/source.py`
- `tests/test_source_claims.py`
- `tests/test_source_relations.py`

**Intent:**
After each `pks source add-*`, attempt finalize immediately and report the result as advisory output, not a fatal post-write gate.

**Tests first:**

1. add a failing test that `source add-claim` writes or refreshes `merge/finalize/demo.yaml`
2. add a failing test that blocked finalize does not cause `source add-claim` to fail
3. add equivalent coverage for `add-concepts`, `add-justification`, and `add-stance` if one shared helper is not already exercised sufficiently

**Implementation:**

1. add one helper in `propstore/cli/source.py` that:
   - calls `finalize_source_branch(repo, name)`
   - echoes success on completion
   - catches exceptions and emits an advisory note to stderr
2. call that helper after each successful `commit_source_*_batch()`

**Targeted tests:**

- `tests/test_source_claims.py`
- `tests/test_source_relations.py`

**Broader tests:**

- source CLI and source relation tests

**Commit when green:**

- `propstore: auto-finalize source add commands`

---

## Slice 2: Allow Per-Paper Promotion For Unique New Concepts

**Repo:** `C:/Users/Q/code/propstore`

**Files likely touched:**
- `propstore/source_ops.py`
- `propstore/concept_alignment.py` if shared helpers become necessary
- `tests/test_source_relations.py`
- possibly `tests/test_concept_alignment_cli.py`

**Intent:**
Make `pks source promote` materialize unambiguous source-local concepts onto master, while still blocking ambiguous cases.

**Tests first:**

1. failing test: a source branch with one unique proposed concept can promote successfully
2. failing test: promoted claims rewrite concept references to the master artifact id created during promotion
3. failing test: a concept collision that is genuinely ambiguous still blocks promotion with a clear error

**Implementation:**

1. extend the concept-resolution path used by `promote_source_branch()`
2. for source concepts with no `registry_match` and no master handle collision:
   - create canonical master concept documents during promote
   - assign stable artifact/logical/version ids
3. if there is a master-name collision or other ambiguity:
   - keep promotion blocked
   - emit a concrete error naming the unresolved handles

**Targeted tests:**

- `tests/test_source_relations.py`
- any concept-alignment tests needed for shared helpers

**Broader tests:**

- source tests
- concept-alignment tests

**Commit when green:**

- `propstore: promote unique source-local concepts`

---

## Slice 3: Add Thin Propstore Skills, Keep Reader Pure

**Repo:** `C:/Users/Q/code/research-papers-plugin`

**Files likely touched:**
- `plugins/research-papers/skills/source-bootstrap/SKILL.md`
- `plugins/research-papers/skills/source-promote/SKILL.md`
- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Intent:**
Move propstore orchestration into dedicated skills rather than polluting `paper-reader`.

**Tests first:**

1. failing contract test that `source-bootstrap` exists and documents:
   - `pks source init`
   - `pks source write-notes`
   - `pks source write-metadata`
2. failing contract test that `source-promote` exists and documents:
   - `pks source promote`
3. keep the existing `paper-reader` purity test intact

**Implementation:**

1. add `source-bootstrap`
2. add `source-promote`
3. do not modify `paper-reader` to contain `pks source` calls

**Targeted tests:**

- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Commit when green:**

- `plugin: add source bootstrap and promote skills`

---

## Slice 4: Make Register-Concepts Notes-First And Rerunnable

**Repo:** `C:/Users/Q/code/research-papers-plugin`

**Files likely touched:**
- `plugins/research-papers/skills/register-concepts/SKILL.md`
- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Intent:**
Stop deriving the concept inventory primarily from `claims.yaml`. `notes.md` is the primary source; `claims.yaml` is supplementary if present.

**Tests first:**

1. failing contract test that `register-concepts` no longer requires `claims.yaml`
2. failing contract test that `notes.md` is the primary extraction source
3. failing contract test that `propose_concepts.py pks-batch` is supplementary rather than primary

**Implementation:**

1. rewrite `register-concepts/SKILL.md`
2. document an agent-first concept pass from `notes.md`
3. keep `propose_concepts.py pks-batch` as a straggler-catcher if `claims.yaml` exists
4. preserve rerunnability and `pks source add-concepts`

**Targeted tests:**

- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Commit when green:**

- `plugin: make register-concepts notes-first`

---

## Slice 5: Harden Extract-Claims Verification Loop

**Repo:** `C:/Users/Q/code/research-papers-plugin`

**Files likely touched:**
- `plugins/research-papers/skills/extract-claims/SKILL.md`
- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Intent:**
Require page-image spot-checks for precise numerics and make the claims/concepts iteration fully pipeline-safe.

**Tests first:**

1. failing contract test that `extract-claims` instructs page-image spot-checks for numeric claims
2. failing contract test that it documents the unknown-concept retry loop driven by finalize feedback
3. failing contract test that orchestrated usage is non-interactive and does not stop to ask whether to overwrite

**Implementation:**

1. add page-to-PNG indexing guidance
2. require spot-checks for values, confidence intervals, p-values, and similar exact numerics
3. document retry behavior when auto-finalize reports unknown concept references
4. ensure orchestration instructions are non-interactive

**Targeted tests:**

- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Commit when green:**

- `plugin: harden extract-claims verification loop`

---

## Slice 6: Rewrite Paper-Process As A Pure Orchestrator

**Repo:** `C:/Users/Q/code/research-papers-plugin`

**Files likely touched:**
- `plugins/research-papers/skills/paper-process/SKILL.md`
- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Intent:**
Make `paper-process` call skills only. No inline propstore mutation commands.

**Tests first:**

1. failing contract test that `paper-process` references:
   - `paper-retriever`
   - `paper-reader`
   - `source-bootstrap`
   - `register-concepts`
   - `extract-claims`
   - `extract-justifications`
   - `extract-stances`
   - `source-promote`
2. failing contract test that it no longer inlines:
   - `pks source init`
   - `pks source write-notes`
   - `pks source write-metadata`
   - `pks source finalize`
   - `pks source promote`

**Implementation:**

1. rewrite `paper-process/SKILL.md`
2. keep fallback behavior based on printing the skill text
3. do not edit `emit_nested_process_fallback.py` unless fallback mechanics themselves change

**Targeted tests:**

- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Broader tests:**

- plugin workflow contract tests

**Commit when green:**

- `plugin: make paper-process a pure orchestrator`

---

## Slice 7: Add Ingest-New-Papers Without Breaking Reader Wrapper

**Repo:** `C:/Users/Q/code/research-papers-plugin`

**Files likely touched:**
- `plugins/research-papers/skills/ingest-new-papers/SKILL.md`
- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Intent:**
Add the batch wrapper around full ingestion without changing the existing semantics of `process-new-papers`.

**Tests first:**

1. preserve the existing test that `process-new-papers` remains a `paper-reader` wrapper
2. add a failing contract test that `ingest-new-papers` invokes `paper-process`

**Implementation:**

1. add `ingest-new-papers`
2. leave `process-new-papers` intact for compatibility

**Targeted tests:**

- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Commit when green:**

- `plugin: add ingest-new-papers without breaking reader wrapper`

---

## Slice 8: Simplify Ingest-Collection Around Incremental Per-Paper Promotion

**Repo:** `C:/Users/Q/code/research-papers-plugin`

**Files likely touched:**
- `plugins/research-papers/skills/ingest-collection/SKILL.md`
- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Intent:**
Remove the collection-wide ceremony as the normal path, while still allowing one optional stance-backfill/enrichment pass after all papers are ingested.

**Tests first:**

1. failing contract test that `ingest-collection` runs per-paper `paper-process`
2. failing contract test that sidecar build is deferred to the end
3. failing contract test that stance backfill is optional, not a mandatory second promotion phase
4. failing contract test that the old multi-phase concept-alignment ceremony is no longer described as the default path

**Implementation:**

1. rewrite `ingest-collection/SKILL.md`
2. make per-paper processing the default
3. defer `pks build` until the end
4. document an optional enrichment/backfill pass

**Targeted tests:**

- `plugins/research-papers/tests/test_source_workflow_contracts.py`

**Broader tests:**

- full plugin suite

**Commit when green:**

- `plugin: simplify ingest-collection around per-paper promotion`

---

## Slice 9: Migrate Away From Sync Helper, Then Deprecate It

**Repo:** `C:/Users/Q/code/research-papers-plugin`

**Files likely touched:**
- `plugins/research-papers/tests/test_sync_propstore_source.py`
- `plugins/research-papers/tests/test_pks_pipeline_integration.py`
- `plugins/research-papers/scripts/sync_propstore_source.py`

**Intent:**
Retire the sync helper only after tests no longer depend on it.

**Tests first:**

1. replace sync-helper-centric tests with direct contract checks against the new skill boundaries
2. only after those tests pass, add a deprecation test or contract check if desired

**Implementation:**

1. migrate tests off `sync_propstore_source.py`
2. add a deprecation header to the script
3. keep it as a compatibility shim until explicitly removed in a later plan

**Targeted tests:**

- migrated plugin integration/contract tests

**Broader tests:**

- full plugin suite

**Commit when green:**

- `plugin: deprecate sync helper after test migration`

---

## Execution Checklist

- [ ] Slice 1 complete and committed
- [ ] Slice 2 complete and committed
- [ ] Slice 3 complete and committed
- [ ] Slice 4 complete and committed
- [ ] Slice 5 complete and committed
- [ ] Slice 6 complete and committed
- [ ] Slice 7 complete and committed
- [ ] Slice 8 complete and committed
- [ ] Slice 9 complete and committed

---

## Final Verification

Do not report completion before all of the following pass.

### Propstore repo

1. targeted tests for slices 1-2
2. relevant broader source/concept suites
3. full suite:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv 2>&1 | Tee-Object "logs/test-runs/$ts-propstore-full.log"
```

### Plugin repo

1. targeted workflow-contract and integration tests after each slice
2. full plugin suite after slices 6, 8, and 9:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv 2>&1 | Tee-Object "logs/test-runs/$ts-plugin-full.log"
```

### End-to-end

1. fresh `pks init`
2. run one `paper-process` on a known paper
3. verify:
   - source finalize report exists
   - promotion succeeds
   - `pks build` succeeds
   - `pks world status` succeeds
4. run collection ingestion
5. run one final build
6. run optional stance backfill if needed and verify no regressions

---

## Completion Standard

This plan is complete only when:

1. per-paper promotion works for unique new concepts
2. `paper-process` is a pure orchestrator
3. `paper-reader` remains propstore-free
4. collection ingestion is incremental by default
5. sync-helper dependence is removed from tests before deprecation
6. every slice above is either checked off or explicitly deferred by the user
