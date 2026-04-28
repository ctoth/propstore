from __future__ import annotations

from hypothesis import given, strategies as st

from propstore.families.documents.micropubs import MicropublicationDocument
from propstore.families.identity.micropubs import (
    canonical_micropub_payload,
    micropub_artifact_id,
)
from quire.documents import convert_document_value


def _micropub(payload: dict[str, object]) -> MicropublicationDocument:
    return convert_document_value(
        payload,
        MicropublicationDocument,
        source="tests:micropub.yaml",
    )


def _payload(
    *,
    claim_id: str = "ps:claim:alpha",
    context_id: str = "ctx_alpha",
    source_id: str = "tag:local@propstore,2026:source/demo",
    evidence_ref: str = "demo:1",
    artifact_id: str = "ps:micropub:old",
    version_id: str = "old-version",
) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "version_id": version_id,
        "context": {"id": context_id},
        "claims": [claim_id],
        "source": source_id,
        "evidence": [{"kind": "paper_page", "reference": evidence_ref}],
        "assumptions": ["domain == 'argumentation'"],
        "provenance": {"paper": "demo", "page": 1},
    }


def test_micropub_id_is_trusty_uri_over_canonical_payload() -> None:
    left = _micropub(_payload())
    right = _micropub({
        "source": "tag:local@propstore,2026:source/demo",
        "claims": ["ps:claim:alpha"],
        "context": {"id": "ctx_alpha"},
        "provenance": {"page": 1, "paper": "demo"},
        "assumptions": ["domain == 'argumentation'"],
        "evidence": [{"reference": "demo:1", "kind": "paper_page"}],
        "version_id": "different-recursive-version",
        "artifact_id": "ps:micropub:different-recursive-artifact",
    })

    assert canonical_micropub_payload(left) == canonical_micropub_payload(right)
    assert micropub_artifact_id(left) == micropub_artifact_id(right)
    assert micropub_artifact_id(left).startswith("ni:///sha-256;")

    changed = _micropub(_payload(evidence_ref="demo:2"))
    assert micropub_artifact_id(changed) != micropub_artifact_id(left)


@given(
    claim_id=st.from_regex(r"ps:claim:[a-z0-9_]{1,12}", fullmatch=True),
    context_id=st.from_regex(r"ctx_[a-z0-9_]{1,12}", fullmatch=True),
    source_id=st.from_regex(
        r"tag:local@propstore,2026:source/[a-z0-9_]{1,12}",
        fullmatch=True,
    ),
    page=st.integers(min_value=1, max_value=999),
)
def test_micropub_id_is_deterministic_for_same_canonical_payload(
    claim_id: str,
    context_id: str,
    source_id: str,
    page: int,
) -> None:
    first = _micropub(
        _payload(
            claim_id=claim_id,
            context_id=context_id,
            source_id=source_id,
            evidence_ref=f"demo:{page}",
            artifact_id="ps:micropub:first",
            version_id="first-version",
        )
    )
    second = _micropub(
        _payload(
            claim_id=claim_id,
            context_id=context_id,
            source_id=source_id,
            evidence_ref=f"demo:{page}",
            artifact_id="ps:micropub:second",
            version_id="second-version",
        )
    )

    assert micropub_artifact_id(first) == micropub_artifact_id(second)


@given(
    claims=st.lists(
        st.from_regex(r"ps:claim:[a-z0-9_]{1,8}", fullmatch=True),
        min_size=1,
        max_size=4,
        unique=True,
    ),
)
def test_micropub_canonical_payload_ignores_nonsemantic_claim_order(
    claims: list[str],
) -> None:
    left = _micropub({
        "artifact_id": "ps:micropub:left",
        "context": {"id": "ctx_alpha"},
        "claims": claims,
        "source": "tag:local@propstore,2026:source/demo",
    })
    right = _micropub({
        "artifact_id": "ps:micropub:right",
        "context": {"id": "ctx_alpha"},
        "claims": list(reversed(claims)),
        "source": "tag:local@propstore,2026:source/demo",
    })

    assert canonical_micropub_payload(left) == canonical_micropub_payload(right)
    assert micropub_artifact_id(left) == micropub_artifact_id(right)
