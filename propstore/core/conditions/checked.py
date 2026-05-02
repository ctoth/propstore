"""Checked ConditionIR carriers for runtime-facing condition semantics."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import json
from typing import Any

from propstore.core.conditions.codec import condition_ir_from_json, condition_ir_to_json
from propstore.core.conditions.ir import ConditionIR


CHECKED_CONDITION_SET_JSON_VERSION = 1


@dataclass(frozen=True)
class CheckedCondition:
    source: str
    ir: ConditionIR
    registry_fingerprint: str
    warnings: tuple[str, ...] = ()
    encoded_ir: str | None = None

    def __post_init__(self) -> None:
        source = self.source.strip()
        if source == "":
            raise ValueError("checked condition source must be non-empty")
        fingerprint = self.registry_fingerprint.strip()
        if fingerprint == "":
            raise ValueError("condition registry fingerprint must be non-empty")
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "registry_fingerprint", fingerprint)
        object.__setattr__(self, "warnings", tuple(self.warnings))
        encoded_ir = self.encoded_ir
        if encoded_ir is None:
            encoded_ir = json.dumps(
                condition_ir_to_json(self.ir),
                sort_keys=True,
                separators=(",", ":"),
            )
        elif encoded_ir.strip() == "":
            raise ValueError("checked condition encoded IR must be non-empty")
        object.__setattr__(self, "encoded_ir", encoded_ir)


@dataclass(frozen=True)
class CheckedConditionSet:
    conditions: tuple[CheckedCondition, ...]
    registry_fingerprint: str

    def __post_init__(self) -> None:
        fingerprint = self.registry_fingerprint.strip()
        if fingerprint == "":
            raise ValueError("condition registry fingerprint must be non-empty")
        normalized = _normalize_checked_conditions(self.conditions)
        for condition in normalized:
            if condition.registry_fingerprint != fingerprint:
                raise ValueError(
                    "all checked conditions must share the condition-set registry fingerprint"
                )
        object.__setattr__(self, "conditions", normalized)
        object.__setattr__(self, "registry_fingerprint", fingerprint)

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(condition.source for condition in self.conditions)


def checked_condition_set(
    conditions: Iterable[CheckedCondition],
) -> CheckedConditionSet:
    normalized = _normalize_checked_conditions(conditions)
    if not normalized:
        return CheckedConditionSet(
            conditions=(),
            registry_fingerprint="empty",
        )
    return CheckedConditionSet(
        conditions=normalized,
        registry_fingerprint=normalized[0].registry_fingerprint,
    )


def _normalize_checked_conditions(
    conditions: Iterable[CheckedCondition],
) -> tuple[CheckedCondition, ...]:
    by_source: dict[str, CheckedCondition] = {}
    for condition in conditions:
        existing = by_source.get(condition.source)
        if existing is not None:
            if existing.registry_fingerprint != condition.registry_fingerprint:
                raise ValueError(
                    f"duplicate condition {condition.source!r} has multiple registry fingerprints"
                )
            continue
        by_source[condition.source] = condition
    return tuple(by_source[source] for source in sorted(by_source))


def checked_condition_set_to_json(
    condition_set: CheckedConditionSet,
) -> dict[str, Any]:
    return {
        "version": CHECKED_CONDITION_SET_JSON_VERSION,
        "registry_fingerprint": condition_set.registry_fingerprint,
        "conditions": [
            {
                "source": condition.source,
                "warnings": list(condition.warnings),
                "ir": condition_ir_to_json(condition.ir),
            }
            for condition in condition_set.conditions
        ],
    }


def checked_condition_set_from_json(
    payload: Mapping[str, Any],
) -> CheckedConditionSet:
    version = payload.get("version")
    if version != CHECKED_CONDITION_SET_JSON_VERSION:
        raise ValueError(f"unsupported checked condition-set encoding version: {version!r}")
    fingerprint = payload.get("registry_fingerprint")
    if not isinstance(fingerprint, str) or not fingerprint:
        raise ValueError("checked condition-set encoding requires registry_fingerprint")
    entries = payload.get("conditions")
    if not isinstance(entries, list):
        raise ValueError("checked condition-set encoding requires conditions list")

    conditions: list[CheckedCondition] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("checked condition entry must be a mapping")
        source = entry.get("source")
        if not isinstance(source, str) or not source:
            raise ValueError("checked condition entry requires source")
        warnings = entry.get("warnings", ())
        if not isinstance(warnings, list | tuple):
            raise ValueError("checked condition warnings must be a sequence")
        conditions.append(
            CheckedCondition(
                source=source,
                ir=condition_ir_from_json(_entry_mapping(entry.get("ir"))),
                registry_fingerprint=fingerprint,
                warnings=tuple(str(warning) for warning in warnings),
            )
        )
    return CheckedConditionSet(
        conditions=tuple(conditions),
        registry_fingerprint=fingerprint,
    )


def _entry_mapping(value: object) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("checked condition IR entry must be a mapping")
    return value
