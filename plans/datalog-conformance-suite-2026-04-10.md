# Plan: Datalog Conformance Test Suite

**Date:** 2026-04-10
**Repo:** `~/code/datalog-conformance-tests` (new, separate repo)
**Pattern:** Same as `~/code/moo-conformance-tests` — YAML test specs, pytest plugin, evaluator protocol
**Build:** uv + hatchling, pytest, hypothesis, ruff, pyright

---

## Context

We are building a Defeasible Datalog evaluator as a separate package (like ast-equiv, bridgman). Before writing the evaluator, we build the conformance test suite. The suite is implementation-agnostic: YAML files define programs and expected results, a pytest plugin bridges to any evaluator satisfying a Python protocol.

Test cases are primarily harvested from existing implementations (Souffle, Nemo, SPINdle, crepe) and secondarily derived from paper examples (Maher 2021, Goldszmidt 1992, Morris 2020, Antoniou 2007).

Reference report: `reports/datalog-conformance-test-sources.md`
Reference design: `~/code/moo-conformance-tests`

---

## Repo Structure

```
datalog-conformance-tests/
  src/datalog_conformance/
    __init__.py
    schema.py              # dataclasses for YAML test structure
    plugin.py              # pytest plugin: discovery, parametrization
    runner.py              # bridges YAML to evaluator protocol
    protocol.py            # Protocol classes evaluators must satisfy
    _tests/
      basic/
        facts.yaml         # ground facts only, query them back
        simple_rules.yaml  # single-rule derivation
        joins.yaml         # multi-predicate body
        projection.yaml    # subset of args in head
        union.yaml         # multiple rules, same head predicate
      recursion/
        transitive.yaml    # transitive closure (the hello-world)
        same_generation.yaml
        mutual.yaml        # mutually recursive predicates
        linear.yaml        # linear vs nonlinear recursion
      negation/
        stratified.yaml    # clean stratification
        unstratified.yaml  # should be rejected or WFS
        double_negation.yaml
        negation_in_recursion.yaml  # requires WFS
      errors/
        unbound_variable.yaml    # head var not in body
        arity_mismatch.yaml
        safety_violations.yaml
        cyclic_negation.yaml     # rejection or WFS behavior
      aggregation/           # optional, may defer
        count.yaml
        min_max.yaml
        sum.yaml
      defeasible/
        basic/
          strict_only.yaml         # strict rules = classical Datalog
          defeasible_only.yaml     # defeasible rules, no conflicts
          mixed.yaml               # strict + defeasible interaction
          defeater.yaml            # defeaters block without asserting
        superiority/
          simple_priority.yaml     # r1 > r2
          chain_priority.yaml      # r1 > r2 > r3
          cycle_detection.yaml     # priority cycles → error or handling
        ambiguity/
          blocking.yaml            # Antoniou 2007 p.13 examples
          propagating.yaml         # Antoniou 2007 p.14 examples
          blocking_vs_propagating.yaml  # same theory, different policy, different results
        closure/
          rational_closure.yaml       # Morris 2020 examples
          lexicographic_closure.yaml  # Morris 2020 examples
          baserank.yaml               # ranking computation
        klm/
          reflexivity.yaml
          left_logical_equivalence.yaml
          right_weakening.yaml
          conjunction.yaml           # And
          disjunction.yaml           # Or
          cautious_monotonicity.yaml # CM
          rational_monotonicity.yaml # RM
          relevant_closure_failures.yaml  # Morris counterexamples
      tolerance/
        consistent_theory.yaml     # Goldszmidt: all defaults tolerable
        inconsistent_theory.yaml   # some defaults intolerable
        system_z_equivalence.yaml  # tolerance ↔ System Z
      compilation/
        maher_definite.yaml        # Theorem 19: +Δ ↔ definitely_
        maher_defeasible.yaml      # Theorem 15: +∂ ↔ defeasibly_
        structural_properties.yaml # Theorem 21: call-consistency etc.
      benchmarks/
        transitive_closure_scaling.yaml  # rbench TC
        same_generation_scaling.yaml     # rbench SG
        join1.yaml                       # rbench JOIN1
  scripts/
    harvest_souffle.py     # Souffle .dl + .csv → YAML
    harvest_nemo.py        # Nemo test format → YAML
    harvest_spindle.py     # SPINdle test cases → YAML
    harvest_crepe.py       # crepe error tests → YAML
  tests/
    test_schema.py         # schema validation, round-trip
    test_plugin.py         # plugin discovery, parametrization
    test_runner.py         # runner with a trivial mock evaluator
  docs/
    YAML_SCHEMA.md         # complete schema reference
    HARVESTING.md          # how tests were sourced, per-test attribution
    CONTRIBUTING.md        # how to add new tests
  pyproject.toml
  CLAUDE.md
  README.md
  LICENSE                  # MIT
```

---

## Phase 1: Scaffolding (no tests yet)

**Gate:** `uv run pytest tests/` passes with at least the schema and plugin meta-tests.

### 1.1 Create repo and pyproject.toml

```toml
[project]
name = "datalog-conformance"
version = "0.1.0"
description = "Portable conformance test suite for Datalog and Defeasible Datalog evaluators"
requires-python = ">=3.11"
license = {text = "MIT"}
dependencies = [
    "pyyaml>=6.0",
    "pytest>=8.0",
    "hypothesis>=6.0",
]

[project.entry-points.pytest11]
datalog_conformance = "datalog_conformance.plugin"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/datalog_conformance"]

[tool.hatch.build.targets.wheel.force-include]
"src/datalog_conformance/_tests" = "datalog_conformance/_tests"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]

[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "strict"
```

### 1.2 Define the evaluator protocol

`src/datalog_conformance/protocol.py`:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class DatalogEvaluator(Protocol):
    """Evaluates a standard Datalog program."""
    def evaluate(self, program: "Program") -> "Model": ...

@runtime_checkable
class DefeasibleEvaluator(Protocol):
    """Evaluates a defeasible theory under a given policy."""
    def evaluate(
        self,
        theory: "DefeasibleTheory",
        policy: "Policy",
    ) -> "DefeasibleModel": ...
```

The actual data types (`Program`, `Model`, `DefeasibleTheory`, `Policy`, `DefeasibleModel`) are defined in `schema.py`. They are simple dataclasses — no logic, just structure.

### 1.3 Define the YAML schema

`src/datalog_conformance/schema.py` — dataclasses that mirror the YAML structure.

**For core Datalog tests:**

```yaml
name: string            # unique within file
description: string     # what this tests
source: string          # where we stole it (e.g. "souffle/semantic/recursive")
tags: [string]          # for filtering (e.g. [recursion, basic])
skip: string | null     # reason to skip, or null

program:
  facts:                # predicate_name -> list of tuples
    edge: [[a, b], [b, c]]
  rules:                # list of rule strings in Datalog syntax
    - "path(X, Y) :- edge(X, Y)."
    - "path(X, Y) :- edge(X, Z), path(Z, Y)."

expect:                 # predicate_name -> set of expected tuples
  path: [[a, b], [a, c], [a, d], [b, c], [b, d], [c, d]]

# OR for error tests:
expect_error: string    # e.g. "unbound_variable", "arity_mismatch"
```

**For defeasible tests:**

```yaml
name: string
description: string
source: string
tags: [string]

theory:
  facts:
    bird: [[tweety]]
    penguin: [[opus]]
  strict_rules:
    - id: r1
      head: "bird(X)"
      body: ["penguin(X)"]
  defeasible_rules:
    - id: r2
      head: "flies(X)"
      body: ["bird(X)"]
  defeaters:
    - id: r3
      head: "~flies(X)"
      body: ["penguin(X)"]
  superiority:
    - [r3, r2]
  conflicts:             # optional: explicit mutual exclusivity
    - [flies, "~flies"]

# Single-policy expectation:
expect:
  definitely:
    bird: [[tweety], [opus]]
  defeasibly:
    flies: [[tweety]]
  not_defeasibly:
    flies: [[opus]]

# OR multi-policy expectation:
expect_per_policy:
  blocking:
    defeasibly:
      q: [[a]]
  propagating:
    ambiguous:
      q: [[a]]
```

**For KLM property tests:**

```yaml
name: string
description: string
source: string
tags: [klm, property_name]

# KLM property tests specify a property and theories that should satisfy/violate it
klm_property: CM              # Reflexivity|LLE|RW|And|Or|CM|RM
theories:
  - theory: { ... }
    satisfies:
      rational_closure: true
      lexicographic_closure: true
      relevant_closure: false   # Morris counterexample
```

### 1.4 Build the pytest plugin

`src/datalog_conformance/plugin.py` — follows the moo-conformance-tests pattern:

1. **`pytest_addoption`**: Add `--datalog-evaluator` option (import path to evaluator class) and `--datalog-tags` for filtering.
2. **`discover_yaml_tests()`**: Walk `_tests/`, parse YAML, validate via schema dataclasses.
3. **`pytest_generate_tests()`**: Parametrize a single test function with `(suite_file, test_case)` pairs. Test IDs: `basic/joins::two_predicate_body`.
4. **Tag filtering**: `--datalog-tags=recursion,basic` runs only tests with those tags.
5. **Skip handling**: Tests with `skip:` are `pytest.skip(reason)`.

### 1.5 Build the runner

`src/datalog_conformance/runner.py`:

1. Load the evaluator class from the import path.
2. For each test case:
   - If `program:` key → construct `Program` from YAML, call `DatalogEvaluator.evaluate()`, compare `Model` against `expect:`.
   - If `theory:` key → construct `DefeasibleTheory` from YAML, call `DefeasibleEvaluator.evaluate()` for each policy in `expect_per_policy:`, compare.
   - If `expect_error:` → assert the evaluator raises the expected error type.
3. Comparison: expected tuples are compared as sets (order-independent). Model predicates not in `expect:` are ignored (open-world: we only assert on what the test specifies).

### 1.6 Meta-tests

`tests/test_schema.py`: Schema dataclass round-trips (YAML → dataclass → dict → YAML).
`tests/test_plugin.py`: Plugin discovers test files, parametrizes correctly.
`tests/test_runner.py`: Runner with a trivial mock evaluator (returns hardcoded facts) passes/fails correctly.

---

## Phase 2: Harvest Core Datalog Tests

**Gate:** At least 100 core Datalog test cases in `_tests/basic/`, `_tests/recursion/`, `_tests/negation/`, `_tests/errors/`.

### 2.1 Souffle harvester

`scripts/harvest_souffle.py`:

- Clone `souffle-lang/souffle` (or point at local checkout)
- Walk `tests/semantic/` and `tests/evaluation/`
- For each test directory: read `.dl` file, parse facts and rules, read expected `.csv` outputs
- Convert to YAML schema
- Write to `_tests/{category}/souffle_{name}.yaml`
- Track source attribution: `source: "souffle/semantic/{dirname}"`

Souffle syntax is close to standard Datalog but has extensions (aggregates, ADTs, functors). The harvester should:
- Convert the syntactically portable subset (basic rules, negation, recursion)
- Skip tests that use Souffle-specific features (mark as `skip: "souffle-specific extension"`)
- Log what was converted vs skipped

Target: ~150-200 portable tests from Souffle's 383 categories.

### 2.2 Nemo harvester

`scripts/harvest_nemo.py`:

- Read from `knowsys/nemo` `resources/testcases/`
- Nemo syntax is cleaner, closer to textbook. Less filtering needed.
- Target: ~50-60 tests from Nemo's 83 files.

### 2.3 crepe error harvester

`scripts/harvest_crepe.py`:

- Read from `ekzhang/crepe` `tests/ui/`
- These are programs that should be rejected (unbound vars, arity mismatches, etc.)
- Convert to `expect_error:` format
- Target: ~20-30 error/rejection tests.

### 2.4 Manual curation pass

After harvesting, review all converted tests:
- Remove duplicates across sources
- Ensure tags are consistent
- Verify expected outputs are correct (spot-check against source)
- Write `docs/HARVESTING.md` documenting provenance

---

## Phase 3: Harvest Defeasible Reasoning Tests

**Gate:** At least 50 defeasible test cases in `_tests/defeasible/`.

### 3.1 SPINdle harvester

`scripts/harvest_spindle.py`:

- Source: `spindle-racket` on Codeberg (LGPL-3.0, 800+ test cases)
- Convert SPINdle's defeasible theory format to our YAML schema
- Map SPINdle's rule types to our `strict_rules`/`defeasible_rules`/`defeaters`
- Map SPINdle's superiority declarations
- SPINdle supports both ambiguity blocking and propagating — harvest both
- Target: ~80-100 defeasible tests

### 3.2 DePYsible tests

- Source: `stefano-bragaglia/DePYsible` (BSD-2-Clause)
- 8 Python test files — manually convert to YAML
- These are small but directly in Python, easy to verify
- Target: ~15-20 tests

### 3.3 Paper-derived tests

Manually author from explicit examples in the papers:

**Maher 2021:**
- Example 3 (p.8): team defeat scenario
- Example theories from Theorems 15, 19 verification
- Structural property examples from Theorem 21

**Antoniou 2007:**
- p.13: ambiguity blocking meta-program examples
- p.14: ambiguity propagating variant examples
- p.22: performance benchmark theories (if sizes are given)

**Morris 2020:**
- Example 3 (p.9): BaseRank computation
- Example 5 (p.11): variable/constant interaction limitation
- pp.26-29: KLM failure counterexamples for Relevant Closure (Or, CM, RM)
- Rational/Lexicographic examples from pp.15-18

**Goldszmidt 1992:**
- p.5: tolerance examples
- p.7: System Z equivalence examples

Target: ~30-40 paper-derived tests.

---

## Phase 4: Hypothesis Property Tests

**Gate:** Hypothesis strategies generate valid programs; property tests run green with a reference evaluator.

### 4.1 Datalog program generators

`src/datalog_conformance/strategies.py` (or in the test files):

```python
from hypothesis import strategies as st

# Strategy: generate a random Datalog program
# - N predicates with random arities
# - M facts with random constants
# - K rules with random bodies (respecting arity)
# - Ensure range-restriction (all head vars appear in body)
```

### 4.2 Properties to test

These go in `tests/test_properties.py` (meta-level — properties of the test suite and evaluator protocol):

1. **Fixpoint property**: `evaluate(P).facts` is a fixpoint of `P.rules` — applying rules to the model produces no new facts.
2. **Monotonicity of facts**: Adding a fact to `P` can only add conclusions, never remove (for positive Datalog without negation).
3. **Determinism**: `evaluate(P) == evaluate(P)` always (same program → same model).
4. **Subset property**: For stratified programs, stratum-k model is a subset of the final model.
5. **Empty program**: `evaluate(empty) == empty_model`.
6. **Facts-only**: `evaluate(facts_only) == facts` (no rules → model equals input facts).

For defeasible:
7. **Definite subsumes defeasible**: Everything `definitely` provable is also `defeasibly` provable.
8. **Strict-only equivalence**: A defeasible theory with only strict rules should produce the same conclusions as a standard Datalog program with those rules.
9. **KLM properties** (for Rational/Lexicographic closure): generated random theories satisfy Reflexivity, LLE, RW, And, Or, CM, RM.

---

## Phase 5: Documentation and Polish

**Gate:** README is complete, YAML_SCHEMA.md documents every field, HARVESTING.md has full provenance.

### 5.1 README.md

- What this is, why it exists
- How to install: `uv add datalog-conformance --dev`
- How to run against your evaluator: `uv run pytest --datalog-evaluator=mypackage.MyEvaluator`
- How to filter: `--datalog-tags=defeasible,basic`
- Test count summary by category
- License and attribution

### 5.2 YAML_SCHEMA.md

Complete field reference for all three test types (core, defeasible, KLM).

### 5.3 HARVESTING.md

Per-source documentation:
- Souffle: which directories, what was converted, what was skipped, license (UPL-1.0)
- Nemo: same (Apache-2.0)
- SPINdle: same (LGPL-3.0 — note implications for the test suite's license)
- crepe: same (Apache-2.0)
- DePYsible: same (BSD-2-Clause)
- Papers: which examples from which pages

### 5.4 CLAUDE.md

Project instructions for AI assistants working on this repo.

---

## Hard Gates (summary)

| Phase | Gate | Metric |
|-------|------|--------|
| 1 | Scaffolding works | `uv run pytest tests/` green, plugin discovers YAML |
| 2 | Core Datalog tests | >= 100 tests in basic/recursion/negation/errors |
| 3 | Defeasible tests | >= 50 tests in defeasible/ |
| 4 | Property tests | Hypothesis strategies generate valid programs, properties hold |
| 5 | Documentation | README, YAML_SCHEMA, HARVESTING all complete |

---

## Dependency Note

The conformance suite has NO dependency on the evaluator package. It depends only on pytest, pyyaml, and hypothesis. The evaluator is provided at test time via `--datalog-evaluator` CLI option or a pytest fixture. This is the same pattern as moo-conformance-tests where the MOO server is external.

When the evaluator package exists, it will add `datalog-conformance` as a dev dependency and provide its evaluator class for the plugin to test against.

## License Consideration

SPINdle tests are LGPL-3.0. The test YAML files derived from SPINdle should carry attribution. Since the conformance suite is MIT and the YAML test cases are data (not code linked into the evaluator), LGPL should not infect the evaluator package. But note this in HARVESTING.md and get Q's read on it.
