# Architecture Audit — 2026-03-24

## Methodology

Read every `.py` file under `propstore/`, mapped all imports, classified each
module into the declared six-layer architecture, and checked for violations.

---

## 1. Layer Assignment (as observed)

| Layer | Modules |
|-------|---------|
| 1 Source-of-truth storage | `stances.py`, `worldline.py` (data classes only), `cli/repository.py`, `cli/helpers.py` (YAML I/O, counters) |
| 2 Theory/typing | `cel_checker.py`, `z3_conditions.py`, `form_utils.py`, `unit_dimensions.py`, `opinion.py`, `calibrate.py`, `value_comparison.py`, `validate.py`, `validate_claims.py`, `validate_contexts.py`, `sympy_generator.py`, `description_generator.py`, `propagation.py`, `parameterization_groups.py`, `parameterization_walk.py`, `resources.py` |
| 3 Heuristic analysis | `embed.py`, `relate.py`, `condition_classifier.py`, `conflict_detector/` |
| 4 Argumentation | `dung.py`, `dung_z3.py`, `preference.py`, `argumentation.py`, `structured_argument.py`, `praf.py`, `praf_dfquad.py`, `praf_treedecomp.py`, `maxsat_resolver.py`, `param_conflicts.py` |
| 5 Render | `world/` (model, bound, hypothetical, resolution, atms, value_resolver, types, labelled), `sensitivity.py`, `graph_export.py`, `worldline_runner.py` |
| 6 Agent workflow | `cli/` commands, `build_sidecar.py` |

---

## 2. UPWARD Dependencies (Layer Violations)

### CRITICAL: `relate.py` (Layer 3) imports from `cli/helpers.py` (Layer 6)

**File:** `/propstore/relate.py:15`
```python
from propstore.cli.helpers import write_yaml_file
```

The heuristic analysis layer (`relate.py`) reaches **up** into the CLI/agent
workflow layer to get a YAML writing utility. `write_yaml_file` is a trivial
function (`yaml.dump` wrapper) that has no business living in the CLI layer.
The `relate.py` module uses it in `write_stance_file()` to persist stance
classification results to disk. This is both a layer violation and a sign that
`relate.py` conflates two concerns: classifying stances (heuristic) and
writing files to the knowledge store (workflow).

### MODERATE: `build_sidecar.py` (Layer 6) imports from `validate.py` (Layer 2) — OK direction, but...

`build_sidecar.py:33` has `from propstore.cli.repository import Repository`
under `TYPE_CHECKING`, and `validate_claims.py:19` has the same. These are
fine as TYPE_CHECKING guards. However, `world/model.py:46` has a **runtime**
import of `from propstore.cli.repository import Repository` inside `from_path()`.
The WorldModel (Layer 5) pulls in the CLI layer at runtime. This should be
refactored so Repository is injected, not imported.

### MODERATE: `validate.py` (Layer 2) TYPE_CHECKING import from `cli/repository.py`

`validate.py:32` and `validate_claims.py:19` both import `Repository` under
`TYPE_CHECKING`. This is tolerable but creates a conceptual dependency of the
typing layer on the CLI layer. The `Repository` type should live in a shared
infrastructure module, not in `cli/`.

---

## 3. Core Principle Violations: Heuristic Output Mutating Source-of-Truth

### CRITICAL: `relate.py:write_stance_file()` writes directly to knowledge/stances/

`relate.py:468-489` writes stance classification results (LLM output) directly
to the knowledge store on disk:

```python
def write_stance_file(stances_dir, source_claim_id, stances, model_name):
    stances_dir.mkdir(parents=True, exist_ok=True)
    ...
    path = stances_dir / f"{safe_name}.yaml"
    write_yaml_file(path, data)
```

This is called from `cli/claim.py:428` which imports `write_stance_file`.
The heuristic analysis layer (LLM stance classification) writes **directly**
to source-of-truth storage. Per the design principle, heuristic output should
be proposal artifacts, never source mutations. The fact that these stance files
are then consumed by `build_sidecar.py:_populate_stances_from_files()` and
become part of the sidecar means LLM output enters the argumentation layer
as hardened data.

There is no "proposal" intermediary. The LLM says "rebuts:strong" and it goes
straight into `knowledge/stances/` and then into the AF.

### MODERATE: `embed.py` writes directly to the sidecar database

`embed.py:embed_claims()` and `embed_concepts()` write embedding vectors and
status rows directly into the sidecar SQLite database. While the sidecar is a
derived artifact (rebuilt from source), the embeddings persist across rebuilds
via `extract_embeddings()`/`restore_embeddings()`. This blurs the line between
the sidecar as a deterministic compilation of source data and the sidecar as a
cache for heuristic computations.

---

## 4. Build-Time Filtering vs Render-Time Filtering

### MODERATE: `build_sidecar.py` runs conflict detection at build time

`build_sidecar.py:305` runs `_populate_conflicts()` during sidecar build,
which calls `detect_conflicts()` and stores results in a `conflict` table.
These conflicts are then used by `BoundWorld._recomputed_conflicts()` at
render time, which re-runs conflict detection on the active claims.

The build-time conflict table is essentially dead: the render layer recomputes
conflicts over active claims anyway (`world/bound.py:82-100`). The build-time
table pre-computes conflicts over ALL claims regardless of conditions, which
means it includes phi-node conflicts that may not be relevant to the current
belief space. This is not harmful (render recomputes) but is wasteful and
misleading — it suggests build-time filtering matters when it does not.

### LOW: `argumentation.py:137` prunes vacuous opinions at AF construction time

```python
if opinion_u is not None and opinion_u > 0.99:
    continue
```

This is documented as a "performance optimization only" and the threshold
(0.99) is near-vacuous, so it's arguably acceptable. But it IS a gate before
render time. The comment even cites "Per CLAUDE.md design checklist: no gates
before render time" while violating it.

---

## 5. Circular Imports

### CRITICAL: `praf_treedecomp.py` <-> `praf.py` circular import

- `praf.py:150` imports `from propstore.praf_treedecomp import estimate_treewidth`
- `praf_treedecomp.py:383` imports `from propstore.praf import _evaluate_semantics`

Both are runtime imports (not TYPE_CHECKING). The `praf.py` import is inside
a function body (`compute_praf_acceptance`), and `praf_treedecomp.py:383` is
inside `_compute_brute_force_fallback`. Python handles this via deferred
resolution, but it creates a fragile dependency where import order matters and
refactoring either module risks ImportError.

### MODERATE: `argumentation.py` -> `praf.py` -> `opinion.py` -> (leaf)

`argumentation.py:200` deferred-imports `from propstore.praf import ...` inside
`build_praf()`. This is not circular but is a sign that the argumentation module
is accumulating dependencies on the probabilistic layer.

---

## 6. Dead Code / Unused Imports

### `_FIND_CLAIM_CONFIG.join_columns` references `c.concept_id`

`embed.py:294` references `c.concept_id` in the SQL join column string, but
the claim table column is named `concept_id` only if the claim has one. The
actual column name in the sidecar schema (per `build_sidecar.py`) is indeed
`concept_id`, so this works, but it is fragile — it depends on the schema
having this exact column name.

### `_form_cache` global mutable state in `form_utils.py`

`form_utils.py:56` has `_form_cache: dict[...] = {}` as a module-level
mutable. This survives across test runs and sidecar rebuilds. If a form file
changes on disk, the cached `FormDefinition` is stale. There is no cache
invalidation mechanism.

### `_symbol_table` global mutable state in `unit_dimensions.py`

Same issue: `unit_dimensions.py:33` has `_symbol_table: dict | None = None`
which is never invalidated. `register_form_units()` mutates this global, but
if called multiple times with different `forms_dir`, old registrations persist.

### `equation_comparison.py` — never imported by any propstore module

Searching for `equation_comparison` across all `.py` files:
- No propstore module imports it at runtime.
- It may be imported by tests or external code, but within the propstore
  package itself it appears to be dead code.

---

## 7. CLI Separation of Concerns

### MODERATE: CLI helpers contain business logic

`cli/helpers.py` contains `write_yaml_file()`, `load_concept_file()`,
`CounterLock`, `atomic_next_counter()`, `next_id()`, `find_concept()`, and
`load_all_concepts_by_id()`. Several of these are pure data operations with no
CLI dependency (no `click` usage). They belong in a shared utilities module,
not in `cli/`. This is why `relate.py` had to import from `cli/helpers.py` —
the utility function was mislocated.

### LOW: `cli/compiler_cmds.py` imports heavy modules at command time

Commands like `validate`, `build`, `query` lazy-import heavy dependencies
(`propstore.build_sidecar`, `propstore.world`, etc.) inside Click command
functions. This is fine for CLI performance but makes the actual dependency
graph harder to trace statically.

---

## 8. Additional Findings

### SQL injection surface in `embed.py`

`embed.py:106,111` constructs table names by string concatenation:
```python
table_name = f"{prefix}_{model_key}"
conn.execute(f"CREATE VIRTUAL TABLE [{table_name}] ...")
```

`model_key` comes from `_sanitize_model_key()` which strips non-alphanumeric
characters, so this is mitigated. However, the bracket-quoting `[{table_name}]`
is used inconsistently — some queries use it, some don't. A malicious model
name like `a]--` after sanitization becomes `a___` which is safe, but the
inconsistency in quoting suggests the defense is accidental rather than
systematic.

### `_current_guards` instance state in `z3_conditions.py`

`Z3ConditionSolver._condition_to_z3()` at line 277 sets
`self._current_guards: list[Any] = []` and then the `_translate_binary`
division handler at line 163 appends to `self._current_guards`. This is
thread-unsafe: if two threads call `_condition_to_z3` concurrently, they
share `_current_guards` state. The field is also not initialized in `__init__`,
so accessing it before `_condition_to_z3` would raise `AttributeError`.

### `relate.py` conflates heuristic classification with file I/O

`relate.py` contains both:
1. LLM-based stance classification (`_classify_stance_async`, `classify_stance`)
2. File writing (`write_stance_file`)
3. Database querying (`_get_claim_text`, `_find_shared_concepts`)

This module crosses three layers: it queries the sidecar (render layer), calls
LLMs (heuristic layer), and writes to source storage (storage layer). It
should be split into at least two modules.

### `worldline.py:is_stale()` has a hidden import cycle risk

`worldline.py:285` does `from propstore.worldline_runner import run_worldline`
inside a method. `worldline_runner.py:29` imports from `propstore.worldline`.
This is a deferred circular import that works but is fragile.

### Missing error handling in `build_sidecar.py` embedding restore

`build_sidecar.py:321` catches `(ImportError, Exception)` which is just
`Exception`. The `ImportError` is redundant. More importantly, the broad
`except` silently swallows any error during embedding restore, including
data corruption scenarios, with only a stderr print.

---

## Summary of Severity

| Severity | Count | Key Issues |
|----------|-------|------------|
| CRITICAL | 3 | `relate.py` -> `cli/helpers.py` upward import; `relate.py` writes LLM output directly to source storage; `praf`/`praf_treedecomp` circular import |
| MODERATE | 6 | WorldModel runtime import of CLI Repository; build-time conflict detection is redundant; CLI helpers contain mislocated business logic; global mutable caches without invalidation; `z3_conditions` thread-unsafe state; `relate.py` crosses three architectural layers |
| LOW | 3 | Inconsistent SQL quoting in embed.py; vacuous-opinion pruning gate; dead `equation_comparison.py` module |
