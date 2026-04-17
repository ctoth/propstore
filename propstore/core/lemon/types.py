from __future__ import annotations

from dataclasses import dataclass

from propstore.provenance import Provenance


def _require_text(value: str, field: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field} must be non-empty")
    return cleaned


def _fold_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


@dataclass(frozen=True, slots=True)
class OntologyReference:
    """The ontology entity side of a lemon lexicalization."""

    uri: str
    label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "uri", _require_text(self.uri, "uri"))
        if self.label is not None:
            object.__setattr__(self, "label", _require_text(self.label, "label"))


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
        object.__setattr__(self, "written_rep", _require_text(self.written_rep, "written_rep"))
        object.__setattr__(self, "language", _require_text(self.language, "language"))
        if self.phonetic_rep is not None:
            object.__setattr__(
                self,
                "phonetic_rep",
                _require_text(self.phonetic_rep, "phonetic_rep"),
            )


@dataclass(frozen=True, slots=True)
class LexicalSense:
    """The sense-disambiguating link from a lexical entry to one ontology entity."""

    reference: OntologyReference
    usage: str | None = None
    provenance: Provenance | None = None

    def __post_init__(self) -> None:
        if self.usage is not None:
            object.__setattr__(self, "usage", _require_text(self.usage, "usage"))


@dataclass(frozen=True, slots=True)
class LexicalEntry:
    """A lemon lexical entry with forms and one or more senses."""

    identifier: str
    canonical_form: LexicalForm
    senses: tuple[LexicalSense, ...]
    other_forms: tuple[LexicalForm, ...] = ()
    physical_dimension_form: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "identifier", _require_text(self.identifier, "identifier"))
        if not self.senses:
            raise ValueError("LexicalEntry requires at least one lexical sense")
        if self.physical_dimension_form is not None:
            object.__setattr__(
                self,
                "physical_dimension_form",
                _require_text(self.physical_dimension_form, "physical_dimension_form"),
            )

    @property
    def forms(self) -> tuple[LexicalForm, ...]:
        return (self.canonical_form, *self.other_forms)

    @property
    def references(self) -> tuple[OntologyReference, ...]:
        return tuple(sense.reference for sense in self.senses)


def lexical_entry_identity_key(entry: LexicalEntry) -> tuple[str, str, str | None]:
    """Return exact lexical identity: language, canonical written form, dimensions."""

    return (
        _fold_text(entry.canonical_form.language),
        _fold_text(entry.canonical_form.written_rep),
        None if entry.physical_dimension_form is None else _fold_text(entry.physical_dimension_form),
    )
