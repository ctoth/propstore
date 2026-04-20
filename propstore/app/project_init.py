"""Project initialization and packaged seed artifact workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from quire.documents import decode_yaml_mapping
from propstore.families.documents.concepts import ConceptDocument
from propstore.families.forms.documents import FormDocument
from propstore.families.registry import (
    ConceptFileRef,
    FormRef,
    PropstoreFamily,
    semantic_init_roots,
    semantic_root_path,
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
    paths: tuple[Path, ...]


def initialize_project(root: Path) -> ProjectInitReport:
    """Initialize a project and seed packaged forms/concepts when needed."""
    paths = _project_paths(root)
    if semantic_root_path(PropstoreFamily.CONCEPTS.value, root).is_dir():
        return ProjectInitReport(root=root, initialized=False, paths=paths)

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
        repo.git.commit_files(seed_files, "Seed default forms and concepts")
        repo.snapshot.sync_worktree()

    return ProjectInitReport(root=root, initialized=True, paths=paths)


def _project_paths(root: Path) -> tuple[Path, ...]:
    semantic_paths = [
        root / semantic_root
        for semantic_root in semantic_init_roots()
    ]
    return (
        *semantic_paths,
        root / "justifications",
        root / "sidecar",
        root / "sources",
    )


def _seed_form_documents(repo: Repository) -> list[tuple[FormRef, FormDocument]]:
    """Return typed default forms ready for artifact-store persistence."""
    form_documents: list[tuple[FormRef, FormDocument]] = []
    package_forms_dir = _get_resource("forms")
    if not package_forms_dir.is_dir():
        raise ProjectInitError(
            f"init requires packaged form resources at {package_forms_dir}"
        )
    for form_path in sorted(
        (
            child
            for child in package_forms_dir.iterdir()
            if child.is_file() and child.name.endswith(".yaml")
        ),
        key=lambda path: path.name,
    ):
        payload = decode_yaml_mapping(form_path.read_bytes(), source=str(form_path))
        form_documents.append(
            (
                FormRef(form_path.name.removesuffix(".yaml")),
                convert_document_value(payload, FormDocument, source=str(form_path)),
            )
        )
    return form_documents


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


def _seed_description_kind(entry: dict[str, object]) -> dict[str, object] | None:
    raw_kind = entry.get("description_kind")
    if not isinstance(raw_kind, dict):
        return None
    slots = []
    for slot in raw_kind.get("slots", []):
        if not isinstance(slot, dict):
            continue
        slot_name = str(slot["name"])
        slot_type = str(slot["type"])
        slot_payload: dict[str, object] = {
            "name": slot_name,
            "type_constraint": _ontology_reference(slot_type),
        }
        bundle = _seed_proto_role_bundle(slot)
        if bundle is not None:
            slot_payload["proto_role_bundle"] = bundle
        slots.append(slot_payload)
    return {
        "name": str(entry["name"]),
        "reference": _ontology_reference(str(entry["artifact_id"]), str(entry["name"])),
        "slots": slots,
    }


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


def _seed_concept_payload(entry: dict[str, object]) -> dict[str, object]:
    name = str(entry["name"])
    artifact_id = str(entry["artifact_id"])
    form = str(entry.get("form", "structural"))
    sense: dict[str, object] = {
        "reference": _ontology_reference(artifact_id, name),
        "usage": str(entry["definition"]),
        "provenance": _seed_provenance(),
    }
    description_kind = _seed_description_kind(entry)
    if description_kind is not None:
        sense["description_kind"] = description_kind
    qualia = _seed_qualia(entry)
    if qualia is not None:
        sense["qualia"] = qualia

    payload: dict[str, object] = {
        "status": "accepted",
        "artifact_id": artifact_id,
        "ontology_reference": _ontology_reference(artifact_id, name),
        "lexical_entry": {
            "identifier": f"entry:{entry['ref']}",
            "canonical_form": {
                "written_rep": name,
                "language": "en",
            },
            "senses": [sense],
            "physical_dimension_form": form,
        },
        "domain": "propstore-seed",
    }
    is_a = entry.get("is_a")
    if isinstance(is_a, str) and is_a:
        payload["relationships"] = [{"type": "is_a", "target": is_a}]
    return payload


def _seed_concept_documents(repo: Repository) -> list[tuple[ConceptFileRef, ConceptDocument]]:
    concept_documents: list[tuple[ConceptFileRef, ConceptDocument]] = []
    package_concepts_dir = _get_resource("concepts")
    if not package_concepts_dir.is_dir():
        raise ProjectInitError(
            f"init requires packaged concept resources at {package_concepts_dir}"
        )
    for seed_path in sorted(
        (
            child
            for child in package_concepts_dir.iterdir()
            if child.is_file() and child.name.endswith(".yaml")
        ),
        key=lambda path: path.name,
    ):
        resource = decode_yaml_mapping(seed_path.read_bytes(), source=str(seed_path))
        entries = resource.get("concepts")
        if not isinstance(entries, list):
            raise ProjectInitError(f"{seed_path} must contain a concepts list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise ProjectInitError(f"{seed_path} contains a non-mapping concept entry")
            ref = ConceptFileRef(str(entry["ref"]))
            concept_documents.append(
                (
                    ref,
                    convert_document_value(
                        _seed_concept_payload(entry),
                        ConceptDocument,
                        source=f"{seed_path}:{ref.name}",
                    ),
                )
            )
    return concept_documents


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
