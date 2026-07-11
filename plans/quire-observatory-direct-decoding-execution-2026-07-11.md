# Quire direct observatory decoding

Date: 2026-07-11

Status: complete.

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
  owners and become strict frozen nested `msgspec.Struct` values in place.
- Quire decodes fixture bytes and converts/lowers the complete typed graph.
- Observatory owners retain schema-version invariants, deterministic ordering,
  semantic evaluation, and derived content hashes.
- `ObservatoryReport.operator_summaries` is a typed tuple. This is both the
  semantic collection and the direct persisted list shape; no dict-to-list
  transform survives.

The read-only subagent audit found that Quire's typed document byte decoder was
YAML, while the observatory contract is JSON-only. Using it would silently have
broadened accepted fixture syntax. Quire therefore gained the generic
`decode_json_document_bytes` owner API in pushed commit
`b3258064d84795eb8ae930cfe5c3fdd6cbe18a03`; Propstore pins that exact commit.
`convert_document_value`, `document_to_payload`, and canonical struct
normalization cover the rest of the graph.

The owners remain direct frozen structs instead of inheriting Quire's mutable
`DocumentStruct` convenience base. Quire's generic typed APIs accept the structs
directly, so no second marker base or configuration-only interface was added.

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
  rewrite the existing owners in place as strict frozen typed structs decoded
  directly by Quire.
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

- Deleted five `from_dict` / `to_dict` / `_content_payload` lifecycles and all
  observatory mapping, sequence, coercion, and hash-carrier helpers.
- Rewrote the five existing semantic owners as strict frozen typed structs.
- Changed `operator_summaries` from a runtime dict/persisted list dual shape to
  one sorted typed tuple.
- CLI fixture loading now calls Quire's strict typed JSON decoder directly; CLI
  JSON rendering lowers the typed report directly through Quire.
- Direct typed lowering intentionally omits redundant computed `content_hash`
  and `passed` wire keys. All five contracts were bumped from v1 to v2; v1
  payloads fail hard and the public documentation records the new contract.
- Quire owner gate: `uv run pytest tests/test_documents.py` — 15 passed;
  `uv run pyright quire` — 0 errors. Quire commit pushed:
  `b3258064d84795eb8ae930cfe5c3fdd6cbe18a03`.
- Propstore focused gate: 19 passed
  (`logs/test-runs/pytest-20260711-155547.log`).
- Propstore type gate: `uv run pyright propstore` — 0 errors.
- Ruff gate: all changed Python files clean.
- Search gates: zero deleted mapping lifecycle/helper/caller symbols and zero
  observatory codec/adapter/payload/DTO replacements.
- Diff gate: `git diff --check` clean. The tracked CRLF observatory file required
  the repository-local `cr-at-eol` Git whitespace setting; no whole-file
  line-ending conversion was retained.
- Propstore source commit:
  `381b444ca614b7965dae062422e3f13950b450a9`.
