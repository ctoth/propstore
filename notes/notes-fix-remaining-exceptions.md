# Fix Remaining 7 Bare except Exception Catches

## GOAL
Narrow 7 bare `except Exception` catches to specific types with logging, TDD style.

## BASELINE
842 passed, 222 warnings

## OBSERVATIONS FROM READING ALL 7 LOCATIONS

### Location 1: build_sidecar.py:250
- Embedding snapshot failure. Calls `extract_embeddings`, `_load_vec_extension`, `sqlite3.connect`.
- Already has `except ImportError` above. The broad catch is for graceful degradation.
- DECISION: Keep `except Exception` but add `logging.warning`. This is intentionally broad - embedding snapshot is optional.

### Location 2: cli/helpers.py:57
- `yaml.safe_load(entry.read_text())` in `_scan_max_concept_id`
- Should catch `yaml.YAMLError` specifically.
- Also could get `OSError` from `read_text()`, but that's a different concern - probably should propagate.

### Location 3: embed.py:226
- `litellm.embedding(model=model_name, input=texts)` call
- litellm is imported via `_require_litellm()` lazily. No direct import at top.
- Need to check what litellm exceptions look like. Will use `(Exception,)` pattern with litellm-specific if available.
- The function already has `litellm` in local scope from earlier call.

### Location 4: param_conflicts.py:147
- `_cached_parse(sympy_expr_str, tuple(inputs))` then `float(expr.subs(input_values))`
- SymPy errors: SympifyError, TypeError, ValueError, ZeroDivisionError
- Already has `warnings.warn` in the handler - good.

### Location 5: relate.py:154
- `await litellm.acompletion(...)` call
- Same litellm pattern as Location 3.

### Location 6: sympy_generator.py:50
- `parse_expr(text)` call
- Should catch `(SympifyError, TypeError, ValueError, SyntaxError)`

### Location 7: world/value_resolver.py:162
- `ast_compare(...)` call - Z3 equivalence check
- Should catch Z3-specific exceptions. Need to check what's imported/used elsewhere.

## KEY FINDINGS FROM READING
- Z3 pattern already established: catch `(Z3TranslationError, z3.Z3Exception)` with local imports
- ast_compare pattern: catch `(ValueError, SyntaxError)` — established in algorithms.py:48
- sympy parse_expr: catch `(SympifyError, TypeError, ValueError, SyntaxError)` — SympifyError already imported in sympy_generator.py
- litellm: imported lazily via `_require_litellm()`, no direct top-level import
- ActiveClaimResolver constructor requires: parameterizations_for, is_param_compatible, value_of, extract_variable_concepts, collect_known_values, extract_bindings
- _embed_entities signature: (conn, model_name, config, entity_ids=None, batch_size=64, on_progress=None)
- build_sidecar embedding snapshot code is inline (no separate function), imports locally

## STATUS
- RED tests written (v2, fixed constructor args and signatures)
- Need to run RED tests to confirm they fail for the right reason
- Then GREEN phase: fix each of the 7 source locations
- Then full test suite verification

## GREEN PHASE IN PROGRESS
- Location 1 (build_sidecar.py): DONE — kept broad catch, added logging.warning + comment
- Location 2 (cli/helpers.py): DONE — narrowed to yaml.YAMLError, added logging
- Location 3 (embed.py): DONE — narrowed to (ConnectionError, TimeoutError, OSError, ValueError)
- Location 4 (param_conflicts.py): DONE — narrowed to (SympifyError, TypeError, ValueError, ZeroDivisionError, AssertionError). Need to add SympifyError import.
- Location 5 (relate.py): TODO
- Location 6 (sympy_generator.py): TODO
- Location 7 (value_resolver.py): TODO

## GREEN PHASE RESULTS (first run)
- 5 of 7 tests pass
- Embed test fails: sqlite conn needs row_factory=sqlite3.Row (fixed)
- Param conflicts test fails: mock not reaching the code path. The function uses `parameterization_relationships` (not `parameterization`) in concept_data. My test data has `parameterization` key. Also inputs need `form` set to non-category. The loop skips because:
  1. It looks for `parameterization_relationships` list, not `parameterization` dict
  2. It checks `rel.get("exactness") == "exact"`
  3. It checks all inputs have non-category form
  4. It checks all inputs have scalar claims

## NEXT
- Fix param_conflicts test data to match actual code path
- Fix embed test (row_factory done)
- Run tests again, then full suite, then commit
