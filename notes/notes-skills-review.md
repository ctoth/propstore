# Skills Review: research-papers-plugin

Scout report, 2026-03-23. Every claim cites a specific file and line.

## 1. Top-Level Structure

Repository root: `C:/Users/Q/code/research-papers-plugin/`

```
.claude-plugin/marketplace.json   -- marketplace registration
.gitignore
README.md                         -- plugin overview + installation docs
notes.md                          -- session notes (35KB)
notes-2026-03-21.md               -- session notes
plugins/research-papers/          -- the actual plugin
  .claude-plugin/plugin.json      -- plugin metadata (version 3.3.1)
  prompts/tag-papers-harness.md   -- standalone harness prompt for tagging
  scripts/                        -- 16 Python scripts (see section 3)
  skills/                         -- 13 skill directories, each with SKILL.md
  templates/papers-gitignore      -- gitignore template for consumer projects
  tests/                          -- 8 test files
  vocabularies/video-understanding.yaml -- seed vocabulary for concept normalization
```

The marketplace.json (`/.claude-plugin/marketplace.json:1-16`) declares one plugin named "research-papers" sourced from `./plugins/research-papers`. The plugin.json (`plugins/research-papers/.claude-plugin/plugin.json:1-9`) has version 3.3.1.

---

## 2. Skill-by-Skill Analysis

### 2.1 paper-retriever

**File:** `plugins/research-papers/skills/paper-retriever/SKILL.md`

**Frontmatter:**
- `name: paper-retriever`
- `argument-hint: "<arxiv-url-or-doi> [optional-output-name]"`
- `disable-model-invocation: false`
- No tool restrictions, no context/agent settings

**What it does:** Downloads a scientific paper PDF. Accepts arxiv URLs, DOIs, ACL Anthology URLs, AAAI URLs, or plain titles. For titles, it calls `search_papers.py` to find the paper first (line 27). Then calls `fetch_paper.py` (line 37) which resolves metadata, creates the paper directory (`Author_Year_ShortTitle`), writes `metadata.json`, and attempts PDF download via a waterfall: direct download, Unpaywall, then reports fallback needed.

If `fetch_paper.py` returns `fallback_needed: true` (line 49), the skill tries browser automation for sci-hub in priority order: Playwright MCP (lines 57-71), Claude-in-Chrome (lines 75-81), or asks the user for manual download (line 85).

**Outputs:** `papers/<dirname>/paper.pdf` and `papers/<dirname>/metadata.json`

**Propstore interaction:** None. This is a pure retrieval skill.

**Notable:** Uses `$CLAUDE_PLUGIN_ROOT` to reference scripts (line 28, 37). Has the standard "File Modified Error Workaround" and "Parallel Swarm Awareness" boilerplate (lines 114-128).

---

### 2.2 paper-reader

**File:** `plugins/research-papers/skills/paper-reader/SKILL.md`

**Frontmatter:**
- `name: paper-reader`
- `argument-hint: "[path/to/paper.pdf]"`
- `disable-model-invocation: false`
- No tool restrictions

**What it does:** The longest and most complex skill. Reads a scientific paper and creates structured implementation-focused notes.

1. **Step 0 (lines 14-47):** Checks for existing paper directory using `paper_hash.py lookup`. If already complete, deletes root PDF and stops. If partially complete, fills gaps.

2. **Step 1 (lines 50-88):** Converts PDF to page images using `magick` (ImageMagick) at 150 DPI. Creates directory `papers/Author_Year_ShortTitle/pngs/`. Uses `mv` never `cp` for the source PDF (line 71, emphasized as CRITICAL at line 77). Decision: papers <=50 pages get read directly, >50 pages use chunk protocol.

3. **Step 2A (lines 92-97):** Direct read for <=50 pages. EVERY page must be read -- explicitly forbids skipping with a stern warning (line 94): "Agents routinely skip pages to save tokens -- this produces incomplete notes that miss equations, parameters, and key details."

4. **Step 2B (lines 100-157):** Chunk protocol for >50 pages. Splits into 50-page chunks, writes a template prompt to `prompts/paper-chunk-reader.md`, dispatches subagents per chunk (or processes sequentially), then synthesizes.

5. **Step 3 (lines 161-242):** Writes `notes.md` with extensive structure: frontmatter (title, authors, year, venue, doi_url), one-sentence summary, problem addressed, key contributions, methodology, key equations (LaTeX), parameters (mandatory table format), implementation details, figures, results, limitations, arguments against prior work, design rationale, testable properties, relevance, open questions, related work.

6. **Steps 4-6 (lines 301-358):** Writes `description.md` (3 sentences + tags frontmatter), `abstract.md` (verbatim + interpretation), `citations.md` (full reference list + key citations).

7. **Step 7 (lines 362-367):** Invokes the **reconcile** skill on the paper directory. This is a skill-to-skill dependency.

8. **Step 8 (lines 370-378):** Updates `papers/index.md`. Marked as NOT optional.

**Outputs:** `papers/Author_Year_Title/` containing notes.md, description.md, abstract.md, citations.md, pngs/, index.md entry. Papers >50pp also get chunks/.

**Propstore interaction:** None directly -- but outputs (notes.md, parameters, equations, testable properties) are the raw material that `extract-claims` later converts to propstore claims.

**Mandatory formats defined here:**
- Parameter tables: one row per parameter, specific columns required (lines 256-268)
- Equations: one per `$$` block, no prose inside (lines 274-279)
- Page citations: `*(p.N)*` notation required on every finding (lines 282-298)
- Frontmatter schema with required/recommended/optional/legacy fields (lines 246-249)

---

### 2.3 paper-process

**File:** `plugins/research-papers/skills/paper-process/SKILL.md`

**Frontmatter:**
- `name: paper-process`
- `argument-hint: "<url-or-doi-or-title>"`
- `disable-model-invocation: false`

**What it does:** A thin orchestrator that chains three skills in sequence:
1. **Step 1 (line 14):** Invoke `paper-retriever`
2. **Step 2 (line 19):** Invoke `paper-reader`
3. **Step 3 (lines 28-37):** Clean up root-level PDF if the source was a local file
4. **Step 4 (line 41):** Invoke `extract-claims`
5. **Step 5 (lines 48-56):** Write a per-paper report to `reports/paper-$SAFE_NAME.md`

**Outputs:** Everything from all three sub-skills plus a report file.

**Propstore interaction:** Indirectly through `extract-claims` invocation.

**Notable:** Error handling is sequential -- if retrieval fails, stops; if reading fails, stops before claims. This is the main "do everything for one paper" entry point.

---

### 2.4 extract-claims

**File:** `plugins/research-papers/skills/extract-claims/SKILL.md`

**Frontmatter:**
- `name: extract-claims`
- `argument-hint: "<papers/Author_Year_Title> [--mode enrich|create]"`
- `disable-model-invocation: false`
- Version comment: `context-aware-2026-03-22` (line 7)

**What it does:** The primary propstore integration point. Two modes:

**Mode 1: Enrich (default, lines 46-196):** Takes an existing `claims.yaml` (from `generate_claims.py`) and improves it: resolves page numbers, maps concepts to registry IDs, converts LaTeX sympy to valid SymPy, populates variable bindings, adds CEL conditions, adds notes, adds stances (ASPIC+ taxonomy), adds uncertainty/sample_size.

**Mode 2: Full Creation (lines 224-448):** Creates claims.yaml from scratch using notes.md. Extracts 8 claim types:
- **parameter** (lines 239-257): concept, value, unit, conditions
- **equation** (lines 266-292): expression, sympy, variables with bindings
- **observation** (lines 296-316): statement + concepts list
- **model** (lines 320-339): multi-equation frameworks with parameter bindings
- **measurement** (lines 342-359): target_concept, measure type, value, methodology
- **mechanism** (lines 362-378): causal/architectural arguments
- **comparison** (lines 388-408): contrastive positioning against prior work
- **limitation** (lines 410-430): scope boundaries and failure modes

**Concept Registration (lines 458-575):** Before extracting any claims, the skill runs a concept-first flow:
- Step A: Check if propstore concepts directory exists
- Step B: Read existing concepts and load category vocabulary via `pks concept categories`
- Step C: Identify concepts this paper needs
- Step D: Register missing concepts via `pks concept add`

This is significant -- the skill can fall back to "graceful degradation mode" if no concepts directory exists (line 468), using descriptive names instead.

**Context identification (lines 577-603):** Identifies which theoretical tradition the paper belongs to (ATMS, ASPIC+, Dung, etc.), checks existing contexts via `pks context add`, assigns context IDs to claims.

**Stances taxonomy (lines 144-163):** Uses ASPIC+ taxonomy:
- Attack: rebuts, undercuts, undermines
- Support: supports, explains
- Preference: supersedes

**Claim Value Filter (lines 633-696):** Detailed rules on what to EXTRACT (architectural insights, design constraints, validated thresholds), SKIP (training hyperparams without interpretation, study logistics, config dumps), and CONVERT (collapse repeated measurements into pattern observations).

**Claim Decomposition (lines 665-740):** One proposition per claim. Detailed examples of bad (packed) vs good (decomposed) claims. Special rule for definitional claims: don't explode tuples into separate claims.

**Post-Write Validation (lines 757-768):** Runs `pks claim validate-file` after writing. Must pass before extraction is considered complete.

**Outputs:** `<paper_dir>/claims.yaml`, potentially new concepts and contexts in the propstore.

**Propstore interaction:** DEEP. This skill reads from and writes to:
- `concepts/*.yaml` or `knowledge/concepts/*.yaml` (read)
- `knowledge/contexts/*.yaml` (read)
- `pks concept add`, `pks concept add-value`, `pks context add` (write)
- `pks claim validate-file` (validate)

---

### 2.5 reconcile

**File:** `plugins/research-papers/skills/reconcile/SKILL.md`

**Frontmatter:**
- `name: reconcile`
- `argument-hint: "<papers/Author_Year_Title> or --all"`
- `disable-model-invocation: false`

**What it does:** Cross-references a paper against the collection bidirectionally. Five major steps:

1. **Forward cross-referencing (lines 49-97):** Reads citations.md, searches `papers/index.md` for matching papers. Writes `## Collection Cross-References` section in notes.md with subsections: Already in Collection, New Leads, Supersedes or Recontextualizes, Conceptual Links.

2. **Reverse citation search (lines 106-138):** Greps the entire collection for references to this paper by author+year pattern.

3. **Conceptual links (lines 142-215):** Topic-based connections that aren't citation-based. Classifies as Strong/Moderate/Weak. Strong connections are bidirectionally annotated; moderate only on the reconciled paper. Explicitly marked as NOT optional (line 146).

4. **Reconcile citing papers (lines 219-271):** For papers that cite this one, moves leads from "New Leads" to "Now in Collection", fixes inaccurate descriptions, annotates answered open questions, documents finding tensions.

5. **Bidirectional annotation (lines 209-215):** Updates connected papers' notes.md for strong connections.

**Outputs:** Modified notes.md files across multiple papers in the collection.

**Propstore interaction:** None. Operates entirely on papers/ markdown files.

**Notable:** The "Reconciliation Principle" (lines 305-326) is a formal specification of what bidirectional consistency means. Idempotency checks are mandated before every write (lines 337-343). The skill has two lead-discovery locations (line 226): `### New Leads (Not Yet in Collection)` (reconciled papers) and `## Related Work Worth Reading` (unreconciled papers from paper-reader default).

---

### 2.6 reconcile-vocabulary

**File:** `plugins/research-papers/skills/reconcile-vocabulary/SKILL.md`

**Frontmatter:**
- `name: reconcile-vocabulary`
- `argument-hint: "<papers-directory> [--fix] [--vocabulary <path>]"`
- `disable-model-invocation: false`

**What it does:** Normalizes concept names across all `claims.yaml` files. Collects every concept reference (from concept, target_concept, concepts list, variable concept fields), builds a frequency table, identifies collision groups using: vocabulary file matches, string similarity (token overlap, 0.6 threshold, line 59), and abbreviation expansion. In `--fix` mode, rewrites all claims.yaml files to use canonical names.

**Outputs:** `reports/vocabulary-reconciliation-report.md`, optionally modified claims.yaml files.

**Propstore interaction:** Reads claims.yaml files, can rewrite them. Uses the vocabulary YAML (like `vocabularies/video-understanding.yaml`) for canonical mappings.

---

### 2.7 lint-paper

**File:** `plugins/research-papers/skills/lint-paper/SKILL.md`

**Frontmatter:**
- `name: lint-paper`
- `argument-hint: "<papers/Author_Year_Title> or --all"`
- `disable-model-invocation: false`

**What it does:** Read-only audit. Checks 10 things per paper:
1. Required files: notes.md, description.md (required); abstract.md, citations.md (recommended)
2. Source artifact: paper.pdf or pngs/ (required -- "notes without a verifiable source are untrustworthy", line 35)
3. Notes metadata: YAML frontmatter with title/year
4. Tags: description.md frontmatter with tags field
5. Wikilinks: checks for legacy bold refs
6. Frontmatter validity
7. Cross-references section present
8. In papers/index.md
9. Index description matches description.md
10. Page citations in notes (grep for `(p.[0-9]`)

Uses `papers/db.yaml` as schema contract (line 12).

**Outputs:** Console report only. Error codes: NOTES_METADATA_MISSING, UNTAGGED, LEGACY_BOLD_REFS, NOT_RECONCILED, NOT_INDEXED, INDEX_STALE, NO_SOURCE_ARTIFACT, ORPHAN_PDF, NO_PAGE_CITATIONS.

**Propstore interaction:** None. Pure file audit.

**Notable:** Explicitly says "No AI needed -- just file checks and grep" (line 11) and "Do NOT use AI/LLM features" (line 167).

---

### 2.8 tag-papers

**File:** `plugins/research-papers/skills/tag-papers/SKILL.md`

**Frontmatter:**
- `name: tag-papers`
- `argument-hint: "<papers/Author_Year_Title> or --all"`
- `disable-model-invocation: false`

**What it does:** Adds tags to untagged papers. Reads existing tag vocabulary from `papers/index.md` and optionally `papers/tags.yaml` (canonical tag vocabulary, line 40). Reads notes.md + description.md to choose 2-5 tags. Guidelines: lowercase-hyphenated, prefer existing tags, mix broad+narrow, 3 tags typical. Writes tags as YAML frontmatter in description.md, updates index.md.

**Outputs:** Modified description.md (frontmatter) and index.md files.

**Propstore interaction:** None.

---

### 2.9 process-leads

**File:** `plugins/research-papers/skills/process-leads/SKILL.md`

**Frontmatter:**
- `name: process-leads`
- `argument-hint: "[--all | N] [--parallel M]"`
- `disable-model-invocation: false`

**What it does:** Discovers papers cited as "New Leads" across the collection and retrieves+reads them. Two discovery modes:
- **Mode A (lines 18-22):** Notes-based, uses `paper_hash.py extract-leads`
- **Mode B (lines 26-33):** Citation-graph based via `get_citations.py` and Semantic Scholar

Triages leads (lines 49-60): sorts by retrieval likelihood, defers books/old papers/dissertations. Dispatches `paper-process` as subagents (one per lead) -- explicitly mandated even in sequential mode to protect context window (lines 67-68). Parallel mode processes in waves of M agents.

Post-processing: the foreman runs reconcile + index.md update after each agent/wave completes (not the subagent).

**Outputs:** `reports/process-leads-report.md` with succeeded/failed/remaining counts.

**Propstore interaction:** Indirectly through paper-process -> extract-claims.

**Notable:** `--all` means "keep going until session ends naturally" (line 39), not "finish everything." Explicitly forbids worktree isolation (line 79): "Paper-process writes to shared state (papers/index.md, cross-references in existing papers' notes.md via reconcile). Worktrees strand all of that with no clean merge path."

---

### 2.10 process-new-papers

**File:** `plugins/research-papers/skills/process-new-papers/SKILL.md`

**Frontmatter:**
- `name: process-new-papers`
- `argument-hint: ""`
- `disable-model-invocation: false`

**What it does:** Simple batch processor. Lists all `papers/*.pdf` root-level PDFs (by convention, root-level = unprocessed). Invokes `paper-reader` on each sequentially. One at a time, no parallelism.

**Outputs:** Papers moved from root to subdirectories.

**Propstore interaction:** None directly.

**Notable:** Very short skill (66 lines). Relies on the convention that a PDF in papers/ root is unprocessed -- once processed, the PDF is `mv`'d into a subdirectory.

---

### 2.11 research

**File:** `plugins/research-papers/skills/research/SKILL.md`

**Frontmatter:**
- `name: research`
- `argument-hint: "[topic]"`
- `context: fork` (spawns in forked context)
- `agent: general-purpose`

**What it does:** Web research on a topic. Searches for papers, documentation, implementations, comparison studies. Writes findings to `reports/research-$ARGUMENTS.md` in a structured template: summary, approaches found (with pros/cons/complexity), key papers, existing implementations, tradeoffs, recommendations, estimated effort.

**Outputs:** `reports/research-$ARGUMENTS.md`

**Propstore interaction:** None.

**Notable:** One of only two skills that sets `context: fork` and `agent: general-purpose` (the other is `adjudicate`). This means it runs as a separate agent instance.

---

### 2.12 adjudicate

**File:** `plugins/research-papers/skills/adjudicate/SKILL.md`

**Frontmatter:**
- `name: adjudicate`
- `argument-hint: "[topic-scope or --all]"`
- `context: fork`
- `agent: general-purpose`

**What it does:** Produces formal judgments on disagreements across the paper collection. Not summaries -- verdicts. Operates in three modes: full collection sweep (`--all`), single topic, or specific paper set.

Evidence hierarchy (lines 74-88): multiple replications > single study, direct measurement > derived, larger sample > smaller, modern tech > older, etc. Override conditions are specified (lines 90-93).

Four error categories (lines 96-97): WRONG (methodology error), SUPERSEDED (better data replaced it), LIMITED (correct but overgeneralized), INCOMPARABLE (measured different things).

Verdict documents go to `research/verdicts/NN-topic-name.md` with sections: Papers Considered, Historical Timeline, Findings by Category, What Subsumes What, Genuinely Uncertain, Best Current Understanding, Synthesizer Audit, Open Questions.

Wave ordering for `--all` mode (lines 164-178): Wave 1 foundations, Wave 2 dynamics, Wave 3 higher-level, Wave 4 master synthesis.

**Outputs:** `research/verdicts/*.md` files, `research/verdicts/00-master-synthesis.md`, `research/verdicts/notes-progress.md`

**Propstore interaction:** None directly -- reads paper notes, writes verdict documents. However, the Synthesizer Audit section (lines 136-138) is designed to produce replacement values for implementation, which could feed into propstore claims.

**Notable:** The tone instruction (lines 146-148) is explicit: "Ruthless. If the evidence says a paper was wrong, say it plainly." Can invoke paper-process to acquire missing critical papers mid-adjudication (lines 158-162).

---

### 2.13 make-skill

**File:** `plugins/research-papers/skills/make-skill/SKILL.md`

**Frontmatter:**
- `name: make-skill`
- `argument-hint: "[prompt-path(s)] [--name name] [--global]"`
- `allowed-tools: Read, Write, Bash(mkdir:*), Bash(ls:*), Glob`

**What it does:** Meta-skill for creating new skills from existing prompts. Analyzes prompt files to extract fixed elements (boilerplate) vs variable elements (what $ARGUMENTS replaces). Determines appropriate frontmatter settings based on workflow characteristics (research, implementation, audit, commit/deploy). Generates SKILL.md with proper structure.

Always includes the "File Modified Error Workaround" and "Parallel Swarm Awareness" boilerplate in generated skills (lines 110-127).

**Outputs:** A new `SKILL.md` file in either `./.claude/skills/` or `~/.claude/skills/`

**Propstore interaction:** None.

**Notable:** The ONLY skill with `allowed-tools` restrictions (line 6). Shows user a summary and waits for confirmation before writing (lines 162-188).

---

## 3. Scripts

16 Python scripts in `plugins/research-papers/scripts/`:

| Script | Purpose |
|--------|---------|
| `_paper_id.py` | Shared utility (underscore prefix = internal) |
| `audit_paper_corpus.py` | Audit paper collection completeness |
| `batch_generate_claims.py` | Run generate_claims.py across all papers |
| `bootstrap_concepts.py` | Deduplicate/group concept names from claims |
| `canonicalize-tags.py` | Normalize tags |
| `cross-reference-papers.py` | Find cross-references between papers |
| `fetch_paper.py` | Download paper PDFs with metadata resolution |
| `generate-paper-index.py` | Rebuild papers/index.md and tagged/ symlinks |
| `generate_claims.py` | Parse notes.md to produce draft claims.yaml |
| `get_citations.py` | Fetch citations from Semantic Scholar |
| `lint_paper_schema.py` | Schema validation for paper files |
| `migrate-format.py` | Legacy format migration (bold refs -> wikilinks) |
| `migrate_notes_frontmatter.py` | Add/fix frontmatter in notes.md |
| `normalize_notes_schema.py` | Normalize notes.md schema |
| `paper_db_manifest.py` | Paper database manifest |
| `paper_hash.py` | Hash-based paper lookup + lead extraction |
| `propose_concepts.py` | Propose concept registrations |
| `search_papers.py` | Search for papers by title (arxiv, S2) |

---

## 4. Shared Configuration and Templates

**Vocabulary file:** `plugins/research-papers/vocabularies/video-understanding.yaml` (lines 1-67). Maps paper terms to canonical concept names for the video-understanding domain. Has `concepts` mapping (term -> canonical) and `abbreviations` mapping. Used by `extract-claims` and `reconcile-vocabulary`. This is a domain-specific seed vocabulary -- there could be others for different research domains.

**Template:** `plugins/research-papers/templates/papers-gitignore` (lines 1-10). Gitignore template for consumer projects: excludes PDFs, pngs/, temp conversion files, and tagged/ symlinks.

**Prompt:** `plugins/research-papers/prompts/tag-papers-harness.md` (lines 1-57). A standalone harness prompt specifically for the Qlatt project. Hardcodes paths (`C:\Users\Q\code\Qlatt\papers`) and references the tag-papers SKILL.md as policy. Includes a post-tagging step to run `generate-paper-index.py`. This is the only prompt file and is project-specific rather than generic.

**Standard boilerplate** appears in most skills:
- "File Modified Error Workaround" block (5-step retry protocol for Edit/Write failures)
- "Parallel Swarm Awareness" block (never use git restore/checkout/reset/clean)
- Completion block specifying exact output format and DO NOT list

---

## 5. Skill Relationships

### Dependency Graph (A -> B means A invokes B)

```
paper-process -> paper-retriever
paper-process -> paper-reader
paper-process -> extract-claims

paper-reader -> reconcile (Step 7)

process-leads -> paper-process (via subagents)
process-leads -> reconcile (foreman runs post-agent)

process-new-papers -> paper-reader

adjudicate -> paper-process (optional, to fill gaps)

reconcile-vocabulary -> (reads claims.yaml files produced by extract-claims)
```

### Standalone Skills (no inbound or outbound skill dependencies)
- `research` -- pure web research
- `lint-paper` -- pure audit
- `tag-papers` -- pure tagging
- `make-skill` -- meta/tooling

### The Main Pipeline

The primary flow is: `paper-retriever` -> `paper-reader` -> `reconcile` -> `extract-claims`

This is bundled as `paper-process`, and `process-leads` orchestrates multiple `paper-process` invocations.

### Propstore Integration Points

Only `extract-claims` directly touches the propstore. It:
- Reads: `concepts/*.yaml`, `knowledge/concepts/*.yaml`, `knowledge/contexts/*.yaml`
- Writes: new concepts via `pks concept add`, new values via `pks concept add-value`, new contexts via `pks context add`
- Validates: `pks claim validate-file`
- Produces: `claims.yaml` per paper

Everything else in the pipeline exists to produce the raw material (notes.md) that `extract-claims` then converts to propstore-compatible claims.

---

## 6. Patterns and Conventions

### Frontmatter Schema

All skills use YAML frontmatter with these fields:
- `name` (required)
- `description` (required)
- `argument-hint` (required) -- shows the user what arguments to pass
- `disable-model-invocation` (optional, default false) -- no skill sets this to true
- `context` (optional) -- only `research` and `adjudicate` set `fork`
- `agent` (optional) -- only `research` and `adjudicate` set `general-purpose`
- `allowed-tools` (optional) -- only `make-skill` restricts tools

### $ARGUMENTS and $CLAUDE_PLUGIN_ROOT

Skills use `$ARGUMENTS` as the user-provided input placeholder and `$CLAUDE_PLUGIN_ROOT` to reference scripts within the plugin.

### Completion Pattern

Every skill ends with a structured completion output format (usually in a code block) and a "Do NOT" list of forbidden actions. This is consistent across all skills.

### Bash Embedding

Skills embed bash snippets as instructions for the agent, not as directly executable scripts. The agent is expected to run them in context. This is a "prompt as program" pattern.

### Error Handling

Most skills have sequential error handling: if step N fails, stop before step N+1. The `paper-process` skill is the clearest example (lines 59-62).

---

## 7. Surprising Findings

1. **No skill sets `disable-model-invocation: true`.** The make-skill documentation (line 66) says to set this for skills with side effects (commits, deploys), but no actual skill uses it. Every skill has `disable-model-invocation: false` or omits it.

2. **Only one skill has tool restrictions.** `make-skill` has `allowed-tools: Read, Write, Bash(mkdir:*), Bash(ls:*), Glob`. All other skills have unrestricted tool access. Given that `lint-paper` explicitly says "No AI needed" and `tag-papers` only modifies description.md + index.md, these seem like candidates for tool restrictions that weren't applied.

3. **The tag-papers-harness.md prompt is Qlatt-specific.** It hardcodes `C:\Users\Q\code\Qlatt\papers` (line 3) and references a specific project. This is the only non-generic file in the plugin -- everything else is project-agnostic. It lives in `prompts/` rather than `skills/`, suggesting it was a one-off.

4. **The vocabulary file is video-understanding only.** The plugin appears to have been used for at least two different research domains (video understanding and now the propstore's argumentation/TMS domain), but only one seed vocabulary exists. The `extract-claims` skill handles this gracefully via its graceful degradation mode (line 468).

5. **paper-reader is extremely aggressive about completeness.** The "Read EVERY page image" instruction at line 94 is one of the strongest directives in any skill: "If you skip pages, the notes are worthless." This suggests a history of agents cutting corners.

6. **reconcile's conceptual links step explicitly says "not optional" (line 146).** This suggests it was being skipped by agents, requiring the explicit callout. The same pattern appears with paper-reader's index.md update: "This step is NOT optional" (line 378).

7. **extract-claims has a version comment** (`context-aware-2026-03-22`, line 7) that no other skill has. This suggests active iteration on this particular skill.

8. **process-leads explicitly forbids worktrees** (line 79) with a detailed explanation of why they don't work for this use case. This is an anti-pattern note likely born from experience.

9. **adjudicate can invoke paper-process mid-execution** (lines 158-162) to acquire missing papers it discovers while adjudicating. This makes it the only skill that can trigger the full pipeline as a side effect of analysis.

10. **The `pks` CLI is the sole interface to the propstore** from the plugin's perspective. Every propstore operation in extract-claims goes through `pks concept add`, `pks concept add-value`, `pks context add`, or `pks claim validate-file`. The plugin never directly reads or writes propstore YAML files -- it uses the CLI as an abstraction layer.
