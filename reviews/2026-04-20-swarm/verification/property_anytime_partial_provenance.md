# Property verification: anytime partial-result provenance

Workstream item: T12.5.

Property:
- Enumeration ceilings must produce explicit partial/ceiling results with vacuous remainder provenance rather than silently truncating or exhausting.

Verification:
- `powershell -File scripts/run_logged_pytest.ps1 -Label T12-property-sweep tests/remediation/phase_1_crits/test_T1_1_merge_preserves_rivals.py tests/remediation/phase_3_ignorance/test_T3_11_dogmatic_opinion_audit.py tests/remediation/phase_7_race_atomicity/test_T7_6_full_race_suite.py tests/remediation/phase_8_dos_anytime`
- Result: 9 passed, `created: 16/16 workers`.
- Log path: `logs/test-runs/T12-property-sweep-20260421-220547.log` (not committed).

Covered tests:
- `tests/remediation/phase_8_dos_anytime/test_T8_1_assignment_candidates_ceiling.py`
- `tests/remediation/phase_8_dos_anytime/test_T8_1_choose_incision_set_ceiling.py`
- `tests/remediation/phase_8_dos_anytime/test_T8_1_future_queryable_sets_ceiling.py`
- `tests/remediation/phase_8_dos_anytime/test_T8_1_ic_merge_distance_ceiling.py`
- `tests/remediation/phase_8_dos_anytime/test_T8_4_atms_build_termination_guard.py`

Result: verified.
