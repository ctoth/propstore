from __future__ import annotations

import click

from propstore.app.claims import (
    ClaimRelateRequest,
    ClaimSidecarMissingError,
    ClaimWorkflowError,
    relate_claims,
)
from propstore.cli.claim import claim
from propstore.cli.helpers import EXIT_VALIDATION, fail
from propstore.cli.output import emit


@claim.command()
@click.argument("claim_id", required=False, default=None)
@click.option("--all", "relate_all_flag", is_flag=True, help="Relate all claims")
@click.option("--model", required=True, help="LLM model for classification")
@click.option("--embedding-model", default=None, help="Embedding model for similarity")
@click.option("--top-k", default=5, type=int, help="Number of similar claims to classify")
@click.option("--concurrency", default=20, type=int, help="Max concurrent LLM calls")
@click.pass_obj
def relate(
    obj: dict,
    claim_id: str | None,
    relate_all_flag: bool,
    model: str,
    embedding_model: str | None,
    top_k: int,
    concurrency: int,
) -> None:
    """Classify epistemic relationships between similar claims via LLM.

    Uses embedding similarity to pick top-k candidates per claim, then calls
    the LLM to label each (support / rebut / refine / etc.) and commits the
    classifications as stance proposal files to the stance proposal placement branch.
    The main branch is not mutated; promote proposals into source-of-truth
    storage with ``pks proposal promote``.
    """
    if claim_id is not None and relate_all_flag:
        fail("--all cannot be used with a claim ID", exit_code=EXIT_VALIDATION)

    repo = obj["repo"]
    try:
        report = relate_claims(
            repo,
            ClaimRelateRequest(
                claim_id=claim_id,
                relate_all=relate_all_flag,
                model=model,
                embedding_model=embedding_model,
                top_k=top_k,
                concurrency=concurrency,
            ),
            on_progress=lambda done, total: (
                emit(f"  {done}/{total} claims processed", err=True)
                if done % 10 == 0 or done == total
                else None
            ),
        )
    except ClaimSidecarMissingError as exc:
        fail(exc)
    except ClaimWorkflowError as exc:
        fail(exc)

    if claim_id and not relate_all_flag:
        if report.stances:
            for stance in report.stances:
                emit(
                    f"  {str(stance['type']):12s} "
                    f"{str(stance.get('strength', '')):8s} "
                    f"-> {stance['target']}  {stance.get('note', '')}"
                )
            assert report.commit_sha is not None
            emit(
                f"\nCommitted {len(report.relpaths)} proposal file(s) to "
                f"{report.branch} at {report.commit_sha[:8]}"
            )
        else:
            emit("No epistemic relationships found.")
        return

    if relate_all_flag:
        if report.commit_sha is not None:
            emit(
                f"Proposal commit: {report.commit_sha[:8]} on {report.branch} "
                f"({len(report.relpaths)} file(s))"
            )
        emit(
            f"\nProcessed: {report.claims_processed}, "
            f"Stances found: {report.stances_found}, "
            f"No relation: {report.no_relation}"
        )
        return

    fail("provide a claim ID or use --all")
