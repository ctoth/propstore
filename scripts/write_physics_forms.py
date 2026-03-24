"""Write enriched and new physics form YAML files to forms/ directory."""
from pathlib import Path
import yaml

forms_dir = Path(__file__).parent.parent / "forms"

# All forms: existing ones get enriched, new ones get created
forms = {
    # === Enriching existing bare stubs ===
    "pressure": {
        "name": "pressure",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "Pa",
        "dimensions": {"M": 1, "L": -1, "T": -2},
        "common_alternatives": [
            {"unit": "atm", "type": "multiplicative", "multiplier": 101325},
            {"unit": "bar", "type": "multiplicative", "multiplier": 100000},
            {"unit": "psi", "type": "multiplicative", "multiplier": 6894.76},
        ],
    },
    "frequency": {
        "name": "frequency",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "Hz",
        "dimensions": {"T": -1},
        "common_alternatives": [
            {"unit": "kHz", "type": "multiplicative", "multiplier": 1000},
            {"unit": "MHz", "type": "multiplicative", "multiplier": 1000000},
            {"unit": "GHz", "type": "multiplicative", "multiplier": 1000000000},
        ],
    },
    "time": {
        "name": "time",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "s",
        "dimensions": {"T": 1},
        "common_alternatives": [
            {"unit": "ms", "type": "multiplicative", "multiplier": 0.001},
            {"unit": "min", "type": "multiplicative", "multiplier": 60},
            {"unit": "h", "type": "multiplicative", "multiplier": 3600},
        ],
    },
    "rate": {
        "name": "rate",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "1/s",
        "dimensions": {"T": -1},
    },
    # === New physics forms ===
    "mass": {
        "name": "mass",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "kg",
        "dimensions": {"M": 1},
        "common_alternatives": [
            {"unit": "g", "type": "multiplicative", "multiplier": 0.001},
            {"unit": "mg", "type": "multiplicative", "multiplier": 0.000001},
            {"unit": "t", "type": "multiplicative", "multiplier": 1000},
        ],
    },
    "force": {
        "name": "force",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "N",
        "dimensions": {"M": 1, "L": 1, "T": -2},
        "common_alternatives": [
            {"unit": "kN", "type": "multiplicative", "multiplier": 1000},
            {"unit": "dyn", "type": "multiplicative", "multiplier": 0.00001},
        ],
    },
    "acceleration": {
        "name": "acceleration",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "m/s\u00b2",
        "dimensions": {"L": 1, "T": -2},
    },
    "velocity": {
        "name": "velocity",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "m/s",
        "dimensions": {"L": 1, "T": -1},
        "common_alternatives": [
            {"unit": "km/h", "type": "multiplicative", "multiplier": 0.277778},
            {"unit": "km/s", "type": "multiplicative", "multiplier": 1000},
        ],
    },
    "distance": {
        "name": "distance",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "m",
        "dimensions": {"L": 1},
        "common_alternatives": [
            {"unit": "km", "type": "multiplicative", "multiplier": 1000},
            {"unit": "cm", "type": "multiplicative", "multiplier": 0.01},
            {"unit": "mm", "type": "multiplicative", "multiplier": 0.001},
            {"unit": "AU", "type": "multiplicative", "multiplier": 149597870700},
        ],
    },
    "energy": {
        "name": "energy",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "J",
        "dimensions": {"M": 1, "L": 2, "T": -2},
        "common_alternatives": [
            {"unit": "kJ", "type": "multiplicative", "multiplier": 1000},
            {"unit": "eV", "type": "multiplicative", "multiplier": 1.602176634e-19},
            {"unit": "erg", "type": "multiplicative", "multiplier": 1e-7},
        ],
    },
    "momentum": {
        "name": "momentum",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "kg\u00b7m/s",
        "dimensions": {"M": 1, "L": 1, "T": -1},
    },
    "power": {
        "name": "power",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "W",
        "dimensions": {"M": 1, "L": 2, "T": -3},
        "common_alternatives": [
            {"unit": "kW", "type": "multiplicative", "multiplier": 1000},
            {"unit": "MW", "type": "multiplicative", "multiplier": 1000000},
            {"unit": "hp", "type": "multiplicative", "multiplier": 745.7},
        ],
    },
    "temperature": {
        "name": "temperature",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "K",
        "dimensions": {"\u0398": 1},
        "common_alternatives": [
            {"unit": "\u00b0C", "type": "affine", "multiplier": 1, "offset": 273.15},
        ],
    },
    "volume": {
        "name": "volume",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "m\u00b3",
        "dimensions": {"L": 3},
        "common_alternatives": [
            {"unit": "L", "type": "multiplicative", "multiplier": 0.001},
            {"unit": "mL", "type": "multiplicative", "multiplier": 0.000001},
        ],
    },
    "amount": {
        "name": "amount",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "mol",
        "dimensions": {"N": 1},
    },
    "density": {
        "name": "density",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "kg/m\u00b3",
        "dimensions": {"M": 1, "L": -3},
    },
    "electric_potential": {
        "name": "electric_potential",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "V",
        "dimensions": {"M": 1, "L": 2, "T": -3, "I": -1},
        "common_alternatives": [
            {"unit": "mV", "type": "multiplicative", "multiplier": 0.001},
            {"unit": "kV", "type": "multiplicative", "multiplier": 1000},
        ],
    },
    "resistance": {
        "name": "resistance",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "\u03a9",
        "dimensions": {"M": 1, "L": 2, "T": -3, "I": -2},
        "common_alternatives": [
            {"unit": "k\u03a9", "type": "multiplicative", "multiplier": 1000},
            {"unit": "M\u03a9", "type": "multiplicative", "multiplier": 1000000},
        ],
    },
    "electric_current": {
        "name": "electric_current",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "A",
        "dimensions": {"I": 1},
        "common_alternatives": [
            {"unit": "mA", "type": "multiplicative", "multiplier": 0.001},
        ],
    },
    "charge": {
        "name": "charge",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "C",
        "dimensions": {"I": 1, "T": 1},
    },
    "area": {
        "name": "area",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "m\u00b2",
        "dimensions": {"L": 2},
    },
    "gravitational_param": {
        "name": "gravitational_param",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "m\u00b3/(kg\u00b7s\u00b2)",
        "dimensions": {"L": 3, "M": -1, "T": -2},
        "note": "Form for the gravitational constant G and similar quantities with dimensions L3 M-1 T-2.",
    },
    "molar_energy_per_temperature": {
        "name": "molar_energy_per_temperature",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "J/(mol\u00b7K)",
        "dimensions": {"M": 1, "L": 2, "T": -2, "N": -1, "\u0398": -1},
        "note": "Form for the molar gas constant R and similar thermodynamic quantities.",
    },
    "electric_permittivity": {
        "name": "electric_permittivity",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "F/m",
        "dimensions": {"I": 2, "T": 4, "M": -1, "L": -3},
        "note": "Form for vacuum permittivity (epsilon_0) and similar quantities.",
    },
    "magnetic_permeability": {
        "name": "magnetic_permeability",
        "kind": "quantity",
        "dimensionless": False,
        "unit_symbol": "H/m",
        "dimensions": {"M": 1, "L": 1, "T": -2, "I": -2},
        "note": "Form for vacuum permeability (mu_0) and similar quantities.",
    },
}


def write_form(name, data):
    path = forms_dir / f"{name}.yaml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    return path


written = []
for name, data in forms.items():
    p = write_form(name, data)
    written.append(str(p))
    print(f"  wrote {p.name}")

print(f"\nWrote {len(written)} form files")
