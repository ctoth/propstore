# Notes: Bench-Capon 2003 Retrieval

## Goal
Retrieve and process "Persuasion in practical argument using value-based argumentation frameworks" by Bench-Capon 2003.

## Observations
- search_papers.py search didn't find exact match on arxiv (paper is from 2003, likely journal)
- fetch_paper.py resolved metadata via DOI 10.1093/logcom/13.3.429 but couldn't download PDF (fallback_needed=true)
- Directory created: papers/Bench-Capon_2003_PersuasionPracticalArgumentValue-based/
- metadata.json written with title, authors, year
- Sci-Hub blocked by WebFetch tool
- OUP open access URL (https://academic.oup.com/logcom/article-pdf/13/3/429/4241286/130429.pdf) returns HTML not PDF (likely auth wall)
- Semantic Scholar says paper is "BRONZE" open access
- S2 corpus ID: 11245194, paper ID: ac1f090bd4a6dd5dfac17500335fa9fd27aef88d

## Current blocker
- OUP returns 403 (Cloudflare challenge) -- cannot download via curl
- Sci-Hub blocked by WebFetch tool
- Liverpool repository doesn't have this paper
- ResearchGate returns 403
- No browser automation tools available (no Playwright, no Claude-in-Chrome)
- Removed invalid HTML file from paper directory
- **BLOCKED: Need Q to manually download PDF to papers/Bench-Capon_2003_PersuasionPracticalArgumentValue-based/paper.pdf**

## What exists
- papers/Bench-Capon_2003_PersuasionPracticalArgumentValue-based/metadata.json (title, authors, year, DOI)
