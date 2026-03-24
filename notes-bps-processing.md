# BPS Paper Processing Notes

## Paper
- **Title:** Building Problem Solvers
- **Authors:** Kenneth D. Forbus, Johan de Kleer
- **Publisher:** MIT Press (A Bradford Book)
- **Year:** 1993 (confirming from copyright page)
- **Pages:** 727 (PDF pages)
- **Directory name:** Forbus_1993_BuildingProblemSolvers

## Status
- [x] Identified paper metadata from cover/title pages
- [ ] Confirmed year from copyright page
- [ ] Created directory structure
- [ ] Moved PDF to paper directory
- [ ] Converted pages to PNGs
- [ ] Wrote chunk reader template prompt
- [ ] Dispatched chunk reader agents
- [ ] Synthesized notes
- [ ] Wrote description.md, abstract.md, citations.md
- [ ] Ran reconcile
- [ ] Updated index.md

## Chunk Plan
727 pages / 50 = 15 chunks:
- Chunk 1: 000-049
- Chunk 2: 050-099
- Chunk 3: 100-149
- Chunk 4: 150-199
- Chunk 5: 200-249
- Chunk 6: 250-299
- Chunk 7: 300-349
- Chunk 8: 350-399
- Chunk 9: 400-449
- Chunk 10: 450-499
- Chunk 11: 500-549
- Chunk 12: 550-599
- Chunk 13: 600-649
- Chunk 14: 650-699
- Chunk 15: 700-726

## Observations
- PDF is a library scan (Northwestern University Library sticker on p.1)
- Some pages are blank (p.2, p.3, p.5 are blank)
- This is a classic AI textbook covering TMS, ATMS, constraint propagation, qualitative physics
- Highly relevant to propstore project (de Kleer is co-author, covers ATMS extensively)
- Copyright page confirmed: © 1993 Massachusetts Institute of Technology, ISBN 0-262-06157-0
- PDF is 114MB — too large for text extraction via Read tool
- Publisher: MIT Press (A Bradford Book), Cambridge MA

## Book Structure (from TOC, pages 8-14)
1. Preface (p.1) | 2. Introduction (p.9) | 3. Classical Problem Solving (p.19)
4. Pattern-Directed Inference Systems (p.69) | 5. Extending PDIS (p.109)
6. Intro to TMS (p.151) | 7. JTMS (p.171) | 8. Putting JTMS to Work (p.197)
9. Logic-Based TMS (p.265) | 10. Putting LTMS to Work (p.309)
11. Qualitative Process Theory (p.347) | 12. ATMS (p.425)
13. Improving TMS Completeness (p.455) | 14. Putting ATMS to Work (p.495)
15. Antecedent Constraint Languages (p.535) | 16. Assumption-Based Constraint Languages (p.589)
17. Tiny Diagnosis Engine (p.619) | 18. Symbolic Relaxation (p.647)
19. Some Frontiers (p.681) | A. Programs to Work (p.691) | Index (p.695)
Note: book page numbers have offset from PDF page numbers (front matter)

## Current Status (updated after v2 dispatch)
- All 727 PNGs converted successfully
- **First dispatch (v1): ALL 15 agents FAILED** — they restated the task and waited for confirmation instead of executing. The CLAUDE.md "restate before acting" rule overrode the worker identity declaration. Zero chunk files produced.
- **Second dispatch (v2): Fixed prompt** — added explicit "Do NOT restate, do NOT wait, start IMMEDIATELY" instructions.
- **v2 results so far (8/15 complete):**
  - chunk-000-049.md: DONE — Front matter, Preface, Intro, CPS begins
  - chunk-200-249.md: DONE — JTMS code walkthrough, JTRE, dependency-directed search
  - chunk-250-299.md: DONE — JSAINT, LTMS intro, BCP algorithm
  - chunk-400-449.md: DONE — QP Theory examples, ATMS basics/labels
  - chunk-500-549.md: DONE — CLTMS impl, Putting ATMS to Work, ATRE, planning
  - chunk-550-599.md: DONE — Ch15 TCON constraint language
  - chunk-600-649.md: DONE — ATCON, Tiny Diagnosis Engine
  - chunk-700-726.md: DONE — Ch19 end, Appendix A, Index
  - chunk-050-099.md: DONE — CPS algebra, Ch4 PDIS begins, TRE design
  - chunk-100-149.md: DONE — TRE impl, natural deduction, Ch5 FTRE begins
  - chunk-350-399.md: DONE — Ch10 end, Ch11 QP Theory / TGIZMO
  - chunk-150-199.md: DONE — FTRE examples, Ch6 TMS intro, Ch7 JTMS begins
  - chunk-450-499.md: DONE — ATMS algorithms/code, Ch13 TMS completeness
  - chunk-700-726.md: DONE (verified by v2 agent, already complete from v1)
  - chunk-300-349.md: DONE — LTMS code, LTRE design, indirect proof
  - chunk-650-699.md: DONE — Model-based diagnosis, WALTZER CSP, Ch19 Frontiers
- **ALL 15 CHUNKS COMPLETE** — 374KB total extracted notes
- Next: synthesize into notes.md, then write description/abstract/citations

## Completed Prep
- Directory created: papers/Forbus_1993_BuildingProblemSolvers/ with pngs/ and chunks/
- PDF moved from papers/BPS-Searchable.pdf to papers/Forbus_1993_BuildingProblemSolvers/paper.pdf
- Chunk reader template prompt written to prompts/bps-chunk-reader.md
- Foreman and subagent protocols read
- prompts/ and reports/ directories created
- All 727 pages converted to PNGs
- TOC read and book structure documented

## Completed Steps
1. [x] Read all 15 chunk files (via parallel agents)
2. [x] Synthesize into notes.md (via synthesis agent, 400 lines, 34KB)
3. [x] Write description.md, abstract.md, citations.md
4. [x] Run reconcile — 5 papers already in collection, 4 new leads, 12 conceptual links
5. [x] Update papers/index.md
6. [x] ALL DONE
