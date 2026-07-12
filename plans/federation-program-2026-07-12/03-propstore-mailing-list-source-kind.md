# Slice 3 - Mailing-List Message Source Kind

Status: queued behind the active Propstore slice ledger.

## Outcome

Propstore admits `mailing_list_message` as an honest source kind through the existing source lifecycle and CLI validation boundary.

## Owner

Propstore source family vocabulary and source lifecycle.

## Scope

- `propstore/core/source_types.py`
- `tests/test_cli_source_p101.py`
- `docs/cli-reference.md`

## Required behavior

- `pks source init` accepts `--kind mailing_list_message`.
- Source origin and content-file digest behave exactly like existing source initialization.
- Unknown kinds still fail loudly.
- Existing academic-paper behavior is unchanged.

## Forbidden substitutions

- no use of `academic_paper` for email;
- no generic free-form kind string;
- no plugin-local source-kind translation;
- no reply graph, source-link, or extraction semantics in Propstore.

## Gates

- focused source-kind and CLI initialization tests;
- `uv run pyright propstore`;
- project Ruff gate;
- logged relevant pytest gate.

## Completion

One small committed Propstore change. The corpus ingestion slice starts only after this commit is available to `corpus-plugins`.
