"""Extract all concept names from claims.yaml files and build frequency table."""
import yaml
import json
from pathlib import Path
from collections import defaultdict

papers_dir = Path("C:/Users/Q/code/propstore/papers")
concept_papers = defaultdict(set)  # concept_name -> set of papers
concept_count = defaultdict(int)   # concept_name -> total occurrences
concept_sources = defaultdict(list)  # concept_name -> list of (paper, claim_id, field)

for claims_file in sorted(papers_dir.glob("*/claims.yaml")):
    paper_name = claims_file.parent.name
    try:
        data = yaml.safe_load(claims_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR reading {claims_file}: {e}")
        continue

    if not data or "claims" not in data:
        print(f"SKIP {paper_name}: no claims")
        continue

    for claim in data["claims"]:
        claim_id = claim.get("id", "?")

        # Extract from concepts list
        if "concepts" in claim and isinstance(claim["concepts"], list):
            for c in claim["concepts"]:
                if isinstance(c, str):
                    concept_papers[c].add(paper_name)
                    concept_count[c] += 1
                    concept_sources[c].append((paper_name, claim_id, "concepts"))

        # Extract from label field (used in Dung, Modgil, Clark, etc.)
        if "label" in claim and isinstance(claim["label"], str):
            label = claim["label"]
            concept_papers[label].add(paper_name)
            concept_count[label] += 1
            concept_sources[label].append((paper_name, claim_id, "label"))

        # Extract from parameters/variables with concept field
        for param_field in ["parameters", "variables"]:
            if param_field in claim and isinstance(claim[param_field], list):
                for param in claim[param_field]:
                    if isinstance(param, dict) and "concept" in param:
                        c = param["concept"]
                        if isinstance(c, str):
                            concept_papers[c].add(paper_name)
                            concept_count[c] += 1
                            concept_sources[c].append((paper_name, claim_id, f"{param_field}.concept"))

        # Extract from target_concept
        if "target_concept" in claim and isinstance(claim["target_concept"], str):
            c = claim["target_concept"]
            concept_papers[c].add(paper_name)
            concept_count[c] += 1
            concept_sources[c].append((paper_name, claim_id, "target_concept"))

# Output results
print(f"Total unique concept names: {len(concept_papers)}")
print(f"Total concept references: {sum(concept_count.values())}")
print(f"Papers scanned: {len(list(papers_dir.glob('*/claims.yaml')))}")
print()

# Sort by frequency
sorted_concepts = sorted(concept_papers.keys())

# Output as JSON for further processing
output = {}
for c in sorted_concepts:
    output[c] = {
        "count": concept_count[c],
        "papers": sorted(concept_papers[c]),
        "sources": concept_sources[c]
    }

out_path = Path("C:/Users/Q/code/propstore/scripts/concept_inventory.json")
out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
print(f"Wrote inventory to {out_path}")

# Print all concepts grouped by first token
print("\n=== ALL CONCEPTS (alphabetical) ===")
for c in sorted_concepts:
    papers = sorted(concept_papers[c])
    print(f"  {c} ({concept_count[c]}x, {len(papers)} papers: {', '.join(papers[:3])}{'...' if len(papers) > 3 else ''})")
