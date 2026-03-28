# Phase 4+5+6: Mutations through git, pks log, Repository integration

## 2026-03-27

**GOAL:** Wire all CLI mutation commands to write through git, add `pks log`, add `Repository.ensure_git()`, update `Repository.init()`.

**STATE:** Reading complete. All source files read. Ready to implement.

**FILES TO MODIFY:**
- `propstore/cli/concept.py` — 4a-4f: concept add/alias/rename/deprecate/link/add-value through git
- `propstore/cli/context.py` — 4g: context add through git
- `propstore/cli/__init__.py` — 4h: promote through git, Phase 5: pks log command
- `propstore/cli/worldline_cmds.py` — 4i: worldline create through git
- `propstore/cli/init.py` — 4j: pks init commits forms via git
- `propstore/cli/repository.py` — Phase 6: Repository.init() calls KnowledgeRepo.init(), add ensure_git()
- `tests/test_git_backend.py` — 7 new tests

**DONE:**
- Phase 6: `repository.py` — `Repository.init()` now calls `KnowledgeRepo.init()`, added `ensure_git()`
- Phase 4a: `concept.py` — concept add uses `git.next_concept_id()` when git available, CounterLock fallback preserved
- Phase 4b: `concept.py` — concept alias commits via git
- Phase 4c: `concept.py` — concept rename uses `git.commit_batch()`, removed subprocess import
- Phase 4d: `concept.py` — concept deprecate commits via git
- Phase 4e: `concept.py` — concept link commits via git
- Phase 4f: `concept.py` — concept add-value commits via git
- Phase 4g: `context.py` — context add commits via git
- Phase 4h: `__init__.py` — promote commits via git with adds/deletes
- Phase 4i: `worldline_cmds.py` — worldline create commits via git
- Phase 4j: `init.py` — seeds forms then commits them, removed .counters/ from output

**REMAINING:**
- Fix 3 failing tests: concept_add, concept_rename, log_output
- Run full test suite
- Report file
- Commit

**CURRENT BLOCKER:** 3 tests fail with "No knowledge/ directory found". `Repository.init()` creates dirs correctly (verified). The CliRunner with `-C` flag should find them. Need to debug why `Repository.find()` can't see `concepts/` inside CliRunner.

Possible: `git.commit_files()` + `git.sync_worktree()` in the test setup is removing the concepts dir (empty dir cleanup in sync_worktree). The forms commit + sync happens AFTER dirs are created, and sync removes empty dirs like concepts/.
