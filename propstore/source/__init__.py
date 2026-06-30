"""The source-branch subsystem: author, finalize, promote.

A *source branch* (``source/<stem>``) holds the in-progress proposal for one
external source. This package owns its whole lifecycle: authoring claims/concepts/
relations onto the branch, finalizing it (the promotability precondition + Clark
micropublication compose), and promoting the valid slice into canonical
``master`` while quarantining the rest. Phase 6d's concept-alignment *math* half
(``alignment``) also lives here; its repository-bound half lands with proposals.

The submodule functions are re-exported here as the subsystem's surface; callers
may also import the submodules directly.
"""

from __future__ import annotations

from .alignment import (
    align_sources,
    build_alignment_artifact,
    classify_relation,
    concept_proposal_branch,
    decide_alignment,
    promote_alignment,
)
from .common import (
    init_source_branch,
    initial_source_document,
    load_source_claims_document,
    load_source_concepts_document,
    load_source_document,
    load_source_finalize_report,
    load_source_justifications_document,
    load_source_metadata,
    load_source_micropubs_document,
    load_source_notes,
    load_source_stances_document,
    normalize_source_slug,
    source_branch_name,
    source_paper_slug,
    source_tag_uri,
)
from .finalize import finalize_source_branch
from .promote import (
    PromotionResult,
    SourceConceptPromotionResolution,
    load_finalize_report,
    promote_source_branch,
    resolve_source_concept_promotions,
    sync_source_branch,
)
from .registry import (
    load_primary_branch_concepts,
    primary_branch_concept_match,
)
from .stages import SourcePromotionPlan
from .status import (
    SourceStatusReport,
    SourceStatusState,
    inspect_source_status,
)

__all__ = [
    "PromotionResult",
    "align_sources",
    "build_alignment_artifact",
    "classify_relation",
    "concept_proposal_branch",
    "decide_alignment",
    "promote_alignment",
    "SourceConceptPromotionResolution",
    "SourcePromotionPlan",
    "SourceStatusReport",
    "SourceStatusState",
    "finalize_source_branch",
    "init_source_branch",
    "initial_source_document",
    "inspect_source_status",
    "load_finalize_report",
    "load_primary_branch_concepts",
    "load_source_claims_document",
    "load_source_concepts_document",
    "load_source_document",
    "load_source_finalize_report",
    "load_source_justifications_document",
    "load_source_metadata",
    "load_source_micropubs_document",
    "load_source_notes",
    "load_source_stances_document",
    "normalize_source_slug",
    "primary_branch_concept_match",
    "promote_source_branch",
    "resolve_source_concept_promotions",
    "source_branch_name",
    "source_paper_slug",
    "source_tag_uri",
    "sync_source_branch",
]
