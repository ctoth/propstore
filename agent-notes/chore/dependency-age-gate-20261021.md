# Dependency release-age gate

## Goal

Require a rolling 14-day age for registry candidates and pin CI to uv 0.13.1,
while preserving existing locked dependency versions, sources, and hashes.

## State

- Project `exclude-newer = "14 days"` and exact CI uv pin are applied.
- uv 0.13.1 regenerated the lock with source builds disabled: revision 5,
  `exclude-newer-span = "P14D"`, backwards-compatibility sentinel, and seven
  timestamp formatting normalizations. All 108 package versions, sources, and
  artifact hashes match the original lock.
- The existing CI command remains `uv sync --dev --locked`.
- Draft publication and hosted CI are next. No merge is authorized.

## Decisions and evidence

- Build-disabled metadata resolution rejected `uv==0.13.4`, uploaded
  2026-10-20T15:11:02Z, with an explicit exclude-newer cutoff of October 7.
  Both user-config and project-config invocations rejected it.
- Eligible `packaging==26.3` resolved successfully without builds.
- `uv lock --no-build --no-python-downloads` succeeded. A per-package comparison
  confirmed unchanged versions, sources, and artifact hashes.
- `uv sync --dev --locked --dry-run --no-build --no-python-downloads --offline`
  accepted the lock and resolved 108 packages, then exited 2 because the existing
  Git dependency assignment-selection has no binary distribution. No environment
  was created. Normal installation belongs to hosted CI.
- `git diff --check` passed. actionlint and zizmor are unavailable locally.

## Coverage and limitations

The gate constrains registry candidate selection by publication time. It does
not establish that existing locks, Git revisions, local sources, or direct URL
artifacts passed registry-age review. Explicit configuration/CLI overrides and
package-specific exceptions can change the policy. Frozen installs skip lock
freshness checks. Existing pinned Git sources are retained. Emergency exceptions
require a narrow reviewed change.

Reference: https://docs.astral.sh/uv/concepts/resolution/#time-based-reproducible-resolutions

## Next step

Commit, push only this feature branch, open a draft PR, and inspect its normal
hosted CI. Preserve dependency versions and hashes during any repair.
