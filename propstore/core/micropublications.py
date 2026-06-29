"""Runtime micropublication objects for ATMS bundle reasoning.

A micropublication (Clark et al. 2014) bundles a set of claims with the context,
assumptions, stance, and source that publish them together. At world-build time
each bundle materializes as an ATMS node with a context-labelled environment
(CLAUDE.md, layer 2). This module owns the ONE runtime micropublication value;
there is no source/finalize charter for it in the rewrite yet, so the carrier
lives in ``core``. :meth:`ActiveMicropublication.from_mapping` and
:func:`coerce_active_micropublication` are validating deserialization narrowings,
not cross-package coercers.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, TypeGuard

from propstore.core.id_types import ContextId, to_context_id


def _is_mapping(value: object) -> TypeGuard[Mapping[str, Any]]:
    return isinstance(value, Mapping)


def _is_str_collection(value: object) -> TypeGuard[list[Any] | tuple[Any, ...] | set[Any]]:
    return isinstance(value, (list, tuple, set))


def _parse_string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    loaded = value
    if isinstance(value, str):
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return (value,)
    if _is_str_collection(loaded):
        return tuple(str(item) for item in loaded)
    return (str(loaded),)


@dataclass(frozen=True)
class ActiveMicropublication:
    """A claim bundle published under one context, with its assumptions."""

    artifact_id: str
    context_id: ContextId
    claim_ids: tuple[str, ...]
    assumptions: tuple[str, ...] = ()
    stance: str | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if not self.artifact_id:
            raise ValueError("micropublication artifact_id is required")
        if not self.claim_ids:
            raise ValueError("micropublication claim_ids must not be empty")
        object.__setattr__(self, "context_id", to_context_id(self.context_id))
        object.__setattr__(
            self, "claim_ids", tuple(str(claim_id) for claim_id in self.claim_ids)
        )
        object.__setattr__(
            self, "assumptions", tuple(str(item) for item in self.assumptions)
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ActiveMicropublication:
        raw_context = data.get("context_id")
        if raw_context is None:
            raw_context = data.get("context")
        if _is_mapping(raw_context):
            raw_context = raw_context.get("id")
        if raw_context is None:
            raise ValueError("micropublication context_id is required")
        return cls(
            artifact_id=str(data["artifact_id"]),
            context_id=to_context_id(raw_context),
            claim_ids=_parse_string_tuple(data.get("claim_ids") or data.get("claims")),
            assumptions=_parse_string_tuple(data.get("assumptions")),
            stance=None if data.get("stance") is None else str(data.get("stance")),
            source=None if data.get("source") is None else str(data.get("source")),
        )


ActiveMicropublicationInput = ActiveMicropublication | Mapping[str, Any]


def coerce_active_micropublication(
    micropublication: ActiveMicropublicationInput,
) -> ActiveMicropublication:
    """Narrow a micropublication input (object or mapping) to the value type."""

    if isinstance(micropublication, ActiveMicropublication):
        return micropublication
    return ActiveMicropublication.from_mapping(micropublication)
