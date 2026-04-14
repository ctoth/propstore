"""Typed document models for authored context YAML files."""

from __future__ import annotations

from propstore.artifacts.schema import DocumentStruct


class ContextDocument(DocumentStruct):
    id: str
    name: str
    description: str | None = None
    inherits: str | None = None
    assumptions: tuple[str, ...] = ()
    excludes: tuple[str, ...] = ()
