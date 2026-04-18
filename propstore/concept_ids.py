from __future__ import annotations

import re
from pathlib import Path

from propstore.artifacts.documents.concepts import ConceptIdScanDocument
from propstore.artifacts.schema import DocumentSchemaError, decode_document_path
from propstore.knowledge_path import KnowledgePath, coerce_knowledge_path

_CONCEPT_ID_RE = re.compile(r"^concept(\d+)$")


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
