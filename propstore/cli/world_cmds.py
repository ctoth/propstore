"""pks world - query and reason over the compiled knowledge base."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import json
import sys
from collections.abc import Callable, Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import click

from propstore.cli.helpers import open_world_model
from propstore.repository import Repository
from propstore.world.types import ATMSNodeStatus, ValueStatus, coerce_value_status

if TYPE_CHECKING:
    from propstore.core.active_claims import ActiveClaim
    from propstore.core.graph_types import ActiveWorldGraph
    from propstore.world import BoundWorld, QueryableAssumption, RenderPolicy, WorldModel
    from propstore.core.labels import Label, SupportQuality


def _bind_world(
    wm: WorldModel,
    bindings: Mapping[str, str],
    *,
    context_id: str | None = None,
    policy: RenderPolicy | None = None,
) -> BoundWorld:
    from propstore.world import Environment
    from propstore.core.id_types import to_context_id

    environment = Environment(
        bindings=dict(bindings),
        context_id=(None if context_id is None else to_context_id(context_id)),
    )
    return wm.bind(environment=environment, policy=policy)


def _lifecycle_policy(
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
    *,
    base: "RenderPolicy | None" = None,
) -> "RenderPolicy":
    """Construct (or clone) a ``RenderPolicy`` carrying the Phase 4
    lifecycle visibility flags.

    Closes axis-1 findings 3.1 / 3.2 / 3.3 per
    ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``.
    When ``base`` is provided, the existing policy's non-visibility
    fields survive; only the three new flags are overwritten — this
    lets commands like ``pks world resolve`` (which already construct a
    feature-rich RenderPolicy) layer the new flags on without losing
    any prior configuration.
    """
    from dataclasses import replace

    from propstore.world import RenderPolicy as _RenderPolicy

    if base is None:
        return _RenderPolicy(
            include_drafts=include_drafts,
            include_blocked=include_blocked,
            show_quarantined=show_quarantined,
        )
    return replace(
        base,
        include_drafts=include_drafts,
        include_blocked=include_blocked,
        show_quarantined=show_quarantined,
    )

# ── World command group ──────────────────────────────────────────────


@click.group()
@click.pass_obj
def world(obj: dict) -> None:
    """Query the compiled knowledge base."""
    pass


def _resolve_world_target(wm, target: str) -> str:
    """Resolve a world command target by alias, concept ID, or canonical name."""
    return wm.resolve_concept(target) or target


@world.command("status")
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft' in the counts.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked' in the counts."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help=(
        "Surface a Diagnostics count line sourced from build_diagnostics."
    ),
)
@click.pass_obj
def world_status(
    obj: dict,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """Show knowledge base stats (concepts, claims, conflicts).

    Claim counts reflect the lifecycle-visibility policy selected by the
    three opt-in flags. Closes axis-1 findings 3.1 / 3.2 / 3.3
    (``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``):
    the sidecar holds every row and the render layer decides what to
    report.
    """
    from propstore.world.queries import WorldStatusRequest, get_world_status

    repo: Repository = obj["repo"]
    policy = _lifecycle_policy(include_drafts, include_blocked, show_quarantined)
    with open_world_model(repo) as wm:
        report = get_world_status(wm, WorldStatusRequest(policy=policy))
        click.echo(f"Concepts: {report.concept_count}")
        click.echo(f"Claims:   {report.visible_claim_count}")
        click.echo(f"Conflicts: {report.conflict_count}")
        if policy.show_quarantined:
            click.echo(f"Diagnostics: {report.diagnostic_count}")


@world.command("query")
@click.argument("concept_id")
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft'.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked'."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help=(
        "Append a Diagnostics block sourced from build_diagnostics."
    ),
)
@click.pass_obj
def world_query(
    obj: dict,
    concept_id: str,
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """Show all claims for a concept under the lifecycle-visibility
    policy.

    Closes axis-1 findings 3.1 / 3.2 / 3.3
    (``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``):
    the default output excludes rows quarantined by the build
    (``build_status='blocked'``), drafts (``stage='draft'``), and
    promotion-blocked mirror rows; opt-in flags lift each filter.
    """
    from propstore.world.queries import (
        UnknownConceptError,
        WorldConceptQueryRequest,
        query_world_concept,
    )

    repo: Repository = obj["repo"]
    policy = _lifecycle_policy(include_drafts, include_blocked, show_quarantined)
    with open_world_model(repo) as wm:
        try:
            report = query_world_concept(
                wm,
                WorldConceptQueryRequest(target=concept_id, policy=policy),
            )
        except UnknownConceptError:
            click.echo(f"Unknown concept: {concept_id}", err=True)
            sys.exit(1)

        click.echo(f"{report.canonical_name} ({report.concept_display_id})")
        if not report.claims:
            click.echo("  (no claims)")
        for claim in report.claims:
            click.echo(
                f"  {claim.display_id}: {claim.claim_type} "
                f"{claim.value_display} conditions={claim.conditions}"
            )
        if policy.show_quarantined:
            if report.diagnostics:
                click.echo("Diagnostics:")
                for diagnostic in report.diagnostics:
                    click.echo(
                        f"  {diagnostic.target} "
                        f"[{diagnostic.diagnostic_kind}] {diagnostic.message}"
                    )


@world.command("bind")
@click.argument("args", nargs=-1)
@click.pass_obj
def world_bind(obj: dict, args: tuple[str, ...]) -> None:
    """Show active claims under condition bindings.

    Usage: pks world bind domain=example [concept_id]

    Arguments with '=' are bindings, the last argument without '=' is a concept filter.
    """
    from propstore.world.queries import (
        WorldBindActiveReport,
        WorldBindConceptReport,
        WorldBindRequest,
        query_bound_world,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, query_concept = _parse_bindings(args)
        report = query_bound_world(
            wm,
            WorldBindRequest(bindings=bindings, target=query_concept),
        )

        if isinstance(report, WorldBindConceptReport):
            click.echo(f"{report.concept_display_id}: {report.status}")
            for claim in report.claims:
                click.echo(
                    f"  {claim.display_id}: {claim.value_display} "
                    f"source={claim.source}"
                )
            return

        assert isinstance(report, WorldBindActiveReport)
        click.echo(f"Active claims: {report.active_claim_count}")
        for claim in report.claims:
            click.echo(
                f"  {claim.display_id}: {claim.concept_display_id} "
                f"{claim.value_display} conditions={claim.conditions}"
            )


@world.command("explain")
@click.argument("claim_id")
@click.pass_obj
def world_explain(obj: dict, claim_id: str) -> None:
    """Show the stance chain for a claim."""
    from propstore.world.queries import (
        UnknownClaimError,
        WorldExplainRequest,
        explain_world_claim,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        try:
            report = explain_world_claim(wm, WorldExplainRequest(claim_id=claim_id))
        except UnknownClaimError:
            click.echo(f"Unknown claim: {claim_id}", err=True)
            sys.exit(1)

    click.echo(
        f"{report.claim_display_id}: {report.claim_type} "
        f"concept={report.concept_display_id} "
        f"value={report.value}"
    )
    if not report.stances:
        click.echo("  (no stances)")
    for stance in report.stances:
        indent = "    " if stance.nested else "  "
        click.echo(
            f"{indent}{stance.source_display_id} "
            f"{stance.stance_type} -> {stance.target_display_id}"
            f" (strength={stance.strength}, note={stance.note})"
        )


@world.command("algorithms")
@click.option("--stage", default=None, help="Filter by processing stage")
@click.option("--concept", default=None, help="Filter by concept")
@click.pass_obj
def world_algorithms(obj: dict, stage: str | None, concept: str | None) -> None:
    """List algorithm claims in the world model."""
    from propstore.world.queries import (
        WorldAlgorithmsRequest,
        list_world_algorithms,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        report = list_world_algorithms(
            wm,
            WorldAlgorithmsRequest(stage=stage, concept=concept),
        )

    if not report.algorithms:
        click.echo("No algorithm claims found.")
        return

    # Table header
    click.echo(f"{'ID':<20} {'Name':<30} {'Stage':<15} {'Concept(s)'}")
    click.echo("-" * 80)
    for claim in report.algorithms:
        click.echo(
            f"{claim.claim_id:<20} {claim.name:<30} "
            f"{claim.stage:<15} {claim.concept_id}"
        )

    click.echo(f"\n{len(report.algorithms)} algorithm claim(s).")


def _parse_bindings(args: tuple[str, ...]) -> tuple[dict[str, str], str | None]:
    """Parse CLI args into (bindings, concept_id).

    Arguments with '=' are bindings, the last argument without '=' is concept_id.
    """
    from propstore.cli.helpers import parse_kv_pairs

    parsed_objects, remaining = parse_kv_pairs(args)
    parsed: dict[str, str] = {}
    for key, value in parsed_objects.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise click.ClickException("world bindings must be plain string key=value pairs")
        parsed[key] = value
    concept_id = remaining[-1] if remaining else None
    return parsed, concept_id


def _parse_hypothetical_add(add_json: str | None):
    """Parse the CLI JSON payload for ``world hypothetical --add``."""
    from propstore.world.queries import WorldHypotheticalSyntheticClaimSpec

    if add_json is None:
        return ()
    try:
        raw = json.loads(add_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"invalid --add JSON: {exc.msg}") from exc
    entries = [raw] if isinstance(raw, dict) else raw
    if not isinstance(entries, list):
        raise click.ClickException("--add JSON must be an object or a list of objects")
    specs: list[WorldHypotheticalSyntheticClaimSpec] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise click.ClickException("--add JSON entries must be objects")
        claim_id = entry.get("id")
        concept_id = entry.get("concept_id")
        if not isinstance(claim_id, str) or not claim_id:
            raise click.ClickException("--add JSON entries require string id")
        if not isinstance(concept_id, str) or not concept_id:
            raise click.ClickException("--add JSON entries require string concept_id")
        conditions = entry.get("conditions", [])
        if not isinstance(conditions, list):
            raise click.ClickException("--add JSON conditions must be a list")
        value = entry.get("value")
        if value is not None and (
            not isinstance(value, str | int | float) or isinstance(value, bool)
        ):
            raise click.ClickException("--add JSON value must be a string or number")
        specs.append(
            WorldHypotheticalSyntheticClaimSpec(
                claim_id=claim_id,
                concept_id=concept_id,
                claim_type=entry.get("type", "parameter"),
                value=float(value) if isinstance(value, int | float) else value,
                conditions=tuple(conditions),
            )
        )
    return tuple(specs)


def _format_chain_concept(concept) -> str:
    if concept.canonical_name:
        return f"{concept.display_id} ({concept.canonical_name})"
    return str(concept.display_id)


def _format_revision_payload(payload: dict) -> str:
    claim_type = payload.get("type")
    concept_id = payload.get("concept_id")
    value = payload.get("value")
    unit = payload.get("unit")
    parts: list[str] = []
    if claim_type:
        parts.append(f"type={claim_type}")
    if concept_id:
        parts.append(f"concept={concept_id}")
    if value is not None:
        if unit:
            parts.append(f"value={value} {unit}")
        else:
            parts.append(f"value={value}")
    return " ".join(parts)


def _revision_atom_display_id(atom_id: str, *, payload: Mapping[str, object] | None = None) -> str:
    if payload is not None:
        logical_id = payload.get("logical_id") or payload.get("primary_logical_id")
        if isinstance(logical_id, str) and logical_id:
            return f"claim:{logical_id.split(':', 1)[1] if ':' in logical_id else logical_id}"
        logical_ids = payload.get("logical_ids")
        if isinstance(logical_ids, list):
            for entry in logical_ids:
                if not isinstance(entry, Mapping):
                    continue
                value = entry.get("value")
                if isinstance(value, str) and value:
                    return f"claim:{value}"
    return atom_id


def _format_revision_assumption(assumption) -> str:
    return (
        f"{assumption.assumption_id}: kind={assumption.kind} "
        f"source={assumption.source} cel={assumption.cel}"
    )


def _parse_revision_atom_json(atom_json: str) -> dict:
    try:
        data = json.loads(atom_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid --atom JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise click.ClickException("--atom must decode to a JSON object")
    return data


def _emit_revision_result(result) -> None:
    click.echo(f"Accepted ({len(result.accepted_atom_ids)} atoms):")
    for atom_id in result.accepted_atom_ids:
        click.echo(f"  {atom_id}")

    click.echo(f"Rejected ({len(result.rejected_atom_ids)} atoms):")
    for atom_id in result.rejected_atom_ids:
        click.echo(f"  {atom_id}")

    click.echo(f"Incision set: {', '.join(result.incision_set) if result.incision_set else '(none)'}")


def _emit_revision_explanation(explanation) -> None:
    click.echo(f"Accepted ({len(explanation.accepted_atom_ids)} atoms):")
    for atom_id in explanation.accepted_atom_ids:
        click.echo(f"  {atom_id}")

    click.echo(f"Rejected ({len(explanation.rejected_atom_ids)} atoms):")
    for atom_id in explanation.rejected_atom_ids:
        click.echo(f"  {atom_id}")

    incision = explanation.incision_set
    click.echo(f"Incision set: {', '.join(incision) if incision else '(none)'}")
    click.echo("Atoms:")
    for atom_id, detail in explanation.atoms.items():
        line = f"  {atom_id}: status={detail.status} reason={detail.reason}"
        ranking = detail.ranking
        if ranking is not None:
            line += f" support_count={ranking.support_count or 0}"
        click.echo(line)


def _emit_epistemic_state(state) -> None:
    click.echo(f"Iterated state ({len(state.accepted_atom_ids)} accepted atoms)")
    click.echo(f"History length: {len(state.history)}")
    click.echo("Ranking:")
    for rank, atom_id in enumerate(state.ranked_atom_ids, start=1):
        click.echo(f"  {rank}. {atom_id}")


def _emit_iterated_revision(result, previous_state, next_state, *, operator: str) -> None:
    click.echo(f"Operator: {operator}")
    _emit_revision_result(result)
    click.echo(f"Next state ({len(next_state.accepted_atom_ids)} accepted atoms)")
    click.echo(f"History length: {len(next_state.history)}")
    click.echo("Ranking:")
    for rank, atom_id in enumerate(next_state.ranked_atom_ids, start=1):
        click.echo(f"  {rank}. {atom_id}")
    click.echo("Ranking delta:")
    previous_ranking = previous_state.ranking
    for atom_id in next_state.ranked_atom_ids:
        old_rank = previous_ranking.get(atom_id)
        new_rank = next_state.ranking.get(atom_id)
        if old_rank is None:
            click.echo(f"  + {atom_id}: new at rank {new_rank}")
        elif old_rank != new_rank:
            click.echo(f"  ~ {atom_id}: {old_rank} -> {new_rank}")
    for atom_id, old_rank in previous_ranking.items():
        if atom_id not in next_state.ranking:
            click.echo(f"  - {atom_id}: dropped from rank {old_rank}")
    click.echo("History:")
    last_episode = next_state.history[-1] if next_state.history else None
    if last_episode is None:
        click.echo("  (empty)")
    else:
        click.echo(
            f"  {last_episode.operator}: input={last_episode.input_atom_id} "
            f"targets={list(last_episode.target_atom_ids)} "
            f"accepted={len(last_episode.accepted_atom_ids)} "
            f"rejected={len(last_episode.rejected_atom_ids)}"
        )


@world.command("revision-base")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the revision base")
@click.pass_obj
def world_revision_base(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show the current revision-facing belief base for a scoped world."""
    from propstore.support_revision.state import is_assumption_atom, is_claim_atom
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        revision_base,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        base = revision_base(wm, RevisionWorldRequest(bindings, context))

        click.echo(f"Revision base ({len(base.atoms)} atoms, {len(base.assumptions)} assumptions)")
        for atom in base.atoms:
            if is_claim_atom(atom):
                payload = atom.claim.to_dict()
            elif is_assumption_atom(atom):
                payload = {
                    "assumption_id": atom.assumption.assumption_id,
                    "cel": atom.assumption.cel,
                    "kind": atom.assumption.kind,
                    "source": atom.assumption.source,
                }
            else:
                raise TypeError(f"unsupported revision atom: {type(atom).__name__}")
            details = _format_revision_payload(payload)
            atom_display_id = _revision_atom_display_id(atom.atom_id, payload=payload)
            if details:
                click.echo(f"  {atom_display_id}: {details}")
            else:
                click.echo(f"  {atom_display_id}")

        if base.assumptions:
            click.echo("Assumptions:")
            for assumption in base.assumptions:
                click.echo(f"  {_format_revision_assumption(assumption)}")


@world.command("revision-entrenchment")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the revision entrenchment")
@click.pass_obj
def world_revision_entrenchment(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show the current deterministic entrenchment ordering for a scoped world."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        revision_entrenchment,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        report = revision_entrenchment(wm, RevisionWorldRequest(bindings, context))

        click.echo(f"Entrenchment ({len(report.ranked_atom_ids)} atoms)")
        for rank, atom_id in enumerate(report.ranked_atom_ids, start=1):
            reason = report.reasons.get(atom_id)
            support_count = 0 if reason is None or reason.support_count is None else reason.support_count
            essential_support = () if reason is None else reason.essential_support
            override = None if reason is None else reason.override_priority
            click.echo(
                f"  {rank}. {atom_id} "
                f"support_count={support_count} "
                f"essential_support={_format_assumption_ids(essential_support)} "
                f"override={override}"
            )


@world.command("expand")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to add")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_expand(obj: dict, args: tuple[str, ...], atom_json: str, context: str | None) -> None:
    """Expand the scoped revision belief base without mutating source YAML."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        expand_revision,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        result = expand_revision(
            wm,
            RevisionWorldRequest(bindings, context),
            _parse_revision_atom_json(atom_json),
        )
        _emit_revision_result(result)


@world.command("contract")
@click.argument("args", nargs=-1)
@click.option("--target", "targets", multiple=True, required=True, help="Existing atom or claim id to contract")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_contract(obj: dict, args: tuple[str, ...], targets: tuple[str, ...], context: str | None) -> None:
    """Contract the scoped revision belief base without mutating source YAML."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        contract_revision,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        result = contract_revision(
            wm,
            RevisionWorldRequest(bindings, context),
            targets,
        )
        _emit_revision_result(result)


@world.command("revise")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to admit")
@click.option("--conflict", "conflicts", multiple=True, help="Existing atom or claim id that conflicts with the new atom")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_revise(
    obj: dict,
    args: tuple[str, ...],
    atom_json: str,
    conflicts: tuple[str, ...],
    context: str | None,
) -> None:
    """Revise the scoped belief base without mutating source YAML."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        revise_world,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        result = revise_world(
            wm,
            RevisionWorldRequest(bindings, context),
            _parse_revision_atom_json(atom_json),
            conflicts,
        )
        _emit_revision_result(result)


@world.command("revision-explain")
@click.argument("args", nargs=-1)
@click.option("--operation", type=click.Choice(["expand", "contract", "revise"]), required=True)
@click.option("--atom", "atom_json", default=None, help="JSON revision atom for expand/revise")
@click.option("--target", "targets", multiple=True, help="Existing atom or claim id for contract")
@click.option("--conflict", "conflicts", multiple=True, help="Existing atom or claim id that conflicts with the new atom")
@click.option("--context", default=None, help="Context to scope the revision operation")
@click.pass_obj
def world_revision_explain(
    obj: dict,
    args: tuple[str, ...],
    operation: str,
    atom_json: str | None,
    targets: tuple[str, ...],
    conflicts: tuple[str, ...],
    context: str | None,
) -> None:
    """Explain one revision operation over the current scoped world."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        explain_revision_operation,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)

        if operation == "expand":
            if atom_json is None:
                raise click.ClickException("--atom is required for --operation expand")
            atom = _parse_revision_atom_json(atom_json)
        elif operation == "contract":
            if not targets:
                raise click.ClickException("--target is required for --operation contract")
            atom = None
        else:
            if atom_json is None:
                raise click.ClickException("--atom is required for --operation revise")
            atom = _parse_revision_atom_json(atom_json)

        try:
            explanation = explain_revision_operation(
                wm,
                RevisionWorldRequest(bindings, context),
                operation=operation,
                atom=atom,
                targets=targets,
                conflicts=conflicts,
            )
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        _emit_revision_explanation(explanation)


@world.command("iterated-state")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the iterated revision state")
@click.pass_obj
def world_iterated_state(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Inspect the current explicit iterated revision state for a scoped world."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        epistemic_state,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        state = epistemic_state(wm, RevisionWorldRequest(bindings, context))
        _emit_epistemic_state(state)


@world.command("iterated-revise")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to admit")
@click.option("--conflict", "conflicts", multiple=True, help="Existing atom or claim id that conflicts with the new atom")
@click.option("--operator", type=click.Choice(["restrained", "lexicographic"]), default="restrained")
@click.option("--context", default=None, help="Context to scope the iterated revision operation")
@click.pass_obj
def world_iterated_revise(
    obj: dict,
    args: tuple[str, ...],
    atom_json: str,
    conflicts: tuple[str, ...],
    operator: str,
    context: str | None,
) -> None:
    """Run one iterated revision episode and print the next explicit state."""
    from propstore.support_revision.workflows import (
        RevisionWorldRequest,
        iterated_revise_world,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        report = iterated_revise_world(
            wm,
            RevisionWorldRequest(bindings, context),
            atom=_parse_revision_atom_json(atom_json),
            conflicts=conflicts,
            operator=operator,
        )
        _emit_iterated_revision(
            report.result,
            report.previous_state,
            report.next_state,
            operator=report.operator,
        )


@contextmanager
def _open_atms_world(
    repo: Repository,
    args: tuple[str, ...],
    *,
    context: str | None = None,
):
    from propstore.world.atms_workflows import ATMSBindRequest, bind_atms_world

    with open_world_model(repo) as wm:
        bindings, concept_id = _parse_bindings(args)
        bound = bind_atms_world(wm, ATMSBindRequest(bindings, context))
        yield wm, bound, bindings, concept_id


def _format_assumption_ids(assumption_ids: Sequence[str]) -> str:
    if not assumption_ids:
        return "[]"
    return "[" + ", ".join(str(assumption_id) for assumption_id in assumption_ids) + "]"


def _parse_queryables(
    queryables: tuple[str, ...],
) -> list[QueryableAssumption]:
    from propstore.world.types import coerce_queryable_assumptions

    return list(coerce_queryable_assumptions(queryables))


def _format_status_value(status: object) -> str:
    if isinstance(status, str):
        return status
    if isinstance(status, Enum):
        return str(status.value)
    return str(status)


def _support_metadata_for(
    bound: object,
    active_claims: Sequence["ActiveClaim"],
) -> dict[str, tuple[Label | None, SupportQuality]]:
    from propstore.world.types import ClaimSupportView

    if not isinstance(bound, ClaimSupportView):
        return {}

    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
    for claim in active_claims:
        support_metadata[str(claim.claim_id)] = bound.claim_support(claim)
    return support_metadata


def _active_graph_for(bound: object) -> ActiveWorldGraph | None:
    from propstore.world.types import HasActiveGraph

    if isinstance(bound, HasActiveGraph):
        return bound._active_graph
    return None


def _format_future_summary(future: dict) -> str:
    queryables = ", ".join(future.get("queryable_cels", ()))
    return (
        f"[{queryables}] -> {future['status']}"
        f" environment={_format_assumption_ids(future.get('environment', ())) }"
    )


@world.command("atms-status")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_status(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show ATMS-native claim status, support quality, and essential support."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, concept_id):
        resolved = None
        if concept_id:
            resolved = _resolve_world_target(wm, concept_id)
        active_claims = sorted(bound.active_claims(resolved), key=lambda claim: str(claim.claim_id))
        if not active_claims:
            click.echo("No active claims for the current ATMS view.")
            return

        for claim in active_claims:
            inspection = bound.claim_status(str(claim.claim_id))
            click.echo(
                f"{claim.claim_id}: status={inspection.status.value} "
                f"support_quality={inspection.support_quality.value} "
                f"essential_support={_format_assumption_ids(inspection.essential_support.assumption_ids if inspection.essential_support else ())}"
            )
            click.echo(f"  reason: {inspection.reason}")


@world.command("atms-context")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_context(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show which ATMS-supported claims hold in the current bound environment."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, concept_id):
        environment_key = tuple(
            assumption.assumption_id
            for assumption in bound._environment.assumptions
        )
        click.echo(f"Environment: {_format_assumption_ids(environment_key)}")

        claim_ids = bound.claims_in_environment(environment_key)
        if concept_id:
            resolved = _resolve_world_target(wm, concept_id)
            allowed = {
                str(claim.claim_id)
                for claim in bound.active_claims(resolved)
            }
            claim_ids = [claim_id for claim_id in claim_ids if claim_id in allowed]

        if not claim_ids:
            click.echo("No claims have exact ATMS support in the current environment.")
            return

        for claim_id in sorted(claim_ids):
            inspection = bound.claim_status(claim_id)
            click.echo(
                f"{claim_id}: status={inspection.status.value} "
                f"essential_support={_format_assumption_ids(inspection.essential_support.assumption_ids if inspection.essential_support else ())}"
            )


@world.command("atms-verify")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_verify(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Run ATMS label self-checks for the current bound environment."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (_wm, bound, _bindings, _concept_id):
        report = bound.atms_engine().verify_labels()
        if report["ok"]:
            click.echo("ATMS labels verified.")
            return

        for section in (
            "consistency_errors",
            "minimality_errors",
            "soundness_errors",
            "completeness_errors",
        ):
            errors = report.get(section) or []
            if not errors:
                continue
            click.echo(f"{section}:")
            for error in errors:
                click.echo(f"  {error}")

    sys.exit(2)


@world.command("atms-futures")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_futures(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded ATMS future environments for a claim or concept."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        claim = wm.get_claim(target)
        if claim is not None:
            report = bound.claim_future_statuses(target, parsed_queryables, limit=limit)
            click.echo(
                f"{target}: current_status={report['current'].status.value} "
                f"could_become_in={report['could_become_in']} "
                f"could_become_out={report['could_become_out']}"
            )
            for future in report["futures"]:
                click.echo(
                    f"  future [{', '.join(future['queryable_cels'])}] -> {future['status'].value}"
                )
            return

        resolved = _resolve_world_target(wm, target)
        concept_report = bound.concept_future_statuses(resolved, parsed_queryables, limit=limit)
        if not concept_report:
            click.echo("No active claims for the requested ATMS future view.")
            return
        for claim_id in sorted(concept_report):
            report = concept_report[claim_id]
            click.echo(
                f"{claim_id}: current_status={report['current'].status.value} "
                f"could_become_in={report['could_become_in']} "
                f"could_become_out={report['could_become_out']}"
            )
            for future in report["futures"]:
                click.echo(
                    f"  future [{', '.join(future['queryable_cels'])}] -> {future['status'].value}"
                )


@world.command("atms-why-out")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_why_out(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Explain whether an ATMS OUT status is missing-support or nogood-pruned."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        claim = wm.get_claim(target)
        if claim is not None:
            report = bound.atms_engine().why_out(
                f"claim:{target}",
                queryables=parsed_queryables,
                limit=limit,
            )
            click.echo(
                f"{target}: out_kind={report['out_kind'].value if report['out_kind'] is not None else 'none'} "
                f"future_activatable={report['future_activatable']}"
            )
            click.echo(
                f"  candidate_queryables={_format_assumption_ids([', '.join(item) for item in report['candidate_queryable_cels']])}"
            )
            click.echo(f"  reason: {report['reason']}")
            return

        resolved = _resolve_world_target(wm, target)
        concept_report = bound.why_concept_out(resolved, parsed_queryables, limit=limit)
        click.echo(
                f"{resolved}: value_status={concept_report['value_status']} "
                f"supported_claim_ids={_format_assumption_ids(concept_report['supported_claim_ids'])}"
            )
        for claim_id, report in sorted(concept_report["claim_reasons"].items()):
            click.echo(
                f"  {claim_id}: out_kind={report['out_kind'].value if report['out_kind'] is not None else 'none'} "
                f"future_activatable={report['future_activatable']}"
            )


@world.command("atms-stability")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_stability(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded ATMS-native stability over the implemented future replay substrate."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        claim = wm.get_claim(target)
        if claim is not None:
            report = bound.claim_stability(target, parsed_queryables, limit=limit)
            click.echo(
                f"{target}: status={report['current'].status.value} "
                f"stable={report['stable']} "
                f"consistent_futures={report['consistent_future_count']}"
            )
            if not report["witnesses"]:
                click.echo("  no bounded consistent future flips the status")
            for witness in report["witnesses"]:
                click.echo(
                    f"  witness [{', '.join(witness['queryable_cels'])}] -> {witness['status'].value}"
                )
            return

        resolved = _resolve_world_target(wm, target)
        report = bound.concept_stability(resolved, parsed_queryables, limit=limit)
        click.echo(
            f"{resolved}: value_status={report['current_status']} "
            f"stable={report['stable']} "
            f"consistent_futures={report['consistent_future_count']}"
        )
        if not report["witnesses"]:
            click.echo("  no bounded consistent future flips the value status")
        for witness in report["witnesses"]:
            click.echo(
                f"  witness [{', '.join(witness['queryable_cels'])}] -> {witness['status']}"
            )


@world.command("atms-relevance")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_relevance(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show which bounded queryables can flip an ATMS or concept status."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        claim = wm.get_claim(target)
        if claim is not None:
            report = bound.claim_relevance(target, parsed_queryables, limit=limit)
            click.echo(
                f"{target}: current_status={report['current'].status.value} "
                f"relevant_queryables={_format_assumption_ids(report['relevant_queryables'])}"
            )
            for queryable_cel, pairs in sorted(report["witness_pairs"].items()):
                for pair in pairs:
                    click.echo(
                        f"  {queryable_cel}: "
                        f"[{', '.join(pair['without']['queryable_cels'])}] -> {pair['without']['status'].value}; "
                        f"[{', '.join(pair['with']['queryable_cels'])}] -> {pair['with']['status'].value}"
                    )
            return

        resolved = _resolve_world_target(wm, target)
        report = bound.concept_relevance(resolved, parsed_queryables, limit=limit)
        click.echo(
            f"{resolved}: current_status={report['current_status']} "
            f"relevant_queryables={_format_assumption_ids(report['relevant_queryables'])}"
        )
        for queryable_cel, pairs in sorted(report["witness_pairs"].items()):
            for pair in pairs:
                click.echo(
                    f"  {queryable_cel}: "
                    f"[{', '.join(pair['without']['queryable_cels'])}] -> {pair['without']['status']}; "
                    f"[{', '.join(pair['with']['queryable_cels'])}] -> {pair['with']['status']}"
                )


@world.command("atms-interventions")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--target-status", required=True, help="Desired ATMS node status (IN/OUT)")
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_interventions(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    target_status: str,
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show bounded additive intervention plans for an ATMS claim or concept."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        click.echo("bounded additive plans over declared queryables")
        click.echo("not revision/contraction")

        claim = wm.get_claim(target)
        if claim is not None:
            try:
                typed_target_status = ATMSNodeStatus(target_status)
            except ValueError as exc:
                raise click.ClickException(str(exc)) from exc
            plans = bound.claim_interventions(
                target,
                parsed_queryables,
                typed_target_status,
                limit=limit,
            )
            for plan in plans:
                status_val = _format_status_value(plan["result_status"])
                click.echo(
                    f"  plan [{', '.join(plan['queryable_cels'])}] -> {status_val}"
                )
            return

        resolved = _resolve_world_target(wm, target)
        try:
            typed_target_status = coerce_value_status(target_status)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        if typed_target_status is None:
            raise click.ClickException("target status is required")
        plans = bound.concept_interventions(
            resolved,
            parsed_queryables,
            typed_target_status,
            limit=limit,
        )
        for plan in plans:
            status_val = _format_status_value(plan["result_status"])
            click.echo(
                f"  plan [{', '.join(plan['queryable_cels'])}] -> {status_val}"
            )


@world.command("atms-next-query")
@click.argument("target")
@click.argument("args", nargs=-1)
@click.option("--target-status", required=True, help="Desired ATMS node status (IN/OUT)")
@click.option("--queryable", "queryables", multiple=True, required=True,
              help="Future/queryable assumption (CEL or key=value)")
@click.option("--limit", default=8, show_default=True, type=int,
              help="Maximum number of future environments to inspect")
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_next_query(
    obj: dict,
    target: str,
    args: tuple[str, ...],
    target_status: str,
    queryables: tuple[str, ...],
    limit: int,
    context: str | None,
) -> None:
    """Show next-query suggestions derived from bounded additive intervention plans."""
    repo: Repository = obj["repo"]
    with _open_atms_world(repo, args, context=context) as (wm, bound, _bindings, _concept_id):
        parsed_queryables = _parse_queryables(queryables)
        click.echo("derived from bounded additive intervention plans")

        claim = wm.get_claim(target)
        if claim is not None:
            try:
                typed_target_status = ATMSNodeStatus(target_status)
            except ValueError as exc:
                raise click.ClickException(str(exc)) from exc
            suggestions = bound.claim_next_queryables(
                target,
                parsed_queryables,
                typed_target_status,
                limit=limit,
            )
            for suggestion in suggestions:
                click.echo(
                    f"  {suggestion['queryable_cel']}: "
                    f"coverage={suggestion['plan_count']} "
                    f"smallest_plan_size={suggestion['smallest_plan_size']}"
                )
            return

        resolved = _resolve_world_target(wm, target)
        try:
            typed_target_status = coerce_value_status(target_status)
        except ValueError as exc:
            raise click.ClickException(str(exc)) from exc
        if typed_target_status is None:
            raise click.ClickException("target status is required")
        suggestions = bound.concept_next_queryables(
            resolved,
            parsed_queryables,
            typed_target_status,
            limit=limit,
        )
        for suggestion in suggestions:
            click.echo(
                f"  {suggestion['queryable_cel']}: "
                f"coverage={suggestion['plan_count']} "
                f"smallest_plan_size={suggestion['smallest_plan_size']}"
            )


@world.command("derive")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft' during derivation.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked' during derivation."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help="Allow build_diagnostics rows to surface if derivation renders them.",
)
@click.pass_obj
def world_derive(
    obj: dict,
    concept_id: str,
    args: tuple[str, ...],
    include_drafts: bool,
    include_blocked: bool,
    show_quarantined: bool,
) -> None:
    """Derive a value for a concept via parameterization relationships
    under the selected lifecycle-visibility policy.

    Per axis-1 findings 3.1 / 3.2 / 3.3
    (``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``):
    derivation works over the policy-filtered claim set; opt-in flags
    lift the default hides for drafts / blocked / quarantined rows.

    Usage: pks world derive concept5 domain=example --include-drafts
    """
    from propstore.world.queries import WorldDeriveRequest, derive_world_value

    repo: Repository = obj["repo"]
    policy = _lifecycle_policy(include_drafts, include_blocked, show_quarantined)
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        report = derive_world_value(
            wm,
            WorldDeriveRequest(
                concept_id=concept_id,
                bindings=bindings,
                policy=policy,
            ),
        )

    click.echo(f"{report.concept_id}: {report.status}")
    if report.value is not None:
        click.echo(f"  value: {report.value}")
    if report.formula:
        click.echo(f"  formula: {report.formula}")
    if report.input_values:
        click.echo(f"  inputs: {report.input_values}")
    if report.exactness:
        click.echo(f"  exactness: {report.exactness}")


@world.command("resolve")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--strategy", required=True,
              type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.option("--override", "override_id", default=None, help="Claim ID for override strategy")
@click.option("--semantics", default="grounded",
              type=click.Choice(["grounded", "preferred", "stable"]),
              help="Argumentation semantics (default: grounded)")
@click.option("--set-comparison", "set_comparison", default="elitist",
              type=click.Choice(["elitist", "democratic"]),
              help="Set comparison for preference ordering (default: elitist)")
@click.option("--decision-criterion", "decision_criterion", default="pignistic",
              type=click.Choice(["pignistic", "lower_bound", "upper_bound", "hurwicz"]),
              help="Decision criterion for opinion interpretation (default: pignistic)")
@click.option("--pessimism-index", "pessimism_index", default=0.5,
              type=float, help="Hurwicz pessimism index α ∈ [0,1] (default: 0.5)")
@click.option("--reasoning-backend", "reasoning_backend", default="claim_graph",
              type=click.Choice(["claim_graph", "aspic", "atms", "praf"]),
              help="Argumentation backend (default: claim_graph)")
@click.option("--praf-strategy", "praf_strategy", default="auto",
              type=click.Choice(["auto", "mc", "exact", "dfquad_quad", "dfquad_baf"]),
              help="PrAF computation strategy (default: auto)")
@click.option("--praf-epsilon", "praf_epsilon", default=0.01,
              type=float, help="PrAF MC error tolerance (default: 0.01)")
@click.option("--praf-confidence", "praf_confidence", default=0.95,
              type=float, help="PrAF MC confidence level (default: 0.95)")
@click.option("--praf-seed", "praf_seed", default=None,
              type=int, help="PrAF MC RNG seed (default: random)")
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft' in resolution input.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked' in resolution input."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help="Allow build_diagnostics rows to inform resolution output.",
)
@click.pass_obj
def world_resolve(obj: dict, concept_id: str, args: tuple[str, ...],
                  strategy: str, override_id: str | None,
                  semantics: str, set_comparison: str,
                  decision_criterion: str,
                  pessimism_index: float,
                  reasoning_backend: str,
                  praf_strategy: str,
                  praf_epsilon: float,
                  praf_confidence: float,
                  praf_seed: int | None,
                  include_drafts: bool,
                  include_blocked: bool,
                  show_quarantined: bool) -> None:
    """Resolve a conflicted concept using a strategy.

    Lifecycle-visibility flags (``--include-drafts``,
    ``--include-blocked``, ``--show-quarantined``) augment the
    constructed ``RenderPolicy`` to surface draft / blocked / quarantined
    rows alongside resolution. Closes axis-1 findings 3.1 / 3.2 / 3.3 per
    ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``.

    Usage: pks world resolve concept1 domain=example --strategy argumentation
    """
    from propstore.world import (
        RenderPolicy,
        ResolutionStrategy,
    )
    from propstore.world.queries import (
        WorldResolveError,
        WorldResolveRequest,
        resolve_world_value,
    )
    from propstore.world.types import normalize_argumentation_semantics

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        resolved = _resolve_world_target(wm, concept_id)
        strat = ResolutionStrategy(strategy)
        overrides_dict = {resolved: override_id} if override_id else None
        from propstore.world.types import normalize_reasoning_backend

        backend = normalize_reasoning_backend(reasoning_backend)

        policy = RenderPolicy(
            reasoning_backend=backend,
            strategy=strat,
            semantics=normalize_argumentation_semantics(semantics),
            comparison=set_comparison,
            decision_criterion=decision_criterion,
            pessimism_index=pessimism_index,
            praf_strategy=praf_strategy,
            praf_mc_epsilon=praf_epsilon,
            praf_mc_confidence=praf_confidence,
            praf_mc_seed=praf_seed,
            overrides={} if overrides_dict is None else overrides_dict,
            include_drafts=include_drafts,
            include_blocked=include_blocked,
            show_quarantined=show_quarantined,
        )

        try:
            report = resolve_world_value(
                wm,
                WorldResolveRequest(
                    concept_id=concept_id,
                    bindings=bindings,
                    policy=policy,
                ),
            )
        except WorldResolveError as e:
            click.echo(f"ERROR: {e}", err=True)
            sys.exit(1)

    click.echo(f"{report.concept_display_id}: {report.status}")
    if report.value is not None:
        click.echo(f"  value: {report.value}")
    if report.winning_claim_display_id:
        click.echo(f"  winner: {report.winning_claim_display_id}")
    if report.strategy:
        click.echo(f"  strategy: {report.strategy}")
    if report.reason:
        click.echo(f"  reason: {report.reason}")
    if report.acceptance_probs:
        click.echo("  acceptance_probs:")
        for probability in report.acceptance_probs:
            click.echo(f"    {probability.claim_id}: {probability.probability:.4f}")


@world.command("extensions")
@click.argument("args", nargs=-1)
@click.option("--backend", "backend_name", default="claim_graph",
              type=click.Choice(["claim_graph", "aspic", "atms", "praf"]),
              help="Argumentation backend (default: claim_graph)")
@click.option("--semantics", default="grounded",
              type=click.Choice(["grounded", "preferred", "stable"]),
              help="Argumentation semantics (default: grounded)")
@click.option("--set-comparison", "set_comparison", default="elitist",
              type=click.Choice(["elitist", "democratic"]),
              help="Set comparison for preference ordering (default: elitist)")
@click.option("--context", default=None, help="Context to scope the argumentation")
@click.option("--praf-strategy", "praf_strategy", default="auto",
              type=click.Choice(["auto", "mc", "exact", "dfquad_quad", "dfquad_baf"]),
              help="PrAF computation strategy (default: auto)")
@click.option("--praf-epsilon", "praf_epsilon", default=0.01,
              type=float, help="PrAF MC error tolerance (default: 0.01)")
@click.option("--praf-confidence", "praf_confidence", default=0.95,
              type=float, help="PrAF MC confidence level (default: 0.95)")
@click.option("--praf-seed", "praf_seed", default=None,
              type=int, help="PrAF MC RNG seed (default: random)")
@click.pass_obj
def world_extensions(obj: dict, args: tuple[str, ...],
                     backend_name: str, semantics: str, set_comparison: str,
                     context: str | None,
                     praf_strategy: str,
                     praf_epsilon: float,
                     praf_confidence: float,
                     praf_seed: int | None) -> None:
    """Show argumentation extensions — all claims that survive scrutiny.

    Usage: pks world extensions domain=example --semantics grounded
    """
    from propstore.relation_analysis import stance_summary
    from propstore.world import ReasoningBackend, WorldModel
    from propstore.world.types import normalize_reasoning_backend

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        from propstore.core.active_claims import coerce_active_claims

        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings, context_id=context)
        active = coerce_active_claims(bound.active_claims())
        if not active:
            click.echo("No active claims for given bindings.")
            return

        claim_ids = {str(claim.claim_id) for claim in active}
        backend = normalize_reasoning_backend(backend_name)

        if backend == ReasoningBackend.ATMS:
            click.echo(
                "ERROR: backend 'atms' does not expose Dung extensions; "
                "use worldline or resolve with reasoning_backend=atms instead.",
                err=True,
            )
            sys.exit(2)

        if backend == ReasoningBackend.PRAF:
            from propstore.praf import build_praf
            from propstore.praf import compute_praf_acceptance

            praf = build_praf(wm, claim_ids, comparison=set_comparison)
            praf_result = compute_praf_acceptance(
                praf, semantics=semantics,
                strategy=praf_strategy,
                query_kind="argument_acceptance",
                inference_mode="credulous",
                mc_epsilon=praf_epsilon,
                mc_confidence=praf_confidence,
                rng_seed=praf_seed,
            )
            summary = stance_summary(wm, claim_ids)
            click.echo(f"Backend: {backend.value}")
            click.echo(f"Semantics: {semantics}")
            click.echo(f"Strategy used: {praf_result.strategy_used}")
            if praf_result.samples is not None:
                click.echo(f"MC samples: {praf_result.samples}")
            click.echo(f"Active claims: {len(claim_ids)}")
            click.echo(f"Stances: {summary['total_stances']} total, "
                       f"{summary['included_as_attacks']} included as attacks")
            click.echo("\nAcceptance probabilities:")
            claim_map = {str(claim.claim_id): claim for claim in active}
            acceptance_probs = (
                {}
                if praf_result.acceptance_probs is None
                else praf_result.acceptance_probs
            )
            for cid, prob in sorted(
                acceptance_probs.items(),
                key=lambda x: -x[1],
            ):
                c = claim_map.get(cid)
                label = cid
                if c:
                    value = c.value
                    concept_id_val = None if c.concept_id is None else str(c.concept_id)
                    if concept_id_val:
                        concept = wm.get_concept(concept_id_val)
                        if concept is None:
                            cname = concept_id_val
                        else:
                            from propstore.core.row_types import coerce_concept_row

                            cname = coerce_concept_row(concept).canonical_name
                        if value is not None:
                            label = f"{cid}: {cname} = {value}"
                        else:
                            label = f"{cid}: {cname}"
                click.echo(f"  {label}  P(accepted) = {prob:.4f}")
            return

        if backend == ReasoningBackend.CLAIM_GRAPH:
            from propstore.claim_graph import (
                build_argumentation_framework,
                compute_claim_graph_justified_claims,
            )

            result = compute_claim_graph_justified_claims(
                wm, claim_ids,
                semantics=semantics,
                comparison=set_comparison,
            )
            af = build_argumentation_framework(
                wm, claim_ids,
                comparison=set_comparison,
            )
            arg_to_claim = {cid: cid for cid in claim_ids}
        elif backend == ReasoningBackend.ASPIC:
            from propstore.structured_projection import (
                build_structured_projection,
                compute_structured_justified_arguments,
            )
            from propstore.grounding.bundle import GroundedRulesBundle

            grounding_bundle = GroundedRulesBundle.empty()
            bundle_getter = getattr(wm, "grounding_bundle", None)
            if callable(bundle_getter):
                typed_bundle_getter = cast(
                    Callable[[], GroundedRulesBundle],
                    bundle_getter,
                )
                grounding_bundle = typed_bundle_getter()

            aspic_projection = build_structured_projection(
                wm,
                active,
                bundle=grounding_bundle,
                support_metadata=_support_metadata_for(bound, active),
                comparison=set_comparison,
                active_graph=_active_graph_for(bound),
            )
            result = compute_structured_justified_arguments(
                aspic_projection,
                semantics=semantics,
                backend=ReasoningBackend.ASPIC,
            )
            af = aspic_projection.framework
            arg_to_claim = dict(aspic_projection.argument_to_claim_id)
        else:
            raise NotImplementedError(f"Unknown backend: {backend.value}")

        summary = stance_summary(wm, claim_ids)
        click.echo(f"Backend: {backend.value}")
        click.echo(f"Semantics: {semantics}")
        click.echo(f"Set comparison: {set_comparison}")
        click.echo(f"Active claims: {len(claim_ids)}")
        click.echo(f"Stances: {summary['total_stances']} total, "
                   f"{summary['included_as_attacks']} included as attacks, "
                   f"{summary['vacuous_count']} vacuous, "
                   f"{summary['excluded_non_attack']} non-attack")
        if summary["models"]:
            click.echo(f"Models: {', '.join(summary['models'])}")

        claim_map = {str(claim.claim_id): claim for claim in active}

        def _claim_label(cid: str) -> str:
            """Format a claim for display: id (type) concept = value."""
            c = claim_map.get(cid)
            if c is None:
                return cid
            ctype = c.claim_type or "?"
            concept_id = None if c.concept_id is None else str(c.concept_id)
            value = c.value
            cname = None
            if concept_id:
                concept = wm.get_concept(concept_id)
                if concept:
                    from propstore.core.row_types import coerce_concept_row

                    cname = coerce_concept_row(concept).canonical_name
            if ctype == "parameter" and value is not None:
                return f"{cid}: {cname} = {value}"
            if ctype == "equation":
                expr = c.expression or ""
                return f"{cid}: {expr}" if expr else f"{cid} ({ctype})"
            if ctype in ("observation", "limitation", "mechanism", "comparison"):
                stmt = c.statement or c.description or ""
                if len(stmt) > 60:
                    stmt = stmt[:57] + "..."
                return f"{cid}: {stmt}" if stmt else f"{cid} ({ctype})"
            if value is not None:
                return f"{cid}: {cname} = {value}" if cname else f"{cid} = {value}"
            return f"{cid} ({ctype})"

        def _group_by_type(cids: set[str]) -> dict[str, list[str]]:
            groups: dict[str, list[str]] = {}
            for cid in sorted(cids):
                c = claim_map.get(cid)
                ctype = c.claim_type if c and c.claim_type else "unknown"
                groups.setdefault(ctype, []).append(cid)
            return groups

        if semantics == "grounded":
            if backend == ReasoningBackend.ASPIC:
                assert isinstance(result, frozenset)
                justified_claims = {
                    claim_id
                    for arg_id in result
                    if (claim_id := arg_to_claim.get(arg_id)) is not None
                }
            else:
                assert isinstance(result, frozenset)
                justified_claims = set(result)

            defeated = claim_ids - justified_claims
            defeaters_map: dict[str, list[str]] = {}
            for src, tgt in af.defeats:
                src_claim = arg_to_claim.get(src, src)
                tgt_claim = arg_to_claim.get(tgt, tgt)
                if tgt_claim in defeated:
                    defeaters_map.setdefault(tgt_claim, []).append(src_claim)

            accepted_groups = _group_by_type(justified_claims)
            click.echo(f"Accepted ({len(justified_claims)} claims):")
            for ctype, cids in sorted(accepted_groups.items()):
                click.echo(f"  {ctype} ({len(cids)}):")
                for cid in cids:
                    click.echo(f"    {_claim_label(cid)}")

            if defeated:
                click.echo(f"Defeated ({len(defeated)} claims):")
                for cid in sorted(defeated):
                    defeaters = defeaters_map.get(cid, [])
                    if defeaters:
                        by = ", ".join(sorted(defeaters))
                        click.echo(f"  {_claim_label(cid)}")
                        click.echo(f"    defeated by: {by}")
                    else:
                        click.echo(f"  {_claim_label(cid)}")
        else:
            assert isinstance(result, list)
            click.echo(f"Extensions ({len(result)}):")
            for i, ext in enumerate(result):
                ext_claims = (
                    {
                        claim_id
                        for arg_id in ext
                        if (claim_id := arg_to_claim.get(arg_id)) is not None
                    }
                    if backend == ReasoningBackend.ASPIC
                    else set(ext)
                )
                click.echo(f"  Extension {i + 1} ({len(ext_claims)} claims):")
                groups = _group_by_type(ext_claims)
                for ctype, cids in sorted(groups.items()):
                    click.echo(f"    {ctype}:")
                    for cid in cids:
                        click.echo(f"      {_claim_label(cid)}")


@world.command("hypothetical")
@click.argument("args", nargs=-1)
@click.option("--remove", multiple=True, help="Claim ID to remove")
@click.option("--add", "add_json", default=None, help="JSON synthetic claim")
@click.pass_obj
def world_hypothetical(obj: dict, args: tuple[str, ...],
                       remove: tuple[str, ...], add_json: str | None) -> None:
    """Show what changes if claims are removed/added.

    Usage: pks world hypothetical domain=example --remove claim2
    """
    from propstore.world.queries import (
        WorldHypotheticalRequest,
        diff_hypothetical_world,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        report = diff_hypothetical_world(
            wm,
            WorldHypotheticalRequest(
                bindings=bindings,
                remove_claim_ids=tuple(remove),
                add_claims=_parse_hypothetical_add(add_json),
            ),
        )

    if not report.changes:
        click.echo("No changes detected.")
    else:
        for change in report.changes:
            click.echo(
                f"{change.concept_display_id}: "
                f"{change.base_status} → {change.hypothetical_status}"
            )


@world.command("chain")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--strategy", default=None,
              type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.option(
    "--include-drafts",
    is_flag=True,
    default=False,
    help="Surface claim_core rows with stage='draft' during chain traversal.",
)
@click.option(
    "--include-blocked",
    is_flag=True,
    default=False,
    help=(
        "Surface claim_core rows with build_status='blocked' or "
        "promotion_status='blocked' during chain traversal."
    ),
)
@click.option(
    "--show-quarantined",
    is_flag=True,
    default=False,
    help="Allow build_diagnostics rows to inform chain output.",
)
@click.pass_obj
def world_chain(obj: dict, concept_id: str, args: tuple[str, ...],
                strategy: str | None,
                include_drafts: bool,
                include_blocked: bool,
                show_quarantined: bool) -> None:
    """Traverse the parameter space to derive a target concept.

    Lifecycle-visibility flags are accepted and layered onto any
    strategy-derived policy per
    ``reviews/2026-04-16-code-review/workstreams/ws-z-render-gates.md``
    (axis-1 findings 3.1 / 3.2 / 3.3).

    Usage: pks world chain concept5 domain=example --strategy sample_size
    """
    from propstore.world.queries import WorldChainRequest, query_world_chain

    # The flags do not change the chain traversal shape today — chain_query
    # reads parameterization + relationship state, not lifecycle-filtered
    # claim sets. The flags are accepted here so users can pipe the same
    # invocation across `pks world ...` subcommands without per-subcommand
    # option divergence; build/render-time policy work already applies at
    # the store layer via ``WorldModel.claims_with_policy``. When a
    # future chain implementation threads a ``RenderPolicy``, this helper
    # remains the construction site.
    _ = _lifecycle_policy(include_drafts, include_blocked, show_quarantined)

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        report = query_world_chain(
            wm,
            WorldChainRequest(
                concept_id=concept_id,
                bindings=bindings,
                strategy=strategy,
            ),
        )

    click.echo(f"Target: {_format_chain_concept(report.target)}")
    click.echo(f"Result: {report.status}")
    if report.value is not None:
        click.echo(f"  value: {report.value}")
    click.echo(f"Steps ({len(report.steps)}):")
    for step in report.steps:
        click.echo(
            f"  {_format_chain_concept(step.concept)}: {step.value} ({step.source})"
        )


@world.command("export-graph")
@click.argument("args", nargs=-1)
@click.option("--format", "fmt", type=click.Choice(["dot", "json"]), default="dot")
@click.option("--group", "group_id", type=int, default=None,
              help="Parameterization group ID to filter by")
@click.option("--output", "output_file", default=None, help="Output file path")
@click.pass_obj
def world_export_graph(obj: dict, args: tuple[str, ...], fmt: str,
                       group_id: int | None, output_file: str | None) -> None:
    """Export the knowledge graph as DOT or JSON.

    Usage: pks world export-graph domain=example --format dot --output graph.dot
    """
    from propstore.graph_export import GraphExportRequest, export_knowledge_graph

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        report = export_knowledge_graph(
            wm,
            GraphExportRequest(bindings=bindings, group_id=group_id),
        )

    if fmt == "json":
        output = json.dumps(report.graph.to_json(), indent=2)
    else:
        output = report.graph.to_dot()

    if output_file:
        Path(output_file).write_text(output)
        click.echo(f"Graph written to {output_file}")
    else:
        click.echo(output)


@world.command("sensitivity")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def world_sensitivity(obj: dict, concept_id: str, args: tuple[str, ...],
                      fmt: str) -> None:
    """Analyze which input most influences a derived quantity.

    Usage: pks world sensitivity concept5 domain=example
    """
    from propstore.sensitivity import SensitivityRequest, query_sensitivity

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        report = query_sensitivity(
            wm,
            SensitivityRequest(concept_id=concept_id, bindings=bindings),
        )
        result = report.result

    if result is None:
        click.echo(f"No sensitivity analysis available for {report.concept_id}.")
        return

    if fmt == "json":
        data = {
            "concept_id": result.concept_id,
            "formula": result.formula,
            "output_value": result.output_value,
            "input_values": result.input_values,
            "entries": [
                {
                    "input_concept_id": e.input_concept_id,
                    "partial_derivative_expr": e.partial_derivative_expr,
                    "partial_derivative_value": e.partial_derivative_value,
                    "elasticity": e.elasticity,
                }
                for e in result.entries
            ],
        }
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(f"Sensitivity: {report.concept_id}")
        click.echo(f"Formula: {result.formula}")
        click.echo(f"Output value: {result.output_value}")
        click.echo(f"Inputs: {result.input_values}")
        click.echo("")
        click.echo(f"{'Input':<25} {'Partial':>12} {'Elasticity':>12}")
        click.echo("-" * 51)
        for e in result.entries:
            pval = f"{e.partial_derivative_value:.6g}" if e.partial_derivative_value is not None else "N/A"
            elast = f"{e.elasticity:.4f}" if e.elasticity is not None else "N/A"
            click.echo(f"{e.input_concept_id:<25} {pval:>12} {elast:>12}")


@world.command("fragility")
@click.argument("args", nargs=-1)
@click.option("--concept", "concept_id", default=None, help="Focus on a single concept")
@click.option("--top-k", "top_k", type=int, default=20, help="Number of results")
@click.option("--skip-atms", is_flag=True, default=False)
@click.option("--skip-discovery", is_flag=True, default=False)
@click.option("--skip-conflict", is_flag=True, default=False)
@click.option("--skip-grounding", is_flag=True, default=False)
@click.option("--skip-bridge", is_flag=True, default=False)
@click.option(
    "--ranking-policy",
    "ranking_policy",
    type=click.Choice(["heuristic_roi", "family_local_only", "pareto"]),
    default="heuristic_roi",
)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def world_fragility(obj: dict, args: tuple[str, ...], concept_id: str | None,
                    top_k: int, skip_atms: bool,
                    skip_discovery: bool, skip_conflict: bool,
                    skip_grounding: bool, skip_bridge: bool,
                    ranking_policy: str, fmt: str) -> None:
    """Rank intervention targets by fragility — what to inspect next."""
    from propstore.fragility import FragilityRequest, query_fragility

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, context_id = _parse_bindings(args)
        report = query_fragility(
            wm,
            FragilityRequest(
                bindings=bindings,
                context_id=context_id,
                concept_id=concept_id,
                top_k=top_k,
                include_atms=not skip_atms,
                include_discovery=not skip_discovery,
                include_conflict=not skip_conflict,
                include_grounding=not skip_grounding,
                include_bridge=not skip_bridge,
                ranking_policy=ranking_policy,
            ),
        )

    if fmt == "json":
        result_dict = {
            "world_fragility": report.world_fragility,
            "analysis_scope": report.analysis_scope,
            "interventions": [
                {
                    "intervention_id": item.target.intervention_id,
                    "kind": item.target.kind,
                    "family": item.target.family,
                    "subject_id": item.target.subject_id,
                    "description": item.target.description,
                    "cost_tier": item.target.cost_tier,
                    "local_fragility": item.local_fragility,
                    "roi": item.roi,
                    "ranking_policy": item.ranking_policy,
                    "score_explanation": item.score_explanation,
                }
                for item in report.interventions
            ],
            "interactions": [asdict(i) for i in report.interactions],
        }
        click.echo(json.dumps(result_dict, indent=2))
    else:
        click.echo(f"Fragility Analysis (top {top_k}, ranking={ranking_policy})")
        click.echo("=" * 60)
        click.echo("")
        click.echo(
            f"{'Rank':>4}  {'Score':>5}  {'ROI':>5}  {'Cost':>4}  {'Family':<10} {'Kind':<20} {'Intervention'}"
        )
        for i, item in enumerate(report.interventions, 1):
            roi = f"{item.roi:.2f}"
            cost = str(item.target.cost_tier)
            click.echo(
                f"{i:>4}  {item.local_fragility:>5.2f}  {roi:>5}  {cost:>4}  "
                f"{item.target.family:<10} {item.target.kind:<20} {item.target.intervention_id}"
            )
        click.echo("")
        click.echo(f"World fragility: {report.world_fragility:.2f}")

        # Display interactions if present
        if report.interactions:
            click.echo("")
            click.echo("Interactions:")
            for inter in report.interactions:
                itype = inter.interaction_type
                a_id = inter.intervention_a_id
                b_id = inter.intervention_b_id
                concepts = inter.subjects_affected
                if itype == "synergistic":
                    desc = "synergistic (neither alone flips, both together flip)"
                elif itype == "redundant":
                    desc = "redundant (both alone flip — learning one suffices)"
                elif itype == "mixed":
                    desc = "mixed (synergistic and redundant for different concepts)"
                elif itype == "independent":
                    desc = "independent"
                else:
                    desc = "unknown (no ATMS data)"
                concept_str = f" for {', '.join(concepts)}" if concepts else ""
                click.echo(f"  {a_id} + {b_id}: {desc}{concept_str}")


@world.command("check-consistency")
@click.argument("args", nargs=-1)
@click.option("--transitive", is_flag=True, help="Check multi-hop transitive conflicts")
@click.pass_obj
def world_check_consistency(obj: dict, args: tuple[str, ...],
                            transitive: bool) -> None:
    """Check for conflicts, optionally including transitive (multi-hop) ones.

    Usage: pks world check-consistency domain=example
           pks world check-consistency --transitive
    """
    from propstore.world.consistency import (
        WorldConsistencyRequest,
        check_world_consistency,
    )

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        report = check_world_consistency(
            repo,
            wm,
            WorldConsistencyRequest(bindings=bindings, transitive=transitive),
        )

    if report.transitive:
        if not report.conflicts:
            click.echo("No transitive conflicts found.")
        else:
            click.echo(f"Found {len(report.conflicts)} transitive conflict(s):")
            for conflict in report.conflicts:
                click.echo(
                    f"  {conflict.concept_id}: "
                    f"{conflict.value_a} vs {conflict.value_b}"
                )
                if conflict.derivation_chain:
                    click.echo(f"    chain: {conflict.derivation_chain}")
        return

    if not report.conflicts:
        click.echo("No conflicts under current bindings.")
    else:
        click.echo(f"Found {len(report.conflicts)} conflict(s):")
        for conflict in report.conflicts:
            click.echo(
                f"  {conflict.concept_id}: {conflict.warning_class} "
                f"({conflict.claim_a_id} vs {conflict.claim_b_id})"
            )

