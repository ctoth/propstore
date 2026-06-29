"""Plain claim-set helpers for Phase 6c merge-math tests.

The merge math takes plain per-branch claim sets, so these build
:class:`~propstore.merge.MergeClaim` values directly over the one canonical
:class:`~propstore.families.claims.Claim` — no git store, no ``Repository`` snapshot
(those land in Phase 9). Provenance (paper/page) is carried alongside the claim
because the rewrite charter is provenance-free.
"""

from __future__ import annotations

from propstore.families.claims import Claim, ClaimType
from propstore.merge import MergeClaim


def obs_claim(
    cid: str,
    statement: str,
    concepts: list[str],
    *,
    paper: str = "test_paper",
    page: int = 1,
    conditions: list[str] | None = None,
) -> MergeClaim:
    claim = Claim(
        claim_id=cid,
        claim_type=ClaimType.OBSERVATION,
        statement=statement,
        concepts=tuple(concepts),
        conditions=tuple(conditions or ()),
    )
    merge_claim = MergeClaim.from_claim(claim, paper=paper, page=page)
    if merge_claim is None:
        raise AssertionError("claim did not normalize to a merge claim")
    return merge_claim


def param_claim(
    cid: str,
    concept: str,
    value: float,
    *,
    paper: str = "test_paper",
    page: int = 1,
    conditions: list[str] | None = None,
) -> MergeClaim:
    claim = Claim(
        claim_id=cid,
        claim_type=ClaimType.PARAMETER,
        output_concept=concept,
        value=value,
        unit="K",
        conditions=tuple(conditions or ()),
    )
    merge_claim = MergeClaim.from_claim(claim, paper=paper, page=page)
    if merge_claim is None:
        raise AssertionError("claim did not normalize to a merge claim")
    return merge_claim
