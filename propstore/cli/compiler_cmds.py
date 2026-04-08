"""pks validate / build / query / export-aliases — top-level compiler commands."""
from __future__ import annotations

import json
import sqlite3
import sys
from collections.abc import Mapping, Sequence
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import click
import yaml

from propstore.cli.helpers import EXIT_VALIDATION, open_world_model
from propstore.cli.repository import Repository
from propstore.identity import (
    primary_logical_id,
)

if TYPE_CHECKING:
    from propstore.core.graph_types import ActiveWorldGraph
    from propstore.world import BoundWorld, QueryableAssumption, RenderPolicy, WorldModel
    from propstore.world.labelled import Label, SupportQuality


def _maybe_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _format_value_with_si(claim: Mapping[str, object]) -> str:
    """Format a claim's value with optional SI normalization.

    Returns e.g. ``value=0.2 kHz (SI: 200.0 Hz)`` when the stored unit
    differs from the canonical SI unit, or ``value=200.0 Hz`` when they match.
    """
    value = claim.get("value")
    unit = claim.get("unit")
    value_si = claim.get("value_si")
    numeric_value = _maybe_float(value)
    numeric_value_si = _maybe_float(value_si)
    if (
        isinstance(unit, str)
        and numeric_value is not None
        and numeric_value_si is not None
        and numeric_value_si != numeric_value
    ):
        return f"value={value} {unit} (SI: {value_si} Hz)"
    if isinstance(unit, str):
        return f"value={value} {unit}"
    return f"value={value}"


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


@click.command()
@click.pass_obj
def validate(obj: dict) -> None:
    """Validate all concepts and claims. Runs CEL type-checking."""
    from propstore.validate import load_concepts, validate_concepts
    from propstore.validate_claims import (
        build_concept_registry,
        load_claim_files,
        validate_claims,
    )

    repo: Repository = obj["repo"]
    tree = repo.tree()
    concepts_root = tree / "concepts"
    if not concepts_root.exists():
        click.echo("No concept files found.")
        return

    concepts = load_concepts(concepts_root)
    if not concepts:
        click.echo("No concept files found.")
        return

    # Validate form schema files
    from propstore.form_utils import validate_form_files

    form_errors = validate_form_files(tree / "forms")
    for e in form_errors:
        click.echo(f"ERROR (form): {e}", err=True)

    concept_result = validate_concepts(
        concepts,
        claims_dir=(tree / "claims") if (tree / "claims").exists() else None,
        forms_dir=tree / "forms",
    )

    for w in concept_result.warnings:
        click.echo(f"WARNING: {w}", err=True)
    for e in concept_result.errors:
        click.echo(f"ERROR: {e}", err=True)

    # Claims (if directory exists)
    claim_error_count = 0
    claim_file_count = 0
    claims_root = tree / "claims"
    if claims_root.exists():
        files = load_claim_files(claims_root)
        claim_file_count = len(files)
        if files:
            registry = build_concept_registry(repo)
            claim_result = validate_claims(files, registry)
            for w in claim_result.warnings:
                click.echo(f"WARNING: {w}", err=True)
            for e in claim_result.errors:
                click.echo(f"ERROR: {e}", err=True)
            claim_error_count = len(claim_result.errors)

    total_errors = len(concept_result.errors) + claim_error_count + len(form_errors)

    if total_errors == 0:
        click.echo(
            f"Validation passed: {len(concepts)} concept(s), "
            f"{claim_file_count} claim file(s)")
    else:
        click.echo(f"Validation FAILED: {total_errors} error(s)", err=True)
        sys.exit(EXIT_VALIDATION)


@click.command()
@click.option("-o", "--output", default=None, help="Output path")
@click.option("--force", is_flag=True, help="Force rebuild")
@click.pass_obj
def build(obj: dict, output: str | None, force: bool) -> None:
    """Validate everything, build sidecar, run conflict detection."""
    from propstore.build_sidecar import build_sidecar
    from propstore.validate import load_concepts, validate_concepts
    from propstore.validate_claims import (
        build_concept_registry,
        load_claim_files,
        validate_claims,
    )

    repo: Repository = obj["repo"]
    git = repo.git
    hash_key = None if git is None else git.head_sha()
    tree = repo.tree(commit=hash_key) if hash_key is not None else repo.tree()

    concepts_root = tree / "concepts"
    if not concepts_root.exists():
        click.echo("No concept files found.")
        return

    concepts = load_concepts(concepts_root)
    if not concepts:
        click.echo("No concept files found.")
        return

    # Step 0: Validate form schema files
    from propstore.form_utils import validate_form_files

    form_errors = validate_form_files(tree / "forms")
    if form_errors:
        for e in form_errors:
            click.echo(f"ERROR (form): {e}", err=True)
        click.echo("Build aborted: form validation failed.", err=True)
        sys.exit(EXIT_VALIDATION)

    # Step 1: Validate concepts
    concept_result = validate_concepts(
        concepts,
        claims_dir=(tree / "claims") if (tree / "claims").exists() else None,
        forms_dir=tree / "forms",
    )
    if not concept_result.ok:
        for e in concept_result.errors:
            click.echo(f"ERROR: {e}", err=True)
        click.echo("Build aborted: concept validation failed.", err=True)
        sys.exit(EXIT_VALIDATION)

    # Step 1b: Load and validate contexts (if any)
    from propstore.validate_contexts import load_contexts, validate_contexts
    context_files = None
    context_ids: set[str] = set()
    if (tree / "contexts").exists():
        ctx_list = load_contexts(tree / "contexts")
        if ctx_list:
            ctx_result = validate_contexts(ctx_list)
            for w in ctx_result.warnings:
                click.echo(f"WARNING (context): {w}", err=True)
            if not ctx_result.ok:
                for e in ctx_result.errors:
                    click.echo(f"ERROR (context): {e}", err=True)
                click.echo("Build aborted: context validation failed.", err=True)
                sys.exit(EXIT_VALIDATION)
            context_files = ctx_list
            context_ids = {c.data["id"] for c in ctx_list if c.data.get("id")}

    # Step 2: Validate claims (if any)
    claim_files = None
    concept_registry = None
    if (tree / "claims").exists():
        files = load_claim_files(tree / "claims")
        if files:
            concept_registry = build_concept_registry(repo)
            claim_result = validate_claims(
                files, concept_registry,
                context_ids=context_ids if context_ids else None,
            )
            if not claim_result.ok:
                for e in claim_result.errors:
                    click.echo(f"ERROR: {e}", err=True)
                click.echo("Build aborted: claim validation failed.", err=True)
                sys.exit(EXIT_VALIDATION)
            claim_files = files

    # Step 3: Build sidecar
    sidecar_path = Path(output) if output else repo.sidecar_path
    rebuilt = build_sidecar(
        tree, sidecar_path, force=force,
        commit_hash=hash_key,
    )

    # Step 4: Summary via WorldModel (proves the roundtrip)
    from propstore.world import WorldModel

    warning_count = len(concept_result.warnings)
    try:
        wm = WorldModel(repo)
        s = wm.stats()
        claim_count = s["claims"]

        conflicts = wm.conflicts()
        # Group PHI_NODEs by concept for compact display;
        # count them separately from real conflicts.
        from collections import defaultdict
        phi_groups: dict[str, set[str]] = defaultdict(set)
        phi_node_count = 0
        real_conflict_count = 0
        for c in conflicts:
            wc = c["warning_class"]
            if wc in ("PHI_NODE", "CONTEXT_PHI_NODE"):
                key = f"{wc}: {c['concept_id']}"
                phi_groups[key].add(c["claim_a_id"])
                phi_groups[key].add(c["claim_b_id"])
                phi_node_count += 1
            else:
                real_conflict_count += 1
                click.echo(
                    f"  {wc}: {c['concept_id']} "
                    f"({c['claim_a_id']} vs {c['claim_b_id']})", err=True)
        for key, claim_ids in phi_groups.items():
            sorted_ids = sorted(claim_ids)
            click.echo(
                f"  {key} — {len(sorted_ids)} branches: "
                f"{', '.join(sorted_ids)}", err=True)
        conflict_count = real_conflict_count
        wm.close()
    except FileNotFoundError:
        # Sidecar didn't get written (no claims?) — fall back to counting
        conflict_count = 0
        phi_node_count = 0
        claim_count = 0
        if claim_files:
            for cf in claim_files:
                claim_count += len(cf.data.get("claims", []))

    status = "rebuilt" if rebuilt else "unchanged"
    click.echo(
        f"Build {status}: {len(concepts)} concepts, {claim_count} claims, "
        f"{conflict_count} conflicts, {phi_node_count} phi-nodes, "
        f"{warning_count} warnings")


@click.command()
@click.argument("sql")
@click.pass_obj
def query(obj: dict, sql: str) -> None:
    """Run raw SQL against the sidecar SQLite."""
    repo: Repository = obj["repo"]
    sidecar = repo.sidecar_path
    if not sidecar.exists():
        click.echo("ERROR: Sidecar not found. Run 'pks build' first.", err=True)
        sys.exit(1)

    conn = sqlite3.connect(sidecar)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    try:
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        if rows:
            # Print header
            keys = rows[0].keys()
            click.echo("\t".join(keys))
            for row in rows:
                click.echo("\t".join(str(row[k]) for k in keys))
        else:
            click.echo("(no results)")
    except sqlite3.Error as e:
        click.echo(f"SQL error: {e}", err=True)
        sys.exit(1)
    finally:
        conn.close()


@click.command("export-aliases")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text",
              help="Output format")
@click.pass_obj
def export_aliases(obj: dict, fmt: str) -> None:
    """Export the alias lookup table."""
    repo: Repository = obj["repo"]
    concepts_root = repo.tree() / "concepts"
    if not concepts_root.exists():
        click.echo("ERROR: No concepts directory.", err=True)
        sys.exit(1)

    from propstore.validate import load_concepts

    concepts = load_concepts(concepts_root)
    aliases: dict[str, dict[str, str]] = {}

    for c in concepts:
        d = c.data
        logical_id = primary_logical_id(d) or d.get("canonical_name", "")
        name = d.get("canonical_name", "")
        for a in d.get("aliases", []) or []:
            alias_name = a.get("name", "")
            if alias_name:
                aliases[alias_name] = {"logical_id": logical_id, "name": name}

    if fmt == "json":
        click.echo(json.dumps(aliases, indent=2))
    else:
        for alias_name, info in sorted(aliases.items()):
            click.echo(f"{alias_name} -> {info['logical_id']} ({info['name']})")


# ── World command group ──────────────────────────────────────────────


@click.group()
@click.pass_obj
def world(obj: dict) -> None:
    """Query the compiled knowledge base."""
    pass


def _resolve_world_target(wm, target: str) -> str:
    """Resolve a world command target by alias, concept ID, or canonical name."""
    return wm.resolve_concept(target) or target


def _world_concept_display_id(wm, concept_id: str) -> str:
    concept = wm.get_concept(concept_id)
    if concept is None:
        return concept_id
    logical_id = concept.get("primary_logical_id")
    if isinstance(logical_id, str) and logical_id:
        return logical_id
    return str(concept.get("id") or concept_id)


def _world_claim_display_id(claim: Mapping[str, object]) -> str:
    logical_id = claim.get("logical_id") or claim.get("primary_logical_id")
    if isinstance(logical_id, str) and logical_id:
        return logical_id
    claim_id = claim.get("id")
    return str(claim_id) if claim_id is not None else "?"


@world.command("status")
@click.pass_obj
def world_status(obj: dict) -> None:
    """Show knowledge base stats (concepts, claims, conflicts)."""
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        s = wm.stats()
        click.echo(f"Concepts: {s['concepts']}")
        click.echo(f"Claims:   {s['claims']}")
        click.echo(f"Conflicts: {s['conflicts']}")


@world.command("query")
@click.argument("concept_id")
@click.pass_obj
def world_query(obj: dict, concept_id: str) -> None:
    """Show all claims for a concept."""
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        resolved = _resolve_world_target(wm, concept_id)
        concept = wm.get_concept(resolved)
        if concept is None:
            click.echo(f"Unknown concept: {concept_id}", err=True)
            sys.exit(1)

        click.echo(f"{concept['canonical_name']} ({_world_concept_display_id(wm, resolved)})")
        claims = wm.claims_for(resolved)
        if not claims:
            click.echo("  (no claims)")
        for c in claims:
            conds = c.get("conditions_cel") or "[]"
            val_part = _format_value_with_si(c)
            click.echo(f"  {_world_claim_display_id(c)}: {c['type']} {val_part} conditions={conds}")


@world.command("bind")
@click.argument("args", nargs=-1)
@click.pass_obj
def world_bind(obj: dict, args: tuple[str, ...]) -> None:
    """Show active claims under condition bindings.

    Usage: pks world bind domain=example [concept_id]

    Arguments with '=' are bindings, the last argument without '=' is a concept filter.
    """
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        # Parse: args with '=' are bindings, last arg without '=' is concept_id
        binding_args = [a for a in args if "=" in a]
        non_binding = [a for a in args if "=" not in a]
        query_concept = non_binding[-1] if non_binding else None

        parsed: dict[str, str] = {}
        for b in binding_args:
            if "=" not in b:
                click.echo(f"Invalid binding: {b} (expected key=value)", err=True)
                sys.exit(1)
            key, _, value = b.partition("=")
            parsed[key] = value

        bound = _bind_world(wm, parsed)

        if query_concept:
            resolved = _resolve_world_target(wm, query_concept)
            result = bound.value_of(resolved)
            click.echo(f"{_world_concept_display_id(wm, resolved)}: {result.status}")
            for c in result.claims:
                val_part = _format_value_with_si(c)
                click.echo(f"  {_world_claim_display_id(c)}: {val_part} source={c.get('source_paper')}")
        else:
            active = bound.active_claims()
            click.echo(f"Active claims: {len(active)}")
            for c in active:
                conds = c.get("conditions_cel") or "[]"
                val_part = _format_value_with_si(c)
                click.echo(
                    f"  {_world_claim_display_id(c)}: {_world_concept_display_id(wm, str(c.get('concept_id', '?')))} "
                    f"{val_part} conditions={conds}")


@world.command("explain")
@click.argument("claim_id")
@click.pass_obj
def world_explain(obj: dict, claim_id: str) -> None:
    """Show the stance chain for a claim."""
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        claim = wm.get_claim(claim_id)
        if claim is None:
            click.echo(f"Unknown claim: {claim_id}", err=True)
            sys.exit(1)

    claim_display_id = _world_claim_display_id(claim)
    click.echo(
        f"{claim_display_id}: {claim['type']} "
        f"concept={_world_concept_display_id(wm, str(claim.get('concept_id')))} "
        f"value={claim.get('value')}"
    )
    chain = wm.explain(claim.get("id") or claim_id)
    if not chain:
        click.echo("  (no stances)")
    for s in chain:
        src = s['claim_id']
        src_claim = wm.get_claim(src)
        src_display_id = _world_claim_display_id(src_claim) if src_claim else src
        tgt_claim = wm.get_claim(s['target_claim_id'])
        tgt_display_id = _world_claim_display_id(tgt_claim) if tgt_claim else s['target_claim_id']
        indent = "  " if src == claim.get("id") else "    "
        click.echo(
            f"{indent}{src_display_id} {s['stance_type']} -> {tgt_display_id}"
            f" (strength={s.get('strength')}, note={s.get('note')})")
    wm.close()


@world.command("algorithms")
@click.option("--stage", default=None, help="Filter by processing stage")
@click.option("--concept", default=None, help="Filter by concept")
@click.pass_obj
def world_algorithms(obj: dict, stage: str | None, concept: str | None) -> None:
    """List algorithm claims in the world model."""
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        # Fetch all algorithm claims
        all_claims = wm.claims_for(None)
        algos = [c for c in all_claims if c.get("type") == "algorithm"]

    if stage:
        algos = [c for c in algos if c.get("stage") == stage]
    if concept:
        algos = [c for c in algos if c.get("concept_id") == concept]

    if not algos:
        click.echo("No algorithm claims found.")
        wm.close()
        return

    # Table header
    click.echo(f"{'ID':<20} {'Name':<30} {'Stage':<15} {'Concept(s)'}")
    click.echo("-" * 80)
    for a in algos:
        aid = a.get("id", "?")
        name = a.get("name") or a.get("body", "")[:25] or "?"
        a_stage = a.get("stage") or "-"
        a_concept = a.get("concept_id") or "-"
        click.echo(f"{aid:<20} {name:<30} {a_stage:<15} {a_concept}")

    click.echo(f"\n{len(algos)} algorithm claim(s).")
    wm.close()


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


def _emit_revision_explanation(explanation: dict) -> None:
    click.echo(f"Accepted ({len(explanation['accepted_atom_ids'])} atoms):")
    for atom_id in explanation["accepted_atom_ids"]:
        click.echo(f"  {atom_id}")

    click.echo(f"Rejected ({len(explanation['rejected_atom_ids'])} atoms):")
    for atom_id in explanation["rejected_atom_ids"]:
        click.echo(f"  {atom_id}")

    incision = explanation["incision_set"]
    click.echo(f"Incision set: {', '.join(incision) if incision else '(none)'}")
    click.echo("Atoms:")
    for atom_id, detail in explanation["atoms"].items():
        line = f"  {atom_id}: status={detail['status']} reason={detail['reason']}"
        ranking = detail.get("ranking")
        if isinstance(ranking, dict):
            line += f" support_count={ranking.get('support_count', 0)}"
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
@click.pass_obj
def world_revision_base(obj: dict, args: tuple[str, ...]) -> None:
    """Show the current revision-facing belief base for a scoped world."""
    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings)
        base = bound.revision_base()

        click.echo(f"Revision base ({len(base.atoms)} atoms, {len(base.assumptions)} assumptions)")
        for atom in base.atoms:
            payload = dict(atom.payload)
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
@click.pass_obj
def world_revision_entrenchment(obj: dict, args: tuple[str, ...]) -> None:
    """Show the current deterministic entrenchment ordering for a scoped world."""
    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings)
        report = bound.revision_entrenchment()

        click.echo(f"Entrenchment ({len(report.ranked_atom_ids)} atoms)")
        for rank, atom_id in enumerate(report.ranked_atom_ids, start=1):
            reason = report.reasons.get(atom_id, {})
            support_count = reason.get("support_count", 0)
            essential_support = reason.get("essential_support") or []
            override = reason.get("override")
            click.echo(
                f"  {rank}. {atom_id} "
                f"support_count={support_count} "
                f"essential_support={_format_assumption_ids(essential_support)} "
                f"override={override}"
            )


@world.command("expand")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to add")
@click.pass_obj
def world_expand(obj: dict, args: tuple[str, ...], atom_json: str) -> None:
    """Expand the scoped revision belief base without mutating source YAML."""
    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings)
        result = bound.expand(_parse_revision_atom_json(atom_json))
        _emit_revision_result(result)


@world.command("contract")
@click.argument("args", nargs=-1)
@click.option("--target", "targets", multiple=True, required=True, help="Existing atom or claim id to contract")
@click.pass_obj
def world_contract(obj: dict, args: tuple[str, ...], targets: tuple[str, ...]) -> None:
    """Contract the scoped revision belief base without mutating source YAML."""
    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings)
        result = bound.contract(_contract_target_arg(targets))
        _emit_revision_result(result)


@world.command("revise")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to admit")
@click.option("--conflict", "conflicts", multiple=True, help="Existing atom or claim id that conflicts with the new atom")
@click.pass_obj
def world_revise(obj: dict, args: tuple[str, ...], atom_json: str, conflicts: tuple[str, ...]) -> None:
    """Revise the scoped belief base without mutating source YAML."""
    from propstore.revision.operators import normalize_revision_input

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings)
        atom = _parse_revision_atom_json(atom_json)
        base = bound.revision_base()
        normalized = normalize_revision_input(base, atom)
        conflict_map = {normalized.atom_id: tuple(conflicts)} if conflicts else None
        result = bound.revise(atom, conflicts=conflict_map)
        _emit_revision_result(result)


@world.command("revision-explain")
@click.argument("args", nargs=-1)
@click.option("--operation", type=click.Choice(["expand", "contract", "revise"]), required=True)
@click.option("--atom", "atom_json", default=None, help="JSON revision atom for expand/revise")
@click.option("--target", "targets", multiple=True, help="Existing atom or claim id for contract")
@click.option("--conflict", "conflicts", multiple=True, help="Existing atom or claim id that conflicts with the new atom")
@click.pass_obj
def world_revision_explain(
    obj: dict,
    args: tuple[str, ...],
    operation: str,
    atom_json: str | None,
    targets: tuple[str, ...],
    conflicts: tuple[str, ...],
) -> None:
    """Explain one revision operation over the current scoped world."""
    from propstore.revision.operators import normalize_revision_input

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings)

        if operation == "expand":
            if atom_json is None:
                raise click.ClickException("--atom is required for --operation expand")
            result = bound.expand(_parse_revision_atom_json(atom_json))
        elif operation == "contract":
            if not targets:
                raise click.ClickException("--target is required for --operation contract")
            result = bound.contract(_contract_target_arg(targets))
        else:
            if atom_json is None:
                raise click.ClickException("--atom is required for --operation revise")
            atom = _parse_revision_atom_json(atom_json)
            base = bound.revision_base()
            normalized = normalize_revision_input(base, atom)
            conflict_map = {normalized.atom_id: tuple(conflicts)} if conflicts else None
            result = bound.revise(atom, conflicts=conflict_map)

        explanation = bound.revision_explain(result)
        _emit_revision_explanation(explanation)


@world.command("iterated-state")
@click.argument("args", nargs=-1)
@click.pass_obj
def world_iterated_state(obj: dict, args: tuple[str, ...]) -> None:
    """Inspect the current explicit iterated revision state for a scoped world."""
    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings)
        state = bound.epistemic_state()
        _emit_epistemic_state(state)


@world.command("iterated-revise")
@click.argument("args", nargs=-1)
@click.option("--atom", "atom_json", required=True, help="JSON revision atom to admit")
@click.option("--conflict", "conflicts", multiple=True, help="Existing atom or claim id that conflicts with the new atom")
@click.option("--operator", type=click.Choice(["restrained", "lexicographic"]), default="restrained")
@click.pass_obj
def world_iterated_revise(
    obj: dict,
    args: tuple[str, ...],
    atom_json: str,
    conflicts: tuple[str, ...],
    operator: str,
) -> None:
    """Run one iterated revision episode and print the next explicit state."""
    from propstore.revision.operators import normalize_revision_input

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings)
        atom = _parse_revision_atom_json(atom_json)
        state = bound.epistemic_state()
        normalized = normalize_revision_input(state.base, atom)
        conflict_map = {normalized.atom_id: tuple(conflicts)} if conflicts else None
        result, next_state = bound.iterated_revise(
            atom,
            conflicts=conflict_map,
            operator=operator,
            state=state,
        )
        _emit_iterated_revision(result, state, next_state, operator=operator)


def _bind_atms_world(
    repo: Repository,
    args: tuple[str, ...],
    *,
    context: str | None = None,
):
    from propstore.world import ReasoningBackend, RenderPolicy, WorldModel

    wm = WorldModel(repo)
    bindings, concept_id = _parse_bindings(args)
    policy = RenderPolicy(reasoning_backend=ReasoningBackend.ATMS)
    bound = _bind_world(wm, bindings, context_id=context, policy=policy)
    return wm, bound, bindings, concept_id


def _format_assumption_ids(assumption_ids: Sequence[str]) -> str:
    if not assumption_ids:
        return "[]"
    return "[" + ", ".join(str(assumption_id) for assumption_id in assumption_ids) + "]"


def _parse_queryables(
    queryables: tuple[str, ...],
) -> list[QueryableAssumption]:
    from propstore.world.types import coerce_queryable_assumptions

    return list(coerce_queryable_assumptions(queryables))


def _contract_target_arg(targets: tuple[str, ...]) -> str | tuple[str, ...]:
    if len(targets) == 1:
        return targets[0]
    return targets


def _format_status_value(status: object) -> str:
    if isinstance(status, str):
        return status
    if isinstance(status, Enum):
        return str(status.value)
    return str(status)


def _support_metadata_for(
    bound: object,
    active_claims: Sequence[dict[str, Any]],
) -> dict[str, tuple[Label | None, SupportQuality]]:
    from propstore.world.types import ClaimSupportView

    if not isinstance(bound, ClaimSupportView):
        return {}

    support_metadata: dict[str, tuple[Label | None, SupportQuality]] = {}
    for claim in active_claims:
        claim_id = claim.get("id")
        if isinstance(claim_id, str) and claim_id:
            support_metadata[claim_id] = bound.claim_support(claim)
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
    wm, bound, _bindings, concept_id = _bind_atms_world(repo, args, context=context)

    resolved = None
    if concept_id:
        resolved = _resolve_world_target(wm, concept_id)
    active_claims = sorted(bound.active_claims(resolved), key=lambda claim: claim["id"])
    if not active_claims:
        click.echo("No active claims for the current ATMS view.")
        wm.close()
        return

    for claim in active_claims:
        inspection = bound.claim_status(claim["id"])
        click.echo(
            f"{claim['id']}: status={inspection.status.value} "
            f"support_quality={inspection.support_quality.value} "
            f"essential_support={_format_assumption_ids(inspection.essential_support.assumption_ids if inspection.essential_support else ())}"
        )
        click.echo(f"  reason: {inspection.reason}")

    wm.close()


@world.command("atms-context")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_context(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Show which ATMS-supported claims hold in the current bound environment."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, concept_id = _bind_atms_world(repo, args, context=context)

    environment_key = tuple(
        assumption.assumption_id
        for assumption in bound._environment.assumptions
    )
    click.echo(f"Environment: {_format_assumption_ids(environment_key)}")

    claim_ids = bound.claims_in_environment(environment_key)
    if concept_id:
        resolved = _resolve_world_target(wm, concept_id)
        allowed = {
            claim["id"]
            for claim in bound.active_claims(resolved)
        }
        claim_ids = [claim_id for claim_id in claim_ids if claim_id in allowed]

    if not claim_ids:
        click.echo("No claims have exact ATMS support in the current environment.")
        wm.close()
        return

    for claim_id in sorted(claim_ids):
        inspection = bound.claim_status(claim_id)
        click.echo(
            f"{claim_id}: status={inspection.status.value} "
            f"essential_support={_format_assumption_ids(inspection.essential_support.assumption_ids if inspection.essential_support else ())}"
        )

    wm.close()


@world.command("atms-verify")
@click.argument("args", nargs=-1)
@click.option("--context", default=None, help="Context to scope the ATMS inspection")
@click.pass_obj
def world_atms_verify(obj: dict, args: tuple[str, ...], context: str | None) -> None:
    """Run ATMS label self-checks for the current bound environment."""
    repo: Repository = obj["repo"]
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    report = bound.atms_engine().verify_labels()
    if report["ok"]:
        click.echo("ATMS labels verified.")
        wm.close()
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

    wm.close()
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
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

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
        wm.close()
        return

    resolved = _resolve_world_target(wm, target)
    concept_report = bound.concept_future_statuses(resolved, parsed_queryables, limit=limit)
    if not concept_report:
        click.echo("No active claims for the requested ATMS future view.")
        wm.close()
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
    wm.close()


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
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

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
        wm.close()
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
    wm.close()


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
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

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
        wm.close()
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
    wm.close()


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
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

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
        wm.close()
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
    wm.close()


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
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    parsed_queryables = _parse_queryables(queryables)
    click.echo("bounded additive plans over declared queryables")
    click.echo("not revision/contraction")

    claim = wm.get_claim(target)
    if claim is not None:
        plans = bound.claim_interventions(target, parsed_queryables, target_status, limit=limit)
        for plan in plans:
            status_val = _format_status_value(plan["result_status"])
            click.echo(
                f"  plan [{', '.join(plan['queryable_cels'])}] -> {status_val}"
            )
        wm.close()
        return

    resolved = _resolve_world_target(wm, target)
    plans = bound.concept_interventions(resolved, parsed_queryables, target_status, limit=limit)
    for plan in plans:
        status_val = _format_status_value(plan["result_status"])
        click.echo(
            f"  plan [{', '.join(plan['queryable_cels'])}] -> {status_val}"
        )
    wm.close()


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
    wm, bound, _bindings, _concept_id = _bind_atms_world(repo, args, context=context)

    parsed_queryables = _parse_queryables(queryables)
    click.echo("derived from bounded additive intervention plans")

    claim = wm.get_claim(target)
    if claim is not None:
        suggestions = bound.claim_next_queryables(target, parsed_queryables, target_status, limit=limit)
        for suggestion in suggestions:
            click.echo(
                f"  {suggestion['queryable_cel']}: "
                f"coverage={suggestion['plan_count']} "
                f"smallest_plan_size={suggestion['smallest_plan_size']}"
            )
        wm.close()
        return

    resolved = _resolve_world_target(wm, target)
    suggestions = bound.concept_next_queryables(resolved, parsed_queryables, target_status, limit=limit)
    for suggestion in suggestions:
        click.echo(
            f"  {suggestion['queryable_cel']}: "
            f"coverage={suggestion['plan_count']} "
            f"smallest_plan_size={suggestion['smallest_plan_size']}"
        )
    wm.close()


@world.command("derive")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.pass_obj
def world_derive(obj: dict, concept_id: str, args: tuple[str, ...]) -> None:
    """Derive a value for a concept via parameterization relationships.

    Usage: pks world derive concept5 domain=example
    """
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        resolved = _resolve_world_target(wm, concept_id)
        bound = _bind_world(wm, bindings)
        result = bound.derived_value(resolved)

    click.echo(f"{resolved}: {result.status}")
    if result.value is not None:
        click.echo(f"  value: {result.value}")
    if result.formula:
        click.echo(f"  formula: {result.formula}")
    if result.input_values:
        click.echo(f"  inputs: {result.input_values}")
    if result.exactness:
        click.echo(f"  exactness: {result.exactness}")
    wm.close()


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
                  praf_seed: int | None) -> None:
    """Resolve a conflicted concept using a strategy.

    Usage: pks world resolve concept1 domain=example --strategy argumentation
    """
    from propstore.world import (
        ReasoningBackend,
        RenderPolicy,
        ResolutionStrategy,
        WorldModel,
        resolve,
    )
    from propstore.world.types import normalize_argumentation_semantics

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        resolved = _resolve_world_target(wm, concept_id)
        bound = _bind_world(wm, bindings)
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
            overrides=overrides_dict or {},
        )

        try:
            result = resolve(
                bound, resolved, policy=policy, world=wm,
            )
        except (ValueError, NotImplementedError) as e:
            click.echo(f"ERROR: {e}", err=True)
            sys.exit(1)

        click.echo(f"{_world_concept_display_id(wm, resolved)}: {result.status}")
        if result.value is not None:
            click.echo(f"  value: {result.value}")
        if result.winning_claim_id:
            winning_claim = wm.get_claim(result.winning_claim_id)
            winner_id = _world_claim_display_id(winning_claim) if winning_claim else result.winning_claim_id
            click.echo(f"  winner: {winner_id}")
        if result.strategy:
            click.echo(f"  strategy: {result.strategy}")
        if result.reason:
            click.echo(f"  reason: {result.reason}")
        if result.acceptance_probs:
            click.echo("  acceptance_probs:")
            for cid, prob in sorted(result.acceptance_probs.items()):
                click.echo(f"    {cid}: {prob:.4f}")


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
    from propstore.argumentation import stance_summary
    from propstore.world import ReasoningBackend, WorldModel
    from propstore.world.types import normalize_reasoning_backend

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings, context_id=context)
        active = bound.active_claims()
        if not active:
            click.echo("No active claims for given bindings.")
            return

        claim_ids = {c["id"] for c in active}
        backend = normalize_reasoning_backend(backend_name)

        if backend == ReasoningBackend.ATMS:
            click.echo(
                "ERROR: backend 'atms' does not expose Dung extensions; "
                "use worldline or resolve with reasoning_backend=atms instead.",
                err=True,
            )
            sys.exit(2)

        if backend == ReasoningBackend.PRAF:
            from propstore.argumentation import build_praf
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
            claim_map = {c["id"]: c for c in active}
            acceptance_probs = praf_result.acceptance_probs or {}
            for cid, prob in sorted(
                acceptance_probs.items(),
                key=lambda x: -x[1],
            ):
                c = claim_map.get(cid)
                label = cid
                if c:
                    value = c.get("value")
                    concept_id_val = c.get("concept_id")
                    if concept_id_val:
                        concept = wm.get_concept(concept_id_val)
                        cname = concept.get("canonical_name", concept_id_val) if concept else concept_id_val
                        if value is not None:
                            label = f"{cid}: {cname} = {value}"
                        else:
                            label = f"{cid}: {cname}"
                click.echo(f"  {label}  P(accepted) = {prob:.4f}")
            return

        if backend == ReasoningBackend.CLAIM_GRAPH:
            from propstore.argumentation import (
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
            from propstore.structured_argument import (
                build_structured_projection,
                compute_structured_justified_arguments,
            )

            aspic_projection = build_structured_projection(
                wm,
                active,
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

        claim_map = {c["id"]: c for c in active}

        def _claim_label(cid: str) -> str:
            """Format a claim for display: id (type) concept = value."""
            c = claim_map.get(cid)
            if c is None:
                return cid
            ctype = c.get("type", "?")
            concept_id = c.get("concept_id")
            value = c.get("value")
            cname = None
            if concept_id:
                concept = wm.get_concept(concept_id)
                if concept:
                    cname = concept.get("canonical_name", concept_id)
            if ctype == "parameter" and value is not None:
                return f"{cid}: {cname} = {value}"
            if ctype == "equation":
                expr = c.get("expression", "")
                return f"{cid}: {expr}" if expr else f"{cid} ({ctype})"
            if ctype in ("observation", "limitation", "mechanism", "comparison"):
                stmt = c.get("statement") or c.get("description") or ""
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
                ctype = c.get("type", "unknown") if c else "unknown"
                groups.setdefault(ctype, []).append(cid)
            return groups

        if semantics == "grounded":
            if backend == ReasoningBackend.ASPIC:
                assert isinstance(result, frozenset)
                justified_claims = {arg_to_claim[arg_id] for arg_id in result}
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
                    {arg_to_claim[arg_id] for arg_id in ext}
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
    from propstore.core.id_types import to_concept_id
    from propstore.world import HypotheticalWorld, SyntheticClaim, WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings)
        synthetics: list[SyntheticClaim] = []
        if add_json:
            data = json.loads(add_json)
            if isinstance(data, dict):
                data = [data]
            for d in data:
                synthetics.append(SyntheticClaim(
                    id=d["id"],
                    concept_id=to_concept_id(d["concept_id"]),
                    type=d.get("type", "parameter"),
                    value=d.get("value"),
                    conditions=d.get("conditions", []),
                ))

        resolved_remove = [wm.resolve_claim(claim_id) or claim_id for claim_id in remove]
        hypo = HypotheticalWorld(bound, remove=resolved_remove, add=synthetics)
        diff = hypo.diff()

        if not diff:
            click.echo("No changes detected.")
        else:
            for cid, (base_vr, hypo_vr) in diff.items():
                click.echo(f"{_world_concept_display_id(wm, cid)}: {base_vr.status} → {hypo_vr.status}")


@world.command("chain")
@click.argument("concept_id")
@click.argument("args", nargs=-1)
@click.option("--strategy", default=None,
              type=click.Choice(["recency", "sample_size", "argumentation", "override"]))
@click.pass_obj
def world_chain(obj: dict, concept_id: str, args: tuple[str, ...],
                strategy: str | None) -> None:
    """Traverse the parameter space to derive a target concept.

    Usage: pks world chain concept5 domain=example --strategy sample_size
    """
    from propstore.world import ResolutionStrategy, WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        resolved = _resolve_world_target(wm, concept_id)
        strat = ResolutionStrategy(strategy) if strategy else None
        result = wm.chain_query(resolved, strategy=strat, **bindings)

        def _label(cid: str) -> str:
            """Return 'conceptN (canonical_name)' or just the id if no name."""
            c = wm.get_concept(cid)
            name = c.get("canonical_name", "") if c else ""
            display_id = _world_concept_display_id(wm, cid)
            return f"{display_id} ({name})" if name else display_id

        click.echo(f"Target: {_label(resolved)}")
        click.echo(f"Result: {result.result.status}")
        from propstore.world import DerivedResult
        if isinstance(result.result, DerivedResult) and result.result.value is not None:
            click.echo(f"  value: {result.result.value}")
        click.echo(f"Steps ({len(result.steps)}):")
        for step in result.steps:
            click.echo(f"  {_label(step.concept_id)}: {step.value} ({step.source})")


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
    from propstore.graph_export import build_knowledge_graph
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        bound = _bind_world(wm, bindings) if bindings else None
        graph = build_knowledge_graph(wm, bound=bound, group_id=group_id)

        if fmt == "json":
            output = json.dumps(graph.to_json(), indent=2)
        else:
            output = graph.to_dot()

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
    from propstore.sensitivity import analyze_sensitivity
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        resolved = _resolve_world_target(wm, concept_id)
        bound = _bind_world(wm, bindings)
        result = analyze_sensitivity(wm, resolved, bound)

        if result is None:
            click.echo(f"No sensitivity analysis available for {resolved}.")
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
            click.echo(f"Sensitivity: {resolved}")
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
@click.option("--combination", type=click.Choice(["top2", "mean", "max", "product"]), default="top2")
@click.option("--skip-parametric", is_flag=True, default=False)
@click.option("--skip-epistemic", is_flag=True, default=False)
@click.option("--skip-conflict", is_flag=True, default=False)
@click.option("--sort-by", "sort_by", type=click.Choice(["fragility", "roi"]), default="fragility")
@click.option("--discovery-tier", "discovery_tier", type=int, default=1, help="1=ATMS only, 2=also unknown concepts")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_obj
def world_fragility(obj: dict, args: tuple[str, ...], concept_id: str | None,
                    top_k: int, combination: str, skip_parametric: bool,
                    skip_epistemic: bool, skip_conflict: bool,
                    sort_by: str, discovery_tier: int, fmt: str) -> None:
    """Rank epistemic targets by fragility — what to learn next."""
    from propstore.fragility import rank_fragility

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, context_id = _parse_bindings(args)
        bound = _bind_world(wm, bindings, context_id=context_id)

        report = rank_fragility(
            bound,
            concept_id=concept_id,
            top_k=top_k,
            include_parametric=not skip_parametric,
            include_epistemic=not skip_epistemic,
            include_conflict=not skip_conflict,
            combination=combination,
            sort_by=sort_by,
            discovery_tier=discovery_tier,
        )

        if fmt == "json":
            result_dict = {
                "world_fragility": report.world_fragility,
                "analysis_scope": report.analysis_scope,
                "targets": [
                    {
                        "target_id": t.target_id,
                        "target_kind": t.target_kind,
                        "description": t.description,
                        "fragility": t.fragility,
                        "parametric_score": t.parametric_score,
                        "epistemic_score": t.epistemic_score,
                        "conflict_score": t.conflict_score,
                        "cost_tier": t.cost_tier,
                        "epistemic_roi": t.epistemic_roi,
                    }
                    for t in report.targets
                ],
                "interactions": [dict(i) for i in report.interactions],
            }
            click.echo(json.dumps(result_dict, indent=2))
        else:
            click.echo(f"Fragility Analysis (top {top_k}, combination={combination}, sort={sort_by})")
            click.echo("=" * 60)
            click.echo("")
            click.echo(
                f"{'Rank':>4}  {'Score':>5}  {'ROI':>5}  {'Cost':>4}  {'Kind':<12} {'Target'}"
            )
            for i, t in enumerate(report.targets, 1):
                roi = f"{t.epistemic_roi:.2f}" if t.epistemic_roi is not None else "  -  "
                cost = str(t.cost_tier) if t.cost_tier is not None else "-"
                click.echo(
                    f"{i:>4}  {t.fragility:>5.2f}  {roi:>5}  {cost:>4}  {t.target_kind:<12} "
                    f"{t.target_id}"
                )
            click.echo("")
            click.echo(f"World fragility: {report.world_fragility:.2f}")

            # Display interactions if present
            if report.interactions:
                click.echo("")
                click.echo("Interactions:")
                for inter in report.interactions:
                    itype = inter.get("interaction_type", "unknown")
                    a_id = inter.get("target_a_id", "?")
                    b_id = inter.get("target_b_id", "?")
                    concepts = inter.get("concepts_affected", [])
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
    from propstore.world import WorldModel

    repo: Repository = obj["repo"]
    with open_world_model(repo) as wm:
        bindings, _ = _parse_bindings(args)
        if transitive:
            from propstore.conflict_detector import detect_transitive_conflicts
            from propstore.validate_claims import load_claim_files

            claim_files = load_claim_files(repo.tree() / "claims")
            concept_registry: dict[str, dict] = {}
            for cdata in wm.all_concepts():
                cdata = dict(cdata)
                cid = cdata["id"]
                param_rows = wm.parameterizations_for(cid)
                if param_rows:
                    cdata["parameterization_relationships"] = []
                    for pr in param_rows:
                        prd = dict(pr)
                        cdata["parameterization_relationships"].append({
                            "inputs": json.loads(prd["concept_ids"]),
                            "sympy": prd.get("sympy"),
                            "exactness": prd.get("exactness"),
                            "conditions": json.loads(prd["conditions_cel"]) if prd.get("conditions_cel") else [],
                        })
                concept_registry[cid] = cdata

            records = detect_transitive_conflicts(claim_files, concept_registry)
            if not records:
                click.echo("No transitive conflicts found.")
            else:
                click.echo(f"Found {len(records)} transitive conflict(s):")
                for r in records:
                    click.echo(f"  {r.concept_id}: {r.value_a} vs {r.value_b}")
                    if r.derivation_chain:
                        click.echo(f"    chain: {r.derivation_chain}")
        else:
            bound = _bind_world(wm, bindings)
            conflicts = bound.conflicts()
            if not conflicts:
                click.echo("No conflicts under current bindings.")
            else:
                click.echo(f"Found {len(conflicts)} conflict(s):")
                for c in conflicts:
                    click.echo(
                        f"  {c['concept_id']}: {c.get('warning_class', '?')} "
                        f"({c['claim_a_id']} vs {c['claim_b_id']})"
                    )
