# Notes: Prakken & Horty 2012 Paper Processing

## Task
Process paper: Prakken, H. and Horty, J. (2012). "An appreciation of John Pollock's work on the computational study of argument." Argument & Computation, 3(1), 1-19.

## Observations
1. DOI `https://doi.org/10.1080/19462166.2012.662356` - fetch_paper.py fails with "Could not resolve metadata"
2. Bare DOI `10.1080/19462166.2012.662356` - same failure
3. Title search via search_papers.py launched as background task but produced no output after 15+ seconds - likely hanging or erroring silently

## Current State
- Paper not yet retrieved
- Need to try alternative approach: use sci-hub via Chrome to get the PDF directly, then manually create metadata

## Resolution
- Title search on S2 found correct DOI: `10.1080/19462166.2012.663409` (prompt DOI was wrong)
- fetch_paper.py succeeded with correct DOI, created `papers/Prakken_2012_AppreciationJohnPollock'sWork/`
- PDF was paywalled (fallback_needed=true), retrieved via sci-hub Chrome automation
- PDF is 382KB, 20 pages, valid

## Paper Content (pages 0-9 read so far)
- **Title:** An appreciation of John Pollock's work on the computational study of argument
- **Authors:** Henry Prakken, John Horty
- **Venue:** Argument & Computation, Vol 3, No 1, March 2012, pp 1-19
- **Type:** Survey/appreciation paper reviewing Pollock's contributions to computational argumentation

### Key content observed:
1. **Section 1 (Intro):** Pollock (1940-2009) was a philosopher who contributed to defeasible reasoning and AI. Developed one of the first formal systems for argumentation-based inference.
2. **Section 2 (Historical sketch):** Traces history from defeasibility in legal philosophy (Hart 1949), through Pollock's epistemological work, to AI implementations. Notes connection to Reiter's default logic, non-monotonic reasoning community.
3. **Section 3 (Formal results):**
   - **3.1 Common features:** Pollock's formalization of defeasible reasoning. Reasons from knowledge base using inference rules (conclusive/defeasible). Arguments as lines of inference. Definitions of defeat (rebutting vs undercutting).
   - Figure 1: Example with birds/penguins/ostriches showing defeaters and subarguments
   - Definition 3.1: Self-defeating arguments
   - Definition 3.2: Semantics - arguments in/out at level 0..n, ultimately undefeated
   - **3.2 Semantics:** Pollock's notion of argument construction and defeat. Inference graphs vs argument trees. Partial defeat status assignment (Definition 3.3).
   - Labelling approach: arguments assigned in/out/undecided
   - Self-defeating arguments discussion (parallel and serial self-defeat, Figures 2-3)

## Current State
- Reading pages 0-9 of 20
- Need to continue reading pages 10-19
- Then write notes.md, description.md, abstract.md, citations.md
