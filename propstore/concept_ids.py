from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from propstore.artifacts.documents.concepts import ConceptIdScanDocument
from propstore.artifacts.semantic_families import SEMANTIC_FAMILIES
from quire.documents import DocumentSchemaError, decode_document_path
from quire.refs import RefName
from quire.tree_path import TreePath as KnowledgePath, coerce_tree_path as coerce_knowledge_path

if TYPE_CHECKING:
    from quire.git_store import GitStore
    from propstore.repository import Repository

_CONCEPT_ID_RE = re.compile(r"^concept(\d+)$")
CONCEPT_ID_COUNTER_REF = RefName("refs/propstore/indexes/concept-id-counter")


def _numeric_concept_id(scan_doc: ConceptIdScanDocument) -> int | None:
    for logical_id in scan_doc.logical_ids:
        if logical_id.namespace != "propstore":
            continue
        match = _CONCEPT_ID_RE.match(logical_id.value)
        if match:
            return int(match.group(1))

    for candidate in (scan_doc.id, scan_doc.artifact_id):
        if not isinstance(candidate, str):
            continue
        match = _CONCEPT_ID_RE.match(candidate)
        if match:
            return int(match.group(1))
    return None


def next_concept_id(concepts_root: Path | KnowledgePath) -> int:
    root = coerce_knowledge_path(concepts_root)
    if not root.exists():
        return 1

    max_id = 0
    for entry in root.iterdir():
        if not entry.is_file() or entry.suffix != ".yaml":
            continue
        try:
            scan_doc = decode_document_path(entry, ConceptIdScanDocument)
        except DocumentSchemaError:
            continue
        numeric_id = _numeric_concept_id(scan_doc)
        if numeric_id is not None:
            max_id = max(max_id, numeric_id)
    return max_id + 1


def next_concept_id_for_repo(repo: Repository) -> int:
    concepts_root = SEMANTIC_FAMILIES.root_path("concept", repo.tree())
    if repo.git is None:
        return next_concept_id(concepts_root)
    return next_concept_id_for_git(repo.git, concepts_root)


def next_concept_id_for_git(git: GitStore, concepts_root: Path | KnowledgePath) -> int:
    counter = _read_concept_id_counter(git)
    if counter is not None:
        return counter + 1
    return next_concept_id(concepts_root)


def record_concept_id_for_repo(repo: Repository, numeric_id: int) -> None:
    if repo.git is None:
        return
    record_concept_id_counter(repo.git, numeric_id)


def record_concept_id_counter(git: GitStore, numeric_id: int) -> None:
    current = _read_concept_id_counter(git)
    if current is not None and current >= numeric_id:
        return
    git.write_blob_ref(CONCEPT_ID_COUNTER_REF, f"{numeric_id}\n".encode("ascii"))


def _read_concept_id_counter(git: GitStore) -> int | None:
    payload = git.read_blob_ref(CONCEPT_ID_COUNTER_REF)
    if payload is None:
        return None
    try:
        value = int(payload.decode("ascii").strip())
    except ValueError:
        return None
    if value < 0:
        return None
    return value
