# propstore

A propositional knowledge store compiler. Papers contain claims — propstore inverts the storage model so that **claims cite papers**, not the other way around.

YAML is the source of truth. A deterministic Python compiler validates, type-checks, detects conflicts, and builds a queryable SQLite sidecar. No LLM in the compiler path.

## Architecture

```
concepts/*.yaml          ──┐
claims/*.yaml              ├──▶  compiler  ──▶  sidecar/propstore.sqlite
schema/ (LinkML + JSON)  ──┘      (pks)          (FTS5, conflict table, ...)
```

- **Concepts** are true-named quantities, categories, booleans, or structural types. Each gets a stable ID (`concept12`), a canonical name, and a kind that determines what operations are legal in CEL condition expressions.
- **Claims** bind to concept IDs with provenance, values, units, and CEL conditions that scope when the claim holds. Five claim types: **parameter** (numeric value binding), **equation** (math relationship with variable bindings), **observation** (qualitative), **model** (multi-equation framework), and **measurement** (perceptual/behavioral — JND, threshold, rating).
- **Conflicts** are data, not errors. When two claims for the same concept disagree, the compiler classifies the pair as CONFLICT (same scope), OVERLAP (partial scope overlap), or PHI_NODE (different scope — not actually a conflict).
- **Parameterization groups** — connected-component analysis over concepts linked by algebraic/functional relationships. Each group is a "parameter space" of related quantities.
- **Auto-generation** — the compiler generates SymPy expressions from human-readable equation strings, and produces human-readable descriptions for claims that lack an explicit statement.

## Install

```
uv sync
```

## CLI

Everything goes through `pks`:

```
uv run pks --help
```

### Init

```bash
pks init                # creates ./knowledge/ with concepts/, claims/, sidecar/
pks init myproject      # creates ./myproject/ instead
pks -C /some/path init  # creates /some/path/knowledge/
```

If the target directory already contains `concepts/`, prints "Already initialized" and exits.

### Concepts

```bash
# Add a new concept (status=proposed, ID auto-assigned from counter)
pks concept add --domain speech --name subglottal_pressure \
    --definition "Air pressure below the glottis" --form pressure

# List, show, search
pks concept list [--domain speech] [--status accepted]
pks concept show subglottal_pressure    # accepts ID or canonical_name
pks concept search "vocal fold"

# Mutate (all support --dry-run)
pks concept alias concept12 --name Ps --source Sundberg_1993
pks concept rename concept12 --name new_name
pks concept deprecate concept12 --replaced-by concept1
pks concept link concept1 broader concept4 [--source Paper_2020] [--note "..."]
```

### Claims

```bash
pks claim validate [--dir claims/]
pks claim conflicts [--concept concept1] [--class CONFLICT|OVERLAP|PARAM_CONFLICT]
```

### Compiler

```bash
pks validate          # validate all concepts + claims, CEL type-checking
pks build             # validate → build sidecar → conflict detection → summary
pks query "SELECT * FROM concept WHERE kind_type = 'quantity'"
pks import-papers --papers-root ../research-papers-plugin/papers
pks export-aliases --format json
```

### research-papers-plugin handoff

`propstore` now owns the machine-readable import step from
`../research-papers-plugin`, but the plugin still has to emit the paper-local
claim artifact.

Expected plugin-side artifact per paper:

```text
../research-papers-plugin/papers/<PaperDir>/claims.yaml
```

Import/build flow from this repository:

```bash
pks import-papers --papers-root ../research-papers-plugin/papers
pks validate
pks build
```

The importer copies each `papers/<PaperDir>/claims.yaml` into `claims/<PaperDir>.yaml`
and normalizes `source.paper` to the paper directory name so the sidecar and
the paper corpus use the same paper identity.

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |
| 2 | Validation failure |

### Principles

- Every mutating operation validates before writing. If validation fails, nothing changes on disk.
- Every mutating operation prints what it did.
- `--dry-run` on all mutating commands shows what would happen without writing.
- Hand-editing YAML is always valid — the validator catches mistakes either way.

## Schema

The concept registry schema is defined in LinkML (`schema/concept_registry.linkml.yaml`) and generates JSON Schema for validation. The compiler contract — the invariants that JSON Schema can't express — is documented as prose in `concept-registry-schema.yaml`.

Key invariant: **the compiler never produces output from an invalid state.** If any concept, relationship, or CEL expression fails validation, the entire build fails. No partial sidecar.

## Tests

```
uv run pytest tests/ -v
```

The test suite covers the validator, CEL type-checker, conflict detector,
sidecar builder, CLI, SymPy generator, description generator, and
parameterization groups.

## File layout

```
concepts/
  .counters/speech.next      # just an integer
  subglottal_pressure.yaml
  fundamental_frequency.yaml
  ...
claims/
  paper_alpha.yaml
  paper_beta.yaml
compiler/
  validate.py                # concept validator
  cel_checker.py             # CEL parser + type checker
  validate_claims.py         # claim validator
  conflict_detector.py       # conflict classification
  build_sidecar.py           # SQLite builder
  sympy_generator.py         # SymPy expression auto-generation
  description_generator.py   # human-readable claim descriptions
  parameterization_groups.py # connected-component group analysis
  cli/                       # Click CLI
    __init__.py              # main group
    concept.py               # concept subcommands
    claim.py                 # claim subcommands
    compiler_cmds.py         # validate/build/query/export
    init.py                  # pks init command
    helpers.py               # shared utilities
schema/
  concept_registry.linkml.yaml
  claim.linkml.yaml
  generated/                 # JSON Schema, Python dataclasses
sidecar/
  propstore.sqlite           # compiled output (not checked in)
```
