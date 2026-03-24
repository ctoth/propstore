# Code Review: Propstore Core Data Model and Storage Layer

Scout report. 2026-03-23.

## 1. Data Structures

### 1.1 Concepts (the ontology layer)

**Schema**: `/c/Users/Q/code/propstore/schema/concept_registry.linkml.yaml`
**Loader**: `/c/Users/Q/code/propstore/propstore/validate.py` lines 28-33 (`LoadedConcept` dataclass)

A concept is a named quantity, phenomenon, or structural category. One YAML file per concept in `knowledge/concepts/`. Currently 250 concept YAML files.

Core fields (from LinkML schema):
- `id` -- format `conceptN` (e.g. `concept183`), enforced by regex at `validate.py:68`
- `canonical_name` -- must match filename (`validate.py:200-202`)
- `status` -- lifecycle: proposed/accepted/deprecated (deprecated requires `replaced_by`)
- `definition` -- 1-3 sentences
- `form` -- reference to a form definition file in `knowledge/forms/`
- `domain` -- short domain tag
- `aliases` -- list of {name, source, note}
- `relationships` -- typed edges: broader, narrower, related, component_of, derived_from, contested_definition
- `parameterization_relationships` -- algebraic relationships between concepts with formula, inputs, exactness, conditions

**Forms** (the type system for concepts): 15 form files in `knowledge/forms/`. Each defines a dimensional type: structural, boolean, category, or quantity subtypes (frequency, pressure, ratio, etc.). Loaded via `FormDefinition` dataclass at `form_utils.py:17-28`. Cached by (forms_dir, form_name) at `form_utils.py:30`.

**Contexts**: Currently 1 context file (`ctx_abstract_argumentation.yaml`). Schema at `validate_contexts.py`. Supports inheritance chains, assumptions (CEL expressions), and mutual exclusion. `ContextHierarchy` class (`validate_contexts.py:101-153`) provides query interface for ancestors, effective assumptions, exclusion, and visibility.

### 1.2 Claims (the propositional layer)

**Schema**: `/c/Users/Q/code/propstore/schema/claim.linkml.yaml`
**Loader**: `/c/Users/Q/code/propstore/propstore/validate_claims.py` lines 41-47 (`LoadedClaimFile` dataclass)

A claim file is one YAML per paper, containing extraction metadata and a list of claims. Currently 26 claim files.

Claim types (9 total, from `claim.linkml.yaml:18-39`):
- **parameter** -- numeric value binding for a concept with unit, uncertainty, sample_size
- **equation** -- mathematical relationship with expression, sympy, variable bindings
- **observation** -- qualitative statement with concept references
- **model** -- parameterized equation system (multi-equation)
- **measurement** -- perceptual/behavioral measurement (JND, threshold, rating)
- **algorithm** -- Python function body with AST canonicalization
- **mechanism** -- causal/architectural argument
- **comparison** -- contrastive claim against prior work
- **limitation** -- scope boundary or failure mode

Each claim has provenance (paper, page, section, quote_fragment) and optional CEL conditions.

### 1.3 Stances (the epistemic relations layer)

**Vocabulary**: `/c/Users/Q/code/propstore/propstore/stances.py` -- 7 types: rebuts, undercuts, undermines, supports, explains, supersedes, none

Grounded in Pollock 1987 (rebutting vs undercutting defeat) and Dung 1995 (attack relations). The `none` type exists for logged-but-irrelevant relationships.

Stances live in two places:
1. Inline on claims (in claim YAML files, under `stances` key)
2. Standalone stance files in `knowledge/stances/` -- one file per source claim, named `{paper}__{claimN}.yaml`

Currently ~400 stance files in `knowledge/stances/`. Each contains classification provenance: model, embedding_model, embedding_distance, pass_number, confidence.

### 1.4 Conflicts (computed at build time)

Stored in SQLite `conflicts` table (`build_sidecar.py:644-656`). Detected by `conflict_detector.detect_conflicts` and `detect_transitive_conflicts`. Each conflict record links two claims by concept, with warning_class, conditions, values, and derivation_chain.

### 1.5 Sidecar (the compiled database)

SQLite database built by `build_sidecar.py`. Content-hash addressed -- only rebuilt when semantic inputs change (`build_sidecar.py:37-91`).

Tables:
- `concept` (id, content_hash, seq, canonical_name, status, domain, definition, kind_type, form, form_parameters, range_min, range_max, is_dimensionless, unit_symbol, dates)
- `alias` (concept_id, alias_name, source)
- `relationship` (source_id, type, target_id, conditions_cel, note)
- `parameterization` (output_concept_id, concept_ids, formula, sympy, exactness, conditions_cel)
- `parameterization_group` (concept_id, group_id) -- connected components
- `context`, `context_assumption`, `context_exclusion`
- `claim` (33 columns -- id, content_hash, seq, type, concept_id, value, bounds, uncertainty, unit, conditions_cel, statement, expression, sympy, name, target_concept, measure, methodology, notes, description, auto_summary, body, canonical_ast, variables_json, stage, source_paper, provenance, context_id)
- `claim_stance` (claim_id, target_claim_id, stance_type, strength, conditions_differ, note, resolution provenance)
- `conflicts` (concept_id, claim_a_id, claim_b_id, warning_class, conditions, values, derivation_chain)
- FTS5 indexes: `concept_fts` (over names, aliases, definitions, conditions), `claim_fts` (over statements, conditions, expressions)

## 2. Data Flow

### 2.1 Ingestion

Source of truth is YAML files in `knowledge/`. The ingestion pipeline:

1. **Load**: `load_concepts()` (`validate.py:60-65`), `load_claim_files()` (`validate_claims.py:50-55`), `load_contexts()` (`validate_contexts.py:23-30`) read YAML from disk.

2. **Validate**: Multi-pass validation with errors (hard stop) and warnings (advisory):
   - Concepts: required fields, ID format/uniqueness, filename match, form existence, relationship targets, parameterization inputs, CEL type-checking, deprecation chains (`validate.py:93-371`)
   - Claims: JSON Schema validation, ID format/uniqueness, provenance, context references, CEL conditions, type-specific validation (parameter/equation/observation/model/measurement/algorithm), stance validation (`validate_claims.py:98-241`)
   - Contexts: required fields, ID uniqueness, inheritance references, exclusion references, cycle detection (`validate_contexts.py:33-98`)
   - Forms: JSON Schema validation, dimensions/dimensionless consistency, name/filename match (`form_utils.py:212-256`)

3. **Build sidecar**: `build_sidecar()` (`build_sidecar.py:198-319`):
   - Compute content hash of all inputs (concepts, claims, contexts, forms, stances, schemas)
   - Skip rebuild if hash matches existing sidecar
   - Snapshot embeddings from old sidecar before rebuild
   - Create fresh SQLite with all tables, indexes, FTS
   - Populate concepts, aliases, relationships, parameterizations, parameterization groups
   - Populate contexts
   - Populate claims (with auto-generated descriptions, sympy generation, AST canonicalization)
   - Detect conflicts (direct and transitive)
   - Populate stances (inline from claims + standalone files)
   - Restore embeddings
   - Write content hash

### 2.2 Querying

The sidecar SQLite is the query surface. FTS5 provides full-text search over concepts and claims. The CLI entry point is `pks` (`pyproject.toml:24`). The render layer (not in scope of this review) resolves conflicts using strategies like recency, sample_size, argumentation.

### 2.3 Concept Registry for Claim Validation

`build_concept_registry_from_paths()` (`validate_claims.py:557-597`) builds a lookup dict keyed by concept ID, canonical_name, AND aliases. This means claims can reference concepts by any of these three keys. The enriched dict includes `_form_definition` and `_allowed_units` private keys for unit validation.

## 3. Code Quality Observations

### 3.1 Good

**Content-hash rebuild avoidance** (`build_sidecar.py:37-91`): Thorough. Hashes concepts, claims, context files, form files, stance files, and generated schemas. The `_SEMANTIC_INPUT_VERSION` salt (`build_sidecar.py:34`) means the hash format can be bumped to force rebuilds when the compilation logic changes.

**Validation depth**: The validators catch a genuinely impressive range of semantic errors:
- Circular deprecation chains (`validate.py:352-369`)
- Dimensional mismatch heuristics on parameterizations (`validate.py:287-314`)
- CEL type-checking on conditions throughout (`validate.py:259-265`, `validate_claims.py:207-218`)
- Algorithm body AST parsing with unbound-name detection (`validate_claims.py:515-554`)
- Unit dimensional analysis with fallback to whitelist (`validate_claims.py:373-406`)
- Sympy validation/auto-generation for equations (`validate_claims.py:409-434`)

**Condition classification** (`condition_classifier.py`): Clean two-tier design -- Z3 as primary solver, interval arithmetic as fallback. The conservative OVERLAP default when parsing fails (`condition_classifier.py:137`) is the right choice (avoids false negatives in conflict detection).

**Separation of concerns**: Each file has a clear responsibility. `value_comparison.py` has zero propstore imports -- pure numeric logic. `stances.py` is a tiny vocabulary module. `form_utils.py` handles all form loading with caching.

**Embedding snapshot/restore** (`build_sidecar.py:233-251`, `291-301`): Preserves expensive embedding vectors across sidecar rebuilds. Graceful degradation when sqlite-vec is not installed.

### 3.2 Observations and Minor Concerns

**Module-level mutable cache** in `form_utils.py:30`: `_form_cache: dict[tuple[str, str], FormDefinition | None] = {}` is a process-global mutable cache with no invalidation mechanism. This is fine for a CLI tool (process lifetime = one build), but would be a bug in a long-running server. Same pattern for `_form_schema_cache` at `form_utils.py:199`.

**`repo` parameter typed as `object`**: Throughout the codebase (`build_sidecar.py:41,204`, `validate.py:97`), the `repo` parameter is typed as `object | None` with `# type: ignore[union-attr]` on every attribute access. This is a structural typing gap -- there is presumably a Repository class elsewhere that should be the declared type. Current code works but provides no IDE assistance or type safety.

**`__init__.py` is empty**: `/c/Users/Q/code/propstore/propstore/__init__.py` contains nothing (1 line, blank). This is fine -- explicit imports throughout -- but means there is no public API surface declaration.

**33-column claim INSERT** (`build_sidecar.py:688-696`): The claim table has 33 columns and the INSERT uses positional `?` placeholders. The `_prepare_claim_insert_row` helper returns a 33-element tuple. This is fragile -- adding a column requires coordinating three locations (CREATE TABLE at line 589, INSERT at line 688, tuple construction at line 731-785). A dict-based approach or named parameters would be safer.

**Legacy value-list path** in `value_comparison.py`: The `values_compatible` function (`value_comparison.py:87-131`) has both a "named fields path" and a "legacy list path". The legacy path handles values as lists of numbers. The `extract_interval` function (`value_comparison.py:27-57`) also has a legacy list fallback. This dual-path code works but the legacy path appears to be dead weight if all claims now use named fields.

**Broad exception catch in Z3 classification** (`condition_classifier.py:85-86`): `except Exception: return None` silently swallows any Z3 error. This is intentional (graceful degradation to interval arithmetic) but means Z3 bugs are invisible.

**`conditions_differ` type inconsistency** (`build_sidecar.py:181-182`): If `conditions_differ` is a list, it gets JSON-dumped to a string before INSERT. But the schema declares it as a single string field (`claim.linkml.yaml:403`). This suggests runtime data sometimes has a list where a string is expected.

**Draft rejection in validation** (`validate_claims.py:137-141`): Files with `stage: "draft"` are rejected with an error during validation. This is a hard gate that prevents draft claims from entering the sidecar. Consistent with the project's non-commitment discipline, but worth noting -- draft claims exist somewhere in the pipeline but are filtered before compilation.

### 3.3 Dependency Notes

From `pyproject.toml`:
- `ast-equiv` is a local path dependency (`../ast-equiv`) -- sibling repo
- Z3 is a hard dependency (`z3-solver>=4.12`), not optional, despite the conditional import pattern in `condition_classifier.py:76-78`
- Embeddings are optional (`litellm`, `sqlite-vec`)
- Build system is Hatch

## 4. Surprising / Novel Aspects

**This is a compiler, not a database application.** The YAML files are source code. The sidecar is the compiled artifact. The content hash is the build cache. The validators are the type checker. This is a genuinely unusual architecture -- most knowledge management systems treat the database as source of truth. Here, the database is a disposable build artifact that can be regenerated from YAML at any time.

**CEL as the condition language.** Conditions on claims and relationships use CEL (Common Expression Language) strings, type-checked against the concept registry at validation time (`cel_checker` module). This gives a portable, well-specified condition language that can be evaluated by Z3 for formal reasoning or by interval arithmetic as fallback.

**Stance types directly from argumentation theory.** The 7 stance types (rebuts, undercuts, undermines, supports, explains, supersedes, none) map directly to the Pollock 1987 / Dung 1995 / Modgil & Prakken 2018 literature. The system is not just storing claims -- it is building an argumentation framework where claims can attack and support each other, with multiple resolution strategies at render time.

**Algorithm claims with AST canonicalization.** The `algorithm` claim type stores Python function bodies with AST parsing (`ast_equiv.parse_algorithm`), name extraction (`ast_equiv.extract_names`), canonical AST dumping (`ast_equiv.canonical_dump`), and variable binding validation. This enables structural comparison of algorithms across papers -- two papers describing the same algorithm in different variable names can be detected as equivalent.

**Parameterization groups as connected components.** `build_groups()` (imported from `parameterization_groups`) computes connected components over the parameterization graph. This means the system can answer "which concepts are algebraically related to each other?" without traversing the graph at query time.

**Concept IDs reference by name or alias in claims.** The concept registry built by `build_concept_registry_from_paths()` (`validate_claims.py:557-597`) indexes by ID, canonical_name, and all alias names. A claim can say `concept: "fundamental_frequency"` (the name) instead of `concept: "concept12"` (the ID). This is good for human authoring but creates a potential ambiguity if an alias collides with another concept's name -- the code uses first-wins (`validate_claims.py:591,596`: `if canonical not in registry` / `if alias_name not in registry`).

**Embedding snapshot/restore across rebuilds.** The sidecar is rebuilt from scratch (delete + create), but embedding vectors (which are expensive to compute) are extracted before deletion and restored after rebuild (`build_sidecar.py:233-301`). This is a practical optimization that most systems would not think to do.

**Nine claim types for a knowledge store.** Most knowledge bases have "fact" and maybe "relation". This system has parameter, equation, observation, model, measurement, algorithm, mechanism, comparison, and limitation -- each with different required fields and validation rules. The mechanism/comparison/limitation types reuse observation validation (`validate_claims.py:233-234`) but are semantically distinct in the schema.

## 5. Files Reviewed

- `/c/Users/Q/code/propstore/propstore/__init__.py` -- empty
- `/c/Users/Q/code/propstore/propstore/build_sidecar.py` -- 963 lines, sidecar compilation
- `/c/Users/Q/code/propstore/propstore/validate.py` -- 374 lines, concept validation
- `/c/Users/Q/code/propstore/propstore/validate_claims.py` -- 610 lines, claim validation
- `/c/Users/Q/code/propstore/propstore/validate_contexts.py` -- 154 lines, context validation + hierarchy
- `/c/Users/Q/code/propstore/propstore/stances.py` -- 7 lines, stance vocabulary
- `/c/Users/Q/code/propstore/propstore/resources.py` -- 60 lines, resource loading
- `/c/Users/Q/code/propstore/propstore/form_utils.py` -- 257 lines, form loading + validation
- `/c/Users/Q/code/propstore/propstore/value_comparison.py` -- 155 lines, numeric comparison
- `/c/Users/Q/code/propstore/propstore/condition_classifier.py` -- 329 lines, Z3/interval condition classification
- `/c/Users/Q/code/propstore/propstore/description_generator.py` -- 172 lines, auto-description
- `/c/Users/Q/code/propstore/pyproject.toml` -- 45 lines, project config
- `/c/Users/Q/code/propstore/schema/claim.linkml.yaml` -- 488 lines, claim LinkML schema
- `/c/Users/Q/code/propstore/schema/concept_registry.linkml.yaml` -- 285 lines, concept LinkML schema
- Example data: `knowledge/concepts/argumentation_framework.yaml`, `knowledge/claims/Dung_1995_AcceptabilityArguments.yaml`, `knowledge/forms/structural.yaml`, `knowledge/contexts/ctx_abstract_argumentation.yaml`, `knowledge/stances/Dung_1995_AcceptabilityArguments__claim1.yaml`

## 6. Summary

The propstore core is a well-structured compiler pipeline: YAML source files go through multi-pass validation (structural, referential, dimensional, CEL type-checking) and are compiled into a content-hash-addressed SQLite sidecar with FTS5 indexing. The data model is unusually rich -- 9 claim types, 7 stance types grounded in argumentation theory, CEL conditions with Z3 reasoning, AST-canonical algorithm comparison, and connected-component parameterization groups. The code is clean with good separation of concerns. The main structural weakness is the `repo: object` typing pattern and the fragile 33-column positional INSERT. The legacy value-list code path in `value_comparison.py` may be dead weight. The architecture is novel -- treating a knowledge base as compiled source code rather than a mutable database is an uncommon and principled choice that aligns with the project's core non-commitment discipline.
