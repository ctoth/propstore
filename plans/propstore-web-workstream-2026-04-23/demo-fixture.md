# First Web Demo Fixture

Fixture owner: `tests/web_demo_fixture.py`

Verification test: `tests/test_web_demo_fixture.py`

## Focus Object

The first demo object is claim `demo_focus` in a temporary repository seeded by
`seed_web_demo_repository`.

The fixture creates a real propstore repository and a focused SQLite sidecar
with:

- concept `demo_concept`;
- focus claim `demo_focus`;
- supporter claim `demo_supporter`;
- attacker claim `demo_attacker`;
- source/provenance row `demo_source`;
- one `supports` relation from `demo_supporter` to `demo_focus`;
- one `rebuts` relation from `demo_attacker` to `demo_focus`;
- a build diagnostic and `build_status='blocked'` on the focus claim.

## States Exercised

- Uncertainty: `demo_focus` has numeric uncertainty `0.25`,
  `uncertainty_type='stddev'`, and `sample_size=8`.
- Provenance: `demo_focus` points at `demo_source`, page `7`.
- Supporters: `demo_supporter` supports `demo_focus`.
- Attackers: `demo_attacker` rebuts `demo_focus`.
- Policy state: `demo_focus` is blocked under the default render policy and
  becomes visible only when the render policy includes blocked rows.

## Scope Control

This is not a broad demo corpus. It is a typed repository fixture for the
first server-rendered claim and neighborhood web surface.

No external paper text extraction was used.
