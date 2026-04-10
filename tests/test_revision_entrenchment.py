from __future__ import annotations

import ast
from pathlib import Path

from propstore.core.labels import AssumptionRef, Label
from propstore.revision.entrenchment import compute_entrenchment
from propstore.revision.state import BeliefAtom, BeliefBase, RevisionScope


class _BoundStub:
    def claim_essential_support(self, claim_id: str):
        return None


def test_compute_entrenchment_source_override_outranks_default_ordering() -> None:
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=(
            BeliefAtom(
                atom_id="claim:claim_alpha",
                kind="claim",
                payload={"id": "claim_alpha", "source_paper": "paper_alpha"},
                label=Label.empty(),
            ),
            BeliefAtom(
                atom_id="claim:claim_beta",
                kind="claim",
                payload={"id": "claim_beta", "source_paper": "paper_beta"},
                label=Label.empty(),
            ),
        ),
    )

    report = compute_entrenchment(
        _BoundStub(),
        base,
        overrides={"source:paper_beta": {"priority": "preferred-source"}},
    )

    assert report.ranked_atom_ids[0] == "claim:claim_beta"
    assert report.reasons["claim:claim_beta"].override_priority == "preferred-source"
    assert report.reasons["claim:claim_beta"].override_key == "source:paper_beta"


def test_compute_entrenchment_kind_override_can_promote_assumptions() -> None:
    base = BeliefBase(
        scope=RevisionScope(bindings={}),
        atoms=(
            BeliefAtom(
                atom_id="claim:claim_alpha",
                kind="claim",
                payload={"id": "claim_alpha"},
                label=Label.empty(),
            ),
            BeliefAtom(
                atom_id="assumption:env:x_eq_1",
                kind="assumption",
                payload={
                    "assumption_id": "env:x_eq_1",
                    "cel": "x == 1",
                    "kind": "binding",
                },
                label=None,
            ),
        ),
        assumptions=(
            AssumptionRef(
                assumption_id="env:x_eq_1",
                kind="binding",
                source="binding",
                cel="x == 1",
            ),
        ),
    )

    report = compute_entrenchment(
        _BoundStub(),
        base,
        overrides={"kind:assumption": {"priority": "protect-assumptions"}},
    )

    assert report.ranked_atom_ids[0] == "assumption:env:x_eq_1"
    assert report.reasons["assumption:env:x_eq_1"].override_priority == "protect-assumptions"
    assert report.reasons["assumption:env:x_eq_1"].override_key == "kind:assumption"


def test_revision_modules_do_not_import_ic_merge() -> None:
    revision_dir = Path("propstore/revision")
    assert revision_dir.exists()

    for path in sorted(revision_dir.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imports.append(node.module)
        assert "propstore.repo.ic_merge" not in imports
