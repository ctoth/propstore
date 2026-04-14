from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from propstore.demo import materialize_reasoning_demo


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a small git-backed reasoning demo repository.",
    )
    parser.add_argument("target", type=Path, help="Target knowledge directory")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete the target directory first if it already exists.",
    )
    args = parser.parse_args()

    target = args.target.resolve()
    if target.exists():
        if not args.force:
            raise SystemExit(f"Target already exists: {target}")
        shutil.rmtree(target)

    materialize_reasoning_demo(target)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
