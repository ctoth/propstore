# Propstore Codebase Survey -- Comprehensive Report

## GOAL
Full architectural survey of the propstore codebase: every module, data model, subsystem, data flow, bugs, and innovations.

## Executive Summary

Propstore is a **propositional knowledge store compiler** -- a system that ingests claims from research papers as YAML, validates them against a concept ontology, compiles them into a SQLite sidecar database, and provides a multi-layered query/reasoning system over the compiled knowledge. The system is fundamentally designed around **non-commitment**: it stores conflicting claims without collapsing them, and only resolves conflicts at render time via pluggable resolution strategies including formal argumentation theory (Dung AFs, ASPIC+, bipolar argumentation).

**Scale**: ~55 Python source files, ~15k lines of test code across 33 test files, 250 concept YAML files, 26 claim files from research papers.

---

## 1. Directory Structure

```
propstore/                    # Python package root
  __init__.py                 # empty
  cli/                        # Click CLI layer
    __init__.py               # cli() group, registers all subcommands
    repository.py             # Repository class -- path resolution
    claim.py                  # pks claim {validate,conflicts,compare,embed,similar,relate}
    concept.py                # pks concept {add,alias,rename,deprecate,link,search,list,show,add-value,categories,embed,similar}
    context.py                # pks context {add,list}
    form.py                   # pks form {list,show,add,remove,validate}
    compiler_cmds.py          # pks {validate,build,query,export-aliases,import-papers,world ...}
    init.py                   # pks init
    helpers.py                # file locking, counters, YAML I/O, concept lookup
  world/                      # Render layer -- the "world model"
    __init__.py               # public API re-exports
    types.py                  # protocols (ArtifactStore, BeliefSpace), data classes, enums
    model.py                  # WorldModel -- read-only SQLite reasoner
    bound.py                  # BoundWorld -- condition-bound belief space
    hypothetical.py           # HypotheticalWorld -- in-memory overlay
    value_resolver.py         # ActiveClaimResolver -- shared value/derived resolution
    resolution.py             # resolve() -- resolution strategies
  conflict_detector/          # Conflict detection subsystem
    __init__.py               # detect_conflicts, detect_transitive_conflicts
    models.py                 # ConflictClass enum, ConflictRecord dataclass
    orchestrator.py           # Top-level detect_conflicts dispatcher
    collectors.py             # Group claims by concept/signature
    parameters.py             # Parameter claim conflicts (Z3-optimized partitioning)
    measurements.py           # Measurement claim conflicts
    equations.py              # Equation claim conflicts (SymPy canonicalization)
    algorithms.py             # Algorithm claim conflicts (AST equivalence)
    context.py                # Context-aware conflict classification
  # Theory/typing layer
  cel_checker.py              # CEL expression parser, tokenizer, type-checker
  z3_conditions.py            # CEL-to-Z3 translator, disjointness/equivalence solver
  form_utils.py               # FormDefinition, kind mapping, unit validation
  unit_dimensions.py          # SI dimensional analysis for units
  condition_classifier.py     # Condition pair classification (Z3 primary, interval fallback)
  # Argumentation layer
  argumentation.py            # Stance-to-AF bridge, bipolar support (Cayrol 2005)
  dung.py                     # Dung AF: grounded/preferred/stable/complete extensions
  dung_z3.py                  # Z3-SAT encoded extension computation
  preference.py               # ASPIC+ preference ordering (Modgil & Prakken 2018)
  maxsat_resolver.py          # MaxSMT conflict resolution via z3.Optimize
  stances.py                  # VALID_STANCE_TYPES vocabulary
  # Derivation/analysis
  propagation.py              # SymPy parameterization evaluation
  param_conflicts.py          # Single-hop and multi-hop transitive conflict detection
  parameterization_groups.py  # Union-find connected components
  sensitivity.py              # Partial derivative / elasticity analysis
  # Utility
  sympy_generator.py          # Human-readable math -> SymPy expression
  equation_comparison.py      # Equation canonicalization and signature
  value_comparison.py         # Numeric interval comparison
  description_generator.py    # Auto-generate human-readable claim descriptions
  graph_export.py             # DOT/JSON knowledge graph export
  embed.py                    # Embedding generation/storage via litellm + sqlite-vec
  relate.py                   # LLM-based epistemic stance classification (two-pass NLI)
  resources.py                # Resource loading (dev vs installed mode)
  validate.py                 # Concept validation
  validate_claims.py          # Claim validation
  validate_contexts.py        # Context validation + ContextHierarchy
  build_sidecar.py            # SQLite sidecar builder

knowledge/                    # Live knowledge base
  concepts/                   # 250 YAML concept files
    .counters/                # global.next counter with file locking
  claims/                     # 26 YAML claim files (from papers)
  contexts/                   # Context YAML files
  forms/                      # (empty -- forms live in top-level forms/)
  sidecar/                    # propstore.sqlite (compiled)
  stances/                    # LLM-generated stance files

forms/                        # 16 form definition YAML files
schema/                       # LinkML schemas + generated JSON Schema
tests/                        # 33 test files, ~15k lines
```

---

## 2. Data Model

### 2.1 Concepts (knowledge/concepts/*.yaml)

A concept is a named entity in the ontology. Each YAML file contains:

- **id**: `concept<N>` (e.g., `concept183`)
- **canonical_name**: matches filename (e.g., `argumentation_framework`)
- **status**: `proposed` | `active` | `deprecated`
- **definition**: human-readable text
- **domain**: domain string (e.g., `argumentation`, `speech`)
- **form**: references a form YAML (e.g., `structural`, `category`, `ratio`)
- **form_parameters**: optional dict (e.g., `{values: [val1, val2]}` for categories)
- **aliases**: list of `{name, source, note?}` dicts
- **relationships**: list of `{type, target, source?, note?, conditions?}`
  - Types: `broader`, `narrower`, `related`, `component_of`, `derived_from`, `contested_definition`
- **parameterization_relationships**: list of `{inputs, formula?, sympy?, exactness, conditions?, canonical_claim?}`
- **range**: optional `[min, max]` bounds
- **replaced_by**: concept ID (for deprecated concepts)

Key: the `canonical_name` MUST match the filename. IDs are globally unique, auto-incremented via file-locked counter.

Observed at: `propstore/validate.py` lines 73-377, `propstore/cli/concept.py` lines 119-773.

### 2.2 Claims (knowledge/claims/*.yaml)

Claims are propositional assertions extracted from research papers. Each file contains:

- **source**: `{paper, extraction_model?, extraction_date?}`
- **claims**: list of claim dicts, each with:
  - **id**: `<paper>:<local_id>` (e.g., `Dung_1995_AcceptabilityArguments:claim1`)
  - **type**: one of `parameter`, `equation`, `observation`, `measurement`, `algorithm`, `model`, `mechanism`, `comparison`, `limitation`
  - **provenance**: `{paper, page, section?}`
  - **conditions**: list of CEL expression strings
  - **context**: optional context ID
  - **stances**: inline epistemic relationships to other claims

Type-specific fields:
- **parameter**: `concept`, `value`, `unit`, `lower_bound`, `upper_bound`, `uncertainty`, `uncertainty_type`, `sample_size`
- **equation**: `expression`, `sympy?`, `variables` (list of `{symbol, concept, role}`)
- **observation**: `statement`, `concepts` (list of concept IDs)
- **measurement**: `target_concept`, `measure`, `value`, `unit`, `listener_population`, `methodology`
- **algorithm**: `body` (Python expression), `variables`, `concept`, `stage`
- **model**: `name`, `equations`, `parameters`

Observed at: `propstore/validate_claims.py` lines 100-558.

### 2.3 Forms (forms/*.yaml)

Forms define measurement types and their dimensional structure:

- **name**: must match filename
- **kind**: `quantity` | `category` | `boolean` | `structural` (or inferred from name)
- **unit_symbol**: primary unit (e.g., `Hz`, `Pa`)
- **dimensions**: SI dimension exponents (e.g., `{T: -1}` for frequency)
- **dimensionless**: boolean
- **common_alternatives**: list of `{unit, factor?}` for unit conversion
- **extra_units**: list of `{symbol, dimensions}` for domain-specific units
- **parameters**: optional parameter schema for `form_parameters`

Note: Many form files are minimal stubs (e.g., `forms/frequency.yaml` contains only `name: frequency`). This is a code smell -- the form validation via JSON schema (`schema/generated/form.schema.json`) and dimensional analysis (`unit_dimensions.py`) exists but many forms lack dimensions data.

Observed at: `propstore/form_utils.py` lines 17-257, `forms/frequency.yaml` line 1.

### 2.4 Contexts (knowledge/contexts/*.yaml)

Contexts model research traditions or theoretical frameworks:

- **id**: context identifier
- **name**: display name
- **description**: text
- **inherits**: parent context ID (single inheritance)
- **excludes**: list of mutually exclusive context IDs
- **assumptions**: list of CEL expressions (inherited through chain)

The ContextHierarchy class provides: ancestor chain traversal, effective assumption aggregation, mutual exclusion checking, and visibility queries.

Observed at: `propstore/validate_contexts.py` lines 1-154.

### 2.5 Stances (knowledge/stances/*.yaml)

Stances are epistemic relationships between claims, generated by the `pks claim relate` command (LLM-based NLI classification):

- **source_claim**: claim ID
- **classification_model**: LLM model used
- **classification_date**: date string
- **stances**: list of `{target, type, strength, note, conditions_differ, resolution}`

Stance types (from `stances.py` line 5-7):
- **rebuts**: directly contradicts conclusion
- **undercuts**: attacks inference method (preference-independent defeat)
- **undermines**: weakens premise/evidence quality
- **supports**: corroborating evidence
- **explains**: mechanistic explanation
- **supersedes**: replaces entirely (preference-independent defeat)
- **none**: no relationship

### 2.6 Provenance

Every claim carries provenance: `{paper, page, section?}`. The paper field matches a directory name in `papers/`. Extraction metadata (model, date) lives at the claim-file level. The content-hash system (`build_sidecar.py` lines 39-93) tracks all semantic inputs for cache invalidation.

---

## 3. Storage Layer

### 3.1 Source Storage: YAML Files

All source-of-truth data lives in YAML files under `knowledge/`. This is immutable except by explicit user action. The system never writes to source files from heuristic/LLM output -- those go to separate directories (stances/).

### 3.2 Compiled Sidecar: SQLite

`knowledge/sidecar/propstore.sqlite` is a content-hash-addressed compiled database rebuilt when inputs change. Tables:

**Core tables** (`build_sidecar.py` lines 326-385):
- `concept` -- id, content_hash, seq, canonical_name, status, domain, definition, kind_type, form, form_parameters (JSON), range_min, range_max, is_dimensionless, unit_symbol, dates
- `alias` -- concept_id, alias_name, source
- `relationship` -- source_id, type, target_id, conditions_cel (JSON), note
- `parameterization` -- output_concept_id, concept_ids (JSON array), formula, sympy, exactness, conditions_cel
- `parameterization_group` -- concept_id, group_id (connected components)

**Claim tables** (`build_sidecar.py` lines 592-677):
- `claim` -- id, content_hash, seq, type, concept_id, value, bounds, uncertainty, unit, conditions_cel, statement, expression, sympy_generated, body, canonical_ast, variables_json, stage, source_paper, provenance, context_id
- `claim_stance` -- claim_id, target_claim_id, stance_type, strength, conditions_differ, note, resolution metadata (model, method, confidence, embedding distance, pass number)
- `conflicts` -- concept_id, claim pairs, warning_class, conditions, values, derivation_chain

**FTS5 indexes**: `concept_fts` (name, aliases, definition, conditions), `claim_fts` (statement, conditions, expression)

**Context tables**: `context`, `context_assumption`, `context_exclusion`

**Embedding tables** (optional, created by `embed.py`):
- `embedding_model` -- model_key, model_name, dimensions, created_at
- `embedding_status` / `concept_embedding_status` -- tracking which entities have current embeddings
- `claim_vec_<model_key>` / `concept_vec_<model_key>` -- sqlite-vec virtual tables for KNN search

### 3.3 Content-Hash Addressing

The sidecar is rebuilt only when the SHA-256 hash of all semantic inputs changes (`build_sidecar.py` lines 39-93). Inputs include: concept files, claim files, context files, form files, stance files, and JSON schemas. The hash is stored at `propstore.sqlite.hash`.

### 3.4 Embedding Preservation

On rebuild, embeddings are snapshot/restored to avoid expensive re-computation (`build_sidecar.py` lines 234-305). The system extracts all embedding vectors before rebuild, then restores those whose content_hash hasn't changed.

---

## 4. CLI (`pks`)

Entry point: `propstore.cli:cli` (pyproject.toml line 24).

### Top-level commands:
- `pks init [directory]` -- bootstrap knowledge/ structure, seed forms
- `pks validate` -- validate all concepts, claims, forms, contexts
- `pks build [-o path] [--force]` -- validate + compile sidecar + detect conflicts
- `pks query <SQL>` -- raw SQL against sidecar
- `pks export-aliases [--format text|json]` -- dump alias table
- `pks import-papers --papers-root <path>` -- import claims from paper corpus

### Concept management:
- `pks concept add --domain X --name Y` -- create concept (auto-ID, file-locked counter)
- `pks concept alias <id> --name N --source S` -- add alias
- `pks concept rename <id> --name N` -- rename (updates CEL references, git mv)
- `pks concept deprecate <id> --replaced-by <id>` -- mark deprecated
- `pks concept link <src> <type> <tgt>` -- add relationship
- `pks concept search <query>` -- FTS5 or YAML grep search
- `pks concept list [--domain D] [--status S]`
- `pks concept show <id_or_name>`
- `pks concept add-value <name> --value V` -- add to category value set
- `pks concept categories [--json]` -- list category concepts and values
- `pks concept embed --model M [--all]` -- generate embeddings
- `pks concept similar <id> [--agree] [--disagree]` -- find similar by embedding

### Claim management:
- `pks claim validate [--dir D]` -- validate claim files
- `pks claim validate-file <path>` -- validate single file
- `pks claim conflicts [--concept C] [--class CLASS]` -- detect conflicts
- `pks claim compare <id_a> <id_b> [-b key=val]` -- AST equivalence comparison
- `pks claim embed --model M [--all]` -- generate embeddings
- `pks claim similar <id> [--agree] [--disagree]` -- find similar by embedding
- `pks claim relate <id> --model M [--all]` -- LLM stance classification

### World queries:
- `pks world status` -- concept/claim/conflict counts
- `pks world query <concept_id>` -- show claims for concept
- `pks world bind [key=val ...] [concept_id]` -- show active claims under bindings
- `pks world explain <claim_id>` -- show stance chain
- `pks world algorithms [--stage S] [--concept C]` -- list algorithm claims
- `pks world derive <concept_id> [key=val ...]` -- derive via parameterization
- `pks world resolve <concept_id> --strategy S [key=val ...]` -- resolve conflicts
- `pks world extensions [--semantics S] [key=val ...]` -- show argumentation extensions
- `pks world hypothetical [--remove id] [--add JSON]` -- what-if scenarios
- `pks world chain <concept_id> [key=val ...]` -- traverse parameter space
- `pks world export-graph [--format dot|json]` -- knowledge graph export
- `pks world sensitivity <concept_id> [key=val ...]` -- sensitivity analysis
- `pks world check-consistency [--transitive]` -- conflict checking

---

## 5. Theory/Typing Layer

### 5.1 CEL Type System (`cel_checker.py`)

A hand-written recursive descent parser and type checker for a subset of CEL (Common Expression Language). The parser produces an AST (NameNode, LiteralNode, BinaryOpNode, UnaryOpNode, InNode, TernaryNode) and the type checker validates against a concept registry.

**Kind types**: QUANTITY (numeric), CATEGORY (enum), BOOLEAN, STRUCTURAL (cannot appear in CEL).

**Type rules enforced** (lines 460-604):
- Category concepts cannot be in arithmetic or ordering comparisons
- Boolean concepts cannot be in arithmetic
- Quantity concepts cannot be compared to string literals
- Category values checked against known value sets (warning if extensible, error if not)

### 5.2 Z3 Condition Solver (`z3_conditions.py`)

Translates CEL ASTs to Z3 expressions for formal reasoning about condition compatibility:
- `z3.Real` for quantity concepts
- `z3.EnumSort` for category concepts (finite domain)
- `z3.Bool` for boolean concepts

**Key operations**:
- `are_disjoint(A, B)` -- conjunction is UNSAT (claims can't both be active)
- `are_equivalent(A, B)` -- both `A and not B` and `B and not A` are UNSAT
- `partition_equivalence_classes(list)` -- O(n*k) equivalence partitioning

### 5.3 Form System (`form_utils.py`)

Forms define measurement types with optional dimensional analysis. The FormDefinition dataclass carries: name, kind, unit_symbol, allowed_units, is_dimensionless, dimensions, parameters, extra_units.

### 5.4 Dimensional Analysis (`unit_dimensions.py`)

Resolves unit strings to SI dimension dicts (e.g., `Hz` -> `{T: -1}`). Uses a shipped lookup table from physgen (`_resources/physgen_units.json`) plus form-declared extra_units. Checks dimensional compatibility between claim units and concept forms.

### 5.5 Parameterization Groups (`parameterization_groups.py`)

Union-find algorithm builds connected components from parameterization relationships. Each component is a "parameter space group" -- concepts linked by algebraic/functional relationships that can be traversed to derive values.

---

## 6. Argumentation Layer

### 6.1 Dung Abstract Argumentation (`dung.py`)

Implements Dung 1995 -- the core formal argumentation theory:

- **ArgumentationFramework**: `(arguments: frozenset[str], defeats: frozenset[(str,str)], attacks: frozenset[(str,str)] | None)`
- **Grounded extension**: least fixed point of characteristic function F (lines 106-119)
- **Complete extensions**: fixed points of F that are admissible (lines 122-148)
- **Preferred extensions**: maximal complete extensions (lines 151-170)
- **Stable extensions**: conflict-free sets that defeat all outsiders (lines 173-201)

Key: Modgil & Prakken 2018 Def 14 is implemented -- conflict-free uses **attacks** (pre-preference), defense uses **defeats** (post-preference). This is NOT standard Dung but the ASPIC+ refinement. See `dung.py` lines 45-56, 84-103.

### 6.2 Z3 Extension Computation (`dung_z3.py`)

SAT-encoded alternatives to brute-force extension enumeration. Encodes conflict-free, defense, and completeness constraints as Z3 formulas, then enumerates solutions with blocking clauses. Also provides `credulously_accepted()` and `skeptically_accepted()` queries.

### 6.3 ASPIC+ Preference Ordering (`preference.py`)

Implements Modgil & Prakken 2018 Def 9 and Def 19:

- **Elitist comparison**: set_a < set_b iff EXISTS x in a s.t. FORALL y in b, x < y
- **Democratic comparison**: set_a < set_b iff FORALL x in a EXISTS y in b, x < y
- **Defeat rules**: undercuts/supersedes always succeed; rebuts/undermines succeed iff attacker is NOT strictly weaker

**Claim strength** (lines 56-87): Composite score from sample_size (log-scaled), uncertainty (inverse), and confidence. Missing metadata is neutral (1.0 default).

### 6.4 Argumentation Bridge (`argumentation.py`)

Converts raw stance data into a Dung AF:
1. Load stances between active claims above confidence threshold
2. Classify into attacks (rebuts, undercuts, undermines, supersedes) and supports (supports, explains)
3. Filter attacks through preference ordering to get defeats
4. Compute **Cayrol 2005 derived defeats** from bipolar support chains:
   - Supported defeat: A supports* B, B defeats C => A defeats C
   - Indirect defeat: A defeats B, B supports* C => A defeats C
5. Return AF with both attacks and defeats

This is a genuine implementation of bipolar argumentation per Cayrol 2005 -- unusual in a knowledge management tool.

### 6.5 MaxSMT Resolution (`maxsat_resolver.py`)

Alternative to extension-based resolution: uses z3.Optimize with weighted soft constraints to find the maximally consistent claim subset. Each claim gets a Boolean variable; hard constraints prevent conflicting pairs; soft constraints prefer keeping claims weighted by strength.

---

## 7. Render Layer

### 7.1 WorldModel (`world/model.py`)

Read-only reasoner over the compiled sidecar. Implements the `ArtifactStore` protocol. Key features:
- Lazy Z3 solver initialization
- Lazy context hierarchy loading
- FTS5 search, embedding-based similarity
- BFS stance graph traversal (`explain()`)
- Parameterization group membership queries
- Chain query (iterative resolution through parameter space)

### 7.2 BoundWorld (`world/bound.py`)

A belief space view under specific condition bindings and optional context scoping:
- Converts keyword bindings to CEL conditions (e.g., `domain='speech'` -> `domain == 'speech'`)
- Appends context-inherited assumptions to binding conditions
- **is_active(claim)**: checks context membership (if context_visible set exists) + CEL condition compatibility via Z3 disjointness check
- **value_of(concept_id)**: classifies as `determined` (single value), `conflicted` (multiple distinct values), `no_claims`
- **derived_value()**: delegates to ActiveClaimResolver
- **resolved_value()**: delegates to resolution strategies
- **conflicts()**: revalidates conflicts against current belief space (both stored + recomputed)

### 7.3 ActiveClaimResolver (`world/value_resolver.py`)

Shared resolution logic for BoundWorld and HypotheticalWorld:
- **value_of_from_active()**: handles algorithm claims specially -- uses AST equivalence checking (`ast_equiv.compare`) to determine if multiple algorithm claims are equivalent
- **derived_value()**: evaluates SymPy parameterization expressions with resolved input values

### 7.4 Resolution Strategies (`world/resolution.py`)

Four strategies for resolving conflicted concepts:
- **RECENCY**: pick claim with most recent provenance date
- **SAMPLE_SIZE**: pick claim with largest sample_size
- **ARGUMENTATION**: build AF, compute extension, pick sole survivor
- **OVERRIDE**: explicit user-specified winner

RenderPolicy dataclass allows per-concept strategy overrides.

### 7.5 HypotheticalWorld (`world/hypothetical.py`)

In-memory overlay on a BoundWorld. Supports:
- Removing claims by ID
- Adding synthetic claims (SyntheticClaim dataclass)
- diff() method comparing base vs hypothetical value_of for all affected concepts

### 7.6 Sensitivity Analysis (`sensitivity.py`)

Computes partial derivatives and elasticities for parameterized concepts:
- Parses SymPy expression, resolves input values
- Computes df/dx for each input
- Computes elasticity: (df/dx * x/f) -- normalized sensitivity
- Sorts by |elasticity| descending

---

## 8. Agent Workflow Layer

### 8.1 Embedding (`embed.py`)

Generates and stores embeddings via litellm + sqlite-vec:
- Generic `_embed_entities()` handles both claims and concepts
- Content-hash-based skip logic avoids re-embedding unchanged entities
- Multi-model support with agree/disagree queries (intersection/symmetric difference across models)
- Snapshot/restore across sidecar rebuilds

### 8.2 Relate (`relate.py`)

LLM-based epistemic stance classification:
- Two-pass NLI: first pass classifies all similar pairs, second pass re-examines "none" verdicts for highly similar claims (below distance threshold)
- Confidence scoring: pass 1 strong=0.95, pass 2 strong=0.70
- Async concurrency via `asyncio.gather` with semaphore
- Writes stance YAML files to knowledge/stances/

### 8.3 Import Papers (`cli/compiler_cmds.py` lines 271-336)

Imports claims from a papers/ corpus:
- Reads claims.yaml from each paper directory
- Prefixes claim IDs with paper name for global uniqueness
- Also prefixes inline stance targets

---

## 9. Build System

`pks build` executes the following pipeline (`cli/compiler_cmds.py` lines 83-204):

1. **Validate forms** against JSON Schema
2. **Validate concepts** -- required fields, ID uniqueness, name-filename match, relationship targets, parameterization inputs, CEL type-checking, form-parameter validation
3. **Validate contexts** -- required fields, reference integrity, cycle detection
4. **Validate claims** -- JSON Schema, required fields, ID format/uniqueness, provenance, concept references, CEL conditions, type-specific validation (parameter units, equation parsing, algorithm AST parsing, measurement fields), stance validation
5. **Build sidecar** -- content-hash check, snapshot embeddings, create tables, populate concepts/aliases/relationships/parameterizations/groups/FTS/contexts/claims/stances/conflicts, restore embeddings, commit
6. **Summary** via WorldModel roundtrip

---

## 10. Conflict Detection

### 10.1 Direct Conflicts (`conflict_detector/`)

Four specialized detectors:
- **Parameter conflicts** (`parameters.py`): Z3-optimized equivalence partitioning when >2 claims, pairwise fallback. Uses value interval comparison.
- **Measurement conflicts** (`measurements.py`): groups by (target_concept, measure), listener_population differences create PHI_NODEs
- **Equation conflicts** (`equations.py`): groups by variable signature, SymPy canonicalization for equivalence
- **Algorithm conflicts** (`algorithms.py`): groups by concept, ast_equiv comparison for equivalence

### 10.2 Condition Classification

**Z3 primary path**: equivalent conditions -> CONFLICT, disjoint -> PHI_NODE, overlapping -> OVERLAP.
**Interval arithmetic fallback**: regex-based condition parsing into numeric/discrete constraints.

### 10.3 Transitive Conflicts (`param_conflicts.py`)

Multi-hop chain detection: iterative forward propagation through parameterization chains within connected components. Detects when direct claims disagree with values derived through 2+ hop chains.

### 10.4 Context-Aware Classification

Claims in mutually exclusive contexts or non-visible contexts are classified as CONTEXT_PHI_NODE instead of CONFLICT.

---

## 11. Tests

14,787 lines across 33 test files. Major test files:

| File | Lines | What it tests |
|------|-------|---------------|
| test_world_model.py | 1753 | WorldModel, BoundWorld, chain queries, resolution |
| test_validate_claims.py | 1440 | All claim type validation |
| test_build_sidecar.py | 1360 | Sidecar compilation, embedding snapshot/restore |
| test_cli.py | 1179 | CLI command integration tests |
| test_contexts.py | 1103 | Context hierarchy, visibility, assumptions |
| test_conflict_detector.py | 1046 | All conflict detection paths |
| test_validator.py | 743 | Concept validation |
| test_z3_conditions.py | 642 | Z3 condition solver |
| test_cel_checker.py | 544 | CEL parser and type checker |
| test_sensitivity.py | 511 | Sensitivity analysis |
| test_graph_export.py | 458 | Knowledge graph export |
| test_bipolar_argumentation.py | 443 | Cayrol 2005 bipolar support |
| test_form_dimensions.py | 429 | Form and unit dimensional analysis |
| test_dung.py | 387 | Dung AF extensions |
| test_argumentation_integration.py | 335 | End-to-end argumentation |
| test_claim_notes.py | 339 | Claim notes/description generation |
| test_preference.py | 232 | ASPIC+ preference ordering |
| test_property.py | 190 | Hypothesis property-based tests |
| test_dung_z3.py | 178 | Z3 extension computation |
| test_render_time_filtering.py | 153 | Render-time condition filtering |
| test_render_contracts.py | 56 | Protocol contracts verification |

Notable: `tests/conftest.py` (91 lines) provides shared fixtures including `tmp_repo`, `sample_concept_dir`, `sample_claim_files`, `concept_registry`, and `built_sidecar`.

---

## 12. Bugs, Issues, and Code Smells

### 12.1 Form Definition Stubs

Most form YAML files are minimal stubs containing only `name: <form>`. For example, `forms/frequency.yaml` is just `name: frequency` (1 line). The system has dimensional analysis infrastructure but many forms lack the `dimensions`, `unit_symbol`, or `kind` fields needed to use it. The `form_utils.py` falls back to name-based heuristics (`kind_type_from_form_name` at line 142) when explicit kind is missing.

Observed at: `forms/frequency.yaml` line 1, `forms/category.yaml` line 1.

### 12.2 Module-level Mutable Cache

`form_utils.py` line 30 has a module-level mutable dict `_form_cache`. This is fine for single-process use but would be a problem if the module were used in a long-running server or tests that modify form files between calls. The cache is never invalidated.

### 12.3 Broad Exception Handling in Sidecar Build

`build_sidecar.py` lines 250-255 catches `Exception` broadly for embedding snapshot failures. The comment explains this is intentional (graceful degradation), but it could mask bugs during development.

### 12.4 SQL Injection Surface

`world/model.py` lines 216-220 constructs SQL with f-string placeholders for `IN` clauses: `f"SELECT * FROM claim WHERE id IN ({placeholders})"`. While the actual values are passed as parameters (safe), the `# noqa: S608` comments acknowledge the pattern looks suspicious.

### 12.5 Empty __init__.py

`propstore/__init__.py` is empty (no public API exports). Users must import from submodules directly.

### 12.6 Duplicate _build_z3_solver

`conflict_detector/parameters.py` lines 25-30 has its own `_build_z3_solver` function, while the orchestrator in `conflict_detector/orchestrator.py` lines 69-74 has `_build_condition_solver` doing the same thing. The orchestrator now passes the solver to detectors, making the one in parameters.py a dead code path (it's only used as fallback when solver=None).

---

## 13. Innovations and Distinguishing Features

### 13.1 Non-Commitment Discipline

The core design principle is that the system **never collapses disagreement in storage**. Multiple rival claims can coexist for the same concept. Resolution only happens at render time, under an explicit policy. This is deeply unusual -- most knowledge management systems force a single canonical value.

### 13.2 Formal Argumentation Theory in Production

This is not a toy implementation. The system implements:
- Dung 1995 (grounded/preferred/stable/complete extensions)
- Modgil & Prakken 2018 ASPIC+ (attack vs defeat distinction, preference ordering)
- Cayrol 2005 bipolar argumentation (support-derived defeats)
- Z3-SAT encoding for scalable extension computation
- MaxSMT for weighted conflict resolution

These are used in production resolution strategies, not just academic exercises.

### 13.3 CEL-to-Z3 Condition Reasoning

The system has a full pipeline: parse CEL expressions -> type-check against concept ontology -> translate to Z3 -> solve for disjointness/equivalence. This enables formal reasoning about when claims from different experimental conditions actually conflict.

### 13.4 Content-Hash-Addressed Compilation

The sidecar is a compiled artifact that caches all expensive computation (conflict detection, FTS indexes, parameterization groups). The content-hash system means it's rebuilt only when semantic inputs change, and embeddings are preserved across rebuilds.

### 13.5 Multi-Model Embedding Consensus

The agree/disagree queries across multiple embedding models are innovative: "similar under ALL models" (intersection) and "similar under SOME but not ALL" (symmetric difference) provide a principled way to identify where different embedding spaces agree or disagree about claim similarity.

### 13.6 Two-Pass NLI Stance Classification

The relate system does a first-pass LLM classification, then re-examines "none" verdicts for highly-similar pairs (by embedding distance). This reduces false negatives in epistemic relationship detection.

### 13.7 Hypothetical Reasoning

The HypotheticalWorld provides counterfactual queries: "what would change if we removed claim X and added claim Y?" This is implemented as a zero-copy overlay on BoundWorld.

### 13.8 Protocol-Based Architecture

The `ArtifactStore` and `BeliefSpace` protocols (`world/types.py` lines 90-146) define clean interfaces. WorldModel implements ArtifactStore (read-only store), BoundWorld and HypotheticalWorld implement BeliefSpace (condition-filtered views). This enables testing with mock stores.

---

## 14. Data Flow Summary

```
YAML Sources (knowledge/)
    |
    v
Validators (validate.py, validate_claims.py, validate_contexts.py)
    |
    v
Sidecar Builder (build_sidecar.py) --- content-hash skip check
    |
    +---> Conflict Detector (conflict_detector/) --- Z3 condition reasoning
    |
    +---> FTS5 Indexes
    |
    +---> Parameterization Groups (union-find)
    |
    v
SQLite Sidecar (propstore.sqlite)
    |
    v
WorldModel (world/model.py) --- ArtifactStore protocol
    |
    +---> bind() ---> BoundWorld --- CEL condition filtering via Z3
    |                    |
    |                    +---> value_of() --- determined/conflicted/no_claims
    |                    +---> derived_value() --- SymPy evaluation
    |                    +---> resolved_value() --- strategy dispatch
    |                    +---> HypotheticalWorld --- counterfactual overlay
    |
    +---> Argumentation Pipeline:
    |       stances --> preference filter --> Dung AF --> extensions
    |
    +---> Embeddings (litellm + sqlite-vec) --> similarity queries
    |
    +---> Relate (LLM NLI) --> stance YAML files --> next build cycle
```

---

## FILES READ
Every .py file in propstore/, tests/ file listing, forms/, knowledge/ samples, pyproject.toml, schema/ listing.

## DONE
Complete survey of all 55 source modules, data model, CLI, storage, theory, argumentation, render, agent workflow, build system, tests, bugs, and innovations.
