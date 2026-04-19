"""Strip max_examples from all @settings decorators in test files.

This is a one-shot migration script for Hypothesis phase 1.
"""
import re
from pathlib import Path

TESTS_DIR = Path(__file__).parent.parent / "tests"


def transform_file(path: Path) -> bool:
    """Transform a single test file. Returns True if modified."""
    original = path.read_text(encoding="utf-8")
    text = original

    # --- Pattern: _PROP_SETTINGS = settings(max_examples=N, deadline=None) ---
    # Rule A applied to module-level alias: strip max_examples, keep deadline=None
    text = re.sub(
        r'_PROP_SETTINGS = settings\(max_examples=\d+, deadline=None\)',
        '_PROP_SETTINGS = settings(deadline=None)',
        text,
    )

    # --- Rule G: stateful tests ---
    # Some stateful test classes assign settings after class creation.
    text = re.sub(
        r'(\.settings = settings\()max_examples=\d+,\s*',
        r'\1',
        text,
    )

    # --- Multi-line @settings with max_examples as first arg ---
    # Pattern:
    #   @settings(
    #       max_examples=N,
    #       deadline=...,
    #       suppress_health_check=[...],
    #   )
    # Remove the max_examples=N, line
    text = re.sub(
        r'(\s*@settings\(\n)\s*max_examples=\d+,\n',
        r'\1',
        text,
    )

    # --- Single-line: @settings(max_examples=N, deadline=None, suppress_health_check=[...]) ---
    # Rule C: keep deadline and suppress_health_check
    text = re.sub(
        r'@settings\(max_examples=\d+, (deadline=[^,)]+, suppress_health_check=\[[^\]]*\])\)',
        r'@settings(\1)',
        text,
    )

    # --- Single-line: @settings(max_examples=N, suppress_health_check=[...]) ---
    # Rule F: keep suppress_health_check only
    text = re.sub(
        r'@settings\(max_examples=\d+, (suppress_health_check=\[[^\]]*\])\)',
        r'@settings(\1)',
        text,
    )

    # --- Single-line: @settings(max_examples=N, deadline=N) where N != None ---
    # Rule D: keep custom deadline
    text = re.sub(
        r'@settings\(max_examples=\d+, (deadline=\d+)\)',
        r'@settings(\1)',
        text,
    )

    # --- Single-line: @settings(max_examples=N, deadline=None) ---
    # Rule A: keep deadline=None
    text = re.sub(
        r'@settings\(max_examples=\d+, deadline=None\)',
        r'@settings(deadline=None)',
        text,
    )

    # --- Single-line: @settings(max_examples=N) with no other args ---
    # Rule B: remove entire decorator line
    text = re.sub(
        r'\n *@settings\(max_examples=\d+\)\n',
        '\n',
        text,
    )

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    modified = []
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        if transform_file(path):
            modified.append(path.name)
            print(f"  Modified: {path.name}")

    print(f"\nTotal files modified: {len(modified)}")

    # Verify: check for remaining max_examples
    remaining = []
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        content = path.read_text(encoding="utf-8")
        if path.name == "conftest.py":
            continue
        for i, line in enumerate(content.splitlines(), 1):
            if "max_examples" in line and "conftest" not in path.name:
                remaining.append(f"  {path.name}:{i}: {line.strip()}")

    if remaining:
        print(f"\nWARNING: {len(remaining)} remaining max_examples references:")
        for r in remaining:
            print(r)
    else:
        print("\nAll max_examples references removed from test files.")


if __name__ == "__main__":
    main()
