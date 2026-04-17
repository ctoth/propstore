from __future__ import annotations

import yaml

from propstore.repository import Repository
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.grounding.loading import build_grounded_bundle
from propstore.sidecar.build import build_sidecar
from propstore.world import WorldModel


def test_build_grounded_bundle_returns_explicit_empty_for_rule_free_repo(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    bundle = build_grounded_bundle(repo.tree())

    assert bundle == GroundedRulesBundle.empty()


def test_build_grounded_bundle_rejects_rules_without_predicates(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {
            "rules/rules.yaml": yaml.dump(
                {
                    "source": {"paper": "test"},
                    "rules": [
                        {
                            "id": "r1",
                            "kind": "defeasible",
                            "head": {"predicate": "p"},
                        }
                    ],
                },
                sort_keys=False,
            ).encode("utf-8")
        },
        "add rules without predicates",
    )

    try:
        build_grounded_bundle(repo.tree())
    except ValueError as exc:
        assert "rules/" in str(exc)
        assert "predicates/" in str(exc)
    else:
        raise AssertionError("Expected grounding load boundary to reject rules/ without predicates/")


def test_world_model_grounding_bundle_uses_repo_knowledge_root_and_caches(tmp_path) -> None:
    repo = Repository.init(tmp_path / "knowledge")
    build_sidecar(repo.tree(), repo.sidecar_path, force=True)

    wm = WorldModel(repo)
    try:
        first = wm.grounding_bundle()
        second = wm.grounding_bundle()
    finally:
        wm.close()

    assert first == GroundedRulesBundle.empty()
    assert first is second
