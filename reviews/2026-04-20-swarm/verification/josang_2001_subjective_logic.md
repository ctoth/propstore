# Jøsang 2001 subjective logic verification

Workstream items: T1.4, T3.3, T3.4, T3.7.

Opened page images:
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-005.png`.
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png`.
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-007.png`.
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-008.png`.
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-024.png`.

Verified paper content:
- Opinion is a four-tuple `(belief, disbelief, uncertainty, base rate)`.
- Vacuous opinions represent total uncertainty rather than fabricated support or opposition.
- Dogmatic opinions sit on the probability axis with zero uncertainty.
- The consensus operator combines uncertain opinions and reduces uncertainty under independent evidence.

Implementation checked:
- `propstore/opinion.py` for opinion construction and vacuous opinions.
- `propstore/classify.py` for classifier failures, missing confidence, and missing strength becoming `StanceType.ABSTAIN` with vacuous provenance.
- `propstore/preference.py` and `propstore/heuristic/source_trust.py` for missing metadata and trust derivation.
- `propstore/provenance/__init__.py` for explicit provenance status requirements.

Result: matches the opened PDF pages.
