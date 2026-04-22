# Booth-Meyer 2006 restrained revision verification

Workstream item: T1.3.

Opened page image:
- `papers/Booth_2006_AdmissibleRestrainedRevision/pngs/page-011.png` (printed p.138).

Verified paper content:
- Section 4 states the restrained-revision postulate: among non-minimal valuations, the old preorder is preserved except same-rank alpha/non-alpha ties are split so alpha worlds become more plausible.
- Definition 4 names revision operators satisfying RAGM plus this RR postulate as restrained revision.

Implementation checked:
- `propstore/belief_set/iterated.py::restrained_revise`.
- The implementation ranks minimal formula worlds first, preserves old ranks for the rest, and uses an alpha-before-non-alpha tie key inside old equal-rank classes.

Result: matches the opened PDF page.
