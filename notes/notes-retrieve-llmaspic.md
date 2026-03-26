# Retrieval: LLM-ASPIC+ (Fang 2025)

## GOAL
Download PDF of "LLM-ASPIC+: A Neuro-Symbolic Framework for Defeasible Reasoning" (Fang et al., 2025, ECAI, IOS Press)

## DONE
- fetch_paper.py resolved metadata via Semantic Scholar (DOI: 10.3233/FAIA250981)
- Paper directory created: papers/Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible/
- metadata.json written with authors: Xiaotong Fang, Zhaoqun Li, Chen Chen, B. Liao
- PDF download failed via open-access channels (fallback_needed: true)
- Sci-hub: paper not in database
- IOS Press direct: "Download PDF" button exists but redirects to external sites; curl returns 403
- IOS Press volumearticle/75917: also 403

## Session 2 (Chrome browser tools)
- Sci-hub: still not in DB, but says OpenAlex marks open access
- DOI resolves to https://ebooks.iospress.nl/doi/10.3233/FAIA250981
- Download form: POST to /Download/Pdf with id=75917
- curl POST returned 1233 bytes HTML -- needs browser session cookies
- Next: try browser form submit, or ResearchGate, or author page

## STUCK
- IOS Press download needs session cookies from browser

## NEXT
- Try clicking download in browser or extracting cookies
- Try ResearchGate: https://www.researchgate.net/publication/396786209
- Try author page (already open in tab 429207212)
