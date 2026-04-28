# WS-O-qui: quire fixes — git-backed artifact store

**Status**: CLOSED v0.2.0 / a27b3cbc
**Depends on**: nothing internal to propstore
**Blocks**: none directly. Coordinates with WS-N (which collapses propstore's three duplicate `_canonical_json` implementations onto whatever quire's hashing module ends up being). Coordinates with WS-J (which hashes content for replay determinism).
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)
**Repository**: `C:\Users\Q\code\quire\` — separately versioned (`pyproject.toml` v0.1.1).

---

## Why this workstream exists

Quire is propstore's substrate. Every persistence path in propstore — `repo.git.commit_files`, `commit_batch`, `store_blob`, `commit_flat_tree`, `write_note` — terminates in a `GitStore` instance constructed by quire. Every canonical hash propstore computes for identity (`families/identity/claims.py`, `families/identity/concepts.py`, `artifact_codes.py`, `source/finalize.py`) calls `quire.hashing.canonical_json_sha256`. Every YAML round-trip (`families/**/documents.py`) uses `quire.documents`. Every cross-family lookup uses `quire.references`.

The boundary is not optional and it is not narrow. Cluster S (`reviews/2026-04-26-claude/cluster-S-quire.md`) found 5 HIGH and 7 MED bugs in quire that affect propstore's correctness directly. Two of them (HIGH #1, HIGH #2) mean that quire has *two* canonicalization paths in the same package that disagree. One of them (HIGH #4 + HIGH #5) means concurrent or aborted writers leak orphan blobs the runtime can never see again. One of them (MED #9) means a public method whose name implies "make the worktree match HEAD" leaves the worktree in a state where the next shell `git commit` silently wipes data.

These are quire bugs, not propstore bugs. The fix lives in `C:\Users\Q\code\quire\`. This file documents what to fix, where the propstore-side acceptance evidence will live, and what the propstore pin update looks like once the upstream lands. Test paths under `C:\Users\Q\code\quire\tests\` are the load-bearing artifacts; this propstore-side document is the planning surface and the cross-stream coordination point.

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every Cluster S HIGH and MED listed below is gone from quire, has a green test gating it in `C:\Users\Q\code\quire\tests\`, and propstore's pin in `pyproject.toml` is bumped to a release that contains every fix.

| Finding | Severity | Quire-side citation | Description |
|---|---|---|---|
| **S-H1** | HIGH | `quire/hashing.py:8-15` vs `quire/contracts.py:235-258` | Two canonicalization rules in one package: `canonical_json_sha256` accepts only what `json.dumps` accepts; `_normalize_payload` whitelists `set/frozenset/tuple/msgspec.Struct/dataclass/VersionId`. Same logical payload, different hash depending on which path the caller takes. |
| **S-H2** | HIGH | `quire/hashing.py:8-15` vs `quire/contracts.py:262-268` | `canonical_json_sha256` does not pass `allow_nan=False`. NaN/Inf serialize to non-JSON `NaN`/`Infinity`. Identity hashes silently land outside the JSON grammar. `_normalized_sort_key` (`contracts.py:262-268`) sets `allow_nan=False`. Same package, two answers. |
| **S-H3** | HIGH | `quire/family_store.py:450-461` | `_check_preemptive_head` reads the current head and compares to `expected_head` but holds nothing. Naming suggests a transactional reservation; implementation is opportunistic. Callers who treat it as a pin race past it. |
| **S-H4** | HIGH | `quire/git_store.py:817-845` | `_commit` writes blobs into the object store *before* the ref CAS at line 847. On CAS failure or mid-flight raise, blobs and trees remain in the object store with no quire-side GC. Long-running write-heavy processes accumulate dead objects. |
| **S-H5** | HIGH | `quire/git_store.py:142` | `_mutation_lock` is a `threading.RLock()` per `GitStore` instance. Two processes opening the same on-disk repo coordinate only via dulwich's ref CAS; they do not share this lock. Multi-process writers race past `expected_head`/CAS into the orphan accumulation in S-H4. |
| **S-M1** | MED | `quire/versions.py:17` | `VersionId(value, *, allow_placeholder=True)` — default permissive. `_require_version` in `families.py` only checks `isinstance`. Arbitrary non-empty strings construct `VersionId` instances at the family layer; only the contract round-trip rejects. Drift between in-memory model and persisted form. |
| **S-M2** | MED | `quire/references.py:96-104` | `ReferenceIndex.resolve_id` returns `None` on ambiguity, indistinguishable from "not found." The fallback at line 102 (`if reference in records_by_id: return reference`) partially saves the alias-shadowing case but only when the lookup itself wasn't unique. Cluster A's PK-collision scent surfaces here. |
| **S-M3** | MED | `quire/references.py:36-52` | `ForeignKeySpec.required` and `many` are decorative. They appear only in `contract_body()`. Quire never validates them. Anyone reading the type signature would expect runtime enforcement. |
| **S-M4** | MED | `quire/git_store.py:672-690` vs `:692-694` | `materialize_worktree(remove_extra=False)` writes files but does NOT call `_refresh_on_disk_index`. Only `sync_worktree` does. The docstring at lines 696-706 explicitly says: without index refresh, `git status` reports staged-for-deletion and a subsequent shell `git commit` silently wipes the tree. Public method name implies safety it does not provide. |
| **S-M5** | MED | `quire/artifacts.py:444-460, 470-471` | `HashScatteredYamlPlacement(filename_mode="digest")` (the default) saves documents whose original ref string cannot be recovered from disk. `iter_refs` raises `TypeError` because the codec is not reversible. There is no enforcement that an external index exists. |
| **S-M6** | MED | `quire/artifacts.py:602-624, 646-678` | Placement Protocol Liskov-broken. `FixedFilePlacement` and `TemplateFilePlacement` raise `TypeError` from `iter_refs`, `iter_artifacts`, `ref_from_locator`, and `ref_from_loaded`. The Protocol declares the methods; four of five placements implement them; two raise. Generic iteration over placements must special-case. |
| **S-M7** | MED | `quire/git_store.py:563-589` | `merge_base` calls `ancestor_distances` once per branch, then once per common ancestor (`O(common_ancestors × total_ancestors)`). Dulwich's native `find_common_revisions`/`MergeBase` is not used. |
| **S-Boundary** | OBS | `quire/__init__.py:__all__` | Propstore reaches past `__all__` into `quire.artifacts.*` (e.g. `FlatYamlPlacement`, `HashScatteredYamlPlacement`), `quire.contracts.*` (`ContractManifest`, `check_contract_manifest`), `quire.refs.*`, `quire.tree_path.*`. The exported `__all__` lists 22 names; propstore imports symbols that are NOT in that list from `quire.artifacts`, `quire.contracts`, `quire.tree_path`, `quire.documents`, `quire.references`. Boundary is wider than the public surface admits. |

## Code references (verified by direct read)

All citations below were confirmed by reading the quire source files directly during this workstream's authoring (2026-04-26).

### Hashing divergence (S-H1, S-H2)

`C:\Users\Q\code\quire\quire\hashing.py` is 21 lines. The full definition:

```python
def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

def canonical_json_sha256(payload: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json_bytes(payload)).hexdigest()}"
```

Compare `quire/contracts.py:235-258` (`_normalize_payload`): handles `VersionId` → `str`, `msgspec.Struct` → `to_builtins`, dataclass → `asdict`, `set/frozenset` → sorted list via `_normalized_sort_key`, dict (raises on non-string keys), `tuple` → list, `list`, primitives. Anything else raises `TypeError`. Then `_normalized_sort_key` (262-268) calls `json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",",":"), sort_keys=True)`. Two pieces of evidence in one module:

1. `_normalize_payload` is a whitelist; `canonical_json_bytes` is whatever `json.dumps` accepts. Pass a `frozenset` to the latter and it raises late from inside `json.dumps`. Pass a `tuple` and it gets serialized as a list (silent), but the calling site's static type signature was `Any` so the developer cannot know.
2. `_normalized_sort_key` sets `allow_nan=False`; `canonical_json_bytes` does not. Pass `float("nan")` to the hash function and the output is `NaN` — a non-JSON token. The hash succeeds; downstream JSON parsers fail to round-trip.

Propstore consumers of `canonical_json_sha256`: `propstore/families/identity/claims.py:71`, `propstore/families/identity/concepts.py:62`, `propstore/artifact_codes.py:10`, `propstore/source/finalize.py:6`. Each feeds the function whatever `canonicalize_*_for_version` returns. If any of these ever yield a `frozenset`, `set`, `msgspec.Struct`, or `VersionId`, the hash call raises `TypeError`. If any contain a `NaN` (hostile input or buggy upstream), the hash succeeds but the bytes are non-JSON.

### Preemptive-head opportunism (S-H3)

`quire/family_store.py:450-461`:

```python
def _check_preemptive_head(self) -> None:
    if self.expected_head is None or self.branch is None:
        return
    backend = self.store.backend
    if backend is None:
        return
    current = self.store.branch_head(backend, self.branch)
    if current is not None and current != self.expected_head:
        raise ValueError(
            f"Transaction branch {self.branch!r} head mismatch (preemptive): "
            f"expected {self.expected_head}, got {current}"
        )
```

This is an advisory read with no lock and no reservation. Between this check and the eventual `commit_batch` call (line 441-447), another writer can advance the branch. The CAS in `_commit` will catch it (`git_store.py:847` via `set_if_equals`), but the *naming* says "expected" — clients can reasonably assume "if the preemptive check passes, the commit will not fail with a head-mismatch ValueError." That assumption is wrong.

### Orphan blob accumulation (S-H4)

`quire/git_store.py:790-856` (`_commit`). Sequence:
1. Line 801: `tip_sha = _ref_get(...)` — read current ref
2. Lines 802-808: `expected_head` validation (raises if mismatch)
3. Lines 819-820: `store.add_object(blob)` — write blobs **into the object store** (these are now persistent)
4. Lines 821-828: build path tuples
5. Subsequent `_apply_tree_changes` builds and adds Tree objects
6. Line 847: `set_if_equals(branch_ref, new_commit_sha, tip_sha)` — CAS; raises on race

If step 6 fails (lost race) or any line between steps 3 and 6 raises, the blobs from step 3 are persistent in the object store with nothing referencing them. Dulwich does not auto-pack/gc. Quire exposes no GC. Long-running propstore processes (e.g. `pks web` serving many sources) accumulate orphans indefinitely.

### Cross-process race (S-H5)

`quire/git_store.py:142`:

```python
self._mutation_lock = threading.RLock()
```

This is a per-instance lock. Two `GitStore.open(root)` calls in the same process produce two instances with independent locks (assuming they don't share a singleton; they don't — `GitStore.open` is a fresh constructor). Two *processes* opening the same bare repo path share nothing at all. The only cross-process coordination quire provides is dulwich's `set_if_equals` ref CAS — which catches the *commit* race but does nothing about steps 3-5 of the `_commit` sequence above. Two processes both writing 100 large blobs, both losing the CAS once each, leak 200 blobs. There is no `flock` on the on-disk repo.

### VersionId placeholder default (S-M1)

`quire/versions.py:17-25`:

```python
def __init__(self, value: str, *, allow_placeholder: bool = True) -> None:
    normalized = value.strip()
    if not normalized:
        raise ValueError("VersionId cannot be empty")
    if not allow_placeholder:
        _parse_calendar_version(normalized)
        if normalized in _PLACEHOLDER_VALUES:
            raise ValueError(f"Placeholder contract version is not allowed: {normalized}")
    object.__setattr__(self, "value", normalized)
```

When `allow_placeholder=True` (the default), the only check is non-empty. `VersionId("foo")` succeeds. `_parse_calendar_version` is only called in the strict path. `__lt__` (line 27-30) calls `_parse_calendar_version` unconditionally; sorting placeholder VersionIds raises mid-sort. `families.py` `_require_version` only checks `isinstance(x, VersionId)`. `ContractEntry.from_payload` and `CompatibilityMarker.from_payload` use `allow_placeholder=False` (`contracts.py:44, 67`), so the YAML round-trip *is* strict — but every other code path is loose.

### Reference ambiguity swallow (S-M2)

`quire/references.py:96-104` (the actual location; the workstream prompt cites `refs.py:73-104` but `refs.py` only contains `RefName` and ref-type factories — `ReferenceIndex.resolve_id` lives in `references.py`):

```python
def resolve_id(self, reference: object) -> str | None:
    if not isinstance(reference, str) or not reference:
        return None
    candidates = self.lookup.get(reference, ())
    if len(candidates) == 1:
        return candidates[0]
    if reference in self.records_by_id:
        return reference
    return None
```

When `len(candidates) > 1`, return `None`. No `Resolution` object, no signal that ambiguity vs absence happened. Callers must use `.resolve()` (lines 109-138) which returns `ReferenceResolution(resolved_id=None, ambiguous_candidates=...)`. Default API is the lossy one. The `if reference in self.records_by_id: return reference` fallback handles the case where `reference` is itself a canonical ID — but only when the lookup's candidate list isn't of length 1. Cluster S MED #9 spelled out the alias-shadowing interleaving where `{id: "alpha", aliases: ["beta"]}` and a separate `{id: "beta"}` produce an ambiguous lookup for `"beta"` that the fallback *does* save (because `"beta"` is in `records_by_id`) — but only because the order of lookup entries happens to produce this. Subtle; the API does not promise this rescue.

### ForeignKeySpec decoration (S-M3)

`quire/references.py:36-52`:

```python
@dataclass(frozen=True)
class ForeignKeySpec:
    name: str
    contract_version: VersionId
    source_family: str
    source_field: str
    target_family: str
    required: bool = True
    many: bool = False

    def contract_body(self) -> dict[str, object]:
        return {
            "source_family": self.source_family,
            "source_field": self.source_field,
            "target_family": self.target_family,
            "required": self.required,
            "many": self.many,
        }
```

Grep for `required` usage outside this module: zero validation paths. `many` likewise. They serialize into the contract manifest body so a downstream consumer *could* enforce them — but nothing in quire does. Propstore's `compiler/references.py:9` and `contracts.py:11` import `ForeignKeySpec`; whether propstore enforces is a propstore-side question, not quire's.

### materialize_worktree footgun (S-M4)

`quire/git_store.py:672-723`. `materialize_worktree(*, remove_extra=False)` writes blobs out to the worktree but never calls `_refresh_on_disk_index`. `sync_worktree` (lines 692-694) is a 3-line function that calls `materialize_worktree(remove_extra=True)` then `_refresh_on_disk_index()`. The docstring on `_refresh_on_disk_index` (lines 696-706) is unambiguous:

> Dulwich does not touch the index during commit-object creation; without this step, `git status` in the worktree reports every tracked file as staged-for-deletion (empty index vs populated HEAD tree) and every on-disk file as untracked. A subsequent `git commit` would then silently wipe the tree.

The dangerous shape: a propstore caller invoking `materialize_worktree(remove_extra=False)` to "lay down the tree without nuking ad-hoc files" — the explicit non-destructive option — gets the worst-case index state. Anyone running `git commit` from the shell after that loses the working tree.

### HashScattered digest mode (S-M5)

`quire/artifacts.py:444-460`. With `filename_mode="digest"` (the default per line 441), the on-disk filename is the SHA digest of the encoded ref. `iter_refs` (lines 462-479) and `iter_artifacts` (lines 481-508) raise `TypeError("opaque hash-scattered placement requires an index or loaded-document ref recovery")` when `filename_mode != "encoded_ref"`. `ref_from_locator` (510-519) likewise. The constructor permits the dangerous combination: the only check in `__post_init__` is `if filename_mode == "encoded_ref": _require_reversible_ref_codec(self.codec)`. There is no symmetric check that `filename_mode == "digest"` requires an external index.

### Placement Protocol Liskov (S-M6)

`quire/artifacts.py:602-624` (FixedFilePlacement) and `:646-678` (TemplateFilePlacement). Both raise `TypeError` from `iter_refs`, `iter_artifacts`, `ref_from_locator`, `ref_from_loaded`. The implicit Protocol (the union of methods that `ArtifactFamily` calls on its placement) declares all four; three of five placements implement them; two raise unconditionally.

### merge_base quadratic (S-M7)

`quire/git_store.py:553-589`. Reads `ancestor_distances(sha_a)` and `ancestor_distances(sha_b)` (each a BFS over all ancestors). Then for *each* common ancestor, calls `ancestor_distances(ancestor_sha)` again to test whether candidate is dominated by another candidate. On a long history with many merges, this is `|common| × |total ancestors|`.

### Boundary observation

`quire/__init__.py:20-41`: `__all__` lists `BoundFamily, BoundFamilyRegistry, BoundFamilyTransaction, FamilyDefinition, FamilyIdentityPolicy, FamilyRegistry, ForeignKeySpec, GitStore, GitStorePolicy, NotesRef, RefName, ReferenceIndex, ReferenceResolution, TransactionalBoundFamily, VersionId, canonical_json_bytes, canonical_json_sha256, documents, single_field_ref_type, singleton_ref_type` — 20 names. Propstore consumers (per cluster S report and confirmed grep) reach for: `quire.artifacts.ArtifactFamily, FlatYamlPlacement, HashScatteredYamlPlacement, BranchPlacement` (not in `__all__`); `quire.contracts.ContractManifest, check_contract_manifest` (not in `__all__`); `quire.tree_path.TreePath, FilesystemTreePath, GitTreePath` (not in `__all__`); `quire.references.ForeignKeySpec, ReferenceIndex` (re-exported from top level — these *are* in `__all__`); `quire.documents.*` (re-exported as a subpackage — listed). The mismatch: every placement class plus the contract manifest are public-de-facto via cross-package imports but private-de-jure via `__all__`.

## First failing tests (write these first; all live in `C:\Users\Q\code\quire\tests\` unless noted)

1. **`tests/test_canonical_hash_normalizes_payload.py`** (new)
   - Build a payload containing `frozenset({"a","b"})`, a `tuple`, a `set`, a `msgspec.Struct` instance, a `VersionId`, and a nested dataclass.
   - Compute the contract-side canonical bytes by passing the same payload to `_normalize_payload` then `_normalized_sort_key`.
   - Compute `canonical_json_sha256(payload)` directly.
   - Assert: hashing path either accepts and produces a hash that is consistent with the contract-canonicalized JSON, OR it normalizes via the same code path. Currently the call raises `TypeError` from inside `json.dumps` for `frozenset`/`set`/`Struct`/`VersionId`/dataclass.
   - **Must fail today**: `TypeError` on the first non-JSON-native input.

2. **`tests/test_canonical_hash_rejects_nan.py`** (new)
   - `canonical_json_sha256({"x": float("nan")})` — assert raises `ValueError` (the `allow_nan=False` outcome) OR rounds NaN to a sentinel.
   - Same for `float("inf")` and `float("-inf")`.
   - **Must fail today**: returns `sha256:<hex>` of `{"x":NaN}` (a non-JSON token, but `json.dumps` produces it because `allow_nan` defaults to True).

3. **`tests/test_expected_head_is_transactional.py`** (new)
   - Open two threads against the same `GitStore`. Thread A calls `_check_preemptive_head` with the current head, then sleeps. Thread B advances the branch via a separate commit. Thread A then calls `commit_batch` with the original `expected_head`.
   - Assert: either the preemptive check is documented as advisory (test names that), or it provides a reservation token that the subsequent commit consumes.
   - **Must fail today**: preemptive check passes; subsequent commit raises a different error than the preemptive name implies.

4. **`tests/test_cas_failure_does_not_orphan_blobs.py`** (new)
   - Open two `GitStore` instances against the same on-disk repo. Process A starts a commit; process B advances the branch. Process A's CAS fails.
   - Walk the object store and assert: blobs added by process A's failed commit are *not* present (or are reachable from a recovery ref).
   - **Must fail today**: blobs persist in the object store unreferenced.

5. **`tests/test_multiprocess_lock_serializes_writers.py`** (new)
   - Two subprocesses write to the same on-disk repo concurrently for N seconds.
   - Both observe successful CAS counts and final ref state.
   - Walk object store; assert orphan count is bounded by some explicit policy (zero, or "at most one per failed CAS with documented recovery").
   - **Must fail today**: orphan count is unbounded.

6. **`tests/test_version_id_default_strict.py`** (new)
   - `VersionId("foo")` — assert raises.
   - `VersionId("foo", allow_placeholder=True)` — assert succeeds (explicit opt-in).
   - **Must fail today**: `VersionId("foo")` succeeds with no error.

7. **`tests/test_reference_index_signals_ambiguity.py`** (new)
   - Build a `ReferenceIndex` whose lookup has two records with overlapping aliases.
   - Call `resolve_id(ambiguous_key)` and `exists(ambiguous_key)`.
   - Assert: either raises `AmbiguousReferenceError`, or returns a sentinel/Resolution distinguishable from "not found."
   - **Must fail today**: `resolve_id` returns `None`; `exists` returns `False`. Same as the not-found case.

8. **`tests/test_foreign_key_spec_required_enforced.py`** (new)
   - Construct a `ForeignKeySpec(required=True)`. Build a record whose source_field is empty/missing. Run *something* in quire that should reject this — even if the answer is "quire doesn't enforce, propstore does" — the test names that explicitly with a paper trail.
   - **Must fail today**: the field is decorative.

9. **`tests/test_materialize_worktree_refreshes_index.py`** (new)
   - Open a `GitStore` rooted at a real on-disk repo. Commit a tree. Call `materialize_worktree(remove_extra=False)` (the default).
   - Subprocess `git status` in the worktree. Assert the output is "clean" — not "all files staged for deletion."
   - **Must fail today**: index is empty; status reports D for every tracked file.

10. **`tests/test_hash_scattered_digest_requires_index.py`** (new)
    - Construct `HashScatteredYamlPlacement(filename_mode="digest")` and write a document.
    - Iterate via `iter_refs` — assert either succeeds (with an external-index parameter) or raises a clear `IndexRequiredError` distinguishable from a generic `TypeError`.
    - **Must fail today**: raises `TypeError` with an opaque message; the constructor permits the unsafe combination silently.

11. **`tests/test_placement_protocol_liskov.py`** (new)
    - Iterate over every placement class. For each, call `iter_refs(...)`. Either all succeed or all raise the *same* `Scannable` Protocol's negative.
    - **Must fail today**: 3 succeed, 2 raise `TypeError` with no shared base exception.

12. **`tests/test_merge_base_uses_dulwich_native.py`** (new — perf budget test)
    - Construct a synthetic history with N=200 ancestors and many merges.
    - Assert `merge_base` returns the correct result AND completes within a budget that rules out the current `O(common × total)` walk.
    - **Must fail today**: budget exceeded.

13. **`tests/test_quire_public_surface_pinned.py`** (new in propstore — `propstore/tests/test_quire_boundary.py`)
    - Walk every `from quire.<module> import <name>` in propstore source. Assert each `<name>` is in `quire.<module>.__all__` OR in `quire.__init__.__all__`.
    - **Must fail today**: propstore imports `FlatYamlPlacement` from `quire.artifacts`; not in either `__all__`.

## Production change sequence (quire-side)

Each step lands in its own commit on the quire repo. Commit messages of the form `WS-O-qui step N — <slug>`.

### Step 1 — Collapse hashing onto contracts canonicalization

`quire/hashing.py`: rewrite `canonical_json_bytes` to call `_normalize_payload` (move it out of `contracts.py` into a shared `_canonical.py` module, or have hashing import contracts). Add `allow_nan=False` to the `json.dumps` call. Output remains `sha256:<hex>`.

Acceptance: tests 1 and 2 turn green. Propstore consumers (`families/identity/claims.py`, `families/identity/concepts.py`, `artifact_codes.py`, `source/finalize.py`) get the same hash they got before for JSON-native inputs, and a meaningful hash (or a meaningful error) for `frozenset`/`Struct`/`NaN` inputs.

Cross-stream coordination: WS-N collapses propstore's three duplicate `_canonical_json` (`propstore/observatory.py:34`, `propstore/policies.py:42`, `propstore/epistemic_process.py:50`) onto whatever quire's hashing exports. WS-N must wait for this step or accept that the duplicates will re-diverge.

### Step 2 — Honest `expected_head` semantics

`quire/family_store.py`: rename `_check_preemptive_head` to `_advisory_head_check` OR introduce a real reservation token returned from a new `reserve_branch(branch, expected_head) -> Token` method that the subsequent `commit_batch` consumes. The cluster-S report leaves the design open; this WS picks the simpler rename + docstring path unless Q wants a real reservation.

Acceptance: test 3 turns green with the documented semantics.

### Step 3 — Orphan-blob hygiene

Two parts. First: change `_commit` to construct the full Tree and Commit objects in memory before adding blobs to the object store, OR write blobs to a staging area and only add to the durable store after CAS success. Dulwich's `MemoryObjectStore` can serve as the staging area with a final `add_pack` after CAS.

Second: add a `GitStore.gc(*, dry_run: bool = True) -> GcReport` method that walks reachability from all refs and reports orphans. Make it explicit (no auto-trigger on commit; that's a separate policy decision).

Acceptance: tests 4 and 5 turn green. Long-running propstore processes can run `pks repo gc --dry-run` and see the orphan count.

### Step 4 — Cross-process lock

`quire/git_store.py`: add a `filelock` (or stdlib `fcntl`/`msvcrt`) on a path under the bare repo's `.git/quire.lock`. Acquire it around the entire `_commit` flow (after the `expected_head` check, before blob writes). Release on success or any exception. Document multi-process safety in the README.

Acceptance: test 5 turns green for multi-process contention.

### Step 5 — Strict VersionId default

`quire/versions.py`: flip `allow_placeholder` default to `False`. Audit every call site in quire (and propstore via grep) for explicit `VersionId(...)` constructions; add `allow_placeholder=True` only where placeholders are genuinely intentional (e.g. seed data for tests).

Acceptance: test 6 turns green.

### Step 6 — Ambiguity-signaling reference resolution

`quire/references.py`: change `resolve_id` to return a `Resolution` value (or raise `AmbiguousReferenceError`); update `exists` to mean "exactly one canonical match." Provide a deprecated `resolve_id_legacy` only if propstore needs a transition path — but per Q's "no fallbacks" rule, prefer ripping it out and updating callers in the same PR.

Acceptance: test 7 turns green.

### Step 7 — ForeignKeySpec.required enforcement (or remove)

Two paths, pick one. (a) Implement runtime validation: `ReferenceIndex` consults the spec when resolving. (b) Remove `required` and `many` from `ForeignKeySpec` and document that FK enforcement is propstore's job.

Acceptance: test 8 turns green per the chosen path.

### Step 8 — `materialize_worktree` always refreshes the index

`quire/git_store.py:672`: make `materialize_worktree` call `_refresh_on_disk_index` unconditionally on real (non-memory) repos. If the split between `materialize_worktree` and `sync_worktree` was deliberate (e.g. for `remove_extra=False` use cases), document the deliberate choice and rename one of them so the unsafe variant has an unsafe-sounding name (`materialize_worktree_unsafe_no_index`).

Acceptance: test 9 turns green.

### Step 9 — HashScattered digest mode requires explicit index

`quire/artifacts.py:444`: in `__post_init__`, if `filename_mode == "digest"`, require an external `index_provider` parameter. The placement carries it; `iter_refs` consults it.

Acceptance: test 10 turns green.

### Step 10 — Split Placement Protocol

`quire/artifacts.py`: introduce `ScannablePlacement` Protocol containing `iter_refs`, `iter_artifacts`, `ref_from_locator`, `ref_from_loaded`. `FlatYamlPlacement`, `HashScatteredYamlPlacement(filename_mode="encoded_ref")`, `SingletonFilePlacement` implement it. `FixedFilePlacement` and `TemplateFilePlacement` do not. Generic iteration paths take `ScannablePlacement` not the union.

Acceptance: test 11 turns green; mypy/pyright reports no Liskov violation.

### Step 11 — `merge_base` uses dulwich native

`quire/git_store.py:553`: replace the quadratic body with `dulwich.graph.find_common_revisions` (or whatever the dulwich version pinned by quire exposes). Keep the `ancestor_distances` helper for callers who want it.

Acceptance: test 12 turns green.

### Step 12 — Public surface promotion

`quire/__init__.py`: promote `ArtifactFamily`, `FlatYamlPlacement`, `HashScatteredYamlPlacement`, `FixedFilePlacement`, `TemplateFilePlacement`, `SingletonFilePlacement`, `BranchPlacement`, `ContractManifest`, `check_contract_manifest`, `ContractManifestError`, `TreePath`, `FilesystemTreePath`, `GitTreePath`, `CrossFamilyReferenceIndex` into `__all__`. Equivalently: refactor propstore through a narrower facade. The first option is cheaper.

Acceptance: test 13 (propstore-side) turns green.

## Acceptance gates

Before declaring WS-O-qui done, ALL must hold:

- [x] Quire repo: every test in the "First failing tests" list above is green in `C:\Users\Q\code\quire\tests\`.
- [x] Quire repo: a new tagged release is cut (`v0.2.0`) with a CHANGELOG entry referencing this workstream.
- [x] Propstore: `pyproject.toml` updates the quire pin to the new release.
- [x] Propstore: full test suite under `scripts/run_logged_pytest.ps1` shows no NEW failures vs the baseline `logs/test-runs/pytest-20260426-154852.log`.
- [x] Propstore: `pyright propstore` passes.
- [x] Propstore: `lint-imports` passes (no contract changes expected from this WS, but the boundary promotion in step 12 may surface unintended new public-surface dependencies).
- [x] Propstore: `tests/test_quire_boundary.py` (test 13) passes.
- [x] `docs/gaps.md` (propstore-side): WS-O-qui rows for S-H1 through S-M7 plus S-Boundary all flipped to closed with the quire commit SHAs cited.
- [x] WS-N can now safely import the unified canonicalization from `quire.hashing`.
- [x] `reviews/2026-04-26-claude/workstreams/WS-O-qui-quire.md` STATUS line is `CLOSED <quire_release_tag> / <propstore_pin_commit_sha>`.

Closure evidence:

- Quire release: pushed `ctoth/quire` `master` and tag `v0.2.0`, both at `23bbac27e83fef8c69817c945c8ba72b3941be83`.
- Quire full suite: `uv run pytest -q` in `C:\Users\Q\code\quire` passed `207 passed`.
- Propstore pin: commit `a27b3cbc`; `pyproject.toml` and `uv.lock` both resolve to `git+https://github.com/ctoth/quire@23bbac27e83fef8c69817c945c8ba72b3941be83`.
- Propstore boundary test: `logs/test-runs/quire-boundary-20260428-011134.log`, `1 passed`.
- Propstore static gates: `uv run pyright propstore` passed; `uv run lint-imports` passed with 4 kept contracts.
- Propstore full suite: `logs/test-runs/WS-O-qui-full-20260428-011234.log`, `3031 passed`.

## Done means done

This workstream is done when **every Cluster S HIGH and MED is closed in quire**, the propstore pin is updated, AND propstore's full suite is at-or-better-than-baseline. Specifically:

- S-H1 through S-H5 (5 HIGH): each has a green test in quire.
- S-M1 through S-M7 (7 MED): each has a green test in quire.
- S-Boundary: propstore-side test (`tests/test_quire_boundary.py`) passes — every cross-package `from quire.<sub> import <name>` resolves to a name in `quire.<sub>.__all__` or `quire.__init__.__all__`.
- WS-N can now collapse the three duplicate `_canonical_json` implementations onto `quire.hashing.canonical_json_bytes` without re-introducing divergence.

If any one of those is not true, WS-O-qui stays OPEN. No "we'll get to the placement Liskov split later" — either it's in scope and closed, or it's explicitly deferred to a successor WS in *this* file before declaring done.

## Papers / specs referenced

Quire is paper-adjacent infrastructure. Cluster S's analysis section "Paper-faithful coverage" already noted: quire is *substrate*, not paper-faithful itself. The relevant papers (all on disk; `papers/<dir>/notes.md` confirmed):

- `papers/Carroll_2005_NamedGraphsProvenanceTrust/notes.md` — Named Graphs / provenance / trust. Quire's git notes (`write_note`/`read_note`) are the obvious "named-graph annotation" hook. There is no first-class named-graph quotation; quire stores opaque blobs by SHA. The Liskov split (Step 10) and the boundary promotion (Step 12) make it cleaner for propstore to layer Carroll's structure on top of quire — quire shouldn't try to implement it itself.
- `papers/Buneman_2001_CharacterizationDataProvenance/notes.md` — which/where/why provenance characterization. Quire has commit history (which-provenance) and ref-keyed branches (where-provenance) but no why-provenance; quire's job is the substrate, not the trace. No quire-side fix needed.
- `papers/Kuhn_2014_TrustyURIs/notes.md` — Trusty URIs Type FA1/RA1/RB1. `canonical_json_sha256` returns `sha256:<hex>`. This **resembles** Type FA1 (file-content hash) but does not implement Type RA1/RB1 (RDF graph hash with URI replacement) and does not use the documented `RAhQT…` prefix scheme. Step 1 of this workstream does NOT add Trusty URI compliance; it only fixes the *internal* divergence between `canonical_json_sha256` and `_normalize_payload`. The Trusty URI question is deferred to WS-M (`reviews/2026-04-26-claude/workstreams/WS-M-provenance.md`), per REMEDIATION-PLAN.md Tier 4.2. Open for Q: should propstore docs that imply Trusty-URI compatibility be corrected?
- `papers/Kuhn_2015_DigitalArtifactsVerifiable/notes.md` — successor to Kuhn 2014; same disposition.
- `papers/Kuhn_2017_ReliableGranularReferences/notes.md` — granular references would be the family/ref system. `RefName` validation is solid. Placements implement granular addressing `(branch, path)` per ref. But no signed nanopublication chain, no provenance graph attached to each granular ref. That story is propstore's argumentation/source layer, not quire's.

This workstream does not implement any of those papers. It implements the quire substrate that WS-M will eventually layer them onto. The fix here is not "make quire paper-faithful," it is "make quire's substrate honest about what it is" — collapse the canonicalization divergence, fix the orphan-on-failure path, document the worktree footgun, plug the alias-shadow ambiguity hole.

## Cross-stream notes

- **WS-N (Architecture)** depends on WS-O-qui Step 1: propstore's three duplicate `_canonical_json` implementations collapse onto `quire.hashing` only after this WS unifies quire's two paths. If WS-N runs first, it picks one of the diverged paths and propagates the wrong one into propstore.
- **WS-J (Worldline / hashing)** depends on the same Step 1: the "strict canonical JSON, no `default=str`" requirement in WS-J's "Done means" can only be satisfied if quire's hash is itself strict. WS-J should reference the quire commit SHA in its PR.
- **WS-M (Provenance / Trusty URI)** is downstream of this WS. Trusty URI verification (REMEDIATION-PLAN T4.2) requires that `canonical_json_sha256` either (a) is honestly named "stable JSON SHA-256" and not claimed as Trusty-URI-compatible, or (b) is replaced by a real Trusty URI Type RA1 implementation. Either resolution lives in WS-M, not here.
- **WS-A (Schema fidelity)** does NOT depend on this WS and this WS does not depend on WS-A — they are independent. Per REMEDIATION-PLAN: "WS-O-{arg,gun,qui,bri,ast} can run in parallel with WS-A."

## What this WS does NOT do

- Does NOT implement Trusty URI compliance — that's WS-M.
- Does NOT add a PROV-O serializer — that's WS-M.
- Does NOT change propstore's three duplicate `_canonical_json` files — that's WS-N (this WS only makes the unification *possible*).
- Does NOT add propstore-side render-policy enforcement — that's WS-B.
- Does NOT touch quire's `MemoryRepo` semantics property tests — out of scope; if cluster S's note about untested memory-CAS contention turns out to be a real bug, file a follow-on inside the quire repo.
- Does NOT address the LOW findings (S-L1 through S-L11 in cluster-S-quire.md). Those are deferred to a successor quire workstream OR to "won't fix" status. Per Q's discipline: "Either it's in scope and closed, or it's explicitly removed from this WS in this file (and moved to a successor WS) before declaring done." LOWs are explicitly out of scope here.

## Open questions for Q (carried forward from cluster-S)

These are the cluster-S "Open questions for Q" that this workstream does not silently answer:

1. Should `materialize_worktree` *always* refresh the index, or is the split deliberate? (Step 8 picks "always refresh" with a renamed unsafe variant; Q can override.)
2. Is multi-process write to the same on-disk repo a supported use case? (Step 4 assumes yes and adds a flock; if no, document and skip Step 4.)
3. `VersionId(allow_placeholder=True)` as default — flip? (Step 5 flips it. Q can override.)
4. `ReferenceIndex.resolve_id` — raise on ambiguity, or sentinel value? (Step 6 picks raise; Q can override.)
5. `ForeignKeySpec.required` — enforce in quire or remove? (Step 7 leaves the choice open; pick one.)
6. Trusty URI claim — do propstore docs imply compatibility today? If so, that's a docs fix in WS-M; if not, no action.

These questions are answered in this WS only by the choices encoded in Steps 1-12. Q can reverse any of them by amending this file before any commit lands.
