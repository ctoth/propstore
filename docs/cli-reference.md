# CLI Reference

The CLI is installed as `pks`. All commands should be run via `uv run pks`.

## Project management

```
pks init [DIRECTORY]              Create a new knowledge repository
pks validate                      Validate all concepts, claims, and forms
pks build [-o PATH] [--force]     Validate and compile to sidecar SQLite
pks query SQL                     Run raw SQL against the sidecar
```

## Concepts

```
pks concept add                   Add a new concept
pks concept alias ID              Add an alias to a concept
pks concept rename ID --name NEW  Rename a concept (updates all references)
pks concept deprecate ID          Deprecate with replacement pointer
pks concept link SRC TYPE TGT     Add a relationship between concepts
pks concept search QUERY          Full-text search over concepts
pks concept list [--domain D]     List concepts
pks concept show ID               Show full concept YAML
pks concept embed [ID] --all --model M  Generate concept embeddings via litellm
pks concept similar ID [--model M]      Find similar concepts by embedding distance
```

## Claims

```
pks claim validate                Validate all claim files
pks claim validate-file FILE      Validate a single claims YAML file
pks claim conflicts               Detect and report conflicts
pks claim compare A B             Compare two algorithm claims (ast-equiv)
pks claim relate [ID] --all --model M  Classify epistemic relationships via LLM
pks claim embed [ID] --all --model M   Generate claim embeddings via litellm
pks claim similar ID [--model M]       Find similar claims by embedding distance
```

## Forms

```
pks form list                     List available forms
pks form show NAME                Show a form definition
pks form add --name NAME          Add a new form
pks form remove NAME              Remove a form
pks form validate [NAME]          Validate form definitions
```

## Contexts

```
pks context add                   Add a new context
pks context list                  List all registered contexts
```

## Import / Export

```
pks import-papers --papers-root PATH   Import claims from a papers/ corpus
pks export-aliases [--format json]     Export the alias lookup table
```

## World queries

```
pks world status                  Knowledge base stats
pks world query CONCEPT           Show all claims for a concept
pks world bind [KEY=VAL...] [C]   Show active claims under bindings
pks world derive CONCEPT [K=V]    Derive a value via parameterization
pks world resolve CONCEPT --strategy S  Resolve conflicted claims
pks world hypothetical [--remove ID] [--add JSON]  Counterfactual queries
pks world chain CONCEPT [K=V]     Traverse parameter graph to derive a target
pks world explain CLAIM_ID        Show stance chain for a claim
pks world export-graph [K=V]      Export knowledge graph (DOT or JSON)
pks world sensitivity CONCEPT     Sensitivity analysis on derived quantities
pks world check-consistency       Check for conflicts under bindings
pks world extensions [K=V]        Show argumentation extensions (grounded/preferred/stable)
pks world algorithms [--stage S]  List algorithm claims
```

## ATMS commands

```
pks world atms-status [K=V]       ATMS status, support quality, essential support
pks world atms-context [K=V]      Claims holding in current bound environment
pks world atms-verify [K=V]       Label self-checks
pks world atms-futures ID [K=V]   Bounded future environments
pks world atms-why-out ID [K=V]   Explain OUT status (missing vs nogood-pruned)
pks world atms-stability ID [K=V] Bounded stability and witness futures
pks world atms-relevance ID [K=V] Which queryables matter, with witness flips
pks world atms-interventions ID [K=V]  Bounded additive intervention plans
pks world atms-next-query ID [K=V]     Next-query suggestions from minimal plans
```

## Worldlines

Materialized query artifacts — traced paths through the knowledge space with full provenance.

```
pks worldline create NAME [K=V]   Create a worldline definition
pks worldline run NAME            Materialize a worldline (compute results)
pks worldline show NAME           Show a worldline's results
pks worldline list                List all worldlines
pks worldline diff A B            Compare two worldlines side by side
pks worldline refresh NAME        Re-run a worldline with current knowledge
pks worldline delete NAME         Delete a worldline
```

Worldlines support `--reasoning-backend` (claim_graph, structured_projection, aspic, atms, praf), `--semantics`, `--set-comparison`, `--decision-criterion` (pignistic, lower_bound, upper_bound, hurwicz), and PrAF-specific options (`--praf-strategy`, `--praf-epsilon`, `--praf-confidence`).

## Promotions

```
pks promote                       Move proposal artifacts into knowledge/
```

## Resolution strategies

Used with `pks world resolve`:

| Strategy | Behavior |
|----------|----------|
| `recency` | Most recent paper wins |
| `sample_size` | Largest N wins |
| `argumentation` | Run claim-graph backend, project survivors |
| `override` | Specify a claim ID directly |
