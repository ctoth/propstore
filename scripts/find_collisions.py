"""Find collision groups among concept names using token overlap similarity."""
import json
from pathlib import Path
from collections import defaultdict
from itertools import combinations

inventory_path = Path("C:/Users/Q/code/propstore/scripts/concept_inventory.json")
inventory = json.loads(inventory_path.read_text(encoding="utf-8"))

concepts = sorted(inventory.keys())
print(f"Total concepts: {len(concepts)}")

# === Strategy 1: Exact substring/prefix match (one is prefix/suffix of another) ===
prefix_groups = []
seen_in_prefix = set()
for i, a in enumerate(concepts):
    for b in concepts[i+1:]:
        # Check if one is a substring of the other (not just prefix)
        if a in b or b in a:
            # Only flag if they share significant overlap
            shorter = a if len(a) <= len(b) else b
            longer = b if len(a) <= len(b) else a
            # The shorter must be at least 60% of the longer
            if len(shorter) / len(longer) >= 0.5:
                prefix_groups.append((a, b))
                seen_in_prefix.add(a)
                seen_in_prefix.add(b)

# === Strategy 2: Singular/plural variants ===
plural_groups = []
for c in concepts:
    if c.endswith('s') and c[:-1] in inventory:
        plural_groups.append((c[:-1], c))
    # Also check _ies -> _y
    if c.endswith('ies'):
        singular = c[:-3] + 'y'
        if singular in inventory:
            plural_groups.append((singular, c))

# === Strategy 3: Token overlap similarity ===
def token_sim(a, b):
    ta = set(a.split('_'))
    tb = set(b.split('_'))
    if not ta or not tb:
        return 0.0
    intersection = ta & tb
    union = ta | tb
    return len(intersection) / len(union)

# Only check pairs with at least one shared token (optimization)
token_to_concepts = defaultdict(list)
for c in concepts:
    for tok in c.split('_'):
        if len(tok) > 2:  # skip very short tokens
            token_to_concepts[tok].append(c)

high_sim_pairs = []
checked = set()
for tok, members in token_to_concepts.items():
    if len(members) > 50:  # skip extremely common tokens
        continue
    for i, a in enumerate(members):
        for b in members[i+1:]:
            pair = (min(a,b), max(a,b))
            if pair in checked:
                continue
            checked.add(pair)
            sim = token_sim(a, b)
            if sim >= 0.6 and a != b:
                high_sim_pairs.append((a, b, sim))

high_sim_pairs.sort(key=lambda x: -x[2])

# === Strategy 4: Same concept across papers with different naming ===
# Find concepts that appear in only 1 paper and share high token overlap with multi-paper concepts
single_paper = {c for c, v in inventory.items() if len(v["papers"]) == 1}
multi_paper = {c for c, v in inventory.items() if len(v["papers"]) > 1}

cross_paper_candidates = []
for sc in single_paper:
    for mc in multi_paper:
        sim = token_sim(sc, mc)
        if sim >= 0.6:
            cross_paper_candidates.append((sc, mc, sim))

cross_paper_candidates.sort(key=lambda x: -x[2])

# === Build unified collision groups ===
# Use union-find
parent = {c: c for c in concepts}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
def union(a, b):
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb

# Only merge pairs that are very likely duplicates (sim >= 0.75 or substring)
print("\n=== PLURAL PAIRS ===")
for a, b in plural_groups:
    print(f"  {a} <-> {b}")
    papers_a = set(inventory[a]["papers"])
    papers_b = set(inventory[b]["papers"])
    # Only merge if they don't co-occur in same paper (co-occurrence suggests distinct)
    if not (papers_a & papers_b):
        union(a, b)

print("\n=== SUBSTRING PAIRS (>= 50% length ratio) ===")
for a, b in prefix_groups:
    papers_a = set(inventory[a]["papers"])
    papers_b = set(inventory[b]["papers"])
    sim = token_sim(a, b)
    if sim >= 0.6:
        print(f"  {a} <-> {b} (token_sim={sim:.2f})")

print("\n=== HIGH TOKEN SIMILARITY PAIRS (>= 0.75) ===")
for a, b, sim in high_sim_pairs:
    if sim >= 0.75:
        print(f"  {a} <-> {b} (sim={sim:.2f})")

print("\n=== HIGH TOKEN SIMILARITY PAIRS (0.6-0.75) ===")
for a, b, sim in high_sim_pairs:
    if 0.6 <= sim < 0.75:
        print(f"  {a} <-> {b} (sim={sim:.2f})")

print("\n=== CROSS-PAPER CANDIDATES (single->multi, sim >= 0.6) ===")
for sc, mc, sim in cross_paper_candidates[:30]:
    print(f"  {sc} ({inventory[sc]['papers']}) <-> {mc} ({inventory[mc]['papers']}) sim={sim:.2f}")

# Summary stats
groups = defaultdict(list)
for c in concepts:
    groups[find(c)].append(c)
non_trivial = {k: v for k, v in groups.items() if len(v) > 1}
print(f"\n=== SUMMARY ===")
print(f"Total concepts: {len(concepts)}")
print(f"Auto-merged groups (plural only, no co-occurrence): {len(non_trivial)}")
for canonical, members in sorted(non_trivial.items()):
    print(f"  {canonical}: {members}")
