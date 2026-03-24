"""Check physgen_units.json for physics-relevant compound units."""
import json
from pathlib import Path

units_path = Path(__file__).parent.parent / "propstore" / "_resources" / "physgen_units.json"
data = json.loads(units_path.read_text())

# Units we need for the physics demo
needed = [
    "m/s", "m/s²", "m²", "m³", "kg·m/s", "kg/m³",
    "N", "J", "Pa", "W", "Hz", "V", "C", "K", "mol", "A",
    "kg", "m", "s", "Ω",
]

print("=== Unit availability ===")
for unit in needed:
    if unit in data:
        print(f"  FOUND: {unit!r} -> {data[unit]}")
    else:
        print(f"  MISSING: {unit!r}")

# Also search for close matches for missing ones
missing = [u for u in needed if u not in data]
if missing:
    print(f"\n=== Close matches for missing units ===")
    for m in missing:
        # Strip special chars and search
        base = m.replace("·", "").replace("/", "").replace("²", "2").replace("³", "3")
        matches = [k for k in data if base.lower() in k.lower() or m.lower() in k.lower()]
        if matches:
            print(f"  {m!r} ~ {matches[:5]}")
        else:
            print(f"  {m!r} ~ no close matches")

print(f"\n=== Total units in lookup: {len(data)} ===")
