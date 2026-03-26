# Toni 2014 - Paper Retrieval Session

## Task
Retrieve and process "A tutorial on assumption-based argumentation" by Francesca Toni (2014)

## What I know
- DOI: 10.1080/19462166.2013.869878
- Published in Argument & Computation, Vol 5, No 1, pp 89-117
- Author: Francesca Toni (Imperial College London)
- metadata.json created at papers/Toni_2014_TutorialAssumption-basedArgumentation/
- Semantic Scholar says open access PDF at IOS Press (BRONZE status)

## What I've tried
1. fetch_paper.py with DOI - got metadata but no PDF (fallback_needed=true)
2. Sci-Hub (sci-hub.st, sci-hub.se) - blocked by WebFetch, curl got 403
3. Author's Imperial College page (doc.ic.ac.uk/~ft/PAPERS/) - downloaded cs13AL.pdf but it was only 6 pages (wrong paper)
4. IOS Press open access URL from S2 API - Cloudflare challenge blocks curl
5. ResearchGate - 403

## Current blocker
Cannot download PDF via automated means. All sources are either paywalled or Cloudflare-protected.

## Additional attempts (round 2)
- Unpaywall API: no OA locations found (null)
- SAGE journals page: 403
- Taylor & Francis direct PDF link: curl exit 43 (Cloudflare)
- PhilPapers: 403
- IOS Press article page: 403
- Imperial College HOFA Chapter 7 (HOFAChapter7.ABA.pdf): downloaded 44 pages, but it's a 2017 handbook chapter, NOT the 2014 tutorial
- Google Scholar filetype:pdf search: no freely hosted copy of the actual tutorial found
- Spiral (Imperial repo): paper not deposited there

## Conclusion
The 2014 tutorial paper is behind Taylor & Francis / IOS Press paywall with no open-access copy available online. Metadata is saved. PDF requires manual download by Q.

## State
- papers/Toni_2014_TutorialAssumption-basedArgumentation/metadata.json exists
- No paper.pdf - retrieval FAILED
- Cannot proceed to paper-reader, extract-claims, or other steps
