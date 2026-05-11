# Cluster A: core, storage, source

## Scope
Read in full:
- `propstore/storage/{__init__,git_policy,snapshot,repository_import}.py`
- `propstore/source/{__init__,alignment,claims,common,concepts,finalize,passes,promote,registry,relations,stages,status}.py`
- `propstore/repository.py`
- `propstore/uri.py`, `propstore/concept_ids.py`, `propstore/artifact_codes.py`, `propstore/resources.py`
- `propstore/core/{__init__,claim_types,claim_values,graph_types,id_types,justifications,labels,literal_keys,micropublications,results,store_results,base_rates,environment,source_types,claim_concept_link_roles}.py`
- `propstore/core/conditions/{__init__,ir,cel_frontend,checked,python_backend,sql_backend,z3_backend}.py`
- `propstore/core/relations/kernel.py`
- `propstore/core/assertions/{codec,refs,situated}.py`
- `propstore/core/lemon/{__init__,types}.py`
- `docs/data-model.md`, `.importlinter`

Skimmed only: remaining lemon/, conditions/estree_backend, the smaller core modules (activation, active_claims, algorithm_stage, aliases, analyzers, anytime, embeddings, exactness_types, graph_build, graph_relation_types, relation_types, row_types). They appear to be enum/dataclass shells; explicit findings flagged below where I noticed something while reading callers.

## Bugs

### HIGH

- **`propstore/source/promote.py:711-727`** — Justification filter is broken in two ways. The condition `conclusion not in valid_artifact_ids and not source_claim_index.has_artifact(conclusion)` ADMITS a justification whose conclusion is in the source-branch claim index (e.g. an earlier batch on the same branch) but NOT in this batch's `valid_artifact_ids`. That justification is then promoted to master with a `conclusion` reference that may never land on master (it is on the source branch only). Same bug for premises (line 721-725). The corresponding stance loop at line 690 correctly requires `source_claim in valid_artifact_ids`; the justification handling is inconsistent. Result: dangling cross-branch references on master.

- **`propstore/source/promote.py:840-851` + `:518-548`** — Sidecar mirror writes happen BEFORE the git transaction, with the comment acknowledging a window where sidecar can lead git. If `repo.families.transact(...)` raises (concept collision, ref name issue, anything in `quire.family_store`), the sidecar persists `claim_core` rows with `promotion_status='blocked'` PK'd on `artifact_id`. The next successful retry of the same source promotion will INSERT into `claim_core` for the same artifact_id during sidecar build, colliding with the orphaned blocked row. The blocked-write path at line 508 deletes by id without scoping by branch (the comment on lines 481-510 documents the prior PK-collision bug but the new write path inherits the same single-id PK). Net effect: a failed promote can poison subsequent successful ones.

- **`propstore/source/alignment.py:96-98`** — `if left_entry.references == right_entry.references: return "non_attack"` is followed by an unconditional `return "non_attack"`. The conditional is dead. More importantly, `classify_relation` returns `"non_attack"` by default for the typical case (different lexical identity, different ontology references). The alignment AF therefore credulously accepts every alternative by default. The ONLY paths that produce `"attack"` are: same lexical-entry identity AND different definitions (line 93), or same lexical-form identity AND different definitions (line 95). Two papers proposing two different concept names with conflicting definitions never produce an attack. The point of the alignment AF is to surface conflicts; defaulting to non-attack defeats it.

- **`propstore/source/registry.py:42-47`** — `handle_to_artifact.setdefault(alias_name, artifact_id)` silently keeps the FIRST artifact_id for any clashing alias. Two distinct concepts that share an alias name lose disambiguation: during source promotion the second concept's entries are silently rewritten into the first concept's artifact_id (via `concept_map`). Direct violation of "preserve disagreement". No error, no warning.

- **`propstore/source/finalize.py:213-217`** — Micropublications are silently skipped if `claim.context` is unset or empty (`continue` at line 59-60 of `_compose_source_micropubs`). Promotion of those claims still proceeds through the rest of the pipeline. A claim that lands on master with no micropub is now invisible to micropub-driven render. Per data-model.md every claim is supposed to have a context; if it doesn't, this should be a finalize error, not a silent drop.

- **`propstore/uri.py:19-22`** — `tag_uri(authority, kind, specific)` normalizes `kind` and `specific` but NOT `authority`. The default authority `"local@propstore,2026"` happens to be valid (RFC 4151 disagrees on this format but it parses), but user-supplied authorities from `propstore.yaml` are passed through unsanitized into URIs. An authority containing `/`, `:`, whitespace, or non-ASCII characters yields a malformed tag URI that downstream identity comparisons will treat as canonical. No validation anywhere in `Repository.uri_authority`.

### MED

- **`propstore/source/promote.py:692`** — `resolver.target_is_known(stance.target)` is called with `stance.target` directly. The earlier guard at line 686 only checks `source_claim`, not `target`. If `stance.target` is None or a non-string, the call may crash or return falsely. Compare to `finalize.py:140-142` which DOES guard `target` correctly.

- **`propstore/source/finalize.py:244`** — `transaction.commit_sha is None` is checked AFTER the `with` block exit; the access of `transaction.commit_sha` outside the `with` depends on the family-store transaction object retaining state after `__exit__`. Same pattern at `promote.py:887-889` and `repository_import.py:147-149`. If `transact()` clears commit_sha on exit (common pattern), all three sites silently succeed-with-None.

- **`propstore/source/claims.py:237`, `relations.py:78`, `relations.py:137`** — `datetime.utcnow()` is deprecated in Python 3.12+. Produces a naive datetime and manually appends `Z`. If the runtime ever switches to `datetime.now()` (no tz), the result will silently become host-local time with a misleading `Z` suffix.

- **`propstore/source/passes.py:213`** — `payload.setdefault("status", "accepted")` during concept import. Per data-model.md the status lifecycle is `proposed -> accepted -> deprecated`. Defaulting imports to "accepted" collapses the proposal stage and treats every imported KB row as truth. Direct violation of "imports are opinions". Should default to `proposed` so the operator must explicitly accept.

- **`propstore/source/passes.py:255-258`** — Local-handle collision warning fires for any duplicated `local_id`, regardless of whether stance files reference the colliding handle. Warnings are stored in `state.warnings` and surfaced through `SourceImportNormalizedWrites.warnings`, but `commit_repository_import` (in `repository_import.py:122-159`) does not raise on warnings — it only reads them at plan time and never re-checks them at commit time. Silent partial mis-mapping risk.

- **`propstore/source/passes.py:81`** — `_claim_source_from_import_path(path)` falls back to `Path(path).stem`. For a path like `"claims/.yaml"` the stem is `""`, producing an empty `paper` value with no validation.

- **`propstore/source/promote.py:744-758`** — In-place mutation pattern: pulls dicts out of `promoted_claims_doc.get("claims")` and calls `claim.clear()` then `claim.update(normalized_claim)`. If `attach_source_artifact_codes` returns dicts that share references with anything else (cached input, transaction state, the original `promoted_claims_doc`), the mutation leaks. Rebuild the list instead.

- **`propstore/source/concepts.py:45-48`** — `primary_branch_concept_match(repo, local_name)` and `(repo, proposed_name)` each issue an O(N) full registry load via `load_primary_branch_concepts(repo)` (which iterates all concept handles). Quadratic in the number of concept entries on every import; for a 1000-entry batch on a 5000-entry registry this is 10 million iterations.

- **`propstore/storage/snapshot.py:228-266`** — `_clean_materialized_semantic_files` uses `rglob("*")` while concurrently calling `disk_file.unlink()`. On Windows, this can produce skipped or duplicated entries. Then `prune_candidates` is iterated with `directory.rmdir()` which fails silently on `OSError`; if a temporary file is created in a now-empty dir between scan and rmdir, the dir survives.

- **`propstore/core/graph_types.py:197`** — `coerce_claim_type(self.claim_type)` can return `None` (per `claim_types.py:28-31` it returns None when value is None). The `claim_type: ClaimType` annotation says non-optional; `__post_init__` will silently set it to None. The class invariant is broken if anyone constructs `ClaimNode(claim_type=None)`.

- **`propstore/core/claim_types.py:28-31`** — `coerce_claim_type` raises `ValueError` on unknown string values rather than falling through to `ClaimType.UNKNOWN`. The presence of an `UNKNOWN` sentinel suggests it should be the fallback. Inconsistent with `coerce_source_kind` which gives a helpful error message.

- **`propstore/core/source_types.py:6-8`** — `SourceKind` only has `ACADEMIC_PAPER`. Per the README and project context, propstore is supposed to ingest various source kinds (books, datasets, web pages) — but the enum admits only one. Anything else raises in `coerce_source_kind`. This is either a missing feature or aggressively undocumented.

- **`propstore/repository.py:84-90`** — `git` is `cached_property`; calling code that catches an exception and retries cannot recover because the property is cached. If `is_git_repo(...)` flips to True after the first cache (e.g., repo init in the same process) the cached None persists.

- **`propstore/artifact_codes.py:262-271`** — `verify_claim_tree` passes `source_code=source_actual or ""` but `attach_source_artifact_codes` always uses the real source_code (never empty). Verify can mismatch even if data is correct, when `sources_by_slug.get(source_slug, {})` returned empty (i.e. source missing from sidecar). The mismatch then propagates `overall_status = "mismatch"` even though the claim is internally consistent.

- **`propstore/artifact_codes.py:114`** — `claim_id = rewritten.get("artifact_id")` then `justification_codes_by_conclusion.get(str(claim_id), [])`. If `artifact_id` is None, `str(None) == "None"` and any justifications keyed under literal `"None"` would incorrectly attach. Edge case but real if upstream produces a malformed claim.

- **`propstore/concept_ids.py:139-150`** — `_write_concept_id_counter_if_unchanged` catches `FileLocked, PermissionError`, sleeps 1ms and returns False. The caller `_reserve_next_concept_id` retries up to 64 times. Under heavy contention this can return `RuntimeError("could not reserve concept ID after concurrent updates")` even when the right answer exists. No exponential backoff.

### LOW

- **`propstore/storage/git_policy.py:43-44`** — `_walker` is defined but unused (no callers in scope).

- **`propstore/repository.py:160-168`** — `Repository.init` catches no exceptions partway through. If `init_git_store` writes the .gitignore but `write_bootstrap_manifest` fails, the repo is left in a half-init state and `is_propstore_repo` returns False — but the dir IS a git repo, so retry fails with "directory already a repository".

- **`propstore/source/common.py:75`** — `cast(Repository, object())` placeholder; if `SourceBranchPlacement.address_for` ever inspects the repo argument this crashes at runtime.

- **`propstore/source/alignment.py:217-218`** — `slug = artifact.id.split(":", 1)[1]` will IndexError if `artifact.id` lacks a colon. `build_alignment_artifact` always emits `f"align:{slug}"`, but the code accepts any artifact passed in from outside.

- **`propstore/source/claims.py:79`** — concept-ref filter literal-matches only `"ps:concept:"` and `"tag:"`. Tightly coupled to two URI schemes; adding any third scheme silently skips validation.

- **`propstore/core/labels.py:60-64`** — `subsumes` is named misleadingly: `self.subsumes(other)` returns True iff `self ⊆ other`, i.e., self is the SMALLER environment. In lattice/argumentation literature `subsumes` typically means "covers/is more general than". The code at line 123 is correct in intent (drop supersets) but the method name will confuse readers.

- **`propstore/core/conditions/python_backend.py:31-36`** — `eval()` is locked down with `__builtins__: {}` but the AST is built from `ConditionReference.source_name` which is constrained only to non-empty (`ir.py:71`). If a malformed source ever produces a multi-character "name" like `"a; import os"`, the `compile()` step would raise SyntaxError (Python rejects non-identifier names), so it is effectively safe — but the surface is unsanitized. Worth a hard validate-identifier check at the IR boundary.

- **`propstore/source/promote.py:907-922`** — `sync_source_branch` defaults destination to `repo.root.parent / "papers" / source_paper_slug(...)`. Goes outside the repo by design but with no permission check on `repo.root.parent`. Existing files at the destination are silently overwritten via `target.write_bytes(...)`.

## Missing / Not implemented

- **Justification rule_kind validation** — `data-model.md` lists `rule_kind` ∈ {`reported_claim`, `supports`, `explains`}. `commit_source_justification_proposal` (`relations.py:170`) accepts `rule_kind` as a free-form string with no validation. `claim_justifications_from_active_graph` (`justifications.py:93`) only synthesizes for `{"supports", "explains"}` — anything else from authoring will be silently dropped at runtime synthesis, but persisted.

- **Justification rule_strength validation** — Same gap. `data-model.md` says `strict | defeasible`. No source-side validation.

- **Targeted undercutting integrity** — `data-model.md`: "When multiple defeasible rules support the same conclusion, omitting `target_justification_id` raises an ambiguity error." The source-side never validates that an `undercuts` stance with a `target_justification_id` actually points at a defeasible rule of the right conclusion. (`relations.py:196-242` accepts arbitrary target IDs.)

- **Context lifting rules** — `data-model.md` describes `lifting_rules` per context. No code in scope reads, applies, or surfaces them. Per the scope this might be implemented in `propstore.context_lifting` (out of scope), but the source/promote pipeline does not even carry them through finalize/promote — so they never reach the sidecar.

- **`comparison` and `limitation` claim types** — Defined in `core/claim_types.py`. `_place_promoted_singular_concept` (`promote.py:121-133` and `passes.py:169-181`) treats only `parameter`, `algorithm`, `measurement` specially. `comparison`/`limitation` claims with a singular `concept` field fall through to `concepts: [...]` insertion. Whether the sidecar build recognizes them downstream is out of scope; flagging.

- **Source kinds beyond `academic_paper`** — `core/source_types.py:6-8` (see HIGH section).

- **Conflict witness production from alignment** — `build_alignment_artifact` produces `attacks`, but the alignment never propagates a `ConflictWitness` (`graph_types.py:339`) into the compiled graph. The two systems run in parallel.

## Principle drift

- **"Imports are opinions"** violated by `passes.py:213` (concept status defaults to `accepted`), `passes.py:211-215` (definition defaults to canonical_name with no provenance), and `passes.py:255-258` (collisions silently merge with only a stored warning that nothing acts on).

- **"Preserve disagreement in storage"** violated by:
  - `registry.py:42-47` — alias collisions silently collapse via `setdefault`.
  - `alignment.py:96-98` — alignment AF defaults to `non_attack`, so contradictory proposals are never surfaced as attacks.
  - `finalize.py:_compose_source_micropubs` — silently drops claims with no context instead of preserving them with a flag.
  - `promote.py:_filter_promoted_micropubs:172-176` — drops micropubs entirely if any claim is blocked, instead of preserving as partial.

- **"No source is privileged"** — `concept_ids.py:33-43` privileges the `propstore` namespace logical id over all others when extracting numeric_id. If two namespaces both encode `concept42` the propstore one wins silently.

## Import-contract status

- `.importlinter` declares: storage→merge forbidden, source→heuristic forbidden, lemon→argumentation forbidden, worldline→support_revision forbidden.
- `propstore/storage/*` does not import `propstore.merge` (verified by reading every module). PASS.
- `propstore/source/*` does not import `propstore.heuristic` (verified). PASS.
- `propstore/source/alignment.py:19-20` imports `argumentation.partial_af` — allowed (only `propstore.core.lemon` is forbidden from that).
- `propstore/core/lemon/__init__.py` and `types.py` import only from `propstore.core.lemon.*` and `propstore.provenance` — no `argumentation` import. PASS.

All four contracts pass within the read scope.

## Code smells / redesign suggestions

- `propstore/source/promote.py` is 947 lines and conflates concept resolution, claim filtering, micropub filtering, stance/justification filtering, sidecar mirror writing, transactional commit, and worktree sync. Each phase belongs in its own module with explicit data contracts.

- The triple "in-place clear+update" pattern in `promote.py:744-758` (and the parallel `_normalize_promoted_claim_context` flow) should be replaced with rebuild-and-replace.

- Many call sites pattern-match on string-prefix `"ps:concept:"` / `"tag:"`. Centralize as `is_canonical_concept_ref(value: str) -> bool` and `is_canonical_id(value: str) -> bool`.

- `propstore/source/__init__.py` re-exports from `propstore.claim_references` — reaches across the package boundary. Either move `claim_references` under `source/`, or stop re-exporting.

- `propstore/core/graph_types.py` mixes Active/Compiled/Delta dataclasses with JSON serialization helpers (`label_to_dict`/`from_dict`). Extract serialization to a codec module so `graph_types` is pure data.

- `propstore/core/justifications.py:108` — `tuple(sorted(justifications))` works because `CanonicalJustification` is `order=True`, but the construction order in the function is implicit. Make the sort key explicit.

- `propstore/storage/snapshot.py` mixes git-snapshot reads, materialize, and worktree-clean. `_clean_materialized_semantic_files` is the only mutating method; it could live in a separate `Materializer` object.

- `propstore/source/promote.py:_compute_blocked_claim_artifact_ids:323-419` returns `tuple[set[str], dict[str, list[tuple[str, str]]]]`. A typed dataclass would document the structure better than the comment-driven explanation.

- `propstore/concept_ids.py:_COUNTER_REF_LOCK` is a process-local `threading.Lock`; for cross-process safety it relies on `set_if_equals` CAS. Mixing the two leaves the comment debt unsaid; document that the lock is a fast-path serialization, not a correctness barrier.

## Open questions for Q

1. **Partial-promote justification semantics**: `promote.py:711-727` admits a justification whose conclusion is in the source-branch claim index but not in this batch's `valid_artifact_ids`. Is this intended (justification stays valid even if its conclusion claim is on a sibling source branch awaiting its own promote) or a bug (dangling reference on master)? The stance filter is more conservative; one of the two is wrong.

2. **Alignment default**: should `classify_relation` default to `non_attack` (current behavior, hides conflicts) or `attack` (forces curator review)? "Preserve disagreement" suggests the latter.

3. **Micropub-without-context**: `_compose_source_micropubs` silently skips claims missing a context. Should this be a finalize error?

4. **`UNKNOWN` claim type**: is `ClaimType.UNKNOWN` ever a valid runtime state? `coerce_claim_type` raises on unknown values rather than returning UNKNOWN. Both behaviors live in the codebase.

5. **`SourceKind`**: is `academic_paper` really the only allowed kind, or is the enum stale? The default trust profile (`SourceTrustDocument`) is paper-shaped.

6. **Sidecar-before-git for blocked rows**: the comment on `promote.py:831-839` documents the trade-off but the cross-promote PK collision (HIGH bug above) is not addressed. Is the partial-promote design supposed to scope `claim_core.id` by `(id, branch)` or stick with bare id?

7. **`uri_authority` validation**: should `Repository.uri_authority` validate the configured value against an authority-grammar (RFC 4151 tagging-entity production), or is "garbage in, garbage out" acceptable here?

8. **Eval surface in `python_backend`**: should `ConditionReference.__post_init__` enforce identifier syntax (`str.isidentifier()`) on `source_name` to slam the door on attacker-controlled `eval()` paths?
