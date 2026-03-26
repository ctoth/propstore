# Research Papers Plugin - Code Review

## GOAL
Survey the research-papers-plugin codebase, understand its architecture, relationship to propstore, and workflows.

## STATUS: COMPLETE

---

## 1. What This Plugin Does

The research-papers-plugin (version 3.3.1) is a Claude Code plugin for managing annotated research paper collections. It provides an end-to-end pipeline: discover papers, retrieve PDFs, read and annotate them, extract machine-readable claims, cross-reference across the collection, and adjudicate disagreements.

It works with Claude Code, Codex CLI, and Gemini CLI via a skill-based architecture.

**Location:** `/c/Users/Q/code/research-papers-plugin/`
**Plugin manifest:** `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/.claude-plugin/plugin.json` (line 4: version "3.3.1")

---

## 2. How It Relates to Propstore

The plugin is the **ingestion pipeline** for propstore. It generates the raw material -- claims, concepts, contexts, stances -- that propstore stores and reasons over.

### Direct Integration Points

1. **Claims generation** (`generate_claims.py`, lines 616-699): Produces `claims.yaml` files conforming to propstore's claim schema. Claim types: `parameter`, `equation`, `observation`, `model`, `measurement`, `mechanism`, `comparison`, `limitation`. These map directly to propstore's source-of-truth storage layer.

2. **Concept registration** (`extract-claims/SKILL.md`, lines 458-576): The skill instructs the agent to register concepts in propstore via `pks concept add` before extracting claims. It checks `knowledge/concepts/*.yaml` for existing concepts, creates missing ones, and uses `pks concept add-value` for category values.

3. **Context assignment** (`extract-claims/SKILL.md`, lines 577-603): Claims are assigned to theoretical contexts (e.g., `ctx_atms_tradition`, `ctx_aspic_plus`) via `pks context add`. This feeds propstore's multi-context storage.

4. **Claim validation** (`extract-claims/SKILL.md`, lines 756-766): After writing claims.yaml, the skill calls `uv run pks claim validate-file` -- direct propstore CLI usage.

5. **Vocabulary reconciliation** (`reconcile-vocabulary/SKILL.md`): Normalizes concept names across claims files using string similarity and abbreviation expansion, feeding propstore's concept deduplication.

6. **Adjudication** (`adjudicate/SKILL.md`): Produces verdicts (WRONG, SUPERSEDED, LIMITED, INCOMPARABLE) that map to propstore's argumentation layer -- stance types like `rebuts`, `undercuts`, `supersedes`.

7. **Stances** (`extract-claims/SKILL.md`, lines 144-163): Claims can carry stances using ASPIC+ taxonomy (`rebuts`, `undercuts`, `undermines`, `supports`, `explains`, `supersedes`), matching propstore's argumentation layer vocabulary from `CLAUDE.md` (Modgil & Prakken 2018 grounding).

8. **Conditions** (`extract-claims/SKILL.md`, lines 114-134): CEL expressions on claims (e.g., `"dataset == 'ActivityNet'"`) feed propstore's condition language in the theory/typing layer.

### Data Flow: Plugin to Propstore

```
paper.pdf
  -> paper-reader -> notes.md (structured notes with page citations)
  -> generate_claims.py -> claims.yaml (draft, mechanical)
  -> extract-claims skill -> claims.yaml (enriched, LLM-powered)
  -> pks concept add (registers concepts)
  -> pks context add (registers contexts)
  -> pks claim validate-file (validates against schema)
  -> propstore source-of-truth storage
```

### Vocabulary file

The plugin ships one vocabulary file at `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/vocabularies/video-understanding.yaml`. This maps paper terminology to canonical concept names (e.g., "dense video captioning" and "DVC" both map to `dense_video_captioning`). The domain is "video-understanding" -- suggesting this plugin has been used for a video/audio description research project as well as the argumentation theory project in propstore.

---

## 3. Workflows It Enables

### Workflow A: Single Paper Processing
`paper-process` skill (`paper-process/SKILL.md`): combines retrieval, reading, and claim extraction in one step. Steps: retrieve PDF -> read all pages -> write notes.md/description.md/abstract.md/citations.md -> extract claims -> write report. The skill auto-chains paper-retriever -> paper-reader -> extract-claims.

### Workflow B: Batch Lead Processing
`process-leads` skill (`process-leads/SKILL.md`): Extracts "New Leads" from the collection's cross-reference sections, triages them (books/old papers deferred), and processes them via subagents. Supports `--parallel M` for concurrent processing. Each lead is processed via a subagent to protect the foreman's context window.

### Workflow C: Collection Maintenance
- `lint-paper --all`: Audits all papers for completeness (10 checks including metadata, tags, cross-refs, source artifacts, page citations).
- `tag-papers --all`: Adds tags to untagged papers using existing tag vocabulary.
- `reconcile --all`: Ensures bidirectional cross-references across the entire collection.
- `process-new-papers`: Processes any unprocessed PDFs dropped in papers/ root.

### Workflow D: Claims Pipeline
1. `generate_claims.py` (mechanical, no LLM): Parses markdown parameter tables, `$$` equation blocks, and "Testable Properties" sections from notes.md.
2. `extract-claims` skill (LLM-powered): Enriches draft claims with page numbers, concept resolution, SymPy expressions, variable bindings, conditions, stances, and new claim types (mechanism, comparison, limitation).
3. `batch_generate_claims.py`: Runs step 1 across all papers.
4. `bootstrap_concepts.py`: Deduplicates concepts across all claims files using string similarity with abbreviation expansion (union-find grouping, 0.6 similarity threshold).

### Workflow E: Adjudication
`adjudicate` skill: Reads all paper notes on a topic, produces verdicts with a defined evidence hierarchy and four error categories. Outputs to `research/verdicts/`. Designed for wave-ordered processing (foundations -> dynamics -> higher-level -> master synthesis).

### Workflow F: Vocabulary Reconciliation
`reconcile-vocabulary` skill: Scans all claims.yaml files, builds concept frequency table, identifies collision groups via string similarity, and optionally rewrites claims to use canonical names.

---

## 4. Architecture and Key Components

### Directory Structure

```
research-papers-plugin/
  .claude-plugin/marketplace.json          -- marketplace wrapper
  plugins/research-papers/
    .claude-plugin/plugin.json             -- plugin metadata (v3.3.1)
    skills/                                -- 13 agent skills (SKILL.md each)
    scripts/                               -- 18 Python scripts
    tests/                                 -- 8 test files
    prompts/                               -- 1 prompt template
    templates/                             -- gitignore template
    vocabularies/                          -- 1 domain vocabulary
```

### Skills (13 total)

| Skill | Purpose | Agent Context |
|-------|---------|---------------|
| paper-retriever | Download PDFs (arxiv, DOI, ACL, sci-hub) | default |
| paper-reader | Read paper, extract structured notes | default |
| paper-process | Combined retrieve + read + extract-claims | default |
| lint-paper | Audit paper dirs (read-only) | default |
| reconcile | Bidirectional cross-referencing | default |
| tag-papers | Add tags to untagged papers | default |
| research | Web research on a topic | fork, general-purpose |
| extract-claims | Extract propositional claims | default |
| make-skill | Create new skills from prompts | default |
| process-leads | Batch process citation leads | default |
| process-new-papers | Process unprocessed PDFs | default |
| reconcile-vocabulary | Normalize concept vocabulary | default |
| adjudicate | Produce verdicts on disagreements | fork, general-purpose |

Note: 4 skills (process-leads, process-new-papers, reconcile-vocabulary, adjudicate) are not listed in the README table (README.md lines 17-28) but exist in the skills directory.

### Scripts (18 Python files)

**Core pipeline:**
- `_paper_id.py` (lines 1-247): Shared identifier parsing. Classifies arxiv IDs, DOIs, ACL URLs, S2 IDs. Generates canonical directory names (`Author_Year_ShortTitle`).
- `fetch_paper.py` (lines 1-261): Waterfall PDF download: direct -> arxiv -> ACL -> Unpaywall -> fallback. Uses arxiv and semanticscholar libraries.
- `search_papers.py` (lines 1-172): Multi-source paper search (arxiv + Semantic Scholar), with deduplication by DOI/title.
- `get_citations.py` (lines 1-228): Citation graph traversal via Semantic Scholar. Supports references/citations/both directions. Can filter papers already in collection.
- `generate_claims.py` (lines 1-783): Mechanical claims extraction from notes.md. Parses parameter tables, equations, testable properties. Quality gate: requires (value OR bounds) AND unit for parameter claims.
- `batch_generate_claims.py`: Batch runner for generate_claims.py.
- `bootstrap_concepts.py` (lines 1-288): Concept deduplication using union-find with string similarity (Jaccard + prefix matching + abbreviation expansion). Threshold: 0.6.

**Migration/maintenance:**
- `migrate-format.py`: Legacy Tags: lines to YAML frontmatter, bold refs to wikilinks.
- `migrate_notes_frontmatter.py`: Frontmatter migration.
- `normalize_notes_schema.py`: Schema normalization.
- `canonicalize-tags.py`: Tag canonicalization.

**Collection management:**
- `generate-paper-index.py`: Rebuilds papers/index.md and tagged-papers/ symlinks.
- `cross-reference-papers.py`: Find cross-references between papers.
- `audit_paper_corpus.py`: Corpus auditing.
- `lint_paper_schema.py`: Schema linting.
- `paper_db_manifest.py`: Manifest generation.
- `paper_hash.py`: Paper hashing/lookup.
- `propose_concepts.py`: Concept proposals.

### Tests (8 files)

All under `plugins/research-papers/tests/`:
- `test_audit_paper_corpus.py`
- `test_batch_generate_claims.py`
- `test_bootstrap_concepts.py`
- `test_generate_claims.py`
- `test_generate_paper_index.py`
- `test_lint_paper_schema.py`
- `test_migrate_notes_frontmatter.py`
- `test_normalize_notes_schema.py`

Uses Hypothesis for property-based testing (`.hypothesis/` directory with constant files present).

### Key Design Patterns

1. **Two-phase extraction**: Mechanical (Python script, deterministic) then LLM enrichment (skill). The mechanical phase handles structured data (tables, equations); the LLM phase handles semantic understanding (page resolution, concept mapping, stance identification).

2. **Quality gates**: `generate_claims.py` line 494 rejects parameter claims without both (value or bounds) AND unit. The extract-claims skill has a "Claim Value Filter" (lines 635-658) that filters by query-worthiness.

3. **Graceful degradation**: If no propstore concepts directory exists, extract-claims falls back to descriptive `lowercase_underscore` names (line 468). Claims remain valid without registry-backed concepts.

4. **Subagent isolation**: process-leads dispatches each paper-process as a subagent to protect context window. Paper-reader dispatches chunk readers for papers >50 pages.

5. **Idempotency**: reconcile skill checks for duplicate annotations before writing (lines 338-342). Process-leads uses paper_hash.py lookup to avoid re-processing.

6. **Convention over configuration**: A PDF in papers/ root is unprocessed; processed papers live in subdirectories (process-new-papers/SKILL.md lines 14-15). Directory naming is canonical: `Author_Year_ShortTitle`.

---

## 5. Surprising Findings

1. **README is out of date**: 4 skills (process-leads, process-new-papers, reconcile-vocabulary, adjudicate) exist but are not listed in the README skills table (README.md lines 17-28).

2. **The vocabulary file is domain-specific to video understanding** (`vocabularies/video-understanding.yaml`), not to the argumentation theory domain that propstore currently focuses on. This suggests the plugin was originally developed for a different research domain and later adapted for propstore's argumentation/belief revision work.

3. **Hardcoded email in fetch_paper.py** (line 31): `UNPAYWALL_EMAIL = "research-papers-plugin@example.com"` -- this is a placeholder. Unpaywall recommends using a real email for API access; a placeholder may get rate-limited.

4. **`_ABBREVIATIONS` in bootstrap_concepts.py** (lines 81-119) contains domain-specific abbreviations spanning both speech acoustics (`f0`, `oq`, `vq`, `harm`) and video understanding (`fps`, `iou`, `map`, `attn`). This is an evolving dictionary that grows with each research domain.

5. **No propstore dependency declared**: The plugin operates as a standalone tool that happens to produce propstore-compatible output. There is no Python import of propstore code -- integration is purely through the `pks` CLI and YAML file conventions.

---

## 6. Files Referenced

- `/c/Users/Q/code/research-papers-plugin/README.md` -- plugin overview
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/.claude-plugin/plugin.json` -- version, metadata
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/extract-claims/SKILL.md` -- primary propstore integration
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/reconcile-vocabulary/SKILL.md` -- vocabulary normalization
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/adjudicate/SKILL.md` -- verdict generation
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/paper-reader/SKILL.md` -- paper reading/annotation
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/paper-process/SKILL.md` -- combined pipeline
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/reconcile/SKILL.md` -- cross-referencing
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/paper-retriever/SKILL.md` -- PDF retrieval
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/process-leads/SKILL.md` -- batch lead processing
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/process-new-papers/SKILL.md` -- unprocessed PDF batch
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/lint-paper/SKILL.md` -- collection audit
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/tag-papers/SKILL.md` -- tagging
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/research/SKILL.md` -- web research
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/scripts/generate_claims.py` -- mechanical claims extraction
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/scripts/bootstrap_concepts.py` -- concept deduplication
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/scripts/fetch_paper.py` -- paper fetching
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/scripts/search_papers.py` -- paper search
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/scripts/get_citations.py` -- citation graph
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/scripts/_paper_id.py` -- identifier classification
- `/c/Users/Q/code/research-papers-plugin/plugins/research-papers/vocabularies/video-understanding.yaml` -- domain vocabulary
