"""Repository import: ingest external KB rows as defeasible source claims.

:func:`import_manifest` is the one entry point. It takes a typed
:class:`~propstore.importing.contract.ImportManifest` and lands every row on a
*source branch* (``source/<name>``) through the ordinary source-authoring path
(8-2) — never a direct canonical write to ``master``. The imported source branch
is then just another non-committal source: it follows the normal finalize ->
promote lifecycle (8-3), where its claims can be argued against, superseded, or
quarantined exactly like any hand-authored source.

The import is honest about provenance (CLAUDE.md): the source manifest's trust
status and the import's git provenance note both carry the manifest's declared
:class:`~propstore.provenance.ProvenanceStatus` — ``stated`` or ``defaulted`` —
and the contract refuses to let an import launder a row into ``measured`` /
``calibrated``. No source is privileged ([[feedback_imports_are_opinions]]).
"""

from __future__ import annotations

import msgspec

from propstore.families.registry import SourceRef
from propstore.importing.contract import ImportManifest, ImportResult
from propstore.provenance import (
    Provenance,
    ProvenanceWitness,
    write_provenance_note,
)
from propstore.repository import Repository
from propstore.source.common import (
    current_source_branch_head,
    init_source_branch,
    load_source_document,
    normalize_source_slug,
    source_branch_name,
    source_tag_uri,
    utc_now,
)
from propstore.source.passes import run_import_pipeline


def import_manifest(repo: Repository, manifest: ImportManifest) -> ImportResult:
    """Import a manifest's rows onto a source branch as defeasible claims.

    Creates (or reuses) the source branch, stamps the source manifest's trust
    with the manifest's honest provenance status, normalizes and writes every
    concept/claim/stance row through the source-authoring path, and attaches an
    import provenance note to the resulting source-branch tip.
    """

    init_source_branch(
        repo,
        manifest.source_name,
        kind=manifest.kind,
        origin_type=manifest.origin_type,
        origin_value=manifest.origin_value,
    )
    _stamp_source_trust(repo, manifest)

    pipeline = run_import_pipeline(repo, manifest.source_name, manifest)

    tip = current_source_branch_head(repo, manifest.source_name)
    if tip is None:
        raise ValueError("import did not produce a source-branch commit")
    _attach_import_provenance(repo, manifest, commit_sha=tip)

    return ImportResult(
        source_name=manifest.source_name,
        source_branch=source_branch_name(manifest.source_name),
        commit_sha=tip,
        provenance_status=manifest.provenance_status,
        concept_count=pipeline.concept_count,
        claim_count=pipeline.claim_count,
        stance_count=pipeline.stance_count,
        warnings=pipeline.warnings,
    )


def _stamp_source_trust(repo: Repository, manifest: ImportManifest) -> None:
    """Stamp the imported source manifest's trust with its honest status.

    ``init_source_branch`` writes a ``defaulted`` manifest; here we record the
    manifest's declared status (``stated`` for an external assertion, or
    ``defaulted`` for a fallback) so the source's trust is never silently
    upgraded to a measured/calibrated origin it does not have.
    """

    source_doc = load_source_document(repo, manifest.source_name)
    updated_trust = msgspec.structs.replace(
        source_doc.trust, status=manifest.provenance_status
    )
    updated_doc = msgspec.structs.replace(source_doc, trust=updated_trust)
    repo.families.source_documents.save(
        SourceRef(manifest.source_name),
        updated_doc,
        message=f"Stamp import trust for {normalize_source_slug(manifest.source_name)}",
    )


def _attach_import_provenance(
    repo: Repository, manifest: ImportManifest, *, commit_sha: str
) -> None:
    git = repo.require_git()
    source_uri = source_tag_uri(repo, manifest.source_name)
    write_provenance_note(
        git.raw_repo,
        commit_sha,
        Provenance(
            status=manifest.provenance_status,
            graph_name=f"urn:propstore:import:{commit_sha}",
            witnesses=(
                ProvenanceWitness(
                    asserter=source_uri,
                    timestamp=utc_now(),
                    source_artifact_code=manifest.origin_value,
                    method="import",
                ),
            ),
            operations=("import",),
        ),
    )
