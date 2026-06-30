"""Checked-claim intermediate representation.

The flat-charter compiler does not rebuild the reference tree's
``SemanticClaim`` / ``ResolvedReference`` / ``ClaimFileEntry`` projection mass —
the charter *is* the document. After the claim semantic pass runs, each authored
:class:`~propstore.families.claims.Claim` becomes a :class:`CheckedClaim`: the
normalised claim (its ``conditions_ir`` filled from the checked CEL set) plus the
per-claim diagnostics and a ``blocked`` flag. Invalid claims are kept here as
``blocked`` — the quarantine-not-reject discipline (Z1) lives in this shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from propstore.families.claims import Claim
from propstore.semantic_passes.types import PassDiagnostic


@dataclass(frozen=True)
class CheckedClaim:
    """One claim after the AUTHORED -> CHECKED pass.

    ``claim`` is the normalised claim (``conditions_ir`` filled). ``blocked`` is
    set when the claim carried any error-level diagnostic; a blocked claim is
    still retained (it projects as a ``blocked`` sidecar row at materialize
    time), never dropped. ``diagnostics`` are this claim's own diagnostics.
    """

    claim: Claim
    blocked: bool
    diagnostics: tuple[PassDiagnostic, ...] = ()


@dataclass(frozen=True)
class ClaimCheckedBundle:
    """Every checked claim from a build, blocked ones included.

    This is the claim pipeline's terminal output. It is produced even when some
    claims are blocked — the runner never short-circuits the claim pipeline, so a
    semantic claim failure quarantines rather than aborting the build.
    """

    claims: tuple[CheckedClaim, ...] = ()

    @property
    def checked_claims(self) -> tuple[CheckedClaim, ...]:
        return tuple(checked for checked in self.claims if not checked.blocked)

    @property
    def blocked_claims(self) -> tuple[CheckedClaim, ...]:
        return tuple(checked for checked in self.claims if checked.blocked)

    @property
    def diagnostics(self) -> tuple[PassDiagnostic, ...]:
        return tuple(
            diagnostic for checked in self.claims for diagnostic in checked.diagnostics
        )
