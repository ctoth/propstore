# Paper-Grounded Test Suite Workstream Closeout

Date: 2026-04-16

## Summary

The workstream is complete. No phases are deferred.

Full-suite verification passed:

- `logs/test-runs/paper-grounded-full-20260416-212404.log`
- Result: 2572 passed, 16 warnings
- Warning source: `scripts/test_inventory_report.py` collection warning for
  `TestFileStats` dataclass with an `__init__` constructor

## Deleted Tests

- Deleted pure import/surface smoke coverage:
  - `tests/test_helpers.py::test_write_yaml_file_importable_from_artifact_codecs`
  - `tests/test_render_contracts.py::test_protocol_shapes`
  - `tests/test_form_utils.py::TestFormDefinitionLoading::test_load_form_with_none_returns_none`
  - `tests/test_form_utils.py::TestFormDefinitionLoading::test_load_form_with_empty_string_returns_none`
- Deleted stale review-group and backend-routing files after moving useful
  coverage:
  - `tests/test_atms_value_status_types.py`
  - `tests/test_dung_review_v2.py`
  - `tests/test_exception_narrowing_group3.py`

## Replaced Tests

- Replaced enum annotation checks with conversion-boundary behavior in
  `tests/test_claim_and_stance_document_enums.py`.
- Replaced ATMS annotation checks with runtime status behavior in
  `tests/test_atms_engine.py`.
- Replaced Dung backend routing smoke coverage with backend/oracle differential
  coverage in `tests/test_dung.py`, `tests/test_dung_z3.py`, and
  `tests/test_dung_backend_differential.py`.
- Replaced historical exception-narrowing grouping with subsystem-owned
  RuntimeError/OperationalError propagation coverage in:
  `tests/test_build_sidecar.py`, `tests/test_cli.py`,
  `tests/test_embed_operational_error.py`, `tests/test_param_conflicts.py`,
  `tests/test_classify.py`, `tests/test_sympy_generator.py`, and
  `tests/test_value_resolver_failure_reasons.py`.

## New Property Tests

- URI identity properties in `tests/test_uri.py`:
  `test_tag_uri_is_deterministic_prefixed_and_normalizes_spaces`,
  `test_tag_uri_equivalent_single_whitespace_normalizes_consistently`,
  `test_tag_uri_path_separators_are_normalized`,
  `test_ni_uri_for_bytes_is_deterministic`, and
  `test_ni_uri_for_bytes_changes_when_payload_changes`.
- Dung paper-grounded properties in `tests/test_dung.py`.
- ASPIC transposition and last-link/weakest-link properties in
  `tests/test_aspic.py` and `tests/test_preference.py`.
- Subjective-logic/generated opinion tests in `tests/test_opinion.py`,
  `tests/test_opinion_schema.py`, and `tests/test_render_policy_opinions.py`.
- Diller-style generated revision postulate checks in
  `tests/test_revision_properties.py`.

## New Differential Tests

- Dung/Z3 backend agreement checks in `tests/test_dung_z3.py` and
  `tests/test_dung_backend_differential.py`.
- Repo-owned defeasible conformance checks in
  `tests/test_defeasible_conformance_tranche.py`, loaded from
  `propstore/_resources/conformance/defeasible/**`.

## Paper Page Image Paths Cited In Tests

- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_003.png`
- `papers/Diller_2015_ExtensionBasedBeliefRevision/pages/page_004.png`
- `papers/Dung_1995_AcceptabilityArguments/pngs/page-005.png`
- `papers/Dung_1995_AcceptabilityArguments/pngs/page-006.png`
- `papers/Dung_1995_AcceptabilityArguments/pngs/page-008.png`
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-004.png`
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-006.png`
- `papers/Josang_2001_LogicUncertainProbabilities/pngs/page-024.png`
- `papers/Lehtonen_2024_PreferentialASPIC/pages/page_004.png`
- `papers/Lehtonen_2024_PreferentialASPIC/pages/page_005.png`
- `papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-012.png`
- `papers/Prakken_2010_AbstractFrameworkArgumentationStructured/pngs/page-015.png`
- `papers/vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic/pngs/page-004.png`

## Targeted Log Paths

- `logs/test-runs/paper-grounded-baseline-low-signal-20260416-204042.log`
- `logs/test-runs/paper-grounded-delete-helper-import-20260416-204212.log`
- `logs/test-runs/paper-grounded-delete-render-protocol-shape-20260416-204252.log`
- `logs/test-runs/paper-grounded-delete-form-sentinels-20260416-204447.log`
- `logs/test-runs/paper-grounded-claim-stance-enum-behavior-20260416-204538.log`
- `logs/test-runs/paper-grounded-atms-status-behavior-20260416-204712.log`
- `logs/test-runs/paper-grounded-uri-properties-20260416-204819.log`
- `logs/test-runs/paper-grounded-dung-properties-20260416-205013.log`
- `logs/test-runs/paper-grounded-dung-z3-differential-20260416-205134.log`
- `logs/test-runs/paper-grounded-aspic-transposition-20260416-205504.log`
- `logs/test-runs/paper-grounded-last-link-20260416-205902.log`
- `logs/test-runs/paper-grounded-subjective-logic-20260416-210428.log`
- `logs/test-runs/paper-grounded-subjective-logic-cleanup-20260416-210537.log`
- `logs/test-runs/paper-grounded-revision-postulates-20260416-210845.log`
- `logs/test-runs/paper-grounded-defeasible-conformance-20260416-211422.log`
- `logs/test-runs/paper-grounded-exception-narrowing-20260416-212047.log`
- `logs/test-runs/paper-grounded-changed-suite-20260416-212308.log`

## Full-Suite Log Path

- `logs/test-runs/paper-grounded-full-20260416-212404.log`

## Deferred Work

None.

Known product gap recorded for later work:

- `reports/paper-grounded-revision-postulate-gap-2026-04-16.md`
- `docs/gaps.md`
