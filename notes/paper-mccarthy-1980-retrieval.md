# McCarthy 1980 — Circumscription Retrieval

## 2026-03-24

### Goal
Retrieve and process McCarthy 1980 "Circumscription — A Form of Non-Monotonic Reasoning" (Artificial Intelligence journal).

### Done
- Searched via search_papers.py — found S2 match (no DOI listed, year shown as 1995)
- Used known DOI `10.1016/0004-3702(80)90011-9` with fetch_paper.py — metadata resolved successfully
- Directory created: `papers/McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning/`
- metadata.json written
- Sci-hub page loaded successfully in Chrome, PDF URL extracted: `https://sci-hub.st/storage/2024/195/2dbd0d4098f80cd06a8856da6f202627/mccarthy1980.pdf`
- curl download returned only 898 bytes of HTML — NOT a valid PDF

### Retrieval COMPLETE
- curl failed (sci-hub blocks without session cookies — returns 898 byte HTML redirect)
- Used JavaScript blob fetch within Chrome page context — successfully downloaded 1,175,728 bytes
- Copied from Downloads to paper directory
- Verified: PDF document, version 1.2, 13 pages
- Source: sci-hub via DOI 10.1016/0004-3702(80)90011-9

### Files
- `papers/McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning/paper.pdf` — 13-page PDF
- `papers/McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning/metadata.json` — S2 metadata

### Reading COMPLETE
- All 13 pages read (pp. 27-39)
- Paper structure: 8 sections + references
  1. Introduction — The Qualification Problem
  2. The Need for Non-Monotonic Reasoning (monotonicity property, predicate vs domain circumscription)
  3. Missionaries and Cannibals (illustrative example)
  4. The Formalism of Circumscription (core definition, eq 1)
  5. Domain Circumscription (eq 20-21)
  6. The Model Theory of Predicate Circumscription (minimal entailment, theorem)
  7. More on Blocks (frame problem application, prevents predicate)
  8. Remarks and Acknowledgments (8 observations)
- Key formal content: circumscription schema (eq 1), joint circumscription (eq 2), domain circumscription (eq 20), minimal models, submodel relation
- 12 references total

### Paper Reading COMPLETE — All output files written
- notes.md: comprehensive notes with all equations, examples, testable properties
- abstract.md: verbatim abstract + interpretation
- citations.md: all 12 references + 4 key follow-ups
- description.md: 3-sentence summary with tags

### Next
- Step 7: reconcile (cross-reference with existing papers)
- Step 8: update papers/index.md
- Step 4: extract-claims
- Step 5: report
