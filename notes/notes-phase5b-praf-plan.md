# Phase 5B: Probabilistic Argumentation Frameworks — Implementation Plan

## Summary

This plan designs `propstore/praf.py` and `ReasoningBackend.PRAF` to replace deterministic Dung extension computation with probabilistic argumentation that marginalizes over possible subgraphs. The core data structure is a PrAF = (A, P_A, D, P_D) wrapping the existing `ArgumentationFramework` with independent existence probabilities derived from opinion expectations (Li 2011, Def 2). Two computation strategies are provided: Monte Carlo sampling with Agresti-Coull adaptive stopping (Li 2011, Algorithm 1) for general use, and exact tree-decomposition DP (Popescu 2024) for low-treewidth graphs. A third strategy — DF-QuAD gradual semantics over QBAFs (Freedman 2025) — is included as a complementary fast-path for acyclic support/attack structures. Results are acceptance probabilities per argument rather than binary accept/reject, requiring `ResolvedResult` to carry a probability map alongside the existing winner/reason fields.

## 1. Architecture

### 1.1 Data Structures

```python
# propstore/praf.py (new module)

@dataclass(frozen=True)
class ProbabilisticAF:
    """PrAF = (A, P_A, D, P_D) per Li 2011, Def 2."""
    framework: ArgumentationFramework  # the full (A, D) envelope
    p_args: dict[str, float]           # P_A: argument -> existence probability
    p_defeats: dict[tuple[str, str], float]  # P_D: defeat -> existence probability

@dataclass(frozen=True)
class PrAFResult:
    """Result of probabilistic extension computation."""
    acceptance_probs: dict[str, float]  # argument -> P(accepted)
    strategy_used: str                  # "mc", "exact_dp", "dfquad"
    samples: int | None                 # MC sample count (None for exact/dfquad)
    confidence_interval_half: float | None  # MC error bound
    semantics: str                      # which Dung semantics was used
```

**Design decisions:**

- **P_A**: For active claims, P_A = 1.0 (claims are given as existing in the belief space; the ATMS/condition layer already filters inactive claims). This follows the design proposal (Part 2, Mechanism 1): "P_A(claim) = 1 for all active claims." Only if we later model argument existence uncertainty (e.g., "this claim might be retracted") would P_A < 1 matter. Li 2011, p.2 supports both choices.

- **P_D**: Each defeat's existence probability comes from `Opinion.expectation()` on the stance that generates it. Per Josang 2001, Def 6: E(omega) = b + a*u. This maps directly to P_D per the design proposal (Part 2, Mechanism 1). For stances with no opinion data (legacy), P_D = confidence if available, else P_D = 1.0 (certain defeat — backward compatible with deterministic behavior).

- **Storage**: In-memory only. PrAF is constructed at query time from sidecar data (opinion columns on claim_stance). Not persisted in sidecar. Rationale: PrAF depends on which claims are active (a render-time decision), so it cannot be pre-computed at build time without violating the design checklist ("Is filtering happening at build time or render time? If build -> WRONG.").

- **Wrapping vs extending**: PrAF wraps `ArgumentationFramework` rather than extending it. This preserves the existing deterministic code path untouched — `dung.py` functions operate on the wrapped AF directly when sampling a subgraph.

### 1.2 Module Layout

```
propstore/
  praf.py              # NEW: ProbabilisticAF, MC sampler, exact DP, hybrid dispatch
  praf_treedecomp.py   # NEW: Tree decomposition + nice TD conversion + treewidth estimation
  praf_dfquad.py       # NEW: DF-QuAD gradual semantics for QBAFs (Freedman 2025)
  dung.py              # UNCHANGED: deterministic Dung semantics (reused by MC sampler)
  argumentation.py     # MODIFIED: build_praf() alongside existing build_argumentation_framework()
  world/types.py       # MODIFIED: ReasoningBackend.PRAF, RenderPolicy fields
  world/resolution.py  # MODIFIED: PRAF dispatch path
  opinion.py           # UNCHANGED: Opinion.expectation() provides P_D
```

Rationale for three files instead of one: tree decomposition is algorithmically complex (~300-500 lines) and independently testable. DF-QuAD is a separate semantics with different properties. Keeping them separate follows the existing pattern (dung.py vs dung_z3.py).

### 1.3 Integration with Existing ArgumentationFramework

The `ArgumentationFramework` dataclass stays frozen and unchanged. PrAF construction happens in `argumentation.py`:

```python
def build_praf(
    store: ArtifactStore,
    active_claim_ids: set[str],
    *,
    comparison: str = "elitist",
) -> ProbabilisticAF:
    """Build PrAF by annotating AF edges with opinion-derived probabilities."""
    # 1. Build the full AF envelope (all stances participate, soft epsilon prune only)
    af = build_argumentation_framework(store, active_claim_ids, comparison=comparison)
    # 2. Load opinion data for each stance
    # 3. Map Opinion.expectation() -> P_D for each defeat
    # 4. P_A = 1.0 for all active claims
    ...
```

This reuses the existing AF construction logic (Cayrol derived defeats, preference filtering, support chains) and layers probabilities on top.

## 2. Extension Computation — Three Strategies

### 2.1 Strategy A: Monte Carlo Sampling (Li 2011, Algorithm 1)

**Algorithm:**

```
function mc_acceptance(praf, query_args, semantics, epsilon=0.01, confidence=0.95):
    z = 1.96  # normal quantile for 95% CI
    count = 0
    n = 0
    min_samples = 30  # minimum before checking convergence

    while True:
        n += 1
        # Sample a subgraph
        sampled_args = {a for a in praf.framework.arguments if random() < praf.p_args[a]}
        sampled_defeats = {(f,t) for (f,t) in praf.framework.defeats
                          if f in sampled_args and t in sampled_args
                          and random() < praf.p_defeats[(f,t)]}

        # Build deterministic AF and compute extension
        sub_af = ArgumentationFramework(
            arguments=frozenset(sampled_args),
            defeats=frozenset(sampled_defeats),
            attacks=...  # filter attacks similarly
        )
        ext = grounded_extension(sub_af)  # reuse existing dung.py

        # Check if query is satisfied
        if query_args <= ext:
            count += 1

        # Agresti-Coull stopping (Li 2011, Eq. 5)
        if n >= min_samples:
            p_hat = count / n
            required_n = (4 * p_hat * (1 - p_hat)) / (epsilon ** 2) - 4
            if n > required_n:
                break

    return count / n, n
```

**Key implementation notes:**

- Defeats are only sampled when both endpoints are present (Li 2011, p.5, step 2c — enforces Definition 3).
- The semantic evaluation function xi^S is pluggable — pass `grounded_extension`, `preferred_extensions`, or `stable_extensions` from dung.py (Li 2011, p.4-5: "parametric in semantic evaluation function").
- For preferred/stable (which return lists of extensions), the query check is: "is query_args a subset of any extension in the list?" (credulous acceptance, per Popescu 2024, p.3).
- Agresti-Coull corrects for boundary cases where p_hat is near 0 or 1, where the normal approximation breaks down (Li 2011, p.6-7).
- Seeded RNG for reproducibility in tests.
- **Per-argument acceptance**: Rather than querying for a specific set, compute acceptance probability for each argument individually. Run one sampling loop, compute extension for each sample, accumulate per-argument counts. This gives the full acceptance probability map in a single pass.

**Complexity**: O(N * (|A| + |D|)) per Li 2011, p.9. N depends only on the estimated probability (worst case at p=0.5: ~9604 samples for epsilon=0.01 at 95% confidence), not on AF size. CPU time per iteration is linear in |A| + |D|.

### 2.2 Strategy B: Exact DP on Tree Decomposition (Popescu 2024)

**When to use**: Treewidth <= configurable threshold (default 12). Per Popescu 2024, p.8: DP is competitive with MC on low-treewidth instances, but the 3^k table size factor makes it impractical for high treewidth.

**Algorithm outline:**

1. **Compute primal graph**: Undirected graph where arguments are nodes and each defeat creates an edge between endpoints (Popescu 2024, p.4).
2. **Compute tree decomposition**: Use a heuristic algorithm (min-degree or min-fill) to find a tree decomposition. Estimate treewidth from the result.
3. **Convert to nice tree decomposition**: Four node types — leaf, introduce, forget, join (Popescu 2024, p.5).
4. **DP traversal** (post-order):
   - Each table row: (partial labelling of bag arguments as I/O/U, probability value)
   - Leaf: single row, empty labelling, probability 1
   - Introduce (add argument a): extend each existing row with a labelled as I, O, or U, checking AF constraints, multiplying by P(a) and relevant P_D values
   - Forget (remove argument a): finalize conditions for a, merge rows that agree on remaining arguments
   - Join: multiply probabilities from compatible rows of two children
5. **Root table**: sum probabilities where the query argument is labelled I.

**Witness mechanism** (Popescu 2024, p.6-7): For "out" arguments, need to track whether at least one attacking "in" argument exists with a realized attack edge. This is the key non-obvious detail — without witnesses, the algorithm incorrectly labels arguments as "out" when no actual attacker is "in."

**Complexity**: O(3^k * n) where k is treewidth, n is number of arguments (Popescu 2024, Theorem 7). For k=12: 3^12 = 531,441 table rows per bag. Memory usage ~4MB per bag at 8 bytes per row. Feasible.

**Tree decomposition library**: No Python library provides tree decomposition out of the box with the quality needed. Options:
- Implement min-degree heuristic (simple, ~100 lines, gives upper bound on treewidth)
- Use `networkx` for graph operations, implement TD on top
- The htd library (Abseher 2017, cited by Popescu) is C++ — would need a Python wrapper

**Recommendation**: Implement min-degree heuristic in `praf_treedecomp.py`. It's simple, gives a reasonable treewidth upper bound, and avoids external dependencies. If the estimated treewidth exceeds the threshold, fall back to MC.

### 2.3 Strategy C: DF-QuAD Gradual Semantics (Freedman 2025)

**What it is**: A gradual semantics for Quantitative Bipolar Argumentation Frameworks (QBAFs) that computes continuous strengths in [0,1] rather than binary accept/reject. Propstore already has bipolar structure (attacks + supports from Cayrol 2005).

**The aggregation function** (Freedman 2025, p.3):

```python
def dfquad_strength(base_score, combined_influence):
    """DF-QuAD aggregation. Freedman 2025, p.3."""
    if combined_influence >= 0:
        return base_score + combined_influence * (1 - base_score)
    else:
        return base_score + combined_influence * base_score

def dfquad_combine(supporter_strengths, attacker_strengths):
    """Combine supporter and attacker influence."""
    support = 1 - product(1 - s for s in supporter_strengths) if supporter_strengths else 0
    attack = 1 - product(1 - s for s in attacker_strengths) if attacker_strengths else 0
    return support - attack
```

**Why include it**:
1. It is ~20 lines of math (Freedman 2025, p.3) — low implementation cost.
2. Propstore already has support relations (Cayrol 2005 bipolar AF) which PrAF ignores (PrAF only handles Dung attacks). DF-QuAD uses both.
3. It provides continuous strengths, not binary, aligning with the opinion-based representation.
4. Proven monotonicity properties: increasing supporter base score increases claim strength; increasing attacker base score decreases it (Freedman 2025, Propositions 3-4). This is formally guaranteed contestability.
5. It runs in O(|A| + |D|) — no sampling, no DP, no exponential blowup.

**How it relates to PrAF**: They are **complementary, not competing**:
- PrAF (Li 2011) answers: "What is the probability that argument A is in a Dung extension, given uncertainty about which attacks exist?" — structural uncertainty.
- DF-QuAD (Freedman 2025) answers: "What is the aggregated strength of argument A, given graded base scores and attack/support structure?" — graded evaluation within a fixed structure.
- Hunter 2017's epistemic approach bridges them: probability of belief in A constrained by topology.

**Recommendation**: Implement DF-QuAD as a third strategy option. It is the natural fit when the user cares about graded strength rather than extension membership probability. Use Opinion.expectation() as base scores.

### 2.4 Hybrid Dispatch

```python
def compute_praf_acceptance(
    praf: ProbabilisticAF,
    *,
    semantics: str = "grounded",
    strategy: str = "auto",          # "auto", "mc", "exact", "dfquad"
    mc_epsilon: float = 0.01,
    mc_confidence: float = 0.95,
    treewidth_cutoff: int = 12,
    rng_seed: int | None = None,
) -> PrAFResult:
    if strategy == "dfquad":
        return _compute_dfquad(praf)
    if strategy == "exact":
        return _compute_exact_dp(praf, semantics)
    if strategy == "mc":
        return _compute_mc(praf, semantics, mc_epsilon, mc_confidence, rng_seed)

    # Auto dispatch
    n_args = len(praf.framework.arguments)

    # Fast path: if all P_D are 1.0 (or very close), this is a deterministic AF
    if all(p >= 0.999 for p in praf.p_defeats.values()):
        # Fall back to deterministic Dung — no sampling needed
        return _deterministic_fallback(praf, semantics)

    # Small AF: exact enumeration (Li 2011, p.8: exact beats MC below ~13 args)
    if n_args <= 13:
        return _compute_exact_enumeration(praf, semantics)

    # Medium AF with low treewidth: exact DP
    tw = estimate_treewidth(praf.framework)
    if tw <= treewidth_cutoff:
        return _compute_exact_dp(praf, semantics)

    # Large or high-treewidth: MC
    return _compute_mc(praf, semantics, mc_epsilon, mc_confidence, rng_seed)
```

**The deterministic fallback** is important for backward compatibility: when all opinions have expectation ~1.0 (as with current dogmatic stances), PrAF should return the same results as the existing deterministic backend, with acceptance probabilities of exactly 0.0 or 1.0. This satisfies the testable property from Li 2011, p.2: "For PrAF where all P_A = 1 and all P_D = 1: P_PrAF(X) in {0, 1} and equals standard Dung evaluation."

## 3. ATMS Integration

### 3.1 PrAF Subgraphs as ATMS Environments

Each inducible DAF (sampled subgraph) in the constellations approach is a possible world — this maps directly to an ATMS environment (de Kleer 1986). The ATMS maintains labels (minimal assumption sets) for each datum; each PrAF subgraph corresponds to a specific set of assumptions about which defeats exist.

However, the ATMS integration should be **deferred to a later phase** for these reasons:

1. The current ATMS backend (`ReasoningBackend.ATMS` in resolution.py) operates at a different granularity — it tracks claim support via label propagation, not defeat existence.
2. Gap 3 from the design proposal ("consensus + ATMS interaction") is unresolved. Combining opinion consensus across ATMS contexts may inadvertently collapse contexts, violating non-commitment.
3. The MC sampler already effectively samples ATMS-like contexts (each sample is a possible world). Adding ATMS label tracking on top would be redundant unless we need to persist intermediate contexts.

**Recommendation for Phase 5B**: PrAF samples AF subgraphs directly (not ATMS contexts). The mapping between PrAF possible worlds and ATMS environments is documented but not implemented. Phase 5C can address the ATMS+PrAF integration once Gap 3 is resolved.

### 3.2 What to Document Now

The plan should note the theoretical correspondence (Li 2011, notes.md, Relevance item 1; Popescu 2024, notes.md, Conceptual Links, de Kleer): "Each inducible DAF is a possible world — this is exactly an ATMS environment/context." This creates a clear path for future integration without prematurely coupling the systems.

## 4. Integration Points

### 4.1 ReasoningBackend.PRAF

Add to `propstore/world/types.py`:

```python
class ReasoningBackend(Enum):
    CLAIM_GRAPH = "claim_graph"
    STRUCTURED_PROJECTION = "structured_projection"
    ATMS = "atms"
    PRAF = "praf"  # NEW
```

### 4.2 RenderPolicy Extensions

Add to `RenderPolicy`:

```python
@dataclass(frozen=True)
class RenderPolicy:
    # ... existing fields ...
    # PrAF-specific fields
    praf_strategy: str = "auto"           # "auto", "mc", "exact", "dfquad"
    praf_mc_epsilon: float = 0.01         # MC error tolerance (Li 2011, p.8)
    praf_mc_confidence: float = 0.95      # MC confidence level
    praf_treewidth_cutoff: int = 12       # max treewidth for exact DP (Popescu 2024, p.8)
    praf_mc_seed: int | None = None       # RNG seed for reproducibility (None = random)
    praf_acceptance_threshold: float = 0.5  # acceptance prob above which argument is "in"
```

These are render-time parameters (not build-time), per the design checklist.

### 4.3 Resolution Dispatch

In `resolution.py`, add a new elif branch in `resolve()`:

```python
elif reasoning_backend == ReasoningBackend.PRAF:
    winner_id, reason = _resolve_praf(
        active, view.active_claims(), world,
        semantics=semantics, comparison=comparison, policy=policy,
    )
```

The `_resolve_praf` function:
1. Builds PrAF via `build_praf()` from argumentation.py
2. Computes acceptance probabilities via `compute_praf_acceptance()`
3. Filters target claims by acceptance probability >= threshold
4. Returns winner if exactly one survives, or None with reason

### 4.4 ResolvedResult Changes

`ResolvedResult` needs to carry acceptance probabilities. Add an optional field:

```python
@dataclass
class ResolvedResult:
    # ... existing fields ...
    acceptance_probs: dict[str, float] | None = None  # NEW: per-claim acceptance probability
```

This is backward-compatible (None for non-PRAF backends). The render layer can display these alongside the winner/reason.

### 4.5 Connected Component Decomposition (Hunter 2017, Prop 18)

For large AFs, decompose into connected components and compute PrAF acceptance independently per component. Hunter 2017, p.27 proves separability: the probability of an argument being accepted depends only on its connected component. This is a significant optimization:

- If an AF has 100 arguments but decomposes into 10 components of ~10 each, exact computation is feasible for each component (10 args < 13 threshold).
- Even for MC, smaller components converge faster.

**Implementation**: Before dispatching to MC/exact/DP, compute connected components of the primal graph. Apply the chosen strategy independently per component. Merge results.

## 5. Implementation Phases

### Phase 5B-1: Core PrAF Data Structure + MC Sampler (estimated: 1 session)

**Dependencies**: opinion.py (exists), dung.py (exists), argumentation.py (exists)

**Deliverables**:
- `propstore/praf.py`: ProbabilisticAF, PrAFResult dataclasses
- MC sampler with Agresti-Coull stopping (Li 2011, Algorithm 1)
- `build_praf()` in argumentation.py
- Per-argument acceptance probability computation
- Deterministic fallback for P_D ~= 1.0
- Connected component decomposition
- Unit tests: small hand-computed PrAFs, convergence tests, deterministic equivalence

### Phase 5B-2: ReasoningBackend.PRAF Integration (estimated: 1 session)

**Dependencies**: Phase 5B-1

**Deliverables**:
- `ReasoningBackend.PRAF` in types.py
- `RenderPolicy` PrAF fields
- `_resolve_praf()` in resolution.py
- `ResolvedResult.acceptance_probs` field
- Integration tests: end-to-end from claim_stance data through PrAF to resolution

### Phase 5B-3: DF-QuAD Gradual Semantics (estimated: 1 session)

**Dependencies**: Phase 5B-1 (PrAF data structure), argumentation.py (bipolar AF with supports)

**Deliverables**:
- `propstore/praf_dfquad.py`: DF-QuAD aggregation function, QBAF construction from bipolar AF
- Base score from Opinion.expectation()
- Integration with `praf_strategy="dfquad"` dispatch
- Unit tests: monotonicity properties (Freedman 2025, Props 3-4), known QBAF examples

### Phase 5B-4: Tree Decomposition + Exact DP (estimated: 2 sessions)

**Dependencies**: Phase 5B-1

**Deliverables**:
- `propstore/praf_treedecomp.py`: min-degree treewidth estimation, nice tree decomposition construction
- Exact DP with I/O/U labelling tables (Popescu 2024, Algorithms 1-3)
- Witness mechanism for "out" arguments
- Hybrid dispatch (auto strategy selection)
- Unit tests: small AFs with hand-computed exact probabilities, agreement between MC and exact on same input, treewidth estimation validation

### Phase 5B-5: Polish + Performance (estimated: 1 session)

**Dependencies**: Phases 5B-1 through 5B-4

**Deliverables**:
- Profile typical propstore AF sizes and treewidths
- Tune default parameters (epsilon, treewidth cutoff, min_samples)
- Add `praf_strategy` to WorldlinePolicy and CLI
- Documentation in notes

## 6. Testing Strategy

### 6.1 MC Sampling Tests

- **Seeded RNG**: All MC tests use `rng_seed` parameter for deterministic behavior. The sampler accepts a `random.Random` instance (Li 2011, Algorithm 1 uses random number generation).
- **Convergence test**: Run MC with decreasing epsilon, verify CI half-width decreases as 1/sqrt(N) (Li 2011, p.6). Specifically: at epsilon=0.1, samples should be ~O(100); at epsilon=0.01, ~O(10000).
- **Boundary test**: PrAF with P_D near 0 should converge in few samples; P_D near 0.5 should require most samples (Li 2011, p.7, Fig 2).
- **Deterministic equivalence**: PrAF with all P_A=1, P_D=1 must return 0.0 or 1.0 matching `grounded_extension(af)` (Li 2011, p.2).

### 6.2 Exact DP Tests

- **Small known AFs**: The worked example from Li 2011, p.3 (4 arguments, specific probabilities, P_PrAF({a}) = 0.8) must be exactly reproduced.
- **Agreement with brute-force**: For AFs with <= 8 arguments, enumerate all 2^(|A|+|D|) subgraphs, compute exact probability, verify DP agrees.
- **Agreement with MC**: For the same small AFs, MC with tight epsilon should agree with exact to within epsilon.
- **Semantics consistency**: stable extensions are complete extensions with U=empty, so P_stable^ext <= P_complete^ext (Popescu 2024, p.5).

### 6.3 DF-QuAD Tests

- **Monotonicity** (Freedman 2025, Prop 3): Increasing supporter base score must increase root strength. Increasing attacker base score must decrease root strength.
- **Contestability** (Freedman 2025, Prop 4): Moving argument from support to attack must decrease root strength.
- **Boundedness**: All outputs in [0,1] for all inputs in [0,1].
- **Identity**: Argument with no attackers/supporters has strength = base_score.

### 6.4 Hybrid Dispatch Tests

- AF with 5 arguments: auto selects exact enumeration (< 13 threshold)
- AF with 20 arguments, treewidth 3: auto selects exact DP
- AF with 20 arguments, treewidth 15: auto selects MC
- AF with all P_D=1.0: auto selects deterministic fallback

### 6.5 Property-Based Tests

- Sum of all induced DAF probabilities = 1 (Li 2011, Proposition 1)
- P_acceptance in [0,1] for all arguments
- MC iteration count independent of AF size (depends on estimated probability) (Li 2011, p.9)
- COH constraint: if A attacks B, P(A accepted) + P(B accepted) <= 1 under grounded semantics (Hunter 2017, p.9)

### 6.6 Integration Tests

- End-to-end: claim_stance rows with opinion columns -> build_praf -> compute_praf_acceptance -> resolve -> ResolvedResult with acceptance_probs
- Backward compatibility: existing tests pass unchanged when using CLAIM_GRAPH backend
- Policy test: RenderPolicy(reasoning_backend=ReasoningBackend.PRAF, praf_strategy="mc", praf_mc_seed=42) produces deterministic results

## 7. Computational Concerns

### 7.1 Typical AF Sizes

Based on code survey: propstore AFs are built from `active_claim_ids` which come from the belief space (condition-filtered claims for a concept). Typical knowledge bases have O(10-100) claims per concept, with stances between them. The AF for a single concept resolution is likely small (5-30 arguments). The AF for a full belief space (all active claims) could be larger (50-200+ arguments).

**Recommendation**: Profile actual AF sizes from existing propstore builds. If typical concept-level AFs are < 20 arguments, exact methods may suffice for most queries. If full-belief-space AFs are the norm for resolution, MC is necessary.

### 7.2 MC Sample Count Estimates

Per Li 2011, Eq. 5 with Agresti-Coull correction:
- N > 4 * p * (1-p) / epsilon^2 - 4
- Worst case (p=0.5): N > 1/epsilon^2 - 4
- At epsilon=0.01: N > 9,996 samples
- At epsilon=0.05: N > 396 samples
- At epsilon=0.1: N > 96 samples

Per iteration cost: one `grounded_extension()` call on a subgraph. Current dung.py grounded_extension is O(|A|^2 * |D|) in the worst case (fixpoint iteration). For a 50-argument AF, this is fast (<1ms per iteration). So 10,000 iterations ~ 10 seconds. Acceptable for batch/CLI but may be slow for interactive use.

**Optimization opportunities**:
- Connected component decomposition reduces per-iteration AF size
- Caching: if a subgraph was already computed, skip re-computation (but memory cost)
- Parallel sampling (each iteration is independent)

### 7.3 Treewidth Estimation

Min-degree heuristic: repeatedly remove the vertex with minimum degree, adding edges between its neighbors. The maximum degree encountered gives an upper bound on treewidth. O(|A|^2) time. This is a standard heuristic (Bodlaender 2010) used in practice.

For propstore AFs: if the attack graph is sparse (most claims don't attack each other), treewidth may be low. If there's a concept with many conflicting claims all attacking each other (clique), treewidth will be high. Need to profile.

### 7.4 Memory Usage

- MC sampler: O(|A| + |D|) per iteration, no accumulation beyond counters. Minimal memory.
- Exact DP: O(3^k * n) total table entries, where k is treewidth, n is number of bags. At k=12: 531K entries per bag * 8 bytes * n bags. For n=50 bags: ~200MB. Feasible but significant.
- DF-QuAD: O(|A| + |D|). Minimal.

### 7.5 Connected Component Decomposition

Per Hunter 2017, Prop 18: acceptance probability separates over connected components. This means:
- Compute connected components of the undirected attack graph
- Apply PrAF independently per component
- Merge results (disjoint argument sets, no interaction)

This is critical for scalability. A 200-argument AF that decomposes into 20 components of 10 arguments each is trivially solvable exactly (10 < 13 threshold).

## 8. Open Questions for Q

1. **P_A values**: RESOLVED — Option C. P_A = Opinion.dogmatic_true() for now (claims exist with certainty). Add a `p_arg_from_claim(claim) -> Opinion` hook that defaults to dogmatic_true but can be overridden when extraction confidence arrives. Both p_args and p_defeats are `dict[..., Opinion]` (not float) — same representation, same algebra, same render-time criteria. The MC sampler uses `.expectation()` as the sampling probability, but the full opinion is available for pessimistic/optimistic decision criteria.

2. **Full-belief-space vs concept-level AFs**: RESOLVED — Option C. Always build the full AF (preserving all cross-concept interactions, no filtering before render time per design checklist). Internally, `compute_praf_acceptance()` decomposes into connected components (Hunter 2017, Prop 18 proves separability — results are mathematically identical). Only components containing the target concept's claims are computed. This is an internal optimization, not an API-level decision — the caller passes the full PrAF and gets the full result. If future mechanisms introduce cross-component interactions, only the internal dispatch changes.

3. **DF-QuAD priority**: RESOLVED — Include in Phase 5B-3. Too cheap to defer (~20 lines), too useful to skip. Answers a different question than PrAF ("how strong?" vs "does it survive?") — both are valid render-time policies. Also serves as the fast-path safety net if MC is too slow for interactive use. O(|A|+|D|), no sampling.

4. **Phase 5B-4 priority**: RESOLVED — Option A. Build the whole thing. We have the algorithm at line level from Popescu 2024 notes, we have cross-validation tests (exact must agree with MC and brute-force on small AFs), and the witness mechanism is documented. The tests will catch bugs. Ship all three strategies: MC + DF-QuAD + exact DP.

5. **Acceptance threshold**: RESOLVED — Option B. No threshold. Return the full probability map on `ResolvedResult.acceptance_probs`. The existing decision criteria (pignistic/lower_bound/upper_bound/hurwicz from Phase 4) interpret the probabilities at render time. Remove `praf_acceptance_threshold` from the proposed RenderPolicy fields. Key distinction from the deleted `confidence_threshold`: that gate destroyed data *before* reasoning. PrAF output interpretation happens *after* reasoning — all information was used, now we're presenting results. That's the render layer's job, not ours.

6. **CLI exposure**: RESOLVED — Option A. Full CLI exposure from day one. `--reasoning-backend praf`, `--praf-strategy auto|mc|exact|dfquad`, `--praf-epsilon`, `--praf-mc-seed`, etc. The CLI is the interface — you can't create worldline programs without these flags. Ship them all.

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MC too slow for interactive use | Medium | Medium | Connected component decomposition; coarser epsilon for interactive, tighter for batch; profile first |
| Treewidth estimation inaccurate | Low | Low | Min-degree heuristic is well-studied; inaccuracy just means falling back to MC more often |
| DP implementation bugs in witness mechanism | High | Medium | Extensive cross-validation against brute-force and MC on small AFs |
| P_D values clustered near 1.0 (low uncertainty) | High | Low | Deterministic fallback detects this and skips sampling — zero overhead |
| Existing tests break | Low | High | PRAF is a new backend; existing backends untouched; opt-in via ReasoningBackend.PRAF |
| Opinion columns missing on legacy data | Medium | Low | Fallback: if no opinion columns, use confidence as P_D; if no confidence, P_D = 1.0 |
| Phase 5B-4 (exact DP) takes longer than estimated | Medium | Medium | Ship MC-only first (Phases 5B-1 and 5B-2), add exact DP later |

### Key Risk: Scope Creep

The tree decomposition DP (Popescu 2024) is the highest-risk phase. It involves non-trivial graph algorithms (tree decomposition, nice TD conversion) and a complex DP with witness tracking. Recommendation: implement Phases 5B-1 through 5B-3 first, delivering a working PrAF backend with MC + DF-QuAD. Add exact DP only if profiling shows it's needed.

### What's Safe

- MC sampler is straightforward — the algorithm is published (Li 2011, Algorithm 1), reuses existing dung.py, and has clear convergence guarantees.
- DF-QuAD is ~20 lines of math with proven properties.
- Integration points (ReasoningBackend.PRAF, RenderPolicy fields, resolution dispatch) follow established patterns from the existing three backends.
- All changes are additive — no existing code is modified in ways that could break existing backends.
