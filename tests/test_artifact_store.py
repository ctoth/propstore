from __future__ import annotations

from pathlib import Path

from propstore.artifacts import (
    SOURCE_DOCUMENT_FAMILY,
    SOURCE_FINALIZE_REPORT_FAMILY,
    SourceRef,
    WORLDLINE_FAMILY,
    WorldlineRef,
)
from propstore.cli.repository import Repository
from propstore.repo.branch import create_branch
from propstore.source.common import initial_source_document, source_branch_name
from propstore.source_documents import (
    SourceFinalizeCalibrationDocument,
    SourceFinalizeReportDocument,
)
from propstore.worldline import WorldlineDefinition


def test_artifact_store_roundtrips_source_document(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    create_branch(repo.git, source_branch_name("demo"))

    source_doc = initial_source_document(
        repo,
        "demo",
        kind="academic_paper",
        origin_type="manual",
        origin_value="demo",
    )

    commit_sha = repo.artifacts.save(
        SOURCE_DOCUMENT_FAMILY,
        SourceRef("demo"),
        source_doc,
        message="Write source doc",
    )

    assert commit_sha
    loaded = repo.artifacts.require(SOURCE_DOCUMENT_FAMILY, SourceRef("demo"))
    assert loaded.to_payload() == source_doc.to_payload()


def test_artifact_transaction_writes_multiple_source_artifacts(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    create_branch(repo.git, source_branch_name("demo"))

    source_doc = initial_source_document(
        repo,
        "demo",
        kind="academic_paper",
        origin_type="manual",
        origin_value="demo",
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

    transaction = repo.artifacts.transact(
        message="Write source artifacts",
        branch=source_branch_name("demo"),
    )
    transaction.save(SOURCE_DOCUMENT_FAMILY, SourceRef("demo"), source_doc)
    transaction.save(SOURCE_FINALIZE_REPORT_FAMILY, SourceRef("demo"), report)
    commit_sha = transaction.commit()

    assert commit_sha
    loaded_source = repo.artifacts.require(SOURCE_DOCUMENT_FAMILY, SourceRef("demo"))
    loaded_report = repo.artifacts.require(SOURCE_FINALIZE_REPORT_FAMILY, SourceRef("demo"))
    assert loaded_source.to_payload() == source_doc.to_payload()
    assert loaded_report.to_payload() == report.to_payload()


def test_artifact_store_roundtrips_and_lists_worldlines(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    definition = WorldlineDefinition.from_dict({
        "id": "demo_worldline",
        "name": "Demo worldline",
        "targets": ["force", "mass"],
        "inputs": {
            "bindings": {"location": "earth"},
            "overrides": {"mass": 10.0},
        },
    })

    commit_sha = repo.artifacts.save(
        WORLDLINE_FAMILY,
        WorldlineRef("demo_worldline"),
        definition.to_document(),
        message="Write worldline",
    )

    assert commit_sha
    loaded = repo.artifacts.require(WORLDLINE_FAMILY, WorldlineRef("demo_worldline"))
    listed = repo.artifacts.list(WORLDLINE_FAMILY)

    assert WorldlineDefinition.from_document(loaded) == definition
    assert listed == [WorldlineRef("demo_worldline")]
