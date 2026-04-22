# Coste-Marquis et al. 2007 partial AF merge verification

Workstream item: T8.3.

Opened page image:
- `papers/Coste-Marquis_2007_MergingDung'sArgumentationSystems/pngs/page-009.png`.

Verified paper content:
- Merging partial argumentation frameworks is presented as expansion plus fusion.
- Aggregation functions include sum, max, and leximax.
- Definition 18 gives an edit-distance style measure where attack/non-attack mismatches cost 1 and ignorance-related cases cost 0.5.

Implementation checked:
- `C:/Users/Q/code/argumentation/src/argumentation/partial_af.py`.
- Propstore tests for T8.3 exercise tractable routing for partial AF merge and ceiling behavior for general enumeration.

Result: matches the opened PDF page.
