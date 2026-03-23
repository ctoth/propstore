# Fix Remaining 7 Bare `except Exception` Catches — Report

## Summary

Narrowed 7 remaining bare `except Exception` catches to specific exception types with logging. One location (build_sidecar embedding snapshot) intentionally kept a broad catch with logging and documentation.

## Test Count

- **Before:** 842 passed
- **After:** 849 passed (7 new tests added)
- **Regressions:** 0

## Changes by Location

### Location 1: `propstore/build_sidecar.py:250`
- **Before:** `except Exception as exc:` with `print()` to stderr
- **After:** `except Exception as exc:` with `logging.warning()` and explanatory comment
- **Rationale:** Kept broad catch intentionally. Embedding snapshot is optional graceful degradation — any failure (sqlite-vec issues, corrupt DB, missing extensions) should not block sidecar rebuild. Added comment documenting the design decision.

### Location 2: `propstore/cli/helpers.py:57`
- **Before:** `except Exception: continue`
- **After:** `except yaml.YAMLError: logging.warning(...); continue`
- **Rationale:** Only YAML parsing errors should be swallowed during concept ID scanning. Other errors (RuntimeError, OSError from read_text) should propagate.

### Location 3: `propstore/embed.py:226`
- **Before:** `except Exception: errors += len(batch); continue`
- **After:** `except (ConnectionError, TimeoutError, OSError, ValueError) as exc: logging.warning(...); errors += len(batch); continue`
- **Rationale:** litellm API calls can fail with network/connection errors. These are expected transient failures. RuntimeError and other unexpected errors should propagate.

### Location 4: `propstore/param_conflicts.py:147`
- **Before:** `except Exception:` with `warnings.warn()`
- **After:** `except (SympifyError, TypeError, ValueError, ZeroDivisionError, AssertionError):` with same warning
- **Rationale:** SymPy `parse_expr` and `subs`/`float()` can raise these specific exceptions. `SympifyError` for invalid expressions, `TypeError`/`ValueError` for type mismatches, `ZeroDivisionError` for division by zero, `AssertionError` from the `assert isinstance()` guard.

### Location 5: `propstore/relate.py:154`
- **Before:** `except Exception:` returning failure dict
- **After:** `except (ConnectionError, TimeoutError, OSError, ValueError) as exc:` with `logging.warning()` returning failure dict
- **Rationale:** Same pattern as Location 3 — litellm async API call. Network/API errors are expected; other errors should propagate.

### Location 6: `propstore/sympy_generator.py:50`
- **Before:** `except Exception as exc:` returning error result
- **After:** `except (SympifyError, TypeError, ValueError, SyntaxError, TokenError) as exc:` with `logging.warning()` returning error result
- **Rationale:** `parse_expr` can raise these specific sympy/parsing exceptions. `TokenError` was already imported in the file. Unexpected errors should propagate.

### Location 7: `propstore/world/value_resolver.py:162`
- **Before:** `except Exception: return False`
- **After:** `except (ValueError, SyntaxError) as exc: logging.warning(...); return False`
- **Rationale:** `ast_compare` raises `ValueError` or `SyntaxError` on parse/comparison failures. Same pattern already established in `conflict_detector/algorithms.py:48`.

## Locations Keeping Broad Catches

Only **Location 1** (`build_sidecar.py`) kept the broad `except Exception` catch, with added logging and a comment explaining why. Embedding snapshot is an optional optimization — any failure should degrade gracefully.

## Files Changed

- `propstore/build_sidecar.py` — added `import logging`, replaced `print()` with `logging.warning()`, added explanatory comment
- `propstore/cli/helpers.py` — added `import logging`, narrowed to `yaml.YAMLError`
- `propstore/embed.py` — added `import logging`, narrowed to `(ConnectionError, TimeoutError, OSError, ValueError)`
- `propstore/param_conflicts.py` — added `SympifyError` import, narrowed to `(SympifyError, TypeError, ValueError, ZeroDivisionError, AssertionError)`
- `propstore/relate.py` — added `import logging`, narrowed to `(ConnectionError, TimeoutError, OSError, ValueError)`
- `propstore/sympy_generator.py` — added `import logging`, narrowed to `(SympifyError, TypeError, ValueError, SyntaxError, TokenError)`
- `propstore/world/value_resolver.py` — added `import logging`, narrowed to `(ValueError, SyntaxError)`
- `tests/test_exception_narrowing_group3.py` — 7 new tests
