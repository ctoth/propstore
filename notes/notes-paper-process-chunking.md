# Paper-Process Plugin Survey: Chunking and Reliability

**GOAL:** Understand how paper-process works end-to-end and identify the most reliable way to process 6 papers without agents dying mid-paper.

**Surveyed repo:** `C:/Users/Q/code/research-papers-plugin/`

---

## 1. End-to-End Flow (paper-process skill)

**File:** `C:/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/paper-process/SKILL.md`

The paper-process skill is a 5-step sequential orchestrator:

1. **Retrieve** (paper-retriever skill) -- download PDF via waterfall: arxiv direct -> S2 open access -> unpaywall -> sci-hub browser automation
2. **Read** (paper-reader skill) -- convert PDF to PNGs via ImageMagick, read every page image, write notes.md + description.md + abstract.md + citations.md, run reconcile, update index.md
3. **Clean up** -- delete source PDF from papers/ root (only if source was a local file)
4. **Extract claims** (extract-claims skill) -- concept registration + claim extraction into claims.yaml + validation
5. **Report** -- write summary to `./reports/paper-$SAFE_NAME.md`

Error handling is fail-fast: retrieval failure stops everything (line 59), reading failure skips claim extraction (line 60).

---

## 2. Paper-Reader: How Large Papers Are Handled

**File:** `C:/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/paper-reader/SKILL.md`

### Size threshold: 50 pages

**<=50 pages (Step 2A, line 92-97):** The agent reads EVERY page image itself. No delegation, no chunking. The skill is explicit: "34 pages = 34 Read tool calls." It warns: "Agents routinely skip pages to save tokens -- this produces incomplete notes" (line 94).

**>50 pages (Step 2B, line 100-157):** Chunk protocol kicks in:
- Split into 50-page chunks (pages 000-049, 050-099, etc.)
- Write a template prompt to `./prompts/paper-chunk-reader.md`
- Dispatch one subagent per chunk in parallel
- Each chunk agent writes to `chunks/chunk-START-END.md`
- After all chunks complete, synthesize into unified notes.md
- Abstract and citations can be delegated to haiku subagents (lines 336, 356)

### What one agent must do for a <=50pp paper

After reading all pages, the SAME agent must:
- Step 3: Write exhaustive notes.md (format template is ~80 lines of structure, demands every equation, every parameter, page citations on everything)
- Step 4: Write description.md (3 sentences + tags)
- Step 5: Write abstract.md (verbatim + interpretation)
- Step 6: Write citations.md (full reference list + key citations)
- Step 7: Run reconcile skill (cross-reference against collection)
- Step 8: Update papers/index.md

**This is the primary bottleneck.** A 30-page paper means ~30 image reads (each consuming substantial tokens for the image content) plus all the structured output generation. There is zero delegation for papers under the 50-page threshold.

---

## 3. Extract-Claims: The Second Context Bomb

**File:** `C:/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/extract-claims/SKILL.md` (851 lines)

When paper-process invokes extract-claims after paper-reader, the agent must:
1. Read notes.md (the big file it just wrote)
2. Read the concept registry (`concepts/*.yaml`)
3. Read form definitions (`pks form list`)
4. Load condition vocabulary (`pks concept categories`)
5. Read existing claims files for duplicate detection
6. Register missing concepts (one `pks concept add` per new concept)
7. Extract up to 8 claim types: parameter, equation, observation, model, measurement, mechanism, comparison, limitation
8. Write claims.yaml
9. Run validation (`pks claim validate-file`)
10. Fix and re-validate until clean

**Combined cost:** paper-process = paper-reader (all pages + 8 output steps) + extract-claims (registry reads + multi-type extraction + validation). For a 30-page paper this is likely 200k+ tokens of context.

---

## 4. Retriever, Reader, and Claims Can Be Invoked Separately

Each is an independent skill with its own SKILL.md:

| Skill | Input | Output | Can run alone? |
|-------|-------|--------|----------------|
| `paper-retriever` | URL/DOI/title | `papers/Dir/paper.pdf` + `metadata.json` | Yes |
| `paper-reader` | PDF path or paper dir | notes.md, description.md, abstract.md, citations.md, index update | Yes |
| `extract-claims` | Paper directory | claims.yaml | Yes (needs notes.md) |

paper-process just orchestrates them sequentially. Nothing prevents calling them as three separate agent invocations.

---

## 5. Skill Frontmatter: No Model or Timeout Specs

All skills have `disable-model-invocation: false`. None specify:
- `model:` (no model preference anywhere in frontmatter)
- `timeout:` (no timeout configuration)
- `context:` (only the `research` skill has `context: fork`)

The only model mentions are soft recommendations in paper-reader body text: "delegate abstract to a **haiku** subagent" (line 336) and "delegate citations to a **haiku** subagent" (line 356) -- but only for chunked (>50pp) papers.

**Surprising finding:** The `process-leads` skill (line 68) explicitly documents the context-death problem: "Every paper-process invocation runs as a subagent, even in sequential mode. This protects the foreman's context window from the large volume of page-reading output that paper-process generates. Without subagents, processing 3-4 papers fills the context window and forces compaction, losing earlier work."

This is the operational experience talking. It directly names the failure mode.

---

## 6. Existing Mechanisms for Breaking Work Into Smaller Pieces

1. **Chunking (>50pp only):** 50-page chunk protocol with parallel subagents (paper-reader Step 2B, line 100-157)
2. **process-leads skill:** `--parallel M` flag for concurrent paper-process subagents, wave-based batching. Explicitly mandates subagents even in sequential mode (line 68-69). File: `C:/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/process-leads/SKILL.md`
3. **process-new-papers skill:** Sequential processing, one paper at a time via paper-reader. File: `C:/Users/Q/code/research-papers-plugin/plugins/research-papers/skills/process-new-papers/SKILL.md`
4. **Haiku delegation:** abstract.md and citations.md can be delegated to haiku subagents, but only documented for chunked papers (paper-reader lines 336, 356)

### Key gaps

- For papers <=50 pages, there is NO mechanism to break paper-reader into smaller pieces. One agent does everything.
- paper-process bundles reader + claims extraction into one agent. There is no option to split these into two separate agent invocations.
- process-new-papers does NOT use subagents -- it invokes paper-reader directly (line 37: `/research-papers:paper-reader papers/filename.pdf`), meaning the foreman agent itself does the reading. This will die on paper 2 or 3.

---

## 7. The Retrieval Script (fetch_paper.py)

**File:** `C:/Users/Q/code/research-papers-plugin/plugins/research-papers/scripts/fetch_paper.py`

Pure Python, no LLM needed. Waterfall download strategy (line 207-230):
1. Direct PDF URL from metadata (arxiv, ACL, S2 open access)
2. Arxiv PDF URL construction from arxiv_id
3. ACL direct download
4. Unpaywall API lookup

If all fail, returns `fallback_needed: true` and the skill falls back to browser automation (sci-hub). The script itself is lightweight -- retrieval is not a context bottleneck. The bottleneck is reading.

---

## 8. Key Question: Most Reliable Way to Process 6 Papers

### The problem

One paper-process invocation consumes enormous context (30 page images + exhaustive notes + claims extraction). Processing 6 papers sequentially in one agent session is impossible -- the process-leads skill already documents that "3-4 papers fills the context window and forces compaction."

### Recommended approach (based on what the plugin already knows works)

**Use the process-leads pattern: one subagent per paper, foreman only orchestrates.**

The process-leads skill (lines 67-89) already has the right architecture:
- Foreman dispatches one subagent per paper
- Each subagent runs the full paper-process pipeline in isolation
- Subagent context death only kills that paper, not the session
- Foreman's context stays clean for orchestration
- Sequential mode: dispatch one, wait, dispatch next
- Parallel mode (`--parallel M`): waves of M concurrent agents

### Concrete options, ranked by reliability

**Option A: process-leads skill directly (if papers are cited in existing collection)**
If the 6 papers appear as "New Leads" in existing paper citations, just run:
```
/research-papers:process-leads 6
```
This uses the proven subagent-per-paper pattern.

**Option B: Manual foreman pattern (if papers are arbitrary URLs/DOIs)**
The foreman dispatches 6 subagents (sequentially or in waves of 2-3), each running paper-process for one paper. This is what process-leads does internally -- replicate the pattern manually.

**Option C: Split retrieval from reading**
1. Run all 6 retrievals yourself (fetch_paper.py is lightweight, no LLM context cost)
2. Then dispatch one subagent per paper for paper-reader only
3. Then dispatch one subagent per paper for extract-claims only

This has the lowest per-agent context cost but triples the number of agent invocations.

**Option D: Further decompose paper-reader (requires skill changes)**
Lower the chunk threshold from 50 to 20-25 pages, so even "normal" papers get chunked into parallel subagents. This would be a skill modification, not currently supported.

### What will NOT work

- Running paper-process 6 times sequentially in one agent session (context death around paper 3)
- Using process-new-papers as-is (does not use subagents, foreman does the reading)
- Trusting a single agent to read + extract claims for all 6 papers

### Risk factors for individual paper agents dying

- Papers over ~35 pages may exhaust context even for a single paper-process run (reading + claims)
- The extract-claims skill is 851 lines of instructions alone -- the skill prompt itself consumes significant context before any work begins
- Papers with many equations/parameters produce very long notes.md, which extract-claims must then re-read

### Mitigation for large individual papers

- Pre-check page counts before dispatching (use `pdfinfo` or count PNGs after conversion)
- For papers >35 pages, consider splitting paper-reader and extract-claims into separate agent invocations (Option C above)
- For papers >50 pages, the existing chunk protocol should engage automatically

---

## Files Referenced

| File | What it tells us |
|------|------------------|
| `plugins/research-papers/skills/paper-process/SKILL.md` | Orchestrator: retrieve -> read -> cleanup -> claims -> report |
| `plugins/research-papers/skills/paper-reader/SKILL.md` | 50-page chunk threshold, exhaustive reading requirement, 8 output steps |
| `plugins/research-papers/skills/paper-retriever/SKILL.md` | Waterfall download, browser automation fallback |
| `plugins/research-papers/skills/extract-claims/SKILL.md` | 851-line claim extraction, concept registration, validation loop |
| `plugins/research-papers/skills/process-leads/SKILL.md` | Proven subagent-per-paper pattern, documents context death at 3-4 papers |
| `plugins/research-papers/skills/process-new-papers/SKILL.md` | Sequential processing WITHOUT subagents -- will die on multi-paper runs |
| `plugins/research-papers/scripts/fetch_paper.py` | Lightweight Python retrieval, no LLM context cost |
| `plugins/research-papers/notes-2026-03-21.md` | Recent code review session, skill improvements |
| `plugins/research-papers/README.md` | Installation, skill listing, claims pipeline overview |
