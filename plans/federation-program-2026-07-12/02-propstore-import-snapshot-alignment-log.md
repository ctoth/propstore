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

## Iteration 2 - `pinned imported concept alignment`

Slice read:
- `propstore/source/alignment.py`
- `propstore/families/alignment.py`
- `propstore/cli/concept/alignment.py`
- `propstore/source/stages.py`
- Quire `BoundFamily.pin` / `PinnedBoundFamily`
- repository-import provenance notes

Surfaces:
- loose proposal mapping lifecycle in `propstore.source.alignment`
  - Disposition: delete
  - Owner after cleanup: typed `AlignmentArgument` values owned by the alignment family.
  - Action: delete `_proposal_field`, mapping classifiers, name-minted ontology references, and `build_alignment_artifact`'s mapping input.
  - Evidence: these mappings cross the semantic boundary and cannot record the required pinned import provenance.
- `align_sources`
  - Disposition: delete
  - Owner after cleanup: repository-snapshot alignment workflow in `propstore.source.alignment`.
  - Action: remove source-branch parsing and read typed concepts from explicitly supplied pinned import branches.
  - Evidence: source-branch parsing is not repository-import provenance and the plan forbids deriving provenance from branch names.
- alignment document argument fields
  - Disposition: rewrite
  - Owner after cleanup: `propstore.families.alignment.AlignmentArgument`.
  - Action: carry repository origin, source commit, import branch/commit, concept id, ontology reference, lexical entry, canonical name, definition, and form.
  - Evidence: the current document stores loose-proposal vocabulary and omits snapshot provenance.
- decision and promotion lifecycle
  - Disposition: keep
  - Owner after cleanup: existing alignment owner functions.
  - Action: preserve the established capability while changing it to read the typed argument's canonical concept fields directly.
  - Evidence: these functions act on durable alignment artifacts and do not create the forbidden import-alignment representation.
- CLI `concept align`
  - Disposition: rewrite
  - Owner after cleanup: presentation-only typed request construction plus the alignment owner call.
  - Action: accept explicit import branches; do not parse provenance in the CLI.

Gate results:
- Pass: `powershell -File scripts/run_logged_pytest.ps1 tests/test_alignment_classification.py tests/test_concept_alignment_cli.py tests/test_concept_alignment_promotion.py tests/test_repository_import.py` - 25 passed in 9.00s (`logs/test-runs/pytest-20260712-184102.log`).
- Pass: `uv run pyright propstore` - 0 errors.
- Pass: focused Ruff gate.
- Pass: forbidden alignment and import-identity searches - zero hits.
- Pass: `git diff --check`.

Commit:
- `732b4393 Align pinned repository import snapshots`.

Next slice:
- Fixed-point searches and full named gates.

## Iteration 3 - `requested-scope fixed point`

Slice read:
- every production and test path named by Slice 2
- `propstore/source/__init__.py` deletion fallout
- `plans/federation-program-2026-07-12/02-propstore-import-snapshot-alignment.md`

Surfaces:
- imported snapshot normalization
  - Disposition: keep
  - Owner after cleanup: `propstore.importing.snapshot_passes`.
  - Action: no further change after the repository-origin identity and typed-reference gates passed.
  - Evidence: rival same-named concepts remain independently addressable; claim, variable, context, and stance references stay valid on their import branches.
- pinned snapshot alignment
  - Disposition: keep
  - Owner after cleanup: `propstore.source.alignment` using typed family and provenance APIs directly.
  - Action: no further change after deterministic artifact, provenance, attack, and master-isolation gates passed.
  - Evidence: forbidden production searches are zero-hit and the full named runtime gates pass.
- alignment document
  - Disposition: keep
  - Owner after cleanup: `propstore.families.alignment`.
  - Action: no further change; every required provenance and concept field is a typed document field.
- CLI alignment command
  - Disposition: keep
  - Owner after cleanup: presentation-only request construction and rendering.
  - Action: no further change; provenance resolution and storage semantics remain in the alignment owner.

Gate results:
- Pass: final logged focused pytest - 25 passed in 10.01s (`logs/test-runs/pytest-20260712-200925.log`).
- Pass: `uv run pyright propstore` - 0 errors, 0 warnings.
- Pass: focused Ruff gate.
- Pass: forbidden alignment surfaces - zero hits.
- Pass: forbidden import-identity surfaces - zero hits.
- Pass: `git diff --check`.

Commit:
- Implementation commits `e9502380` and `732b4393`; this fixed-point record is committed separately.

Next slice:
- None in the requested scope. Slice 2 reached fixed point.
