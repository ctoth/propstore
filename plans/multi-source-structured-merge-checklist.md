# Multi-Source Structured Merge Checklist

**Date:** 2026-03-29
**Depends on:** `proposals/multi-source-structured-merge.md`
**Scope:** remaining preparation and implementation control surface for formal multi-source merge completion
**Status:** Draft

---

## Goal

Finish the merge stack as the authoritative peer to the revision stack.

This checklist starts from the current repo baseline:

- PAF kernel exists
- exact merge operators exist
- repo merge object exists
- completion queries exist
- CLI inspection/commit exist
- first structured-summary slice exists

So the job is no longer “invent merge semantics.” The job is:

1. consolidate the formal path
2. identify and eliminate remaining bridge/legacy production paths
3. tighten structured projection
4. prepare later policy/governance layers to sit on top of the merge object

---

## Non-Negotiable Rules

1. `PartialArgumentationFramework` stays the canonical merge kernel.
2. Merge must not route through revision code paths.
3. Revision must not be used as a substitute for merge.
4. Bridge code is allowed only when explicitly marked transitional.
5. Storage merge commits remain provenance objects, not the merge operator itself.
6. Structured consumers may project from the merge kernel, but may not silently redefine merge semantics.
7. Phase 6 is merge completion work, not a generic incomplete-information phase.
8. Source preference defaults downstream of merge unless later work proves a principled kernel-level alternative.

---

## Phase 6.0: Audit And Boundary Lock

Primary deliverables:

- proposal aligned to actual code
- merge gap audit
- implementation checklist

Primary files:

- `proposals/multi-source-structured-merge.md`
- `plans/multi-source-structured-merge-checklist.md`
- `reports/multi-source-structured-merge-gap-audit-2026-03-29.md`
- `reports/multi-source-merge-consumer-inventory-2026-03-29.md`
- `reports/structured-merge-contract-gaps-2026-03-29.md`

Tasks:

1. classify current merge modules as:
   - canonical
   - bridge
   - missing
2. identify old or transitional production paths that still rely on:
   - synthetic contradiction stances
   - claim-bucket semantics
   - merge behavior described more weakly or more strongly than implemented
3. capture the exact next coding sequence before any production edits begin

Acceptance:

- proposal, checklist, and audit agree on the current baseline
- next coding slice is unambiguous

---

## Phase 6.1: Canonical Merge Object Everywhere

Goal:

- ensure the formal merge object is the single authoritative merge representation in production paths

Primary files:

- `propstore/repo/merge_classifier.py`
- `propstore/repo/merge_report.py`
- `propstore/repo/merge_commit.py`
- any remaining merge-facing consumers identified by the audit

Tasks:

1. inventory every production consumer of merge outputs
2. mark each consumer as:
   - already canonical
   - bridge but acceptable temporarily
   - must be replaced
3. remove or replace remaining legacy merge-bucket dependencies
4. add explicit tests proving canonical consumers operate on `RepoMergeFramework` / `PartialArgumentationFramework`

Acceptance:

- no user-facing merge semantics depend on claim-bucket public APIs
- any remaining bridge path is documented as transitional
- bridge cleanup is sequenced by actual production usage, not by aesthetics
- merge kernel tests and direct-consumer tests are green

---

## Phase 6.2: Operator And Query Hardening

Goal:

- treat the exact operator/query layer as a tested kernel, not just a convenient helper

Primary files:

- `propstore/repo/merge_framework.py`
- `propstore/repo/paf_merge.py`
- `propstore/repo/paf_queries.py`
- `tests/test_paf_core.py`
- `tests/test_paf_merge.py`
- `tests/test_paf_queries.py`
- `reports/multi-source-merge-operator-query-gap-audit-2026-03-29.md`
- `plans/multi-source-merge-phase62-slice.md`

Tasks:

1. audit current tests against the proposal’s algebraic and literature regressions
2. add any missing property tests for:
   - partition
   - completion exactness
   - distance properties
   - unanimity
   - profile-order invariance
   - concordance collapse
   - ignorance monotonicity under fixation
3. add tiny exact regressions distinguishing:
   - `sum`
   - `max`
   - `leximax`
4. ensure query helpers are tested only against the canonical merge kernel

Acceptance:

- operator semantics are pinned by tests, not only docs
- query semantics over completions are explicit and reproducible

---

## Phase 6.3: Structured Projection Tightening

Goal:

- turn the current first-slice branch-local structured summary into an execution-grade boundary

Primary files:

- `propstore/repo/structured_merge.py`
- `propstore/aspic_bridge.py`
- `tests/test_structured_merge_projection.py`

Tasks:

1. define the branch-local summary contract precisely:
   - IDs
   - provenance
   - attack/non-attack/ignorance interpretation
2. identify what the current summary loses relative to the structured theory
3. add tests for:
   - summary reuse when branches are identical
   - stability of summary IDs
   - preservation of branch provenance
   - no silent collapse of out-of-scope uncertainty
4. decide which structured details remain intentionally deferred

Acceptance:

- structured-summary contract is explicit and testable
- proposal and tests agree on what the first structured slice does and does not preserve

---

## Phase 6.4: User-Facing Merge Query Surfaces

Goal:

- ensure public merge commands and reports speak in terms of the canonical merge object

Primary files:

- `propstore/cli/merge_cmds.py`
- `propstore/repo/merge_report.py`
- `docs/semantic-merge.md`
- `docs/cli-reference.md`
- world/query integration files identified during implementation

Tasks:

1. audit current CLI/report outputs for semantic honesty
2. decide whether additional public surfaces are needed before Phase 8 policy work
3. keep storage-commit and formal-merge reporting clearly separate
4. add tests for any new user-visible query/report paths

Acceptance:

- public outputs match the formal merge object rather than hiding it
- merge commit commands remain clearly distinct from merge operators

---

## Phase 6.5: Policy Readiness

Goal:

- prepare merge to support Phase 8 policy/governance without baking policy implicitly into the kernel

Primary files:

- merge proposal/checklist
- future policy proposal files

Tasks:

1. identify where source preference enters:
   - merge itself
   - post-merge defeat
   - explanation only
2. list the current hard-coded or implicit defaults that must become policy later
3. define the minimum metadata the merge path must preserve for future policy objects

Current literature-backed default:

- keep source preference out of the merge kernel
- treat it as post-merge defeat policy or explanation policy unless a later design pass justifies something stronger

Acceptance:

- later policy/governance work has a clean insertion point
- merge kernel remains structural rather than policy-entangled

---

## Test Discipline

Every coding slice that follows this checklist must:

1. write RED tests first
2. make the smallest GREEN change
3. run targeted tests as `uv run pytest -vv`
4. tee output to `logs/test-runs/`
5. reread this checklist before choosing the next slice
6. commit only the files owned by that slice

---

## Required Preparation Artifacts Before Coding

These should exist before any Phase 6 production edits:

1. updated `proposals/multi-source-structured-merge.md`
2. this checklist
3. a repo-grounded gap audit
4. a live merge-consumer inventory
5. a structured-summary contract gap memo
6. a first coding-slice RED/GREEN plan

If any of these disagree, coding should wait until they are reconciled.

---

## Next Coding Slice

After the active inspect/commit and reporting surface work, the next slice should be Phase 6.5 policy readiness scoping.

Recommended targets:

- `proposals/multi-source-structured-merge.md`
- `plans/multi-source-structured-merge-checklist.md`
- a new policy-readiness memo under `reports/`

Why:

- the public merge/query surfaces now speak honestly in terms of the canonical merge object
- the next architectural risk is accidental policy leakage into the structural merge kernel
- Phase 8 governance work needs a clean insertion point before more merge features accrete
