"""Source-branch family charters and their nested document structs.

A *source branch* (``source/<stem>``) holds the in-progress proposal for one
external source: a manifest (:class:`SourceDocument`), the proposed concept
vocabulary (:class:`SourceConceptsDocument`), the extracted claims
(:class:`SourceClaimsDocument`), and the inter-/intra-claim relations
(:class:`SourceStancesDocument`, :class:`SourceJustificationsDocument`). Each is
ONE quire ``@charter`` class stored as a fixed file on the source branch via
:data:`SOURCE_BRANCH`.

Substrate boundary (CLAUDE.md):

* These families are deliberately **foreign-key free**. A source branch is
  isolated: the canonical concept/claim families it ultimately references do not
  exist on the branch, so a charter-FK that validated at write time could never
  be satisfied. The source-local handle → canonical FK *lowering* happens later,
  inside the source subsystem, through quire's ``FamilyReferenceIndex`` (see
  :mod:`propstore.source.reference_indexes`) — never by mirroring a canonical id
  into a source charter or by string munging.
* The nested structs are the single canonical spelling of each shape; there is
  no ``*Document``/``*Row`` second spelling and no ``to_payload`` conversion.
  They are carried as JSON-blob charter fields, matching every other propstore
  family.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

import msgspec

from quire.artifacts import BranchPlacement, FixedFilePlacement
from quire.charter_class import CharterDoc, charter, charter_field
from quire.refs import single_field_ref_type

from propstore.core.algorithm_stage import AlgorithmStage
from propstore.core.source_types import SourceKind
from propstore.families.claims import ClaimType, Exactness
from propstore.families.micropublications import MicropublicationEvidence
from propstore.provenance import ProvenanceStatus
from propstore.stances import StanceType

# ---------------------------------------------------------------------------
# Source-branch placement + ref type
# ---------------------------------------------------------------------------

SOURCE_BRANCH = BranchPlacement(
    policy="template",
    template="source/{stem}",
    ref_field="name",
    codec="safe_slug",
    collision_suffix="sha256",
)
"""Place a source-branch artifact on ``source/<safe-slug of the source name>``."""


if TYPE_CHECKING:

    @dataclass(frozen=True)
    class SourceRef:
        name: str

else:
    SourceRef = single_field_ref_type("SourceRef", "name", module=__name__)


# ---------------------------------------------------------------------------
# Nested structs (single canonical spelling; carried as JSON-blob fields)
# ---------------------------------------------------------------------------


class _Struct(msgspec.Struct, forbid_unknown_fields=True):
    """Base for nested source structs: strict-field like ``CharterDoc``."""


class SourceOriginDocument(_Struct):
    type: str
    value: str
    retrieved: str | None = None
    content_ref: str | None = None


class SourceTrustQualityDocument(_Struct):
    status: ProvenanceStatus
    b: float
    d: float
    u: float
    a: float


class SourceTrustPriorDocument(_Struct):
    """The four Jøsang components of a calibrated prior-trust opinion.

    Stored as the bare ``b``/``d``/``u``/``a`` mass of the ``doxa.Opinion``
    ``calibrate_source_trust`` projects — never a second ``Opinion`` spelling.
    Absent (``None``) until promote-time calibration stamps it; a defaulted
    source trust carries no prior, so ignorance is honest, not a fabricated 0.5.
    """

    b: float
    d: float
    u: float
    a: float


class SourceTrustDocument(_Struct):
    status: ProvenanceStatus
    quality: SourceTrustQualityDocument | None = None
    prior_base_rate: SourceTrustPriorDocument | None = None
    derived_from: tuple[str, ...] = ()


class SourceMetadataDocument(_Struct):
    name: str


class SourceConceptAliasDocument(_Struct):
    name: str
    source: str | None = None
    note: str | None = None


class SourceConceptRegistryMatchDocument(_Struct):
    artifact_id: str
    canonical_name: str | None = None


class SourceConceptFormParametersDocument(_Struct):
    construction: str | None = None
    extensible: bool | None = None
    note: str | None = None
    reference: str | None = None
    values: tuple[str, ...] | None = None


class SourceParameterizationRelationshipDocument(_Struct):
    inputs: tuple[str, ...]
    formula: str | None = None
    sympy: str | None = None
    exactness: Exactness | None = None
    source: str | None = None
    bidirectional: bool | None = None
    conditions: tuple[str, ...] = ()
    note: str | None = None
    canonical_claim: str | None = None
    fit_statistics: str | None = None


class SourceConceptEntryDocument(_Struct):
    local_name: str | None = None
    proposed_name: str | None = None
    definition: str | None = None
    form: str | None = None
    aliases: tuple[SourceConceptAliasDocument, ...] = ()
    form_parameters: SourceConceptFormParametersDocument | None = None
    parameterization_relationships: tuple[
        SourceParameterizationRelationshipDocument, ...
    ] = ()
    status: str | None = None
    registry_match: SourceConceptRegistryMatchDocument | None = None
    artifact_code: str | None = None


class SourceProvenanceDocument(_Struct):
    paper: str | None = None
    page: int | None = None
    figure: str | None = None
    quote_fragment: str | None = None
    section: str | None = None
    table: str | None = None


class ExtractionProvenanceDocument(_Struct):
    reader: str | None = None
    method: str | None = None
    timestamp: str | None = None


class ClaimLogicalIdDocument(_Struct):
    namespace: str
    value: str
    confidence: float | None = None
    pass_number: int | None = None

    @property
    def formatted(self) -> str:
        return f"{self.namespace}:{self.value}"


class ClaimSourceDocument(_Struct):
    paper: str
    extraction_date: str | None = None
    extraction_model: str | None = None
    extraction_prompt_hash: str | None = None


class FitStatisticsDocument(_Struct):
    r: float | None = None
    r_sd: float | None = None
    slope: float | None = None
    slope_sd: float | None = None


class VariableBindingDocument(_Struct):
    concept: str
    symbol: str | None = None
    role: str | None = None
    name: str | None = None


class ParameterBindingDocument(_Struct):
    name: str
    concept: str
    note: str | None = None


class ResolutionDocument(_Struct):
    method: str
    embedding_distance: float | None = None
    embedding_model: str | None = None
    model: str | None = None
    pass_number: int | None = None
    confidence: float | None = None
    # NOTE (8-3): an opinion-bearing resolution (``doxa.Opinion``) is added with
    # the argumentation/trust calibration surface; source authoring never sets it.


class ClaimStanceDocument(_Struct):
    """A stance embedded on a claim (target is another claim's handle)."""

    type: StanceType
    target: str
    conditions_differ: str | None = None
    note: str | None = None
    resolution: ResolutionDocument | None = None
    strength: str | None = None
    target_justification_id: str | None = None


class SourceClaimDocument(_Struct):
    """One extracted claim on a source branch (the ~40-field source claim).

    ``id`` / ``source_local_id`` are the source-local handles; ``artifact_id`` /
    ``version_id`` / ``logical_ids`` are the derived canonical identity stamped
    by :func:`propstore.source.claims.normalize_source_claims_payload`. Concept
    references (``concept`` / ``concepts`` / ``target_concept`` / binding
    ``concept`` fields) hold source-local concept handles until promotion lowers
    them to canonical concept FKs.
    """

    artifact_id: str | None = None
    logical_ids: tuple[ClaimLogicalIdDocument, ...] = ()
    version_id: str | None = None
    type: ClaimType | None = None
    provenance: SourceProvenanceDocument | None = None
    id: str | None = None
    body: str | None = None
    concept: str | None = None
    concepts: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    context: str | None = None
    equations: tuple[str, ...] = ()
    exactness: Exactness | None = None
    expression: str | None = None
    fit: FitStatisticsDocument | None = None
    listener_population: str | None = None
    lower_bound: float | None = None
    measure: str | None = None
    methodology: str | None = None
    name: str | None = None
    notes: str | None = None
    parameters: tuple[ParameterBindingDocument, ...] = ()
    sample_size: int | None = None
    stage: AlgorithmStage | None = None
    stances: tuple[ClaimStanceDocument, ...] = ()
    statement: str | None = None
    sympy: str | None = None
    target_concept: str | None = None
    uncertainty: float | None = None
    uncertainty_type: str | None = None
    unit: str | None = None
    upper_bound: float | None = None
    value: float | None = None
    variables: tuple[VariableBindingDocument, ...] = ()
    source_local_id: str | None = None
    artifact_code: str | None = None


class SourceAttackTargetDocument(_Struct):
    target_claim: str | None = None
    target_justification_id: str | None = None
    target_premise_index: int | None = None


class SourceJustificationDocument(_Struct):
    id: str | None = None
    conclusion: str | None = None
    premises: tuple[str, ...] = ()
    rule_kind: str | None = None
    rule_strength: str | None = None
    provenance: SourceProvenanceDocument | None = None
    attack_target: SourceAttackTargetDocument | None = None
    artifact_code: str | None = None


class SourceStanceEntryDocument(_Struct):
    source_claim: str | None = None
    perspective_source_claim_id: str | None = None
    target: str | None = None
    type: StanceType | None = None
    strength: str | None = None
    note: str | None = None
    conditions_differ: str | None = None
    resolution: ResolutionDocument | None = None
    target_justification_id: str | None = None
    artifact_code: str | None = None


class SourceMicropublicationDocument(_Struct):
    """A Clark micropublication bundle composed on a source branch (8-3a).

    The source-branch counterpart of the canonical
    :class:`~propstore.families.micropublications.Micropublication`: it bundles a
    source claim with its evidence, assumptions (the claim's conditions), stance,
    bibliographic provenance, and source identity. It is **foreign-key free** —
    ``context_id`` and ``claims`` hold the claim-side handles as authored, lowered
    to canonical FKs only when the source branch is promoted. ``artifact_id`` /
    ``version_id`` are the content identity stamped by
    :mod:`propstore.families.identity.micropubs` (an ``ni:`` trusty URI over the
    canonical payload), not a logical handle.
    """

    artifact_id: str
    context_id: str
    claims: tuple[str, ...]
    version_id: str | None = None
    evidence: tuple[MicropublicationEvidence, ...] = ()
    assumptions: tuple[str, ...] = ()
    stance: StanceType | None = None
    provenance: SourceProvenanceDocument | None = None
    source: str | None = None


class SourceParameterizationGroupMergeDocument(_Struct):
    merged_group: tuple[str, ...]
    previous_groups: tuple[tuple[str, ...], ...]
    introduced_by: tuple[str, ...]


class SourceFinalizeCalibrationDocument(_Struct):
    prior_base_rate_status: str
    source_quality_status: str
    fallback_to_default_base_rate: bool


# ---------------------------------------------------------------------------
# Family charters (one fixed file per source branch)
# ---------------------------------------------------------------------------

_SOURCE_CONTRACT_VERSION = "2026.06.29"


@charter(
    key="source_documents",
    name="source_documents",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=FixedFilePlacement("source.yaml", branch=SOURCE_BRANCH),
)
class SourceDocument(CharterDoc):
    """The source-branch manifest: identity, kind, origin, and trust."""

    id: str
    kind: SourceKind
    origin: Annotated[SourceOriginDocument, charter_field(json=True)]
    trust: Annotated[SourceTrustDocument, charter_field(json=True)]
    metadata: Annotated[SourceMetadataDocument | None, charter_field(json=True)] = None
    artifact_code: str | None = None


@charter(
    key="source_concepts",
    name="source_concepts",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=FixedFilePlacement("concepts.yaml", branch=SOURCE_BRANCH),
)
class SourceConceptsDocument(CharterDoc):
    """The proposed concept vocabulary for a source branch."""

    concepts: Annotated[
        tuple[SourceConceptEntryDocument, ...], charter_field(json=True)
    ] = ()


@charter(
    key="source_claims",
    name="source_claims",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=FixedFilePlacement("claims.yaml", branch=SOURCE_BRANCH),
)
class SourceClaimsDocument(CharterDoc):
    """The extracted claims for a source branch."""

    claims: Annotated[tuple[SourceClaimDocument, ...], charter_field(json=True)] = ()
    source: Annotated[ClaimSourceDocument | None, charter_field(json=True)] = None
    produced_by: Annotated[
        ExtractionProvenanceDocument | None, charter_field(json=True)
    ] = None


@charter(
    key="source_stances",
    name="source_stances",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=FixedFilePlacement("stances.yaml", branch=SOURCE_BRANCH),
)
class SourceStancesDocument(CharterDoc):
    """The inter-claim stances for a source branch."""

    stances: Annotated[
        tuple[SourceStanceEntryDocument, ...], charter_field(json=True)
    ] = ()
    source: Annotated[ClaimSourceDocument | None, charter_field(json=True)] = None
    produced_by: Annotated[
        ExtractionProvenanceDocument | None, charter_field(json=True)
    ] = None


@charter(
    key="source_justifications",
    name="source_justifications",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=FixedFilePlacement("justifications.yaml", branch=SOURCE_BRANCH),
)
class SourceJustificationsDocument(CharterDoc):
    """The intra-paper justification structure for a source branch."""

    justifications: Annotated[
        tuple[SourceJustificationDocument, ...], charter_field(json=True)
    ] = ()
    source: Annotated[ClaimSourceDocument | None, charter_field(json=True)] = None
    produced_by: Annotated[
        ExtractionProvenanceDocument | None, charter_field(json=True)
    ] = None


@charter(
    key="source_micropubs",
    name="source_micropubs",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=FixedFilePlacement("micropublications.yaml", branch=SOURCE_BRANCH),
)
class SourceMicropublicationsDocument(CharterDoc):
    """The Clark micropublication bundles composed for a source branch.

    Written by :func:`propstore.source.finalize.finalize_source_branch` once
    every source claim is micropublication-coverable. FK-free on the source
    branch (the lowering to canonical claim/context FKs is a promote-time
    concern); each bundle carries its own content identity.
    """

    micropubs: Annotated[
        tuple[SourceMicropublicationDocument, ...], charter_field(json=True)
    ] = ()
    source: Annotated[ClaimSourceDocument | None, charter_field(json=True)] = None


@charter(
    key="source_finalize_reports",
    name="source_finalize_reports",
    contract_version=_SOURCE_CONTRACT_VERSION,
    placement=FixedFilePlacement("finalize-report.yaml", branch=SOURCE_BRANCH),
)
class SourceFinalizeReportDocument(CharterDoc):
    """The finalize-time precondition report for a source branch.

    Records whether the branch is promotable (``status="ready"``) or what is
    missing (``status="blocked"`` plus the per-kind reference/coverage errors).
    This is a workflow precondition recorded on the source branch — it never
    collapses or drops a rival claim (that would violate the non-commitment
    discipline); it only states whether the finalize completed.
    """

    kind: str
    source: str
    status: str
    artifact_code_status: str
    calibration: Annotated[SourceFinalizeCalibrationDocument, charter_field(json=True)]
    micropub_status: str = "not_composed"
    claim_reference_errors: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    micropub_coverage_errors: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    justification_reference_errors: Annotated[
        tuple[str, ...], charter_field(json=True)
    ] = ()
    stance_reference_errors: Annotated[tuple[str, ...], charter_field(json=True)] = ()
    concept_alignment_candidates: Annotated[
        tuple[str, ...], charter_field(json=True)
    ] = ()
    parameterization_group_merges: Annotated[
        tuple[SourceParameterizationGroupMergeDocument, ...], charter_field(json=True)
    ] = ()
