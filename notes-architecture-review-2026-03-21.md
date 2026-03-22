# Architecture Review Session — 2026-03-21

## Goal
Q asked: consider the actual architecture, the papers/concepts, then what's the next obvious step / next superpower to unlock.

## What I Observed

### Engine (working)
- Full compiler pipeline: validate → build SQLite sidecar → WorldModel reasoner
- 6 claim types: parameter, equation, observation, model, measurement, algorithm
- Conflict detection via Z3, AST equivalence for algorithms, CEL conditions
- WorldModel: value_of, derived_value, resolve, bind, hypothetical, chain_query
- Embeddings (litellm + sqlite-vec), FTS5, graph export
- Domain-independent (speech hardcoding removed in modularize-world-model branch)
- 530+ tests passing
- World subpackage: types.py, resolution.py, model.py, bound.py, hypothetical.py

### Research Library (deep)
- 25 papers across: TMS lineage (Doyle→McAllester→de Kleer ATMS), AGM belief revision (Alchourron→Dixon bridge), argumentation (Dung→Pollock→ASPIC+→Cayrol bipolar), scientific communication (Clark micropubs, Groth nanopubs, Greenberg citation distortion), argument mining (Mayer 2020), incomplete info (Odekerken 2023)
- papers/index.md has rich summaries of all 25

### Knowledge Base (nearly empty)
- 23 concepts in knowledge/concepts/ — all argumentation domain, all `status: proposed`, all skeleton (no aliases, no relationships, no parameterizations)
- Zero claims in knowledge/claims/
- Zero sidecar built
- No claims/ directory at all

### Papers Claims (populated but not imported)
- 25 papers have claims.yaml files in their paper directories
- Real LLM-extracted claims (checked Dung and de Kleer — observations, models with equations, proper provenance)
- These have NEVER been imported into knowledge/claims/

### The Gap
The engine is built, the fuel (claims) exists in papers/, but the fuel line (import-papers) hasn't been run. The knowledge store is dead because claims haven't been imported.

## What I Tried
- Read all major code modules via explorer agent
- Read papers/index.md for paper summaries
- Read 4 notes files (2026-03-20, 2026-03-21, propstore-integration-session, domain-independence, composition-analysis-3, modularize-world-model, algorithm-claims)
- Checked knowledge/concepts/, knowledge/claims/, knowledge/sidecar/ state
- Read sample claims.yaml from Dung and de Kleer papers
- Read a sample concept file (argumentation_framework.yaml)

## What Worked
- Full architecture picture assembled
- Clear identification of the gap between engine and data

## What Didn't Work
- Research explorer agent restated instead of acting on first try (had to SendMessage)

## Recommendation to Q
**Next obvious step:** Run `pks import-papers` on this repo's own papers, then `pks build`, then `pks world status`. This connects the fuel line — claims from 25 papers flow into the knowledge store, sidecar gets built, conflicts detected, world model becomes queryable.

**Next superpower:** Cross-paper reasoning over the argumentation theory collection itself. The system built to reason about reasoning can reason about its own theoretical foundations — finding where Pollock contradicts Dung, where Cayrol extends Dung, where Modgil 2018 revises 2014, all automatically via conflict detection + stance graph.

## Next Step
Waiting for Q's go-ahead to run import-papers and light up the knowledge base.
