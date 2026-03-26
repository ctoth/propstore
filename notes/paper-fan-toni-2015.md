# Fan & Toni 2015 — Paper Processing Session

## Date: 2026-03-24

## GOAL
Retrieve, read, and extract claims from Fan & Toni 2015 "On Computing Explanations in Argumentation" (AAAI 2015).

## DONE
- Found paper via web search: AAAI 2015, DOI 10.1609/aaai.v29i1.9420
- fetch_paper.py resolved metadata from Semantic Scholar, created papers/Fan_2015_ComputingExplanationsArgumentation/
- PDF download via fetch_paper.py got 403, but direct curl with User-Agent header succeeded
- PDF verified: 615KB, valid PDF v1.6
- metadata.json written with abstract, authors, year, DOI

## FILES
- papers/Fan_2015_ComputingExplanationsArgumentation/paper.pdf — the paper
- papers/Fan_2015_ComputingExplanationsArgumentation/metadata.json — metadata from S2

## DONE (continued)
- Converted PDF to 7 page images (AAAI conference paper)
- Page 5 rendered black; re-extracted with negation — readable after that
- Read all 7 pages
- Wrote notes.md — exhaustive extraction of definitions, theorems, implementation details
- Wrote description.md, abstract.md, citations.md

## KEY OBSERVATIONS
- Paper introduces "related admissibility" — filters admissible sets to remove freeloading args
- Defines MiE, CoE, MaE explanation types
- Computational mechanism: dispute forests (extension of Dung/Kowalski/Toni dispute trees)
- Works in both AA and ABA settings
- Directly relevant to propstore argumentation + render layers

## DONE (final)
- Cross-references added to notes.md (6 collection matches, 3 new leads)
- papers/index.md updated with Fan_2015 entry
- 3 new concepts registered: related_admissibility, dispute_tree, dispute_forest
- claims.yaml created: 11 claims, validation PASS (0 errors, 0 warnings)
- Report written to reports/paper-Fan_2015_ComputingExplanationsArgumentation.md

## COMPLETE
