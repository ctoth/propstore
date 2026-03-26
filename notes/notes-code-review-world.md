# Code Review: World Model, Rendering, and Query Subsystem

**Date:** 2026-03-23
**Scope:** `propstore/world/`, `propstore/cli/`, and supporting modules (`relate.py`, `embed.py`, `graph_export.py`, `parameterization_groups.py`, `param_conflicts.py`, `unit_dimensions.py`, `equation_comparison.py`, `sympy_generator.py`)

---

## 1. How the World Model Works

### Architecture Overview

The world model is a **read-only reasoner** over a pre-compiled SQLite sidecar database. The pipeline is:

1. YAML source files (concepts, claims, contexts, stances) live in `knowledge/`
2. `pks build` validates everything, then compiles into `knowledge/sidecar/propstore.sqlite`
3. `WorldModel` reads from that sidecar at query time -- it never writes to source files

The key abstraction layers are:

- **`ArtifactStore` (Protocol)** -- raw data access (get_concept, claims_for, stances_between, etc.). `WorldModel` implements this. Defined at `types.py:91-128`.
- **`BeliefSpace` (Protocol)** -- filtered view with value resolution (active_claims, value_of, derived_value, resolved_value). `BoundWorld` and `HypotheticalWorld` implement this. Defined at `types.py:131-145`.
- **`WorldModel`** -- the `ArtifactStore` implementation. Opens the SQLite sidecar, provides raw queries, and serves as the factory for `BoundWorld` via `bind()`. Defined at `model.py:37`.

### Querying Flow

1. User calls `WorldModel.bind(**conditions)` to get a `BoundWorld` (`model.py:402-438`)
2. `BoundWorld` filters claims via Z3 condition compatibility (`bound.py:157-178`)
3. `BoundWorld.value_of(concept_id)` returns a `ValueResult` with status: `determined`, `conflicted`, `no_claims`, or `underdetermined` (`bound.py:254-256`)
4. If conflicted, `BoundWorld.resolved_value(concept_id)` applies a resolution strategy (`bound.py:270-273`)
5. `BoundWorld.derived_value(concept_id)` computes values via parameterization relationships (algebraic formulas linking concepts) (`bound.py:258-268`)

### Value Resolution Logic (ActiveClaimResolver)

`value_resolver.py:105-139` (`value_of_from_active`) is the core value determination:

- If no active claims: `no_claims`
- If only algorithm claims: checks pairwise AST equivalence via `ast_equiv.compare`. If all equivalent: `determined`. Otherwise: `conflicted`.
- If mixed algorithm + value claims: uses only value claims for determination
- If only value claims: unique values = `determined`, multiple distinct values = `conflicted`

### Condition Binding

`BoundWorld._is_active()` at `bound.py:157-178` uses a two-step filter:

1. **Context membership** -- if a context is bound, only claims from that context or its ancestors are visible. Claims with no context (`NULL context_id`) are always visible.
2. **CEL condition compatibility** -- uses Z3 to check if the claim's conditions are disjoint from the binding conditions. If disjoint, the claim is inactive.

The binding system converts keyword arguments to CEL expressions (e.g., `domain="speech"` becomes `domain == 'speech'`) at `bound.py:144-155`.

### Context Hierarchy

Loaded lazily from the sidecar at `model.py:106-163`. Supports:
- Inheritance (`inherits` field)
- Mutual exclusion (`excludes` field)
- Effective assumptions (inherited from context and its ancestors)

When binding with a `context_id`, the `Environment` is enriched with `effective_assumptions` from the hierarchy (`model.py:424-431`).

---

## 2. How Hypothetical Reasoning Works

`HypotheticalWorld` (`hypothetical.py:15`) is an **in-memory overlay** on a `BoundWorld`. It takes:

- `remove: list[str]` -- claim IDs to suppress
- `add: list[SyntheticClaim]` -- synthetic claims to inject

Key operations:

- **`active_claims()`** (`hypothetical.py:46-55`) -- takes base active claims, removes suppressed IDs, then appends synthetic claims that pass the base's `_is_active()` check
- **`diff()`** (`hypothetical.py:145-161`) -- compares `value_of` results between base and hypothetical for all affected concepts. Returns only concepts whose status or value set changed.
- **`recompute_conflicts()`** (`hypothetical.py:111-143`) -- O(n^2) pairwise comparison within each concept to find value disagreements among active claims
- **`conflicts()`** (`hypothetical.py:92-102`) -- merges base conflicts with newly recomputed ones, deduplicating by (claim_a, claim_b, concept) tuple

The CLI exposes this at `compiler_cmds.py:722-767`:
```
pks world hypothetical domain=example --remove claim2 --add '{"id":"synth1","concept_id":"concept1","value":42}'
```

---

## 3. Resolution Strategies

Four strategies in `resolution.py`, selected via the `ResolutionStrategy` enum (`types.py:31-35`):

### RECENCY (`resolution.py:16-34`)
Picks the claim whose `provenance_json` contains the most recent `date` string. Uses lexicographic string comparison on ISO date strings. Returns `None` if no claims have dates.

### SAMPLE_SIZE (`resolution.py:37-48`)
Picks the claim with the largest `sample_size` field. Straightforward numeric max.

### ARGUMENTATION (`resolution.py:51-93`)
Full formal argumentation:
- Delegates to `propstore.argumentation.compute_justified_claims`
- Builds a Dung AF from the stance graph filtered through preference ordering
- For `grounded` semantics: picks sole survivor from the grounded extension
- For `preferred`/`stable`: takes intersection across all extensions
- Only resolves if exactly one claim survives; otherwise remains conflicted

### OVERRIDE (`resolution.py:156-169`)
User explicitly picks a winning claim by ID. Validates that the override claim is actually active.

### RenderPolicy

`RenderPolicy` (`types.py:80-87`) bundles strategy configuration:
- Default strategy for all concepts
- Per-concept strategy overrides (`concept_strategies`)
- Argumentation parameters: `semantics`, `comparison`, `confidence_threshold`
- Manual overrides dict

The `resolve()` function at `resolution.py:96-203` orchestrates: checks if already determined or no_claims, extracts policy parameters, then dispatches to the appropriate strategy.

---

## 4. Chain Queries

`WorldModel.chain_query()` at `model.py:442-525` traverses the parameter space:

1. Seeds with user-provided bindings
2. Gets the parameterization group for the target concept
3. Iterates: for each unresolved concept in the group, tries `value_of` -> `resolved_value` (if conflicted and strategy given) -> `derived_value`
4. Repeats until no progress (`changed = False`)
5. Returns a `ChainResult` with all steps and the final result

This enables computing derived quantities from multi-step algebraic chains (e.g., A and B are known, C = f(A,B), D = g(C), so D can be derived).

---

## 5. CLI Interface and User-Facing Features

The CLI entry point is `propstore/cli/__init__.py`, exposing the `pks` command via Click.

### Command Groups

| Group | Key Commands |
|-------|-------------|
| `pks concept` | `add`, `alias`, `rename`, `deprecate`, `link`, `search`, `list`, `show`, `add-value`, `categories`, `embed`, `similar` |
| `pks claim` | `validate`, `validate-file`, `conflicts`, `compare`, `embed`, `similar`, `relate` |
| `pks context` | `add`, `list` |
| `pks form` | `add`, `list`, `show`, `remove`, `validate` |
| `pks world` | `status`, `query`, `bind`, `explain`, `derive`, `resolve`, `extensions`, `hypothetical`, `chain`, `export-graph`, `sensitivity`, `check-consistency`, `algorithms` |
| Top-level | `validate`, `build`, `query` (raw SQL), `export-aliases`, `import-papers`, `init` |

### Notable CLI Features

- **`pks world bind`** (`compiler_cmds.py:401-451`): Accepts positional args where `key=value` are bindings and the last non-binding arg is a concept filter. Flexible but unusual UX.
- **`pks world resolve`** (`compiler_cmds.py:580-639`): Full argumentation with `--semantics`, `--set-comparison`, `--confidence-threshold` options.
- **`pks world hypothetical`** (`compiler_cmds.py:722-767`): JSON input for synthetic claims via `--add`.
- **`pks world sensitivity`** (`compiler_cmds.py:850-912`): Computes partial derivatives and elasticities for derived quantities.
- **`pks world export-graph`** (`compiler_cmds.py:808-847`): DOT and JSON export of the knowledge graph.
- **`pks claim relate`** (`cli/claim.py:339-397`): Two-pass NLI stance classification with LLM.
- **`pks query`** (`compiler_cmds.py:207-235`): Raw SQL against sidecar -- power-user escape hatch.

### Repository Structure

`Repository` (`repository.py:12-105`) walks up from CWD to find `knowledge/` with a `concepts/` subdirectory. Standard layout:
```
knowledge/
  concepts/          # YAML concept definitions
    .counters/       # Auto-increment IDs with file locking
  claims/            # YAML claim files
  contexts/          # YAML context definitions
  forms/             # YAML form (type/unit) definitions
  stances/           # YAML stance files (LLM-generated)
  sidecar/           # propstore.sqlite (compiled)
```

---

## 6. Supporting Modules

### relate.py -- NLI Stance Classification

Two-pass async LLM classification (`relate.py:110-308`):
1. First pass: classify all embedding-similar claim pairs
2. Second pass: re-examine "none" verdicts below a distance threshold with a more detailed prompt

Confidence is mapped from (pass_number, strength) tuples at `relate.py:75-78`. Pass 1 strong = 0.95, pass 2 strong = 0.70. Concurrency controlled via `asyncio.Semaphore`.

### embed.py -- Vector Embeddings

Uses `litellm` for embedding generation and `sqlite-vec` for KNN search. Key design:
- Content-hash based staleness detection (`embed.py:189-206`)
- Embedding snapshot/restore across sidecar rebuilds (`embed.py:520-682`)
- Multi-model support with `agree` (intersection) and `disagree` (symmetric difference) queries (`embed.py:370-444`)
- Generic `_EmbedConfig`/`_FindConfig` dataclasses avoid code duplication between claim and concept embeddings

### graph_export.py -- Knowledge Graph

Builds a `KnowledgeGraph` from the sidecar with nodes (concepts + claims) and edges (parameterization, relationship, stance, claim_of). Supports DOT rendering via graphviz and JSON export. Group filtering by parameterization group ID.

### parameterization_groups.py -- Union-Find

Clean union-find with path compression and union-by-rank for finding connected components among concepts linked by parameterization relationships (`parameterization_groups.py:12-76`). Each component is a "parameter space group."

### param_conflicts.py -- Conflict Detection

Two levels:
- **Single-hop** (`_detect_param_conflicts`, line 61): For each exact parameterization, evaluates SymPy expression with input claim values, compares to direct claims
- **Multi-hop** (`detect_transitive_conflicts`, line 183): Iterative forward propagation through chains of 2+ hops, with context merging logic that rejects incoherent contexts

The context merging at `param_conflicts.py:35-58` is notable: it checks mutual exclusion, then picks the most specific (deepest ancestor chain) compatible context.

### unit_dimensions.py -- Dimensional Analysis

Resolves unit strings to SI dimension dicts (e.g., `"kPa"` -> `{"M": 1, "L": -1, "T": -2}`). Ships a lookup table from physgen's ISO 80000 data, extended by form-defined `extra_units`.

### equation_comparison.py -- SymPy Canonicalization

Builds canonical equation signatures for grouping (`equation_signature`, line 13) and canonical string representations via SymPy simplification (`canonicalize_equation`, line 43). Maps variable symbols to concept IDs before simplification.

### sympy_generator.py -- Expression Parsing

Converts human-readable math strings to SymPy-parseable form. Handles `^` -> `**` conversion, extracts RHS from equations. Also validates that all free symbols in an expression are declared in the variables list.

---

## 7. Code Quality Observations

### Strengths

1. **Clean protocol-based abstraction.** `ArtifactStore` and `BeliefSpace` protocols at `types.py:90-145` create a solid seam between data access and reasoning. This enables `HypotheticalWorld` to overlay without subclassing `WorldModel`.

2. **Lazy initialization throughout.** Z3 solver, concept registry, context hierarchy are all lazily loaded in `WorldModel` (`model.py:65-101, 106-163`). Good for CLI responsiveness.

3. **The `ActiveClaimResolver` composition pattern.** `value_resolver.py:13-26` uses constructor injection of callables rather than inheritance. Both `BoundWorld` and `HypotheticalWorld` construct their own resolver with appropriate callbacks. This is clean and testable.

4. **Content-hash based embedding staleness.** `embed.py:189-206` skips unchanged entities on re-embed, and the snapshot/restore mechanism (`embed.py:520-682`) preserves embeddings across sidecar rebuilds. Operationally important.

5. **Two-pass NLI design.** `relate.py:277-306` re-examines high-similarity pairs that got "none" on first pass. This catches subtle relationships that a single prompt misses.

6. **Cross-platform file locking.** `helpers.py:15-43` handles both Windows (`msvcrt`) and Unix (`fcntl`) for counter atomicity. The retry loop for `LK_NBLCK` on Windows is a thoughtful detail.

7. **Comprehensive CLI.** The `pks world` subcommand group exposes nearly every reasoner capability, including hypothetical reasoning, sensitivity analysis, argumentation extensions, and graph export.

### Concerns

1. **`_has_table` called repeatedly without caching.** `WorldModel._has_table()` at `model.py:319-323` does a `sqlite_master` query each time. It is called for every `claims_for`, `stances_between`, `conflicts`, `all_parameterizations`, `all_relationships`, `all_claim_stances`, and `all_parameterization` calls. For a read-only database, the set of tables never changes. This should be cached.

2. **`_claim_has_target_concept` detection via `pragma_table_info`.** At `model.py:193-199`, the schema is probed at runtime to check for a `target_concept` column. This suggests schema evolution is happening in-place rather than via migrations. The probe is cached, but the pattern implies the codebase needs to handle multiple sidecar schema versions.

3. **SQL injection surface in `claims_by_ids` and `stances_between`.** At `model.py:214` and `model.py:225`, f-string placeholders are used for `IN` clauses. The `# noqa: S608` comments acknowledge this. While the placeholders are `?`-based (safe), the f-string construction of the query structure itself is not ideal for maintainability. The pattern is correct but looks suspicious.

4. **`BoundWorld.conflicts()` recomputes conflicts every call.** At `bound.py:278-296`, `_recomputed_conflicts()` calls `detect_conflicts` which does full pairwise comparison plus SymPy evaluation. This is expensive and uncached. If `conflicts()` is called multiple times (e.g., during graph export + display), the cost doubles.

5. **`HypotheticalWorld` reaches into private members of `BoundWorld`.** At `hypothetical.py:28-29`:
   ```python
   parameterizations_for=getattr(self._base._store, "parameterizations_for", lambda _cid: []),
   is_param_compatible=self._base._is_param_compatible,
   ```
   And at `hypothetical.py:53`: `self._base._is_active(sc_dict)`. This tight coupling means any refactoring of `BoundWorld` internals breaks `HypotheticalWorld`.

6. **`chain_query` re-derives the target value at the end.** At `model.py:502-518`, after the iteration loop finds the target value, it re-calls `derived_value` or `value_of` to get a result object to return. This is wasteful -- the result was already computed during iteration.

7. **The `relate.py` second-pass loop has a subtle issue.** At `relate.py:302-306`:
   ```python
   for idx, task in second_tasks:
       second_result = await task
       first_pass_results = list(first_pass_results)
       first_pass_results[idx] = second_result
   ```
   `first_pass_results` is converted to a new list on every iteration. This is `O(n * m)` where n is the number of results and m is the number of second-pass items. Not a correctness bug, but wasteful.

8. **`embed.py` restore_embeddings has an O(n) scan for `embedded_at`.** At `embed.py:634`:
   ```python
   next((s["embedded_at"] for s in snapshot.claim_statuses
         if s["model_key"] == model_key and s["claim_id"] == claim_id), "")
   ```
   This linear scan runs for every restored embedding. For large snapshots, this is O(n^2). The `status_lookup` dict already exists but only stores `content_hash`, not `embedded_at`.

9. **`main.py` at repo root is a stub.** `main.py` just prints "Hello from propstore!" -- it is not the CLI entry point. The real entry point is `propstore/cli/__init__.py:cli`. This could confuse newcomers.

10. **`BoundWorld.__init__` accepts both `bindings`/`context_id` and `environment`** (`bound.py:106-115`). If `environment` is provided, `bindings` and `context_id` are ignored. The dual interface is a migration artifact -- the old positional args still work but `environment` is the intended path.

---

## 8. Surprising or Novel Things

### The ATMS/AGM Design Principle

The entire system is built around **never collapsing disagreement in storage**. Multiple conflicting claims coexist permanently. Resolution only happens at render time, and different render policies can produce different "truths" from the same corpus. This is directly grounded in de Kleer's ATMS (Assumption-based Truth Maintenance System) -- every datum is labeled with its minimal assumption sets, and the system never commits to one context.

### Z3 for Condition Compatibility

The condition system uses Z3 (an SMT solver) to check whether two sets of CEL conditions are satisfiable simultaneously (`bound.py:177-178`). This is more powerful than simple string matching -- it can determine that `temperature > 300` and `temperature < 200` are disjoint even though the strings don't match.

### AST-Based Algorithm Equivalence

At `value_resolver.py:141-166`, when multiple algorithm claims exist for the same concept, the system checks if they are semantically equivalent by comparing their ASTs via `ast_equiv.compare`. Known values are substituted to help the comparison. This means two papers presenting the same formula with different variable names will be recognized as agreeing.

### Sensitivity Analysis via Symbolic Differentiation

The `pks world sensitivity` command (visible at `compiler_cmds.py:850-912`) computes partial derivatives and elasticities for derived quantities. This tells the user which input measurement most influences the output -- a tool typically found in engineering simulation software, not knowledge management systems.

### Multi-Model Embedding Agreement/Disagreement

`embed.py:370-444` provides `find_similar_agree` (intersection across all embedding models) and `find_similar_disagree` (claims that are similar under some models but not others). The disagreement set is genuinely interesting -- it surfaces cases where different embedding representations capture different aspects of similarity.

### Two-Pass NLI with Confidence Decay

The stance classification system (`relate.py`) uses a two-pass approach where the second pass uses a more detailed prompt for high-similarity pairs that got "none" on first pass. Critically, second-pass verdicts have lower confidence (0.70 max vs 0.95 for first pass, at `relate.py:75-78`). This encodes epistemic humility about the more aggressive prompt.

---

## Files Reviewed

| File | Lines | Purpose |
|------|-------|---------|
| `propstore/world/__init__.py` | 37 | Public re-exports |
| `propstore/world/model.py` | 526 | WorldModel -- read-only reasoner over sidecar |
| `propstore/world/resolution.py` | 204 | Resolution strategies (recency, sample_size, argumentation, override) |
| `propstore/world/value_resolver.py` | 167 | ActiveClaimResolver -- value determination logic |
| `propstore/world/hypothetical.py` | 167 | HypotheticalWorld -- in-memory overlay |
| `propstore/world/bound.py` | 307 | BoundWorld -- condition-bound belief space |
| `propstore/world/types.py` | 146 | Data classes, enums, protocols |
| `propstore/relate.py` | 483 | NLI stance classification via LLM |
| `propstore/embed.py` | 683 | Embedding generation, storage, similarity search |
| `propstore/graph_export.py` | 241 | Knowledge graph export (DOT, JSON) |
| `propstore/parameterization_groups.py` | 77 | Union-find for parameter space groups |
| `propstore/param_conflicts.py` | 430 | Single-hop and multi-hop conflict detection |
| `propstore/unit_dimensions.py` | 103 | Unit-to-SI-dimensions resolver |
| `propstore/equation_comparison.py` | 96 | SymPy equation canonicalization |
| `propstore/sympy_generator.py` | 110 | Human-readable math to SymPy |
| `propstore/cli/__init__.py` | 48 | CLI entry point and command registration |
| `propstore/cli/claim.py` | 398 | Claim subcommands |
| `propstore/cli/compiler_cmds.py` | 984 | Build, validate, world query commands |
| `propstore/cli/concept.py` | 773 | Concept management subcommands |
| `propstore/cli/context.py` | 93 | Context management subcommands |
| `propstore/cli/form.py` | 250 | Form management subcommands |
| `propstore/cli/helpers.py` | 213 | File locking, counter management, YAML I/O |
| `propstore/cli/init.py` | 68 | Project initialization |
| `propstore/cli/repository.py` | 106 | Repository path resolution |
| `main.py` | 6 | Stub (not the real entry point) |
