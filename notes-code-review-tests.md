# Test Suite Review -- propstore

**Date**: 2026-03-23
**Reviewer**: Scout agent (Gauntlet protocol)
**Status**: COMPLETE -- all 27 test files read, suite executed.

## Test Run Result

```
824 passed, 212 warnings in 44.22s
```

Zero failures. All 212 warnings originate from `propstore/conflict_detector/orchestrator.py:65` -- parameterization evaluation warnings for sympy expressions that cannot be evaluated during conflict detection. These are non-fatal `UserWarning` messages.

## Tests Per File (descending)

| File | Tests | Primary concern |
|------|------:|-----------------|
| test_world_model.py | 108 | WorldModel: bind, value_of, resolve, chain, hypothetical, derived |
| test_validate_claims.py | 82 | Claim file validation (all claim types, provenance, ID, references) |
| test_build_sidecar.py | 69 | SQLite sidecar builder (tables, content, FTS, hashing, contexts) |
| test_cel_checker.py | 63 | CEL expression type-checker (tokenizer, parser, type rules) |
| test_cli.py | 57 | CLI commands (init, concept add/alias/rename/deprecate/link, validate, build, query) |
| test_contexts.py | 52 | Context loading, validation, hierarchy, sidecar integration, BoundWorld |
| test_validator.py | 43 | Concept file validator (ID, filename, deprecation, relationships, parameterization, forms) |
| test_dung.py | 42 | Dung 1995 semantics (grounded, preferred, stable, complete) |
| test_z3_conditions.py | 39 | Z3 condition disjointness, equivalence, caching, integration |
| test_conflict_detector.py | 39 | Conflict classification (all claim types, conditions, parameterization) |
| test_preference.py | 27 | ASPIC+ preference ordering (strictly_weaker, defeat_holds, claim_strength) |
| test_bipolar_argumentation.py | 27 | Cayrol 2005 bipolar AF, Modgil-Prakken attack-based CF |
| test_dung_z3.py | 21 | Z3 SAT extension computation (oracle comparison against brute-force) |
| test_form_dimensions.py | 20 | SI dimension metadata on forms (schema, validation, loading, CLI) |
| test_description_generator.py | 19 | Auto-generated claim descriptions |
| test_argumentation_integration.py | 16 | Full argumentation pipeline (stances to extensions) |
| test_sympy_generator.py | 13 | SymPy expression generation and symbol validation |
| test_maxsat_resolver.py | 11 | MaxSMT conflict resolution via z3.Optimize |
| test_graph_export.py | 10 | KnowledgeGraph construction and serialization (DOT, JSON) |
| test_render_time_filtering.py | 8 | Confidence threshold filtering, stance summary, no defeat table |
| test_init.py | 8 | `pks init` command (structure, forms, validate-after-init) |
| test_helpers.py | 8 | YAML helpers (load_yaml_dir, write_yaml_file) |
| test_sensitivity.py | 7 | Sensitivity analysis (partial derivatives, elasticity, nonlinear) |
| test_property.py | 7 | Property-based tests for CEL tokenizer and interval comparison |
| test_propagation.py | 7 | SymPy evaluation helper (evaluate_parameterization) |
| test_claim_notes.py | 7 | Claim notes field (validation, sidecar, WorldModel, roundtrip) |
| test_parameterization_groups.py | 6 | Connected-component grouping of parameterized concepts |
| test_render_contracts.py | 5 | RenderPolicy/Environment/ArtifactStore/BeliefSpace type shapes |
| test_form_utils.py | 3 | FormDefinition loading edge cases |

Plus 1 non-test helper: `sqlite_argumentation_store.py` (test adapter for SQLite-backed argumentation store, 30 lines).

---

## 1. What Is Tested and How Thoroughly

### Layer 1: Source-of-truth storage
- **Concepts**: Validation tested comprehensively in `test_validator.py` (43 tests) -- ID uniqueness, filename match, deprecation chains, relationship targets, parameterization inputs (existence, kind, self-reference, conditional exactness), form validation, CEL in relationships, canonical claims, relationship types, form parameter validation.
- **Claims**: Validation tested in `test_validate_claims.py` (82 tests) -- all 5 claim types (parameter, equation, observation, model, measurement), ID format/uniqueness, concept references, provenance, required fields, stances, CEL conditions, measurement-specific fields, algorithm claims.
- **Contexts**: Loading, validation, hierarchy, sidecar integration in `test_contexts.py` (52 tests) -- inheritance, exclusions, cycles, effective assumptions, visibility, context tables in sidecar, BoundWorld context filtering.
- **Sidecar**: Building tested in `test_build_sidecar.py` (69 tests) -- table creation (concept, alias, relationship, parameterization, FTS5, claim, claim_stance, context, parameterization_group), content correctness, rebuild skipping, content hashing, force rebuild.

### Layer 2: Theory / typing
- **CEL checker**: `test_cel_checker.py` (63 tests) -- tokenizer, parser, type checking per concept kind (quantity, category, boolean, structural), undefined concepts, complex expressions, parse errors, registry building from dicts and LoadedConcepts.
- **Forms**: `test_form_dimensions.py` (20 tests) -- SI dimensions, schema validation, validation logic, FormDefinition loading, CLI. `test_form_utils.py` (3 tests) -- edge cases.
- **SymPy**: `test_sympy_generator.py` (13 tests) -- expression generation, symbol checking, edge cases.
- **Z3 conditions**: `test_z3_conditions.py` (39 tests) -- disjointness (numeric, category, boolean, mixed, compound, in-operator, cross-concept arithmetic, negation), equivalence, batch equivalence classes, caching, integration with conflict detector.

### Layer 3: Heuristic analysis
- **Conflict detection**: `test_conflict_detector.py` (39 tests) -- classification (COMPATIBLE, PHI_NODE, CONFLICT, OVERLAP, PARAM_CONFLICT, CONTEXT_PHI_NODE), value comparison (tolerance, ranges), named value fields, measurement claims, equation claims, algorithm claims, transitive context semantics. Property tests for symmetry and reflexivity.

### Layer 4: Argumentation
- **Dung semantics**: `test_dung.py` (42 tests) -- concrete tests for grounded/preferred/stable/complete with classic examples (Nixon diamond, reinstatement, odd cycle, self-attacker, chain of four). Property tests verify 11+ formal theorems from Dung 1995.
- **Z3-backed Dung**: `test_dung_z3.py` (21 tests) -- oracle-based testing (z3 matches brute-force for all semantics), credulous/skeptical acceptance, hard instances (chain-10, odd-cycle-7).
- **Bipolar AF**: `test_bipolar_argumentation.py` (27 tests) -- Cayrol 2005 derived defeats, Modgil-Prakken attack-based CF, extension-level tests.
- **ASPIC+ preference**: `test_preference.py` (27 tests) -- strictly_weaker (elitist/democratic), defeat_holds, claim_strength. Property tests verify irreflexivity, asymmetry, singleton agreement, unconditional defeat, weaker-blocked, equal-succeeds, non-negative strength.
- **Integration**: `test_argumentation_integration.py` (16 tests) -- full pipeline from stances to extensions. Property tests for AF closure, grounded CF, justified subset.
- **MaxSAT**: `test_maxsat_resolver.py` (11 tests) -- z3.Optimize weighted conflict resolution, conflict-free invariant.

### Layer 5: Render
- **WorldModel**: `test_world_model.py` (108 tests) -- 15 test classes covering construction, unbound queries, explain, bind/active_claims, value_of, bound conflicts, bound explain, derived value (forward propagation), hypothetical world (counterfactual), conflict resolution (recency, sample_size, argumentation, override), chain query, hypothesis properties (partitioning, monotonicity, determinism), cross-feature properties (invariance, substitutability, isolation), transitive consistency, algorithm claims in world model.
- **Render contracts**: `test_render_contracts.py` (5 tests) -- type shapes for RenderPolicy, Environment, ArtifactStore, BeliefSpace.
- **Render-time filtering**: `test_render_time_filtering.py` (8 tests) -- confidence threshold on stance filtering, stance summary metadata, no defeat table in schema.
- **Sensitivity**: `test_sensitivity.py` (7 tests) -- partial derivatives, elasticity, ranking, nonlinear parameterization, condition-gated.

### Layer 6: Agent workflow
- **CLI**: `test_cli.py` (57 tests) -- init, concept add/alias/rename/deprecate/link, validate, build, query/value-of/explain, algorithm claims via CLI.
- **Description generator**: `test_description_generator.py` (19 tests) -- all claim types, conditions formatting.
- **Graph export**: `test_graph_export.py` (10 tests) -- unbound/bound graphs, group scoping, serialization, conflicted claims.

---

## 2. Testing Patterns

### Pattern 1: Pervasive Hypothesis property-based testing
12 of 27 test files use Hypothesis. This is the suite's most distinctive quality. Files using `@given`:
- `test_dung.py` (200 examples per property, 11 properties)
- `test_preference.py` (200 examples per property, 7 properties)
- `test_argumentation_integration.py` (100 examples, 4 properties)
- `test_dung_z3.py` (100 examples, 3 oracle properties)
- `test_cel_checker.py` (50 examples, 2 properties)
- `test_conflict_detector.py` (50 examples, 2 properties)
- `test_property.py` (50 examples, 5 properties on tokenizer + intervals)
- `test_form_dimensions.py` (50 examples, 6 properties)
- `test_contexts.py` (40 examples, 2 properties)
- `test_claim_notes.py` (2 properties including sidecar roundtrip)
- `test_build_sidecar.py` (2 properties)
- `test_validate_claims.py` (1 property)

### Pattern 2: Literature-grounded tests
Tests explicitly reference formal theorems:
- Dung 1995: Properties labeled P1-P12 with theorem/definition numbers (e.g., "P7: Grounded is fixed point of F (Def 20, Thm 25)")
- Cayrol & Lagasquie-Schiex 2005: "Definition 3"
- Modgil & Prakken 2018: "Definition 14", "Definition 9", "Definition 19"
- Each property test has a docstring citing the specific theorem it verifies.

### Pattern 3: Oracle-based testing
`test_dung_z3.py` uses the brute-force Dung implementations as oracles to verify the Z3 SAT encodings produce identical results. This is a strong correctness verification pattern.

### Pattern 4: In-memory SQLite for speed
Argumentation tests (`test_argumentation_integration.py`, `test_bipolar_argumentation.py`, `test_render_time_filtering.py`) use `:memory:` SQLite with direct inserts rather than building full sidecars. This keeps them fast.

### Pattern 5: Full vertical-slice integration tests
Several tests build the full pipeline (YAML concepts -> load_concepts -> build_sidecar -> WorldModel -> query). Examples: `test_world_model.py`, `test_graph_export.py`, `test_sensitivity.py`, `test_claim_notes.py`.

### Pattern 6: Click CliRunner for CLI testing
`test_cli.py` and `test_init.py` use Click's CliRunner with `tmp_path` + `monkeypatch.chdir` for isolated CLI testing. Tests verify both output messages and file system effects.

### Pattern 7: Regression tests with docstrings explaining the bug
`test_z3_conditions.py::TestSoundnessBugRegression` explicitly documents the bug being prevented: "The old code returned PHI_NODE because the condition strings were different. But F1/F0 > 3.0 is a subset of F1/F0 > 2.0 -- they OVERLAP, not disjoint." (`test_z3_conditions.py`, lines 79-88)

---

## 3. What Tests Reveal About System Capabilities

1. **Multiple claim types**: parameter, equation, observation, model, measurement, algorithm. Each has distinct validation rules and conflict detection logic.

2. **Condition-aware reasoning**: CEL expressions are parsed, type-checked, and evaluated for disjointness/overlap using Z3. This enables PHI_NODE classification (different values are fine if conditions are disjoint).

3. **Four argumentation semantics**: grounded, preferred, stable, complete -- both brute-force and Z3-backed. Plus credulous/skeptical acceptance queries.

4. **Bipolar argumentation**: Support relations create derived defeats (Cayrol 2005). Attack-based conflict-free is stricter than defeat-based (Modgil-Prakken 2018).

5. **Multiple resolution strategies**: recency, sample_size, argumentation (with configurable semantics), override, MaxSAT. Per-concept strategy overrides possible.

6. **Hypothetical reasoning**: Counterfactual worlds that add/remove claims and recompute conflicts.

7. **Sensitivity analysis**: Symbolic partial derivatives and elasticity via SymPy for parameterized concepts.

8. **Chain queries**: Multi-hop binding chains across concepts (e.g., "what is the value of X given that Y depends on Z?").

9. **Context hierarchy**: Inheritance, exclusion, effective assumptions. Contexts filter claim visibility.

10. **Knowledge graph export**: DOT and JSON serialization of concept/claim/stance graphs with bound filtering.

---

## 4. Coverage Gaps

### Gap 1: No conftest.py for shared fixtures
The `concept_dir` fixture is duplicated nearly verbatim across `test_build_sidecar.py` (line 20), `test_graph_export.py` (line 18), `test_sensitivity.py` (line 16), and `test_world_model.py` (line 41). Each creates the same 5-7 concept YAML files. A shared conftest.py fixture would reduce ~400 lines of duplication.

### Gap 2: No conftest.py for shared SQLite schema
The `_create_schema()` helper that creates claim/claim_stance tables is duplicated identically in:
- `test_argumentation_integration.py` (lines 27-59)
- `test_bipolar_argumentation.py` (lines 41-72)
- `test_render_time_filtering.py` (lines 27-58)

### Gap 3: No conftest.py for shared claim helpers
`make_parameter_claim()`, `make_claim_file()`, `make_concept_registry()` are duplicated across `test_conflict_detector.py`, `test_z3_conditions.py`, `test_property.py`, `test_claim_notes.py`, and `test_validate_claims.py` with slight variations.

### Gap 4: No negative/error path tests for WorldModel
`test_world_model.py` is the largest test file (108 tests) but focuses heavily on correct behavior. There are no tests for:
- Corrupted sidecar database
- Missing tables
- Schema version mismatches
- Concurrent access

### Gap 5: No performance/scaling tests
The Hypothesis-generated AFs max out at 8 arguments. The "hard instances" in `test_dung_z3.py` go up to 10 arguments. There are no tests verifying behavior with hundreds of concepts or thousands of claims.

### Gap 6: Limited CLI error path coverage
`test_cli.py` tests some error paths (validation failure, nonexistent replacement) but does not test:
- Malformed YAML input
- Permission errors
- Concurrent CLI operations

### Gap 7: No tests for the `__init__.py` module itself
`tests/__init__.py` exists but appears to be empty (no tests). The `test_init.py` tests `pks init`, not the package init.

### Gap 8: Render policy interaction tests are thin
`test_render_contracts.py` has only 5 tests checking type shapes. The actual interaction between RenderPolicy fields (strategy + concept_strategies + overrides + semantics + comparison + confidence_threshold) under various combinations is tested indirectly through `test_world_model.py::TestConflictResolution` but not exhaustively.

### Gap 9: No test for `pks build` idempotency with claims
`test_build_sidecar.py::TestRebuildSkipping` tests skip-when-unchanged for concepts, but the interaction with claim files (added/removed/modified claims triggering rebuild) is not tested.

### Gap 10: Algorithm claim tests are recent and minimal
Algorithm claims appear in `test_conflict_detector.py` (7 tests) and `test_world_model.py::TestAlgorithmWorldModel` (6 tests), but there are no algorithm-specific tests for sidecar storage, CLI query, or graph export of algorithm claims.

---

## 5. Code Quality Assessment

### Strengths

1. **Docstrings on nearly every test**: Most test methods have docstrings explaining what they verify and why. The argumentation tests are exemplary -- each property test cites the formal theorem it verifies.

2. **Clear test organization**: Tests are grouped into well-named classes by concern (e.g., `TestConflictClassification`, `TestValueComparison`, `TestParameterizationConflict`).

3. **Property-based testing is used where it matters most**: The formal argumentation layer uses Hypothesis extensively to verify mathematical properties, not just examples. This is the right place for it.

4. **Integration tests cover the full pipeline**: From YAML files through sidecar build to WorldModel queries. This catches interface mismatches between layers.

5. **Regression tests document the bugs they prevent**: `TestSoundnessBugRegression` in `test_z3_conditions.py` is a model for how to write regression tests.

6. **Good use of pytest features**: `tmp_path`, `monkeypatch`, parametric fixtures. No raw `unittest` anywhere.

### Weaknesses

1. **Massive fixture duplication**: The concept_dir fixture (~100 lines) is copy-pasted across 4+ files. This is the single largest code quality issue in the test suite. If the concept schema changes, 4+ files need updating.

2. **Helper function duplication**: `make_parameter_claim`, `make_concept_registry`, `_create_schema` are duplicated with minor variations. This creates risk of tests using subtly different schemas.

3. **Some tests rebuild the sidecar redundantly**: In `test_build_sidecar.py`, each test in `TestTableCreation` calls `build_sidecar` independently. A class-scoped fixture would be more efficient while still being isolated.

4. **`time.sleep(0.1)` in test_build_sidecar.py line 396**: Fragile timing-based assertion for rebuild skipping. Could fail on slow CI.

5. **No `conftest.py`**: The entire `tests/` directory has no `conftest.py`. All fixtures are defined locally in each file. This is the root cause of the duplication.

6. **Mixed assertion styles**: Some tests use `assert result.ok`, others use `assert not result.errors`, others use `assert len(records) == 0`. The intent is usually the same but the expression varies.

---

## Summary

The propstore test suite is **unusually strong** for a project of this size. The combination of property-based testing grounded in formal argumentation theory, oracle-based verification of the Z3 solver, and full vertical-slice integration tests creates a high-confidence safety net. The 824 tests all pass cleanly.

The main improvement opportunity is **extracting shared fixtures and helpers into conftest.py** to eliminate the ~500+ lines of duplication across test files. This would also reduce the risk of schema drift between test files.

The gaps identified (no error-path tests for WorldModel, no performance tests, thin render policy interaction coverage) are typical of a project that has prioritized correctness testing of the formal core over defensive edge-case testing. Given the project's design principle of "non-commitment at the semantic core," the emphasis on correctness testing is appropriate.
