"""Committed-snapshot repository import planning and commit helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from propstore.identity import (
    compute_claim_version_id,
    compute_concept_version_id,
    derive_concept_artifact_id,
    format_logical_id,
    normalize_claim_file_payload,
    normalize_identity_namespace,
    normalize_logical_value,
    rewrite_stance_file_payload,
)
from propstore.repo.branch import branch_head, create_branch

if TYPE_CHECKING:
    from propstore.cli.repository import Repository


SEMANTIC_ROOT_DIRS = (
    "claims",
    "concepts",
    "contexts",
    "forms",
    "stances",
    "worldlines",
)


@dataclass(frozen=True)
class RepoImportPlan:
    """Planned committed-snapshot import from a source repo into a destination repo."""

    source_repo: str
    source_commit: str
    target_branch: str
    repo_name: str
    writes: dict[str, bytes]
    deletes: list[str]
    touched_paths: list[str]
    sync_worktree_default: bool
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepoImportResult:
    """Committed repository import result."""

    surface: str
    source_repo: str
    source_commit: str
    target_branch: str
    commit_sha: str
    touched_paths: list[str]
    deleted_paths: list[str]
    worktree_synced: bool


def _infer_repo_name(repo: Repository) -> str:
    root = repo.root
    if root.name == "knowledge" and root.parent.name:
        return root.parent.name
    return root.name


def _iter_semantic_paths(repo: Repository, *, commit: str) -> dict[str, bytes]:
    git = repo.git
    if git is None:
        raise ValueError("Repository must be git-backed")

    tree = git._get_tree(commit)
    if tree is None:
        return {}

    flattened: dict[str, bytes] = {}
    git._flatten_tree(tree, "", flattened)
    return {
        path: git.read_file(path, commit=commit)
        for path in sorted(flattened)
        if path.split("/", 1)[0] in SEMANTIC_ROOT_DIRS
    }


def _decode_yaml(content: bytes, *, path: str) -> dict[str, Any]:
    data = yaml.safe_load(content) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Imported semantic file {path!r} must decode to a mapping")
    return data


def _encode_yaml(data: dict[str, Any]) -> bytes:
    return yaml.safe_dump(data, sort_keys=False).encode("utf-8")


def _normalize_concept_payload(
    data: dict[str, Any],
    *,
    default_domain: str,
) -> tuple[dict[str, Any], set[str]]:
    normalized = dict(data)
    raw_id = normalized.pop("id", None)
    canonical_name = normalized.get("canonical_name")
    effective_name = (
        canonical_name
        if isinstance(canonical_name, str) and canonical_name
        else str(raw_id or "concept")
    )
    normalized["canonical_name"] = effective_name
    effective_domain = str(normalized.get("domain") or default_domain or "propstore")
    normalized["domain"] = effective_domain

    propstore_handle = normalize_logical_value(str(raw_id or effective_name))
    artifact_id = normalized.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id:
        artifact_id = derive_concept_artifact_id("propstore", propstore_handle)
    normalized["artifact_id"] = artifact_id

    primary_namespace = normalize_identity_namespace(effective_domain)
    primary_value = normalize_logical_value(str(effective_name))
    logical_ids: list[dict[str, str]] = [{"namespace": primary_namespace, "value": primary_value}]
    if primary_namespace != "propstore" or propstore_handle != primary_value:
        logical_ids.append({"namespace": "propstore", "value": propstore_handle})
    normalized["logical_ids"] = logical_ids
    normalized["version_id"] = compute_concept_version_id(normalized)

    reference_keys = {artifact_id, primary_value, effective_name, propstore_handle}
    if isinstance(raw_id, str) and raw_id:
        reference_keys.add(raw_id)
    for entry in logical_ids:
        formatted = format_logical_id(entry)
        if formatted:
            reference_keys.add(formatted)
    for alias in normalized.get("aliases", []) or []:
        if not isinstance(alias, dict):
            continue
        alias_name = alias.get("name")
        if isinstance(alias_name, str) and alias_name:
            reference_keys.add(alias_name)

    return normalized, reference_keys


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

    rewritten["version_id"] = compute_concept_version_id(rewritten)
    return rewritten


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

        claim_copy["version_id"] = compute_claim_version_id(claim_copy)
        updated_claims.append(claim_copy)

    rewritten["claims"] = updated_claims
    return rewritten


def _normalize_import_writes(
    writes: dict[str, bytes],
    *,
    repo_name: str,
) -> tuple[dict[str, bytes], list[str]]:
    normalized = dict(writes)
    warnings: list[str] = []
    concept_ref_map: dict[str, str] = {}

    concept_paths = [path for path in sorted(writes) if path.startswith("concepts/")]
    normalized_concepts: dict[str, dict[str, Any]] = {}
    for path in concept_paths:
        payload, reference_keys = _normalize_concept_payload(
            _decode_yaml(writes[path], path=path),
            default_domain=repo_name,
        )
        normalized_concepts[path] = payload
        artifact_id = payload["artifact_id"]
        for reference_key in reference_keys:
            concept_ref_map[str(reference_key)] = artifact_id

    for path in concept_paths:
        normalized[path] = _encode_yaml(
            _rewrite_concept_payload_refs(
                normalized_concepts[path],
                concept_ref_map=concept_ref_map,
            )
        )

    local_to_artifact: dict[str, str | None] = {}
    claim_paths = [path for path in sorted(writes) if path.startswith("claims/")]
    for path in claim_paths:
        payload, local_map = normalize_claim_file_payload(
            _decode_yaml(writes[path], path=path),
            default_namespace=repo_name,
        )
        payload = _rewrite_claim_concept_refs(payload, concept_ref_map=concept_ref_map)
        normalized[path] = _encode_yaml(payload)
        for local_id, artifact_id in local_map.items():
            previous = local_to_artifact.get(local_id)
            if previous is None and local_id in local_to_artifact:
                continue
            if previous is not None and previous != artifact_id:
                local_to_artifact[local_id] = None
                warnings.append(
                    f"ambiguous imported claim handle {local_id!r}; stance files must use artifact IDs"
                )
                continue
            local_to_artifact[local_id] = artifact_id

    stance_paths = [path for path in sorted(writes) if path.startswith("stances/")]
    for path in stance_paths:
        payload = _decode_yaml(writes[path], path=path)
        source_claim = payload.get("source_claim")
        if isinstance(source_claim, str) and source_claim in local_to_artifact and local_to_artifact[source_claim] is None:
            raise ValueError(
                f"Imported stance file {path!r} references ambiguous source_claim {source_claim!r}"
            )
        stances = payload.get("stances")
        if isinstance(stances, list):
            for stance in stances:
                if not isinstance(stance, dict):
                    continue
                target = stance.get("target")
                if isinstance(target, str) and target in local_to_artifact and local_to_artifact[target] is None:
                    raise ValueError(
                        f"Imported stance file {path!r} references ambiguous target {target!r}"
                    )
        resolved_map = {
            local_id: artifact_id
            for local_id, artifact_id in local_to_artifact.items()
            if artifact_id is not None
        }
        normalized[path] = _encode_yaml(
            rewrite_stance_file_payload(payload, local_to_artifact=resolved_map)
        )

    return normalized, warnings


def plan_repo_import(
    destination_repo: Repository,
    source_repo_path: Path,
    *,
    target_branch: str | None = None,
) -> RepoImportPlan:
    """Plan a committed-snapshot import from a source repo into a destination repo."""
    from propstore.cli.repository import Repository, RepositoryNotFound

    if destination_repo.git is None:
        raise ValueError("Destination repository must be git-backed")

    try:
        source_repo = Repository.find(source_repo_path.resolve())
    except RepositoryNotFound as exc:
        raise ValueError("Source repository must be git-backed") from exc
    if source_repo.git is None:
        raise ValueError("Source repository must be git-backed")

    source_commit = source_repo.git.head_sha()
    if source_commit is None:
        raise ValueError("Source repository has no committed HEAD")

    primary_branch = destination_repo.git.primary_branch_name()
    repo_name = _infer_repo_name(source_repo)
    selected_branch = target_branch or f"import/{repo_name}"
    writes, warnings = _normalize_import_writes(
        _iter_semantic_paths(source_repo, commit=source_commit),
        repo_name=repo_name,
    )

    existing_paths: set[str] = set()
    existing_branch_sha = branch_head(destination_repo.git, selected_branch)
    if existing_branch_sha is not None:
        existing_paths = set(_iter_semantic_paths(destination_repo, commit=existing_branch_sha))
    deletes = sorted(existing_paths - set(writes))
    touched_paths = sorted(set(writes) | set(deletes))

    return RepoImportPlan(
        source_repo=str(source_repo.root),
        source_commit=source_commit,
        target_branch=selected_branch,
        repo_name=repo_name,
        writes=writes,
        deletes=deletes,
        touched_paths=touched_paths,
        sync_worktree_default=(selected_branch == primary_branch),
        warnings=warnings,
    )


def commit_repo_import(
    repo: Repository,
    plan: RepoImportPlan,
    *,
    message: str | None = None,
    sync_worktree: str = "auto",
) -> RepoImportResult:
    """Commit a planned import onto the destination repository."""

    git = repo.git
    if git is None:
        raise ValueError("Destination repository must be git-backed")

    if sync_worktree not in {"auto", "always", "never"}:
        raise ValueError("sync_worktree must be one of: auto, always, never")

    primary_branch = git.primary_branch_name()
    if branch_head(git, plan.target_branch) is None and plan.target_branch != primary_branch:
        create_branch(git, plan.target_branch)

    commit_sha = git.commit_batch(
        adds=plan.writes,
        deletes=plan.deletes,
        message=message or f"Import {plan.repo_name} at {plan.source_commit[:12]}",
        branch=plan.target_branch,
    )

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
        git.sync_worktree()

    return RepoImportResult(
        surface="repo_import_commit",
        source_repo=plan.source_repo,
        source_commit=plan.source_commit,
        target_branch=plan.target_branch,
        commit_sha=commit_sha,
        touched_paths=list(plan.touched_paths),
        deleted_paths=list(plan.deletes),
        worktree_synced=should_sync,
    )
