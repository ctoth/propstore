"""Phase 1 walking-skeleton tests: ONE concept, author -> store -> sidecar ->
query -> render, with the non-commitment (present-but-filtered-at-render) proof.

These are behavioral tests over the real quire substrate (in-memory git store +
on-disk sqlite sidecar). They prove the architecture, not concept completeness.
"""

from __future__ import annotations

import msgspec
import pytest
from sqlalchemy import select

from quire.sqlalchemy_store import readonly_session

from propstore.families.concepts import Concept, ConceptStatus
from propstore.render import RenderPolicy, render_concepts
from propstore.storage import ConceptRepository


@pytest.fixture
def repo() -> ConceptRepository:
    return ConceptRepository()


# --- charter / identity discipline -----------------------------------------


def test_charter_projection_falls_out_of_the_charter() -> None:
    """The sidecar columns ARE the charter fields — no hand-authored DTO.

    The projection table/model are derived from the single ``Concept`` charter
    class; the columns equal the document field names.
    """

    schema_object = Concept.__charter__.to_schema_object()
    column_names = {field.name for field in schema_object.fields}
    assert {
        "concept_id",
        "canonical_name",
        "status",
        "definition",
        "category_values",
        "category_extensible",
    } <= column_names
    assert {"local_name", "form", "form_parameters", "registry_match"}.isdisjoint(
        column_names
    )
    # The generated SQLAlchemy model name is derived, not separately authored.
    assert Concept.__charter_model__.__name__ == "ConceptModel"


def test_identity_excludes_provenance() -> None:
    """Provenance is not a concept field, so it can never enter identity."""

    field_names = {f.name for f in msgspec.structs.fields(Concept)}
    assert "provenance" not in field_names
    assert Concept.__charter__.family.identity_field == "concept_id"


def test_concept_is_the_only_spelling() -> None:
    """There is no second concept spelling (Document/Record/Row/payload)."""

    import propstore.families.concepts as module

    public = {name for name in vars(module) if not name.startswith("_")}
    banned = {n for n in public if n.endswith(("Document", "Record", "Row"))}
    assert banned == set()
    assert not hasattr(Concept, "to_payload")
    assert not hasattr(Concept, "from_payload")


# --- author -> store -> query ----------------------------------------------


def test_author_then_load_round_trips_through_git(repo: ConceptRepository) -> None:
    concept = Concept(
        concept_id="concept:mass",
        canonical_name="Mass",
        definition="amount of matter",
    )
    sha = repo.author(concept, message="author mass")
    assert isinstance(sha, str) and sha

    loaded = repo.get("concept:mass")
    assert loaded == concept


def test_storage_is_raw_no_normalization(repo: ConceptRepository) -> None:
    """The stored form is byte-identical to what was authored.

    Untrimmed whitespace and original casing survive: normalization, if any,
    is a render-time concern, never baked at storage.
    """

    raw_name = "  Specific Heat Capacity  "
    repo.author(
        Concept(concept_id="concept:cp", canonical_name=raw_name),
        message="author raw",
    )
    loaded = repo.get("concept:cp")
    assert loaded is not None
    assert loaded.canonical_name == raw_name


# --- sidecar build (never drops) -------------------------------------------


def test_build_sidecar_projects_every_concept_including_blocked(
    repo: ConceptRepository, tmp_path
) -> None:
    """The build NEVER filters: blocked/draft concepts are rows too."""

    repo.author(Concept(concept_id="concept:a", canonical_name="A"), message="a")
    repo.author(
        Concept(concept_id="concept:b", canonical_name="B", status=ConceptStatus.DRAFT),
        message="b",
    )
    repo.author(
        Concept(
            concept_id="concept:c", canonical_name="C", status=ConceptStatus.BLOCKED
        ),
        message="c",
    )

    sidecar = tmp_path / "concept.sqlite"
    schema = repo.build_sidecar(sidecar)

    model = schema.model("concept")
    with readonly_session(sidecar, schema) as session:
        ids = {row.concept_id for row in session.scalars(select(model))}
    assert ids == {"concept:a", "concept:b", "concept:c"}


# --- render-filter proof: present-in-sidecar-but-filtered-at-render ----------


def test_blocked_concept_present_in_sidecar_but_filtered_at_render(
    repo: ConceptRepository, tmp_path
) -> None:
    """The core non-commitment proof.

    A blocked concept is physically present in the sidecar yet absent from the
    default render, and becomes visible the moment the policy includes it — with
    NO change to storage.
    """

    repo.author(
        Concept(concept_id="concept:ok", canonical_name="OK"), message="ok"
    )
    repo.author(
        Concept(
            concept_id="concept:blk",
            canonical_name="Blocked",
            status=ConceptStatus.BLOCKED,
        ),
        message="blk",
    )

    sidecar = tmp_path / "concept.sqlite"
    schema = repo.build_sidecar(sidecar)

    # Present in storage/sidecar: the blocked row physically exists.
    model = schema.model("concept")
    with readonly_session(sidecar, schema) as session:
        stored_ids = {row.concept_id for row in session.scalars(select(model))}
    assert "concept:blk" in stored_ids

    # Filtered at render under the default policy.
    default_ids = {c.concept_id for c in render_concepts(sidecar, schema)}
    assert default_ids == {"concept:ok"}
    assert "concept:blk" not in default_ids

    # Visible once the policy opts the status in — same sidecar, no rebuild.
    opened_ids = {
        c.concept_id
        for c in render_concepts(sidecar, schema, RenderPolicy(include_blocked=True))
    }
    assert opened_ids == {"concept:ok", "concept:blk"}


def test_draft_filtered_independently_of_blocked(
    repo: ConceptRepository, tmp_path
) -> None:
    repo.author(Concept(concept_id="concept:ok", canonical_name="OK"), message="ok")
    repo.author(
        Concept(
            concept_id="concept:d", canonical_name="Draft", status=ConceptStatus.DRAFT
        ),
        message="d",
    )
    repo.author(
        Concept(
            concept_id="concept:b",
            canonical_name="Blocked",
            status=ConceptStatus.BLOCKED,
        ),
        message="b",
    )

    sidecar = tmp_path / "concept.sqlite"
    schema = repo.build_sidecar(sidecar)

    drafts_only = {
        c.concept_id
        for c in render_concepts(sidecar, schema, RenderPolicy(include_drafts=True))
    }
    assert drafts_only == {"concept:ok", "concept:d"}

    everything = {
        c.concept_id
        for c in render_concepts(
            sidecar,
            schema,
            RenderPolicy(include_drafts=True, include_blocked=True),
        )
    }
    assert everything == {"concept:ok", "concept:d", "concept:b"}


def test_render_policy_admits() -> None:
    default = RenderPolicy()
    assert default.admits(ConceptStatus.AUTHORED)
    assert not default.admits(ConceptStatus.DRAFT)
    assert not default.admits(ConceptStatus.BLOCKED)
    assert RenderPolicy(include_blocked=True).admits(ConceptStatus.BLOCKED)
    assert RenderPolicy(include_drafts=True).admits(ConceptStatus.DRAFT)
