# Chow 1970 reject-option verification

Workstream item: T3.1.

Local paper state:
- There is no tracked `papers/Chow_1970_*` paper directory in this repo.
- Command-line attempts to fetch the PDF from MIT/IEEE/ResearchGate were blocked (`403`, IEEE `418`, ResearchGate `1020`).

Opened page images:
- Browser PDF source: `https://www.researchgate.net/profile/Fabrice-Clerot/post/Do-you-know-a-Bayes-classifier-which-creates-unrecognized-regions/attachment/59d61e9ec49f478072e97562/AS%3A271742742794240%401441799926252/download/Chow%2B-%2BOn%2Boptimum%2Brecognition%2Band%2Breject%2Btradeoff.pdf`
- Browser screenshots inspected for pages 41-43.

Verified paper content:
- The paper defines reject as withholding recognition rather than forcing a class decision.
- The optimum rule rejects a pattern when the maximum posterior probability is below the threshold.
- Acceptance and rejection regions are separated by the posterior threshold; error decreases as rejection increases.

Implementation checked:
- `propstore/stances.py` includes `StanceType.ABSTAIN`.
- `propstore/classify.py::classify_stance_from_llm_output` routes classifier errors, missing confidence, zero confidence, and missing strength to `ABSTAIN` with vacuous opinion instead of forcing a relationship type.
- Remediation tests under `tests/remediation/phase_3_ignorance/test_T3_1*.py` cover the reject/abstain behavior.

Result: matches the opened scanned PDF pages. Verification used browser-rendered page images because local PDF download was blocked.
