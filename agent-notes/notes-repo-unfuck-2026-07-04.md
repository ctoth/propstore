# Repo unfuck — 2026-07-04 session notes

## Mission
Q: "the repo, this project" got weird/broken — clean up the working tree.

## Facts established
- Branch `worldline-layer` == `master` (same commit 53bc3798). Switched to master. TODO: delete worldline-layer branch at end.
- No modified tracked files; all mess was untracked.
- `thinggy` contained a **live PyPI API token** — moved out of repo; Q must revoke/rotate at pypi.org. Flagged in chat.
- Mangled file `C<U+F03A>UsersQ...pre-g3-test_praf.py` = stale pre-g3 draft of PrAF tests; superseded by tracked tests/test_praf_*.py.
- `out` = 766KB git-log dump; `bash.exe.stackdump`, `.coverage.Empiricist.*` = machine debris.
- `pyghidra_mcp_projects/` = Ghidra project unrelated to propstore.
- `logs/` = April/May baseline test logs (leave on disk, gitignore).
- `scratchpad/` = inventory work (keep on disk, gitignore).
- `.claude/` = settings.local.json + lock + checkpoint note (gitignore whole dir).

## Done
- Attic created: `C:\Users\Q\code\propstore-attic-2026-07-04\`
- Moved to attic: out, bash.exe.stackdump, .coverage.*, .tmp/, .tmp-reasoning-demo/, pyghidra_mcp_projects/, thinggy, mangled praf file. Nothing deleted.

## Progress update (post-gitignore)
- .gitignore commit landed: 6a68f992 on master. All tooling debris now ignored; remaining untracked = content set only.
- First batch `git add` was BLOCKED by ward PreToolUse hook: "Only touched or explicitly adopted paths may be staged."
- Resolution: `ward adopt <exact repo-relative paths>` grants commit authority. Ran it for all 24 content files (10 top-level + 14 in family-protocol-cutover notes/). Adoption GRANTED — output confirmed.
- Commit messages written to scratchpad msg2–msg6.txt.
- Blocker: none. Next: rerun the 5 staged commits, delete worldline-layer branch, final status check, report (incl. PyPI token revocation reminder).

## DONE — final state (2026-07-04)
- Second ward adopt with explicit --session 2ef722ef-… worked (first adopt landed under wrong session ID). Staging then required exact file paths, not dirs.
- All 5 content commits landed: 14c6991f, a61f528a, 28d07bd9, 87b23e52, da772252 (+ gitignore 6a68f992).
- worldline-layer branch deleted (was 53bc3798, ancestor of master).
- `git status`: working tree clean, master ahead of origin/master by 6. NOT pushed (Q's call).
- Attic verified: all debris + thinggy (PyPI token — Q must revoke) in C:\Users\Q\code\propstore-attic-2026-07-04\

## Remaining plan (historical, completed)
1. .gitignore: add /.claude/, /logs/, /scratchpad/, /.tmp/, /.tmp-*/, *.stackdump, .coverage, .coverage.* → commit.
2. Content commits (verify `git diff --cached --name-only` before each; multiline msgs via -F file):
   a. proposals/relations-as-concepts + relations-unified-substrate + workstreams/relations-as-concepts-2026-05-31/inventory.md
   b. plans/dead-scaffolding-deletion-2026-05-30.md + workstreams/payload-method-deletion-2026-05-31.md
   c. workstreams/may-2026-request-audit.md + scripts/extract_codex_requests.py + scripts/verify_codex_request_audit.py
   d. workstreams/family-protocol-cutover-2026-05-24/notes/ (mds + world_charters_last_living.py; *.log already ignored)
   e. papers-2026-04-26.md + propstore-web-gui-vamp-2026-04-19.md (root notes)
3. Delete branch worldline-layer (same commit as master, zero loss).
4. Final `git status` must be clean. Report to Q incl. token revocation reminder.
