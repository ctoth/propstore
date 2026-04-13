# Test Guidance

This suite optimizes for semantic protection, not raw test count.

## Marker Intent

- `unit`: local behavior with minimal setup.
- `property`: invariants, metamorphic checks, or generated-state coverage.
- `differential`: compare a public surface against an oracle, alternate backend, or trusted helper.
- `e2e`: minimally mocked workflow coverage across real product surfaces.
- `migration`: temporary compatibility or cutover coverage. Use only when an external constraint forces a transition path.
- `slow`: materially slower than the default suite budget.

## Test Selection Rules

- Prefer `property` or `differential` tests when the surface admits order invariance, roundtrips, idempotence, history independence, or backend equivalence.
- Prefer API or semantic contract assertions over internal call-routing assertions.
- Use CLI tests when the command output, repo mutation, or command composition is itself part of the product surface.
- Use `e2e` tests for one real path per major workflow, not for every edge case.

## Mocking Rules

- Do not monkeypatch core semantic pipelines when a real repo-backed path is feasible.
- Mock only external services, nondeterministic integrations, or dependencies whose real setup would dominate the test cost.
- A command-survival test is not enough if the underlying workflow can be exercised for real.

## Internal Routing Checks

If a test must assert internal call routing, the test docstring or an adjacent comment must say why the observable contract is insufficient. Without that justification, prefer a public-result contract instead.

## Migration Tests

- Mark migration-only coverage with `@pytest.mark.migration`.
- Keep migration tests isolated from durable product contracts.
- Review the current migration inventory with:

```powershell
uv run scripts/list_migration_tests.py
```
