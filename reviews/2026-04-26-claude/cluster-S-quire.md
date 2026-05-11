# Cluster S: quire dependency (git-backed artifact store)

## Scope and purpose

Quire is a separately-versioned package at `C:\Users\Q\code\quire\` (`pyproject.toml` v0.1.1; deps: `dulwich>=1.1.0`, `msgspec>=0.19.0`, `pyyaml>=6.0`). It is propstore's substrate: a typed, schema-aware document store implemented as a thin layer over git plumbing via `dulwich`, with no working tree by default.

What it provides (verified by `quire/__init__.py:1-41` and the per-module reads):

- `GitStore` — bare object-store / refs / notes / branches / merge-base operations.
- `RefName`, `NotesRef`, `VersionId` — validated newtypes.
- `ArtifactFamily` and placement policies (`FlatYamlPlacement`, `HashScatteredYamlPlacement`, `FixedFilePlacement`, `TemplateFilePlacement`, `SingletonFilePlacement`) — pluggable `(branch, path)` codecs.
- `FamilyRegistry` / `BoundFamilyRegistry` / `BoundFamily` — duplicate-key/name/accessor checked groupings with attribute-style access.
- `DocumentFamilyStore` and `DocumentFamilyTransaction` — load/save/move/delete plus batched `commit_batch` transactions.
- `ContractManifest` and `check_contract_manifest` — drift detection on persisted ABI.
- `ReferenceIndex` / `CrossFamilyReferenceIndex` / `ForeignKeySpec` — cross-family lookups with ambiguity reporting.
- `documents` subpackage — msgspec YAML codec, `DocumentStruct` base, `LoadedDocument`, `load_document_dir`.
- `tree_path` — abstract `TreePath` with filesystem and git-backed implementations.
- `hashing.canonical_json_sha256` — deterministic JSON hash helper.

Confirmed boundary contract used by propstore (Grep results):
- `from quire.artifacts import ArtifactFamily, …` (propstore/families/registry.py:10), `from quire.families import FamilyDefinition, FamilyIdentityPolicy, FamilyRegistry` (registry.py:19), `from quire.documents import …` (many), `from quire.references import ForeignKeySpec, …` (compiler/references.py:9, contracts.py:11), `from quire.refs import RefName, single_field_ref_type, singleton_ref_type` (concept_ids.py:13, families/registry.py:32), `from quire.versions import VersionId` (registry.py:33, contracts.py:12), `from quire.hashing import canonical_json_sha256` (artifact_codes.py:10, families/identity/claims.py:8, families/identity/concepts.py:8, source/finalize.py:6), `from quire.git_store import GitStore` (concept_ids.py:16; tests reference `GitStore` directly), `from quire.tree_path import …` (compiler/context.py:11, families/forms/__init__.py:14, world/model.py:36, etc.).

Direct mutator usage from propstore: `repo.git.commit_files(...)`, `repo.git.commit_batch(...)`, `kr.store_blob(...)`, `kr.commit_flat_tree(...)` (e.g. `propstore/merge/merge_commit.py:152`–154; `propstore/app/project_init.py:47`; tests/test_import_repo.py and tests/test_cli.py many places).

So: every persistence path in propstore terminates in quire. Propstore exposes `repo.git` which is a `GitStore`.

## Architecture overview

Layering, observed:

- `git_store.py` (1157 lines) — sole interaction surface with dulwich `BaseRepo`. Holds a `threading.RLock` (`_mutation_lock`) plus an `OrderedDict` LRU `_object_cache` (cap 8192). Every mutation goes through `_commit` (`git_store.py:790-856`) which builds a tree via `_apply_tree_changes` and uses `refs.set_if_equals` for CAS update.
- `refs.py`, `notes.py`, `versions.py` — small validated newtypes; `VersionId` enforces calendar `YYYY.MM.DD` only when `allow_placeholder=False`.
- `tree_path.py` — `TreePath` Protocol + filesystem and git-backed implementations (`FilesystemTreePath`, `GitTreePath`).
- `hashing.py` — 20 lines, just `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=False)` then sha256.
- `references.py` — pure data structures, no IO. `ReferenceIndex.resolve_id` returns single match or `None`.
- `contracts.py` — `ContractManifest` + `check_contract_manifest` raises on body change without bump or marker.
- `artifacts.py` (783 lines) — `ArtifactFamily` and the five placement policies; ref codecs.
- `family_store.py` — orchestration over a `DocumentStoreBackend` Protocol. Default codec is `DEFAULT_DOCUMENT_CODEC` (msgspec YAML, see `documents/codecs.py:167`).
- `families.py` — typed grouping + `BoundFamily.__getattr__` accessor surface.
- `documents/{schema,codecs,loaded}.py` — msgspec-strict YAML decoding with `forbid_unknown_fields=True`.

Dependencies are one-way: `git_store → notes/refs/tree_path`; `family_store → artifacts → versions`; `families → artifacts + family_store + contracts + references + versions`. No upward reference. Clean.

## Hashing / content-address stability

`canonical_json_bytes` (`hashing.py:8-15`) — `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`.

Stability concerns I observed:

1. **`ensure_ascii=False` plus Unicode normalization not applied.** Two semantically equal strings differing only in NFC vs NFD form will hash differently. Hashing identifiers from heterogeneous sources (file paths, OWL labels) without normalization is a silent collision/divergence risk at the boundary. (`hashing.py:13`)
2. **No type discipline on input.** `Any` payload — passing a `tuple` vs `list` will raise `TypeError` from `json.dumps` only if non-JSON; passing a dict with non-string keys raises late. The contracts module has its own `_normalize_payload` (`contracts.py:235-258`) that normalizes sets/tuples/structs. **Inconsistency:** `canonical_json_sha256` does not use `_normalize_payload`. Two callers can produce different hashes for the same logical payload depending on whether they pre-normalize. Propstore consumers (`families/identity/claims.py:71`, `families/identity/concepts.py:62`) feed it whatever `canonicalize_*_for_version` returns; if either function ever yields a `frozenset` or `tuple`, the hash is fragile.
3. **Floats round-trip.** `json.dumps` formatting of floats is platform-dependent in edge cases; `NaN`/`Inf` would be serialized as `NaN`/`Infinity` (non-strict JSON). Hashing should set `allow_nan=False` — the contracts sort key does (`contracts.py:262-268`), but `hashing.py` does not. Discrepancy.
4. **No version/algorithm tag in the hash beyond `sha256:` prefix.** If the canonicalization rule ever changes, every persisted hash silently invalidates without a way to detect old vs new. There is no `format_version` field in the hash output.

## Git transaction discipline

Lock contention and atomicity:

1. **In-process RLock only.** `_mutation_lock = threading.RLock()` (`git_store.py:142`) protects within-process. There is **no on-disk lock file**. Two `GitStore` instances pointing at the same on-disk repo (e.g. parallel processes, or two `GitStore.open(root)` in the same process for the same path) race at the dulwich-refs layer. The CAS via `set_if_equals` saves correctness *for the ref update itself* — but the staged Blob/Tree objects are written to the object store *before* the CAS at `_commit` (`git_store.py:817-845`). On a stale CAS, the loose objects remain orphaned. Repeated failures grow garbage.
2. **Multi-file commit atomicity.** Adds and deletes in `commit_batch` materialize one `Tree`, one `Commit`, then one `set_if_equals` (`git_store.py:847`). Atomic at the ref update — good. But if `_apply_tree_changes` itself raises mid-way, partial blobs were already added to `object_store` (line 819-820 add blobs before tree construction). Object store writes are not transactional; nothing rolls them back. This is benign for git semantics (orphan objects) but means content is exposed by SHA before the commit "exists".
3. **`expected_head` semantics.** `_commit` reads `tip_sha` once (`git_store.py:801`) and validates `expected_head` against it (`802-808`). It then passes that same `tip_sha` to `set_if_equals` (`847`). **Bug-like behavior:** between the read and the CAS, the ref *can* change; the CAS will fail and raise (`851`). Good. But the test `_check_preemptive_head` in `family_store.py:450-461` does an *additional* read before the transaction — this is purely advisory: a successful preemptive read does not pin anything, and the actual CAS still races. The naming "expected_head" suggests a reservation; it is only an opportunistic check. Semantics are honest if you read the code, but easy to misuse.
4. **`commit_flat_tree` does not check `expected_head` consistently with `_commit`.** It reads `current_head` once (`git_store.py:349`), CAS at line 383. Same race window. OK.
5. **No fsync / packing strategy.** `dulwich.Repo` writes loose objects. If host crashes mid-commit, recovery relies on dulwich/git's loose-object semantics. Not quire's bug; worth noting.
6. **Note writes do not respect `_mutation_lock` for read paths.** `read_note` (`git_store.py:636-637`) is unlocked but reads through dulwich; harmless because reads are immutable. But `write_note` / `delete_note` lock the quire mutex; the underlying dulwich `Notes.set_note` itself takes its own commit on the notes ref — no integration with `expected_head`. A racing note writer can clobber concurrent writes (the dulwich Notes API uses last-writer-wins inside its own commit chain).
7. **`MemoryRepo` semantics.** Object cache is shared across threads, OK with RLock. But note that `MemoryRepo`'s ref backend may not support `set_if_equals` semantics identically — worth a property test (none observed in `test_git_properties.py` for memory CAS contention).

Cluster A's flag about `cached_property` git lock-in: searching `propstore` for `cached_property|@property\s*\n\s*def\s+git` returned no matches — that flag is in propstore code I did not have to review here. Not a quire issue per se.

## Reference & version semantics

Versions:

- `VersionId(value, allow_placeholder=True)` — calendar version `YYYY.MM.DD` is enforced *only* when `allow_placeholder=False` (`versions.py:21-25`). When `allow_placeholder=True` (the default), arbitrary non-empty strings pass. **Concrete consequence:** `ContractEntry.from_payload` and `CompatibilityMarker.from_payload` use `allow_placeholder=False` (`contracts.py:44, 67`), but plain `VersionId("foo")` calls elsewhere accept anything. This split is footgun-shaped: nothing prevents a developer from instantiating a non-calendar version, and the contract layer rejects it only on round-trip through YAML. (`families.py` `_require_version` only checks isinstance, not `allow_placeholder=False`.)
- `__lt__` is calendar-only (`versions.py:27-30`). Comparing two placeholder `VersionId("0")` instances raises `ValueError` from `_parse_calendar_version`. Sorting a mix of placeholder and calendar versions raises midway.
- **No monotonicity check.** Nothing prevents bumping from `2026.04.18` to `2025.01.01` (going backwards). `check_contract_manifest` only checks that *something changed*, not direction.
- **No gap detection.** Quire has no notion of "previous version" beyond what's in the persisted manifest; you can skip versions arbitrarily. That's by design (calendar versions are intentionally non-monotonic by version *number*).
- **No rollback story.** `revert_commit` (`git_store.py:470-537`) generates a forward commit that undoes a target commit. It refuses if the target's paths have been touched since (`520`). This is per-commit, not per-version. There is no `VersionId`-level rollback.

References:

- `ReferenceIndex.resolve_id` (`references.py:96-104`) returns the unique candidate or `None` (silently swallows ambiguity). Callers must call `.resolve()` to discover ambiguity. Footgun: silent `None` on ambiguity is indistinguishable from "not found". Good test in `references.py` would catch this; haven't verified callers.
- **Dangling references.** `ReferenceIndex` has *no concept* of dangling — `exists()` only confirms the lookup table contains the key. Quire does not enforce FK integrity; that is propstore's job. `ForeignKeySpec.required` is metadata only — quire never validates it. This is a contract leak: declaring `required=True` does nothing at the quire layer.
- **`build_reference_lookup`** (`references.py:73-87`) collapses all `key → target_id` entries: if two records claim the same alias, both are appended. `resolve_id` returns `None` if `len(candidates) != 1`. **No warning** is emitted; ambiguity is silent unless the caller uses `.resolve()`.

Refs:

- `RefName` validation (`refs.py:11-34`) is reasonable: rejects empty parts, `..`, `@{`, `~^:?*[`, `.lock` suffix, control chars. Does not enforce git's full ref-format rules — e.g. `refs/foo.lock` is rejected, but a *component* containing `.lock` mid-name (`refs/foo.locker`) is allowed; git rejects only path components ending in `.lock`. The check uses `endswith(".lock")` per component, so this is correct. Minor: the docstring is missing.
- **No length cap.** Some filesystems cap path length; ref names that produce long file paths (e.g. `_branch_meta_ref` URL-quoting a long branch name at `git_store.py:124`) can exceed Windows 260-char limits when materialized. Not checked.

## Boundary with propstore (where it consumes quire)

The boundary is wide. Categorized usage:

1. **Storage write surface (mutation):** `repo.git.commit_files` / `commit_batch` / `commit_flat_tree` / `store_blob` / `write_blob_ref` / `write_note`. Used in `propstore/app/project_init.py:47`, `propstore/merge/merge_commit.py:152-154`, scripts/mergeability_probe*.py, many tests.
2. **Storage read surface:** `repo.git.read_file`, `branch_sha`, `flat_tree_entries`, `iter_subtree_files`, `iter_dir_entries`, `head_sha`, `commit_parent_shas`, `merge_base`, `ancestor_distances`. Used by `propstore/storage/snapshot.py`, `propstore/storage/git_policy.py`.
3. **Family/contract surface:** `from quire.artifacts import ArtifactFamily, FlatYamlPlacement, BranchPlacement, …`; `FamilyDefinition`, `FamilyRegistry`. Heavy use in `propstore/families/registry.py:643+` (the master family registry, ~30+ FamilyDefinitions).
4. **Identity/canonicalization:** `from quire.hashing import canonical_json_sha256` in `propstore/families/identity/{claims,concepts}.py`, `propstore/artifact_codes.py`, `propstore/source/finalize.py`. **Note:** propstore has *its own* duplicate `_canonical_json` implementations in `propstore/observatory.py:34`, `propstore/policies.py:42`, `propstore/epistemic_process.py:50`. These do not import from `quire.hashing`. Drift risk: if quire's canonicalization changes, propstore's local copies will not. (Potential bug source.)
5. **Schema surface:** `from quire.documents import DocumentStruct, DocumentSchemaError, decode_document_path, load_document_dir, convert_document_value, encode_document, decode_yaml_mapping, …` — used in roughly every `propstore/families/**/documents.py`.
6. **TreePath surface:** Aliased as `KnowledgePath` in many places (`compiler/context.py:11`, `families/forms/__init__.py:14`, `world/model.py:36`). Quire owns the abstraction; propstore renames at import site.
7. **Refs:** `RefName`, `single_field_ref_type`, `singleton_ref_type` used in `propstore/concept_ids.py:13` and `propstore/families/registry.py:32`.

The boundary is *not* re-exported through one module — propstore imports from many quire submodules. Refactors in quire that change submodule paths break propstore everywhere. There is no quire-side stability promise: `__init__.py` exports a small surface, but propstore reaches past it (e.g. `quire.artifacts.FlatYamlPlacement` is not in `__init__.__all__`). This is a coupling smell.

## Paper-faithful coverage

I did not have access to read papers from this subagent thread (scope was quire only; the paper paths were given as "probably"). Inferring from quire's surface:

- **Carroll 2005 Named Graphs / provenance / trust** — quire offers git notes (`write_note`/`read_note`) which are the obvious "named-graph annotation" hook. There is no first-class named-graph quotation — quire stores opaque blobs by SHA, not RDF. Propstore would need to layer this on top.
- **Buneman 2001 Characterization of Data Provenance** — quire has commit history (which-provenance) and ref-keyed branches (where-provenance). There is no why-provenance (which inputs caused this output) at quire's layer. Reasonable: that is the argumentation/source layer's job.
- **Kuhn 2014 Trusty URIs** — `canonical_json_sha256` returns `sha256:<hex>`. This *resembles* a Trusty URI Type FA1 (file-content hash) but does **not** implement Type RA1/RB1 (RDF graph hash with URI replacement) or Type FA1 with the documented prefix `RAhQT…`. Output is `sha256:<hex>`, not `RA1.<base64>`. Cannot claim Trusty-URI compatibility.
- **Kuhn 2017 Reliable Granular References** — granular references *would* be the family/ref system. `RefName` validation is solid; placements implement granular addressing `(branch, path)` per ref. But there is no signed nanopublication chain, no provenance graph attached to each granular ref, no introspection that says "this granular ref was derived from those granular refs". That story is propstore's argumentation layer, not quire.

So: quire is **paper-adjacent**, not paper-faithful. It provides the substrate; the paper-faithful layer is upstream. The README explicitly disavows this ("not a general-purpose ORM"; "not a git porcelain"). Fine — but anyone treating `canonical_json_sha256` as a Trusty URI is wrong.

## Bugs

### HIGH

1. **`canonical_json_sha256` does not normalize payload like `contracts._normalize_payload`** (`hashing.py:8` vs `contracts.py:235`). If callers pass `set`, `frozenset`, `tuple`, or `msgspec.Struct`, the contracts subsystem accepts them but the hashing subsystem will raise `TypeError`. Worse, callers who *manually* coerce sets to lists will get a different hash than callers who let contracts normalize. Two paths to "the same" canonical JSON exist.
2. **`canonical_json_sha256` does not set `allow_nan=False`** (`hashing.py:8-15`). NaN/Inf produce non-JSON output (`NaN`, `Infinity`) that is unparseable by other JSON consumers. Identity hashes silently pollute. Compare to `contracts._normalized_sort_key` at `contracts.py:262-268` which *does* set `allow_nan=False`. Inconsistency between two canonicalization paths in the same package.
3. **`expected_head` is best-effort, not pinned.** The "preemptive" check in `_check_preemptive_head` (`family_store.py:450-461`) reads the current head and compares — but does not *hold* anything. Any caller assuming this is a transactional reservation will hit lost updates under contention. Naming suggests stronger semantics than implemented. Document or rename.
4. **Loose-object orphan accumulation on CAS failure.** `_commit` adds blobs and trees to the object store *before* the ref CAS (`git_store.py:817-845`). If the CAS fails (lost race) or `_apply_tree_changes` raises, those objects remain. No GC trigger. Long-running write-heavy processes accumulate dead objects. Dulwich does not auto-pack/gc.
5. **Cross-process lock missing.** `_mutation_lock` is per-`GitStore`-instance. Two processes opening the same on-disk bare repo (e.g. via `GitStore.open(root)`) coordinate only through dulwich's ref CAS. There is no flock/file-lock guarding the higher-level `_commit` flow. Multi-process contention on the same repo is unsafe beyond what `set_if_equals` provides — for instance, two processes can both pass `expected_head` validation, both build trees, both attempt CAS, one will raise — but the loser's tree/blobs are now orphaned (see #4). Documented or unintentional?

### MED

6. **`VersionId` permits placeholders by default.** `__init__(value, *, allow_placeholder=True)` (`versions.py:17`). `_require_version` in `families.py:19-22` only checks `isinstance`, not the strict mode. Result: any `VersionId("0.1")` is accepted at family construction; only at YAML round-trip through `from_payload` will it fail. Drift between in-memory model and persisted form. Default should be `allow_placeholder=False` and explicit opt-in for placeholders.
7. **`ReferenceIndex.resolve_id` swallows ambiguity** (`references.py:96-104`). Returns `None` when `len(candidates) != 1`, indistinguishable from "not found". Callers must use `.resolve()` to detect. Default API is the lossy one. Bug-shaped UX.
8. **`ForeignKeySpec.required` and `many` are decorative.** Quire never enforces them. `references.py:36-52` only carries them in `contract_body()`. Anyone reading the type signature would expect runtime enforcement.
9. **`build_reference_lookup` mixes self-IDs and aliases without typing them** (`references.py:79-87`). The ID-as-key entry collapses with alias-as-key entries: a record `{id: "alpha", aliases: ["beta"]}` produces lookup `{"alpha": ("alpha",), "beta": ("alpha",)}`. If a *different* record has `id: "beta"`, it gets lookup `{"beta": ("beta", "alpha")}` — now `resolve_id("beta")` returns `None` (ambiguous), even though `"beta"` is unambiguously the canonical ID of one of them. The `if reference in self.records_by_id: return reference` fallback at `references.py:102` partially saves this — but it only triggers when the lookup did not resolve uniquely. Consequence: aliases shadow real IDs in some interleavings. Subtle.
10. **`LoadedDocument.document` is `cast(TDocument, document)` even when `document=None`** (`loaded.py:29`). `LoadedDocument(filename="x", source_path=None, document=None)` produces an object that *types* as `TDocument` but holds `None`. Type-system lie. If anything ever constructs a partial `LoadedDocument`, downstream `.document.field` access is a silent `AttributeError` on `None`.
11. **`HashScatteredYamlPlacement.iter_refs` requires `filename_mode == "encoded_ref"`** (`artifacts.py:470-471`). With `"digest"` mode (the default), refs are unrecoverable from disk and must be looked up via an external index. There is no enforcement that an external index *exists*; you can save documents you can never iterate. Footgun.
12. **`FixedFilePlacement` and `TemplateFilePlacement` raise `TypeError` on `iter_refs`/`iter_artifacts`/`ref_from_locator`/`ref_from_loaded`** (`artifacts.py:602-624`, `artifacts.py:646-678`). These violate Liskov: any caller iterating placements generically must special-case. The Protocol `ArtifactPlacementPolicy` declares the methods; the implementations all raise. Should be a separate Protocol for "scannable" placements vs "fixed" ones.
13. **`merge_base` uses a quadratic ancestor scan.** `ancestor_distances` walks all ancestors from each ancestor candidate (`git_store.py:569-572`) — `O(|common ancestors| × |total ancestors|)`. On a long history with merges this is slow. Dulwich provides `find_common_revisions`/`MergeBase` natively; not used.
14. **`materialize_worktree` writes files but does not refresh the on-disk index** unless `sync_worktree` is called (`git_store.py:692-694`). The docstring at `_refresh_on_disk_index` (`git_store.py:696-706`) explicitly calls out that without an index refresh, `git status` reports every tracked file as staged-for-deletion and a subsequent `git commit` would silently wipe the tree. The `materialize_worktree` (`git_store.py:672-690`) public entrypoint **does not** trigger the index refresh — only `sync_worktree` does. Anyone calling `materialize_worktree(remove_extra=False)` then running `git commit` from the shell loses data. The README implies `materialize_worktree` is the side-door API; it is footgun-shaped.
15. **Object cache is per-`GitStore`, not per-`object_store.id`.** Two `GitStore` objects pointing at the same on-disk repo have independent caches. After process A invalidates an object (it shouldn't — git is content-addressed — but dulwich packs can) process B's cache still holds the stale entry. Practically: the LRU is read-mostly; this is not a correctness bug today but it is fragile under repacks.

### LOW

16. **`_normalize_path` strips leading and trailing slashes but does not normalize `.` and `..` segments** (`git_store.py:40-44`). `commit_files({"a/../b/x": data})` does *not* collapse to `b/x`. Tree construction will literally create a child named `..`, which `RefName`-style validators would reject. Untested edge case.
17. **`GitTreePath.cache_key` returns `git-memory:HEAD:` for in-memory repos** (`tree_path.py:174-179`). Two distinct in-memory `GitStore` instances share the same `cache_key` for the same path. If anything memoizes by `cache_key`, it conflates them.
18. **`GitTreePath.is_dir`/`is_file` do mode-bit AND with `0o040000`/`0o100000`** (`tree_path.py:159, 163`). Symlink mode `0o120000` and gitlink/submodule `0o160000` are misclassified: symlink (`0o120000` = `0o100000 | 0o020000`) tests true on `is_file`. Edge but not benign.
19. **`MutexLocked` reentrancy: `_cached_object` acquires `_mutation_lock` then calls `_repo_object`** (`git_store.py:1090-1098`). Inside `_apply_tree_changes`, `_tree_at` calls `_cached_object` while already holding the lock. Works due to `RLock`. Performance: every cache hit serializes through one lock — heavy concurrent reads are lock-bottlenecked.
20. **`encoded_ref` filename mode + `slug`/`safe_slug` codec** rejected by `__post_init__` (`artifacts.py:448-449`) — good. But `address_for` in `digest` mode happily uses one-way codecs (`artifacts.py:451-460`). Consequence: with `codec="slug", filename_mode="digest"` you cannot recover the original ref string from anywhere.
21. **`commit_flat_tree` does not validate that `parents` are actually commit objects in the store.** Garbage parent SHAs produce a corrupt commit object that breaks `commit_parent_shas` later (`git_store.py:466-468`). Cheap to add an isinstance check.
22. **`_branch_meta_ref` URL-quotes branch names** (`git_store.py:124`). `refs/quire/branch-meta/<quoted>`. Ref names allow `/` in components; URL-quoting `feature/foo` to `feature%2Ffoo` works but produces a single component with `%`. Functional, but doubles the storage cost of every branch and is inconsistent with how dulwich stores `refs/heads/feature/foo` as a directory tree on disk. Slight.
23. **`yaml.safe_load` on `_read_branch_meta`** (`git_store.py:866`) — but the writer uses `json.dumps` (`git_store.py:435`). Mixing JSON write and YAML read is harmless because all valid JSON is valid YAML, but inconsistent. Use `json.loads`.
24. **`canonical_json_bytes` accepts arbitrary `Any` payload but raises late.** A bytes value, datetime, Decimal, etc. produces `TypeError` from inside `json.dumps`. No upfront validation. Compare to `contracts._normalize_payload` which whitelists.
25. **`DocumentFamilyTransaction.__exit__` only commits on no-exception path** (`family_store.py:392-394`) — correct — but never `rollback`s. Loose blobs added during `prepare()` are not committed but the blob objects are still in the dulwich object store (cf. HIGH #4). Repeated aborted transactions accumulate orphans.

## Missing features

- **No integrity check / fsck.** Quire never walks the object graph to confirm reachability. After CAS races (HIGH #4) the only recovery is `git gc`, which is not exposed.
- **No write-ahead log / two-phase commit.** Cross-branch atomic writes are impossible: each branch update is one CAS. Updating two branches "atomically" requires sequencing and accepting partial failure.
- **No repacking / GC controls.** `dulwich` exposes pack writers; quire does not.
- **No durable lock for cross-process safety.** As noted in HIGH #5.
- **No pluggable canonicalizer.** `hashing.py` is hardcoded to `json.dumps` config. Cannot inject Trusty URI–style RDF normalization.
- **No identity-policy enforcement at write time.** `FamilyIdentityPolicy` (`families.py:35-54`) declares functions by *name string*; nothing in quire dispatches them. They are pure metadata for contract bodies. Propstore must wire them up itself.
- **No version monotonicity check** even when `allow_placeholder=False`. As noted under "Versions".
- **No notes-as-graphs.** Notes accept opaque bytes. To encode `(commit, predicate, value)` annotations propstore must layer its own format on top.
- **No streaming `iter_artifacts`.** `iter_subtree_files` reads each blob into memory (`git_store.py:271`). For large blobs this is a memory cliff.
- **`merge_base` is the only graph-traversal primitive.** No three-way diff, no patience-style merge, no cherry-pick beyond `revert_commit`.
- **No tag refs.** `refs/tags/` is just a `RefName` like any other; no helpers.
- **No reflog / commit-message structured metadata.** Commit messages are opaque strings.
- **No transaction *names* / IDs.** `DocumentFamilyTransaction` has no client-supplied transaction id; if a crash occurs mid-batch you cannot resume by id.

## Open questions for Q

1. **Should `canonical_json_sha256` and `contracts._normalize_payload` share a single canonicalization?** They diverge today (HIGH #1, #2). Pick one. If hashing is meant to be Trusty-URI-faithful, neither is sufficient; if hashing is "just stable JSON", merge them.
2. **Is the CAS-orphan accumulation acceptable in propstore's lifetime, or do we need a quire-side GC hook?** (HIGH #4) Long-running propstore processes will leak.
3. **Is multi-process write to the same on-disk repo a supported use case?** (HIGH #5) If yes, quire needs a flock. If no, document it.
4. **Should `materialize_worktree` *always* refresh the index, or is the split between `materialize_worktree` and `sync_worktree` deliberate?** (MED #14) Today, calling the public-named method without `remove_extra=True` puts the worktree in a state where shell `git commit` will wipe data. That seems wrong.
5. **`VersionId(allow_placeholder=True)` as default — keep, or flip?** (MED #6). The README example calls `VersionId("2026.04.18", allow_placeholder=False)`; making that the default would push placeholder usage into explicit opt-in.
6. **Should `ReferenceIndex.resolve_id` raise on ambiguity instead of returning `None`?** (MED #7). Or add `resolve_id_strict`. Silent ambiguity is the cluster-A "PK collision" scent.
7. **Is propstore's reach into `quire.artifacts.FlatYamlPlacement`, etc., past `quire/__init__.py`'s `__all__` intentional?** Either add them to the public surface or refactor propstore through a narrower facade.
8. **Identity policy — should quire dispatch `artifact_id_function`/`version_id_function` by name** (e.g. via a registry) or remain pure metadata? Currently it is decorative at the quire layer (#missing-features), which makes contract validation about identity hashing impossible without custom propstore wiring.
9. **Trusty URI claim?** `canonical_json_sha256` returns `sha256:<hex>`. If propstore docs imply this is Trusty-URI compatible, the claim is wrong (paper-faithful section). If not, no action.
10. **Cluster A flagged "sidecar PK collision" — does that map to MED #9 (alias/ID shadowing) here, or is it about something propstore-side I did not see?** Worth cross-checking with cluster A's specific flag.
11. **Notes write semantics (last-writer-wins via dulwich's notes commit chain) — acceptable, or do we need CAS on notes too?** Today `write_note` does not honor `expected_head`-style guarding.
12. **`_object_cache` is hard-coded `_OBJECT_CACHE_LIMIT = 8192`.** For repos with many large blobs this thrashes; for small repos it overcommits memory. Configurable via `GitStorePolicy`?

---

File references cited (all absolute):
- `C:\Users\Q\code\quire\quire\__init__.py`
- `C:\Users\Q\code\quire\quire\hashing.py`
- `C:\Users\Q\code\quire\quire\versions.py`
- `C:\Users\Q\code\quire\quire\refs.py`
- `C:\Users\Q\code\quire\quire\notes.py`
- `C:\Users\Q\code\quire\quire\tree_path.py`
- `C:\Users\Q\code\quire\quire\references.py`
- `C:\Users\Q\code\quire\quire\contracts.py`
- `C:\Users\Q\code\quire\quire\git_store.py`
- `C:\Users\Q\code\quire\quire\artifacts.py`
- `C:\Users\Q\code\quire\quire\family_store.py`
- `C:\Users\Q\code\quire\quire\families.py`
- `C:\Users\Q\code\quire\quire\documents\__init__.py`
- `C:\Users\Q\code\quire\quire\documents\codecs.py`
- `C:\Users\Q\code\quire\quire\documents\schema.py`
- `C:\Users\Q\code\quire\quire\documents\loaded.py`
- `C:\Users\Q\code\quire\pyproject.toml`
- `C:\Users\Q\code\quire\README.md`
- `C:\Users\Q\code\quire\tests\test_git_store.py`
- `C:\Users\Q\code\quire\tests\test_git_properties.py`
- `C:\Users\Q\code\propstore\propstore\families\registry.py` (boundary consumer)
- `C:\Users\Q\code\propstore\propstore\merge\merge_commit.py:152-154` (boundary consumer)
- `C:\Users\Q\code\propstore\propstore\app\project_init.py:47` (boundary consumer)
- `C:\Users\Q\code\propstore\propstore\families\identity\claims.py`, `concepts.py` (canonical-hash boundary)
- `C:\Users\Q\code\propstore\propstore\observatory.py:34`, `policies.py:42`, `epistemic_process.py:50` (duplicate canonicalization in propstore — drift risk)
