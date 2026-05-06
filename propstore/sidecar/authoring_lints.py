"""Authoring-quality lints surfaced during sidecar builds."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from propstore.claims import ClaimFileEntry, claim_file_claims, claim_file_filename
from propstore.families.claims.stages import ClaimStage
from propstore.families.documents.sources import SourceDocument
from propstore.families.documents.stances import StanceFileDocument
from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.types import PassDiagnostic
from propstore.stances import StanceType


def collect_authoring_lints(
    *,
    source_entries: Iterable[tuple[str, SourceDocument]],
    stance_entries: Iterable[tuple[str, StanceFileDocument]],
    claim_files: Sequence[ClaimFileEntry],
) -> tuple[PassDiagnostic, ...]:
    diagnostics: list[PassDiagnostic] = []
    diagnostics.extend(_lint_sources(source_entries))
    diagnostics.extend(_lint_stance_files(stance_entries))
    diagnostics.extend(_lint_claim_files(claim_files))
    return tuple(diagnostics)


def _authoring_warning(
    *,
    code: str,
    message: str,
    family: PropstoreFamily,
    filename: str | None,
    artifact_id: str | None,
) -> PassDiagnostic:
    return PassDiagnostic(
        level="warning",
        code=code,
        message=message,
        family=family,
        stage=ClaimStage.AUTHORED,
        filename=filename,
        artifact_id=artifact_id,
        pass_name="sidecar.authoring_lints",
    )


def _lint_sources(
    source_entries: Iterable[tuple[str, SourceDocument]],
) -> tuple[PassDiagnostic, ...]:
    diagnostics: list[PassDiagnostic] = []
    for slug, source in source_entries:
        if slug.startswith("Unknown_"):
            diagnostics.append(
                _authoring_warning(
                    code="authoring.source_unknown_slug",
                    family=PropstoreFamily.SOURCES,
                    filename=slug,
                    artifact_id=source.id,
                    message=f"source {slug!r} uses an Unknown_* slug",
                )
            )
        if source.metadata is None or not source.metadata.name.strip():
            diagnostics.append(
                _authoring_warning(
                    code="authoring.source_missing_description",
                    family=PropstoreFamily.SOURCES,
                    filename=slug,
                    artifact_id=source.id,
                    message=f"source {slug!r} has no descriptive metadata",
                )
            )
    return tuple(diagnostics)


def _lint_stance_files(
    stance_entries: Iterable[tuple[str, StanceFileDocument]],
) -> tuple[PassDiagnostic, ...]:
    diagnostics: list[PassDiagnostic] = []
    for source_claim, document in stance_entries:
        for index, stance in enumerate(document.stances, start=1):
            stance_label = f"{source_claim}#{index}"
            diagnostics.extend(
                _lint_stance(
                    stance_type=stance.type,
                    strength=stance.strength,
                    target_justification_id=stance.target_justification_id,
                    filename=source_claim,
                    artifact_id=stance_label,
                )
            )
    return tuple(diagnostics)


def _lint_claim_files(
    claim_files: Sequence[ClaimFileEntry],
) -> tuple[PassDiagnostic, ...]:
    diagnostics: list[PassDiagnostic] = []
    for claim_file in claim_files:
        filename = claim_file_filename(claim_file)
        for claim in claim_file_claims(claim_file):
            claim_id = claim.artifact_id or claim.primary_logical_id or claim.id or filename
            provenance = claim.provenance
            if (
                provenance is not None
                and provenance.page == 1
                and provenance.quote_fragment is None
                and provenance.section is None
                and provenance.table is None
                and provenance.figure is None
            ):
                diagnostics.append(
                    _authoring_warning(
                        code="authoring.claim_placeholder_page",
                        family=PropstoreFamily.CLAIMS,
                        filename=filename,
                        artifact_id=claim_id,
                        message=(
                            f"claim {claim_id!r} has provenance page=1 with "
                            "no quote, section, table, or figure"
                        ),
                    )
                )
            for index, stance in enumerate(claim.stances, start=1):
                diagnostics.extend(
                    _lint_stance(
                        stance_type=stance.type,
                        strength=stance.strength,
                        target_justification_id=stance.target_justification_id,
                        filename=filename,
                        artifact_id=f"{claim_id}#stance{index}",
                    )
                )
    return tuple(diagnostics)


def _lint_stance(
    *,
    stance_type: StanceType | None,
    strength: str | None,
    target_justification_id: str | None,
    filename: str | None,
    artifact_id: str | None,
) -> tuple[PassDiagnostic, ...]:
    diagnostics: list[PassDiagnostic] = []
    if strength is None:
        diagnostics.append(
            _authoring_warning(
                code="authoring.stance_missing_strength",
                family=PropstoreFamily.STANCES,
                filename=filename,
                artifact_id=artifact_id,
                message=f"stance {artifact_id!r} has no strength",
            )
        )
    if stance_type == StanceType.UNDERCUTS and target_justification_id is None:
        diagnostics.append(
            _authoring_warning(
                code="authoring.undercut_missing_target_justification",
                family=PropstoreFamily.STANCES,
                filename=filename,
                artifact_id=artifact_id,
                message=(
                    f"undercut stance {artifact_id!r} has no "
                    "target_justification_id"
                ),
            )
        )
    return tuple(diagnostics)
