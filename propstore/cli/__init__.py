"""pks — the propstore CLI.

Single entry point. Subcommand groups registered from sibling modules.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

import click

from propstore.artifacts import MERGE_MANIFEST_FAMILY, MergeManifestRef
from propstore.artifacts.codecs import render_yaml_value
from propstore.cli.concept import concept
from propstore.cli.context import context
from propstore.cli.claim import claim
from propstore.cli.compiler_cmds import validate, build, query, export_aliases, world
from propstore.cli.grounding_cmds import grounding
from propstore.cli.source import source
from propstore.cli.verify import verify
from propstore.cli.worldline_cmds import worldline
from propstore.cli.form import form
from propstore.cli.init import init
from propstore.cli.merge_cmds import merge
from propstore.cli.repository_import_cmd import import_repository_cmd
from propstore.repository import Repository


class _LazyRepository:
    def __init__(self, start: Path | None) -> None:
        self._start = start
        self._repo: Repository | None = None

    def _resolve(self) -> Repository:
        if self._repo is None:
            self._repo = Repository.find(self._start)
        return self._repo

    def __getattr__(self, name: str):
        return getattr(self._resolve(), name)


@click.group()
@click.option("-C", "--directory", default=None, type=click.Path(exists=True),
              help="Run as if pks was started in this directory.")
@click.pass_context
def cli(ctx: click.Context, directory: str | None) -> None:
    """Propositional Knowledge Store CLI."""
    ctx.ensure_object(dict)
    start = Path(directory) if directory else None
    if ctx.resilient_parsing or any(arg in {"--help", "-h"} for arg in sys.argv[1:]):
        return
    if ctx.invoked_subcommand == "init":
        # init bypasses Repository lookup — store the start dir for init to use
        ctx.obj["start"] = start
        return
    ctx.obj["repo"] = _LazyRepository(start)


cli.add_command(concept)
cli.add_command(context)
cli.add_command(claim)
cli.add_command(form)
cli.add_command(source)
cli.add_command(verify)
cli.add_command(validate)
cli.add_command(build)
cli.add_command(query)
cli.add_command(export_aliases)
cli.add_command(init)
cli.add_command(world)
cli.add_command(worldline)
cli.add_command(grounding)
cli.add_command(merge)
cli.add_command(import_repository_cmd)


# ── log command ─────────────────────────────────────────────────────

_LOG_OPERATION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^Initialize knowledge repository$"), "init.repo"),
    (re.compile(r"^Seed default forms$"), "init.forms"),
    (re.compile(r"^Add concept:"), "concept.add"),
    (re.compile(r"^Add alias "), "concept.alias_add"),
    (re.compile(r"^Rename concept:"), "concept.rename"),
    (re.compile(r"^Link "), "concept.link"),
    (re.compile(r"^Add value "), "concept.value_add"),
    (re.compile(r"^Add context:"), "context.add"),
    (re.compile(r"^Add form:"), "form.add"),
    (re.compile(r"^Remove form:"), "form.remove"),
    (re.compile(r"^Import \d+ paper claim file\(s\)$"), "papers.import"),
    (re.compile(r"^Create worldline:"), "worldline.create"),
    (re.compile(r"^Materialize worldline:"), "worldline.materialize"),
    (re.compile(r"^Delete worldline:"), "worldline.delete"),
    (re.compile(r"^Promote \d+ stance proposal file\(s\) from "), "stances.promote"),
    (re.compile(r"^Import .+ at [0-9a-f]{12}$"), "repo.import"),
)


def _classify_log_operation(message: str, parents: list[str]) -> str:
    """Map a commit message to a stable operation label for `pks log`."""
    if len(parents) > 1:
        return "merge.commit"
    for pattern, label in _LOG_OPERATION_PATTERNS:
        if pattern.search(message):
            return label
    return "commit"


def _load_merge_summary(repo: Repository, sha: str) -> dict[str, object] | None:
    manifest = repo.artifacts.load(
        MERGE_MANIFEST_FAMILY,
        MergeManifestRef(),
        commit=sha,
    )
    if manifest is None:
        return None
    merge = manifest.merge
    argument_rows = tuple(merge.arguments)
    materialized_count = sum(1 for row in argument_rows if row.materialized)
    return {
        "branch_a": merge.branch_a,
        "branch_b": merge.branch_b,
        "argument_count": len(argument_rows),
        "materialized_argument_count": materialized_count,
        "semantic_candidate_count": len(merge.semantic_candidate_details),
    }


def _build_log_record(repo: Repository, entry: dict[str, object], *, branch: str, show_files: bool) -> dict[str, object]:
    message = str(entry["message"])
    parents = [str(parent) for parent in entry.get("parents", [])]
    operation = _classify_log_operation(message, parents)
    record: dict[str, object] = {
        "sha": str(entry["sha"]),
        "time": str(entry["time"]),
        "branch": branch,
        "operation": operation,
        "message": message,
        "parents": parents,
    }
    if operation == "merge.commit":
        merge_summary = _load_merge_summary(repo, record["sha"])
        if merge_summary is not None:
            record["merge"] = merge_summary
    if show_files:
        info = repo.snapshot.show_commit(record["sha"])
        record["added"] = list(info.get("added", []))
        record["modified"] = list(info.get("modified", []))
        record["deleted"] = list(info.get("deleted", []))
    return record


def _render_text_log(records: list[dict[str, object]], *, show_files: bool) -> None:
    for record in records:
        sha_short = str(record["sha"])[:8]
        time_str = str(record["time"])
        branch = str(record["branch"])
        operation = str(record["operation"])
        msg_first_line = str(record["message"]).split("\n")[0]
        click.echo(f"  {sha_short}  {time_str}  [{branch}]  {operation:<22}  {msg_first_line}")
        parents = [str(parent) for parent in record.get("parents", [])]
        if len(parents) > 1:
            parent_list = ", ".join(parent[:8] for parent in parents)
            click.echo(f"    parents: {parent_list}")
        merge_summary = record.get("merge")
        if isinstance(merge_summary, dict):
            branch_a = str(merge_summary.get("branch_a", "?"))
            branch_b = str(merge_summary.get("branch_b", "?"))
            argument_count = int(merge_summary.get("argument_count", 0))
            materialized_count = int(merge_summary.get("materialized_argument_count", 0))
            semantic_candidate_count = int(merge_summary.get("semantic_candidate_count", 0))
            click.echo(
                "    merge: "
                f"{branch_a} + {branch_b}; "
                f"materialized={materialized_count}/{argument_count}; "
                f"semantic_candidates={semantic_candidate_count}"
            )
        if not show_files:
            continue
        for path in record.get("added", []):
            click.echo(f"    A {path}")
        for path in record.get("modified", []):
            click.echo(f"    M {path}")
        for path in record.get("deleted", []):
            click.echo(f"    D {path}")


@cli.command("log")
@click.option("-n", "--count", default=20, show_default=True, help="Number of entries to show")
@click.option(
    "--branch",
    "branch_name",
    default=None,
    help="Branch history to inspect. Defaults to the current HEAD branch.",
)
@click.option("--show-files", is_flag=True, help="Show per-commit file changes.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "yaml"]),
    default="text",
    show_default=True,
    help="Render as human-readable text or structured YAML.",
)
@click.pass_context
def log_cmd(ctx, count, branch_name, show_files, output_format):
    """Show knowledge repository history."""
    repo = ctx.obj["repo"]
    snapshot = repo.snapshot
    if branch_name is None:
        branch_name = snapshot.current_branch_name() or snapshot.primary_branch_name()
    if snapshot.branch_head(branch_name) is None:
        raise click.ClickException(f"Branch not found: {branch_name}")
    entries = snapshot.log(max_count=count, branch=branch_name)
    if not entries:
        click.echo("No history yet.")
        return
    records = [
        _build_log_record(repo, entry, branch=branch_name, show_files=show_files)
        for entry in entries
    ]
    if output_format == "yaml":
        payload = {
            "branch": branch_name,
            "entries": records,
        }
        click.echo(render_yaml_value(payload))
        return
    _render_text_log(records, show_files=show_files)


# ── diff command ─────────────────────────────────────────────────────

@cli.command("diff")
@click.argument("commit", required=False, default=None)
@click.pass_context
def diff_cmd(ctx, commit):
    """Show files changed in COMMIT vs its parent (defaults to HEAD)."""
    repo = ctx.obj["repo"]
    result = repo.snapshot.diff(commit1=commit)
    any_changes = False
    for path in result.get("added", []):
        click.echo(f"  Added: {path}")
        any_changes = True
    for path in result.get("modified", []):
        click.echo(f"  Modified: {path}")
        any_changes = True
    for path in result.get("deleted", []):
        click.echo(f"  Deleted: {path}")
        any_changes = True
    if not any_changes:
        click.echo("No changes.")


# ── show command ─────────────────────────────────────────────────────

@cli.command("show")
@click.argument("commit")
@click.pass_context
def show_cmd(ctx, commit):
    """Show details of a specific commit."""
    repo = ctx.obj["repo"]
    try:
        info = repo.snapshot.show_commit(commit)
    except KeyError:
        click.echo(f"Commit not found: {commit}")
        return
    click.echo(f"  Commit: {info['sha'][:8]}")
    click.echo(f"  Author: {info['author']}")
    click.echo(f"  Date: {info['time']}")
    click.echo(f"  Message: {info['message']}")
    click.echo()
    click.echo("  Files:")
    for path in info.get("added", []):
        click.echo(f"    A {path}")
    for path in info.get("modified", []):
        click.echo(f"    M {path}")
    for path in info.get("deleted", []):
        click.echo(f"    D {path}")


# ── checkout command ─────────────────────────────────────────────────

@cli.command("checkout")
@click.argument("commit")
@click.pass_context
def checkout_cmd(ctx, commit):
    """Rebuild the sidecar from a historical commit's tree.

    Leaves git state, working tree, and source YAML untouched, but
    overwrites the on-disk sidecar at ``<repo>/sidecar/propstore.sqlite``
    so that subsequent ``pks world`` / ``pks query`` commands see the
    historical state until the next ``pks build``.
    """
    from propstore.sidecar.build import build_sidecar

    repo = ctx.obj["repo"]

    # Verify commit exists
    try:
        repo.snapshot.show_commit(commit)
    except KeyError:
        click.echo(f"Commit not found: {commit}")
        return

    tree = repo.snapshot.tree(commit=commit)
    if not (tree / "concepts").exists():
        click.echo("No concepts found at that commit.")
        return

    rebuilt = build_sidecar(
        tree, repo.sidecar_path, force=True,
        commit_hash=commit,
    )

    if rebuilt:
        click.echo(f"Sidecar built from commit {commit[:8]}.")
    else:
        click.echo(f"Sidecar already at commit {commit[:8]}.")


# ── promote command ──────────────────────────────────────────────────

@cli.command()
@click.argument("path", required=False, default=None, type=click.Path())
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation prompt.")
@click.pass_context
def promote(ctx: click.Context, path: str | None, yes: bool) -> None:
    """Promote committed stance proposals into source-of-truth storage."""
    from propstore.artifacts import PROPOSAL_STANCE_FAMILY, STANCE_FILE_FAMILY, StanceFileRef
    from propstore.proposals import STANCE_PROPOSAL_BRANCH, stance_proposal_filename

    repo: "Repository" = ctx.obj["repo"]
    target_stances = repo.stances_dir

    proposal_tip = repo.snapshot.branch_head(STANCE_PROPOSAL_BRANCH)
    if proposal_tip is None:
        click.echo(f"No {STANCE_PROPOSAL_BRANCH} branch found. Nothing to promote.")
        return

    available_refs = repo.artifacts.list(PROPOSAL_STANCE_FAMILY, branch=STANCE_PROPOSAL_BRANCH, commit=proposal_tip)
    available_by_name = {
        stance_proposal_filename(ref.source_claim): ref
        for ref in available_refs
    }
    if path is not None:
        requested_name = Path(path).name
        if not requested_name.endswith(".yaml"):
            requested_name = stance_proposal_filename(requested_name)
        selected_refs = [available_by_name[requested_name]] if requested_name in available_by_name else []
    else:
        selected_refs = [available_by_name[name] for name in sorted(available_by_name)]

    if not selected_refs:
        click.echo(f"No stance proposal files found on {STANCE_PROPOSAL_BRANCH}.")
        return

    # Show what will be moved
    for ref in selected_refs:
        name = stance_proposal_filename(ref.source_claim)
        click.echo(f"  {STANCE_PROPOSAL_BRANCH}:stances/{name} -> {target_stances / name}")

    if not yes:
        click.confirm("Promote these files?", abort=True)

    moved = len(selected_refs)
    if moved > 0:
        with repo.artifacts.transact(
            message=f"Promote {moved} stance proposal file(s) from {STANCE_PROPOSAL_BRANCH}",
        ) as transaction:
            for ref in selected_refs:
                transaction.save(
                    STANCE_FILE_FAMILY,
                    StanceFileRef(ref.source_claim),
                    repo.artifacts.require(PROPOSAL_STANCE_FAMILY, ref, commit=proposal_tip),
                )
                click.echo(f"  Promoted: {stance_proposal_filename(ref.source_claim)}")
        repo.snapshot.sync_worktree()

    click.echo(f"\n{moved} file(s) promoted.")
