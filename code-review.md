# Propstore Code Review

**Date:** 2026-03-16
**Scope:** Full codebase — compiler, CLI, schema, tests, data
**Lines reviewed:** ~9,575 across 27 Python files + YAML data/schema

---

## Executive Summary

Propstore is a well-structured propositional knowledge store compiler for
managing scientific concepts, claims, and their relationships in the domain of
voice/speech science. The codebase demonstrates strong domain modeling, thorough
validation logic, and good security practices. However, several architectural
patterns warrant attention: significant code duplication across validators,
overly long functions, a brittle `requires-python >= 3.13` constraint, and gaps
in edge-case handling. The test suite is comprehensive for core logic but has
coverage gaps in the CLI build pipeline and some error paths.

**Overall quality: Good** — solid domain logic, clear naming, safe SQL
practices. The issues below are refinements, not blockers.

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
10. [Recommended Refactoring Priority](#recommended-refactoring-priority)

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

**Location:** `pyproject.toml:5`

The codebase uses no Python 3.13-specific features. The most modern syntax is
`X | Y` union types (3.10+), which are gated behind `from __future__ import
annotations` throughout. This prevents installation on widely-deployed Python
3.11 and 3.12.

**Recommendation:** Lower to `>= 3.10`.

---

## High Priority Issues

### H1. Massive code duplication in value validation

**Location:** `validate_claims.py:209-290` and `validate_claims.py:410-484`

The validation of `value`, `lower_bound`, `upper_bound`, `uncertainty`, and
`uncertainty_type` is copy-pasted between `_validate_parameter()` and
`_validate_measurement()`. This is ~75 lines of identical logic including:
- value/bounds presence checks
- bounds pairing
- bound ordering
- uncertainty pairing
- uncertainty non-negativity

**Recommendation:** Extract a `_validate_value_fields(claim, cid, filename,
claim_type_label, result)` helper.

### H2. Duplicated interval comparison logic in param conflict detection

**Location:** `conflict_detector.py:782-825`

`_detect_param_conflicts()` has two nearly identical blocks for comparing
derived values against direct claims — one for named-field format and one for
legacy list format. The same pattern appears in `detect_conflicts()` for
measurement claims.

**Recommendation:** Unify into a single comparison path that handles both
formats transparently (as `_extract_interval()` already does).

### H3. `validate_concept_data()` re-validates the entire registry

**Location:** `cli/helpers.py:71-88`

This function loads and validates *all* concepts every time it's called, even
though its signature suggests single-concept validation. For a large registry,
this is O(N) file reads per `concept add` call.

**Recommendation:** Either rename to communicate its true behavior, or
restructure to validate incrementally.

### H4. Form definitions loaded from disk with no caching

**Location:** `form_utils.py:35-77`

`load_form()` reads and parses the same YAML file from disk on every call. In
`validate_concepts()`, forms are loaded once per concept (`validate.py:179`),
and again in `build_sidecar.py:234`. For N concepts referencing M forms, this
produces N disk reads instead of M.

**Recommendation:** Add a simple `@functools.lru_cache` or pass a pre-loaded
form registry through the call chain.

### H5. Stances written to sidecar but prior review found them dropped

The code at `build_sidecar.py:524-542` does write stances to the
`claim_stance` table. However, the `claim_stance` table has foreign key
constraints against the `claim` table, but claim IDs in `target_claim_id` may
reference claims in different files that haven't been inserted yet (insertion
order is per-file). SQLite doesn't enforce foreign keys by default, but if
`PRAGMA foreign_keys = ON` is ever enabled, this would fail.

**Recommendation:** Either defer stance insertion until all claims are inserted,
or document that foreign key enforcement is intentionally off.

### H6. `sympy.sympify()` with untrusted input is a code injection risk

**Location:** `sympy_generator.py:46`

`sympy.sympify()` internally uses `eval()`. If claim YAML files contain
malicious expressions, arbitrary Python code could execute during validation
or build. While this is a local CLI tool processing local files, it violates
defense-in-depth. Use `sympy.parsing.sympy_parser.parse_expr()` with
restricted transformations instead.

### H7. Cross-domain counter collision can produce duplicate concept IDs

**Location:** `cli/helpers.py:38-55`, `cli/concept.py:152-154`

Counters are per-domain (`speech.next`, `narr.next`) but the ID prefix is
always `concept` regardless of domain. Two domains starting from counter 1
would both generate `concept1`, causing a duplicate ID error on validation.

---

## Medium Priority Issues

### M1. `_values_compatible()` returns `False` for equal scalars

**Location:** `conflict_detector.py:168-208`

If two claims have simple scalar `value` fields (not lists, not using named
fields), the function falls through to `return False` at line 208, treating
them as incompatible even if they're equal. This is a latent bug currently
masked by the fact that all data uses named fields.

### M2. `assert isinstance(value, float)` in production code

**Location:** `conflict_detector.py:334`

Assertions can be disabled with `python -O`. Use an explicit type check with
an error or `typing.cast()` instead.

### M3. Bare `Exception` catch in equation canonicalization

**Location:** `conflict_detector.py:540`

`_canonicalize_equation()` catches `Exception`, which is too broad. Use a
specific exception tuple matching SymPy's error types.

### M4. `os.chdir()` in CLI group

**Location:** `cli/__init__.py:23`

Changing the process working directory is global state mutation. If the CLI
were ever used as a library or in tests, this would cause surprising side
effects.

**Recommendation:** Pass the directory as Click context instead.

### M5. Missing `conn.close()` in error paths

**Location:** `build_sidecar.py:121-141`

The SQLite connection is opened at line 121 but if any `_create_tables` or
`_populate_*` call raises, the connection is never closed and the partially-
written database file persists.

**Recommendation:** Use `with contextlib.closing(conn)` or `try/finally`.

### M6. Unrecognized claim types silently pass validation

**Location:** `validate_claims.py:195-204`

If a claim has a `type` value other than the five recognized types (parameter,
equation, observation, model, measurement), no error is reported. The claim
passes validation silently.

### M7. Sidecar `relationship` table drops `note` field

**Location:** `build_sidecar.py:269-273`

The relationship table schema has no `note` column, but relationships can have
notes. Relationship notes are silently lost during sidecar build.

### M8. Rename operation writes old file, then git-mv's it

**Location:** `cli/concept.py:314-331`

`write_concept_file(filepath, concept_record.data)` writes the updated
content to the *old* path, then `git mv` renames it. If `git mv` fails for
reasons other than "not a git repo" (e.g., the file is in `.gitignore`), the
file ends up at the old path with new content but an old name, which is an
inconsistent state.

---

## Low Priority Issues

### L1. Inconsistent exit code usage

`cli/claim.py` uses `sys.exit(1)` (lines 33, 36) while `cli/concept.py` uses
`sys.exit(EXIT_ERROR)`. Standardize on the named constants from
`cli/helpers.py`.

### L2. `import sqlite3` inside function body

**Location:** `cli/concept.py:438`

The module-level import pattern is used everywhere else. Minor inconsistency.

### L3. No `__all__` exports

None of the modules define `__all__`, making the public API surface ambiguous.

### L4. Standalone `main()` functions are dead code

`validate.py:391`, `validate_claims.py:513`, and `build_sidecar.py:584` have
`main()` functions that duplicate the `pks` CLI functionality. They're not
registered in `pyproject.toml` as console scripts. Either remove or register.

### L5. Double JSON Schema validation in claim validator

`validate_claims()` validates against JSON Schema at line 132, and `main()` in
the same file validates again at line 541. Running `pks validate` (which calls
`validate_claims()`) and then `pks build` (which also calls it) results in
repeated schema validation.

### L6. `_describe_equation()` returns raw expression

**Location:** `description_generator.py:99-102`

For a function named `_describe_equation`, returning the expression verbatim
without any transformation is misleading. Either rename to `_expression_as_
description` or add actual description generation.

### L7. `_summarize_conditions` name collision

Both `description_generator.py:155` and `conflict_detector.py:325` define
`_summarize_conditions()` with the same name but completely different
signatures and semantics. While both are module-private, this is confusing
when grepping the codebase.

---

## Data Model & Schema

### Strengths

- The LinkML schemas are well-structured with clear documentation.
- The form system (frequency, pressure, duration_ratio, etc.) provides good
  dimensional analysis support.
- Content-addressed hashing on claims enables deduplication.
- The concept registry uses stable numeric IDs (`concept1`, `concept2`) that
  survive renames, which is a good design choice.

### Issues

### D1. Three divergent schema representations with no version lineage

The repo contains three schema files that have drifted apart:
- `concept-registry-schema.yaml` (v0.1.0) uses a `kind` tagged-union system
  (`QuantityKind`, `CategoryKind`, etc.) that **no longer exists** in data.
- `schema/concept_registry.linkml.yaml` (v0.2.0) replaced `kind` with `form`.
- Actual concept YAML files use the v0.2.0 schema.

The root-level schema is stale and misleading. Either delete it or clearly
mark it as superseded.

### D2. No schema for form YAML files

Form definitions (`forms/*.yaml`) are loaded and validated entirely in Python
code. There's no JSON Schema or LinkML schema governing their structure. The
11 form files have inconsistent structure (some have `qudt`, some `base`,
some `parameters`, some `note`). A malformed form file would produce cryptic
Python errors rather than clear validation messages.

### D3. Claim type discrimination not enforced by JSON Schema

The generated JSON Schema (`schema/generated/claim.schema.json`) only
requires `id`, `type`, and `provenance`. A claim with `type: parameter` but
no `concept`, `value`, or `unit` passes schema validation. There are no
`if/then` or `oneOf` constructs for discriminated union enforcement.

### D4. `additionalProperties` contradiction in claim schema

The root-level JSON Schema object has `additionalProperties: true` while the
inner `ClaimFile` `$defs` version has `additionalProperties: false`. The
top-level validation is more permissive than intended.

### D5. Claim ID format mismatch between schema and data

The LinkML schema specifies `claim_NNNN` (underscore, zero-padded). Actual
data uses `claim1`, `claim2` (no underscore, no padding). The validator
enforces `^claim\d+$`, which matches neither format spec.

### D6. `FormParameters` in LinkML doesn't declare `values`/`extensible`

`task.yaml` uses `form_parameters: { values: [...], extensible: true }` but
the `FormParameters` class in the LinkML schema only has `reference`,
`construction`, and `note`. The `values` and `extensible` fields are
undeclared and would fail `additionalProperties: false` validation.

### D7. Counter files are a concurrency hazard

`read_counter()` / `write_counter()` (`cli/helpers.py:38-47`) perform
non-atomic read-then-write operations. Concurrent `pks concept add` calls
could assign duplicate IDs. Consider file locking or atomic write patterns.

### D8. `is_dimensionless` heuristic is fragile

**Location:** `form_utils.py:63-68`

The logic `unit_symbol is None and kind == QUANTITY` classifies any quantity
form without a unit symbol as dimensionless. A form where the unit symbol is
simply missing from the YAML file would be misclassified.

### D9. The `task` concept uses unstructured category values

`concepts/task.yaml` stores category metadata as a note string instead of
structured `values` and `extensible` fields in `form_parameters`. This means
CEL checking cannot validate task values correctly, and every `task == '...'`
condition produces spurious warnings.

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

### Coverage Gaps

### T1. No CLI integration tests for `pks build`

`test_cli.py` tests `concept add`, `rename`, `deprecate`, etc., but there
are no tests for the `build` or `query` commands, which are the most complex
end-to-end paths.

### T2. No tests for `import_papers` command

This command handles external filesystem input and YAML manipulation but has
zero test coverage.

### T3. Edge case: empty claim files

No test validates behavior when a claim file exists but contains
`claims: []` or `claims: null`.

### T4. No property-based tests

Despite `hypothesis` being listed in dev dependencies (`pyproject.toml`),
there are no property-based tests. The CEL tokenizer/parser and numeric
interval comparisons are excellent candidates for fuzzing.

### T5. `test_init.py` is minimal

At 77 lines, it tests the `pks init` command but doesn't verify generated
file contents or directory structure thoroughly.

### T6. No tests for `export_aliases` or `concept search`

Both commands have logic worth testing (FTS fallback, JSON output format).

---

## Performance Considerations

### P1. O(N^2) conflict detection

`detect_conflicts()` compares every pair of claims for each concept (lines
587-614, 623-651, 659-682). For concepts with many claims, this is quadratic.
Acceptable for current data size, but a scaling limitation.

### P2. Repeated SymPy imports and parsing

`_canonicalize_equation()` (called per equation pair) does `import sympy` at
function scope. While Python caches imports, the repeated `sympy.parse_expr()`
calls with no caching of parsed expressions could be expensive for large
equation claim sets.

### P3. Full sidecar rebuild on any change

Even with content-hash-based skip logic, there's no incremental update path.
Any content change triggers a full rebuild of all tables and FTS indexes.

### P4. Form files loaded redundantly

As noted in H4, the same form YAML files are parsed from disk multiple times
across validation, building, and enrichment passes.

---

## Security

The codebase handles security well for a local CLI tool, with one notable
exception:

- **`yaml.safe_load()`** used everywhere — no unsafe YAML loading.
- **Parameterized SQL** queries throughout all SQLite operations.
- **No shell injection:** `subprocess.run` uses list arguments, not
  `shell=True`.
- **`pks query` raw SQL** is appropriate for a local dev tool (though could
  be opened read-only via `sqlite3.connect("file:...?mode=ro", uri=True)`).
- **No credential handling or network access** in the compiler.

**One issue:** `sympy.sympify()` uses `eval()` internally (see H6). While
the risk is mitigated by this being a local CLI tool processing local files,
it should be replaced with `parse_expr()` for defense-in-depth.

---

## Recommended Refactoring Priority

| Priority | Issue | Effort | Impact |
|----------|-------|--------|--------|
| 1 | C1: Lower `requires-python` to `>= 3.10` | 5 min | Unblocks wide adoption |
| 2 | H1: Extract shared value-field validation | 1 hr | Reduces 75 lines of duplication |
| 3 | H4: Cache form definitions | 1 hr | Eliminates redundant disk I/O |
| 4 | M5: Fix SQLite connection leak | 15 min | Prevents resource leaks |
| 5 | M1: Fix `_values_compatible()` scalar path | 30 min | Prevents latent bug |
| 6 | Unify duplicate `ValidationResult` classes | 30 min | Reduces confusion |
| 7 | D1: Add form YAML schema | 2 hr | Catches malformed forms early |
| 8 | H2: Consolidate param conflict comparison | 1 hr | Reduces duplication |
| 9 | T1: Add CLI `build`/`query` integration tests | 3 hr | Covers critical path |
| 10 | D2: Add file locking to counters | 1 hr | Prevents concurrent ID collision |

---

## Summary of Findings

| Category | Count |
|----------|-------|
| Critical | 1 |
| High | 7 |
| Medium | 8 |
| Low | 7 |
| Data model | 9 |
| Test gaps | 6 |
| Performance | 4 |
| Security | 1 |
| **Total** | **43** |

The codebase is well-engineered for its problem domain. The validation logic
is thorough, the CLI is well-organized with dry-run support, and the SQLite
sidecar design is practical. The primary areas for improvement are reducing
code duplication in validators, caching form definitions, expanding test
coverage for the CLI build pipeline, and lowering the Python version
constraint to enable broader adoption.
