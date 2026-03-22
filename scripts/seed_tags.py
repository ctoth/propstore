#!/usr/bin/env python3
"""Seed papers/tags.yaml from existing tag directories in papers/tagged/."""

from pathlib import Path

import yaml


# Known alias merges: alias -> canonical
ALIAS_MERGES = {
    "non-monotonic-reasoning": "nonmonotonic-reasoning",
}

PAPERS_DIR = Path(__file__).resolve().parent.parent / "papers"
TAGGED_DIR = PAPERS_DIR / "tagged"


def main():
    if not TAGGED_DIR.is_dir():
        print(f"No tagged/ directory at {TAGGED_DIR}")
        return

    # Collect all existing tag directory names
    existing_tags = sorted(
        d.name for d in TAGGED_DIR.iterdir() if d.is_dir()
    )
    print(f"Found {len(existing_tags)} existing tags")

    # Build canonical tag registry
    tags: dict[str, dict] = {}
    alias_targets = set(ALIAS_MERGES.values())

    for tag in existing_tags:
        if tag in ALIAS_MERGES:
            # This tag is an alias — add it under the canonical entry
            canonical = ALIAS_MERGES[tag]
            if canonical not in tags:
                tags[canonical] = {"aliases": []}
            if "aliases" not in tags[canonical]:
                tags[canonical]["aliases"] = []
            tags[canonical]["aliases"].append(tag)
            print(f"  ALIAS: {tag} -> {canonical}")
        else:
            # Canonical tag
            if tag not in tags:
                tags[tag] = {}
            print(f"  canonical: {tag}")

    # Write tags.yaml
    output = {"tags": tags}
    tags_path = PAPERS_DIR / "tags.yaml"
    with open(tags_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

    print(f"\nWrote {tags_path}")
    print(f"  {len(tags)} canonical tags")
    alias_count = sum(len(v.get('aliases', [])) for v in tags.values())
    print(f"  {alias_count} aliases")


if __name__ == "__main__":
    main()
