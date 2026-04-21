from __future__ import annotations

from gunray.disagreement import complement as gunray_complement
from gunray.types import GroundAtom


class GunrayComplementEncoder:
    def complement(self, predicate: str) -> str:
        return gunray_complement(GroundAtom(predicate=predicate, arguments=())).predicate


GUNRAY_COMPLEMENT_ENCODER = GunrayComplementEncoder()
