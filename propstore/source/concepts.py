from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from propstore.cli.repository import Repository

from .common import load_yaml_from_branch, source_branch_name
from .registry import primary_branch_concept_match


def get_valid_form_names(repo: Repository) -> list[str] | None:
    forms_tree = repo.tree() / "forms"
    try:
        if not forms_tree.exists():
            return None
    except (FileNotFoundError, OSError):
        return None
    names = sorted(f.stem for f in forms_tree.iterdir() if f.suffix == ".yaml")
    return names if names else None


def validate_form_name(form: str, repo: Repository) -> None:
    valid_forms = get_valid_form_names(repo)
    if valid_forms is None:
        return
    if form not in valid_forms:
        raise ValueError(f"Unknown form {form!r}. Valid forms: {', '.join(valid_forms)}")


def normalize_source_concepts_document(repo: Repository, data: dict[str, Any]) -> dict[str, Any]:
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
            raise ValueError(f"concept #{index} is missing local_name/proposed_name/definition/form")
        validate_form_name(str(form).strip(), repo)
        normalized = copy.deepcopy(entry)
        normalized["local_name"] = str(local_name).strip()
        normalized["proposed_name"] = str(proposed_name).strip()
        normalized["definition"] = str(definition).strip()
        normalized["form"] = str(form).strip()
        aliases = normalized.get("aliases")
        if aliases is None:
            normalized["aliases"] = []
        registry_match = primary_branch_concept_match(repo, normalized["local_name"]) or primary_branch_concept_match(
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
    branch = source_branch_name(source_name)
    loaded = yaml.safe_load(concepts_file.read_text(encoding="utf-8")) or {}
    normalized = normalize_source_concepts_document(repo, loaded)
    return repo.git.commit_batch(
        adds={"concepts.yaml": yaml.safe_dump(normalized, sort_keys=False, allow_unicode=True).encode("utf-8")},
        deletes=[],
        message=f"Write concepts for {source_name}",
        branch=branch,
    )


def commit_source_concept_proposal(
    repo: Repository,
    source_name: str,
    *,
    local_name: str,
    definition: str,
    form: str,
    form_parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_form_name(form, repo)
    branch = source_branch_name(source_name)
    existing = load_yaml_from_branch(repo, branch, "concepts.yaml") or {"concepts": []}
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
    for normalized_entry in doc.get("concepts", []):
        if isinstance(normalized_entry, dict) and normalized_entry.get("local_name") == local_name:
            result: dict[str, Any] = {
                "local_name": local_name,
                "form": normalized_entry.get("form", form),
                "status": normalized_entry.get("status", "proposed"),
            }
            if normalized_entry.get("registry_match"):
                result["registry_match"] = normalized_entry["registry_match"]
            return result
    return {"local_name": local_name, "form": form, "status": "proposed"}
