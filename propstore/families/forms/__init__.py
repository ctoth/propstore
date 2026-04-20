"""Form family document, stage, and pass ownership."""

from __future__ import annotations

from quire.documents import decode_document_path

from propstore.families.forms.documents import FormDocument
from propstore.families.forms.stages import LoadedForm

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from quire.tree_path import TreePath as KnowledgePath


def load_form_documents(forms_dir: Path | KnowledgePath) -> list[LoadedForm]:
    from quire.tree_path import coerce_tree_path

    forms_root = coerce_tree_path(forms_dir)
    if not forms_root.exists():
        return []
    return [
        LoadedForm(
            filename=entry.stem,
            document=decode_document_path(entry, FormDocument),
        )
        for entry in forms_root.iterdir()
        if entry.is_file() and entry.suffix == ".yaml"
    ]


__all__ = [
    "FormDocument",
    "LoadedForm",
    "load_form_documents",
]
