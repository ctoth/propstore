from __future__ import annotations

import re
from typing import TYPE_CHECKING

from propstore.artifacts.documents.concepts import ConceptDocument
from quire.refs import RefName

if TYPE_CHECKING:
    from quire.git_store import GitStore
    from propstore.repository import Repository

_CONCEPT_ID_RE = re.compile(r"^concept(\d+)$")
CONCEPT_ID_COUNTER_REF = RefName("refs/propstore/indexes/concept-id-counter")


def _numeric_concept_id(document: ConceptDocument) -> int | None:
    for logical_id in document.logical_ids:
        if logical_id.namespace != "propstore":
            continue
        match = _CONCEPT_ID_RE.match(logical_id.value)
        if match:
            return int(match.group(1))

    if document.artifact_id is not None:
        match = _CONCEPT_ID_RE.match(document.artifact_id)
        if match:
            return int(match.group(1))
    return None


def next_concept_id_for_repo(repo: Repository) -> int:
    if repo.git is not None:
        counter = _read_concept_id_counter(repo.git)
        if counter is not None:
            return counter + 1
    max_id = 0
    for ref in repo.families.concepts.list():
        document = repo.families.concepts.require(ref)
        numeric_id = _numeric_concept_id(document)
        if numeric_id is not None:
            max_id = max(max_id, numeric_id)
    return max_id + 1


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
