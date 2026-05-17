from __future__ import annotations

from pathlib import Path
from typing import Any

from propstore.families.batch_specs import SOURCE_JUSTIFICATION_BATCH_SPEC, SOURCE_STANCE_BATCH_SPEC
from propstore.families.claims.references import resolve_first_claim_reference_id
from propstore.families.registry import SourceRef
from propstore.repository import Repository, retry_live_branch_update
from quire.documents import convert_document_value, decode_document_batch_bytes
from quire.references import FamilyReferenceIndex
from propstore.stances import StanceType, coerce_stance_type

from .common import (
    load_source_justifications_document,
    load_source_stances_document,
    normalize_source_slug,
)
from propstore.families.documents.sources import (
    ExtractionProvenanceDocument,
    SourceClaimDocument,
    SourceAttackTargetDocument,
    SourceJustificationDocument,
    SourceProvenanceDocument,
    SourceStanceEntryDocument,
)
from .reference_indexes import (
    primary_claim_index as build_primary_claim_index,
    source_claim_index as build_source_claim_index,
)

_ALLOWED_JUSTIFICATION_RULE_KINDS = frozenset({
    "causal_explanation",
    "comparison_based_inference",
    "definition_application",
    "empirical_support",
    "explains",
    "methodological_inference",
    "reported_claim",
    "scope_limitation",
    "statistical_inference",
    "supports",
})
_ALLOWED_JUSTIFICATION_RULE_STRENGTHS = frozenset({
    "strict",
    "defeasible",
})


def _validate_justification_rule_fields(
    *,
    rule_kind: str | None,
    rule_strength: str | None,
) -> None:
    if rule_kind not in _ALLOWED_JUSTIFICATION_RULE_KINDS:
        allowed = ", ".join(sorted(_ALLOWED_JUSTIFICATION_RULE_KINDS))
        raise ValueError(f"rule_kind must be one of: {allowed}")
    if (
        rule_strength is not None
        and rule_strength not in _ALLOWED_JUSTIFICATION_RULE_STRENGTHS
    ):
        allowed = ", ".join(sorted(_ALLOWED_JUSTIFICATION_RULE_STRENGTHS))
        raise ValueError(f"rule_strength must be one of: {allowed}")


def normalize_source_justifications_payload(
    data: tuple[SourceJustificationDocument, ...],
    *,
    claim_index: FamilyReferenceIndex[SourceClaimDocument],
    primary_claim_index: FamilyReferenceIndex[Any] | None = None,
) -> tuple[SourceJustificationDocument, ...]:
    normalized_justifications: list[SourceJustificationDocument] = []
    for index, justification in enumerate(data, start=1):
        if justification.conclusion is None:
            raise ValueError("justification conclusion must be a non-empty string")
        normalized = justification.to_payload()
        normalized["conclusion"] = claim_index.require_id(justification.conclusion)
        normalized["premises"] = [
            _require_source_or_primary_claim_id(
                premise,
                source=claim_index,
                primary=primary_claim_index,
            )
            for premise in justification.premises
        ]
        attack_target = justification.attack_target
        if attack_target is not None and attack_target.target_claim is not None:
            updated_target = attack_target.to_payload()
            updated_target["target_claim"] = _require_source_or_primary_claim_id(
                attack_target.target_claim,
                source=claim_index,
                primary=primary_claim_index,
            )
            normalized["attack_target"] = updated_target
        normalized_justifications.append(
            convert_document_value(
                normalized,
                SourceJustificationDocument,
                source=f"justifications[{index}]",
            )
        )
    return tuple(normalized_justifications)


def commit_source_justifications_batch(
    repo: Repository,
    source_name: str,
    justifications_file: Path,
    *,
    reader: str | None = None,
    method: str | None = None,
) -> str:
    from datetime import datetime, timezone

    claim_index = build_source_claim_index(repo, source_name)
    primary_claim_index = build_primary_claim_index(repo)
    raw = decode_document_batch_bytes(
        justifications_file.read_bytes(),
        SOURCE_JUSTIFICATION_BATCH_SPEC,
        source=str(justifications_file),
    )
    if reader is not None:
        provenance = ExtractionProvenanceDocument(
                reader=reader,
                method=method,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        raw = tuple(
            convert_document_value(
                {
                    **justification.to_payload(),
                    "produced_by": provenance.to_payload(),
                },
                SourceJustificationDocument,
                source=f"{justifications_file}:justifications[{index}]",
            )
            for index, justification in enumerate(raw, start=1)
        )
    normalized = normalize_source_justifications_payload(
        raw,
        claim_index=claim_index,
        primary_claim_index=primary_claim_index,
    )
    return repo.families.source_justifications.save(
        SourceRef(source_name),
        normalized,
        message=f"Write justifications for {normalize_source_slug(source_name)}",
    )


def normalize_source_stances_payload(
    data: tuple[SourceStanceEntryDocument, ...],
    *,
    claim_index: FamilyReferenceIndex[SourceClaimDocument],
    primary_claim_index: FamilyReferenceIndex[Any] | None = None,
) -> tuple[SourceStanceEntryDocument, ...]:
    normalized_stances: list[SourceStanceEntryDocument] = []
    for index, stance in enumerate(data, start=1):
        if stance.source_claim is None:
            raise ValueError("stance source_claim must be a non-empty string")
        normalized = stance.to_payload()
        normalized["source_claim"] = claim_index.require_id(stance.source_claim)
        target = resolve_first_claim_reference_id(
            stance.target,
            claim_index,
            primary_claim_index,
        )
        if target is None:
            raise ValueError(f"unresolved stance target: {stance.target}")
        normalized["target"] = target
        normalized_stances.append(
            convert_document_value(
                normalized,
                SourceStanceEntryDocument,
                source=f"stances[{index}]",
            )
        )
    return tuple(normalized_stances)


def _require_source_or_primary_claim_id(
    reference: object,
    *,
    source: FamilyReferenceIndex[SourceClaimDocument],
    primary: FamilyReferenceIndex[Any] | None,
) -> str:
    resolved = resolve_first_claim_reference_id(
        reference,
        source,
        primary,
    )
    if resolved is None:
        if not isinstance(reference, str) or not reference:
            raise ValueError("claim reference must be a non-empty string")
        source.require_id(reference)  # raises Quire's typed missing error
        raise AssertionError("unreachable")
    return resolved


def commit_source_stances_batch(
    repo: Repository,
    source_name: str,
    stances_file: Path,
    *,
    reader: str | None = None,
    method: str | None = None,
) -> str:
    from datetime import datetime, timezone

    claim_index = build_source_claim_index(repo, source_name)
    primary_claim_index = build_primary_claim_index(repo)
    raw = decode_document_batch_bytes(
        stances_file.read_bytes(),
        SOURCE_STANCE_BATCH_SPEC,
        source=str(stances_file),
    )
    if reader is not None:
        provenance = ExtractionProvenanceDocument(
                reader=reader,
                method=method,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        raw = tuple(
            convert_document_value(
                {
                    **stance.to_payload(),
                    "produced_by": provenance.to_payload(),
                },
                SourceStanceEntryDocument,
                source=f"{stances_file}:stances[{index}]",
            )
            for index, stance in enumerate(raw, start=1)
        )
    normalized = normalize_source_stances_payload(
        raw,
        claim_index=claim_index,
        primary_claim_index=primary_claim_index,
    )
    return repo.families.source_stances.save(
        SourceRef(source_name),
        normalized,
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
    rule_strength: str | None = None,
    page: int | None = None,
    section: str | None = None,
    quote_fragment: str | None = None,
    table: str | None = None,
    figure: str | None = None,
    attack_target_claim: str | None = None,
    attack_target_justification_id: str | None = None,
    attack_target_premise_index: int | None = None,
) -> SourceJustificationDocument:
    branch = repo.families.source_justifications.address(SourceRef(source_name)).branch
    _validate_justification_rule_fields(
        rule_kind=rule_kind,
        rule_strength=rule_strength,
    )

    def update(expected_head: str | None) -> tuple[SourceJustificationDocument, ...]:
        claim_index = build_source_claim_index(repo, source_name)
        primary_claim_index = build_primary_claim_index(repo)
        existing = load_source_justifications_document(
            repo, source_name
        ) or ()
        justifications = [entry for entry in existing if entry.id != just_id]

        justification = SourceJustificationDocument(
            id=just_id,
            conclusion=conclusion,
            premises=tuple(premises),
            rule_kind=rule_kind,
            rule_strength=rule_strength,
        )
        if any(value is not None for value in (page, section, quote_fragment, table, figure)):
            justification = convert_document_value(
                {
                    **justification.to_payload(),
                    "provenance": SourceProvenanceDocument(
                        paper=normalize_source_slug(source_name),
                        page=page,
                        section=section,
                        quote_fragment=quote_fragment,
                        table=table,
                        figure=figure,
                    ),
                },
                SourceJustificationDocument,
                source=f"{branch}:justifications proposal",
            )
        if any(
            value is not None
            for value in (
                attack_target_claim,
                attack_target_justification_id,
                attack_target_premise_index,
            )
        ):
            justification = convert_document_value(
                {
                    **justification.to_payload(),
                    "attack_target": SourceAttackTargetDocument(
                        target_claim=attack_target_claim,
                        target_justification_id=attack_target_justification_id,
                        target_premise_index=attack_target_premise_index,
                    ),
                },
                SourceJustificationDocument,
                source=f"{branch}:justifications proposal",
            )
        justifications.append(justification)
        normalized = normalize_source_justifications_payload(
            tuple(justifications),
            claim_index=claim_index,
            primary_claim_index=primary_claim_index,
        )

        repo.families.source_justifications.save(
            SourceRef(source_name),
            normalized,
            message=f"Propose justification for {normalize_source_slug(source_name)}",
            expected_head=expected_head,
        )
        return normalized

    normalized = retry_live_branch_update(repo, branch, update)
    for entry in normalized:
        if entry.id == just_id:
            return entry
    return normalized[-1]


def commit_source_stance_proposal(
    repo: Repository,
    source_name: str,
    *,
    source_claim: str,
    target: str,
    stance_type: StanceType,
    strength: str | None = None,
    note: str | None = None,
) -> SourceStanceEntryDocument:
    branch = repo.families.source_stances.address(SourceRef(source_name)).branch
    normalized_stance_type = coerce_stance_type(stance_type)
    assert normalized_stance_type is not None

    def update(expected_head: str | None) -> tuple[SourceStanceEntryDocument, ...]:
        claim_index = build_source_claim_index(repo, source_name)
        primary_claim_index = build_primary_claim_index(repo)
        existing = load_source_stances_document(repo, source_name) or ()
        stances = list(existing)

        stance = SourceStanceEntryDocument(
            source_claim=source_claim,
            target=target,
            type=normalized_stance_type,
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
            tuple(stances),
            claim_index=claim_index,
            primary_claim_index=primary_claim_index,
        )

        repo.families.source_stances.save(
            SourceRef(source_name),
            normalized,
            message=f"Propose stance for {normalize_source_slug(source_name)}",
            expected_head=expected_head,
        )
        return normalized

    normalized = retry_live_branch_update(repo, branch, update)
    return normalized[-1]
