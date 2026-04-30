from __future__ import annotations

import ast
from pathlib import Path


APP_ROOT = Path("propstore/app")


def _dataclass_request_fields() -> dict[str, dict[str, ast.AST | None]]:
    requests: dict[str, dict[str, ast.AST | None]] = {}
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or not node.name.endswith("Request"):
                continue
            if not any(
                isinstance(dec, ast.Name) and dec.id == "dataclass"
                or isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Name)
                and dec.func.id == "dataclass"
                for dec in node.decorator_list
            ):
                continue
            fields: dict[str, ast.AST | None] = {}
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    fields[stmt.target.id] = stmt.annotation
            requests[node.name] = fields
    return requests


def test_app_request_dataclasses_do_not_accept_cli_payload_shapes() -> None:
    requests = _dataclass_request_fields()

    offenders: list[str] = []
    for class_name, fields in requests.items():
        for field_name in fields:
            if field_name.endswith("_json"):
                offenders.append(f"{class_name}.{field_name}")
        if "dimensionless" in fields:
            annotation = ast.unparse(fields["dimensionless"] or ast.Constant(None))
            if annotation == "str" or "str | None" in annotation:
                offenders.append(f"{class_name}.dimensionless")
        if "values" in fields and {"form_name", "closed"} <= set(fields):
            annotation = ast.unparse(fields["values"] or ast.Constant(None))
            if annotation == "str" or "str | None" in annotation:
                offenders.append(f"{class_name}.values")

    assert offenders == []


def test_worldline_revision_atom_json_parsing_is_not_owned_by_app_layer() -> None:
    text = Path("propstore/app/worldlines.py").read_text(encoding="utf-8")

    assert "def parse_worldline_revision_atom(" not in text
    assert "--revision-atom" not in text
