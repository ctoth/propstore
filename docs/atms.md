# ATMS (Assumption-based Truth Maintenance System)

The ATMS tracks exact support — which assumptions justify each belief. Unlike Dung extensions which pick winners from a set of conflicting arguments, the ATMS maintains all justification paths simultaneously and lets you ask "what would I need to learn to change my mind?"

Where argumentation discards defeated arguments, the ATMS keeps everything and labels it. Every claim carries a label: the set of minimal assumption combinations under which it holds. Nogoods record which assumption combinations are inconsistent. The result is a complete map of the belief space — which claims hold under which assumptions, which assumptions conflict, and what future evidence could change things.

## Core Concepts

### Labels and Environments

A **label** is a set of minimal environments justifying a datum. Each environment is a sorted tuple of assumption IDs plus a sorted tuple of context IDs (an `EnvironmentKey`). A claim with label `{(x), (y)}` means: this claim holds if assumption x is active, or if assumption y is active — two independent justification paths. A context-scoped claim with label `{context_ids=(ctx_lab_run)}` holds under that explicit context support, not unconditionally.

**Minimality** is enforced automatically across both assumptions and contexts: no environment in a label is a superset of another. If a claim is justified by `{a}` and also by `{a, b}`, only `{a}` survives — the smaller environment is strictly more general. If a claim is justified by `ctx_general` and also by `ctx_general + assumption_x`, only the context-only environment survives. This normalization happens on construction and after every propagation step.

`propstore/core/labels.py:Label` — frozen dataclass, auto-normalized on init
`propstore/core/labels.py:EnvironmentKey` — frozen, ordered, auto-sorted/deduped

### Nogoods

A **nogood** is an environment known to be inconsistent — an assumption combination that leads to contradiction. Nogoods are generated when two conflicting claims both have label support, and the union of their supporting environments produces a contradictory set.

Provenance is tracked: each nogood records which claims caused it and which environments produced it. This means you can always ask *why* an assumption combination is forbidden.

During label propagation, nogoods prune labels: any environment that contains (is subsumed by) a nogood is removed. This is how conflicts propagate — a contradiction discovered between two claims can remove support from a third claim that depended on the same assumptions.

`propstore/core/labels.py:NogoodSet` — frozen, auto-normalized; `excludes(env)` returns true if any nogood is a subset of env
`propstore/world/atms.py:ATMSEngine._update_nogoods` — generates nogoods from active conflicts
`propstore/world/atms.py:ATMSEngine.explain_nogood` — returns provenance for a given nogood

### Support Quality

The ATMS distinguishes four levels of support quality, reflecting how precisely a claim's conditions match the current assumption and context environment:

| Quality | Meaning |
|---------|---------|
| `EXACT` | Conditions match current assumption CELs directly |
| `SEMANTIC_COMPATIBLE` | Active via Z3 condition solving but not an exact CEL match |
| `CONTEXT_VISIBLE_ONLY` | Active through context lifting but without exact ATMS support in the current environment |
| `MIXED` | Combination of semantic and context activation |

The ATMS engine only grants exact support. Context-scoped claims can have exact ATMS support when their context node is part of the label environment. A claim that is only semantically compatible or only context-visible through a non-exact lifting path remains active in `BoundWorld` but OUT in the ATMS. This is deliberate: the ATMS tracks precise justification structure, not approximate compatibility.

`propstore/world/labelled.py:SupportQuality` — enum
`propstore/world/atms.py:ATMSEngine._support_quality_for_node` — classifies support

### Node Status

Every ATMS node has one of three statuses:

| Status | Meaning | Label state |
|--------|---------|-------------|
| `TRUE` | Unconditionally supported | Label contains the empty environment `EnvironmentKey(())` |
| `IN` | Conditionally supported | Label has non-empty environments |
| `OUT` | Not supported | Empty label |

OUT nodes are further distinguished by *why* they are out:

- **`MISSING_SUPPORT`** — the claim never had exact support in the current environment
- **`NOGOOD_PRUNED`** — the claim had exact support, but it was removed by nogood pruning (a conflict eliminated all its supporting environments)

This distinction matters for intervention planning: a nogood-pruned claim might become supported if a conflicting claim is removed, while a missing-support claim needs new assumptions to become active.

`propstore/world/types.py:ATMSNodeStatus` — enum (TRUE, IN, OUT)
`propstore/world/types.py:ATMSOutKind` — enum (MISSING_SUPPORT, NOGOOD_PRUNED)

## Label Propagation

The ATMS builds its graph and propagates labels to fixpoint. The algorithm:

**1. Build assumption and context nodes.** Each environment assumption gets an ATMS node with a singleton assumption label, and each visible context gets a context node with a singleton context label. These nodes support themselves.

`propstore/world/atms.py:ATMSEngine._build_assumption_nodes`
`propstore/world/atms.py:ATMSEngine._build_context_nodes`

**2. Build claim nodes and justifications.** Each active claim gets a node. For claims with `conditions_cel`, the engine finds matching assumption nodes and creates justifications linking assumption nodes to claim nodes. For context-qualified claims, the engine also links the context node as an antecedent.

`propstore/world/atms.py:ATMSEngine._build_claim_nodes_and_justifications`

**3. Propagate labels to fixpoint.** For each justification, combine antecedent labels via cross-product (if a claim depends on assumptions x and y, its label gets `{(x, y)}`). Merge results into the consequent's label. Both operations prune via nogoods. Repeat until no labels change.

`propstore/world/atms.py:ATMSEngine._propagate_labels`
`propstore/world/labelled.py:combine_labels` — cross-product union, nogood-pruned
`propstore/world/labelled.py:merge_labels` — alternative supports merged, normalized

**4. Materialize micropublication and parameterization justifications.** Canonical micropublication bundles become ATMS nodes supported by their context node and member claim nodes. For each compatible parameterization, find all supported provider nodes, evaluate the SymPy formula, create derived nodes and justifications. These are claims whose values are computed from other claims.

`propstore/world/atms.py:ATMSEngine._build_micropublication_nodes_and_justifications`
`propstore/world/atms.py:ATMSEngine._materialize_parameterization_justifications`

**5. Update nogoods from conflicts.** For each active conflict between two claims, take the cross-product of their label environments and add each union as a nogood. Record provenance.

`propstore/world/atms.py:ATMSEngine._update_nogoods`

**6. Repeat until stable.** The main loop iterates steps 3-5 until neither new justifications nor new nogoods are added.

`propstore/world/atms.py:ATMSEngine._build`

## Bounded Replay

Bounded replay is hypothetical future exploration: "if I learned these additional facts, what would change?"

The mechanism is additive only — it adds queryable assumptions to the current environment and rebuilds the ATMS from scratch. It never removes existing assumptions. This is explicitly not AGM revision (which can retract beliefs); it is monotonic extension of the assumption base. The separate `propstore.revision` layer now provides contraction, entrenchment, and revision over derived belief state.

Each future is a full rebuild. The engine enumerates subsets of declared queryable assumptions in increasing width (size 1, then size 2, etc.) up to a configurable limit. For each subset, it constructs a new `ATMSEngine` over an extended environment and records the resulting statuses.

Queryables already present in the current environment are automatically filtered out — you cannot "add" what you already have.

`propstore/world/atms.py:ATMSEngine._future_engine` — builds a new engine per future
`propstore/world/atms.py:ATMSEngine._iter_future_queryable_sets` — enumerates subsets in increasing width
`propstore/world/atms.py:ATMSEngine._extend_environment` — extends environment with queryable assumptions

## Analysis Capabilities

### Stability

Is a claim's status stable across all bounded consistent futures? Stability analysis replays all future environments and checks if any consistent future produces a different ATMS status than the current one.

A stable claim will keep its current status no matter what you learn (within the declared queryable space). An unstable claim has at least one future that flips it — and the engine reports the minimal witnesses.

`propstore/world/atms.py:ATMSEngine.node_stability` — claim-level stability
`propstore/world/atms.py:ATMSEngine.concept_stability` — concept-level (uses BoundWorld value status)

### Relevance

Which queryable assumptions can flip a claim's status? Relevance analysis finds pairs of futures — one with a queryable, one without — where the status differs. A queryable is relevant if adding or removing it from some future changes the outcome.

Returns relevant queryables, irrelevant queryables, and witness pairs showing the flip.

`propstore/world/atms.py:ATMSEngine.node_relevance` — claim-level relevance
`propstore/world/atms.py:ATMSEngine.concept_relevance` — concept-level relevance

### Intervention Planning

What minimal set of queryable assumptions would achieve a target status (IN or OUT)? Intervention planning filters future entries to those that are consistent and reach the target, then removes non-minimal plans (any plan whose queryable set is a superset of another is dropped).

For OUT interventions, the target future must show `NOGOOD_PRUNED` (not just `MISSING_SUPPORT`) — the claim must be actively defeated by a conflict, not merely lacking support.

`propstore/world/atms.py:ATMSEngine.node_interventions` — claim-level interventions
`propstore/world/atms.py:ATMSEngine.concept_interventions` — concept-level interventions

### Next-Query Suggestions

Given intervention plans, which single queryable should you investigate first? The engine groups all plans by individual queryable, then ranks by:

1. Smallest plan size (ascending) — queryables that appear in smaller plans are more impactful
2. Plan count (descending) — queryables that appear in more plans are more versatile
3. CEL alphabetically — tiebreaker

This answers: "What should I learn next to have the greatest impact on this claim's status?"

`propstore/world/atms.py:ATMSEngine.next_queryables_for_node` — claim-level suggestions
`propstore/world/atms.py:ATMSEngine._next_queryables_from_plans` — ranking logic

### Essential Support

The shared assumptions across all compatible label environments. If a claim has environments `{(x, y), (x, z)}`, the essential support is `{x}` — the assumption that appears in every justification path.

Essential support identifies the assumptions a claim cannot do without, regardless of which specific justification path is active.

`propstore/world/atms.py:ATMSEngine.essential_support`

### Micropublication Support

A canonical micropublication is represented as an ATMS node whose antecedents are the bundle's context node and every member claim node. Its label is therefore the cross-product of the exact environments supporting the whole bundle. If one member claim is unsupported, the micropublication node is OUT.

`propstore/world/atms.py:ATMSEngine.supported_micropub_ids` — supported bundle IDs
`propstore/world/atms.py:ATMSEngine.micropub_label` — exact bundle label

## CLI Usage

All ATMS commands are under `pks world atms-*`. They accept bindings as positional arguments (e.g., `domain=argumentation`) and `--context TEXT` for context scoping.

### Status and inspection

```bash
# Show ATMS-native claim status, support quality, and essential support
pks world atms-status domain=argumentation

# Show only claims with exact ATMS support in the current bound environment
pks world atms-context domain=argumentation

# Run ATMS label self-checks (consistency, minimality, soundness, completeness)
pks world atms-verify domain=argumentation
```

### Future analysis

```bash
# Show bounded future environments for a claim
# Requires --queryable to declare what future assumptions to explore
pks world atms-futures claim_id domain=argumentation --queryable framework=general

# Explain whether an OUT status is missing support or nogood-pruned
pks world atms-why-out claim_id domain=argumentation --queryable framework=general
```

### Stability and relevance

```bash
# Is this claim's status stable across all bounded consistent futures?
pks world atms-stability claim_id domain=argumentation --queryable framework=general

# Which queryables can flip this claim's status? With witness pairs.
pks world atms-relevance claim_id domain=argumentation --queryable framework=general
```

### Intervention planning

```bash
# Minimal additive queryable sets that reach target status
pks world atms-interventions claim_id domain=argumentation \
    --target-status IN --queryable framework=general

# Next-query suggestions ranked by impact
pks world atms-next-query claim_id domain=argumentation \
    --target-status IN --queryable framework=general
```

All future-analysis commands accept `--limit N` (default 8) to cap the number of queryable subsets explored.

## Design Boundaries

The ATMS backend is a label-propagation engine with bounded replay. It is explicitly *not*:

- **Not a full de Kleer runtime manager.** de Kleer's (1986) ATMS is a runtime system managing contexts, focus, and incremental update. propstore's ATMS is a batch analysis pass over the active belief space — it builds, propagates, and reports.

- **Not AGM revision.** The ATMS is additive only. Bounded replay adds assumptions; it never retracts them. AGM revision (Alchourron et al. 1985) and the ATMS-AGM correspondence (Dixon 1993) are implemented in the separate revision layer, not inside the ATMS itself.

- **Not full ASPIC+ dynamics.** The ATMS and ASPIC+ backends are separate reasoning backends. The ATMS tracks assumption-level support; ASPIC+ tracks argument-level inference structure. They are not currently integrated.

- **Not Odekerken 2023's ASP-based stability.** Odekerken's stability and relevance analysis uses Answer Set Programming. propstore implements the same concepts (stability, relevance, intervention) via bounded replay — enumerating futures and comparing statuses — rather than ASP-based constraint solving.

## References

- **de Kleer, J. (1986).** "An Assumption-based TMS." — Foundation for the label/nogood/environment model. The ATMS engine implements label propagation, nogood pruning, and environment queries from this paper.

- **Odekerken, D. et al. (2023).** "Argumentation and Reasoning with ASPIC+ under Incomplete Information." — Architectural reference for stability and relevance concepts. propstore implements these via bounded replay rather than the ASP-based approach described in the paper.

- **Martins, J. P. (1983).** "Belief Revision." — Referenced for the concept of belief spaces in the worldline layer.
