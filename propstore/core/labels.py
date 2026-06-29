"""Core label types for the semantic kernel.

The ATMS label / environment / nogood antichain algebra is owned by the
``provenance-semiring`` package (it is a thin polynomial-native layer over the
provenance semiring). propstore imports those canonical types directly —
:class:`Label`, :class:`EnvironmentKey`, :class:`NogoodSet`,
:func:`combine_labels`, :func:`merge_labels`, :func:`normalize_environments`,
and :class:`JustificationRecord` — rather than carrying a second spelling.

This module re-exports them as the propstore-local door, adds the
:class:`SupportQuality` grading and :data:`SupportMetadata` mapping the
structured-projection and analyzer-result layers attach to projected supports,
and owns the deterministic JSON (de)serialization of a :class:`Label`. The
propstore-specific *meaning* of a label's variables (an assumption id versus a
context id, and the ``ps:source:*`` encoding) lives with the world-layer
engine, not here.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from provenance_semiring import (
    EnvironmentKey,
    JustificationRecord,
    Label,
    NogoodSet,
    SourceVariableId,
    SupportQuality,
    combine_labels,
    merge_labels,
    normalize_environments,
)

__all__ = [
    "EnvironmentKey",
    "JustificationRecord",
    "Label",
    "NogoodSet",
    "SupportMetadata",
    "SupportQuality",
    "combine_labels",
    "label_from_dict",
    "label_to_dict",
    "merge_labels",
    "normalize_environments",
]


SupportMetadata = Mapping[str, tuple["Label | None", SupportQuality]]


def label_to_dict(label: Label) -> dict[str, Any]:
    """Serialize a :class:`Label` to a deterministic JSON-ready mapping."""

    return {
        "environments": [sorted(environment.variables) for environment in label.environments]
    }


def label_from_dict(data: Mapping[str, Any] | None) -> Label | None:
    """Rebuild a :class:`Label` from :func:`label_to_dict` output (or ``None``)."""

    if data is None:
        return None
    raw_environments = data.get("environments") or ()
    environments = tuple(
        EnvironmentKey(tuple(SourceVariableId(str(item)) for item in environment))
        for environment in raw_environments
    )
    return Label(environments)
