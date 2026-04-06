# Python API

propstore can be used as a Python library, not just via the `pks` CLI. Import from `propstore` directly. This is useful for notebooks, scripts, and integration with other tools.

```python
from propstore import WorldModel

world = WorldModel.from_path("knowledge")
bound = world.bind(task="speech")
result = bound.value_of("fundamental_frequency")
print(result.status, result.claims)
```

Source: `propstore/world/model.py` (WorldModel), `propstore/world/bound.py` (BoundWorld), `propstore/world/hypothetical.py` (HypotheticalWorld), `propstore/world/types.py` (result types, enums, policies).

## WorldModel

The top-level entry point. A WorldModel wraps a compiled sidecar database and provides concept/claim lookup, similarity search, and the `bind()` method that produces query surfaces.

### Construction

| Constructor | Signature | Description |
|-------------|-----------|-------------|
| `WorldModel.from_path` | `(knowledge_dir: str \| Path) -> WorldModel` | Opens from a knowledge directory. Expects sidecar at `{knowledge_dir}/sidecar/propstore.sqlite`. |
| `WorldModel(...)` | `(repo=repo)` or `(sidecar_path=path)` | Direct constructor from a `Repository` object or an explicit sidecar path. |

WorldModel supports the context manager protocol:

```python
with WorldModel.from_path("knowledge") as world:
    bound = world.bind(task="speech")
    result = bound.value_of("fundamental_frequency")
```

### Methods

#### Binding

| Method | Signature | Description |
|--------|-----------|-------------|
| `bind` | `(environment?, *, policy?, **conditions) -> BoundWorld` | Create a condition-bound view. The primary entry point for querying. |
| `chain_query` | `(target_concept_id, strategy?, **bindings) -> ChainResult` | Multi-step derivation through the parameterization graph. |

`bind()` accepts an explicit `Environment` object, a `RenderPolicy`, and/or keyword condition bindings (e.g., `task="speech"`). If both `environment` and keyword conditions are given, the conditions merge into the environment. Context hierarchy and environment assumptions are compiled automatically.

#### Concept lookup

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_concept` | `(concept_id) -> dict \| None` | Look up a concept by ID. |
| `concept_name` | `(concept_id) -> str \| None` | Canonical name for a concept. |
| `concept_names` | `() -> dict[str, str]` | All `{concept_id: canonical_name}` pairs. |
| `all_concepts` | `() -> list[dict]` | Every concept in the knowledge base. |
| `resolve_alias` | `(alias) -> str \| None` | Resolve an alias to a concept ID. |
| `resolve_concept` | `(name) -> str \| None` | Resolve by alias, ID, or canonical name. |

#### Claim lookup

| Method | Signature | Description |
|--------|-----------|-------------|
| `get_claim` | `(claim_id) -> dict \| None` | Look up a claim by ID. |
| `claims_for` | `(concept_id) -> list[dict]` | All claims for a concept. |
| `claims_by_ids` | `(claim_ids: set[str]) -> dict[str, dict]` | Batch claim lookup. |
| `stances_between` | `(claim_ids: set[str]) -> list[dict]` | Stances among a set of claims. |
| `all_claim_stances` | `() -> list[dict]` | All claim-to-claim stances. |
| `conflicts` | `(concept_id?) -> list[dict]` | Conflict witnesses, optionally scoped to a concept. |
| `explain` | `(claim_id) -> list[dict]` | BFS walk of the stance graph from a claim. |

#### Similarity search

| Method | Signature | Description |
|--------|-----------|-------------|
| `search` | `(query) -> list[dict]` | Full-text search over concepts. |
| `similar_claims` | `(claim_id, model_name?, top_k?) -> list[dict]` | Embedding similarity search for claims. |
| `similar_concepts` | `(concept_id, model_name?, top_k?) -> list[dict]` | Embedding similarity search for concepts. |

#### Forms and parameterizations

| Method | Signature | Description |
|--------|-----------|-------------|
| `forms_by_dimensions` | `(dims: dict[str, int]) -> list[dict]` | Find forms by SI dimensions. |
| `form_algebra_for` | `(form_name) -> list[dict]` | Algebra decompositions producing a form. |
| `form_algebra_using` | `(form_name) -> list[dict]` | Algebra entries where a form is an input. |
| `parameterizations_for` | `(concept_id) -> list[dict]` | Parameterization rows for a concept. |
| `group_members` | `(concept_id) -> list[str]` | All concept IDs in the same parameterization group. |

#### Relationships and graph

| Method | Signature | Description |
|--------|-----------|-------------|
| `all_relationships` | `() -> list[dict]` | All concept-to-concept relationships. |
| `compiled_graph` | `() -> CompiledWorldGraph` | Build/cache the compiled semantic graph. |
| `active_graph` | `(environment, *, context_hierarchy?) -> ActiveWorldGraph` | Activate the graph for an environment. |

#### Stats and internals

| Method | Signature | Description |
|--------|-----------|-------------|
| `stats` | `() -> dict` | Counts of concepts, claims, conflicts. |
| `has_table` | `(name) -> bool` | Check if a sidecar table exists. |
| `condition_solver` | `() -> Z3ConditionSolver` | Lazy Z3 condition solver. |
| `close` | `() -> None` | Close the SQLite connection. |

## BoundWorld

A condition-bound view of the knowledge base. Created via `WorldModel.bind()`, not typically constructed directly. This is the primary query surface.

```python
bound = world.bind(task="speech")
```

### Value queries

| Method | Signature | Description |
|--------|-----------|-------------|
| `value_of` | `(concept_id) -> ValueResult` | Get the value status for a concept under current bindings. |
| `derived_value` | `(concept_id, *, override_values?) -> DerivedResult` | Derive a value via parameterization formulas. |
| `resolved_value` | `(concept_id, *, strategy?, policy?) -> ResolvedResult` | Resolve a conflicted concept using a resolution strategy. |

### Claim inspection

| Method | Signature | Description |
|--------|-----------|-------------|
| `active_claims` | `(concept_id?) -> list[dict]` | Claims active under current bindings. |
| `inactive_claims` | `(concept_id?) -> list[dict]` | Claims inactive under current bindings. |
| `algorithm_for` | `(concept_id) -> list[dict]` | Active algorithm claims for a concept. |
| `is_active` | `(claim: dict) -> bool` | Check if a specific claim is active. |
| `is_determined` | `(concept_id) -> bool` | True when `value_of` returns status `"determined"`. |
| `conflicts` | `(concept_id?) -> list[dict]` | Active conflicts, revalidated against current bindings. |
| `explain` | `(claim_id) -> list[dict]` | Stance walk filtered to active claims. |

### ATMS analysis

These methods require the ATMS reasoning backend. Set it via policy:

```python
policy = RenderPolicy(reasoning_backend=ReasoningBackend.ATMS)
bound = world.bind(task="speech", policy=policy)
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `atms_engine` | `() -> ATMSEngine` | The lazy ATMS engine instance. |
| `claim_status` | `(claim_id) -> ATMSInspection` | ATMS status for a claim (TRUE/IN/OUT). |
| `claim_support` | `(claim: dict) -> tuple[Label \| None, SupportQuality]` | Label support and honesty metadata. |
| `claim_stability` | `(claim_id, queryables, limit?) -> dict` | Bounded ATMS stability analysis. |
| `claim_is_stable` | `(claim_id, queryables, limit?) -> bool` | Whether a claim is stable across consistent futures. |
| `concept_stability` | `(concept_id, queryables, limit?) -> dict` | Value-status stability across futures. |
| `concept_is_stable` | `(concept_id, queryables, limit?) -> bool` | Whether a concept's value is stable across futures. |
| `claim_relevance` | `(claim_id, queryables, limit?) -> dict` | Which queryables can flip a claim's status. |
| `concept_relevance` | `(concept_id, queryables, limit?) -> dict` | Which queryables can flip a concept's value. |
| `claim_interventions` | `(claim_id, queryables, target_status, ...) -> list[dict]` | Intervention plans for achieving a target claim status. |
| `concept_interventions` | `(concept_id, queryables, target_value_status, ...) -> list[dict]` | Intervention plans for achieving a target concept value. |
| `claim_next_queryables` | `(claim_id, queryables, target_status, ...) -> list[dict]` | Next-query suggestions for a claim. |
| `concept_next_queryables` | `(concept_id, queryables, target_value_status, ...) -> list[dict]` | Next-query suggestions for a concept. |
| `why_concept_out` | `(concept_id, queryables?, limit?) -> dict` | Explain why a concept lacks ATMS support. |
| `claims_in_environment` | `(environment) -> list[str]` | Claim IDs visible in an ATMS environment. |
| `explain_claim_support` | `(claim_id) -> dict` | ATMS justification trace for a claim. |

### Fragility

| Method | Signature | Description |
|--------|-----------|-------------|
| `fragility` | `(*, concept_id?, queryables?, top_k?, ...) -> FragilityReport` | Rank epistemic targets by fragility. See [fragility.md](fragility.md). |

### Per-call overrides

`resolved_value()` accepts `strategy` and `policy` keyword arguments that override the BoundWorld's default policy for that single call:

```python
# Override strategy for one call
resolved = bound.resolved_value("concept1",
    strategy=ResolutionStrategy.SAMPLE_SIZE)

# Override full policy for one call
resolved = bound.resolved_value("concept1",
    policy=RenderPolicy(strategy=ResolutionStrategy.RECENCY))
```

## HypotheticalWorld

A counterfactual overlay on a `BoundWorld`. Implements the same `BeliefSpace` protocol, so it supports `value_of`, `derived_value`, `resolved_value`, `active_claims`, `inactive_claims`, `is_determined`, `conflicts`, and `explain`.

Constructed by injecting or removing claims from an existing bound view:

```python
from propstore import HypotheticalWorld, SyntheticClaim

bound = world.bind(task="speech")

# Remove a claim and observe consequences
hypo = HypotheticalWorld(bound, remove=["claim1"])
result = hypo.value_of("concept1")

# Add a synthetic claim
sc = SyntheticClaim(
    id="synth1",
    concept_id="concept2",
    type="measurement",
    value=900.0,
    conditions=["task == 'singing'"],
)
hypo = HypotheticalWorld(bound, add=[sc])
result = hypo.value_of("concept2")

# Cascading effects on derived values
hypo = HypotheticalWorld(bound, remove=["claim2", "claim7"])
derived = hypo.derived_value("concept5")
```

`add` injects synthetic claims into the active set. `remove` removes claim IDs from the active set. Effects cascade through derivations -- removing an input claim can change a derived value downstream.

## Result Types

### ValueResult

Returned by `value_of()`. The basic query result.

| Field | Type | Description |
|-------|------|-------------|
| `concept_id` | `str` | The queried concept. |
| `status` | `ValueStatus` | One of the `ValueStatus` enum values. |
| `claims` | `list[dict]` | Matching active claims. |
| `label` | `Label \| None` | ATMS label, if the ATMS backend is active. |

### DerivedResult

Returned by `derived_value()`. A value computed through parameterization formulas.

| Field | Type | Description |
|-------|------|-------------|
| `concept_id` | `str` | The target concept. |
| `status` | `ValueStatus` | Typically `"derived"` or `"underspecified"`. |
| `value` | `float \| None` | The computed value, if derivation succeeded. |
| `formula` | `str \| None` | The symbolic formula used. |
| `input_values` | `dict[str, float]` | Input concept values used in the computation. |
| `exactness` | `str \| None` | Exactness qualifier from the parameterization. |
| `label` | `Label \| None` | ATMS label tracking assumption provenance. |

### ResolvedResult

Returned by `resolved_value()`. A conflict resolution outcome.

| Field | Type | Description |
|-------|------|-------------|
| `concept_id` | `str` | The queried concept. |
| `status` | `ValueStatus` | Typically `"resolved"` or `"conflicted"`. |
| `value` | `float \| str \| None` | The winning value. |
| `claims` | `list[dict]` | Claims considered during resolution. |
| `winning_claim_id` | `str \| None` | ID of the winning claim. |
| `strategy` | `str \| None` | Which strategy was applied. |
| `reason` | `str \| None` | Human-readable explanation. |
| `label` | `Label \| None` | ATMS label, if applicable. |
| `acceptance_probs` | `dict[str, float] \| None` | Per-claim acceptance probabilities (argumentation strategies). |

### ChainResult / ChainStep

Returned by `chain_query()`. A multi-step derivation trace through the parameterization graph.

**ChainStep:**

| Field | Type | Description |
|-------|------|-------------|
| `concept_id` | `str` | The concept resolved at this step. |
| `value` | `float \| str \| None` | The value obtained. |
| `source` | `str` | One of `"binding"`, `"claim"`, `"derived"`, `"resolved"`. |

**ChainResult:**

| Field | Type | Description |
|-------|------|-------------|
| `target_concept_id` | `str` | The target concept. |
| `result` | `ValueResult \| DerivedResult` | The final result for the target. |
| `steps` | `list[ChainStep]` | Ordered derivation steps. |
| `bindings_used` | `dict[str, Any]` | Condition bindings that were active. |
| `unresolved_dependencies` | `list[str]` | Concepts that could not be resolved. |

### SyntheticClaim

Used with `HypotheticalWorld` to inject counterfactual claims.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier for the synthetic claim. |
| `concept_id` | `str` | Which concept this claim is about. |
| `type` | `str` | Claim type (e.g., `"measurement"`). |
| `value` | `float \| str \| None` | The asserted value. |
| `conditions` | `list[str]` | CEL condition strings. |

## Configuration Types

### RenderPolicy

A frozen dataclass controlling how the render layer resolves values. Passed to `bind()` or as a per-call override on `resolved_value()`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `reasoning_backend` | `ReasoningBackend` | `CLAIM_GRAPH` | Which reasoning engine to use. |
| `strategy` | `ResolutionStrategy \| None` | `None` | Default resolution strategy. |
| `semantics` | `str` | `"grounded"` | Argumentation semantics. The enum includes `grounded`, `legacy_grounded`, `hybrid-grounded`, `bipolar-grounded`, `preferred`, `stable`, `d-preferred`, `s-preferred`, `c-preferred`, `bipolar-stable`, and `complete`; backend support is validated separately. |
| `comparison` | `str` | `"elitist"` | Preference comparison mode. |
| `link` | `str` | `"last"` | ASPIC+ preference link type (last-link or weakest-link). |
| `decision_criterion` | `str` | `"pignistic"` | Decision criterion for belief functions (Denoeux 2019). |
| `pessimism_index` | `float` | `0.5` | Hurwicz pessimism index. |
| `show_uncertainty_interval` | `bool` | `False` | Include uncertainty intervals in output. |
| `praf_strategy` | `str` | `"auto"` | PrAF computation strategy. |
| `praf_mc_epsilon` | `float` | `0.01` | PrAF Monte Carlo error tolerance. |
| `praf_mc_confidence` | `float` | `0.95` | PrAF Monte Carlo confidence level. |
| `praf_treewidth_cutoff` | `int` | `12` | Treewidth cutoff for exact PrAF DP routing. |
| `praf_mc_seed` | `int \| None` | `None` | PrAF Monte Carlo RNG seed. |
| `include_conflict_stances` | `bool` | `False` | Include conflict stances in argumentation. |
| `merge_operator` | `MergeOperator` | `SIGMA` | IC-merge aggregation family for multi-branch resolution. |
| `branch_filter` | `tuple[str, ...] \| None` | `None` | Restrict IC-merge sources to specific branches. |
| `branch_weights` | `Mapping[str, float] \| None` | `None` | Per-branch weighting for IC merge. |
| `integrity_constraints` | `tuple[IntegrityConstraint, ...]` | `()` | Explicit integrity constraints for IC merge. |
| `future_queryables` | `tuple[str, ...]` | `()` | Future queryable assumptions for ATMS. |
| `future_limit` | `int \| None` | `None` | Bound on ATMS future-environment exploration. |
| `overrides` | `Mapping[str, str]` | `{}` | Per-concept value overrides. |
| `concept_strategies` | `Mapping[str, ResolutionStrategy]` | `{}` | Per-concept resolution strategy overrides. |

Common configurations:

```python
from propstore import RenderPolicy, ResolutionStrategy, ReasoningBackend

# Default: claim graph, no resolution strategy
default = RenderPolicy()

# Argumentation-based resolution
argum = RenderPolicy(
    reasoning_backend=ReasoningBackend.CLAIM_GRAPH,
    strategy=ResolutionStrategy.ARGUMENTATION,
    semantics="preferred",
)

# ATMS backend with future queryables
atms = RenderPolicy(
    reasoning_backend=ReasoningBackend.ATMS,
    future_queryables=("task == 'singing'",),
)

# ASPIC+ structured argumentation
aspic = RenderPolicy(
    reasoning_backend=ReasoningBackend.ASPIC,
    strategy=ResolutionStrategy.ARGUMENTATION,
    link="last",
    comparison="elitist",
)

# Probabilistic argumentation
praf = RenderPolicy(
    reasoning_backend=ReasoningBackend.PRAF,
    strategy=ResolutionStrategy.ARGUMENTATION,
)
```

`RenderPolicy` also provides `from_dict(data)` and `to_dict()` for serialization.

### ResolutionStrategy

How to pick a winner when multiple active claims disagree.

| Value | Description |
|-------|-------------|
| `RECENCY` | Most recently authored claim wins. |
| `SAMPLE_SIZE` | Claim backed by the largest sample size wins. |
| `ARGUMENTATION` | Compute Dung extensions and pick the accepted claim. |
| `OVERRIDE` | Use the value from `RenderPolicy.overrides`. |
| `IC_MERGE` | Run integrity-constraint merge across branch-scoped sources. |

### ReasoningBackend

Which reasoning engine computes the argumentation graph.

| Value | Description |
|-------|-------------|
| `CLAIM_GRAPH` | Default claim graph with Dung AF. |
| `STRUCTURED_PROJECTION` | Legacy alias of `ASPIC` for parsed/stored inputs. |
| `ASPIC` | ASPIC+ recursive argument construction. Canonical structured backend. |
| `ATMS` | Assumption-based truth maintenance. |
| `PRAF` | Probabilistic argumentation framework. |

### Environment

A frozen dataclass representing condition bindings and context scope.

| Field | Type | Description |
|-------|------|-------------|
| `bindings` | `Mapping[str, Any]` | Condition variable bindings (e.g., `{"task": "speech"}`). |
| `context_id` | `str \| None` | Context scope. |
| `effective_assumptions` | `tuple[str, ...]` | Compiled assumption CEL strings. |
| `assumptions` | `tuple[AssumptionRef, ...]` | Structured assumption references. |

## Protocols

### BeliefSpace

A `Protocol` implemented by both `BoundWorld` and `HypotheticalWorld`. Code that needs to query values without caring whether the world is real or hypothetical can type-hint against `BeliefSpace`.

Required methods: `active_claims`, `inactive_claims`, `value_of`, `derived_value`, `resolved_value`, `is_determined`, `conflicts`, `explain`.

```python
from propstore.world import BeliefSpace

def analyze(space: BeliefSpace, concept_id: str):
    result = space.value_of(concept_id)
    if result.status == "conflicted":
        return space.resolved_value(concept_id)
    return result
```

## Usage Examples

### Basic value lookup

```python
from propstore import WorldModel

world = WorldModel.from_path("knowledge")
bound = world.bind(task="speech")

result = bound.value_of("fundamental_frequency")
if result.status == "determined":
    claim = result.claims[0]
    print(f"{claim['value']} (from {claim['id']})")
elif result.status == "no_claims":
    print("No claims for this concept under current bindings")
```

### Conflict resolution with different strategies

```python
from propstore import WorldModel, ResolutionStrategy

world = WorldModel.from_path("knowledge")
bound = world.bind(task="speech")

# Try different strategies on the same conflicted concept
for strategy in ResolutionStrategy:
    resolved = bound.resolved_value("fundamental_frequency",
        strategy=strategy)
    print(f"{strategy}: {resolved.value} ({resolved.reason})")
```

### Hypothetical queries

```python
from propstore import WorldModel, HypotheticalWorld, SyntheticClaim

world = WorldModel.from_path("knowledge")
bound = world.bind(task="speech")

# What if we remove a controversial claim?
hypo = HypotheticalWorld(bound, remove=["titze_1994_f0_male"])
result = hypo.value_of("fundamental_frequency")
print(f"Without Titze 1994: {result.status}")

# What if we add a new measurement?
sc = SyntheticClaim(
    id="new_measurement",
    concept_id="fundamental_frequency",
    type="measurement",
    value=125.0,
    conditions=["task == 'speech'"],
)
hypo = HypotheticalWorld(bound, add=[sc])
result = hypo.value_of("fundamental_frequency")
print(f"With new measurement: {result.status}, {len(result.claims)} claims")
```

### ATMS analysis

```python
from propstore import WorldModel, RenderPolicy, ReasoningBackend

world = WorldModel.from_path("knowledge")
policy = RenderPolicy(reasoning_backend=ReasoningBackend.ATMS)
bound = world.bind(task="speech", policy=policy)

# Check ATMS status of a claim
status = bound.claim_status("titze_1994_f0_male")
print(f"Status: {status.status}, Quality: {status.support_quality}")

# Value queries with ATMS label tracking
result = bound.value_of("fundamental_frequency")
if result.label:
    print(f"Supported under {len(result.label.envs)} environments")
```

### Chain derivation

```python
from propstore import WorldModel

world = WorldModel.from_path("knowledge")

# Derive a target concept through its parameterization graph
chain = world.chain_query("jitter_percent", task="speech")
print(f"Result: {chain.result.status}")
for step in chain.steps:
    print(f"  {step.concept_id}: {step.value} (from {step.source})")
if chain.unresolved_dependencies:
    print(f"Missing: {chain.unresolved_dependencies}")
```

### Fragility ranking

```python
from propstore import WorldModel, RenderPolicy, ReasoningBackend

world = WorldModel.from_path("knowledge")
policy = RenderPolicy(reasoning_backend=ReasoningBackend.ATMS)
bound = world.bind(task="speech", policy=policy)

report = bound.fragility(top_k=5)
for target in report.targets:
    print(f"{target.concept_id}: fragility={target.score:.2f}, "
          f"cost={target.cost_tier}, roi={target.roi:.2f}")
```
