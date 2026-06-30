"""Single home for the provenance JSON-LD constants.

The named-graph carrier (:mod:`propstore.provenance`), the PROV-O export
(:mod:`propstore.provenance.prov_o`), and the typed records
(:mod:`propstore.provenance.records`) all share one JSON-LD ``@context`` and one
set of accepted URI scheme prefixes. They live here so there is exactly one
spelling of each (PLAN §12.6: no duplicated ``_CONTEXT`` / ``_URI_PREFIXES``).
This module imports nothing from the package, so importing it never cycles.
"""

from __future__ import annotations

JSONLD_CONTEXT: dict[str, str] = {
    "ps": "https://prop.store/ns#",
    "prov": "http://www.w3.org/ns/prov#",
    "swp": "http://www.w3.org/2004/03/trix/swp-2/",
}

# Schemes accepted for a provenance URI: a named graph id, a derived-from graph
# pointer, and every record identifier must be a real URI under one of these.
URI_SCHEME_PREFIXES: tuple[str, ...] = ("urn:", "ni://", "http://", "https://")
