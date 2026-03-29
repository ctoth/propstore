# Review Remediation Plan

Date: 2026-03-29

Goal: fix the 2026-03-29 review findings one issue at a time, easiest first, with
one focused commit per issue.

This plan is execution-first:

1. Write a RED regression for the current issue.
2. Run the smallest relevant `uv run pytest -vv ...` slice and tee the full output
   to `logs/test-runs/`.
3. Make the smallest code change that fixes the issue honestly.
4. Re-run the same focused slice until green.
5. Re-read this plan and continue with the next unchecked issue.
6. Commit only the files for the current issue.

## Global Rules

1. Do not use feature gating as the final answer when the issue is asking for a
   real fix.
2. If a review finding turns out to be stale, prove that with a regression or a
   targeted verification log before skipping it.
3. For literature-backed issues, reread the relevant local paper notes
   immediately before implementing.
4. Do not batch unrelated cleanup into the current issue's commit.
5. Leave unrelated worktree changes alone.

## Test Discipline

Every test run must use this pattern:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
uv run pytest -vv <TEST_SELECTION> 2>&1 | Tee-Object -FilePath "logs/test-runs/<NAME>-$ts.log"
```

## Commit Order

The order is fixed from easiest safe fixes to heavier formal repairs.

### 1. Exact-DP fallback/support contract

Commit message:
- `fix(praf): repair exact-dp fallback contract`

Scope:
- `propstore/praf_treedecomp.py`
- `propstore/praf.py`
- tests in:
  - `tests/test_praf.py`
  - optionally `tests/test_treedecomp.py`

Work:
- Fix the broken direct fallback in `praf_treedecomp.compute_exact_dp()`
- Make advertised query support match real support
- Keep public routing behavior explicit and honest

Required RED tests:
- direct `compute_exact_dp(praf, "preferred")` fallback does not raise `TypeError`
- exact-DP support metadata does not claim unsupported query modes

Stop condition:
- direct fallback works
- no support surface advertises a query mode that the implementation rejects

### 2. IC merge on unhashable values

Commit message:
- `fix(repo): handle unhashable values in ic-merge operators`

Scope:
- `propstore/repo/ic_merge.py`
- tests in:
  - `tests/test_ic_merge.py`

Work:
- Replace `set`-based deduplication with stable equality-based deduplication
- Preserve the arbitration property for equal values

Required RED tests:
- `max_merge` accepts list-valued profile entries
- `gmax_merge` accepts dict-valued profile entries

Stop condition:
- list/dict profile values no longer crash

### 3. Real merge-base on commit DAGs

Commit message:
- `fix(repo): compute nearest common ancestor for merge-base`

Scope:
- `propstore/repo/branch.py`
- tests in:
  - `tests/test_repo_branch.py`

Work:
- Replace alternating BFS overlap with nearest-common-ancestor logic
- Add a regression involving an actual merge commit shape

Required RED tests:
- merge base prefers a newer common ancestor over an older one
- merge base works correctly once merge commits exist

Stop condition:
- merge-base matches Git-like nearest-common-ancestor semantics on tested DAGs

### 4. Backend capability policy unification

Commit message:
- `fix(semantics): centralize backend capability policy`

Scope:
- `propstore/core/analyzers.py`
- `propstore/structured_argument.py`
- `propstore/cli/worldline_cmds.py`
- `propstore/world/resolution.py`
- `propstore/praf.py`
- tests in:
  - `tests/test_core_analyzers.py`
  - `tests/test_worldline.py`
  - `tests/test_structured_argument.py`
  - `tests/test_praf.py`

Work:
- Define one matrix for backend × semantics × graph kind × query kind
- Use it in CLI, analyzers, structured resolution, and PrAF routing
- Remove contradictory grounded/backend behavior

Required RED tests:
- `claim_graph + grounded` CLI/analyzer surface is coherent
- structured backend does not silently reinterpret `grounded`

Stop condition:
- backend capability errors are consistent across surfaces

### 5. Lazy package root imports

Commit message:
- `refactor(pkg): make propstore package root lazy`

Scope:
- `propstore/__init__.py`
- tests in:
  - `tests/test_init.py`
  - add import-focused regression if needed

Work:
- Stop package import from eagerly dragging in world machinery
- Preserve public import surface

Required RED tests:
- importing a formal kernel does not fail because package root eagerly imports
  unrelated optional dependencies

Stop condition:
- kernel imports are decoupled from world-layer optional dependencies

### 6. Tree decomposition utility correctness on public inputs

Commit message:
- `fix(td): validate decompositions and handle disconnected afs`

Scope:
- `propstore/praf_treedecomp.py`
- tests in:
  - `tests/test_treedecomp.py`

Work:
- Add a decomposition validator
- Make disconnected-input behavior correct or explicitly rejected
- Ensure nice TD conversion does not silently drop components

Required RED tests:
- disconnected AF public TD utility does not silently omit bags
- validator catches invalid running-intersection cases

Stop condition:
- public TD utilities are correct on their advertised domain

### 7. Valid tree decomposition construction

Commit message:
- `fix(td): construct valid tree decompositions`

Scope:
- `propstore/praf_treedecomp.py`
- tests in:
  - `tests/test_treedecomp.py`

Literature:
- `papers/Popescu_2024_ProbabilisticArgumentationConstellation/notes.md`

Work:
- Repair parent-selection/bag-linking so running intersection actually holds
- Add the review's concrete counterexample as a permanent regression

Stop condition:
- decomposition validator passes on the review counterexample and related cases

### 8. Exact grounded DP soundness

Commit message:
- `fix(td): make exact grounded dp sound against enumeration`

Scope:
- `propstore/praf_treedecomp.py`
- `propstore/praf.py`
- tests in:
  - `tests/test_treedecomp.py`
  - `tests/test_treedecomp_differential.py`

Literature:
- `papers/Popescu_2024_ProbabilisticArgumentationConstellation/notes.md`
- `papers/Hunter_2021_ProbabilisticArgumentationSurvey/notes.md`

Work:
- Differentially compare against exact enumeration
- Either repair the current DP or replace it with a faithful local-state DP

Stop condition:
- bounded differential runs pass without gating or silent downgrade for the
  modes we claim to support

### 9. Real `mu` for IC merging

Commit message:
- `feat(merge): introduce integrity constraints for ic-merge`

Scope:
- `propstore/repo/ic_merge.py`
- `propstore/world/types.py`
- callers/tests as needed

Literature:
- `papers/Konieczny_2002_MergingInformationUnderConstraints/notes.md`

Work:
- Introduce an actual integrity-constraint interface
- Apply it when selecting admissible merge results
- Narrow or update postulate claims to match implemented behavior

Stop condition:
- merge operators can enforce a real `mu`
- docs/code no longer imply full IC semantics without constraints

### 10. Duplicate/stale backend surface cleanup

Commit message:
- `refactor(arch): remove stale duplicate backend surface`

Scope:
- `propstore/world/types.py`
- `propstore/world/resolution.py`
- related docs/tests

Work:
- Resolve `structured_projection` vs `aspic` duplication
- Remove stale public distinctions that no longer reflect implementation

Stop condition:
- public backend surface matches actual implementation boundaries

## Source Record

- Review:
  - `reviews/03-29-2026-pro.md`
- Existing related plans:
  - `plans/known-fixes-and-paper-gaps-plan-2026-03-28.md`
  - `plans/literature-alignment-remediation-plan-2026-03-26.md`
- Literature anchors:
  - `papers/Popescu_2024_ProbabilisticArgumentationConstellation/notes.md`
  - `papers/Hunter_2021_ProbabilisticArgumentationSurvey/notes.md`
  - `papers/Konieczny_2002_MergingInformationUnderConstraints/notes.md`
  - `papers/Modgil_2018_GeneralAccountArgumentationPreferences/notes.md`
