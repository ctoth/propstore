# Property verification: CAS retry and concurrent convergence

Workstream item: T12.5.

Property:
- Concurrent writers for merges, refs, and sidecar builds must converge without mixed writes or silent clobbering.

Verification:
- `powershell -File scripts/run_logged_pytest.ps1 -Label T12-property-sweep tests/remediation/phase_1_crits/test_T1_1_merge_preserves_rivals.py tests/remediation/phase_3_ignorance/test_T3_11_dogmatic_opinion_audit.py tests/remediation/phase_7_race_atomicity/test_T7_6_full_race_suite.py tests/remediation/phase_8_dos_anytime`
- Result: 9 passed, `created: 16/16 workers`.
- Log path: `logs/test-runs/T12-property-sweep-20260421-220547.log` (not committed).

Covered test:
- `tests/remediation/phase_7_race_atomicity/test_T7_6_full_race_suite.py::test_full_race_suite_covers_merge_ref_and_sidecar_atomicity`.

Result: verified.
