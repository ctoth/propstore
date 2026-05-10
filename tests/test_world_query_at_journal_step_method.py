"""Production-method tests for ``WorldQuery.at_journal_step``.

These supplement the bridge free-function property tests by constructing a
real ``WorldQuery`` over a current-schema sidecar and invoking the public
method directly.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, cast

from propstore.conflict_detector import ConflictClass
from propstore.sidecar.schema import build_minimal_world_model_schema
from propstore.stances import StanceType
from propstore.support_revision.history import (
    JournalOperator,
    TransitionJournal,
    TransitionOperation,
)
from propstore.world.model import WorldQuery
from quire.tree_path import FilesystemTreePath
from tests.fixtures.journal import (
    make_assertion_atom,
    make_journal_entry,
    make_state,
    single_chapter_journal,
)


def _claim_id(local_id: str) -> str:
    return f"propstore:claim:test/{local_id}"


def _make_atom(local_id: str, ix: int):
    return make_assertion_atom(
        relation_local=f"method_rel_{ix}",
        subject=f"method_subject_{ix}",
        value=f"method_value_{ix}",
        source_claim_local_ids=(local_id,),
    )


def _write_sidecar(
    sidecar_path: Path,
    *claim_ids: str,
    stance_pairs: tuple[tuple[str, str, str], ...] = (),
    conflict_pairs: tuple[tuple[str, str], ...] = (),
) -> None:
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(sidecar_path)
    try:
        build_minimal_world_model_schema(conn)
        for seq, claim_id in enumerate(claim_ids):
            conn.execute(
                """
                INSERT INTO claim_core (
                    id, primary_logical_id, logical_ids_json, version_id,
                    content_hash, seq, type, target_concept,
                    source_slug, source_paper, provenance_page, provenance_json,
                    context_id, premise_kind, branch
                ) VALUES (
                    ?, ?, '[]', '', ?, ?, 'parameter', NULL,
                    NULL, 'method-test', 0, NULL,
                    NULL, 'ordinary', 'master'
                )
                """,
                (claim_id, claim_id, f"hash:{claim_id}", seq),
            )
        for source_id, target_id, stance_type in stance_pairs:
            conn.execute(
                """
                INSERT INTO relation_edge (
                    source_kind, source_id, relation_type, target_kind, target_id
                ) VALUES ('claim', ?, ?, 'claim', ?)
                """,
                (source_id, stance_type, target_id),
            )
        for claim_a_id, claim_b_id in conflict_pairs:
            conn.execute(
                """
                INSERT INTO conflict_witness (
                    concept_id, claim_a_id, claim_b_id, warning_class
                ) VALUES ('concept:test', ?, ?, ?)
                """,
                (claim_a_id, claim_b_id, ConflictClass.CONFLICT.value),
            )
        conn.commit()
    finally:
        conn.close()


def _world_query_for_claims(tmp_path: Path, *claim_ids: str) -> WorldQuery:
    sidecar_path = tmp_path / "sidecar" / "propstore.sqlite"
    _write_sidecar(sidecar_path, *claim_ids)
    return WorldQuery(sidecar_path=sidecar_path)


class _RepoForHistoricalQuery:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.sidecar_path = root / "sidecar" / "propstore.sqlite"

    def tree(self, commit: str | None = None):
        return FilesystemTreePath.from_filesystem_path(self.root)


def test_world_query_method_projects_single_step_journal(tmp_path: Path) -> None:
    atom = _make_atom("method_single", 1)
    journal = single_chapter_journal(
        initial_state=make_state(atoms=(), accepted_atom_ids=()),
        revision_atoms=(atom,),
    )
    world = _world_query_for_claims(tmp_path, _claim_id("method_single"))
    try:
        view = world.at_journal_step(journal, 0)
        assert view.claim_ids() == {_claim_id("method_single")}
    finally:
        world.close()


def test_world_query_method_projects_intermediate_step(tmp_path: Path) -> None:
    first = _make_atom("method_first", 1)
    second = _make_atom("method_second", 2)
    third = _make_atom("method_third", 3)
    journal = single_chapter_journal(
        initial_state=make_state(atoms=(), accepted_atom_ids=()),
        revision_atoms=(first, second, third),
    )
    world = _world_query_for_claims(
        tmp_path,
        _claim_id("method_first"),
        _claim_id("method_second"),
        _claim_id("method_third"),
    )
    try:
        view = world.at_journal_step(journal, 1)
        assert view.claim_ids() == {
            _claim_id("method_first"),
            _claim_id("method_second"),
        }
    finally:
        world.close()


def test_world_query_method_projects_empty_acceptance_step(tmp_path: Path) -> None:
    atom = _make_atom("method_empty", 1)
    state = make_state(atoms=(atom,), accepted_atom_ids=())
    entry = make_journal_entry(
        state_in=state,
        operation=TransitionOperation(
            name="contract",
            input_atom_id=None,
            target_atom_ids=(atom.atom_id,),
        ),
        operator=JournalOperator.CONTRACT,
        operator_input={"atom_id": atom.atom_id},
        state_out=state,
    )
    world = _world_query_for_claims(tmp_path, _claim_id("method_empty"))
    try:
        view = world.at_journal_step(TransitionJournal(entries=(entry,)), 0)
        assert view.claim_ids() == set()
    finally:
        world.close()


def test_world_query_historical_query_builds_temp_sidecar_for_commit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    current_sidecar = tmp_path / "current" / "propstore.sqlite"
    historical_claim_a = _claim_id("historical_a")
    historical_claim_b = _claim_id("historical_b")
    _write_sidecar(current_sidecar, historical_claim_a)
    repo = _RepoForHistoricalQuery(tmp_path / "knowledge")
    repo.root.mkdir()
    requested_commits: list[str] = []

    def fake_build_sidecar(
        repo_arg: object,
        sidecar_path: Path,
        force: bool = False,
        **kwargs: Any,
    ) -> bool:
        requested_commits.append(str(kwargs["commit_hash"]))
        _write_sidecar(
            sidecar_path,
            historical_claim_a,
            historical_claim_b,
            stance_pairs=(
                (
                    historical_claim_a,
                    historical_claim_b,
                    StanceType.SUPPORTS.value,
                ),
            ),
            conflict_pairs=((historical_claim_a, historical_claim_b),),
        )
        return True

    from propstore.sidecar import build as sidecar_build

    monkeypatch.setattr(sidecar_build, "build_sidecar", fake_build_sidecar)
    world = WorldQuery(cast(Any, repo), sidecar_path=current_sidecar)
    commit_sha = "f" * 40
    try:
        with world.historical_query(commit_sha) as historical:
            assert requested_commits == [commit_sha]
            assert set(historical.claims_by_ids({historical_claim_a, historical_claim_b})) == {
                historical_claim_a,
                historical_claim_b,
            }
            assert historical.all_claim_stances()[0].stance_type is StanceType.SUPPORTS
            conflict = historical.conflicts()[0]
            assert str(conflict.claim_a_id) == historical_claim_a
            assert str(conflict.claim_b_id) == historical_claim_b
    finally:
        world.close()
