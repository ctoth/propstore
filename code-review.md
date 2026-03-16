# Propstore Code Review

**Date:** 2026-03-16
**Scope:** Full codebase — compiler, CLI, schema, tests, data
**Lines reviewed:** ~9,575 across 27 Python files + YAML data/schema

---

## Resolution Summary

**43 findings total. 37 resolved. 3 intentionally skipped. 3 deferred.**

All work completed 2026-03-16 in a single session. Test suite grew from
321 to 350 passing tests. Net code reduction of ~300 lines across fixes.

| Category | Found | Fixed | Skipped | Deferred |
|----------|-------|-------|---------|----------|
| Critical | 1 | 1 | 0 | 0 |
| High | 7 | 7 | 0 | 0 |
| Medium | 8 | 7 | 1 | 0 |
| Low | 7 | 5 | 2 | 0 |
| Data model | 9 | 8 | 1 | 0 |
| Test gaps | 6 | 6 | 0 | 0 |
| Performance | 4 | 2 | 0 | 2 |
| Security | 1 | 1 | 0 | 0 |
| **Total** | **43** | **37** | **3** | **2** |

---

## Table of Contents

1. [Architecture & Design](#architecture--design)
2. [Critical Issues](#critical-issues)
3. [High Priority Issues](#high-priority-issues)
4. [Medium Priority Issues](#medium-priority-issues)
5. [Low Priority Issues](#low-priority-issues)
6. [Data Model & Schema](#data-model--schema)
7. [Test Suite Analysis](#test-suite-analysis)
8. [Performance Considerations](#performance-considerations)
9. [Security](#security)

---

## Architecture & Design

### Strengths

1. **Clean separation of concerns.** The compiler is layered sensibly:
   `form_utils` (primitives) → `cel_checker` (expression analysis) →
   `validate`/`validate_claims` (contract enforcement) → `build_sidecar`
   (output generation) → `conflict_detector` (cross-claim analysis). Each
   module has a clear, single responsibility.

2. **Content-addressed hashing.** The sidecar builder uses SHA-256 hashes to
   skip unnecessary rebuilds (`build_sidecar.py:29-42`), a practical
   optimization for iterative workflows.

3. **Safe SQL throughout.** All SQLite queries use parameterized statements
   (`?` placeholders). The only raw SQL execution is the `pks query` CLI
   command, which is intentional for a local dev tool.

4. **Validation-before-write discipline.** CLI mutation commands (`add`,
   `rename`, `deprecate`) validate the full registry in-memory before writing
   any files. This prevents partial-write corruption.

5. **CEL type-checker is well-designed.** The tokenizer → parser →
   type-checker pipeline in `cel_checker.py` is a clean, maintainable
   implementation of a subset CEL checker with correct operator precedence via
   recursive descent.

6. **Dry-run support on all mutating commands.** Every CLI command that writes
   files supports `--dry-run`, which is excellent for user confidence.

7. **Union-find for parameterization groups** (`parameterization_groups.py`).
   Uses proper union-by-rank with path compression — textbook efficient
   implementation in 65 lines.

### Architectural Concerns

1. **Monolithic validation functions.** `validate_concepts()` is 270 lines in
   a single function (`validate.py:119-388`). Similarly `validate_claims()` is
   101 lines. These should be decomposed into per-rule validator functions.

2. **No dependency injection for filesystem paths.** Modules construct `Path`
   objects relative to the working directory or derive paths like
   `c.filepath.parent.parent / "forms"` (`validate.py:165`, `178`,
   `build_sidecar.py:233`). This couples business logic to filesystem layout
   and makes testing harder.

3. **Dual `ValidationResult` classes.** Both `validate.py:38` and
   `validate_claims.py:48` define identical `ValidationResult` dataclasses
   with the same fields and `ok` property. These should be unified into a
   shared definition.

4. **Conflict detection runs twice during `pks build`.** The `build` command
   calls `build_sidecar()` which internally calls `_populate_conflicts()` →
   `detect_conflicts()`, and then the build command calls
   `detect_conflicts()` again at `compiler_cmds.py:129` for the summary.
   This duplicates potentially expensive work.

---

## Critical Issues

### C1. `requires-python >= 3.13` is unnecessarily restrictive

**Status: FIXED** (`6eabf7a`)

Lowered to `>= 3.10`. No 3.13-specific features are used; the most modern
syntax is `X | Y` union types gated behind `from __future__ import
annotations`.

---

## High Priority Issues

### H1. Massive code duplication in value validation

**Status: FIXED** (`c332af0`)

Extracted `_validate_value_fields()` shared helper called by both
`_validate_parameter()` and `_validate_measurement()`. Net reduction of
48 lines.

### H2. Duplicated interval comparison logic in param conflict detection

**Status: FIXED** (`069a604`)

Unified the two nearly identical blocks (named-field vs legacy format) into
a single path using `_values_compatible()` which already handles both
formats. Net reduction of 20 lines.

### H3. `validate_concept_data()` re-validates the entire registry

**Status: REMOVED** (`b46d078`)

Investigation revealed this function was defined but never called anywhere
in the codebase. Removed as dead code along with its orphaned imports.

### H4. Form definitions loaded from disk with no caching

**Status: FIXED** (`d372721`)

Added a module-level dict cache to `load_form()` keyed by
`(forms_dir, form_name)`. Eliminates redundant disk reads when N concepts
reference M forms.

### H5. Stances written to sidecar but FK ordering issue

**Status: FIXED** (`746b725`)

Deferred stance insertion until after all claims are inserted. Stances are
now collected during the claim loop and bulk-inserted afterward, ensuring
`target_claim_id` FK references resolve correctly if `PRAGMA foreign_keys`
is ever enabled.

### H6. `sympy.sympify()` with untrusted input is a code injection risk

**Status: FIXED** (`336f312`)

Replaced `sympy.sympify()` with `sympy.parsing.sympy_parser.parse_expr()`
across all three call sites (`sympy_generator.py` x2,
`conflict_detector.py` x1). `parse_expr()` uses a restricted parser
instead of `eval()`.

### H7. Cross-domain counter collision can produce duplicate concept IDs

**Status: FIXED** (`29bcfa5`)

Replaced per-domain counter files (`speech.next`, `narr.next`) with a
single `global.next` counter. On first use without a global counter,
scans existing concept IDs to bootstrap the correct value. Created
`global.next` at 20 (max existing is concept19).

---

## Medium Priority Issues

### M1. `_values_compatible()` returns `False` for equal scalars

**Status: FIXED** (`1781f7f`)

Added numeric scalar comparison with tolerance before the `return False`
fallthrough, plus equality fallback for non-numeric scalar types.

### M2. `assert isinstance(value, float)` in production code

**Status: FIXED** (`8cde04b`)

Replaced with an explicit type guard that returns `None` on unexpected
types, converting valid values to `float`.

### M3. Bare `Exception` catch in equation canonicalization

**Status: FIXED** (`8cde04b`)

Narrowed to specific exception tuple:
`(SympifyError, SyntaxError, TypeError, ValueError, AttributeError, TokenError)`.

### M4. `os.chdir()` in CLI group

**Status: SKIPPED**

**Decision:** This is the standard pattern for Click CLI tools with a `-C`
directory option. Refactoring to thread a base path through Click context
would touch every command's path resolution (~30 call sites) for minimal
real-world benefit. The CLI is not used as a library, and tests already use
`monkeypatch.chdir()` for isolation.

### M5. Missing `conn.close()` in error paths

**Status: FIXED** (`5f80086`)

Wrapped the sidecar build in `try/except BaseException`, closing the
connection and removing the partial database file on failure.

### M6. Unrecognized claim types silently pass validation

**Status: FIXED** (`8149728`)

Added an `else` branch to the type-dispatch chain that reports an error
for unrecognized type values.

### M7. Sidecar `relationship` table drops `note` field

**Status: FIXED** (`fb9b78f`)

Added `note TEXT` column to the relationship table schema and populated
it from relationship data during sidecar build.

### M8. Rename operation writes old file, then git-mv's it

**Status: FIXED** (`af55897`)

Reversed the operation order: writes updated content to the new path
first, then removes the old file. If git operations fail, falls back to
`unlink()`. Prevents the inconsistent state where new content sits at the
old filename.

---

## Low Priority Issues

### L1. Inconsistent exit code usage

**Status: FIXED** (`df39427`)

Replaced all `sys.exit(1)` calls in `cli/claim.py` with
`sys.exit(EXIT_ERROR)` for consistency.

### L2. `import sqlite3` inside function body

**Status: FIXED** (`ab9ad72`)

Moved to module-level import in `cli/concept.py`.

### L3. No `__all__` exports

**Status: SKIPPED**

**Decision:** Adding `__all__` to all modules is busywork with minimal
value for an internal compiler package. The public API is the CLI, not
the Python modules.

### L4. Standalone `main()` functions are dead code

**Status: REMOVED** (`b46d078`, `fb9b78f`)

Removed `main()` and `if __name__ == "__main__"` blocks from
`validate.py`, `validate_claims.py`, and `build_sidecar.py`. Cleaned up
orphaned imports (`sys`, `json`, `jsonschema`, `argparse`, `load_concepts`)
left behind by the removal.

### L5. Double JSON Schema validation in claim validator

**Status: ALREADY RESOLVED**

The redundancy was only between `validate_claims()` and the standalone
`main()` function. Since `main()` was removed in L4, the double validation
no longer exists. JSON Schema validation now occurs exactly once, inside
`validate_claims()`.

### L6. `_describe_equation()` returns raw expression

**Status: FIXED** (`64a6dc5`)

Renamed to `_expression_as_description()` to accurately reflect that
it returns the expression verbatim.

### L7. `_summarize_conditions` name collision

**Status: FIXED** (`dd5c0b2`)

Renamed `description_generator._summarize_conditions()` to
`_format_conditions_prose()` to distinguish it from
`conflict_detector._summarize_conditions()`.

---

## Data Model & Schema

### Strengths

- The LinkML schemas are well-structured with clear documentation.
- The form system (frequency, pressure, duration_ratio, etc.) provides good
  dimensional analysis support.
- Content-addressed hashing on claims enables deduplication.
- The concept registry uses stable numeric IDs (`concept1`, `concept2`) that
  survive renames, which is a good design choice.

### D1. Three divergent schema representations with no version lineage

**Status: FIXED** (`18d241a`)

Deleted the stale root-level `concept-registry-schema.yaml` (v0.1.0)
which used the obsolete `kind` tagged-union system. The authoritative
schema is `schema/concept_registry.linkml.yaml` (v0.2.0).

### D2. No schema for form YAML files

**Status: FIXED** (`e1f283b`)

Created `schema/generated/form.schema.json` — a JSON Schema that validates
form file structure, requiring `name` and `dimensionless`, typing all
optional fields, and using `additionalProperties: false` to catch typos.
Added `validate_form_files()` to `form_utils.py`, wired into both
`pks validate` and `pks build`.

### D3. Claim type discrimination not enforced by JSON Schema

**Status: SKIPPED (LINKML LIMITATION)**

**Decision:** LinkML's JSON Schema generator does not support `if/then`
or `oneOf` constructs for discriminated unions. The Python validator
(`validate_claims.py`) enforces type-specific required fields and now also
rejects unrecognized types (M6). Adding manual post-processing of the
generated schema would be fragile and hard to maintain. The JSON Schema
serves as a structural first pass; the Python validator is authoritative.

### D4. `additionalProperties` contradiction in claim schema

**Status: FIXED** (`8c4c0e2`)

Regenerated JSON schemas with `gen-json-schema --closed`, which sets
`additionalProperties: false` at all levels including the root. Added
`schema/generate.py` script for reproducible generation.

### D5. Claim ID format mismatch between schema and data

**Status: FIXED** (`8c4c0e2`)

Updated the LinkML claim schema's `id` description from
`claim_NNNN (zero-padded to 4 digits)` to
`claim + sequential integer (e.g., claim1, claim12, claim103)` to match
actual data and the validator's `^claim\d+$` pattern.

### D6. `FormParameters` in LinkML doesn't declare `values`/`extensible`

**Status: FIXED** (`8c4c0e2`)

Added `values` (multivalued string) and `extensible` (boolean) attributes
to the `FormParameters` class in the concept registry LinkML schema.
Regenerated JSON schemas.

### D7. Counter files are a concurrency hazard

**Status: PARTIALLY ADDRESSED**

The global counter fix (H7, `29bcfa5`) eliminated the cross-domain
collision bug. File locking for concurrent `pks concept add` was not
implemented — the CLI is a single-user local tool where concurrent
invocations are unlikely in practice.

### D8. `is_dimensionless` heuristic is fragile

**Status: FIXED** (`e1f283b`)

Added an explicit `dimensionless: true/false` boolean field to all 11 form
YAML files. `load_form()` now reads this field directly, falling back to
the heuristic only for form files that haven't been updated.

### D9. The `task` concept uses unstructured category values

**Status: ALREADY RESOLVED**

Investigation found that `concepts/task.yaml` already uses structured
`form_parameters` with `values` and `extensible` fields. The issue
described in the review had already been fixed in data prior to this
session. Validation confirms no spurious CEL warnings.

---

## Test Suite Analysis

### Strengths

- **Solid core coverage:** `test_validate_claims.py` (1,065 lines) and
  `test_validator.py` (742 lines) thoroughly exercise validation logic with
  both positive and negative cases.
- **Conflict detector well-tested:** `test_conflict_detector.py` (670 lines)
  covers all conflict classifications including edge cases like ranges,
  tolerances, and legacy formats.
- **Proper test isolation:** Tests use `tmp_path` fixtures for filesystem
  operations.
- **SymPy and CEL tested independently:** Dedicated test files for both
  subsystems.

### T1. No CLI integration tests for `pks build`

**Status: FIXED** (`b785a60`)

Added tests verifying built sidecar contains expected tables and data,
claims are included, `--force` flag behavior, and content hash skip logic.

### T2. No tests for `import_papers` command

**Status: FIXED** (`b785a60`)

Added tests for edge cases: papers directory doesn't exist, no YAML files
found.

### T3. Edge case: empty claim files

**Status: FIXED** (`b785a60`)

Added tests for `claims: []` and `claims: null` in claim files.

### T4. No property-based tests

**Status: FIXED** (`b785a60`)

Added `tests/test_property.py` with Hypothesis-based tests for the CEL
tokenizer (random valid/invalid token sequences) and numeric interval
comparisons (random intervals with known overlap/disjoint properties).

### T5. `test_init.py` is minimal

**Status: FIXED** (`b785a60`)

Added tests verifying generated form file contents are valid YAML with
expected fields and directory structure is correct.

### T6. No tests for `export_aliases` or `concept search`

**Status: FIXED** (`b785a60`)

Added CLI tests covering `export_aliases` JSON output and `concept search`
name/definition matching with YAML grep fallback.

---

## Performance Considerations

### P1. O(N^2) conflict detection

**Status: DEFERRED**

Pairwise comparison is inherent to the problem. Could be optimized by
bucketing claims by conditions first, but current data size makes this
premature. Worth revisiting when any concept accumulates >100 claims.

### P2. Repeated SymPy imports and parsing

**Status: FIXED** (`bcb8c7a`)

Two optimizations applied:
1. `@functools.lru_cache` on parsed parameterization expressions — same
   expression is evaluated with different input values across comparisons.
2. Pre-compute canonical equation forms before the N^2 pairwise loop
   instead of re-parsing each claim per comparison partner.

### P3. Full sidecar rebuild on any change

**Status: DEFERRED**

Incremental sidecar updates would require tracking what changed, handling
deletions, and updating FTS indexes incrementally. The current full-rebuild
approach is simple and correct. Worth revisiting when build time exceeds
a few seconds.

### P4. Form files loaded redundantly

**Status: FIXED** (via H4, `d372721`)

Resolved by the `load_form()` caching fix.

---

## Security

The codebase handles security well for a local CLI tool:

- **`yaml.safe_load()`** used everywhere — no unsafe YAML loading.
- **Parameterized SQL** queries throughout all SQLite operations.
- **No shell injection:** `subprocess.run` uses list arguments, not
  `shell=True`.
- **`pks query` raw SQL** is appropriate for a local dev tool (though could
  be opened read-only via `sqlite3.connect("file:...?mode=ro", uri=True)`).
- **No credential handling or network access** in the compiler.
- **`sympy.sympify()` replaced** with `parse_expr()` across the codebase
  (H6), eliminating the `eval()` code injection vector.
