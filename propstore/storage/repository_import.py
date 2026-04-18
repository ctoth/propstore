"""Committed-snapshot repository import planning and commit helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from propstore.artifacts.codecs import decode_yaml_mapping
from propstore.artifacts.resolution import ImportedClaimHandleIndex
from propstore.artifacts.identity import (
    concept_reference_keys,
    normalize_claim_file_payload,
    normalize_canonical_claim_payload,
    normalize_canonical_concept_payload,
)

if TYPE_CHECKING:
    from propstore.artifacts.store import ArtifactRepository
    from propstore.repository import Repository


SEMANTIC_ROOT_DIRS = (
    "claims",
    "concepts",
    "contexts",
    "forms",
    "stances",
    "worldlines",
)


@dataclass(frozen=True)
class RepositoryImportPlan:
    """Planned committed-snapshot import between knowledge repositories."""

    source_repository: str
    source_commit: str
    target_branch: str
    repository_name: str
    writes: dict[str, "PlannedArtifactWrite"]
    deletes: list[str]
    touched_paths: list[str]
    sync_worktree_default: bool
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
    worktree_synced: bool


@dataclass(frozen=True)
class PlannedArtifactWrite:
    """Typed artifact write planned during repository import."""

    family: object
    ref: object
    document: object
    relpath: str


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
            roots=SEMANTIC_ROOT_DIRS,
        )
    }


def _family_for_semantic_path(path: str):
    from propstore.artifacts.families import (
        CLAIMS_FILE_FAMILY,
        CONCEPT_FILE_FAMILY,
        CONTEXT_FAMILY,
        FORM_FAMILY,
        STANCE_FILE_FAMILY,
        WORLDLINE_FAMILY,
    )

    root = path.split("/", 1)[0]
    if root == "claims":
        return CLAIMS_FILE_FAMILY
    if root == "concepts":
        return CONCEPT_FILE_FAMILY
    if root == "contexts":
        return CONTEXT_FAMILY
    if root == "forms":
        return FORM_FAMILY
    if root == "stances":
        return STANCE_FILE_FAMILY
    if root == "worldlines":
        return WORLDLINE_FAMILY
    raise ValueError(f"Unsupported semantic import path {path!r}")


def _planned_write(
    store,
    path: str,
    payload: object,
) -> PlannedArtifactWrite:
    family = _family_for_semantic_path(path)
    ref = store.ref_from_path(family, path)
    document = store.coerce(family, payload, source=path)
    return PlannedArtifactWrite(
        family=family,
        ref=ref,
        document=document,
        relpath=store.resolve(family, ref).relpath,
    )


def _document_payload(document: object) -> object:
    from propstore.artifacts.codecs import document_to_payload

    return document_to_payload(document)


def _decode_yaml(content: bytes, *, path: str) -> dict[str, Any]:
    return decode_yaml_mapping(content, source=path)


def _claim_source_from_import_path(path: str) -> dict[str, str]:
    return {"paper": Path(path).stem}


def _normalize_concept_payload(
    data: dict[str, Any],
    *,
    default_domain: str,
) -> tuple[dict[str, Any], set[str]]:
    raw_id = data.get("id")
    normalized = normalize_canonical_concept_payload(
        dict(data),
        default_domain=str(default_domain or "propstore"),
    )
    return normalized, concept_reference_keys(
        normalized,
        raw_id=raw_id if isinstance(raw_id, str) else None,
    )


def _rewrite_concept_reference(value: Any, concept_ref_map: dict[str, str]) -> Any:
    if not isinstance(value, str):
        return value
    return concept_ref_map.get(value, value)


def _rewrite_concept_payload_refs(
    data: dict[str, Any],
    *,
    concept_ref_map: dict[str, str],
) -> dict[str, Any]:
    rewritten = dict(data)
    if "replaced_by" in rewritten:
        rewritten["replaced_by"] = _rewrite_concept_reference(
            rewritten.get("replaced_by"),
            concept_ref_map,
        )

    relationships = rewritten.get("relationships")
    if isinstance(relationships, list):
        updated_relationships = []
        for rel in relationships:
            if not isinstance(rel, dict):
                updated_relationships.append(rel)
                continue
            rel_copy = dict(rel)
            rel_copy["target"] = _rewrite_concept_reference(rel_copy.get("target"), concept_ref_map)
            updated_relationships.append(rel_copy)
        rewritten["relationships"] = updated_relationships

    parameterizations = rewritten.get("parameterization_relationships")
    if isinstance(parameterizations, list):
        updated_parameterizations = []
        for param in parameterizations:
            if not isinstance(param, dict):
                updated_parameterizations.append(param)
                continue
            param_copy = dict(param)
            inputs = param_copy.get("inputs")
            if isinstance(inputs, list):
                param_copy["inputs"] = [
                    _rewrite_concept_reference(input_id, concept_ref_map)
                    for input_id in inputs
                ]
            updated_parameterizations.append(param_copy)
        rewritten["parameterization_relationships"] = updated_parameterizations

    return normalize_canonical_concept_payload(rewritten)


def _rewrite_claim_concept_refs(
    data: dict[str, Any],
    *,
    concept_ref_map: dict[str, str],
) -> dict[str, Any]:
    rewritten = dict(data)
    claims = rewritten.get("claims")
    if not isinstance(claims, list):
        return rewritten

    updated_claims: list[Any] = []
    for claim in claims:
        if not isinstance(claim, dict):
            updated_claims.append(claim)
            continue
        claim_copy = dict(claim)
        if "concept" in claim_copy:
            claim_copy["concept"] = _rewrite_concept_reference(
                claim_copy.get("concept"),
                concept_ref_map,
            )
        if "target_concept" in claim_copy:
            claim_copy["target_concept"] = _rewrite_concept_reference(
                claim_copy.get("target_concept"),
                concept_ref_map,
            )

        concepts = claim_copy.get("concepts")
        if isinstance(concepts, list):
            claim_copy["concepts"] = [
                _rewrite_concept_reference(concept_ref, concept_ref_map)
                for concept_ref in concepts
            ]

        variables = claim_copy.get("variables")
        if isinstance(variables, list):
            updated_variables = []
            for variable in variables:
                if not isinstance(variable, dict):
                    updated_variables.append(variable)
                    continue
                variable_copy = dict(variable)
                variable_copy["concept"] = _rewrite_concept_reference(
                    variable_copy.get("concept"),
                    concept_ref_map,
                )
                updated_variables.append(variable_copy)
            claim_copy["variables"] = updated_variables

        parameters = claim_copy.get("parameters")
        if isinstance(parameters, list):
            updated_parameters = []
            for parameter in parameters:
                if not isinstance(parameter, dict):
                    updated_parameters.append(parameter)
                    continue
                parameter_copy = dict(parameter)
                parameter_copy["concept"] = _rewrite_concept_reference(
                    parameter_copy.get("concept"),
                    concept_ref_map,
                )
                updated_parameters.append(parameter_copy)
            claim_copy["parameters"] = updated_parameters

        updated_claims.append(normalize_canonical_claim_payload(claim_copy))

    rewritten["claims"] = updated_claims
    return rewritten


def _normalize_imported_concept_write(
    store,
    path: str,
    *,
    payload: dict[str, Any],
    repository_name: str,
) -> tuple[PlannedArtifactWrite, set[str]]:
    seeded_payload = dict(payload)
    raw_id = seeded_payload.get("id")
    canonical_name = seeded_payload.get("canonical_name")
    effective_name = (
        canonical_name
        if isinstance(canonical_name, str) and canonical_name
        else str(raw_id or Path(path).stem or "concept")
    )
    if not isinstance(seeded_payload.get("canonical_name"), str) or not seeded_payload.get("canonical_name"):
        seeded_payload["canonical_name"] = effective_name
    if not isinstance(seeded_payload.get("status"), str) or not seeded_payload.get("status"):
        seeded_payload["status"] = "accepted"
    if not isinstance(seeded_payload.get("definition"), str) or not seeded_payload.get("definition"):
        seeded_payload["definition"] = effective_name
    if not isinstance(seeded_payload.get("form"), str) or not seeded_payload.get("form"):
        seeded_payload["form"] = "structural"

    normalized_payload, reference_keys = _normalize_concept_payload(
        seeded_payload,
        default_domain=repository_name,
    )
    return _planned_write(store, path, normalized_payload), reference_keys


def _normalize_imported_claim_write(
    store,
    path: str,
    *,
    payload: dict[str, Any],
    repository_name: str,
    concept_ref_map: dict[str, str],
) -> tuple[PlannedArtifactWrite, dict[str, str]]:
    seeded_payload = dict(payload)
    source = seeded_payload.get("source")
    has_source = isinstance(source, dict) and isinstance(source.get("paper"), str) and bool(source.get("paper"))

    normalized_payload, local_map = normalize_claim_file_payload(
        seeded_payload if has_source else payload,
        default_namespace=repository_name,
    )
    if not has_source:
        normalized_payload["source"] = _claim_source_from_import_path(path)
    rewritten_payload = _rewrite_claim_concept_refs(
        normalized_payload,
        concept_ref_map=concept_ref_map,
    )
    return _planned_write(store, path, rewritten_payload), local_map


def _normalize_imported_stance_write(
    store,
    path: str,
    *,
    payload: dict[str, Any],
    local_handle_index: ImportedClaimHandleIndex,
) -> PlannedArtifactWrite:
    return _planned_write(
        store,
        path,
        local_handle_index.rewrite_stance_payload(payload, path=path),
    )


def _normalize_import_writes(
    store: ArtifactRepository,
    writes: dict[str, bytes],
    *,
    repository_name: str,
) -> tuple[dict[str, PlannedArtifactWrite], list[str]]:
    normalized: dict[str, PlannedArtifactWrite] = {}
    warnings: list[str] = []
    concept_ref_map: dict[str, str] = {}

    concept_paths = [path for path in sorted(writes) if path.startswith("concepts/")]
    normalized_concepts: dict[str, PlannedArtifactWrite] = {}
    for path in concept_paths:
        concept_write, reference_keys = _normalize_imported_concept_write(
            store,
            path,
            payload=_decode_yaml(writes[path], path=path),
            repository_name=repository_name,
        )
        normalized_concepts[path] = concept_write
        artifact_id = getattr(concept_write.document, "artifact_id", None)
        if not isinstance(artifact_id, str) or not artifact_id:
            raise ValueError(f"Imported concept {path!r} is missing artifact_id after normalization")
        for reference_key in reference_keys:
            concept_ref_map[str(reference_key)] = artifact_id

    for path in concept_paths:
        concept_payload = _document_payload(normalized_concepts[path].document)
        if not isinstance(concept_payload, dict):
            raise TypeError(f"Imported concept {path!r} did not render to a mapping payload")
        normalized[path] = _planned_write(
            store,
            path,
            _rewrite_concept_payload_refs(
                concept_payload,
                concept_ref_map=concept_ref_map,
            ),
        )

    local_handle_index = ImportedClaimHandleIndex()
    claim_paths = [path for path in sorted(writes) if path.startswith("claims/")]
    for path in claim_paths:
        normalized[path], local_map = _normalize_imported_claim_write(
            store,
            path,
            payload=_decode_yaml(writes[path], path=path),
            repository_name=repository_name,
            concept_ref_map=concept_ref_map,
        )
        for local_id, artifact_id in local_map.items():
            if local_handle_index.record(local_id, artifact_id):
                warnings.append(
                    f"ambiguous imported claim handle {local_id!r}; stance files must use artifact IDs"
                )

    stance_paths = [path for path in sorted(writes) if path.startswith("stances/")]
    for path in stance_paths:
        normalized[path] = _normalize_imported_stance_write(
            store,
            path,
            payload=_decode_yaml(writes[path], path=path),
            local_handle_index=local_handle_index,
        )

    passthrough_paths = [
        path
        for path in sorted(writes)
        if path.split("/", 1)[0] in {"contexts", "forms", "worldlines"}
    ]
    for path in passthrough_paths:
        normalized[path] = _planned_write(store, path, _decode_yaml(writes[path], path=path))

    return normalized, warnings


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
    writes, warnings = _normalize_import_writes(
        destination_repository.artifacts,
        _iter_semantic_paths(source_repository, commit=source_commit),
        repository_name=repository_name,
    )

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
        sync_worktree_default=(selected_branch == primary_branch),
        warnings=warnings,
    )


def commit_repository_import(
    repository: Repository,
    plan: RepositoryImportPlan,
    *,
    message: str | None = None,
    sync_worktree: str = "auto",
) -> RepositoryImportResult:
    """Commit a planned import onto the destination repository."""

    if sync_worktree not in {"auto", "always", "never"}:
        raise ValueError("sync_worktree must be one of: auto, always, never")

    primary_branch = repository.snapshot.primary_branch_name()
    if repository.snapshot.branch_head(plan.target_branch) is None and plan.target_branch != primary_branch:
        repository.snapshot.ensure_branch(plan.target_branch)

    with repository.artifacts.transact(
        message=message or f"Import {plan.repository_name} at {plan.source_commit[:12]}",
        branch=plan.target_branch,
    ) as transaction:
        for planned_write in plan.writes.values():
            transaction.save(
                cast(Any, planned_write.family),
                cast(Any, planned_write.ref),
                cast(Any, planned_write.document),
            )
        for path in plan.deletes:
            family = cast(Any, _family_for_semantic_path(path))
            transaction.delete(family, repository.artifacts.ref_from_path(family, path))
    commit_sha = transaction.commit_sha
    if commit_sha is None:
        raise ValueError("repo import transaction did not produce a commit")

    should_sync = False
    if sync_worktree == "always":
        if plan.target_branch != primary_branch:
            raise ValueError(
                "Explicit worktree sync is only supported for the primary branch"
            )
        should_sync = True
    elif sync_worktree == "auto":
        should_sync = plan.sync_worktree_default

    if should_sync:
        repository.snapshot.sync_worktree()

    return RepositoryImportResult(
        surface="repository_import_commit",
        source_repository=plan.source_repository,
        source_commit=plan.source_commit,
        target_branch=plan.target_branch,
        commit_sha=commit_sha,
        touched_paths=list(plan.touched_paths),
        deleted_paths=list(plan.deletes),
        worktree_synced=should_sync,
    )
