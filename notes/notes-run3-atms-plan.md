# Run 3 ATMS Planning — Session Notes

## GOAL
Plan Run 3: first real ATMS engine pass. Preserve claim_graph as default, structured_projection as public opt-in.

## FILES READ

### Code
- `labelled.py` — Current ATMS kernel: AssumptionRef, EnvironmentKey, NogoodSet, Label, JustificationRecord, SupportQuality. Has combine_labels (cross-product), merge_labels (alternative supports), normalize_environments (deduplicate, prune supersets, drop nogoods). This is the data-structure layer only — no engine loop, no propagation, no justification network.
- `bound.py` — BoundWorld: condition-bound view. `is_active()` filters by context + CEL conditions. `_claim_support_label()` reconstructs labels from compiled assumptions. `_attach_value_label`, `_attach_derived_label`, `_attach_resolved_label` — all post-hoc label attachment onto results. Key gap: labels are reconstructed per-query, not maintained incrementally.
- `model.py` — WorldModel: read-only over compiled sidecar (SQLite). `bind()` creates BoundWorld. `chain_query()` iterative resolution. No ATMS state at all — pure query.
- `types.py` — ValueResult, DerivedResult, ResolvedResult all have optional `label: Label | None`. Environment dataclass. RenderPolicy has reasoning_backend field (CLAIM_GRAPH or STRUCTURED_PROJECTION). BeliefSpace protocol.
- `resolution.py` — `resolve()` dispatches to recency, sample_size, override, or argumentation (claim_graph or structured_projection backend).
- `structured_argument.py` — Run 2B: StructuredArgument, StructuredProjection. Projects claims to base arguments, builds AF from stances. Has Cayrol derived defeats (_cayrol_derived_defeats). Uses dung.py for extension computation.
- `worldline_runner.py` — Materialize worldline: bind, resolve targets, sensitivity, argumentation state. Complex but no ATMS engine — just queries.

### Papers
- **de Kleer 1986**: ATMS core. Nodes, assumptions, justifications, environments, labels, nogoods, contexts. Four label properties: consistency, soundness, completeness, minimality. Label update = cross-product of antecedent labels, remove nogoods, remove subsumed. Three primitives: create node, create assumption, add justification. Order-independent.
- **Dixon 1993**: ATMS ≡ AGM under entrenchment encoding. Five levels E1-E5. Essential support = intersection of all foundational belief sets. Context switching = expansion/contraction sequences.
- **Ghidini 2001**: Local Models Semantics. Contexts as partial objects (sets of models). Bridge rules for cross-context reasoning. Compatibility relations.
- **Modgil 2018**: Full ASPIC+. Three attack types (undermine, rebut, undercut). Defeat via preferences. Attack-based conflict-free. Four rationality postulates. Last-link/weakest-link/elitist/democratic.
- **Cayrol 2005**: Bipolar AF. Supported defeat, indirect defeat. Safe sets. d/s/c-admissible.
- **Odekerken 2023**: ASPIC+ with incomplete info. Four justification statuses (unsatisfiable, defended, out, blocked). Stability (coNP-complete), relevance (Sigma_2^P-complete).

## KEY OBSERVATIONS

### What exists (Run 2A + 2B)
1. Label kernel data structures exist and are correct (labelled.py)
2. Labels are computed per-query by reconstructing from compiled assumptions — NOT maintained by an engine
3. No justification network — no node-to-node propagation
4. No incremental label update — every query reconstructs from scratch
5. NogoodSet exists but is never populated from actual conflicts
6. JustificationRecord exists but is never used outside unit tests
7. structured_projection builds an AF from stances + claims, computes Dung extensions — but this is claim-level, not ATMS-level

### What's missing for real ATMS
1. **Justification network**: de Kleer's core — justifications connect antecedent nodes to consequent nodes. Currently claims don't form a justification network.
2. **Label propagation**: When a justification is added, cross-product labels and propagate to consequents. Currently done ad-hoc in `_attach_derived_label`.
3. **Nogood population**: Conflicts should become nogoods. Currently conflict_detector runs separately and nogoods are never fed into the label kernel.
4. **Node registry**: ATMS needs a registry of nodes (claims/datums) with their labels. Currently labels are computed on-the-fly per BoundWorld query.
5. **Incremental updates**: ATMS is order-independent but incremental — add justification triggers label update. Current system is batch (rebuild sidecar).

### What should remain out of scope for Run 3
- Full incremental ATMS (would require rewriting the sidecar pipeline)
- AGM entrenchment (Dixon layer — needs ATMS first)
- Full ASPIC+ (structured rules, not just claims)
- Stability/relevance (Odekerken — needs ATMS justification statuses first)
- Cyclic justification handling (circular support detection)

## NEXT
Write the four-section plan.
