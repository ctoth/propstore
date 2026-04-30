from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.documents.sources import (
    SourceFinalizeCalibrationDocument,
    SourceFinalizeReportDocument,
)
from propstore.families.registry import SourceRef
from propstore.repository import Repository, StaleHeadError
from propstore.source import (
    finalize_source_branch,
    initial_source_document,
    promote_source_branch,
    source_branch_name,
)
from propstore.importing.repository_import import (
    commit_repository_import,
    plan_repository_import,
)


MutationRunner = Callable[[Repository], None]


def _seed_source_branch(repo: Repository, source_name: str) -> str:
    branch = source_branch_name(source_name)
    repo.snapshot.ensure_branch(branch)
    source_doc = initial_source_document(
        repo,
        source_name,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value=source_name,
    )
    repo.families.source_documents.save(
        SourceRef(source_name),
        source_doc,
        message=f"Init source {source_name}",
        branch=branch,
    )
    return branch


def _seed_ready_source_branch(repo: Repository, source_name: str) -> str:
    branch = _seed_source_branch(repo, source_name)
    source_doc = repo.families.source_documents.require(SourceRef(source_name))
    report = SourceFinalizeReportDocument(
        kind="source_finalize_report",
        source=str(source_doc.id),
        status="ready",
        claim_reference_errors=(),
        justification_reference_errors=(),
        stance_reference_errors=(),
        concept_alignment_candidates=(),
        parameterization_group_merges=(),
        artifact_code_status="complete",
        calibration=SourceFinalizeCalibrationDocument(
            prior_base_rate_status="fallback",
            source_quality_status="vacuous",
            fallback_to_default_base_rate=True,
        ),
    )
    repo.families.source_finalize_reports.save(
        SourceRef(source_name),
        report,
        message=f"Finalize {source_name}",
        branch=branch,
    )
    return branch


def _seed_import_source(tmp_path: Path) -> Path:
    project = tmp_path / "source-project"
    repo = Repository.init(project / "knowledge")
    repo.git.commit_batch(
        adds={"contexts/imported.yaml": b"id: imported\nname: Imported\n"},
        deletes=(),
        message="Seed import source",
        branch="master",
    )
    return project


def _advance_branch(repo: Repository, branch: str) -> str:
    return repo.git.commit_batch(
        adds={f"contexts/ws_q_cas_{branch.replace('/', '_')}.yaml": b"id: race\nname: Race\n"},
        deletes=(),
        message="Concurrent writer",
        branch=branch,
    )


def _finalize_runner(repo: Repository) -> None:
    finalize_source_branch(repo, "race")


def _promote_runner(repo: Repository) -> None:
    promote_source_branch(repo, "race")


def _repository_import_runner(source_project: Path) -> MutationRunner:
    def run(repo: Repository) -> None:
        plan = plan_repository_import(repo, source_project)
        commit_repository_import(repo, plan)

    return run


def _materialize_runner(repo: Repository) -> None:
    repo.snapshot.materialize(branch="master", force=True)


@pytest.mark.parametrize(
    ("path_name", "branch", "seed", "runner_factory"),
    [
        ("finalize", "source/race", _seed_source_branch, lambda _tmp: _finalize_runner),
        ("promote", "master", _seed_ready_source_branch, lambda _tmp: _promote_runner),
        (
            "repository_import",
            "import/source-project",
            lambda repo, _source_name: None,
            lambda tmp: _repository_import_runner(_seed_import_source(tmp)),
        ),
        ("materialize", "master", lambda repo, _source_name: None, lambda _tmp: _materialize_runner),
    ],
)
def test_concurrent_writer_loses_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    path_name: str,
    branch: str,
    seed: Callable[[Repository, str], object],
    runner_factory: Callable[[Path], MutationRunner],
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    seed(repo, "race")
    runner = runner_factory(tmp_path)
    if branch.startswith("import/"):
        repo.snapshot.ensure_branch(branch)
    head_at_start = repo.snapshot.branch_head(branch)
    assert head_at_start is not None

    if path_name == "materialize":
        original_files = repo.snapshot.files

        def files_and_race(*args, **kwargs):
            result = original_files(*args, **kwargs)
            _advance_branch(repo, branch)
            return result

        monkeypatch.setattr(repo.snapshot, "files", files_and_race)
    else:
        original_commit_batch = type(repo.git).commit_batch

        def stale_commit_batch(self, adds, deletes, message, *, branch=None, expected_head=None):
            if branch == path_name_branch and expected_head == head_at_start:
                raise ValueError(
                    f"Branch {branch!r} head mismatch: expected {expected_head}, got concurrent-head"
                )
            return original_commit_batch(
                self,
                adds,
                deletes,
                message,
                branch=branch,
                expected_head=expected_head,
            )

        path_name_branch = branch
        monkeypatch.setattr(type(repo.git), "commit_batch", stale_commit_batch)

    with pytest.raises(StaleHeadError) as exc_info:
        runner(repo)

    assert exc_info.value.path == path_name
    assert exc_info.value.branch == branch
    assert exc_info.value.expected_head == head_at_start
