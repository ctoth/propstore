# Codex Cut32 Phase 05 Report

## Workflow Used

I executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut32-phase05.md` through its hard-stop check.

## Result

Halted on **H-D** before production edits.

Phase 05 requires deleting `propstore/families/batch_specs.py` and routing source batch behavior through `FamilyCharter.batch_specs`. The local Quire `FamilyCharter` implementation does not expose `batch_specs`, and current Propstore production code still imports and consumes the standalone batch specs.

## Evidence

- Current branch: `master`.
- Current HEAD: `8e610118d99618f52859aa977efc60c05e30015d`, matching the prompt's required base.
- `C:\Users\Q\code\quire\quire\charters.py:242` defines `class FamilyCharter`.
- `C:\Users\Q\code\quire\quire\charters.py:254` defines `document_contract_version`.
- `rg -n -F -- "batch_specs" C:\Users\Q\code\quire\quire\charters.py` returned no matches.
- `propstore/families/batch_specs.py:14` defines `CLAIM_BATCH_SPEC`.
- `propstore/families/batch_specs.py:21` defines `SOURCE_CONCEPT_BATCH_SPEC`.
- `propstore/families/batch_specs.py:27` defines `SOURCE_CLAIM_BATCH_SPEC`.
- `propstore/families/batch_specs.py:34` defines `SOURCE_JUSTIFICATION_BATCH_SPEC`.
- `propstore/families/batch_specs.py:41` defines `SOURCE_STANCE_BATCH_SPEC`.
- `propstore/families/batch_specs.py:48` defines `SOURCE_MICROPUBLICATION_BATCH_SPEC`.
- Production import sites:
  - `propstore/claims.py:8`
  - `propstore/source/alignment.py:43`
  - `propstore/source/claims.py:13`
  - `propstore/source/concepts.py:10`
  - `propstore/source/relations.py:6`
  - `propstore/families/registry.py:44`
- Registry wrapper evidence:
  - `propstore/families/registry.py:693` defines `decode_source_claims_document`.
  - `propstore/families/registry.py:699` consumes `SOURCE_CLAIM_BATCH_SPEC`.
  - `propstore/families/registry.py:722` consumes `SOURCE_CLAIM_BATCH_SPEC`.
  - `propstore/families/registry.py:682`, `720`, `762`, `804`, and `843` call `render_document_batch`.

## Actions Not Taken

- I did not edit production code.
- I did not delete `propstore/families/batch_specs.py`.
- I did not move FK/reference/contract surfaces.
- I did not run pyright, lint-imports, or the test suite because H-D is a prompt-defined hard-stop before implementation can proceed.
- I did not create the Phase 05 atomic production commit because the requested cut is blocked by H-D.

## Unfinished Phase 05 Items

- V012: registry-owned FK tables remain.
- V013: registry-owned reference key tables remain.
- V014: source batch decode/render/payload helpers in `registry.py` remain.
- V015: `propstore/families/batch_specs.py` remains.
- V016: `contracts.py::iter_document_schema_types` remains.
- V017: `DOCUMENT_SCHEMA_CONTRACT_VERSION_OVERRIDES` remains.

## Blocker

`FamilyCharter.batch_specs` is absent in the local Quire implementation, while Propstore has active production and test consumers of `propstore/families/batch_specs.py`. Deleting that file or moving the constants would require inventing a substitute batch ownership surface, which the prompt forbids.
