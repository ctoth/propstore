# Conflict Detection

When two claims bind to the same concept with different values, propstore classifies the disagreement. Not all disagreements are conflicts -- some are legitimate regime splits where claims hold under provably disjoint conditions. The conflict detector determines which case applies, using Z3 satisfiability checking as the primary reasoning engine and interval arithmetic as a conservative fallback.

## Conflict classes

Six classes describe the relationship between any pair of claims that share a concept:

| Class | Meaning | Reported? |
|-------|---------|-----------|
| `COMPATIBLE` | Values agree (within tolerance) or ranges overlap. | No -- compatible pairs are filtered out before recording. |
| `CONFLICT` | Values differ, conditions identical or logically equivalent. Genuine disagreement -- both claims cannot be true simultaneously. | Yes |
| `PHI_NODE` | Values differ, conditions provably disjoint (Z3-verified or interval-verified). Not a conflict -- a regime split. | Yes (informational) |
| `OVERLAP` | Values differ, conditions partially overlapping. Conservative default when conditions cannot be fully analyzed. | Yes |
| `PARAM_CONFLICT` | A value derived through a parameterization chain contradicts a direct claim. The inputs and the output are individually plausible, but the formula connecting them produces a contradiction. | Yes |
| `CONTEXT_PHI_NODE` | Claims belong to mutually excluded contexts in the context hierarchy. Not a conflict -- a context-based regime split. | Yes (informational) |

The detection order matters: value compatibility is checked first (yielding `COMPATIBLE`), then context exclusion (yielding `CONTEXT_PHI_NODE`), then condition classification (yielding `CONFLICT`, `PHI_NODE`, or `OVERLAP`).

## The detection pipeline

The orchestrator (`conflict_detector/orchestrator.py:detect_conflicts`) coordinates the full pipeline:

1. **Build type registries.** A CEL registry is constructed from the concept registry, and a `Z3ConditionSolver` is built if z3 is installed.

2. **Run type-specific detectors.** Four detectors run in sequence, each sharing the Z3 solver:
   - Parameter conflicts (`conflict_detector/parameters.py`)
   - Measurement conflicts (`conflict_detector/measurements.py`)
   - Equation conflicts (`conflict_detector/equations.py`)
   - Algorithm conflicts (`conflict_detector/algorithms.py`)

3. **Run parameterization chain detection.** Single-hop derivation conflicts are checked via `param_conflicts.py`.

Each type-specific detector follows the same pattern:

1. Group claims by concept or signature using collectors (`conflict_detector/collectors.py`)
2. For each group with 2+ claims, check all pairs
3. Skip if values are compatible (`values_compatible()`)
4. Try context-based classification first (`CONTEXT_PHI_NODE` short-circuits further analysis)
5. Fall through to condition classification (Z3 or interval fallback)

### Type-specific grouping and comparison

**Parameter claims** are grouped by concept ID. Values are compared via numeric tolerance (default 1e-9), interval overlap for ranges, and direct equality for non-numeric values. When a concept has 3+ claims, the detector uses equivalence class optimization (see below) instead of O(N^2) pairwise comparison.

**Measurement claims** are grouped by `(target_concept, measure)` tuple. An additional `PHI_NODE` path exists: claims with different `listener_population` values are classified as regime splits regardless of other conditions.

**Equation claims** are grouped by equation signature -- the dependent concept plus sorted independent concepts. Comparison uses SymPy canonical form (`canonicalize_equation()`) to detect algebraically equivalent expressions.

**Algorithm claims** are grouped by concept ID. Comparison uses `ast_compare()` from the `ast_equiv` package, which produces a similarity score and tier. Equivalent claims at tier <= 2 are treated as compatible.

## Z3 condition reasoning

The `Z3ConditionSolver` (`z3_conditions.py`) translates CEL condition ASTs into Z3 expressions and answers two questions: are these conditions disjoint? Are they equivalent?

### Type mapping

Each concept's kind determines its Z3 representation:

| Concept kind | Z3 type | Notes |
|-------------|---------|-------|
| `QUANTITY` | `z3.Real` | Numeric conditions become real arithmetic |
| `CATEGORY` | `z3.EnumSort` | Known values from the concept registry populate the sort |
| `BOOLEAN` | `z3.Bool` | Boolean conditions map directly |
| `STRUCTURAL` / unknown | `z3.Real` | Fallback for untyped concepts |

CEL AST nodes translate to Z3 as follows: `LiteralNode` becomes `z3.RealVal` or `z3.BoolVal`, `NameNode` becomes a typed Z3 variable, `BinaryOpNode` maps to arithmetic and comparison operators, `UnaryOpNode` maps to `z3.Not` or negation, `InNode` becomes a disjunction of equalities, and `TernaryNode` becomes `z3.If`.

Category comparisons get special handling: `concept == 'value'` patterns resolve string literals against the EnumSort's value map.

### Disjointness check (PHI_NODE)

To determine if two condition sets are disjoint, the solver translates both to Z3, asserts both simultaneously, and checks satisfiability. If `solver.check()` returns `UNSAT`, the conditions cannot be simultaneously satisfied -- they describe non-overlapping regimes.

Example: `task == 'speech'` and `task == 'singing'` are disjoint because `task` is a category with an EnumSort, and two distinct enum values cannot be equal.

### Equivalence check (CONFLICT)

To determine if two condition sets are logically equivalent, the solver checks two implications:

1. `A AND NOT B` is UNSAT (everything satisfying A also satisfies B)
2. `B AND NOT A` is UNSAT (everything satisfying B also satisfies A)

If both hold, the conditions are equivalent -- claims under equivalent conditions with different values are genuine conflicts.

### Division-by-zero guards

When translating division expressions, the solver collects non-zero guards (`right != 0`) and conjoins them into the final Z3 expression. Without this, Z3 would treat `x/0` as an uninterpreted total function, producing unsound results.

### Equivalence classes

When a concept has many claims, pairwise comparison is expensive. `partition_equivalence_classes()` partitions N condition sets into equivalence classes in O(N * K) time (K = number of distinct classes) instead of O(N^2):

1. The first condition set becomes the representative of class 0
2. Each subsequent condition set is compared against existing representatives
3. If equivalent to a representative, join that class; otherwise, start a new class

The parameter conflict detector uses this when a concept has 3+ claims:

- **Within each class:** all pairs are `CONFLICT` (same conditions, different values)
- **Between classes:** disjointness is checked once per class-pair using representatives, then the result applies to all member pairs

### Caching

Three levels of caching reduce redundant Z3 work:

- **AST cache:** CEL string to parsed ASTNode
- **Condition expression cache:** single condition string to Z3 expression
- **Condition set cache:** normalized condition tuple to conjoined Z3 expression

## Fallback: interval arithmetic

When Z3 is unavailable or translation fails, the condition classifier falls back to interval arithmetic (`condition_classifier.py`):

1. **Parse conditions** via regex into numeric constraints (`name <= 3.5`), string constraints (`name == 'value'`), and boolean constraints (`name == true`)
2. **Summarize** per-variable bounds into `_NumericConstraint` (lower/upper bounds, equals, excluded) and `_DiscreteConstraint` objects
3. **Check disjointness** by testing whether numeric ranges are non-overlapping or discrete value sets conflict for any shared variable

The fallback is conservative: when conditions are unparseable (e.g., `F1/F0 > 3.0` with division in the variable name), it returns `OVERLAP` rather than risking an incorrect `PHI_NODE`.

## Regime splits

A `PHI_NODE` represents a legitimate regime split -- two claims that hold under provably non-overlapping conditions. The name comes from SSA phi-nodes (Static Single Assignment form), where different values flow from different control-flow branches and merge at a join point.

Regime splits are not conflicts. A claim that "fundamental frequency is 120 Hz when task is speech" does not contradict "fundamental frequency is 300 Hz when task is singing." These describe different regimes of the same concept.

Two paths produce regime splits:

- **Condition-based (`PHI_NODE`):** Z3 or interval arithmetic proves that the condition sets cannot be simultaneously satisfied.
- **Context-based (`CONTEXT_PHI_NODE`):** The context hierarchy reports that the two claims belong to mutually excluded contexts. This check runs before condition analysis and short-circuits further classification.

## Transitive conflicts (PARAM_CONFLICT)

### Single-hop derivation

For each concept with an exact parameterization relationship (`param_conflicts.py`):

1. Collect scalar values for all input concepts
2. Evaluate the SymPy expression with those inputs (after normalizing to SI units via the concept's form definition)
3. Compare the derived value against direct claims for the output concept
4. If incompatible, emit `PARAM_CONFLICT` with a `derivation_chain` describing the computation

### Multi-hop derivation

`detect_transitive_conflicts()` extends this across chains of 2+ parameterization hops (e.g., A -> B -> C):

1. Build parameterization groups and a directed edge graph
2. Seed resolved values from direct claims
3. Forward-propagate derived values through parameterization edges until fixpoint
4. Compare derived values (from 2+ hop chains) against direct claims
5. Skip derivations whose source claims belong to mutually excluded contexts

Single-hop derivations are handled by the single-hop detector and skipped here to avoid duplicates.

## Feeding into argumentation

Conflict records bridge into the argumentation layer through `ConflictWitness` objects stored in `CompiledWorldGraph.conflicts`.

### Which classes generate defeats

Only "real" conflict classes produce defeats:

| Class | Generates defeats? | Reason |
|-------|-------------------|--------|
| `CONFLICT` | Yes | Genuine disagreement under equivalent conditions |
| `OVERLAP` | Yes | Partial disagreement, conservative treatment |
| `PARAM_CONFLICT` | Yes | Derivation chain contradiction |
| `PHI_NODE` | No | Not a real disagreement -- different regimes |
| `CONTEXT_PHI_NODE` | No | Not a real disagreement -- excluded contexts |
| `COMPATIBLE` | No | Not recorded at all |

### Defeat generation

For each real conflict, the system generates **mutual rebutting defeats** -- both `(A rebuts B)` and `(B rebuts A)`:

```
stance_type: "rebuts"
confidence: 0.5
opinion: vacuous (b=0, d=0, u=1, a=0.5)
```

The vacuous opinion (`u=1.0`) means the conflict is registered but carries no evidential weight. It represents "these claims disagree, but we have no evidence about which is right." This follows the honest-ignorance principle (Josang 2001): total uncertainty is expressed as maximal `u`, not as a fabricated confidence value. Resolution strategies in the render layer then determine the winner.

### Priority rules

Existing explicit stances take priority over conflict-derived stances. If an attack already exists between a pair, the conflict-derived stance is skipped. If a one-directional explicit stance exists, only the reverse direction is filled in. The `include_conflict_stances` flag controls whether conflicts generate stances for claims that already have any stances at all.

## CLI usage

```bash
# Show all detected conflicts
pks claim conflicts

# Filter by concept and conflict class
pks claim conflicts --concept fundamental_frequency --class CONFLICT

# Check consistency under current world bindings
pks world check-consistency domain=speech

# Check for multi-hop transitive conflicts
pks world check-consistency --transitive
```

The `pks build` command also runs conflict detection as part of the build pipeline, reporting conflict counts and grouping PHI_NODEs by concept for compact display.

The `pks world fragility` command includes a `--skip-conflict` flag that excludes conflict-based fragility scores from the ranking.

## References

The conflict detection system is original engineering rather than a direct implementation of a published algorithm, but it connects to several foundational ideas:

- **de Kleer 1986** -- The PHI_NODE concept parallels the ATMS idea of environment-labeled data: different assumption sets yield different values without contradiction.
- **Pollock 1987** -- The mutual rebutting defeats generated from conflicts correspond to Pollock's rebutting defeat type, which feeds into the Dung AF and ASPIC+ layers.
- **Josang 2001** -- Vacuous opinions on conflict-derived stances express total uncertainty honestly, following the subjective logic principle that "I don't know" is a valid signal.
