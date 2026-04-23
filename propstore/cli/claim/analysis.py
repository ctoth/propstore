from __future__ import annotations

import click

from propstore.app.claims import (
    ClaimCompareRequest,
    ClaimComparisonError,
    ClaimSidecarMissingError,
    UnknownClaimError,
    compare_algorithm_claims_from_repo,
)
from propstore.cli.claim import claim
from propstore.cli.helpers import fail
from propstore.cli.output import emit, emit_warning
from propstore.repository import Repository


@claim.command()
@click.argument("id_a")
@click.argument("id_b")
@click.option("--bindings", "-b", multiple=True, help="Known values as key=value pairs")
@click.pass_obj
def compare(obj: dict, id_a: str, id_b: str, bindings: tuple[str, ...]) -> None:
    """Compare two algorithm claims for equivalence."""
    repo: Repository = obj["repo"]

    known_values: dict[str, float] | None = None
    if bindings:
        known_values = {}
        for binding in bindings:
            key, _, value = binding.partition("=")
            try:
                known_values[key] = float(value)
            except ValueError:
                emit_warning(f"WARNING: Ignoring non-numeric binding: {binding}")

    try:
        result = compare_algorithm_claims_from_repo(
            repo,
            ClaimCompareRequest(id_a, id_b, known_values or None),
        )
    except ClaimSidecarMissingError as exc:
        fail(exc)
    except UnknownClaimError as exc:
        fail(f"Claim '{exc.claim_id}' not found.")
    except ClaimComparisonError as exc:
        fail(exc)

    emit(f"Tier:       {result.tier}")
    emit(f"Equivalent: {result.equivalent}")
    emit(f"Similarity: {result.similarity:.4f}")
    if result.details:
        emit(f"Details:    {result.details}")
