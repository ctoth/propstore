# Global IC-Merge And Cleanup Plan

Date: 2026-03-29

Goal: finish the two important deferred tracks left after the review remediation:

1. literature-faithful global `mu` for IC merging
2. post-remediation cleanup so the new merge path is the real production path

This plan is intentionally narrower and more ambitious than the completed
review-remediation plan. The target is not "better than before"; the target is a
world-level constrained merge design that the architecture can honestly support.

## Current State

Implemented today:

- assignment-level `ICMergeProblem` / `ICMergeResult`
- single-concept constrained merge adaptation
- automatic concept-local constraints from existing metadata
- `ResolutionStrategy.IC_MERGE` wired for one concept

Not implemented today:

- multi-concept merged assignments
- cross-concept `mu`
- CEL/Z3-backed global constraints
- full render-time or worldline-level IC-merge wiring
- cleanup of stale surfaces around old merge assumptions

## Global Rules

1. Keep literature claims narrower than the implementation at every step.
2. Do not ship cross-concept-looking APIs that still solve concepts independently.
3. Add RED coverage before each production slice.
4. After every green slice, reread this plan and continue with the next unchecked
   phase unless explicitly redirected.
5. Keep one focused commit per phase.

## Test Discipline

Every test run must use this pattern:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
uv run pytest -vv <TEST_SELECTION> 2>&1 | Tee-Object -FilePath "logs/test-runs/<NAME>-$ts.log"
```

## Phase Order

### 1. Formalize the global merge problem type

Commit message:
- `refactor(merge): formalize global ic-merge problem`

Scope:
- `propstore/world/types.py`
- `propstore/repo/ic_merge.py`
- tests in:
  - `tests/test_ic_merge.py`

Work:
- distinguish single-concept adaptation from true global merge explicitly
- require `ICMergeProblem.concept_ids` and source assignments to support multiple
  concepts without hidden scalar assumptions
- make winner/scores/reporting shaped around merged assignments, not scalar values

Required RED tests:
- two-concept merge problems can be represented without lossy scalar coercion
- assignment scores are stable under source-order permutation

Stop condition:
- the core types and solver entrypoints are natively multi-concept

### 2. Add true cross-concept `mu`

Commit message:
- `feat(merge): enforce cross-concept integrity constraints`

Scope:
- `propstore/repo/ic_merge.py`
- `propstore/world/types.py`
- tests in:
  - `tests/test_ic_merge.py`

Work:
- implement `mu` checks over whole assignments, not one concept at a time
- support constraints that mention multiple concepts in one rule
- keep concept-local metadata constraints as a special case of the same machinery

Required RED tests:
- individually admissible local values can be rejected as a jointly invalid
  merged assignment
- unconstrained multi-concept problems still return admissible assignment winners

Suggested Hypothesis properties:
- every winning assignment satisfies all constraints
- source renaming does not change winning assignments
- unconstrained one-concept problems match the existing scalar kernels

Stop condition:
- at least one real multi-concept constraint changes the winner set compared to
  independent per-concept solving

### 3. Add CEL-backed assignment constraints

Commit message:
- `feat(merge): support cel integrity constraints for global mu`

Scope:
- `propstore/repo/ic_merge.py`
- `propstore/cel_checker.py`
- `propstore/world/model.py`
- tests in:
  - `tests/test_ic_merge.py`
  - add dedicated CEL-backed merge tests if needed

Work:
- evaluate CEL constraints against candidate merged assignments
- bind candidate values by canonical concept identifier
- reject ill-typed constraints early and clearly

Required RED tests:
- a well-typed CEL constraint filters assignments correctly
- an invalid CEL constraint fails explicitly instead of silently passing

Suggested Hypothesis properties:
- adding an always-true CEL constraint does not change winners
- adding an unsatisfiable CEL constraint yields no admissible assignments

Stop condition:
- global `mu` can be expressed with CEL over merged assignments

### 4. Add optional Z3-backed pruning/validation for global `mu`

Commit message:
- `feat(merge): prune global ic-merge candidates with z3`

Scope:
- `propstore/repo/ic_merge.py`
- `propstore/z3_conditions.py`
- tests in:
  - `tests/test_ic_merge.py`

Work:
- use Z3 where available to reject impossible assignment regions earlier
- keep brute-force enumeration as the trusted reference on bounded cases
- prove equivalence between pruned and unpruned winner sets on supported inputs

Required RED tests:
- Z3-pruned and brute-force paths agree on bounded multi-concept cases
- solver unavailability or translation failure falls back cleanly

Stop condition:
- Z3 is an optimization/validation layer, not a semantic fork

### 5. Wire global IC merge into production resolution surfaces

Commit message:
- `feat(world): wire global ic-merge through resolution surfaces`

Scope:
- `propstore/world/resolution.py`
- `propstore/worldline_runner.py`
- `propstore/cli/compiler_cmds.py`
- tests in:
  - `tests/test_resolution_helpers.py`
  - `tests/test_worldline.py`

Work:
- let production callers build one merge problem over the jointly relevant
  concepts when policy asks for IC merge
- return results that are honest when no unique active claim realizes the merged
  assignment
- thread branch filters and branch weights through the global solver

Required RED tests:
- a cross-concept constraint can change production resolution output
- branch-filtered sources change the merged assignment only through the formal
  problem construction, not ad hoc local filtering

Stop condition:
- production IC merge is driven by the global assignment solver

### 6. Cleanup stale merge surfaces and claims

Commit message:
- `refactor(merge): remove stale scalar-only ic-merge surface`

Scope:
- `propstore/repo/ic_merge.py`
- `propstore/world/types.py`
- `CLAUDE.md`
- related docs/tests

Work:
- remove or demote public entrypoints that imply scalar-only semantics are the
  main path
- align docs, names, and comments with the actual global architecture
- keep scalar helpers only as clearly labeled kernels or degenerate adapters

Required RED tests:
- public docs/tests do not describe full IC semantics through scalar wrappers
- production surfaces no longer bypass the global problem type

Stop condition:
- the production path and the documented path are the same path

## Source Record

- Design anchor:
  - `plans/ic-merge-mu-design-2026-03-29.md`
- Completed prerequisite:
  - `plans/review-remediation-plan-2026-03-29.md`
- Literature anchor:
  - `papers/Konieczny_2002_MergingInformationUnderConstraints/notes.md`
