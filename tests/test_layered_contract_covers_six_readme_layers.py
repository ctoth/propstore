from __future__ import annotations

import configparser
from pathlib import Path


EXPECTED_LAYER_ROWS = (
    "propstore.web | propstore.cli",
    "propstore.app",
    "propstore.argumentation | propstore.aspic_bridge | propstore.world | propstore.belief_set",
    "propstore.heuristic",
    "propstore.source",
    "propstore.storage",
)

LEGACY_FORBIDDEN_CONTRACTS = {
    "importlinter:contract:storage-merge",
    "importlinter:contract:source-heuristic",
    "importlinter:contract:heuristic-source-finalize",
    "importlinter:contract:concept-argumentation",
    "importlinter:contract:worldline-support-revision",
}


def _load_importlinter_config() -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read(Path(".importlinter"), encoding="utf-8")
    return parser


def _contract_sections(parser: configparser.ConfigParser) -> list[str]:
    return [
        section
        for section in parser.sections()
        if section.startswith("importlinter:contract:")
    ]


def test_importlinter_declares_one_six_layer_contract() -> None:
    parser = _load_importlinter_config()
    contract_sections = _contract_sections(parser)

    assert len(contract_sections) == 1

    section = contract_sections[0]
    assert parser.get(section, "type") == "layers"
    assert parser.get(section, "name") == "propstore six-layer architecture"
    assert parser.get(section, "containers") == "propstore"
    assert tuple(
        line.strip()
        for line in parser.get(section, "layers").splitlines()
        if line.strip()
    ) == EXPECTED_LAYER_ROWS


def test_legacy_forbidden_contracts_are_deleted() -> None:
    parser = _load_importlinter_config()

    assert not (set(_contract_sections(parser)) & LEGACY_FORBIDDEN_CONTRACTS)
    assert {
        parser.get(section, "type")
        for section in _contract_sections(parser)
    } == {"layers"}
