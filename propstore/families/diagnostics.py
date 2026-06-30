"""Build-diagnostic projection charter.

The world-sidecar build records every diagnostic it produces — a quarantined
dangling reference, a blocked claim's error, a pass failure, an authoring lint, or
a build exception — as a row in this charter-derived ``build_diagnostic`` table.
The reference tree's hand-authored ``build_diagnostics`` projection plus its
``QuarantinableWriter`` projection mass therefore vanishes: the projection *is*
this charter, written with ``session.add_family("build_diagnostic", {...})`` like
every other family (the lowering logic lives in :mod:`propstore.build_diagnostics`).

``BuildDiagnostic`` is a derived-only projection family (never authored to git): it
carries no ``semantic`` tag and declares no foreign keys, mirroring
:class:`~propstore.families.contexts.LiftingMaterialization`. A ``claim_id`` or
``source_ref`` pointing at a not-yet-present (or quarantined) artifact must record
freely, so a hard referential constraint would defeat the purpose.
"""

from __future__ import annotations

from typing import Annotated

from quire.charter_class import CharterDoc, charter, charter_field


@charter(
    key="build_diagnostic",
    name="build_diagnostic",
    contract_version="2026.06.29",
    placement="build_diagnostic",
    identity_field="diagnostic_id",
)
class BuildDiagnostic(CharterDoc):
    """One diagnostic produced while building the world sidecar.

    ``severity`` is ``"error"`` / ``"warning"``; ``blocking`` is ``1`` when the
    diagnostic marks its subject for render-time suppression (a blocked claim, a
    dangling reference, a build exception) and ``0`` for an advisory lint.
    ``source_kind`` names what the diagnostic is about (``"claim"`` /
    ``"stance"`` / ``"sidecar_build"`` / ``"authoring"`` / …); ``source_ref`` is
    the offending artifact id where one applies. References are deliberately not
    foreign keys (see the module docstring).
    """

    diagnostic_id: Annotated[str, charter_field(primary_key=True)]
    source_kind: str
    diagnostic_kind: str
    severity: str
    blocking: int
    message: str
    claim_id: str | None = None
    source_ref: str | None = None
    file: str | None = None
    detail_json: str | None = None
