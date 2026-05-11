"""Loaded-rule file helpers for grounding and ASPIC workflows."""

from __future__ import annotations

from propstore.families.documents.rules import RuleDocument, RulesFileDocument
from quire.documents import LoadedDocument


class LoadedRuleFile(LoadedDocument[RulesFileDocument]):
    """Typed rule-file envelope."""

    @classmethod
    def from_loaded_document(
        cls,
        document: LoadedDocument[RulesFileDocument],
    ) -> LoadedRuleFile:
        return cls(
            filename=document.filename,
            artifact_path=document.artifact_path,
            store_root=document.store_root,
            document=document.document,
        )

    @property
    def rules(self) -> tuple[RuleDocument, ...]:
        return self.document.rules
