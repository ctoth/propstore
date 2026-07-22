"""Derived grounding-build configuration charter.

The world sidecar records the repository-selected grounding argument limit so a
reader opened from only a derived-store handle can deterministically reconstruct
the same :class:`~propstore.grounding.bundle.GroundedRulesBundle`. This family is
derived-only: it carries no semantic tag, no foreign keys, and no grounding
result. Status, sections, arguments, and inspection remain owned by the runtime
bundle.
"""

from __future__ import annotations

from typing import Annotated

from quire.charter_class import CharterDoc, charter, charter_field


@charter(
    key="grounding_build_configuration",
    name="grounding_build_configuration",
    contract_version="2026.07.22",
    placement="grounding_build_configuration",
    identity_field="configuration_id",
)
class GroundingBuildConfiguration(CharterDoc):
    """The grounding configuration selected for one materialized sidecar."""

    configuration_id: Annotated[str, charter_field(primary_key=True)]
    max_arguments: int | None = None
