"""Shared demo-repository builder for the Phase 10-0 render view-builder tests.

Builds a small but representative corpus through ``Repository.init`` -> author
charters; the tests open it with ``WorldQuery`` (which auto-materializes the
sidecar) and drive the ``propstore.app`` view-builders over it. The corpus
exercises every per-field view state: a resolvable concept with a value and
conditions, an unresolvable concept reference (``UNKNOWN``), a value-less scalar
claim (``MISSING``), a value-less equation (``NOT_APPLICABLE``), and DRAFT /
BLOCKED claims for render-time filtering.
"""

from __future__ import annotations

from pathlib import Path

from condition_ir import KindType

from propstore.core.lemon import LexicalEntry
from propstore.core.lemon.forms import LexicalForm
from propstore.core.lemon.references import OntologyReference
from propstore.core.lemon.types import LexicalSense
from propstore.families.claims import Claim, ClaimStatus, ClaimType
from propstore.families.concepts import Concept, ConceptStatus
from propstore.families.contexts import Context
from propstore.families.forms import FormDefinition
from propstore.families.relations import Stance
from propstore.repository import Repository
from propstore.stances import StanceType


def _speed_concept() -> Concept:
    entry = LexicalEntry(
        identifier="speed",
        canonical_form=LexicalForm(written_rep="speed", language="en"),
        senses=(
            LexicalSense(reference=OntologyReference(uri="ex:speed", label="speed")),
        ),
        physical_dimension_form="velocity",
    )
    return Concept(
        concept_id="speed",
        canonical_name="Speed",
        definition="How fast something moves.",
        lexical_entry=entry,
    )


def build_demo_repo(tmp_path: Path) -> Repository:
    """Author the demo corpus and return the repository."""

    repo = Repository.init(tmp_path / "kn")
    repo.families.form.save(
        "velocity",
        FormDefinition(name="velocity", kind=KindType.QUANTITY, unit_symbol="m/s"),
        message="m",
    )
    repo.families.concept.save("speed", _speed_concept(), message="m")
    repo.families.concept.save(
        "distance", Concept(concept_id="distance", canonical_name="Distance"), message="m"
    )
    repo.families.concept.save(
        "draftconcept",
        Concept(
            concept_id="draftconcept",
            canonical_name="Draft Concept",
            status=ConceptStatus.DRAFT,
        ),
        message="m",
    )
    repo.families.context.save("ctx1", Context(context_id="ctx1", name="ctx"), message="m")

    claims = (
        Claim(
            claim_id="p_speed",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="speed",
            value=3.0,
            unit="m/s",
            uncertainty=0.1,
            uncertainty_type="std",
            sample_size=5,
            conditions=("speed > 0",),
        ),
        Claim(
            claim_id="o_speed",
            context_id="ctx1",
            claim_type=ClaimType.OBSERVATION,
            output_concept="speed",
            value=4.0,
            unit="m/s",
            statement="Observed speed of 4.",
        ),
        Claim(
            claim_id="mech1",
            context_id="ctx1",
            claim_type=ClaimType.MECHANISM,
            output_concept="speed",
            statement="Friction reduces speed.",
        ),
        Claim(
            claim_id="eq1",
            context_id="ctx1",
            claim_type=ClaimType.EQUATION,
            expression="v = d / t",
            concepts=("speed", "distance"),
        ),
        Claim(
            claim_id="p_missingval",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="distance",
        ),
        Claim(
            claim_id="p_blocked",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="distance",
            value=9.0,
            status=ClaimStatus.BLOCKED,
        ),
        Claim(
            claim_id="p_draft",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="speed",
            value=1.0,
            status=ClaimStatus.DRAFT,
        ),
    )
    for claim in claims:
        repo.families.claim.save(claim.claim_id, claim, message="m")

    repo.families.stance.save(
        "s_sup",
        Stance(
            stance_id="s_sup",
            source_claim_id="o_speed",
            target_claim_id="p_speed",
            stance_type=StanceType.SUPPORTS,
        ),
        message="m",
    )
    repo.families.stance.save(
        "s_att",
        Stance(
            stance_id="s_att",
            source_claim_id="eq1",
            target_claim_id="p_speed",
            stance_type=StanceType.REBUTS,
        ),
        message="m",
    )
    return repo
