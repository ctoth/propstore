"""Minimal core label types for the semantic kernel.

Full ATMS environment labels (the provenance-semiring-backed antichain with
nogood pruning) arrive with the world layer in Phase 7. This module provides the
minimal :class:`Label` surface the structured-projection and analyzer-result
types need now: an antichain of supporting environments, each an immutable set of
assumption ids, with an unconditional :meth:`Label.empty` environment. It also
carries the :class:`SupportQuality` grading and the :data:`SupportMetadata`
mapping those layers attach to projected supports.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from provenance_semiring import SupportQuality

__all__ = ["Label", "SupportMetadata", "SupportQuality", "label_from_dict", "label_to_dict"]


@dataclass(frozen=True)
class Label:
    """A minimal antichain of supporting environments.

    Each environment is the immutable set of assumption ids that, taken together,
    support the labelled datum. The empty environment (:meth:`empty`) denotes
    unconditional support.
    """

    environments: tuple[frozenset[str], ...] = ()

    @classmethod
    def empty(cls) -> Label:
        """Unconditional support: a single empty environment."""

        return cls((frozenset(),))


SupportMetadata = Mapping[str, tuple["Label | None", SupportQuality]]


def label_to_dict(label: Label) -> dict[str, Any]:
    """Serialize a :class:`Label` to a deterministic JSON-ready mapping."""

    return {"environments": [sorted(environment) for environment in label.environments]}


def label_from_dict(data: Mapping[str, Any] | None) -> Label | None:
    """Rebuild a :class:`Label` from :func:`label_to_dict` output (or ``None``)."""

    if data is None:
        return None
    raw_environments = data.get("environments") or ()
    environments = tuple(
        frozenset(str(item) for item in environment) for environment in raw_environments
    )
    return Label(environments)
