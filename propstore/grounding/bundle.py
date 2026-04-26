"""Immutable bundle wrapping the grounder pipeline output.

Chunk 1.5b (green) of the Phase-1 grounder workstream. The
``GroundedRulesBundle`` is the single frozen handoff object from
``propstore.grounding.grounder.ground`` to downstream consumers (the
T2.5 bridge, the render layer, sidecar persistence). It stores the
four gunray sections verbatim together with the ``rule_files`` and
``facts`` that produced them, so the full provenance chain stays
intact.

Theoretical anchors:

    Diller, M., Borg, A., & Bex, F. (2025). Grounding Rule-Based
    Argumentation Using Datalog.
    - Section 3 (Definition 7, p.3): a Datalog program's fact base is a
      finite set of ground atoms keyed by predicate id; the grounded
      model is a pair ``(program, fact_base) -> model``. Storing the
      model alone would lose the provenance link to the inputs, so the
      bundle carries all three parts.
    - Section 4: the ground model is a pure function of the program;
      it is therefore safe (and required) to make the wrapping bundle
      immutable.

    Garcia, A. J. & Simari, G. R. (2004). Defeasible Logic
    Programming: An Argumentative Approach.
    - Section 4 (p.25): a defeasible program has a four-valued answer
      system ``{YES, NO, UNDECIDED, UNKNOWN}``. Gunray maps that system
      onto four section names
      (``definitely`` / ``defeasibly`` / ``not_defeasibly`` /
      ``undecided``). The non-commitment anchor for the propstore
      pipeline is that **every bundle exposes all four sections**,
      even when some are empty. Render-time policy filters what to
      surface; storage never drops a section. This is the formal
      non-commitment discipline at the semantic core — the repository
      holds the full answer record without privileging one verdict.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

from argumentation.aspic import GroundAtom, Scalar
from propstore.rule_files import LoadedRuleFile

if TYPE_CHECKING:
    from gunray import Argument, GroundingInspection


def _build_empty_sections() -> Mapping[str, Mapping[str, frozenset[tuple[Scalar, ...]]]]:
    """Return a read-only four-valued section map with every bucket empty.

    Garcia & Simari 2004 §4 (p.25): the four-valued answer system
    ``{YES, NO, UNDECIDED, UNKNOWN}`` has four always-present section
    names. The non-commitment discipline (project CLAUDE.md) requires
    that every bundle expose all four, even when vacuous. The zero
    element of the bundle monoid is therefore a bundle with all four
    sections present-and-empty, not a bundle with sections omitted.
    """

    return MappingProxyType(
        {
            "definitely": MappingProxyType({}),
            "defeasibly": MappingProxyType({}),
            "not_defeasibly": MappingProxyType({}),
            "undecided": MappingProxyType({}),
        }
    )


@dataclass(frozen=True)
class GroundedRulesBundle:
    """Immutable record of one grounding-pipeline invocation.

    Attributes:
        source_rules: The ``LoadedRuleFile`` envelopes that were fed to
            the grounder, stored verbatim as a tuple. Diller, Borg, Bex
            2025 §3 keeps the rule base as part of the program
            identity; the bundle therefore carries it alongside the
            derived model so downstream consumers can reach back to the
            authored input.
        source_facts: The ground-atom fact base that was fed to the
            grounder, stored verbatim. Diller, Borg, Bex 2025 §3
            Definition 7: a Datalog fact base is a finite set of ground
            atoms; the grounder never invents facts, so the input tuple
            is faithfully retained.
        sections: The four gunray sections as an immutable
            mapping-of-mappings. Outer key: one of
            ``{"definitely", "defeasibly", "not_defeasibly",
            "undecided"}``. Inner key: predicate id. Inner value:
            ``frozenset`` of argument tuples. Garcia & Simari 2004 §4
            (p.25) four-valued answer system: all four sections are
            always present, even when empty — the grounder re-normalises
            gunray's output (which drops empty sections) so the
            non-commitment discipline is preserved.
        arguments: Ordered tuple of ``gunray.Argument`` objects as
            produced by ``gunray.build_arguments`` (Garcia & Simari
            2004 §3 Def 3.6 — an argument is a minimal, consistent
            defeasible derivation). Populated only when the grounder
            is called with ``return_arguments=True``; defaults to the
            empty tuple so every call site that constructs a bundle
            with only the three legacy fields still type-checks and
            runs. Diller, Borg, Bex 2025 §4 uses argument objects as
            the atomic unit of the dialectical-tree procedure; Block
            3 of the gunray refactor exposes this typed view
            alongside the legacy section projection.
    """

    source_rules: tuple[LoadedRuleFile, ...]
    source_facts: tuple[GroundAtom, ...]
    sections: Mapping[str, Mapping[str, frozenset[tuple[Scalar, ...]]]]
    arguments: tuple["Argument", ...] = field(default_factory=tuple)
    grounding_inspection: "GroundingInspection | None" = None

    @classmethod
    def empty(cls) -> "GroundedRulesBundle":
        """Return the zero-value bundle: no rules, no facts, all four sections empty.

        Used at call sites that do not exercise grounding (legacy
        claim-graph flows, wrapper delegations, tests that don't care
        about ground rules). This is **not** a compat shim — it is the
        identity element for rule-less argumentation and exists so
        every caller can continue to pass a concrete, typed bundle
        rather than an ``Optional``.

        The non-commitment discipline (project CLAUDE.md, Garcia &
        Simari 2004 §4 p.25) requires all four gunray sections to be
        present even when empty; the returned bundle satisfies that
        invariant. Diller, Borg, Bex 2025 §3 Def 7 (p.3): the empty
        fact base is a legal Datalog program — its bundle is well
        defined.
        """

        return cls(
            source_rules=(),
            source_facts=(),
            sections=_build_empty_sections(),
        )
