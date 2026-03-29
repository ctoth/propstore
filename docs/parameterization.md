# Parameterization and Sensitivity

Concepts in a knowledge base are not isolated quantities -- they are connected by algebraic relationships. Fundamental frequency relates to vocal tract length and formant spacing; sample size relates to statistical power and effect size. propstore can express these relationships as symbolic equations, derive values through them, detect conflicts across derivation chains, and analyze which inputs most influence derived quantities.

The parameterization subsystem spans layers 2 through 5 of the architecture: relationships are defined in the typing layer, derivation and conflict detection operate in the heuristic and argumentation layers, and sensitivity analysis feeds into the render layer via worldlines.

Source: `propstore/propagation.py` (evaluation engine), `propstore/sensitivity.py` (sensitivity analysis), `propstore/parameterization_groups.py` (connected components), `propstore/parameterization_walk.py` (graph traversal), `propstore/param_conflicts.py` (conflict detection), `propstore/world/value_resolver.py` (recursive derivation), `propstore/world/model.py` (chain queries).

## Defining Relationships

Parameterization relationships are declared in concept YAML files under the `parameterization_relationships` key. Each entry describes a symbolic equation linking one output concept to one or more input concepts.

```yaml
parameterization_relationships:
  - formula: "ra = ta * F0"
    sympy: "Eq(concept5, concept6 * concept1)"
    inputs: ["concept6", "concept1"]
    exactness: exact
    source: "Fant_1985"
    bidirectional: true
    conditions: ["task == 'speech'"]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `formula` | string | yes | Human-readable formula (e.g. `ra = ta * F0`) |
| `sympy` | string | no | SymPy expression for symbolic evaluation |
| `inputs` | list[string] | yes | Concept IDs of all input quantities |
| `exactness` | `exact` or `approximate` | yes | Whether the relationship is exact or an empirical fit |
| `conditions` | list[string] | no | CEL expressions defining when the relationship holds |
| `source` | string | yes | Paper or source citation |
| `bidirectional` | boolean | yes | Whether the relationship can be solved in either direction |
| `fit_statistics` | string | no | Goodness-of-fit info for approximate relationships |
| `note` | string | no | Free-text note |

The `sympy` field accepts two forms. The `Eq(y, expr)` form declares an equation that can be solved for the output concept symbol. A bare expression (no `Eq` wrapper) is evaluated by direct substitution of input values.

Schema definition: `schema/concept_registry.linkml.yaml` (lines 254-284).

## Parameterization Groups

Concepts linked by parameterization edges form connected components called **parameter space groups**. Two concepts are in the same group if any chain of parameterization relationships connects them, regardless of direction.

Groups are computed by `build_groups()` in `propstore/parameterization_groups.py` using union-find with path compression and union-by-rank. For each concept's `parameterization_relationships`, the function unions the output concept with each input concept. Concepts with no parameterization links appear as singleton groups.

The sidecar build step (`propstore/build_sidecar.py`) persists groups to a `parameterization_group` table, mapping each concept to a sequential group ID (0, 1, 2...). At query time, `WorldModel._group_members(concept_id)` retrieves all concepts in the same group -- this is the scope for chain queries and transitive conflict detection.

## Deriving Values

### Single-hop: `derived_value()`

The recursive derivation engine lives in `ActiveClaimResolver.derived_value()` (`propstore/world/value_resolver.py`, line 55). For a given concept, it:

1. Gets all parameterizations for the concept
2. Filters to those compatible with the current context (CEL condition checking)
3. For each compatible parameterization, attempts derivation via `_derive_from_parameterization()`

Input resolution follows a priority chain: **override values** first, then **direct claim lookup** via `value_of()`, then **recursive derivation** for undetermined inputs. Cycle detection via a derivation stack prevents infinite recursion. If any input is conflicted, derivation halts -- conflict resolution is the render layer's job, not the derivation engine's.

The result is a `DerivedResult` with status (`derived`, `underspecified`, `conflicted`, `no_relationship`), value, formula, input values, and exactness.

Evaluation delegates to `evaluate_parameterization()` in `propstore/propagation.py`, which handles both `Eq()` form (solved via `sympy.solve()`) and bare expressions (direct substitution). Self-referencing inputs (where the output concept appears in the input list) are excluded before evaluation.

### Multi-hop: `chain_query()`

When a single derivation step is not enough -- because the necessary inputs are themselves derived quantities -- `chain_query()` performs iterative fixpoint derivation across the entire parameter space group.

`WorldModel.chain_query()` (`propstore/world/model.py`, line 734):

1. **Bind** the world with optional policy and bindings
2. **Get the parameterization group** for the target concept
3. **Iterate** over the group until no more progress:
   - For each unvisited concept in the group, try direct claim lookup, conflict resolution (if a strategy is provided), or derivation with all currently resolved values as overrides
   - Each resolved concept is added to the override pool and recorded as a `ChainStep`
4. **Final attempt**: if the target is still unresolved, try one more derivation with the full set of resolved values

Each `ChainStep` records the concept, value, and source (`binding`, `claim`, `derived`, or `resolved`). The final `ChainResult` includes the target result, all chain steps, bindings used, and any unresolved dependencies.

### Overrides

Overrides are context-local hypotheses (Martins 1983) that bypass the belief space entirely. They are `float` or `string` values passed to `derived_value()` as `override_values`, which take priority over any stored claims. Overrides are not synthetic claims -- they do not compete with stored beliefs or participate in argumentation. They exist only for the scope of a single derivation or worldline materialization.

## Sensitivity Analysis

The sensitivity engine (`propstore/sensitivity.py`) computes symbolic partial derivatives and elasticities, answering the question: "which input most influences this output?"

For a parameterized concept with expression `f(x1, x2, ...)`:

1. Parse the SymPy expression and extract the RHS (if `Eq` form)
2. Resolve current input values: overrides, then direct claims, then recursive derivation
3. For each input `xi`:
   - Compute the symbolic partial derivative `df/dxi` via `sympy.diff()`
   - Evaluate numerically at current input values
   - Compute **elasticity**: `(df/dxi) * (xi / f)` -- the normalized sensitivity

Elasticity is the key output. It measures the percentage change in the output per percentage change in the input, making sensitivities comparable across inputs with different units and magnitudes. An elasticity of 1.0 means a 1% change in the input produces a 1% change in the output.

Results are sorted by `|elasticity|` descending. The `SensitivityResult` includes the formula, all `SensitivityEntry` records (input concept, symbolic partial derivative, numerical partial derivative, elasticity), current input values, and the computed output value.

## Parameterization Conflict Detection

### Single-hop (PARAM_CONFLICT)

`_detect_param_conflicts()` in `propstore/param_conflicts.py` (line 100) checks for inconsistencies between derived and directly claimed values. For each concept with exact parameterizations:

1. Collect scalar claims for all input concepts
2. Normalize values to SI via form conversions
3. Evaluate the SymPy expression
4. Compare the derived value with direct claims for the output concept
5. If incompatible, emit a `PARAM_CONFLICT` record with the full derivation chain

### Multi-hop (transitive)

`detect_transitive_conflicts()` (line 226) extends conflict detection across chains of two or more hops. For groups with three or more concepts:

1. Use `build_groups()` to find connected components
2. Build directed edges via `parameterization_edges_from_registry()`
3. Perform iterative forward propagation: seed with direct claim values, derive new values through edges until fixpoint (max `len(group) * 2` iterations)
4. Compare derived endpoint values against direct claims
5. Skip single-hop conflicts (already found by `_detect_param_conflicts`)

Context merging via `_merge_contexts_for_derivation()` (line 74) rejects incoherent derivation paths -- if two edges along a chain require mutually exclusive conditions, the path is discarded.

## CLI Usage

```bash
# Derive a single concept value
pks world derive concept5 domain=speech

# Multi-hop chain derivation with conflict resolution strategy
pks world chain concept5 domain=speech --strategy sample_size

# Sensitivity analysis (text or JSON output)
pks world sensitivity concept5 domain=speech
pks world sensitivity concept5 domain=speech --format json

# Export the parameterization graph (DOT or JSON, optionally filtered by group)
pks world export-graph --group 0 --format dot
```

The `pks worldline run` command also integrates parameterization: for any target with status `derived`, sensitivity analysis is automatically included in the worldline result.

## How It Connects

- **Worldlines** use `derived_value()` and `chain_query()` during materialization, and include sensitivity results for derived targets. See [worldlines.md](worldlines.md).
- **Fragility** uses sensitivity data for its parametric dimension -- concepts that are inputs to parameterizations but have no measurements are flagged as high-fragility targets.
- **ATMS** materializes parameterization justifications during label propagation, indexing derived values by their assumption sets.
- **Conflict detection** uses parameterization groups to scope transitive chain analysis, avoiding unbounded graph walks.

## References

- Martins 1983 -- override semantics: context-local hypotheses that supersede stored beliefs without competing with them. Referenced in `propstore/worldline_runner.py`.
