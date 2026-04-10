from __future__ import annotations

from pathlib import Path

import yaml

from propstore.cli.repository import Repository
from propstore.document_schema import convert_document_value, decode_document_path

from .claims import load_source_claim_index
from .common import (
    commit_source_file,
    load_source_justifications_document,
    load_source_stances_document,
    normalize_source_slug,
    source_branch_name,
)
from .document_models import (
    SourceJustificationDocument,
    SourceJustificationsDocument,
    SourceProvenanceDocument,
    SourceStanceEntryDocument,
    SourceStancesDocument,
)


def resolve_local_claim_reference(reference: object, local_to_artifact: dict[str, str]) -> str:
    if not isinstance(reference, str) or not reference:
        raise ValueError("claim reference must be a non-empty string")
    if reference.startswith("ps:claim:"):
        return reference
    artifact_id = local_to_artifact.get(reference)
    if artifact_id is None:
        raise ValueError(f"unresolved local claim reference: {reference}")
    return artifact_id


def normalize_source_justifications_payload(
    data: SourceJustificationsDocument,
    *,
    local_to_artifact: dict[str, str],
) -> SourceJustificationsDocument:
    normalized_justifications: list[SourceJustificationDocument] = []
    for index, justification in enumerate(data.justifications, start=1):
        if justification.conclusion is None:
            raise ValueError("justification conclusion must be a non-empty string")
        normalized = justification.to_payload()
        normalized["conclusion"] = resolve_local_claim_reference(
            justification.conclusion,
            local_to_artifact,
        )
        normalized["premises"] = [
            resolve_local_claim_reference(premise, local_to_artifact)
            for premise in justification.premises
        ]
        attack_target = justification.attack_target
        if attack_target is not None and attack_target.target_claim is not None:
            updated_target = attack_target.to_payload()
            updated_target["target_claim"] = resolve_local_claim_reference(
                attack_target.target_claim,
                local_to_artifact,
            )
            normalized["attack_target"] = updated_target
        normalized_justifications.append(
            convert_document_value(
                normalized,
                SourceJustificationDocument,
                source=f"justifications[{index}]",
            )
        )
    return SourceJustificationsDocument(
        source=data.source,
        justifications=tuple(normalized_justifications),
    )


def commit_source_justifications_batch(repo: Repository, source_name: str, justifications_file: Path) -> str:
    local_to_artifact, _logical_to_artifact, _artifact_ids = load_source_claim_index(repo, source_name)
    normalized = normalize_source_justifications_payload(
        decode_document_path(justifications_file, SourceJustificationsDocument),
        local_to_artifact=local_to_artifact,
    )
    return commit_source_file(
        repo,
        source_name,
        relpath="justifications.yaml",
        content=yaml.safe_dump(normalized.to_payload(), sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Write justifications for {normalize_source_slug(source_name)}",
    )


def normalize_source_stances_payload(
    data: SourceStancesDocument,
    *,
    local_to_artifact: dict[str, str],
) -> SourceStancesDocument:
    normalized_stances: list[SourceStanceEntryDocument] = []
    for index, stance in enumerate(data.stances, start=1):
        if stance.source_claim is None:
            raise ValueError("stance source_claim must be a non-empty string")
        normalized = stance.to_payload()
        normalized["source_claim"] = resolve_local_claim_reference(
            stance.source_claim,
            local_to_artifact,
        )
        target = stance.target
        if isinstance(target, str) and target in local_to_artifact:
            normalized["target"] = local_to_artifact[target]
        normalized_stances.append(
            convert_document_value(
                normalized,
                SourceStanceEntryDocument,
                source=f"stances[{index}]",
            )
        )
    return SourceStancesDocument(
        source=data.source,
        stances=tuple(normalized_stances),
    )


def commit_source_stances_batch(repo: Repository, source_name: str, stances_file: Path) -> str:
    local_to_artifact, _logical_to_artifact, _artifact_ids = load_source_claim_index(repo, source_name)
    normalized = normalize_source_stances_payload(
        decode_document_path(stances_file, SourceStancesDocument),
        local_to_artifact=local_to_artifact,
    )
    return commit_source_file(
        repo,
        source_name,
        relpath="stances.yaml",
        content=yaml.safe_dump(normalized.to_payload(), sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Write stances for {normalize_source_slug(source_name)}",
    )


def commit_source_justification_proposal(
    repo: Repository,
    source_name: str,
    *,
    just_id: str,
    conclusion: str,
    premises: list[str],
    rule_kind: str,
    page: int | None = None,
) -> SourceJustificationDocument:
    branch = source_branch_name(source_name)
    local_to_artifact, _logical, _artifacts = load_source_claim_index(repo, source_name)
    existing = load_source_justifications_document(repo, source_name) or SourceJustificationsDocument(justifications=())
    justifications = [entry for entry in existing.justifications if entry.id != just_id]

    justification = SourceJustificationDocument(
        id=just_id,
        conclusion=conclusion,
        premises=tuple(premises),
        rule_kind=rule_kind,
    )
    if page is not None:
        justification = convert_document_value(
            {**justification.to_payload(), "provenance": SourceProvenanceDocument(page=page)},
            SourceJustificationDocument,
            source=f"{branch}:justifications proposal",
        )
    justifications.append(justification)
    normalized = normalize_source_justifications_payload(
        SourceJustificationsDocument(source=existing.source, justifications=tuple(justifications)),
        local_to_artifact=local_to_artifact,
    )

    commit_source_file(
        repo,
        source_name,
        relpath="justifications.yaml",
        content=yaml.safe_dump(normalized.to_payload(), sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Propose justification for {normalize_source_slug(source_name)}",
    )

    for entry in normalized.justifications:
        if entry.id == just_id:
            return entry
    return normalized.justifications[-1]


def commit_source_stance_proposal(
    repo: Repository,
    source_name: str,
    *,
    source_claim: str,
    target: str,
    stance_type: str,
    strength: str | None = None,
    note: str | None = None,
) -> SourceStanceEntryDocument:
    branch = source_branch_name(source_name)
    local_to_artifact, _logical, _artifacts = load_source_claim_index(repo, source_name)
    existing = load_source_stances_document(repo, source_name) or SourceStancesDocument(stances=())
    stances = list(existing.stances)

    stance = SourceStanceEntryDocument(
        source_claim=source_claim,
        target=target,
        type=stance_type,
    )
    if strength is not None:
        stance = convert_document_value(
            {**stance.to_payload(), "strength": strength},
            SourceStanceEntryDocument,
            source=f"{branch}:stances proposal",
        )
    if note is not None:
        stance = convert_document_value(
            {**stance.to_payload(), "note": note},
            SourceStanceEntryDocument,
            source=f"{branch}:stances proposal",
        )
    stances.append(stance)
    normalized = normalize_source_stances_payload(
        SourceStancesDocument(source=existing.source, stances=tuple(stances)),
        local_to_artifact=local_to_artifact,
    )

    commit_source_file(
        repo,
        source_name,
        relpath="stances.yaml",
        content=yaml.safe_dump(normalized.to_payload(), sort_keys=False, allow_unicode=True).encode("utf-8"),
        message=f"Propose stance for {normalize_source_slug(source_name)}",
    )

    return normalized.stances[-1]
