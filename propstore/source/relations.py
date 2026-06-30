"""Author stance and justification proposals onto a source branch.

Inter-claim *stances* (one claim rebuts/supports/... another) and intra-paper
*justifications* (a conclusion supported by premises under a rule) are authored
against the source branch's own claim handles. On every write the handles are
lowered to canonical claim ids through the source claim reference index (falling
back to the primary index), so a stored relation always points at a resolved
claim id — never a raw source-local handle.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import msgspec
from quire.documents import decode_document_path
from quire.references import FamilyReferenceIndex

from propstore.families.claims import Claim
from propstore.families.registry import SourceRef
from propstore.families.sources import (
    ExtractionProvenanceDocument,
    SourceAttackTargetDocument,
    SourceClaimDocument,
    SourceJustificationDocument,
    SourceJustificationsDocument,
    SourceProvenanceDocument,
    SourceStanceEntryDocument,
    SourceStancesDocument,
)
from propstore.repository import Repository
from propstore.stances import StanceType, coerce_stance_type

from .common import (
    current_source_branch_head,
    is_stale_branch_error,
    load_source_justifications_document,
    load_source_stances_document,
    normalize_source_slug,
)
from .reference_indexes import (
    primary_claim_index as build_primary_claim_index,
    resolve_source_or_primary_claim_id,
    source_claim_index as build_source_claim_index,
)

_ALLOWED_JUSTIFICATION_RULE_KINDS = frozenset(
    {
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
    }
)
_ALLOWED_JUSTIFICATION_RULE_STRENGTHS = frozenset({"strict", "defeasible"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_justification_rule_fields(
    *, rule_kind: str | None, rule_strength: str | None
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


def _require_source_or_primary_claim_id(
    reference: object,
    *,
    source: FamilyReferenceIndex[SourceClaimDocument],
    primary: FamilyReferenceIndex[Claim] | None,
) -> str:
    resolved = resolve_source_or_primary_claim_id(
        reference, source=source, primary=primary
    )
    if resolved is not None:
        return resolved
    if not isinstance(reference, str) or not reference:
        raise ValueError("claim reference must be a non-empty string")
    # Raises quire's typed missing-reference error with the unresolved handle.
    return source.require_id(reference)


# ---------------------------------------------------------------------------
# Justifications
# ---------------------------------------------------------------------------


def normalize_source_justifications_payload(
    data: SourceJustificationsDocument,
    *,
    claim_index: FamilyReferenceIndex[SourceClaimDocument],
    primary_claim_index: FamilyReferenceIndex[Claim] | None = None,
) -> SourceJustificationsDocument:
    """Lower every justification's claim references to canonical claim ids."""

    normalized: list[SourceJustificationDocument] = []
    for justification in data.justifications:
        if justification.conclusion is None:
            raise ValueError("justification conclusion must be a non-empty string")
        conclusion = claim_index.require_id(justification.conclusion)
        premises = tuple(
            _require_source_or_primary_claim_id(
                premise, source=claim_index, primary=primary_claim_index
            )
            for premise in justification.premises
        )
        attack_target = justification.attack_target
        if attack_target is not None and attack_target.target_claim is not None:
            attack_target = msgspec.structs.replace(
                attack_target,
                target_claim=_require_source_or_primary_claim_id(
                    attack_target.target_claim,
                    source=claim_index,
                    primary=primary_claim_index,
                ),
            )
        normalized.append(
            msgspec.structs.replace(
                justification,
                conclusion=conclusion,
                premises=premises,
                attack_target=attack_target,
            )
        )
    return SourceJustificationsDocument(
        justifications=tuple(normalized),
        source=data.source,
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
    """Ingest a justifications-batch YAML onto a source branch."""

    claim_index = build_source_claim_index(repo, source_name)
    primary_claim_index = build_primary_claim_index(repo)
    raw = decode_document_path(justifications_file, SourceJustificationsDocument)
    if reader is not None:
        raw = msgspec.structs.replace(
            raw,
            produced_by=ExtractionProvenanceDocument(
                reader=reader, method=method, timestamp=_utc_now()
            ),
        )
    normalized = normalize_source_justifications_payload(
        raw, claim_index=claim_index, primary_claim_index=primary_claim_index
    )
    return repo.families.source_justifications.save(
        SourceRef(source_name),
        normalized,
        message=f"Write justifications for {normalize_source_slug(source_name)}",
    )


def commit_source_justification_proposal(
    repo: Repository,
    source_name: str,
    *,
    just_id: str,
    conclusion: str,
    premises: tuple[str, ...],
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
    """Propose one justification onto a source branch (compare-and-swap retry)."""

    _validate_justification_rule_fields(
        rule_kind=rule_kind, rule_strength=rule_strength
    )
    paper = normalize_source_slug(source_name)
    provenance: SourceProvenanceDocument | None = None
    if any(item is not None for item in (page, section, quote_fragment, table, figure)):
        provenance = SourceProvenanceDocument(
            paper=paper,
            page=page,
            section=section,
            quote_fragment=quote_fragment,
            table=table,
            figure=figure,
        )
    attack_target: SourceAttackTargetDocument | None = None
    if any(
        item is not None
        for item in (
            attack_target_claim,
            attack_target_justification_id,
            attack_target_premise_index,
        )
    ):
        attack_target = SourceAttackTargetDocument(
            target_claim=attack_target_claim,
            target_justification_id=attack_target_justification_id,
            target_premise_index=attack_target_premise_index,
        )
    new_justification = SourceJustificationDocument(
        id=just_id,
        conclusion=conclusion,
        premises=premises,
        rule_kind=rule_kind,
        rule_strength=rule_strength,
        provenance=provenance,
        attack_target=attack_target,
    )

    last_normalized: SourceJustificationsDocument | None = None
    for attempt in range(8):
        expected_head = current_source_branch_head(repo, source_name)
        claim_index = build_source_claim_index(repo, source_name)
        primary_claim_index = build_primary_claim_index(repo)
        existing = load_source_justifications_document(
            repo, source_name
        ) or SourceJustificationsDocument(justifications=())
        kept = [
            entry for entry in existing.justifications if entry.id != just_id
        ]
        kept.append(new_justification)
        normalized = normalize_source_justifications_payload(
            SourceJustificationsDocument(
                justifications=tuple(kept), source=existing.source
            ),
            claim_index=claim_index,
            primary_claim_index=primary_claim_index,
        )
        try:
            repo.families.source_justifications.save(
                SourceRef(source_name),
                normalized,
                message=f"Propose justification for {paper}",
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


# ---------------------------------------------------------------------------
# Stances
# ---------------------------------------------------------------------------


def normalize_source_stances_payload(
    data: SourceStancesDocument,
    *,
    claim_index: FamilyReferenceIndex[SourceClaimDocument],
    primary_claim_index: FamilyReferenceIndex[Claim] | None = None,
) -> SourceStancesDocument:
    """Lower every stance's source/target claim references to canonical ids."""

    normalized: list[SourceStanceEntryDocument] = []
    for stance in data.stances:
        if stance.source_claim is None:
            raise ValueError("stance source_claim must be a non-empty string")
        source_claim = claim_index.require_id(stance.source_claim)
        target = resolve_source_or_primary_claim_id(
            stance.target, source=claim_index, primary=primary_claim_index
        )
        if target is None:
            raise ValueError(f"unresolved stance target: {stance.target}")
        normalized.append(
            msgspec.structs.replace(
                stance, source_claim=source_claim, target=target
            )
        )
    return SourceStancesDocument(
        stances=tuple(normalized),
        source=data.source,
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
    """Ingest a stances-batch YAML onto a source branch."""

    claim_index = build_source_claim_index(repo, source_name)
    primary_claim_index = build_primary_claim_index(repo)
    raw = decode_document_path(stances_file, SourceStancesDocument)
    if reader is not None:
        raw = msgspec.structs.replace(
            raw,
            produced_by=ExtractionProvenanceDocument(
                reader=reader, method=method, timestamp=_utc_now()
            ),
        )
    normalized = normalize_source_stances_payload(
        raw, claim_index=claim_index, primary_claim_index=primary_claim_index
    )
    return repo.families.source_stances.save(
        SourceRef(source_name),
        normalized,
        message=f"Write stances for {normalize_source_slug(source_name)}",
    )


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
    """Propose one stance onto a source branch (compare-and-swap retry)."""

    normalized_stance_type = coerce_stance_type(stance_type)
    if normalized_stance_type is None:
        raise ValueError("stance_type must be a valid stance type")
    paper = normalize_source_slug(source_name)
    new_stance = SourceStanceEntryDocument(
        source_claim=source_claim,
        target=target,
        type=normalized_stance_type,
        strength=strength,
        note=note,
    )

    last_normalized: SourceStancesDocument | None = None
    for attempt in range(8):
        expected_head = current_source_branch_head(repo, source_name)
        claim_index = build_source_claim_index(repo, source_name)
        primary_claim_index = build_primary_claim_index(repo)
        existing = load_source_stances_document(
            repo, source_name
        ) or SourceStancesDocument(stances=())
        stances = [*existing.stances, new_stance]
        normalized = normalize_source_stances_payload(
            SourceStancesDocument(stances=tuple(stances), source=existing.source),
            claim_index=claim_index,
            primary_claim_index=primary_claim_index,
        )
        try:
            repo.families.source_stances.save(
                SourceRef(source_name),
                normalized,
                message=f"Propose stance for {paper}",
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
