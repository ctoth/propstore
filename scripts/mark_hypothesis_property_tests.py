from __future__ import annotations

from pathlib import Path


TESTS_DIR = Path("tests")


def _has_property_marker(lines: list[str], given_index: int) -> bool:
    indent = lines[given_index][: len(lines[given_index]) - len(lines[given_index].lstrip())]
    index = given_index - 1
    while index >= 0:
        stripped = lines[index].strip()
        if not stripped:
            index -= 1
            continue
        if not stripped.startswith("@"):
            return False
        if lines[index][: len(lines[index]) - len(lines[index].lstrip())] != indent:
            return False
        if stripped.startswith("@pytest.mark.property"):
            return True
        index -= 1
    return False


def _insert_pytest_import(lines: list[str]) -> list[str]:
    if any(line.rstrip("\r\n") == "import pytest" for line in lines):
        return lines

    insertion_index = 0
    if lines and lines[0].startswith("#!"):
        insertion_index = 1
    if insertion_index < len(lines) and lines[insertion_index].strip().startswith('"""'):
        insertion_index += 1
        while insertion_index < len(lines):
            if lines[insertion_index].strip().endswith('"""'):
                insertion_index += 1
                break
            insertion_index += 1
    while insertion_index < len(lines) and (
        lines[insertion_index].strip() == ""
        or lines[insertion_index].startswith("from __future__ import ")
    ):
        insertion_index += 1
    return [*lines[:insertion_index], "import pytest\n", *lines[insertion_index:]]


def _mark_file(path: Path) -> bool:
    original_text = path.read_bytes().decode("utf-8")
    original = original_text.splitlines(keepends=True)
    if not any(line.lstrip().startswith("@given") for line in original):
        return False

    lines = _insert_pytest_import(original)
    marked: list[str] = []
    changed = lines != original
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("@given") and not _has_property_marker(lines, index):
            indent = line[: len(line) - len(stripped)]
            marked.append(f"{indent}@pytest.mark.property\n")
            changed = True
        marked.append(line)
    if changed:
        path.write_bytes("".join(marked).encode("utf-8"))
    return changed


def main() -> int:
    changed_paths = [
        path for path in sorted(TESTS_DIR.glob("test_*.py")) if _mark_file(path)
    ]
    for path in changed_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
