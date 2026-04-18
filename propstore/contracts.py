from __future__ import annotations

import argparse
import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Any

import msgspec
from quire.artifacts import ArtifactFamily
from quire.contracts import ContractEntry, ContractManifest
from quire.references import ForeignKeySpec
from quire.versions import VersionId

if TYPE_CHECKING:
    from propstore.artifacts.documents.claims import ClaimTypeContract
    from propstore.artifacts.semantic_families import SemanticFamilyDefinition

PROPSTORE_REGISTRY_CONTRACT_VERSION = VersionId("2026.04.19")
CONTRACT_MANIFEST_PATH = (
    Path(__file__).resolve().parent
    / "contract_manifests"
    / "semantic-contracts.yaml"
)


def iter_artifact_families() -> tuple[ArtifactFamily[Any, Any, Any], ...]:
    from propstore.artifacts import families

    discovered = [
        value
        for value in vars(families).values()
        if isinstance(value, ArtifactFamily)
    ]
    return tuple(sorted(discovered, key=lambda family: family.name))


def iter_semantic_foreign_keys() -> tuple[ForeignKeySpec, ...]:
    from propstore.artifacts.semantic_families import SEMANTIC_FAMILIES

    return tuple(sorted(SEMANTIC_FAMILIES.foreign_keys(), key=lambda spec: spec.name))


def iter_semantic_families() -> tuple["SemanticFamilyDefinition", ...]:
    from propstore.artifacts.semantic_families import SEMANTIC_FAMILIES

    return tuple(sorted(SEMANTIC_FAMILIES.families, key=lambda family: family.name))


def iter_claim_type_contracts() -> tuple["ClaimTypeContract", ...]:
    from propstore.artifacts.documents.claims import (
        iter_claim_type_contracts as iter_contracts,
    )

    return iter_contracts()


def iter_document_schema_types() -> tuple[type[msgspec.Struct], ...]:
    from propstore.artifacts.documents import (
        claims,
        concepts,
        contexts,
        forms,
        merge,
        micropubs,
        predicates,
        rules,
        source_alignment,
        sources,
        stances,
        worldlines,
    )

    modules = (
        claims,
        concepts,
        contexts,
        forms,
        merge,
        micropubs,
        predicates,
        rules,
        source_alignment,
        sources,
        stances,
        worldlines,
    )
    schema_types: list[type[msgspec.Struct]] = []
    for module in modules:
        for value in vars(module).values():
            if not inspect.isclass(value):
                continue
            if not issubclass(value, msgspec.Struct):
                continue
            if value.__module__ != module.__name__:
                continue
            schema_types.append(value)
    return tuple(sorted(schema_types, key=lambda item: f"{item.__module__}.{item.__name__}"))


def build_propstore_contract_manifest() -> ContractManifest:
    contracts: list[ContractEntry] = []
    contracts.extend(_document_contract(document_type) for document_type in iter_document_schema_types())
    contracts.extend(_family_contract(family) for family in iter_artifact_families())
    contracts.extend(_semantic_family_contract(family) for family in iter_semantic_families())
    contracts.extend(_foreign_key_contract(spec) for spec in iter_semantic_foreign_keys())
    contracts.extend(_claim_type_contract(contract) for contract in iter_claim_type_contracts())
    return ContractManifest(
        format_version=1,
        package_name="propstore",
        package_version="0.1.0",
        registry_name="semantic-family-registry",
        registry_contract_version=PROPSTORE_REGISTRY_CONTRACT_VERSION,
        contracts=tuple(contracts),
    )


def _document_contract(document_type: type[msgspec.Struct]) -> ContractEntry:
    fields = []
    annotations = getattr(document_type, "__annotations__", {})
    for name in getattr(document_type, "__struct_fields__", ()):
        fields.append({
            "name": name,
            "type": _render_type(annotations.get(name, object)),
            "required": name not in getattr(document_type, "__struct_defaults__", ()),
        })
    return ContractEntry(
        kind="document_schema",
        name=document_type.__name__,
        contract_version=PROPSTORE_REGISTRY_CONTRACT_VERSION,
        body={
            "module": document_type.__module__,
            "fields": tuple(fields),
        },
    )


def _family_contract(family: ArtifactFamily[Any, Any, Any]) -> ContractEntry:
    return ContractEntry(
        kind="artifact_family",
        name=family.name,
        contract_version=family.contract_version,
        body={
            "doc_type": f"{family.doc_type.__module__}.{family.doc_type.__qualname__}",
            "resolve_ref": _callback_id(family.resolve_ref),
            "coerce_payload": _callback_id(family.coerce_payload),
            "decode_bytes": _callback_id(family.decode_bytes),
            "encode_document": _callback_id(family.encode_document),
            "render_document": _callback_id(family.render_document),
            "document_payload": _callback_id(family.document_payload),
            "normalize_for_write": _callback_id(family.normalize_for_write),
            "validate_for_write": _callback_id(family.validate_for_write),
            "list_refs": _callback_id(family.list_refs),
            "ref_from_path": _callback_id(family.ref_from_path),
            "ref_from_loaded": _callback_id(family.ref_from_loaded),
            "scan_type": (
                None
                if family.scan_type is None
                else f"{family.scan_type.__module__}.{family.scan_type.__qualname__}"
            ),
        },
    )


def _semantic_family_contract(family: "SemanticFamilyDefinition") -> ContractEntry:
    return ContractEntry(
        kind="semantic_family",
        name=family.name,
        contract_version=family.contract_version,
        body=family.contract_body(),
    )


def _foreign_key_contract(spec: ForeignKeySpec) -> ContractEntry:
    return ContractEntry(
        kind="foreign_key",
        name=spec.name,
        contract_version=spec.contract_version,
        body=spec.contract_body(),
    )


def _claim_type_contract(contract: "ClaimTypeContract") -> ContractEntry:
    return ContractEntry(
        kind="claim_type_contract",
        name=contract.claim_type.value,
        contract_version=contract.contract_version,
        body=contract.contract_body(),
    )


def _callback_id(callback: object) -> str | None:
    if callback is None:
        return None
    module = getattr(callback, "__module__", None)
    qualname = getattr(callback, "__qualname__", None)
    if module and qualname:
        return f"{module}.{qualname}"
    return repr(callback)


def _render_type(value: object) -> str:
    module = getattr(value, "__module__", None)
    qualname = getattr(value, "__qualname__", None)
    if module and qualname:
        return f"{module}.{qualname}"
    return str(value).replace("typing.", "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    payload = build_propstore_contract_manifest().to_yaml()
    if args.write:
        CONTRACT_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONTRACT_MANIFEST_PATH.write_bytes(payload)
    else:
        print(payload.decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
