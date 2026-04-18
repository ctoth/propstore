from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from quire.family_store import DocumentFamilyStore, DocumentFamilyTransaction

from propstore.artifacts import (
    CLAIMS_FILE_FAMILY,
    CONCEPT_FILE_FAMILY,
    SOURCE_DOCUMENT_FAMILY,
    SOURCE_FINALIZE_REPORT_FAMILY,
    SourceRef,
    WORLDLINE_FAMILY,
    ClaimsFileRef,
    ConceptFileRef,
    WorldlineRef,
)
from propstore.repository import Repository
from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.source.common import initial_source_document, source_branch_name
from propstore.artifacts.documents.sources import (
    SourceFinalizeCalibrationDocument,
    SourceFinalizeReportDocument,
)
from propstore.worldline import WorldlineDefinition


def test_repository_artifacts_is_direct_quire_family_store(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    assert type(repo.artifacts) is DocumentFamilyStore
    assert repo.artifacts.owner is repo


def test_artifact_transaction_is_quire_family_transaction(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    transaction = repo.artifacts.transact(message="demo")

    assert isinstance(transaction, DocumentFamilyTransaction)


def test_artifact_store_roundtrips_source_document(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.create_branch(source_branch_name("demo"))

    source_doc = initial_source_document(
        repo,
        "demo",
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
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
    assert loaded.kind is SourceKind.ACADEMIC_PAPER
    assert loaded.origin.type is SourceOriginType.MANUAL


def test_artifact_transaction_writes_multiple_source_artifacts(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.create_branch(source_branch_name("demo"))

    source_doc = initial_source_document(
        repo,
        "demo",
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
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

    with repo.artifacts.transact(
        message="Write source artifacts",
        branch=source_branch_name("demo"),
    ) as transaction:
        transaction.save(SOURCE_DOCUMENT_FAMILY, SourceRef("demo"), source_doc)
        transaction.save(SOURCE_FINALIZE_REPORT_FAMILY, SourceRef("demo"), report)

    commit_sha = transaction.commit_sha
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


def test_artifact_store_renders_typed_documents(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.create_branch(source_branch_name("demo"))

    source_doc = initial_source_document(
        repo,
        "demo",
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="demo",
    )

    rendered = repo.artifacts.render(source_doc)

    assert "kind: academic_paper" in rendered
    assert "metadata:" in rendered
    assert "name: demo" in rendered


def test_artifact_store_moves_worldlines_atomically(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    definition = WorldlineDefinition.from_dict({
        "id": "demo_worldline",
        "name": "Demo worldline",
        "targets": ["force"],
    })
    document = definition.to_document()

    repo.artifacts.save(
        WORLDLINE_FAMILY,
        WorldlineRef("demo_worldline"),
        document,
        message="Seed worldline",
    )

    commit_sha = repo.artifacts.move(
        WORLDLINE_FAMILY,
        WorldlineRef("demo_worldline"),
        WorldlineRef("renamed_worldline"),
        document,
        message="Rename worldline",
    )

    assert commit_sha
    assert repo.artifacts.load(WORLDLINE_FAMILY, WorldlineRef("demo_worldline")) is None
    renamed = repo.artifacts.require_handle(WORLDLINE_FAMILY, WorldlineRef("renamed_worldline"))
    assert renamed.address.require_path() == "worldlines/renamed_worldline.yaml"
    assert WorldlineDefinition.from_document(renamed.document) == definition


def test_artifact_store_derives_refs_from_paths_and_loaded_objects(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    concept_ref = repo.artifacts.ref_from_path(CONCEPT_FILE_FAMILY, "concepts/demo.yaml")
    claims_ref = repo.artifacts.ref_from_path(CLAIMS_FILE_FAMILY, Path("claims/paper.yaml"))

    assert concept_ref == ConceptFileRef("demo")
    assert claims_ref == ClaimsFileRef("paper")

    loaded_concept = SimpleNamespace(source_path=repo.tree() / "concepts" / "demo.yaml")
    loaded_claims = SimpleNamespace(source_path=repo.tree() / "claims" / "paper.yaml")

    assert repo.artifacts.ref_from_loaded(CONCEPT_FILE_FAMILY, loaded_concept) == ConceptFileRef("demo")
    assert repo.artifacts.ref_from_loaded(CLAIMS_FILE_FAMILY, loaded_claims) == ClaimsFileRef("paper")
