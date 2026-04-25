# Compiler + Sidecar + Semantic Passes — Adversary + Analyst Review

**Scope**: `propstore/compiler/`, `propstore/sidecar/`, `propstore/semantic_passes/`, `propstore/contracts.py`, `propstore/contract_manifests/`.
**Reviewer role**: adversary against the core non-commitment / render-time-filter principle; analyst for bugs.

## Principle at stake (quoted verbatim from CLAUDE.md)

> ### Design checklist (before any data-flow decision)
> 1. Does this prevent ANY data from reaching the sidecar? If yes → WRONG.
> 2. Does this require human action before data becomes queryable? If yes → WRONG.
> 3. Does this add a gate anywhere before render time? If yes → WRONG.
> 4. Is filtering happening at build time or render time? If build → WRONG.

> **"The system needs a formal non-commitment discipline at the semantic core."**
> **"Do not collapse disagreement in storage unless the user explicitly requests a migration."**

And disciplines.md rule 5, cited verbatim *inside the source code itself* at `sidecar/build.py:11-12` and `sidecar/schema.py:12`: "Filter at render, not at build." The codebase cites the rule and then violates it in neighboring files.

---

## Design Checklist Violations (per rule)

### Rule 1 — "Does this prevent ANY data from reaching the sidecar?"

**HIGH: `propstore/compiler/workflows.py:131-141, 276-285, 305-309, 324-328, 345-355, 360-363, 394-397, 399-402, 405-415`**
`build_repository` raises `CompilerWorkflowError` on: concept schema errors, form validation failure, concept validation failure, context schema errors, context validation failure, and claim validation failure in two places (`claim_pipeline_result.output` not a `ClaimCheckedBundle`, and `claim_pipeline_result.errors` non-empty). Each path aborts BEFORE `build_sidecar` is ever called — the sidecar is not written at all. Data never reaches storage.

`sidecar/build.py:1-13` docstring boasts that `_raise_on_raw_id_claim_inputs` was removed and replaced with a quarantine-row pattern. The exact same anti-pattern persists in the outer `build_repository` workflow — **form validation failure, concept validation failure, context validation failure, and claim validation failure all still abort the build with no quarantine path**. The fix applied to raw-ids was not generalized.

Severity: **HIGH**.
Fix: convert each abort into (a) a `build_diagnostics` row attached to a synthetic/quarantine entity of the affected family, and (b) a `build_status='blocked'` annotation on the family's core row. Never refuse the build. Render policy decides.

**HIGH: `propstore/sidecar/build.py:95-97`**
```python
if not form_result.ok or not isinstance(form_result.output, FormCheckedRegistry):
    errors = ", ".join(error.render() for error in form_result.errors)
    raise ValueError(f"form validation failed: {errors}")
```
Form validation failure aborts the sidecar build. No `form` rows, no `build_diagnostics` rows, nothing. Rule 1 violation.
Fix: emit partial form rows + quarantine diagnostics. Proceed.

**HIGH: `propstore/sidecar/build.py:159-161`**
```python
if not isinstance(claim_pipeline_result.output, ClaimCheckedBundle):
    errors = ", ".join(error.render() for error in claim_pipeline_result.errors)
    raise ValueError(f"claim validation failed: {errors}")
```
Claim-pipeline failure where `output is None` still aborts. Per `runner.py:47-58`, this happens when a pass returns None and emits errors. The entire build dies despite the raw-id quarantine path existing.
Fix: accept `None` output, still produce concept/source/context rows, and write synthetic `build_diagnostics` rows.

**HIGH: `propstore/sidecar/passes.py:526-529, 539-542, 599-603, 612-615, 773-776`**
Five build-time aborts via `sqlite3.IntegrityError`:
- L526-529: stance references nonexistent source claim
- L539-542: stance references nonexistent target claim
- L599-603: justification references nonexistent conclusion
- L612-615: justification references nonexistent premise
- L773-776: micropublication references nonexistent claim

Each kills the entire sidecar build because of ONE dangling reference in ONE artifact. The render layer exists precisely to filter these; moving the decision to build time violates rules 1, 3, and 4. These bubble up through `compile_sidecar_build_plan` into `build_sidecar`'s top-level try/except that deletes the sidecar (L307-311) — total data loss.

Fix: INSERT the row anyway with a NULL-or-synthetic FK plus a `build_diagnostics` row (`diagnostic_kind='dangling_reference'`, `blocking=1`). Let render decide.

**MEDIUM: `propstore/sidecar/passes.py:544-547` and `propstore/sidecar/claim_utils.py:513-514`**
Invalid stance type raises `ValueError`. One bad enum value in one stance file takes down the entire build.
Fix: store the raw stance-type string plus a `build_diagnostics` row marking it unknown.

**MEDIUM: `propstore/sidecar/passes.py:596-598`**
`ValueError` on justification entry missing an `id`. Aborts build.

**MEDIUM: `propstore/sidecar/claim_utils.py:515-518`**
Same dangling-reference build-time gate at the in-claim stance level.

**MEDIUM: `propstore/sidecar/claim_utils.py:454-455`**
Badly-typed `variables` on an algorithm claim raises `ValueError`, aborting build.

**LOW: `propstore/sidecar/claim_utils.py:102`, `111`**
`coerce_stance_resolution` and `resolution_opinion_columns` raise `ValueError` on non-dict inputs. Another build-time abort path for shapes that should be quarantined.

**LOW: `propstore/sidecar/passes.py:834`**
`raise ValueError("checked claim bundle is required to populate claims")` — internal invariant that still produces a hard abort. Prefer a structured diagnostic.

**LOW: `propstore/semantic_passes/runner.py:55-58`**
A pass returning None output with zero errors raises `PipelineExecutionError`. The "None + errors" branch immediately above returns a structured failure cleanly; the "None + no errors" fallthrough should too.

**LOW: `propstore/sidecar/embedding_store.py:237`**
```python
if claim.seq is None:
    raise ValueError(f"Claim {claim.claim_id} has no sidecar sequence")
```
Inside `load_entities` — a runtime assertion disguised as validation. A single claim without a seq kills any caller iterating the full store. Should yield a `build_diagnostics`-like signal or skip that entity.

### Rule 2 — "Does this require human action before data becomes queryable?"

No direct violations (no confirm/approve prompts). Consequential: Rule-1 gates force the author to fix source before any sidecar exists.

### Rule 3 — "Does this add a gate anywhere before render time?"

All Rule-1 violations also violate Rule 3.

**HIGH (structural): `propstore/sidecar/build.py:307-311`**
```python
except BaseException:
    conn.close()
    if sidecar_path.exists():
        sidecar_path.unlink()
    raise
```
ANY exception during sidecar population — dangling FK, bad stance type, schema bug, SQLite quirk, OOM, Ctrl+C, SystemExit — deletes the sidecar entirely. `BaseException` even grabs KeyboardInterrupt and SystemExit, so an interrupted build is an *erased* build. This meta-gate turns any narrow gate into total data loss.

Fix: scope try/except to individual populate functions. On per-populate failure, write a `build_diagnostics` row and continue. Only nuke the sidecar when the schema itself can't be created. Narrow `BaseException` to `Exception`.

### Rule 4 — "Is filtering happening at build time or render time?"

Schema v3 expresses the render-time-filter pattern correctly: `claim_core.build_status`, `claim_core.stage`, `claim_core.promotion_status`, and the `build_diagnostics` quarantine table. **The write side ignores this contract** except for the raw-id path.

---

## Build-Time Filtering

| Location | What gets filtered out | Severity |
|---|---|---|
| `compiler/workflows.py:131-141` | concepts with schema errors (whole build aborts) | HIGH |
| `compiler/workflows.py:186-196, 405-415` | claims with document-schema errors | HIGH |
| `compiler/workflows.py:212-222, 345-355` | contexts with schema errors | HIGH |
| `compiler/workflows.py:276-285` | concepts (build path) | HIGH |
| `compiler/workflows.py:305-309` | all data when forms fail | HIGH |
| `compiler/workflows.py:324-328` | all data when concepts fail | HIGH |
| `compiler/workflows.py:359-363` | all data when contexts fail | HIGH |
| `compiler/workflows.py:394-397, 399-402` | all data when claims fail | HIGH |
| `sidecar/build.py:95-97` | downstream data when forms fail | HIGH |
| `sidecar/build.py:159-161` | downstream data when claim pipeline output is None | HIGH |
| `sidecar/build.py:307-311` | entire sidecar unlinked on any exception | HIGH |
| `sidecar/passes.py:526-529` | dangling stance source claim | HIGH |
| `sidecar/passes.py:539-542` | dangling stance target claim | HIGH |
| `sidecar/passes.py:544-547` | unknown stance type | MEDIUM |
| `sidecar/passes.py:596-598` | missing justification id | MEDIUM |
| `sidecar/passes.py:599-603` | dangling justification conclusion | HIGH |
| `sidecar/passes.py:612-615` | dangling justification premise | HIGH |
| `sidecar/passes.py:773-776` | dangling micropub claim | HIGH |
| `sidecar/passes.py:834` | missing claim bundle invariant | LOW |
| `sidecar/claim_utils.py:454-455` | badly-typed algorithm variables | MEDIUM |
| `sidecar/claim_utils.py:513-514` | unknown in-claim stance type | MEDIUM |
| `sidecar/claim_utils.py:515-518` | dangling in-claim stance target | HIGH |
| `sidecar/claim_utils.py:102` | non-dict stance resolution | LOW |
| `sidecar/claim_utils.py:111` | non-dict stance opinion | LOW |
| `sidecar/embedding_store.py:237` | claim without seq (kills load_entities caller) | LOW |
| `semantic_passes/runner.py:55-58` | pass returning None without errors | LOW |

**Count: 26 distinct build-time filter/gate sites.** The design principle forbids every one.

---

## Gate Introductions

The most dangerous single pattern is the catch-all at `sidecar/build.py:307-311`. It converts every narrower gate above into a total-data-loss outcome. `BaseException` even catches Ctrl+C and SystemExit.

`sidecar/build.py:79-84` has an implicit gate via content-hash short-circuit — correct in principle, but combined with the non-atomic write it has a stale-read failure mode (see Sidecar Correctness).

---

## Bugs & Silent Failures

### Race / atomicity

**HIGH: `propstore/sidecar/build.py:246-314` — non-atomic sidecar write**

Sequence:
1. L246-247: `sidecar_path.unlink()` if exists (destroys old sidecar first).
2. L249: open new sqlite db at final path.
3. L251-306: populate + commit.
4. L307-311: on exception, unlink.
5. L314: `hash_path.write_text(content_hash)`.

Failure modes:
- Crash between step 2 and commit: sidecar is a partial sqlite db. In-build except unlinks it *if reachable*; process kill / power loss bypasses that. The `.hash` file still holds prior-successful hash → next invocation sees "hash matches" and short-circuits against empty db.
- Crash between commit and hash-write: sidecar populated; hash points at prior build. Next invocation rebuilds (wasteful, not corrupting).
- Concurrent builds: both unlink, both open at same path, writes interleave. SQLite locks the DB but nothing locks `.hash`.

**Correctness bug**: crash mid-write leaves stale-but-hash-matching partial DB.
Fix: write to `sidecar_path.with_suffix(".tmp")`, fsync, `os.replace` to final path, then write and fsync the hash file.

**MEDIUM: `propstore/sidecar/build.py:314`**
`hash_path.write_text(content_hash)` is not fsync'd. OS crash → stale hash.

### Hash / addressing correctness

**MEDIUM: `propstore/sidecar/build.py:81-84` — content hash does not include schema or compiler version**
`commit_hash` is git commit SHA only. Does NOT include:
- `SCHEMA_VERSION` (currently 3). If schema bumps to 4 with unchanged commit, sidecar won't rebuild.
- Compiler code version. Changes to `passes.py` altering row shape won't invalidate the cached sidecar.
- Embedding model version.

Fix: hash = sha256(commit_hash + SCHEMA_VERSION + compiler_version).

**LOW: `propstore/sidecar/build.py:73-84`**
No validation that explicit `commit_hash` argument matches the tree state. External callers passing stale hash poison `.hash`. Latent risk for SDK consumers.

**MEDIUM: `propstore/sidecar/passes.py:212` and `propstore/sidecar/concept_utils.py:17, 22`**
```python
content_hash = record.version_id.removeprefix("sha256:")[:16]
```
Truncates to 16 hex chars. No UNIQUE constraint, no collision detection. Duplicated at two sites, risk of drift.

### Silent failures / swallowed exceptions

**MEDIUM: `propstore/sidecar/build.py:293-297`**
```python
except (ImportError, Exception) as exc:
    ...
```
Catches base `Exception` and continues silently. Stderr noise, no `build_diagnostics`. `(ImportError, Exception)` is redundant syntax (suggests widening over time).

**LOW: `propstore/sidecar/build.py:240-241`**
`except ImportError: pass` — missing `sqlite-vec` silently drops all embeddings, no diagnostic.

**LOW: `propstore/sidecar/claim_utils.py:370-376`**
Unparseable value logged via `logging.getLogger(__name__).warning(...)`. No `build_diagnostics` row. Principle: diagnostics must be queryable, not stderr-only.

**MEDIUM: `propstore/sidecar/passes.py:422-433`**
`dim_verified` silently set to 0 on lookup-failure AND on verification-failure. No diagnostic distinguishes the cases.

**MEDIUM: `propstore/sidecar/passes.py:435-438`**
Silent fallback to unparsed operation on `AlgorithmParseError`. No diagnostic. Dedup key interaction at L439 can produce surprising merges.

**LOW: `propstore/compiler/workflows.py:458-466`**
Only `FileNotFoundError` triggers the fallback, but `WorldModel(repo)` can fail for other reasons (schema drift, corruption). Non-FNF errors bubble up; FNF silently reports zero conflicts.

### Embedding store

**LOW: `propstore/sidecar/embedding_store.py:473, 535`**
```python
if current_hash != status_lookup.get((model_key, claim_id), ""):
    report.stale += 1
```
If the status row is missing from the snapshot, `status_lookup.get(...) == ""`. `current_hash != ""` is always True → always `stale`. Orphan-vs-stale attribution is inaccurate when status is absent.

**LOW: `propstore/sidecar/embedding_store.py:520-528`**
`_restore_concepts` loops over `snapshot.models` but does NOT re-insert into `embedding_model` (unlike `_restore_claims` at L451-459). Asymmetric. Works only because both loops run on the same `snapshot.models` — if a future refactor splits them, concept restore would miss model registration.

### Incremental rebuild edge cases

**LOW: `propstore/sidecar/build.py:215-244`**
Embedding snapshot extracted from the existing sidecar BEFORE new one is created. Concurrent builds race on snapshot extraction and unlink. SQLite locks the DB; nothing locks `.hash`.

### Misc correctness

**LOW: `propstore/compiler/workflows.py:399-402`**
Indentation anomaly — closing paren dedented one space. Runs, lint hazard.

**LOW: `propstore/compiler/workflows.py:371, 377-404`**
`claim_files` initialized to None on L371, reassigned inside `if files:`. Used only in FNF-fallback. Confusing.

**LOW: `propstore/sidecar/passes.py:439`**
`dedup_key = (output_form, tuple(sorted(input_forms)), canonical_operation)` — sorts input_forms. Merges parameterizations with different orderings of the same inputs. Correct for current form algebra; risk for non-commutative future operations.

**MEDIUM: `propstore/sidecar/claim_utils.py:240`**
```python
row.get("build_status") or "ingested",
```
`build_status=""` silently becomes `"ingested"`. Use `row.get("build_status", "ingested")` or explicit `is None` check.

**LOW: `propstore/sidecar/concept_utils.py:102-126`**
`resolve_concept_reference` iterates all concepts linearly for fallback lookup. O(N × alias_count) per call. Scalability cliff at ~10k+ concepts.

**LOW: `propstore/sidecar/concepts.py:76-86`**
`CREATE VIRTUAL TABLE concept_fts` inside `populate_concept_sidecar_rows`. Inconsistent with `claim_fts` which is created in `create_claim_tables`. Drift.

**LOW: `propstore/sidecar/query.py:36-42`**
Returns empty columns tuple on zero rows. Callers rendering headers see nothing. Should derive columns from `cursor.description`.

**LOW: `propstore/sidecar/query.py:27`**
`PRAGMA query_only=ON` — good defensive measure, not effective against ATTACH/DETACH. Minor.

### Semantic pass / registry

**LOW: `propstore/semantic_passes/runner.py:61-65`**
Only reachable when no passes registered and start != target. Worth a unit test.

**LOW: `propstore/semantic_passes/registry.py:74-80`**
Append-only registration; strict stage adjacency in insertion order. Plugin load races or import reordering produce `PipelineRegistryError`. Fragile: no topological sort, no dependency declaration beyond adjacency.

### Contracts

**LOW: `propstore/contracts.py:287-298`**
`CONTRACT_MANIFEST_PATH` computed at module load. `--write` in read-only install paths → `PermissionError` with no helpful message.

**LOW: `propstore/contracts.py:51-63`**
`iter_semantic_pass_classes` rebuilds registry on every call. Not idempotent if family registration has side effects. Currently safe; latent fragility.

**LOW: `contract_manifests/semantic-contracts.yaml`** — 3800 lines, machine-generated. Serves as persisted contract hash. Skim only; no red flags.

---

## Sidecar Correctness (summary)

1. **Non-atomic sidecar write** (HIGH) — crash mid-build leaves stale-hash-matching partial DB.
2. **Hash excludes SCHEMA_VERSION** (MEDIUM) — schema upgrades don't trigger rebuild.
3. **Embedding restore catches base `Exception`** (MEDIUM) — silent data loss.
4. **Global try/except nukes entire sidecar** (HIGH) — meta-level non-commitment violation.
5. **`content_hash` truncated to 16 hex** with no UNIQUE constraint, duplicated logic (MEDIUM).
6. **`build_status` default uses `or` coercion** (MEDIUM) — empty string becomes `'ingested'`.
7. **`BaseException` catch** at `build.py:307` — Ctrl+C destroys sidecar.
8. **Embedding-restore orphan/stale attribution off** when status missing (LOW).

---

## Dead Code / Drift

- `propstore/sidecar/build.py:293` — `except (ImportError, Exception)` redundant syntax.
- `propstore/compiler/workflows.py:47` — `CompilerWorkflowError(Exception)` plain Exception; no structured catcher hierarchy.
- `propstore/semantic_passes/types.py:51-55` — `PassDiagnostic.lower()` and `__contains__` let callers treat diagnostics as strings. Leaky abstraction; relic of prior str-based diagnostic.
- `propstore/semantic_passes/diagnostics.py` — 11 lines, one function. Could fold into `types.py`.
- `propstore/sidecar/concept_utils.py:14-22` vs `propstore/sidecar/passes.py:212` — duplicated 16-char hash truncation.
- `propstore/sidecar/concepts.py:76-86` — `concept_fts` schema created inside a populate function; inconsistent with `claim_fts`.
- `propstore/compiler/__init__.py:10` — re-exports `ResolvedReference` from `ir.py` as backcompat shim for quire's `ReferenceResolution`. Deprecation-worthy.
- `propstore/sidecar/embedding_store.py:491-527` vs `423-489` — `_restore_concepts` is a near-copy of `_restore_claims` minus the `INSERT INTO embedding_model`. Factor common path.

---

## Positive Observations

- **Schema v3 is the right shape.** `claim_core.build_status`, `claim_core.stage`, `claim_core.promotion_status`, and `build_diagnostics` form a proper non-commitment storage surface. Bugs are on the write side.
- **Raw-id quarantine path works.** `sidecar/passes.py:704-755` and `sidecar/claims.py:30-56` correctly implement "no data is refused." This is the canonical pattern the other gates should be converted into.
- **Grounded-fact persistence (`sidecar/rules.py`) is exemplary.** Explicit non-commitment anchor in the docstring; companion `grounded_fact_empty_predicate` table preserves empty-verdict semantics; composite primary key hardens set semantics; four-section keys always present on read; verbatim paper citations with section/page numbers; round-trip property pinned by test. **This module shows what the rest of the write side should look like.**
- **Content-hash addressing via `.hash` file is conceptually right** (modulo schema-version bug).
- **Compilation context is immutable** (`compiler/context.py:36-45`: `MappingProxyType`, `frozenset`).
- **Semantic pass runner has clear stage contracts** (`runner.py:33-42`).
- **Compiler architecture is a real abstraction, not inline spaghetti.** Families → stages → passes → diagnostics.
- **Output-path plumbing exists** — provides the hook for atomic swap refactor.
- **`sidecar/build.py:11-12` docstring cites disciplines.md rule 5 by name** — principle is top-of-mind, even if only half-honored.
- **Contract manifest generation (`contracts.py`)** produces a deterministic diffable artifact.
- **`sidecar/query.py:27`** sets `PRAGMA query_only=ON`.
- **Micropublication population (`sidecar/micropublications.py`)** is thin, no hidden logic.
- **Typed row bundles (`sidecar/stages.py`)** wrap insert tuples in frozen dataclasses — machine-checkable contract between compile and populate.
- **Embedding store has `_is_missing_table_error` defensive lookups** — gracefully handles sidecars built before embedding tables existed, without aborting reads.

---

## Cross-cutting recommendations

1. **Convert `build_sidecar`'s top-level try/except (`build.py:307-311`)** from "unlink everything" to "write a `build_diagnostics` row, commit what's inserted, DO NOT unlink." Narrow `BaseException` → `Exception`. Single change defuses every HIGH-severity gate.

2. **Generalize the raw-id quarantine pattern** (`sidecar/passes.py:704-755`) to:
   - dangling stance targets/sources → synthetic FK + `build_diagnostics`
   - dangling justification conclusions/premises → same
   - dangling micropub claims → same
   - unknown stance types → insert with raw type + diagnostic
   - form validation failures → partial form rows + diagnostics
   - claim pipeline output = None → skip rows, emit pipeline-level diagnostic
   - concept / context schema errors → minimal stub rows + diagnostics

3. **Fix content-hash addressing** to include `SCHEMA_VERSION` and a compiler-version salt.

4. **Make the sidecar write atomic** — tmp path + fsync + `os.replace` + fsync hash.

---

## Scope coverage

Reviewed: `compiler/` (workflows, context, ir, references, `__init__`), `sidecar/` (build, schema, passes, claims, claim_utils, concepts, concept_utils, sources, micropublications, query, rules, stages, embedding_store, `__init__`), `semantic_passes/` (runner, registry, types, diagnostics, `__init__`), `contracts.py`, and `contract_manifests/semantic-contracts.yaml` (skimmed; 3800-line generated file).

All files in scope inspected.
