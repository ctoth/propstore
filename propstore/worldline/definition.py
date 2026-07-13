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

The nested input graph, the render policy, the revision query, and the
materialized results are all declared as typed documents. Quire's charter codec
owns recursive decoding, encoding, and strict field validation; this module owns
only the worldline's semantic declarations and invariants. The payload types
those fields hold (:class:`~propstore.core.render_policy.RenderPolicy`, the ATMS
reports, the worldline result views) live under ``propstore.core`` precisely so
that this storage-pure charter can name them: ``propstore.families.registry``
imports this module, and ``storage``/``source``/``heuristic`` all reach the
registry, so an import of ``propstore.world`` here would break the layering
contract in ``.importlinter``.

The transition ``journal`` is typed too. It was long carried as a ``dict`` on the
claim that a :class:`~propstore.support_revision.history.TransitionJournal`
"nests an untagged atom union msgspec cannot decode" — that has not been true
since the v2/v3 wire formats typed the nested state: ``TransitionJournal`` is a
``msgspec.Struct`` with ``forbid_unknown_fields``, msgspec builds a decoder for
it, and Quire stores it directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

import msgspec
from quire.artifacts import BranchPlacement, FlatYamlPlacement
from quire.charter_class import CharterDoc, charter, charter_field
from quire.documents import DocumentStruct
from quire.refs import single_field_ref_type

from propstore.core.environment import Environment
from propstore.core.render_policy import RenderPolicy
from propstore.support_revision.history import TransitionJournal
from propstore.worldline.query import WorldlineResult, WorldlineRevisionQuery


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
    contract_version="2026.07.13",
    placement=WORLDLINE_PLACEMENT,
    identity_field="name",
)
class WorldlineDefinition(CharterDoc):
    """A worldline: question + optional materialized answer — the charter document.

    The class IS the ``worldlines`` family document (single canonical type).
    There is no ``WorldlineDefinitionDocument`` mirror and no local mapping
    codec around Quire's charter codec.

    ``policy``, ``revision``, ``results``, and ``journal`` are typed documents:
    Quire decodes them into the canonical types directly. No field on this
    charter is a ``dict[str, Any]`` blob behind a hand-written codec.
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
    policy: Annotated[RenderPolicy, charter_field(json=True)] = msgspec.field(
        default_factory=RenderPolicy
    )
    revision: Annotated[WorldlineRevisionQuery | None, charter_field(json=True)] = None
    results: Annotated[WorldlineResult | None, charter_field(json=True)] = None
    journal: Annotated[TransitionJournal | None, charter_field(json=True)] = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Worldline definition requires 'id'")
        if not self.targets:
            raise ValueError("Worldline definition requires 'targets'")
