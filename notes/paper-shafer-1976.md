# Shafer 1976 — A Mathematical Theory of Evidence

## 2026-03-24 — Retrieval session

**GOAL:** Retrieve and process Shafer 1976 "A Mathematical Theory of Evidence" (book, Princeton University Press).

**OBSERVATIONS:**
- search_papers.py hangs — Semantic Scholar rate limits (429s), arxiv has nothing (it's a 1976 book)
- fetch_paper.py also fails — S2 ID `4cd91c51098783ec972f6a0ab430cacdd634a5b2` gets URL-prefixed incorrectly
- Created `papers/Shafer_1976_MathematicalTheoryEvidence/` manually with metadata.json
- Book is available on: Internet Archive (archive.org/details/mathematicaltheo0000shaf), JSTOR (DOI: 10.2307/j.ctv10vm1qb), author site (glennshafer.com/books/amte.html)

**CURRENT STATE:** Directory created, metadata written. Need to retrieve PDF via browser (sci-hub with JSTOR DOI, or Internet Archive).

**RETRIEVAL ATTEMPTS:**
- sci-hub (DOI 10.2307/j.ctv10vm1qb): Not in database
- Internet Archive: Lending-only, no direct PDF download
- Author site (glennshafer.com): No book PDF, only retrospective essays
- dokumen.pub: Requires login, untrusted source
- api.pageplace.de preview: Only 32 pages (book is ~297 pages)
- fitelson.org/topics/shafer.pdf: Only 1 page summary
- arxiv 1811.04787: Different paper about DS theory, not the book

**CURRENT BLOCKER:** Cannot find a freely downloadable full PDF of this 1976 book. It's a Princeton University Press publication — copyrighted and behind paywalls. The 2020 reprint (ISBN 9780691214696) is on JSTOR.

**RESOLUTION:** Used 32-page preview from api.pageplace.de (covers front matter through start of Ch.1). Full book is 297 pages — complete PDF unavailable via automated means.

**READING PROGRESS (32 pages):**
- p0: Cover
- p1: Blank
- p2: Half-title
- p3: Blank
- p4: Full title page — Glenn Shafer, Princeton University Press
- p5: Copyright (c) 1976 Princeton University Press
- p6: Dedication (Tempa Shafer, Ralph Fox)
- p7: Blank
- p8: Foreword by A.P. Dempster (p.vii) — Dempster explains Shafer extended/refined his 1960s theory. Theory rebuilt around combining simple support functions and their weights of evidence. Dempster notes Shafer's "lower probabilities" are degrees of belief. Dempster endorses Bayesian inference but acknowledges value of studying weaker belief representations.
- p9: Foreword cont. (p.viii) — Dempster notes Shafer offers weight of conflict as criterion for comparing specifications. Signed July 1975.
- p10: Preface (p.ix) — Shafer attended Dempster's 1971 course at Harvard. Reinterprets Dempster's "lower probabilities" as epistemic probabilities or degrees of belief. Takes rule for combining degrees of belief as fundamental, abandons idea they arise as lower bounds over Bayesian probabilities. Limited to finite sets of possibilities.
- p11: Preface cont. (p.x) — Acknowledgments, written June 26, 1975.

**READING PROGRESS (cont.):**
- p12-14: Table of Contents — 12 chapters: Introduction, Degrees of Belief, Dempster's Rule of Combination, Simple and Separable Support Functions, Weights of Evidence, Compatible Frames of Discernment, Support Functions, Discernment of Evidence, Quasi Support Functions, Consonance, Statistical Evidence, Dual Nature of Probable Reasoning. Bibliography p287, Index p292.
- p18 (book p.3): Ch.1 Introduction opens. Theory is both theory of evidence AND theory of probable reasoning. Heart = Dempster's rule for combining evidence. Uses numbers [0,1] for degrees of support.
- p19 (book p.4): Synopsis section. Theory of chance vs partial belief. Bayesian theory included as special case.
- p20 (book p.5): THREE AXIOMS of belief functions: (1) Bel(empty)=0, (2) Bel(Theta)=1, (3) superadditivity inequality (inclusion-exclusion lower bound). Ming Vase example.
- p21 (book p.6): Degrees of belief s1+s2 <= 1. Dempster's rule = orthogonal sum of belief functions.
- p22 (book p.7): Simple support function defined: Bel(B)=0 if B doesn't contain A, =s if B contains A but B!=Theta, =1 if B=Theta. Separable support functions = combinations of simple support functions. Support functions = coarsenings of separable support functions.
- p23 (book p.8): Weight of evidence w: s = 1 - e^(-w), so w = -log(1-s). Weight-of-conflict conjecture. Quasi support functions.
- p24 (book p.9): Support vs quasi support functions. Consonant support functions (Ch.10), statistical inference (Ch.11), role of assumptions (Ch.12).
- p25 (book p.10): Chance density q:X->[0,1], sum to 1 (eq 1.1). Dime-Store Dice example.
- p26 (book p.11): Chance function Ch(U) = sum of q(x) for x in U (eq 1.2). Three basic rules for chances: Ch(empty)=0, Ch(X)=1, additivity for disjoint sets. Key: additivity rule is what Shafer REJECTS for degrees of belief.
- p27 (book p.12): Doctrine of Chances. Product chance density for compound experiments.
- p28 (book p.13): Compound experiment examples with dice.
- p29 (book p.14): Conditional chance density q_U(x) = q(x)/Ch(U) if x in U, 0 otherwise.

- p30 (book p.15): Conditional chance Ch(V|U) = Ch(U intersect V)/Ch(U). Rule of conditioning.
- p31 (book p.16): Section 4 "Chances as Degrees of Belief" — chances are features of the world, not necessarily features of knowledge/belief. Preview ends mid-section.

**FILES WRITTEN:**
- metadata.json (committed)
- notes.md (committed)
- description.md (staged)
- abstract.md (staged)
- citations.md (staged)

**REMAINING:**
- Update papers/index.md
- Skip reconcile (Step 7) — book, not a paper with typical cross-refs
- Skip extract-claims (Step 4) — only have preview, not enough for meaningful claims
- Write report (Step 5)
