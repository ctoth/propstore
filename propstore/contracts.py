"""The propstore semantic-contract manifest, versioning, and drift gate.

A *contract* is a wire-stable promise the package makes about a structural
surface: the family registry, each family (its identity policy, its
charter-derived foreign keys, its artifact-family codec), each claim-type
authoring contract, and the semantic-pass pipeline (its stages and passes). The
manifest is the serialized union of those promises; the drift gate
(:mod:`tests.test_contract_manifest`) asserts the checked-in manifest still
matches the one derived from code, and that any body change carried a version
bump (``quire.contracts.check_contract_manifest``).

Rewrite translation (PLAN.md §12.6): in the feature-peak tree the manifest
hand-authored *document-schema*, *artifact_family*, and *foreign_key* entries.
Those bodies are now **charter-derived** — the family registry lifts the FK graph,
the identity policy, and the artifact-family codec off each ``@charter`` class —
so they fold into the registry's own ``family-registry`` / ``family`` contract
entries (:meth:`quire.families.FamilyRegistry.contract_entries`) rather than
being re-emitted by hand. What this module still composes by hand is the part the
charter does not own: the per-type **claim-type** contracts and the **semantic
pass / stage** pipeline contracts.

The substrate boundary holds: the contract types are quire's
(:class:`~quire.contracts.ContractEntry`, :class:`~quire.contracts.ContractManifest`,
:class:`~quire.versions.VersionId`); this module supplies propstore's specifics as
arguments, never as a second spelling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quire.artifacts import ArtifactFamily
from quire.contracts import ContractEntry, ContractManifest, contract_version
from quire.references import ForeignKeySpec

from propstore.claim_contracts import ClaimTypeContract, iter_claim_type_contracts
from propstore.families.registry import (
    PROPSTORE_FAMILY_REGISTRY,
    PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION,
    semantic_foreign_keys,
)

PROPSTORE_REGISTRY_CONTRACT_VERSION = PROPSTORE_FAMILY_REGISTRY_CONTRACT_VERSION
"""The assembled registry's wire-contract version (re-exported for API parity).

The registry is the one source of truth for family/FK/identity contracts; this
alias lets contract consumers read the registry version from the manifest module
without importing the registry directly.
"""

CLAIM_TYPE_CONTRACT_VERSION = contract_version("2026.06.30")
"""Wire-contract version stamped on every claim-type authoring contract entry."""

SEMANTIC_PASS_CONTRACT_VERSION = contract_version("2026.06.30")
"""Wire-contract version stamped on every semantic stage / pass entry."""

CONTRACT_MANIFEST_PATH = (
    Path(__file__).resolve().parent
    / "_resources"
    / "contract_manifests"
    / "semantic-contracts.yaml"
)
"""Where the checked-in manifest lives; the drift gate diffs against it."""


def iter_artifact_families() -> tuple[ArtifactFamily[object, object, object], ...]:
    """Every artifact family the registry assembled, sorted by name.

    The bodies fold into the registry's charter-derived ``family`` entries; this
    selector remains so the drift-coverage tests can assert every family carries
    a contract version.
    """

    families = {
        family.artifact_family.name: family.artifact_family
        for family in PROPSTORE_FAMILY_REGISTRY.families
    }
    return tuple(family for _, family in sorted(families.items()))


def iter_semantic_foreign_keys() -> tuple[ForeignKeySpec, ...]:
    """Every charter-derived semantic foreign-key spec, sorted by spec name.

    The bodies fold into each family's charter-derived ``family`` entry; this
    selector remains for the drift-coverage tests.
    """

    return semantic_foreign_keys()


def iter_semantic_pass_classes() -> tuple[type[Any], ...]:
    """Every registered semantic-pass class, grouped by family, in pipeline order.

    Builds the one pipeline registry exactly as the compiler does, so the manifest
    pins the same passes that actually run. The pass class is the framework's own
    ``type[Any]`` handle (see :mod:`propstore.semantic_passes.registry`).
    """

    from propstore.families.claims_passes import register_claim_pipeline
    from propstore.families.concepts_passes import register_concept_pipeline
    from propstore.families.contexts_passes import register_context_pipeline
    from propstore.families.forms_passes import register_form_pipeline
    from propstore.semantic_passes.registry import PipelineRegistry

    registry = PipelineRegistry()
    register_claim_pipeline(registry)
    register_concept_pipeline(registry)
    register_context_pipeline(registry)
    register_form_pipeline(registry)
    return registry.registered_passes()


def iter_semantic_stage_contracts() -> tuple[tuple[str, str, type[Any]], ...]:
    """Every ``(stage_value, family, stage_enum_class)`` the passes traverse.

    Derived from the registered passes — a pass's ``input_stage`` and
    ``output_stage`` are the only source of truth for which stages exist, so a
    stage cannot drift away from a pass that produces or consumes it.
    """

    stages: dict[tuple[str, str], type[Any]] = {}
    for pass_class in iter_semantic_pass_classes():
        family = pass_class.family.value
        for stage in (pass_class.input_stage, pass_class.output_stage):
            stages[(family, stage.value)] = type(stage)
    return tuple(
        (stage_value, family, stage_class)
        for (family, stage_value), stage_class in sorted(stages.items())
    )


def build_propstore_contract_manifest() -> ContractManifest:
    """Assemble the full semantic-contract manifest from code.

    Charter-derived family/FK/identity contracts come straight from the
    registry; the claim-type and semantic-pass/stage contracts are composed here.
    """

    contracts: list[ContractEntry] = list(PROPSTORE_FAMILY_REGISTRY.contract_entries())
    contracts.extend(
        _claim_type_contract(contract) for contract in iter_claim_type_contracts()
    )
    contracts.extend(
        _semantic_stage_contract(*entry) for entry in iter_semantic_stage_contracts()
    )
    contracts.extend(
        _semantic_pass_contract(pass_class)
        for pass_class in iter_semantic_pass_classes()
    )
    return ContractManifest(
        format_version=1,
        package_name="propstore",
        package_version="0.1.0",
        registry_name=PROPSTORE_FAMILY_REGISTRY.name,
        registry_contract_version=PROPSTORE_FAMILY_REGISTRY.contract_version,
        contracts=tuple(contracts),
    )


def _claim_type_contract(contract: ClaimTypeContract) -> ContractEntry:
    return ContractEntry(
        kind="claim_type_contract",
        name=contract.claim_type.value,
        contract_version=CLAIM_TYPE_CONTRACT_VERSION,
        body=_claim_type_body(contract),
    )


def _claim_type_body(contract: ClaimTypeContract) -> dict[str, object]:
    body: dict[str, object] = {
        "required_fields": list(contract.required_fields),
        "nonempty_fields": list(contract.nonempty_fields),
        "concept_links": [
            {
                "field": link.field,
                "role": link.role.value,
                "source": link.source.value,
                "target_family": link.target_family,
            }
            for link in contract.concept_links
        ],
        # Field-less marker dataclasses normalize to ``{}`` and lose their
        # identity, so the contract pins the qualified class name of each check.
        "semantic_checks": [
            f"{type(check).__module__}.{type(check).__qualname__}"
            for check in contract.semantic_checks
        ],
    }
    if contract.value_group is not None:
        body["value_group"] = {
            "value_field": contract.value_group.value_field,
            "lower_bound_field": contract.value_group.lower_bound_field,
            "upper_bound_field": contract.value_group.upper_bound_field,
            "uncertainty_field": contract.value_group.uncertainty_field,
            "uncertainty_type_field": contract.value_group.uncertainty_type_field,
        }
    if contract.unit_policy is not None:
        body["unit_policy"] = {
            "required": contract.unit_policy.required,
            "dimensionless_default_unit": contract.unit_policy.dimensionless_default_unit,
            "form_concept_field": contract.unit_policy.form_concept_field,
        }
    return body


def _semantic_stage_contract(
    stage_value: str,
    family: str,
    stage_class: type[Any],
) -> ContractEntry:
    return ContractEntry(
        kind="semantic_stage",
        name=stage_value,
        contract_version=SEMANTIC_PASS_CONTRACT_VERSION,
        body={
            "family": family,
            "class": f"{stage_class.__module__}.{stage_class.__qualname__}",
        },
    )


def _semantic_pass_contract(pass_class: type[Any]) -> ContractEntry:
    return ContractEntry(
        kind="semantic_pass",
        name=pass_class.name,
        contract_version=SEMANTIC_PASS_CONTRACT_VERSION,
        body={
            "family": pass_class.family.value,
            "input_stage": pass_class.input_stage.value,
            "output_stage": pass_class.output_stage.value,
            "class": f"{pass_class.__module__}.{pass_class.__qualname__}",
        },
    )


def write_propstore_contract_manifest(path: Path = CONTRACT_MANIFEST_PATH) -> Path:
    """(Re)write the checked-in manifest from code; returns the path written."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_propstore_contract_manifest().to_yaml())
    return path
