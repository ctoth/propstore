"""Micropublication model declarations and family-owned compilation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass

from quire.references import FamilyReferenceIndex

from propstore.families.claims.references import ClaimReferenceRecord
from propstore.families.diagnostics.declaration import QuarantineDiagnostic
from propstore.families.documents.micropubs import MicropublicationDocument


class Micropublication:
    id: str
    context_id: str
    assumptions_json: str
    evidence_json: str
    stance: str | None
    provenance_json: str | None
    source_slug: str | None
    claim_links: list["MicropublicationClaimLink"]

    def __init__(
        self,
        *,
        id: str,
        context_id: str,
        assumptions_json: str = "[]",
        evidence_json: str = "[]",
        stance: str | None = None,
        provenance_json: str | None = None,
        source_slug: str | None = None,
    ) -> None:
        self.id = id
        self.context_id = context_id
        self.assumptions_json = assumptions_json
        self.evidence_json = evidence_json
        self.stance = stance
        self.provenance_json = provenance_json
        self.source_slug = source_slug
        self.claim_links = []

    @property
    def claim_ids(self) -> tuple[str, ...]:
        return tuple(
            link.claim_id
            for link in sorted(self.claim_links, key=lambda link: (link.seq, link.claim_id))
        )


class MicropublicationClaimLink:
    micropublication_id: str
    claim_id: str
    seq: int
    micropublication: Micropublication | None

    def __init__(
        self,
        *,
        micropublication_id: str,
        claim_id: str,
        seq: int,
    ) -> None:
        self.micropublication_id = micropublication_id
        self.claim_id = claim_id
        self.seq = seq
        self.micropublication = None


@dataclass(frozen=True)
class MicropublicationWriteModels:
    micropublications: tuple[Micropublication, ...]
    claim_links: tuple[MicropublicationClaimLink, ...]


def compile_micropublication_models_with_diagnostics(
    micropub_entries: Iterable[tuple[str, MicropublicationDocument]],
    claim_index: FamilyReferenceIndex[ClaimReferenceRecord],
) -> tuple[MicropublicationWriteModels, tuple[QuarantineDiagnostic, ...]]:
    valid_claim_ids = set(claim_index.ids())
    micropublications: list[Micropublication] = []
    claim_links: list[MicropublicationClaimLink] = []
    diagnostics: list[QuarantineDiagnostic] = []

    for filename, micropub in sorted(micropub_entries, key=lambda item: item[0]):
        resolved_claims: list[str] = []
        missing_claim_ref: str | None = None
        for claim_id in micropub.claims:
            resolved_claim = claim_index.resolve_id(claim_id)
            if (
                not isinstance(resolved_claim, str)
                or resolved_claim not in valid_claim_ids
            ):
                if isinstance(resolved_claim, str) and resolved_claim:
                    missing_claim_ref = resolved_claim
                elif isinstance(claim_id, str) and claim_id:
                    missing_claim_ref = claim_id
                else:
                    missing_claim_ref = micropub.artifact_id
                break
            resolved_claims.append(resolved_claim)
        if missing_claim_ref is not None:
            message = (
                f"micropublication artifact {micropub.artifact_id} references "
                f"nonexistent claim '{missing_claim_ref}'"
            )
            diagnostics.append(
                QuarantineDiagnostic(
                    artifact_id=missing_claim_ref,
                    kind="micropublication",
                    diagnostic_kind="micropublication_validation",
                    message=message,
                    file=filename,
                )
            )
            continue

        micropublications.append(
            Micropublication(
                id=micropub.artifact_id,
                context_id=str(micropub.context.id),
                assumptions_json=json.dumps(
                    list(micropub.assumptions),
                    sort_keys=True,
                ),
                evidence_json=json.dumps(
                    [item.to_payload() for item in micropub.evidence],
                    sort_keys=True,
                ),
                stance=None if micropub.stance is None else micropub.stance.value,
                provenance_json=(
                    None
                    if micropub.provenance is None
                    else json.dumps(
                        micropub.provenance.to_payload(),
                        sort_keys=True,
                    )
                ),
                source_slug=micropub.source,
            )
        )
        for seq, claim_id in enumerate(resolved_claims, start=1):
            claim_links.append(
                MicropublicationClaimLink(
                    micropublication_id=micropub.artifact_id,
                    claim_id=claim_id,
                    seq=seq,
                )
            )

    return (
        MicropublicationWriteModels(
            micropublications=tuple(micropublications),
            claim_links=tuple(claim_links),
        ),
        tuple(diagnostics),
    )
