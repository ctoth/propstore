# Analyst Final Review Notes

**GOAL:** Verify all 8 coding groups addressed issues, no regressions.

## DONE - Checks Completed

### Check 1: Full test suite - PASS
- 841 passed, 0 failures, 222 warnings
- Warnings are all about sympy parameterization eval -- pre-existing

### Check 2: Sidecar build - PASS
- "Build unchanged: 250 concepts, 410 claims, 0 conflicts, 0 warnings"

### Check 3: World model loads - PASS
- Concepts: 250, Claims: 410, Conflicts: 0

### Check 4: Bare except Exception - FAIL
- 8 remaining `except Exception` in propstore source
- `build_sidecar.py:250` -- catches embedding snapshot failure, logged. Arguably justified as last-resort for optional feature.
- `cli/helpers.py:57` -- YAML parse error catch. Should be `yaml.YAMLError`.
- `embed.py:226` -- litellm API call. Should be `litellm.exceptions.*` or at minimum `(APIError, Timeout, ConnectionError)`.
- `conflict_detector/parameters.py:213` -- Z3 solver fallback. Should be specific Z3 exception.
- `param_conflicts.py:147` -- SymPy eval. Should be `(SympifyError, TypeError, ValueError)`.
- `relate.py:154` -- litellm API call. Same as embed.py.
- `sympy_generator.py:50` -- parse_expr. Should be `(SympifyError, TypeError, ValueError)`.
- `world/value_resolver.py:162` -- Z3 equivalence check. Should be specific exception.

### Check 5: Private access outside bound.py - PARTIAL PASS
- `_is_active` not found anywhere (good - was removed or renamed)
- `value_resolver.py` stores injected callables as `self._is_param_compatible` etc. -- these are INSTANCE ATTRIBUTES on ValueResolver itself, not accessing bound.py privates. This is fine -- dependency injection pattern.

### Check 6: type: ignore[union-attr] - FAIL
- `validate_claims.py:607-608` -- two occurrences on repo.concepts_dir, repo.forms_dir
- `world/bound.py:131` -- on context_hierarchy.ancestors()
- `world/model.py:41` -- on repo.sidecar_path
- The check asked specifically about build_sidecar.py and validate.py. validate_claims.py still has them.

### Check 7: Git log - ISSUE
- I count 7 commits from this session, not 8:
  1. 109e643 Type repo parameter as Repository, remove type: ignore comments
  2. cdb8fbe Refactor claim INSERT from positional tuple to named dict
  3. 6d4d5ed Make BoundWorld collaborator methods public, fix CEGAR docstring
  4. b6bb887 Cache _has_table and conflicts, fix O(n^2) embedding scan and O(n*m) list conversion
  5. ac922bc Fix claim_strength normalization: divide by component count
  6. 947b34b Narrow bare except Exception catches to specific types with logging
  7. 61b8aee Extract shared test helpers into conftest.py, fix sleep-based mtime test
- Missing: one commit. Need to verify what the 8th group was supposed to be.

### Check 8: Spot-check key fixes
- preference.py:87 `return score / components` -- PASS
- dung_z3.py CEGAR removed -- PASS
- model.py _has_table has cache (_table_cache dict) -- PASS
- bound.py conflicts has cache (_conflicts_cache dict) -- PASS
- build_sidecar.py _prepare_claim_insert_row returns dict -- PASS

## ISSUES FOUND

1. **8 bare `except Exception` remain** in propstore source. Commit 947b34b claimed to narrow these but clearly didn't catch all of them.
2. **type: ignore[union-attr] remains** in validate_claims.py (2 occurrences), bound.py (1), model.py (1). Commit 109e643 claimed to remove these but missed validate_claims.py. The check specifically asked about validate.py (which may mean validate_claims.py).
3. **Only 7 commits visible, not 8.** Need to verify.

## NEXT
- Write final report
