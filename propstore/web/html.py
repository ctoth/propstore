"""Accessible HTML presenters for the Phase-10-0 app reports.

Pure-Python, escape-by-default rendering (no template engine): every dynamic
value passes through :func:`html.escape`, every page is one ``<main>`` with a
single ``<h1>`` and ``<h2>``-titled ``<section>`` landmarks, and every table
carries ``<th>`` headers with non-empty ``<td>`` cells. The literals the owner
view-builders use for honest ignorance (``unknown``, ``vacuous``, ``blocked``,
``missing``, ``not applicable``, ``unavailable``) flow straight through to the
DOM so an assistive-technology reader hears them verbatim. The presenters render
the *typed* report dataclasses from :mod:`propstore.app`; they hold no domain
logic of their own.
"""

from __future__ import annotations

from html import escape
from typing import NamedTuple
from urllib.parse import quote

from propstore.app.claim_views import ClaimViewReport
from propstore.app.claims import ClaimSummaryReport
from propstore.app.concept_views import (
    ConceptClaimGroup,
    ConceptRelatedClaimLink,
    ConceptViewReport,
)
from propstore.app.concepts import ConceptListReport, ConceptSearchReport
from propstore.app.neighborhoods import (
    SemanticEdge,
    SemanticMove,
    SemanticNeighborhoodReport,
    SemanticNeighborhoodRow,
    SemanticNode,
)
from propstore.app.rendering import RenderPolicySummary
from propstore.app.repository_overview import (
    InventoryRow,
    OverviewSection,
    RepositoryOverviewReport,
)


class LinkRow(NamedTuple):
    """One table row whose first cell is a link and the rest plain cells."""

    link_text: str
    href: str
    cells: tuple[str, ...]


# ── page presenters ──────────────────────────────────────────────────────────


def render_index_page(report: RepositoryOverviewReport) -> str:
    body = "\n".join(
        [
            _h1("propstore"),
            _paragraph(report.prose_summary),
            _render_policy_section(report.render_policy),
            _section("Inventory", _inventory_table(report.inventory_rows)),
            _section("Provenance", _overview_section_body(report.provenance_summary)),
            _section("Recent Activity", _overview_section_body(report.recent_activity)),
            _section(
                "Notable Conflicts", _overview_section_body(report.notable_conflicts)
            ),
        ]
    )
    return _page("propstore", body)


def render_claim_index_page(
    report: ClaimSummaryReport, *, query: str | None, concept: str | None
) -> str:
    rows = [
        LinkRow(
            entry.claim_id,
            f"/claim/{quote(entry.claim_id, safe='')}",
            (
                entry.concept_display,
                entry.claim_type,
                entry.value_display,
                entry.condition_display,
                _state_label(entry.status_state),
            ),
        )
        for entry in report.entries
    ]
    body = "\n".join(
        [
            _h1("Claims"),
            _section(
                "Filters",
                _dl(
                    [
                        ("Query", query or "none"),
                        ("Concept filter", concept or "none"),
                    ]
                ),
            ),
            _section(
                "Claims",
                _link_table(
                    (
                        "Claim",
                        "Concept(s)",
                        "Type",
                        "Value / Summary",
                        "Conditions",
                        "Status",
                    ),
                    rows,
                ),
            ),
        ]
    )
    return _page("Claims", body)


def render_claim_page(report: ClaimViewReport) -> str:
    neighborhood_href = f"/claim/{quote(report.claim_id, safe='')}/neighborhood"
    body = "\n".join(
        [
            _h1(report.heading),
            _section(
                "Summary",
                _dl(
                    [
                        ("Status", _status_text(report.status.state, report.status.reason)),
                        ("Claim type", report.claim_type),
                        ("Name", report.name or "missing"),
                        ("Statement", report.statement or "missing"),
                        ("Concept", report.concept.sentence),
                        ("Value", report.value.sentence),
                        ("Uncertainty", report.uncertainty.sentence),
                        ("Condition regime", report.condition.sentence),
                    ]
                ),
            ),
            _render_policy_section(report.render_policy),
            _section(
                "Provenance",
                _dl(
                    [
                        ("State", _state_label(report.provenance.state)),
                        ("Detail", report.provenance.sentence),
                    ]
                ),
            ),
            _section(
                "Neighborhood",
                _link_paragraph(
                    "Open semantic neighborhood for this claim", neighborhood_href
                ),
            ),
            _machine_ids_section([("Claim ID", report.claim_id)]),
        ]
    )
    return _page(report.heading, body)


def render_concept_page(report: ConceptViewReport) -> str:
    body = "\n".join(
        [
            _h1(report.heading),
            _section(
                "Summary",
                _dl(
                    [
                        ("Status", _status_text(report.status.state, report.status.reason)),
                        ("Canonical name", report.canonical_name or "missing"),
                        ("Definition", report.definition or "missing"),
                        ("Concept status", report.concept_status),
                    ]
                ),
            ),
            _render_policy_section(report.render_policy),
            _section(
                "Form",
                _dl(
                    [
                        ("State", _state_label(report.form.state)),
                        ("Form name", report.form.form_name or "missing"),
                        ("Unit", report.form.unit or "missing"),
                        ("Sentence", report.form.sentence),
                    ]
                ),
            ),
            _section(
                "Value Summary",
                _dl(
                    [
                        ("State", _state_label(report.value_summary.state)),
                        ("Claim count", str(report.value_summary.claim_count)),
                        ("Unit", report.value_summary.unit or "missing"),
                        ("Sentence", report.value_summary.sentence),
                    ]
                ),
            ),
            _section(
                "Uncertainty",
                _dl(
                    [
                        ("State", _state_label(report.uncertainty_summary.state)),
                        ("Claim count", str(report.uncertainty_summary.claim_count)),
                        ("Sentence", report.uncertainty_summary.sentence),
                    ]
                ),
            ),
            _section(
                "Provenance",
                _dl(
                    [
                        ("State", _state_label(report.provenance_summary.state)),
                        ("Claim count", str(report.provenance_summary.claim_count)),
                        ("Sentence", report.provenance_summary.sentence),
                    ]
                ),
            ),
            _section("Claims By Type", _claim_groups(report.claim_groups)),
            _section("Related Claims", _related_claims_table(report.related_claim_links)),
            _machine_ids_section([("Concept ID", report.concept_id)]),
        ]
    )
    return _page(report.heading, body)


def render_concept_index_page(
    report: ConceptListReport | ConceptSearchReport,
    *,
    query: str | None,
    domain: str | None,
    status: str | None,
) -> str:
    entries = (
        report.entries if isinstance(report, ConceptListReport) else report.hits
    )
    rows = [
        LinkRow(
            entry.concept_id,
            f"/concept/{quote(entry.concept_id, safe='')}",
            (
                entry.canonical_name,
                entry.status or "missing",
                entry.definition or "missing",
            ),
        )
        for entry in entries
    ]
    body = "\n".join(
        [
            _h1("Concepts"),
            _section(
                "Filters",
                _dl(
                    [
                        ("Query", query or "none"),
                        ("Domain filter", domain or "none"),
                        ("Status filter", status or "none"),
                    ]
                ),
            ),
            _section(
                "Concepts",
                _link_table(
                    ("Concept", "Canonical Name", "Status", "Definition"), rows
                ),
            ),
        ]
    )
    return _page("Concepts", body)


def render_neighborhood_page(report: SemanticNeighborhoodReport) -> str:
    claim_href = f"/claim/{quote(report.focus.focus_id, safe='')}"
    body = "\n".join(
        [
            _h1(f"Neighborhood for {report.focus.display_id}"),
            _section(
                "Focus",
                "\n".join(
                    [
                        _dl(
                            [
                                ("Focus kind", report.focus.kind),
                                ("Focus ID", report.focus.focus_id),
                                (
                                    "Status",
                                    _status_text(
                                        report.status.state, report.status.reason
                                    ),
                                ),
                                (
                                    "Visible under policy",
                                    _bool_text(report.status.visible_under_policy),
                                ),
                                ("Summary", report.prose_summary),
                            ]
                        ),
                        _link_paragraph(
                            "Open claim view for this focus claim", claim_href
                        ),
                    ]
                ),
            ),
            _section("Available Moves", _moves_table(report.moves)),
            _section("Supporters", _rows_table(_section_rows(report, "supporters"))),
            _section("Attackers", _rows_table(_section_rows(report, "attackers"))),
            _section("Conditions", _rows_table(_section_rows(report, "conditions"))),
            _section("Provenance", _rows_table(_section_rows(report, "provenance"))),
            _section(
                "Shared Concept",
                _rows_table(_section_rows(report, "shared_concept")),
            ),
            _section(
                "Raw Graph Projection",
                "\n".join(
                    [_nodes_table(report.nodes), _edges_table(report.edges)]
                ),
            ),
            _render_policy_section(report.render_policy),
        ]
    )
    return _page(f"Neighborhood for {report.focus.display_id}", body)


def render_error_page(title: str, message: str) -> str:
    body = "\n".join(
        [
            _h1(title),
            _section(
                "What happened",
                "\n".join(
                    [
                        _paragraph(message),
                        _link_paragraph("Return to repository overview", "/"),
                    ]
                ),
            ),
        ]
    )
    return _page(title, body)


# ── section / component helpers ──────────────────────────────────────────────


def _inventory_table(rows: tuple[InventoryRow, ...]) -> str:
    link_rows = [
        LinkRow(
            row.kind,
            row.href,
            (str(row.count), _state_label(row.state), row.sentence),
        )
        for row in rows
        if row.href is not None
    ]
    plain_rows = [
        (row.kind, str(row.count), _state_label(row.state), row.sentence)
        for row in rows
        if row.href is None
    ]
    headers = ("Kind", "Count", "State", "Sentence")
    if not rows:
        return _table(headers, [])
    body_rows = [
        _link_table_row(link_row, len(headers)) for link_row in link_rows
    ] + [_plain_row(row) for row in plain_rows]
    return _table_from_body(headers, body_rows)


def _overview_section_body(section: OverviewSection) -> str:
    return _dl(
        [
            ("State", _state_label(section.state)),
            ("Sentence", section.sentence),
        ]
    )


def _claim_groups(groups: tuple[ConceptClaimGroup, ...]) -> str:
    if not groups:
        return _paragraph("No claim groups are available.")
    fragments: list[str] = []
    for group in groups:
        rows = [
            LinkRow(
                entry.claim_id,
                f"/claim/{quote(entry.claim_id, safe='')}",
                (
                    entry.claim_type,
                    entry.value_display,
                    entry.condition_display,
                    _state_label(entry.status_state),
                    entry.status_reason,
                ),
            )
            for entry in group.entries
        ]
        fragments.append(
            "\n".join(
                [
                    f"<h3>{escape(group.claim_type)}</h3>",
                    _paragraph(group.sentence),
                    _link_table(
                        ("Claim", "Type", "Value", "Conditions", "Status", "Reason"),
                        rows,
                    ),
                ]
            )
        )
    return "\n".join(fragments)


def _related_claims_table(links: tuple[ConceptRelatedClaimLink, ...]) -> str:
    rows = [
        LinkRow(
            link.claim_id,
            f"/claim/{quote(link.claim_id, safe='')}",
            (link.relation, link.sentence),
        )
        for link in links
    ]
    return _link_table(("Claim", "Relation", "Sentence"), rows)


def _moves_table(moves: tuple[SemanticMove, ...]) -> str:
    return _table(
        ("Move", "State", "Count", "Sentence", "Targets"),
        [
            (
                _state_label(move.kind),
                _state_label(move.state),
                str(move.target_count),
                move.sentence,
                ", ".join(move.target_ids) if move.target_ids else "none",
            )
            for move in moves
        ],
    )


def _rows_table(rows: tuple[SemanticNeighborhoodRow, ...]) -> str:
    return _table(
        ("Subject", "Relation", "Object", "State", "Sentence"),
        [
            (
                row.subject_id,
                row.relation,
                row.object_id,
                _state_label(row.state),
                row.sentence,
            )
            for row in rows
        ],
    )


def _edges_table(edges: tuple[SemanticEdge, ...]) -> str:
    return _table(
        ("Source", "Relation", "Target", "Sentence"),
        [
            (edge.source_id, edge.edge_kind, edge.target_id, edge.sentence)
            for edge in edges
        ],
    )


def _nodes_table(nodes: tuple[SemanticNode, ...]) -> str:
    return _table(
        ("Kind", "Node ID", "Display ID", "Sentence"),
        [(node.kind, node.node_id, node.display_id, node.sentence) for node in nodes],
    )


def _section_rows(
    report: SemanticNeighborhoodReport, section: str
) -> tuple[SemanticNeighborhoodRow, ...]:
    return tuple(row for row in report.table_rows if row.section == section)


def _render_policy_rows(summary: RenderPolicySummary) -> list[tuple[str, str]]:
    return [
        ("Reasoning backend", summary.reasoning_backend),
        ("Strategy", summary.strategy),
        ("Semantics", summary.semantics),
        ("Set comparison", summary.set_comparison),
        ("Include drafts", _bool_text(summary.include_drafts)),
        ("Include blocked", _bool_text(summary.include_blocked)),
        ("Show quarantined", _bool_text(summary.show_quarantined)),
    ]


def _render_policy_section(summary: RenderPolicySummary) -> str:
    return _section("Render State", _dl(_render_policy_rows(summary)))


def _machine_ids_section(rows: list[tuple[str, str]]) -> str:
    return _section("Machine IDs", _dl(rows))


# ── primitive HTML builders ──────────────────────────────────────────────────


def _page(heading: str, body: str) -> str:
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="utf-8">\n'
        '    <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"    <title>{escape(heading)} - propstore</title>\n"
        '    <link rel="stylesheet" href="/static/web.css">\n'
        "  </head>\n"
        "  <body>\n"
        '    <main aria-labelledby="page-heading">\n'
        f"{body}\n"
        "    </main>\n"
        "  </body>\n"
        "</html>\n"
    )


def _h1(text: str) -> str:
    return f'<h1 id="page-heading">{escape(text)}</h1>'


def _section(heading: str, body: str) -> str:
    slug = _slug(heading)
    return (
        f'<section aria-labelledby="{slug}">\n'
        f'<h2 id="{slug}">{escape(heading)}</h2>\n'
        f"{body}\n"
        "</section>"
    )


def _dl(rows: list[tuple[str, str]]) -> str:
    cells = "\n".join(
        f"<dt>{escape(label)}</dt><dd>{escape(value or 'missing')}</dd>"
        for label, value in rows
    )
    return f"<dl>\n{cells}\n</dl>"


def _paragraph(text: str) -> str:
    return f"<p>{escape(text)}</p>"


def _link_paragraph(text: str, href: str) -> str:
    return f'<p><a href="{escape(href)}">{escape(text)}</a></p>'


def _table(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> str:
    body_rows = rows or [_empty_row(len(headers))]
    return _table_from_body(headers, [_plain_row(row) for row in body_rows])


def _link_table(headers: tuple[str, ...], rows: list[LinkRow]) -> str:
    if not rows:
        return _table_from_body(headers, [_plain_row(_empty_row(len(headers)))])
    return _table_from_body(
        headers, [_link_table_row(row, len(headers)) for row in rows]
    )


def _table_from_body(headers: tuple[str, ...], rows: list[str]) -> str:
    head = "".join(f"<th scope=\"col\">{escape(header)}</th>" for header in headers)
    body = "\n".join(rows)
    return (
        '<div class="table-wrap">\n'
        "<table>\n"
        f"<thead><tr>{head}</tr></thead>\n"
        f"<tbody>\n{body}\n</tbody>\n"
        "</table>\n"
        "</div>"
    )


def _plain_row(cells: tuple[str, ...]) -> str:
    return "<tr>" + "".join(f"<td>{escape(_cell(cell))}</td>" for cell in cells) + "</tr>"


def _link_table_row(row: LinkRow, header_count: int) -> str:
    if len(row.cells) != header_count - 1:
        raise ValueError(
            f"LinkRow has {len(row.cells) + 1} cells for {header_count} headers"
        )
    first = (
        f'<td><a href="{escape(row.href)}">{escape(_cell(row.link_text))}</a></td>'
    )
    rest = "".join(f"<td>{escape(_cell(cell))}</td>" for cell in row.cells)
    return f"<tr>{first}{rest}</tr>"


def _empty_row(header_count: int) -> tuple[str, ...]:
    return tuple(
        "none" if index == 0 else "not applicable" for index in range(header_count)
    )


def _status_text(state: str, reason: str) -> str:
    return f"{_state_label(state)}: {reason}"


def _state_label(state: str) -> str:
    return state.replace("_", " ")


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _cell(value: str) -> str:
    return value if value != "" else "missing"


def _slug(heading: str) -> str:
    return "".join(
        char if char.isalnum() else "-" for char in heading.lower()
    ).strip("-")
