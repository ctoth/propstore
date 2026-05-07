from __future__ import annotations

from propstore.support_revision.entrenchment import compute_entrenchment
from tests.test_revision_operators import _base_with_shared_support


def test_support_overrides_are_reasons_not_formal_ordering() -> None:
    base, _, ids = _base_with_shared_support()

    report = compute_entrenchment(
        None,
        base,
        overrides={f"source:{ids['legacy']}": {"priority": 0}},
    )
    baseline = compute_entrenchment(None, base)

    assert report.ranked_atom_ids == baseline.ranked_atom_ids
    assert report.reasons[ids["legacy"]].support_count is not None
