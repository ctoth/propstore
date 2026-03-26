# Codebase Review — 2026-03-23 (in progress)

## GOAL
Thorough survey of the propstore codebase: structure, data model, CLI, build, tests, algorithms.

## Top-Level Structure (observed)

The project root contains:
- `propstore/` — Python package (NOT src/propstore)
- `knowledge/` — data directory with subdirs: claims, concepts, contexts, forms, sidecar, stances
- `papers/` — 30+ paper directories (Author_Year_Title format)
- `tests/` — 30+ test files
- `scripts/` — utility scripts (extract_concepts, reconcile_vocab, etc.)
- `schema/` — LinkML schemas (claim.linkml.yaml, concept_registry.linkml.yaml, generate.py, generated/)
- `forms/` — TBD (separate from knowledge/forms?)
- `plans/`, `prompts/`, `reports/`, `design-spikes/` — TBD
- `pyproject.toml` — build config
- `main.py` — TBD
- `propstore.sqlite` — SQLite database (root level, separate from sidecar)
- Many notes-*.md files and log files (not tracked in git)

## Python Package Structure (propstore/)

Entry point: `pks = propstore.cli:cli` (pyproject.toml line 24)

Dependencies: click, linkml, pyyaml, jsonschema, sympy, z3-solver, graphviz, ast-equiv (local ../ast-equiv)
Optional: litellm, sqlite-vec (embeddings)
Dev: pytest, hypothesis, rope

### Modules in propstore/:
- `cli/` subpackage: __init__, claim, compiler_cmds, concept, context, form, helpers, init, repository
- `world/` subpackage: __init__, bound, hypothetical, model, resolution, types
- Core modules: argumentation, build_sidecar, cel_checker, condition_classifier, conflict_detector, description_generator, dung, dung_z3, embed, equation_comparison, form_utils, graph_export, maxsat_resolver, param_conflicts, parameterization_groups, preference, propagation, relate, resources, sensitivity, sympy_generator, unit_dimensions, validate, validate_claims, validate_contexts, value_comparison, z3_conditions

## CLI Commands (observed from cli/__init__.py and compiler_cmds.py)

Top-level groups/commands:
- `pks concept` — add, alias, rename, deprecate, link, search, list, add-value, categories, show, embed, similar
- `pks claim` — validate, validate-file, conflicts, compare, embed, similar, relate
- `pks context` — TBD (not yet read)
- `pks form` — TBD (not yet read)
- `pks validate` — validates all concepts + claims + forms + CEL type-checking
- `pks build` — validate everything, build sidecar SQLite, run conflict detection
- `pks query` — raw SQL against sidecar
- `pks export-aliases` — export alias lookup table (text or JSON)
- `pks import-papers` — import claims.yaml from papers/ directories into knowledge/claims/
- `pks init` — initialize repository structure
- `pks world` — subcommands: status, query, bind, explain, algorithms, derive, resolve, extensions, hypothetical, chain, export-graph, sensitivity, check-consistency

## Repository Structure (from cli/repository.py)

Repository class finds `knowledge/` directory by walking up from cwd.
Subdirectories:
- `knowledge/concepts/` — concept YAML files, plus `.counters/` for ID generation
- `knowledge/claims/` — claim YAML files
- `knowledge/contexts/` — context YAML files
- `knowledge/forms/` — form definition YAML files
- `knowledge/sidecar/` — compiled SQLite database (`propstore.sqlite`)
- `knowledge/stances/` — stance YAML files (epistemic relationships between claims)

## Build System (from build_sidecar.py)

`pks build` does:
1. Validate form files
2. Validate concepts (CEL type-checking, cross-references, form compatibility)
3. Load and validate contexts
4. Validate claims
5. Build SQLite sidecar with tables:
   - concept (id, content_hash, seq, canonical_name, status, domain, definition, kind_type, form, form_parameters, range_min/max, is_dimensionless, unit_symbol, dates)
   - alias (concept_id, alias_name, source)
   - relationship (source_id, type, target_id, conditions_cel, note)
   - parameterization (output_concept_id, concept_ids, formula, sympy, exactness, conditions_cel)
   - parameterization_group (concept_id, group_id) — connected components
   - concept_fts (FTS5 index)
   - context, context_assumption, context_exclusion
   - claim (id, content_hash, many fields including type, value, bounds, conditions, expressions, body/canonical_ast for algorithms, source_paper, provenance, context_id)
   - claim_stance (claim_id, target_claim_id, stance_type, strength, resolution metadata)
   - conflicts (concept_id, claim_a_id, claim_b_id, warning_class, conditions, values)
   - claim_fts (FTS5 index)
6. Content-hash addressed — only rebuilds when source changes
7. Preserves embeddings across rebuilds (snapshot/restore pattern)
8. Populates stances from both inline claim stances and standalone stance files

## World Model (from world/model.py)

WorldModel is a read-only reasoner over the compiled sidecar. Key operations:
- get_concept, get_claim, resolve_alias, claims_for, search
- stances_between, explain (BFS walk of stance graph)
- similar_claims, similar_concepts (via sqlite-vec embeddings)
- bind(environment, policy) -> BoundWorld (condition-filtered view)
- chain_query — traverses parameter space to derive target concept (iterative resolution)
- Lazy Z3 solver setup for condition reasoning

## Resolution Strategies (from world/resolution.py)

Four strategies for resolving conflicted concepts:
1. RECENCY — pick claim with most recent date in provenance
2. SAMPLE_SIZE — pick claim with largest sample_size
3. ARGUMENTATION — build Dung AF from stance graph, compute extension, pick survivor
4. OVERRIDE — user specifies which claim wins

## Data Types (from world/types.py)

Key types:
- ValueResult — status: determined/conflicted/underdetermined/no_claims
- DerivedResult — status: derived/underspecified/no_relationship/conflicted
- ResolvedResult — adds winning_claim_id, strategy, reason
- Environment — bindings (condition key-value pairs) + optional context_id
- RenderPolicy — strategy, semantics, comparison, confidence_threshold, overrides, per-concept strategies
- BeliefSpace protocol — active_claims, value_of, derived_value, resolved_value, conflicts
- ArtifactStore protocol — full store interface (concepts, claims, stances, search, etc.)

## Conflict Detection (from conflict_detector.py)

ConflictClass enum: COMPATIBLE, PHI_NODE, CONFLICT, OVERLAP, PARAM_CONFLICT, CONTEXT_PHI_NODE
- PHI_NODE = values differ but conditions fully disjoint (not a real conflict)
- CONTEXT_PHI_NODE = different unrelated contexts (not a real conflict)
- CONFLICT = values differ, conditions identical
- OVERLAP = values differ, conditions partially overlapping

## Dung AF (from dung.py)

Implements Dung 1995: ArgumentationFramework dataclass with arguments, defeats, attacks.
Functions: attackers_of, conflict_free, defends, characteristic_fn.
Computes grounded/preferred/stable/complete extensions.

## Claim Types (from build_sidecar.py _populate_claims)

Six claim types: parameter, measurement, observation, equation, model, algorithm
- parameter: concept_id, value, bounds, uncertainty, sample_size, unit
- measurement: target_concept, measure, methodology, population, value+bounds
- observation: statement (text)
- equation: expression, auto-generates sympy
- model: name
- algorithm: concept_id, body (code), canonical_ast (via ast-equiv), variables, stage

## STILL TODO
- Read actual knowledge/ YAML files for concrete data model examples
- Read argumentation.py for ASPIC+ implementation
- Read cel_checker.py, z3_conditions.py for condition reasoning
- Read form_utils.py for form system
- Read relate.py for LLM-based stance classification
- Read tests for coverage
- Read papers/ structure
- Read scripts/
- Read world/bound.py and world/hypothetical.py fully
