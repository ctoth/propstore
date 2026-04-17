# Paper-Grounded Test Suite Baseline

Date: 2026-04-16

Workstream: `plans/paper-grounded-test-suite-workstream-2026-04-16.md`

## Migration Inventory

Command:

```powershell
uv run scripts/list_migration_tests.py
```

Result:

```text
No migration-marked tests found.
```

## Low-Signal Candidate Baseline

Command:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label paper-grounded-baseline-low-signal tests/test_helpers.py tests/test_render_contracts.py tests/test_form_utils.py tests/test_claim_and_stance_document_enums.py tests/test_atms_value_status_types.py tests/test_uri.py tests/test_literal_keys.py
```

Result: `68 passed`

Log:

- `logs/test-runs/paper-grounded-baseline-low-signal-20260416-204042.log`

## Paper Page Image Existence Check

All workstream-listed page image paths existed in this checkout:

- `papers/Dung_1995_AcceptabilityArguments/pngs/page-005.png`
- `papers/Dung_1995_AcceptabilityArguments/pngs/page-006.png`
- `papers/Dung_1995_AcceptabilityArguments/pngs/page-008.png`
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-05.png`
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-07.png`
- `papers/Oikarinen_2010_CharacterizingStrongEquivalenceArgumentation/pages/page-12.png`
- `papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-012.png`
- `papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png`
- `papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png`
- `papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png`
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-004.png`
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png`
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-024.png`
- `papers/vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic/pngs/page-004.png`
- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_003.png`
- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_004.png`
