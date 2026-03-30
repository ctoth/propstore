# Pure Git Semantic Model Checklist

**Date:** 2026-03-30
**Scope:** migrate propstore from mixed filesystem/git semantics to a pure git semantic model
**Status:** Draft

---

## Goal

Make git the only authoritative semantic store.

For git-backed repos:

1. semantic reads resolve from git `HEAD` by default
2. semantic writes create git commits directly
3. working-tree files are not a semantic input surface
4. local file mutation is not a first-class workflow for semantic objects

This is stronger than the current import-repo slice. It is a repo-wide semantic contract change.

---

## Non-Negotiable Rules

1. `KnowledgeRepo` remains the authoritative storage layer.
2. `Repository.tree()` must stop meaning “ambient filesystem state” for git-backed repos.
3. Commands must not read uncommitted YAML as semantic truth.
4. Commands must not require local file rewrites in order to perform semantic updates.
5. `sync_worktree()` is materialization only, not a semantic write path.
6. Derived artifacts like sidecars remain generated outputs, not source-of-truth data.

---

## Current State

Already aligned or close:

- [propstore/repo/git_backend.py](/C:/Users/Q/code/propstore/propstore/repo/git_backend.py)
- [propstore/build_sidecar.py](/C:/Users/Q/code/propstore/propstore/build_sidecar.py)
- [propstore/validate.py](/C:/Users/Q/code/propstore/propstore/validate.py)
- [propstore/validate_contexts.py](/C:/Users/Q/code/propstore/propstore/validate_contexts.py)
- merge and repo-import code under [propstore/repo/](/C:/Users/Q/code/propstore/propstore/repo)

Primary semantic contradiction:

- [propstore/cli/repository.py](/C:/Users/Q/code/propstore/propstore/cli/repository.py)
  `Repository.tree(commit=None)` currently returns `FilesystemKnowledgePath`.

Primary migration risk:

- many CLI commands mix semantic reads with concrete `Path`-based mutation logic

---

## Phase 1: Core Contract Flip Preparation

Primary files:

- [propstore/cli/repository.py](/C:/Users/Q/code/propstore/propstore/cli/repository.py)
- [propstore/knowledge_path.py](/C:/Users/Q/code/propstore/propstore/knowledge_path.py)
- [tests/test_knowledge_path.py](/C:/Users/Q/code/propstore/tests/test_knowledge_path.py)

Tasks:

1. Add an explicit semantic-read API for git-backed repos.
2. Add an explicit local/materialized path API for the rare non-semantic file operations that remain.
3. Rewrite the `Repository.tree()` contract tests to assert git-backed `HEAD` semantics.
4. Decide whether `Repository.collection()` survives; it currently returns `Path`, which is wrong for a pure semantic API.

Likely contract:

- `repo.tree()` or `repo.semantic_tree()` returns git `HEAD` when `repo.git` exists
- direct local `Path` access must be explicit and exceptional

---

## Phase 2: Pure Semantic Reader Migration

These callsites mostly read semantic state and should move first.

Primary files:

- [propstore/cli/compiler_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/compiler_cmds.py)
- [propstore/validate.py](/C:/Users/Q/code/propstore/propstore/validate.py)
- [propstore/cli/claim.py](/C:/Users/Q/code/propstore/propstore/cli/claim.py)

Tasks:

1. Convert all default semantic reads in `validate`, `build`, `export-aliases`, and world-facing compiler helpers to the git-backed semantic tree.
2. Remove direct semantic dependence on `repo.concepts_dir`, `repo.claims_dir`, and `repo.forms_dir` where a `KnowledgePath` read is sufficient.
3. Make claim validation default to semantic tree reads instead of concrete directories when no override is given.
4. Keep explicit path-override commands explicit and clearly non-default if they remain at all.

Key callsites already identified:

- `propstore/cli/compiler_cmds.py:96`
- `propstore/cli/compiler_cmds.py:337`
- `propstore/cli/compiler_cmds.py:488`
- `propstore/cli/compiler_cmds.py:2298`
- `propstore/validate.py:129`
- `propstore/cli/claim.py:110`
- `propstore/cli/claim.py:193`

---

## Phase 3: Filesystem-Mutation Command Redesign

These commands currently depend on concrete files and cannot just inherit the semantic flip.

Primary files:

- [propstore/cli/concept.py](/C:/Users/Q/code/propstore/propstore/cli/concept.py)
- [propstore/cli/context.py](/C:/Users/Q/code/propstore/propstore/cli/context.py)
- [propstore/cli/form.py](/C:/Users/Q/code/propstore/propstore/cli/form.py)
- [propstore/cli/worldline_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/worldline_cmds.py)
- [propstore/cli/__init__.py](/C:/Users/Q/code/propstore/propstore/cli/__init__.py)
- [propstore/cli/init.py](/C:/Users/Q/code/propstore/propstore/cli/init.py)
- [propstore/relate.py](/C:/Users/Q/code/propstore/propstore/relate.py)

Tasks:

1. Remove `_require_local_source_path(...)` assumptions from concept mutation flows.
2. Rewrite concept add/alias/rename/deprecate/link/add-value to:
   - read from the semantic tree
   - construct new YAML blobs in memory
   - commit through `KnowledgeRepo.commit_files()` or `commit_batch()`
   - avoid local file rewrites as the source of truth
3. Rewrite context add/list around semantic tree reads and direct git commits.
4. Rewrite form add/remove/validate/list/show so forms are read semantically and written by direct commit, not local file operations.
5. Rewrite worldline definition storage if worldlines remain tracked semantic artifacts. Current implementation is file-first.
6. Rewrite `promote` so proposal promotion is a git object transformation, not a filesystem rename followed by commit.
7. Rewrite `import-papers` so imported claim YAML is committed directly rather than written to disk first.
8. Rewrite stance proposal emission in `relate.py` if proposals remain in-repo tracked artifacts.
9. Rewrite `init` so seed forms are committed directly from packaged resources rather than copied to disk first.

High-risk examples:

- `propstore/cli/concept.py:121`
- `propstore/cli/concept.py:319`
- `propstore/cli/concept.py:342`
- `propstore/cli/context.py:36`
- `propstore/cli/form.py:34`
- `propstore/cli/worldline_cmds.py:229`
- `propstore/cli/__init__.py:186`
- `propstore/cli/init.py:59`
- `propstore/relate.py:533`

---

## Phase 4: Helper And API Boundary Cleanup

Primary files:

- [propstore/cli/helpers.py](/C:/Users/Q/code/propstore/propstore/cli/helpers.py)
- [propstore/form_utils.py](/C:/Users/Q/code/propstore/propstore/form_utils.py)
- [propstore/validate_claims.py](/C:/Users/Q/code/propstore/propstore/validate_claims.py)
- [propstore/worldline.py](/C:/Users/Q/code/propstore/propstore/worldline.py)

Tasks:

1. Split semantic lookup helpers from local filesystem helpers.
2. Replace `find_concept`, `load_concept_file`, and `write_yaml_file` coupling with git-native equivalents for semantic objects.
3. Expand `form_utils` so the remaining `Path`-only helpers are no longer required for semantic code paths.
4. Replace `build_concept_registry_from_paths(...)` with a semantic-tree-native version.
5. Decide whether `WorldlineDefinition.from_file()` / `to_file()` should become blob-based repo helpers for tracked worldlines.
6. Revisit counters:
   - if concept IDs remain git-derived, `KnowledgeRepo.next_concept_id()` is fine
   - filesystem counter locks become legacy-only or removable

Blocked-by examples:

- `propstore/form_utils.py:170`
- `propstore/form_utils.py:384`
- `propstore/form_utils.py:431`
- `propstore/validate_claims.py:703`
- `propstore/validate_claims.py:747`
- `propstore/worldline.py:160`
- `propstore/cli/helpers.py:160`

---

## Phase 5: Tests And Docs

Primary files:

- [tests/test_knowledge_path.py](/C:/Users/Q/code/propstore/tests/test_knowledge_path.py)
- CLI tests under [tests/](/C:/Users/Q/code/propstore/tests)
- [docs/git-backend.md](/C:/Users/Q/code/propstore/docs/git-backend.md)
- [docs/cli-reference.md](/C:/Users/Q/code/propstore/docs/cli-reference.md)

Tasks:

1. Rewrite tests that currently encode filesystem-default semantics.
2. Add regressions proving uncommitted working-tree files do not affect semantic commands.
3. Add regressions proving semantic mutation commands do not require local file rewrites.
4. Update docs to state explicitly:
   - git `HEAD` is the default semantic state
   - working tree is optional materialization only
   - local file edits are not part of the semantic workflow

Known old-contract test:

- `tests/test_knowledge_path.py:95`

---

## Phase 6: Final Flip And Legacy Removal

Tasks:

1. Flip the default semantic API once reader and writer migrations are complete.
2. Remove remaining fallback filesystem semantic paths for git-backed repos.
3. Minimize or remove `sync_worktree()` calls from ordinary semantic command flows.
4. Decide whether non-git repos remain supported or become a legacy compatibility mode.

Acceptance:

1. For git-backed repos, semantic reads never depend on ambient filesystem state.
2. For git-backed repos, semantic writes never depend on mutating local YAML as an intermediate authority.
3. The only authoritative semantic state is the git object graph.

---

## Recommended Sequencing

1. Phase 1: core API contract
2. Phase 2: pure readers
3. Phase 4: helper cleanup that unblocks command rewrites
4. Phase 3: mutation command redesign
5. Phase 5: tests/docs consolidation
6. Phase 6: final default flip and legacy removal

Reason:

- flipping the default first would break command code that still assumes concrete files
- the right migration is to remove those assumptions, then make the default honest

