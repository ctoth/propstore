# Baumann & Brewka 2010 — Retrieval Notes

## 2026-03-24

**GOAL:** Retrieve and process "Expanding Argumentation Frameworks: Enforcing and Monotonicity Results"

**STATUS:** Retrieval in progress — PDF not yet obtained

### What I know
- DOI: 10.3233/978-1-60750-619-5-75
- Published in COMMA 2010, Frontiers in AI and Applications vol 216, pp 75-86
- Authors: Ringo Baumann, Gerhard Brewka (both Leipzig University)
- Directory exists: papers/Baumann_2010_ExpandingArgumentationFrameworksEnforcing/ with metadata.json
- Semantic Scholar ID: d18743f8412e5895429f9ad28334d4448ca41808

### Retrieval attempts
1. **fetch_paper.py** — fallback_needed=true, no open-access PDF found via Unpaywall
2. **sci-hub.st** — "статья отсутствует в базе" (not in database)
3. **sci-hub.se** — DNS unreachable
4. **Baumann's Leipzig page** — publications.html has no direct PDF links for this paper
5. **ResearchGate direct link** — curl returned HTML (cookie wall), not PDF. 24KB HTML file.
6. **WebSearch for filetype:pdf** — no direct hit for this specific paper

### Retrieval SUCCESS
- ResearchGate download via Chrome worked — PDF downloaded to Downloads, moved to paper dir
- 12 pages, PDF version 1.4, 127KB
- Converted to 12 page PNGs

### Paper content (read all 12 pages)
- **Problem:** How to revise a Dung AF by adding new arguments that interact with old ones
- **Key concepts:** Normal, strong, weak expansions; enforcement (conservative, liberal); monotonicity
- **Definitions 5-6:** Expansion types (normal/strong/weak) and enforcement types (conservative/liberal, with or without semantics change)
- **Proposition 1:** Impossibility results for enforcing — normal expansions can't defend all elements of desired set, can't contain all defended elements, etc.
- **Theorem 2:** Conservative (liberal) strong enforcing (exchanging arguments) conditions
- **Theorem 3:** Conservative (liberal) weak enforcing (eliminating arguments) conditions
- **Theorem 4:** Key positive result — any conflict-free set can be enforced by conservative strong expansion (adds one argument + attacks)
- **Theorem 5:** Monotonicity — weak expansions of AF under semantics satisfying directionality preserve extension count and justification state monotonically
- **Corollary 6:** Justification state monotonicity (credulously/skeptically justified args persist)
- **Definition 7:** Expansion chains; Corollary 1 about checking acceptability in initial AF of chain
- 14 references

### Next steps
- Write notes.md, abstract.md, citations.md, description.md
- Update metadata.json with abstract
- Run reconcile, update index.md
- Extract claims
