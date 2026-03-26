# Heartwood Codebase Review — 2026-03-25

## Goal
Q asked what ~/src/heartwood is doing that propstore could learn from.

## What I Observed

Heartwood is a personal knowledge graph with a reasoning engine (~4500 LOC Python). Core modules: reason.py (7-pass pipeline), memory.py (compounding across runs), beliefs.py (claim extraction), revision.py (AGM-style contradiction detection), graph_analysis.py (NetworkX centrality/communities), link_prediction.py (multi-signal scoring), storage_fs.py (filesystem backend), mcp_server.py (7 MCP tools).

### Patterns worth stealing for propstore

1. **Graph-aware similarity thresholds** — BFS hop distance adjusts cosine threshold. Close nodes need higher similarity; distant nodes get lower bar. Propstore uses flat thresholds.

2. **PPR subgraph extraction for LLM context** — Personalized PageRank seeded on candidate pair, extract top-k relevant nodes, send focused context to LLM. Better than raw text dumps.

3. **Entrenchment ordering** — Multi-factor score (source type, corroboration, recency decay, graph degree) for retraction priority. Propstore has opinion strength via SL but no formal entrenchment.

4. **Pydantic max-length fields on accumulated state** — Caps on themes, rules, strategies prevent unbounded context growth. Sidecar could use budget discipline.

5. **Hedge preservation in extraction** — "I'm thinking about X" stays confidence 0.4, not promoted to fact. Calibrated stance mapping for claim extraction.

6. **Three-layer contradiction detection** — Structural (entity+negation) → Embedding (similarity+polarity) → LLM confirmation. Cheapest layer first. Cost-stratified.

7. **Episodic memory across runs** — 4 channels (living summary, reflections, rules, strategies). Each run's output feeds next run's context. Propstore builds are stateless — memory artifacts as proposals would fit the architecture.

### Where propstore is ahead

- Formal argumentation (Dung AF, ASPIC+, bipolar, extensions)
- Subjective Logic opinion algebra vs scalar confidence
- Non-commitment discipline (holds rivals without collapsing)
- ATMS assumption-based truth maintenance

## Status
Review complete. Findings delivered to Q in conversation.

## Next Steps
Up to Q — potential follow-ups:
- Prototype episodic memory for pks build (as proposal artifacts)
- Adapt graph-aware thresholds for embedding similarity
- Add entrenchment scoring to claim/opinion layer
- Cost-stratified contradiction detection pipeline
