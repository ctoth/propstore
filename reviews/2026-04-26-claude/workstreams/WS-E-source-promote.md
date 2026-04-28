# WS-E: Source-promote and finalize correctness

**Status**: CLOSED 152818da
**Depends on**: WS-A (schema fidelity), WS-C Step 2 reorder per D-6 (promote-ordering reorder — WS-E only consumes the reorder, not the full WS-C scope), WS-CM (micropub identity for finalize/promote surfaces), WS-Q-cas (branch-head CAS discipline)
**Blocks**: WS-K (heuristic discipline), WS-L (merge non-commitment), WS-M (provenance)
**Owner**: Codex implementation owner + human reviewer required

---

## Why this workstream exists

Source-promote is the gate where defeasible source-branch claims become master-branch knowledge. Every bug in this gate either silently loses disagreement (alias merges, micropub drops, alignment defaulting to non-attack) or silently corrupts master with dangling cross-batch references. Cluster A's HIGH findings concentrate here for a reason: this is the file where the "preserve disagreement" and "imports are opinions" principles either hold or fall.

WS-C owns the *primitive* that makes git-and-sidecar writes atomic. WS-Q-cas owns the *branch-head CAS discipline* that ensures promote reads against a captured master head and threads it to quire commit. WS-E consumes both at the source-promote/finalize call sites and additionally fixes the source-promote-specific correctness bugs that those workstreams do not address (justification filter, alignment default, alias collisions, micropub-without-context, in-place mutation, time handling, validation gaps).

WS-A is a hard prerequisite because every WS-E test asserts something about claim_core / source_finalize_report / micropub rows that the test fixture must produce in production-faithful shape. Until WS-A lands, any green WS-E test would be measuring against fictional schema.

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed is gone from `gaps.md` and has a green test gating it.

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T1.6 (WS-E half)** | Claude REMEDIATION-PLAN Tier 1 | `propstore/source/promote.py:840-851` + `:518-548` | SQLite-before-git ordering at source-promote call site. WS-C provides the atomicity primitive; WS-E reorders/wraps the source-promote-specific call so failed promotes cannot poison subsequent successful ones. |
| **T3.5 (revised per Codex 1.14)** | Claude REMEDIATION-PLAN Tier 3 | `propstore/source/promote.py:711-727` | Justification filter admits a justification whose conclusion or premise is in the source-branch claim index but resolves to neither this batch's `valid_artifact_ids` NOR the master-branch artifact snapshot the promote is running against. Q's open-question A.1 answer ("conservative") is refined by Codex 1.14: the conservative rule is "every reference resolves either in the current promotion batch OR in the canonical repository snapshot being promoted against," NOT "every reference must be in this batch alone." Blanket batch-only rejection would drop legitimate cross-batch claims that justify against already-accepted master content. |
| **T3.6** | Claude REMEDIATION-PLAN Tier 3 | `propstore/source/alignment.py:96-98` | `classify_relation` defaults to `"non_attack"` for the typical case. The conditional at line 96 is dead (the `return` at line 98 executes whether or not 96 fired). Alignment AF therefore credulously accepts every alternative; the AF's purpose is defeated. |
| **T3.7** | Claude REMEDIATION-PLAN Tier 3 | `propstore/source/registry.py:42-47` | `handle_to_artifact.setdefault(alias_name, artifact_id)` silently merges two distinct concepts that share an alias name. Direct violation of "preserve disagreement". |
| **T3.8** | Claude REMEDIATION-PLAN Tier 3 | `propstore/source/finalize.py:213-217` (driver) + `:59-60` (skip site) | Micropubs are silently skipped for context-less claims. Promotion of those claims still proceeds; the claims land on master invisible to micropub-driven render. |
| **Cluster A HIGH-1** | `cluster-A-core-storage-source.md` | `propstore/source/promote.py:711-727` | Same as T3.5 — full bug description in Cluster A. |
| **Cluster A HIGH-3** | `cluster-A-core-storage-source.md` | `propstore/source/alignment.py:96-98` | Same as T3.6. |
| **Cluster A HIGH-4** | `cluster-A-core-storage-source.md` | `propstore/source/registry.py:42-47` | Same as T3.7. |
| **Cluster A HIGH-5** | `cluster-A-core-storage-source.md` | `propstore/source/finalize.py:213-217` | Same as T3.8. |
| **Cluster A MED M1** | `cluster-A-core-storage-source.md` | `propstore/source/promote.py:692` | `resolver.target_is_known(stance.target)` is called with `stance.target` directly; no guard that target is a non-empty string. |
| **Cluster A MED M2** | `cluster-A-core-storage-source.md` | `propstore/source/promote.py:887-889`, `propstore/source/finalize.py:244` | `transaction.commit_sha` read AFTER `with` block exit. |
| **Cluster A MED M4** | `cluster-A-core-storage-source.md` | `propstore/source/passes.py:213` | `payload.setdefault("status", "accepted")` collapses the proposal stage. |
| **Cluster A MED M5** | `cluster-A-core-storage-source.md` | `propstore/source/passes.py:255-258` | Local-handle collision warning never re-checked at commit time. |
| **Cluster A MED M7** | `cluster-A-core-storage-source.md` | `propstore/source/promote.py:744-758` | `claim.clear()` + `claim.update(...)` in-place mutation. |
| **Adjacent: datetime.utcnow** | `cluster-A-core-storage-source.md` MED | `propstore/source/claims.py:237`, `relations.py:78`, `relations.py:137` | Deprecated naive UTC. |
| **Adjacent: rule_kind validation** | `cluster-A-core-storage-source.md` Missing | `propstore/source/relations.py` (commit_source_justification_proposal) | Free-form rule_kind / rule_strength accepted; later silently dropped at synthesis. |
| **Cluster A HIGH-2 (split)** | `cluster-A-core-storage-source.md` | `propstore/source/promote.py:840-851` + `:518-548` | The PK-collision part of HIGH-2 is the source-promote-specific application of T1.6. WS-C primitive + WS-E call-site reordering jointly close it. |

Open question A.1 (partial-promote justification semantics) — **resolved as refined by Codex 1.14**: a justification is admitted iff every reference (conclusion + premises) resolves into the *enlarged* set `current_batch_ids ∪ master_branch_artifact_ids`. Anything that resolves only to the source-branch claim index but is not in this batch and not on master is dropped (and surfaced as deferred in the finalize report). This preserves the disagreement-preservation intent of "conservative" while not silently rejecting legitimate cross-batch claims that justify against master content.

## Code references (verified by direct read)

### Justification filter (T3.5 / Cluster A HIGH-1 / Codex 1.14)

`propstore/source/promote.py:711-727`:

```python
if justifications_doc is None:
    filtered_justifications_payload = None
else:
    valid_justification_entries: list[dict[str, Any]] = []
    for justification in justifications_doc.justifications:
        conclusion = justification.conclusion
        if not isinstance(conclusion, str):
            continue
        if conclusion not in valid_artifact_ids and not source_claim_index.has_artifact(conclusion):
            continue
        if any(
            not isinstance(premise, str)
            or (premise not in valid_artifact_ids and not source_claim_index.has_artifact(premise))
            for premise in justification.premises
        ):
            continue
        valid_justification_entries.append(justification.to_payload())
```

The current `not source_claim_index.has_artifact(...)` clause is too permissive: it admits dangling refs to other source-branch artifacts NOT being promoted in this batch. But a strict batch-only rule would be too restrictive: a new source claim may legitimately premise on a master claim already accepted in a prior promote.

Per Codex 1.14: replace with strict membership in the *enlarged* set `current_batch_ids ∪ master_branch_artifact_ids`. The stance loop at `:686-693` must be widened identically (today it requires `source_claim in valid_artifact_ids` outright, which has the same too-restrictive defect once `valid_artifact_ids` is read as batch-only).

### Alignment default (T3.6 / Cluster A HIGH-3)

`propstore/source/alignment.py:90-98`:

```python
left_entry = _proposal_lexical_entry(left)
right_entry = _proposal_lexical_entry(right)
if lexical_entry_identity_key(left_entry) == lexical_entry_identity_key(right_entry):
    return "attack" if left["definition"] != right["definition"] else "non_attack"
if lexical_form_identity_key(left_entry) == lexical_form_identity_key(right_entry):
    return "attack" if left["definition"] != right["definition"] else "non_attack"
if left_entry.references == right_entry.references:
    return "non_attack"
return "non_attack"
```

The `if` at line 96 is dead — both branches return the same value. The default at line 98 is `non_attack`. Two papers proposing two different concept names with conflicting definitions never produce an attack.

### Alias collisions (T3.7 / Cluster A HIGH-4)

`propstore/source/registry.py:42-47`:

```python
for alias in concept.get("aliases") or []:
    if not isinstance(alias, dict):
        continue
    alias_name = alias.get("name")
    if isinstance(alias_name, str) and alias_name:
        handle_to_artifact.setdefault(alias_name, artifact_id)
```

`setdefault` keeps the first writer; second concept's entries are silently rewritten via `concept_map`. No error, no warning.

### Context-less micropub drop (T3.8 / Cluster A HIGH-5)

`propstore/source/finalize.py:53-60`, `:160-165`, `:213-217`: a context-less claim is silently skipped at micropub composition; the claim itself still persists. Per `data-model.md` every claim must have a context — context-less should be a finalize error, not a silent drop.

### MED items in promote.py

- **M1** (`promote.py:692`): no guard before `resolver.target_is_known`.
- **M2** (`promote.py:887-889`, `finalize.py:244`): commit_sha read after `with` exit.
- **M4** (`passes.py:213`): default `status="accepted"`.
- **M5** (`passes.py:255-258`): warnings stored, never re-checked at commit.
- **M7** (`promote.py:744-758`): in-place dict mutation.

### Adjacent: datetime + validation

- `claims.py:237`, `relations.py:78`, `relations.py:137`: `datetime.utcnow()`.
- `relations.py:commit_source_justification_proposal`: no rule_kind / rule_strength validation.

### Cross-stream coordination

- **WS-C** owns T1.6's atomicity primitive consumed at `promote.py:840-851`.
- **WS-Q-cas (D-23)** owns the branch-head CAS discipline. WS-E's promote path captures the master head it reads against (the snapshot used to compute `master_branch_artifact_ids`) and threads that captured head to the quire commit so a concurrent master mutation between read and commit aborts the promote rather than letting it land against a moved target.
- **Codex review** (`reviews/2026-04-26-codex/README.md`): finding 1.14 is the source of the enlarged-set rule above. Codex #6/#7 (schema parity) is upstream of WS-E via WS-A; not duplicated here.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_source_promote_dangling_refs.py`** (new — gating test for T3.5 / Codex 1.14)
   This test exercises BOTH legitimate and illegitimate cross-batch justification cases.

   Case A (INVALID — must be rejected):
   - Set up a source branch with two batches. Batch 1 commits source-local claim `C1` but does NOT promote it; `C1` exists only in `source_claim_index`. Batch 2 includes a justification referencing `C1` as conclusion or premise.
   - Promote batch 2 against a master that does not contain `C1`.
   - Assert: justification is NOT in the promoted output; `source_finalize_report` flags it as deferred / not promoted because `C1` resolves to neither `current_batch_ids` nor `master_branch_artifact_ids`.

   Case B (VALID — must be accepted):
   - Set up master with claim `M1` already accepted from a prior promote.
   - Source branch batch references `M1` as a premise of a new justification whose conclusion is a new claim in the current batch.
   - Promote against current master.
   - Assert: justification IS in the promoted output (legitimate cross-batch dependency on canonical master content).

   Case C (INVALID — must be rejected):
   - Justification's premise is in the source-branch claim index but is neither in the current batch NOR on master.
   - Assert: dropped; surfaced as deferred.

   **Must fail today**: lines 719/721-725 admit Case C (via `source_claim_index.has_artifact`); a naive batch-only rewrite would also wrongly reject Case B. The current single-test predecessor that asserted blanket rejection is wrong and is rewritten into this matrix.

2. **`tests/test_alignment_default_classification.py`** (new — gating test for T3.6)
   - Two `proposal` dicts: different lexical-entry identity, different lexical-form identity, different references, conflicting definitions.
   - Assert `classify_relation(left, right) == "attack"`.
   - **Must fail today**: returns `"non_attack"` per line 98.

3. **`tests/test_alignment_dead_branch.py`** (new — defense in depth)
   - Two proposals where `left_entry.references == right_entry.references` and definitions differ.
   - Assert `classify_relation == "attack"`.
   - **Must fail today**: line 96 returns `"non_attack"` regardless of definition equality.

4. **`tests/test_alias_collision_rejected.py`** (new — gating test for T3.7)
   - Register two distinct concepts each declaring alias `"velocity"`.
   - Assert `_load_primary_branch_concept_index` raises `ConceptAliasCollisionError` listing both concepts.
   - **Must fail today**: silent merge via `setdefault`.

5. **`tests/test_finalize_micropub_required.py`** (new — gating test for T3.8)
   - Run `finalize_source_branch` on a branch with one claim missing `context`.
   - Assert: finalize report status is `blocked`, micropub-coverage section names the offending claim, no claim/justification/stance documents are saved on this run.
   - **Must fail today**: claims save proceeds; only the micropub document is silently skipped.

6. **`tests/test_promote_atomicity_source_call_site.py`** (new — gating test for T1.6 WS-E half)
   - Inject a fault into the git transaction during `promote_source_branch`.
   - Assert: no orphan `claim_core` rows; clean retry succeeds without PK collision.
   - **Must fail today**: sidecar mirror writes happen before git transaction.
   - **Note**: depends on WS-C; until WS-C lands this is `xfail(strict=True, reason="depends on WS-C")`.

7. **`tests/test_promote_branch_head_cas.py`** (new — gating test for the WS-Q-cas cross-link)
   - Run `promote_source_branch` against captured master head `H0`. Mid-promote (between snapshot read and quire commit), mutate master to head `H1`.
   - Assert: promote aborts with a typed `BranchHeadMovedError`; no sidecar mutation; report names `H0` (expected) and `H1` (observed).
   - **Must fail today**: promote captures no head and threads no head to quire; race silently lands against `H1`.
   - **Note**: depends on WS-Q-cas providing the captured-head plumbing; until WS-Q-cas lands this is `xfail(strict=True, reason="depends on WS-Q-cas")`.

8. **`tests/test_promote_stance_target_guarded.py`** (new — M1)
   - Run promote with stance whose `target` is `None` or empty.
   - Assert: rejected at validation with clear error.

9. **`tests/test_transaction_commit_sha_lifetime.py`** (new — M2)
   - Patch `transact()` to clear `commit_sha` on `__exit__`.
   - Assert: `promote_source_branch` and `finalize_source_branch` raise rather than returning `None` silently.

10. **`tests/test_concept_import_status_proposed.py`** (new — M4)
    - Import concepts batch with no `status` field.
    - Assert: imported concept has `status == "proposed"`.

11. **`tests/test_local_handle_collision_blocks_commit.py`** (new — M5)
    - Import payload with two claims sharing a `local_id`.
    - Assert: `commit_repository_import` raises (or finalize report blocks).

12. **`tests/test_promote_claim_immutability.py`** (new — M7)
    - After `promote_source_branch`, assert input `promoted_claims_doc` (deepcopy snapshot) is not mutated.

13. **`tests/test_extraction_provenance_aware_timestamps.py`** (new — datetime adjacent)
    - Patch `datetime.now(timezone.utc)` and `datetime.utcnow` to distinct values; assert persisted timestamp is the timezone-aware value.

14. **`tests/test_justification_rule_kind_validated.py`** (new — rule_kind adjacent)
    - Submit justification proposal with `rule_kind="bogus"`.
    - Assert: rejected at commit with clear error.

15. **`tests/test_workstream_e_done.py`** (new — gating sentinel) — fails while WS-E stays open, passes after closeout artifacts agree.

## Production change sequence

Each step lands in its own commit with message `WS-E step N — <slug>`.

### Step 1 — Justification filter with enlarged valid set (T3.5 / Codex 1.14)

`propstore/source/promote.py:711-727`: replace the existing logic with strict membership in the enlarged set:

```
valid_artifact_ids = current_batch_ids ∪ master_branch_artifact_ids
```

Both the stance loop (`:686-693`) and the justification loop (conclusion + every premise) test against this enlarged set. Drop the `source_claim_index.has_artifact(...)` admission. `master_branch_artifact_ids` is supplied by the captured master snapshot read at promote entry (the same snapshot WS-Q-cas requires for branch-head CAS — Step 5b threads the head; this step consumes the snapshot).

Deferred justifications (those whose conclusion or any premise resolves to neither set) stay on the source branch and are surfaced in the finalize report.

Acceptance: test 1 (all three cases) turns green.

### Step 2 — Alignment default (T3.6)

`propstore/source/alignment.py:90-98`: rewrite. Decide attack/non-attack on `definition` equality at every lexical-key tier; default to `attack` (forces curator review per "preserve disagreement"). Delete the dead `references == references` branch or merge with the lexical-form branch.

Acceptance: tests 2, 3 turn green.

### Step 3 — Alias collisions (T3.7)

`propstore/source/registry.py:42-47`: replace `setdefault` with explicit collision detection raising typed `ConceptAliasCollisionError`. Update callers to surface as finalize-report block.

Acceptance: test 4 turns green.

### Step 4 — Context-less claim is a finalize error (T3.8)

`propstore/source/finalize.py`: in claim_errors accumulation (lines 120-123), add check that every claim has non-empty `context`. Surface in finalize report under new `micropub_coverage_errors`. The no-error gate at line 171 includes this field. Delete the `continue` at `_compose_source_micropubs:59-60` and assert context-presence in the composer.

Acceptance: test 5 turns green.

### Step 5 — Atomicity at source-promote call site (T1.6 WS-E half)

Depends on WS-C. Replace sidecar-before-git ordering at `promote.py:840-851` with WS-C primitive. Verify `:518-548` blocked-write path is included in rollback semantics. Do NOT introduce a `(artifact_id, branch)` PK alternative — WS-C is the chosen path.

Acceptance: test 6 turns green (no longer xfailed).

### Step 5b — Branch-head CAS at promote entry (WS-Q-cas cross-link, D-23)

Depends on WS-Q-cas. At promote entry, capture the master head as `expected_head` and read the master artifact snapshot used by Step 1 against that head. Thread `expected_head` to the quire commit per WS-Q-cas's CAS API. If the head moved between read and commit, abort with `BranchHeadMovedError`; no sidecar mutation occurs (Step 5 ordering ensures this).

Acceptance: test 7 turns green (no longer xfailed).

### Step 6 — MED cleanup (M1, M2, M4, M5, M7)

Each in its own commit:
- **M1**: at `promote.py:692`, guard `stance.target` is non-empty string before `target_is_known`.
- **M2**: capture `transaction.commit_sha` INSIDE the `with` block at `promote.py:887`, `finalize.py:244`, and `repository_import.py:147-149`.
- **M4**: `passes.py:213` change default `"accepted"` → `"proposed"`.
- **M5**: in `commit_repository_import`, raise on any local-handle-collision warning (typed warning class for structural detection).
- **M7**: at `promote.py:744-758`, rebuild claims list instead of in-place clear/update.

Acceptance: tests 8, 9, 10, 11, 12 turn green.

### Step 7 — datetime + rule_kind validation

- `claims.py:237`, `relations.py:78`, `relations.py:137`: replace `datetime.utcnow().strftime(...)` with `datetime.now(timezone.utc).strftime(...)`.
- `relations.py` (commit_source_justification_proposal): validate `rule_kind ∈ {"reported_claim", "supports", "explains"}` and `rule_strength ∈ {"strict", "defeasible"}` at commit. Use enums.

Acceptance: tests 13, 14 turn green.

### Step 8 — Close gaps and gate

- Update `docs/gaps.md`: remove T3.5, T3.6, T3.7, T3.8, T1.6 (WS-E half), MEDs.
- Flip `tests/test_workstream_e_done.py` xfail → pass.
- Update STATUS to `CLOSED <sha>`.

## Acceptance gates

- [x] WS-A is CLOSED.
- [x] WS-C is CLOSED (Step 5 prerequisite).
- [x] WS-CM is CLOSED (micropub identity prerequisite).
- [x] WS-Q-cas is CLOSED (Step 5b prerequisite).
- [x] `uv run pyright propstore` passes 0 errors.
- [x] `uv run lint-imports` passes.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-E-targeted-preclose tests/test_source_promote_dangling_refs.py tests/test_alignment_default_classification.py tests/test_alias_collision_rejected.py tests/test_finalize_micropub_required.py tests/test_transaction_commit_sha_lifetime.py tests/test_concept_import_status_proposed.py tests/test_local_handle_collision_blocks_commit.py tests/test_promote_claim_immutability.py tests/test_extraction_provenance_aware_timestamps.py tests/test_justification_rule_kind_validated.py tests/test_promote_atomicity.py tests/test_branch_head_cas_matrix.py tests/test_cas_rejection_no_orphan_rows.py` all green.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-E-properties tests/test_source_promote_properties.py` all green.
- [x] Full suite — `powershell -File scripts/run_logged_pytest.ps1 -Label WS-E-full-final-rerun` passed `3076 passed`.
- [x] WS-E property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged WS-E test run or a named companion run, except sameAs provenance which is explicitly moved to WS-L because WS-L owns the sameAs representation.
- [x] `docs/gaps.md` clean for all listed findings.
- [x] STATUS line `CLOSED 152818da`.

## Done means done

WS-E is done when **every finding in the table is closed**. Specifically:

- T3.5 (with the Codex 1.14 enlarged-set rule), T3.6, T3.7, T3.8, T1.6 (source-half), Cluster A HIGH-1/3/4/5, MEDs M1/M2/M4/M5/M7, datetime + rule_kind — all green-tested.
- Open question A.1 is answered in code per Codex 1.14: justification filter requires every reference to resolve in `current_batch_ids ∪ master_branch_artifact_ids`.
- Branch-head CAS is wired through promote per WS-Q-cas.
- `gaps.md` updated; gating sentinel passes.

If any one is not true, WS-E stays OPEN. No "we'll do the timestamp fix later." Either it's in scope and closed, or moved to a successor WS in this file before declaring done.

## Papers / specs referenced

- `data-model.md` for rule_kind / rule_strength enum surfaces and the "every claim has a context" requirement.
- "preserve disagreement" / "imports are opinions" in project memory — justify the alignment-default flip and alias-collision raise.
- No external papers gate this WS.

## Cross-stream notes

- **Upstream**: WS-A (schema parity), WS-C (atomicity primitive — Step 5), WS-Q-cas (CAS discipline — Step 5b).
- **Downstream**: WS-K (consumes `proposed`-by-default lifecycle from Step 6), WS-L (consumes consistent source-promote provenance), WS-M (consumes timezone-aware timestamps from Step 7).
- **Parallel**: WS-B, WS-D.

## What this WS does NOT do

- Does NOT introduce the atomicity primitive (WS-C deliverable).
- Does NOT introduce the branch-head CAS primitive (WS-Q-cas deliverable). WS-E only consumes both.
- Does NOT touch broader micropub-blocked-claim logic in `promote.py:_filter_promoted_micropubs:172-176` — refactor lands in WS-L.
- Does NOT fix in-place mutation in heuristic modules (only the source-promote site at `promote.py:744-758`). Heuristic-side cleanup is WS-K.
- Does NOT touch `propstore/uri.py:19-22` authority validation — folded into WS-A per D-24.
- Does NOT fix `concept_ids.py` privileged-namespace behavior — WS-A per D-24 or WS-K.
- Does NOT add justification target_justification_id integrity for undercutters (`relations.py:196-242`) — WS-F.
