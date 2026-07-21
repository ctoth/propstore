"""The non-committal grounded-rules result bundle.

A :class:`GroundedRulesBundle` is the immutable result of grounding: the source
rules/facts/superiority that went in, the four marking sections that came out
(``yes`` / ``no`` / ``undecided`` / ``unknown`` — ALWAYS all four present, even
when empty), the enumerated arguments, the grounding inspection, and a
budget-status pair. Non-commitment: nothing is dropped at build time; which
sections/arguments are *visible* is a render-time decision.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

import gunray

from propstore.families.rules import DefeasibleRule, RuleSuperiority

SECTION_NAMES: tuple[str, str, str, str] = ("yes", "no", "undecided", "unknown")

SectionRows = frozenset[tuple[gunray.Scalar, ...]]
SectionMap = Mapping[str, Mapping[str, SectionRows]]


def build_empty_sections() -> SectionMap:
    """An immutable section map with all four keys present and empty."""

    empty_inner: dict[str, SectionRows] = {}
    return MappingProxyType(
        {name: MappingProxyType(dict(empty_inner)) for name in SECTION_NAMES}
    )


@dataclass(frozen=True)
class GroundedRulesBundle:
    """The immutable, non-committal result of grounding a rule/fact program.

    ``sections`` is a read-only mapping (``MappingProxyType`` outer and inner,
    ``frozenset`` rows) so the result cannot be mutated in place. ``status`` is
    ``"complete"`` normally and ``"budget_exceeded"`` when argument enumeration
    overflowed; ``budget_reason`` carries the overflow reason in that case.
    """

    source_rules: tuple[DefeasibleRule, ...]
    source_facts: tuple[gunray.GroundAtom, ...]
    sections: SectionMap
    source_superiority: tuple[RuleSuperiority, ...] = ()
    arguments: tuple[gunray.Argument, ...] = ()
    grounding_inspection: gunray.GroundingInspection | None = None
    status: str = "complete"
    budget_reason: str | None = None

    @classmethod
    def empty(cls) -> GroundedRulesBundle:
        """An empty bundle whose sections still carry all four (empty) keys."""

        return cls(source_rules=(), source_facts=(), sections=build_empty_sections())
