from __future__ import annotations

import threading
from pathlib import Path

from propstore.app.contexts import ContextAddRequest, ContextWorkflowError, add_context
from propstore.app.predicates import PredicateAddRequest, add_predicate
from propstore.app.rules import RuleAddRequest, add_rule
from propstore.families.registry import ContextRef, PredicateFileRef, RuleFileRef
from propstore.repository import Repository
from propstore.sidecar.build import build_sidecar
from propstore.source import promote_source_branch
from tests.test_branch_head_cas_matrix import _seed_ready_source_branch


def test_head_bound_transactions_serialize_head_capture_and_commit(
    tmp_path: Path,
) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    initial_head = repo.snapshot.branch_head("master")
    assert initial_head is not None

    first_entered = threading.Event()
    release_first = threading.Event()
    second_entered = threading.Event()
    first_done = threading.Event()
    second_done = threading.Event()
    failures: list[BaseException] = []
    observed_heads: dict[str, str | None] = {}
    commits: dict[str, str] = {}

    def first_writer() -> None:
        try:
            with repo.head_bound_transaction("master", path="first") as txn:
                observed_heads["first"] = txn.expected_head
                first_entered.set()
                release_first.wait(timeout=5)
                commits["first"] = txn.commit_batch(
                    adds={"contexts/first.yaml": b"id: first\nname: First\n"},
                    deletes=(),
                    message="First writer",
                )
        except BaseException as exc:
            failures.append(exc)
        finally:
            first_done.set()

    def second_writer() -> None:
        try:
            first_entered.wait(timeout=5)
            with repo.head_bound_transaction("master", path="second") as txn:
                second_entered.set()
                observed_heads["second"] = txn.expected_head
                commits["second"] = txn.commit_batch(
                    adds={"contexts/second.yaml": b"id: second\nname: Second\n"},
                    deletes=(),
                    message="Second writer",
                )
        except BaseException as exc:
            failures.append(exc)
        finally:
            second_done.set()

    first_thread = threading.Thread(target=first_writer)
    second_thread = threading.Thread(target=second_writer)
    first_thread.start()
    assert first_entered.wait(timeout=5)
    second_thread.start()
    assert not second_entered.wait(timeout=0.1)

    release_first.set()
    assert first_done.wait(timeout=5)
    assert second_done.wait(timeout=5)
    first_thread.join(timeout=5)
    second_thread.join(timeout=5)

    assert failures == []
    assert observed_heads["first"] == initial_head
    assert observed_heads["second"] == commits["first"]
    assert repo.snapshot.branch_head("master") == commits["second"]
    assert repo.git.read_file("contexts/first.yaml", commit=commits["second"])
    assert repo.git.read_file("contexts/second.yaml", commit=commits["second"])


def test_concurrent_context_add_duplicate_name_loses_cleanly(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    start = threading.Barrier(3)
    reports: list[object] = []
    failures: list[BaseException] = []

    def add(description: str) -> None:
        try:
            start.wait(timeout=5)
            reports.append(
                add_context(
                    repo,
                    ContextAddRequest(name="race", description=description),
                    dry_run=False,
                )
            )
        except BaseException as exc:
            failures.append(exc)

    threads = [
        threading.Thread(target=add, args=("first",)),
        threading.Thread(target=add, args=("second",)),
    ]
    for thread in threads:
        thread.start()
    start.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=5)

    assert len(reports) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], ContextWorkflowError)
    assert repo.families.contexts.require(ContextRef("race")).id == "race"


def test_concurrent_predicate_adds_to_same_file_both_commit(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    start = threading.Barrier(3)
    failures: list[BaseException] = []

    def add(predicate_id: str) -> None:
        try:
            start.wait(timeout=5)
            add_predicate(
                repo,
                PredicateAddRequest(
                    file="race",
                    predicate_id=predicate_id,
                    arity=1,
                    arg_types=("entity",),
                ),
            )
        except BaseException as exc:
            failures.append(exc)

    threads = [
        threading.Thread(target=add, args=("p_first",)),
        threading.Thread(target=add, args=("p_second",)),
    ]
    for thread in threads:
        thread.start()
    start.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=5)

    assert failures == []
    document = repo.families.predicates.require(PredicateFileRef("race"))
    assert {entry.id for entry in document.predicates} == {"p_first", "p_second"}


def test_concurrent_rule_adds_to_same_file_both_commit(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    add_predicate(
        repo,
        PredicateAddRequest(
            file="race",
            predicate_id="race_predicate",
            arity=1,
            arg_types=("entity",),
        ),
    )
    start = threading.Barrier(3)
    failures: list[BaseException] = []

    def add(rule_id: str) -> None:
        try:
            start.wait(timeout=5)
            add_rule(
                repo,
                RuleAddRequest(
                    file="race",
                    paper="RacePaper",
                    rule_id=rule_id,
                    kind="defeasible",
                    head="race_predicate(X)",
                ),
            )
        except BaseException as exc:
            failures.append(exc)

    threads = [
        threading.Thread(target=add, args=("r_first",)),
        threading.Thread(target=add, args=("r_second",)),
    ]
    for thread in threads:
        thread.start()
    start.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=5)

    assert failures == []
    document = repo.families.rules.require(RuleFileRef("race"))
    assert {entry.id for entry in document.rules} == {"r_first", "r_second"}


def test_sidecar_build_serializes_with_source_promote(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import propstore.sidecar.build as build_module

    repo = Repository.init(tmp_path / "knowledge")
    _seed_ready_source_branch(repo, "race")
    build_entered = threading.Event()
    release_build = threading.Event()
    promote_done = threading.Event()
    failures: list[BaseException] = []

    def locked_build(*args, **kwargs) -> bool:
        build_entered.set()
        release_build.wait(timeout=5)
        return True

    monkeypatch.setattr(build_module, "_build_sidecar_locked", locked_build)

    def run_build() -> None:
        try:
            build_sidecar(repo, repo.sidecar_path, force=True)
        except BaseException as exc:
            failures.append(exc)

    def run_promote() -> None:
        try:
            promote_source_branch(repo, "race")
        except BaseException as exc:
            failures.append(exc)
        finally:
            promote_done.set()

    build_thread = threading.Thread(target=run_build)
    promote_thread = threading.Thread(target=run_promote)
    build_thread.start()
    assert build_entered.wait(timeout=5)
    promote_thread.start()
    assert not promote_done.wait(timeout=0.1)
    release_build.set()
    build_thread.join(timeout=5)
    promote_thread.join(timeout=5)

    assert failures == []
    assert promote_done.is_set()
