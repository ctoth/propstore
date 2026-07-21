"""Branch-local structured projection and structured merge candidates.

A branch's claims and stances are projected — store-free — into a single Dung
framework: each branch's claims become ASPIC+ literals, its stances become
contrariness, and :func:`propstore.aspic_bridge.build_bridge_csaf` runs the kernel.
:func:`build_structured_merge_candidates` then merges the per-branch frameworks with
the argumentation package's sum/max/leximax AF-merge operators (CLAUDE.md substrate
boundary: those operators are the package's own, used directly).

This is the structured-merge MATH over plain claim/stance inputs: callers pass the
per-branch claim and stance sets directly. The store-reading half (reading a branch's
claims and stances out of git) lands with the ``Repository`` facade in Phase 9.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from argumentation.core.dung import ArgumentationFramework
from argumentation.frameworks.af_merging import (
    leximax_merge_frameworks,
    max_merge_frameworks,
    sum_merge_frameworks,
)
from argumentation.frameworks.partial_af import EnumerationExceeded

from propstore.aspic_bridge import build_bridge_csaf, csaf_to_projection
from propstore.aspic_bridge.translate import StanceInput
from propstore.core.active_claims import ActiveClaim
from propstore.core.justifications import CanonicalJustification
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.merge.merge_claims import MergeClaim
from propstore.stances import StanceType
from propstore.structured_projection import (
    StructuredProjection,
    compute_structured_justified_arguments,
)


@dataclass(frozen=True)
class BranchArgumentationEvidence:
    branch: str
    backend: str
    semantics: str
    accepted_assertion_ids: tuple[str, ...]
    witness_assertion_ids: tuple[str, ...]
    skeptical_assertion_ids: tuple[str, ...] = ()
    decision_owner: str = "merge_policy"


@dataclass(frozen=True)
class MergeStanceRow:
    """A scoped, deterministic stance row used for branch-summary identity."""

    claim_id: str
    target_claim_id: str
    stance_type: StanceType
    target_justification_id: str | None = None


@dataclass(frozen=True)
class BranchStructuredSummary:
    branch: str
    assertion_ids: tuple[str, ...]
    claim_provenance: dict[str, dict[str, object]]
    content_signature: str
    relation_surface: dict[str, str]
    lossiness: tuple[str, ...]
    active_claims: tuple[MergeClaim, ...]
    stance_rows: tuple[MergeStanceRow, ...]
    projection: StructuredProjection
    decision_owner: str = "merge_policy"


_RELATION_SURFACE = {
    "attack": "preserved_via_projection",
    "non_attack": "not_preserved_in_summary",
    "ignorance": "not_preserved_in_summary",
}
_LOSSINESS = (
    "subargument_identity",
    "justification_identity",
    "preference_metadata",
    "support_metadata",
    "known_non_attack_relations",
    "ignorance_relations",
)
_EMPTY_STANCES: Mapping[str, Sequence[StanceInput]] = MappingProxyType({})


def _sorted_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(str(value) for value in values)))


def argumentation_evidence_from_projection(
    *,
    branch: str,
    projection: StructuredProjection,
    claim_assertion_ids: Mapping[str, Sequence[str]],
    semantics: str = "grounded",
) -> BranchArgumentationEvidence:
    """Project justified-argument acceptance onto branch claim assertion ids."""

    justified = compute_structured_justified_arguments(projection, semantics=semantics)
    accepted_argument_ids: frozenset[str]
    skeptical_argument_ids: frozenset[str]
    if isinstance(justified, frozenset):
        accepted_argument_ids = justified
        skeptical_argument_ids = justified
    elif justified:
        accepted_argument_ids = frozenset[str]().union(*justified)
        skeptical_argument_ids = justified[0]
        for extension in justified[1:]:
            skeptical_argument_ids &= extension
    else:
        accepted_argument_ids = frozenset()
        skeptical_argument_ids = frozenset()

    accepted: list[str] = []
    skeptical: list[str] = []
    witness: list[str] = []
    for argument_id in sorted(accepted_argument_ids):
        claim_id = projection.argument_to_claim_id.get(argument_id)
        if claim_id is not None:
            accepted.extend(
                str(value) for value in claim_assertion_ids.get(claim_id, ())
            )
    for argument_id in sorted(skeptical_argument_ids):
        claim_id = projection.argument_to_claim_id.get(argument_id)
        if claim_id is not None:
            skeptical.extend(
                str(value) for value in claim_assertion_ids.get(claim_id, ())
            )
    for claim_id in sorted(projection.claim_to_argument_ids):
        witness.extend(str(value) for value in claim_assertion_ids.get(claim_id, ()))

    return BranchArgumentationEvidence(
        branch=branch,
        backend="argumentation",
        semantics=semantics,
        accepted_assertion_ids=_sorted_unique(accepted),
        skeptical_assertion_ids=_sorted_unique(skeptical),
        witness_assertion_ids=_sorted_unique(witness),
    )


def _merge_active_claim(claim: MergeClaim, branch: str) -> ActiveClaim:
    """The branch-scoped active view of one merge claim.

    Identity is the branch-scoped ``artifact_id`` (not the document's own
    ``claim_id``); ``branch``/``source_paper`` ride along so assignment-selection
    source grouping and entrenchment source overrides see the merge claim's real
    provenance facts.
    """

    return ActiveClaim.from_claim(
        claim.claim,
        claim_id=claim.artifact_id,
        branch=claim.branch_origin or branch,
        source_assertion_ids=(claim.assertion_id,),
        source_paper=claim.paper,
    )


def _canonical_stances(
    stances: Sequence[StanceInput],
    in_scope: frozenset[str],
) -> tuple[MergeStanceRow, ...]:
    rows: list[MergeStanceRow] = []
    for stance in stances:
        if stance.claim_id not in in_scope or stance.target_claim_id not in in_scope:
            continue
        rows.append(
            MergeStanceRow(
                claim_id=stance.claim_id,
                target_claim_id=stance.target_claim_id,
                stance_type=stance.stance_type,
                target_justification_id=stance.target_justification_id,
            )
        )
    rows.sort(
        key=lambda row: (
            row.claim_id,
            row.target_claim_id,
            row.stance_type.value,
            row.target_justification_id or "",
        )
    )
    return tuple(rows)


def _stance_input_from_row(row: MergeStanceRow) -> StanceInput:
    """Attribute access. The row already carries exactly these fields, typed."""

    return StanceInput(
        claim_id=row.claim_id,
        target_claim_id=row.target_claim_id,
        stance_type=row.stance_type,
        target_justification_id=row.target_justification_id,
    )


def _content_signature(
    claims: Sequence[MergeClaim],
    stance_rows: Sequence[MergeStanceRow],
) -> str:
    claims_payload = sorted(
        (
            {
                "artifact_id": claim.artifact_id,
                "semantic": claim.semantic_key(),
                "provenance": claim.provenance_mapping(),
            }
            for claim in claims
        ),
        key=lambda entry: str(entry["artifact_id"]),
    )
    stances_payload = [
        {
            "claim_id": row.claim_id,
            "target_claim_id": row.target_claim_id,
            "stance_type": row.stance_type.value,
            "target_justification_id": row.target_justification_id,
        }
        for row in stance_rows
    ]
    encoded = json.dumps(
        {"claims": claims_payload, "stances": stances_payload},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _empty_projection() -> StructuredProjection:
    return StructuredProjection(
        arguments=(),
        framework=ArgumentationFramework(
            arguments=frozenset(),
            defeats=frozenset(),
            attacks=frozenset(),
        ),
        claim_to_argument_ids={},
        argument_to_claim_id={},
    )


def build_branch_structured_summary(
    branch: str,
    claims: Sequence[MergeClaim],
    stances: Sequence[StanceInput] = (),
) -> BranchStructuredSummary:
    """Project one branch's claims and stances into a structured merge summary."""

    in_scope = frozenset(claim.artifact_id for claim in claims)
    stance_rows = _canonical_stances(stances, in_scope)
    assertion_ids = tuple(sorted(claim.assertion_id for claim in claims))
    claim_provenance = {
        claim.artifact_id: claim.provenance_mapping() for claim in claims
    }
    content_signature = _content_signature(claims, stance_rows)

    if claims:
        active_claims = [_merge_active_claim(claim, branch) for claim in claims]
        # Each branch-local claim enters the KB as a reported premise: the store
        # path synthesizes these reported justifications from claim rows, so the
        # store-free path does the same here.
        justifications = [
            CanonicalJustification(
                justification_id=f"reported:{claim.artifact_id}",
                conclusion_claim_id=claim.artifact_id,
                rule_kind="reported_claim",
            )
            for claim in claims
        ]
        stance_inputs = [_stance_input_from_row(row) for row in stance_rows]
        csaf = build_bridge_csaf(
            active_claims,
            justifications,
            stance_inputs,
            bundle=GroundedRulesBundle.empty(),
        )
        projection = csaf_to_projection(csaf, active_claims)
    else:
        projection = _empty_projection()

    return BranchStructuredSummary(
        branch=branch,
        assertion_ids=assertion_ids,
        claim_provenance=claim_provenance,
        content_signature=content_signature,
        relation_surface=dict(_RELATION_SURFACE),
        lossiness=_LOSSINESS,
        active_claims=tuple(claims),
        stance_rows=stance_rows,
        projection=projection,
    )


def build_structured_merge_candidates(
    claim_sets_per_branch: Mapping[str, Sequence[MergeClaim]],
    branch_a: str,
    branch_b: str,
    *,
    operator: str = "sum",
    stance_sets_per_branch: Mapping[str, Sequence[StanceInput]] = _EMPTY_STANCES,
) -> list[ArgumentationFramework]:
    """Merge the two branches' structured frameworks under the chosen operator."""

    summaries = {
        branch: build_branch_structured_summary(
            branch,
            claim_sets_per_branch.get(branch, ()),
            stance_sets_per_branch.get(branch, ()),
        )
        for branch in (branch_a, branch_b)
    }
    profile = {
        branch: summary.projection.framework for branch, summary in summaries.items()
    }

    if operator == "sum":
        return _require_candidates(sum_merge_frameworks(profile))
    if operator == "max":
        return _require_candidates(max_merge_frameworks(profile))
    if operator == "leximax":
        return _require_candidates(leximax_merge_frameworks(profile))
    raise ValueError(f"Unknown structured merge operator: {operator}")


def _require_candidates(
    result: list[ArgumentationFramework] | EnumerationExceeded,
) -> list[ArgumentationFramework]:
    if isinstance(result, EnumerationExceeded):
        raise RuntimeError(str(result))
    return result


__all__ = [
    "BranchArgumentationEvidence",
    "BranchStructuredSummary",
    "MergeStanceRow",
    "argumentation_evidence_from_projection",
    "build_branch_structured_summary",
    "build_structured_merge_candidates",
]
