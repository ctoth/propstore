from __future__ import annotations

from propstore.artifacts.schema import (
    DocumentSchemaError,
    DocumentStruct,
    decode_document_bytes,
    load_document,
)


class _ExampleDocument(DocumentStruct):
    name: str
    value: int


def test_decode_document_bytes_is_strict() -> None:
    payload = b"name: demo\nvalue: 3\nextra: nope\n"

    try:
        decode_document_bytes(payload, _ExampleDocument, source="example.yaml")
    except DocumentSchemaError as exc:
        assert "example.yaml" in str(exc)
        assert "extra" in str(exc)
    else:
        raise AssertionError("expected strict document decode failure")


def test_load_document_captures_source_metadata(tmp_path) -> None:
    path = tmp_path / "demo.yaml"
    path.write_text("name: demo\nvalue: 3\n", encoding="utf-8")

    loaded = load_document(path, _ExampleDocument, knowledge_root=tmp_path)

    assert loaded.filename == "demo"
    assert loaded.document == _ExampleDocument(name="demo", value=3)
    assert loaded.source_path is not None
    assert loaded.source_path.as_posix().endswith("demo.yaml")
    assert loaded.knowledge_root is not None
