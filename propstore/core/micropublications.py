"""The micropublication bundle as the argumentation layer consumes it.

An :class:`ActiveMicropublication` is a frozen field-subset VIEW over the
canonical :class:`~propstore.families.micropublications.Micropublication`
charter — built by attribute access in :meth:`ActiveMicropublication.from_micropublication`,
never re-typed from a payload mapping. It is the micropublication counterpart of
:class:`~propstore.core.active_claims.ActiveClaim`.

The Clark principal-claim rule is *not* restated here: it is imported from the
charter module, so the stored bundle and the runtime view can never disagree
about which claim a bundle is about.
"""

from __future__ import annotations

import msgspec

from propstore.families.micropublications import (
    Micropublication,
    principal_claim_id,
    validate_principal_claim,
)


class ActiveMicropublication(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, omit_defaults=True
):
    """One micropublication bundle as the ATMS and argumentation layers see it."""

    artifact_id: str
    context_id: str
    claim_ids: tuple[str, ...]
    principal_claim: str | None = None
    assumptions: tuple[str, ...] = ()
    source: str | None = None

    def __post_init__(self) -> None:
        if not self.claim_ids:
            raise ValueError("micropublication claims must not be empty")
        validate_principal_claim(self.claim_ids, self.principal_claim)

    @classmethod
    def from_micropublication(
        cls, micropublication: Micropublication
    ) -> ActiveMicropublication:
        """Project the canonical charter into the active view. Pure attribute access."""

        return cls(
            artifact_id=micropublication.artifact_id,
            context_id=micropublication.context_id,
            claim_ids=micropublication.claims,
            principal_claim=micropublication.principal_claim,
            assumptions=micropublication.assumptions,
            source=micropublication.source,
        )

    @property
    def principal_claim_id(self) -> str:
        """The principal claim ``c`` this bundle is about."""

        return principal_claim_id(self.claim_ids, self.principal_claim)


__all__ = ["ActiveMicropublication"]
