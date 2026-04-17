from __future__ import annotations

from dataclasses import dataclass

from propstore.core.lemon.forms import require_text


@dataclass(frozen=True, slots=True)
class OntologyReference:
    """The ontology entity side of a lemon lexicalization."""

    uri: str
    label: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "uri", require_text(self.uri, "uri"))
        if self.label is not None:
            object.__setattr__(self, "label", require_text(self.label, "label"))
