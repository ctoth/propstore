# Cleanup Refactor Fixed-Point Log - 2026-05-26

Target architecture:
- Source-local authoring, finalization, promotion, status, and alignment are
  lifecycle transitions over typed family records.
- Source modules keep source semantics only.
- Document shape, payload rewriting, reference normalization, and claim-core
  status reads live with family/charter owners and generic family APIs.

Forbidden surfaces:
- `propstore/source/claim_concepts.py`
- `propstore.source.claim_concepts`
- `ClaimConceptSource = ClaimDocument | SourceClaimDocument | Mapping[str, Any]`
- `rewrite_claim_concept_refs`
- `_place_source_local_concept`
- direct source-status `claim_core` SQL/table lookup
- source-loader fanout in `propstore/source/common.py`
- concrete document-class fields in `SourcePromotionPlan`

Search gates:
- `rg -n -F -- "propstore.source.claim_concepts" propstore tests`
- `rg -n -F -- "ClaimDocument | SourceClaimDocument | Mapping" propstore/source propstore tests`
- `rg -n -F -- "_place_source_local_concept" propstore tests`
- `rg -n -F -- "derived.schema.table" propstore/source/status.py propstore/cli/source/lifecycle.py tests/test_cli_source_status.py`
- `rg -n -F -- "select(claim_core.c.id, claim_core.c.promotion_status)" propstore/source propstore/cli/source tests`

Runtime gates:
- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label source-claim-lifecycle tests/test_source_claim_concept_rewrite.py tests/test_source_promotion_alignment.py::test_promote_source_branch_writes_canonical_artifact_families`
- `powershell -File scripts/run_logged_pytest.ps1 -Label source-status-lifecycle tests/test_cli_source_status.py`
- `powershell -File scripts/run_logged_pytest.ps1 -Label source-lifecycle tests/test_cli_source_status.py tests/test_finalize_micropub_required.py tests/test_source_promotion_alignment.py tests/test_source_promote_dangling_refs.py`

## Iteration 1 - `source claim concept normalization`

Slice read:
- `propstore/source/claim_concepts.py`
- `propstore/importing/passes.py`
- `propstore/source/promote.py`
- `propstore/families/identity/claims.py`
- `propstore/families/claims/stages.py`
- `tests/test_source_claim_concept_rewrite.py`

Surfaces:
- `propstore/source/claim_concepts.py`
  - Disposition: delete
  - Owner after cleanup: `propstore.families.claims.lifecycle`
  - Action: Deleted the root source helper module and moved the still-needed
    import and source-promotion claim normalization behavior to the claim-family
    lifecycle owner.
  - Evidence: Import and promotion callers now use
    `propstore.families.claims.lifecycle`; the old source import path has zero
    hits.
- `ClaimConceptSource`
  - Disposition: delete
  - Owner after cleanup: typed entry points split by input shape
  - Action: Replaced the mixed alias with `rewrite_imported_claim_concept_refs`
    for mapping payloads and `rewrite_source_claim_concept_refs` for
    `SourceClaimDocument` records.
  - Evidence: The exact union-alias search has zero hits.
- `_place_source_local_concept`
  - Disposition: delete
  - Owner after cleanup: claim-family lifecycle normalization
  - Action: Removed the old helper name and kept placement behavior inside the
    claim-family rewrite flow.
  - Evidence: The old helper-name search has zero hits.

Gate results:
- Pass: `rg -n -F -- "propstore.source.claim_concepts" propstore tests`
- Pass: `rg -n -F -- "ClaimDocument | SourceClaimDocument | Mapping" propstore/source propstore tests`
- Pass: `rg -n -F -- "_place_source_local_concept" propstore tests`
- Pass: `uv run pyright propstore`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label source-claim-lifecycle tests/test_source_claim_concept_rewrite.py tests/test_source_promotion_alignment.py::test_promote_source_branch_writes_canonical_artifact_families`
  - Evidence: `logs/test-runs/source-claim-lifecycle-20260525-231058.log`, 8 passed.

Commit:
- `fcb9f67c Move claim concept lifecycle normalization to claim family`

Next slice:
- Source status direct `claim_core` lookup.

## Iteration 2 - `source status claim rows`

Slice read:
- `propstore/source/status.py`
- `propstore/cli/source/lifecycle.py`
- `propstore/families/claims/declaration.py`
- `tests/test_cli_source_status.py`

Surfaces:
- Direct `claim_core` source-status lookup
  - Disposition: move
  - Owner after cleanup: `propstore.families.claims.declaration`
  - Action: Added `source_branch_promotion_status_rows` as the claim-family
    owner API for source-branch promotion-status rows and rewired
    `inspect_source_status` to use it.
  - Evidence: Source status no longer asks the derived schema for the
    `claim_core` table or issues the status-row `select` directly.

Gate results:
- Pass: `rg -n -F -- "derived.schema.table" propstore/source/status.py propstore/cli/source/lifecycle.py tests/test_cli_source_status.py`
- Pass: `rg -n -F -- "select(claim_core.c.id, claim_core.c.promotion_status)" propstore/source propstore/cli/source tests`
- Pass: `uv run pyright propstore`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label source-status-lifecycle tests/test_cli_source_status.py`
  - Evidence: `logs/test-runs/source-status-lifecycle-20260525-231334.log`, 5 passed.

Commit:
- `b406fc6d Move source status claim rows to claim family`

Next slice:
- Source relation normalization for justifications and stances.
