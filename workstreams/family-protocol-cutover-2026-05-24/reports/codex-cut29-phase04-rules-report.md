# Cut 29 Phase 04 Rules Report

Executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut29-phase04-rules.md`.

## Workflow Used

Requested workflow was used: read the prompt, read `propstore/families/documents/rules.py`, read audit section 3.10, inspect the existing rules declaration and adjacent generated-document patterns, implement the authored-rule charters, update importers, regenerate the manifest, run gates, and commit atomically.

## Changes

- Extended `propstore/families/rules/declaration.py` with `AUTHORED_RULES_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")`, `AUTHORED_RULE_CHARTER`, `AUTHORED_RULE_PROPOSAL_CHARTER`, `RULE_SUPERIORITY_CHARTER`, and `AUTHORED_RULE_CHARTERS`.
- Kept existing grounded-runtime `RULES_CHARTERS` alongside the new authored-rule charters.
- Moved `TermDocument`, `AtomDocument`, `BodyLiteralDocument`, `RuleSourceDocument`, `RuleExtractionProvenance`, `RuleDocument`, `RuleProposalDocument`, and `RuleSuperiorityDocument` ownership into `rules/declaration.py`.
- Replaced top-level rule, proposal-rule, and rule-superiority document classes with `generated_document()` types while keeping nested JSON-blob structs as `msgspec.Struct`.
- Updated registry family definitions to use `AUTHORED_RULES_FAMILY_CONTRACT_VERSION` and registered `*rules.AUTHORED_RULE_CHARTERS` in `world_catalog()`.
- Deleted `propstore/families/documents/rules.py`.
- Updated production and test importers from `propstore.families.documents.rules` to `propstore.families.rules.declaration`.
- Regenerated `propstore/_resources/contract_manifests/semantic-contracts.yaml`.

## Gates

- `uv run pyright propstore` passed: 0 errors, 0 warnings.
- `uv run lint-imports` passed: 1 kept, 0 broken.
- `powershell -File scripts/run_logged_pytest.ps1` passed: 3526 passed, 4 skipped, 30 warnings in 416.13s.
- Focused recheck passed before the full suite: `tests/test_rule_documents.py tests/test_proposal_rules_family.py tests/test_grounded_bundle_round_trip.py tests/test_semantic_family_registry.py tests/test_contract_manifest.py` -> 42 passed.

## Notes

- No `.to_payload()` rule-document callsites were found, so no `document_to_payload()` migration was needed.
- The existing grounded bundle payload path remains in place, as requested out of scope.
- The authored and grounded paths use the same generated `RuleDocument` type for the existing blob round-trip; no separate shim was added.
