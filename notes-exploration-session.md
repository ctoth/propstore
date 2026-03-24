# Propstore Codebase Exploration: Argumentation → World/Render Layer Seams

## GOAL
Thoroughly understand code seams between argumentation layer and world/render layer; identify where assumptions/environments are tracked vs not; identify current commitments that ATMS-style labeling would need to change.

## STATUS: IN PROGRESS (24 tool calls completed)

## FINDINGS SO FAR

### 1. ARGUMENTATION LAYER (dung.py, preference.py)

**dung.py Structure:**
- Pure Dung AF: `ArgumentationFramework(arguments, defeats, attacks=None)`
- Arguments are string identifiers
- Defeats = attack pairs surviving preference filter
- Attacks = full attack set before preference filtering
- Extension semantics: grounded, preferred, stable, complete
- All computed over a single (Args, Defeats) pair

**Key Observation:** NO ASSUMPTION/ENVIRONMENT TRACKING
- Extensions are computed as sets of argument IDs
- No label structure (de Kleer ATMS style)
- No context/environment parameter in AF structure
- conflict_free() checks against attacks (pre-preference)
- defends() checks against defeats (post-preference)

**preference.py Structure:**
- `claim_strength(claim)`: computes ordinal strength from metadata (sample_size, uncertainty, confidence)
- `defeat_holds(attack_type, attacker_strengths, target_strengths, comparison)`: determines if attack succeeds
  - Undercutting/supersedes: always succeed (preference-independent)
  - Rebutting/undermining: succeed iff attacker NOT strictly weaker
- `strictly_weaker()`: Elitist vs Democratic comparison modes

**Key Observation:** PREFERENCES ARE STATIC
- claim_strength is computed once from static metadata
- defeat_holds is deterministic given strengths
- No environment/context parameter
- Strength vectors are scalar floats or lists of floats, not parameterized by environment

### 2. RENDER/WORLD LAYER (world/types.py, model.py, worldline.py)

**Environment Data Structure (types.py):**
```python
@dataclass(frozen=True)
class Environment:
    bindings: Mapping[str, Any]          # e.g., {"temp": 25.3}
    context_id: str | None = None         # which context active
    effective_assumptions: tuple[str, ...] = field(default_factory=tuple)
```

**RenderPolicy (types.py):**
```python
@dataclass(frozen=True)
class RenderPolicy:
    reasoning_backend: ReasoningBackend = "claim_graph"
    strategy: ResolutionStrategy | None = None  # recency, sample_size, argumentation, override
    semantics: str = "grounded"
    comparison: str = "elitist"
    confidence_threshold: float = 0.5
    overrides: Mapping[str, str] = field(default_factory=dict)
    concept_strategies: Mapping[str, ResolutionStrategy] = field(default_factory=dict)
```

**WorldModel (model.py):**
- Read-only reasoner over SQLite sidecar
- Loads concepts, claims, claim_stances from DB
- Has methods: get_concept, get_claim, claims_for, stances_between, conflicts
- Creates BoundWorld via `bind(environment, policy, **conditions)` method
- Builds Z3ConditionSolver lazily

**WorldlineDefinition (worldline.py):**
- Question part: id, name, inputs (bindings + overrides + context), policy, targets
- Answer part: results (values, steps, dependencies, sensitivity, argumentation)
- Stateless artifact (can be serialized to/from YAML)

**Key Observations:**
- Environment is tracked at bind() time
- BUT: Context hierarchy effects (effective_assumptions) are resolved once at bind(), not dynamically
- No label structures passed to argumentation layer
- Assumptions are tuple of strings, not parameterized constraints

### 3. CRITICAL GAP: How Does Argumentation Get Called?

**From worldline.py:**
- I see WorldlineDefinition but need to check worldline_runner.py to see how AF is constructed
- Results include "argumentation" field but structure unknown
- RenderPolicy has semantics="grounded" but which extension semantics used?

**From types.py:**
- ResolutionStrategy.ARGUMENTATION exists but not yet seen implementation
- No clear API for constructing AF from claims + stances

## TODO NEXT

Need to read:
1. propstore/worldline_runner.py — how is AF materialized from claims?
2. propstore/world/bound.py — BoundWorld implementation
3. propstore/world/resolution.py — the resolve() function
4. propstore/maxsat_resolver.py — max-sat resolution
5. propstore/propagation.py — what propagates?
6. propstore/z3_conditions.py — condition solver
7. propstore/conflict_detector/ — conflict detection
8. tests/test_worldline.py — see actual execution paths
9. tests/test_semantic_repairs.py — see repair mechanisms

## KEY HYPOTHESES TO VERIFY

1. **Assumptions are not environment-parameterized:** claim_strength and defeat_holds take only static inputs, not Environment
2. **Extensions are computed once, not per-environment:** Need to see if AF is rebuilt per environment
3. **No ATMS-style labeling:** Environment tracking is shallow (bindings dict + context_id), not label structures
4. **Render-time commitment:** Once a resolution strategy picks a winner, that's the canonical fact in values/steps
5. **Ground truth is immutable:** Sidecar (SQLite) is never mutated by render logic

## CONNECTIONS TO MAKE

- claim_strength → used where? (guess: when building argument strengths)
- defeat_holds → used where? (guess: when filtering attacks to defeats)
- effective_assumptions → used where? (guess: condition filtering?)
- Z3ConditionSolver → validates which conditions? When?
- "argumentation" in WorldlineResult → what structure? How computed?

