from __future__ import annotations

from pathlib import Path

from argumentation.aspic import GroundAtom
from sqlalchemy import select

from quire.sqlalchemy_store import (
    create_sqlalchemy_store,
    readonly_session,
    writable_session,
)
from propstore.families.rules.declaration import (
    AtomDocument,
    BodyLiteralDocument,
    RuleDocument,
    TermDocument,
)
from propstore.families.rules.declaration import (
    GroundedBundleInput,
    load_grounded_bundle,
    persist_grounded_bundle,
)
from propstore.families.registry import (
    world_schema,
)
from propstore.grounding.grounder import ground
from propstore.grounding.predicates import PredicateRegistry


def _fresh_store(tmp_path: Path) -> Path:
    sidecar_path = tmp_path / "propstore.sqlite"
    create_sqlalchemy_store(sidecar_path, world_schema())
    return sidecar_path


def _birds_fly_bundle():
    variable = TermDocument(kind="var", name="X")
    rule = RuleDocument(
        id="flies_if_bird",
        kind="defeasible",
        head=AtomDocument(predicate="flies", terms=(variable,)),
        body=(
            BodyLiteralDocument(
                kind="positive",
                atom=AtomDocument(predicate="bird", terms=(variable,)),
            ),
        ),
    )
    return ground(
        (rule,),
        (GroundAtom("bird", ("tweety",)),),
        PredicateRegistry(()),
        return_arguments=True,
    )


def test_grounded_bundle_rehydrates_inputs_and_arguments(tmp_path: Path) -> None:
    bundle = _birds_fly_bundle()
    sidecar_path = _fresh_store(tmp_path)

    with writable_session(sidecar_path, world_schema()) as derived:
        persist_grounded_bundle(derived, bundle)
        derived.session.commit()

    with readonly_session(sidecar_path, world_schema()) as derived:
        restored = load_grounded_bundle(derived)

    assert restored.source_rules == bundle.source_rules
    assert restored.source_facts == bundle.source_facts
    assert restored.sections == bundle.sections
    assert restored.arguments == bundle.arguments
    assert restored.grounding_inspection is not None
