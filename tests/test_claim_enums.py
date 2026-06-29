"""Phase 3 claim enum decode through the charter document codec.

Ports the ClaimType half of the reference document-enum contract: a valid type
decodes to the enum member; an unrecognized type fails to decode (it is not
silently coerced).
"""

from __future__ import annotations

import pytest

from propstore.families.claims import Claim, ClaimType


def test_valid_claim_type_decodes_to_enum_member() -> None:
    codec = Claim.__charter__.document_codec()
    claim = codec.convert(
        {"claim_id": "c1", "claim_type": "algorithm"}, Claim, source="test"
    )
    assert isinstance(claim, Claim)
    assert claim.claim_type is ClaimType.ALGORITHM


def test_unknown_claim_type_fails_to_decode() -> None:
    codec = Claim.__charter__.document_codec()
    with pytest.raises(Exception):
        codec.convert({"claim_id": "c1", "claim_type": "bogus"}, Claim, source="test")


def test_claim_type_has_the_ten_taxonomy_members() -> None:
    assert {t.value for t in ClaimType} == {
        "parameter",
        "equation",
        "observation",
        "mechanism",
        "comparison",
        "limitation",
        "model",
        "measurement",
        "algorithm",
        "unknown",
    }
