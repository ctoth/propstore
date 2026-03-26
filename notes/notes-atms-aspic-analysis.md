# ATMS vs ASPIC+ Architecture Analysis Session

## GOAL
Answer Q's question: Should ASPIC+ be the storage core or a projection over an ATMS-style labelled belief space? Provide four sections: Core Recommendation, Minimal Semantic Contract, Biggest Risks, Migration Shape.

## OBSERVED — Current Architecture

### Storage Layer
- SQLite: claims, stances, contexts, conditions_cel, provenance
- No justification labels, no nogoods, no assumption-set tracking
- Single active environment at a time (Environment dataclass)

### Key Seams
- `BeliefSpace` protocol: active_claims, value_of, derived_value, resolved_value, conflicts, explain
- `RenderPolicy`: reasoning_backend (enum, only CLAIM_GRAPH), strategy, semantics, comparison
- `ReasoningBackend` enum: only CLAIM_GRAPH currently; designed for extension
- `BoundWorld`: single-environment condition binding + Z3 disjointness
- `ActiveClaimResolver`: value resolution from active claims (no AF involvement)

### Argumentation Layer
- Claims are arguments (flat, no internal structure)
- Stances are attacks/supports (from DB)
- `build_argumentation_framework()`: Dung AF + Cayrol bipolar derived defeats + Modgil preference filtering
- Extension computation: grounded/preferred/stable via brute-force or Z3
- MaxSAT alternative: `compute_consistent_beliefs()` via z3.Optimize

### What's Missing for ATMS
1. No justification labels (minimal assumption sets per datum)
2. No nogood storage (inconsistent assumption combinations)
3. No multi-environment exploration (single BoundWorld at a time)
4. No entrenchment ordering (Dixon's 5-level scheme)
5. No incremental label maintenance

### What's Missing for Full ASPIC+
1. No structured arguments (claims are flat, no inference chains)
2. No strict vs defeasible rule distinction
3. No sub-argument structure
4. No undercutting attacks on inference rules (only on claims)

## OBSERVED — Paper Consensus
- de Kleer 1986: Store ALL assumption sets as labels, never commit to one context
- Dixon 1993: ATMS context switching = AGM operations; entrenchment from justification structure
- Ghidini 2001: Contexts are partial objects; bridge rules for cross-context; non-commitment via partial truth
- Modgil 2018: Attack-based conflict-free; preference orderings turn attacks into defeats
- Odekerken 2023: Four justification statuses; stability/relevance as decision problems
- Cayrol 2005: Bipolar support creates derived defeat paths

## KEY INSIGHT
The current code already has the right layering instinct:
- Storage is immutable claims + stances + provenance
- BoundWorld is a single-environment projection
- AF construction happens at render time from active claims
- Resolution strategies are render-time policies

The gap is: BoundWorld can only explore ONE environment at a time. ATMS labels would let you see ALL environments simultaneously. But the current BeliefSpace protocol doesn't need to change for this — you'd add a new reasoning backend that materializes labels, and BoundWorld would remain a single-environment view over that.

## RECOMMENDATION DIRECTION
ASPIC+ should be a projection (reasoning backend), not the storage core. The storage core should remain claim+stance+provenance with the option to compute ATMS-style labels as a materialized view. The BeliefSpace protocol and worldline system are already compatible with this.

## FILES READ
- CLAUDE.md, types.py, resolution.py, bound.py, argumentation.py, value_resolver.py, worldline.py
- papers/index.md + 7 paper notes via subagent
- dung.py, preference.py, model.py, maxsat_resolver.py, z3_conditions.py via subagent
