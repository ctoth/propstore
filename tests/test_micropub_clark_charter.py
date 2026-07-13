"""The micropublication charter enforces Clark 2014's formal components.

Clark, Ciccarese & Goble 2014: MP = (A, mp, c, A_c, Φ, R). The minimal form is
one Claim plus one Attribution ("every element must have Attribution"), and the
principal claim c is the distinguished greatest element of the support order.
The charter enforces the representable parts — nonempty claims, attribution,
and a well-defined principal claim — while R (the support/challenge relation)
is delegated to the stance layer.
"""

from __future__ import annotations

import pytest

from propstore.core.micropublications import ActiveMicropublication
from propstore.families.micropublications import Micropublication


def _bundle(**overrides: object) -> Micropublication:
    fields: dict[str, object] = {
        "artifact_id": "ni:///sha-256;abc",
        "context_id": "ctx1",
        "claims": ("cl1",),
        "source": "src:paper",
    }
    fields.update(overrides)
    return Micropublication(**fields)  # type: ignore[arg-type]


class TestClarkMinimalForm:
    def test_bundle_requires_at_least_one_claim(self) -> None:
        with pytest.raises(ValueError, match="claim"):
            _bundle(claims=())

    def test_bundle_requires_attribution(self) -> None:
        with pytest.raises(ValueError, match="[Aa]ttribution"):
            _bundle(source=None)

    def test_provenance_counts_as_attribution(self) -> None:
        from propstore.provenance import Provenance, ProvenanceStatus

        provenance = Provenance(
            status=ProvenanceStatus.STATED,
            witnesses=(),
            operations=("authored",),
        )
        bundle = _bundle(source=None, provenance=provenance)
        assert bundle.provenance is provenance


class TestPrincipalClaim:
    def test_single_claim_bundle_derives_its_principal(self) -> None:
        bundle = _bundle()
        assert bundle.principal_claim_id == "cl1"

    def test_multi_claim_bundle_requires_explicit_principal(self) -> None:
        with pytest.raises(ValueError, match="principal"):
            _bundle(claims=("cl1", "cl2"))

    def test_explicit_principal_is_honored(self) -> None:
        bundle = _bundle(claims=("cl1", "cl2"), principal_claim="cl2")
        assert bundle.principal_claim_id == "cl2"

    def test_principal_must_be_a_member_of_claims(self) -> None:
        with pytest.raises(ValueError, match="principal"):
            _bundle(claims=("cl1", "cl2"), principal_claim="cl3")


class TestActiveMicropublicationPrincipal:
    def test_single_claim_active_bundle_derives_its_principal(self) -> None:
        active = ActiveMicropublication(
            artifact_id="mp1", context_id="ctx1", claim_ids=("cl1",)
        )
        assert active.principal_claim_id == "cl1"

    def test_active_principal_must_be_a_member(self) -> None:
        with pytest.raises(ValueError, match="principal"):
            ActiveMicropublication(
                artifact_id="mp1",
                context_id="ctx1",
                claim_ids=("cl1",),
                principal_claim="cl9",
            )

    def test_projection_from_the_charter_carries_principal_through(self) -> None:
        # The view is built by attribute access from the canonical charter —
        # there is no from_mapping, so the stored bundle and the runtime view
        # cannot disagree about the principal claim.
        active = ActiveMicropublication.from_micropublication(
            _bundle(claims=("cl1", "cl2"), principal_claim="cl2")
        )
        assert active.principal_claim_id == "cl2"
        assert active.claim_ids == ("cl1", "cl2")

    def test_multi_claim_active_bundle_requires_explicit_principal(self) -> None:
        with pytest.raises(ValueError, match="principal"):
            ActiveMicropublication(
                artifact_id="mp1", context_id="ctx1", claim_ids=("cl1", "cl2")
            )
