# Hunter 2017 COH verification

Workstream item: T4.7. The workstream labels this "Caminada-Wu 2009 COH"; `rg -F "Caminada-Wu"` finds only the workstream. The implemented production surface cites Hunter and Thimm/Hunter probabilistic argumentation, so I verified the actual implemented citation.

Opened page image:
- `papers/Hunter_2017_ProbabilisticReasoningAbstractArgumentation/pngs/page-009.png`.

Verified paper content:
- Standard epistemic constraints include COH: for an attack from `A` to `B`, the probability of `A` is constrained by the probability of `B` as `P(A) <= 1 - P(B)`.

Implementation checked:
- `propstore/praf/engine.py::enforce_coh`.
- Tests assert COH requires attacks and is applied before preference-layer defeat rewriting.

Result: matches the opened PDF page for the citation actually used by the code. The workstream paper label is mismatched.
