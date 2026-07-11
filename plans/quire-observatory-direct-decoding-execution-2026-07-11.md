# Quire direct observatory decoding

Date: 2026-07-11

Status: execution started.

Active control surface: `protocols:cleanup-refactor`.

Baseline:

- branch: `master`
- HEAD: `9c7f168a2da1a287d50a8c0a54aaad00d4903b57`
- tracked files: clean
- excluded untracked user artifacts: `pyghidra_mcp_projects/`,
  `reviews/2026-07-11-propstore-deep-review.md`, and
  `tests/test_micropub_clark_charter.py`

## Slice

Only A2 surface 6, `propstore/observatory.py`, plus its direct CLI and tests.

## Target architecture

- `SemanticTraceRecord`, `EvaluationScenario`, `ScenarioEvaluation`,
  `OperatorFamilySummary`, and `ObservatoryReport` remain the direct semantic
  owners and become strict nested Quire `DocumentStruct` values in place.
- Quire decodes fixture bytes and converts/lowers the complete typed graph.
- Observatory owners retain schema-version invariants, deterministic ordering,
  semantic evaluation, and derived content hashes.
- `ObservatoryReport.operator_summaries` is a typed tuple. This is both the
  semantic collection and the direct persisted list shape; no dict-to-list
  transform survives.

No new Quire capability is required. Existing `DocumentStruct`,
`decode_document_bytes`, `convert_document_value`, `document_to_payload`, and
canonical struct normalization cover the complete graph.

## Forbidden surfaces

- `from_dict`, `to_dict`, `_content_payload`
- `_is_mapping`, `_is_sequence`, `_plain`, `_mapping`, `_sequence`, `_strings`,
  `_check_hash`, and local mapping reconstruction
- `Mapping[str, Any]` / `dict[str, Any]` observatory semantic carriers
- an `ObservatoryCodec`, payload/record/DTO twin, adapter, compatibility reader,
  fallback parser, repeated field list, or per-field kwargs builder
- old and new fixture/report representations accepted together

## Ownership classifications and dispositions

- Five observatory classes: **valid capability with wrong representation** ->
  rewrite the existing owners in place as strict `DocumentStruct` values.
- Five `from_dict` / `to_dict` / `_content_payload` lifecycles and generic shape
  helpers: **deleted old surface** -> delete.
- Schema-version checks, deterministic sorting, `passed`, content hashes, and
  `evaluate_scenarios`: **valid semantic capability in the correct owner** ->
  keep on the existing observatory owners without mapping methods.
- CLI `json.loads` plus `EvaluationScenario.from_dict`: **IO-boundary-only
  carrier followed by duplicate decoding** -> call Quire byte decoding directly.
- CLI JSON rendering and fixture construction in tests: **IO boundary** -> lower
  the typed document directly with Quire; no semantic mapping enters core code.
- Mapping round-trip tests: **valid boundary contract with wrong
  representation** -> prove strict nested Quire round trips and rejection.

## Gates

Search gates:

- zero `from_dict`, `to_dict`, `_content_payload`, generic shape helper, or loose
  semantic mapping surface in `propstore/observatory.py`
- zero observatory caller invocation of deleted methods
- zero local observatory codec/adapter/payload/DTO replacement

Runtime gates:

- `powershell -File scripts/run_logged_pytest.ps1 tests/test_observatory.py tests/test_cli_phase10_advanced.py`
- `uv run pyright propstore`
- `git diff --check`

## Execution log

Pending first deletion.
