"""OntoLex-Lemon core objects for concept lexicalization."""

from propstore.core.lemon.forms import LexicalForm
from propstore.core.lemon.types import (
    LexicalEntry,
    LexicalSense,
    OntologyReference,
    lexical_entry_identity_key,
)

__all__ = [
    "LexicalEntry",
    "LexicalForm",
    "LexicalSense",
    "OntologyReference",
    "lexical_entry_identity_key",
]
