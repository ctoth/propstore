# Pearl 2000 — Causality: Models, Reasoning, and Inference

## 2026-03-24 — Retrieval session

### GOAL
Retrieve and process Pearl 2000 "Causality" book PDF using paper-process skill.

### STATE
- Plugin root: `/c/Users/Q/.claude/plugins/cache/research-papers-marketplace/research-papers/3.3.4`
- CLAUDE_PLUGIN_ROOT env var is not set in bash — need to use full path
- Chrome is available (tabs_context_mcp works, have tab group 1324347735)
- Paper-retriever skill read — uses search_papers.py then fetch_paper.py
- This is a BOOK not a paper — may need special handling (partial PDF, chapter, etc.)

### DONE
1. search_papers.py found the book via S2 (DOI: 10.2307/3182612 — actually a book review DOI)
2. fetch_paper.py created directory, metadata — PDF fallback needed
3. Sci-hub with book review DOI returned Hitchcock 2001 review, not the book
4. Sci-hub with actual book DOI (10.1017/CBO9780511803161) — not in database
5. WebSearch found PDF at ILLC UvA archive (2nd edition, 2009)
6. Downloaded: 7.4MB, 487 pages, valid PDF
7. Fixed metadata DOI to 10.1017/CBO9780511803161
8. Converting to page images (background task bolvl7eaf — 487 pages, will take a while)

### OBSERVATIONS
- PDF is password-protected — Read tool rejects even ghostscript-decrypted version
- magick conversion IS working on the encrypted PDF — ~90+ pages done as of last check
- Read first 10 page images successfully: cover, title, copyright, TOC
- SECOND EDITION (2009), ISBN 978-0-521-89560-6
- Book TOC structure (10 chapters):
  - Ch 1: Intro to Probabilities, Graphs, Causal Models (p.1)
  - Ch 2: Theory of Inferred Causation (p.41)
  - Ch 3: Causal Diagrams and Identification of Causal Effects (p.65)
  - Ch 4: Actions, Plans, and Direct Effects (p.107)
  - (more chapters to read from TOC pages 010+)
- PDF page offset: page-008.png = book page vii (TOC). Book p.1 ~ PDF page ~15

### KEY CONTENT READ
- Preface 1st ed (p.016-019): Two fundamental questions of causality, Pearl's shift from empiricist to causal realism
- Preface 2nd ed (p.020): Ch 11 new, corrections/updates to all chapters
- Ch 1 (p.022-059): Probability theory, Bayesian networks, d-separation, Markov condition, causal BNs, functional causal models, structural equations, do-operator intro, counterfactuals in functional models
- Ch 3 (p.086-108): Causal diagrams, identification of causal effects, intervention in Markovian models, back-door criterion (Def 3.3.1), front-door criterion (3.3.2), do-calculus (Theorem 3.4.1 — three rules), graphical tests of identifiability
- Ch 7 (p.222-250): Structural counterfactuals, causal model definition (Def 7.1.1), submodel (7.1.2), effect of action (7.1.3), potential response (7.1.4), counterfactual (7.1.5), axioms: composition, consistency/effectiveness, reversibility
- Ch 10 (p.330-340): Actual causation, sustenance (Def 10.5.1), causal beams (Def 10.3.1), natural beams, actual cause (Def 10.3.3), contributory cause (Def 10.3.4)

### NEXT
- Write notes.md (synthesize all readings)
- Write description.md, abstract.md, citations.md
- Update index.md
- Run extract-claims skill
- Write report
