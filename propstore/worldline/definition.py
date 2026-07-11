"""The worldline charter — the persisted ``worldlines`` family document.

The worldline is a **single canonical charter type** (CLAUDE.md substrate
discipline): :class:`WorldlineDefinition` IS the persisted ``worldlines`` family
document. There is deliberately no ``WorldlineDefinitionDocument`` second
spelling and no ``to_document``/``from_document`` mirror coercer — the git
document, the sidecar columns, and the serialized contract all fall out of the
charter field annotations, exactly as for the other charter families.

This module is **storage-pure**: it imports nothing from ``propstore.world``,
``propstore.worldline.runner``, or the argumentation layer. The charter-derived
registry (``propstore.families.registry``) is imported by ``propstore.storage``,
so any upward import here would drag storage into the world/argumentation layers
and break the substrate import contracts.

The nested input graph is declared as typed Quire documents. Quire's charter
codec owns recursive decoding, encoding, and strict field validation; this
module owns only the worldline's semantic declarations and invariants.

The transition ``journal`` cannot be structurally decoded by msgspec — a captured
:class:`~propstore.support_revision.history.TransitionJournal` nests an untagged
``AssertionAtom | AssumptionAtom`` union — so it is stored as the journal's own
canonical dict (``TransitionJournal.to_dict()``) and parsed back through the
package-owned :meth:`TransitionJournal.from_mapping` via
:meth:`WorldlineDefinition.transition_journal`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any

import msgspec
from quire.artifacts import BranchPlacement, FlatYamlPlacement
from quire.charter_class import CharterDoc, charter, charter_field
from quire.documents import DocumentStruct
from quire.refs import single_field_ref_type

from propstore.core.environment import Environment
from propstore.support_revision.history import TransitionJournal

class WorldlineRevisionTargetValidationError(ValueError):
    """Raised when a revision target cannot be resolved as an atom id."""


def validated_revision_target(operation: str, target: object) -> str | None:
    if target is None:
        return None
    target_id = str(target)
    if operation == "contract" and not (
        target_id.startswith("ps:assertion:")
        or target_id.startswith("assumption:")
    ):
        raise WorldlineRevisionTargetValidationError(
            "Worldline revision target must be an assertion or assumption atom id: "
            f"{target_id}"
        )
    return target_id


class WorldlineInputs(DocumentStruct):
    """Strict nested input document for a worldline query."""

    environment: Environment = msgspec.field(default_factory=Environment)
    overrides: dict[str, float | str] = msgspec.field(
        default_factory=dict[str, float | str]
    )


WORLDLINE_BRANCH = BranchPlacement(policy="current")
"""Worldlines are mutable **current-branch** artifacts — not master-canonical.

Unlike the semantic charter families (which land on the primary branch), a
worldline is authored/refreshed state that lives on whatever branch the caller
is working on. ``BranchPlacement(policy="current")`` resolves to the owner's
current branch (``GitStore.current_branch_name``), the same resolution every
charter's default placement already uses; making it explicit records the intent.
"""


if TYPE_CHECKING:

    @dataclass(frozen=True)
    class WorldlineRef:
        name: str

else:
    WorldlineRef = single_field_ref_type("WorldlineRef", "name", module=__name__)


WORLDLINE_PLACEMENT: FlatYamlPlacement[object, WorldlineRef] = FlatYamlPlacement(
    "worldlines",
    WorldlineRef,
    ref_field="name",
    branch=WORLDLINE_BRANCH,
)
"""Store each worldline at ``worldlines/<name>.yaml`` on the current branch."""


@charter(
    key="worldlines",
    name="worldlines",
    contract_version="2026.06.29",
    placement=WORLDLINE_PLACEMENT,
    identity_field="name",
)
class WorldlineDefinition(CharterDoc):
    """A worldline: question + optional materialized answer — the charter document.

    The class IS the ``worldlines`` family document (single canonical type).
    There is no ``WorldlineDefinitionDocument`` mirror and no local mapping
    codec around Quire's charter codec.

    ``journal`` cannot ride as its runtime type: a
    :class:`~propstore.support_revision.history.TransitionJournal` nests an
    untagged atom union msgspec cannot decode, so it is persisted as the journal's
    own canonical dict (:meth:`TransitionJournal.to_dict`) and reconstructed on
    demand by :meth:`transition_journal` via the package-owned
    :meth:`TransitionJournal.from_mapping`.
    """

    name: Annotated[str, charter_field(primary_key=True)] = ""
    id: str = ""
    created: str = ""
    targets: Annotated[list[str], charter_field(json=True)] = msgspec.field(
        default_factory=list[str]
    )
    inputs: Annotated[WorldlineInputs, charter_field(json=True)] = msgspec.field(
        default_factory=WorldlineInputs
    )
    policy: Annotated[dict[str, Any], charter_field(json=True)] = msgspec.field(
        default_factory=dict[str, Any]
    )
    revision: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    results: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    journal: Annotated[dict[str, Any] | None, charter_field(json=True)] = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Worldline definition requires 'id'")
        if not self.targets:
            raise ValueError("Worldline definition requires 'targets'")
        if self.revision is not None:
            validated_revision_target(
                str(self.revision.get("operation", "")),
                self.revision.get("target"),
            )

    def transition_journal(self) -> TransitionJournal | None:
        """Reconstruct the captured journal as its canonical package type.

        The persisted ``journal`` field holds the journal's own serialized dict
        (:meth:`TransitionJournal.to_dict`); this is the package-owned parse back
        to the single canonical :class:`TransitionJournal` — never a mirror type.
        """

        if self.journal is None:
            return None
        return TransitionJournal.from_mapping(self.journal)
