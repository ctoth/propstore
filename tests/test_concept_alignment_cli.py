"""End-to-end imported-snapshot alignment through the presentation boundary."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner, Result
from condition_ir import KindType

from propstore.cli import cli
from propstore.core.lemon import (
    LexicalEntry,
    LexicalForm,
    LexicalSense,
    OntologyReference,
)
from propstore.families.alignment import ConceptAlignmentArtifact, ConceptAlignmentRef
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.importing.repository_import import (
    RepositoryImportResult,
    commit_repository_import,
    plan_repository_import,
)
from propstore.provenance import ProvenanceStatus, read_provenance_note
from propstore.repository import Repository


_SHARED_URI = "https://example.org/shared#inertia"


def _alignment_slug(cluster_id: str) -> str:
    return cluster_id.split(":", 1)[1]


def _lexical_entry(identifier: str, name: str, ontology_uri: str) -> LexicalEntry:
    return LexicalEntry(
        identifier=identifier,
        canonical_form=LexicalForm(written_rep=name, language="en"),
        senses=(LexicalSense(reference=OntologyReference(uri=ontology_uri)),),
        physical_dimension_form="quantity",
    )


def _author_source(root: Path, *, repository_name: str) -> Repository:
    repo = Repository.init(root / repository_name / "knowledge")
    repo.families.form.save(
        "quantity",
        FormDefinition(
            name="quantity",
            kind=KindType.QUANTITY,
            dimensions={"M": 1},
            unit_symbol="kg",
        ),
        message="form",
    )
    mass_uri = f"https://example.org/{repository_name}#mass"
    repo.families.concept.save(
        "concept:mass",
        Concept(
            concept_id="concept:mass",
            canonical_name="Mass",
            definition=f"Mass according to {repository_name}.",
            ontology_reference=OntologyReference(uri=mass_uri),
            lexical_entry=_lexical_entry("mass", "Mass", mass_uri),
        ),
        message="mass",
    )
    repo.families.concept.save(
        "concept:inertia",
        Concept(
            concept_id="concept:inertia",
            canonical_name="Inertia",
            definition=f"Inertia according to {repository_name}.",
            ontology_reference=OntologyReference(uri=_SHARED_URI),
            lexical_entry=_lexical_entry("inertia", "Inertia", _SHARED_URI),
        ),
        message="inertia",
    )
    return repo


def _import(destination: Repository, source: Repository) -> RepositoryImportResult:
    return commit_repository_import(
        destination,
        plan_repository_import(destination, source.root.parent),
    )


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(cli, ["-C", str(repo.root), "concept", *args])


def test_align_pins_imported_snapshots_and_writes_deterministic_open_proposal(
    tmp_path: Path,
) -> None:
    destination = Repository.init(tmp_path / "destination" / "knowledge")
    source_a = _author_source(tmp_path, repository_name="repo-a")
    source_b = _author_source(tmp_path, repository_name="repo-b")
    import_a = _import(destination, source_a)
    import_b = _import(destination, source_b)
    git = destination.require_git()
    master_before = git.branch_sha(git.primary_branch_name())

    first = _invoke(
        destination,
        [
            "align",
            "--imports",
            import_b.target_branch,
            "--imports",
            import_a.target_branch,
        ],
    )

    assert first.exit_code == 0, first.output
    cluster_id = first.output.strip().split()[-1]
    slug = _alignment_slug(cluster_id)
    artifact = destination.families.concept_alignments.require(
        ConceptAlignmentRef(slug)
    )
    assert artifact.decision.status == "open"
    assert len(artifact.arguments) == 4
    assert git.branch_sha(git.primary_branch_name()) == master_before

    expected_snapshots = {
        str(source_a.root): import_a,
        str(source_b.root): import_b,
    }
    for argument in artifact.arguments:
        imported = expected_snapshots[argument.repository_origin]
        assert argument.source_commit == imported.source_commit
        assert argument.import_branch == imported.target_branch
        assert argument.import_commit == imported.commit_sha
        assert argument.concept_id.startswith("ps:concept:")
        assert argument.ontology_reference is not None
        assert argument.lexical_entry is not None
        assert argument.form == "quantity"

    mass_arguments = [
        argument for argument in artifact.arguments if argument.canonical_name == "Mass"
    ]
    assert len(mass_arguments) == 2
    assert mass_arguments[0].concept_id != mass_arguments[1].concept_id
    assert (
        mass_arguments[0].id,
        mass_arguments[1].id,
    ) in artifact.framework.non_attacks

    inertia_arguments = [
        argument
        for argument in artifact.arguments
        if argument.canonical_name == "Inertia"
    ]
    assert len(inertia_arguments) == 2
    assert {
        (inertia_arguments[0].id, inertia_arguments[1].id),
        (inertia_arguments[1].id, inertia_arguments[0].id),
    }.issubset(set(artifact.framework.attacks))

    for imported in (import_a, import_b):
        provenance = read_provenance_note(git.raw_repo, imported.commit_sha)
        assert provenance is not None
        assert provenance.status is ProvenanceStatus.STATED
        assert provenance.derived_from == (imported.source_commit,)

    encoded_first = ConceptAlignmentArtifact.__charter__.document_codec().encode(
        artifact
    )
    second = _invoke(
        destination,
        [
            "align",
            "--imports",
            import_a.target_branch,
            "--imports",
            import_b.target_branch,
        ],
    )
    assert second.exit_code == 0, second.output
    repeated = destination.families.concept_alignments.require(
        ConceptAlignmentRef(slug)
    )
    assert repeated == artifact
    assert (
        ConceptAlignmentArtifact.__charter__.document_codec().encode(repeated)
        == encoded_first
    )
    assert git.branch_sha(git.primary_branch_name()) == master_before


def test_align_requires_two_explicit_import_branches(tmp_path: Path) -> None:
    destination = Repository.init(tmp_path / "destination" / "knowledge")
    source = _author_source(tmp_path, repository_name="repo-a")
    imported = _import(destination, source)

    result = _invoke(
        destination,
        ["align", "--imports", imported.target_branch],
    )

    assert result.exit_code != 0
    assert "at least two branches" in result.output
