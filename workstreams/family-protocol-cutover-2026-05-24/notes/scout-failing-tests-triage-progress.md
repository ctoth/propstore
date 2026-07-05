# Scout: failing-tests-triage progress

## 2026-05-24 - state

- HEAD: e13e302d195ddf38bbde5c965744e992ae57166b
- Tracked tree: clean. Only untracked files (.tmp/, logs/, etc.) — not relevant to tests.
- Prompt: workstreams/family-protocol-cutover-2026-05-24/prompts/scout-failing-tests-triage.md (READ).
- Deliverable: workstreams/family-protocol-cutover-2026-05-24/reports/scout-failing-tests-triage.md (NOT YET WRITTEN).

## Reads done

- 00-index.md (Refactor Zen, phase table, First Repair Answer)
- 01-deleted-file-fallout-repair.md
- 02-quire-generated-family-protocols.md
- 03-generic-family-lookup-cleanup.md
- 04-family-document-deletion.md

## Reads remaining

- 05-12 phase files (need to read all per prompt section "Reads you MUST do")
- 6 scout reports under reports/charter-cutover-breakdown/

## Commands run

- `git status --short` + `git rev-parse HEAD` — captured tree state.
- (Pytest + pyright NOT yet run.)

## Blocker

None. Next steps:
1. ~~Finish reading phases 05-12~~ DONE.
2. Read remaining 4 scout reports under reports/charter-cutover-breakdown/ (read: quire-prereqs-report, family-docs-registry-report; remaining: source-lifecycle, root-semantic-surfaces, worldline-resolution, old-workstream-reconciliation).
3. Run logged pytest, tee log to notes/.
4. Run pyright propstore, tee log to notes/.
5. Build inventory + phase mapping + first-cut recommendation.
6. Write the report deliverable.

## Key observations (so far)

- Scout reports live at `C:\Users\Q\code\propstore\reports\charter-cutover-breakdown\`, NOT under workstreams/.../reports/.
- The two deleted files (confirmed deleted) are `propstore/families/world_charters.py` and `propstore/families/claims/metadata.py` (per phase 01 + family-docs-registry-report). Production importers verified by family-docs-registry-report:
  - `world_charters` importers: `propstore/compiler/workflows.py`, `propstore/app/concepts/display.py`, `propstore/families/embeddings/declaration.py`, `propstore/families/contexts/declaration.py`, `propstore/families/claims/sidecar_runtime.py`, `propstore/families/concepts/sidecar_runtime.py`, `propstore/source/status.py`, `propstore/world/model.py`, plus many tests.
  - `claim_metadata_value` importers: `propstore/preference.py`, `propstore/praf/engine.py`, `propstore/world/resolution.py`.
- These import-fallout sites are the strongest candidate for the "Phase 1 first cut" since the index calls them out explicitly in "First Repair Answer".

No commits — scout is read-only.
