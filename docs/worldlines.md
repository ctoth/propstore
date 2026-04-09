# Worldlines

A worldline is a materialized query -- a traced, reproducible path through the knowledge space. It captures both the question (what to resolve, under what conditions, with what policy, and optionally what revision operation to run) and the answer (resolved values, derivation trace, dependencies, and optional revision outcome). You can define a question without running it, run it later, and detect when the answer has gone stale.

The name comes from physics: a worldline is a path through a space parameterized by context. Here, the "space" is the compiled knowledge base and the "context" is the set of bindings, assumptions, overrides, and resolution policy that scope the query.

Grounded in: de Kleer 1986 (ATMS labels as assumption-indexed beliefs), Martins 1983 (belief spaces).

Source: `propstore/worldline/definition.py` (data model), `propstore/worldline/runner.py` (materialization engine), `propstore/cli/worldline_cmds.py` (CLI).

## Concepts

### Question and answer

A worldline separates the *question* from the *answer*. The question is a `WorldlineDefinition`: target concepts to resolve, an environment (bindings, context, assumptions), overrides, a render policy, and an optional revision query block. The answer is a `WorldlineResult`: resolved values, derivation trace, dependency sets, sensitivity analysis, argumentation state, and an optional revision result payload.

You can create a worldline (the question) without running it. The `results` field starts as `None`. Running the worldline materializes the answer.

### Materialization

Running a worldline means resolving each target concept through a 5-step cascade:

1. **Override** -- if the concept has a context-local override value, return immediately. Per Martins 1983, overrides are context-local hypotheses that supersede stored beliefs without competing with them.
2. **Direct claim lookup** -- query the bound world for the concept's value. If determined (single active claim), use it.
3. **Conflict resolution** -- if the concept is conflicted (multiple active claims with incompatible values), apply the resolution strategy from the render policy.
4. **Derivation** -- attempt to derive the value via the parameterization graph (symbolic equations linking concepts).
5. **Chain query** -- multi-step iterative fixpoint derivation across parameterization groups.

If none of these succeed, the target is reported as underspecified with a reason: `no_claims`, `no_values`, `conflicted`, or `underdetermined`.

Before the main resolution pass, a pre-resolution step walks the parameterization graph from targets via `reachable_concepts()` and resolves any conflicted input concepts. This ensures derived values have clean inputs.

### Provenance

Every materialized worldline tracks four kinds of dependencies:

- **Claim dependencies** -- every claim consulted during resolution, accumulated across all resolution steps (flat set, not minimal).
- **Stance dependencies** -- active stances between claims, collected from the argumentation graph or stance database.
- **Context dependencies** -- the context ID and effective assumptions that scoped the query, prefixed with `assumption:`.
- **Derivation trace** -- an ordered list of resolution steps, each recording the concept name, resolved value, source type (`binding`, `override`, `claim`, `resolved`, `derived`, `error`, `underspecified`), and optional metadata (claim ID, formula, strategy, reason).

For derived targets, the engine also traces input provenance recursively (`propstore/worldline/resolution.py:trace_input_source`), building a nested `inputs_used` dict that records where each derived input came from.

### Staleness detection

Each materialized worldline stores a content hash: a SHA-256 digest (truncated to 16 hex chars) computed over the full result payload -- values, steps, dependencies, sensitivity, argumentation state, and revision payload.

To check staleness: re-materialize the worldline with current knowledge, compute a new hash, compare. Different hash = stale. The hash covers everything, so any change to upstream claims, stances, derivation formulas, or argumentation outcomes will produce a different hash.

## Lifecycle

### Create

Define the question: targets, bindings, overrides, reasoning backend, strategy, and optionally a revision query.

```bash
pks worldline create my_query --target fundamental_frequency --bind speaker_sex=male

# Revision-aware worldline
pks worldline create revised_query --target fundamental_frequency \
  --revision-operation revise \
  --revision-atom '{"kind":"claim","id":"synthetic_freq","value":123.0}' \
  --revision-conflict claim:synthetic_freq=freq_claim1
```

This writes a YAML file at `worldlines/my_query.yaml` containing only the question (no results). If a git backend is available, the file is committed automatically.

### Run

Materialize the answer. Requires a built sidecar (`pks build` first).

```bash
pks worldline run my_query
```

If the worldline file exists, it loads the stored definition. Otherwise, you can create and run in one step by passing `--target` and other flags directly.

### Show

Inspect results, derivation trace, sensitivity, argumentation state, revision query/result state, and dependencies.

```bash
pks worldline show my_query
pks worldline show my_query --check  # staleness detection
```

The `--check` flag re-materializes and compares content hashes, reporting whether the stored answer is still current.

## Revision-aware worldlines

Worldlines can now carry an explicit revision query block. This keeps the question and answer separated:

- `WorldlineDefinition.revision` records the requested operation
- `WorldlineResult.revision` records the materialized result

Supported operations:

- `expand`
- `contract`
- `revise`
- `iterated_revise`

The query block mirrors the current revision APIs:

```yaml
revision:
  operation: revise
  atom:
    kind: claim
    id: synthetic_freq
    value: 123.0
  conflicts:
    claim:synthetic_freq:
      - freq_claim1
```

Iterated revision can additionally record the operator family:

```yaml
revision:
  operation: iterated_revise
  atom:
    kind: claim
    id: synthetic_freq
    value: 123.0
  conflicts:
    claim:synthetic_freq:
      - freq_claim1
  operator: lexicographic
```

The result payload keeps one-shot and iterated outputs distinct:

- one-shot operations store `accepted_atom_ids`, `rejected_atom_ids`, `incision_set`, and `explanation`
- iterated revision stores that result plus an explicit serialized epistemic-state summary
- merge-point refusal is captured as an explicit revision error payload rather than being silently omitted

### List

Show all worldlines with status (materialized or pending) and targets.

```bash
pks worldline list
```

### Diff

Compare two materialized worldlines side by side -- input differences (bindings, overrides), per-target value differences with status, and dependency differences (claims only in A, only in B).

```bash
pks worldline diff query_a query_b
```

### Refresh

Re-run with current knowledge. Uses the stored definition as-is (no CLI overrides).

```bash
pks worldline refresh my_query
```

### Delete

Remove the worldline file from disk.

```bash
pks worldline delete my_query
```

## Reasoning backends

Each worldline selects a reasoning backend via `--reasoning-backend`. Backends are only active when the resolution strategy is `argumentation`.

| Backend | Enum value | What it captures |
|---------|-----------|-----------------|
| `claim_graph` | `CLAIM_GRAPH` | Justified/defeated claim sets via Dung AF over claim rows |
| `aspic` | `ASPIC` | Full ASPIC+ engine. |
| `atms` | `ATMS` | ATMS label state from assumption-based truth maintenance |
| `praf` | `PRAF` | Acceptance probabilities per claim via probabilistic AF |

Each backend has additional parameters configurable via the render policy:

- **All backends**: `semantics` (backend-dependent; the worldline CLI accepts `grounded`, `preferred`, `stable`, `d-preferred`, `s-preferred`, `c-preferred`, `bipolar-stable`, `complete`), `comparison` (elitist / democratic)
- **aspic**: `link` (last / weakest -- ASPIC+ link principle per Modgil & Prakken 2018 Defs 19-21)
- **praf**: `praf_strategy` (auto / mc / exact / dfquad_quad / dfquad_baf), `praf_mc_epsilon`, `praf_mc_confidence`, `praf_mc_seed`, `praf_treewidth_cutoff`

The argumentation state captured in the worldline result varies by backend:
- `claim_graph` / `aspic`: `{"justified": [...], "defeated": [...]}`
- `atms`: delegated to `atms_engine().argumentation_state()`
- `praf`: `{"backend": "praf", "acceptance_probs": {...}, "strategy_used": ..., "samples": ..., "confidence_interval_half": ..., "semantics": ...}`

## The materialization engine

The engine (`propstore/worldline/runner.py:run_worldline`) executes in 7 phases:

### Phase 1: Build query environment

Extract environment (bindings, context ID), overrides, policy, and strategy from the worldline definition. Call `world.bind(environment, policy=policy)` to get a `BoundWorld` with Z3 condition solving active.

### Phase 2: Resolve overrides

Override concept names are resolved to concept IDs. Overrides are passed as `override_values` to `derived_value()` -- they are not injected as synthetic claims. Per Martins 1983, overrides are context-local hypotheses that supersede, not compete with, stored beliefs.

### Phase 3: Resolve each target

For each target concept, run the 5-step cascade (override, direct claim, conflict resolution, derivation, chain query). Before this main pass, the pre-resolution step (`propstore/worldline/resolution.py:pre_resolve_conflicts`) walks the parameterization graph to resolve conflicted inputs.

### Phase 4: Sensitivity analysis

For derived targets, compute elasticity and partial derivatives via `analyze_sensitivity()`. Results are stored per-target with input concept names. Failures produce explicit error entries, not silent swallowing.

### Phase 5: Argumentation state

Only runs when `strategy == ARGUMENTATION`. Dispatches to the selected reasoning backend (see table above). Collects stance dependencies from the argumentation graph.

### Phase 6: Revision state

Only runs when the worldline definition has an explicit `revision` block. The runner delegates to the existing `BoundWorld` revision surface:

- `expand(...)`
- `contract(...)`
- `revise(...)`
- `iterated_revise(...)`

One-shot revision stores an operation result payload. Iterated revision stores that result plus explicit epistemic-state summary. Merge-point refusal is surfaced as an explicit revision error payload.

### Phase 7: Content hash

Build the dependency dict (`claims`, `stances`, `contexts`), then compute a deterministic SHA-256 over the JSON-serialized result payload. Truncate to 16 hex chars. This hash is the basis for staleness detection.

## Storage

Worldlines are stored as YAML files at `{repo_root}/worldlines/{name}.yaml`. One file per worldline, committed to git on creation.

The file contains the full `WorldlineDefinition`: question fields (id, name, created, inputs, policy, targets, optional `revision`) plus an optional `results` block that appears after materialization. Read via `WorldlineDefinition.from_file()`, written via `WorldlineDefinition.to_file()`.

## Use cases

**When would you use worldlines vs direct world queries?**

- **Reproducibility** -- a worldline is a saved, diffable query. Run it again next month and see whether the answer changed.
- **Staleness detection** -- "has anything changed since I last asked this question?" Content hash comparison answers this without manual inspection.
- **Comparison** -- "how does this answer change under different reasoning backends, semantics, or bindings?" Create two worldlines with different policies and `pks worldline diff` them.
- **Provenance** -- "what claims contributed to this answer?" The dependency sets and derivation trace give full attribution.
- **Sensitivity** -- "which inputs matter most for this derived value?" Elasticity and partial derivatives are computed and stored per-target.

## References

- de Kleer, J. (1986). An assumption-based TMS. *Artificial Intelligence*, 28(2), 127-162. ATMS labels: every datum indexed by minimal assumption sets.
- Martins, J. P. (1983). Reasoning in multiple belief spaces. Technical Report. Belief spaces as context-local hypothesis management.
