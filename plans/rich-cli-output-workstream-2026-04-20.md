# Rich CLI Output Workstream

Date: 2026-04-20

## Goal

Make the CLI output layer consistent, readable, and reusable without moving
terminal presentation into `propstore.app`.

The app package owns typed workflows and reports. The CLI owns Click command
declarations, option parsing, request construction, terminal rendering, and
exit-code mapping.

## Constraints

- Do not import Rich from `propstore.app`.
- Preserve machine-readable YAML and JSON command output.
- Preserve high-value output substrings currently asserted by tests.
- Disable terminal markup/color under normal `CliRunner` capture.
- Keep changes in committed, reviewable slices because other agents may be
  editing this repository concurrently.
- Leave unrelated dirty or untracked files alone.

## Target Shape

Add a CLI-local presentation toolkit:

```text
propstore/cli/output/
  __init__.py
  console.py
  errors.py
  sections.py
  tables.py
  yaml.py
```

The toolkit provides:

- shared Rich console access
- status, warning, and error emitters
- stable YAML emission through `quire.documents.render_yaml_value`
- key/value section rendering
- lightweight table rendering

## Execution Slices

1. Foundation
   - Declare Rich as a direct dependency.
   - Add `propstore.cli.output`.
   - Convert low-risk YAML/status commands.
   - Verify with pyright and a focused CLI smoke batch.

2. Source and Proposal Commands
   - Convert source lifecycle, batch, authoring, proposal, and promote output.
   - Keep existing message text stable.
   - Verify source and proposal tests.

3. Worldline Commands
   - Convert worldline create/run/show/list/diff/delete output.
   - Use shared section/table helpers where useful.
   - Preserve existing materialized worldline substrings.
   - Verify worldline tests.

4. World Query, Reasoning, and Revision
   - Convert status/query/bind/explain/algorithms, derive/resolve/extensions,
     and revision output.
   - Use shared tables for rankings, algorithm rows, accepted/defeated claims,
     and revision summaries.
   - Verify world and revision tests.

5. ATMS
   - Convert ATMS status/context/verify/futures/why-out/stability/relevance/
     interventions/next-query output.
   - Preserve asserted technical substrings while removing ad hoc spacing.
   - Verify ATMS tests.

6. Claim, Concept, Form, Context, Grounding, History
   - Convert the remaining command families to shared output helpers.
   - Keep JSON/YAML surfaces stable.
   - Verify the broader CLI regression batch.

## Completion Criteria

- `uv run pyright propstore` passes.
- Focused logged pytest batches pass for each converted slice.
- No Rich imports exist under `propstore.app`.
- Remaining `click.echo` usage is limited to places where Click behavior is
  specifically needed, or removed entirely from command modules.
- Work is committed in coherent slices.
