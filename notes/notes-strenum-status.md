# StrEnum Status Conversion Notes

## GOAL
Convert bare string status fields on ValueResult, DerivedResult, ResolvedResult to a StrEnum.

## FINDINGS

### Status values collected from all sources:

**ValueResult statuses** (from value_resolver.py, bound.py, resolution.py):
- "determined"
- "conflicted"
- "no_claims"
- "no_values"
- "underdetermined" (mentioned in types.py comment, used in worldline_runner.py line 594)

**DerivedResult statuses** (from value_resolver.py):
- "derived"
- "no_relationship"
- "underspecified"
- "conflicted"

**ResolvedResult statuses** (from resolution.py):
- "determined"
- "no_claims"
- "conflicted"
- "resolved"

### Dataclasses to update (types.py):
- ValueResult.status: str -> ValueStatus
- DerivedResult.status: str -> DerivedStatus
- ResolvedResult.status: str -> ResolvedStatus

Wait -- prompt says single ValueStatus enum. Let me re-read... prompt says "ValueStatus" with all values. But the statuses are different per result type. I'll use a single enum with ALL values as the prompt specifies, since StrEnum == str means no breakage.

### Combined unique status values:
- determined, conflicted, no_claims, no_values, underdetermined, derived, no_relationship, underspecified, resolved

### Construction sites (files that create result objects with status=):
1. propstore/world/value_resolver.py - ValueResult and DerivedResult construction
2. propstore/world/resolution.py - ResolvedResult construction
3. propstore/worldline_runner.py - dict-based status assignments (NOT dataclass, skip these)
4. tests/test_labelled_core.py - test constructions
5. tests/test_worldline.py - test constructions

### Comparison sites (DO NOT TOUCH per prompt):
- Many .status == "..." comparisons across all files

## PLAN
1. Add StrEnum import and ValueStatus class to types.py
2. Update status annotations on ValueResult, DerivedResult, ResolvedResult
3. Update construction sites in value_resolver.py and resolution.py with enum members
4. Do NOT touch worldline_runner.py dict status assignments (those are plain dicts, not dataclasses)
5. Do NOT touch test files' comparison sites
6. DO update test files' construction sites (where they build ValueResult/DerivedResult directly)
7. Run tests

## DONE
1. types.py: Added `from enum import StrEnum`, defined `ValueStatus(StrEnum)` with all 9 values
2. types.py: Updated ValueResult, DerivedResult, ResolvedResult status annotations to `ValueStatus`
3. value_resolver.py: Added ValueStatus import, replaced ALL status string literals with enum members
4. resolution.py: Added ValueStatus import (construction site replacements still needed)

## REMAINING
- resolution.py: Replace status string literals with enum members (6 sites)
- Test files: Update construction sites (test_labelled_core.py, test_worldline.py) -- these build ValueResult/DerivedResult directly with status="..."
- Run tests
- Commit

## TEST RESULTS
1022 passed, 1 failed (pre-existing: test_atms_cli_surfaces_interventions_and_next_queries -- missing CLI command, unrelated)

## COMMIT
987d822 - "Convert status fields from bare strings to StrEnum for type safety"

## STATUS
Committed. Need to write final report to reports/fix-strenum-status-report.md.
