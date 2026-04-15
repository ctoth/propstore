# CLI Reference

`pks` is the propstore command-line interface -- a scientific claim compiler and reasoning engine. All commands should be run via `uv run pks`.

```bash
uv run pks <command> [options]
```

## Global Options

| Option | Type | Description |
|--------|------|-------------|
| `-C`, `--directory` | PATH | Run as if pks was started in this directory |

---

## Project Management

### `pks init [DIRECTORY]`

Initialize a new propstore project directory. Creates the standard directory structure (`concepts/`, `claims/`, `contexts/`, `forms/`, `justifications/`, `sidecar/`, `sources/`, `stances/`, `worldlines/`). If no DIRECTORY argument is given, it creates `knowledge/` in the current working directory.

```bash
uv run pks init
uv run pks init my-project
```

### `pks build`

Validate everything, build sidecar, run conflict detection.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-o`, `--output` | TEXT | -- | Output path |
| `--force` | FLAG | false | Force rebuild |

```bash
uv run pks build
uv run pks build --force -o out/sidecar.sqlite
```

### `pks validate`

Validate all concepts and claims. Runs CEL type-checking. No options.

```bash
uv run pks validate
```

### `pks query SQL`

Run raw SQL against the sidecar SQLite.

```bash
uv run pks query "SELECT * FROM claims WHERE concept_id LIKE 'speech%'"
```

### `pks checkout COMMIT`

Build sidecar from a historical commit (non-destructive).

```bash
uv run pks checkout abc1234
```

### `pks merge inspect BRANCH_A BRANCH_B`

Inspect the formal merge framework between two branches. Prints a YAML `formal_merge_report` with `framework_type: partial_argumentation_framework`, the merged argument universe, uncertain relations, and acceptance summary for the requested semantics.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--semantics` | `grounded\|preferred\|stable` | grounded | Completion semantics used for the summary |

```bash
uv run pks merge inspect agent/paper-a agent/paper-b
uv run pks merge inspect agent/paper-a agent/paper-b --semantics preferred
```

### `pks merge commit BRANCH_A BRANCH_B`

Create a two-parent storage merge commit from the formal merge framework between two branches. Prints YAML `storage_merge_commit` metadata with the branch pair, target branch, `claims/merged.yaml`, `merge/manifest.yaml`, and the resulting commit SHA.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--message` | TEXT | -- | Override the default merge commit message |
| `--target-branch` | TEXT | master | Branch ref that receives the merge commit |

```bash
uv run pks merge commit agent/paper-a agent/paper-b
uv run pks merge commit agent/paper-a agent/paper-b --target-branch synthesis --message "Merge paper branches"
```

### `pks import-repo SOURCE_REPO`

Import the committed semantic snapshot of another propstore repo onto a destination branch. Prints YAML `repo_import_commit` metadata with the source repo path, source commit, target branch, commit SHA, touched semantic paths, and whether the destination worktree was synced.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--target-branch` | TEXT | `import/<repo-name>` | Branch ref that receives the import commit |
| `--message` | TEXT | -- | Override the default import commit message |

```bash
uv run pks -C repo-a import-repo ../repo-b
uv run pks -C repo-a import-repo ../repo-b --target-branch master
```

### `pks log`

Show branch-scoped knowledge repository history with operation labels.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-n`, `--count` | INTEGER | 20 | Number of entries to show |
| `--branch` | TEXT | `master` | Branch history to inspect |
| `--show-files` | FLAG | `false` | Include per-commit added/modified/deleted paths |
| `--format` | `text\|yaml` | `text` | Render as text or structured YAML |

```bash
uv run pks log
uv run pks log --branch agent/paper-a
uv run pks log --show-files
uv run pks log --format yaml
uv run pks log -n 50
```

### `pks show COMMIT`

Show details of a specific commit.

```bash
uv run pks show abc1234
```

### `pks diff [COMMIT]`

Show files changed between HEAD and COMMIT (or HEAD vs parent).

```bash
uv run pks diff
uv run pks diff abc1234
```

### `pks promote [PATH]`

Promote committed stance proposals from the `proposal/stances` branch into source-of-truth storage on `master`. If PATH is given, promotes only that stance file or claim-id-derived filename; otherwise promotes all committed stance proposal files on the proposal branch.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-y`, `--yes` | FLAG | false | Skip confirmation prompt |

```bash
uv run pks promote
uv run pks promote some-stance.yaml -y
```

### `pks source`

Manage source branches and source-local artifacts. The source workflow replaces
the old paper-import bridge.

Key subcommands:

- `pks source init <name> --kind <kind> --origin-type <type> --origin-value <value> [--content-file FILE]`
- `pks source write-notes <name> --file notes.md`
- `pks source write-metadata <name> --file metadata.json`
- `pks source propose-concept <name> --name <concept> --definition <text> --form <form>`
- `pks source add-concepts <name> --batch concepts.yaml`
- `pks source add-claim <name> --batch claims.yaml`
- `pks source add-justification <name> --batch justifications.yaml`
- `pks source add-stance <name> --batch stances.yaml`
- `pks source finalize <name>`
- `pks source promote <name>`
- `pks source sync <name> [--output-dir DIR]`

```bash
uv run pks source init Demo_2026 --kind academic_paper --origin-type file --origin-value Demo_2026.pdf
uv run pks source write-notes Demo_2026 --file ../research/papers/Demo_2026/notes.md
uv run pks source write-metadata Demo_2026 --file ../research/papers/Demo_2026/metadata.json
uv run pks source propose-concept Demo_2026 --name pitch --definition "Fundamental frequency of voiced speech" --form frequency
uv run pks source add-claim Demo_2026 --batch ../research/papers/Demo_2026/claims.yaml
uv run pks source finalize Demo_2026
uv run pks source promote Demo_2026
uv run pks source sync Demo_2026
```

### `pks export-aliases`

Export the alias lookup table.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | `text\|json` | -- | Output format |

```bash
uv run pks export-aliases --format json
```

---

## Concepts (`pks concept`)

### `pks concept add`

Add a new concept to the registry.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--domain` | TEXT | -- | Domain prefix (e.g. speech, a11y, finance) (required) |
| `--name` | TEXT | -- | Canonical name (lowercase, underscored) (required) |
| `--definition` | TEXT | -- | Definition (prompted if omitted) |
| `--form` | TEXT | -- | Form name (references `forms/<name>.yaml`, prompted if omitted) |
| `--values` | TEXT | -- | Comma-separated values (required for category concepts) |
| `--dry-run` | FLAG | false | [Dry-run](#dry-run) |

```bash
uv run pks concept add --domain speech --name pitch --form frequency --definition "Fundamental frequency of voiced speech"
```

### `pks concept add-value CONCEPT_NAME`

Add a value to a category concept's value set.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--value` | TEXT | -- | Value to add (required) |
| `--dry-run` | FLAG | false | [Dry-run](#dry-run) |

```bash
uv run pks concept add-value speech.vowel_quality --value "mid-central"
```

### `pks concept alias CONCEPT_ID`

Add an alias to a concept.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name` | TEXT | -- | Alias name (required) |
| `--source` | TEXT | -- | Source paper or 'common' (required) |
| `--note` | TEXT | -- | Optional note |
| `--dry-run` | FLAG | false | [Dry-run](#dry-run) |

```bash
uv run pks concept alias speech.pitch --name "F0" --source "common"
```

### `pks concept categories`

List all category concepts and their allowed values.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--json` | FLAG | false | Output as JSON |

```bash
uv run pks concept categories
```

### `pks concept deprecate CONCEPT_ID`

Deprecate a concept with a replacement.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--replaced-by` | TEXT | -- | Replacement concept ID (required) |
| `--dry-run` | FLAG | false | [Dry-run](#dry-run) |

```bash
uv run pks concept deprecate speech.old_name --replaced-by speech.new_name
```

### `pks concept embed [CONCEPT_ID]`

Generate embeddings for concepts via litellm. See [Embedding options](#embedding-options).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | FLAG | false | Embed all concepts |
| `--model` | TEXT | -- | litellm model string, or 'all' (required) |
| `--batch-size` | INTEGER | -- | Concepts per API call |

```bash
uv run pks concept embed --all --model text-embedding-3-small
uv run pks concept embed speech.pitch --model all
```

### `pks concept link SOURCE_ID RELATION TARGET_ID`

Add a relationship between concepts.

| Argument | Required | Description |
|----------|----------|-------------|
| `SOURCE_ID` | yes | Source concept |
| `RELATION` | yes | One of: `broader`, `narrower`, `related`, `component_of`, `derived_from`, `contested_definition` |
| `TARGET_ID` | yes | Target concept |

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--source` | TEXT | -- | Source paper |
| `--note` | TEXT | -- | Note |
| `--conditions` | TEXT | -- | Comma-separated CEL expressions |
| `--dry-run` | FLAG | false | [Dry-run](#dry-run) |

```bash
uv run pks concept link speech.pitch derived_from speech.glottal_pulse_rate --source "Titze_1994"
```

### `pks concept list`

List concepts, optionally filtered.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--domain` | TEXT | -- | Filter by domain |
| `--status` | TEXT | -- | Filter by status |

```bash
uv run pks concept list --domain speech
```

### `pks concept rename CONCEPT_ID`

Rename a concept (updates canonical_name and filename).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name` | TEXT | -- | New canonical name (required) |
| `--dry-run` | FLAG | false | [Dry-run](#dry-run) |

```bash
uv run pks concept rename speech.old_name --name new_name
```

### `pks concept search QUERY`

Search concepts by name, definition, or alias.

```bash
uv run pks concept search "frequency"
```

### `pks concept show CONCEPT_ID_OR_NAME`

Show full concept YAML.

```bash
uv run pks concept show speech.pitch
```

### `pks concept similar CONCEPT_ID`

Find similar concepts by embedding distance. See [Embedding options](#embedding-options).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--model` | TEXT | -- | litellm model string (default: first available) |
| `--top-k` | INTEGER | -- | Number of results |
| `--agree` | FLAG | false | Similar under ALL stored models |
| `--disagree` | FLAG | false | Similar under some models but not others |

```bash
uv run pks concept similar speech.pitch --top-k 5
```

---

## Claims (`pks claim`)

### `pks claim compare ID_A ID_B`

Compare two algorithm claims for equivalence.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-b`, `--bindings` | TEXT | -- | Known values as key=value pairs |

```bash
uv run pks claim compare algo_claim_1 algo_claim_2
```

### `pks claim conflicts`

Detect and report claim conflicts.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--concept` | TEXT | -- | Filter by concept ID |
| `--class` | `CONFLICT\|OVERLAP\|PARAM_CONFLICT` | -- | Filter by warning class |

```bash
uv run pks claim conflicts
uv run pks claim conflicts --concept speech.pitch --class CONFLICT
```

### `pks claim embed [CLAIM_ID]`

Generate embeddings for claims via litellm. See [Embedding options](#embedding-options).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | FLAG | false | Embed all claims |
| `--model` | TEXT | -- | litellm model string, or 'all' (required) |
| `--batch-size` | INTEGER | -- | Claims per API call |

```bash
uv run pks claim embed --all --model text-embedding-3-small
```

### `pks claim relate [CLAIM_ID]`

Classify epistemic relationships between similar claims via LLM. The resulting stance proposal snapshots are committed to the `proposal/stances` branch rather than written into source-of-truth state.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | FLAG | false | Relate all claims |
| `--model` | TEXT | -- | LLM model for classification (required) |
| `--embedding-model` | TEXT | -- | Embedding model for similarity |
| `--top-k` | INTEGER | -- | Number of similar claims to classify |
| `--concurrency` | INTEGER | -- | Max concurrent LLM calls |
| `--second-pass-threshold` | FLOAT | -- | Distance threshold for second-pass NLI |

```bash
uv run pks claim relate --all --model gpt-4o --embedding-model text-embedding-3-small
```

### `pks claim show CLAIM_ID`

Display details of a single claim.

```bash
uv run pks claim show speech.pitch.claim_01
```

### `pks claim similar CLAIM_ID`

Find similar claims by embedding distance. See [Embedding options](#embedding-options).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--model` | TEXT | -- | litellm model string (default: first available) |
| `--top-k` | INTEGER | -- | Number of results |
| `--agree` | FLAG | false | Similar under ALL stored models |
| `--disagree` | FLAG | false | Similar under some models but not others |

```bash
uv run pks claim similar speech.pitch.claim_01 --top-k 10
```

### `pks claim validate`

Validate all claim files.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dir` | TEXT | -- | Claims directory |
| `--concepts-dir` | TEXT | -- | Concepts directory |

```bash
uv run pks claim validate
```

### `pks claim validate-file FILEPATH`

Validate a single claims YAML file.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--concepts-dir` | TEXT | -- | Concepts directory |

```bash
uv run pks claim validate-file knowledge/claims/speech/pitch.yaml
```

---

## Forms (`pks form`)

### `pks form add`

Add a new form definition.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name` | TEXT | -- | Form name (lowercase, underscored) (required) |
| `--unit` | TEXT | -- | Primary unit symbol (e.g. Hz, Pa) |
| `--qudt` | TEXT | -- | QUDT IRI (e.g. qudt:HZ) |
| `--base` | TEXT | -- | Base type (e.g. ratio) |
| `--dimensions` | TEXT | -- | JSON dict of SI dimension exponents, e.g. `'{"T": -1}'` |
| `--dimensionless` | TEXT | -- | Whether the form is dimensionless (true/false) |
| `--common-alternatives` | TEXT | -- | JSON array of alternative unit conversions |
| `--note` | TEXT | -- | Human-readable note about this form |
| `--dry-run` | FLAG | false | [Dry-run](#dry-run) |

```bash
uv run pks form add --name frequency --unit Hz --qudt qudt:HZ --dimensions '{"T": -1}'
```

### `pks form list`

List all available forms.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dims` | TEXT | -- | Filter by dimensions (e.g. `M:1,L:1,T:-2`). Implies showing dims column. |
| `--show-dims` | FLAG | false | Show dimensions column |

```bash
uv run pks form list
uv run pks form list --dims "T:-1"
```

### `pks form remove NAME`

Remove a form definition.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force` | FLAG | false | Remove even if concepts reference this form |
| `--dry-run` | FLAG | false | [Dry-run](#dry-run) |

```bash
uv run pks form remove old_form --force
```

### `pks form show NAME`

Show full form definition YAML, plus algebra if sidecar exists.

```bash
uv run pks form show frequency
```

### `pks form validate [NAME]`

Validate form definitions (one or all). Checks that every form YAML has a valid name field and that forms referenced by concepts actually exist.

```bash
uv run pks form validate
uv run pks form validate frequency
```

---

## Contexts (`pks context`)

### `pks context add`

Add a new context to the registry.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--name` | TEXT | -- | Context ID (e.g., ctx_atms_tradition) (required) |
| `--description` | TEXT | -- | Short description (required) |
| `--inherits` | TEXT | -- | Parent context ID |
| `--excludes` | TEXT | -- | Comma-separated excluded context IDs |
| `--dry-run` | FLAG | false | [Dry-run](#dry-run) |

```bash
uv run pks context add --name ctx_atms_tradition --description "Papers from the ATMS research tradition"
```

### `pks context list`

List all registered contexts. No options.

```bash
uv run pks context list
```

---

## World Queries (`pks world`)

Many world commands accept positional `KEY=VALUE` bindings to scope queries by condition. These are passed as trailing arguments.

### Core Queries

#### `pks world status`

Show knowledge base stats (concepts, claims, conflicts). No options.

```bash
uv run pks world status
```

#### `pks world query CONCEPT_ID`

Show all claims for a concept.

```bash
uv run pks world query speech.pitch
```

#### `pks world bind [ARGS]...`

Show active claims under condition bindings. Arguments with `=` are bindings; the last argument without `=` is a concept filter.

```bash
uv run pks world bind domain=speech
uv run pks world bind domain=speech speech.pitch
```

#### `pks world derive CONCEPT_ID [ARGS]...`

Derive a value for a concept via parameterization relationships.

```bash
uv run pks world derive speech.formant_ratio domain=speech
```

#### `pks world chain CONCEPT_ID [ARGS]...`

Traverse the parameter space to derive a target concept.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--strategy` | `recency\|sample_size\|argumentation\|override` | -- | Resolution strategy |

```bash
uv run pks world chain speech.formant_ratio domain=speech --strategy sample_size
```

#### `pks world resolve CONCEPT_ID [ARGS]...`

Resolve a conflicted concept using a strategy. Supports [Argumentation options](#argumentation-options), [PrAF options](#praf-options), and [Decision criterion options](#decision-criterion-options).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--strategy` | `recency\|sample_size\|argumentation\|override` | -- | Resolution strategy (required) |
| `--override` | TEXT | -- | Claim ID for override strategy |

```bash
uv run pks world resolve speech.pitch domain=speech --strategy argumentation --semantics preferred
```

#### `pks world explain CLAIM_ID`

Show the stance chain for a claim.

```bash
uv run pks world explain speech.pitch.claim_01
```

#### `pks world hypothetical [ARGS]...`

Show what changes if claims are removed or added.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--remove` | TEXT | -- | Claim ID to remove |
| `--add` | TEXT | -- | JSON synthetic claim |

```bash
uv run pks world hypothetical domain=speech --remove speech.pitch.claim_02
```

#### `pks world revision-base [ARGS]...`

Show the current finite revision belief base for a scoped world.

```bash
uv run pks world revision-base speaker_sex=male
```

#### `pks world revision-entrenchment [ARGS]...`

Show the current deterministic entrenchment ordering for that scoped revision base.

```bash
uv run pks world revision-entrenchment speaker_sex=male
```

#### `pks world expand [ARGS]...`

Run one-shot expansion over the derived revision base. Does not mutate source YAML.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--atom` | TEXT | -- | JSON revision atom to add (required) |

```bash
uv run pks world expand speaker_sex=male --atom '{"kind":"claim","id":"synthetic_freq","value":123.0}'
```

#### `pks world contract [ARGS]...`

Run one-shot contraction over the derived revision base. Does not mutate source YAML.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--target` | TEXT | -- | Existing atom or claim id to contract (repeatable, required) |

```bash
uv run pks world contract speaker_sex=male --target freq_claim1
```

#### `pks world revise [ARGS]...`

Run one-shot revision over the derived revision base. Does not mutate source YAML.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--atom` | TEXT | -- | JSON revision atom to admit (required) |
| `--conflict` | TEXT | -- | Existing atom or claim id that conflicts with the new atom |

```bash
uv run pks world revise speaker_sex=male --atom '{"kind":"claim","id":"synthetic_freq","value":123.0}' --conflict freq_claim1
```

#### `pks world revision-explain [ARGS]...`

Explain one one-shot revision operation over the current scoped world.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--operation` | `expand\|contract\|revise` | -- | Revision operation to explain (required) |
| `--atom` | TEXT | -- | JSON revision atom for `expand` / `revise` |
| `--target` | TEXT | -- | Existing atom or claim id for `contract` |
| `--conflict` | TEXT | -- | Existing atom or claim id that conflicts with the new atom |

```bash
uv run pks world revision-explain speaker_sex=male --operation contract --target freq_claim1
```

#### `pks world iterated-state [ARGS]...`

Inspect the current explicit iterated revision state for a scoped world.

```bash
uv run pks world iterated-state speaker_sex=male
```

#### `pks world iterated-revise [ARGS]...`

Run one iterated revision episode and print the next explicit epistemic state. This remains a revision-state transform, not a worldline.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--atom` | TEXT | -- | JSON revision atom to admit (required) |
| `--conflict` | TEXT | -- | Existing atom or claim id that conflicts with the new atom |
| `--operator` | `restrained\|lexicographic` | restrained | Iterated operator family |

```bash
uv run pks world iterated-revise speaker_sex=male --atom '{"kind":"claim","id":"synthetic_freq","value":123.0}' --conflict freq_claim1 --operator lexicographic
```

#### `pks world sensitivity CONCEPT_ID [ARGS]...`

Analyze which input most influences a derived quantity.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | `text\|json` | -- | Output format |

```bash
uv run pks world sensitivity speech.formant_ratio domain=speech
```

#### `pks world export-graph [ARGS]...`

Export the knowledge graph as DOT or JSON.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format` | `dot\|json` | -- | Output format |
| `--group` | INTEGER | -- | Parameterization group ID to filter by |
| `--output` | TEXT | -- | Output file path |

```bash
uv run pks world export-graph domain=speech --format dot --output graph.dot
```

#### `pks world check-consistency [ARGS]...`

Check for conflicts, optionally including transitive (multi-hop) ones.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--transitive` | FLAG | false | Check multi-hop transitive conflicts |

```bash
uv run pks world check-consistency domain=speech --transitive
```

#### `pks world algorithms`

List algorithm claims in the world model.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--stage` | TEXT | -- | Filter by processing stage |
| `--concept` | TEXT | -- | Filter by concept |

```bash
uv run pks world algorithms --stage preprocessing
```

#### `pks world fragility [ARGS]...`

Rank intervention targets by fragility -- what to inspect next.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--concept` | TEXT | -- | Focus on a single concept |
| `--top-k` | INTEGER | 20 | Number of ranked interventions |
| `--skip-atms` | FLAG | false | Skip ATMS assumption interventions |
| `--skip-discovery` | FLAG | false | Skip missing-measurement interventions |
| `--skip-conflict` | FLAG | false | Skip conflict interventions |
| `--skip-grounding` | FLAG | false | Skip ground-fact and grounded-rule interventions |
| `--skip-bridge` | FLAG | false | Skip bridge undercut interventions |
| `--ranking-policy` | `heuristic_roi\|family_local_only\|pareto` | `heuristic_roi` | Ranking policy |
| `--format` | `text\|json` | `text` | Output format |

```bash
uv run pks world fragility --ranking-policy pareto --skip-grounding
```

### Extensions

#### `pks world extensions [ARGS]...`

Show argumentation extensions -- all claims that survive scrutiny. Supports [Argumentation options](#argumentation-options) and [PrAF options](#praf-options).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--backend` | `claim_graph\|aspic\|atms\|praf` | claim_graph | Argumentation backend |

```bash
uv run pks world extensions domain=speech --semantics grounded
uv run pks world extensions domain=speech --backend praf --praf-strategy mc
```

### ATMS Commands

All ATMS commands support [ATMS options](#atms-options).

#### `pks world atms-status [ARGS]...`

Show ATMS-native claim status, support quality, and essential support.

```bash
uv run pks world atms-status --context ctx_atms_tradition
```

#### `pks world atms-context [ARGS]...`

Show which ATMS-supported claims hold in the current bound environment.

```bash
uv run pks world atms-context --context ctx_atms_tradition
```

#### `pks world atms-verify [ARGS]...`

Run ATMS label self-checks for the current bound environment.

```bash
uv run pks world atms-verify
```

#### `pks world atms-futures TARGET [ARGS]...`

Show bounded ATMS future environments for a claim or concept.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--queryable` | TEXT | -- | Future/queryable assumption (CEL or key=value) (required) |
| `--limit` | INTEGER | 8 | Maximum number of future environments to inspect |

```bash
uv run pks world atms-futures speech.pitch --queryable "domain=speech" --limit 4
```

#### `pks world atms-stability TARGET [ARGS]...`

Show bounded ATMS-native stability over the implemented future replay substrate.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--queryable` | TEXT | -- | Future/queryable assumption (CEL or key=value) (required) |
| `--limit` | INTEGER | 8 | Maximum number of future environments to inspect |

```bash
uv run pks world atms-stability speech.pitch --queryable "domain=speech"
```

#### `pks world atms-relevance TARGET [ARGS]...`

Show which bounded queryables can flip an ATMS or concept status.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--queryable` | TEXT | -- | Future/queryable assumption (CEL or key=value) (required) |
| `--limit` | INTEGER | 8 | Maximum number of future environments to inspect |

```bash
uv run pks world atms-relevance speech.pitch --queryable "domain=speech"
```

#### `pks world atms-interventions TARGET [ARGS]...`

Show bounded additive intervention plans for an ATMS claim or concept.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--target-status` | TEXT | -- | Desired ATMS node status (IN/OUT) (required) |
| `--queryable` | TEXT | -- | Future/queryable assumption (CEL or key=value) (required) |
| `--limit` | INTEGER | 8 | Maximum number of future environments to inspect |

```bash
uv run pks world atms-interventions speech.pitch --target-status IN --queryable "domain=speech"
```

#### `pks world atms-next-query TARGET [ARGS]...`

Show next-query suggestions derived from bounded additive intervention plans.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--target-status` | TEXT | -- | Desired ATMS node status (IN/OUT) (required) |
| `--queryable` | TEXT | -- | Future/queryable assumption (CEL or key=value) (required) |
| `--limit` | INTEGER | 8 | Maximum number of future environments to inspect |

```bash
uv run pks world atms-next-query speech.pitch --target-status IN --queryable "domain=speech"
```

#### `pks world atms-why-out TARGET [ARGS]...`

Explain whether an ATMS OUT status is missing-support or nogood-pruned.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--queryable` | TEXT | -- | Future/queryable assumption (CEL or key=value) |
| `--limit` | INTEGER | 8 | Maximum number of future environments to inspect |

```bash
uv run pks world atms-why-out speech.pitch --queryable "domain=speech"
```

---

## Worldlines (`pks worldline`)

Materialized query artifacts -- traced paths through the knowledge space with full provenance.

### `pks worldline create NAME`

Create a worldline definition (question only, no results yet). Supports [Argumentation options](#argumentation-options), [PrAF options](#praf-options), [Decision criterion options](#decision-criterion-options), [ASPIC+ options](#aspic-options), and [Revision Worldline Options](#revision-worldline-options).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--bind` | TEXT | -- | Condition binding (key=value) |
| `--with` | TEXT | -- | Value override (concept=value) |
| `--target` | TEXT | -- | Target concept to derive/resolve (repeatable, required) |
| `--strategy` | `recency\|sample_size\|argumentation\|override` | -- | Resolution strategy |
| `--context` | TEXT | -- | Context to scope the query |
| `--revision-operation` | `expand\|contract\|revise\|iterated_revise` | -- | Optional revision operation to attach |
| `--revision-atom` | TEXT | -- | JSON revision atom for `expand` / `revise` / `iterated_revise` |
| `--revision-target` | TEXT | -- | Revision target for `contract` |
| `--revision-conflict` | TEXT | -- | Conflict mapping `atom_id=target[,target...]`; repeatable |
| `--revision-operator` | `restrained\|lexicographic` | -- | Iterated revision operator family |

```bash
uv run pks worldline create my-worldline --target speech.pitch --bind domain=speech --strategy argumentation
```

### `pks worldline run NAME`

Run (materialize) a worldline. Creates it first if it doesn't exist. Supports [Argumentation options](#argumentation-options), [PrAF options](#praf-options), [Decision criterion options](#decision-criterion-options), [ASPIC+ options](#aspic-options), and [Revision Worldline Options](#revision-worldline-options).

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--bind` | TEXT | -- | Condition binding (key=value) |
| `--with` | TEXT | -- | Value override (concept=value) |
| `--target` | TEXT | -- | Target concept (repeatable; required only when creating a new worldline) |
| `--strategy` | `recency\|sample_size\|argumentation\|override` | -- | Resolution strategy |
| `--context` | TEXT | -- | Context scope |
| `--revision-operation` | `expand\|contract\|revise\|iterated_revise` | -- | Optional revision operation to attach |
| `--revision-atom` | TEXT | -- | JSON revision atom for `expand` / `revise` / `iterated_revise` |
| `--revision-target` | TEXT | -- | Revision target for `contract` |
| `--revision-conflict` | TEXT | -- | Conflict mapping `atom_id=target[,target...]`; repeatable |
| `--revision-operator` | `restrained\|lexicographic` | -- | Iterated revision operator family |

```bash
uv run pks worldline run my-worldline
```

### `pks worldline show NAME`

Show a worldline's results, including any stored revision query and revision result payload.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--check` | FLAG | false | Check for staleness |

```bash
uv run pks worldline show my-worldline --check
```

### `pks worldline list`

List all worldlines. No options.

```bash
uv run pks worldline list
```

### `pks worldline diff NAME_A NAME_B`

Compare two worldlines side by side.

```bash
uv run pks worldline diff baseline experimental
```

### `pks worldline refresh NAME`

Re-run a worldline with current knowledge.

```bash
uv run pks worldline refresh my-worldline
```

### `pks worldline delete NAME`

Delete a worldline.

```bash
uv run pks worldline delete old-worldline
```

---

## Shared Option Groups

Several option sets recur across multiple commands. They are defined here once and referenced by name from individual commands.

### Argumentation Options

Used by: `world extensions`, `world resolve`, `worldline create`, `worldline run`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--reasoning-backend` | `claim_graph\|aspic\|atms\|praf` | claim_graph | Argumentation backend |
| `--semantics` | backend-dependent | grounded | Argumentation semantics. `worldline create/run` accepts `grounded`, `preferred`, `stable`, `d-preferred`, `s-preferred`, `c-preferred`, `bipolar-stable`, and `complete`; backend support is validated separately. |
| `--set-comparison` | `elitist\|democratic` | elitist | Set comparison for preference ordering |
| `--context` | TEXT | -- | Context to scope the argumentation |

Note: `world extensions` uses `--backend` instead of `--reasoning-backend`.
Note: `world resolve` and `world extensions` currently accept only `grounded`, `preferred`, and `stable` for `--semantics`.

### PrAF Options

Used alongside argumentation options when `--backend`/`--reasoning-backend` is `praf`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--praf-strategy` | `auto\|mc\|exact\|dfquad_quad\|dfquad_baf` | auto | PrAF computation strategy |
| `--praf-epsilon` | FLOAT | 0.01 | PrAF MC error tolerance |
| `--praf-confidence` | FLOAT | 0.95 | PrAF MC confidence level |
| `--praf-seed` | INTEGER | random | PrAF MC RNG seed |

### Decision Criterion Options

Used by: `world resolve`, `worldline create`, `worldline run`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--decision-criterion` | `pignistic\|lower_bound\|upper_bound\|hurwicz` | pignistic | Decision criterion for opinion interpretation |
| `--pessimism-index` | FLOAT | 0.5 | Hurwicz pessimism index (0-1) |

### ASPIC+ Options

Used by: `worldline create`, `worldline run`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--link-principle` | `last\|weakest` | last | ASPIC+ link principle (Modgil & Prakken 2018, Defs 19-21) |

### Revision Worldline Options

Used by: `worldline create`, `worldline run`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--revision-operation` | `expand\|contract\|revise\|iterated_revise` | -- | Optional revision operation attached to the worldline |
| `--revision-atom` | TEXT | -- | JSON revision atom for `expand` / `revise` / `iterated_revise` |
| `--revision-target` | TEXT | -- | Revision target for `contract` |
| `--revision-conflict` | TEXT | -- | Conflict mapping `atom_id=target[,target...]`; repeatable |
| `--revision-operator` | `restrained\|lexicographic` | -- | Iterated revision operator family |

### ATMS Options

Used by all `world atms-*` commands.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--context` | TEXT | -- | Context to scope the ATMS inspection |

Commands that support future-environment exploration (`atms-futures`, `atms-stability`, `atms-relevance`, `atms-interventions`, `atms-next-query`, `atms-why-out`) additionally accept:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--queryable` | TEXT | -- | Future/queryable assumption (CEL or key=value) |
| `--limit` | INTEGER | 8 | Maximum number of future environments to inspect |

### Embedding Options

Used by: `concept embed`, `concept similar`, `claim embed`, `claim similar`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--model` | TEXT | -- | litellm model string (or 'all' for embed commands) |
| `--top-k` | INTEGER | -- | Number of results (similar commands) |
| `--agree` | FLAG | false | Similar under ALL stored models (similar commands) |
| `--disagree` | FLAG | false | Similar under some models but not others (similar commands) |

### Dry-run

Used by: `concept add`, `concept add-value`, `concept alias`, `concept deprecate`, `concept link`, `concept rename`, `context add`, `form add`, `form remove`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dry-run` | FLAG | false | Show what would happen without writing |

---

## Resolution Strategies

Used with `pks world resolve --strategy` and `pks worldline create/run --strategy`.

| Strategy | Behavior |
|----------|----------|
| `recency` | Most recent paper wins |
| `sample_size` | Largest sample size wins |
| `argumentation` | Run argumentation backend, project survivors |
| `override` | Specify a claim ID directly via `--override` |
