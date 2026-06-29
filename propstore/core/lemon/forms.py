"""Lexical forms — the surface-realization side of a lemon lexicalization.

OntoLex-Lemon and Buitelaar (2011) keep linguistic *form* strictly separate from
ontology/world facts. A :class:`LexicalForm` therefore carries only written /
phonetic realizations and a language tag. Physical dimensions are NOT a form
property: they live on :class:`~propstore.core.lemon.types.LexicalEntry`
(``physical_dimension_form``). ``forbid_unknown_fields`` makes that boundary
enforceable — constructing a form with a dimensional keyword raises ``TypeError``
(see ``tests/test_lemon_concepts.py``).
"""

from __future__ import annotations

import msgspec


def require_text(value: str, field: str) -> str:
    """Return ``value`` stripped, raising ``ValueError`` if it is blank."""

    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field} must be non-empty")
    return cleaned


def fold_text(value: str) -> str:
    """Case/whitespace-fold text for identity comparison (not for storage)."""

    return " ".join(value.strip().casefold().split())


class LexicalForm(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A surface realization of a lexical entry: written form + language."""

    written_rep: str
    language: str
    phonetic_rep: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "written_rep", require_text(self.written_rep, "written_rep"))
        object.__setattr__(self, "language", require_text(self.language, "language"))
        if self.phonetic_rep is not None:
            object.__setattr__(
                self,
                "phonetic_rep",
                require_text(self.phonetic_rep, "phonetic_rep"),
            )
