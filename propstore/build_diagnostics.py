"""Lowering build diagnostics to ``BuildDiagnostic`` rows, plus authoring lints.

This is the build-side logic that sits above the :class:`BuildDiagnostic` charter
(:mod:`propstore.families.diagnostics`). It is a separate module so the charter
module stays import-light (the registry imports the charter; this module imports
the registry), avoiding a families <-> registry cycle.

Three diagnostic sources flow through here into ``BuildDiagnostic`` rows:

* a :class:`QuarantineDiagnostic` — a dangling stance / justification /
  micropublication reference found while compiling the plan;
* a :class:`~propstore.semantic_passes.types.PassDiagnostic` — a semantic-pass or
  authoring-lint diagnostic;
* a build exception — recorded just before re-raising so a failed build still
  leaves a queryable trace.

Plus :func:`collect_authoring_lints`, the advisory authoring checks the build runs
over master-resident claims and stances (``--strict-authoring`` upgrades them).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

from propstore.families.claims import Claim, ClaimType
from propstore.families.claims_passes import ClaimStage
from propstore.families.diagnostics import BuildDiagnostic
from propstore.families.registry import PropstoreFamily
from propstore.families.relations import Stance
from propstore.semantic_passes.types import PassDiagnostic
from propstore.stances import StanceType


@dataclass(frozen=True)
class QuarantineDiagnostic:
    """A dangling-reference finding produced while compiling the build plan.

    The plan compiler emits one of these for a stance / justification /
    micropublication that references a claim absent from the build's claim set.
    The referencing row itself still inserts (quarantine, not drop); this records
    why render policy should hide it.
    """

    artifact_id: str
    kind: str
    diagnostic_kind: str
    message: str
    file: str | None = None


def quarantine_to_build_diagnostic(
    diagnostic: QuarantineDiagnostic, *, diagnostic_id: str
) -> BuildDiagnostic:
    """Lower a :class:`QuarantineDiagnostic` to a blocking ``BuildDiagnostic``."""

    return BuildDiagnostic(
        diagnostic_id=diagnostic_id,
        source_kind=diagnostic.kind,
        diagnostic_kind=diagnostic.diagnostic_kind,
        severity="error",
        blocking=1,
        message=diagnostic.message,
        claim_id=diagnostic.artifact_id if diagnostic.kind == "claim" else None,
        source_ref=diagnostic.artifact_id,
        file=diagnostic.file,
    )


def pass_to_build_diagnostic(
    diagnostic: PassDiagnostic, *, diagnostic_id: str
) -> BuildDiagnostic:
    """Lower a semantic-pass / authoring :class:`PassDiagnostic` to a row.

    ``blocking`` follows the level: an error blocks (its subject is hidden at
    render); a warning is advisory.
    """

    return BuildDiagnostic(
        diagnostic_id=diagnostic_id,
        source_kind=diagnostic.family.value,
        diagnostic_kind=diagnostic.code,
        severity=diagnostic.level,
        blocking=1 if diagnostic.is_error else 0,
        message=diagnostic.render(),
        claim_id=(
            diagnostic.artifact_id
            if diagnostic.family is PropstoreFamily.CLAIM
            else None
        ),
        source_ref=diagnostic.artifact_id,
        file=diagnostic.filename,
    )


def build_exception_diagnostic(
    exc: BaseException, *, diagnostic_id: str
) -> BuildDiagnostic:
    """The ``build_exception`` row recorded when sidecar population raises."""

    return BuildDiagnostic(
        diagnostic_id=diagnostic_id,
        source_kind="sidecar_build",
        diagnostic_kind="build_exception",
        severity="error",
        blocking=1,
        message=str(exc) or exc.__class__.__name__,
    )


def collect_authoring_lints(
    *,
    claims: Iterable[Claim],
    stances: Iterable[Stance],
) -> tuple[PassDiagnostic, ...]:
    """Advisory authoring lints over master-resident claims and stances.

    Each lint is ``level="warning"``; the build appends them to its messages and
    ``--strict-authoring`` upgrades every one to ``"error"``
    (:func:`upgrade_lints_to_errors`). The reference tree's source / provenance
    lints keyed off fields absent from the flat charter (``provenance.page``, the
    stance ``strength`` / ``target_justification_id`` fields) are replaced by the
    lints the actual charter fields support.
    """

    lints: list[PassDiagnostic] = []
    for claim in claims:
        if claim.claim_type is None or claim.claim_type is ClaimType.UNKNOWN:
            lints.append(
                PassDiagnostic(
                    level="warning",
                    code="authoring.claim_unknown_type",
                    message=f"claim {claim.claim_id!r} has no recognized claim_type",
                    family=PropstoreFamily.CLAIM,
                    stage=ClaimStage.AUTHORED,
                    artifact_id=claim.claim_id,
                    pass_name="diagnostics.authoring_lints",
                )
            )
    for stance in stances:
        if stance.confidence is None:
            lints.append(
                PassDiagnostic(
                    level="warning",
                    code="authoring.stance_missing_confidence",
                    message=f"stance {stance.stance_id!r} has no confidence",
                    family=PropstoreFamily.STANCE,
                    stage=ClaimStage.AUTHORED,
                    artifact_id=stance.stance_id,
                    pass_name="diagnostics.authoring_lints",
                )
            )
        if (
            stance.stance_type is StanceType.UNDERCUTS
            and stance.target_claim_id is None
        ):
            lints.append(
                PassDiagnostic(
                    level="warning",
                    code="authoring.undercut_missing_target",
                    message=f"undercut stance {stance.stance_id!r} has no target claim",
                    family=PropstoreFamily.STANCE,
                    stage=ClaimStage.AUTHORED,
                    artifact_id=stance.stance_id,
                    pass_name="diagnostics.authoring_lints",
                )
            )
    return tuple(lints)


def upgrade_lints_to_errors(
    lints: Iterable[PassDiagnostic],
) -> tuple[PassDiagnostic, ...]:
    """Upgrade every authoring lint to ``level="error"`` (``--strict-authoring``)."""

    return tuple(replace(lint, level="error") for lint in lints)
