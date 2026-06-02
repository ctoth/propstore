"""Form family document, stage, and pass ownership."""

from __future__ import annotations

from quire.documents import LoadedDocument, decode_document_path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from quire.tree_path import TreePath as KnowledgePath
    from propstore.families.forms.models import FormDocument


def load_form_documents(
    forms_dir: Path | KnowledgePath,
) -> list[LoadedDocument[FormDocument]]:
    from quire.tree_path import coerce_tree_path
    from propstore.families.forms.models import FORM_DOCUMENT_TYPE

    forms_root = coerce_tree_path(forms_dir)
    if not forms_root.exists():
        return []
    return [
        LoadedDocument(
            filename=entry.stem,
            artifact_path=entry,
            store_root=forms_root,
            document=decode_document_path(entry, FORM_DOCUMENT_TYPE),
        )
        for entry in forms_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]


__all__ = [
    "load_form_documents",
]
