# Slice 4 - One Real Mailing-List Message Into Propstore

Status: queued; depends on Slice 3.

## Outcome

One substantive root message from the real BlindHandyman Thunderbird archive reaches Propstore's existing validation boundary as a source branch with a minimal concept set and one provenance-bearing observation claim.

## Owner

`../corpus-plugins/plugins/mailing-lists`; Propstore owns validation after handoff.

## Source unit

One email message identified by `Message-ID`. The thread is reply-graph context, not the source unit. Exact `.eml` bytes provide the content digest.

## Scope

- `plugins/mailing-lists/skills/thread-reader/SKILL.md`
- `plugins/mailing-lists/skills/source-bootstrap/SKILL.md`
- `plugins/mailing-lists/skills/extract-claims/SKILL.md`
- focused plugin tests using synthetic messages
- one disposable live run against `Archives-1`

## Required behavior

- Split the archive with the existing `thread-split` workflow.
- Select and read one substantive root message with its `thread.json` record.
- Preserve Message-ID, author, date, subject, thread ID, sequence, parent ID, and exact source path.
- Call `pks source init --kind mailing_list_message` with the `.eml` content file.
- Propose the minimum concepts and one observation claim directly through `pks source propose-*`.
- Raw mbox and generated `.eml` files remain untracked.

## Forbidden substitutions

- no intermediate YAML batches;
- no thread-as-source substitution;
- no shared `spine` helper until a second plugin proves reuse;
- no finalize/promote, full-thread orchestration, source-link entity, or archive-scale ingestion in this slice.

## Gates

- Existing thread-split tests pass.
- Real archive split reports nonzero messages/threads and explicit fallback/skipped counts.
- Selected root `.eml` agrees with `thread.json` and has no parent.
- Source initialization plus one real concept and claim proposal exit successfully in a disposable repository.
- Branch inspection proves digest and proposal artifacts.
- Git proves raw corpus data is untracked.

## Completion

One committed corpus-plugins vertical slice proving real non-paper knowledge reaches Propstore without bypassing its validation boundary.
