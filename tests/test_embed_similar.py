"""Embedding index + similarity over a real world sidecar (quire vec adapter).

Skip-gated on the ``sqlite-vec`` extra (installed in dev, so these run here). A
deterministic fake embedder stands in for ``litellm`` so the vectors — and hence
the distances and neighbour sets — are exact. Covers: embed -> store, k-NN with
honest distances and self-exclusion, honest-empty for an unknown id, the
``WorldQuery.similar_*`` readers, concept embeddings, and the multi-model
agree/disagree (E4) signal.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("sqlite_vec")

from propstore.derived_build import materialize_world_sidecar  # noqa: E402
from propstore.families.claims import Claim, ClaimType  # noqa: E402
from propstore.families.concepts import Concept  # noqa: E402
from propstore.families.contexts import Context  # noqa: E402
from propstore.families.embeddings import declaration as emb  # noqa: E402
from propstore.repository import Repository  # noqa: E402
from propstore.world import WorldQuery  # noqa: E402

# Per-model 2-D vectors keyed by the embedded text (each claim's statement is its
# id). Distance from cl1 = origin is just |x|. model-a orders cl2..cl7 by index;
# model-b promotes cl5/cl6 ahead of cl4, so with the agree/disagree window of 2k=4
# the two top-4 neighbour sets agree on {cl2,cl3,cl5} and disagree on cl4 (a-only)
# and cl6 (b-only).
_VEC_A = {f"cl{i}": [float(i - 1), 0.0] for i in range(1, 8)}
_VEC_B = {
    "cl1": [0.0, 0.0],
    "cl2": [1.0, 0.0],
    "cl3": [2.0, 0.0],
    "cl5": [3.0, 0.0],
    "cl6": [4.0, 0.0],
    "cl4": [5.0, 0.0],
    "cl7": [6.0, 0.0],
}
# Concept embedding text is the canonical name (no definitions authored below).
_CONCEPT_VEC = {
    "Speed": [0.0, 0.0],
    "Velocity": [1.0, 0.0],
    "Pressure": [9.0, 0.0],
}


def _fake_litellm(table_by_model: dict[str, dict[str, list[float]]]) -> MagicMock:
    litellm = MagicMock()

    def embedding(model: str, input: Sequence[str]) -> MagicMock:
        table = table_by_model[model]
        response = MagicMock()
        response.data = [{"embedding": table[text]} for text in input]
        return response

    litellm.embedding.side_effect = embedding
    return litellm


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    repo.families.context.save("ctx1", Context(context_id="ctx1", name="ctx"), message="m")
    repo.families.concept.save(
        "speed", Concept(concept_id="speed", canonical_name="Speed"), message="m"
    )
    repo.families.concept.save(
        "velocity", Concept(concept_id="velocity", canonical_name="Velocity"), message="m"
    )
    repo.families.concept.save(
        "pressure", Concept(concept_id="pressure", canonical_name="Pressure"), message="m"
    )
    for claim_id in ("cl1", "cl2", "cl3", "cl4", "cl5", "cl6", "cl7"):
        repo.families.claim.save(
            claim_id,
            Claim(
                claim_id=claim_id,
                context_id="ctx1",
                claim_type=ClaimType.OBSERVATION,
                output_concept="speed",
                statement=claim_id,
            ),
            message="m",
        )
    return repo


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    return _repo(tmp_path)


def _sidecar_path(repo: Repository) -> Path:
    handle, _ = materialize_world_sidecar(repo)
    return handle.path


def _claims(repo: Repository) -> list[Claim]:
    with WorldQuery(repo) as world:
        return list(world.claims_for(None))


def _concepts(repo: Repository) -> list[Concept]:
    with WorldQuery(repo) as world:
        return list(world.all_concepts())


def _embed_claims(repo: Repository, model: str, table: dict[str, list[float]]) -> None:
    claims = _claims(repo)
    with patch(
        "propstore.heuristic.embed.require_litellm",
        return_value=_fake_litellm({model: table}),
    ):
        with emb.embedding_connection(_sidecar_path(repo), readonly=False) as conn:
            emb.ensure_embedding_tables(conn)
            emb.embed_claims(conn, claims, model)


def test_embed_then_find_similar_ranks_by_distance(repo: Repository) -> None:
    _embed_claims(repo, "model-a", _VEC_A)
    with emb.embedding_connection(_sidecar_path(repo), readonly=True) as conn:
        hits = emb.find_similar_claims(conn, _claims(repo), "cl1", "model-a", top_k=3)
    ids = [str(hit.claim_id) for hit in hits]
    assert ids == ["cl2", "cl3", "cl4"]  # nearest-first, self excluded
    assert hits[0].distance < hits[1].distance < hits[2].distance
    assert all(hit.distance >= 0.0 for hit in hits)


def test_find_similar_unknown_claim_is_honest_empty(repo: Repository) -> None:
    _embed_claims(repo, "model-a", _VEC_A)
    with emb.embedding_connection(_sidecar_path(repo), readonly=True) as conn:
        assert emb.find_similar_claims(conn, _claims(repo), "nope", "model-a") == []


def test_embed_skips_unchanged_on_reembed(repo: Repository) -> None:
    _embed_claims(repo, "model-a", _VEC_A)
    claims = _claims(repo)
    with patch(
        "propstore.heuristic.embed.require_litellm",
        return_value=_fake_litellm({"model-a": _VEC_A}),
    ):
        with emb.embedding_connection(_sidecar_path(repo), readonly=False) as conn:
            result = emb.embed_claims(conn, claims, "model-a")
    assert result == {"embedded": 0, "skipped": 7, "errors": 0}


def test_world_query_similar_claims_backed(repo: Repository) -> None:
    _embed_claims(repo, "model-a", _VEC_A)
    with WorldQuery(repo) as world:
        hits = world.similar_claims("cl1", model_name="model-a", top_k=2)
    assert [str(hit.claim_id) for hit in hits] == ["cl2", "cl3"]


def test_world_query_similar_claims_honest_empty_without_index(repo: Repository) -> None:
    # No embedding run -> no registered model -> honest empty (not fabricated).
    with WorldQuery(repo) as world:
        assert world.similar_claims("cl1") == []


def test_concept_embeddings_and_similarity(repo: Repository) -> None:
    concepts = _concepts(repo)
    with patch(
        "propstore.heuristic.embed.require_litellm",
        return_value=_fake_litellm({"model-a": _CONCEPT_VEC}),
    ):
        with emb.embedding_connection(_sidecar_path(repo), readonly=False) as conn:
            emb.ensure_embedding_tables(conn)
            emb.embed_concepts(conn, concepts, "model-a")
    with WorldQuery(repo) as world:
        hits = world.similar_concepts("speed", model_name="model-a", top_k=2)
    ids = [str(hit.concept_id) for hit in hits]
    assert ids[0] == "velocity"  # nearest to speed
    assert "pressure" in ids


def test_multi_model_agree_disagree(repo: Repository) -> None:
    _embed_claims(repo, "model-a", _VEC_A)
    _embed_claims(repo, "model-b", _VEC_B)
    with emb.embedding_connection(_sidecar_path(repo), readonly=True) as conn:
        models = {row["model_name"] for row in emb.get_registered_models(conn)}
        assert models == {"model-a", "model-b"}
        agree = emb.find_similar_claims_agree(conn, _claims(repo), "cl1", top_k=2)
        disagree = emb.find_similar_claims_disagree(conn, _claims(repo), "cl1", top_k=2)

    agree_ids = {str(row["id"]) for row in agree}
    disagree_ids = {str(row["id"]) for row in disagree}
    # cl2 is nearest under both models -> agreement, not disagreement.
    assert "cl2" in agree_ids
    assert "cl2" not in disagree_ids
    # cl4 (in the top-4 only under model-a) and cl6 (only under model-b) disagree.
    assert {"cl4", "cl6"} <= disagree_ids
    for row in disagree:
        if str(row["id"]) in {"cl4", "cl6"}:
            assert row["similar_in"]
            assert row["not_similar_in"]
