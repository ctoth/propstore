from __future__ import annotations

from argumentation.aspic import GroundAtom

from propstore.aspic_bridge.translate import claims_to_literals
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.structured_projection import ProjectionAtom


def test_aspic_backend_atom_identity_includes_contextual_ist_frame() -> None:
    """Modgil and Prakken 2018 pngs/page-013 define attack conflict-free
    extensions over ASPIC arguments/literals; McCarthy 1993 pngs/page-000 and
    Guha 1991 pngs/page-007 require the literal consumed there to be
    `ist(context, proposition)`, not a propstore claim id.
    """

    literals = claims_to_literals(
        [
            {
                "id": "claim_x",
                "context_id": "ctx_a",
                "source_assertion_ids": ["assertion_x"],
            }
        ]
    )

    assert {literal.atom for literal in literals.values()} == {
        GroundAtom("ist", ("ctx_a", "claim_x"))
    }


def test_projection_atom_keeps_backend_atom_separate_from_source_identity() -> None:
    """Diller 2025 pngs/page-004/page-005 pins backend ground atoms and
    non-approximated grounding as backend facts; source assertion ids stay in
    projection-frame metadata.
    """

    projection = ProjectionAtom(
        backend="aspic",
        backend_atom=GroundAtom("ist", ("ctx_a", "claim_x")),
        backend_atom_id='{"arguments":["ctx_a","claim_x"],"negated":false,"predicate":"ist"}',
        negated=False,
        source_assertion_ids=("assertion_x",),
    )

    assert projection.backend_atom == GroundAtom("ist", ("ctx_a", "claim_x"))
    assert projection.source_assertion_ids == ("assertion_x",)
    assert projection.backend_atom.predicate != "assertion_x"


def test_gunray_bundle_preserves_four_answer_sections() -> None:
    """Garcia and Simari 2004 pngs/page-025 pins YES/NO/UNDECIDED/UNKNOWN as
    four distinct answer sections that must not collapse into source truth.
    """

    assert set(GroundedRulesBundle.empty().sections) == {
        "yes",
        "no",
        "undecided",
        "unknown",
    }
