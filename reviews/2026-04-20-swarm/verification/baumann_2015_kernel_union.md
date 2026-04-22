# Baumann 2015 kernel union verification

Workstream items: T6.2, T10.4.

Opened page images:
- `papers/Baumann_2015_AGMMeetsAbstractArgumentation/pngs/page-002.png` (printed p.2736).
- `papers/Baumann_2015_AGMMeetsAbstractArgumentation/pngs/page-003.png` (printed p.2737).

Verified paper content:
- The paper defines kernel-based Dung-logics and uses kernel equality as the syntactic handle for equivalence.
- Theorem 5 states that when the model intersection is non-empty, the expansion result is the union of the corresponding kernels.
- Lemma 6 connects non-empty model intersection to the kernel-union construction being free of the relevant contradiction.

Implementation checked:
- `C:/Users/Q/code/argumentation/src/argumentation/af_revision.py::baumann_2015_kernel_union_expand`.
- `stable_kernel` and `baumann_2015_kernel` preserve the argument set and remove semantics-redundant non-self attacks from self-attacking sources for stable kernels.
- `C:/Users/Q/code/argumentation/tests/test_af_revision.py` checks kernel union, idempotence, and semantics-specific kernels.

Result: matches the opened PDF pages for the stable-kernel subset implemented by the dependency.
