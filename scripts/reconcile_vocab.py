"""
Vocabulary reconciliation: identify true duplicates, merge them, report results.

True duplicates are concept names that refer to the same underlying concept
but use different naming conventions. We distinguish these from pairs where
one concept is a specialization of another (those stay separate).
"""
import yaml
import json
from pathlib import Path
from collections import defaultdict
from copy import deepcopy

papers_dir = Path("C:/Users/Q/code/propstore/papers")
inventory_path = Path("C:/Users/Q/code/propstore/scripts/concept_inventory.json")
inventory = json.loads(inventory_path.read_text(encoding="utf-8"))

# ============================================================
# MERGE DECISIONS
# Each entry: (canonical, alias, reason)
# These are cases where two names refer to the SAME concept.
# ============================================================
MERGES = [
    # Singular/plural normalization
    ("argumentation_scheme", "argumentation_schemes",
     "Plural variant of same concept; Walton uses singular, Prakken uses plural"),
    ("claim_lineage", "claim_lineages",
     "Plural variant of same concept in same paper (Clark 2014)"),

    # Prefix-qualified variants of same concept
    ("belief_revision", "agm_belief_revision",
     "AGM belief revision IS belief revision - the AGM prefix just names the framework authors. "
     "Both refer to the same operation. Papers using 'agm_belief_revision' (Dixon, Shapiro) and "
     "'belief_revision' (Martins, Reiter, Shapiro) discuss the same concept."),

    # Paper-specific label vs general concept where same paper has both
    ("three_attack_types", "three_attack_types_full",
     "Modgil 2014 uses 'three_attack_types', Modgil 2018 uses 'three_attack_types_full' - "
     "same concept (undermining/rebutting/undercutting), the '_full' suffix is a paper-label artifact"),
    ("last_link_ordering", "last_link_ordering_full",
     "Modgil 2014 vs 2018 naming - same ordering principle, '_full' is label artifact"),
    ("weakest_link_ordering", "weakest_link_ordering_full",
     "Modgil 2014 vs 2018 naming - same ordering principle, '_full' is label artifact"),
    ("contrariness_function", "contrariness_function_generalization",
     "Modgil 2014 defines it, Modgil 2018 generalizes it - but the label refers to the same function concept"),

    # Rebutting/undercutting defeat/defeater are the same concept
    ("rebutting_defeat", "rebutting_defeater",
     "Same concept - 'defeat' and 'defeater' both refer to the rebutting defeat relation. "
     "Prakken/Clark/Walton use 'defeat', Pollock uses 'defeater'"),
    ("undercutting_defeat", "undercutting_defeater",
     "Same concept - Prakken/Clark/Walton use 'defeat', Pollock uses 'defeater'"),

    # ASPIC+ naming variants
    ("aspic_plus", "aspic_plus_full_system",
     "Both refer to the ASPIC+ framework - Odekerken uses 'aspic_plus', Modgil 2018 uses "
     "'aspic_plus_full_system' as a label for the complete definition"),

    # Fundamental lemma
    ("fundamental_lemma", "fundamental_lemma_holds",
     "Same concept - Dung 1995 defines it as 'fundamental_lemma', "
     "Modgil 2018 labels the claim that it holds for their system"),

    # Context switching
    ("context_switching", "context_switching_elimination",
     "Both discuss the same concept of context switching in TMS/ATMS. "
     "Dixon uses 'context_switching', deKleer uses 'context_switching_elimination' to describe "
     "how ATMS eliminates the need for it - but the concept referenced is the same"),

    # TMS node types
    ("tms_node", "in_node",
     "NOT MERGING - in_node is a specific state of a tms_node"),
]

# Filter out the last entry (which was a note-to-self)
MERGES = [m for m in MERGES if not m[2].startswith("NOT MERGING")]

# ============================================================
# KEPT DISTINCT decisions (documenting why similar pairs are NOT merged)
# ============================================================
KEPT_DISTINCT = [
    ("belief_maintenance_system", "belief_maintenance_system_architecture",
     "BMS is the system concept; architecture is specifically about how it's structured"),
    ("non_monotonic_reasoning", "non_monotonic_reasoning_elegance",
     "The 'elegance' variant refers to a specific claim about TMS handling NMR elegantly"),
    ("stable_extension", "stable_extension_baf",
     "Different definitions - Dung's stable extension vs Cayrol's BAF-specific variant"),
    ("stable_extension", "stable_extension_characterization",
     "Extension is the concept; characterization is a theorem about it"),
    ("characteristic_function", "admissible_characteristic_function",
     "General F_AF vs admissible-specific variant in Dung's paper"),
    ("belief_revision", "belief_revision_system",
     "The concept vs a system that implements it"),
    ("belief_space", "current_belief_space",
     "General concept vs the specific active/current one"),
    ("knowledge_base", "knowledge_base_definition",
     "The concept vs the formal definition claim label"),
    ("oscar_system", "oscar_system_architecture",
     "The system vs its specific architecture"),
    ("truth_function", "closed_truth_function",
     "General concept vs specific closed variant in Ginsberg"),
    ("truth_function", "reduced_truth_function",
     "General concept vs specific reduced variant in Ginsberg"),
    ("well_founded", "well_founded_justification",
     "General property vs specific TMS justification type"),
    ("well_founded", "well_founded_support",
     "General property vs specific support relation"),
    ("well_founded", "well_founded_framework",
     "General property vs Dung's specific framework type"),
    ("inference_rules", "defeasible_inference_rules",
     "General inference rules vs specifically defeasible ones"),
    ("partial_order", "strict_partial_order",
     "Partial order allows equality; strict does not - mathematically distinct"),
    ("and_operator", "and_operator_belief",
     "The logical AND vs its belief-interval computation"),
    ("not_operator", "not_operator_belief",
     "The logical NOT vs its belief-interval computation"),
    ("invertible_link", "invertible_support_link",
     "These may be the same but appear in different contexts within Falkenhainer"),
    ("propagation_threshold", "propagation_delta_threshold",
     "Different thresholds - one for absolute belief, one for change delta"),
    ("context_switching", "context_switching_cost",
     "The mechanism vs its computational cost"),
    ("exponential_growth", "exponential_label_growth",
     "General exponential growth vs specifically label-set growth in ATMS"),
    ("data_pool", "data_pool_mechanism",
     "The data structure vs the mechanism that operates on it"),
    ("preferred_extension", "preferred_extension_existence",
     "The concept vs the theorem that one always exists"),
    ("citation_network", "citation_network_size",
     "The network vs a measurement of its size"),
    ("grant_proposal", "grant_proposal_distortions",
     "The document type vs distortions found in them"),
    ("fixed_point", "fixed_point_operator",
     "The mathematical object vs the operator that computes it"),
    ("statistical_syllogism", "statistical_syllogism_undercutter",
     "The reasoning pattern vs its specific undercutter"),
    ("hard_support_link", "invertible_support_link",
     "Genuinely different BMS link types - hard cannot retract, invertible can"),
    ("dempster_rule", "dempster_rule_simplified",
     "Full Dempster's rule vs simplified version for BMS"),
    ("rationality_postulate_direct_consistency", "rationality_postulate_indirect_consistency",
     "Two different rationality postulates - direct vs indirect"),
    ("last_link_ordering", "weakest_link_ordering",
     "Different argument ordering principles in ASPIC+ - last link looks at top rule, weakest link at all rules"),
    ("argument_component", "argument_component_detection",
     "The NLP entity type vs the detection task"),
    ("claim", "claim_lineage",
     "A claim vs the provenance chain of a claim"),
    ("rct_dataset", "rct_dataset_statistics",
     "The dataset vs descriptive statistics about it"),
    ("sequence_tagging", "sequence_tagging_hyperparameters",
     "The NLP technique vs its specific hyperparameter settings"),
]

# ============================================================
# Apply merges to claims.yaml files
# ============================================================
# Build alias -> canonical map
alias_to_canonical = {}
for canonical, alias, reason in MERGES:
    alias_to_canonical[alias] = canonical

modified_files = []

for claims_file in sorted(papers_dir.glob("*/claims.yaml")):
    paper_name = claims_file.parent.name
    text = claims_file.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    if not data or "claims" not in data:
        continue

    changed = False
    for claim in data["claims"]:
        # Fix concepts lists
        if "concepts" in claim and isinstance(claim["concepts"], list):
            new_concepts = []
            for c in claim["concepts"]:
                if isinstance(c, str) and c in alias_to_canonical:
                    new_concepts.append(alias_to_canonical[c])
                    changed = True
                else:
                    new_concepts.append(c)
            claim["concepts"] = new_concepts

        # Fix label field
        if "label" in claim and isinstance(claim["label"], str):
            if claim["label"] in alias_to_canonical:
                claim["label"] = alias_to_canonical[claim["label"]]
                changed = True

        # Fix parameters/variables concept fields
        for param_field in ["parameters", "variables"]:
            if param_field in claim and isinstance(claim[param_field], list):
                for param in claim[param_field]:
                    if isinstance(param, dict) and "concept" in param:
                        if isinstance(param["concept"], str) and param["concept"] in alias_to_canonical:
                            param["concept"] = alias_to_canonical[param["concept"]]
                            changed = True

        # Fix target_concept
        if "target_concept" in claim and isinstance(claim["target_concept"], str):
            if claim["target_concept"] in alias_to_canonical:
                claim["target_concept"] = alias_to_canonical[claim["target_concept"]]
                changed = True

    if changed:
        # Write back with yaml
        with open(claims_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
        modified_files.append(str(claims_file))
        print(f"MODIFIED: {paper_name}/claims.yaml")

# ============================================================
# Recount after merges
# ============================================================
concept_papers_after = defaultdict(set)
concept_count_after = defaultdict(int)

for claims_file in sorted(papers_dir.glob("*/claims.yaml")):
    paper_name = claims_file.parent.name
    data = yaml.safe_load(claims_file.read_text(encoding="utf-8"))
    if not data or "claims" not in data:
        continue
    for claim in data["claims"]:
        if "concepts" in claim and isinstance(claim["concepts"], list):
            for c in claim["concepts"]:
                if isinstance(c, str):
                    concept_papers_after[c].add(paper_name)
                    concept_count_after[c] += 1
        if "label" in claim and isinstance(claim["label"], str):
            concept_papers_after[claim["label"]].add(paper_name)
            concept_count_after[claim["label"]] += 1
        for pf in ["parameters", "variables"]:
            if pf in claim and isinstance(claim[pf], list):
                for p in claim[pf]:
                    if isinstance(p, dict) and "concept" in p and isinstance(p["concept"], str):
                        concept_papers_after[p["concept"]].add(paper_name)
                        concept_count_after[p["concept"]] += 1
        if "target_concept" in claim and isinstance(claim["target_concept"], str):
            concept_papers_after[claim["target_concept"]].add(paper_name)
            concept_count_after[claim["target_concept"]] += 1

print(f"\n=== RESULTS ===")
print(f"Concepts before: 754")
print(f"Concepts after: {len(concept_papers_after)}")
print(f"Merges applied: {len(MERGES)}")
print(f"Files modified: {len(modified_files)}")
for f in modified_files:
    print(f"  {f}")

# Output merge details for report
print(f"\n=== MERGE DETAILS ===")
for canonical, alias, reason in MERGES:
    print(f"  {alias} -> {canonical}: {reason}")

# Write results for report generation
results = {
    "before_count": 754,
    "after_count": len(concept_papers_after),
    "merges": [{"canonical": c, "alias": a, "reason": r} for c, a, r in MERGES],
    "kept_distinct": [{"a": a, "b": b, "reason": r} for a, b, r in KEPT_DISTINCT],
    "modified_files": modified_files,
}
results_path = Path("C:/Users/Q/code/propstore/scripts/reconciliation_results.json")
results_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
print(f"\nResults written to {results_path}")
