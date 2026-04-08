"""Concept alignment artifacts on proposal branches."""

from __future__ import annotations

import copy
from collections import Counter
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import yaml

from propstore.cli.repository import Repository
from propstore.identity import compute_concept_version_id, derive_concept_artifact_id
from propstore.repo.branch import branch_head, create_branch
from propstore.repo.merge_framework import PartialArgumentationFramework
from propstore.repo.paf_queries import credulously_accepted_arguments, skeptically_accepted_arguments
from propstore.uri import DEFAULT_URI_AUTHORITY, concept_tag_uri, source_tag_uri


CONCEPT_PROPOSAL_BRANCH = "proposal/concepts"


def _slug(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value.strip().lower())
    cleaned = cleaned.strip("_-")
    return cleaned or "alignment"


def _load_yaml(repo: Repository, branch: str, relpath: str) -> dict[str, Any] | None:
    tip = branch_head(repo.git, branch)
    if tip is None:
        return None
    try:
        return yaml.safe_load(repo.git.read_file(relpath, commit=tip)) or {}
    except FileNotFoundError:
        return None


def commit_source_concept_proposal(
    repo: Repository,
    source_name: str,
    *,
    local_name: str,
    definition: str,
    form: str,
    form_parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Propose a concept on a source branch.

    Returns a dict with keys: ``local_name``, ``status`` ("linked" or
    "proposed"), and optionally ``registry_match`` (with ``artifact_id``
    and ``canonical_name``) when linked to an existing concept.
    """
    _validate_form_name(form, repo)
    branch = f"source/{source_name}"
    existing = _load_yaml(repo, branch, "concepts.yaml") or {"concepts": []}
    concepts = list(existing.get("concepts", []))
    concepts = [entry for entry in concepts if not (isinstance(entry, dict) and entry.get("local_name") == local_name)]
    entry: dict[str, Any] = {
        "local_name": local_name,
        "proposed_name": local_name,
        "definition": definition,
        "form": form,
    }
    if form_parameters:
        entry["form_parameters"] = form_parameters
    concepts.append(entry)
    doc = normalize_source_concepts_document(repo, {"concepts": concepts})
    repo.git.commit_batch(
        adds={"concepts.yaml": yaml.safe_dump(doc, sort_keys=False, allow_unicode=True).encode("utf-8")},
        deletes=[],
        message=f"Propose concepts for {source_name}",
        branch=branch,
    )
    # Find the entry we just added to return its status info.
    for entry in doc.get("concepts", []):
        if isinstance(entry, dict) and entry.get("local_name") == local_name:
            result: dict[str, Any] = {
                "local_name": local_name,
                "form": entry.get("form", form),
                "status": entry.get("status", "proposed"),
            }
            if entry.get("registry_match"):
                result["registry_match"] = entry["registry_match"]
            return result
    return {"local_name": local_name, "form": form, "status": "proposed"}


def _get_valid_form_names(repo: Repository) -> list[str] | None:
    """Return sorted valid form names from the repo, or None if no forms directory."""
    forms_tree = repo.tree() / "forms"
    try:
        if not forms_tree.exists():
            return None
    except (FileNotFoundError, OSError):
        return None
    names = sorted(f.stem for f in forms_tree.iterdir() if f.suffix == ".yaml")
    return names if names else None


def _validate_form_name(form: str, repo: Repository) -> None:
    """Raise ValueError if form is not a known form in the repo."""
    valid_forms = _get_valid_form_names(repo)
    if valid_forms is None:
        return  # No forms directory — skip validation
    if form not in valid_forms:
        raise ValueError(
            f"Unknown form {form!r}. Valid forms: {', '.join(valid_forms)}"
        )


def normalize_source_concepts_document(repo: Repository, data: dict[str, Any]) -> dict[str, Any]:
    from propstore.source_ops import _master_concept_match

    concepts = data.get("concepts", [])
    if not isinstance(concepts, list):
        raise ValueError("concepts.yaml must contain a 'concepts' list")

    normalized_concepts: list[dict[str, Any]] = []
    for index, entry in enumerate(concepts, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"concept #{index} must be a mapping")
        local_name = entry.get("local_name") or entry.get("proposed_name")
        proposed_name = entry.get("proposed_name") or entry.get("local_name")
        definition = entry.get("definition")
        form = entry.get("form")
        if not all(isinstance(value, str) and value.strip() for value in (local_name, proposed_name, definition, form)):
            raise ValueError(
                f"concept #{index} is missing local_name/proposed_name/definition/form"
            )
        _validate_form_name(str(form).strip(), repo)
        normalized = copy.deepcopy(entry)
        normalized["local_name"] = str(local_name).strip()
        normalized["proposed_name"] = str(proposed_name).strip()
        normalized["definition"] = str(definition).strip()
        normalized["form"] = str(form).strip()
        aliases = normalized.get("aliases")
        if aliases is None:
            normalized["aliases"] = []
        registry_match = _master_concept_match(repo, normalized["local_name"]) or _master_concept_match(
            repo,
            normalized["proposed_name"],
        )
        normalized["status"] = "linked" if registry_match is not None else "proposed"
        if registry_match is not None:
            normalized["registry_match"] = registry_match
        else:
            normalized.pop("registry_match", None)
        normalized_concepts.append(normalized)
    return {"concepts": normalized_concepts}


def commit_source_concepts_batch(repo: Repository, source_name: str, concepts_file: Path) -> str:
    branch = f"source/{source_name}"
    loaded = yaml.safe_load(concepts_file.read_text(encoding="utf-8")) or {}
    normalized = normalize_source_concepts_document(repo, loaded)
    return repo.git.commit_batch(
        adds={"concepts.yaml": yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8")},
        deletes=[],
        message=f"Write concepts for {source_name}",
        branch=branch,
    )


def _token_overlap(left: str, right: str) -> float:
    left_tokens = {token for token in _slug(left).split("_") if token}
    right_tokens = {token for token in _slug(right).split("_") if token}
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _classify_relation(left: dict[str, Any], right: dict[str, Any]) -> str:
    if left["proposed_name"] == right["proposed_name"] and left["form"] == right["form"]:
        return "attack" if left["definition"] != right["definition"] else "non_attack"
    if left["form"] == right["form"] and _token_overlap(left["definition"], right["definition"]) >= 0.5:
        return "ignorance"
    return "non_attack"


def build_alignment_artifact(
    proposals: list[dict[str, Any]],
    *,
    authority: str = DEFAULT_URI_AUTHORITY,
) -> dict[str, Any]:
    enriched: list[dict[str, Any]] = []
    id_counts: Counter[str] = Counter()
    for proposal in proposals:
        local_handle = str(proposal["local_handle"])
        base_id = f"alt_{_slug(local_handle)}"
        id_counts[base_id] += 1
        arg_id = base_id if id_counts[base_id] == 1 else f"{base_id}_{id_counts[base_id]}"
        enriched.append(
            {
                "id": arg_id,
                "source": proposal["source"],
                "local_handle": local_handle,
                "proposed_name": proposal["proposed_name"],
                "proposed_uri": concept_tag_uri(
                    proposal["proposed_name"],
                    authority=authority,
                ),
                "definition": proposal["definition"],
                "form": proposal["form"],
            }
        )

    if not enriched:
        raise ValueError("Need at least one proposal")

    cluster_seed = enriched[0]["proposed_name"]
    cluster_id = f"align:{_slug(cluster_seed)}"
    arguments = [argument["id"] for argument in enriched]
    attacks: list[list[str]] = []
    ignorance: list[list[str]] = []
    non_attacks: list[list[str]] = []

    by_id = {argument["id"]: argument for argument in enriched}
    for attacker, target in product(arguments, arguments):
        if attacker == target:
            non_attacks.append([attacker, target])
            continue
        relation = _classify_relation(by_id[attacker], by_id[target])
        if relation == "attack":
            attacks.append([attacker, target])
        elif relation == "ignorance":
            ignorance.append([attacker, target])
        else:
            non_attacks.append([attacker, target])

    paf = PartialArgumentationFramework(
        arguments=frozenset(arguments),
        attacks=frozenset(tuple(pair) for pair in attacks),
        ignorance=frozenset(tuple(pair) for pair in ignorance),
        non_attacks=frozenset(tuple(pair) for pair in non_attacks),
    )
    skeptical = sorted(skeptically_accepted_arguments(paf))
    credulous = sorted(credulously_accepted_arguments(paf))
    operator_scores = {
        operator: {argument: int(argument in credulous) for argument in arguments}
        for operator in ("sum", "max", "leximax")
    }

    return {
        "kind": "concept_alignment_framework",
        "id": cluster_id,
        "sources": [str(argument["source"]) for argument in enriched],
        "arguments": enriched,
        "framework": {
            "attacks": attacks,
            "ignorance": ignorance,
            "non_attacks": non_attacks,
        },
        "queries": {
            "skeptical_acceptance": skeptical,
            "credulous_acceptance": credulous,
            "operator_scores": operator_scores,
        },
        "decision": {
            "status": "open",
            "accepted": [],
            "rejected": [],
            "promoted_concept": None,
        },
    }


def align_sources(repo: Repository, source_branches: list[str]) -> dict[str, Any]:
    proposals: list[dict[str, Any]] = []
    for branch in source_branches:
        concepts_doc = _load_yaml(repo, branch, "concepts.yaml") or {}
        source_doc = _load_yaml(repo, branch, "source.yaml") or {}
        branch_source_name = branch.split("/", 1)[1] if "/" in branch else branch
        source_uri = str(source_doc.get("id") or source_tag_uri(branch_source_name, authority=repo.uri_authority))
        for entry in concepts_doc.get("concepts", []) or []:
            if not isinstance(entry, dict):
                continue
            proposals.append(
                {
                    "source": source_uri,
                    "local_handle": str(entry.get("local_name") or entry.get("proposed_name") or "concept"),
                    "proposed_name": str(entry.get("proposed_name") or entry.get("local_name") or "concept"),
                    "definition": str(entry.get("definition") or ""),
                    "form": str(entry.get("form") or "structural"),
                }
            )
    artifact = build_alignment_artifact(proposals, authority=repo.uri_authority)
    if branch_head(repo.git, CONCEPT_PROPOSAL_BRANCH) is None:
        create_branch(repo.git, CONCEPT_PROPOSAL_BRANCH)
    slug = artifact["id"].split(":", 1)[1]
    repo.git.commit_batch(
        adds={
            f"merge/concepts/{slug}.yaml": yaml.safe_dump(artifact, sort_keys=False, allow_unicode=True).encode("utf-8")
        },
        deletes=[],
        message=f"Align concepts for {slug}",
        branch=CONCEPT_PROPOSAL_BRANCH,
    )
    return artifact


def load_alignment_artifact(repo: Repository, cluster_id: str) -> tuple[str, dict[str, Any]]:
    slug = cluster_id.split(":", 1)[1] if ":" in cluster_id else cluster_id
    artifact = _load_yaml(repo, CONCEPT_PROPOSAL_BRANCH, f"merge/concepts/{slug}.yaml")
    if artifact is None:
        raise FileNotFoundError(cluster_id)
    return slug, artifact


def save_alignment_artifact(repo: Repository, slug: str, artifact: dict[str, Any], *, message: str) -> str:
    return repo.git.commit_batch(
        adds={
            f"merge/concepts/{slug}.yaml": yaml.safe_dump(artifact, sort_keys=False, allow_unicode=True).encode("utf-8")
        },
        deletes=[],
        message=message,
        branch=CONCEPT_PROPOSAL_BRANCH,
    )


def decide_alignment(repo: Repository, cluster_id: str, *, accept: list[str], reject: list[str]) -> dict[str, Any]:
    slug, artifact = load_alignment_artifact(repo, cluster_id)
    updated = copy.deepcopy(artifact)
    updated["decision"]["accepted"] = accept
    updated["decision"]["rejected"] = reject
    updated["decision"]["status"] = "decided"
    save_alignment_artifact(repo, slug, updated, message=f"Decide concept alignment {cluster_id}")
    return updated


def promote_alignment(repo: Repository, cluster_id: str) -> dict[str, Any]:
    slug, artifact = load_alignment_artifact(repo, cluster_id)
    accepted = list(artifact.get("decision", {}).get("accepted", []))
    if not accepted:
        raise ValueError(f"No accepted alternatives recorded for {cluster_id}")
    accepted_id = accepted[0]
    selected = None
    for argument in artifact.get("arguments", []):
        if isinstance(argument, dict) and argument.get("id") == accepted_id:
            selected = argument
            break
    if selected is None:
        raise ValueError(f"Accepted alternative {accepted_id!r} not found")

    canonical_name = str(selected["proposed_name"])
    local_handle = _slug(canonical_name)
    concept_doc = {
        "canonical_name": canonical_name,
        "status": "accepted",
        "definition": str(selected.get("definition") or ""),
        "domain": "source",
        "form": str(selected.get("form") or "structural"),
        "artifact_id": derive_concept_artifact_id("propstore", local_handle),
        "logical_ids": [
            {"namespace": "source", "value": local_handle},
            {"namespace": "propstore", "value": local_handle},
        ],
    }
    concept_doc["version_id"] = compute_concept_version_id(concept_doc)
    repo.git.commit_batch(
        adds={
            f"concepts/{local_handle}.yaml": yaml.safe_dump(concept_doc, sort_keys=False, allow_unicode=True).encode("utf-8")
        },
        deletes=[],
        message=f"Promote concept alignment {cluster_id}",
        branch="master",
    )
    repo.git.sync_worktree()
    updated = copy.deepcopy(artifact)
    updated["decision"]["promoted_concept"] = concept_tag_uri(
        local_handle,
        authority=repo.uri_authority,
    )
    updated["decision"]["status"] = "promoted"
    save_alignment_artifact(repo, slug, updated, message=f"Record concept promotion {cluster_id}")
    return updated
