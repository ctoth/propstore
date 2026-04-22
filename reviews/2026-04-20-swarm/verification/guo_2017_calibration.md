# Guo et al. 2017 calibration verification

Workstream item: T3.2.

Opened page images:
- `papers/Guo_2017_CalibrationModernNeuralNetworks/pngs/page-001.png`.
- `papers/Guo_2017_CalibrationModernNeuralNetworks/pngs/page-005.png`.

Verified paper content:
- Perfect calibration is equality between confidence and empirical accuracy.
- Reliability diagrams and expected calibration error summarize calibration gaps.
- Temperature scaling applies `softmax(z / T)` with `T > 0`; `T = 1` is identity, and the scalar temperature does not change class accuracy.
- The temperature is fit on validation negative log likelihood.

Implementation checked:
- `propstore/calibrate.py` implements corpus calibration, ECE-style binning, temperature scaling, and `ProvenanceStatus.CALIBRATED` for calibrated opinions.
- Tests in `tests/test_calibrate.py` and remediation tests cover calibrated provenance and opinion boundaries.

Result: matches the opened PDF pages.
