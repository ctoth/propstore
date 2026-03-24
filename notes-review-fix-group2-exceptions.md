# Group 2: Narrow Bare Exception Catches — Session Notes (COMPLETE)

## GOAL
Fix 4 bare `except Exception` catches using TDD (RED then GREEN).

## BASELINE
824 passed, 212 warnings

## DONE
- Read all 4 source locations, verified line numbers match
- Verified exception hierarchy: Z3TranslationError(Exception) at z3_conditions.py:32, z3.Z3Exception is separate

## OBSERVATIONS
- Location 1: condition_classifier.py:85 — `except Exception: return None` in `_try_z3_classify`
- Location 2: algorithms.py:47 — `except Exception: continue` around `ast_compare()`
- Location 3: parameters.py:52 — `except Exception: eq_classes = None` around `partition_equivalence_classes()`
- Location 4: z3_conditions.py:351 — `except Exception: continue` in `partition_equivalence_classes` method

## KEY FINDINGS
- Z3TranslationError inherits from Exception directly (NOT from z3.Z3Exception)
- So both z3.Z3Exception and Z3TranslationError need catching in Z3-related locations
- algorithms.py uses ast_compare from ast_equiv package — ValueError/SyntaxError are the expected failures
- test_condition_classifier.py does NOT exist (needs creation)
- test_conflict_detector.py EXISTS (add to it)
- test_z3_conditions.py EXISTS (add to it)

## API FINDINGS
- ConceptInfo(id, canonical_name, kind, category_values=[], category_extensible=True) — no `values` param
- LoadedClaimFile(filename, filepath, data) — no `path` or `claims` params
- Existing helper: `make_claim_file(claims, filename="test_paper")` in test_conflict_detector.py
- detect_algorithm_conflicts expects LoadedClaimFile with data dict containing claims list
- Need to check how algorithm claims flow through _collect_algorithm_claims

## RED PHASE COMPLETE
- 4 "expected error caught" tests PASS
- 4 "unexpected error propagates" tests FAIL (as expected — bare except Exception catches them)
- Test constructors fixed: ConceptInfo(id=, canonical_name=, kind=), make_claim_file() helper

## GREEN PHASE IN PROGRESS
- Location 1 (condition_classifier.py:85): FIXED — catch (z3.Z3Exception, Z3TranslationError), local imports
- Location 2 (algorithms.py:47): TODO
- Location 3 (parameters.py:52): TODO
- Location 4 (z3_conditions.py:351): TODO

## NEXT
- Apply remaining 3 GREEN fixes
- Run tests
- Commit all changes
- Write report
