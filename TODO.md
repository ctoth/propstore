# propstore TODO

Prioritized based on review-v0.md, narrative review, and data assessment (2026-03-22).

## 1. Contexts as First-Class Theory Objects [NEXT]

Promote contexts from CEL filters to named, composable theory objects with inheritance
and exclusion. Framework-level disagreements (de Kleer vs Doyle on circular support) are
currently misclassified as absolute rebuttals — they're perspectives within different
traditions. Design report: reports/design-atms-environments.md

## 2. Causal Edges

New relationship type on claims: causes, enables, prevents. Parallels the stance system
but for causal rather than epistemic relations. Currently causal claims are flattened into
observation text. Smallest change, broadest applicability.
Resolution status: open; tracked separately from the worldline-journal bridge.
See propstore-narrative-review.md.

## 3. Proposition Layer

Normalize semantic content independent of assertion events. Group claims that assert the
same thing in different words. For numeric domains: content-hash identity. For qualitative:
emerge from stance graph (high-confidence "supports" = same proposition). Design report:
reports/design-proposition-layer.md

## 4. Evidence Aggregation

Replace heuristic resolution (recency, sample_size, stance, override) with principled
evidence aggregation: ASPIC+ structural defeat + composite quality scoring + grounded
extension computation. Design report: reports/design-evidence-aggregation.md

## 5. Subgraph Pattern Queries

Template-based pattern matching over the knowledge graph: find controversy structures,
replication patterns, causal chains, paradigm shifts. Depends on causal edges and
the completed worldline-journal bridge for temporal projection.
Resolution status: open; tracked separately from temporal projection.
See propstore-narrative-review.md.

## 6. Explanation Layer

Unified explanation primitive combining active evidence, excluded evidence, derivation
chain, conflict resolution reasoning, and nearby contradictions. The stance graph (756
edges) already provides raw material. Needs contexts and propositions to be meaningful.

## Resolved: Temporal Projection

The narrative-review `world.at(time)` need is resolved for the current bridge scope by
worldline journals: `pks worldline build-journal` captures a durable
`TransitionJournal`, and `pks worldline at-step NAME STEP` projects the accepted
claim view at a journal step. This replaces claim-level `valid_from` / `valid_until`
as the default temporal-query path for worldline and fiction-curation work.
