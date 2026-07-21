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

from dataclasses import dataclass, field
from pathlib import Path

import msgspec

from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    SourceRef,
    semantic_import_roots,
)
from propstore.importing.contract import ImportManifest, ImportResult
from propstore.importing.snapshot_passes import run_source_import_pipeline
from propstore.provenance import (
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
    write_provenance_note,
)
from propstore.repository import Repository, RepositoryNotFound
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
from propstore.source.stages import (
    PlannedSemanticWrite,
    SourceImportAuthoredWrites,
    SourceImportNormalizedWrites,
)


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


# ---------------------------------------------------------------------------
# Committed-snapshot repo-to-repo import (the canonical-snapshot path)
# ---------------------------------------------------------------------------


_IMPORTER_ID = "urn:propstore:agent:repository-import"
_IMPORT_METHOD = "repository-import"


def _empty_str_list() -> list[str]:
    return []


@dataclass(frozen=True)
class RepositoryImportPlan:
    """A planned committed-snapshot import between knowledge repositories.

    ``writes`` are the normalized, identity-reconciled, reference-rewritten
    artifacts to land on ``target_branch``; ``deletes`` are the import-branch
    paths the latest source snapshot no longer contains (so the import converges
    onto the source rather than accreting). ``warnings`` are non-fatal
    ambiguities surfaced by normalization — never silently dropped.
    """

    source_repository: str
    source_commit: str
    target_branch: str
    repository_name: str
    writes: dict[str, PlannedSemanticWrite]
    deletes: list[str]
    touched_paths: list[str]
    warnings: list[str] = field(default_factory=_empty_str_list)


@dataclass(frozen=True)
class RepositoryImportResult:
    """The committed outcome of a repo-to-repo import."""

    surface: str
    source_repository: str
    source_commit: str
    target_branch: str
    commit_sha: str
    touched_paths: list[str]
    deleted_paths: list[str]


def _infer_repository_name(repository: Repository) -> str:
    root = repository.root
    if root.name == "knowledge" and root.parent.name:
        return root.parent.name
    return root.name


def _iter_semantic_paths(repository: Repository, *, commit: str) -> dict[str, bytes]:
    return {
        tree_file.relpath: tree_file.content
        for tree_file in repository.require_git().iter_tree_files(
            commit=commit,
            roots=semantic_import_roots(),
        )
    }


def _import_provenance(plan: RepositoryImportPlan, *, commit_sha: str) -> Provenance:
    """The provenance named graph for one committed repository import.

    The witness pins the exact source bytes: ``source_artifact_code`` is the
    where pointer (the source repository), and the version/content hash name the
    committed snapshot it was read from. ``stated`` is the only honest status —
    an import never observed or calibrated anything.
    """

    return Provenance(
        status=ProvenanceStatus.STATED,
        graph_name=f"urn:propstore:repository-import:{commit_sha}",
        witnesses=(
            ProvenanceWitness(
                asserter=_IMPORTER_ID,
                timestamp=utc_now(),
                source_artifact_code=plan.source_repository,
                method=_IMPORT_METHOD,
                source_version_id=plan.source_commit,
                source_content_hash=f"git:{plan.source_commit}",
            ),
        ),
        derived_from=(plan.source_commit,),
        operations=(_IMPORT_METHOD,),
    )


def plan_repository_import(
    destination_repository: Repository,
    source_repository_path: Path,
    *,
    target_branch: str | None = None,
) -> RepositoryImportPlan:
    """Plan a committed-snapshot import from one knowledge repository into another.

    Reads the source repository's *committed* canonical semantic tree (its HEAD,
    never the working tree), normalizes it into the importing repository's
    namespace, and computes the writes/deletes that make the ``import/<name>``
    branch converge onto that snapshot. Plans only — nothing is committed and no
    source row is privileged ([[feedback_imports_are_opinions]]).
    """

    try:
        source_repository = Repository.find(source_repository_path.resolve())
    except RepositoryNotFound as exc:
        raise ValueError("Source repository must be git-backed") from exc

    source_commit = source_repository.require_git().head_sha()
    if source_commit is None:
        raise ValueError("Source repository has no committed HEAD")

    repository_name = _infer_repository_name(source_repository)
    selected_branch = target_branch or f"import/{repository_name}"

    pipeline = run_source_import_pipeline(
        SourceImportAuthoredWrites(
            store=destination_repository.families.store,
            writes=_iter_semantic_paths(source_repository, commit=source_commit),
            repository_name=repository_name,
        )
    )
    normalized = pipeline.output
    if not isinstance(normalized, SourceImportNormalizedWrites):
        errors = ", ".join(error.render() for error in pipeline.errors)
        raise ValueError(f"Repository import normalization failed: {errors}")
    writes = normalized.writes
    warnings: list[str] = list(normalized.warnings)

    existing_paths: set[str] = set()
    existing_branch_sha = destination_repository.require_git().branch_sha(
        selected_branch
    )
    if existing_branch_sha is not None:
        existing_paths = set(
            _iter_semantic_paths(destination_repository, commit=existing_branch_sha)
        )
    deletes = sorted(existing_paths - set(writes))
    touched_paths = sorted(set(writes) | set(deletes))

    return RepositoryImportPlan(
        source_repository=str(source_repository.root),
        source_commit=source_commit,
        target_branch=selected_branch,
        repository_name=repository_name,
        writes=writes,
        deletes=deletes,
        touched_paths=touched_paths,
        warnings=warnings,
    )


def commit_repository_import(
    repository: Repository,
    plan: RepositoryImportPlan,
    *,
    message: str | None = None,
) -> RepositoryImportResult:
    """Commit a planned committed-snapshot import onto its target branch.

    Writes the normalized artifacts and prunes the planned deletes in one
    two-parent-free commit on ``plan.target_branch`` (created if absent), then
    attaches a ``stated`` import provenance note carrying the source commit as
    ``derived_from`` — honest provenance that never launders the import into a
    measured/calibrated origin, and never enters artifact identity (it lives on
    the git note, not the document).
    """

    if plan.warnings:
        raise ValueError("; ".join(plan.warnings))

    git = repository.require_git()
    primary_branch = git.primary_branch_name()
    if (
        git.branch_sha(plan.target_branch) is None
        and plan.target_branch != primary_branch
    ):
        git.create_branch(plan.target_branch)

    commit_sha: str | None = None
    with git.head_bound_transaction(plan.target_branch) as head_txn:
        with head_txn.families_transact(
            repository.families,
            message=message
            or f"Import {plan.repository_name} at {plan.source_commit[:12]}",
        ) as transaction:
            for planned_write in plan.writes.values():
                transaction.by_artifact_family(planned_write.family).save(
                    planned_write.ref, planned_write.document
                )
            for path in plan.deletes:
                family = PROPSTORE_FAMILY_REGISTRY.family_for_path(path)
                ref = repository.families.by_artifact_family(
                    family.artifact_family
                ).ref_from_path(path)
                transaction.by_artifact_family(family.artifact_family).delete(ref)
        commit_sha = head_txn.commit_sha
    if commit_sha is None:
        raise ValueError("repository import transaction did not produce a commit")

    write_provenance_note(
        git.raw_repo,
        commit_sha,
        _import_provenance(plan, commit_sha=commit_sha),
    )

    return RepositoryImportResult(
        surface="repository_import_commit",
        source_repository=plan.source_repository,
        source_commit=plan.source_commit,
        target_branch=plan.target_branch,
        commit_sha=commit_sha,
        touched_paths=list(plan.touched_paths),
        deleted_paths=list(plan.deletes),
    )
