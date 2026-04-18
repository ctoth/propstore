from __future__ import annotations

from quire.documents import (
    DocumentSchemaError,
    DocumentStruct,
    decode_document_bytes,
    load_document_dir,
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


def test_load_document_dir_returns_empty_for_missing_none_and_empty_dirs(tmp_path) -> None:
    assert load_document_dir(None, _ExampleDocument) == []
    assert load_document_dir(tmp_path / "missing", _ExampleDocument) == []

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    assert load_document_dir(empty_dir, _ExampleDocument) == []


def test_load_document_dir_skips_non_yaml_files_and_directories(tmp_path) -> None:
    documents_dir = tmp_path / "documents"
    nested_dir = documents_dir / "nested.yaml"
    documents_dir.mkdir()
    nested_dir.mkdir()
    (documents_dir / "demo.yaml").write_text("name: demo\nvalue: 3\n", encoding="utf-8")
    (documents_dir / "notes.txt").write_text("not: yaml\n", encoding="utf-8")
    (nested_dir / "ignored.yaml").write_text("name: ignored\nvalue: 0\n", encoding="utf-8")

    loaded = load_document_dir(documents_dir, _ExampleDocument)

    assert [document.filename for document in loaded] == ["demo"]
    assert loaded[0].document == _ExampleDocument(name="demo", value=3)


def test_load_document_dir_loads_direct_yaml_children_deterministically(tmp_path) -> None:
    documents_dir = tmp_path / "documents"
    documents_dir.mkdir()
    (documents_dir / "b.yaml").write_text("name: beta\nvalue: 2\n", encoding="utf-8")
    (documents_dir / "a.yaml").write_text("name: alpha\nvalue: 1\n", encoding="utf-8")

    loaded = load_document_dir(documents_dir, _ExampleDocument)

    assert [document.filename for document in loaded] == ["a", "b"]
    assert [document.document.name for document in loaded] == ["alpha", "beta"]


def test_load_document_dir_preserves_source_metadata(tmp_path) -> None:
    documents_dir = tmp_path / "documents"
    documents_dir.mkdir()
    (documents_dir / "demo.yaml").write_text("name: demo\nvalue: 3\n", encoding="utf-8")

    [loaded] = load_document_dir(documents_dir, _ExampleDocument)

    assert loaded.filename == "demo"
    assert loaded.source_path is not None
    assert loaded.source_path.as_posix().endswith("documents/demo.yaml")
    assert loaded.knowledge_root is not None
    assert loaded.knowledge_root.as_posix().endswith(tmp_path.name)


def test_load_document_dir_wrapper_controls_return_type(tmp_path) -> None:
    documents_dir = tmp_path / "documents"
    documents_dir.mkdir()
    (documents_dir / "demo.yaml").write_text("name: demo\nvalue: 3\n", encoding="utf-8")

    loaded = load_document_dir(
        documents_dir,
        _ExampleDocument,
        wrapper=lambda document: f"{document.filename}:{document.document.value}",
    )

    assert loaded == ["demo:3"]
