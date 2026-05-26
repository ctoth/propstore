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

## Iteration 3 - `source relation normalization`

Slice read:
- `propstore/source/relations.py`
- `propstore/source/__init__.py`
- `propstore/families/claims/lifecycle.py`
- `propstore/families/stances/declaration.py`
- `tests/test_source_promotion_alignment.py`
- `tests/test_source_promote_dangling_refs.py`

Surfaces:
- `normalize_source_justifications_payload`
  - Disposition: move
  - Owner after cleanup: `propstore.families.claims.lifecycle`
  - Action: Moved source justification reference normalization to the
    claim-family lifecycle owner because it resolves claim references for
    source-local justification records.
  - Evidence: The function definition exists only under
    `propstore/families/claims/lifecycle.py`; `propstore/source/relations.py`
    only calls the owner API from workflow orchestration.
- `normalize_source_stances_payload`
  - Disposition: move
  - Owner after cleanup: `propstore.families.stances.lifecycle`
  - Action: Moved source stance reference normalization to the stance-family
    lifecycle owner.
  - Evidence: The function definition exists only under
    `propstore/families/stances/lifecycle.py`; the source package no longer
    exports either relation-normalization helper.

Gate results:
- Pass: `rg -n -F -- "def normalize_source_justifications_payload" propstore/source propstore/families`
  - Remaining definition: `propstore/families/claims/lifecycle.py`.
- Pass: `rg -n -F -- "def normalize_source_stances_payload" propstore/source propstore/families`
  - Remaining definition: `propstore/families/stances/lifecycle.py`.
- Pass: `uv run pyright propstore`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label source-relation-lifecycle tests/test_source_promotion_alignment.py tests/test_source_promote_dangling_refs.py`
  - Evidence: `logs/test-runs/source-relation-lifecycle-20260525-231703.log`, 14 passed.

Commit:
- `a45e9faa Move source relation normalization to family lifecycle`

Next slice:
- Source-local claim identity policy.

## Iteration 4 - `source-local claim identity`

Slice read:
- `propstore/source/claims.py`
- `propstore/source/__init__.py`
- `propstore/families/claims/lifecycle.py`
- source claim/status/promotion tests importing `normalize_source_claims_payload`

Surfaces:
- `stable_claim_logical_value`
  - Disposition: move
  - Owner after cleanup: `propstore.families.claims.lifecycle`
  - Action: Moved stable source-local claim identity derivation to the
    claim-family lifecycle owner.
  - Evidence: `propstore/source/claims.py` no longer owns claim logical value
    hashing.
- `normalize_source_claims_payload`
  - Disposition: move
  - Owner after cleanup: `propstore.families.claims.lifecycle`
  - Action: Moved source-local claim ID/logical-ID/artifact-ID stamping to the
    claim-family lifecycle owner and removed the source package export.
  - Evidence: The only production definition is
    `propstore/families/claims/lifecycle.py`; tests import the owner API
    directly instead of `propstore.source`.

Gate results:
- Pass: `rg -n -F -- "def normalize_source_claims_payload" propstore/source propstore/families`
  - Remaining definition: `propstore/families/claims/lifecycle.py`.
- Pass: `rg -n -F -- "from propstore.source import normalize_source_claims_payload" tests propstore`
- Pass: `rg -n -F -- "from propstore.source.claims import normalize_source_claims_payload" tests propstore`
- Pass: `uv run pyright propstore`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label source-claim-identity-lifecycle tests/test_source_claims.py tests/test_source_cannot_mint_canonical_ids.py tests/test_cli_source_status.py tests/test_source_promotion_alignment.py::test_promote_source_branch_writes_canonical_artifact_families`
  - Evidence: `logs/test-runs/source-claim-identity-lifecycle-20260525-232134.log`, 18 passed.

Commit:
- `be1af68b Move source claim identity to claim family`

Next slice:
- Source concept projection and primary-branch match payload rewriting.

## Iteration 5 - `source concept lifecycle`

Slice read:
- `propstore/source/registry.py`
- `propstore/source/concepts.py`
- `propstore/source/finalize.py`
- `propstore/source/promote.py`
- `propstore/families/concepts/stages.py`
- `tests/test_source_relations.py`

Surfaces:
- `propstore/source/registry.py`
  - Disposition: delete
  - Owner after cleanup: `propstore.families.concepts.lifecycle`
  - Action: Deleted the source registry helper module and moved primary
    concept lookup, source concept projection, and parameterization merge
    preview behavior to the concept-family lifecycle owner.
  - Evidence: No `propstore.source.registry` or `from .registry` callers remain.
- Source package concept lifecycle exports
  - Disposition: delete
  - Owner after cleanup: `propstore.families.concepts.lifecycle`
  - Action: Removed `load_primary_branch_concepts`,
    `load_primary_branch_concept_docs`, `parameterization_group_merge_preview`,
    `preview_source_parameterization_group_merges`,
    `primary_branch_concept_match`, and `projected_source_concepts` from the
    source package export surface.
  - Evidence: Source workflow modules and tests import the concept-family owner
    directly.

Gate results:
- Pass: `rg -n -F -- "propstore.source.registry" propstore tests`
- Pass: `rg -n -F -- "from .registry" propstore/source`
- Pass: `rg -n -F -- "from propstore.source import parameterization_group_merge_preview" tests propstore`
- Pass: `rg -n -F -- "def projected_source_concepts" propstore/source propstore/families`
  - Remaining definition: `propstore/families/concepts/lifecycle.py`.
- Pass: `uv run pyright propstore`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label source-concept-lifecycle tests/test_source_relations.py tests/test_source_promotion_alignment.py::test_promote_source_branch_materializes_blocked_rows_from_source_state tests/test_finalize_micropub_required.py`
  - Evidence: `logs/test-runs/source-concept-lifecycle-20260525-232459.log`, 13 passed.

Commit:
- `3079f269 Move source concept lifecycle to concept family`

Next slice:
- Source loader fanout in `propstore/source/common.py`.
