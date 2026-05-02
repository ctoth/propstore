"""Typed condition registry projection and synthetic binding helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum

from propstore.cel_bindings import (
    STANDARD_SYNTHETIC_BINDING_NAMES as _STANDARD_SYNTHETIC_BINDING_NAMES,
)
from propstore.cel_types import CelRegistryFingerprint


class KindType(Enum):
    QUANTITY = "quantity"
    CATEGORY = "category"
    BOOLEAN = "boolean"
    STRUCTURAL = "structural"
    TIMEPOINT = "timepoint"


@dataclass
class ConceptInfo:
    """Minimal concept info needed for condition type-checking."""

    id: str
    canonical_name: str
    kind: KindType
    category_values: list[str] = field(default_factory=list)
    category_extensible: bool = True


def scope_condition_registry(
    registry: Mapping[str, ConceptInfo],
    concept_ids: set[str] | frozenset[str] | list[str] | tuple[str, ...],
) -> dict[str, ConceptInfo]:
    """Return the canonical-name keyed subset for the requested concept ids."""
    scoped_ids = {str(concept_id) for concept_id in concept_ids}
    return {
        canonical_name: info
        for canonical_name, info in registry.items()
        if info.id in scoped_ids
    }


def with_synthetic_concepts(
    registry: Mapping[str, ConceptInfo],
    concepts: Iterable[ConceptInfo],
) -> dict[str, ConceptInfo]:
    """Return a copy of *registry* augmented with synthetic condition concepts."""
    result = dict(registry)
    for info in concepts:
        result[info.canonical_name] = info
    return result


def synthetic_category_concept(
    *,
    concept_id: str,
    canonical_name: str,
    values: Sequence[str],
    extensible: bool,
) -> ConceptInfo:
    """Build a synthetic category concept for runtime condition state."""
    return ConceptInfo(
        id=concept_id,
        canonical_name=canonical_name,
        kind=KindType.CATEGORY,
        category_values=[value for value in values if isinstance(value, str)],
        category_extensible=extensible,
    )


def with_standard_synthetic_bindings(
    registry: Mapping[str, ConceptInfo],
) -> dict[str, ConceptInfo]:
    """Augment a registry with standard non-concept condition bindings."""
    synthetic_concepts = [
        synthetic_category_concept(
            concept_id=f"ps:concept:__{canonical_name}__",
            canonical_name=canonical_name,
            values=(),
            extensible=True,
        )
        for canonical_name in _STANDARD_SYNTHETIC_BINDING_NAMES
        if canonical_name not in registry
    ]
    if not synthetic_concepts:
        return dict(registry)
    return with_synthetic_concepts(registry, synthetic_concepts)


def condition_registry_fingerprint(
    registry: Mapping[str, ConceptInfo],
) -> CelRegistryFingerprint:
    """Return a deterministic fingerprint of condition-relevant registry semantics."""
    payload = [
        {
            "canonical_name": canonical_name,
            "id": info.id,
            "kind": info.kind.value,
            "category_values": sorted(info.category_values),
            "category_extensible": info.category_extensible,
        }
        for canonical_name, info in sorted(registry.items())
    ]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return CelRegistryFingerprint(f"sha256:{digest}")
