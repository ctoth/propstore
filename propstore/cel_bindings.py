"""Standard synthetic CEL binding dimensions.

These names are part of the runtime environment contract, not part of CEL
parsing or type checking itself.
"""

from __future__ import annotations

STANDARD_SYNTHETIC_BINDING_DESCRIPTIONS: dict[str, str] = {
    "source": "Claim provenance source identifier used in authored conditions.",
    "domain": "Concept or claim domain binding used in authored conditions.",
    "source_kind": "Source kind binding exposed from claim provenance.",
    "origin_type": "Source origin type binding exposed from provenance metadata.",
    "name": "Generic runtime name binding used by some authored CEL surfaces.",
    "framework": "Framework binding exposed by generated or runtime conditions.",
    "mode": "Runtime mode binding used by generated or overlay conditions.",
    "variant": "Variant binding exposed by generated or runtime conditions.",
}

STANDARD_SYNTHETIC_BINDING_NAMES = tuple(STANDARD_SYNTHETIC_BINDING_DESCRIPTIONS)
