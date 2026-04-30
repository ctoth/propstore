"""Shared reasoning backend and semantics selectors."""

from __future__ import annotations

from enum import StrEnum


class ReasoningBackend(StrEnum):
    """Argumentation implementation selector."""

    CLAIM_GRAPH = "claim_graph"
    ASPIC = "aspic"
    ATMS = "atms"
    PRAF = "praf"


class ArgumentationSemantics(StrEnum):
    """Canonical semantics names exposed by argumentation-capable backends."""

    GROUNDED = "grounded"
    PREFERRED = "preferred"
    STABLE = "stable"
    D_PREFERRED = "d-preferred"
    S_PREFERRED = "s-preferred"
    C_PREFERRED = "c-preferred"
    BIPOLAR_STABLE = "bipolar-stable"
    COMPLETE = "complete"
    PRAF_PAPER_TD_COMPLETE = "praf-paper-td-complete"
    ASPIC_DIRECT_GROUNDED = "aspic-direct-grounded"
    ASPIC_INCOMPLETE_GROUNDED = "aspic-incomplete-grounded"


_ARGUMENTATION_SEMANTICS_ALIASES: dict[str, ArgumentationSemantics] = {
    ArgumentationSemantics.GROUNDED.value: ArgumentationSemantics.GROUNDED,
    ArgumentationSemantics.PREFERRED.value: ArgumentationSemantics.PREFERRED,
    ArgumentationSemantics.STABLE.value: ArgumentationSemantics.STABLE,
    ArgumentationSemantics.D_PREFERRED.value: ArgumentationSemantics.D_PREFERRED,
    ArgumentationSemantics.S_PREFERRED.value: ArgumentationSemantics.S_PREFERRED,
    ArgumentationSemantics.C_PREFERRED.value: ArgumentationSemantics.C_PREFERRED,
    "bipolar_stable": ArgumentationSemantics.BIPOLAR_STABLE,
    ArgumentationSemantics.BIPOLAR_STABLE.value: ArgumentationSemantics.BIPOLAR_STABLE,
    ArgumentationSemantics.COMPLETE.value: ArgumentationSemantics.COMPLETE,
    ArgumentationSemantics.PRAF_PAPER_TD_COMPLETE.value: (
        ArgumentationSemantics.PRAF_PAPER_TD_COMPLETE
    ),
    ArgumentationSemantics.ASPIC_DIRECT_GROUNDED.value: (
        ArgumentationSemantics.ASPIC_DIRECT_GROUNDED
    ),
    ArgumentationSemantics.ASPIC_INCOMPLETE_GROUNDED.value: (
        ArgumentationSemantics.ASPIC_INCOMPLETE_GROUNDED
    ),
}

_CLI_ARGUMENTATION_SEMANTICS = (
    ArgumentationSemantics.GROUNDED,
    ArgumentationSemantics.PREFERRED,
    ArgumentationSemantics.STABLE,
    ArgumentationSemantics.D_PREFERRED,
    ArgumentationSemantics.S_PREFERRED,
    ArgumentationSemantics.C_PREFERRED,
    ArgumentationSemantics.BIPOLAR_STABLE,
    ArgumentationSemantics.COMPLETE,
    ArgumentationSemantics.PRAF_PAPER_TD_COMPLETE,
    ArgumentationSemantics.ASPIC_DIRECT_GROUNDED,
    ArgumentationSemantics.ASPIC_INCOMPLETE_GROUNDED,
)

_BACKEND_SEMANTICS: dict[ReasoningBackend, frozenset[ArgumentationSemantics]] = {
    ReasoningBackend.CLAIM_GRAPH: frozenset({
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.PREFERRED,
        ArgumentationSemantics.STABLE,
        ArgumentationSemantics.D_PREFERRED,
        ArgumentationSemantics.S_PREFERRED,
        ArgumentationSemantics.C_PREFERRED,
        ArgumentationSemantics.BIPOLAR_STABLE,
    }),
    ReasoningBackend.ASPIC: frozenset({
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.PREFERRED,
        ArgumentationSemantics.STABLE,
        ArgumentationSemantics.COMPLETE,
        ArgumentationSemantics.ASPIC_DIRECT_GROUNDED,
        ArgumentationSemantics.ASPIC_INCOMPLETE_GROUNDED,
    }),
    ReasoningBackend.ATMS: frozenset({
        ArgumentationSemantics.GROUNDED,
    }),
    ReasoningBackend.PRAF: frozenset({
        ArgumentationSemantics.GROUNDED,
        ArgumentationSemantics.PREFERRED,
        ArgumentationSemantics.STABLE,
        ArgumentationSemantics.COMPLETE,
        ArgumentationSemantics.PRAF_PAPER_TD_COMPLETE,
    }),
}


def normalize_reasoning_backend(value: ReasoningBackend | str) -> ReasoningBackend:
    if isinstance(value, ReasoningBackend):
        return value
    try:
        return ReasoningBackend(str(value))
    except ValueError as exc:
        raise ValueError(f"Unknown reasoning_backend '{value}'") from exc


def normalize_argumentation_semantics(
    value: ArgumentationSemantics | str,
) -> ArgumentationSemantics:
    if isinstance(value, ArgumentationSemantics):
        return value
    normalized = _ARGUMENTATION_SEMANTICS_ALIASES.get(str(value))
    if normalized is None:
        raise ValueError(f"Unknown semantics: {value}")
    return normalized


def cli_argumentation_semantics_values() -> tuple[str, ...]:
    return tuple(semantics.value for semantics in _CLI_ARGUMENTATION_SEMANTICS)


def supported_argumentation_semantics(
    backend: ReasoningBackend | str,
) -> frozenset[ArgumentationSemantics]:
    normalized_backend = normalize_reasoning_backend(backend)
    return _BACKEND_SEMANTICS[normalized_backend]


def validate_backend_semantics(
    backend: ReasoningBackend | str,
    semantics: ArgumentationSemantics | str,
) -> tuple[ReasoningBackend, ArgumentationSemantics]:
    normalized_backend = normalize_reasoning_backend(backend)
    normalized_semantics = normalize_argumentation_semantics(semantics)
    supported = supported_argumentation_semantics(normalized_backend)
    if normalized_semantics not in supported:
        supported_names = ", ".join(item.value for item in sorted(supported, key=str))
        raise ValueError(
            f"{normalized_backend.value} does not support semantics "
            f"'{normalized_semantics.value}'; supported semantics: {supported_names}"
        )
    return normalized_backend, normalized_semantics
