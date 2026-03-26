# ATMS Overclaim Audit — 2026-03-24

## GOAL
Attack the proposed Run 4 from the standpoint of overclaiming and premature abstraction.

## Proposed Run 4 scope
"ATMS future environments, stability, relevance, and minimal support-changing interventions over queryable assumptions, while AGM revision and richer structured argumentation wait."

## What Actually Exists (observed)

### ATMSEngine (atms.py, ~794 lines)
- Batch-builds all nodes and justifications at construction time (eager, not incremental)
- Propagates labels via fixed-point loop (not incremental de Kleer update)
- Nogoods derived from BoundWorld.conflicts() — cross-product of conflicting claim labels
- Node statuses: TRUE (empty env in label), IN (nonempty label), OUT (empty label). No FALSE.
- Essential support: intersection of compatible environments' assumption sets
- Environment queries: nodes_in_environment returns nodes whose label subsumes a given env
- Explain: justification trace walk with cycle detection
- verify_labels: checks consistency, minimality, soundness, completeness against expected

### Labelled kernel (labelled.py, ~213 lines)
- EnvironmentKey: frozen sorted tuple of assumption_ids, with subsumes/union
- Label: minimal antichain of EnvironmentKeys (normalize_environments prunes supersets + nogoods)
- NogoodSet: tuple of EnvironmentKeys, excludes via subsumes check
- combine_labels: cross-product union
- merge_labels: merge alternative supports
- No incremental update protocol. No retraction. No context switching.

### BoundWorld (bound.py)
- Constructed with fixed Environment (bindings + context + assumptions)
- Lazy ATMSEngine accessor (constructs once, caches)
- ATMS backend gates in value_of/derived_value/resolved_value
- claim_status, claim_essential_support, claims_in_environment, explain_claim_support — all delegate to engine
- NO method to modify environment after construction
- NO method to add/retract assumptions
- NO method to switch contexts

### HypotheticalWorld (hypothetical.py) — EXISTS but not read yet
- Imported in __init__.py

### Tests (test_atms_engine.py, ~787 lines)
- 12 test functions, all use _ATMSStore (mock store) and _make_bound
- Tests cover: label propagation, nogoods, order independence, cycles, semantic vs exact, context, node status, essential support, environment queries, explain, verify, worldline integration, CLI
- NO test for retraction, context switching, stability, relevance, or interventions
- NO test for incremental update

## Key Observations for Overclaim Analysis

1. **"Future environments"** — The system has no concept of "future" environments. BoundWorld is immutable after construction. There is no API to hypothesize "what if assumption A were added/removed?" The engine rebuilds from scratch each time. "Future environments" would require either (a) incremental ATMS or (b) constructing new BoundWorlds and diffing, which is just re-running from scratch.

2. **"Stability"** — Odekerken's stability asks "will this node's status change if more info arrives?" This requires reasoning about *incomplete* justification networks. The current engine has no notion of incomplete information — it builds the full graph from all active claims. Stability would require tracking which nodes could potentially gain new justifications.

3. **"Relevance"** — Odekerken's relevance asks "which unresolved queries matter for this node?" Similar problem: requires modeling missing information. The engine doesn't distinguish "no justification exists" from "justification exists but antecedents are unsupported."

4. **"Minimal support-changing interventions"** — This would mean: "what is the smallest set of assumptions to add/remove to change node X's status?" This is a search problem over the environment space. The current engine provides essential_support (intersection of compatible envs) but that's a read operation, not an intervention planner. Computing minimal interventions requires either (a) enumerate candidate environments and re-propagate, or (b) symbolic analysis of the justification graph. Neither exists.

5. **"Queryable assumptions"** — Assumptions ARE queryable (assumption nodes, labels, essential_support). But "queryable" in the ATMS sense means you can ask "in which environments does X hold?" — which nodes_in_environment already does. The word "queryable" here doesn't add new functionality, it describes what already exists.

## NEXT
Write the three sections. Don't read more files.
