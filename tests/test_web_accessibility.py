"""Phase 10-2: accessible-document-structure proof for the web HTML adapter.

Parses the rendered HTML with the stdlib HTML parser and asserts the
assistive-technology-relevant facts directly — one ``<main>`` landmark, a single
``<h1>``, ``<h2>``-titled sections, tables with column headers and non-empty
cells, descriptive link text, and the honest-ignorance literals the owner views
emit. No screen reader required: the DOM facts are the proof.
"""

from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
from pathlib import Path

import pytest

from propstore.web.html import LinkRow, _link_table
from tests.web_helpers import demo_client

_CSS_PATH = Path("propstore") / "web" / "static" / "web.css"


class _HtmlAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.h1_texts: list[str] = []
        self.h2_texts: list[str] = []
        self.title_text = ""
        self.main_count = 0
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


def test_claim_page_has_accessible_document_structure(tmp_path: Path) -> None:
    html = demo_client(tmp_path).get("/claim/p_missingval").text
    audit = _audit(html)

    assert audit.h1_texts == ["Claim p_missingval"]
    assert audit.title_text == "Claim p_missingval - propstore"
    assert audit.main_count == 1
    assert {
        "Summary",
        "Render State",
        "Provenance",
        "Neighborhood",
        "Machine IDs",
    } <= set(audit.h2_texts)
    assert "Open semantic neighborhood for this claim" in audit.link_texts
    assert "missing" in html
    assert "vacuous" in html


def test_concept_page_has_accessible_tables(tmp_path: Path) -> None:
    html = demo_client(tmp_path).get("/concept/speed").text
    audit = _audit(html)

    assert audit.h1_texts == ["Concept speed"]
    assert audit.title_text == "Concept speed - propstore"
    assert audit.main_count == 1
    assert {
        "Summary",
        "Render State",
        "Form",
        "Value Summary",
        "Uncertainty",
        "Provenance",
        "Claims By Type",
        "Related Claims",
        "Machine IDs",
    } <= set(audit.h2_texts)
    assert audit.table_count >= 1
    assert all(count > 0 for count in audit.header_counts)
    assert all(cell for cell in audit.cell_texts)


def test_neighborhood_page_has_accessible_tables_and_literals(tmp_path: Path) -> None:
    html = demo_client(tmp_path).get("/claim/p_speed/neighborhood").text
    audit = _audit(html)

    assert audit.h1_texts == ["Neighborhood for p_speed"]
    assert audit.main_count == 1
    assert {
        "Focus",
        "Available Moves",
        "Supporters",
        "Attackers",
        "Conditions",
        "Provenance",
        "Shared Concept",
        "Raw Graph Projection",
        "Render State",
    } <= set(audit.h2_texts)
    assert audit.table_count >= 6
    assert all(count > 0 for count in audit.header_counts)
    assert all(cell for cell in audit.cell_texts)
    assert "Open claim view for this focus claim" in audit.link_texts
    assert "unavailable" in html


def test_error_page_has_accessible_heading_and_message(tmp_path: Path) -> None:
    response = demo_client(tmp_path).get("/claim/does-not-exist")
    audit = _audit(response.text)

    assert response.status_code == 404
    assert audit.h1_texts == ["Claim Not Found"]
    assert audit.title_text == "Claim Not Found - propstore"
    assert audit.main_count == 1
    assert audit.h2_texts == ["What happened"]
    assert "not found" in unescape(response.text).lower()
    assert 'href="/"' in response.text


def test_web_surface_has_no_hover_or_pointer_required_css() -> None:
    css = _CSS_PATH.read_text(encoding="utf-8")

    assert ":hover" not in css
    assert "pointer-events" not in css
    assert "cursor:" not in css


def test_web_css_has_document_reading_system() -> None:
    css = _CSS_PATH.read_text(encoding="utf-8")

    assert "max-width:" in css
    assert "overflow-x: auto" in css
    assert ":focus-visible" in css
    assert "outline:" in css
    assert "@media print" in css
    assert "@media (max-width:" in css


def test_link_table_uses_typed_rows_and_rejects_misaligned_cells() -> None:
    html = _link_table(
        ("Claim", "Status"),
        [LinkRow("p_speed", "/claim/p_speed", ("known",))],
    )

    assert '<a href="/claim/p_speed">p_speed</a>' in html
    assert "<td>known</td>" in html

    with pytest.raises(ValueError, match="LinkRow has 2 cells for 3 headers"):
        _link_table(
            ("Claim", "Status", "Reason"),
            [LinkRow("p_speed", "/claim/p_speed", ("known",))],
        )
