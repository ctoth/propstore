"""``pks verify`` — canonical claim-tree integrity verification.

A thin Click adapter (CLAUDE.md "CLI adapter discipline") over the read-only
owner auditor :func:`propstore.verify.verify_claim_tree`: ``verify tree`` walks
the charter-derived foreign-key graph at a commit and renders the typed integrity
report. Non-commitment (CLAUDE.md): the auditor reports, it never drops or
collapses; a dangling reference or malformed identity makes the tree not-``ok``
and the command exits non-zero, while quarantined records are surfaced but
excused. No verification logic lives here.
"""

from __future__ import annotations

import click

from propstore.cli.helpers import EXIT_VALIDATION, CliContext, exit_with_code, require_repo
from propstore.cli.output import emit_yaml
from propstore.reporting import json_ready
from propstore.verify import verify_claim_tree


@click.group()
def verify() -> None:
    """Verify canonical semantic artifact trees."""


@verify.command("tree")
@click.option("--commit", default=None, help="Audit the tree as of this commit.")
@click.pass_obj
def verify_tree(obj: CliContext, commit: str | None) -> None:
    """Audit canonical claim-tree foreign-key integrity."""
    repo = require_repo(obj)
    report = verify_claim_tree(repo, commit=commit)
    payload = json_ready(report)
    if isinstance(payload, dict):
        payload = {"ok": report.ok, **payload}
    emit_yaml(payload)
    if not report.ok:
        exit_with_code(EXIT_VALIDATION)
