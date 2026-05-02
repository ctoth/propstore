# Data Model

propstore has canonical authored artifacts in `knowledge/`, plus a compiled SQLite sidecar used as the read/query surface. Git/YAML is the source of truth; the sidecar is a versioned materialization.

The main authored entities are **sources**, **concepts**, **forms**, **claims**, **stances**, **authored justifications**, and **contexts**. Conditions are fields on claims and relations, not a separate top-level entity.

## Sources

Sources live in `sources/<slug>.yaml` and are first-class provenance records. Claims compile with a stable `source_slug` foreign-key-style reference to these rows.

```yaml
id: tag:example.org,2026:halpin-2010
kind: academic_paper
origin:
  type: doi
  value: 10.1016/j.websem.2010.01.001
  retrieved: 2026-04-07
trust:
  prior_base_rate: 0.6
  quality:
    venue: peer_reviewed
artifact_code: sha256:...
```

Source-branch `notes.md` and metadata remain canonical git artifacts. They are not compiled into claim reasoning tables.

## Concepts

A concept is a named quantity, category, or structural entity. One YAML file per concept in `concepts/`, filename matches `canonical_name`.

```yaml
id: concept1
canonical_name: fundamental_frequency
status: accepted
definition: Rate of vocal fold vibration during phonation.
domain: speech
form: frequency
aliases:
  - name: F0
    source: common
  - name: pitch_frequency
    source: Titze_1994
relationships:
  - type: component_of
    target: concept5
parameterization_relationships:
  - formula: "f0 = 1 / T0"
    sympy: "Eq(concept1, 1 / concept2)"
    inputs: [concept2]
    exactness: exact
    source: definition
    bidirectional: true
```

**Status lifecycle:** `proposed` -> `accepted` -> `deprecated` (with `replaced_by` pointer). Concepts are never deleted.

**Kind system:** Each concept has a `form` referencing a form definition file. The form determines the concept's kind:

| Kind | Examples | CEL behavior |
|------|----------|-------------|
| `quantity` | frequency, pressure, duration | Numeric comparisons and arithmetic |
| `category` | voice_quality_type, language | Equality and `in` checks against value sets |
| `boolean` | is_voiced | Boolean logic |
| `structural` | voice_source | Cannot appear in CEL expressions |
| `timepoint` | valid_from, valid_until | Numeric comparisons (epoch seconds); automatic interval ordering constraints; not valid for parameterization/dimensional algebra |

## Forms

Form definitions live in `forms/<name>.yaml` and define dimensional type signatures:

```yaml
name: frequency
unit_symbol: Hz
dimensionless: false
dimensions:
  T: -1
common_alternatives:
  - unit: kHz
    type: multiplicative
    multiplier: 0.001
```

The compiler uses form definitions for unit validation via dimensional analysis, checking that claim units are compatible with concept dimensions.

### Unit conversions (common_alternatives)

The `common_alternatives` array defines how non-SI units convert to the form's SI base unit. Three conversion types:

- **Multiplicative:** `si_value = raw * multiplier`. Example: kHz has multiplier 1000, so 5 kHz becomes 5000 Hz.
- **Affine:** `si_value = raw * multiplier + offset`. Used for temperature scales — degC uses offset 273.15 to convert to Kelvin.
- **Logarithmic:** `si_value = reference * base^(raw / divisor)`. Used for decibel scales — dB SPL uses base 10, divisor 20, reference 0.00002 Pa.

During sidecar build, all claim values are normalized to SI via these conversions (with pint as fallback for standard unit prefixes). The sidecar stores both raw and SI-normalized values (`value_si`, `lower_bound_si`, `upper_bound_si`).

### Domain-specific units (extra_units)

The `extra_units` field registers domain-specific units not recognized by pint. Each entry has a `symbol` and optionally `dimensions`. These units are added to the form's allowed unit set and registered into the dimensional analysis symbol table.

See [units-and-forms.md](units-and-forms.md) for full details on SI normalization, form algebra, and dimensional analysis.

## Claims

Claims are extracted from papers and stored in `claims/<paper_name>.yaml`. There are nine claim types.

### parameter

A numeric value binding for a concept under stated conditions:

```yaml
- id: claim1
  type: parameter
  concept: concept1
  value: 120.0
  uncertainty: 15.0
  uncertainty_type: sd
  unit: Hz
  conditions:
    - "speaker_sex == 'male'"
  provenance:
    paper: Titze_1994
    page: 42
```

```yaml
- id: claim1
  type: parameter
  concept: ad_reading_speed
  value: 180.0
  unit: "words/min"
  conditions:
    - "task == 'audio_description'"
  provenance:
    paper: Li_2026_ADCanvas
    page: 8
```

### equation

A mathematical relationship with variable bindings:

```yaml
- id: claim10
  type: equation
  expression: "OQ = (T_o) / T_0"
  sympy: "Eq(OQ, T_o / T_0)"
  variables:
    - symbol: OQ
      concept: concept3
    - symbol: T_o
      concept: concept4
    - symbol: T_0
      concept: concept2
  provenance:
    paper: Henrich_2003
    page: 8
```

### measurement

A perceptual or behavioral measurement:

```yaml
- id: claim20
  type: measurement
  target_concept: concept1
  measure: jnd_relative
  value: 0.003
  unit: ratio
  listener_population: native_english
  provenance:
    paper: Moore_1973
    page: 15
```

### observation

A qualitative claim that resists parameterization:

```yaml
- id: claim30
  type: observation
  statement: "Breathiness increases with incomplete glottal closure"
  concepts: [concept7, concept8]
  provenance:
    paper: Klatt_1990
    page: 22
```

### model

A parameterized equation system:

```yaml
- id: claim40
  type: model
  name: "Klatt cascade formant synthesizer"
  equations:
    - "output = cascade(F1, F2, F3, F4, F5)"
  parameters:
    - name: F1
      concept: concept10
  provenance:
    paper: Klatt_1980
    page: 5
```

### algorithm

A procedural computation as a Python function body:

```yaml
- id: claim50
  type: algorithm
  concept: concept12
  stage: excitation
  body: |
    def glottal_pulse(t, T0, Tp, Tn):
        if t < Tp:
            return 0.5 * (1 - math.cos(math.pi * t / Tp))
        elif t < Tp + Tn:
            return math.cos(math.pi * (t - Tp) / (2 * Tn))
        else:
            return 0.0
  variables:
    - name: t
      concept: concept60
    - name: T0
      concept: concept2
  provenance:
    paper: Klatt_1980
    page: 12
```

### mechanism

A causal or explanatory process linking concepts:

```yaml
- id: claim60
  type: mechanism
  statement: "Undercutting defeat removes the connection between premise and conclusion without challenging the premise itself"
  concepts: [undercutting_attack, defeasible_reasoning]
  provenance:
    paper: Pollock_1987
    page: 485
```

### comparison

A comparative claim between approaches, methods, or systems:

```yaml
- id: claim61
  type: comparison
  statement: "Preferred semantics produces more extensions than grounded semantics on frameworks with even-length cycles"
  concepts: [preferred_extension, grounded_extension]
  provenance:
    paper: Dung_1995
    page: 331
```

### limitation

A known boundary, failure case, or applicability constraint:

```yaml
- id: claim62
  type: limitation
  statement: "Stable extensions are not guaranteed to exist for all argumentation frameworks"
  concepts: [stable_extension, argumentation_framework]
  provenance:
    paper: Dung_1995
    page: 328
```

## Conditions

Claims and relationships can be scoped by **conditions** -- CEL (Common Expression Language) expressions that define when they hold:

```yaml
conditions:
  - "speaker_sex == 'male'"
  - "task == 'speech'"
```

CEL is an authoring frontend. The compiler checks each condition against the
condition registry in `propstore.core.conditions.cel_frontend`, lowers it to
`ConditionIR`, and stores a checked semantic payload alongside the authored
source text. Runtime activation, conflict detection, graph queries, and
parameterization compatibility consume `CheckedConditionSet` or encoded
`ConditionIR`; they do not reparse `conditions_cel`.

If condition IR storage changes, the sidecar is rebuilt. Derived sidecar
storage intentionally has no compatibility reader for older condition payload
shapes.

- quantity concepts use numeric comparisons
- boolean concepts use boolean logic
- closed categories (`extensible: false`) use finite enum semantics, so undeclared literals are hard errors
- open categories (`extensible: true`) use symbolic string semantics, so undeclared literals remain semantically valid and only warn at check time
- unknown concept names are hard errors everywhere

## Justifications

Justifications are inference rules that connect premise claims to conclusion claims. There are two distinct cases:

- Authored justifications live in `justifications/<source>.yaml` and compile into the sidecar `justification` table.
- Runtime-derived justifications such as `reported:claim_id` and `supports:a->b` are built from the active claim graph when argumentation code needs them. They are not persisted in the sidecar.

### Data model

Each justification is a `CanonicalJustification` with these fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `justification_id` | `str` | — | Unique identifier (e.g., `reported:claim1` or `supports:claim2->claim3`) |
| `conclusion_claim_id` | `str` | — | The claim this justification concludes |
| `premise_claim_ids` | `tuple[str, ...]` | `()` | Claims that serve as premises |
| `rule_kind` | `str` | `"reported_claim"` | Type of inference rule |
| `rule_strength` | `str` | `"defeasible"` | Whether the rule is strict or defeasible |
| `provenance` | `ProvenanceRecord \| None` | `None` | Source attribution |
| `attributes` | `tuple[tuple[str, Any], ...]` | `()` | Additional metadata as sorted key-value pairs |

### rule_kind

Three values:

- **`reported_claim`** — Every claim automatically gets a `reported_claim` justification. This represents the claim's direct assertion from its source paper, with no premises.
- **`supports`** — A premise claim provides corroborating evidence for the conclusion claim.
- **`explains`** — A premise claim provides a mechanistic explanation for the conclusion claim.

### rule_strength

Two values, corresponding to ASPIC+ rule types (Modgil & Prakken 2018, Def 2):

- **`strict`** — The inference is logically unattackable. Strict rules have no name and cannot be undercut.
- **`defeasible`** — The inference is tentative and can be undercut. Defeasible rules are named by their `justification_id`, which enables targeted undercutting (Def 8c).

### ASPIC+ mapping

Justifications translate directly to ASPIC+ rules via the bridge in `aspic_bridge.py`. `reported_claim` justifications become knowledge base premises (not rules). Justifications with premises become strict or defeasible rules depending on `rule_strength`. See [structured-argumentation.md](structured-argumentation.md) for the full translation pipeline (T1–T7).

### Targeted undercutting

An `undercuts` stance can include a `target_justification_id` field to attack a specific defeasible rule rather than all rules concluding a given claim. When multiple defeasible rules support the same conclusion, omitting `target_justification_id` raises an ambiguity error. This implements Pollock's (1987) undercutting defeat: the attacker targets the inference rule itself, not the conclusion.

### Authoring

Authored justifications are optional and look like:

```yaml
justifications:
  - id: just1
    conclusion: claim_observation
    premises: [claim_parameter]
    rule_kind: reported_claim
    rule_strength: defeasible
```

The sidecar stores authored justifications exactly so source-authored inference structure remains queryable. Support and explanation edges still participate in argumentation, but their `CanonicalJustification` records are synthesized at runtime from the active graph.

## Stances

Claims can express epistemic relations to other claims:

```yaml
stances:
  - type: rebuts
    target: claim15
    strength: strong
    note: "Contradicting conclusion with larger sample size"
  - type: supersedes
    target: claim42
```

Six stance types (ASPIC+ taxonomy, active voice — the claim holding the stance acts on the target):

| Type | Category | Weight | Meaning |
|------|----------|--------|---------|
| `rebuts` | Attack | -1.0 | Directly contradicts the target's conclusion |
| `undercuts` | Attack | -1.0 | Attacks the inference method or reasoning |
| `undermines` | Attack | -0.5 | Weakens a premise or evidence quality |
| `supports` | Support | +1.0 | Provides corroborating evidence |
| `explains` | Support | +0.5 | Provides a mechanistic explanation |
| `supersedes` | Preference | --- | Replaces the target entirely (short-circuits resolution) |

Based on ASPIC+ (Modgil & Prakken 2014) and Pollock's rebutting vs undercutting distinction (Prakken & Horty 2012).

Stances feed into the argumentation framework — attacks become defeat candidates filtered through preference ordering, supports contribute to claim strength.

## Contexts

Contexts represent research traditions, theoretical frameworks, or experimental paradigms that scope groups of claims. One YAML file per context in `contexts/`:

```yaml
id: ctx_abstract_argumentation
name: ctx_abstract_argumentation
description: Dung's abstract argumentation framework tradition — arguments as abstract
  entities with attack relations, multiple acceptability semantics
structure:
  assumptions:
    - "domain == 'argumentation'"
  parameters:
    tradition: abstract
  perspective: dung
lifting_rules:
  - id: lift_dung_to_argumentation
    source:
      id: ctx_abstract_argumentation
    target:
      id: ctx_argumentation
    mode: monotonic
```

Claims reference their context via `context: {id: ...}`. The compiler validates that all context references resolve to registered contexts. Contexts are structured logical terms with authored assumptions, parameters, and perspective metadata. Visibility inheritance is not a production concept; cross-context visibility is granted only by explicit lifting rules.

## Schema

The data model is defined in [LinkML](https://linkml.io/) at `schema/concept_registry.linkml.yaml` and `schema/claim.linkml.yaml`. JSON Schema is generated from these for validation. Run `schema/generate.py` to regenerate.
