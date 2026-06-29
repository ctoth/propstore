"""Phase 7a-world-A: charter store -> compiled graph -> activation -> justifications.

Ported from the reference ``test_core_justifications`` over the charter feed
(``CharterStore``) instead of the deleted dict/``*RowInput`` store.
"""

from __future__ import annotations

from propstore.core.activation import activate_compiled_world_graph
from propstore.core.environment import Environment
from propstore.core.graph_build import build_compiled_world_graph
from propstore.core.justifications import claim_justifications_from_active_graph
from propstore.core.labels import compile_environment_assumptions
from propstore.families.claims import Claim, ClaimType
from propstore.families.relations import Stance
from propstore.stances import StanceType
from tests.world_store_feed import CharterStore


def _store() -> CharterStore:
    return CharterStore(
        claims=(
            Claim(claim_id="claim_a", claim_type=ClaimType.PARAMETER, output_concept="c1", value=1.0),
            Claim(claim_id="claim_b", claim_type=ClaimType.PARAMETER, output_concept="c2", value=2.0),
            Claim(claim_id="claim_c", claim_type=ClaimType.PARAMETER, output_concept="c3", value=3.0),
        ),
        stances=(
            Stance(
                stance_id="s_ab",
                source_claim_id="claim_a",
                target_claim_id="claim_b",
                stance_type=StanceType.SUPPORTS,
            ),
            Stance(
                stance_id="s_bc",
                source_claim_id="claim_b",
                target_claim_id="claim_c",
                stance_type=StanceType.EXPLAINS,
            ),
        ),
    )


def _active_graph(store: CharterStore):
    return activate_compiled_world_graph(
        build_compiled_world_graph(store),
        environment=Environment(assumptions=compile_environment_assumptions(bindings={})),
        solver=None,
    )


def test_claim_justifications_from_active_graph_preserves_reported_and_support_edges() -> None:
    justifications = claim_justifications_from_active_graph(_active_graph(_store()))
    by_id = {item.justification_id: item for item in justifications}

    assert by_id["reported:claim_a"].conclusion_claim_id == "claim_a"
    assert by_id["reported:claim_b"].premise_claim_ids == ()
    assert by_id["supports:claim_a->claim_b"].premise_claim_ids == ("claim_a",)
    assert by_id["supports:claim_a->claim_b"].conclusion_claim_id == "claim_b"
    assert by_id["explains:claim_b->claim_c"].premise_claim_ids == ("claim_b",)


def test_claim_justifications_from_active_graph_is_deterministic_under_order_changes() -> None:
    store = _store()
    reversed_store = CharterStore(
        claims=tuple(reversed(store.claims)),
        stances=tuple(reversed(store.stances)),
    )

    forward = claim_justifications_from_active_graph(_active_graph(store))
    reverse = claim_justifications_from_active_graph(_active_graph(reversed_store))

    assert [item.to_dict() for item in forward] == [item.to_dict() for item in reverse]
