from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

import pytest

from propstore.web.html import (
    LinkRow,
    _link_table,
    render_claim_page,
    render_concept_page,
    render_error_page,
    render_neighborhood_page,
)
from tests.test_web_claim_routes import _report as _claim_report
from tests.test_web_concept_routes import _report as _concept_report
from tests.test_web_neighborhood_routes import _report as _neighborhood_report


class _HtmlAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_texts: list[str] = []
        self.h2_texts: list[str] = []
        self.title_text = ""
        self.main_count = 0
        self.section_count = 0
        self.table_count = 0
        self.header_counts: list[int] = []
        self.cell_texts: list[str] = []
        self.link_texts: list[str] = []
        self._stack: list[str] = []
        self._current_text = ""
        self._current_header_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._stack.append(tag)
        if tag == "main":
            self.main_count += 1
        if tag == "section":
            self.section_count += 1
        if tag == "table":
            self.table_count += 1
            self._current_header_count = 0
        if tag == "th":
            self._current_header_count += 1
        if tag in {"h1", "h2", "title", "td", "a"}:
            self._current_text = ""

    def handle_data(self, data: str) -> None:
        if self._stack and self._stack[-1] in {"h1", "h2", "title", "td", "a"}:
            self._current_text += data

    def handle_endtag(self, tag: str) -> None:
        text = self._current_text.strip()
        if tag == "h1":
            self.h1_texts.append(text)
        if tag == "h2":
            self.h2_texts.append(text)
        if tag == "title":
            self.title_text = text
        if tag == "td":
            self.cell_texts.append(text)
        if tag == "a":
            self.link_texts.append(text)
        if tag == "table":
            self.header_counts.append(self._current_header_count)
        if self._stack:
            self._stack.pop()


def _audit(html: str) -> _HtmlAudit:
    parser = _HtmlAudit()
    parser.feed(html)
    return parser


def test_claim_page_has_accessible_document_structure() -> None:
    html = render_claim_page(_claim_report())
    audit = _audit(html)

    assert audit.h1_texts == ["Claim claim1"]
    assert audit.title_text == "Claim claim1 - propstore"
    assert audit.main_count == 1
    assert set(audit.h2_texts) >= {
        "Summary",
        "Render State",
        "Provenance",
        "Neighborhood",
        "Machine IDs",
    }
    assert "Open semantic neighborhood for this claim" in audit.link_texts
    assert "unknown" in html
    assert "vacuous" in html
    assert "blocked" in html
    assert "missing" in html
    assert "not applicable" in html


def test_neighborhood_page_has_accessible_tables_and_literals() -> None:
    html = render_neighborhood_page(_neighborhood_report())
    audit = _audit(html)

    assert audit.h1_texts == ["Neighborhood for Claim One"]
    assert audit.title_text == "Neighborhood for Claim One - propstore"
    assert audit.main_count == 1
    assert set(audit.h2_texts) >= {
        "Focus",
        "Available Moves",
        "Supporters",
        "Attackers",
        "Conditions",
        "Provenance",
        "Shared Concept",
        "Raw Graph Projection",
        "Render State",
    }
    assert audit.table_count >= 6
    assert all(count > 0 for count in audit.header_counts)
    assert all(cell for cell in audit.cell_texts)
    assert "Open claim view for this focus claim" in audit.link_texts
    assert "unavailable" in html
    assert "vacuous" in html
    assert "unknown" in html
    assert "blocked" in html


def test_concept_page_has_accessible_tables_and_literals() -> None:
    html = render_concept_page(_concept_report())
    audit = _audit(html)

    assert audit.h1_texts == ["Concept fundamental_frequency"]
    assert audit.title_text == "Concept fundamental_frequency - propstore"
    assert audit.main_count == 1
    assert set(audit.h2_texts) >= {
        "Summary",
        "Render State",
        "Form",
        "Value Summary",
        "Uncertainty",
        "Provenance",
        "Claims By Type",
        "Related Claims",
        "Machine IDs",
    }
    assert audit.table_count >= 2
    assert all(count > 0 for count in audit.header_counts)
    assert all(cell for cell in audit.cell_texts)
    assert "paper:claim1" in audit.link_texts
    assert "known" in html
    assert "missing" in html
    assert "blocked" in html


def test_error_page_has_accessible_heading_and_literal_message() -> None:
    html = render_error_page("Claim Not Found", "Claim 'missing' not found.")
    audit = _audit(html)

    assert audit.h1_texts == ["Claim Not Found"]
    assert audit.title_text == "Claim Not Found"
    assert audit.main_count == 1
    assert audit.h2_texts == ["Error"]
    assert "Claim &#x27;missing&#x27; not found." in html


def test_web_surface_has_no_hover_or_pointer_required_css() -> None:
    css = (Path("propstore") / "web" / "static" / "web.css").read_text(encoding="utf-8")

    assert ":hover" not in css
    assert "pointer-events" not in css
    assert "cursor:" not in css


def test_web_css_has_document_reading_system() -> None:
    css = (Path("propstore") / "web" / "static" / "web.css").read_text(encoding="utf-8")

    assert "max-width:" in css
    assert "overflow-x: auto" in css
    assert ":focus-visible" in css
    assert "outline:" in css
    assert "@media print" in css
    assert "@media (max-width:" in css


def test_link_table_uses_typed_rows_and_rejects_misaligned_cells() -> None:
    html = _link_table(
        ("Claim", "Status"),
        [LinkRow("paper:claim1", "/claim/claim1", ("known",))],
    )

    assert '<a href="/claim/claim1">paper:claim1</a>' in html
    assert "<td>known</td>" in html

    with pytest.raises(ValueError, match="LinkRow has 2 cells for 3 headers"):
        _link_table(
            ("Claim", "Status", "Reason"),
            [LinkRow("paper:claim1", "/claim/claim1", ("known",))],
        )


def test_html_presenters_use_shared_layout_helpers() -> None:
    source = (Path("propstore") / "web" / "html.py").read_text(encoding="utf-8")

    assert "_render_policy_rows" in source
    assert "_render_policy_section" in source
    assert "_machine_ids_section" in source
    assert '"Reasoning backend", report.render_policy.reasoning_backend' not in source
    assert '"Include drafts", _bool_text(report.render_policy.include_drafts)' not in source
