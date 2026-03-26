# Data Model

propstore's data model has six main entities: **concepts**, **forms**, **claims**, **conditions**, **stances**, and **contexts**. Everything lives in YAML files under `knowledge/`.

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

Claims and relationships can be scoped by **conditions** — CEL (Common Expression Language) expressions that define when they hold:

```yaml
conditions:
  - "speaker_sex == 'male'"
  - "task == 'speech'"
```

The compiler type-checks conditions against the concept registry: quantity concepts get numeric comparisons, category concepts get equality/`in` checks with value-set validation, boolean concepts get boolean logic.

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
```

Claims reference their context via `context_id`. The compiler validates that all `context_id` references resolve to registered contexts. Contexts support hierarchy (`parent`), mutual exclusion (`excludes`), and visibility scoping — a BoundWorld can be filtered to show only claims from a given context and its descendants.

## Schema

The data model is defined in [LinkML](https://linkml.io/) at `schema/concept_registry.linkml.yaml` and `schema/claim.linkml.yaml`. JSON Schema is generated from these for validation. Run `schema/generate.py` to regenerate.
