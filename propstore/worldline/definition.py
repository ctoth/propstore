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

The world-shaped compute values a worldline carries — the render policy, the
query environment, the revision query, and the materialized result — are stored
as their **existing dict serialization** (``RenderPolicy.to_dict()`` etc.) in
``policy`` / ``inputs`` / ``revision`` / ``results``. The compute forms are built
ONE-WAY from those mappings at use time by the caller (``propstore.worldline.query``
/ ``runner``) via ``RenderPolicy.from_dict(...)``, ``Environment.from_dict(...)``,
``WorldlineRevisionQuery.from_dict(...)`` — a boundary crossing that is a call,
not a conversion (CLAUDE.md substrate discipline point 3). These stored mappings
are serialization of the one canonical compute type, not parallel spellings.

The transition ``journal`` cannot be structurally decoded by msgspec — a captured
:class:`~propstore.support_revision.history.TransitionJournal` nests an untagged
``AssertionAtom | AssumptionAtom`` union — so it is stored as the journal's own
canonical dict (``TransitionJournal.to_dict()``) and parsed back through the
package-owned :meth:`TransitionJournal.from_mapping` via
:meth:`WorldlineDefinition.transition_journal`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, TypeGuard

import msgspec
from quire.artifacts import BranchPlacement, FlatYamlPlacement
from quire.charter_class import CharterDoc, charter, charter_field
from quire.refs import single_field_ref_type

from propstore.support_revision.history import TransitionJournal


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _optional_mapping(value: object, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not _is_mapping(value):
        raise ValueError(f"worldline field '{field_name}' must be a mapping")
    return value


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

    The class IS the ``worldlines`` family document (single canonical type). The
    world-shaped values (``inputs`` / ``policy`` / ``revision`` / ``results``) ride
    as their dict serialization so this module stays storage-pure; the compute
    forms are reconstructed one-way at use time by ``propstore.worldline.query`` /
    ``runner`` (``RenderPolicy.from_dict`` etc.). There is no
    ``WorldlineDefinitionDocument`` mirror and no ``to_document``/``from_document``
    coercer.

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
    inputs: Annotated[dict[str, Any], charter_field(json=True)] = msgspec.field(
        default_factory=dict[str, Any]
    )
    policy: Annotated[dict[str, Any], charter_field(json=True)] = msgspec.field(
        default_factory=dict[str, Any]
    )
    revision: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    results: Annotated[dict[str, Any] | None, charter_field(json=True)] = None
    journal: Annotated[dict[str, Any] | None, charter_field(json=True)] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WorldlineDefinition:
        if "id" not in data:
            raise ValueError("Worldline definition requires 'id'")
        targets = data.get("targets")
        if not targets:
            raise ValueError("Worldline definition requires 'targets'")

        raw_revision = data.get("revision")
        revision = None
        if raw_revision is not None:
            revision_map = _optional_mapping(raw_revision, "revision")
            # Validate the revision target eagerly at parse time (raises on an
            # unprefixed contract target); the stored form is the raw mapping.
            validated_revision_target(
                str(revision_map.get("operation", "")),
                revision_map.get("target"),
            )
            revision = dict(revision_map)

        raw_results = data.get("results")
        raw_journal = data.get("journal")
        return cls(
            id=data["id"],
            name=data.get("name", ""),
            created=data.get("created", ""),
            inputs=dict(_optional_mapping(data.get("inputs"), "inputs")),
            policy=dict(_optional_mapping(data.get("policy"), "policy")),
            targets=list(targets),
            revision=revision,
            results=(
                None
                if raw_results is None
                else dict(_optional_mapping(raw_results, "results"))
            ),
            journal=(
                None
                if raw_journal is None
                else dict(_optional_mapping(raw_journal, "journal"))
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"id": self.id}
        if self.name:
            data["name"] = self.name
        if self.created:
            data["created"] = self.created
        if self.inputs:
            data["inputs"] = dict(self.inputs)
        if self.policy:
            data["policy"] = dict(self.policy)
        data["targets"] = list(self.targets)
        if self.revision is not None:
            data["revision"] = dict(self.revision)
        if self.results is not None:
            data["results"] = dict(self.results)
        if self.journal is not None:
            data["journal"] = dict(self.journal)
        return data

    def transition_journal(self) -> TransitionJournal | None:
        """Reconstruct the captured journal as its canonical package type.

        The persisted ``journal`` field holds the journal's own serialized dict
        (:meth:`TransitionJournal.to_dict`); this is the package-owned parse back
        to the single canonical :class:`TransitionJournal` — never a mirror type.
        """

        if self.journal is None:
            return None
        return TransitionJournal.from_mapping(self.journal)
