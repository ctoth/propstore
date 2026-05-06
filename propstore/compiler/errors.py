from __future__ import annotations


class CompilerWorkflowError(Exception):
    """Raised when a compiler workflow reports blocking diagnostics."""

    def __init__(self, summary: str, messages: object) -> None:
        super().__init__(summary)
        self.summary = summary
        self.messages = messages
