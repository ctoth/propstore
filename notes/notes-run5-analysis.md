# Run 5 Analysis — Post-ATMS Introspection

## GOAL
Determine the best next run after Run 4 (ATMS introspection).

## What Run 4 Delivered (observed from code + tests)
- ATMSEngine with global label/nogood propagation over bound worlds
- Node status: TRUE/IN/OUT via `_status_from_label()` using ATMSNodeStatus enum
- Essential support: Dixon's ES(p,E) = intersection of all foundational belief sets
- Environment queries: `nodes_in_environment()` — what holds in a given environment
- Label verification: `verify_labels()` — consistency, soundness, completeness, minimality
- Explain/introspect: `explain_node()` with full justification traces
- Support quality honesty: EXACT vs SEMANTIC_COMPATIBLE vs CONTEXT_VISIBLE_ONLY
- Nogood provenance: tracks which conflicts produced each nogood
- CLI: atms-status, atms-context, atms-verify commands
- Worldline capture: argumentation_state() with per-node detail
- 12 tests covering propagation, nogoods, order-independence, cycles, essential support, explain, verify, CLI

## What the Papers Say Comes Next

### Dixon 1993 — AGM Bridge
- ATMS context switching = AGM expansion/contraction
- Entrenchment levels E1-E5 encode justificational structure
- ES changes drive entrenchment changes
- Rule revision via entrenchment decrease (ATMS can't do this natively)
- **Gap**: No entrenchment computation exists. No contraction/expansion API.

### Odekerken 2023 — Stability/Relevance
- Four justification statuses (unsatisfiable/defended/out/blocked) under incomplete info
- Stability: will status survive all possible completions?
- Relevance: which queryables would change status?
- Complexity: stability coNP-complete, relevance Σ₂ᵖ-complete
- **Gap**: None of this exists. This is the "future environments" question.

### de Kleer 1986 (Problem Solving)
- Consumer architecture: modular forward-chaining rules over ATMS
- Control disjunctions, kernel environments, scheduling
- **Gap**: No consumer/scheduling layer exists.

### Martins 1983 — Multiple Belief Spaces
- Contexts as sets of hypotheses defining belief spaces
- Restriction sets (= nogoods) distributed per hypothesis
- **Gap**: Current ATMS has one bound world. No multi-agent/multi-perspective reasoning.

### Ginsberg 1985 — Counterfactuals
- Set proposition to unknown, recompute closure
- Sublanguage V controls what may change
- **Gap**: No "retract assumption and recompute" API.

### Alchourron 1985 — AGM Postulates
- Contraction/revision postulates as correctness criteria
- Recovery postulate, Levi/Harper identities
- **Gap**: No way to verify ATMS behavior satisfies AGM postulates.

## Seam Analysis — What the Code Can Support

### Ready now (seams exist, just need wiring)
1. **Counterfactual "what-if"**: The ATMS already computes labels for all environments simultaneously. A "what if assumption X were retracted" query = filter nodes whose label doesn't require X. This is just a projection — no recomputation needed.
2. **Stability over future environments**: Given the engine's `verify_labels()` and `nodes_in_environment()`, you can check whether a node's status is invariant under all consistent supersets of the current environment. For small assumption counts, enumerate.
3. **Entrenchment from essential support**: Dixon's algorithm maps ES changes → entrenchment. ES is already computed. The algorithm is mechanical.

### Needs new infrastructure
1. **Consumer architecture**: Would need a rule engine over the ATMS. Major feature.
2. **Multi-perspective belief spaces**: Would need BoundWorld to support multiple simultaneous contexts. Architectural change.
3. **Full AGM compliance testing**: Would need a formal test harness that generates AGM postulate checks.

## Current Constraints
- labelled.py has all the primitives (EnvironmentKey, Label, NogoodSet, combine/merge/normalize)
- ATMSEngine._build() is batch, not incremental
- No assumption retraction — the engine is built once per BoundWorld
- No way to "subtract" an assumption and see what changes without rebuilding
