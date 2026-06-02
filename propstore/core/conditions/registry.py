"""Typed condition registry projection and synthetic binding helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import Enum
from types import MappingProxyType

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


@dataclass(frozen=True)
class ConditionRegistry(Mapping[str, ConceptInfo]):
    """Condition type environment keyed by CEL-visible concept name."""

    concepts_by_name: Mapping[str, ConceptInfo] = field(default_factory=dict)

    def __post_init__(self) -> None:
        frozen = {
            str(name): replace(info, category_values=list(info.category_values))
            for name, info in self.concepts_by_name.items()
        }
        object.__setattr__(self, "concepts_by_name", MappingProxyType(frozen))

    @classmethod
    def from_mapping(
        cls,
        concepts_by_name: Mapping[str, ConceptInfo],
    ) -> "ConditionRegistry":
        return cls(concepts_by_name)

    def __getitem__(self, key: str) -> ConceptInfo:
        return self.concepts_by_name[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.concepts_by_name)

    def __len__(self) -> int:
        return len(self.concepts_by_name)

    def resolve(self, name: str) -> ConceptInfo | None:
        return self.concepts_by_name.get(name)

    def scope(
        self,
        concept_ids: set[str] | frozenset[str] | list[str] | tuple[str, ...],
    ) -> "ConditionRegistry":
        scoped_ids = {str(concept_id) for concept_id in concept_ids}
        return ConditionRegistry(
            {
                canonical_name: info
                for canonical_name, info in self.concepts_by_name.items()
                if info.id in scoped_ids
            }
        )

    def with_synthetic_concepts(
        self,
        concepts: Iterable[ConceptInfo],
    ) -> "ConditionRegistry":
        result = dict(self.concepts_by_name)
        for info in concepts:
            result[info.canonical_name] = info
        return ConditionRegistry(result)

    def with_standard_synthetic_bindings(self) -> "ConditionRegistry":
        synthetic_concepts = [
            synthetic_category_concept(
                concept_id=f"ps:concept:__{canonical_name}__",
                canonical_name=canonical_name,
                values=(),
                extensible=True,
            )
            for canonical_name in _STANDARD_SYNTHETIC_BINDING_NAMES
            if canonical_name not in self.concepts_by_name
        ]
        if not synthetic_concepts:
            return self
        return self.with_synthetic_concepts(synthetic_concepts)

    @property
    def fingerprint(self) -> CelRegistryFingerprint:
        registry_semantics = [
            {
                "canonical_name": canonical_name,
                "id": info.id,
                "kind": info.kind.value,
                "category_values": sorted(info.category_values),
                "category_extensible": info.category_extensible,
            }
            for canonical_name, info in sorted(self.concepts_by_name.items())
        ]
        encoded = json.dumps(
            registry_semantics,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return CelRegistryFingerprint(f"sha256:{digest}")


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
