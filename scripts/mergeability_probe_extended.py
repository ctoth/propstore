from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml

from propstore.cli.repository import Repository
from propstore.identity import normalize_claim_file_payload
from propstore.repo.branch import create_branch
from propstore.repo.merge_classifier import build_merge_framework
from propstore.repo.merge_report import semantic_candidate_details
from propstore.repo.repo_import import commit_repo_import, plan_repo_import


def _init_repo(root: Path) -> Repository:
    return Repository.init(root / "knowledge")


def _dump_yaml(data: dict[str, Any]) -> bytes:
    return yaml.safe_dump(data, sort_keys=False).encode("utf-8")


def _commit_yaml(
    repo: Repository,
    relative_path: str,
    data: dict[str, Any],
    message: str,
    *,
    branch: str | None = None,
    normalize: bool = False,
    default_namespace: str | None = None,
) -> str:
    payload = data
    if normalize:
        payload, _ = normalize_claim_file_payload(data, default_namespace=default_namespace)
    content = _dump_yaml(payload)
    assert repo.git is not None
    effective_branch = "master" if branch is None else branch
    return repo.git.commit_files({relative_path: content}, message, branch=effective_branch)


def _toy_claim(
    claim_id: str,
    statement: str,
    *,
    concept: str,
    value: float | None = None,
) -> dict[str, Any]:
    claim: dict[str, Any] = {
        "id": claim_id,
        "type": "parameter" if value is not None else "observation",
        "statement": statement,
        "concepts": [concept],
        "provenance": {"paper": "toy-paper", "page": 1},
    }
    if value is not None:
        claim["concept"] = concept
        claim["value"] = value
        claim["unit"] = "K"
    return claim


def _doc(claims: list[dict[str, Any]], *, paper: str | None) -> dict[str, Any]:
    data: dict[str, Any] = {"claims": claims}
    if paper is not None:
        data["source"] = {"paper": paper}
    return data


def _merge_summary(repo: Repository, branch_a: str, branch_b: str) -> dict[str, Any]:
    assert repo.git is not None
    merge = build_merge_framework(repo.git, branch_a, branch_b)
    return {
        "argument_count": len(merge.arguments),
        "argument_ids": [argument.claim_id for argument in merge.arguments],
        "canonical_claim_ids": [argument.canonical_claim_id for argument in merge.arguments],
        "branch_origins": {
            argument.claim_id: list(argument.branch_origins)
            for argument in merge.arguments
        },
        "attack_count": len(merge.framework.attacks),
        "ignorance_count": len(merge.framework.ignorance),
        "semantic_candidate_count": len(merge.semantic_candidates),
        "semantic_candidate_details": semantic_candidate_details(merge),
    }


def experiment_raw_branch_merge_without_identity(base: Path) -> dict[str, Any]:
    repo = _init_repo(base / "raw_branch_merge")
    assert repo.git is not None
    base_sha = repo.git.commit_files({}, "seed")
    branch_name = "researcher/b"
    create_branch(repo.git, branch_name, source_commit=base_sha)

    left = _doc(
        [_toy_claim("claim1", "Same statement.", concept="c", value=1.0)],
        paper="SharedPaper",
    )
    right = _doc(
        [_toy_claim("claim1", "Same statement.", concept="c", value=1.0)],
        paper="SharedPaper",
    )
    _commit_yaml(repo, "claims/shared.yaml", left, "left raw", normalize=False)
    _commit_yaml(repo, "claims/shared.yaml", right, "right raw", branch=branch_name, normalize=False)

    return _merge_summary(repo, "master", branch_name)


def experiment_imported_same_paper_same_ids_conflict(base: Path) -> dict[str, Any]:
    hub = _init_repo(base / "import_same_id_conflict_hub")
    researcher_a = _init_repo(base / "import_same_id_conflict_a")
    researcher_b = _init_repo(base / "import_same_id_conflict_b")

    _commit_yaml(
        researcher_a,
        "claims/shared.yaml",
        _doc([_toy_claim("claim1", "Shared result.", concept="drug_x", value=0.8)], paper="SharedPaper"),
        "seed a",
        normalize=False,
    )
    _commit_yaml(
        researcher_b,
        "claims/shared.yaml",
        _doc([_toy_claim("claim1", "Shared result.", concept="drug_x", value=0.2)], paper="SharedPaper"),
        "seed b",
        normalize=False,
    )

    result_a = commit_repo_import(hub, plan_repo_import(hub, researcher_a.root.parent))
    result_b = commit_repo_import(hub, plan_repo_import(hub, researcher_b.root.parent))
    summary = _merge_summary(hub, result_a.target_branch, result_b.target_branch)
    summary["branch_a"] = result_a.target_branch
    summary["branch_b"] = result_b.target_branch
    return summary


def experiment_imported_missing_source_namespace(base: Path) -> dict[str, Any]:
    hub = _init_repo(base / "missing_source_namespace_hub")
    researcher_a = _init_repo(base / "missing_source_namespace_a")
    researcher_b = _init_repo(base / "missing_source_namespace_b")

    raw_doc = _doc(
        [_toy_claim("claim1", "Same statement.", concept="drug_x", value=0.8)],
        paper=None,
    )
    _commit_yaml(researcher_a, "claims/shared.yaml", raw_doc, "seed a", normalize=False)
    _commit_yaml(researcher_b, "claims/shared.yaml", raw_doc, "seed b", normalize=False)

    result_a = commit_repo_import(hub, plan_repo_import(hub, researcher_a.root.parent))
    result_b = commit_repo_import(hub, plan_repo_import(hub, researcher_b.root.parent))
    summary = _merge_summary(hub, result_a.target_branch, result_b.target_branch)
    summary["branch_a"] = result_a.target_branch
    summary["branch_b"] = result_b.target_branch
    return summary


def experiment_normalized_fork_then_diverge(base: Path) -> dict[str, Any]:
    repo = _init_repo(base / "normalized_fork")
    assert repo.git is not None
    base_doc = _doc(
        [_toy_claim("base.claim", "Shared base claim.", concept="base", value=1.0)],
        paper="SharedPaper",
    )
    base_sha = _commit_yaml(
        repo,
        "claims/shared.yaml",
        base_doc,
        "seed base",
        normalize=True,
    )
    branch_name = "researcher/b"
    create_branch(repo.git, branch_name, source_commit=base_sha)

    left_doc = _doc(
        [
            _toy_claim("base.claim", "Shared base claim.", concept="base", value=1.0),
            _toy_claim("new.same", "Both researchers add this.", concept="overlap", value=2.0),
            _toy_claim("left.only", "Left only.", concept="left", value=3.0),
        ],
        paper="SharedPaper",
    )
    right_doc = _doc(
        [
            _toy_claim("base.claim", "Shared base claim.", concept="base", value=1.0),
            _toy_claim("new.same", "Both researchers add this.", concept="overlap", value=2.0),
            _toy_claim("right.only", "Right only.", concept="right", value=4.0),
        ],
        paper="SharedPaper",
    )

    _commit_yaml(repo, "claims/shared.yaml", left_doc, "left diverges", normalize=True)
    _commit_yaml(
        repo,
        "claims/shared.yaml",
        right_doc,
        "right diverges",
        branch=branch_name,
        normalize=True,
    )

    return _merge_summary(repo, "master", branch_name)


def main() -> None:
    with TemporaryDirectory(prefix="propstore-mergeability-extended-") as tempdir:
        base = Path(tempdir)
        results = {
            "raw_branch_merge_without_identity": experiment_raw_branch_merge_without_identity(base),
            "imported_same_paper_same_ids_conflict": experiment_imported_same_paper_same_ids_conflict(base),
            "imported_missing_source_namespace": experiment_imported_missing_source_namespace(base),
            "normalized_fork_then_diverge": experiment_normalized_fork_then_diverge(base),
        }
        print(json.dumps(results, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
