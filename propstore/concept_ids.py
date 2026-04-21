from __future__ import annotations

import re
import threading
import time
from typing import TYPE_CHECKING, Any, cast

from dulwich.file import FileLocked
from dulwich.objects import Blob

from propstore.families.concepts.documents import ConceptDocument
from quire.refs import RefName

if TYPE_CHECKING:
    from quire.git_store import GitStore
    from propstore.repository import Repository

_CONCEPT_ID_RE = re.compile(r"^concept(\d+)$")
CONCEPT_ID_COUNTER_REF = RefName("refs/propstore/indexes/concept-id-counter")
_COUNTER_WRITE_ATTEMPTS = 64
_COUNTER_REF_LOCK = threading.Lock()


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
        return _reserve_next_concept_id(repo)
    return _next_concept_id_from_documents(repo)


def _next_concept_id_from_documents(repo: Repository) -> int:
    max_id = 0
    for ref in repo.families.concepts.iter():
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
    for _attempt in range(_COUNTER_WRITE_ATTEMPTS):
        current, ref_sha = _read_concept_id_counter_state(git)
        if current is not None and current >= numeric_id:
            return
        if _write_concept_id_counter_if_unchanged(git, ref_sha, numeric_id):
            return
    raise RuntimeError("could not record concept ID counter after concurrent updates")


def _read_concept_id_counter(git: GitStore) -> int | None:
    value, _ref_sha = _read_concept_id_counter_state(git)
    return value


def _reserve_next_concept_id(repo: Repository) -> int:
    if repo.git is None:
        return _next_concept_id_from_documents(repo)
    for _attempt in range(_COUNTER_WRITE_ATTEMPTS):
        current, ref_sha = _read_concept_id_counter_state(repo.git)
        numeric_id = current + 1 if current is not None else _next_concept_id_from_documents(repo)
        if _write_concept_id_counter_if_unchanged(repo.git, ref_sha, numeric_id):
            return numeric_id
    raise RuntimeError("could not reserve concept ID after concurrent updates")


def _read_concept_id_counter_state(git: GitStore) -> tuple[int | None, str | None]:
    ref_sha = git.read_ref(CONCEPT_ID_COUNTER_REF)
    if ref_sha is None:
        return None, None
    try:
        obj = git.raw_repo[ref_sha.encode("ascii")]
    except KeyError:
        return None, ref_sha
    if not isinstance(obj, Blob):
        return None, ref_sha
    try:
        value = int(obj.data.decode("ascii").strip())
    except ValueError:
        return None, ref_sha
    if value < 0:
        return None, ref_sha
    return value, ref_sha


def _write_concept_id_counter_if_unchanged(
    git: GitStore,
    expected_ref_sha: str | None,
    numeric_id: int,
) -> bool:
    with _COUNTER_REF_LOCK:
        try:
            blob_sha = git.store_blob(f"{numeric_id}\n".encode("ascii")).encode("ascii")
            refs = cast(Any, git.raw_repo.refs)
            ref_name = cast(Any, CONCEPT_ID_COUNTER_REF.as_bytes())
            new_ref = cast(Any, blob_sha)
            if expected_ref_sha is None:
                return bool(refs.add_if_new(ref_name, new_ref))
            old_ref = cast(Any, expected_ref_sha.encode("ascii"))
            return bool(refs.set_if_equals(ref_name, old_ref, new_ref))
        except (FileLocked, PermissionError):
            time.sleep(0.001)
            return False
