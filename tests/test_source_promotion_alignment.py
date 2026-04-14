from __future__ import annotations

from pathlib import Path

from propstore.artifacts import (
    CANONICAL_SOURCE_FAMILY,
    CLAIMS_FILE_FAMILY,
    CONCEPT_ALIGNMENT_FAMILY,
    CONCEPT_FILE_FAMILY,
    CanonicalSourceRef,
    ClaimsFileRef,
    ConceptAlignmentRef,
    ConceptFileRef,
    SOURCE_CLAIMS_FAMILY,
    SOURCE_CONCEPTS_FAMILY,
    SOURCE_DOCUMENT_FAMILY,
    SOURCE_FINALIZE_REPORT_FAMILY,
    SourceRef,
)
from propstore.cli.repository import Repository
from propstore.document_schema import convert_document_value
from propstore.identity import derive_concept_artifact_id
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.source import (
    CONCEPT_PROPOSAL_BRANCH,
    align_sources,
    decide_alignment,
    initial_source_document,
    load_alignment_artifact,
    normalize_source_claims_payload,
    promote_alignment,
    promote_source_branch,
    source_branch_name,
)
from propstore.source_documents import (
    SourceClaimsDocument,
    SourceConceptsDocument,
    SourceFinalizeCalibrationDocument,
    SourceFinalizeReportDocument,
)


def _save_source(repo: Repository, source_name: str, concepts_payload: dict, claims_payload: dict | None = None) -> None:
    branch = source_branch_name(source_name)
    repo.snapshot.ensure_branch(branch)

    source_doc = initial_source_document(
        repo,
        source_name,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value=source_name,
    )
    repo.artifacts.save(
        SOURCE_DOCUMENT_FAMILY,
        SourceRef(source_name),
        source_doc,
        message=f"Init source {source_name}",
    )

    concepts_doc = convert_document_value(
        concepts_payload,
        SourceConceptsDocument,
        source=f"{branch}:concepts.yaml",
    )
    repo.artifacts.save(
        SOURCE_CONCEPTS_FAMILY,
        SourceRef(source_name),
        concepts_doc,
        message=f"Write concepts for {source_name}",
    )

    if claims_payload is None:
        return

    raw_claims = convert_document_value(
        claims_payload,
        SourceClaimsDocument,
        source=f"{branch}:claims.yaml",
    )
    normalized_claims, _ = normalize_source_claims_payload(
        raw_claims,
        source_uri=source_doc.id,
        source_namespace=source_name,
    )
    repo.artifacts.save(
        SOURCE_CLAIMS_FAMILY,
        SourceRef(source_name),
        normalized_claims,
        message=f"Write claims for {source_name}",
    )

    report = SourceFinalizeReportDocument(
        kind="source_finalize_report",
        source=str(source_doc.id),
        status="ready",
        claim_reference_errors=(),
        justification_reference_errors=(),
        stance_reference_errors=(),
        concept_alignment_candidates=(),
        parameterization_group_merges=(),
        artifact_code_status="incomplete",
        calibration=SourceFinalizeCalibrationDocument(
            prior_base_rate_status="fallback",
            source_quality_status="vacuous",
            fallback_to_default_base_rate=True,
        ),
    )
    repo.artifacts.save(
        SOURCE_FINALIZE_REPORT_FAMILY,
        SourceRef(source_name),
        report,
        message=f"Finalize {source_name}",
    )


def test_align_and_promote_alignment_use_artifact_store(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.snapshot.ensure_branch(CONCEPT_PROPOSAL_BRANCH)

    _save_source(
        repo,
        "paper_a",
        {
            "concepts": [
                {
                    "local_name": "gravity",
                    "proposed_name": "gravity",
                    "definition": "Acceleration due to gravity.",
                    "form": "quantity",
                }
            ]
        },
    )
    _save_source(
        repo,
        "paper_b",
        {
            "concepts": [
                {
                    "local_name": "gravity_constant",
                    "proposed_name": "gravity",
                    "definition": "Acceleration due to gravity.",
                    "form": "quantity",
                }
            ]
        },
    )

    artifact = align_sources(
        repo,
        [source_branch_name("paper_a"), source_branch_name("paper_b")],
    )
    slug = artifact.id.split(":", 1)[1]
    stored = repo.artifacts.require(
        CONCEPT_ALIGNMENT_FAMILY,
        ConceptAlignmentRef(slug),
    )
    assert stored.to_payload() == artifact.to_payload()

    decided = decide_alignment(repo, artifact.id, accept=[artifact.arguments[0].id], reject=[])
    assert decided.decision.status == "decided"

    promoted = promote_alignment(repo, artifact.id)
    promoted_concept = repo.artifacts.require(
        CONCEPT_FILE_FAMILY,
        ConceptFileRef("gravity"),
    )
    reloaded_alignment = load_alignment_artifact(repo, artifact.id)[1]

    assert promoted.decision.status == "promoted"
    assert promoted_concept.canonical_name == "gravity"
    assert reloaded_alignment.decision.status == "promoted"


def test_promote_source_branch_writes_canonical_artifact_families(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    _save_source(
        repo,
        "paper_source",
        {
            "concepts": [
                {
                    "local_name": "gravity",
                    "proposed_name": "gravity",
                    "definition": "Acceleration due to gravity.",
                    "form": "quantity",
                }
            ]
        },
        claims_payload={
            "source": {"paper": "paper_source"},
            "claims": [
                {
                    "id": "gravity_claim_local",
                    "type": "parameter",
                    "concept": "gravity",
                    "value": 9.81,
                    "unit": "m/s^2",
                    "provenance": {"paper": "paper_source", "page": 1},
                }
            ],
        },
    )

    commit_sha = promote_source_branch(repo, "paper_source")

    assert commit_sha
    canonical_source = repo.artifacts.require(
        CANONICAL_SOURCE_FAMILY,
        CanonicalSourceRef("paper_source"),
    )
    claims_file = repo.artifacts.require(
        CLAIMS_FILE_FAMILY,
        ClaimsFileRef("paper_source"),
    )
    concept_file = repo.artifacts.require(
        CONCEPT_FILE_FAMILY,
        ConceptFileRef("gravity"),
    )

    assert canonical_source.metadata is not None
    assert claims_file.claims[0].concept == derive_concept_artifact_id("propstore", "gravity")
    assert concept_file.artifact_id == derive_concept_artifact_id("propstore", "gravity")
