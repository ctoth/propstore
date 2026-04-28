# WS-J: Worldline determinism, hashing, overlay-world rename

**Status**: CLOSED 9eefe5ce
**Depends on**: WS-A (schema fidelity — required before any test below can be trusted), WS-D (math naming / sensitivity / argumentation surface — overlaps Step 3 multi-extension surface), and **WS-I** (ATMS unbounded-stable interface). Worldline runs consume ATMS-derived state in `revision_capture`, `materialize`, and the sensitivity loop; until WS-I lands its replacement interface, multi-extension and revision tests below are exercising surfaces whose stability semantics have not been corrected. Land WS-A, then WS-D, then WS-I, then WS-J.
**Blocks**: WS-J2 (InterventionWorld / Pearl do() / Halpern HP-modified). WS-J2 is gated on the `OverlayWorld` rename landing here so it has a clean class to subclass / sit beside.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1).

---

## Why this workstream exists

The worldline layer's job is to materialize a deterministic, content-addressable result for a `WorldlineDefinition` against a `WorldModel`, so that callers can answer "is this stale?" by comparing 16 hex characters. The runner does this. The runner also has six independent ways to produce a different hash for the same inputs without anything actually changing. Each one is small. Together they invalidate the single contract `is_stale` is documented to provide (`docs/worldlines.md:46-48`).

`HypotheticalWorld` is the project's overlay surface for "what if this claim were also asserted." It is named, structured, and used as if it implements Pearl-style intervention (`do(X = x)`). It does not. It is a graph overlay: it adds a competing claim and lets conflict resolution adjudicate. For overdetermined / preempted causal scenarios — the case papers like Halpern 2005 (forest-fire, Suzy-Billy) exist to formalize — the overlay produces wrong answers compared to a Pearl/HP intervention. **D-11 resolved this**: the class is renamed to `OverlayWorld` here in WS-J, and a separate `InterventionWorld` implementing Pearl 2000 / Halpern 2015 HP-modified actual cause lands in WS-J2. WS-J does not implement Pearl semantics. It locks in the honest name and ships the determinism fixes.

This workstream closes the determinism findings without ambiguity, executes the rename via rope, and leaves the Pearl `do()` operator, Halpern AC1/AC2/AC3, Spohn kappa, and Bonanno merge to dedicated follow-up workstreams (WS-J2 covers the first two; the others remain unowned).

## Resolved decisions

- **D-11** — `HypotheticalWorld` rename + Pearl do(). Decision: **both**. WS-J takes Path A (rename to `OverlayWorld`, document overlay semantics, no Pearl implementation). WS-J2 (separate file) takes Path B (`InterventionWorld` with parameterization-edge severing per Pearl 2000 §3.2.1 and Halpern 2015 HP-modified, AC1/AC2/AC3 actual-cause definition). The previously open question at the bottom of this file is closed; see "Cross-stream notes" for the WS-J2 hand-off.
- **Codex 2.8** — WS-J / WS-I ordering. Decision: **WS-J depends on WS-I**. Worldline materialization, revision_capture, and the sensitivity loop all consume ATMS-derived stable-extension state. Running WS-J's determinism tests on top of the un-corrected bounded-stable surface would gate determinism guarantees against an interface that WS-I is about to replace. Header above reflects this; WS-I lands first.
- **Codex 2.10** — Hash test premises. Decision: rewrite both. The transient-error test compares **two equivalent failures with different exception reprs** and asserts equal hashes (failure-vs-success was the wrong frame — those produce different materialized outputs and should hash differently). The repr-stability test asserts **typed failure on unknown objects** rather than stable hashing of unknown types — the strict encoder from Step 1 raises on anything non-JSON-native, and that is the honest contract.
- **Codex 2.11** — Budget API. Decision: **`max_candidates` is a required keyword argument on owner-layer APIs**. No default, no configured constant, no fallback. Every public caller passes an explicit value at the call site. No hidden compat path.
- **Codex 2.12** — Real replay storage contract. Decision: define what the journal stores **before** implementing replay. New Step 4a (journal contract) precedes Step 4b (replay execution). Without a typed operator name, recorded operator input, version/policy snapshot, and normalized state, "replay" has nothing to dispatch and is just chain-integrity rewrapped.

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed is gone from `docs/gaps.md` and has a green test gating it.

| Finding | Source | Citation | Description |
|---|---|---|---|
| **J-H1** | Cluster J | `propstore/worldline/runner.py:117-121, :127-133, :203-207` | Transient subsystem errors mutate the content hash; the exception repr (often containing memory addresses) is interpolated into `error=f"...failed: {exc}"` and fed into `compute_worldline_content_hash`. |
| **J-H2** | Cluster J | `propstore/worldline/hashing.py:44`, `propstore/support_revision/history.py:47`, `propstore/worldline/argumentation.py:289`, `propstore/support_revision/projection.py:174` | `json.dumps(..., default=str)` is the canonical-hash basis in four locations. Any non-JSON object silently coerces to `str(value)`, which can embed a memory address. |
| **J-H3** | Cluster J | `propstore/worldline/argumentation.py:107-111` | Argumentation backend honors only `len(extensions) == 1`; multi-extension semantics (preferred, stable, multi-status) silently produce `argumentation_state = None`. |
| **J-H4** | Cluster J | `propstore/support_revision/history.py:239-256` | `check_replay_determinism` only verifies hash-chain integrity. It does not re-execute operators on `state_in` to confirm `state_out` reproduces. The method name overstates the guarantee. |
| **J-H5** | Cluster J | `propstore/support_revision/operators.py:91-99` and `:255-296` | `_choose_incision_set` accepts a `max_candidates` ceiling and reports `EnumerationExceeded` when crossed. The public `contract()` callers never pass it, so the public surface enumerates `2^|candidates|` unguarded. |
| **J-H6** | Cluster J | `propstore/support_revision/iterated.py:108-112` | `_entrenchment_from_state` rebuilds an `EntrenchmentReport` from the prior state's `ranked_atom_ids` and `entrenchment_reasons`. It does not call `compute_entrenchment` on the revised base. Iterated revisions diverge from one-shot revisions on the same input. |
| **J-R1 (rename)** | Cluster J + D-11 | `propstore/world/hypothetical.py:438-593` and every importer | `HypotheticalWorld` falsely implies Pearl-style intervention. Rename to `OverlayWorld` via rope. Update every importer in one pass. No alias. Docstring states overlay semantics explicitly. |
| **J-M1** | Cluster J | `propstore/worldline/hashing.py:46`, `propstore/support_revision/projection.py:176` | SHA-256 truncated to 16 hex chars (worldline) / 32 hex chars (projection). 16 hex = 64-bit; collision risk at ~2^32. |
| **J-M2** | Cluster J | `propstore/support_revision/snapshot_types.py:319-329` | `EpistemicStateSnapshot.from_state` is a shallow reference copy. Stable today only because referenced dataclasses are frozen. Any future mutable field silently breaks historical immutability. |
| **J-M3** | Cluster J | `propstore/worldline/revision_capture.py:91-95` | `_query_target_atom_ids` accepts `target` strings beginning with `ps:assertion:` or `assumption:` and raises on anything else. The `WorldlineRevisionQuery` schema does not constrain `target` shape, so user-supplied concept-name targets crash at capture. |
| **J-M4** | Cluster J | `propstore/worldline/trace.py:47` | Override sentinel is the bare string prefix `"__override_"`. Not a constant, not enforced. Renaming/reformatting the synthetic claim ID anywhere in the codebase silently leaks override claims into `dependency_claims`. |
| **J-M5** | Cluster J | `propstore/context_lifting.py:208` vs `propstore/core/activation.py:70-73` | `LiftingMaterializationStatus.BLOCKED` is computed and recorded with a `clashing_set`, but the consumer at activation.py only checks `status is LIFTED`. Blocked exceptions exist as data and contribute nothing observable. |

Adjacent finding included in scope (cheaper here than later):

| Finding | Citation | Why included |
|---|---|---|
| `_revision_state_snapshot` returns the live state object when `to_dict` is callable | `propstore/worldline/revision_capture.py:72-79` | One-line fix, same review surface as J-M2 (snapshot immutability discipline). |

## Code references (verified by direct read)

### J-H1 — exception reprs in content hash
- `propstore/worldline/runner.py:108-121` — argumentation `except Exception as exc` writes `WorldlineArgumentationState(status="error", error=f"argumentation capture failed: {exc}")`.
- `propstore/worldline/runner.py:127-133` — same pattern for revision capture (`error=f"revision capture failed: {exc}"`).
- `propstore/worldline/runner.py:203-207` — same pattern per-target for sensitivity (`error=f"sensitivity analysis failed: {exc}"`).
- `propstore/worldline/runner.py:143-151` — `compute_worldline_content_hash(... argumentation=argumentation_state, revision=revision_state, ...)`. Error payloads with stringified exceptions go into the SHA-256.

### J-H2 — `default=str` everywhere
- `propstore/worldline/hashing.py:40-46` — `json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)` then `hashlib.sha256(...).hexdigest()[:16]`.
- `propstore/support_revision/history.py:40-47` — `_canonical_json` uses `default=str`.
- `propstore/worldline/argumentation.py:284-289` — `_stance_dependency_key` uses `default=str`.
- `propstore/support_revision/projection.py:168-176` — `_digest` uses `default=str`, truncates to 32 hex.

### J-H3 — single-extension only
- `propstore/worldline/argumentation.py:107-128` — `if len(analyzer_result.extensions) == 1:` is the only path that sets `justified_claims`; otherwise it stays `None` and the function returns `None` at line 127-128. Anything with multiple extensions yields no argumentation state.

### J-H4 — fake `check_replay_determinism`
- `propstore/support_revision/history.py:239-256` — `check_replay_determinism` only verifies `entry.to_dict()["state_in_hash"] == entry.state_in.content_hash`, the analogous state_out comparison, and chain contiguity. No call into `revise()` / `contract()` to actually replay.

### J-H5 — public contract enumerates 2^|candidates|
- `propstore/support_revision/operators.py:86-99` — public `contract(base, targets, *, entrenchment)` calls `_choose_incision_set(base, target_ids, entrenchment)` with no `max_candidates` kwarg.
- `propstore/support_revision/operators.py:257-296` — `_choose_incision_set(... *, max_candidates: int | None = None)`. Only short-circuits with `EnumerationExceeded` when `max_candidates is not None and examined >= max_candidates`. The docstring cites Zilberstein 1996 anytime-bounded search; the bound is implemented but not wired into the public surface.

### J-H6 — iterated entrenchment is stale
- `propstore/support_revision/iterated.py:70` — `current_entrenchment = _entrenchment_from_state(state)` (built from PRIOR state) is what feeds `revise(state.base, normalized, entrenchment=current_entrenchment, ...)` at line 78-83.
- `propstore/support_revision/iterated.py:108-112` — `_entrenchment_from_state` rebuilds an `EntrenchmentReport` from `state.ranked_atom_ids` and `state.entrenchment_reasons`; never calls `compute_entrenchment(state.base)` against the revised base.

### J-R1 — HypotheticalWorld is an overlay, not a Pearl intervention
- `propstore/world/hypothetical.py:481-490` — builds a `GraphDelta(add_claims, remove_claim_ids)` and applies it. There is no severing of parameterizations feeding the overridden concept.
- `propstore/world/hypothetical.py:552-560` — `_recomputed_conflicts` runs; the override claim competes with the existing claim under conflict-resolution policy.
- `propstore/world/hypothetical.py:587-593` — overlay `BoundWorld` evaluates parameterizations from parents whose edges were never cut.
- The class name `HypotheticalWorld` reads as Pearl/Halpern intervention to anyone with that vocabulary. The implementation is overlay + conflict resolution. The fix here is **renaming to match what the code actually does**. The Pearl `do()` operator that severs parameterization edges is implemented in WS-J2 as a sibling class `InterventionWorld`, not by mutating this class.

### J-M1 — 16-hex truncation
- `propstore/worldline/hashing.py:46` — `hexdigest()[:16]` (64 bits).
- `propstore/support_revision/projection.py:176` — `hexdigest()[:32]` (128 bits, fine).
- `propstore/support_revision/history.py:51` — `hexdigest()` (full 256 bits, fine). **Correction to brief**: history snapshots use the full hash; only worldline content hash is 16-hex.

### J-M2 — shallow snapshot
- `propstore/support_revision/snapshot_types.py:319-329` — `EpistemicStateSnapshot.from_state` reference-copies `scope`, `base`, `accepted_atom_ids`, `ranked_atom_ids`, `ranking`, `entrenchment_reasons` straight from the input state. Frozen-dataclass invariants are the only thing preserving snapshot immutability today.

### J-M3 — contract target validation
- `propstore/worldline/revision_capture.py:88-95` — `_query_target_atom_ids` accepts only strings starting with `ps:assertion:` or `assumption:`; raises a bare `ValueError` otherwise. The `WorldlineRevisionQuery.target` schema does not constrain to those prefixes, so user-supplied concept names crash at capture.

### J-M4 — `__override_` string sentinel
- `propstore/worldline/trace.py:46-48` — `if claim_id and not claim_id.startswith("__override_")`. No constant, no enforcement.

### J-M5 — BLOCKED records computed but never observed
- `propstore/context_lifting.py:202-213` — emits `LiftedAssertion(... status=BLOCKED, exception_id=..., clashing_set=...)`.
- `propstore/core/activation.py:62-74` — `return any(... and materialization.status is LiftingMaterializationStatus.LIFTED for materialization in materializations)`. No reference to BLOCKED, no recording of `clashing_set` in `WorldlineDependencies`. Bozzato 2018 CKR semantics treat the clashing assumption set as a justification — the data model carries it, the use site discards it.

## First failing tests (write these first; they MUST fail before any production change)

1. **`tests/test_worldline_hash_excludes_transient_errors.py`** (new — rewritten per Codex 2.10)
   - Build a worldline whose argumentation backend raises a `RuntimeError` on materialization. Run it twice, with two **different** exception instances whose `__repr__` differs (e.g., one carries `id(self)` in its message via a custom `__repr__`, the other a different memory address; or simply two `RuntimeError("argumentation backend died")` instances inspected via `repr(exc)` which differs across processes when the exception class embeds `<...at 0x...>` chaining).
   - Both runs should categorize as the **same failure** under the closed enum from Step 2 (`WorldlineCaptureError.ARGUMENTATION`).
   - Assert: the two materialized worldline content hashes are **equal**.
   - This is the correct premise: equivalent failures must hash equally because stable error categorization replaces the free-form repr. We are NOT asserting that a failure hashes equal to a success — those produce different materialized results and SHOULD differ.
   - **Must fail today**: today the runner interpolates `f"...failed: {exc}"` straight into the hash payload, so the two reprs hash differently.

2. **`tests/test_worldline_hash_repr_typed_failure.py`** (new — rewritten per Codex 2.10; property test, `@pytest.mark.property`)
   - Step 1 introduces a strict canonical encoder (`canonical_dumps`) that raises `TypeError` on any non-JSON-native value. This test locks in that behavior.
   - Hypothesis strategy: a payload containing one of `{Enum instance, set, dataclass not pre-converted, custom non-JSON object whose __repr__ embeds id(self), datetime, Path}`.
   - Call `canonical_dumps(payload)` directly.
   - Assert it raises `TypeError` (or a typed subclass — pick `CanonicalEncodingError`) naming the offending type.
   - Add the symmetric positive case: a Hypothesis strategy of pure JSON-native payloads (`dict[str, Union[str, int, float, bool, None, list[...], dict[...]]]`) round-trips deterministically across two `canonical_dumps` calls and yields byte-equal output.
   - At the call-site level, every consumer of `canonical_dumps` is expected to pre-normalize (Enums → `.value`, sets → `sorted(tuple(...))`, dataclasses → `to_dict()`) before encoding. A separate test `test_worldline_payload_normalization.py` asserts each call site does that pre-normalization step and that the resulting payload survives `canonical_dumps` without raising.
   - **Must fail today**: `default=str` swallows everything silently — no `TypeError` is raised, the encoder produces a string with embedded memory addresses, and there is no `canonical_dumps` symbol.

3. **`tests/test_worldline_argumentation_multi_extension.py`** (new)
   - Build a claim graph with `preferred` semantics that yields two extensions.
   - Run `capture_argumentation_state` and assert `argumentation_state` is not None.
   - **Must fail today**: `argumentation.py:107` requires `len == 1`, returns None, runner records nothing.

4. **`tests/test_journal_entry_contract.py`** (new — added per Codex 2.12, gates Step 4a before replay)
   - Construct a single revision via `revise(state_in, atom, ...)`. Inspect the resulting `TransitionJournal` entry.
   - Assert the entry exposes a typed operator name as a `JournalOperator` enum value (`JournalOperator.REVISE | CONTRACT | ITERATED_REVISE | ...`). Bare strings are rejected.
   - Assert `entry.operator_input` round-trips through `canonical_dumps` (i.e., it is a normalized JSON-native shape). For `revise`, that is the formula being asserted; for `contract`, the set being contracted; for `iterated_revise`, the input plus the prior-state reference.
   - Assert `entry.version_policy_snapshot` carries: revision policy version, ranking policy version, entrenchment policy version. Mutating any of those between two otherwise-identical revisions produces journal entries that are NOT byte-equal under `canonical_dumps`.
   - Assert `entry.normalized_state_in` and `entry.normalized_state_out` are sufficient to dispatch the operator from scratch — explicitly: a fresh process with no other context can deserialize the entry, look up `entry.operator`, call `dispatch(operator, state_in=entry.normalized_state_in, operator_input=entry.operator_input, policy=entry.version_policy_snapshot)`, and obtain a `state_out` byte-equal to the journal-recorded `state_out`. (Step 4b uses this guarantee; Step 4a must establish it.)
   - **Must fail today**: today's journal entry stores hash chain plus `to_dict()` blobs; there is no `JournalOperator` enum, no policy snapshot, and no normalization guarantee.

5. **`tests/test_replay_determinism_actually_replays.py`** (new — depends on test 4 above)
   - Build a `TransitionJournal` whose recorded `state_out` is bit-identical but algorithmically wrong (i.e., not what `revise(state_in, formula)` would produce when dispatched fresh from the journal entry).
   - Call `journal.replay()` (Step 4b's new method).
   - Assert it reports an error pointing at the divergent entry, naming the operator and the input.
   - **Must fail today**: `check_replay_determinism` only checks chain integrity, no replay happens, returns `ok=True`.

6. **`tests/test_contract_enumeration_bound.py`** (new — rewritten per Codex 2.11)
   - Construct a belief base with N supports such that `2^N` candidates would exceed any sensible bound.
   - Call public `contract(base, targets, entrenchment=...)` **without** the `max_candidates` keyword. Assert `TypeError: contract() missing 1 required keyword-only argument: 'max_candidates'`.
   - Call public `contract(base, targets, entrenchment=..., max_candidates=8)`. Assert it raises `EnumerationExceeded` with a partial-result payload (since `2^N` > 8).
   - Call public `contract(base, targets, entrenchment=..., max_candidates=2**N + 1)`. Assert it returns a normal result.
   - Repeat the same three calls for public `revise`, `iterated_revise`, and any other owner-layer operator that delegates to `_choose_incision_set` (audit at Step 5).
   - **Must fail today**: `max_candidates` is not in the public signature; the function enumerates fully without bound.

7. **`tests/test_iterated_revision_recomputes_entrenchment.py`** (new)
   - Build a base where revising introduces an atom that should change support counts (and therefore entrenchment).
   - Compare `iterated_revise` result to `revise` + fresh `compute_entrenchment` on the revised base.
   - Assert agreement.
   - **Must fail today**: `_entrenchment_from_state` reuses prior ranking.

8. **`tests/test_lifting_blocked_in_provenance.py`** (new)
   - Author rule c1→c2 with an exception that blocks proposition P. Materialize through `activation.py`. Inspect `WorldlineResult.dependencies` for blocked-exception identifiers.
   - **Must fail today**: blocked records are computed but `WorldlineDependencies` carries neither rule_ids nor exception_ids.

9. **`tests/test_worldline_target_shape_validation.py`** (new)
   - Construct a `WorldlineRevisionQuery` with `target="some-concept-name"`.
   - Run the worldline.
   - Assert it surfaces a structured `ValidationError`, not a bare `ValueError` from inside `_query_target_atom_ids`.
   - **Must fail today**: bare ValueError leaks.

10. **`tests/test_overlay_world_renamed.py`** (new — locks in J-R1)
    - AST-walks `propstore/` and `tests/`; asserts no `import HypotheticalWorld`, no `from propstore.world.hypothetical import HypotheticalWorld`, no class definition named `HypotheticalWorld`, and no public attribute `propstore.HypotheticalWorld`.
    - Asserts `propstore.world.overlay.OverlayWorld` exists (or `propstore.world.hypothetical.OverlayWorld` if the module file is kept under its current name; pick one, lock it in).
    - Asserts the docstring of `OverlayWorld` contains the explicit overlay-vs-Pearl disclaimer (text-match a sentinel substring such as "overlay semantics — not a Pearl intervention").
    - **Must fail today**: the class is still named `HypotheticalWorld`, callers still import that name, no disclaimer in docstring.

11. **`tests/test_workstream_j_done.py`** (new — gating sentinel) — `xfail` until WS-J closes; flips to `pass` on the final commit.

## Production change sequence

Each step lands in its own commit with a message of the form `WS-J step N — <slug>`.

### Step 1 — Strict canonical encoder
Add `propstore/canonical_json.py` with:
```python
class CanonicalEncodingError(TypeError):
    """Raised when canonical_dumps encounters a non-JSON-native value."""

def canonical_dumps(payload: Any) -> str:
    """Strict JSON encoder. Raises CanonicalEncodingError on unknown types."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
```
The default `json.dumps` already raises `TypeError` when no `default` is provided and an unknown type appears; wrap that as `CanonicalEncodingError` for typed catching. Replace every `default=str` site with this:
- `propstore/worldline/hashing.py:40-44`
- `propstore/support_revision/history.py:40-47`
- `propstore/worldline/argumentation.py:285-289`
- `propstore/support_revision/projection.py:168-176`

For each call site, walk the payload one level up and pre-normalize (Enums → `.value`, sets → `sorted(tuple(...))`, dataclasses → `to_dict()`, datetime → ISO8601 string). The encoder fails loudly on regression.

Acceptance: `tests/test_worldline_hash_repr_typed_failure.py` turns green.

### Step 2 — Exception reprs out of the hash
Define a closed enum of error categories:
```python
class WorldlineCaptureError(Enum):
    ARGUMENTATION = "argumentation"
    REVISION = "revision"
    SENSITIVITY = "sensitivity"
```
Modify `WorldlineArgumentationState`, `WorldlineRevisionState`, `WorldlineSensitivityOutcome` so that the `error` field stores `category: WorldlineCaptureError` (not a free-form string). Log the full exception via `logger.warning(..., exc_info=True)` (already done). The `to_dict()` for these payloads emits only the category — the hash sees a stable token.

Acceptance: `tests/test_worldline_hash_excludes_transient_errors.py` turns green.

### Step 3 — Multi-extension argumentation surface
Extend `WorldlineArgumentationState` with `extensions: tuple[frozenset[str], ...]` and `inference_mode: Literal["credulous", "skeptical", "grounded"]`. Update `propstore/worldline/argumentation.py:107-128` to:
- For grounded: `extensions[0]` (unique by definition).
- For preferred / stable / multi-status: capture all extensions; compute `justified` as credulous (union) or skeptical (intersection) per `policy.argumentation.inference_mode`.
- Coordinate with WS-D, which is also touching argumentation. Land WS-D first.

Acceptance: `tests/test_worldline_argumentation_multi_extension.py` turns green.

### Step 4a — Journal entry contract (added per Codex 2.12)

Replay is meaningless if the journal cannot reproduce its own inputs. Land the storage contract before the dispatcher.

- New module-level enum `propstore.support_revision.history.JournalOperator` with members `REVISE`, `CONTRACT`, `ITERATED_REVISE` (extend as new owner-layer operators land — closed-enum discipline). Bare strings are rejected at journal-entry construction time.
- Extend `TransitionJournalEntry` (frozen dataclass) with these required fields:
  - `operator: JournalOperator` — typed dispatch tag.
  - `operator_input: Mapping[str, Any]` — JSON-native, `canonical_dumps`-safe. For `REVISE`, `{"formula": <normalized formula>}`. For `CONTRACT`, `{"targets": <sorted list of target atom ids>}`. For `ITERATED_REVISE`, `{"formula": ..., "prior_entry_hash": <hex>}`.
  - `version_policy_snapshot: Mapping[str, str]` — fields: `revision_policy_version`, `ranking_policy_version`, `entrenchment_policy_version`. Source these from the policy bundle in scope at operator-call time.
  - `normalized_state_in: Mapping[str, Any]` — `EpistemicState.to_canonical_dict()` output (deep, JSON-native, deterministic field order).
  - `normalized_state_out: Mapping[str, Any]` — same shape.
- Add `EpistemicState.to_canonical_dict()` if it does not already exist; reject `default=str` in its implementation; pre-normalize sets/Enums/dataclasses explicitly.
- Update every `revise` / `contract` / `iterated_revise` call path that journals to populate the new fields. Per the no-fallbacks rule: no optional fields, no migration shim. Old journal blobs are not loaded by new code; if any test fixture journal exists in-tree, regenerate it.
- Add `dispatch(operator: JournalOperator, *, state_in, operator_input, policy) -> EpistemicState` as a single registry-driven entry point in `propstore.support_revision.dispatch`. Step 4b uses it.

Acceptance: `tests/test_journal_entry_contract.py` turns green; the journal entry's `operator_input + version_policy_snapshot + normalized_state_in` is provably sufficient to dispatch a fresh operator call.

### Step 4b — Real replay using the journal contract
Rename `check_replay_determinism` → `check_chain_integrity` (one commit, mechanical, no shim — the old method only ever did chain integrity). Add a new method on `TransitionJournal`:
```python
def replay(self) -> ReplayReport:
    """For every entry: deserialize, dispatch via JournalOperator, compare result hash to recorded hash."""
```
For each entry: call `dispatch(entry.operator, state_in=entry.normalized_state_in, operator_input=entry.operator_input, policy=entry.version_policy_snapshot)`; compute the canonical hash of the resulting `state_out`; compare against `entry.normalized_state_out`'s hash. Any divergence yields a `ReplayDivergence` row in the report naming the entry index, operator, and input.

Acceptance: `tests/test_replay_determinism_actually_replays.py` turns green.

### Step 5 — Bound the public `contract` enumeration (locked-in per Codex 2.11)

`max_candidates` is a **required keyword argument** on every owner-layer surface that delegates to `_choose_incision_set`. No default. No `DEFAULT_INCISION_MAX_CANDIDATES` constant. No fallback path. Every caller passes an explicit value.

Affected public signatures (audit list — extend during implementation if more are found):
- `propstore.support_revision.operators.contract(base, targets, *, entrenchment, max_candidates: int)`
- `propstore.support_revision.operators.revise(base, formula, *, entrenchment, max_candidates: int)`
- `propstore.support_revision.iterated.iterated_revise(state, formula, *, max_candidates: int)`
- Any other public surface that reaches `_choose_incision_set` in the call graph.

Caller updates (one pass, no shim, per `feedback_no_fallbacks`):
- Walk every call site via grep / rope. Each gets an explicit `max_candidates=` argument. Pick the value at the call site based on the operation's tolerance — CLI and worldline-runner paths pick a budget appropriate to a user-facing operation; sensitivity-loop paths pick a tighter budget; AGM-postulate test paths pick a deliberately-large budget when proving an operator runs to completion on a small base.
- The callers OWN the value. The library is policy-free on this dimension.

`EnumerationExceeded` carries a partial-result payload so callers that catch it can surface `ResultStatus.BUDGET_EXCEEDED` (coordinates with WS-O-gun D-18 wire-up — this is the same discipline upstream).

Acceptance: `tests/test_contract_enumeration_bound.py` turns green; grep for `_choose_incision_set` from outside `support_revision/` returns zero direct hits; every public-API caller passes `max_candidates=` explicitly.

### Step 6 — Iterated revision recomputes entrenchment
Replace `_entrenchment_from_state(state)` at `iterated.py:70` with `compute_entrenchment(state.base)`. Verify that test `tests/test_iterated_revision_recomputes_entrenchment.py` turns green and existing iterated-revision tests still pass; if any depended on the stale-ranking quirk, that's a separate AGM-postulate test bug — fix the test.

Acceptance: `tests/test_iterated_revision_recomputes_entrenchment.py` turns green.

### Step 7 — Rename `HypotheticalWorld` → `OverlayWorld` (rope-driven)
Per **D-11**, this is a mechanical rope rename, no alias.

- Rename the class `HypotheticalWorld` → `OverlayWorld` in `propstore/world/hypothetical.py:438-593`.
- Rename the module file `propstore/world/hypothetical.py` → `propstore/world/overlay.py` (rope handles the file move + the package `__init__` re-export adjustment).
- Update the class docstring to state the semantics explicitly. Required text: "An overlay world in which a synthetic claim asserting `X = x` is added; the existing parameterization graph is preserved and conflict resolution decides which claim wins. This is overlay semantics — not a Pearl intervention. For Pearl `do()` / Halpern HP-modified intervention, see `InterventionWorld` (WS-J2)."
- Walk every importer with rope: tests, CLI, docs code-blocks, `propstore.__init__`. Single PR. No `from .hypothetical import HypotheticalWorld as OverlayWorld` shim. No `HypotheticalWorld = OverlayWorld` alias. The rule from D-3 / `feedback_no_fallbacks` applies: rip out the old name, let mis-imports break, fix every caller.
- After the rename lands, `tests/test_overlay_world_renamed.py` (the AST-walk gate from the failing-tests list) becomes the standing guard against regression.

Acceptance: `tests/test_overlay_world_renamed.py` turns green; `grep -r HypotheticalWorld propstore tests docs` returns zero hits.

### Step 8 — Cluster J-M cleanups
- **J-M1 widen worldline hash to 32 hex** at `hashing.py:46` — 128-bit collision safety.
- **J-M2 deep-copy `EpistemicStateSnapshot.from_state`** — wrap mutable fields explicitly even though they're frozen today (defense against future field additions).
- **J-M3 validate `WorldlineRevisionQuery.target`** — at schema parse time, accept only the prefixed forms; structured error.
- **J-M4 promote `__override_` to a constant** — `propstore/worldline/_constants.py:OVERRIDE_CLAIM_PREFIX`. Centralize, reference from every call site.
- **J-M5 carry blocked lifting exceptions in `WorldlineDependencies`** — add `lifting_rules: tuple[str, ...]` and `blocked_exceptions: tuple[str, ...]`. Wire from `activation.py` and `sidecar/passes.py`.
- **adjacent**: `_revision_state_snapshot` returns a snapshot, never the live state — fix `revision_capture.py:72-79` to require the bound's snapshot method or build one explicitly.

Each is its own commit.

Acceptance: `tests/test_lifting_blocked_in_provenance.py` and `tests/test_worldline_target_shape_validation.py` turn green; the J-M findings vanish from `gaps.md`.

### Step 9 — Close gaps and gate
- Update `docs/gaps.md`: remove entries for J-H1, J-H2, J-H3, J-H4, J-H5, J-H6, J-R1, and J-M1..J-M5; add a `# WS-J closed <sha>` line in the "Closed gaps" section.
- Confirm the WS-J2 stub exists at `reviews/2026-04-26-claude/workstreams/WS-J2-intervention-world.md`. WS-J's "closed" status does not depend on WS-J2 being closed — only on the stub existing so the deferred Pearl work is tracked.
- Open follow-up workstream stubs for the OTHER missing features that this WS does **not** close (Spohn kappa, Bonanno merge, lifting-rule transitive closure, cheap `is_stale` fingerprint).
- Flip `tests/test_workstream_j_done.py` from `xfail` to `pass`.
- Update STATUS line in this file to `CLOSED <sha>`.

## Acceptance gates

Before declaring WS-J done, ALL must hold:

- [x] `uv run pyright propstore` — passes with 0 errors.
- [x] `uv run lint-imports` — passes.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-J <listed test files>` — all green.
- [x] Full suite — no NEW failures vs the WS-A baseline.
- [x] No `default=str` remains in any module under `propstore/worldline/` or `propstore/support_revision/`.
- [x] `_choose_incision_set` is unreachable from any public call site without an explicit `max_candidates=` keyword argument; no default exists for that parameter on owner-layer APIs.
- [x] `TransitionJournalEntry` carries `operator: JournalOperator`, `operator_input`, `version_policy_snapshot`, `normalized_state_in`, `normalized_state_out`. `journal.replay()` dispatches via `JournalOperator` and compares hashes.
- [x] No symbol `HypotheticalWorld` survives anywhere in `propstore/`, `tests/`, or `docs/` (verified by `tests/test_overlay_world_renamed.py`).
- [x] `OverlayWorld` docstring contains the overlay-vs-Pearl disclaimer.
- [x] WS-J2 stub file exists.
- [x] `tests/test_workstream_j_done.py` passes.
- [x] STATUS line is `CLOSED a15eefc0`.

## What this WS does NOT do

These are real findings raised in cluster J or downstream of D-11 that this WS deliberately defers:

- **`InterventionWorld` / Pearl `do()` operator implementation** — **deferred to WS-J2** per D-11. WS-J2 implements parameterization-edge severing, AC1/AC2/AC3 actual-cause, and Halpern 2015 HP-modified semantics on top of (or beside) the renamed `OverlayWorld`. WS-J2 has its own paper-citation discipline and its own test corpus.
- **Halpern actual-cause AC1/AC2/AC3 evaluator** — **part of WS-J2**. Requires partition-search + freeze-and-test reasoning per Halpern 2005 Def 3.1 / Halpern 2015 HP-modified. Sits on top of `InterventionWorld`.
- **Spohn OCF kappa values with firmness parameter** — tracked by `WS-J3-spohn-kappa.md`. Today `EpistemicState.ranking` is a positional sort key derived from index in `ranked_atom_ids` (`iterated.py:22`, `:51`). Migrating to true Spohn kappa is a state-shape change with implications for snapshots, history, and AGM postulate verification. Required for Darwiche-Pearl C1-C4 and any subjective-logic bridge.
- **Bonanno 2012 ternary `B(h, K, phi)` merge operator** — tracked by `WS-J4-bonanno-merge.md`. `iterated.py:66-67` raises on `len(merge_parent_commits) > 1`. Test `test_run_worldline_revision_merge_point_refusal_is_explicit` asserts this is intentional. The `merge_parent_commits` data model already accepts a DAG.
- **Lifting-rule transitive closure** — tracked by `WS-J5-lifting-closure.md`. `context_lifting.py:176-214` is single-pass. Bozzato 2018 CKR semantics define lifting as a fixpoint under `eval()`. The cycle handling and closure are also missing.
- **Cheap `is_stale` fingerprint path** — tracked by `WS-J6-worldline-stale-fingerprint.md`. `definition.py:368-371` calls `run_worldline` to compute the comparison hash. A list-stale CLI hits O(N) full materializations. Designing a fingerprint table that captures (claims, stances, contexts, parameterizations) without rerun is its own design.
- **Sensitivity over string-typed overrides** — `runner.py:173-177` silently drops them. WS-D may handle this; if not, a separate ticket.
- `R-7` (`pre_resolve_conflicts` set-iteration ordering), `R-6` (chain step under-counting non-claim sources), `R-8` (assumption ordering), `B23` (display_claim_id collision) — these belong in a determinism-microbug followup. Listing them keeps the audit honest; closing them in this WS would broaden scope past what the listed acceptance gates can verify.

If any of those are pulled into WS-J during implementation, they must be added to the table at the top of this file in the same commit. No silent scope creep.

## Papers / specs referenced

- **Pearl 2000** §3.2.1 `do(X=x)` definition (`papers/Pearl_2000_.../notes.md`) — cited only to explain what `OverlayWorld` is *not* doing. The implementation lives in WS-J2.
- **Halpern & Pearl 2005** Definition 3.1 (AC1/AC2/AC3) (`papers/Halpern_2005_.../notes.md`) — cited only to explain what `OverlayWorld` is *not* doing. WS-J2.
- **Halpern 2015 HP-modified** (`papers/Halpern_2015_.../notes.md`) — cited only to explain what `OverlayWorld` is *not* doing. WS-J2.
- **Spohn 1988** A_n-conditionalization with firmness `n` (`papers/Spohn_1988_.../notes.md`) — missing-feature, separate WS.
- **Bonanno 2007** Backward Uniqueness; **Bonanno 2010** §6 ternary `B(h, K, phi)` — missing-feature, separate WS.
- **Bozzato 2018** CKR semantics with clashing-set justifications — J-M5 plus the lifting-closure missing-feature.
- **McCarthy 1993** / **McCarthy 1997** `ist(c, p)` modal lifting — uninterpreted BRIDGE / SPECIALIZATION / DECONTEXTUALIZATION tags.
- **Zilberstein 1996** — cited in `operators.py:264-269` docstring for `EnumerationExceeded`. Pattern exists but is now wired into the public surface as a required-keyword bound (J-H5 / Step 5).

## Cross-stream notes

- **WS-A** schema parity is a prerequisite for trustworthy worldline tests. Do not start WS-J implementation before WS-A merges, even though WS-J does not touch the sidecar schema directly — `WorldlineResult` round-trip serialization runs through the sidecar in some test paths.
- **WS-D** (math naming / sensitivity / argumentation surface) overlaps with Step 3 (multi-extension) and the J-M5 cleanup of sensitivity error handling. Land WS-D first; rebase Step 3 onto its argumentation surface.
- **WS-I** (ATMS unbounded-stable interface replacement) is a hard prerequisite per Codex 2.8: `revision_capture`, `materialize`, and the sensitivity loop all consume ATMS-derived state. WS-J's determinism guarantees only mean something on top of WS-I's corrected stability surface. WS-I lands first; WS-J rebases its multi-extension and revision tests onto the new interface.
- **WS-J2** (`InterventionWorld` / Pearl `do()` / Halpern HP-modified) is the immediate downstream workstream. WS-J2 is gated on Step 7 of this file (the rename) landing first, so WS-J2 can either subclass `OverlayWorld` or sit beside it without name confusion. WS-J2 owns the parameterization-edge severing, AC1/AC2/AC3 evaluator, SCM data structure, and the Pearl/Halpern test corpus. WS-J declares done with WS-J2 still OPEN — they are sequenced, not coupled.
- The `imports_are_opinions` project memory note is relevant to the Spohn-OCF deferral: positional ranking precludes the subjective-logic uncertainty bridge that note alludes to. When the OCF kappa workstream lands, it should re-read that note.

## Done means done

This workstream is done when **every finding in the table at the top is closed**, not when "most" are closed. Specifically:

- J-H1, J-H2, J-H3, J-H4, J-H5, J-H6, J-R1, J-M1, J-M2, J-M3, J-M4, J-M5 — twelve findings, twelve corresponding green tests in CI.
- Adjacent finding (`_revision_state_snapshot` returning live state) — fixed.
- Journal entry contract (Step 4a) lands before replay (Step 4b); both are green.
- `max_candidates` is a required keyword argument on every owner-layer operator; no default exists.
- `HypotheticalWorld` is gone from the codebase. `OverlayWorld` exists with the overlay-vs-Pearl disclaimer in its docstring.
- WS-J2 stub file exists at `reviews/2026-04-26-claude/workstreams/WS-J2-intervention-world.md` so the deferred Pearl work is tracked even if not yet implemented.
- `gaps.md` is updated.
- The workstream's gating sentinel test (`tests/test_workstream_j_done.py`) has flipped from xfail to pass.
- Follow-up workstream stubs for the other deferred items (Spohn, Bonanno, lifting closure, cheap is_stale) exist, even if empty, so they're not lost.

If any one of those is not true, WS-J stays OPEN. No "we'll get to multi-extension later." Either it's in scope and closed, or it's explicitly listed under "What this WS does NOT do" in this file before declaring done.
