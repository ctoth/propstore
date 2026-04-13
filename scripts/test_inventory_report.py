from __future__ import annotations

import argparse
import ast
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestFileStats:
    path: Path
    test_count: int


@dataclass(frozen=True)
class CoverageEntry:
    path: Path
    line_rate: float


def _count_tests(path: Path) -> int:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return 0
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _collect_test_stats(tests_dir: Path) -> list[TestFileStats]:
    stats: list[TestFileStats] = []
    for path in sorted(tests_dir.glob("test_*.py")):
        stats.append(TestFileStats(path=path, test_count=_count_tests(path)))
    return stats


def _parse_coverage_xml(coverage_xml: Path, src_dir: Path) -> list[CoverageEntry]:
    tree = ET.parse(coverage_xml)
    root = tree.getroot()
    entries: list[CoverageEntry] = []
    for cls in root.findall(".//class"):
        filename = cls.attrib.get("filename")
        if not filename:
            continue
        path = Path(filename)
        if not path.is_absolute():
            path = (coverage_xml.parent.parent / filename).resolve()
        try:
            relative = path.resolve().relative_to(src_dir.resolve())
        except ValueError:
            continue
        entries.append(
            CoverageEntry(
                path=src_dir / relative,
                line_rate=float(cls.attrib.get("line-rate", "0")),
            )
        )
    return sorted(entries, key=lambda entry: (entry.line_rate, str(entry.path)))


def _matching_test_files(module_path: Path, test_stats: list[TestFileStats]) -> list[TestFileStats]:
    stem = module_path.stem
    prefix = f"test_{stem}"
    return [stats for stats in test_stats if stats.path.stem == prefix]


def _print_heading(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize test inventory and optional coverage blind spots."
    )
    parser.add_argument(
        "--coverage-xml",
        type=Path,
        help="coverage XML produced by pytest-cov",
    )
    parser.add_argument(
        "--src-dir",
        type=Path,
        default=Path("propstore"),
        help="source directory to inspect",
    )
    parser.add_argument(
        "--tests-dir",
        type=Path,
        default=Path("tests"),
        help="tests directory to inspect",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=20,
        help="maximum rows per section",
    )
    args = parser.parse_args()

    src_dir = args.src_dir.resolve()
    tests_dir = args.tests_dir.resolve()
    test_stats = _collect_test_stats(tests_dir)
    source_files = sorted(src_dir.rglob("*.py"))

    _print_heading("Largest Test Files By Test Count")
    for stats in sorted(test_stats, key=lambda item: item.test_count, reverse=True)[: args.top]:
        print(f"{stats.test_count:4d}  {stats.path.relative_to(Path.cwd())}")

    _print_heading("Source Files With No Direct Matching Test File")
    no_direct_matches = [
        path
        for path in source_files
        if path.name != "__init__.py" and not _matching_test_files(path, test_stats)
    ]
    for path in no_direct_matches[: args.top]:
        print(path.relative_to(Path.cwd()))
    print(f"total: {len(no_direct_matches)}")

    if args.coverage_xml:
        coverage_entries = _parse_coverage_xml(args.coverage_xml.resolve(), src_dir)

        _print_heading("Lowest Coverage Source Files")
        for entry in coverage_entries[: args.top]:
            matching = _matching_test_files(entry.path, test_stats)
            matching_text = ", ".join(stats.path.name for stats in matching) if matching else "no direct match"
            print(
                f"{entry.line_rate * 100:6.2f}%  {entry.path.relative_to(Path.cwd())}  "
                f"[tests: {matching_text}]"
            )

        _print_heading("Many Tests But Low Direct-Match Coverage")
        candidates: list[tuple[int, float, Path]] = []
        for entry in coverage_entries:
            matching = _matching_test_files(entry.path, test_stats)
            if not matching:
                continue
            test_count = sum(stats.test_count for stats in matching)
            if test_count >= 10:
                candidates.append((test_count, entry.line_rate, entry.path))
        for test_count, line_rate, path in sorted(
            candidates,
            key=lambda item: (-item[0], item[1], str(item[2])),
        )[: args.top]:
            print(
                f"{test_count:4d} tests  {line_rate * 100:6.2f}%  "
                f"{path.relative_to(Path.cwd())}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
