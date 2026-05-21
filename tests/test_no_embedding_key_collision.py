from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

def test_embedding_identity_distinguishes_punctuation_collisions() -> None:
    from propstore.heuristic.embedding_identity import EmbeddingModelIdentity

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


def test_sidecar_embedding_registry_stores_typed_identity_rows(tmp_path: Path) -> None:
    from quire.sqlalchemy_store import create_sqlalchemy_store, writable_session

    from propstore.families.world_charters import EmbeddingModel, world_sqlalchemy_schema
    from propstore.heuristic.embedding_identity import EmbeddingModelIdentity

    schema = world_sqlalchemy_schema()
    store_path = tmp_path / "embedding-models.sqlite"
    create_sqlalchemy_store(store_path, schema)

    identities = [
        EmbeddingModelIdentity(
            provider="litellm",
            model_name=model_name,
            model_version="2026-04",
            content_digest="same-provider-spec",
        )
        for model_name in ("a/b", "a-b", "a_b", "a b")
    ]

    with writable_session(store_path, schema) as derived:
        for identity in identities:
            derived.add(
                EmbeddingModel(
                    model_identity_hash=identity.identity_hash,
                    provider=identity.provider,
                    model_name=identity.model_name,
                    model_version=identity.model_version,
                    content_digest=identity.content_digest,
                    dimensions=2,
                    created_at="2026-04-29T00:00:00+00:00",
                )
            )

        duplicate = identities[0]
        derived.session.merge(
            EmbeddingModel(
                model_identity_hash=duplicate.identity_hash,
                provider=duplicate.provider,
                model_name=duplicate.model_name,
                model_version=duplicate.model_version,
                content_digest=duplicate.content_digest,
                dimensions=2,
                created_at="2026-04-29T00:00:00+00:00",
            )
        )
        derived.commit()

    with writable_session(store_path, schema) as derived:
        table = schema.table("embedding_model")
        rows = derived.session.execute(
            table.select().order_by(table.c.model_name)
        ).mappings().all()
        column_names = set(table.c.keys())

    assert len(rows) == 4
    assert {row["model_name"] for row in rows} == {"a/b", "a-b", "a_b", "a b"}
    assert len({row["model_identity_hash"] for row in rows}) == 4
    assert "model_key" not in column_names


def test_embedding_sanitizer_deleted() -> None:
    embed_source = Path("propstore/heuristic/embed.py").read_text()

    assert "_sanitize_model_key" not in embed_source


_identity_text = st.text(
    alphabet=st.characters(
        blacklist_categories=("Cs",),
        blacklist_characters=("\x00",),
    ),
    min_size=1,
    max_size=24,
)


@pytest.mark.property
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
def test_embedding_model_identity_hash_is_injective_over_generated_tuples(
    tuples: list[tuple[str, str, str, str]],
) -> None:
    """WS-K property: identity uses the full provider/name/revision/spec tuple."""
    from propstore.heuristic.embedding_identity import EmbeddingModelIdentity

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
