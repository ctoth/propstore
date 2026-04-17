# Oikarinen Strong-Equivalence Kernel Search

Date: 2026-04-16

Workstream phase: `plans/paper-grounded-test-suite-workstream-2026-04-16.md` Phase 5.

## Result

No production implementation of Oikarinen strong-equivalence kernels exists in the current repo state.

Searched surfaces:

- `propstore/`
- `tests/`
- `docs/`
- `plans/`
- `reviews/`

Search terms included:

- `strong equivalence`
- `strong_equivalence`
- `a-kernel`
- `a*-kernel`
- `kernel`
- `Oikarinen`
- `equivalence`

The only direct Oikarinen implementation-relevant hits were review/workstream documentation:

- `reviews/2026-04-16-code-review/axis-3a-argumentation.md` says Oikarinen 2010 kernel-based strong equivalence is not implemented.
- `reviews/2026-04-16-code-review/paper-manifest.md` describes the paper content.
- `plans/paper-grounded-test-suite-workstream-2026-04-16.md` defines this Phase 5 search.

## Decision

No `tests/test_strong_equivalence_kernels.py` was added because there is no production kernel surface to test. No placeholder or xfail tests were committed.

Relevant paper image paths checked during Phase 0 and still serving as the grounding for a future implementation workstream:

- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-05.png`
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-07.png`
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-12.png`
