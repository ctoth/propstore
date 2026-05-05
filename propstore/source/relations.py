from __future__ import annotations

from pathlib import Path

from propstore.claim_references import ClaimReferenceIndex, load_source_claim_reference_index
from propstore.families.registry import SourceRef
from propstore.repository import Repository
from quire.documents import convert_document_value, decode_document_path
from propstore.stances import StanceType, coerce_stance_type

from .common import (
    current_source_branch_head,
    is_stale_branch_error,
    load_source_justifications_document,
    load_source_stances_document,
    normalize_source_slug,
    source_branch_name,
)
from propstore.families.documents.sources import (
    ExtractionProvenanceDocument,
    SourceAttackTargetDocument,
    SourceJustificationDocument,
    SourceJustificationsDocument,
    SourceProvenanceDocument,
    SourceStanceEntryDocument,
    SourceStancesDocument,
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
    data: SourceJustificationsDocument,
    *,
    claim_index: ClaimReferenceIndex,
) -> SourceJustificationsDocument:
    normalized_justifications: list[SourceJustificationDocument] = []
    for index, justification in enumerate(data.justifications, start=1):
        if justification.conclusion is None:
            raise ValueError("justification conclusion must be a non-empty string")
        normalized = justification.to_payload()
        normalized["conclusion"] = claim_index.resolve_local(justification.conclusion)
        normalized["premises"] = [
            claim_index.resolve_local(premise)
            for premise in justification.premises
        ]
        attack_target = justification.attack_target
        if attack_target is not None and attack_target.target_claim is not None:
            updated_target = attack_target.to_payload()
            updated_target["target_claim"] = claim_index.resolve_local(attack_target.target_claim)
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
        produced_by=data.produced_by,
    )


def commit_source_justifications_batch(
    repo: Repository,
    source_name: str,
    justifications_file: Path,
    *,
    reader: str | None = None,
    method: str | None = None,
) -> str:
    from datetime import datetime, timezone

    claim_index = load_source_claim_reference_index(repo, source_name)
    raw = decode_document_path(justifications_file, SourceJustificationsDocument)
    if reader is not None:
        raw = SourceJustificationsDocument(
            source=raw.source,
            justifications=raw.justifications,
            produced_by=ExtractionProvenanceDocument(
                reader=reader,
                method=method,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
    normalized = normalize_source_justifications_payload(
        raw,
        claim_index=claim_index,
    )
    return repo.families.source_justifications.save(
        SourceRef(source_name),
        normalized,
        message=f"Write justifications for {normalize_source_slug(source_name)}",
    )


def normalize_source_stances_payload(
    data: SourceStancesDocument,
    *,
    claim_index: ClaimReferenceIndex,
) -> SourceStancesDocument:
    normalized_stances: list[SourceStanceEntryDocument] = []
    for index, stance in enumerate(data.stances, start=1):
        if stance.source_claim is None:
            raise ValueError("stance source_claim must be a non-empty string")
        normalized = stance.to_payload()
        normalized["source_claim"] = claim_index.resolve_local(stance.source_claim)
        normalized["target"] = claim_index.rewrite_local_target(stance.target)
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
        produced_by=data.produced_by,
    )


def commit_source_stances_batch(
    repo: Repository,
    source_name: str,
    stances_file: Path,
    *,
    reader: str | None = None,
    method: str | None = None,
) -> str:
    from datetime import datetime, timezone

    claim_index = load_source_claim_reference_index(repo, source_name)
    raw = decode_document_path(stances_file, SourceStancesDocument)
    if reader is not None:
        raw = SourceStancesDocument(
            source=raw.source,
            stances=raw.stances,
            produced_by=ExtractionProvenanceDocument(
                reader=reader,
                method=method,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
    normalized = normalize_source_stances_payload(
        raw,
        claim_index=claim_index,
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
    branch = source_branch_name(source_name)
    _validate_justification_rule_fields(
        rule_kind=rule_kind,
        rule_strength=rule_strength,
    )
    last_normalized: SourceJustificationsDocument | None = None
    for attempt in range(8):
        expected_head = current_source_branch_head(repo, source_name)
        claim_index = load_source_claim_reference_index(repo, source_name)
        existing = load_source_justifications_document(repo, source_name) or SourceJustificationsDocument(justifications=())
        justifications = [entry for entry in existing.justifications if entry.id != just_id]

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
            SourceJustificationsDocument(source=existing.source, justifications=tuple(justifications)),
            claim_index=claim_index,
        )

        try:
            repo.families.source_justifications.save(
                SourceRef(source_name),
                normalized,
                message=f"Propose justification for {normalize_source_slug(source_name)}",
                expected_head=expected_head,
            )
        except ValueError as exc:
            if attempt == 7 or not is_stale_branch_error(exc):
                raise
            continue
        last_normalized = normalized
        break

    if last_normalized is not None:
        for entry in last_normalized.justifications:
            if entry.id == just_id:
                return entry
        return last_normalized.justifications[-1]
    raise ValueError(f"could not write justification proposal {just_id!r}")


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
    branch = source_branch_name(source_name)
    normalized_stance_type = coerce_stance_type(stance_type)
    assert normalized_stance_type is not None
    last_normalized: SourceStancesDocument | None = None
    for attempt in range(8):
        expected_head = current_source_branch_head(repo, source_name)
        claim_index = load_source_claim_reference_index(repo, source_name)
        existing = load_source_stances_document(repo, source_name) or SourceStancesDocument(stances=())
        stances = list(existing.stances)

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
            SourceStancesDocument(source=existing.source, stances=tuple(stances)),
            claim_index=claim_index,
        )

        try:
            repo.families.source_stances.save(
                SourceRef(source_name),
                normalized,
                message=f"Propose stance for {normalize_source_slug(source_name)}",
                expected_head=expected_head,
            )
        except ValueError as exc:
            if attempt == 7 or not is_stale_branch_error(exc):
                raise
            continue
        last_normalized = normalized
        break

    if last_normalized is not None:
        return last_normalized.stances[-1]
    raise ValueError("could not write stance proposal")
