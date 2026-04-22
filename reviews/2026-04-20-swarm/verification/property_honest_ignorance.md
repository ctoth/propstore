# Property verification: honest ignorance

Workstream item: T12.5.

Property:
- Dogmatic opinions must be explicit and cited; missing evidence must remain vacuous rather than fabricated.

Verification:
- `powershell -File scripts/run_logged_pytest.ps1 -Label T12-property-sweep tests/remediation/phase_1_crits/test_T1_1_merge_preserves_rivals.py tests/remediation/phase_3_ignorance/test_T3_11_dogmatic_opinion_audit.py tests/remediation/phase_7_race_atomicity/test_T7_6_full_race_suite.py tests/remediation/phase_8_dos_anytime`
- Result: 9 passed, `created: 16/16 workers`.
- Log path: `logs/test-runs/T12-property-sweep-20260421-220547.log` (not committed).

Covered test:
- `tests/remediation/phase_3_ignorance/test_T3_11_dogmatic_opinion_audit.py::test_dogmatic_opinion_constructors_are_explicitly_cited`.

Result: verified.
