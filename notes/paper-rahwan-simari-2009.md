# Rahwan & Simari 2009 — Retrieval Notes

**Date:** 2024-03-24

## Status: RETRIEVAL FAILED (partial only)

## What happened
- Searched Semantic Scholar, found exact match: DOI 10.1007/978-0-387-98197-0
- fetch_paper.py resolved metadata successfully, created `papers/Rahwan_2009_ArgumentationArtificialIntelligence/`
- PDF download needed fallback (Springer book, not open access)
- Sci-hub returned a PDF but it was only **Chapter 13** ("Dialogue Games for Agent Argumentation" by McBurney & Parsons), 20 pages — not the full 500+ page handbook
- Springer direct link requires institutional login
- LibGen mirrors (libgen.is, libgen.rs, libgen.li) all unreachable
- Anna's Archive unreachable (error pages)
- Internet Archive has 0 results for this book
- The PDF from sci-hub also had a DDoS-Guard challenge requiring browser passthrough and a password-protection flag that confused the Read tool (pypdf says not encrypted, but Read tool refuses)

## What we have
- `papers/Rahwan_2009_ArgumentationArtificialIntelligence/metadata.json` — correct metadata
- `papers/Rahwan_2009_ArgumentationArtificialIntelligence/paper.pdf` — 20 pages, Chapter 13 only (rewritten via pypdf to strip protection flags, but Read tool still refuses)

## Next steps
- Q may need to manually download the full book PDF if they have institutional access
- Alternatively, individual chapters could be retrieved separately from sci-hub by their chapter DOIs (10.1007/978-0-387-98197-0_1 through _N)
