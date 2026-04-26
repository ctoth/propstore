from __future__ import annotations

from gunray import GroundAtom, complement


class GunrayComplementEncoder:
    def complement(self, predicate: str) -> str:
        return complement(GroundAtom(predicate=predicate, arguments=())).predicate


GUNRAY_COMPLEMENT_ENCODER = GunrayComplementEncoder()
