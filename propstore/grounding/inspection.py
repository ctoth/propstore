"""Typed inspection reports for the grounded rule surface.

The CLI renders these reports, but the grounding package owns the surface
classification, bundle loading, atom parsing, query membership checks, and
argument/rule projection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from argumentation.aspic import GroundAtom, Scalar
from propstore.grounding.loading import build_grounded_bundle

if TYPE_CHECKING:
    from gunray import Argument
    from gunray.types import GroundDefeasibleRule

    from propstore.grounding.bundle import GroundedRulesBundle
    from propstore.repository import Repository


SECTION_ORDER = (
    "definitely",
    "defeasibly",
    "not_defeasibly",
    "undecided",
)


class GroundingInspectionError(Exception):
    """Raised when the grounding surface cannot be inspected."""


@dataclass(frozen=True)
class GroundingSurface:
    predicate_files: tuple[str, ...]
    rule_files: tuple[str, ...]

    @property
    def has_authoring(self) -> bool:
        return bool(self.predicate_files or self.rule_files)

    @property
    def missing_predicates(self) -> bool:
        return bool(self.rule_files) and not bool(self.predicate_files)


@dataclass(frozen=True)
class GroundingStatusReport:
    surface: GroundingSurface
    surface_state: str
    message: str | None
    facts_count: int
    section_counts: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class GroundRuleLine:
    rule_id: str
    text: str


@dataclass(frozen=True)
class GroundingShowReport:
    facts: tuple[str, ...]
    rules: tuple[GroundRuleLine, ...]
    sections: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class GroundingQueryReport:
    atom: GroundAtom
    matched_sections: tuple[str, ...]


@dataclass(frozen=True)
class GroundingArgumentsReport:
    arguments: tuple[str, ...]


def inspect_grounding_surface(repo: "Repository") -> GroundingSurface:
    return GroundingSurface(
        predicate_files=tuple(
            sorted(
                f"{ref.name}.yaml"
                for ref in repo.families.predicates.iter()
            )
        ),
        rule_files=tuple(
            sorted(
                f"{ref.name}.yaml"
                for ref in repo.families.rules.iter()
            )
        ),
    )


def require_grounding_bundle(
    repo: "Repository",
    *,
    return_arguments: bool,
) -> "GroundedRulesBundle":
    surface = inspect_grounding_surface(repo)
    if not surface.has_authoring:
        raise GroundingInspectionError(
            "No grounding authoring found: predicates/ and rules/ contain no YAML files."
        )
    if surface.missing_predicates:
        raise GroundingInspectionError(
            "Invalid grounding surface: rules/ has YAML files but predicates/ has none."
        )
    try:
        return build_grounded_bundle(
            repo,
            return_arguments=return_arguments,
        )
    except ValueError as exc:
        raise GroundingInspectionError(f"Grounding unavailable: {exc}") from exc


def format_ground_atom(predicate: str, arguments: tuple[Scalar, ...]) -> str:
    return repr(GroundAtom(predicate=predicate, arguments=arguments))


def _sort_row(row: tuple[Scalar, ...]) -> tuple[str, ...]:
    return tuple(repr(value) for value in row)


def _section_atom_count(bundle: "GroundedRulesBundle", name: str) -> int:
    return sum(len(rows) for rows in bundle.sections[name].values())


def _grounded_rules(bundle: "GroundedRulesBundle") -> tuple["GroundDefeasibleRule", ...]:
    seen: dict[
        tuple[str, str, str, tuple[str, ...]],
        "GroundDefeasibleRule",
    ] = {}
    for argument in bundle.arguments:
        for rule in argument.rules:
            key = (
                rule.rule_id,
                rule.kind,
                format_ground_atom(rule.head.predicate, tuple(rule.head.arguments)),
                tuple(
                    format_ground_atom(atom.predicate, tuple(atom.arguments))
                    for atom in rule.body
                ),
            )
            seen[key] = rule
    return tuple(
        sorted(
            seen.values(),
            key=lambda rule: (
                rule.rule_id,
                rule.kind,
                format_ground_atom(rule.head.predicate, tuple(rule.head.arguments)),
                tuple(
                    format_ground_atom(atom.predicate, tuple(atom.arguments))
                    for atom in rule.body
                ),
            ),
        )
    )


def format_ground_rule(rule: "GroundDefeasibleRule") -> str:
    arrow = {
        "strict": "<-",
        "defeasible": "-<",
        "defeater": "~<",
    }.get(rule.kind, "<-")
    body = ", ".join(
        format_ground_atom(atom.predicate, tuple(atom.arguments))
        for atom in rule.body
    ) or "true"
    head = format_ground_atom(rule.head.predicate, tuple(rule.head.arguments))
    return f"{rule.rule_id}: {head} {arrow} {body}"


def format_argument(argument: "Argument") -> str:
    conclusion = format_ground_atom(
        argument.conclusion.predicate,
        tuple(argument.conclusion.arguments),
    )
    if not argument.rules:
        return f"{conclusion} <= fact"
    rules = ", ".join(
        sorted(rule.rule_id for rule in argument.rules)
    )
    return f"{conclusion} <= {rules}"


def parse_query_atom(text: str) -> GroundAtom:
    query = text.strip()
    if not query:
        raise GroundingInspectionError("Grounding query atom must be non-empty.")
    if "(" not in query:
        return GroundAtom(predicate=query, arguments=())
    if not query.endswith(")"):
        raise GroundingInspectionError(f"Malformed grounding atom: {text!r}")
    predicate, _, raw_args = query.partition("(")
    predicate = predicate.strip()
    raw_args = raw_args[:-1].strip()
    if not predicate:
        raise GroundingInspectionError(f"Malformed grounding atom: {text!r}")
    if not raw_args:
        return GroundAtom(predicate=predicate, arguments=())
    arguments: list[Scalar] = []
    for part in raw_args.split(","):
        token = part.strip()
        if token == "":
            raise GroundingInspectionError(f"Malformed grounding atom: {text!r}")
        if token.lower() == "true":
            arguments.append(True)
            continue
        if token.lower() == "false":
            arguments.append(False)
            continue
        if token.startswith('"') and token.endswith('"') and len(token) >= 2:
            arguments.append(token[1:-1])
            continue
        if token.startswith("'") and token.endswith("'") and len(token) >= 2:
            arguments.append(token[1:-1])
            continue
        try:
            arguments.append(int(token))
            continue
        except ValueError:
            pass
        try:
            if any(char in token for char in (".", "e", "E")):
                arguments.append(float(token))
                continue
        except ValueError:
            pass
        arguments.append(token)
    return GroundAtom(predicate=predicate, arguments=tuple(arguments))


def inspect_grounding_status(repo: "Repository") -> GroundingStatusReport:
    surface = inspect_grounding_surface(repo)
    if not surface.has_authoring:
        return GroundingStatusReport(
            surface=surface,
            surface_state="none",
            message="No grounding authoring found: predicates/ and rules/ contain no YAML files.",
            facts_count=0,
            section_counts=(),
        )
    if surface.missing_predicates:
        return GroundingStatusReport(
            surface=surface,
            surface_state="invalid",
            message="Invalid grounding surface: rules/ has YAML files but predicates/ has none.",
            facts_count=0,
            section_counts=(),
        )

    bundle = require_grounding_bundle(repo, return_arguments=False)
    return GroundingStatusReport(
        surface=surface,
        surface_state="ready",
        message=None,
        facts_count=len(bundle.source_facts),
        section_counts=tuple(
            (section, _section_atom_count(bundle, section))
            for section in SECTION_ORDER
        ),
    )


def inspect_grounding_show(repo: "Repository") -> GroundingShowReport:
    bundle = require_grounding_bundle(repo, return_arguments=True)
    rules = _grounded_rules(bundle)
    sections: list[tuple[str, tuple[str, ...]]] = []
    for section in SECTION_ORDER:
        section_rows = bundle.sections[section]
        lines: list[str] = []
        for predicate in sorted(section_rows):
            rows = sorted(section_rows[predicate], key=_sort_row)
            for row in rows:
                lines.append(format_ground_atom(predicate, tuple(row)))
        sections.append((section, tuple(lines)))

    return GroundingShowReport(
        facts=tuple(repr(fact) for fact in bundle.source_facts),
        rules=tuple(
            GroundRuleLine(rule_id=rule.rule_id, text=format_ground_rule(rule))
            for rule in rules
        ),
        sections=tuple(sections),
    )


def inspect_grounding_query(repo: "Repository", atom: str) -> GroundingQueryReport:
    bundle = require_grounding_bundle(repo, return_arguments=False)
    query_atom = parse_query_atom(atom)
    matched_sections = tuple(
        name
        for name in SECTION_ORDER
        if tuple(query_atom.arguments) in bundle.sections[name].get(query_atom.predicate, frozenset())
    )
    return GroundingQueryReport(
        atom=query_atom,
        matched_sections=matched_sections,
    )


def inspect_grounding_arguments(repo: "Repository") -> GroundingArgumentsReport:
    bundle = require_grounding_bundle(repo, return_arguments=True)
    return GroundingArgumentsReport(
        arguments=tuple(format_argument(argument) for argument in bundle.arguments),
    )
