"""The ontology-entity side of a lemon lexicalization."""

from __future__ import annotations

import msgspec

from propstore.core.lemon.forms import require_text


class OntologyReference(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A reference to one ontology entity (the meaning a sense points at)."""

    uri: str
    label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "uri", require_text(self.uri, "uri"))
        if self.label is not None:
            object.__setattr__(self, "label", require_text(self.label, "label"))
