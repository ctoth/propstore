"""Project initialization and packaged seed artifact workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from quire.documents import decode_yaml_mapping
from propstore.families.concepts.declaration import ConceptDocument
from propstore.families.forms.models import FORM_DOCUMENT_TYPE, FormDocument
from propstore.families.registry import (
    ConceptFileRef,
    FormRef,
)
from propstore.repository import Repository
from propstore.resources import _get_resource
from quire.documents import convert_document_value


class ProjectInitError(Exception):
    pass


@dataclass(frozen=True)
class ProjectInitReport:
    root: Path
    initialized: bool


def initialize_project(root: Path) -> ProjectInitReport:
    """Initialize a project and seed packaged forms/concepts when needed."""
    if Repository.is_propstore_repo(root):
        return ProjectInitReport(root=root, initialized=False)

    repo = Repository.init(root)
    form_documents = _seed_form_documents(repo)
    concept_documents = _seed_concept_documents(repo)

    if form_documents or concept_documents:
        if repo.git is None:
            raise ProjectInitError("init requires a git-backed repository")
        seed_files: Mapping[str | Path, bytes] = {
            **_render_seed_form_files(repo, form_documents),
            **_render_seed_concept_files(repo, concept_documents),
        }
        seed_commit = repo.require_git().commit_files(
            seed_files, "Seed default forms and concepts"
        )
        repo.write_bootstrap_manifest(seed_commit=seed_commit)

    return ProjectInitReport(root=root, initialized=True)


def _seed_provenance() -> dict[str, object]:
    return {
        "status": "stated",
        "witnesses": [
            {
                "asserter": "propstore",
                "timestamp": "2026-04-17T00:00:00Z",
                "source_artifact_code": "ps:resource:phase3-seed",
                "method": "packaged-resource",
            }
        ],
    }


def _ontology_reference(uri: str, label: str | None = None) -> dict[str, str]:
    reference = {"uri": uri}
    if label is not None:
        reference["label"] = label
    return reference


def _seed_proto_role_bundle(slot: dict[str, object]) -> dict[str, object] | None:
    bundle: dict[str, object] = {}
    proto_agent = slot.get("proto_agent")
    if isinstance(proto_agent, dict):
        bundle["proto_agent_entailments"] = [
            {
                "property": str(property_name),
                "value": float(value),
                "provenance": _seed_provenance(),
            }
            for property_name, value in proto_agent.items()
        ]
    proto_patient = slot.get("proto_patient")
    if isinstance(proto_patient, dict):
        bundle["proto_patient_entailments"] = [
            {
                "property": str(property_name),
                "value": float(value),
                "provenance": _seed_provenance(),
            }
            for property_name, value in proto_patient.items()
        ]
    return bundle or None


def _seed_qualia(entry: dict[str, object]) -> dict[str, object] | None:
    raw_qualia = entry.get("qualia")
    if not isinstance(raw_qualia, dict):
        return None
    qualia: dict[str, object] = {}
    for role, values in raw_qualia.items():
        if not isinstance(values, list):
            continue
        role_values = []
        for value in values:
            if not isinstance(value, dict):
                continue
            role_values.append(
                {
                    "reference": _ontology_reference(
                        str(value["reference"]),
                        str(value["label"]) if "label" in value else None,
                    ),
                    "type_constraint": {
                        "reference": _ontology_reference(str(value["type_constraint"]))
                    },
                    "provenance": _seed_provenance(),
                }
            )
        qualia[str(role)] = role_values
    return qualia or None


def _render_seed_form_files(
    repo: Repository,
    form_documents: list[tuple[FormRef, FormDocument]],
) -> dict[str | Path, bytes]:
    """Render typed seed forms to repo-relative YAML blobs for one commit."""
    rendered: dict[str | Path, bytes] = {}
    for ref, document in form_documents:
        prepared = repo.families.forms.prepare(ref, document)
        rendered[prepared.address.require_path()] = prepared.content
    return rendered


def _render_seed_concept_files(
    repo: Repository,
    concept_documents: list[tuple[ConceptFileRef, ConceptDocument]],
) -> dict[str | Path, bytes]:
    rendered: dict[str | Path, bytes] = {}
    for ref, document in concept_documents:
        prepared = repo.families.concepts.prepare(ref, document)
        rendered[prepared.address.require_path()] = prepared.content
    return rendered
