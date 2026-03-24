# Guha 1991 Retrieval Session

## GOAL
Retrieve and process "Contexts: A Formalization and Some Applications" by R.V. Guha (1991 PhD thesis, Stanford)

## FINDINGS
- Paper NOT on arxiv (1991 thesis, predates arxiv)
- search_papers.py with S2 source returned no useful results
- WebSearch found:
  - PostScript file at: http://www-formal.stanford.edu/guha/guha-thesis.ps
  - Semantic Scholar entry: https://www.semanticscholar.org/paper/63dc637595eec644f0462f87996fe90edc85c763
  - ProQuest entry exists but likely paywalled
  - Google Books entry exists (no full text)
  - Also known as STAN-CS-91-1399-Thesis and MCC Tech Report ACT-CYC-423-91

## PLAN
1. Try fetch_paper.py with the S2 paper ID
2. If that fails for PDF, download the .ps file from Stanford and convert to PDF
3. Then proceed with paper-reader and extract-claims skills

## READING PROGRESS
- Pages 0-9 read (of 147)
- Title page says "February 10, 1995" (not 1991 as commonly cited - may be revised version)
- Page 1-2: Contents (rendered blank in PS conversion)
- Page 3: Chapter 1 Introduction - "The Symbolic Model of AI" - KB = declarative encoding + procedures
- Page 4: 1.2 Exceptions - KB sentences not dependent on external context for truth; most general statements have exceptions; default logic needed
- Page 4: 1.2.3 Homogeneity - KBs are homogeneous (single vocabulary, single theory)
- Page 5: 1.3 Problems with this model - Cyc KB (1.5M assertions, wide coverage); 1.3.1 The Vocabulary problem
- Page 6: Vocabulary problem - buying/selling example. Need "upward compatibility" of vocabularies. Vocabulary choice makes assumptions.
- Page 7: 1.3.3 Notation - ist(NaiveMoneyMt A1) means "A1 is true in context NaiveMoneyMt"
- Page 8: "What is a Context" - contexts are rich objects (not just sets of assumptions), capture contextual dependencies. Context = partial description of context + vocabulary + assumptions.
- Page 9: Using Contexts - lifting rules between contexts (ist(NaiveMoneyMt A) -> ist(GTT cost(x List) = A)). Concepts: Decontextualized/Reifying/Decontextualized. Key: McCarthy first introduced contexts in [Advice Taker].

## KEY CONCEPTS SO FAR
- ist(context, formula) - "is true in" predicate - fundamental operation
- Contexts as first-class objects in the logic
- Lifting rules connect formulas across contexts
- Vocabulary assumptions are captured by context choice
- Decontextualization and reification of context-dependent statements

## STATUS
- Pages 0-69 read
- Chunk 000-049 file written (by parallel process, comprehensive)
- Chunk 050-099 file started
- Key content: Ch1 intro, Ch2 logic+lifting formal theory, Ch3 applications in Cyc
- Pages 50-69: Lift-and-Solve strategy, Car Selection Program example, temporal reasoning (fixing time to Now, explicit temporal qualifications, contexts vs defaults, weather/car example)
- No blockers, continuing to read pages 70-146
