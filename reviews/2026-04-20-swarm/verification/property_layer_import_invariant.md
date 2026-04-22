# Property verification: layer import invariant

Workstream item: T12.5.

Property:
- The layer contracts must reject known architectural backflow between storage, merge, source, heuristic, concept, argumentation, worldline, and support revision surfaces.

Verification:
- `uv run lint-imports`
- Result: analyzed 359 files and 2440 dependencies; 4 contracts kept, 0 broken.

Contracts:
- `storage -> merge`
- `source -> heuristic`
- `concept -> argumentation`
- `worldline -> support_revision`

Result: verified.
