# Application Layer And Undo

## Decision

Propstore gets a real application layer at `propstore.application`.

The CLI is a presentation adapter over that layer. Every CLI-visible operation
has a typed request and typed report. Commands that can change repository state,
derived state, or external files also produce an undo plan and a command journal
entry. Read-only commands still use the request/report cycle, but their undo
plan is `NoOpUndo`.

This package owns command execution. Domain packages keep owning domain
semantics. Quire stays the generic Git/document substrate.

## Package Shape

`propstore.application`:

- `commands.py`: command protocol, command ids, execution context, status,
  request/report base classes, command registry.
- `effects.py`: typed effect records for commits, ref changes, sidecar writes,
  worktree syncs, external file writes, and no-op reads.
- `journal.py`: command journal storage and loading.
- `undo.py`: undo plan types and the undo executor.
- `errors.py`: typed command failures for CLI/API mapping.
- `repository.py`: `init`, `log`, `diff`, `show`, `checkout`, `import_repository`,
  `merge inspect`, `merge commit`.
- `compiler.py`: `validate`, `build`, `query`, `export_aliases`.
- `concepts.py`: concept display, mutation, alignment, embedding.
- `claims.py`: claim show, validation, embedding, comparison, relation.
- `forms.py`: form list/show/add/remove/validate.
- `contexts.py`: context add/list.
- `sources.py`: source init/write/add/finalize/promote/status/sync/provenance.
- `worldlines.py`: worldline create/run/refresh/delete/show/list/diff.
- `world.py`: world queries, reasoning, ATMS, revision, analysis commands.
- `proposals.py`: proposal promotion.
- `micropubs.py`: micropublication bundle/show/lift.
- `grounding.py`: grounding inspection.

Package `__init__.py` stays shallow. It should not import command families.

## Command Cycle

Every command runs through the same application-level cycle:

1. CLI/API parses user input into a typed request.
2. Application command captures `CommandEnvelope`.
3. Command validates the request and current repository state.
4. Command records expected branch heads for every mutable branch it will touch.
5. Command executes domain-owner functions.
6. Command receives typed effects from the write path.
7. Command returns a typed report.
8. Command writes a journal entry with the request, report, effects, and undo
   plan.

The CLI may render the report and map typed failures to exit codes. It may not
own mutation semantics, compiler workflows, source workflows, merge semantics,
or undo policy.

## Undo As Recovery Support

Undo is not a single button with one inherent meaning. It is a user recovery
intention that the application supports with several mechanisms: chronological
undo, selective undo, derived-state rebuild, external-file restore, branch
restore, and explicit non-undoability.

Every undoable command must answer four questions:

1. Which activity stream is relevant?
2. What are the units in that stream?
3. Which unit is affected by this undo request?
4. What state change counts as undoing that unit?

For propstore:

- activity streams are global repository history, actor-local command history,
  branch-local history, source-local branch history, and derived-output history;
- units are command effects, not raw CLI invocations;
- affected units are selected by command id, branch, actor, artifact, path, ref,
  or "last";
- undo definitions are carried by explicit `UndoPlan` values.

The default command `pks undo last` means global chronological undo over the
current repository branch context. Actor-local undo is a distinct request:

```text
pks undo --mine
```

`--mine` selects from the actor's own journal stream. It may only execute
without confirmation when later interleaved effects are independent of the
selected command. If they are not independent, the command must preview
conflicts and ask for explicit choices.

## Command Envelope

Each command receives:

```python
@dataclass(frozen=True)
class CommandEnvelope:
    command_id: CommandId
    command_name: str
    request_type: str
    actor: str | None
    started_at: str
    repository_id: str
    branch: str | None
    head_before: Mapping[str, str | None]
    parent_command_id: CommandId | None = None
    dry_run: bool = False
```

`head_before` is not advisory. Any command that writes a branch passes the
captured head through quire's `expected_head` path. A moved branch fails before
writing a new commit.

## Reports And Failures

Requests and reports are command-specific dataclasses. They are not loose
payloads in the core pipeline.

Failures are typed:

- `ValidationFailure`: request is well-formed but invalid against current repo.
- `PreconditionFailure`: expected branch, file, sidecar, or source state is
  missing or stale.
- `ConflictFailure`: undo or mutation conflicts with changed paths.
- `ExternalEffectFailure`: external file operation failed.
- `InternalCommandFailure`: unexpected invariant violation.

The CLI renders failures. The application layer does not call `sys.exit`, import
Click, or write to stdout/stderr.

## Journal Storage

The command journal lives in the knowledge repo, but outside the semantic tree.

Use a dedicated ref:

```text
refs/propstore/command-journal
```

Each journal commit appends immutable JSON documents under deterministic paths:

```text
commands/YYYY/MM/DD/<command-id>.json
```

This keeps command history with the repository while preventing semantic branch
reverts from deleting the audit trail. It also lets commands that do not create
semantic commits, such as `build`, `query`, or failed commands, still be
journaled.

Git notes remain useful for indexing command ids from produced commits:

```text
refs/notes/propstore/commands
```

The note is an index, not the source of truth. The journal ref is the source of
truth.

## Journal Entry

```python
@dataclass(frozen=True)
class CommandJournalEntry:
    command_id: CommandId
    command_name: str
    status: Literal["succeeded", "failed", "dry_run"]
    request_type: str
    request: object
    report_type: str | None
    report: object | None
    effects: tuple[CommandEffect, ...]
    undo_plan: UndoPlan
    head_before: Mapping[str, str | None]
    head_after: Mapping[str, str | None]
    started_at: str
    finished_at: str
    parent_command_id: CommandId | None
```

Failed commands are journaled if the repository exists. They get
`NonUndoableUndo(reason="command did not complete")` unless the command created
partial effects and then returned a compensating undo plan.

`init` is special because the journal ref does not exist until the repo exists.
It writes a bootstrap journal entry after repository creation, marked
non-undoable from inside that repository.

## Undo Plans

Undo is explicit. Every command report carries exactly one undo plan:

- `NoOpUndo`: read-only command or dry run.
- `RevertCommitsUndo`: revert one or more single-parent commits in reverse
  order using quire's `revert_commit`.
- `RestoreTreeUndo`: create a new commit whose tree restores a branch to a
  recorded commit. This covers merge commits and other non-single-parent writes.
- `RebuildDerivedUndo`: rebuild derived sidecar/output state from a recorded
  source commit or remove the derived output if it did not exist before.
- `RestoreExternalFilesUndo`: restore external files from journaled backups, or
  delete files that did not exist before.
- `CompositeUndo`: ordered list of undo plans.
- `NonUndoableUndo`: explicit hard boundary with a reason.

Undo execution is itself a command:

```text
pks undo [last|<command-id>] [--dry-run]
```

Undo writes a new journal entry. It never edits or deletes the original journal
entry. The original entry can be marked undone by an index record on the journal
ref, not by mutation in place.

## Redo Plans

Redo is explicit. It is not "rerun the CLI string." A redo uses the original
typed request plus the command's dependency and expected-head policy.

Every undo journal entry may produce a `RedoPlan`:

- `RedoCommand`: execute the original command request again, with fresh expected
  heads and dependency checks.
- `RedoEffects`: replay recorded effects only when the application can prove
  the original pre-state still holds.
- `RebuildDerivedRedo`: rebuild derived output from the same semantic source
  commit.
- `NonRedoableRedo`: explicit hard boundary with a reason.

Redo must not discard commands from the journal. Redo is a new command entry
that links to the original command and the undo command.

## Undo Correctness Rules

- Undo must use expected-head checks.
- Undo must fail rather than silently overwrite changed paths.
- Undo of a command that produced several commits applies inverse effects in
  reverse order.
- Undo of a merge commit uses `RestoreTreeUndo`, not single-parent revert.
- Undo is append-only by default. It creates corrective commits; it does not
  reset branch refs or erase public history.
- Undo operations are themselves commands and journal entries. They are not
  deletion from history.
- Selective undo must operate over affected semantic objects, paths, refs, and
  derived outputs, not only over chronological command position.
- When a selected command conflicts with later effects the user wants to keep,
  the application must either compute a preview with explicit conflict choices
  or fail with a typed conflict. It must not guess silently.
- Commands are never discarded from the history buffer without a direct user
  request for history surgery.
- Stable result matters more than stable execution. A command need not be
  re-executed in exactly the same runtime state if the corrective command
  produces the same semantic result and preserves relevant derived/report
  results.
- Minimal undo is preferred: undo the selected command and commands dependent
  on it, while leaving independent commands untouched.
- Undo of source state must not mutate canonical state unless the original
  command did.
- Undo of canonical promotion must not delete source-local authoring state.
- Undo of derived state may rebuild or restore cache artifacts; it does not
  change semantic source history.
- External side effects are undoable only when the command captured enough
  before-state to restore them. Otherwise the command must declare
  `NonUndoableUndo`.

## Command Semantics Matrix

### Repository Commands

| Command | Effect | Undo |
| --- | --- | --- |
| `pks init` | Creates repository, seed commits, journal ref | `NonUndoableUndo`; repo did not have a journal before creation |
| `pks log` | Read-only history report | `NoOpUndo` |
| `pks diff` | Read-only diff report | `NoOpUndo` |
| `pks show` | Read-only commit report | `NoOpUndo` |
| `pks checkout` | Rebuilds sidecar from historical commit | `RebuildDerivedUndo` to previous sidecar source commit or delete previous-missing sidecar |
| `pks import-repository` | Writes imported semantic snapshot to target branch; may sync worktree | `RevertCommitsUndo` for ordinary import commits; `RestoreTreeUndo` if import creates non-single-parent history; derived/worktree effects are separate |

### Compiler And Sidecar Commands

| Command | Effect | Undo |
| --- | --- | --- |
| `pks validate` | Read-only validation report | `NoOpUndo` |
| `pks build` | Writes derived sidecar and diagnostics output | `RebuildDerivedUndo`; if output path is external, restore/delete via `RestoreExternalFilesUndo` when before-state was captured |
| `pks query` | Read-only SQL over sidecar | `NoOpUndo` |
| `pks export-aliases` | Read-only export to stdout | `NoOpUndo`; if later given file output, use external-file restore |

### Concept Commands

| Command | Effect | Undo |
| --- | --- | --- |
| `pks concept list/search/categories/show` | Read-only concept reports | `NoOpUndo` |
| `pks concept add` | Adds concept document and updates concept-id counter ref | `CompositeUndo`: revert concept commit and restore counter ref if it moved only because of this command |
| `pks concept alias` | Mutates one concept document | `RevertCommitsUndo` |
| `pks concept rename` | Mutates concept and dependent claim/concept condition references | `RevertCommitsUndo`; conflict if any touched path changed |
| `pks concept deprecate` | Mutates replacement/deprecation metadata | `RevertCommitsUndo` |
| `pks concept link` | Mutates concept relationship metadata | `RevertCommitsUndo` |
| `pks concept qualia-add` | Mutates concept qualia metadata | `RevertCommitsUndo` |
| `pks concept description-kind` | Mutates description-kind metadata | `RevertCommitsUndo` |
| `pks concept proto-role` | Mutates proto-role metadata | `RevertCommitsUndo` |
| `pks concept add-value` | Mutates category value set | `RevertCommitsUndo` |
| `pks concept embed/similar` | Sidecar/vector derived data or read-only similarity | embed: `RebuildDerivedUndo`; similar: `NoOpUndo` |
| `pks concept align` | Writes source alignment/proposal artifact | `RevertCommitsUndo` |
| `pks concept query` | Read-only alignment report | `NoOpUndo` |
| `pks concept decide` | Writes alignment decision artifact | `RevertCommitsUndo` |
| `pks concept promote` | Promotes alignment decision into canonical concept changes | `RevertCommitsUndo` or `CompositeUndo` if multiple commits |

### Claim Commands

| Command | Effect | Undo |
| --- | --- | --- |
| `pks claim show/validate/validate-file/conflicts/compare/similar` | Read-only reports | `NoOpUndo` |
| `pks claim embed` | Writes derived embedding sidecar state | `RebuildDerivedUndo` |
| `pks claim relate` | Writes stance proposal artifacts on proposal branch | `RevertCommitsUndo` |

### Form And Context Commands

| Command | Effect | Undo |
| --- | --- | --- |
| `pks form list/show/validate` | Read-only reports | `NoOpUndo` |
| `pks form add` | Adds form document | `RevertCommitsUndo` |
| `pks form remove` | Deletes form document after reference checks | `RevertCommitsUndo` |
| `pks context list` | Read-only report | `NoOpUndo` |
| `pks context add` | Adds context document | `RevertCommitsUndo` |

### Source Commands

| Command | Effect | Undo |
| --- | --- | --- |
| `pks source init` | Creates source branch and source metadata/content commits | `CompositeUndo`: delete source branch if still at produced tip, delete source metadata refs, remove synced workspace files if created |
| `pks source write-notes` | Writes notes artifact to source branch | `RevertCommitsUndo` |
| `pks source write-metadata` | Writes metadata artifact to source branch | `RevertCommitsUndo` |
| `pks source add-concepts` | Writes source-local concept inventory | `RevertCommitsUndo` |
| `pks source add-claim` | Writes source-local claim artifact | `RevertCommitsUndo` |
| `pks source add-justification` | Writes source-local justification artifact | `RevertCommitsUndo` |
| `pks source add-stance` | Writes source-local stance artifact | `RevertCommitsUndo` |
| `pks source propose-concept` | Writes source proposal artifact | `RevertCommitsUndo` |
| `pks source propose-claim` | Writes source proposal artifact | `RevertCommitsUndo` |
| `pks source propose-justification` | Writes source proposal artifact | `RevertCommitsUndo` |
| `pks source propose-stance` | Writes source proposal artifact | `RevertCommitsUndo` |
| `pks source finalize` | Writes finalize report/status artifacts on source branch | `RevertCommitsUndo` |
| `pks source promote` | Writes canonical artifacts to primary branch and blocked-status mirror rows | `CompositeUndo`: revert canonical commits and rebuild sidecar; source branch remains |
| `pks source status` | Read-only sidecar report | `NoOpUndo` |
| `pks source sync` | Writes external workspace files from source branch | `RestoreExternalFilesUndo` if before-state captured; otherwise `NonUndoableUndo` |
| `pks source stamp-provenance` | Mutates arbitrary external file | `RestoreExternalFilesUndo` only with before-file backup; otherwise non-undoable |

### Proposal, Merge, And Micropub Commands

| Command | Effect | Undo |
| --- | --- | --- |
| `pks promote` | Promotes committed proposal artifacts into primary branch | `RevertCommitsUndo` or `CompositeUndo` |
| `pks merge inspect` | Read-only merge framework report | `NoOpUndo` |
| `pks merge commit` | Creates storage merge commit and merge manifest | `RestoreTreeUndo`; two-parent merge commits are not single-parent reverts |
| `pks micropub bundle` | Writes micropublication bundle/materialized artifacts | `RevertCommitsUndo` |
| `pks micropub show` | Read-only report | `NoOpUndo` |
| `pks micropub lift` | Writes lifted micropub/context artifact | `RevertCommitsUndo` |

### Worldline Commands

| Command | Effect | Undo |
| --- | --- | --- |
| `pks worldline list/show/diff` | Read-only reports | `NoOpUndo` |
| `pks worldline create` | Writes worldline definition | `RevertCommitsUndo` |
| `pks worldline run` | Creates or updates materialized worldline results | `RevertCommitsUndo` |
| `pks worldline refresh` | Updates materialized worldline results | `RevertCommitsUndo` |
| `pks worldline delete` | Deletes worldline artifact | `RevertCommitsUndo` |

### World, Grounding, And Verify Commands

| Command | Effect | Undo |
| --- | --- | --- |
| `pks world status/query/bind/explain/algorithms` | Read-only world reports | `NoOpUndo` |
| `pks world hypothetical/chain/export-graph/sensitivity/fragility/check-consistency` | Read-only analyses unless file output is added | `NoOpUndo`; file output uses external-file restore |
| `pks world derive/resolve/extensions` | Read-only reasoning reports | `NoOpUndo` |
| `pks world revision base/entrenchment/expand/contract/revise/explain/iterated-state/iterated-revise` | Read-only revision reports unless a future command persists state | `NoOpUndo` |
| `pks world atms status/context/verify/futures/why-out/stability/relevance/interventions/next-query` | Read-only ATMS reports | `NoOpUndo` |
| `pks grounding status/show/query/arguments` | Read-only grounding reports | `NoOpUndo` |
| `pks verify tree` | Read-only evidence verification | `NoOpUndo` |

## Merge Undo Semantics

Undoing a merge means undoing the effect of the merge on the target branch.
It does not delete either input branch and it does not pretend the merge never
happened.

For `pks merge commit`, the target branch has a two-parent merge commit:

```text
parent 1: target branch before merge
parent 2: merged-in branch
```

The default undo is append-only:

1. Read the merge command journal entry.
2. Identify the target branch and the pre-merge target tree, usually parent 1.
3. Require the target branch head to be the expected merge commit, or fail with
   a stale-head conflict.
4. Create a new single-parent corrective commit on the target branch whose tree
   equals the pre-merge target tree.
5. Journal the undo command.

This is `RestoreTreeUndo`. It is deliberately not quire's single-parent
`revert_commit`, because a storage merge commit has two parents and the
application must choose the mainline. For propstore, the mainline is the target
branch being merged into.

Pushed vs unpushed matters:

- Pushed or shared history: always use append-only undo. Do not rewrite refs.
- Unpushed local history: branch rewind could be a separate history-surgery
  command, but it is not normal undo. It would need an explicit request, an
  exact expected-head check, and a journal entry saying the ref was rewritten.

The application-level `undo` command should not guess whether a branch has been
pushed. It should use append-only undo unless the user invokes an explicit
future rewrite command. That keeps local and shared repositories on the same
semantic model.

A reverted merge has one subtle consequence: raw Git may consider the input
branch already merged even though the target tree has been restored. Future
propstore merge commands must use propstore's semantic merge framework and
explicit command journal state, not raw Git's "already merged" shortcut, when
deciding whether a merge should run again.

## Selective Undo Model

Azurite's selective undo design is the closest prior-art shape for what
propstore needs, but propstore has better objects than a text editor. Instead of
tracking character ranges and dynamic offsets, propstore tracks semantic objects
and storage effects:

- artifact refs: concepts, claims, forms, contexts, sources, stances,
  justifications, worldlines, merge manifests;
- paths and object ids in quire/Git;
- branch refs and expected heads;
- sidecar outputs and external-file outputs;
- command ids and parent command ids.

The important lesson is not to treat undo as only "go back one step." A user may
want to undo an old command while preserving later work. That makes undo a
selective operation over effects.

### Operation Units

The primitive undoable units are command effects, not CLI invocations and not
raw file edits:

- `CommitEffect`: branch, commit sha, parent shas, touched paths, before/after
  tree ids when needed.
- `RefEffect`: ref name, old value, new value.
- `ArtifactEffect`: family, ref, path, old artifact id, new artifact id.
- `SidecarEffect`: sidecar path, old source commit, new source commit.
- `ExternalFileEffect`: file path, old bytes hash or missing marker, new bytes
  hash or missing marker.

A high-level command may emit several primitive effects. Undo planning happens
over those effects.

### Atomic And Composite Commands

Commands are indivisible from the user's perspective, but not from the
application's perspective.

- `AtomicCommand`: one domain effect that cannot be split in user-facing undo.
- `CompositeCommand`: a user command that contains several atomic effects.

The journal stores both levels. A composite command has one command id and one
report, but its undo plan can address the contained effects. Default undo of a
composite command is whole-command undo. Selective undo may preview partial
effect undo only when the command declares that partial undo is meaningful.

Examples:

- `form add` is atomic.
- `concept rename` is composite because it mutates the concept and dependent
  references.
- `source promote` is composite because it can write canonical artifacts,
  blocked-status mirror rows, and derived sidecar state.
- `merge commit` is composite because it writes a merge commit and manifest.

### Dependency Types

Undo planning tracks two dependency classes:

- `ImplicitDependency`: computed from effects. If command B changes an artifact,
  path, ref, or output produced by command A, B depends on A. Dependencies are
  transitive.
- `ExplicitDependency`: declared by the command. If command B uses command A's
  result without touching the same object, B still depends on A.

Examples of explicit dependencies:

- `source promote` depends on `source finalize`.
- `build` depends on the semantic source commit it compiled.
- `worldline run` depends on the worldline definition and the sidecar/source
  commit used to compute results.
- `claim relate` depends on embedding state and the claim snapshot it read.

Minimal undo of command A must include commands that depend on A unless the user
chooses to keep their results and the application can prove that keeping them is
consistent.

### Conflict Classes

Selective undo is conflict-free when every affected object still has the value
produced by the command being undone. It conflicts when a later command changed
the same object, path, ref, sidecar output, or external file.

Propstore should classify conflicts by object type:

- `PathConflict`: a path touched by the command no longer matches the command's
  after-state.
- `ArtifactConflict`: the family/ref identity exists but its current artifact id
  differs from the command's after-state.
- `RefConflict`: a branch/ref moved away from the expected head.
- `DerivedOutputConflict`: sidecar or external output changed since the command.
- `CompositeConflict`: several primitive conflicts in one command.

Conflict-free selective undo can execute directly. Conflicting selective undo
must produce a preview with alternatives or fail.

### Independence And Commutativity

Selective and actor-local undo depend on independence. A later command is
independent of the selected command when reordering the two effects would leave
the same semantic result and the same relevant display/report result.

Propstore uses a conservative approximation:

- Effects on disjoint artifact refs are independent.
- Effects on disjoint Git paths are independent unless a family-level invariant
  says otherwise.
- Effects on the same branch ref are not independent unless their artifact/path
  effects are independent and the branch can be restored with expected-head
  checks.
- Effects on the same artifact ref are not independent by default.
- Derived sidecar effects are independent of semantic commits only when they can
  be rebuilt from the chosen semantic source commit.
- External-file effects are not independent unless they touch disjoint files.
- Commands with explicit dependencies are not independent even when their
  direct path/artifact effects are disjoint.

If independence is known, local/selective undo can be implemented by replaying a
corrected effect order as an append-only corrective command. If independence is
unknown, the application must not pretend it is safe. It should produce a
preview with alternatives or raise `ConflictFailure`.

### History Buffers And Virtual Stack Tops

Propstore has several history buffers:

- global repository journal;
- branch-local journal view;
- source branch journal view;
- actor-local journal view;
- derived-output journal view.

Linear undo uses a virtual stack top over the selected buffer. The virtual stack
top is the youngest executed command in that buffer that is not already undone
by a later undo command. Linear redo uses the oldest contiguous undone command
after that virtual stack top.

Selective undo does not move a stack pointer. It selects a command from a
buffer, computes dependencies and conflicts, and appends a corrective command.

### Preview And Keep Rules

Undo should have a preview mode:

```text
pks undo <command-id> --preview
```

Preview returns:

- selected command and effects;
- affected artifacts, paths, refs, and outputs;
- conflict-free inverse effects;
- conflicts with later commands;
- available alternatives.

For conflicting selective undo, the user-facing model should be:

- "undo this command";
- "also undo these conflicting later commands";
- "keep this artifact/path/ref as it is";
- "cancel".

That mirrors Azurite's "keep this code unchanged" idea, but at propstore's
semantic-object level. Keeping an artifact unchanged means the inverse plan must
exclude that artifact's effect and report that the command was only partially
undone.

### Selective Undo Policy

The default `pks undo last` is simple chronological undo. It selects the newest
undoable command on the current branch and executes its plan.

`pks undo <command-id>` is selective undo. It may be older than the latest
command. It must:

1. Load the target command's effects.
2. Find later journal entries that touched the same objects.
3. Classify conflicts.
4. If conflict-free, execute the inverse plan.
5. If conflicting, require `--preview` or explicit conflict choices.

This implies the journal needs an object-effect index. The source of truth is
still the journal ref; the index can be rebuilt from entries.

### Research Note

This design is informed by YoungSeok Yoon and Brad A. Myers, "Supporting
Selective Undo in a Code Editor" (ICSE 2015):
https://www.cs.cmu.edu/~NatProg/papers/ICSE15-Azurite-v12-CameraReady.pdf

The relevant transferable ideas are: undo entries remain part of history;
selective undo needs affected-object tracking; conflicts must be detected rather
than guessed through; preview and "keep this unchanged" controls make conflict
resolution usable. Propstore should implement those ideas over semantic effects
instead of text ranges.

This design is also informed by Gregory D. Abowd and Alan J. Dix, "Giving undo
attention" (1992):
https://alandix.com/academic/papers/undo92/undo.pdf

The relevant transferable ideas are: undo should be treated as support for a
user recovery intention, not merely as a system function; designers must name
the relevant activity stream, units, affected unit, and definition of undo; and
local undo in interleaved/shared histories is only sensible when independence or
commutativity conditions hold. Propstore implements those ideas through command
effects, actor/branch/source streams, explicit undo plans, and conservative
independence checks.

This design is also informed by Karel Jakubec, Marek Polak, Martin Necasky, and
Irena Holubova, "Undo/Redo Operations in Complex Environments" (Procedia
Computer Science 32, 2014). The local copy read for this note was
`C:\Users\Q\Downloads\UndoRedo_Operations_in_Complex_Environments.pdf`.

The relevant transferable ideas are: commands can be atomic internally while
remaining indivisible to the user; histories may be split across multiple
workspaces/buffers; dependencies are both implicit and explicit; selective undo
should preserve independent commands; redo must be modeled explicitly; and a
good undo manager should prefer minimal undo of dependent commands over
discarding unrelated history.

## Implementation Slices

1. Create `propstore.application.commands`, `effects`, `journal`, and `undo`
   types.
2. Add journal storage on `refs/propstore/command-journal`.
3. Add atomic/composite command effect recording.
4. Add implicit and explicit dependency recording.
5. Add the object-effect index derived from journal entries.
6. Add conservative independence/commutativity checks for selective and
   actor-local undo.
7. Add `pks undo` backed by journal lookup, preview, conflict classification,
   and undo-plan execution.
8. Add redo plans and `pks redo` after undo is journaled.
9. Move one small mutation command end to end, starting with `form add` or
   `context add`.
10. Move concept mutations next because they exercise multi-file commits,
   validation, concept-id counter handling, and worktree sync.
11. Move source lifecycle after concept mutation because source commands need
   composite undo and branch deletion semantics.
12. Move merge commit once `RestoreTreeUndo` exists.

The implementation should delete CLI-owned production paths as each command
family moves. Do not add compatibility wrappers that preserve the old owner.
