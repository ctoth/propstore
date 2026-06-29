"""Lexical entries and senses — the lemon entry/sense backbone.

A :class:`LexicalEntry` is one lemon lexical entry: a canonical surface form,
optional other forms, and one OR MORE :class:`LexicalSense` links into ontology
references. This shape encodes the lemon laws directly:

* **Polysemy** is multiple senses on one entry (the entry requires ``>= 1`` sense).
* **Homography** is distinct entries sharing one written form: the *form* identity
  key collides while the *entry* identity key (which includes the identifier) does
  not — homographs are never silently collapsed.
* **The form/dimension boundary**: physical dimensions live on the ENTRY
  (``physical_dimension_form``), never on :class:`~propstore.core.lemon.forms.LexicalForm`.
  Phase 2a models only the *reference* to a physical-dimension form (a name); the
  forms/dimensions layer itself is Phase 2b.

``LexicalSense.reference`` is functional (one sense → one ontology entity); a
sense additionally carries optional sense-level semantic content (qualia,
description kind, Dowty role bundles) and optional provenance. Identity EXCLUDES
provenance: :func:`lexical_entry_identity_key` is computed from the identifier and
the surface form only, so attaching or changing provenance never changes what an
entry *is* (PLAN.md §12.4).
"""

from __future__ import annotations

import msgspec

from propstore.core.lemon.description_kinds import DescriptionKind
from propstore.core.lemon.forms import LexicalForm, fold_text, require_text
from propstore.core.lemon.proto_roles import ProtoRoleBundle
from propstore.core.lemon.qualia import QualiaStructure
from propstore.core.lemon.references import OntologyReference
from propstore.provenance import Provenance


class LexicalSense(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """The sense-disambiguating link from a lexical entry to one ontology entity."""

    reference: OntologyReference
    usage: str | None = None
    provenance: Provenance | None = None
    qualia: QualiaStructure | None = None
    description_kind: DescriptionKind | None = None
    role_bundles: dict[str, ProtoRoleBundle] | None = None

    def __post_init__(self) -> None:
        if self.usage is not None:
            object.__setattr__(self, "usage", require_text(self.usage, "usage"))
        if self.role_bundles is not None:
            for role_name in self.role_bundles:
                require_text(role_name, "role_bundles key")


class LexicalEntry(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
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


def lexical_form_identity_key(entry: LexicalEntry) -> tuple[str, str, str | None]:
    """Return the surface-form identity: (language, written form, dimensions).

    Homographs share this key (same written form + language + dimensions) while
    remaining distinct entries — provenance plays no part.
    """

    return (
        fold_text(entry.canonical_form.language),
        fold_text(entry.canonical_form.written_rep),
        None
        if entry.physical_dimension_form is None
        else fold_text(entry.physical_dimension_form),
    )


def lexical_entry_identity_key(entry: LexicalEntry) -> tuple[str, str, str, str | None]:
    """Return the lexical-entry identity (identifier + form), excluding provenance.

    Two entries differing only in sense provenance share this key; two homographs
    (same form, different identifier) do not.
    """

    form_key = lexical_form_identity_key(entry)
    return (entry.identifier, form_key[0], form_key[1], form_key[2])
