# WS-C: Sidecar atomicity & SQLite discipline

**Status**: OPEN
**Depends on**: WS-A (schema fidelity must land first; WS-C tests assume production schema is reachable from fixtures), WS-CM (canonical micropub payload + Trusty URI identity), WS-Q-cas (branch-head compare-and-swap discipline at propstore call sites — D-23)
**Blocks**: WS-E (source/promote correctness — depends on WS-C Step 2 promote-ordering reorder per D-6); and indirectly WS-K, WS-L which sit downstream of source/promote
**Owner**: Codex implementation owner + human reviewer required

---

## Why this matters

Two of the three highest-cost failure classes in propstore live in this workstream:

1. **A failed promote can poison subsequent successful ones.** `propstore/source/promote.py` writes sidecar rows BEFORE the git transaction commits, with the comment at `:831-839` explicitly acknowledging this inversion. If `repo.families.transact(...)` raises after the sidecar rows land, the sidecar is now ahead of git — and the next attempt to promote the same source slug will collide with the orphaned `claim_core` row keyed on `(artifact_id)` with `promotion_status='blocked'`. The PK is single-id, not `(id, branch)`, so the same artifact_id from the same source on a retry has no slot to land in. Claude cluster A flagged this as HIGH (H2). The defense the comment offers ("blocked claims stay on their source branch") is structurally incorrect once a *retry* of the same promote runs, because the retry inserts the same artifact_id again. **D-6 (DECISIONS.md) settles the structural choice: reorder the writes — git transaction first, sidecar mirror after — so the sidecar is a derived projection of committed git state.**

2. **`materialize` corrupts a worktree before reporting why it refused.** `propstore/storage/snapshot.py:201-216` walks the snapshot files in one loop and writes every non-conflicting destination *before* it knows whether any other file conflicts. The conflict check is in the same loop body (`:205-209`); the raise at `:214-216` happens only after the loop has finished. By the time the user sees `MaterializeConflictError`, half the worktree is already overwritten and the other half is the user's edits. There is no recovery path — the snapshot files have replaced whatever was there. Codex #1.

3. **Two pieces of dedupe code lie about why they are safe.** `propstore/sidecar/claims.py:72-83` and `propstore/sidecar/micropublications.py:17-29` both contain docstrings asserting their `id`s are "content-hash-derived, so two files that carry the same id carry definitionally identical content." They are not. `propstore/families/identity/claims.py:18-25` derives `artifact_id` from the *logical handle* (`namespace:value` where namespace is the source paper slug). `propstore/source/finalize.py:38-40` derives micropub `artifact_id` from `(source_id, claim_id)` — the *referent's* id, not the micropub's content. So a re-promote that legitimately changes the content but keeps the logical handle silently has the second writer dropped. The "first-writer-wins is safe because content is identical" comment is a load-bearing falsehood. Codex #2 and Codex #3. **Per D-7/D-29 the micropub identity moves to WS-CM: a Trusty URI over the full canonical micropub payload. WS-C consumes that closed identity surface for sidecar dedupe; it does not define a placeholder hash and does not wait on WS-M for payload shape.** The claim-side dedupe still needs the `version_id` discipline because `claim_core.artifact_id` remains the *logical* handle by design.

Below this sit two other gaps: `build_repository` swallows `FileNotFoundError` and reports success indistinguishable from a missing sidecar (Claude N HIGH-1 / T1.7), and `_sidecar_content_hash` (`build.py:77-82`) ignores compiler/pass/family semantic version, so a code change that alters compiled output reuses a stale sidecar (Codex #5). **Per Codex 1.15, the cache key is derived from actual inputs rather than a hand-maintained semver constant.**

This is the last "data substrate is a lie" workstream. Once it lands, downstream workstreams can trust that what's in the sidecar matches what's in git, and that what's in git matches what `materialize` produced.

## Review findings covered

| Finding | Source | Citation | Description | Decision |
|---|---|---|---|---|
| **T1.4** | Claude REMEDIATION-PLAN | `propstore/storage/snapshot.py:201-216` | `materialize` preflight conflict pass — no partial overwrite. | Engineering fix; no DECISION required. |
| **T1.6** | Claude REMEDIATION-PLAN | `propstore/source/promote.py:518-548`, `:573`, `:840-851` | SQLite-before-git in promote. | **D-6: REORDER.** Git transaction first, sidecar mirror after. PK rescope rejected. Diagnostics on the sidecar-leads-git path move to in-memory return values from promote. |
| **T1.7** | Claude REMEDIATION-PLAN | `propstore/compiler/workflows.py:609-616` | `build_repository` re-raises sidecar `FileNotFoundError` instead of swallowing. | Engineering fix; no DECISION required. |
| **Codex #1** | `reviews/2026-04-26-codex/workstreams/ws-03-storage-sidecar-identity-atomicity.md` | `propstore/storage/snapshot.py:201-216` | Materialize partial-overwrite. | Engineering fix; no DECISION required. |
| **Codex #2** | Codex ws-03 | `propstore/sidecar/claims.py:72-94`, `propstore/families/identity/claims.py:18-25` | Claim dedupe false content-identity premise — `artifact_id` is logical-derived. | Logical id stays (project principle: handles are stable). Add `version_id` conflict discipline. |
| **Codex #3** | Codex ws-03 | `propstore/source/finalize.py:38-40`, `propstore/sidecar/micropublications.py:17-57` | Micropub IDs not content-derived. | **Identity owned by WS-CM (D-29).** WS-C consumes WS-CM's `micropub_artifact_id` and asserts the sidecar dedupe-shape contract on top of it. |
| **Codex #5** | Codex ws-03 | `propstore/sidecar/build.py:77-82`, `:317-320` | Sidecar cache invalidation ignores compiler/pass/family semantic versions. | **Per Codex 1.15: derive the cache key from actual inputs (sidecar schema version, pass names+versions, generated schema version, dependency pins, build-time config). Manual override secondary.** |
| **Claude A H2** | `reviews/2026-04-26-claude/cluster-A-core-storage-source.md` line 24 | `propstore/source/promote.py:840-851` + `:518-548` | A failed promote can poison subsequent successful ones. | Resolved by D-6 reorder. |
| **Claude N HIGH-1** | `reviews/2026-04-26-claude/cluster-N-compiler-importing.md` lines 74-80 | `propstore/compiler/workflows.py:562-576`, `:609-616` | `build_repository` reports success indistinguishable from "empty repo" / missing sidecar. | Engineering fix; no DECISION required. |

Adjacent findings included in this WS because they sit in the same files and are cheaper to close together than to defer:

| Finding | Citation | Why included |
|---|---|---|
| `claim_concept_link` PK collision on duplicate insert | `propstore/sidecar/schema.py:401-410`, `propstore/sidecar/claims.py:93-94` | The parent dedupe at `:85-92` skips claim rows but the link loop at `:93-94` inserts unconditionally; PK `(claim_id, role, ordinal, concept_id)` will violate. Codex ws-03 first failing test #3. |
| `micropublication_claim` link dedupe correctness | `propstore/sidecar/micropublications.py:48-64` | Sibling of the above. Once WS-M ships content-derived ids, the parent dedupe key is truly idempotent on identical content; the link-side still needs explicit dedupe to survive duplicate input rows from the same compiled batch. |
| `_clean_materialized_semantic_files` rglob+unlink race | `propstore/storage/snapshot.py:228-266` | Already in the same file as T1.4; while we are touching `materialize`, fix the iterator-mutation race. Claude A MED. |

Findings adjacent but DEFERRED out of this WS (and to where):

- Codex #4 (read-only sidecar opens RW) — moves to WS-B (render-policy/web), per REMEDIATION-PLAN Tier 1 grouping. Not WS-C; WS-C is about *write* discipline.
- **Branch-head compare-and-swap for finalize/import/promote** — owned by **WS-Q-cas** (D-23). WS-Q-cas defines the propstore-side discipline (capture expected head, thread to `quire.family_store.transact`, fail-without-mutation on stale head). WS-C tests for promote atomicity (test 2 below) reference WS-Q-cas's test matrix for the concurrent-finalize / concurrent-import scenarios; WS-C does not duplicate that matrix.
- T4.2 Trusty URI provenance export/verification beyond micropub identity — owned by WS-M. The micropub identity primitive itself is owned by WS-CM and consumed here.

## Code references (verified by direct read)

### Materialize partial-overwrite (Codex #1, T1.4)

`propstore/storage/snapshot.py:200-216`:

```python
tracked_paths = {snapshot_file.relpath for snapshot_file in snapshot_files}
conflicts: list[str] = []
written: list[str] = []
for snapshot_file in snapshot_files:
    destination = self.repo.root / snapshot_file.relpath
    if destination.exists() and destination.is_file():
        existing = destination.read_bytes()
        if existing != snapshot_file.content and not force:
            conflicts.append(snapshot_file.relpath)
            continue
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(snapshot_file.content)         # writes BEFORE conflict tally complete
    written.append(snapshot_file.relpath)

if conflicts:
    details = ", ".join(sorted(conflicts))
    raise MaterializeConflictError(f"Refusing to overwrite local edits: {details}")
```

Loop writes before the loop ends. By the time the conflict raise fires, every path in `written` has already been overwritten.

### Promote: sidecar-before-git (T1.6, Claude A H2)

`propstore/source/promote.py:831-852` (verified by Read):

```python
# Mirror blocked claims into the sidecar BEFORE the git commit.
# [comment block defending the inversion at :831-839]
if promotion_plan.blocked_claims:
    _write_promotion_blocked_sidecar_rows(
        repo.sidecar_path,
        promotion_plan.source_branch,
        promotion_plan.slug,
        promotion_plan.blocked_claims,
        promotion_plan.blocked_reasons,
    )

with repo.families.transact(
    message=f"Promote source {slug}",
    branch=repo.snapshot.primary_branch_name(),
) as transaction:
    ...
```

The DELETE-then-INSERT loop inside `_write_promotion_blocked_sidecar_rows` runs at `propstore/source/promote.py:507-548`, with `conn.commit()` at `:573` finalizing the sidecar mirror before `transact()` is even entered. The DELETE at `:507-510` keys on `id` alone:

```python
conn.execute("DELETE FROM claim_core WHERE id = ?", (artifact_id,))
```

Schema (`propstore/sidecar/schema.py:380-399`) declares `claim_core.id` as the only primary key. Branch is a column, not part of the key. **Per D-6 we are NOT changing the PK.** The fix is ordering: drop the sidecar mirror's lead position and let it follow git.

### `build_repository` swallowing FileNotFoundError (T1.7, Claude N HIGH-1)

`propstore/compiler/workflows.py:609-616` (verified by grep — `except FileNotFoundError:` is at `:609`). The compiler then returns a `RepositoryBuildReport` with `claim_count=0, conflict_count=0, phi_node_count=0` whether the sidecar was missing or genuinely empty. Caller cannot distinguish.

### Sidecar cache hash (Codex #5, Codex 1.15)

`propstore/sidecar/build.py:77-82`:

```python
def _sidecar_content_hash(source_revision: str) -> str:
    payload = (
        f"schema_version:{sidecar_schema.SCHEMA_VERSION}\n"
        f"source_revision:{source_revision}\n"
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

`:317-320`:

```python
if not force and sidecar_path.exists() and hash_path.exists():
    existing_hash = hash_path.read_text().strip()
    if existing_hash == content_hash:
        return False
```

A change to any compiler pass, family contract, or compiled-output shape produces a different sidecar from the same git revision. The cache hash will not notice. The user must `--force` to recover. **Codex 1.15 rejects the original "hand-maintained `BUILD_SEMANTIC_VERSION` constant" plan** — that approach silently rots whenever an author forgets to bump. The cache key is derived from inputs that already exist and are already authoritative.

### Claim/micropub identity (Codex #2, Codex #3)

`propstore/sidecar/claims.py:72-94`:

```python
"""...
Bug 5 (v0.3.2): ``artifact_id`` is content-hash-derived, so two
claim files that carry the same id carry definitionally identical
claim content. ...
"""

seen_claim_ids: set[str] = set()
for row in rows.claim_rows:
    claim_id = row.values.get("id")
    if isinstance(claim_id, str) and claim_id in seen_claim_ids:
        continue
    insert_claim_row(conn, row.values)
    if isinstance(claim_id, str):
        seen_claim_ids.add(claim_id)
for row in rows.claim_link_rows:
    insert_claim_concept_link_row(conn, row.values)        # unconditional; will PK-violate
```

The docstring is wrong on the first sentence. `propstore/families/identity/claims.py:18-25` derives `artifact_id` from the *logical handle* — that is by design. Conflict discipline runs on `(artifact_id, version_id)`.

`propstore/source/finalize.py:38-40` (verified by Read):

```python
def _stable_micropub_artifact_id(source_id: str, claim_id: str) -> str:
    digest = hashlib.sha256(f"{source_id}\0{claim_id}".encode("utf-8")).hexdigest()[:24]
    return f"ps:micropub:{digest}"
```

This is the function WS-CM deletes and replaces with `micropub_artifact_id(document)`, a Trusty URI over the full canonical micropub payload. WS-C does not specify the canonicalisation, the algorithm token, the truncation policy, or the URI scheme — those are WS-CM's. WS-C only asserts the dedupe-shape contract: that two micropubs with different authored content end up with different artifact ids in the sidecar.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_T1_4_materialize_atomicity.py`** (new — Codex #1, T1.4)
   - Build a repo with at least three semantic files at known paths.
   - Locally edit one of them so its bytes differ from the snapshot.
   - Call `materialize(force=False)`.
   - Assert: `MaterializeConflictError` raised AND every untouched (non-conflicting) destination file still equals its pre-call bytes.
   - **Must fail today**: `:211 destination.write_bytes(...)` runs in the loop body before the raise.

2. **`tests/test_promote_atomicity.py`** (new — D-6 / T1.6 / Claude A H2)
   - Set up a source branch with a known blocked claim list.
   - Monkeypatch `repo.families.transact` to raise mid-context.
   - Run `promote_source_branch`.
   - Assert: NO orphan sidecar rows exist for the failed promote — `SELECT COUNT(*) FROM claim_core WHERE id = ? AND promotion_status = 'blocked'` returns 0 for every blocked artifact_id; same for `build_diagnostics WHERE diagnostic_kind = 'promotion_blocked' AND source_ref = ?`.
   - Re-run promote (without the monkeypatch).
   - Assert: retry succeeds, no PK violation on `claim_core.id`, blocked rows now present exactly once.
   - Assert: the blocked-claim diagnostic information is reachable from the promote function's *return value* (in-memory `PromotionResult` or equivalent), not only from the sidecar — this is the explicit D-6 redirection of the diagnostic surface.
   - **Note**: concurrent-promote / stale-head scenarios live in WS-Q-cas's test matrix, not here. WS-C's test 2 covers the single-process "git fails after sidecar wrote" failure mode; WS-Q-cas covers "another process raced us and won."
   - **Must fail today**: the sidecar write at `:840-847` precedes `transact`; orphan rows survive the failure and the second insertion at `:518-548` collides on `id`. There is also no return-value channel for the diagnostics yet.

3. **`tests/test_micropub_identity_dedupe_shape.py`** (new — Codex #3 dedupe-shape side; depends on WS-CM closing)
   - Construct two micropubs with the same `(source_id, claim_id)` but different authored payload (different `evidence`, or different `assumptions`, or different `provenance`).
   - Compose the source micropubs document via `_compose_source_micropubs`.
   - Assert: the two micropubs end up at DISTINCT rows in the sidecar `micropublication` table — the dedupe layer does not collapse them.
   - Assert: a freshly authored micropub identical byte-for-byte to a previously authored one collapses to a single row (idempotent dedupe on identical canonical payload).
   - **What this test does NOT assert**: the canonical payload bytes or Trusty URI implementation details. Those are WS-CM's contract. WS-C's contract is "different authored content => different rows; identical authored content => one row" using the WS-CM artifact id.
   - **Must fail today**: `_stable_micropub_artifact_id` ignores every authored field except `(source_id, claim_id)`; the two micropubs collide on artifact id and the second is dropped by `seen_micropub_ids` in `propstore/sidecar/micropublications.py:31-46`.

4. **`tests/test_T1_7_build_repository_propagates_sidecar_errors.py`** (new — T1.7, Claude N HIGH-1)
   - Build a repo, then delete the sidecar file.
   - Call `build_repository`.
   - Assert: raises (or returns a report with `rebuilt=False, sidecar_missing=True`) — not a silent zero-count success.
   - **Must fail today**: `workflows.py:609-616` swallows `FileNotFoundError` and returns zero-everything.

5. **`tests/test_codex2_claim_dedupe_diverges_on_version.py`** (new — Codex #2)
   - Construct two claim rows with the same `artifact_id` but different `version_id`.
   - Build sidecar.
   - Assert: a hard typed conflict diagnostic is emitted; the second claim is NOT silently dropped.
   - **Must fail today**: `populate_claims` first-writer-wins skips on `id` collision regardless of version_id.

6. **`tests/test_codex2_claim_concept_link_dedupe.py`** (new — adjacent, link-side)
   - Construct one claim row with one concept-link row, but submit them twice (simulating a re-promote).
   - Build sidecar twice.
   - Assert: idempotent — no PK violation on `claim_concept_link`.
   - **Must fail today**: link loop at `claims.py:93-94` is unconditional.

7. **`tests/test_codex5_sidecar_cache_derived_invalidation.py`** (new — Codex #5 / Codex 1.15)
   - Build sidecar at a known input set.
   - Vary one input at a time and rebuild without touching `source_revision`:
     - Bump sidecar schema version → assert rebuild.
     - Add or rename a registered compiler/semantic pass → assert rebuild.
     - Bump a registered pass's version field → assert rebuild.
     - Bump generated-schema version → assert rebuild.
     - Bump a relevant dependency pin (e.g. `argumentation`, `gunray`, `quire`, `bridgman`, `ast-equiv`) in the pyproject lock → assert rebuild.
     - Toggle a registered build-time config option → assert rebuild.
     - Change an irrelevant dependency pin (e.g. a dev-only test runner) → assert cache hit (the derivation correctly excludes it).
   - Assert each rebuild trigger fires WITHOUT the user setting any manual-override constant.
   - Separately assert: a documented manual override (`PROPSTORE_SIDECAR_CACHE_BUST` env var or equivalent) forces a rebuild on demand. Override is the secondary path, not primary.
   - **Must fail today**: `_sidecar_content_hash` ignores every input beyond `SCHEMA_VERSION` + `source_revision`.

8. **`tests/test_workstream_c_done.py`** (new — gating sentinel)
   - `xfail` until WS-C closes; flips to `pass` on the final commit. Same pattern as WS-A.

## Production change sequence

Each step lands in its own commit, message of the form `WS-C step N — <slug>`. Run after WS-A, WS-CM, and WS-Q-cas merge; the schema-parity precondition matters because tests 2-7 build sidecars via production schema, the dedupe-shape test depends on WS-CM's real identity surface, and the done gate depends on WS-Q-cas's branch-head matrix.

### Step 1 — Materialize preflight (T1.4, Codex #1)

`propstore/storage/snapshot.py:201-216`:

- Split into two passes. Pass 1 walks `snapshot_files` and ONLY classifies each as `conflict` / `unchanged` / `to_write`. No writes.
- If `conflicts` is non-empty and `not force`, raise `MaterializeConflictError` immediately. No partial state.
- Pass 2 writes the `to_write` set.

Acceptance: test 1 turns green.

### Step 2 — Promote ordering: git first, sidecar after (D-6, T1.6, Claude A H2)

This is the locked-in fix. No optionality. Detailed move list:

1. **Move `_write_promotion_blocked_sidecar_rows` invocation.** Source: `propstore/source/promote.py:840-847`. Destination: AFTER the `with repo.families.transact(...) as transaction:` block closes successfully. Concretely: the new control flow is `transact -> obtain sha -> mirror sidecar (best-effort) -> return result`.
2. **Decide failure mode for the post-commit sidecar mirror.** If the sidecar write itself fails after git commit succeeded, the source-of-truth (git) is still correct and the sidecar can be rebuilt by `build_repository`. The mirror call wraps in a guard that logs a structured warning and surfaces it via the in-memory return value but does NOT raise.
3. **Delete the comment block at `propstore/source/promote.py:831-839`.** It documents the prior bug, not the fix. Replace with a one-line comment: `# Sidecar mirror is a derived projection of committed git state (D-6).`
4. **Add an in-memory diagnostics channel.** `promote_source_branch` currently returns `str` (the commit sha). Change the return type to a `PromotionResult(commit_sha, blocked_claims, sidecar_mirror_ok)` dataclass. The blocked-claim diagnostic information that previously had to be persisted to sidecar-before-git now flows through this return value.
5. **Update callers.** Grep for `promote_source_branch(` across the repo and change call sites to consume `.commit_sha` plus `.blocked_claims` where appropriate. No alias / no shim — per D-3 and per Q's "update the callers" rule.
6. **Keep `_write_promotion_blocked_sidecar_rows` itself unchanged.** Its DELETE-then-INSERT shape at `:497-548` is correct *as a post-git mirror operation*: the DELETE removes any prior promote's mirror rows for this artifact_id and INSERT writes the current state.
7. **Do NOT scope `claim_core` PK by `(id, branch)`.** D-6 explicitly rejects this path.
8. **Branch-head CAS coordination.** This step does NOT add expected-head capture or stale-head rejection — that work belongs to WS-Q-cas. WS-C step 2 only fixes the within-process ordering. The cross-process race window closes when WS-Q-cas threads `expected_head` through `quire.family_store.transact`.

Acceptance: test 2 turns green. The single-process orphan-row scenario disappears because the sidecar mirror never runs unless git committed. Concurrent-process safety is WS-Q-cas's gate.

### Step 3 — Consume WS-CM micropub identity for dedupe-shape contract

WS-C does not define the canonical payload shape and does not install a temporary hash. WS-CM has already deleted the old `(source_id, claim_id)` identity surface and installed `micropub_artifact_id(document)` over the full canonical payload. WS-C's job is to make the sidecar dedupe layer use that real identity correctly.

1. **Verify the sidecar receives WS-CM-produced ids.** Follow the source-finalize path into the sidecar row and assert the `micropublication.id` value is the WS-CM `micropub_artifact_id(document)` result.
2. **Verify the dedupe layer consumes the payload-derived identity correctly.** `propstore/sidecar/micropublications.py:17-57` uses `seen_micropub_ids` for first-writer-wins. The dedupe key is the WS-CM id; confirm the field it indexes matches.
3. **Delete the load-bearing-falsehood docstring at `propstore/sidecar/micropublications.py:14-29`.** Replace with: `"""Populate micropublication tables. ``micropublication.id`` is derived from the full canonical payload by WS-CM. Identical authored content yields identical ids; modified content yields a new id. First-writer-wins dedupe on this id is therefore safe."""`
4. **Update the matching `propstore/sidecar/claims.py:72-83` docstring** with the truth (see Step 4).
5. **Acknowledge the new-id-on-modification semantic.** Modifying any authored field of a micropub produces a new artifact id — that is correct, because it is a new version of the assertion. Grep for downstream consumers that previously assumed micropub artifact ids were stable across re-promotes; update any UI surface that says "the micropub for claim X" to query by `(claims, source)` rather than by artifact id.

Acceptance: test 3 turns green. WS-CM's identity tests cover the hash/canonical-payload side; WS-C covers sidecar dedupe behavior using that id.

### Step 4 — Claim-side `version_id` discipline (Codex #2, link-side)

`claim_core.artifact_id` remains a logical handle. The fix is on the dedupe side:

1. Verify (per WS-A) that `claim_core` has `version_id` and `content_hash` columns. WS-A schema work should already cover this.
2. Replace the first-writer-wins dedupe at `propstore/sidecar/claims.py:85-92` with the discipline:
   - Same `artifact_id` AND same `version_id`: idempotent skip.
   - Same `artifact_id` AND different `version_id`: emit a typed `claim_version_conflict` build diagnostic, do NOT insert the second row.
3. Replace `propstore/sidecar/claims.py:93-94` unconditional INSERT with explicit dedupe via `seen_link_keys: set[tuple[str, str, int, str]]` keyed on the full PK tuple `(claim_id, role, ordinal, concept_id)`.
4. Delete the load-bearing-falsehood docstring at `propstore/sidecar/claims.py:72-83`. Replace with the truth: `artifact_id` is the *logical* id; `version_id` is the content hash; conflict discipline runs on `(artifact_id, version_id)`.

Acceptance: tests 5, 6 turn green.

### Step 5 — `build_repository` propagates sidecar errors (T1.7)

`propstore/compiler/workflows.py:609-616`:

- Delete the bare `except FileNotFoundError:` swallow.
- Replace with explicit `RepositoryBuildReport(sidecar_missing=True, ...)` and add the field to the report dataclass.
- Update every caller of `build_repository` to surface the new field; specifically `pks build` in `propstore/app/compiler.py` should set a non-zero exit code on `sidecar_missing=True`.

Acceptance: test 4 turns green. Verify by running `pks build` against an empty repo and confirming exit code distinguishes "no concepts" (currently returns early at workflows.py:404-413) from "sidecar missing."

### Step 6 — Derived sidecar cache key (Codex #5 / Codex 1.15)

`propstore/sidecar/build.py:77-82` — replace the hand-coded payload with a derivation over actual inputs. The cache key SHA-256-digests a canonical-JSON document with these fields:

- `sidecar_schema_version`: read from `propstore/sidecar/schema.py::SCHEMA_VERSION` (existing).
- `passes`: a sorted list of `(name, version)` tuples enumerated from the registered compiler/semantic pass registry. Registry traversal is read-only; passes that ship without a version field are a hard error (Q-style: fix the pass, don't paper over it).
- `generated_schema_version`: from the generated-schema module (the schema produced by the compiler — distinct from the sidecar storage schema).
- `dependency_pins`: a sorted list of `(distribution_name, locked_version)` tuples filtered to packages whose output rows the compiler reads — start the allowlist with `argumentation`, `gunray`, `quire`, `bridgman`, `ast-equiv` and add to it as new derivations land. Pins are read from the project's lockfile (uv.lock) at build time; verify the read path is deterministic.
- `build_time_config`: a sorted dict of registered build-time options that change compiled output (start with the empty allowlist; add explicit entries as options are registered).
- `source_revision`: as today.

The final cache hash is `sha256(canonical_json(<that document>))`. Any change to any input causes a different hash. No author has to remember to bump anything.

Manual override exists as a secondary path:

- A `PROPSTORE_SIDECAR_CACHE_BUST` env var (or `--rebuild` CLI flag, choose one and document) forces a rebuild on demand. Used when an author wants to force a fresh build despite identical inputs. NOT the primary invalidation mechanism.

Add structured logging at the rebuild decision point so the user sees *which* input changed when a rebuild fires.

Acceptance: test 7 turns green. No CI gate on a hand-maintained constant — there is no constant.

### Step 7 — Adjacent fixes in the same files

- `propstore/storage/snapshot.py:228-266` — fix the `rglob` + `unlink` race in `_clean_materialized_semantic_files`. Accumulate the deletion list first, then iterate and delete. Same shape as Step 1 preflight.

### Step 8 — Close gaps and gate

- Update `docs/gaps.md`: remove the entries for T1.4, T1.6, T1.7, and the Codex #1/#2/#3/#5 mirrors. Add a `# WS-C closed <sha>` line.
- Flip `tests/test_workstream_c_done.py` from `xfail` to `pass`.
- Update this file's STATUS line to `CLOSED <sha>`.

Acceptance: `tests/test_workstream_c_done.py` passes; gaps.md reflects closure; the per-PR architecture-gate (T0.3) still runs green.

## Acceptance gates

Before declaring WS-C done, ALL must hold:

- [ ] `uv run pyright propstore` — passes with 0 errors.
- [ ] `uv run lint-imports` — passes (this WS does not change contracts).
- [ ] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-C tests/test_T1_4_materialize_atomicity.py tests/test_promote_atomicity.py tests/test_micropub_identity_dedupe_shape.py tests/test_T1_7_build_repository_propagates_sidecar_errors.py tests/test_codex2_claim_dedupe_diverges_on_version.py tests/test_codex2_claim_concept_link_dedupe.py tests/test_codex5_sidecar_cache_derived_invalidation.py tests/test_workstream_c_done.py` — all green.
- [ ] Full suite `powershell -File scripts/run_logged_pytest.ps1` — no NEW failures vs. the WS-A merge-time baseline.
- [ ] `propstore/sidecar/claims.py` and `propstore/sidecar/micropublications.py` no longer contain the "content-hash-derived, so two files that carry the same id carry definitionally identical content" docstrings.
- [ ] `propstore/source/promote.py` no longer carries the "writing sidecar BEFORE the git commit" comment block at `:831-839`. The sidecar mirror runs strictly after `transact` succeeds.
- [ ] `promote_source_branch` returns a `PromotionResult` (or equivalent) carrying blocked-claim diagnostics in-memory; persisted-state-as-diagnostic-channel is gone.
- [ ] Micropub artifact ids in the sidecar are produced by WS-CM's `micropub_artifact_id`; no placeholder hash exists in WS-C.
- [ ] `propstore/compiler/workflows.py` no longer swallows `FileNotFoundError` from the sidecar.
- [ ] `_sidecar_content_hash` derives its key from the inputs listed in Step 6; no hand-maintained `BUILD_SEMANTIC_VERSION` constant exists in tree.
- [ ] WS-Q-cas's promote-related test matrix runs and is green (hard dependency; WS-C does not own those tests but will not declare done while they fail).
- [ ] WS-C property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged WS-C test run or a named companion run.
- [ ] `docs/gaps.md` has no open rows for the findings listed in the table above.
- [ ] Workstream STATUS line is `CLOSED <sha>`.

## Done means done

WS-C is done when **every finding in the table at the top is closed**, not when "most" are closed. Specifically:

- T1.4, T1.6, T1.7, Codex #1, Codex #2, Codex #3 (dedupe-shape side; identity side owned by WS-CM), Codex #5, Claude A H2, Claude N HIGH-1 — every one has a corresponding green test in CI.
- The two false docstrings are gone — no inheritor of this codebase reads "artifact_id is content-hash-derived" and is misled.
- A failed promote leaves no orphan sidecar state (single-process). Concurrent-process safety is gated by WS-Q-cas's matrix passing.
- Modified-payload micropubs receive new ids (verified at the dedupe layer here; verified at the identity layer in WS-CM).
- The sidecar cache invalidates automatically when any of its derived inputs changes (no hand-bumped constant).
- `gaps.md` is updated. The workstream's gating sentinel (`test_workstream_c_done.py`) has flipped from xfail to pass.

If any one of those is not true, WS-C stays OPEN.

## Papers / specs referenced

- **Trusty URI / nanopub** (Kuhn 2014) — drives the *intent* of the micropub identity work. **WS-CM owns the micropub identity implementation.** WS-C consumes the API. Broader provenance export remains in WS-M.
- No paper drives Steps 1, 2, 4-8 — those are software-engineering atomicity gates.

## Cross-stream notes

- **Hard dependency on WS-A.** Tests 2-7 build sidecars and inspect schema columns; they assume `_REQUIRED_SCHEMA` matches production. Do not start WS-C until WS-A merges.
- **Hard dependency on WS-CM.** WS-CM owns canonical micropub payload and Trusty URI identity. WS-C consumes `micropub_artifact_id` and does not add a placeholder identity path.
- **Hard dependency on WS-Q-cas (D-23).** WS-Q-cas owns the propstore-side branch-head compare-and-swap discipline (capture expected head, thread to `quire.family_store.transact`, fail-without-mutation on stale head). WS-C's promote ordering fix (Step 2) closes the within-process orphan-row window; WS-Q-cas closes the cross-process stale-head window. WS-C tests do not duplicate WS-Q-cas's concurrent-finalize / concurrent-import / concurrent-materialize matrix; WS-C's done-criterion includes WS-Q-cas's matrix passing.
- **Unblocks WS-E.** WS-E (source/promote correctness) sits on top of a corrected promote ordering. WS-E can begin once WS-C Step 2 lands.
- **Indirect bearing on WS-K and WS-L.** Both depend on WS-E, transitively on WS-C. WS-M depends on WS-CM directly for identity, not on WS-C.

## What this WS does NOT do

- Does NOT implement Trusty URI hashing or verification for micropub identity — owned by WS-CM.
- Does NOT specify any canonical-JSON convention, hash algorithm, URI scheme, or truncation policy for micropub identity — owned by WS-CM.
- Does NOT add branch-head compare-and-swap to import/finalize/promote — owned by WS-Q-cas.
- Does NOT touch read-only sidecar opens (Codex #4 / T1.5) — that's WS-B (render policy / web boundary).
- Does NOT change embedding model key sanitization — out of scope; folded into WS-K per D-19.
- Does NOT re-architect the sidecar build pipeline. Step 6 derives a cache key from existing inputs; deeper restructure is research-tier and not in scope.
- Does NOT change short 16/24-hex identity hashes to full SHA-256 — folded into WS-M per D-20.

## Resolved / owned-elsewhere questions

The following items were open in earlier drafts of WS-C and have since been resolved or relocated:

- **Micropub canonical-JSON convention** — Owned by WS-M.
- **Trusty URI module location and API** — Owned by WS-M (`propstore/provenance/trusty.py`).
- **Truncation policy for the micropub artifact id suffix** — Owned by WS-M (resolved at the project-wide identity-hash-policy level via D-20).
- **Branch-head compare-and-swap discipline** — Owned by WS-Q-cas (D-23).
- **Cache invalidation strategy** — Resolved per Codex 1.15: derived from inputs, manual override is secondary. No hand-maintained semver constant.
- **Concurrent-promote test matrix** — Owned by WS-Q-cas.
