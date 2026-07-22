"""CLI adapter tests for the ``pks world`` command family (Phase 10-1).

Exercises the thin Click adapters end-to-end against the real owner tier
(:mod:`propstore.world.reasoning_reports`, :mod:`propstore.sensitivity`,
:mod:`propstore.world.consistency`, :mod:`propstore.fragility`,
:mod:`propstore.support_revision.workflows`). The world is built with the same
``Repository.init`` -> author charters -> ``WorldQuery`` recipe as
``test_world_reasoning_reports``; commands are invoked through the ``world`` group
with the repo handle attached to ``ctx.obj`` (the root group attaches it lazily in
real use).

Ported and adapted from the reference ``test_revision_cli`` /
``test_revision_phase1_cli`` / ``test_cli_render_policy_flags``; cases whose owner
does not exist in the rewrite are noted in the worker report under "deferred".
"""

from __future__ import annotations

import json
from pathlib import Path

import click
import pytest
from click.testing import CliRunner, Result

from propstore.cli.world import world
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.relations import Stance
from propstore.repository import Repository
from propstore.stances import StanceType
from propstore.support_revision.workflows import RevisionWorldRequest, revision_base
from propstore.world import WorldQuery


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    for concept_id in ("A", "B", "C", "D", "speed"):
        repo.families.concept.save(
            concept_id,
            Concept(concept_id=concept_id, canonical_name=concept_id),
            message="m",
        )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "aa_pa",
        Claim(
            claim_id="aa_pa",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="A",
            value=2.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "ab_pb",
        Claim(
            claim_id="ab_pb",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="B",
            value=3.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "zz_eq",
        Claim(
            claim_id="zz_eq",
            context_id="ctx1",
            claim_type=ClaimType.EQUATION,
            output_concept="C",
            concepts=("A", "B"),
            expression="A + B",
            sympy="A + B",
        ),
        message="m",
    )
    repo.families.claim.save(
        "alg1",
        Claim(
            claim_id="alg1",
            context_id="ctx1",
            claim_type=ClaimType.ALGORITHM,
            output_concept="D",
            name="algo one",
            body="def f(x):\n    return x\n",
        ),
        message="m",
    )
    repo.families.claim.save(
        "s1",
        Claim(
            claim_id="s1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="speed",
            value=10.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "s2",
        Claim(
            claim_id="s2",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="speed",
            value=20.0,
        ),
        message="m",
    )
    repo.families.stance.save(
        "st1",
        Stance(
            stance_id="st1",
            source_claim_id="s1",
            target_claim_id="s2",
            stance_type=StanceType.REBUTS,
        ),
        message="m",
    )
    return repo


@pytest.fixture
def repo(tmp_path: Path) -> Repository:
    return _repo(tmp_path)


def _invoke(repo: Repository, args: list[str]) -> Result:
    return CliRunner().invoke(world, args, obj={"repo": repo})


# ── query family ────────────────────────────────────────────────────────────────


def test_status_renders_counts(repo: Repository) -> None:
    result = _invoke(repo, ["status"])
    assert result.exit_code == 0, result.output
    assert "Concepts:           5" in result.output
    assert "Claims:             6" in result.output
    assert "Stances:            1" in result.output


def test_status_json_shape(repo: Repository) -> None:
    result = _invoke(repo, ["status", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["concept_count"] == 5
    assert data["visible_claim_count"] == 6
    assert "conflict_count" in data


def test_status_show_quarantined_adds_diagnostics_line(repo: Repository) -> None:
    result = _invoke(repo, ["status", "--show-quarantined"])
    assert result.exit_code == 0, result.output
    assert "Diagnostics:" in result.output


def test_query_lists_claims_for_concept(repo: Repository) -> None:
    result = _invoke(repo, ["query", "A"])
    assert result.exit_code == 0, result.output
    assert "aa_pa" in result.output


def test_query_unknown_concept_fails(repo: Repository) -> None:
    result = _invoke(repo, ["query", "nope"])
    assert result.exit_code != 0
    assert "Unknown concept: nope" in result.output


def test_query_json_shape(repo: Repository) -> None:
    result = _invoke(repo, ["query", "A", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["canonical_name"] == "A"


def test_bind_lists_active_claims(repo: Repository) -> None:
    result = _invoke(repo, ["bind"])
    assert result.exit_code == 0, result.output
    assert "Active claims: 6" in result.output


def test_bind_with_target_reports_status(repo: Repository) -> None:
    result = _invoke(repo, ["bind", "A"])
    assert result.exit_code == 0, result.output
    assert "A: determined" in result.output


def test_explain_shows_stance_chain(repo: Repository) -> None:
    result = _invoke(repo, ["explain", "s1"])
    assert result.exit_code == 0, result.output
    assert "concept=speed" in result.output
    assert "s2" in result.output


def test_explain_unknown_claim_fails(repo: Repository) -> None:
    result = _invoke(repo, ["explain", "nope"])
    assert result.exit_code != 0
    assert "Unknown claim: nope" in result.output


def test_algorithms_lists_algorithm_claims(repo: Repository) -> None:
    result = _invoke(repo, ["algorithms"])
    assert result.exit_code == 0, result.output
    assert "alg1" in result.output
    assert "algo one" in result.output


# ── reasoning family ──────────────────────────────────────────────────────────


def test_derive_computes_value(repo: Repository) -> None:
    result = _invoke(repo, ["derive", "C"])
    assert result.exit_code == 0, result.output
    assert "C: derived" in result.output
    assert "value: 5.0" in result.output


def test_resolve_argumentation_picks_winner(repo: Repository) -> None:
    result = _invoke(repo, ["resolve", "speed", "--strategy", "argumentation"])
    assert result.exit_code == 0, result.output
    assert "speed: resolved" in result.output
    assert "winner: s1" in result.output


def test_chain_derives_target(repo: Repository) -> None:
    result = _invoke(repo, ["chain", "C"])
    assert result.exit_code == 0, result.output
    assert "Result: derived" in result.output
    assert "value: 5.0" in result.output


def test_hypothetical_overlay_reports_change(repo: Repository) -> None:
    result = _invoke(
        repo,
        [
            "hypothetical",
            "--add",
            json.dumps(
                {"id": "syn_a", "concept_id": "A", "type": "parameter", "value": 100.0}
            ),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "A:" in result.output


def test_hypothetical_json_shape(repo: Repository) -> None:
    result = _invoke(repo, ["hypothetical", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert "changes" in data
    assert "extension_diff" in data


def test_hypothetical_add_preserves_scalar_value_types() -> None:
    from propstore.cli.world.reasoning import _parse_hypothetical_add

    specs = _parse_hypothetical_add(
        json.dumps(
            [
                {"id": "text", "concept_id": "A", "value": "fast"},
                {"id": "boolean", "concept_id": "A", "value": True},
                {"id": "integer", "concept_id": "A", "value": 2},
                {"id": "float", "concept_id": "A", "value": 2.5},
            ]
        )
    )

    assert type(specs[0].value) is str
    assert type(specs[1].value) is bool
    assert type(specs[2].value) is int
    assert type(specs[3].value) is float


def test_hypothetical_add_rejects_nonscalar_value() -> None:
    from propstore.cli.world.reasoning import _parse_hypothetical_add

    with pytest.raises(click.ClickException, match="value must be a scalar"):
        _parse_hypothetical_add(
            json.dumps({"id": "nested", "concept_id": "A", "value": [1]})
        )


# ── analysis family ───────────────────────────────────────────────────────────


def test_sensitivity_runs(repo: Repository) -> None:
    result = _invoke(repo, ["sensitivity", "C"])
    assert result.exit_code == 0, result.output
    # C = A + B has a parameterization, so a result is produced.
    assert "Sensitivity: C" in result.output


def test_check_consistency_runs(repo: Repository) -> None:
    result = _invoke(repo, ["check-consistency"])
    assert result.exit_code == 0, result.output


def test_fragility_runs(repo: Repository) -> None:
    result = _invoke(repo, ["fragility"])
    assert result.exit_code == 0, result.output
    assert "Fragility Analysis" in result.output


# ── render-policy flag acceptance ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "args",
    [
        ["status"],
        ["query", "A"],
        ["derive", "C"],
        ["resolve", "speed", "--strategy", "recency"],
    ],
)
def test_lifecycle_flags_accepted(repo: Repository, args: list[str]) -> None:
    result = _invoke(
        repo,
        [*args, "--include-drafts", "--include-blocked", "--show-quarantined"],
    )
    assert "no such option" not in result.output.lower()
    assert "error: got unexpected" not in result.output.lower()


# ── revision family ───────────────────────────────────────────────────────────


def _assertion_atom_id(repo: Repository) -> str:
    with WorldQuery(repo) as world_query:
        base = revision_base(
            world_query, RevisionWorldRequest(bindings={}, context_id="ctx1")
        )
    atom_ids = [atom.atom_id for atom in base.atoms]
    assert atom_ids, "expected at least one revision atom"
    return atom_ids[0]


def test_revision_base_shows_atoms(repo: Repository) -> None:
    result = _invoke(repo, ["revision", "base", "--context", "ctx1"])
    assert result.exit_code == 0, result.output
    assert "ps:assertion:" in result.output


def test_revision_entrenchment_shows_ranked_atoms(repo: Repository) -> None:
    result = _invoke(repo, ["revision", "entrenchment", "--context", "ctx1"])
    assert result.exit_code == 0, result.output
    assert "ps:assertion:" in result.output


def test_revision_iterated_state_empty_history(repo: Repository) -> None:
    result = _invoke(repo, ["revision", "iterated-state", "--context", "ctx1"])
    assert result.exit_code == 0, result.output
    assert "Iterated state" in result.output
    assert "History length: 0" in result.output


def test_revision_expand_shows_accepted_atom(repo: Repository) -> None:
    atom_id = _assertion_atom_id(repo)
    result = _invoke(
        repo,
        [
            "revision",
            "expand",
            "--context",
            "ctx1",
            "--atom",
            json.dumps({"kind": "assertion", "id": atom_id}),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Accepted" in result.output
    assert atom_id in result.output


def test_revision_contract_shows_decision_then_realization(repo: Repository) -> None:
    atom_id = _assertion_atom_id(repo)
    result = _invoke(
        repo,
        ["revision", "contract", "--context", "ctx1", "--target", atom_id],
    )
    assert result.exit_code == 0, result.output
    assert result.output.index("Formal decision:") < result.output.index(
        "Support realization:"
    )
    assert "Incision set" in result.output
    assert atom_id in result.output


def test_revision_revise_admits_atom(repo: Repository) -> None:
    atom_id = _assertion_atom_id(repo)
    result = _invoke(
        repo,
        [
            "revision",
            "revise",
            "--context",
            "ctx1",
            "--atom",
            json.dumps({"kind": "assertion", "id": atom_id}),
            "--conflict",
            atom_id,
        ],
    )
    assert result.exit_code == 0, result.output
    assert atom_id in result.output


def test_revision_explain_shows_atom_status(repo: Repository) -> None:
    atom_id = _assertion_atom_id(repo)
    result = _invoke(
        repo,
        [
            "revision",
            "explain",
            "--context",
            "ctx1",
            "--operation",
            "contract",
            "--target",
            atom_id,
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Atoms:" in result.output
    # The adapter renders the owner's per-atom explanation map verbatim.
    assert f"{atom_id}: status=" in result.output


def test_revision_iterated_revise_shows_next_state(repo: Repository) -> None:
    atom_id = _assertion_atom_id(repo)
    result = _invoke(
        repo,
        [
            "revision",
            "iterated-revise",
            "--context",
            "ctx1",
            "--atom",
            json.dumps({"kind": "assertion", "id": atom_id}),
            "--conflict",
            atom_id,
            "--operator",
            "lexicographic",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Operator: lexicographic" in result.output
    assert "Next state" in result.output
    assert "Ranking delta:" in result.output


# ── export-graph family ──────────────────────────────────────────────────────────


def test_export_graph_default_dot(repo: Repository) -> None:
    result = _invoke(repo, ["export-graph"])
    assert result.exit_code == 0, result.output
    assert "digraph" in result.output
    assert "->" in result.output
    assert "A" in result.output


def test_export_graph_json_shape(repo: Repository) -> None:
    result = _invoke(repo, ["export-graph", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert set(data) == {"nodes", "edges"}
    concept_ids = {n["id"] for n in data["nodes"] if n["node_type"] == "concept"}
    assert {"A", "B", "C"} <= concept_ids
    # The equation claim zz_eq parameterizes C from (A, B).
    param = {
        (e["source"], e["target"])
        for e in data["edges"]
        if e["edge_type"] == "parameterization"
    }
    assert ("A", "C") in param
    assert ("B", "C") in param


def test_export_graph_group_scoping(repo: Repository) -> None:
    result = _invoke(repo, ["export-graph", "--group-id", "0", "--format", "json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    concept_ids = {n["id"] for n in data["nodes"] if n["node_type"] == "concept"}
    # The single parameterization group is the equation output {C}.
    assert "C" in concept_ids
    assert "D" not in concept_ids
