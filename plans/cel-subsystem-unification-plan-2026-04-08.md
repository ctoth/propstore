# CEL Subsystem Unification Plan

Date: 2026-04-08

Goal: replace the current split CEL implementation with one clean production
subsystem that:

1. has one production runtime backend
2. has one canonical registry-construction path
3. has zero production shims or duplicate evaluators
4. uses principled open-category semantics for `extensible: true`
5. updates all callers and docs in the same execution track

## Execution Status

- U0: Not started
- U1: Not started
- U2: Not started
- U3: Not started
- U4: Not started
- U5: Not started
- U6: Not started
- U7: Not started

## Decision Summary

This plan is authoritative for the CEL cleanup effort.

The intended end state is:

- one production CEL backend: Z3-backed reasoning and concrete satisfaction
- no production handwritten CEL AST evaluator outside that backend
- no internal "legacy concept dict" compatibility layer in the compiler/world path
- one canonical CEL registry API used by validation, compiler passes, world
  activation, conflict detection, and IC-merge
- category semantics split by openness:
  - `extensible: false` -> closed finite enum semantics
  - `extensible: true` -> open symbolic string semantics

Because the repository has no legacy knowledge repos to preserve, this plan does
not permit compatibility shims as a migration crutch.

## Current State

Production CEL today is split across:

- parser/type-checker in `propstore/cel_checker.py`
- Z3 backend in `propstore/z3_conditions.py`
- a second handwritten production evaluator in `propstore/repo/ic_merge.py`

Registry plumbing is also split across:

- `propstore/cel_checker.py` registry builders
- manual `ConceptInfo` assembly in `propstore/world/model.py`
- manual `ConceptInfo` assembly in `propstore/world/resolution.py`
- compiler projection back into an internal "legacy concept dict" shape in
  `propstore/compiler/context.py`

Known semantic mismatch to remove:

- extensible categories warn at checker time for undeclared literals
- IC-merge currently fails hard on the same shape in the Z3 path

Known documentation mismatch to remove:

- docs still describe fallback behavior that is no longer the desired or
  canonical production contract

## Global Rules

1. No production compatibility shims.
   Old helper surfaces may exist only long enough to complete one focused phase,
   and must be deleted before plan closeout.

2. One runtime semantics only.
   There must not be a second user-facing or production-visible CEL execution
   mode.

3. Unknown concept names remain hard errors everywhere.

4. Open-category support must not weaken unknown-name checking.

5. Docs are part of the implementation.
   A phase that changes CEL semantics is not complete until the corresponding
   docs are updated.

6. The brute-force oracle, if retained, is test-only.

7. After every green slice, reread this plan and continue with the next
   unchecked phase unless explicitly redirected.

## Test Discipline

Every test run in this plan must use this pattern:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
uv run pytest -vv <TEST_SELECTION> 2>&1 | Tee-Object -FilePath "logs/test-runs/<NAME>-$ts.log"
```

Targeted suites for this effort:

- `tests/test_cel_checker.py`
- `tests/test_z3_conditions.py`
- `tests/test_ic_merge.py`
- `tests/test_condition_classifier.py`
- `tests/test_conflict_detector.py`
- `tests/test_world_model.py`
- `tests/test_atms_engine.py`
- `tests/test_resolution_helpers.py`
- `tests/test_claim_compiler.py`

Full-suite closeout:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
New-Item -ItemType Directory -Force logs/test-runs | Out-Null
uv run pytest -vv 2>&1 | Tee-Object -FilePath "logs/test-runs/cel-unification-full-suite-$ts.log"
```

## Semantic Contract For This Plan

### Names

- Unknown concept names are hard errors in checker, solver-backed reasoning,
  activation, conflict detection, and IC-merge.

### Closed categories

- `extensible: false` means the declared `values` are the full domain.
- CEL literals not in that set are hard errors.
- Runtime representation uses closed enum semantics.

### Open categories

- `extensible: true` means the declared `values` are known/common values, not a
  closed domain.
- CEL literals not in that set are semantically valid.
- Checker warnings for undeclared open-category literals are allowed as lint,
  but must not change runtime truth conditions.
- Runtime representation uses symbolic string semantics.

### Open-category reasoning obligations

- `x == 'a'` and `x == 'b'` with distinct literals are disjoint.
- `x != 'a'` is not treated as equivalent to any finite disjunction unless that
  disjunction is stated explicitly.
- `x in ['a', 'b']` means finite membership in those listed literals, not domain
  closure.

## Phase Order

### U0. Freeze the semantic contract in tests

Commit message:

- `test(cel): freeze open and closed category semantics`

Scope:

- `tests/test_cel_checker.py`
- `tests/test_z3_conditions.py`
- `tests/test_ic_merge.py`
- `tests/test_condition_classifier.py`
- add dedicated CEL semantics tests if needed

Work:

- add RED tests for:
  - undeclared literals on extensible categories are semantically valid
  - undeclared literals on non-extensible categories are hard errors
  - open-category equality on different literals is disjoint
  - open-category inequality does not collapse to closed-domain reasoning
  - `in [...]` works under open-category semantics
  - unknown concept names stay hard errors everywhere
- flip existing tests that encode the old IC-merge failure behavior for
  extensible categories

Stop condition:

- the desired category semantics are fully expressed as failing tests before
  implementation changes begin

### U1. Create one canonical CEL registry construction surface

Commit message:

- `refactor(cel): centralize cel registry construction`

Scope:

- `propstore/cel_checker.py` or a new dedicated CEL registry module
- `propstore/compiler/context.py`
- `propstore/world/model.py`
- `propstore/world/resolution.py`
- `propstore/conflict_detector/orchestrator.py`

Work:

- define one canonical registry API for:
  - authored concept payloads
  - loaded concept entries
  - store/sidecar concept rows
  - scoped concept subsets
  - synthetic injected concepts such as `source`
- remove manual `ConceptInfo(...)` construction outside the CEL subsystem
- stop rebuilding equivalent registry logic in world/model and world/resolution

Required RED tests:

- registry builders from authored and sidecar/store inputs produce equivalent
  CEL concept metadata for the same concepts
- scoped registries preserve category openness and values correctly

Stop condition:

- no production caller outside the CEL subsystem constructs `ConceptInfo`
  manually

### U2. Remove the internal legacy concept-dict compatibility path

Commit message:

- `refactor(compiler): delete internal legacy concept registry projection`

Scope:

- `propstore/compiler/context.py`
- `propstore/compiler/passes.py`
- `propstore/sidecar/build.py`
- `propstore/validate_claims.py`
- `tests/test_claim_compiler.py`

Work:

- replace internal "legacy concept dict" projections with canonical concept
  payload/context structures
- rename `_normalize_legacy_concept_record()` if the function survives as a
  modern normalization helper
- delete `compilation_context_from_legacy_registry()` and
  `legacy_concept_registry_for_context*()` unless a test-only helper still needs
  an equivalent local fixture adapter
- update compiler passes and sidecar build to consume canonical context data
  directly

Required RED tests:

- claim compilation and sidecar build no longer require a legacy registry shape
- no production path depends on `compilation_context_from_legacy_registry()`

Stop condition:

- production code no longer manufactures or depends on an internal legacy
  concept-registry dict shape

### U3. Make the Z3 backend the single production CEL runtime

Commit message:

- `feat(cel): unify runtime semantics in z3 backend`

Scope:

- `propstore/z3_conditions.py`
- `propstore/cel_checker.py`
- targeted tests above

Work:

- implement category representation by openness:
  - closed category -> enum semantics
  - extensible category -> string semantics
- ensure checker and runtime agree on:
  - unknown name errors
  - open-category undeclared literals
  - closed-category value rejection
- preserve existing numeric, boolean, arithmetic, division-guard, and caching
  behavior

Required RED tests:

- open-category literals no longer fail translation in runtime reasoning
- closed categories still reject undeclared literals
- equality, inequality, and `in` semantics match the contract above

Stop condition:

- one backend correctly handles all production CEL runtime semantics without
  category mismatches

### U4. Route concrete CEL satisfaction through the unified backend

Commit message:

- `refactor(cel): unify concrete binding evaluation`

Scope:

- `propstore/z3_conditions.py`
- `propstore/repo/ic_merge.py`
- any other production caller doing direct CEL evaluation

Work:

- make the canonical backend own concrete binding evaluation
- define one binding contract for quantity, boolean, closed category, and open
  category values
- reuse solver/backend instances where possible instead of rebuilding per check

Required RED tests:

- concrete satisfaction checks behave identically across world activation and
  IC-merge use cases
- open-category concrete assignments satisfy undeclared-literal comparisons

Stop condition:

- production code no longer evaluates CEL by walking the AST outside the
  unified backend

### U5. Delete the handwritten production evaluator from IC-merge

Commit message:

- `refactor(ic-merge): remove duplicate production cel evaluator`

Scope:

- `propstore/repo/ic_merge.py`
- `tests/test_ic_merge.py`

Work:

- delete `_eval_cel_ast`
- delete `_eval_cel_constraint_bruteforce` from production code
- keep any brute-force oracle in tests only, if still useful for bounded
  verification
- make IC-merge cache or reuse the unified backend for repeated assignment
  checks inside one merge problem

Required RED tests:

- default IC-merge path still proves it is not using the old brute-force path
- bounded-oracle agreement survives if the oracle is moved to test code

Stop condition:

- `propstore/repo/ic_merge.py` contains no independent CEL execution semantics

### U6. Update all production callers to the unified subsystem

Commit message:

- `refactor(cel): migrate all callers to unified subsystem`

Scope:

- `propstore/condition_classifier.py`
- `propstore/conflict_detector/orchestrator.py`
- `propstore/core/activation.py`
- `propstore/world/bound.py`
- `propstore/world/model.py`
- `propstore/world/resolution.py`
- validator and compiler CEL call sites

Work:

- move all callers onto the canonical registry and runtime APIs
- remove dead helper imports and branch logic left over from the split
- ensure world activation, conflict detection, and IC-merge all share the same
  CEL contract

Required RED tests:

- the same CEL expressions produce the same semantic answers across:
  - conflict classification
  - active/inactive claim checks
  - parameter compatibility checks
  - IC-merge constraints

Stop condition:

- search confirms one production CEL runtime path and one registry path

### U7. Update docs and perform final cleanup

Commit message:

- `docs(cel): align docs with unified subsystem`

Scope:

- `README.md`
- `docs/data-model.md`
- `docs/conflict-detection.md`
- `docs/parameterization.md`
- `docs/python-api.md`
- any CEL-relevant CLI docs

Work:

- document open vs closed category semantics explicitly
- document one production backend and remove stale dual-path language
- correct any fallback descriptions that are no longer true
- document that IC-merge, activation, validation, and conflict detection use
  one CEL semantics
- remove any dead code or dead tests left after the migration

Closeout checks:

- `rg -n "_eval_cel_ast|_eval_cel_constraint_bruteforce|compilation_context_from_legacy_registry|legacy_concept_registry_for_context|compatibility shim" propstore tests docs`
- `rg -n "ConceptInfo\\(" propstore | rg -v "propstore/cel_checker.py|propstore/z3_conditions.py|tests"`

Stop condition:

- docs match implementation, dead split code is removed, and no production shim
  surfaces remain

## Final Acceptance Criteria

This plan is complete only when all of the following are true:

1. There is exactly one production CEL runtime backend.
2. There is exactly one canonical CEL registry-construction family.
3. No production handwritten CEL evaluator remains.
4. No production internal legacy concept-registry dict path remains.
5. Extensible categories are open-domain everywhere.
6. Non-extensible categories are closed-domain everywhere.
7. Unknown concept names are hard errors everywhere.
8. Validation, compiler passes, conflict detection, activation, bound-world
   checks, and IC-merge all use the same CEL semantics.
9. Docs describe the new semantics accurately.
10. Targeted suites and the full suite pass.

## Risks To Watch Closely

- accidentally weakening unknown-name failures while opening extensible
  categories
- silently preserving closed-world reasoning for open-category inequality
- breaking IC-merge concept-id to canonical-name binding projection
- leaving world/model or world/resolution on local registry assembly after
  apparent migration
- leaving docs that still describe stale fallback behavior
- moving the old oracle into a hidden production helper instead of a test-only
  reference
