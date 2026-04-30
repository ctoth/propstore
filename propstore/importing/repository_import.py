"""Committed-snapshot repository import planning and commit helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from propstore.families.registry import (
    semantic_family_for_path,
    semantic_import_roots,
)
from propstore.source.passes import run_source_import_pipeline
from propstore.source.stages import (
    PlannedSemanticWrite,
    SourceImportAuthoredWrites,
    SourceImportNormalizedWrites,
)
from propstore.provenance import (
    Provenance,
    ProvenanceStatus,
    ProvenanceWitness,
    write_provenance_note,
)
from propstore.provenance.records import (
    ImportRunProvenanceRecord,
    LicenseProvenanceRecord,
    SourceVersionProvenanceRecord,
)

if TYPE_CHECKING:
    from propstore.repository import Repository


@dataclass(frozen=True)
class RepositoryImportPlan:
    """Planned committed-snapshot import between knowledge repositories."""

    source_repository: str
    source_commit: str
    target_branch: str
    repository_name: str
    writes: dict[str, PlannedSemanticWrite]
    deletes: list[str]
    touched_paths: list[str]
    import_run: ImportRunProvenanceRecord
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepositoryImportResult:
    """Committed repository import result."""

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
        snapshot_file.relpath: snapshot_file.content
        for snapshot_file in repository.snapshot.files(
            commit=commit,
            roots=semantic_import_roots(),
        )
    }


def _import_run_record(
    *,
    source_repository: str,
    source_commit: str,
    repository_name: str,
) -> ImportRunProvenanceRecord:
    source_digest = hashlib.sha256(source_repository.encode("utf-8")).hexdigest()
    source = SourceVersionProvenanceRecord(
        source_id=f"urn:propstore:repository:{source_digest}",
        version_id=source_commit,
        content_hash=f"git:{source_commit}",
    )
    license_record = LicenseProvenanceRecord(
        license_id="urn:propstore:license:unspecified",
        label="Unspecified",
    )
    return ImportRunProvenanceRecord(
        run_id=f"urn:propstore:repository-import:{source_commit}",
        importer_id="urn:propstore:agent:repository-import",
        imported_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        source=source,
        license=license_record,
    )


def plan_repository_import(
    destination_repository: Repository,
    source_repository_path: Path,
    *,
    target_branch: str | None = None,
) -> RepositoryImportPlan:
    """Plan a committed-snapshot import between knowledge repositories."""
    from propstore.repository import Repository, RepositoryNotFound

    try:
        source_repository = Repository.find(source_repository_path.resolve())
    except RepositoryNotFound as exc:
        raise ValueError("Source repository must be git-backed") from exc

    source_commit = source_repository.snapshot.head_sha()
    if source_commit is None:
        raise ValueError("Source repository has no committed HEAD")

    primary_branch = destination_repository.snapshot.primary_branch_name()
    repository_name = _infer_repository_name(source_repository)
    selected_branch = target_branch or f"import/{repository_name}"
    import_pipeline_result = run_source_import_pipeline(
        SourceImportAuthoredWrites(
            store=destination_repository.families.store,
            writes=_iter_semantic_paths(source_repository, commit=source_commit),
            repository_name=repository_name,
        )
    )
    if not isinstance(import_pipeline_result.output, SourceImportNormalizedWrites):
        errors = ", ".join(error.render() for error in import_pipeline_result.errors)
        raise ValueError(f"Repository import normalization failed: {errors}")
    normalized_import = import_pipeline_result.output
    writes = normalized_import.writes
    warnings = list(normalized_import.warnings)

    existing_paths: set[str] = set()
    existing_branch_sha = destination_repository.snapshot.branch_head(selected_branch)
    if existing_branch_sha is not None:
        existing_paths = set(_iter_semantic_paths(destination_repository, commit=existing_branch_sha))
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
        import_run=_import_run_record(
            source_repository=str(source_repository.root),
            source_commit=source_commit,
            repository_name=repository_name,
        ),
        warnings=warnings,
    )


def commit_repository_import(
    repository: Repository,
    plan: RepositoryImportPlan,
    *,
    message: str | None = None,
) -> RepositoryImportResult:
    """Commit a planned import onto the destination repository."""

    if plan.warnings:
        raise ValueError("; ".join(plan.warnings))

    primary_branch = repository.snapshot.primary_branch_name()
    if repository.snapshot.branch_head(plan.target_branch) is None and plan.target_branch != primary_branch:
        repository.snapshot.ensure_branch(plan.target_branch)

    commit_sha: str | None = None
    with repository.head_bound_transaction(plan.target_branch, path="repository_import") as head_txn:
        with head_txn.families_transact(
            message=message or f"Import {plan.repository_name} at {plan.source_commit[:12]}",
        ) as transaction:
            for planned_write in plan.writes.values():
                transaction.by_artifact_family(cast(Any, planned_write.family)).save(
                    cast(Any, planned_write.ref),
                    cast(Any, planned_write.document),
                )
            for path in plan.deletes:
                semantic_family = semantic_family_for_path(path)
                bound_family = transaction.by_artifact_family(cast(Any, semantic_family.artifact_family))
                bound_family.delete(bound_family.ref_from_path(path))
        commit_sha = head_txn.commit_sha
    if commit_sha is None:
        raise ValueError("repo import transaction did not produce a commit")
    git = repository.git
    if git is None:
        raise ValueError("repository import provenance requires a git-backed repository")
    write_provenance_note(
        git.raw_repo,
        commit_sha,
        Provenance(
            status=ProvenanceStatus.STATED,
            graph_name=f"urn:propstore:repository-import:{commit_sha}",
            witnesses=(
                ProvenanceWitness(
                    asserter=plan.import_run.importer_id,
                    timestamp=plan.import_run.imported_at,
                    source_artifact_code=plan.source_repository,
                    method="repository-import",
                ),
            ),
            derived_from=(plan.source_commit,),
            operations=("repository-import",),
        ),
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
