# Research Papers Plugin -- Comprehensive Survey Report

## Location
`C:/Users/Q/code/research-papers-plugin` (sibling repo to propstore, not a dependency in pyproject.toml)

## Overview
A Claude Code / Codex CLI / Gemini CLI plugin (version 3.3.1) for managing annotated research paper collections. It provides agent skills (prompts that instruct LLMs how to perform tasks) and Python scripts (deterministic tooling the skills invoke). The plugin is NOT a Python package -- it is a collection of standalone scripts with PEP 723 inline dependency declarations, plus markdown-based skill definitions.

## Repository Structure

```
research-papers-plugin/
  .claude-plugin/marketplace.json          # Marketplace wrapper
  plugins/research-papers/
    .claude-plugin/plugin.json             # Plugin manifest v3.3.1
    scripts/           (18 Python files)   # Deterministic tooling
    skills/            (13 SKILL.md files) # LLM agent instructions
    tests/             (8 test files)      # Unit + property tests
    prompts/           (1 .md file)        # Prompt template
    vocabularies/      (1 .yaml file)      # Seed concept vocabulary
```

---

## 1. SCRIPTS (18 files)

### 1a. Paper Identity and Retrieval

| Script | Purpose | External Deps |
|--------|---------|---------------|
| `_paper_id.py` | Shared identifier parsing: classify arxiv/DOI/ACL/S2 identifiers, parse citations, generate canonical dirnames | None |
| `fetch_paper.py` | PDF download with waterfall strategy: arxiv API -> Semantic Scholar -> Unpaywall -> direct | arxiv, semanticscholar, requests |
| `paper_hash.py` | Paper identity resolution: lookup by citation, generate dirname, parse citation strings, extract unfulfilled leads from notes | None (imports _paper_id) |
| `search_papers.py` | Multi-source paper search (arxiv + Semantic Scholar) with deduplication | arxiv, semanticscholar |
| `get_citations.py` | Citation graph traversal via Semantic Scholar; filter papers already in collection | semanticscholar |

### 1b. Claims Pipeline

| Script | Purpose | External Deps |
|--------|---------|---------------|
| `generate_claims.py` (783 lines) | **Deterministic** extraction of claims.yaml from notes.md: parses parameter tables, $$ equation blocks, testable properties. No LLM needed. | pyyaml |
| `batch_generate_claims.py` | Runs generate_claims across all paper dirs. Uses importlib hack to load sibling. | pyyaml (via generate_claims) |
| `bootstrap_concepts.py` | Collects concept names from claims files, groups similar ones via string similarity (union-find + abbreviation expansion + Jaccard overlap). O(n^2). | pyyaml |
| `propose_concepts.py` | Creates propstore concept YAML files from claims. Infers form from units (Hz->frequency, ms->time, etc.) and name patterns (regex). Reads counters/global.next for monotonic IDs. | pyyaml |

### 1c. Corpus Management

| Script | Purpose | External Deps |
|--------|---------|---------------|
| `generate-paper-index.py` | Rebuilds papers/index.md and tagged/ symlinks. Tag validation against tags.yaml registry. | pyyaml |
| `cross-reference-papers.py` | Finds cited papers in collection via author+year string matching. Appends cross-reference section to notes.md. | None |
| `canonicalize-tags.py` | Rewrites tags in description.md frontmatter using tags.yaml alias map. Transitive alias resolution. | pyyaml |
| `audit_paper_corpus.py` | Read-only corpus audit: file coverage, format families, metadata key signatures, crossref status. | None |
| `lint_paper_schema.py` | Schema linter: enforces canonical frontmatter, required files, tag format. Imports audit_paper_corpus and paper_db_manifest. | None |
| `paper_db_manifest.py` | Loads papers/db.yaml manifest defining schema version, required/recommended files, canonical keys, legacy aliases. Has DEFAULT_MANIFEST fallback. Hand-rolls YAML parsing. | None |

### 1d. Migration Tools

| Script | Purpose |
|--------|---------|
| `migrate-format.py` | Tags: lines -> YAML frontmatter; bold refs -> wikilinks. Idempotent. |
| `migrate_notes_frontmatter.py` | Extracts # Title and **Key:** Value metadata -> YAML frontmatter. Idempotent. |
| `normalize_notes_schema.py` | Normalizes alias keys (author->authors, doi->doi_url), fills year from dirname, canonical key order. Idempotent. |

---

## 2. SKILLS (13 SKILL.md files)

Skills are markdown documents that instruct LLM agents. They reference `${CLAUDE_PLUGIN_ROOT}` for script paths.

### 2a. Core Pipeline Skills

| Skill | What it does | Approximate size |
|-------|-------------|-----------------|
| **paper-retriever** | Downloads paper PDF. Waterfall: fetch_paper.py -> sci-hub via Playwright/Chrome -> manual fallback. | ~129 lines |
| **paper-reader** | Reads paper, extracts structured notes. PDF->PNG via ImageMagick. <=50pp direct read, >50pp chunked with parallel subagents. Produces notes.md, description.md, abstract.md, citations.md. Most detailed extraction guidelines. | ~432 lines |
| **paper-process** | Combined retrieve + read + extract-claims + report in one step. | ~62 lines |
| **extract-claims** | LLM-powered claim extraction/enrichment. 8 claim types: parameter, equation, observation, model, measurement, mechanism, comparison, limitation. Concept-first rule. Context identification (ASPIC+, Dung, ATMS traditions). Post-write validation via `pks claim validate-file`. | ~786 lines |

### 2b. Collection Management Skills

| Skill | What it does |
|-------|-------------|
| **reconcile** | Bidirectional cross-referencing: forward (this paper cites -> collection), reverse (collection cites -> this), conceptual links (topic-based, not citation-based), supersedes/recontextualizes tracking. Idempotent. |
| **reconcile-vocabulary** | Normalize concept names across claims files. Collision group detection, optional rewrite mode. |
| **tag-papers** | Add tags to untagged papers using notes.md content. Prefers existing tags from tags.yaml. |
| **lint-paper** | Read-only audit: file completeness, format compliance, index consistency. |
| **process-leads** | Extract "New Leads" from collection, triage by availability, process via subagents. Supports --parallel. |
| **process-new-papers** | Process unprocessed PDFs in papers/ root (convention: root PDF = unprocessed). |

### 2c. Analysis and Meta Skills

| Skill | What it does |
|-------|-------------|
| **adjudicate** | Systematically adjudicate disagreements across papers. Four categories: WRONG, SUPERSEDED, LIMITED, INCOMPARABLE. Produces verdict documents with Synthesizer Audit sections. |
| **research** | Web research on a topic, produces structured findings report to reports/ directory. |
| **make-skill** | Meta-skill: creates new skills from prompt files. Analyzes patterns, determines frontmatter, generates SKILL.md. |

---

## 3. HOW IT INTEGRATES WITH PROPSTORE

The plugin is NOT a Python dependency of propstore. Integration is at the agent/CLI level:

### Direct propstore CLI calls (from extract-claims skill):
- `pks concept add --name <name> --domain <domain> --form <form> --definition "<def>"` -- register concepts
- `pks concept add-value <concept> --value "<value>"` -- add values to category concepts
- `pks concept categories` -- list category concepts and allowed values
- `pks context add --name <name> --description "<desc>"` -- register theoretical contexts
- `pks claim validate-file <path>` -- validate claims.yaml against propstore schema

### File-level integration:
- Reads `concepts/*.yaml` or `knowledge/concepts/*.yaml` for concept registry
- Reads `knowledge/contexts/*.yaml` for theoretical contexts
- `propose_concepts.py` writes concept YAML files directly to propstore's concepts directory
- `test_generate_claims.py` line 10 references a path into propstore: `propstore/schema/generated/claim.schema.json`

### Data flow: Paper -> Propstore
1. **Retrieve**: fetch_paper.py downloads PDF + metadata.json
2. **Read**: paper-reader skill produces notes.md (structured extraction), description.md, abstract.md, citations.md
3. **Mechanical claims**: generate_claims.py parses notes.md tables/equations/properties -> claims.yaml (stage: draft)
4. **LLM enrichment**: extract-claims skill enriches claims (page numbers, concept resolution, SymPy, conditions, stances, new claim types)
5. **Concept registration**: extract-claims registers concepts in propstore before writing claims
6. **Validation**: `pks claim validate-file` validates the final claims.yaml
7. **Concept bootstrapping**: propose_concepts.py creates propstore concept files from claims, with form inference

---

## 4. EXTERNAL SERVICE DEPENDENCIES

| Service | Used by | Purpose |
|---------|---------|---------|
| **arxiv API** | fetch_paper.py, search_papers.py | Paper metadata + PDF download |
| **Semantic Scholar API** | fetch_paper.py, search_papers.py, get_citations.py | Metadata, citation graph, search |
| **Unpaywall API** | fetch_paper.py | Open-access PDF URLs |
| **ImageMagick** (`magick`) | paper-reader skill | PDF -> page image conversion |
| **pdfinfo** | paper-reader skill | Page count (optional) |
| **Playwright MCP** | paper-retriever skill | Browser automation for paywalled papers (optional) |
| **Claude-in-Chrome MCP** | paper-retriever skill | Alternative browser automation (optional) |
| **pks CLI** (propstore) | extract-claims skill, propose_concepts.py | Concept/context registration, claim validation |
| **LLM agent** | All skills | Skills are prompts executed by Claude/Codex/Gemini |

---

## 5. TESTS (8 files)

All tests use `importlib.util` to load scripts as modules (no package structure). Test frameworks: unittest (most), pytest (test_generate_paper_index.py), hypothesis (test_bootstrap_concepts.py).

| Test file | What it tests | Notable |
|-----------|--------------|---------|
| `test_generate_claims.py` | Parameter table parsing, range parsing, uncertainty parsing, equation extraction, testable properties, full pipeline, claim IDs | References propstore schema path at line 10 |
| `test_batch_generate_claims.py` | Batch processing, skip-existing, empty dir, summary counts | |
| `test_bootstrap_concepts.py` | Concept extraction, grouping, idempotency, property-based tests via Hypothesis | Good use of property-based testing |
| `test_audit_paper_corpus.py` | Notes format detection, description style detection, frontmatter keys | |
| `test_lint_paper_schema.py` | Violation detection, canonical frontmatter acceptance, manifest loading | |
| `test_generate_paper_index.py` | Tag registry loading, validation, alias resolution | Uses pytest fixtures |
| `test_migrate_notes_frontmatter.py` | Migration from title+metadata to frontmatter, idempotency | |
| `test_normalize_notes_schema.py` | Alias key rewriting, year inference from dirname, idempotency | |

---

## 6. PROMPTS AND VOCABULARIES

### Prompts
- `prompts/tag-papers-harness.md` -- A concrete harness prompt hardcoded to `C:\Users\Q\code\Qlatt\papers`. Not a generic template.

### Vocabularies
- `vocabularies/video-understanding.yaml` -- Seed vocabulary for video understanding / audio description research. Maps natural language terms to canonical concept names (e.g., "dense video captioning" -> `dense_video_captioning`, "DVC" -> `dense_video_captioning`). Also has abbreviation mappings.

---

## 7. BUGS, ISSUES, AND CODE SMELLS

### Bugs

1. **extract-claims SKILL.md forward-references Steps A-D as "above" but they appear below** (line 51 says "run the Concept Registration steps (A through D) above" but Steps A-D are at lines 462+). This will confuse LLM agents following the instructions top-to-bottom.

2. **cross-reference-papers.py fails if index.md does not exist** -- line 30 calls `INDEX_MD.read_text()` unconditionally. No existence check.

3. **lint_paper_schema.py imports audit_paper_corpus and paper_db_manifest by bare name** (lines 18-24) with no sys.path setup. This only works if CWD is the scripts directory, or if those modules were previously loaded into sys.modules by the test harness.

### Code Smells

4. **Bare except clauses that silently swallow errors**:
   - `fetch_paper.py` lines 68, 107, 128 -- `except Exception` with no logging
   - `propose_concepts.py` line 151 -- `except Exception: continue` when loading YAML

5. **sys.path manipulation for imports** -- `fetch_paper.py` line 28, `get_citations.py` line 26, `paper_hash.py` line 25 all do `sys.path.insert(0, ...)`. Fragile, non-standard.

6. **importlib hack in batch_generate_claims.py** (lines 18-26) -- loads sibling script via importlib.util.spec_from_file_location instead of proper package imports.

7. **Module-level side effects** -- `audit_paper_corpus.py` line 28, `cross-reference-papers.py` line 24, `generate-paper-index.py` line 21, `normalize_notes_schema.py` line 27 all resolve paths at import time from sys.argv, making them unusable as libraries without careful sys.argv setup.

8. **UNPAYWALL_EMAIL is a hardcoded placeholder** -- `fetch_paper.py` line 31: `"research-papers-plugin@example.com"`. Should be configurable via env var or config.

9. **O(n^2) all-pairs similarity in bootstrap_concepts.py** (lines 208-210). For N concepts, this does N*(N-1)/2 comparisons. Will be slow for large concept sets (>1000).

10. **paper_db_manifest.py hand-rolls YAML parsing** (lines 86-114) instead of using pyyaml, which is already a dependency of other scripts.

11. **Inconsistent filename conventions** -- some use hyphens (`canonicalize-tags.py`, `cross-reference-papers.py`), others underscores (`generate_claims.py`, `bootstrap_concepts.py`). Hyphenated filenames cannot be imported as Python modules without importlib hacks.

12. **No package structure** -- all scripts are standalone files. No `__init__.py`, no setup.py/pyproject.toml for the plugin itself. Every test file reimplements the same importlib loading boilerplate.

13. **tag-papers-harness.md has hardcoded absolute paths** to `C:\Users\Q\code\Qlatt\papers` (lines 1, 8, 40). Not portable.

14. **test_generate_claims.py hardcodes a cross-repo path** at line 10: `propstore/schema/generated/claim.schema.json`. This path is relative to some assumed parent directory structure. The schema is referenced but never actually used in the test file (no JSON schema validation test exists).

### Design Observations (not bugs)

15. **Skills are extremely detailed** -- extract-claims is 786 lines of instructions. This is a feature (deterministic behavior from LLMs) but creates maintenance burden. Changes to claim types or propstore schema require updating the skill doc.

16. **The adjudicate skill has a strong editorial voice** -- "Ruthless. If the evidence says a paper was wrong, say it plainly." This is deliberate design, not a smell.

17. **Graceful degradation** -- extract-claims gracefully falls back to descriptive concept names if no propstore concept registry exists (lines 466-468). Good design.

18. **All migration scripts are idempotent** -- running them multiple times produces the same result. Good design, well-tested.

---

## 8. DATA FLOW SUMMARY

```
                     User provides URL/DOI/title
                              |
                     paper-retriever skill
                     (fetch_paper.py)
                              |
                     paper-reader skill
                     (ImageMagick, LLM reads pages)
                              |
              +-------+-------+-------+-------+
              |       |       |       |       |
           notes.md  desc.md  abs.md  cit.md  index.md
              |
     generate_claims.py  (deterministic)
              |
         claims.yaml (stage: draft)
              |
     extract-claims skill  (LLM enrichment)
              |
         claims.yaml (enriched: page numbers, concepts, conditions, stances)
              |
     propose_concepts.py  (or pks concept add)
              |
         concepts/*.yaml  (in propstore)
              |
     pks claim validate-file
              |
         Validated claims in propstore
```

Parallel tracks:
- reconcile skill: bidirectional cross-referencing after each paper
- bootstrap_concepts.py: batch concept deduplication
- reconcile-vocabulary skill: normalize concept names across claims
- adjudicate skill: render verdicts on disagreements

---

## FILES READ (complete inventory)

Every source file in the repository was read in full:
- 18 Python scripts
- 13 SKILL.md files
- 8 test files
- 1 prompt file
- 1 vocabulary file
- 3 config/meta files (README.md, marketplace.json, plugin.json)
