# propstore

Compiler and reasoning backend for structured scientific claims.

`propstore` is the engine layer in a larger workflow. The paper-facing frontend lives in the sibling `research-papers-plugin` repo, which handles paper retrieval, reading, annotation, and claim extraction. `propstore` takes the resulting structured concepts, claims, contexts, and stances; validates them; compiles them into a sidecar SQLite store; and supports conflict analysis, argumentation queries, counterfactual overlays, and ATMS-style inspection over the compiled corpus.

## Architecture

```text
Layer 6: Agent Workflow    — extract-claims, reconcile, relate, adjudicate
Layer 5: Render            — resolution strategies, world queries, worldlines, hypotheticals
Layer 4: Argumentation     — Dung AF, ASPIC+, PrAF, bipolar, ATMS
Layer 3: Heuristic         — embeddings, LLM stance classification (proposals only)
Layer 2: Theory / Typing   — forms, dimensions, CEL type-checking, Z3 conditions
Layer 1: Source Storage    — claims, concepts, contexts, stances, provenance (immutable)
```

Dependencies flow downward only. Layers 1-2 are the formal core. Layer 3 produces proposals, never mutations. Layer 4 operates over assumption-labeled data. Layer 5 applies policy at query time. Layer 6 orchestrates multi-step agent workflows.

### Where it fits

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

- Validates forms, concepts, contexts, and claims against LinkML schemas and CEL type-checking
- Compiles a knowledge repo into a queryable SQLite sidecar
- Detects condition-sensitive conflicts with Z3, including regime splits vs real disagreement
- Projects claim relations into argumentation frameworks via multiple reasoning backends (see below)
- Computes grounded, complete, preferred, and stable extensions
- Runs hypothetical add/remove overlays without mutating the base world
- Derives values through parameterization chains and computes symbolic sensitivity
- Compares algorithm claims for equivalence across differently written implementations
- Exposes ATMS-style support, stability, relevance, and intervention queries over the active belief space
- Materializes worldlines: traced, reproducible paths through the knowledge space with full provenance
- Represents uncertainty honestly via subjective logic opinions with calibrated evidence mapping

## Reasoning Backends

propstore ships multiple reasoning backends at different abstraction levels, selectable via `--reasoning-backend`:

| Backend | What it does | Key files |
|---------|-------------|-----------|
| `claim_graph` | Dung AF over active claim rows with heuristic metadata preferences. Default backend. | `argumentation.py`, `dung.py`, `dung_z3.py` |
| `structured_projection` | Full ASPIC+ argument construction: recursive PremiseArg/StrictArg/DefeasibleArg, three-type attack (Def 8), last-link/weakest-link preference defeat (Defs 19-21) | `aspic_bridge.py`, `aspic.py` |
| `aspic` | Direct ASPIC+ bridge entry point | `aspic_bridge.py` |
| `praf` | Probabilistic argumentation: MC sampling with Agresti-Coull stopping (Li et al. 2012), DF-QuAD gradual semantics (Freedman et al. 2025), optional COH enforcement (Hunter & Thimm 2017) | `praf.py`, `praf_dfquad.py` |
| `atms` | ATMS label propagation and bounded replay over the active belief space (de Kleer 1986). Does not expose Dung extensions — use ATMS-native commands instead. | `world/atms.py` |

Additional argumentation infrastructure:

- **Bipolar argumentation** (`bipolar.py`) — Cayrol 2005 derived defeats with fixpoint, d/s/c-admissibility, stable extensions
- **Subjective logic** (`opinion.py`) — Jøsang 2001 Opinion = (b,d,u,a) with consensus fusion, discounting, negation, conjunction, disjunction, ordering, uncertainty maximization
- **Calibration** (`calibrate.py`) — Temperature scaling (Guo et al. 2017), corpus CDF calibration, evidence-to-opinion mapping (Sensoy et al. 2018), ECE
- **Decision criteria** — Pignistic (default), Hurwicz, lower/upper bound per Denoeux 2019, selectable via `--decision-criterion`

## What It Does Not Claim

- It does not read PDFs or extract claims from raw papers by itself
- It is not the main end-user paper workflow; that lives in `research-papers-plugin`
- It is not a general scientific truth machine
- ASPIC+ rationality postulates (Thms 12-15) are achieved by construction via transposition closure and c-consistency, not runtime-verified
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

Rank claims by fragility (what to learn next):

```bash
uv run pks -C knowledge world fragility --top-k 10
uv run pks -C knowledge world fragility --concept concept5 --sort-by roi
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

Create and run worldlines:

```bash
# Create a worldline targeting specific concepts with a reasoning backend
uv run pks -C knowledge worldline create my_query domain=speech --reasoning-backend praf --praf-strategy mc

# Materialize results
uv run pks -C knowledge worldline run my_query

# Inspect results, compare worldlines, refresh with new data
uv run pks -C knowledge worldline show my_query
uv run pks -C knowledge worldline diff query_a query_b
uv run pks -C knowledge worldline refresh my_query
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
- Stances and conflict records can be projected into multiple reasoning backends — from flat Dung AFs through structured ASPIC+ arguments to probabilistic acceptance
- Uncertainty is represented honestly via subjective logic opinions with calibrated evidence mapping, not collapsed to point estimates
- Hypothetical overlays let you ask "what changes if I remove or add this claim?"
- Parameterization chains and symbolic derivatives let you inspect how derived quantities move
- ATMS-style queries expose support quality, relevance, stability, and bounded intervention plans instead of only returning a winner
- Worldlines capture reproducible, traced paths through the knowledge space with full provenance and staleness detection

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
- [Argumentation](docs/argumentation.md) — reasoning backends, conflict detection, ATMS overview
- [Structured Argumentation (ASPIC+)](docs/structured-argumentation.md) — recursive argument construction, three-type attack, preference defeat
- [Probabilistic Argumentation (PrAF)](docs/probabilistic-argumentation.md) — MC sampling, Agresti-Coull stopping, DF-QuAD gradual semantics
- [Subjective Logic and Calibration](docs/subjective-logic.md) — Opinion algebra, temperature scaling, evidence-to-opinion mapping, decision criteria
- [ATMS](docs/atms.md) — assumption-based truth maintenance, label propagation, bounded replay, interventions
- [Bipolar Argumentation](docs/bipolar-argumentation.md) — Cayrol 2005, derived defeats, three admissibility variants
- [Conflict Detection](docs/conflict-detection.md) — Z3 condition reasoning, regime splits, six conflict classes
- [Parameterization and Sensitivity](docs/parameterization.md) — derivation chains, chain queries, elasticity analysis
- [Algorithm Comparison](docs/algorithm-comparison.md) — ast-equiv four-tier equivalence ladder
- [Fragility Analysis](docs/fragility.md) — parametric, epistemic, and conflict fragility with ROI ranking
- [Worldlines](docs/worldlines.md) — materialized query artifacts, provenance tracking, staleness detection
- [CLI Reference](docs/cli-reference.md) — command reference (69 commands across 7 groups)
- [Integration](docs/integration.md) — how this fits with `research-papers-plugin`

## Dependencies

| Package | Role |
|---------|------|
| [Z3](https://github.com/Z3Prover/z3) | SMT solving for condition reasoning, conflict analysis, and extension computation |
| [SymPy](https://www.sympy.org/) | Symbolic math for parameterization and sensitivity |
| [LinkML](https://linkml.io/) | Schema definition and JSON Schema generation |
| [click](https://click.palletsprojects.com/) | CLI framework |
| [bridgman](https://github.com/ctoth/bridgman) | Dimensional analysis for unit compatibility |
| [pint](https://pint.readthedocs.io/) | Unit parsing and conversion |
| [graphviz](https://graphviz.readthedocs.io/) | Graph export (DOT format) |
| `ast-equiv` | Algorithm canonicalization and equivalence comparison |
| [litellm](https://github.com/BerriAI/litellm) | Optional embeddings and stance classification |
| [sqlite-vec](https://github.com/asg017/sqlite-vec) | Optional vector search in SQLite |
