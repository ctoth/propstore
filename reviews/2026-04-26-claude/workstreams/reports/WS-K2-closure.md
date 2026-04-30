# WS-K2 Closure

Workstream: WS-K2 meta-rule extraction pipeline
Closing implementation commit: `2f76cb38`
Knowledge corpus commit: `47c82cc` in nested `knowledge/`

## Findings Closed

- D-9: predicate and rule extraction now run through proposal-review promotion gates with prompt provenance.
- D-10: promoted rules live under `knowledge/rules/<paper-name>/`.
- D-8 consumer side: promoted rules fire through `propstore.source_trust_argumentation`.
- Codex 2.13: predicate registration is a propstore proposal/promote workflow, not a missing external skill.
- Codex 2.14: CLI help, dry-run, propose, promote, unknown-id, and no-commit review tests are logged and green.
- Empty `knowledge/predicates/` and `knowledge/rules/` gaps are closed for the 13 target papers.

## Red Tests First

- `tests/test_proposal_predicates_family.py` and `tests/test_proposal_rules_family.py` failed first on missing proposal families/documents.
- `tests/test_propose_predicates_lifecycle.py`, `tests/test_promote_predicates_proposals.py`, `tests/test_propose_rules_lifecycle.py`, and `tests/test_promote_rules_proposals.py` failed first on missing extraction and promotion APIs.
- The six CLI tests failed first on missing `pks proposal` rule/predicate commands.
- `tests/test_extracted_rules_lint_clean.py`, `tests/test_extracted_rules_fire_against_argumentation.py`, and `tests/test_workstream_k2_done.py` failed first on the absent corpus and acceptance artifacts.

## Logged Gates

- `logs/test-runs/WS-K2-red-families-20260429-202426.log`
- `logs/test-runs/WS-K2-families-green-20260429-202751.log`
- `logs/test-runs/WS-K2-red-predicate-lifecycle-20260429-202926.log`
- `logs/test-runs/WS-K2-predicate-lifecycle-green-20260429-203112.log`
- `logs/test-runs/WS-K2-red-rule-lifecycle-20260429-203231.log`
- `logs/test-runs/WS-K2-rule-lifecycle-green-20260429-203442.log`
- `logs/test-runs/WS-K2-red-cli-20260429-203737.log`
- `logs/test-runs/WS-K2-cli-green-20260429-203922.log`
- `logs/test-runs/WS-K2-red-corpus-20260429-204131.log`
- `logs/test-runs/WS-K2-corpus-green-20260429-204504.log`
- `logs/test-runs/WS-K2-targeted-20260429-204728.log`
- `logs/test-runs/WS-K2-20260429-205025.log`
- `logs/test-runs/WS-K2-cli-20260429-205025.log`
- `logs/test-runs/WS-K2-property-gates-20260429-210148.log`
- `logs/test-runs/WS-K2-resource-prompts-20260429-211035.log`
- `logs/test-runs/WS-K2-full-after-resources-20260429-211305.log` — 3425 passed, 2 skipped.

Additional gates:
- `uv run pyright propstore` — 0 errors.
- `uv run lint-imports` — 5 kept, 0 broken.
- `uv run python reviews/2026-04-26-claude/workstreams/check_index_order.py` — required before final close.

## Property Gates

- Generated proposed rules using undeclared predicates fail lint/promotion admission.
- Generated promoted rules are variable-safe: head variables must appear in a positive body literal.
- Predicate proposal YAML round-trip preserves name, arity, argument types, and source-paper provenance.
- Generated metadata facts fire deterministically through the WS-K consumer API.

## Files Changed

- Proposal families/documents: `propstore/families/registry.py`, `propstore/families/documents/predicates.py`, `propstore/families/documents/rules.py`.
- Extraction and promotion APIs: `propstore/heuristic/predicate_extraction.py`, `propstore/heuristic/rule_extraction.py`, `propstore/proposals_predicates.py`, `propstore/proposals_rules.py`.
- Prompt resources: `propstore/heuristic/__resources__/predicate_extraction_prompt.txt`, `propstore/heuristic/__resources__/rule_extraction_prompt.txt`, and archived `v1.txt` copies.
- Corpus helpers and consumer integration: `propstore/heuristic/rule_corpus.py`, `propstore/source_trust_argumentation/__init__.py`.
- CLI: `propstore/cli/proposal.py`.
- Corpus artifacts: nested `knowledge` commit `47c82cc`.
- Contract and closure docs: `propstore/contract_manifests/semantic-contracts.yaml`, `docs/gaps.md`, this report, and the WS-K2/index status lines.

## Acceptance

The acceptance log records 26 proposed and 26 accepted rules across the 13 target papers: 100% global acceptance and 100% per-paper acceptance. The single v1 rejection (`invented_predicate/2`) is recorded in `WS-K2-rejection-log.csv`; v2 tightened the prompt to arity-qualified registered predicates only.

## Remaining Risks

The current extracted corpus is intentionally small: one promoted firing rule per target paper plus the acceptance-log companion count. A successor can add multi-prompt agreement and broader rule coverage, but no WS-K2 acceptance gate is deferred.
