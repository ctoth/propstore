# Units and Forms

Forms define the dimensional type system. Every concept has a form that determines its unit, dimensions, and kind. The compiler uses forms for unit validation, SI normalization, and form algebra derivation.

Source: `propstore/form_utils.py` (FormDefinition, UnitConversion, normalize/from SI, pint integration), `propstore/unit_dimensions.py` (bridgman integration, symbol table), `propstore/build_sidecar.py` (form and form_algebra tables, SI normalization during build), `propstore/world/model.py` (form queries), `propstore/cli/form.py` (CLI commands), `propstore/validate.py` (dimensional compatibility checking).

## Form Definitions

Form definitions live in YAML files under `forms/`. Each file declares one form with the following schema:

```yaml
name: frequency
unit_symbol: Hz
dimensionless: false
dimensions:
  T: -1
kind: quantity
common_alternatives:
  - unit: kHz
    type: multiplicative
    multiplier: 1000
  - unit: MHz
    type: multiplicative
    multiplier: 1000000
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Lowercase identifier, must match filename. Pattern: `^[a-z][a-z0-9_]*$` |
| `dimensionless` | boolean | yes | Whether this form has no physical dimensions |
| `unit_symbol` | string | no | SI unit symbol (e.g. `Hz`, `N`, `K`) |
| `dimensions` | dict | no | SI base dimension exponents |
| `kind` | enum | no | `quantity`, `category`, `boolean`, `structural`, or `timepoint` |
| `common_alternatives` | list | no | Unit conversions (see below) |
| `extra_units` | list | no | Domain-specific units not in pint |

The schema enforces `additionalProperties: false` -- no extra fields are permitted. Schema definition: `schema/generated/form.schema.json`.

37 forms ship with propstore in `propstore/_resources/forms/`. Examples:

- **frequency** -- `dimensions: {T: -1}`, `unit_symbol: Hz`
- **force** -- `dimensions: {M: 1, L: 1, T: -2}`, `unit_symbol: N`
- **temperature** -- `dimensions: {Theta: 1}`, `unit_symbol: K`
- **gravitational_param** -- `dimensions: {L: 3, M: -1, T: -2}`, `unit_symbol: "m^3/(kg*s^2)"`
- **ratio** -- minimal: just `name: ratio`, no dimensions, no unit_symbol (treated as dimensionless by heuristic)

Dimensionless forms (ratio, score, amplitude_ratio, boolean, category, etc.) have no physical dimensions and do not participate in unit conversion.

## Temporal Forms (Timepoint)

The `timepoint` kind represents temporal positions as epoch seconds (UTC). It is semantically distinct from `quantity`: both map to `z3.Real` for constraint solving, but timepoints are not valid for parameterization or dimensional algebra (you cannot derive a temperature from a timepoint via bridgman).

The shipped `timepoint.yaml` form:

```yaml
name: timepoint
kind: timepoint
dimensionless: true
```

### Authoring temporal concepts

Define concepts with `form: timepoint`. By convention, interval endpoints use `_from` / `_until` suffixes:

```yaml
canonical_name: valid_from
form: timepoint

canonical_name: valid_until
form: timepoint
```

### Temporal CEL conditions on claims

Use standard CEL numeric comparisons to scope claims temporally:

```
valid_from >= 1609459200
valid_until <= 1640995200
```

These constrain the claim's validity to the year 2021 (epoch seconds). Temporal conditions compose freely with non-temporal conditions (`temperature > 300 && valid_from >= 1609459200`).

### Temporal conditions on contexts (McCarthy's specialize-time)

Following McCarthy (1993), temporal specialization is context specialization. A context with temporal conditions narrows the time window in which its propositions hold:

```yaml
conditions:
  - "valid_from >= 1609459200"
  - "valid_until <= 1640995200"
```

This is equivalent to McCarthy's `ist(specialize-time(c, 2021), p)` -- the proposition `p` holds in context `c` restricted to the year 2021.

### Automatic interval ordering

When the CEL registry contains TIMEPOINT concepts forming an interval pair (names ending in `_from` and `_until` with a matching prefix), the Z3 solver automatically adds `from_var <= until_var`. This prevents nonsensical inverted intervals (e.g. `valid_from=300, valid_until=100`) and is required for correct disjointness detection.

The detection is prefix-based, so custom interval pairs like `experiment_from` / `experiment_until` get the same constraint automatically.

### Temporal disjointness (Allen 1983)

Two claims with non-overlapping temporal scopes are non-conflicting. The Z3 solver detects this via UNSAT of the conjunction:

- Claim A: `valid_from >= 100 && valid_until <= 200`
- Claim B: `valid_from >= 300 && valid_until <= 400`

These are disjoint because no assignment can satisfy both condition sets while maintaining `valid_from <= valid_until`. This encodes Allen's `before` relation (`e1 < s2`) as Z3 real arithmetic.

See [conflict-detection.md](conflict-detection.md) for full details on Z3 disjointness checking.

## Dimensional Signatures

The `dimensions` dict maps SI base dimension symbols to integer exponents:

| Symbol | SI Base Quantity |
|--------|-----------------|
| `L` | Length |
| `M` | Mass |
| `T` | Time |
| `I` | Electric current |
| `Theta` | Temperature |
| `N` | Amount of substance |
| `J` | Luminous intensity |

Domain-specific keys (`Currency`, `Quantity`) are also permitted by the schema.

`dims_signature()` (`form_utils.py`) produces a canonical string representation by stripping zero exponents and sorting by key:

- Force: `"L:1,M:1,T:-2"`
- Frequency: `"T:-1"`
- Dimensionless: `""`
- Missing dimensions: `None`

This canonical form is used for dimensional equality checks and form lookup by dimensions.

## Unit Conversions

Forms declare alternative units via `common_alternatives`. Each entry specifies a conversion type and the parameters needed to convert between the alternative unit and the SI unit.

### Multiplicative

`si_value = raw * multiplier`

The simplest conversion -- a linear scaling factor. Example from `frequency.yaml`:

```yaml
common_alternatives:
  - unit: kHz
    type: multiplicative
    multiplier: 1000
  - unit: MHz
    type: multiplicative
    multiplier: 1000000
  - unit: GHz
    type: multiplicative
    multiplier: 1000000000
```

### Affine

`si_value = raw * multiplier + offset`

Used for temperature scales with non-zero offsets. Handled by pint for the actual conversion. Example from `temperature.yaml`:

```yaml
common_alternatives:
  - unit: degC
    type: affine
    multiplier: 1.0
    offset: 273.15
  - unit: degF
    type: affine
    multiplier: 0.5556
    offset: 255.372
```

### Logarithmic

`si_value = reference * base^(raw / divisor)`

Used for decibel scales and other logarithmic units. This conversion is **not** handled by pint -- propstore computes it explicitly in `normalize_to_si()` and `from_si()` before the pint fallthrough. Example from `sound_pressure_level.yaml`:

```yaml
common_alternatives:
  - unit: dB_SPL
    type: logarithmic
    base: 10
    divisor: 20
    reference: 0.00002
```

The inverse is `raw = divisor * log_base(si_value / reference)`.

### extra_units

Domain-specific units not recognized by pint can be declared via the `extra_units` field. Each entry has a `symbol` and optionally `dimensions`. These are added to `FormDefinition.allowed_units` and registered into the bridgman symbol table via `register_form_units()` in `unit_dimensions.py`. No shipped form currently uses `extra_units` -- it exists for user-defined forms.

### Pint Integration

A single global pint registry (`form_utils.py`) handles all standard unit conversions. Pint automatically supports SI prefix combinations (THz, kPa, etc.) even without explicit `common_alternatives` entries, affine offset conversions for temperature, and compound unit expressions. The alias mapping `_PINT_ALIASES` translates propstore unit symbols to pint-recognized names (e.g. `degC`, `degF`, `micro`).

## SI Normalization

At build time, every numeric claim is normalized to SI units. The sidecar's `claim_numeric_payload` table stores three computed columns: `value_si`, `lower_bound_si`, and `upper_bound_si`.

The normalization pipeline in `_prepare_claim_row()` (`build_sidecar.py`):

1. Start with the raw typed values from the claim
2. Look up the claim's concept, then its form, then the `FormDefinition`
3. If a form definition exists, call `normalize_to_si(value, unit, form_def)` for value, lower_bound, and upper_bound
4. On conversion failure (unknown unit, non-numeric value), fall back to raw values

`normalize_to_si()` (`form_utils.py`):

1. If the unit is `None` or matches the SI `unit_symbol`, return the raw value
2. If the unit has an explicit logarithmic conversion, compute `reference * base^(raw / divisor)`
3. Otherwise, delegate to pint: `ureg.Quantity(value, unit).to(si_unit).magnitude`

The inverse function `from_si()` follows the same pattern for display purposes.

SI normalization enables unit-agnostic comparison and conflict detection. The CLI displays both values when they differ: `"value=200 kHz (SI: 200000 Hz)"`.

## Form Algebra

Form algebra captures how forms compose through parameterization expressions. If a concept has a parameterization relationship like `force = mass * acceleration`, the form algebra records that the `force` form is produced by multiplying `mass` and `acceleration` forms.

### Table Schema

```sql
CREATE TABLE form_algebra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    output_form TEXT NOT NULL,
    input_forms TEXT NOT NULL,        -- JSON array of form names
    operation TEXT NOT NULL,           -- sympy expression with form names
    source_concept_id TEXT,
    source_formula TEXT,              -- human-readable formula
    dim_verified INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (output_form) REFERENCES form(name)
);
```

### Auto-derivation

During sidecar build, `_populate_form_algebra()` (`build_sidecar.py`) processes every concept with `parameterization_relationships`:

1. Resolve all input concept IDs to form names via `id_to_form` lookup
2. Substitute concept IDs with form names in the sympy expression
3. Validate dimensions with bridgman's `verify_expr()` -- sets `dim_verified=0` if invalid
4. Deduplicate by `(output_form, sorted(input_forms), canonical_operation)`
5. Insert into the `form_algebra` table

### Queries

`WorldModel` (`propstore/world/model.py`) provides two query methods:

- `form_algebra_for(form_name)` -- returns all entries where `output_form` matches: "what decomposes into this form?"
- `form_algebra_using(form_name)` -- returns all entries where the form appears in `input_forms`: "where is this form used as an input?"
- `forms_by_dimensions(dims)` -- returns all forms matching the given dimension signature, using `bridgman.dims_equal()`.

## Dimensional Analysis (Bridgman)

The `bridgman` library provides dimensional analysis functions used across four subsystems:

**Dimensional equality** (`unit_dimensions.py`): `dims_equal(unit_dims, form_dims)` checks whether two dimension dicts are equal, treating missing keys as exponent 0.

**Concept validation** (`validate.py`): Two-tier dimensional compatibility checking. First tries sympy-based `verify_expr()` for tree-walking dimensional verification. Falls back to brute-force multiplication/division combinations using `mul_dims` and `div_dims`.

**Claim validation** (`validate_claims.py`): Uses `verify_expr()` to check dimensional consistency of equation claims.

**Form algebra verification** (`build_sidecar.py`): Uses `verify_expr()` during sidecar build to validate form algebra entries, setting the `dim_verified` flag.

**CLI display** (`cli/form.py`): Uses `dims_equal()` for filtering forms by dimensions and `format_dims()` for human-readable output (e.g. `"M*L*T^-2"`).

The `--strict` flag on import commands enables pre-check dimensional validation via bridgman before claims enter the store.

## CLI Usage

```bash
# List all forms
pks form list

# List forms with dimensions displayed
pks form list --show-dims

# Filter forms by dimensional signature
pks form list --dims M:1,L:1,T:-2 --show-dims

# Show a form's definition, conversions, and algebra
pks form show frequency

# Add a custom form
pks form add --name custom_unit --unit "m/s^2" --dimensions '{"L":1,"T":-2}'

# Remove a form (checks for referencing concepts, requires --force if any exist)
pks form remove custom_unit

# Validate form definitions against schema
pks form validate
pks form validate frequency
```

`pks form show` dumps the raw YAML, appends a unit conversions section listing each `common_alternative` with its type and parameters, and -- when a sidecar exists -- appends a form algebra section showing decompositions and uses.

## How It Connects

- **Data model** defines concepts with a `form` field referencing form definitions. See [data-model.md](data-model.md).
- **Parameterization** uses form algebra to verify dimensional consistency of symbolic equations. See [parameterization.md](parameterization.md).
- **Conflict detection** relies on SI-normalized values for unit-agnostic comparison. See [conflict-detection.md](conflict-detection.md).
