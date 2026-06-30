"""Owner-layer project initialization seed (Phase 10-0b).

``initialize_project`` runs ``Repository.init`` and seeds the packaged default
forms + base concepts (mapped from the historical resource shape onto the current
charter types) in one commit. It is idempotent on an already-initialized repo.
"""

from __future__ import annotations

from pathlib import Path

from propstore.app.project_init import initialize_project
from propstore.families.concepts import Concept
from propstore.families.forms import FormDefinition
from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository


def _load_concept(repo: Repository, concept_id: str) -> Concept:
    loaded = repo.families.concept.load(concept_id)
    assert isinstance(loaded, Concept)
    return loaded


def _load_form(repo: Repository, name: str) -> FormDefinition:
    loaded = repo.families.form.load(name)
    assert isinstance(loaded, FormDefinition)
    return loaded


def test_initialize_project_seeds_and_is_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "kn"
    report = initialize_project(root)
    assert report.initialized is True
    assert report.root == root
    assert Repository.is_propstore_repo(root)

    # Second call is a no-op.
    again = initialize_project(root)
    assert again.initialized is False


def test_initialize_project_seeds_forms(tmp_path: Path) -> None:
    root = tmp_path / "kn"
    initialize_project(root)
    repo = Repository.find(root)
    frequency = _load_form(repo, "frequency")
    assert frequency.unit_symbol == "Hz"
    assert "kHz" in frequency.conversions
    # An affine conversion form round-trips its offset.
    temperature = _load_form(repo, "temperature")
    assert temperature.conversions["°C"].type == "affine"
    assert temperature.conversions["°C"].offset == 273.15


def test_initialize_project_seeds_description_kind_concepts(tmp_path: Path) -> None:
    root = tmp_path / "kn"
    initialize_project(root)
    repo = Repository.find(root)

    measurement = _load_concept(repo, "ps:concept:measurement")
    assert measurement.canonical_name == "Measurement"
    entry = measurement.lexical_entry
    assert entry is not None
    sense = entry.senses[0]
    assert sense.provenance is not None
    assert sense.provenance.status is ProvenanceStatus.STATED
    description = sense.description_kind
    assert description is not None
    slot_names = {slot.name for slot in description.slots}
    assert {"quantity-measured", "value", "instrument"} <= slot_names
    # The instrument slot carries a Dowty proto-agent bundle from the seed.
    instrument = next(slot for slot in description.slots if slot.name == "instrument")
    assert instrument.proto_role_bundle is not None
    assert instrument.proto_role_bundle.proto_agent_entailments[0].property == "causation"


def test_initialize_project_seeds_qualia(tmp_path: Path) -> None:
    root = tmp_path / "kn"
    initialize_project(root)
    repo = Repository.find(root)

    instrument = _load_concept(repo, "ps:concept:measurement_instrument")
    entry = instrument.lexical_entry
    assert entry is not None
    qualia = entry.senses[0].qualia
    assert qualia is not None
    assert qualia.telic[0].reference.uri == "ps:concept:measurement"
