from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import yaml

from propstore.cli.repository import Repository
from propstore.repo.branch import create_branch
from propstore.repo.merge_classifier import build_merge_framework
from propstore.repo.merge_commit import create_merge_commit
from propstore.repo.repo_import import commit_repo_import, plan_repo_import
from propstore.repo.structured_merge import (
    build_branch_structured_summary,
    build_structured_merge_candidates,
)
from propstore.claims import claim_file_payload, load_claim_files


REPO_ROOT = Path(__file__).resolve().parents[1]
PAPERS_ROOT = REPO_ROOT / "papers"


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _init_repo(root: Path) -> Repository:
    return Repository.init(root / "knowledge")


def _copy_claim_file(repo: Repository, *, source_path: Path, target_name: str | None = None) -> None:
    target = repo.root / "claims" / (target_name or source_path.name)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, target)
    assert repo.git is not None
    repo.git.commit_files(
        {f"claims/{target.name}": target.read_bytes()},
        f"add {target.name}",
    )


def _count_claims(claims_root: Path) -> int:
    return sum(
        len(claim_file_payload(claim_file).get("claims", []))
        for claim_file in load_claim_files(claims_root)
    )


def _branch_claim_stats(repo: Repository, branch: str) -> dict[str, Any]:
    assert repo.git is not None
    tree = repo.git.tree(commit=repo.git.branch_sha(branch))
    claims_root = tree / "claims"
    claim_files = load_claim_files(claims_root)

    raw_ids: list[str] = []
    per_file_counts: dict[str, int] = {}
    for claim_file in claim_files:
        claims = [
            claim
            for claim in claim_file_payload(claim_file).get("claims", [])
            if isinstance(claim, dict)
        ]
        per_file_counts[claim_file.filename] = len(claims)
        for claim in claims:
            claim_id = claim.get("id")
            if isinstance(claim_id, str):
                raw_ids.append(claim_id)

    duplicates = {
        claim_id: count
        for claim_id, count in Counter(raw_ids).items()
        if count > 1
    }
    return {
        "branch": branch,
        "claim_file_count": len(claim_files),
        "raw_claim_count": len(raw_ids),
        "unique_claim_id_count": len(set(raw_ids)),
        "duplicate_claim_ids": duplicates,
        "per_file_counts": per_file_counts,
    }


def _merged_claim_ids(repo: Repository, merge_sha: str) -> list[str]:
    assert repo.git is not None
    merged_tree = repo.git.tree(commit=merge_sha)
    merged_docs = load_claim_files(merged_tree / "claims")
    ids: list[str] = []
    for claim_file in merged_docs:
        for claim in claim_file_payload(claim_file).get("claims", []):
            if isinstance(claim, dict) and isinstance(claim.get("id"), str):
                ids.append(claim["id"])
    return ids


def _toy_claim(
    claim_id: str,
    statement: str,
    *,
    concept: str,
    value: float | None = None,
    conditions: list[str] | None = None,
    stances: list[dict[str, Any]] | None = None,
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
    if conditions:
        claim["conditions"] = conditions
    if stances:
        claim["stances"] = stances
    return claim


def _toy_doc(paper: str, claims: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "source": {
            "paper": paper,
            "extraction_model": "probe",
            "extraction_date": "2026-04-02",
        },
        "claims": claims,
    }


def _commit_doc(repo: Repository, relative_path: str, payload: dict[str, Any], message: str) -> None:
    data = yaml.safe_dump(payload, sort_keys=False).encode("utf-8")
    path = repo.root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    assert repo.git is not None
    repo.git.commit_files({relative_path.replace("\\", "/"): data}, message)


def experiment_toy_unique_ids(base: Path) -> dict[str, Any]:
    hub = _init_repo(base / "toy_unique_hub")
    researcher_a = _init_repo(base / "toy_unique_a")
    researcher_b = _init_repo(base / "toy_unique_b")

    _commit_doc(
        researcher_a,
        "claims/shared_a.yaml",
        _toy_doc(
            "shared-paper",
            [
                _toy_claim(
                    "shared.effect",
                    "Drug X lowers symptom Y.",
                    concept="drug_x_effect",
                    value=0.8,
                ),
                _toy_claim(
                    "a.only",
                    "A-only auxiliary claim.",
                    concept="a_aux",
                    value=1.0,
                ),
            ],
        ),
        "seed researcher A",
    )
    _commit_doc(
        researcher_b,
        "claims/shared_b.yaml",
        _toy_doc(
            "shared-paper",
            [
                _toy_claim(
                    "shared.effect",
                    "Drug X lowers symptom Y.",
                    concept="drug_x_effect",
                    value=0.8,
                ),
                _toy_claim(
                    "b.only",
                    "B-only auxiliary claim.",
                    concept="b_aux",
                    value=2.0,
                ),
            ],
        ),
        "seed researcher B",
    )

    plan_a = plan_repo_import(hub, researcher_a.root.parent)
    result_a = commit_repo_import(hub, plan_a)
    plan_b = plan_repo_import(hub, researcher_b.root.parent)
    result_b = commit_repo_import(hub, plan_b)

    assert hub.git is not None
    merge = build_merge_framework(hub.git, result_a.target_branch, result_b.target_branch)
    merge_sha = create_merge_commit(
        hub.git,
        result_a.target_branch,
        result_b.target_branch,
        target_branch="master",
    )
    return {
        "branch_a": result_a.target_branch,
        "branch_b": result_b.target_branch,
        "emitted_argument_ids": [argument.claim_id for argument in merge.arguments],
        "canonical_groups": {
            claim_id: sorted(
                argument.claim_id
                for argument in merge.arguments
                if argument.canonical_claim_id == claim_id
            )
            for claim_id in sorted({argument.canonical_claim_id for argument in merge.arguments})
        },
        "attack_count": len(merge.framework.attacks),
        "ignorance_count": len(merge.framework.ignorance),
        "merged_claim_ids": _merged_claim_ids(hub, merge_sha),
    }


def experiment_toy_same_semantics_different_ids(base: Path) -> dict[str, Any]:
    hub = _init_repo(base / "toy_different_ids_hub")
    researcher_a = _init_repo(base / "toy_different_ids_a")
    researcher_b = _init_repo(base / "toy_different_ids_b")

    shared_a = _toy_claim(
        "claim1",
        "Drug X lowers symptom Y.",
        concept="drug_x_effect",
        value=0.8,
    )
    shared_b = _toy_claim(
        "drug_x_effect.main_result",
        "Drug X lowers symptom Y.",
        concept="drug_x_effect",
        value=0.8,
    )
    _commit_doc(researcher_a, "claims/paper.yaml", _toy_doc("shared-paper", [shared_a]), "seed A")
    _commit_doc(researcher_b, "claims/paper.yaml", _toy_doc("shared-paper", [shared_b]), "seed B")

    plan_a = plan_repo_import(hub, researcher_a.root.parent)
    result_a = commit_repo_import(hub, plan_a)
    plan_b = plan_repo_import(hub, researcher_b.root.parent)
    result_b = commit_repo_import(hub, plan_b)

    assert hub.git is not None
    merge = build_merge_framework(hub.git, result_a.target_branch, result_b.target_branch)
    return {
        "branch_a": result_a.target_branch,
        "branch_b": result_b.target_branch,
        "emitted_argument_ids": [argument.claim_id for argument in merge.arguments],
        "canonical_claim_ids": [argument.canonical_claim_id for argument in merge.arguments],
        "branch_origins": {
            argument.claim_id: list(argument.branch_origins)
            for argument in merge.arguments
        },
        "attack_count": len(merge.framework.attacks),
        "ignorance_count": len(merge.framework.ignorance),
    }


def experiment_toy_structured_merge(base: Path) -> dict[str, Any]:
    hub = _init_repo(base / "toy_structured_hub")
    assert hub.git is not None

    base_sha = hub.git.commit_files({}, "seed")
    create_branch(hub.git, "researcher/a", source_commit=base_sha)
    create_branch(hub.git, "researcher/b", source_commit=base_sha)

    doc = _toy_doc(
        "structured-paper",
        [
            _toy_claim(
                "claim.alpha",
                "Alpha supports itself.",
                concept="alpha",
                stances=[{"target": "claim.beta", "type": "contradicts"}],
            ),
            _toy_claim(
                "claim.beta",
                "Beta is challenged by alpha.",
                concept="beta",
            ),
        ],
    )
    _commit_doc(hub, "claims/claims.yaml", doc, "master structured state")
    hub.git.commit_files(
        {"claims/claims.yaml": yaml.safe_dump(doc, sort_keys=False).encode("utf-8")},
        "structured a",
        branch="researcher/a",
    )
    hub.git.commit_files(
        {"claims/claims.yaml": yaml.safe_dump(doc, sort_keys=False).encode("utf-8")},
        "structured b",
        branch="researcher/b",
    )

    summary_a = build_branch_structured_summary(hub.git, "researcher/a")
    candidates = build_structured_merge_candidates(hub.git, "researcher/a", "researcher/b")
    return {
        "summary_claim_ids": list(summary_a.claim_ids),
        "projection_attack_count": len(summary_a.projection.framework.attacks),
        "lossiness": list(summary_a.lossiness),
        "candidate_count": len(candidates),
        "candidate_attack_counts": [len(candidate.attacks) for candidate in candidates],
    }


def experiment_actual_four_papers(base: Path) -> dict[str, Any]:
    hub = _init_repo(base / "actual_hub")
    researcher_a = _init_repo(base / "actual_a")
    researcher_b = _init_repo(base / "actual_b")

    shared_one = "Aarts_2015_EstimatingReproducibilityPsychologicalScience"
    shared_two = "Altmejd_2019_PredictingReplicabilitySocialScience"
    a_only = "Raff_2021_QuantifyingReproducibleMLResearch"
    b_only = "Yang_2020_EstimatingDeepReplicabilityScientific"

    paper_sets = {
        researcher_a: [shared_one, shared_two, a_only],
        researcher_b: [shared_one, shared_two, b_only],
    }
    for repo, papers in paper_sets.items():
        for paper in papers:
            source = PAPERS_ROOT / paper / "claims.yaml"
            _copy_claim_file(repo, source_path=source, target_name=f"{paper}.yaml")

    plan_a = plan_repo_import(hub, researcher_a.root.parent)
    result_a = commit_repo_import(hub, plan_a)
    plan_b = plan_repo_import(hub, researcher_b.root.parent)
    result_b = commit_repo_import(hub, plan_b)

    assert hub.git is not None
    stats_a = _branch_claim_stats(hub, result_a.target_branch)
    stats_b = _branch_claim_stats(hub, result_b.target_branch)
    merge = build_merge_framework(hub.git, result_a.target_branch, result_b.target_branch)
    merge_sha = create_merge_commit(
        hub.git,
        result_a.target_branch,
        result_b.target_branch,
        target_branch="master",
    )

    merged_ids = _merged_claim_ids(hub, merge_sha)
    merged_tree = hub.git.tree(commit=merge_sha)
    merged_paths = sorted(path.as_posix() for path in merged_tree.iterdir())
    return {
        "researcher_a_branch_stats": stats_a,
        "researcher_b_branch_stats": stats_b,
        "emitted_argument_count": len(merge.arguments),
        "emitted_argument_ids_head": [argument.claim_id for argument in merge.arguments[:10]],
        "canonical_claim_ids_head": [argument.canonical_claim_id for argument in merge.arguments[:10]],
        "attack_count": len(merge.framework.attacks),
        "ignorance_count": len(merge.framework.ignorance),
        "merged_claim_count": len(merged_ids),
        "merged_claim_ids": merged_ids,
        "merge_commit_top_level_entries": merged_paths,
    }


def experiment_fork_then_diverge(base: Path) -> dict[str, Any]:
    hub = _init_repo(base / "fork_hub")
    assert hub.git is not None

    base_doc = _toy_doc(
        "shared-paper",
        [
            _toy_claim("shared.paper.claim", "Shared base claim.", concept="shared", value=1.0),
        ],
    )
    _commit_doc(hub, "claims/shared.yaml", base_doc, "seed shared base")
    base_sha = hub.git.head_sha()
    assert base_sha is not None

    create_branch(hub.git, "researcher/a", source_commit=base_sha)
    create_branch(hub.git, "researcher/b", source_commit=base_sha)

    a_doc = _toy_doc(
        "researcher-a-paper",
        [
            _toy_claim("shared.paper.claim", "Shared base claim.", concept="shared", value=1.0),
            _toy_claim("new.same", "A and B both add this same claim.", concept="overlap", value=2.0),
            _toy_claim("a.unique", "Researcher A unique claim.", concept="a_unique", value=3.0),
        ],
    )
    b_doc = _toy_doc(
        "researcher-b-paper",
        [
            _toy_claim("shared.paper.claim", "Shared base claim.", concept="shared", value=1.0),
            _toy_claim("new.same", "A and B both add this same claim.", concept="overlap", value=2.0),
            _toy_claim("b.unique", "Researcher B unique claim.", concept="b_unique", value=4.0),
        ],
    )

    hub.git.commit_files(
        {"claims/shared.yaml": yaml.safe_dump(a_doc, sort_keys=False).encode("utf-8")},
        "researcher a diverges",
        branch="researcher/a",
    )
    hub.git.commit_files(
        {"claims/shared.yaml": yaml.safe_dump(b_doc, sort_keys=False).encode("utf-8")},
        "researcher b diverges",
        branch="researcher/b",
    )

    merge = build_merge_framework(hub.git, "researcher/a", "researcher/b")
    return {
        "emitted_argument_ids": [argument.claim_id for argument in merge.arguments],
        "branch_origins": {
            argument.claim_id: list(argument.branch_origins)
            for argument in merge.arguments
        },
        "attack_count": len(merge.framework.attacks),
        "ignorance_count": len(merge.framework.ignorance),
    }


def main() -> None:
    with TemporaryDirectory(prefix="propstore-mergeability-") as tempdir:
        base = Path(tempdir)
        results = {
            "toy_unique_ids": experiment_toy_unique_ids(base),
            "toy_same_semantics_different_ids": experiment_toy_same_semantics_different_ids(base),
            "toy_structured_merge": experiment_toy_structured_merge(base),
            "actual_four_papers": experiment_actual_four_papers(base),
            "fork_then_diverge": experiment_fork_then_diverge(base),
        }
        print(json.dumps(results, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
