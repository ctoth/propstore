"""Lazy semantic pipeline registration."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from propstore.families.registry import PropstoreFamily
from propstore.semantic_passes.types import FamilyPipeline, StageId


class PipelineRegistryError(ValueError):
    """Raised when pass declarations do not form a valid pipeline."""


class PipelineRegistry:
    def __init__(self) -> None:
        self._passes: dict[
            PropstoreFamily,
            list[type[Any]],
        ] = defaultdict(list)
        self._names: dict[PropstoreFamily, set[str]] = defaultdict(set)

    def register(
        self,
        pass_class: type[Any],
        *,
        family: PropstoreFamily | None = None,
    ) -> None:
        declared_family = pass_class.family
        if family is not None and declared_family is not family:
            raise PipelineRegistryError(
                f"pass {pass_class.name!r} declares family "
                f"{declared_family.value!r}, not {family.value!r}"
            )
        if pass_class.name in self._names[declared_family]:
            raise PipelineRegistryError(
                f"duplicate pass name {pass_class.name!r} "
                f"for family {declared_family.value!r}"
            )
        self._passes[declared_family].append(pass_class)
        self._names[declared_family].add(pass_class.name)

    def registered_passes(self) -> tuple[type[Any], ...]:
        return tuple(
            pass_class
            for family in sorted(self._passes, key=lambda item: item.value)
            for pass_class in self._passes[family]
        )

    def pipeline(
        self,
        *,
        family: PropstoreFamily,
        start_stage: StageId,
        target_stage: StageId,
    ) -> FamilyPipeline:
        if start_stage == target_stage:
            return FamilyPipeline(
                family=family,
                start_stage=start_stage,
                target_stage=target_stage,
                passes=(),
            )

        registered = tuple(self._passes.get(family, ()))
        if not registered:
            raise PipelineRegistryError(
                f"no semantic passes registered for family {family.value!r}"
            )

        current_stage = start_stage
        selected: list[type[Any]] = []
        for pass_class in registered:
            if pass_class.input_stage != current_stage:
                raise PipelineRegistryError(
                    f"pass {pass_class.name!r} expects "
                    f"{pass_class.input_stage.value!r} after "
                    f"{current_stage.value!r}"
                )
            selected.append(pass_class)
            current_stage = pass_class.output_stage
            if current_stage == target_stage:
                return FamilyPipeline(
                    family=family,
                    start_stage=start_stage,
                    target_stage=target_stage,
                    passes=tuple(selected),
                )

        raise PipelineRegistryError(
            f"pipeline for family {family.value!r} cannot reach "
            f"target stage {target_stage.value!r} from {start_stage.value!r}"
        )
