# Project Overview Session — 2026-03-24

## GOAL
Q asked: what is this project, does it work, what can it actually do? Not abstractly — real usage.

## OBSERVED

### Infrastructure
- 1,023 tests, collected in 1.4s
- CLI: `pks` with subcommands: validate, build, query, world, claim, concept, context, form, worldline
- Dependencies: Z3 solver, SymPy, LinkML, optional litellm+sqlite-vec for embeddings
- Build pipeline: YAML sources → SQLite sidecar (content-hash addressed)
- `pks world` has 20+ subcommands including: bind, chain, derive, resolve, hypothetical, sensitivity, extensions, atms-*

### Current Data
- 250 concepts, 410 claims, 0 conflicts in the sidecar
- 27 claim files, all from academic papers about argumentation theory itself
- Two claim types in data: `observation` (qualitative statements) and `measurement` (numeric values)
- Measurements: Greenberg 2009 citation distortion stats (94% supportive citation share), Mayer 2020 F1 scores (0.87 argument component detection)
- Most claims have `concept_id = None` in the sidecar (concepts linked via `concepts` list in YAML, not `concept_id`)

### Key Capabilities (from code)
- **BoundWorld**: binds environment conditions, Z3 figures out which claims are active
- **HypotheticalWorld**: overlay removes/adds claims without mutation, re-resolves
- **Resolution strategies**: recency, sample_size, argumentation (Dung AF)
- **Argumentation**: Dung grounded/preferred/stable extensions, Cayrol bipolar support, ASPIC+ inspired preferences
- **Propagation**: SymPy evaluation of parameterization relationships (density = mass/volume style)
- **Sensitivity**: partial derivatives and elasticities for derived quantities
- **ATMS**: assumption-based truth maintenance with labels, contexts, stability analysis
- **Conflict detection**: Z3-based condition overlap checking
- **Worldlines**: materialized, hashed query snapshots

## KEY FINDING
The engine is serious (real formal methods, real test coverage). But the data is self-referential — papers about argumentation loaded into an argumentation system. It hasn't been pointed at a domain where contested knowledge actually matters (pharma, materials science, engineering, policy).

## NEXT
Session complete — Q was asking an orientation question, not requesting work.
