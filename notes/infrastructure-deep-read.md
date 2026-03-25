# Infrastructure Deep Read — Scout Report

Date: 2026-03-25
Status: COMPLETE

## Files Read

All 37 specified source files, plus pyproject.toml, schema/generated/ contents,
and sample YAML files from knowledge/concepts/, knowledge/claims/, knowledge/forms/,
knowledge/contexts/, and knowledge/stances/.

---

## 1. Data Flow: YAML Through Build Into Sidecar

### Source YAML Structure

Knowledge lives in `knowledge/` with these subdirectories:
- `concepts/` — one YAML per concept (e.g. `acceptability.yaml`)
- `claims/` — one YAML per paper, containing a `claims:` list (e.g. `Cayrol_2005_...yaml`)
- `contexts/` — one YAML per context (e.g. `ctx_abstract_argumentation.yaml`)
- `forms/` — one YAML per form type (e.g. `boolean.yaml`, `amplitude_ratio.yaml`)
- `stances/` — one YAML per source claim, containing cross-claim stance classifications

Forms are defined in `propstore/forms/` (shipped with the package) OR `knowledge/forms/`
(project data). The distinction is managed by `Repository` which resolves `forms_dir`.
See `resources.py` for the dev-vs-installed detection pattern.

### Build Pipeline (build_sidecar.py)

The pipeline in `build_sidecar()` (line 205-342) is:

1. **Content hash check** — SHA-256 over all YAML inputs + schemas + forms + stances
   (`_content_hash`, line 39-93). If hash matches stored `.hash` file, skip rebuild.

2. **Embedding snapshot** — Before destroying old DB, extract all embedding vectors
   via `extract_embeddings()` (line 240-263). This preserves expensive LLM-generated
   embeddings across rebuilds.

3. **Fresh SQLite build** — Delete old DB, create new one with:
   - `_create_tables` — concept, alias, relationship, parameterization, parameterization_group, form, form_algebra tables
   - `_create_context_tables` — context, context_assumption, context_exclusion
   - `_populate_forms` — loads all form YAMLs into `form` table
   - `_populate_concepts` — each concept gets: id, content_hash, seq, canonical_name, status, domain, definition, kind_type, form, form_parameters (JSON), range_min/max, is_dimensionless, unit_symbol, dates
   - `_populate_aliases` — flattens concept aliases into separate table
   - `_populate_relationships` — concept-to-concept relationships with CEL conditions
   - `_populate_parameterizations` — stores inputs as JSON array, formula, sympy, exactness, conditions
   - `_populate_parameterization_groups` — union-find connected components via `parameterization_groups.py`
   - `_populate_form_algebra` — derives form-level algebraic relationships from parameterizations, validates dimensions with bridgman
   - `_build_fts_index` — FTS5 over concept names, aliases, definitions, conditions

4. **Claim tables** (when claim_files provided):
   - `_create_claim_tables` — claim, claim_stance (with opinion columns), conflicts, claim_fts
   - `_populate_claims` — normalizes concept references (name/alias to ID), generates auto_summary via `description_generator.py`, generates sympy from expressions, computes SI-normalized values, stores canonical AST for algorithms
   - `_populate_conflicts` — runs `detect_conflicts()` AND `detect_transitive_conflicts()`, stores results
   - `_build_claim_fts_index` — FTS5 over claim statements, conditions, expressions
   - `_populate_stances_from_files` — reads stance YAML files and inserts into claim_stance table

5. **Embedding restore** — Restores vectors where content_hash still matches (line 314-324).

6. **Commit and write hash file**.

### Key Transformations During Build

What changes between YAML and sidecar:

| YAML field | Sidecar column | Transformation |
|---|---|---|
| concept references by name/alias | concept_id | Resolved to canonical ID via `_resolve_concept_reference` (build_sidecar.py:1046-1074) |
| claim value (any numeric) | value REAL, value_si REAL | Parsed to float; SI-normalized via pint using form's unit_symbol (build_sidecar.py:977-1004) |
| claim lower_bound/upper_bound | lower_bound_si, upper_bound_si | Same SI normalization |
| equation expression (human text) | sympy_generated TEXT | Auto-generated SymPy via `sympy_generator.py` |
| algorithm body (pseudocode) | canonical_ast TEXT | Parsed and canonicalized via `ast_equiv.canonical_dump` |
| claim conditions (CEL strings) | conditions_cel TEXT (JSON array) | Serialized as JSON |
| concept form_parameters (dict) | form_parameters TEXT | Serialized as JSON |
| parameterization inputs (list) | concept_ids TEXT | Serialized as JSON array |
| inline stances on claims | claim_stance rows | Extracted from claim YAML, deferred until all claims inserted (FK constraint) |
| stance files | claim_stance rows | Loaded from knowledge/stances/ YAML files after claims |
| concept aliases (list of dicts) | alias table rows | Flattened: one row per alias |

---

## 2. What Gets Lost or Transformed During Build

### Definitely Lost

1. **Concept `relationships` field `note`** is stored in the relationship table (build_sidecar.py:650-655), but the **concept `notes` field** (top-level free-text notes on a concept) is NOT stored in the concept table. The concept table has no `notes` column.

2. **Claim `concepts` list** (for observation/mechanism/comparison/limitation claims) — the claim table has `concept_id` (singular) and `target_concept` columns. Multi-concept observation claims store their concept list only in the source YAML; there is no junction table for the many-to-many relationship. The `concept_id` column gets `None` for observation claims (build_sidecar.py:1156-1157 only sets `statement`).

3. **Equation `variables` list** — stored only as `variables_json TEXT` (a JSON blob). Individual variable-concept bindings are not stored in a relational table. This means you cannot SQL-query "which equations reference concept X as a variable" without JSON parsing.

4. **Model claim `equations` and `parameters`** — the model claim type stores only `name` in the sidecar (build_sidecar.py:1161). The model's equation list and parameter list are not stored. They exist only in source YAML.

5. **Claim `description` field** — there is a `description` column in claim table, but `_extract_typed_claim_fields` never populates it from any claim type. Only `auto_summary` (generated) and `notes` get written. The `description` column gets whatever `normalized_claim.get("description")` returns, which is only present if manually authored.

### Transformed (Potentially Lossy)

6. **Numeric value coercion** — claim `value` is coerced to `float` via `_extract_numeric_claim_fields` (build_sidecar.py:1167-1188). Non-numeric values get `None` with a warning. String values for category concepts are silently dropped.

7. **SI normalization can fail silently** — if pint can't convert the unit, the raw value is kept as `value_si` (build_sidecar.py:1000-1004). There's no flag indicating whether SI normalization succeeded or fell back.

8. **SymPy generation is best-effort** — when `sympy_generated` is None and `sympy_error` is non-None, the equation has no machine-parseable form in the sidecar. The system degrades gracefully but the equation is invisible to dimensional analysis and conflict detection.

9. **Concept canonical_name must match filename** — enforced by validate.py:208-210. This means renaming a concept requires changing both the file and the `canonical_name` field.

---

## 3. What the CLI Actually Does vs Architecture

### CLI Structure (cli/__init__.py)

The `pks` CLI (entry point: `propstore.cli:cli`) has these command groups:
- `concept` — concept CRUD
- `context` — context management
- `claim` — claim CRUD
- `form` — form management
- `validate` — run validators
- `build` — build sidecar
- `query` — query the sidecar
- `export-aliases` — export alias list
- `import-papers` — import papers
- `init` — initialize a repository
- `world` — world queries (resolution, value lookup)
- `worldline` — worldline materialization
- `promote` — move proposals to source-of-truth storage

### Architecture Alignment

The six-layer architecture from CLAUDE.md maps to code as follows:

| Layer | Architecture Says | What Code Actually Does |
|---|---|---|
| 1. Source storage | Immutable YAML, never mutated by heuristic | Correct. Build reads YAML, writes SQLite. YAML is read-only during build. `promote` is the only mutation path, and it's explicit. |
| 2. Theory/typing | Forms, dimensions, CEL, Z3 | Fully implemented. `form_utils.py`, `cel_checker.py`, `z3_conditions.py`, `unit_dimensions.py`, `bridgman` integration. |
| 3. Heuristic analysis | Embeddings, LLM stance classification, proposals only | Correct. `embed.py` is query-only. Stance files record `resolution.method: nli_first_pass` with model provenance. Stances live in `knowledge/stances/` (proposal artifacts). |
| 4. Argumentation | Dung AF, ASPIC+, extensions | NOT in the files I read. The `worldline_runner.py` imports from `propstore.argumentation` (line 199) and `propstore.structured_argument` (line 216-217). These modules were not in my read list but clearly exist. The conflict_detector does NOT feed into argumentation — it's a separate build-time analysis. |
| 5. Render | Resolution strategies, world queries, hypotheticals | `worldline_runner.py` implements this. Imports `propstore.world.resolve`, `propstore.world.Environment`, `propstore.world.RenderPolicy`. Multiple reasoning backends: `claim_graph`, `structured_projection`, `atms`. |
| 6. Agent workflow | extract-claims, reconcile, relate, adjudicate | Not visible in these files. Presumably separate CLI commands or scripts. |

### main.py Is a Stub

`main.py` in the project root (line 1-6) just prints "Hello from propstore!" — it is NOT the CLI entry point. The actual entry point is `propstore.cli:cli` as defined in pyproject.toml line 29.

---

## 4. Conflict Detector and Argumentation: Two Separate Systems

### The Disconnect

The conflict detector (`conflict_detector/`) and the argumentation layer (`propstore.argumentation`, `propstore.structured_argument`) are **completely separate systems** that operate at different times and serve different purposes:

**Conflict Detector** (build-time):
- Runs during `_populate_conflicts` in `build_sidecar.py:1274-1304`
- Compares claim pairs within the same concept
- Classifies as CONFLICT, PHI_NODE, OVERLAP, PARAM_CONFLICT, CONTEXT_PHI_NODE
- Results stored in `conflicts` table in sidecar
- Uses Z3 for condition analysis, SymPy for equation canonicalization, AST comparison for algorithms
- Does NOT construct argumentation frameworks
- Does NOT compute extensions
- Does NOT use stances

**Argumentation Layer** (render-time):
- Runs during worldline materialization in `worldline_runner.py:190-276`
- Only activates when `strategy=argumentation` in WorldlinePolicy
- Imports `propstore.argumentation.compute_claim_graph_justified_claims` (line 199)
- Or `propstore.structured_argument.build_structured_projection` (line 216)
- Or ATMS engine (line 250-256)
- Uses `claim_stance` table (which comes from stance YAML files and inline stances)
- Computes justified/defeated claim sets
- These sets then inform conflict resolution

### How They Could Connect (But Don't)

The `conflicts` table stores which claims conflict. The argumentation layer works from
`claim_stance` (which records supports/attacks/contradicts between claims). These are
different data sources:

- `conflicts` table = "these claims have incompatible values for the same concept"
- `claim_stance` table = "this claim supports/attacks/contradicts that claim" (human or LLM classified)

There is no code that converts `conflicts` rows into argumentation framework attacks.
The argumentation layer builds its framework entirely from `claim_stance` data.

### maxsat_resolver.py: Orphaned?

`maxsat_resolver.py` defines `resolve_conflicts()` which takes conflict pairs and claim strengths and returns a maximally consistent subset. However, I found no import of this module in any of the files I read. It may be used by code in `propstore/world/` (which I did not read), or it may be orphaned.

Grep would be needed to confirm whether `maxsat_resolver` is imported anywhere.

---

## 5. Embeddings in the Resolution Pipeline

### Embeddings Are NOT Used in Resolution

Embeddings (`embed.py`) are a standalone heuristic analysis tool. They are:

- Generated via `pks embed` CLI commands (not during build)
- Stored in sqlite-vec virtual tables in the sidecar
- Preserved across rebuilds via snapshot/restore
- Queried via `find_similar()`, `find_similar_agree()`, `find_similar_disagree()`

**No module in the resolution pipeline imports embed.py:**
- `worldline_runner.py` does not import embed
- `conflict_detector/` does not import embed
- `maxsat_resolver.py` does not import embed
- `build_sidecar.py` only imports embed for snapshot/restore during rebuild

### Where Embeddings Are Used

Embeddings are used in the **heuristic analysis layer** (layer 3):
- Stance generation: the stance YAML files record `embedding_model` and `embedding_distance` in their `resolution` metadata (observed in `knowledge/stances/Alchourron_1985_TheoryChange__claim1.yaml`). This means some external workflow uses embedding similarity to find candidate claim pairs for stance classification.
- The `embed.py:_embedding_text_for_claim` function (line 56-61) prioritizes `auto_summary` which is generated during build by `description_generator.py`. This means embeddings depend on the sidecar being built first.

### The Indirect Path

Embeddings influence resolution indirectly:
1. Embeddings find similar claims
2. External workflow (agent layer) classifies stances between similar claims
3. Stances are stored as YAML files in `knowledge/stances/`
4. Build compiles stances into `claim_stance` table
5. Argumentation layer reads `claim_stance` to build frameworks
6. Frameworks determine justified/defeated claims
7. Resolution uses justified set to pick winning claims

This is a long, manual, multi-step pipeline. There is no automated path from "embedding says these are similar" to "argumentation resolves this conflict."

---

## 6. Additional Findings

### Opinion Columns on claim_stance

The `claim_stance` table has Subjective Logic opinion columns (build_sidecar.py:849-858):
```sql
opinion_belief REAL,
opinion_disbelief REAL,
opinion_uncertainty REAL,
opinion_base_rate REAL DEFAULT 0.5,
CHECK (
    opinion_belief IS NULL
    OR abs(opinion_belief + opinion_disbelief + opinion_uncertainty - 1.0) < 0.01
)
```
This implements Josang 2001. The CHECK constraint enforces the opinion tuple sum constraint
with a tolerance of 0.01. These opinion columns are populated from stance YAML `resolution`
metadata (build_sidecar.py:191-198).

### Condition Classification Has Three Tiers

`condition_classifier.py` (line 97-141) uses a tiered approach:
1. **Identical conditions** (sorted string match) -> CONFLICT
2. **Z3 primary path** -> equivalent=CONFLICT, disjoint=PHI_NODE, else OVERLAP
3. **Interval arithmetic fallback** (regex parsing of simple conditions) -> same classification
4. **Last resort** -> OVERLAP (conservative)

### Form Schema Is Minimal but Strict

`schema/generated/form.schema.json` requires only `name` and `dimensionless`. The `kind`
field is optional — if absent, `form_utils.py:kind_type_from_form_name` (line 257-267) uses
a name-based heuristic (only "category", "structural", "boolean" are special; everything
else is QUANTITY).

### claim.schema.json Is Missing

The generated schema directory contains `concept_registry.schema.json`, `form.schema.json`,
and `concept_registry.py`, but I did NOT see `claim.schema.json`. The claim validator
checks for it at `schema/generated/claim.schema.json` (validate_claims.py:117-118) and
skips JSON Schema validation if the file doesn't exist. This means claim validation
currently relies entirely on the Python structural checks, not the JSON Schema.

### Content Hash Scope

The sidecar content hash (`_content_hash`, build_sidecar.py:39-93) covers:
- All concept YAML files (sorted by filename)
- All claim YAML files
- All context YAML files (by filepath bytes)
- All form YAML files
- All stance YAML files
- All generated schema JSON files

This means ANY change to forms, schemas, or stances triggers a full rebuild.
Embedding snapshot/restore mitigates the cost of losing embedding vectors.

### Dependencies: Two Local Packages

`pyproject.toml` (line 42-44) shows two local/custom dependencies:
- `ast-equiv` — local path dependency (`../ast-equiv`), used for algorithm AST comparison
- `bridgman` — git dependency from github.com/ctoth/bridgman, used for dimensional analysis

### pyproject.toml: linkml Listed but Not Obviously Used

`linkml>=1.8` is in dependencies (pyproject.toml:8). The schema directory has `claim.linkml.yaml`
and `concept_registry.linkml.yaml`. The `schema/generate.py` file likely generates JSON schemas
from LinkML. But the actual runtime code uses `jsonschema` directly, not LinkML runtime.

---

## 7. Summary of Key Architectural Observations

1. **Build is a complete recompilation** — no incremental updates. Hash-based skip is the
   only optimization. This is by design: the sidecar is content-hash addressed.

2. **Three separate conflict/resolution systems** exist:
   - `conflict_detector/` (build-time, value comparison, stored in `conflicts` table)
   - `maxsat_resolver.py` (Z3 optimization, possibly orphaned)
   - `propstore.argumentation` + `propstore.structured_argument` (render-time, Dung AF/ASPIC+)

3. **Embeddings are decoupled from everything** — they're a heuristic discovery tool that
   feeds into a manual stance-classification workflow, not an automated pipeline.

4. **The conflict detector and argumentation layer do not share data structures** — conflicts
   table != attack relation. Stances (human/LLM classified) are the actual input to argumentation.

5. **Multi-concept claims lose their concept bindings** — observation claims referencing
   multiple concepts have no relational representation in the sidecar.

6. **Model claims are severely truncated** — only `name` survives into the sidecar; equations
   and parameters lists are lost.

7. **claim.schema.json may be missing** from schema/generated/, meaning JSON Schema
   validation of claims silently does nothing.
