from __future__ import annotations

from dataclasses import dataclass


def require_text(value: str, field: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field} must be non-empty")
    return cleaned


def fold_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


@dataclass(frozen=True, slots=True)
class LexicalForm:
    """A surface realization of a lexical entry.

    Buitelaar 2011 and OntoLex-Lemon keep linguistic form separate from
    ontology/world facts. Physical dimensions therefore belong on the entry or
    an adjacent measurement document, not here.
    """

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
