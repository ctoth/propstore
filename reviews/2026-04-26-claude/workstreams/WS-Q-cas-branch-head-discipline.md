# WS-Q-cas: Branch-head CAS discipline at propstore call sites

**Status**: CLOSED 8b1ff8ec
**Depends on**: WS-A (test fixture parity — without it, race tests are written against fictional schemas), WS-O-qui (quire's expected-head primitives must be transactional, not advisory)
**Blocks**: WS-C (atomicity tests assume CAS already exists), WS-E (source promote ordering relies on this discipline)
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)
**Spawned by**: DECISIONS.md D-23 (Codex addendum 1.7)

---

## Why this workstream exists

WS-O-qui specifies what quire's kernel must do: turn `_check_preemptive_head` from an advisory pre-flight peek into a transactional CAS commit primitive that refuses to write when the branch head has moved since the caller read it. That is the kernel side. It is necessary and not sufficient.

Even with a perfect kernel, propstore can race itself if call sites do any of the following:

- Read the branch head, drop the value, then call a commit primitive that re-reads the head internally. The kernel CAS would compare the head against itself; both writers would observe a clean tip and both would commit.
- Capture the head correctly but fail to thread it through the layers between the read site and the commit site, so the commit primitive never receives an `expected_head`.
- Catch a CAS rejection and retry silently, which collapses two intended writes into a last-writer-wins outcome and silently breaks the non-commitment discipline at the project core (MEMORY: project_design_principle.md).
- Write sidecar rows (claim_core, source registry, embeddings, materialized views) before the kernel CAS commits, so a CAS rejection leaves orphan sidecar state pointing at a commit that never happened.

D-23 separated these concerns from WS-O-qui because they are not kernel bugs — they are call-site contract bugs. WS-Q-cas owns the audit, the typed error surface, the ordering rule (CAS first, sidecar second, never the reverse), and the concurrent-race test matrix that proves every mutation path loses cleanly.

This workstream is the propstore-side counterpart to WS-O-qui. Both must close before WS-C and WS-E can claim atomicity guarantees.

## Review findings covered

| Finding | Source | Description |
|---|---|---|
| **D-23** | DECISIONS.md (Codex addendum 1.7) | No propstore-side WS guarantees that every import/finalize/promote/materialize path captures the head it read and threads it to the subsequent commit. |
| **D-6 (interaction)** | DECISIONS.md | Promote ordering reorder must occur inside the head-bound transaction. Cannot land if the underlying CAS is missing. |
| **D-7 (interaction)** | DECISIONS.md | Micropub depends on per-claim CAS being honored at the call site, not only at the kernel. |
| **gaps.md (race-window)** | docs/gaps.md | Concurrent finalize / concurrent promote / concurrent import races are currently un-gated. |

This WS does NOT close D-6 or D-7 directly — those have their own workstreams (WS-E for D-6, the micropub WS for D-7). It closes the substrate they both stand on.

## Code to audit (READ-ONLY in this WS — production untouched until tests fail)

Each path below has the same audit shape:

1. Where is the branch head read?
2. Is the read value captured into a local variable that flows to the commit?
3. Is the commit primitive called with an explicit `expected_head` argument?
4. Are sidecar mutations sequenced after the kernel commit returns success, never before?
5. On CAS rejection, does the path raise a typed error that propagates without writing sidecar state?

### propstore/source/finalize.py
- Question 1: where in finalize is the head read? Audit must record file:line.
- Question 2: does finalize pass the captured head to `quire.commit(...)`? Or does the commit primitive re-read the head internally?
- Question 3: does finalize update sidecar status (`claim_core.build_status`, source registry rows) before or after the kernel commit?
- Expected gap: finalize likely reads the head once for validation, then calls a commit primitive that re-reads. Two concurrent finalize calls on the same source branch would both see a clean tip.

### propstore/source/promote.py
- Promote already has D-6 reorder pending. The reorder MUST happen inside the head-bound transaction, otherwise the reorder runs against a head that may have advanced between `read_head()` and `commit(expected_head=...)`.
- Audit: capture the head BEFORE the reorder logic builds the new tree object. Pass that head into the commit. If the head has moved between capture and commit, abort the reorder, do not retry.
- Expected gap: promote currently does not capture the head at all; it relies on quire's internal head read at commit time.

### propstore/storage/repository_import.py
- Repository import is the largest blast-radius mutation: it touches branch heads, sidecar registry rows, possibly embedding registry rows, possibly materialized views.
- Audit: head capture for EACH branch the import touches. A multi-branch import that captures only one head is still racy against any concurrent writer on the other branches.
- Expected gap: import probably captures nothing and treats the kernel as if it serializes for free.

### propstore/storage/snapshot.py
- Materialize/build is read-mostly but it writes derived sidecar state (`claim_core` runtime columns, materialized views) and that derived state is keyed by branch head. If materialize reads head H, builds derived state, and commits derived state into the sidecar without re-checking that head H is still current, the sidecar references a commit older than the live tip.
- Audit: head capture at start of materialize. Sidecar derived-row writes must be conditioned on head still equaling H at write time, OR the derived rows must record H explicitly so a later check can detect staleness.
- Expected gap: materialize writes derived rows tagged with "current head" at build time, not "head when materialize started." A concurrent commit that lands between materialize-start and materialize-write produces sidecar rows tagged with the wrong head.

### propstore/sidecar/build.py
- Sidecar build is the projection layer. Same hazard as materialize: it reads heads, projects rows, writes them. The projection must be tagged with the head it read FROM, not the head visible at write time.
- Audit: every sidecar row that records `branch_head` or equivalent — confirm the value comes from the captured-at-read variable, not from a re-read.

### propstore/embed.py
- Embedding registry mutations are sidecar-only on the surface, but they are referenced BY materialize and build. If embed writes against head H' while build reads against H, the sidecar contains embeddings for a tree the build never saw.
- Audit: embed commits to sidecar must be sequenced inside the same head-bound transaction as the build/materialize that triggered them. No cross-transaction embed writes.

### propstore/repository.py
- This is the transaction primitive layer. Audit it last because the call-site audits will reveal what shape the primitive needs.
- Required surface: `with repo.head_bound_transaction(branch) as txn:` returns a context that captures the head once, exposes it as `txn.expected_head`, and threads it to every kernel commit issued inside the block. On exit, sidecar writes commit only if the kernel CAS succeeded.
- Expected gap: today's primitives almost certainly do not enforce this. The audit must produce a precise diff between current shape and required shape.

### ../quire/quire/family_store.py:_check_preemptive_head
- This is the kernel function WS-O-qui will harden. WS-Q-cas reads it to confirm what arguments it needs from the call site. If WS-O-qui changes the signature, WS-Q-cas must reflect that.
- Audit only — no edits in WS-Q-cas. Edits there belong to WS-O-qui.

### ../quire/quire/git_store.py
- The CAS commit primitive itself. Audit to confirm: what does it raise on rejection? Does it raise a distinct exception class (e.g., `StaleHeadError`) or a generic one? The propstore-side typed error surface depends on this. WS-O-qui owns the answer; WS-Q-cas owns mapping it.

## First failing tests (write these first; they MUST fail before any production change)

### 1. `tests/test_branch_head_cas_matrix.py` (new — primary gate)

A parameterized test exercising all four mutation paths under simulated concurrent commits. The test is the acceptance gate for this entire WS.

Structure:

```python
@pytest.mark.parametrize("path", [
    "finalize",
    "promote",
    "repository_import",
    "materialize",
])
def test_concurrent_writer_loses_cleanly(path, repo_with_branch):
    head_at_start = repo_with_branch.read_head("source/foo")
    # Inject a concurrent commit that advances the head.
    inject_concurrent_commit(repo_with_branch, "source/foo")
    # The path under test should have captured head_at_start at its read time.
    # When it tries to commit, the kernel CAS rejects.
    with pytest.raises(StaleHeadError) as exc:
        run_path(path, repo_with_branch, "source/foo")
    # The rejection MUST be typed, MUST identify the path, MUST identify the branch.
    assert exc.value.branch == "source/foo"
    assert exc.value.expected_head == head_at_start
    # Sidecar MUST have no rows from the failed attempt.
    assert sidecar_rows_for_attempt(repo_with_branch, exc.value.attempt_id) == []
```

What this test asserts that nothing today asserts:

- The path captured the head at read time (not at commit time).
- The path threaded that head to the kernel CAS.
- The CAS rejection produced a typed error, not a generic IOError or RuntimeError.
- No orphan sidecar state survived the failed attempt.

Must fail today on every parametrize value. If any path passes today, the audit lied about that path.

### 2. `tests/test_cas_rejection_no_orphan_rows.py` (new)

A focused test for the sidecar-write-after-CAS ordering. Distinct from the matrix test because the matrix test treats sidecar absence as one assertion among many; this test interrogates sidecar state in detail.

Structure:
- Simulate CAS rejection during finalize (mock the kernel commit to raise StaleHeadError).
- Inspect `claim_core`, source registry table, embedding registry, materialized-view tables.
- Assert: zero rows for the failed attempt across every sidecar table.

Must fail today: at least one path almost certainly writes sidecar state before kernel commit and does not roll back on CAS rejection.

### 3. `tests/test_cas_no_silent_retry.py` (new)

A correctness test, not a race test. Verifies that the propstore call sites do NOT swallow CAS rejections and retry silently.

Structure:
- Mock the kernel commit to raise StaleHeadError exactly once, then succeed.
- Call each mutation path.
- Assert: the path raises StaleHeadError to the caller. It does NOT retry. Two intended writes do NOT collapse to one.

This is the non-commitment discipline gate. If a finalize call silently retries on CAS rejection, two concurrent users would each have their finalize accepted with last-writer-wins semantics, and the loser would never know their work was discarded. That violates the project's core principle (MEMORY: project_design_principle.md).

Must fail today on any path that does silent retry.

### 4. `tests/test_head_bound_transaction_primitive.py` (new)

A unit test for the new `repo.head_bound_transaction(branch)` primitive. Verifies:
- Captures head once on entry.
- Exposes `txn.expected_head` as a read-only attribute equal to the captured value.
- Every kernel commit issued inside the block receives `expected_head=txn.expected_head` automatically.
- Sidecar writes inside the block are buffered and flush only after the kernel commit succeeds.
- On CAS rejection, sidecar buffer is discarded; no rows reach the sidecar DB.

Must fail today: the primitive does not exist.

### 5. `tests/test_workstream_q_cas_done.py` (new — gating sentinel)

`xfail` until WS-Q-cas closes; flips to `pass` on the final commit. Pattern from WS-A.

## Production change sequence

Each step lands as one commit with message `WS-Q-cas step N — <slug>`.

### Step 1 — Add `head_bound_transaction` primitive to `propstore/repository.py`

Define the context manager. It captures the head from quire on entry, holds it as `txn.expected_head`, exposes `txn.commit(...)` which forwards to quire with the captured head, and buffers sidecar writes until the kernel commit returns.

This step must NOT touch the call sites yet. It only adds the primitive plus its unit test.

Acceptance: `tests/test_head_bound_transaction_primitive.py` turns green.

### Step 2 — Migrate `propstore/source/finalize.py` to use `head_bound_transaction`

Refactor finalize to open the head-bound transaction at the start of the operation, perform all kernel writes through `txn.commit(...)`, perform all sidecar writes through `txn.sidecar_write(...)`. No silent retries. CAS rejection propagates as `StaleHeadError`.

Acceptance: `test_branch_head_cas_matrix.py[finalize]` turns green; `test_cas_rejection_no_orphan_rows.py` for finalize turns green; `test_cas_no_silent_retry.py` for finalize turns green.

### Step 3 — Migrate `propstore/source/promote.py`

Same refactor. The D-6 reorder logic moves inside the head-bound transaction. If D-6 has not landed yet, this step lands first and D-6 lands inside the existing head-bound block.

Acceptance: matrix test for promote turns green; `test_cas_rejection_no_orphan_rows.py` for promote; `test_cas_no_silent_retry.py` for promote.

### Step 4 — Migrate `propstore/storage/repository_import.py`

Multi-branch case: open one head-bound transaction per branch the import touches, OR open a single multi-branch transaction primitive if quire supports it. WS-O-qui must answer this question; if quire only supports single-branch CAS, repository_import must fail loud when the import spans branches and serialize per-branch.

Acceptance: matrix test for repository_import turns green.

### Step 5 — Migrate `propstore/storage/snapshot.py` (materialize/build)

Materialize captures heads for every branch it reads, builds derived state tagged with those captured heads, commits sidecar rows through the head-bound transactions. On any CAS rejection from any branch, the entire materialize aborts and no derived rows are written.

Acceptance: matrix test for materialize turns green.

### Step 6 — Migrate `propstore/sidecar/build.py` and `propstore/embed.py`

Sidecar build is invoked by materialize; embed is invoked by build. After step 5, these may already flow through the head-bound transaction implicitly. Audit confirms; if any direct caller of build or embed exists outside materialize, that caller is migrated too.

Acceptance: no remaining `quire.commit(...)` call site in propstore exists outside a `head_bound_transaction` block. This is enforceable as an import-linter / AST gate; add the gate as part of this step.

### Step 7 — Add the AST gate

`tests/test_no_unbounded_quire_commit.py` (new): AST-walks `propstore/`, finds every call to `quire.commit` or `quire.family_store.commit` or equivalent, asserts each is lexically inside a `with repo.head_bound_transaction(...)` block.

This gate prevents regressions. New code added later cannot reintroduce the bug without breaking the test.

Acceptance: gate test green; CI runs it on every PR.

### Step 8 — Close the gap and gate the WS

- Update `docs/gaps.md`: remove the race-window entries; add `# WS-Q-cas closed <sha>` to the Closed section.
- Flip `tests/test_workstream_q_cas_done.py` from xfail to pass.
- Update STATUS line in this file to `CLOSED <sha>`.

Acceptance: sentinel test passes; gaps.md updated; STATUS line flipped.

## Acceptance gates

Before declaring WS-Q-cas done, ALL must hold:

- [x] WS-A is CLOSED. (Race tests are written against the production schema; without WS-A they would test fictional shapes.)
- [x] WS-O-qui is CLOSED. (Without transactional CAS in the kernel, propstore-side discipline cannot be enforced no matter how careful the call sites are.)
- [x] `uv run pyright propstore` passes with 0 errors.
- [x] `uv run lint-imports` passes.
- [x] `tests/test_branch_head_cas_matrix.py` passes for all four parametrize values.
- [x] `tests/test_cas_rejection_no_orphan_rows.py` passes.
- [x] `tests/test_cas_no_silent_retry.py` passes.
- [x] `tests/test_head_bound_transaction_primitive.py` passes.
- [x] `tests/test_no_unbounded_quire_commit.py` (the AST gate) passes.
- [x] Full suite — no NEW failures vs the WS-A baseline.
- [x] WS-Q property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged WS-Q test run or a named companion run.
- [x] Every mutation path enumerated in SCOPE has been migrated to `head_bound_transaction`.
- [x] `docs/gaps.md` has no open rows for the findings listed above.
- [x] STATUS line in this file is `CLOSED <sha>`.

## Done means done

This workstream is done when EVERY mutation path passes its concurrent-race test, EVERY CAS rejection produces a typed error, and NO orphan sidecar rows survive a race failure on any path. Specifically:

- Finalize, promote, repository_import, materialize all pass the matrix test.
- The four targeted tests above all pass.
- The AST gate exists and prevents future unbounded `quire.commit` calls.
- gaps.md is updated.
- The sentinel test has flipped from xfail to pass.

If any one of those is not true, WS-Q-cas stays OPEN. No partial close. Either every path is bound by the head-bound transaction primitive, or this WS is not done.

## Cross-stream notes

- WS-O-qui must close before this WS can close. The kernel must actually reject stale-head commits transactionally; otherwise this WS's discipline is ceremony.
- WS-A must close before this WS's first failing tests can be trusted. Race tests written against fictional schemas would prove nothing.
- WS-C (sidecar atomicity tests) inherits this WS's primitive. Once `head_bound_transaction` exists, WS-C's atomicity guarantees can be expressed in terms of it.
- WS-E (source promote ordering, D-6) lands its reorder INSIDE the `head_bound_transaction` block created in Step 3. If WS-E lands before this WS, the reorder is unsafe; if WS-E lands after, the reorder is naturally protected.
- The micropub WS (D-7) has the same shape: per-claim writes must flow through `head_bound_transaction`. That WS will reuse this primitive without redefining it.

## What this WS does NOT do

- Does NOT modify the kernel CAS primitive (`_check_preemptive_head` or `git_store.commit`). That is WS-O-qui.
- Does NOT add new mutation paths. It audits and migrates existing paths only.
- Does NOT change the schema. WS-A owns schema fidelity.
- Does NOT define render policy or visibility filters. WS-B owns that.
- Does NOT implement the D-6 promote reorder. WS-E owns that, using this WS's primitive.
- Does NOT implement micropub. The micropub WS owns that, using this WS's primitive.
- Does NOT change quire's API surface. If quire's API needs changes for transactional CAS, WS-O-qui changes them; this WS consumes whatever surface WS-O-qui ships.

## Discipline reminder

Statement: every commit primitive call site is a place where the non-commitment discipline can be silently violated. Two writers with valid intent can each be granted a clean head if the kernel does not enforce CAS, OR if the kernel does enforce CAS but the call site silently retries on rejection. Both failure modes look identical from the user's perspective: their work was accepted, then silently overwritten. The first failure mode is WS-O-qui's. The second is this WS's. Both must close. Neither alone is sufficient.

The project core (MEMORY: project_design_principle.md) requires that disagreement never collapse in storage unless the user explicitly requests migration. A silent CAS retry is a disagreement collapse. This WS exists to make that collapse impossible at every propstore mutation path.
