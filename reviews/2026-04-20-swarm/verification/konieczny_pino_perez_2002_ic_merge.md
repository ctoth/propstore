# Konieczny-Pino Perez 2002 IC merging verification

Workstream item: T3.6.

Opened page image:
- `papers/Konieczny_2002_MergingInformationUnderConstraints/pngs/page-012.png`.

Verified paper content:
- The merge operators are model-theoretic: interpretations are ordered by aggregate distance to the input profile, then constrained by the integrity constraint.
- The distance aggregation examples include sum-like and max-like orderings over distances to profile members.
- Unsatisfied profile members should not shift winners by contributing an ordinary finite distance.

Implementation checked:
- `propstore/belief_set/ic_merge.py::merge_belief_profile`.
- `_distance_to_formula` returns `math.inf` for unsatisfied profile members and the merge code supports sum and gmax aggregators.
- Enumeration limits raise partial/ceiling results rather than silently truncating.

Result: matches the opened PDF page.
