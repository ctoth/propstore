# Paper: Dunne & Wooldridge 2009 - Complexity of Abstract Argumentation

## 2026-03-24 Retrieval Session

**Goal:** Retrieve and process this paper (chapter in Rahwan & Simari 2009 book).

**Status:** Retrieval in progress - PDF download blocked by sci-hub cookie/session requirement.

**Observations:**
- DOI: 10.1007/978-0-387-98197-0_5
- fetch_paper.py resolved metadata from Semantic Scholar successfully
- Paper directory created: `papers/Dunne_2009_ComplexityAbstractArgumentation/`
- metadata.json written with title, authors (P. Dunne, M. Wooldridge), year 2009
- No open-access PDF available (fallback_needed: true)
- Sci-hub has the PDF at: `https://sci-hub.st/storage/zero/1141/7de6125c085533826a285062938c2e49/dunne2009.pdf`
- Browser can load it (contentType: application/pdf), but curl gets 898-byte HTML redirect
- Even with User-Agent and Referer headers, curl still gets the redirect
- Sci-hub appears to require session cookies for direct download

**Current blocker:** Need to either extract browser cookies for curl, use WebFetch, or use browser JS to save the PDF content.

**Next:** Try WebFetch tool or extract cookies from browser session.
