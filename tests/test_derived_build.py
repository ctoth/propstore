"""World-sidecar materialize: content-hash cache key, rebuild-on-change, projection.

These pin the 9-0-rest-B build spine:

* ``materialize_world_sidecar`` returns ``built=True`` on the first build and
  ``built=False`` on an unchanged rebuild — quire owns rebuild-on-change, propstore
  only supplies the content hash (``TestRebuildSkipping`` analog);
* the content hash is sensitive to the source revision and the
  ``PROPSTORE_SIDECAR_CACHE_BUST`` knob (``test_codex5_sidecar_cache`` analog);
* ``_build_sidecar_file`` populates the charter-derived schema directly via
  ``session.add_family`` (the projection IS the charter).
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest

from propstore.derived_build import (
    _SIDECAR_CACHE_DEPENDENCIES,
    materialize_world_sidecar,
    world_sidecar_hash,
    world_sidecar_hash_inputs,
)
from propstore.derived_schema import build_world_sidecar_schema
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.repository import Repository


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            statement="x",
        ),
        message="m",
    )
    return repo


def test_first_build_builds_then_unchanged_rebuild_skips(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    handle, built = materialize_world_sidecar(repo)
    assert built is True
    assert Path(handle.path).is_file()

    handle2, built2 = materialize_world_sidecar(repo)
    assert built2 is False
    assert handle2.path == handle.path


def test_force_rebuilds_even_when_unchanged(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    materialize_world_sidecar(repo)
    _, built = materialize_world_sidecar(repo, force=True)
    assert built is True


def test_source_change_invalidates_cache_and_rebuilds(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    materialize_world_sidecar(repo)
    # A new authored claim moves the head sha, changing the content hash.
    repo.families.claim.save(
        "cl2",
        Claim(
            claim_id="cl2",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            statement="y",
        ),
        message="m",
    )
    _, built = materialize_world_sidecar(repo)
    assert built is True


def test_cache_bust_env_changes_content_hash(monkeypatch: pytest.MonkeyPatch) -> None:
    schema = build_world_sidecar_schema()
    monkeypatch.delenv("PROPSTORE_SIDECAR_CACHE_BUST", raising=False)
    base = world_sidecar_hash("rev", schema_hash=schema.catalog_hash)
    monkeypatch.setenv("PROPSTORE_SIDECAR_CACHE_BUST", "bust")
    busted = world_sidecar_hash("rev", schema_hash=schema.catalog_hash)
    assert base != busted


def test_hash_inputs_carry_the_expected_keys() -> None:
    schema = build_world_sidecar_schema()
    inputs = world_sidecar_hash_inputs("rev", schema_hash=schema.catalog_hash)
    assert inputs["source_revision"] == "rev"
    assert inputs["schema_hash"] == schema.catalog_hash
    assert "passes" in inputs
    assert "family_contract_versions" in inputs
    assert "dependency_pins" in inputs
    assert "build_time_config" in inputs
    assert inputs["grounding_config"] == {"max_arguments": None}


@pytest.fixture
def compiler_lockfile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    lockfile = tmp_path / "uv.lock"
    lockfile.write_bytes((Path(__file__).resolve().parents[1] / "uv.lock").read_bytes())
    monkeypatch.setattr("propstore.derived_build._sidecar_lockfile", lambda: lockfile)
    return lockfile


def _change_dependency(
    lockfile: Path, name: str, *, remove: bool = False, git_revision: bool = False
) -> None:
    sections = lockfile.read_text(encoding="utf-8").split("[[package]]")
    for index, section in enumerate(sections):
        if not section.startswith(f'\nname = "{name}"\n'):
            continue
        if remove:
            del sections[index]
        elif git_revision:
            prefix, source = section.split('git = "', 1)
            url, suffix = source.split('"', 1)
            repository, _ = url.split("?rev=", 1)
            revision = "0" * 40
            sections[index] = (
                f'{prefix}git = "{repository}?rev={revision}#{revision}"{suffix}'
            )
        else:
            prefix, version = section.split('version = "', 1)
            _, suffix = version.split('"', 1)
            sections[index] = f'{prefix}version = "999.0.0"{suffix}'
        lockfile.write_text("[[package]]".join(sections), encoding="utf-8")
        return
    raise AssertionError(f"{name} is absent from the real lockfile")


def test_dependency_selection_resolves_every_declared_distribution() -> None:
    inputs = world_sidecar_hash_inputs("rev", schema_hash="schema")
    assert set(inputs["dependency_pins"]) == set(_SIDECAR_CACHE_DEPENDENCIES)
    assert {"condition-ir", "eq-equiv", "cel-parser", "formal-argumentation"} <= set(
        inputs["dependency_pins"]
    )


@pytest.mark.parametrize("dependency", _SIDECAR_CACHE_DEPENDENCIES)
def test_compiler_dependency_pin_invalidates_hash(
    compiler_lockfile: Path, dependency: str
) -> None:
    before = world_sidecar_hash("same-knowledge-commit", schema_hash="same-schema")
    _change_dependency(compiler_lockfile, dependency)
    after = world_sidecar_hash("same-knowledge-commit", schema_hash="same-schema")
    assert before != after


@pytest.mark.parametrize(
    "dependency", ("condition-ir", "eq-equiv", "formal-argumentation", "quire")
)
def test_compiler_git_revision_invalidates_hash(
    compiler_lockfile: Path, dependency: str
) -> None:
    before = world_sidecar_hash("rev", schema_hash="schema")
    _change_dependency(compiler_lockfile, dependency, git_revision=True)
    assert world_sidecar_hash("rev", schema_hash="schema") != before


def test_unrelated_dependency_does_not_invalidate_hash(compiler_lockfile: Path) -> None:
    before = world_sidecar_hash("rev", schema_hash="schema")
    _change_dependency(compiler_lockfile, "click")
    assert world_sidecar_hash("rev", schema_hash="schema") == before


def test_missing_compiler_dependency_is_an_error(compiler_lockfile: Path) -> None:
    _change_dependency(compiler_lockfile, "condition-ir", remove=True)
    with pytest.raises(ValueError, match="world-sidecar.*condition-ir"):
        world_sidecar_hash("rev", schema_hash="schema")


@pytest.mark.parametrize("project_name", (None, "unrelated-project"))
def test_installed_package_rejects_unrelated_adjacent_lockfile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, project_name: str | None
) -> None:
    monkeypatch.setattr(
        "propstore.derived_build.__file__", str(tmp_path / "propstore/derived_build.py")
    )
    (tmp_path / "uv.lock").write_bytes(
        (Path(__file__).resolve().parents[1] / "uv.lock").read_bytes()
    )
    if project_name:
        (tmp_path / "pyproject.toml").write_text(
            f'[project]\nname = "{project_name}"\n', encoding="utf-8"
        )
    with pytest.raises(ValueError, match="compiler dependency lockfile is absent"):
        world_sidecar_hash("rev", schema_hash="schema")


def test_source_checkout_uses_its_current_compiler_lockfile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "propstore.derived_build.__file__", str(tmp_path / "propstore/derived_build.py")
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "propstore"\n', encoding="utf-8"
    )
    lockfile = tmp_path / "uv.lock"
    lockfile.write_bytes((Path(__file__).resolve().parents[1] / "uv.lock").read_bytes())
    before = world_sidecar_hash("rev", schema_hash="schema")
    _change_dependency(lockfile, "condition-ir", git_revision=True)
    assert world_sidecar_hash("rev", schema_hash="schema") != before
    _change_dependency(lockfile, "condition-ir", remove=True)
    with pytest.raises(ValueError, match="world-sidecar.*condition-ir"):
        world_sidecar_hash("rev", schema_hash="schema")


def test_built_wheel_materializes_with_its_bundled_compiler_identity(
    tmp_path: Path,
) -> None:
    project_root = Path(__file__).resolve().parents[1]
    expected = world_sidecar_hash_inputs("rev", schema_hash="schema")["dependency_pins"]
    subprocess.run(
        [
            "uv", "build", "--wheel", "--python", sys.executable,
            "--out-dir", str(tmp_path / "dist"), str(project_root),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    (wheel,) = (tmp_path / "dist").glob("*.whl")
    installed = tmp_path / "installed"
    with ZipFile(wheel) as archive:
        assert archive.read("propstore/_compiler_dependencies.lock") == (
            project_root / "uv.lock"
        ).read_bytes()
        archive.extractall(installed)
    # This is deliberately not Propstore's lockfile. The wheel must ignore it.
    (installed / "uv.lock").write_text("not valid TOML", encoding="utf-8")
    probe = '''
import json
import sys
from pathlib import Path
import propstore.derived_build as build
from propstore.repository import Repository
assert Path(build.__file__).resolve().is_relative_to(Path.cwd())
assert build._sidecar_lockfile().parent == Path(build.__file__).parent
assert build.world_sidecar_hash_inputs("rev", schema_hash="schema")["dependency_pins"] == json.loads(sys.argv[1])
repo = Repository.init(Path(sys.argv[2]))
handle, built = build.materialize_world_sidecar(repo)
assert built and Path(handle.path).is_file()
again, built = build.materialize_world_sidecar(repo)
assert not built and again.path == handle.path
'''
    subprocess.run(
        [sys.executable, "-c", probe, json.dumps(expected), str(tmp_path / "knowledge")],
        cwd=installed,
        env={**os.environ, "PYTHONPATH": str(installed)},
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("dependency", ("condition-ir", "eq-equiv", "z3-solver"))
def test_compiler_dependency_change_rebuilds_existing_sidecar(
    tmp_path: Path, compiler_lockfile: Path, dependency: str
) -> None:
    repo = _repo(tmp_path)
    revision = repo.require_git().head_sha()
    first, built = materialize_world_sidecar(repo)
    assert built
    unchanged, built = materialize_world_sidecar(repo)
    assert not built
    assert unchanged.path == first.path

    _change_dependency(
        compiler_lockfile, dependency, git_revision=dependency != "z3-solver"
    )
    changed, built = materialize_world_sidecar(repo)
    assert built
    assert changed.path != first.path
    assert repo.require_git().head_sha() == revision
    assert Path(first.path).is_file()
    assert Path(changed.path).is_file()


def test_hash_changes_with_source_revision() -> None:
    schema = build_world_sidecar_schema()
    a = world_sidecar_hash("rev-a", schema_hash=schema.catalog_hash)
    b = world_sidecar_hash("rev-b", schema_hash=schema.catalog_hash)
    assert a != b


def test_hash_changes_with_grounding_budget() -> None:
    schema = build_world_sidecar_schema()
    bounded = world_sidecar_hash(
        "rev", schema_hash=schema.catalog_hash, grounding_max_arguments=1
    )
    differently_bounded = world_sidecar_hash(
        "rev", schema_hash=schema.catalog_hash, grounding_max_arguments=2
    )
    assert bounded != differently_bounded


def test_build_projects_charter_families_into_sidecar(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    handle, _ = materialize_world_sidecar(repo)
    conn = sqlite3.connect(handle.path)
    try:
        assert conn.execute("SELECT concept_id FROM concept").fetchall() == [("c1",)]
        assert conn.execute("SELECT claim_id FROM claim").fetchall() == [("cl1",)]
        assert conn.execute("SELECT context_id FROM context").fetchall() == [("ctx1",)]
        assert conn.execute(
            "SELECT configuration_id, max_arguments FROM grounding_build_configuration"
        ).fetchall() == [("grounding", None)]
    finally:
        conn.close()


def test_historical_build_projects_config_from_requested_commit(tmp_path: Path) -> None:
    repo = _repo(tmp_path)
    git = repo.require_git()
    historical_commit = git.commit_files(
        {"propstore.yaml": b"grounding_max_arguments: 3\n"},
        "Set historical grounding budget",
    )
    git.commit_files(
        {"propstore.yaml": b"grounding_max_arguments: 7\n"},
        "Set current grounding budget",
    )

    handle, _ = materialize_world_sidecar(repo, commit=historical_commit)

    conn = sqlite3.connect(handle.path)
    try:
        assert conn.execute(
            "SELECT configuration_id, max_arguments FROM grounding_build_configuration"
        ).fetchall() == [("grounding", 3)]
    finally:
        conn.close()
