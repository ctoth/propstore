# propstore

A propositional knowledge store compiler. Papers contain claims — propstore inverts the storage model so that **claims cite papers**, not the other way around.

YAML is the source of truth. A deterministic Python compiler validates, type-checks, detects conflicts, and builds a queryable SQLite sidecar. No LLM in the compiler path.

## Architecture

```
concepts/*.yaml          ──┐
claims/*.yaml              │
forms/*.yaml               ├──▶  compiler  ──▶  sidecar/propstore.sqlite
schema/ (LinkML + JSON)  ──┘      (pks)          (FTS5, conflict table, ...)
                                    │
                                    └──▶  WorldModel (read-only reasoner)
```

- **Concepts** are true-named quantities, categories, booleans, or structural types. Each gets a stable ID (`concept12`), a canonical name, and a kind that determines what operations are legal in CEL condition expressions.
- **Claims** bind to concept IDs with provenance, values, units, and CEL conditions that scope when the claim holds. Claims support an optional `notes` field for methodological context, experimental conditions, or caveats. Five claim types: **parameter** (numeric value binding), **equation** (math relationship with variable bindings), **observation** (qualitative), **model** (multi-equation framework), and **measurement** (perceptual/behavioral — JND, threshold, rating).
- **Forms** define the measurement/representation kind for concepts (e.g. `pressure`, `category`, `boolean`). Each form is a YAML file in `forms/` that specifies kind type, units, any parameters (category values, extensibility), and optional SI base **dimensions**.
- **Conflicts** are data, not errors. When two claims for the same concept disagree, the compiler classifies the pair as CONFLICT (same scope), OVERLAP (partial scope overlap), or PHI_NODE (different scope — not actually a conflict). Classification uses Z3 satisfiability checking as the primary path, with interval arithmetic as fallback.
- **Parameterization groups** — connected-component analysis over concepts linked by algebraic/functional relationships. Each group is a "parameter space" of related quantities.
- **Auto-generation** — the compiler generates SymPy expressions from human-readable equation strings, and produces human-readable descriptions for claims that lack an explicit statement.
- **WorldModel** — a read-only reasoner over the compiled sidecar. Supports condition-bound views: bind concrete values to condition variables (e.g. `vowel_height="high"`) and query which claims are active, conflicted, or determined under those bindings. Uses Z3 to test whether a claim's conditions are compatible with the bindings.

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
pks init                # creates ./knowledge/ with concepts/, claims/, forms/, sidecar/
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

### Forms

```bash
pks form list
pks form show pressure
pks form add --file forms/pressure.yaml
pks form remove pressure
pks form validate [pressure]       # validate one or all form definitions
```

#### Form Dimensions

Forms can declare SI base dimensions via a `dimensions` map. Keys are SI dimension symbols (`L`, `M`, `T`, `I`, `Theta`, `N`, `J`); values are integer exponents. Only include dimensions with non-zero exponents.

```yaml
# forms/frequency.yaml
name: frequency
dimensionless: false
unit_symbol: Hz
dimensions:
  T: -1

# forms/pressure.yaml
name: pressure
dimensionless: false
unit_symbol: Pa
dimensions:
  M: 1
  L: -1
  T: -2
```

Dimensionless forms omit `dimensions` (or leave it empty).

### Claims

```bash
pks claim validate [--dir claims/]
pks claim conflicts [--concept concept1] [--class CONFLICT|OVERLAP|PARAM_CONFLICT]
```

#### Claim Notes

Claims support an optional `notes` string for methodological context that doesn't fit elsewhere:

```yaml
- id: claim42
  type: parameter
  concept: concept12
  value: 250.0
  unit: Hz
  notes: "Measured during sustained phonation; excludes breathy onset tokens."
  provenance:
    paper: Smith_2020
    page: 7
```

Use `notes` for experimental conditions, caveats, or methodological details that qualify the claim but aren't captured by conditions or provenance fields.

### World

Query the compiled knowledge base through the WorldModel reasoner:

```bash
pks world status                   # concept/claim/conflict counts
pks world query concept12          # all claims for a concept
pks world explain claim_001        # stance chain for a claim
pks world bind concept12 vowel_height=high  # active claims under bindings
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

The test suite covers the validator, CEL type-checker, Z3 condition solver,
conflict detector, sidecar builder, WorldModel, CLI, SymPy generator,
description generator, and parameterization groups.

## Repository layout

`pks init` creates a `knowledge/` directory:

```
knowledge/
  concepts/           # one YAML per concept (hand-editable)
  claims/             # one YAML per paper/source
  forms/              # form definitions (kind, units, parameters)
  sidecar/            # compiled SQLite output (not checked in)
```
