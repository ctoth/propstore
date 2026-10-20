# Dulwich loose-object fixed-release validation

## Goal
Validate upstream 1.2.10 against the 1.2.9 loose-object regression, then publish a minimal dependency-only draft from current master. Do not modify/close Dependabot #313, comment upstream, mark ready or merge. Preserve baseline/user work and every reproduction artifact.

## State
Fresh branch `fix/dulwich-loose-object-1-2-10`, base/current default `20134084f056d70fa1a83918b3e5b4d726bea0ce`. Read global/project AGENTS/CLAUDE and relevant dependency integration notes; no nested instructions. Real local remote is ctoth/propstore; accessible canonical repo is propstore/propstore. #313 remains OPEN at supplied `4c3523ef3d7bca52e4475e8e65c8a3157626e9d0`, changes only uv.lock 1.2.7 -> 1.2.9. Read failed CI `39384707773`: **6 failed, 1986 passed, 4 skipped**, all failures journal/worldline round trips with `zlib.error: object header exceeds maximum size`.

Verified primary upstream issue https://github.com/jelmer/dulwich/issues/2292, fix PR https://github.com/jelmer/dulwich/pull/2293 and released source at https://github.com/jelmer/dulwich/releases/tag/dulwich-1.2.10. Read both tagged parser implementations: 1.2.9 rejects unconsumed compressed tail before looking for the header NUL; 1.2.10 checks NUL and rejects only a header reaching 8192 bytes without it. The released body/header guards remain present. No local parser change or guard override.

ACTUAL PACKAGE REPRODUCTION COMPLETE on Python3.13.15, each version resolved by uv into this worktree's own isolated cache (printed `importlib.metadata.version`, actual module and interpreter paths verified; shared environments unchanged). Script `.tmp/reproduce-dulwich-loose-object.py` and all nine generated bare repos remain preserved. Six round trips per version cover `ShaFile.from_file` and a separately reopened disk `Repo.object_store`: 8182-byte payload (10-byte header, 45 compressed bytes), 8183-byte payload (10-byte header, 45 compressed bytes), 200000-byte payload (12-byte header, 230 compressed bytes). 1.2.7 passes all six; 1.2.9 passes both 8182 cases and raises exact `zlib.error: object header exceeds maximum size` in the four larger cases; 1.2.10 passes all six. Both 1.2.9 and 1.2.10 still reject a genuine 20000-byte oversized header with the same error. The boundary blob ID is `a3a69cb0b6b2ffd0c4f79f1ac3e9dc3645da8c4c`; 200000-byte blob ID `a213aa40f11f7af2a9c9e973df599278413060bb`.

Updated only Dulwich's uv.lock block to 1.2.10 using official PyPI metadata: source archive SHA256 `106546960f592216315e56d32a92e72e67f1e86671335722f833f5ecd5b73314`, size1310282; same 35 compatible wheel families, artifact URLs/hashes/sizes/timestamps from PyPI, excluding CPython3.10 artifacts because project Python>=3.11 (same prior lock policy). Dependency edges remain typing-extensions (<3.12) and urllib3. No manifest constraint, Quire/source pin, application/test code, workflow or parser change. Draft/full CI next.

Parsed old/current TOML comparison confirms exactly one changed package (`dulwich` 1.2.7 -> 1.2.10); **107 other packages and all top-level lock metadata unchanged**, same dependency edges and all **35 wheel platform/ABI tags** preserved. Source diff is only uv.lock (37 artifact/version lines replaced) plus this required note. Actual package-version probes all completed successfully with the expected regression/control outcomes.

## Decisions and why
Smallest repo change: only Dulwich's package block in uv.lock (version/artifact URLs/hashes/metadata, roughly 45 lines), plus this required task note. Leave manifest constraints, other packages, application/test code and workflows unchanged. Keep reproducer untracked in `.tmp/`; retained upstream already supplies the library regression. Test actual PyPI packages 1.2.7/1.2.9/1.2.10 in isolated uv environments under this worktree's own cache; this is the candidate-version testing explicitly authorized by the parent, with no shared-environment installs. Compare 8182/8183-byte payload boundary, 200000-byte body, reopened disk repositories and genuinely oversized-header rejection. Full Propstore suite runs through fresh draft CI against the fixed locked release, consistent with global CI instructions.

## Surprises
`gh pr diff --stat` is unsupported by this gh version; no mutation occurred. PR file list and exact dependency block supply the needed scope evidence.

## Next step
Confirm parsed lock changes only Dulwich, publish dependency-only draft plus required note, and verify fresh full Propstore CI with actual locked 1.2.10. Keep master at 1.2.7 and #313 unchanged; no ready/merge.
