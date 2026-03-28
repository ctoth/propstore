# propstore

Compiler and reasoning backend for structured scientific claims.

`propstore` is the engine layer in a larger workflow. The paper-facing frontend lives in the sibling `research-papers-plugin` repo, which handles paper retrieval, reading, annotation, and claim extraction. `propstore` takes the resulting structured concepts, claims, contexts, and stances; validates them; compiles them into a sidecar SQLite store; and supports conflict analysis, argumentation queries, counterfactual overlays, and ATMS-style inspection over the compiled corpus.

> Snapshot from one active corpus, not a guaranteed fresh-checkout demo: 315 concepts | 410 claims | 26 papers | 2050 auto-classified stances

## Where it fits

```text
PDFs / paper directories
  -> research-papers-plugin
  -> claims.yaml + concept registry + stance proposals
  -> propstore
  -> sidecar SQLite + query engine + reasoning backends
```

If you want to work with raw papers, start with `research-papers-plugin`.

If you want to work on the compiler, validator, sidecar builder, or reasoning engine, start here.

If you want a reproducible showcase corpus, use a dedicated demo repo or local demo corpus rather than assuming this source tree is itself a polished demo dataset.

## What It Does Today

- Validates forms, concepts, contexts, and claims
- Compiles a knowledge repo into a queryable SQLite sidecar
- Detects condition-sensitive conflicts with Z3, including regime splits vs real disagreement
- Projects claim relations into argumentation frameworks and computes grounded, preferred, and stable-style results where supported
- Runs hypothetical add/remove overlays without mutating the base world
- Derives values through parameterization chains and computes symbolic sensitivity
- Compares algorithm claims for equivalence across differently written implementations
- Exposes ATMS-style support, stability, relevance, and intervention queries over the active belief space

## What It Does Not Claim

- It does not read PDFs or extract claims from raw papers by itself
- It is not the main end-user paper workflow; that lives in `research-papers-plugin`
- It is not a general scientific truth machine
- ASPIC+ argument construction is integrated via `aspic_bridge.py` but does not yet cover the full specification (e.g., no contrariness-closure validation, no full rationality-postulate checking at runtime)
- It is not full AGM revision or a full de Kleer runtime manager
- This repo includes engine code plus evolving local knowledge fixtures; it should not be presented as a turnkey corpus demo

## What This Can Actually Do

Compile a knowledge repo into a sidecar:

```bash
uv run pks -C knowledge build
```

Inspect conflicts under bindings:

```bash
uv run pks -C knowledge claim conflicts
uv run pks -C knowledge world check-consistency domain=argumentation
```

Ask which claims survive the current argumentation projection:

```bash
uv run pks -C knowledge world extensions --semantics grounded
uv run pks -C knowledge world extensions --semantics preferred --set-comparison democratic
```

Run counterfactual overlays:

```bash
uv run pks -C knowledge world hypothetical --remove claim42
uv run pks -C knowledge world hypothetical --add '{"id":"synth1","concept_id":"concept1","value":150,"conditions":[]}'
```

Compare algorithms across papers:

```bash
uv run pks -C knowledge claim compare claim50 claim51 -b T0=0.008
```

Export graphs and inspect sensitivity:

```bash
uv run pks -C knowledge world export-graph --format json
uv run pks -C knowledge world sensitivity concept5 task=speech
```

Inspect ATMS support and intervention plans:

```bash
uv run pks -C knowledge world atms-status domain=argumentation
uv run pks -C knowledge world atms-interventions claim_id domain=argumentation
```

## Typical Workflow

1. Use `research-papers-plugin` to retrieve papers, read them, and produce structured `claims.yaml` files.
2. Initialize a propstore knowledge repo.
3. Import paper-local claims into the knowledge repo.
4. Build the sidecar.
5. Query, compare, export, and run reasoning passes over the compiled result.

```bash
# 1. Create a fresh knowledge repo
uv run pks init knowledge

# 2. Import claims extracted elsewhere
uv run pks -C knowledge import-papers --papers-root ../your-paper-project/papers

# 3. Validate and compile
uv run pks -C knowledge build

# 4. Query the compiled world
uv run pks -C knowledge world status
uv run pks -C knowledge world query fundamental_frequency
uv run pks -C knowledge world bind task=speech speaker_sex=male fundamental_frequency
```

## Why This Is Interesting

Most claim stores stop at ingestion or retrieval. `propstore` tries to push further into compilation and reasoning:

- Claims are scoped by typed CEL conditions, so disagreement can be classified as real conflict, partial overlap, or clean regime split
- Stances and conflict records can be projected into a reasoning graph rather than treated as plain metadata
- Hypothetical overlays let you ask "what changes if I remove or add this claim?"
- Parameterization chains and symbolic derivatives let you inspect how derived quantities move
- ATMS-style queries expose support quality, relevance, stability, and bounded intervention plans instead of only returning a winner

That is the real value proposition: not "we solved science", but "we can compile a structured claims corpus into something you can interrogate like a reasoning system".

## Installation

Requires Python 3.11+. Uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync
uv run pks --help
```

The current development setup expects a sibling `../ast-equiv` checkout via `uv.lock`.

Optional for embeddings and LLM-assisted stance classification:

```bash
uv pip install "propstore[embeddings]"
```

## How It Works

`pks build` runs a compiler pipeline over a knowledge repo:

1. Form validation
2. Concept validation
3. Context validation
4. Claim validation
5. Sidecar build
6. Conflict detection

The result is a SQLite sidecar plus a query layer over active claims, relations, parameterizations, and conflicts.

## Data Model

The core entities are:

- concepts
- forms
- claims
- conditions
- stances
- contexts

Claim types currently include:

- `parameter`
- `equation`
- `measurement`
- `observation`
- `model`
- `algorithm`
- `mechanism`
- `comparison`
- `limitation`

See [docs/data-model.md](docs/data-model.md) for concrete YAML examples.

## Documentation

- [Data Model](docs/data-model.md) — concepts, forms, claim types, conditions, stances, contexts
- [Argumentation](docs/argumentation.md) — claim-graph backend, semantic axes, MaxSMT, ATMS boundaries
- [CLI Reference](docs/cli-reference.md) — command reference
- [Integration](docs/integration.md) — how this fits with `research-papers-plugin`

## Dependencies

| Package | Role |
|---------|------|
| [Z3](https://github.com/Z3Prover/z3) | SMT solving for condition reasoning, conflict analysis, and optimization |
| [SymPy](https://www.sympy.org/) | Symbolic math for parameterization and sensitivity |
| [LinkML](https://linkml.io/) | Schema definition and JSON Schema generation |
| [click](https://click.palletsprojects.com/) | CLI framework |
| `ast-equiv` | Algorithm canonicalization and equivalence comparison |
| [litellm](https://github.com/BerriAI/litellm) | Optional embeddings and stance classification |
| [sqlite-vec](https://github.com/asg017/sqlite-vec) | Optional vector search in SQLite |
