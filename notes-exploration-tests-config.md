# Thorough Exploration: Tests, Knowledge Data, Configuration

## GOAL
Complete audit of propstore's test suite, knowledge data formats, configuration, and scripts. Identify test coverage gaps, data formats, and infrastructure patterns.

## DONE

### Configuration & Infrastructure
- **pyproject.toml** read
  - Python 3.11+ required
  - Key deps: click, linkml, pyyaml, jsonschema, sympy, z3-solver, graphviz, ast-equiv
  - Optional: litellm, sqlite-vec (embeddings)
  - Entry point: `pks = "propstore.cli:cli"`
  - Dev deps: pytest, hypothesis, rope
  - Uses hatchling build backend

- **.ward/rules/foreman-gate.yaml** read
  - Gates Bash and Edit tools in "foreman" phase
  - Write allowed only to prompts/ and notes-*.md
  - Enforces coordination over execution

- **tests/conftest.py** read
  - Helper functions (not pytest fixtures):
    - `create_argumentation_schema()`: Creates claim + claim_stance tables for testing
    - `make_parameter_claim()`: Builds minimal parameter claim dict
    - `make_concept_registry()`: Builds mock registry with 3 concepts (frequency, pressure, category)

### Test Files Read So Far (7 of 33)
1. **test_init.py** — CLI init command tests
   - Creates knowledge/ structure with concepts/, claims/, forms/, sidecar/, .counters/
   - Tests form file YAML validity
   - Tests custom path creation
   - Tests idempotency ("already initialized" case)
   - 9 test cases total

2. **test_parameterization_groups.py** — Connected-component analysis
   - Tests `build_groups()` function
   - Verifies concepts connected via parameterization_relationships group correctly
   - Tests: chains, disconnected clusters, single concepts, multiple inputs
   - 6 test cases

3. **test_propagation.py** — SymPy evaluation helper
   - Tests `evaluate_parameterization()` function
   - Handles equations (Eq), missing inputs, division, self-reference, NaN
   - 8 test cases

4. **test_property.py** — Property-based tests using Hypothesis
   - CEL tokenizer tests: valid idents, operators, int/float comparisons, strings, compound expressions
   - Numeric interval comparison: overlapping ranges (compatible), disjoint ranges (conflict), identical scalars
   - 8 test cases + ~300 hypothesis examples

5. **test_sympy_generator.py** — SymPy expression generation
   - Tests `generate_sympy()`: equations, caret->power conversion, unparseable handling
   - Tests `check_symbols()`: symbol matching, unbound warnings, constant handling
   - 14 test cases

### Knowledge Directory Structure (Globs completed)
- **knowledge/forms/**: 15 YAML files
  - amplitude_ratio.yaml, dimensionless_compound.yaml, duration_ratio.yaml, flow.yaml, flow_derivative.yaml
  - frequency.yaml, level.yaml, pressure.yaml, structural.yaml, time.yaml
  - count.yaml, rate.yaml, score.yaml, ratio.yaml, boolean.yaml, category.yaml

- **knowledge/concepts/**: 60+ YAML files
  - Argumentation: acceptability, admissible_set, agm_postulates, aspic_plus, assumption, atms, etc.
  - Optimization: maxsat_algorithm, weighted_maxsmt, pareto_front, linear_arithmetic_optimization
  - Constraint/logic: constraint_satisfaction, sat_encoding, smt_solver, answer_set_programming
  - Graph: treewidth, tree_decomposition, clique_width, primal_graph

- **knowledge/contexts/**: 
  - ctx_abstract_argumentation.yaml (at least 1)

- **knowledge/claims/**: 30+ YAML files
  - Academic papers: Alchourron_1985, Cayrol_2005, Clark_2014, Dixon_1993, Doyle_1979, Dung_1995, Falkenhainer_1987, Ginsberg_1985, Greenberg_2009, Groth_2010, Martins_1983, Martins_1988, Mayer_2020, McAllester_1978, McDermott_1983, Modgil_2014, Modgil_2018, Odekerken_2023, Pollock_1987, Prakken_2012, Reiter_1980, Shapiro_1998, Walton_2015, deKleer_1984, deKleer_1986 (2 files)

### Scripts Directory (Glob completed)
- Python scripts: rename_package.py, verify_ast_equiv.py, validate_claims_only.py, extract_concepts.py, find_collisions.py, reconcile_vocab.py, pdf_receiver.py, register_concepts.py, review_assessment.py, seed_tags.py
- JSON: concept_inventory.json, reconciliation_results.json
- Shell: test_ward_rules.sh

## CURRENT STATE
- Have read: 5 test files completely
- Still need to read: 28 test files (test_validator.py, test_dung.py, test_render_contracts.py, test_contexts.py, test_argumentation_integration.py, test_bipolar_argumentation.py, test_condition_classifier.py, test_z3_conditions.py, etc.)
- Sample knowledge files not yet read (need actual format inspection)
- Scripts not yet read (need to understand purpose/patterns)

## NEXT
Continue reading remaining test files in batches to identify:
- Coverage gaps
- Problematic/skipped tests
- Testing patterns used (pytest fixtures, parametrize, etc.)
- Any broken tests

Then read sample knowledge files and scripts.
