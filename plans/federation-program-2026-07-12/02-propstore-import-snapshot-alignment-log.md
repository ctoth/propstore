# Cleanup Refactor Fixed-Point Log - 2026-07-12

Target architecture:
- Committed repository snapshots retain repository-origin namespaced identities on pinned import branches.
- Alignment reads typed `Concept` documents through pinned Quire family APIs.
- `propstore.source.alignment` owns typed partial-argumentation semantics.
- `propstore.families.alignment` owns the durable typed proposal document.

Forbidden surfaces:
- Canonical-name concept collapse during repository import.
- Loose proposal dictionaries or mapping accessors in alignment semantics.
- Name, token, or Jaccard identity decisions.
- Branch-name parsing as provenance.
- Alignment wrappers, adapters, bridge normalizers, fallback readers, or unconditional equivalence closure.

Search gates:
- `rg -n "_proposal_field|Mapping\[str, object\]|align_imports|split\(\"/\", 1\)|Jaccard|sameAs|union.find|fallback|adapter|normaliz" propstore/source/alignment.py propstore/cli/concept/alignment.py`
- `rg -n "canonical name|canonical_name\)|derive_concept_artifact_id\(slug\)" propstore/importing/snapshot_passes.py`

Runtime gates:
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_repository_import.py tests/test_alignment_classification.py tests/test_concept_alignment_cli.py tests/test_concept_alignment_promotion.py`
- `uv run pyright propstore`
- `uv run ruff check propstore/importing/snapshot_passes.py propstore/source/stages.py propstore/source/alignment.py propstore/families/alignment.py propstore/cli/concept/alignment.py tests/test_repository_import.py tests/test_alignment_classification.py tests/test_concept_alignment_cli.py tests/test_concept_alignment_promotion.py`
- `git diff --check`

Baseline:
- Focused logged pytest: 26 passed in 25.50s (`logs/test-runs/pytest-20260712-182508.log`).

## Iteration 1 - `repository snapshot identity`

Slice read:
- `propstore/importing/snapshot_passes.py`
- `propstore/source/stages.py`
- `propstore/importing/repository_import.py`
- canonical concept, claim, context, and stance charters

Surfaces:
- `_normalize_concept_batch`
  - Disposition: rewrite
  - Owner after cleanup: `propstore.importing.snapshot_passes`
  - Action: delete canonical-name reconciliation and derive imported identity from repository origin plus source artifact identity.
  - Evidence: canonical-name equality currently maps rival repository concepts to the same `concept_id`.
- claim concept-reference rewriting
  - Disposition: rewrite
  - Owner after cleanup: `propstore.importing.snapshot_passes`
  - Action: rewrite every typed concept reference, including `ClaimVariable.concept`, through the import-local identity map.
  - Evidence: the current pass rewrites scalar and tuple references but leaves typed variable references stale.
- context and stance references
  - Disposition: keep
  - Owner after cleanup: their canonical family charters plus import-local claim reference index
  - Action: retain branch-local context ids and typed stance claim-id rewriting.
  - Evidence: each imported KB remains on its own branch; claim ids are already repository-namespaced.

Gate results:
- Pass: `powershell -File scripts/run_logged_pytest.ps1 tests/test_repository_import.py` - 12 passed in 12.10s (`logs/test-runs/pytest-20260712-182851.log`).
- Pass: `uv run ruff check propstore/importing/snapshot_passes.py tests/test_repository_import.py`.
- Pass: `git diff --check`.

Commit:
- `e9502380 Preserve repository concept identity on import`.

Next slice:
- Typed pinned-snapshot concept alignment.
