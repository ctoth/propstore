# Propstore Grok + Integration Notes (2026-03-17)

## GOAL
Understand propstore thoroughly, assess README accuracy, then identify integration points with research-papers-plugin.

## How Propstore Actually Works

### Data Model
- **Concepts** = named quantities/categories/booleans with stable IDs (concept1..N). YAML source of truth. Each has: canonical_name, domain, form, definition, optional aliases/relationships/parameterizations.
- **Claims** = evidence from papers. Five types: parameter (numeric binding), equation (math), observation (qualitative), model (multi-equation), measurement (perceptual/behavioral). Each has provenance (paper + page), optional CEL conditions, optional stances (supports/contradicts other claims).
- **Forms** = measurement/representation kind for concepts. YAML files defining kind_type (quantity/category/boolean/structural), unit_symbol, allowed_units, dimensionless flag, parameters.
- **Conflicts** = compiler-detected disagreements between claims. Classified via Z3 satisfiability: CONFLICT (same scope), OVERLAP (partial), PHI_NODE (disjoint scopes), PARAM_CONFLICT (via parameterization chain).

### Compilation Pipeline
1. `pks validate` — loads concepts/*.yaml + claims/*.yaml, runs JSON Schema validation, compiler contract checks (ID format, uniqueness, deprecation chains, relationship targets, CEL type-checking against concept registry, form compatibility, unit validation)
2. `pks build` — validate → build SQLite sidecar (concepts + FTS5 + aliases + relationships + parameterization groups + claims + conflicts + claim FTS5 + stances) → WorldModel roundtrip verification
3. Content-hashing for incremental rebuilds (skip if unchanged)

### WorldModel Reasoner (read-only over sidecar)
- `value_of(concept_id)` → evidence: determined/conflicted/no_claims
- `derived_value(concept_id)` → inference via SymPy parameterization evaluation
- `resolve(concept_id, strategy)` → policy: recency/sample_size/stance/override
- `bind(**conditions)` → BoundWorld with Z3-based condition filtering
- `HypotheticalWorld` → counterfactual: add/remove claims, diff, recompute_conflicts
- `chain_query(target, strategy, **bindings)` → multi-hop propagation through parameter space
- `analyze_sensitivity(concept_id)` → partial derivatives + elasticities
- `build_knowledge_graph()` → DOT/JSON graph export

### CEL Type System
- Tokenizer + recursive-descent parser → AST
- Type-checks names against concept registry kinds
- Category concepts: value set checking (extensible or closed)
- Boolean/quantity type mismatch detection
- Z3 translation for satisfiability queries

### import-papers handoff
- `pks import-papers --papers-root ../research-papers-plugin/papers` scans for `papers/<PaperDir>/claims.yaml`
- Copies to `claims/<PaperDir>.yaml`, normalizes `source.paper` to dirname
- Then `pks validate && pks build` to compile

## State of knowledge/
- Only has `sidecar/` with compiled SQLite — no concepts/, claims/, forms/ source YAML in the repo
- The source YAML lives somewhere else (or hasn't been created yet for this repo)

## README Assessment
The README is accurate and comprehensive. It correctly describes:
- Architecture, concept/claim/form/conflict semantics
- All CLI commands including the world subcommands
- The import-papers handoff from research-papers-plugin
- Schema, testing, repository layout

**One gap**: README says `pks init` creates concepts/, claims/, forms/, sidecar/ — but the actual knowledge/ dir in this repo has NONE of those except sidecar/. This suggests the YAML source lives elsewhere or this is an output-only checkout.

## PEP 723 / Inline Script Metadata
Q asked about using PEP 723 annotations so a standalone script can declare propstore as a dependency and `uv run script.py` just works. This would look like:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "propstore",
# ]
# ///
```

This requires propstore to be on PyPI (or specify a git URL in the dep). Currently propstore is not published.

## research-papers-plugin Structure
- Claude Code plugin with skills: paper-retriever, paper-reader, reconcile, tag-papers, etc.
- Paper output: `papers/<Author_Year_Title>/` with notes.md (YAML frontmatter + structured extraction), description.md, abstract.md, citations.md, paper.pdf
- notes.md has: Key Equations (LaTeX), Parameters table (Name/Symbol/Units/Default/Range/Notes), Testable Properties
- Scripts: audit_paper_corpus.py, lint_paper_schema.py, cross-reference-papers.py, generate-paper-index.py
- No `claims.yaml` exists yet in any paper directory — the import bridge is specified but not implemented on the plugin side

## Integration Points (proposed)

### 1. claims.yaml Generator (new skill in research-papers-plugin)
The paper-reader already extracts Parameters tables and Key Equations into notes.md. A new skill/script would convert those into propstore claims.yaml format:
- Parameter table rows → `type: parameter` claims with concept, value, unit, conditions
- Key Equations → `type: equation` claims with expression, variables, sympy
- Testable Properties → `type: observation` claims
- Provenance auto-populated from notes.md frontmatter (paper name, year)

This is the missing half of the `pks import-papers` bridge.

### 2. Concept Discovery (new propstore CLI command or script)
When importing papers, claims reference concepts that may not exist yet. Options:
- `pks import-papers --discover-concepts` creates proposed concepts from claim references
- Or a standalone script that scans claims.yaml files and reports unmapped concept references

### 3. Form-Aware Parameter Extraction
The paper-reader's Parameter table includes Units — this maps to propstore's form system. The claims.yaml generator could:
- Look up existing forms to set the right unit
- Suggest new forms for units not yet in the registry

### 4. Cross-Reference Reconciliation
research-papers-plugin's reconcile skill tracks which papers cite which. This maps to propstore's stance system — if Paper B says "contrary to Paper A's finding," that's a `contradicts` stance. The reconcile output could feed stance declarations into claims.yaml.

### 5. Bidirectional Index
propstore's FTS5 search could be exposed to the paper collection — "find all papers that have claims about concept X" — complementing the plugin's tag-based index.
