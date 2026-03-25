# Error Handling Audit — 2026-03-24

Systematic review of all `.py` files under `propstore/`, `propstore/cli/`,
`propstore/conflict_detector/`, and `propstore/world/` for silent failures,
swallowed exceptions, inadequate error handling, and related defects.

---

## 1. Bare `except` / `except Exception` that swallow errors

### F1.1 — `structured_argument.py:205` — bare `except Exception`
```python
except Exception:
    has_conditions = True
```
In `_default_support_metadata`, a bare `except Exception` catches any JSON
decode failure on `conditions_cel` and silently assumes conditions exist.
This hides malformed data. The same pattern appears in `bound.py:744-747`
(`_support_quality`).

### F1.2 — `build_sidecar.py:256-260` — intentionally broad except
```python
except Exception as exc:
    logging.warning("Embedding snapshot failed: %s", exc)
```
Catches all exceptions during embedding snapshot. While documented as
intentional, this swallows `KeyboardInterrupt` since it catches `Exception`
not `BaseException` -- wait, actually the outer try/except at line 332 catches
`BaseException`, so this is fine for Exception. However, it still swallows
`MemoryError`, `SystemExit` subclasses of Exception, etc. The comment says
"intentionally broad" but does not list which specific exceptions are expected.

### F1.3 — `build_sidecar.py:321` — `except (ImportError, Exception)`
```python
except (ImportError, Exception) as exc:
```
`ImportError` is a subclass of `Exception`, so listing both is redundant. More
importantly, this catches everything during embedding restore and only prints
a warning. A corrupted restore could silently produce an inconsistent sidecar.

### F1.4 — `worldline_runner.py:179` — bare `except Exception`
```python
except Exception:
    logger.warning("sensitivity analysis failed for %s", target_name, exc_info=True)
```
Sensitivity analysis failure is silently swallowed. The worldline result will
contain no sensitivity data with no indication to the caller that it was
attempted and failed.

### F1.5 — `worldline_runner.py:266` — bare `except Exception`
```python
except Exception:
    logger.warning("argumentation capture failed", exc_info=True)
```
Same pattern: argumentation state capture failure is silently swallowed.

### F1.6 — `embed.py:198-199` — `except sqlite3.OperationalError: pass`
```python
except sqlite3.OperationalError:
    pass  # table doesn't exist yet
```
Swallows ALL OperationalError, not just "table not found". A disk-full error,
permission error, or corruption error would be silently ignored.

### F1.7 — `embed.py:368-369` — same pattern
```python
except sqlite3.OperationalError:
    return []
```
`get_registered_models` returns empty list on any database error, not just
missing table.

### F1.8 — `embed.py:443-444` — `except ValueError: pass`
```python
except ValueError:
    pass
```
In `_find_similar_disagree_generic`, a ValueError during embedding lookup is
silently swallowed. Could hide a real data integrity issue.

### F1.9 — `embed.py:526-527`, `547-548`, `557`, `572-573`
Multiple `except sqlite3.OperationalError` blocks that swallow errors during
embedding extraction/restore. All assume "table doesn't exist" but catch
every possible DB error.

### F1.10 — `build_sidecar.py:498` — bare `except Exception`
```python
except Exception:
    operation = sympy_str
```
In `_populate_form_algebra`, any sympy parsing failure silently falls back to
the raw string. No logging, no warning.

### F1.11 — `build_sidecar.py:536-537` — bare `except Exception`
```python
except Exception:
    canon_op = operation
```
Same function, canonical dump failure silently uses raw operation string.

---

## 2. Fallback to default values that hide real errors

### F2.1 — `calibrate.py:28` — `_softmax` division
```python
return [e / total for e in exps]
```
If all logits are extremely negative, `total` could be zero (all exps
underflow to 0.0). This would produce `nan` or `inf` values silently.
No guard on `total == 0`.

### F2.2 — `form_utils.py:199` — logarithmic `from_si` with zero/negative
```python
return conv.divisor * math.log(si_value / conv.reference, conv.base)
```
If `si_value <= 0` or `conv.reference <= 0`, `math.log` raises
`ValueError`/`math domain error`. No guard. If `conv.base` is 1, `math.log`
also raises. The forward path (`normalize_to_si`) has the same issue with
`conv.base ** (value / conv.divisor)` when `conv.divisor == 0`.

### F2.3 — `preference.py:87` — claim_strength returns `[1.0]` default
```python
if not dims:
    return [1.0]  # neutral default for claims with no metadata
```
When claims lack ALL metadata (sample_size, uncertainty, confidence), they get
strength `[1.0]`. This means two claims with no metadata are considered equally
strong, and the elitist/democratic comparison cannot distinguish them. This is
a design choice but it means that argumentation-based resolution silently
treats unknown-strength claims as strong.

### F2.4 — `relate.py:152-166` — API failure returns "none" stance
When the LLM API call fails (ConnectionError, etc.), the function returns
`type: "none"` with `confidence: 0.0`. This is indistinguishable in the
output from a genuine "no relationship" classification. The `note` field
says "classification failed" but downstream consumers may not check it.

### F2.5 — `relate.py:171-186` — JSON parse failure returns "none" stance
Same pattern: malformed LLM response returns "none" with no indication to
downstream that it was a parse failure rather than a genuine classification.

### F2.6 — `propagation.py:63` — evaluate_parameterization returns None
```python
except (TypeError, ValueError, ZeroDivisionError, AttributeError):
    return None
```
All evaluation errors return `None`, which callers interpret as "can't derive".
A real bug (e.g., wrong variable names in sympy expression) looks identical
to "insufficient inputs".

### F2.7 — `equation_comparison.py:54-55` — SymPy ImportError returns None
```python
except ImportError:
    return None
```
If SymPy is not installed, `canonicalize_equation` silently returns None,
making all equation claims appear non-comparable. No warning.

---

## 3. Unchecked return values / None not checked

### F3.1 — `argumentation.py:162-163` — `.get()` with empty dict default
```python
attacker_claim = claims_by_id.get(source_id, {})
target_claim = claims_by_id.get(target_id, {})
```
If a claim ID is not found (data inconsistency), `claim_strength({})` is
called with an empty dict, returning `[1.0]`. This silently treats missing
claims as having neutral strength rather than flagging the inconsistency.

### F3.2 — `praf.py:267` — KeyError on missing defeat probability
```python
p_d = praf.p_defeats[(f, t)].expectation()
```
In `_sample_subgraph`, if a defeat is in the framework but not in
`p_defeats`, this raises `KeyError`. The `build_praf` function in
`argumentation.py:220-227` handles derived defeats by inserting
`dogmatic_true()`, but if there is any code path that constructs a
`ProbabilisticAF` without complete `p_defeats`, this will crash.

### F3.3 — `worldline_runner.py:411` — `vr.claims[0]` without empty check
```python
claim = vr.claims[0] if vr.claims else {}
```
This is technically guarded, but the empty-dict fallback means
`claim.get("value")` returns `None`, and the step records
`claim_id: None`. Downstream code that expects a real claim ID
will silently receive None.

### F3.4 — `sensitivity.py:104` — `vr.claims[0].get("value")`
```python
val = vr.claims[0].get("value") if vr.claims else None
```
If the first claim has no value field, `val` is None and the function
returns None (line 117), but the caller in worldline_runner has no way
to distinguish "input has no value" from "input not found".

---

## 4. Division by zero risks

### F4.1 — `argumentation.py:346-347` — mean of claim_strength dimensions
```python
for dims in [claim_strength(claims_by_id[cid])]
```
`claim_strength` always returns at least `[1.0]`, so `len(dims)` is always
>= 1. However, the expression `sum(dims) / len(dims)` is in a dict
comprehension that filters on `cid in claims_by_id`. If `claims_by_id` is
empty, `strengths` would be empty. The downstream `resolve_conflicts` handles
empty `claim_strengths` by returning `frozenset()`.

### F4.2 — `form_utils.py:176` — logarithmic conversion divisor
```python
return conv.reference * conv.base ** (value / conv.divisor)
```
If `conv.divisor == 0`, this is a `ZeroDivisionError`. No guard. The
`UnitConversion` dataclass defaults `divisor=1.0` but there is no validation
that it is non-zero.

### F4.3 — `form_utils.py:199` — reverse logarithmic conversion
```python
return conv.divisor * math.log(si_value / conv.reference, conv.base)
```
If `conv.reference == 0`, `ZeroDivisionError`. If `conv.base == 1`,
`ZeroDivisionError` from `math.log`.

### F4.4 — `praf.py:387` — counts[a] / n when n could be 0
```python
all_acceptance[a] = counts[a] / n
```
`n` starts at 0 and increments in the while loop. The loop always executes
at least once (no early break before increment), so `n >= 1`. Safe in
practice, but there is no explicit guard.

### F4.5 — `sensitivity.py:147` — elasticity division
```python
elasticity = partial_val * x_val / output_value
```
Guarded by `output_value != 0` check on line 145. But `x_val` could be 0,
which is valid (elasticity would be 0). No issue here. However, if
`output_value` is very close to zero but not exactly zero, the elasticity
could be extremely large with no capping.

---

## 5. Float comparison with `==`

### F5.1 — `value_comparison.py:167` — float equality
```python
if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
    return abs(float(value_a) - float(value_b)) < tolerance
```
This is correct (uses tolerance). Good.

### F5.2 — `hypothetical.py:143` — direct float equality
```python
if val_a != val_b:
```
In `recompute_conflicts`, values from claims are compared with `!=` directly.
These could be floats. Two measurements of the same quantity that differ by
floating-point rounding would be flagged as conflicts. The proper conflict
detector uses tolerance-based comparison, but this shortcut path does not.

### F5.3 — `praf.py:249` — float equality for tied PrAF acceptance
```python
best_claims = [cid for cid, p in target_probs.items() if p == best_prob]
```
In `resolution.py:248`, acceptance probabilities are compared with `==`.
MC-sampled probabilities could differ by tiny floating-point amounts,
producing false "ties" or false "single winners".

### F5.4 — `description_generator.py:60` — float-int comparison
```python
if isinstance(n, int) or (isinstance(n, float) and n == int(n)):
```
`n == int(n)` is exact float comparison. For large floats, `int(n)` could
overflow or lose precision. For values like `1.0000000000000002`, this
incorrectly treats them as integers.

---

## 6. Mutable default arguments

### F6.1 — `argumentation.py:33` — `visited: set[str] | None = None`
```python
def _transitive_support_targets(
    source: str,
    supports: set[tuple[str, str]],
    visited: set[str] | None = None,
) -> set[str]:
    if visited is None:
        visited = set()
```
This is the correct pattern (None default, create inside). Not a bug.

No mutable default argument bugs found. The codebase consistently uses
`field(default_factory=...)` for dataclass fields and `None` defaults
with creation inside function bodies.

---

## 7. Global state mutation

### F7.1 — `form_utils.py:56` — module-level form cache
```python
_form_cache: dict[tuple[str, str], FormDefinition | None] = {}
```
Module-level mutable dict. `load_form()` populates it and never clears it.
In long-running processes or tests, stale cache entries persist. If a form
YAML file is modified on disk, the cache returns stale data. No invalidation
mechanism. No thread safety.

### F7.2 — `form_utils.py:306` — module-level schema cache
```python
_form_schema_cache: dict | None = None
```
Same pattern. `_load_form_schema()` caches forever with no invalidation.

### F7.3 — `unit_dimensions.py:33` — module-level symbol table
```python
_symbol_table: dict[str, Dimensions] | None = None
```
Lazy-loaded, never invalidated. `register_form_units()` mutates it in place
(line 71: `table[symbol] = ...`). Multiple calls to `register_form_units()`
with different forms_dirs accumulate entries from all calls. This is a silent
cross-contamination risk in tests or multi-repo scenarios.

### F7.4 — `resources.py:13` — module-level development mode flag
```python
_DEVELOPMENT_MODE: bool | None = None
```
Cached permanently. If the `.git` directory is created or removed during
process lifetime, the cached value is wrong.

### F7.5 — `propagation.py:14` — LRU cache on parse_cached
```python
@functools.lru_cache(maxsize=128)
def parse_cached(expr_str: str, symbol_names: tuple[str, ...]):
```
This caches SymPy parse results globally. The cache key includes symbol
names but not any context. Since SymPy Symbol objects are module-global
singletons, this is safe for correctness but the cache never shrinks
(LRU eviction is the only cleanup).

---

## 8. Assertion used for runtime validation

### F8.1 — `param_conflicts.py:180` — assert for runtime check
```python
assert isinstance(sympy_expr_str, str)
```
This is caught by `except (..., AssertionError)` on line 188, so it is
effectively used as a runtime type check. If Python runs with `-O`, this
assertion is stripped, and the `evaluate_parameterization` call receives
a non-string, likely causing a different, harder-to-diagnose error.

### F8.2 — `param_conflicts.py:356` — assert for type narrowing
```python
assert not isinstance(derived_context, _Sentinel)
```
Same concern: used for runtime narrowing, disabled under `-O`.

### F8.3 — `form_utils.py:315` — assert for None check
```python
assert _form_schema_cache is not None
```
If `json.load` returns None (empty/malformed JSON), this assertion fires.
Under `-O`, `_load_form_schema` returns None, and `jsonschema.validate`
receives None as schema, producing a confusing error.

### F8.4 — `praf_treedecomp.py:603,703` — assert in DP loops
```python
assert v is not None
```
In introduce/forget node processing. If the nice tree decomposition has a
bug, this fires. Under `-O`, `v` would be None and the downstream dict
lookups would KeyError with no useful context.

### F8.5 — `world/model.py:337` — assert after None narrowing
```python
assert model_name is not None  # narrowed above
```
Pattern used in `similar_claims` and `similar_concepts`. Safe in normal
operation but fragile under `-O`.

---

## 9. Resource leaks

### F9.1 — `build_sidecar.py:269` — sqlite connection not in context manager
```python
conn = sqlite3.connect(sidecar_path)
try:
    ...
except BaseException:
    conn.close()
    ...
    raise
conn.close()
```
The try/except/finally pattern is manually managed. If an exception occurs
between `conn = sqlite3.connect(...)` and the `try:` block (unlikely but
possible if the Python runtime raises an async exception), the connection
leaks. A `with` statement or try/finally would be more robust.

### F9.2 — `world/model.py:56-57` — connection opened without context manager
```python
self._conn = sqlite3.connect(sidecar_path)
```
The `WorldModel` implements `__enter__`/`__exit__` but if constructed
without `with`, the connection stays open until garbage collection.
The `close()` method exists but must be called manually.

---

## 10. Missing error paths (if/elif without else)

### F10.1 — `cel_checker.py:432-444` — _resolve_type for UnaryOpNode
The function handles `node.op == "!"` and `node.op == "-"` but has no
else branch. If a new unary operator is added to the parser without
updating this function, `_resolve_type` falls through to the next
isinstance check and eventually returns `ExprType.UNKNOWN` silently.

### F10.2 — `build_sidecar.py:1143-1160` — _extract_typed_claim_fields
The chain of `if ctype == ...` / `elif ctype == ...` has no final `else`.
Unrecognized claim types silently get all-None fields. The validator
catches unrecognized types, but if validation is skipped (e.g., force
build), this produces silent data loss.

---

## 11. SQL injection surface

### F11.1 — `embed.py:105-112` — f-string in SQL
```python
conn.execute(
    f"CREATE VIRTUAL TABLE [{table_name}] USING vec0(embedding float[{dimensions}])"
)
```
`table_name` is derived from `_sanitize_model_key(model_name)` which strips
non-alphanumeric characters. `dimensions` is an integer from the API response.
The sanitization prevents SQL injection through the table name, but the
bracket-quoting `[{table_name}]` is the defense. If `_sanitize_model_key`
were changed, this would become injectable. The `dimensions` value is not
sanitized but is always an integer from the embedding API.

### F11.2 — `embed.py:246` and multiple other places
```python
conn.execute(f"DELETE FROM [{table_name}] WHERE rowid = ?", (seq,))
```
Same pattern throughout `embed.py`. Table names are f-string interpolated
but bracket-quoted and sanitized. Parameters use `?` placeholders. This is
acceptable given the sanitization but fragile.

---

## 12. Silent type coercion

### F12.1 — `build_sidecar.py:1165` — float coercion without validation
```python
value = float(raw_value) if raw_value is not None else None
```
In `_extract_numeric_claim_fields`, if `raw_value` is a non-numeric string
(e.g., "N/A"), `float()` raises `ValueError`. This propagates up to
`_populate_claims` and aborts the entire sidecar build. There is no graceful
handling or per-claim error reporting.

### F12.2 — `value_comparison.py:44` — float coercion in extract_interval
```python
return (float(value), float(lower_bound), float(upper_bound))
```
Same pattern: if any of these are non-numeric strings, `float()` raises
with no per-claim context in the error message.

---

## 13. Z3 condition solver state leak

### F13.1 — `z3_conditions.py:277` — `_current_guards` as instance state
```python
self._current_guards: list[Any] = []
```
In `_condition_to_z3`, `_current_guards` is set as an instance attribute
before translating. If `_translate` is called recursively or concurrently,
the guards list could be corrupted. The cache on line 276 means the guards
are only collected on first translation, but if two conditions share a
sub-expression, the second translation reuses the cached result and the
guards from the first call are already baked in. This is probably correct
for single-threaded use but is fragile.

---

## Summary of severity

**High (data correctness risk):**
- F1.6, F1.7, F1.8, F1.9: OperationalError swallowing hides DB corruption
- F2.4, F2.5: LLM failures indistinguishable from "no relationship"
- F5.2: Direct float `!=` in conflict detection (false positives/negatives)
- F5.3: Float `==` on MC-sampled probabilities (unstable resolution)
- F7.1, F7.3: Global mutable caches with no invalidation
- F8.1, F8.2: Runtime assertions disabled under `-O`

**Medium (operational risk):**
- F1.4, F1.5: Silent swallowing of analysis failures
- F2.2, F4.2, F4.3: Division by zero in unit conversion
- F3.2: Missing defeat in PrAF causes KeyError crash
- F12.1: Non-numeric claim value aborts entire build

**Low (code quality / defense in depth):**
- F1.2, F1.3, F1.10, F1.11: Over-broad exception handling
- F2.3, F2.6, F2.7: Silent None returns hide root causes
- F7.2, F7.4, F7.5: Permanent global caches (low risk in practice)
- F8.3, F8.4, F8.5: Assertions for type narrowing
- F9.1, F9.2: Manual connection lifecycle management
- F11.1, F11.2: SQL via f-string (mitigated by sanitization)
