"""Application-layer world revision workflows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from propstore.app.world import open_app_world_model
from propstore.repository import Repository
from propstore.support_revision.state import BeliefAtom, is_assumption_atom, is_assertion_atom


class WorldRevisionAppError(Exception):
    """Base class for expected world-revision app failures."""


class WorldRevisionValidationError(WorldRevisionAppError):
    pass


@dataclass(frozen=True)
class AppRevisionWorldRequest:
    bindings: Mapping[str, str]
    context: str | None = None


@dataclass(frozen=True)
class AppRevisionExpandRequest:
    world: AppRevisionWorldRequest
    atom: Mapping[str, object]


@dataclass(frozen=True)
class AppRevisionContractRequest:
    world: AppRevisionWorldRequest
    targets: Sequence[str]


@dataclass(frozen=True)
class AppRevisionReviseRequest:
    world: AppRevisionWorldRequest
    atom: Mapping[str, object]
    conflicts: Sequence[str]


@dataclass(frozen=True)
class AppRevisionExplainRequest:
    world: AppRevisionWorldRequest
    operation: str
    atom: Mapping[str, object] | None = None
    targets: Sequence[str] = ()
    conflicts: Sequence[str] = ()


@dataclass(frozen=True)
class AppIteratedReviseRequest:
    world: AppRevisionWorldRequest
    atom: Mapping[str, object]
    conflicts: Sequence[str]
    operator: str


@dataclass(frozen=True)
class RevisionAtomDisplay:
    atom_id: str
    display_id: str
    claim_type: str | None = None
    concept_id: str | None = None
    value: object | None = None
    unit: str | None = None


def _lower_request(request: AppRevisionWorldRequest):
    from propstore.support_revision.workflows import RevisionWorldRequest

    return RevisionWorldRequest(request.bindings, request.context)


def revision_atom_display(atom: BeliefAtom) -> RevisionAtomDisplay:
    if is_assertion_atom(atom):
        claim = atom.primary_source_claim
        primary_logical_id = None if claim is None else claim.primary_logical_id
        if primary_logical_id:
            display_value = primary_logical_id.split(":", 1)[1] if ":" in primary_logical_id else primary_logical_id
            display_id = display_value
        else:
            display_id = atom.atom_id
        return RevisionAtomDisplay(
            atom_id=atom.atom_id,
            display_id=display_id,
            claim_type=None if claim is None or claim.claim_type is None else claim.claim_type.value,
            concept_id=None if claim is None or claim.value_concept_id is None else str(claim.value_concept_id),
            value=None if claim is None else claim.row.value,
            unit=None if claim is None else claim.unit,
        )
    if is_assumption_atom(atom):
        return RevisionAtomDisplay(
            atom_id=atom.atom_id,
            display_id=atom.atom_id,
        )
    raise TypeError(f"unsupported revision atom: {type(atom).__name__}")


def world_revision_base(repo: Repository, request: AppRevisionWorldRequest):
    from propstore.support_revision.workflows import revision_base

    with open_app_world_model(repo) as world:
        return revision_base(world, _lower_request(request))


def world_revision_entrenchment(repo: Repository, request: AppRevisionWorldRequest):
    from propstore.support_revision.workflows import revision_entrenchment

    with open_app_world_model(repo) as world:
        return revision_entrenchment(world, _lower_request(request))


def world_revision_expand(repo: Repository, request: AppRevisionExpandRequest):
    from propstore.support_revision.workflows import expand_revision

    with open_app_world_model(repo) as world:
        return expand_revision(world, _lower_request(request.world), dict(request.atom))


def world_revision_contract(repo: Repository, request: AppRevisionContractRequest):
    from propstore.support_revision.workflows import contract_revision

    with open_app_world_model(repo) as world:
        return contract_revision(world, _lower_request(request.world), tuple(request.targets))


def world_revision_revise(repo: Repository, request: AppRevisionReviseRequest):
    from propstore.support_revision.workflows import revise_world

    with open_app_world_model(repo) as world:
        return revise_world(
            world,
            _lower_request(request.world),
            dict(request.atom),
            tuple(request.conflicts),
        )


def world_revision_explain(repo: Repository, request: AppRevisionExplainRequest):
    from propstore.support_revision.workflows import explain_revision_operation

    if request.operation == "expand" and request.atom is None:
        raise WorldRevisionValidationError("--atom is required for --operation expand")
    if request.operation == "contract" and not request.targets:
        raise WorldRevisionValidationError("--target is required for --operation contract")
    if request.operation == "revise" and request.atom is None:
        raise WorldRevisionValidationError("--atom is required for --operation revise")
    with open_app_world_model(repo) as world:
        try:
            return explain_revision_operation(
                world,
                _lower_request(request.world),
                operation=request.operation,
                atom=None if request.atom is None else dict(request.atom),
                targets=tuple(request.targets),
                conflicts=tuple(request.conflicts),
            )
        except ValueError as exc:
            raise WorldRevisionValidationError(str(exc)) from exc


def world_revision_epistemic_state(repo: Repository, request: AppRevisionWorldRequest):
    from propstore.support_revision.workflows import epistemic_state

    with open_app_world_model(repo) as world:
        return epistemic_state(world, _lower_request(request))


def world_revision_iterated_revise(repo: Repository, request: AppIteratedReviseRequest):
    from propstore.support_revision.workflows import iterated_revise_world

    with open_app_world_model(repo) as world:
        return iterated_revise_world(
            world,
            _lower_request(request.world),
            atom=dict(request.atom),
            conflicts=tuple(request.conflicts),
            operator=request.operator,
        )
