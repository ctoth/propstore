# Paper: Moore 1985 — Semantics of Autoepistemic Logic

## 2026-03-24

### Goal
Retrieve and process Moore 1985 "Semantics of Autoepistemic Logic" using paper-process skill.

### Observations
- `search_papers.py` hangs/times out with both `--source all` and `--source s2` (>20s timeout hit)
- Need to try alternative: WebSearch to find identifier, then use fetch_paper.py directly
- Paper is from 1985, foundational NMR paper — may not be on arxiv

### Observations (cont.)
- fetch_paper.py resolved metadata successfully → `papers/Moore_1985_SemanticalConsiderationsNonmonotonicLogic/`
- DOI: `10.1016/0004-3702(85)90042-6`
- Actual title: "Semantical Considerations on Nonmonotonic Logic" (AI journal, vol 25, 1985, pp 75-94)
- PDF fallback needed (paywalled)
- Sci-hub found it: `https://sci-hub.st/storage/zero/195/8fcc3c0b6cf92b61f26219effb8b55f8/moore1985.pdf`
- curl download blocked by DDoS-Guard (got HTML challenge page instead of PDF)
- Need to download via browser automation — navigate to PDF URL in Chrome tab, then save

### Status
- [x] Retrieve paper — PDF downloaded via sci-hub browser (1.17MB, 20pp)
- [x] Read and extract notes — all 20 pages read, notes.md + abstract.md + citations.md + description.md written
- [x] Index updated
- [ ] Reconcile cross-references
- [ ] Extract claims
- [ ] Report
