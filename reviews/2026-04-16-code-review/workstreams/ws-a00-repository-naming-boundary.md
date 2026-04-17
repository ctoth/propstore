# Workstream A00 - Repository Naming Boundary

Date: 2026-04-17
Status: complete
Blocks: `ws-a0-repository-artifact-boundary.md`, `ws-a-semantic-substrate.md` phase 2 continuation
Review context: `ws-a0-repository-artifact-boundary.md`, `../axis-2-layer-discipline.md`, `disciplines.md`

## Problem

The repository layer currently exposes two repo-shaped surfaces:

- `propstore.repo.repository.Repository`, the high-level knowledge repository facade used by CLI, source, artifact, world, and test code.
- `propstore.repo.KnowledgeRepo`, the low-level Dulwich-backed git carrier.

That leaves call sites spelling `repo.repository.Repository` and forces readers to distinguish `Repository`, `repo`, and `KnowledgeRepo` by convention instead of by architecture. This is a layer-boundary defect, not a compatibility concern.

## Target Shape

- The high-level facade lives at `propstore.repository.Repository`.
- The low-level Dulwich carrier is named `GitStore` and remains implementation storage, not another repository facade.
- `propstore.repo.repository` is deleted.
- `KnowledgeRepo` is deleted as a propstore production/test surface; callers use `GitStore`.
- No compatibility alias, shim, re-export, fallback import, or dual import path is permitted.

## Gates

- A structural test rejects any `propstore.repo.repository` import.
- A structural test rejects `propstore/repo/repository.py`.
- A structural test rejects propstore-owned classes named `KnowledgeRepo`.
- A structural test verifies `propstore.repository.Repository` is the canonical facade and does not depend on `propstore.world`.
- A structural test verifies `propstore.repo.GitStore` is the low-level git carrier exported by the repo package.

## Execution Plan

1. Add failing boundary gates for the bad names.
2. Move `Repository` from `propstore/repo/repository.py` to `propstore/repository.py`.
3. Rename `KnowledgeRepo` to `GitStore` and update every caller directly.
4. Delete `propstore/repo/repository.py`.
5. Run the naming gates and affected repository/artifact suites through `scripts/run_logged_pytest.ps1`.
6. Update this workstream log, commit, and push only explicit source/test/workstream files.

## Progress Log

- 2026-04-17: Workstream opened after the WS-A phase 2 execution exposed that the completed WS-A0 cleanup still left a confusing `repo.repository.Repository` import surface plus a second `KnowledgeRepo` type.
- 2026-04-17: Completed. `Repository` now lives at `propstore.repository.Repository`; the low-level Dulwich carrier is `propstore.repo.GitStore`; `propstore/repo/repository.py` was deleted; structural gates reject the old import path and the old carrier class name. Verification: `repository-naming-gates-green` passed (`7 passed`), then `repository-naming-affected-2` passed (`158 passed`), including GitStore Hypothesis properties and repository import normalization properties.
