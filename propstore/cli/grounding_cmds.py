from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import click

from propstore.aspic import GroundAtom
from propstore.grounding.loading import build_grounded_bundle

if TYPE_CHECKING:
    from propstore.repository import Repository
    from propstore.grounding.bundle import GroundedRulesBundle
    from gunray import Argument
    from gunray.types import GroundDefeasibleRule, Scalar


_SECTION_ORDER = (
    "definitely",
    "defeasibly",
    "not_defeasibly",
    "undecided",
)


@dataclass(frozen=True)
class _GroundingSurface:
    predicate_files: tuple[str, ...]
    rule_files: tuple[str, ...]

    @property
    def has_authoring(self) -> bool:
        return bool(self.predicate_files or self.rule_files)

    @property
    def missing_predicates(self) -> bool:
        return bool(self.rule_files) and not bool(self.predicate_files)


def _yaml_file_names(node) -> tuple[str, ...]:
    if not node.exists() or not node.is_dir():
        return ()
    return tuple(
        sorted(
            entry.name
            for entry in node.iterdir()
            if entry.is_file() and entry.suffix == ".yaml"
        )
    )


def _inspect_grounding_surface(repo: "Repository") -> _GroundingSurface:
    tree = repo.tree()
    return _GroundingSurface(
        predicate_files=_yaml_file_names(tree / "predicates"),
        rule_files=_yaml_file_names(tree / "rules"),
    )


def _require_grounding_bundle(
    repo: "Repository",
    *,
    return_arguments: bool,
) -> "GroundedRulesBundle":
    surface = _inspect_grounding_surface(repo)
    if not surface.has_authoring:
        raise click.ClickException(
            "No grounding authoring found: predicates/ and rules/ contain no YAML files."
        )
    if surface.missing_predicates:
        raise click.ClickException(
            "Invalid grounding surface: rules/ has YAML files but predicates/ has none."
        )
    try:
        return build_grounded_bundle(
            repo.tree(),
            return_arguments=return_arguments,
        )
    except ValueError as exc:
        raise click.ClickException(f"Grounding unavailable: {exc}") from exc


def _format_ground_atom(predicate: str, arguments: tuple["Scalar", ...]) -> str:
    return repr(GroundAtom(predicate=predicate, arguments=arguments))


def _sort_row(row: tuple["Scalar", ...]) -> tuple[str, ...]:
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
                _format_ground_atom(rule.head.predicate, tuple(rule.head.arguments)),
                tuple(
                    _format_ground_atom(atom.predicate, tuple(atom.arguments))
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
                _format_ground_atom(rule.head.predicate, tuple(rule.head.arguments)),
                tuple(
                    _format_ground_atom(atom.predicate, tuple(atom.arguments))
                    for atom in rule.body
                ),
            ),
        )
    )


def _format_ground_rule(rule: "GroundDefeasibleRule") -> str:
    arrow = {
        "strict": "<-",
        "defeasible": "-<",
        "defeater": "~<",
    }.get(rule.kind, "<-")
    body = ", ".join(
        _format_ground_atom(atom.predicate, tuple(atom.arguments))
        for atom in rule.body
    ) or "true"
    head = _format_ground_atom(rule.head.predicate, tuple(rule.head.arguments))
    return f"{rule.rule_id}: {head} {arrow} {body}"


def _format_argument(argument: "Argument") -> str:
    conclusion = _format_ground_atom(
        argument.conclusion.predicate,
        tuple(argument.conclusion.arguments),
    )
    if not argument.rules:
        return f"{conclusion} <= fact"
    rules = ", ".join(
        sorted(rule.rule_id for rule in argument.rules)
    )
    return f"{conclusion} <= {rules}"


def _parse_query_atom(text: str) -> GroundAtom:
    query = text.strip()
    if not query:
        raise click.ClickException("Grounding query atom must be non-empty.")
    if "(" not in query:
        return GroundAtom(predicate=query, arguments=())
    if not query.endswith(")"):
        raise click.ClickException(f"Malformed grounding atom: {text!r}")
    predicate, _, raw_args = query.partition("(")
    predicate = predicate.strip()
    raw_args = raw_args[:-1].strip()
    if not predicate:
        raise click.ClickException(f"Malformed grounding atom: {text!r}")
    if not raw_args:
        return GroundAtom(predicate=predicate, arguments=())
    arguments: list["Scalar"] = []
    for part in raw_args.split(","):
        token = part.strip()
        if token == "":
            raise click.ClickException(f"Malformed grounding atom: {text!r}")
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


@click.group()
def grounding() -> None:
    """Inspect the grounded rule theory directly."""


@grounding.command("status")
@click.pass_obj
def grounding_status(obj: dict) -> None:
    repo: "Repository" = obj["repo"]
    surface = _inspect_grounding_surface(repo)
    click.echo(f"Predicate files: {len(surface.predicate_files)}")
    click.echo(f"Rule files: {len(surface.rule_files)}")

    if not surface.has_authoring:
        click.echo("Grounding surface: none")
        click.echo("No grounding authoring found: predicates/ and rules/ contain no YAML files.")
        return
    if surface.missing_predicates:
        click.echo("Grounding surface: invalid")
        click.echo("Invalid grounding surface: rules/ has YAML files but predicates/ has none.")
        return

    bundle = _require_grounding_bundle(repo, return_arguments=False)
    click.echo("Grounding surface: ready")
    click.echo(f"Facts: {len(bundle.source_facts)}")
    for section in _SECTION_ORDER:
        click.echo(f"  {section}: {_section_atom_count(bundle, section)}")


@grounding.command("show")
@click.pass_obj
def grounding_show(obj: dict) -> None:
    repo: "Repository" = obj["repo"]
    bundle = _require_grounding_bundle(repo, return_arguments=True)
    rules = _grounded_rules(bundle)

    click.echo(f"Facts ({len(bundle.source_facts)}):")
    if not bundle.source_facts:
        click.echo("  <empty>")
    else:
        for fact in bundle.source_facts:
            click.echo(f"  {fact!r}")

    click.echo(f"Grounded rules ({len(rules)}):")
    if not rules:
        click.echo("  <empty>")
    else:
        for rule in rules:
            click.echo(f"  {_format_ground_rule(rule)}")

    click.echo("Sections:")
    for section in _SECTION_ORDER:
        click.echo(f"  {section}:")
        section_rows = bundle.sections[section]
        if not section_rows:
            click.echo("    <empty>")
            continue
        for predicate in sorted(section_rows):
            rows = sorted(section_rows[predicate], key=_sort_row)
            for row in rows:
                click.echo(f"    {_format_ground_atom(predicate, tuple(row))}")


@grounding.command("query")
@click.argument("atom")
@click.pass_obj
def grounding_query(obj: dict, atom: str) -> None:
    repo: "Repository" = obj["repo"]
    bundle = _require_grounding_bundle(repo, return_arguments=False)
    query_atom = _parse_query_atom(atom)

    matched_sections = [
        name
        for name in _SECTION_ORDER
        if tuple(query_atom.arguments) in bundle.sections[name].get(query_atom.predicate, frozenset())
    ]
    click.echo(f"{query_atom!r}")
    if matched_sections:
        click.echo(f"  status: {', '.join(matched_sections)}")
        return
    click.echo("  status: absent")


@grounding.command("arguments")
@click.pass_obj
def grounding_arguments(obj: dict) -> None:
    repo: "Repository" = obj["repo"]
    bundle = _require_grounding_bundle(repo, return_arguments=True)
    click.echo(f"Arguments ({len(bundle.arguments)}):")
    if not bundle.arguments:
        click.echo("  <empty>")
        return
    for argument in bundle.arguments:
        click.echo(f"  {_format_argument(argument)}")
