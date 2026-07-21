"""Embedding model identity — lossless, injective, no lossy key sanitizer.

Rewrite-native port of the reference ``test_no_embedding_key_collision.py``
identity cases (the SQL-row cases move to ``test_embed_similar.py``). Two model
names differing only by punctuation must hash distinctly — there is no
``model_key`` sanitizer collapsing them.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.heuristic.embedding_identity import EmbeddingModelIdentity


def test_identity_distinguishes_punctuation_collisions() -> None:
    identities = [
        EmbeddingModelIdentity(
            provider="litellm",
            model_name=model_name,
            model_version="2026-04",
            content_digest="same-provider-spec",
        )
        for model_name in ("a/b", "a-b", "a_b", "a b")
    ]
    assert len(set(identities)) == 4
    assert len({identity.identity_hash for identity in identities}) == 4


def test_from_model_name_defaults_and_digest() -> None:
    identity = EmbeddingModelIdentity.from_model_name("provider/model")
    assert identity.provider == "litellm"
    assert identity.model_name == "provider/model"
    assert identity.model_version == ""
    assert identity.content_digest.startswith("sha256:")
    assert identity.identity_hash.startswith("sha256:")


def test_from_registry_row_round_trips() -> None:
    original = EmbeddingModelIdentity.from_model_name("openai/text-embedding-3-small")
    row = {
        "provider": original.provider,
        "model_name": original.model_name,
        "model_version": original.model_version,
        "content_digest": original.content_digest,
    }
    assert EmbeddingModelIdentity.from_registry_row(row) == original


def test_embedding_sanitizer_is_absent() -> None:
    from pathlib import Path

    source = Path("propstore/heuristic/embed.py").read_text(encoding="utf-8")
    assert "_sanitize_model_key" not in source
    assert "model_key" not in source


_identity_text = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cs",), blacklist_characters=("\x00",)
    ),
    min_size=1,
    max_size=24,
)


@given(
    tuples=st.lists(
        st.tuples(
            _identity_text,
            _identity_text,
            _identity_text,
            st.integers(min_value=1, max_value=4096).map(lambda value: f"dim:{value}"),
        ),
        min_size=1,
        max_size=20,
        unique=True,
    )
)
@settings(max_examples=100)
def test_identity_hash_is_injective(tuples: list[tuple[str, str, str, str]]) -> None:
    identities = [
        EmbeddingModelIdentity(
            provider=provider,
            model_name=model_name,
            model_version=model_version,
            content_digest=content_digest,
        )
        for provider, model_name, model_version, content_digest in tuples
    ]
    assert len({identity.identity_hash for identity in identities}) == len(tuples)
