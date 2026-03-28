# Epistemic Fragility System — Implementation Plan

**Goal:** Answer "What is the cheapest thing I could learn that would most change what I believe?" by fusing parametric sensitivity, ATMS stability/relevance, and conflict topology into a ranked list of epistemic interventions.

## Architecture Overview

```
                    ┌──────────────────────────┐
                    │   fragility.rank()        │  ← public API
                    │   Returns: ranked list of │
                    │   FragilityTarget objects  │
                    └────────┬─────────────────┘
                             │ combines scores
              ┌──────────────┼──────────────────┐
              │              │                  │
   ┌──────────▼───┐  ┌──────▼──────┐  ┌────────▼────────┐
   │  Parametric   │  │  Epistemic  │  │  Conflict-      │
   │  Sensitivity  │  │  Stability  │  │  Topological    │
   │              │  │             │  │                 │
   │ sensitivity.py│  │ atms.py    │  │ praf.py +       │
   │ (existing)   │  │ (existing) │  │ conflict_det.   │
   └──────────────┘  └─────────────┘  └─────────────────┘
```

The fragility module sits at the **render layer** (layer 5). It reads from argumentation (layer 4) and theory (layer 2) but never mutates source storage. It produces ranked recommendations — proposals, not truth.

### Why render layer, not argumentation layer

The fragility ranking depends on a render policy (which resolution strategy? which semantics? which decision criterion?). Different policies yield different fragility rankings. The same corpus might prioritize "get more samples for claim X" under one policy and "resolve the conflict between Y and Z" under another. This is a render-time concern.

## Module 1: N-Source Weighted Belief Fusion

**File:** `propstore/opinion.py` (additions to existing module)

### What to add

Two new functions following van der Heijden 2018:

**`wbf(*opinions: Opinion) -> Opinion`** — Weighted Belief Fusion (Definition 4)

The N-source WBF formula weights each source's contribution by its certainty (1 - u). For N opinions ω₁...ωN:

```
b_fused(x) = Σᵢ [bᵢ(x) · (1/uᵢ) · Πⱼ≠ᵢ uⱼ] / κ
u_fused    = Πⱼ uⱼ / κ
```

where κ is a normalizing denominator. When all sources have equal uncertainty, WBF reduces to simple averaging of belief masses — this is a required property (van der Heijden Theorem 1).

The pairwise `consensus_pair` already implements the N=2 case. WBF generalizes it. The existing `consensus()` fold is NOT equivalent to true N-source WBF because pairwise folding loses the weighting symmetry (the fold order affects results when more than 2 dogmatic-ish opinions are involved). The N-source formula computes the correct result directly.

**`ccf(*opinions: Opinion) -> Opinion`** — Cumulative & Compromise Fusion (Definition 5)

CCF handles the case where WBF cannot (all sources dogmatic). Three phases:
1. **Consensus extraction:** Find shared belief mass across all sources
2. **Compromise:** Average the residual belief mass
3. **Normalization:** Ensure b + d + u = 1

CCF is needed because WBF's denominator κ → 0 when all uᵢ → 0. CCF gracefully handles this by switching to averaging.

**Combined entry point: `fuse(*opinions: Opinion, method: str = "auto") -> Opinion`**

- `method="wbf"`: always WBF (raises if all dogmatic)
- `method="ccf"`: always CCF
- `method="auto"`: WBF if any source has u > 0; CCF if all dogmatic

### Rationale

The existing `consensus()` uses pairwise folding. For 2 sources this is correct, but for N > 2 sources it accumulates rounding asymmetry. `relate.py` currently calls `consensus_pair` once (two sources: categorical opinion + corpus distance opinion). When fragility analysis fuses opinions from multiple papers about the same claim, we need the true N-source formula.

### Edge cases

- Single opinion: return it unchanged
- All vacuous: return vacuous (WBF numerator is all zeros, CCF compromise phase produces uniform)
- Mixed dogmatic/uncertain: WBF handles this (dogmatic sources get infinite weight, finite sources wash out — same as `consensus_pair` behavior)
- Empty input: raise ValueError (same as existing `consensus()`)

### Integration with `relate.py`

The two-pass fusion in `relate.py:_classify_stance_async` (lines 211-226) currently uses `consensus_pair(categorical_opinion, corpus_opinion)`. When a third opinion source appears (e.g., a calibration reference), replace with `fuse(categorical, corpus, calibration)`. This is a drop-in replacement — `fuse` with 2 inputs should produce identical results to `consensus_pair`.

## Module 2: The Fragility Engine

**File:** `propstore/fragility.py` (new file)

### Core data structures

```python
@dataclass(frozen=True)
class FragilityTarget:
    """One thing you could learn, scored by epistemic leverage."""
    target_id: str           # concept_id, claim_id, or queryable CEL
    target_kind: str         # "concept" | "claim" | "assumption" | "conflict"
    description: str         # human-readable: "Measure sample_size for X"

    # Individual dimension scores (each in [0, 1], higher = more fragile)
    parametric_score: float | None   # from sensitivity analysis
    epistemic_score: float | None    # from ATMS stability/relevance
    conflict_score: float | None     # from conflict topology

    # Combined score
    fragility: float         # combined score in [0, 1]

    # Provenance: what produced each score
    parametric_detail: dict | None
    epistemic_detail: dict | None
    conflict_detail: dict | None


@dataclass(frozen=True)
class FragilityReport:
    """Complete fragility analysis for a bound world."""
    targets: tuple[FragilityTarget, ...]  # sorted by fragility descending
    world_fragility: float                # aggregate: how fragile is the whole world?
    analysis_scope: str                   # what was analyzed
```

### The three dimensions

#### Dimension 1: Parametric sensitivity (existing `sensitivity.py`)

For each derived concept, `analyze_sensitivity` already computes elasticities — how much the output changes per unit change in each input. The fragility score for a parametric input is:

```
parametric_score(input_i) = |elasticity_i| / max(|elasticity_j| for all j)
```

Normalized to [0, 1]. The most elastic input gets score 1.0.

**What's new:** Currently `sensitivity.py` only works on SymPy-derived quantities. Fragility extends this to opinion-valued inputs by asking: "If this concept's opinion changed from vacuous to dogmatic-true (or vice versa), how much would the fused output opinion change?" This is a finite-difference sensitivity on the opinion space:

```
opinion_sensitivity(concept_i) = |E(fused_with_i_dogmatic) - E(fused_with_i_vacuous)|
```

where E is the probability expectation. This uses the new WBF to compute the fused opinion with and without concept_i's contribution. High opinion sensitivity means this concept's evidence has high leverage on the fused belief.

**Literature grounding:** Coupé & van der Gaag 2002 show that BN sensitivity is a rational function of single parameters — the same structural insight applies here. Ballester-Ripoll 2024's Sobol indices would be the ideal generalization (capturing interaction effects), but the OAT (one-at-a-time) approach is sufficient for Phase 1 and avoids the tensor decomposition complexity.

#### Dimension 2: Epistemic stability (existing `atms.py`)

The ATMS engine already computes exactly what we need:

- **`is_stable(node_id, queryables)`** — does the conclusion hold across all bounded futures?
- **`relevant_queryables(node_id, queryables)`** — which assumptions could flip it?
- **`status_flip_witnesses(node_id, queryables)`** — minimal sets that cause a flip

The fragility score for a concept/claim is:

```
epistemic_score(node) = 1.0 if not stable, 0.0 if stable
```

But this is binary. We refine it using the *fraction of futures that flip*:

```
epistemic_score(node) = |flipping_futures| / |consistent_futures|
```

A node that flips in 7/8 futures is more fragile than one that flips in 1/8.

For queryables (things you could learn), the score comes from *how many nodes they flip*:

```
queryable_leverage(q) = |{nodes whose status flips when q is added}| / |all_nodes|
```

This is already computable from `node_relevance` — a queryable that appears in many nodes' relevant sets has high leverage.

**Literature grounding:** Odekerken 2022/2023 defines stability and relevance formally for ASPIC+. The ATMS implementation uses bounded replay rather than ASP enumeration, which is computationally cheaper but only covers the declared queryable space (not all possible completions). This is appropriate — the queryable space represents things we *could actually measure*, not all possible worlds.

#### Dimension 3: Conflict topology

This dimension answers: "Which disagreements, if resolved, would most change the world view?"

**Step 1: Identify active conflicts.** The conflict detector already produces ConflictRecords. The ATMS nogoods also identify assumption-sets that are jointly inconsistent.

**Step 2: Score each conflict by downstream impact.** For each conflict between claims A and B:

1. Compute the current world state (grounded extension, or acceptance probabilities under PrAF)
2. Compute a hypothetical world where A wins (B removed)
3. Compute a hypothetical world where B wins (A removed)
4. The conflict's fragility score is the maximum change:

```
conflict_score(A, B) = max(
    hamming(extension_current, extension_A_wins),
    hamming(extension_current, extension_B_wins)
) / |arguments|
```

For PrAF (probabilistic), use the L1 distance between acceptance probability vectors instead of Hamming distance on extensions.

**Step 3: For gradual semantics (DF-QuAD)**, use AlAnaissy 2024's impact measures directly. The revised impact measure ImpS^rev quantifies how much removing one argument's attacks changes another's strength:

```
conflict_score_gradual(A, B) = |σ(B | remove A→B attacks) - σ(B)|
```

This is cheaper than Shapley values (which require 2^|attackers| evaluations) and satisfies the key axioms (Void Impact, Independence, Balanced Impact).

**Literature grounding:** Cayrol & Lagasquie-Schiex 2014 classify argument additions as conservative/expansive/altering/destructive. A destructive addition is maximally fragile. The conflict score above measures distance to destructive transitions. AlAnaissy 2024's impact measures provide the gradual-semantics counterpart.

### Combining the three dimensions

The three scores are combined into a single fragility score. The combination must respect that:

1. Not all dimensions apply to every target (a non-derived concept has no parametric score)
2. The dimensions are not independent (a parametric input that's also epistemically unstable is doubly fragile)
3. Propstore's non-commitment principle means the combination policy should be configurable at render time

**Default combination: uncertainty-weighted maximum.**

```python
def combine_fragility(
    parametric: float | None,
    epistemic: float | None,
    conflict: float | None,
) -> float:
    scores = [s for s in (parametric, epistemic, conflict) if s is not None]
    if not scores:
        return 0.0
    return max(scores)  # fragility is as high as its weakest dimension
```

**Why max, not mean?** A concept that is parametrically robust but epistemically fragile is still fragile. The max captures this. The mean would hide it.

Alternative combination policies (configurable at render time):
- `"max"`: default — fragility = worst dimension
- `"mean"`: average of available scores
- `"product"`: multiplicative (only fragile if ALL dimensions are fragile — very conservative)
- `"weighted"`: user-supplied weights per dimension

The `FragilityTarget` preserves all three individual scores so downstream consumers can apply their own policy.

### World-level fragility

The aggregate world fragility summarizes how fragile the entire belief state is:

```
world_fragility = mean(top_k fragility scores)
```

where k = min(10, |targets|). This avoids dilution from many low-fragility targets.

### Public API

```python
def rank_fragility(
    bound: BoundWorld,
    *,
    queryables: list[QueryableAssumption] | None = None,
    top_k: int = 20,
    include_parametric: bool = True,
    include_epistemic: bool = True,
    include_conflict: bool = True,
    combination: str = "max",
    semantics: str = "grounded",
) -> FragilityReport:
    """Rank epistemic targets by fragility.

    Parameters
    ----------
    bound : BoundWorld
        The current world view to analyze.
    queryables : list, optional
        Assumptions that could be resolved. If None, auto-discovered
        from inactive claims and unbound conditions.
    top_k : int
        Return only the top-k most fragile targets.
    include_parametric / include_epistemic / include_conflict : bool
        Which dimensions to compute (skip expensive ones if not needed).
    combination : str
        How to combine dimension scores: "max", "mean", "product", "weighted".
    semantics : str
        Which argumentation semantics to use for conflict scoring.
    """
```

### Cost model

Each dimension has different computational cost:

| Dimension | Cost | Bottleneck |
|-----------|------|------------|
| Parametric | O(concepts × inputs) | SymPy differentiation (cached) |
| Epistemic | O(concepts × 2^queryables) | ATMS bounded replay |
| Conflict | O(conflicts × AF_eval) | Extension computation per hypothetical |

The `limit` parameter on ATMS operations (default 8) bounds the epistemic dimension. For conflict topology, we only evaluate the top-k conflicts by opinion uncertainty (high-u conflicts are most likely to be fragile).

## Module 3: CLI Integration

**File:** `propstore/cli/world.py` (additions) or new `propstore/cli/fragility.py`

```
pks world fragility [--concept CONCEPT_ID] [--top-k 20] [--combination max]
                    [--semantics grounded] [--skip-parametric] [--skip-epistemic]
                    [--skip-conflict] [BINDINGS...]
```

Output: a table of FragilityTargets, sorted by score:

```
Rank  Score  Kind        Target                    Why
1     0.92   concept     reynolds_number           Parametric: elasticity 3.7 on viscosity
2     0.85   assumption  temperature == 300K       Epistemic: flips 6/8 futures
3     0.78   conflict    claim:a12 vs claim:b07    Conflict: resolving changes 4 extensions
...
```

The `--concept` flag focuses analysis on a single concept's fragility (which inputs to this concept matter most?). Without it, the analysis covers the entire world.

## Module 4: Worldline Integration

**File:** `propstore/world/bound.py` (additions)

Add a `fragility()` method to `BoundWorld` that delegates to `rank_fragility`:

```python
def fragility(self, **kwargs) -> FragilityReport:
    from propstore.fragility import rank_fragility
    return rank_fragility(self, **kwargs)
```

This makes fragility accessible from the world model API, not just the CLI.

## Test Strategy

### Property tests (Hypothesis)

**WBF properties:**

1. **Commutativity:** `wbf(a, b) == wbf(b, a)` for all valid opinions a, b
2. **N=2 equivalence:** `wbf(a, b) == consensus_pair(a, b)` for non-dogmatic inputs
3. **Idempotency preservation:** `wbf(a, a) == a` for non-dogmatic a (same evidence twice doesn't change belief — van der Heijden Theorem 1 consequence)
4. **Vacuous identity:** `wbf(a, vacuous) == a` (vacuous source contributes nothing)
5. **Uncertainty reduction:** `wbf(a, b).u <= min(a.u, b.u)` (fusion never increases uncertainty — Jøsang 2001 property)
6. **Summation invariant:** fused opinion satisfies b + d + u = 1
7. **Expectation bounds:** `min(E(a), E(b)) <= E(wbf(a,b)) <= max(E(a), E(b))` (fusion expectation is between inputs)

**Hypothesis strategy for opinions:**

```python
@st.composite
def opinions(draw, min_u=0.01):
    """Generate valid non-dogmatic opinions."""
    u = draw(st.floats(min_value=min_u, max_value=1.0))
    remaining = 1.0 - u
    b = draw(st.floats(min_value=0.0, max_value=remaining))
    d = remaining - b
    a = draw(st.floats(min_value=0.01, max_value=0.99))
    return Opinion(b, d, u, a)
```

**CCF properties:**

1. **Handles all-dogmatic:** `ccf(dogmatic_true, dogmatic_false)` returns a valid opinion (doesn't raise)
2. **Agrees with WBF when possible:** for non-dogmatic inputs, `ccf(a, b) ≈ wbf(a, b)` (approximately, since CCF adds compromise averaging)
3. **Summation invariant:** b + d + u = 1

**Fragility properties:**

1. **Score bounds:** all fragility scores in [0, 1]
2. **Monotonicity:** adding a relevant queryable to an unstable node does not decrease epistemic_score
3. **Empty world:** a world with no claims has world_fragility = 0
4. **Single claim, no conflicts:** fragility comes only from parametric dimension (if derived) or is 0
5. **Symmetric conflicts:** if A rebuts B and B rebuts A with equal strength, conflict_score(A,B) > 0

### Integration tests

1. **Toy diamond parameterization:** concept C derived from A and B. Make A high-elasticity, B low-elasticity. Verify A ranks higher in fragility.
2. **Conflicting claims:** two papers disagree on a measurement. Verify the conflict appears in fragility ranking.
3. **ATMS stability:** set up a world where one queryable assumption flips a conclusion. Verify it appears as high-fragility.
4. **Full pipeline:** `pks world fragility` on the actual knowledge base produces valid output.

### Edge cases

- All claims dogmatic (u=0): CCF handles fusion, parametric sensitivity still works, epistemic dimension returns all-stable
- No conflicts: conflict dimension returns empty, other dimensions still work
- No parameterizations: parametric dimension returns empty
- No queryables declared: epistemic dimension auto-discovers from inactive claims
- Cyclic argumentation: DF-QuAD fixpoint handles cycles, fragility uses converged strengths

## Open Questions

### 1. Sobol indices vs OAT sensitivity

Ballester-Ripoll 2024 shows that OAT sensitivity can miss interaction effects. For Phase 1, OAT (what `sensitivity.py` already does) is sufficient. But for Phase 2, should we implement Sobol total indices? The tensor train decomposition (TT rank ≤ √|Φ| + P) makes this tractable, but it's a significant implementation effort. **Recommendation:** defer to Phase 2 unless users report false-negative fragility (a parameter that seems robust but isn't).

### 2. Shapley attribution vs revised impact

AlAnaissy 2024 defines both ImpS^rev (O(n) per argument) and ImpSh (O(2^n) Shapley values). ImpS^rev satisfies fewer axioms but is tractable. ImpSh satisfies all nine axioms but is exponential. **Recommendation:** use ImpS^rev for Phase 1. Offer ImpSh as an opt-in for small frameworks (< 15 arguments).

### 3. Queryable auto-discovery

When `queryables` is not provided, the system needs to discover what could be learned. Options:
- Inactive claims (claims excluded by current conditions)
- Unbound condition variables (conditions that aren't yet set)
- Concepts with no claims (completely unknown quantities)

The ATMS already has `QueryableAssumption` objects. The question is whether fragility should extend this to "concepts we've never measured" — things outside the current knowledge base entirely. **Recommendation:** Phase 1 uses the existing queryable infrastructure. Phase 2 could integrate with the paper collection to suggest "read paper X which might contain a measurement of concept Y."

### 4. Cost modeling

The question asks for the "cheapest" thing to learn. Fragility alone measures leverage (how much would it change beliefs), not cost. Cost is domain-specific: reading a paper is cheap, running an experiment is expensive, replicating a study is very expensive. **Recommendation:** Phase 1 ranks by leverage only. Phase 2 adds optional cost annotations to concepts/claims, and the ranking becomes leverage/cost (epistemic ROI).

### 5. Entrenchment ordering

Gärdenfors 1988 defines epistemic entrenchment as the ordering that determines what to give up during belief revision. Fragility is inverse entrenchment — the least entrenched beliefs are most fragile. The ATMS essential support already provides a partial entrenchment ordering (beliefs supported by fewer assumptions are less entrenched). Should the fragility module formalize this as a full Gärdenfors-compatible ordering? **Recommendation:** not in Phase 1. The essential_support from ATMS is a sufficient proxy. A full AGM-compatible entrenchment ordering requires implementing Dixon 1993's ATMS-to-AGM bridge, which is currently aspirational per CLAUDE.md.

### 6. Multi-frame opinions

Van der Heijden 2018 defines WBF for multinomial opinions (multiple outcomes), not just binary. Propstore currently uses binary opinions (b, d, u, a). Should WBF support multinomial? **Recommendation:** no. The binary opinion algebra is sufficient for the claim-level fusion propstore does. Multinomial would require a new MultinomialOpinion type, which is a separate design effort. The binary WBF formula is a special case of the multinomial one, so upgrading later is backward-compatible.

## Suggested Phasing

### Phase 1: Foundation (WBF + fragility engine skeleton)

1. Implement `wbf()` and `ccf()` in `opinion.py` with property tests
2. Implement `FragilityTarget`, `FragilityReport`, and the `rank_fragility()` function
3. Wire up parametric dimension (delegates to existing `sensitivity.py`)
4. Wire up epistemic dimension (delegates to existing ATMS stability/relevance)
5. Basic CLI: `pks world fragility`
6. Integration test on toy world

**Dependencies:** None — all underlying modules exist.

### Phase 2: Conflict topology dimension

1. Implement conflict scoring via hypothetical world evaluation
2. Integrate AlAnaissy ImpS^rev for gradual semantics
3. Wire into `rank_fragility`
4. Property tests for conflict scoring

**Dependencies:** Phase 1 complete.

### Phase 3: Opinion sensitivity extension

1. Extend `sensitivity.py` (or add to `fragility.py`) to compute opinion-space sensitivity — "what if this concept went from vacuous to dogmatic?"
2. Use WBF to compute fused opinions under hypothetical evidence
3. This connects the parametric and epistemic dimensions: a concept with high opinion sensitivity AND high ATMS instability is doubly fragile

**Dependencies:** Phase 1 (WBF) complete.

### Phase 4: Polish and integration

1. Replace `consensus_pair` fold in `relate.py` with `fuse()` for N > 2 sources
2. Add `fragility()` method to `BoundWorld`
3. Add cost annotations (optional) to ranking
4. Sobol indices (optional, if OAT proves insufficient)
5. Shapley impact (optional, for small frameworks)

**Dependencies:** Phases 1-3 complete.
