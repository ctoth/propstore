from __future__ import annotations

from dataclasses import dataclass

from propstore.core.lemon.forms import LexicalForm, fold_text, require_text
from propstore.provenance import Provenance


@dataclass(frozen=True, slots=True)
class OntologyReference:
    """The ontology entity side of a lemon lexicalization."""

    uri: str
    label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "uri", require_text(self.uri, "uri"))
        if self.label is not None:
            object.__setattr__(self, "label", require_text(self.label, "label"))


@dataclass(frozen=True, slots=True)
class LexicalSense:
    """The sense-disambiguating link from a lexical entry to one ontology entity."""

    reference: OntologyReference
    usage: str | None = None
    provenance: Provenance | None = None

    def __post_init__(self) -> None:
        if self.usage is not None:
            object.__setattr__(self, "usage", require_text(self.usage, "usage"))


@dataclass(frozen=True, slots=True)
class LexicalEntry:
    """A lemon lexical entry with forms and one or more senses."""

    identifier: str
    canonical_form: LexicalForm
    senses: tuple[LexicalSense, ...]
    other_forms: tuple[LexicalForm, ...] = ()
    physical_dimension_form: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "identifier", require_text(self.identifier, "identifier"))
        if not self.senses:
            raise ValueError("LexicalEntry requires at least one lexical sense")
        if self.physical_dimension_form is not None:
            object.__setattr__(
                self,
                "physical_dimension_form",
                require_text(self.physical_dimension_form, "physical_dimension_form"),
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
        fold_text(entry.canonical_form.language),
        fold_text(entry.canonical_form.written_rep),
        None if entry.physical_dimension_form is None else fold_text(entry.physical_dimension_form),
    )
