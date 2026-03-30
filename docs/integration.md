# Integration

## research-papers-plugin

propstore consumes claims extracted by the [research-papers-plugin](https://github.com/ctoth/research-papers-plugin). The concept-first workflow:

1. **Read papers** — `paper-reader` skill extracts structured notes from PDFs
2. **Extract claims** — `extract-claims` skill reads the concept registry, creates missing concepts via `pks concept add`, then produces `claims.yaml` referencing only registered concepts
3. **Import** — `pks import-papers --papers-root ../papers/` copies claim files into the knowledge repository. The `--strict` flag enforces dimensional consistency on equation claims via bridgman. If any equation's SymPy expression fails dimensional verification against its variable forms, the entire import is aborted. Without `--strict`, dimensional mismatches are warnings only.

```bash
# Import with dimensional pre-check
pks import-papers --papers-root ../papers --strict

# Dry run to preview
pks import-papers --papers-root ../papers --dry-run
```
4. **Build** — `pks build` validates, detects conflicts, compiles the sidecar
5. **Embed** — `pks claim embed --all --model <model>` generates embeddings for cross-paper search
6. **Query** — `pks claim similar`, `pks world query`, `pks world bind`, etc.

The concept registry grows organically as papers are processed. Each extraction agent sees the full registry and reuses existing concepts where possible. Path dependence (which paper is processed first) is acceptable — reconciliation via embedding similarity merges duplicate concepts after the fact.

Without propstore installed, `extract-claims` still works — it uses descriptive concept names without registry validation. propstore adds structured validation, conflict detection, and cross-paper reasoning on top.

## Reconciliation workflow

As the concept registry grows through paper processing, duplicate concepts may emerge — different papers using different names for the same underlying idea. The reconciliation workflow:

1. **Embed concepts** — concept definitions are embedded alongside claims
2. **Find duplicates** — concepts with similar definitions are merge candidates
3. **Merge** — deprecate duplicate concepts with `replaced_by` pointers, rewrite claims
4. **Re-embed** — normalized concepts produce cleaner claim similarity

This is automated — no human review required. The `proposed -> accepted -> deprecated` lifecycle tracks concept maturity. Reconciliation runs after each batch of papers.

## Promote workflow

The heuristic analysis layer (Layer 3) produces proposals — stance classifications, concept merges, relationship annotations. Stance proposals are committed on the `proposal/stances` branch and are not source-of-truth until promoted.

`pks promote` copies committed stance proposal blobs from `proposal/stances` into `master`'s `knowledge/stances/`. This is the gate between heuristic output and source-of-truth storage. The promotion is atomic: a single git commit records the accepted stance state on `master`.

```bash
# Preview what would be promoted
pks promote

# Promote all pending stances
pks promote -y

# Promote a single committed proposal file
pks promote specific-stance.yaml
```

Currently, only stance proposals are supported. Concept and claim proposals must be manually reviewed and moved.

## Embeddings and similarity search

Optional: requires `pip install 'propstore[embeddings]'` (adds litellm and sqlite-vec).

Generate vector embeddings for claims using any LLM provider via litellm:

```bash
# Embed all claims with a model
pks claim embed --all --model gemini/gemini-embedding-001

# Find similar claims across the collection
pks claim similar claim1 --top-k 5

# Multi-model: embed with a second model
pks claim embed --all --model voyage/voyage-3-large

# Claims similar under ALL models (high confidence)
pks claim similar claim1 --agree

# Claims where models disagree (worth investigating)
pks claim similar claim1 --disagree
```

```bash
# Concept embeddings — find duplicate or overlapping concepts
pks concept embed --all --model gemini/gemini-embedding-001
pks concept similar structured_decomposition --top-k 5
```

Concept embeddings use the concept's canonical name, aliases, and definition as embedding text. Similar concepts are candidates for merging via `pks concept deprecate`.

Embeddings are stored in the sidecar SQLite database (one vector table per model) and survive `pks build` rebuilds. Re-running `pks claim embed --all` skips unchanged claims (incremental via content hash tracking). Use `--model all` to re-embed with every previously registered model.

## Stance classification

Optional: requires `propstore[embeddings]`.

`pks claim relate` uses an LLM to classify epistemic relationships between similar claims. It finds embedding-similar claim pairs, then prompts the model to classify each pair into one of the stance types (rebuts, undercuts, undermines, supports, explains, supersedes, or none). Results are committed as stance proposal snapshots on the `proposal/stances` branch.

```bash
# Classify relationships for a single claim against its nearest neighbors
pks claim relate claim1 --model gemini/gemini-2.0-flash --top-k 5

# Relate all claims (batch mode with concurrency control)
pks claim relate --all --model gemini/gemini-2.0-flash --concurrency 10

# Two-pass: use a tighter embedding threshold for the second pass
pks claim relate --all --model gemini/gemini-2.0-flash --second-pass-threshold 0.3
```

This feeds the argumentation framework — the classified stances become the attack and support relations that Dung extension computation operates on.

## Algorithm comparison (ast-equiv)

Papers often describe the same algorithm differently — different variable names, intermediate variables, loop styles. The [ast-equiv](../ast-equiv) package determines whether two Python function bodies compute the same thing.

**Canonicalization pipeline:**
1. Parse to AST
2. Normalize variable names to concept names via bindings dict
3. Alpha-rename remaining variables by position of first use
4. Normalize `while` loops to `for` loops where possible
5. Inline single-use temporary variables
6. Canonicalize: constant folding, identity elimination (`x + 0`, `x * 1`), repeated multiplication to powers, commutative sort, `x += y` to `x = x + y`, `range(0, N, 1)` to `range(N)`, boolean simplification, dead code removal, chained comparison collapse

**Four-tier comparison ladder:**
1. **Canonical AST match** — structural equality after canonicalization
2. **SymPy algebraic equivalence / Bytecode match** — algebraically equivalent expressions, or identical compiled bytecode
3. **Partial evaluation** — substitute known parameter values, then compare bytecode (two algorithms that differ only in a parameter become identical)
4. Structural similarity score (informational, not used for equivalence claims)

Usage via CLI:
```bash
pks claim compare claim50 claim51
pks claim compare claim50 claim51 -b T0=0.008
```
