"""Storage-authoring helpers for the Phase 9-2 two-parent merge-commit tests.

Unlike :mod:`tests.merge_helpers` (which builds plain ``MergeClaim`` sets for the
pure merge math), these author real claims and concepts into a git-backed
:class:`~propstore.repository.Repository` through the families API, so the
``create_merge_commit`` path reads them back out of the branch trees.
"""

from __future__ import annotations

from pathlib import Path

from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.repository import Repository


def init_repo(root: Path) -> Repository:
    return Repository.init(root)


def author_concept(
    repo: Repository,
    concept_id: str,
    *,
    branch: str | None = None,
    name: str | None = None,
) -> str:
    return repo.families.concept.save(
        concept_id,
        Concept(concept_id=concept_id, canonical_name=name or concept_id),
        message=f"author concept {concept_id}",
        branch=branch,
    )


def author_param_claim(
    repo: Repository,
    claim_id: str,
    concept: str,
    value: float,
    *,
    branch: str | None = None,
    unit: str = "K",
    conditions: tuple[str, ...] = (),
) -> str:
    claim = Claim(
        claim_id=claim_id,
        claim_type=ClaimType.PARAMETER,
        output_concept=concept,
        value=value,
        unit=unit,
        conditions=conditions,
    )
    return repo.families.claim.save(
        claim_id, claim, message=f"author claim {claim_id}", branch=branch
    )


def author_obs_claim(
    repo: Repository,
    claim_id: str,
    statement: str,
    *,
    branch: str | None = None,
    conditions: tuple[str, ...] = (),
) -> str:
    """Author a concept-free observation claim (no concept foreign keys)."""

    claim = Claim(
        claim_id=claim_id,
        claim_type=ClaimType.OBSERVATION,
        statement=statement,
        conditions=conditions,
    )
    return repo.families.claim.save(
        claim_id, claim, message=f"author claim {claim_id}", branch=branch
    )
