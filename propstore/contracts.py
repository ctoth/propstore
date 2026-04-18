from __future__ import annotations

import argparse
import inspect
from pathlib import Path
from typing import Any

import msgspec
from quire.contracts import ContractEntry, ContractManifest
from quire.versions import VersionId

from propstore.artifacts.types import ArtifactFamily

PROPSTORE_REGISTRY_CONTRACT_VERSION = VersionId("2026.04.18")
CONTRACT_MANIFEST_PATH = (
    Path(__file__).resolve().parent
    / "contract_manifests"
    / "semantic-contracts.yaml"
)


def iter_artifact_families() -> tuple[ArtifactFamily[Any, Any], ...]:
    from propstore.artifacts import families

    discovered = [
        value
        for value in vars(families).values()
        if isinstance(value, ArtifactFamily)
    ]
    return tuple(sorted(discovered, key=lambda family: family.name))


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


def _family_contract(family: ArtifactFamily[Any, Any]) -> ContractEntry:
    return ContractEntry(
        kind="artifact_family",
        name=family.name,
        contract_version=family.contract_version,
        body={
            "doc_type": f"{family.doc_type.__module__}.{family.doc_type.__qualname__}",
            "has_coerce_payload": family.coerce_payload is not None,
            "has_decode_bytes": family.decode_bytes is not None,
            "has_encode_document": family.encode_document is not None,
            "has_render_document": family.render_document is not None,
            "has_document_payload": family.document_payload is not None,
            "has_normalize_for_write": family.normalize_for_write is not None,
            "has_validate_for_write": family.validate_for_write is not None,
            "has_list_refs": family.list_refs is not None,
            "has_ref_from_path": family.ref_from_path is not None,
            "has_ref_from_loaded": family.ref_from_loaded is not None,
            "scan_type": (
                None
                if family.scan_type is None
                else f"{family.scan_type.__module__}.{family.scan_type.__qualname__}"
            ),
        },
    )


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
