# propstore

A compiler and query engine for propositional knowledge extracted from scientific papers across any research domain — speech science, video understanding, medicine, or any field where papers make empirical claims.

propstore takes structured claims — parameter values, equations, measurements, algorithms, qualitative observations, mechanisms, comparisons, limitations — extracted from papers, each tagged with the conditions under which they hold, and compiles them into a queryable SQLite database. The compiler validates everything, detects conflicts between claims, and the query engine supports condition-scoped lookups, derivation through parameterization chains, conflict resolution via argumentation semantics, sensitivity analysis, and counterfactual reasoning.

## The problem

Scientific literature contains claims like "fundamental frequency averages 120 Hz for male speakers" and "fundamental frequency averages 210 Hz for female speakers." These aren't contradictions — they hold under different conditions. But across dozens of papers and hundreds of claims, you need machinery to:

- Distinguish genuine conflicts from claims that simply have different conditions
- Derive values through algebraic relationships when direct measurements aren't available
- Resolve genuine disagreements using argumentation semantics (Dung frameworks, ASPIC+ preference ordering, MaxSMT optimization)
- Compare algorithm implementations that describe the same computation with different variable names and coding styles
- Ask "what if" questions: what changes if you remove a claim or inject a synthetic one?

Or across video understanding papers: Paper A claims "MapReduce decomposition outperforms retrieval-based approaches for long video QA with 10% accuracy improvement" while Paper B claims "dense perception of all video segments outperforms selective key-segment retrieval even when controlling for total content seen." Are these the same finding? Do they support each other? propstore finds out.

## Installation

Requires Python 3.11+. Uses [uv](https://docs.astral.sh/uv/) for dependency management.

```
uv sync
```

propstore depends on [ast-equiv](../ast-equiv), a sibling package for algorithm equivalence comparison. The `uv.lock` resolves it from a local path (`../ast-equiv`).

The CLI is installed as `pks`:

```
uv run pks --help
```

## Getting started

```bash
# Create a new knowledge repository
pks init

# Add concepts (created during paper processing, or manually):
pks concept add --domain video --name dense_video_captioning \
  --form structural \
  --definition "Generating descriptions for all events in a video with temporal boundaries"

pks concept add --domain video --name temporal_grounding \
  --form structural \
  --definition "Mapping textual descriptions to specific time intervals in video"

# Import claims from a research-papers collection
pks import-papers --papers-root ../papers/

# Validate and build
pks validate
pks build

# Query
pks world status
pks world query dense_video_captioning

# Embed claims and concepts for similarity search (optional, requires propstore[embeddings])
pks claim embed --all --model gemini/gemini-embedding-001
pks concept embed --all --model gemini/gemini-embedding-001

# Find similar claims across papers
pks claim similar claim1 --top-k 5

# Find similar concepts (potential duplicates to merge)
pks concept similar dense_video_captioning --top-k 5
```

## Data model

### Concepts

A concept is a named quantity, category, or structural entity. One YAML file per concept, filename matches `canonical_name`.

```yaml
id: concept1
canonical_name: fundamental_frequency
status: accepted
definition: Rate of vocal fold vibration during phonation.
domain: speech
form: frequency
aliases:
  - name: F0
    source: common
  - name: pitch_frequency
    source: Titze_1994
relationships:
  - type: component_of
    target: concept5
parameterization_relationships:
  - formula: "f0 = 1 / T0"
    sympy: "Eq(concept1, 1 / concept2)"
    inputs: [concept2]
    exactness: exact
    source: definition
    bidirectional: true
```

**Status lifecycle:** `proposed` -> `accepted` -> `deprecated` (with `replaced_by` pointer). Concepts are never deleted.

**Kind system:** Each concept has a `form` referencing a form definition file. The form determines the concept's kind:

| Kind | Examples | CEL behavior |
|------|----------|-------------|
| `quantity` | frequency, pressure, duration | Numeric comparisons and arithmetic |
| `category` | voice_quality_type, language | Equality and `in` checks against value sets |
| `boolean` | is_voiced | Boolean logic |
| `structural` | voice_source | Cannot appear in CEL expressions |

### Forms

Form definitions live in `forms/<name>.yaml` and define dimensional type signatures:

```yaml
name: frequency
unit_symbol: Hz
dimensionless: false
dimensions:
  T: -1
common_alternatives:
  - unit: kHz
    type: multiplicative
    multiplier: 0.001
```

The compiler uses form definitions for unit validation via dimensional analysis, checking that claim units are compatible with concept dimensions.

### Claims

Claims are extracted from papers and stored in `claims/<paper_name>.yaml`. Nine claim types:

**parameter** — A numeric value binding for a concept under stated conditions:

Speech science example:
```yaml
- id: claim1
  type: parameter
  concept: concept1
  value: 120.0
  uncertainty: 15.0
  uncertainty_type: sd
  unit: Hz
  conditions:
    - "speaker_sex == 'male'"
  provenance:
    paper: Titze_1994
    page: 42
```

Accessibility example:
```yaml
- id: claim1
  type: parameter
  concept: ad_reading_speed
  value: 180.0
  unit: "words/min"
  conditions:
    - "task == 'audio_description'"
  provenance:
    paper: Li_2026_ADCanvas
    page: 8
```

**equation** — A mathematical relationship with variable bindings:

Speech science example:
```yaml
- id: claim10
  type: equation
  expression: "OQ = (T_o) / T_0"
  sympy: "Eq(OQ, T_o / T_0)"
  variables:
    - symbol: OQ
      concept: concept3
    - symbol: T_o
      concept: concept4
    - symbol: T_0
      concept: concept2
  provenance:
    paper: Henrich_2003
    page: 8
```

Video understanding example:
```yaml
- id: claim11
  type: equation
  expression: "CIDEr = (1/N) * sum(g_n * CIDEr_n)"
  sympy: "Eq(CIDEr, (1/N) * Sum(g_n * CIDEr_n, (n, 1, N)))"
  variables:
    - symbol: CIDEr
      concept: caption_quality_score
    - symbol: N
      concept: ngram_order
  provenance:
    paper: Wang_2024_EventDVC
    page: 6
```

**measurement** — A perceptual or behavioral measurement:

Speech science example:
```yaml
- id: claim20
  type: measurement
  target_concept: concept1
  measure: jnd_relative
  value: 0.003
  unit: ratio
  listener_population: native_english
  provenance:
    paper: Moore_1973
    page: 15
```

Video understanding example:
```yaml
- id: claim21
  type: measurement
  target_concept: dense_video_captioning
  measure: SODA_c
  value: 6.1
  unit: score
  conditions:
    - "dataset == 'ActivityNet'"
  provenance:
    paper: Wang_2024_EventDVC
    page: 9
```

**observation** — A qualitative claim that resists parameterization:

Speech science example:
```yaml
- id: claim30
  type: observation
  statement: "Breathiness increases with incomplete glottal closure"
  concepts: [concept7, concept8]
  provenance:
    paper: Klatt_1990
    page: 22
```

Video understanding example:
```yaml
- id: claim31
  type: observation
  statement: "Structured decomposition of video into per-agent attributes followed by LLM synthesis outperforms direct end-to-end VLM captioning"
  concepts: [dense_video_captioning, mixture_of_experts]
  provenance:
    paper: Li_2024_Wolf
    page: 7
```

**model** — A parameterized equation system:

Speech science example:
```yaml
- id: claim40
  type: model
  name: "Klatt cascade formant synthesizer"
  equations:
    - "output = cascade(F1, F2, F3, F4, F5)"
  parameters:
    - name: F1
      concept: concept10
  provenance:
    paper: Klatt_1980
    page: 5
```

Video understanding example:
```yaml
- id: claim41
  type: model
  name: "MapReduce video QA decomposition"
  equations:
    - "answer = reduce(map(segment_answers, question))"
  parameters:
    - name: segment_answers
      concept: segment_level_qa
  provenance:
    paper: He_2024_MRVideo
    page: 4
```

**algorithm** — A procedural computation as a Python function body:

Speech science example:
```yaml
- id: claim50
  type: algorithm
  concept: concept12
  stage: excitation
  body: |
    def glottal_pulse(t, T0, Tp, Tn):
        if t < Tp:
            return 0.5 * (1 - math.cos(math.pi * t / Tp))
        elif t < Tp + Tn:
            return math.cos(math.pi * (t - Tp) / (2 * Tn))
        else:
            return 0.0
  variables:
    - name: t
      concept: concept60
    - name: T0
      concept: concept2
  provenance:
    paper: Klatt_1980
    page: 12
```

Video understanding example:
```yaml
- id: claim51
  type: algorithm
  concept: adaptive_keyframe_selection
  stage: preprocessing
  body: |
    def select_keyframes(video_frames, similarity_threshold):
        keyframes = [video_frames[0]]
        for frame in video_frames[1:]:
            if cosine_similarity(frame, keyframes[-1]) < similarity_threshold:
                keyframes.append(frame)
        return keyframes
  variables:
    - name: video_frames
      concept: video_frame_sequence
    - name: similarity_threshold
      concept: frame_similarity_threshold
  provenance:
    paper: Katna_2025_AKS
    page: 5
```

**mechanism** — A causal or explanatory process linking concepts:

```yaml
- id: claim60
  type: mechanism
  statement: "Undercutting defeat removes the connection between premise and conclusion without challenging the premise itself"
  concepts: [undercutting_attack, defeasible_reasoning]
  provenance:
    paper: Pollock_1987
    page: 485
```

**comparison** — A comparative claim between approaches, methods, or systems:

```yaml
- id: claim61
  type: comparison
  statement: "Preferred semantics produces more extensions than grounded semantics on frameworks with even-length cycles"
  concepts: [preferred_extension, grounded_extension]
  provenance:
    paper: Dung_1995
    page: 331
```

**limitation** — A known boundary, failure case, or applicability constraint:

```yaml
- id: claim62
  type: limitation
  statement: "Stable extensions are not guaranteed to exist for all argumentation frameworks"
  concepts: [stable_extension, argumentation_framework]
  provenance:
    paper: Dung_1995
    page: 328
```

### Conditions

Claims and relationships can be scoped by **conditions** — CEL (Common Expression Language) expressions that define when they hold:

```yaml
conditions:
  - "speaker_sex == 'male'"
  - "task == 'speech'"
```

The compiler type-checks conditions against the concept registry: quantity concepts get numeric comparisons, category concepts get equality/`in` checks with value-set validation, boolean concepts get boolean logic.

### Stances

Claims can express epistemic relations to other claims:

```yaml
stances:
  - type: rebuts
    target: claim15
    strength: strong
    note: "Contradicting conclusion with larger sample size"
  - type: supersedes
    target: claim42
```

Six stance types (ASPIC+ taxonomy, active voice — the claim holding the stance acts on the target):

| Type | Category | Weight | Meaning |
|------|----------|--------|---------|
| `rebuts` | Attack | -1.0 | Directly contradicts the target's conclusion |
| `undercuts` | Attack | -1.0 | Attacks the inference method or reasoning |
| `undermines` | Attack | -0.5 | Weakens a premise or evidence quality |
| `supports` | Support | +1.0 | Provides corroborating evidence |
| `explains` | Support | +0.5 | Provides a mechanistic explanation |
| `supersedes` | Preference | — | Replaces the target entirely (short-circuits resolution) |

Based on ASPIC+ (Modgil & Prakken 2014) and Pollock's rebutting vs undercutting distinction (Prakken & Horty 2012).

Stances feed into the argumentation framework (see below) — attacks become defeat candidates filtered through preference ordering, supports contribute to claim strength.

### Contexts

Contexts represent research traditions, theoretical frameworks, or experimental paradigms that scope groups of claims. One YAML file per context in `contexts/`:

```yaml
id: ctx_abstract_argumentation
name: ctx_abstract_argumentation
description: Dung's abstract argumentation framework tradition — arguments as abstract
  entities with attack relations, multiple acceptability semantics
```

Claims reference their context via `context_id`. The compiler validates that all `context_id` references resolve to registered contexts. Contexts support hierarchy (`parent`), mutual exclusion (`excludes`), and visibility scoping — a BoundWorld can be filtered to show only claims from a given context and its descendants.

```bash
# Add a context
pks context add --id ctx_belief_revision --name ctx_belief_revision \
  --description "AGM-style belief revision tradition"

# List contexts
pks context list
```

## Argumentation

propstore currently ships one reasoning backend: a claim-graph backend. It builds a Dung AF over active claim rows, uses heuristic claim metadata for preferences, and uses claim conditions only to determine activity. This is inspired by Dung and ASPIC+ style reasoning, but it is not a full structured-argument ASPIC+ implementation.

### Dung abstract argumentation

The core engine implements Dung's abstract argumentation framework AF = (Args, Defeats). Given a set of arguments (claims) and a defeat relation (derived from stances filtered through preference ordering), it computes:

- **Grounded extension** — the unique minimal complete extension (skeptical reasoning)
- **Preferred extensions** — maximal admissible sets (credulous reasoning)
- **Stable extensions** — conflict-free sets that defeat all external arguments

Two backends: brute-force enumeration (`dung.py`) and Z3 SAT encoding (`dung_z3.py`) for scalability.

### Claim-graph bridge

The bridge layer (`argumentation.py`) converts raw stances into a Dung AF:

1. Load stances between active claims with confidence above threshold
2. Undercutting and supersedes attacks always become defeats
3. Rebutting and undermining attacks become defeats only if the attacker is at least as strong as the target (elitist comparison) or the attacking set is at least as strong (democratic comparison)
4. Build the Dung AF from surviving defeats
5. Compute extensions under chosen semantics

## Semantic axes

- `reasoning_backend` selects how the active belief space is interpreted. The default and only implemented backend today is `claim_graph`.
- `resolution_strategy` selects how to pick a winner when a conflicted concept still has multiple active claims after belief-space reasoning.
- `comparison` selects the preference-comparison rule used inside the claim-graph argumentation backend.

The long-term target architecture is a labelled belief space. Current worldline files and CLI defaults still run on the claim-graph backend.

### MaxSMT conflict resolution

For large conflict sets, `maxsat_resolver.py` uses Z3's Optimize with weighted soft constraints to find the maximally consistent subset of claims. Each claim gets a soft constraint weighted by its strength score — the solver keeps as many strong claims as possible while eliminating all conflicts.

### Extensions CLI

```bash
# Show the grounded extension (claims that survive all attacks)
pks world extensions --semantics grounded

# Preferred extensions under condition bindings
pks world extensions domain=argumentation --semantics preferred

# Stable extensions with democratic set comparison
pks world extensions --semantics stable --set-comparison democratic
```

## Compiler pipeline

`pks build` runs the full pipeline:

1. **Form validation** — JSON Schema check on all `forms/*.yaml`
2. **Concept validation** — Required fields, ID format and uniqueness, filename-name match, deprecation chain integrity, CEL type-checking, form parameter compatibility, dimensional heuristics on parameterization inputs
3. **Context validation** — Required fields, ID uniqueness, hierarchy cycle detection, exclusion consistency, parent reference resolution
4. **Claim validation** — JSON Schema, concept reference resolution (by ID, canonical name, or alias), context reference validation, unit compatibility via dimensional analysis, algorithm body parsing with AST cross-check of declared variables against names used in the body
5. **Sidecar build** — SQLite database with concept, alias, relationship, parameterization, parameterization_group, context, claim, claim_stance, defeat, and conflicts tables, plus FTS5 indexes over names/definitions/conditions
6. **Conflict detection** — Batch equivalence classification of condition pairs, direct conflicts between claims on the same concept, plus transitive conflicts through parameterization chains

Incremental: the sidecar is content-hash addressed and only rebuilt when source data changes.

## Conflict detection

When two claims bind to the same concept, the conflict detector classifies them:

| Class | Meaning |
|-------|---------|
| `COMPATIBLE` | Values consistent (within tolerance or overlapping ranges). Not reported. |
| `PHI_NODE` | Values differ, conditions fully disjoint (Z3-verified). Not a conflict — they describe different regimes. |
| `CONFLICT` | Values differ, conditions identical or both unconditional. Genuine disagreement. |
| `OVERLAP` | Values differ, conditions partially overlapping. Needs investigation. |
| `PARAM_CONFLICT` | Conflict detected via parameterization chain: claim A and claim B individually consistent, but deriving through a shared formula produces contradictory outputs. |

Condition disjointness is checked via Z3 satisfiability. Category concepts get EnumSorts, quantity concepts get Reals, boolean concepts get Bools. Condition pairs are first grouped into equivalence classes by structural similarity, so Z3 is only called once per unique condition pattern.

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

## Stance classification (claim relate)

Optional: requires `propstore[embeddings]`.

`pks claim relate` uses an LLM to classify epistemic relationships between similar claims. It finds embedding-similar claim pairs, then prompts the model to classify each pair into one of the stance types (rebuts, undercuts, undermines, supports, explains, supersedes, or none). Results are written back as stances in the claim YAML files.

```bash
# Classify relationships for a single claim against its nearest neighbors
pks claim relate claim1 --model gemini/gemini-2.0-flash --top-k 5

# Relate all claims (batch mode with concurrency control)
pks claim relate --all --model gemini/gemini-2.0-flash --concurrency 10

# Two-pass: use a tighter embedding threshold for the second pass
pks claim relate --all --model gemini/gemini-2.0-flash --second-pass-threshold 0.3
```

This feeds the argumentation framework — the classified stances become the attack and support relations that Dung extension computation operates on.

## Reconciliation workflow

As the concept registry grows through paper processing, duplicate concepts may emerge — different papers using different names for the same underlying idea. The reconciliation workflow:

1. **Embed concepts** — concept definitions are embedded alongside claims
2. **Find duplicates** — concepts with similar definitions are merge candidates
3. **Merge** — deprecate duplicate concepts with `replaced_by` pointers, rewrite claims
4. **Re-embed** — normalized concepts produce cleaner claim similarity

This is automated — no human review required. The `proposed → accepted → deprecated` lifecycle tracks concept maturity. Reconciliation runs after each batch of papers.

## Algorithm comparison (ast-equiv)

Papers often describe the same algorithm differently — different variable names, intermediate variables, loop styles. The `ast-equiv` package determines whether two Python function bodies compute the same thing.

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
uv run pks claim compare claim50 claim51
uv run pks claim compare claim50 claim51 -b T0=0.008
```

## World model queries

After `pks build`, the world model provides read-only queries against the sidecar database with condition-binding support.

### Bind conditions

Scope all queries to claims active under specific conditions:

```bash
uv run pks world bind task=speech speaker_sex=male concept1
```

A claim is active under bindings B when its conditions are not disjoint from B (checked via Z3).

### Value lookup

What do the claims say about a concept?

```bash
uv run pks world query concept1
```

Returns status: `determined` (one consistent value), `conflicted` (multiple disagreeing values), `underdetermined` (range but no point value), or `no_claims`.

### Derivation

Compute a value through parameterization relationships:

```bash
uv run pks world derive concept5 task=speech
```

Evaluates SymPy expressions with input values resolved from claims. Handles `Eq(y, expr)` form (solve for y) and bare expressions (direct substitution).

### Resolution

Resolve conflicting claims using a strategy:

```bash
uv run pks world resolve concept1 task=speech --strategy sample_size
```

Strategies: `recency` (most recent paper wins), `sample_size` (largest N wins), `argumentation` (run the current claim-graph backend over the whole active belief space, then project survivors back to the target concept), `override` (specify a claim ID).

### Chain queries

Traverse the parameter graph to derive a target concept, resolving conflicts along the way:

```bash
uv run pks world chain concept5 task=speech --strategy sample_size
```

### Hypothetical worlds

What changes if claims are removed or added?

```bash
uv run pks world hypothetical task=speech --remove claim2
uv run pks world hypothetical --add '{"id":"synth1","concept_id":"concept1","value":150,"conditions":[]}'
```

Returns a diff: which concepts changed status, from what to what.

### Sensitivity analysis

Which input most influences a derived output?

```bash
uv run pks world sensitivity concept5 task=speech
```

Computes partial derivatives and elasticities via SymPy symbolic differentiation.

### Graph export

```bash
uv run pks world export-graph --format dot --output graph.dot
uv run pks world export-graph task=speech --format json --group 0
```

Exports concept nodes, claim nodes, and parameterization/relationship/stance/claim_of edges. Supports filtering by parameterization group and condition bindings.

### Consistency checking

```bash
uv run pks world check-consistency task=speech
uv run pks world check-consistency --transitive
```

### Argumentation extensions

Which claims survive scrutiny under formal argumentation semantics?

```bash
uv run pks world extensions --semantics grounded
uv run pks world extensions domain=argumentation --semantics preferred
uv run pks world extensions --semantics stable --set-comparison democratic
```

The grounded extension is unique and represents the skeptically justified claims. Preferred extensions are maximal admissible sets — each represents a credulous position. Stable extensions (when they exist) are the strongest: conflict-free sets that defeat every non-member.

## CLI reference

```
pks init [DIRECTORY]              Create a new knowledge repository
pks validate                      Validate all concepts, claims, and forms
pks build [-o PATH] [--force]     Validate and compile to sidecar SQLite
pks query SQL                     Run raw SQL against the sidecar

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

pks claim validate                Validate all claim files
pks claim validate-file FILE      Validate a single claims YAML file
pks claim conflicts               Detect and report conflicts
pks claim compare A B             Compare two algorithm claims (ast-equiv)
pks claim relate [ID] --all --model M  Classify epistemic relationships via LLM
pks claim embed [ID] --all --model M   Generate claim embeddings via litellm
pks claim similar ID [--model M]       Find similar claims by embedding distance

pks form list                     List available forms
pks form show NAME                Show a form definition
pks form add --name NAME          Add a new form
pks form remove NAME              Remove a form
pks form validate [NAME]          Validate form definitions

pks context add                   Add a new context
pks context list                  List all registered contexts

pks import-papers --papers-root PATH   Import claims from a papers/ corpus
pks export-aliases [--format json]     Export the alias lookup table

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

## Integration with research-papers-plugin

propstore consumes claims extracted by the [research-papers-plugin](../research-papers-plugin). The concept-first workflow:

1. **Read papers** — `paper-reader` skill extracts structured notes from PDFs
2. **Extract claims** — `extract-claims` skill reads the concept registry, creates missing concepts via `pks concept add`, then produces `claims.yaml` referencing only registered concepts
3. **Import** — `pks import-papers --papers-root ../papers/` copies claim files into the knowledge repository
4. **Build** — `pks build` validates, detects conflicts, compiles the sidecar
5. **Embed** — `pks claim embed --all --model <model>` generates embeddings for cross-paper search
6. **Query** — `pks claim similar`, `pks world query`, `pks world bind`, etc.

The concept registry grows organically as papers are processed. Each extraction agent sees the full registry and reuses existing concepts where possible. Path dependence (which paper is processed first) is acceptable — reconciliation via embedding similarity merges duplicate concepts after the fact.

Without propstore installed, `extract-claims` still works — it uses descriptive concept names without registry validation. propstore adds structured validation, conflict detection, and cross-paper reasoning on top.

## Schema

The data model is defined in [LinkML](https://linkml.io/) at `schema/concept_registry.linkml.yaml` and `schema/claim.linkml.yaml`. JSON Schema is generated from these for validation. Run `schema/generate.py` to regenerate.

## Dependencies

- [click](https://click.palletsprojects.com/) — CLI framework
- [LinkML](https://linkml.io/) — schema definition and JSON Schema generation
- [PyYAML](https://pyyaml.org/) + [jsonschema](https://python-jsonschema.readthedocs.io/) — YAML loading and validation
- [SymPy](https://www.sympy.org/) — symbolic math for parameterization evaluation, sensitivity analysis, and equation claim validation
- [Z3](https://github.com/Z3Prover/z3) — SMT solver for condition disjointness, SAT-backed extension computation, and MaxSMT conflict resolution
- [Graphviz](https://graphviz.readthedocs.io/) — DOT graph export
- [ast-equiv](../ast-equiv) — algorithm canonicalization and equivalence comparison

**Optional (for embeddings):**
- [litellm](https://github.com/BerriAI/litellm) — unified LLM API for embedding generation and stance classification
- [sqlite-vec](https://github.com/asg017/sqlite-vec) — vector search in SQLite
