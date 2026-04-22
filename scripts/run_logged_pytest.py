"""Run pytest while teeing output to a timestamped log file."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def _has_worker_arg(args: list[str]) -> bool:
    return any(arg in {"-n", "--numprocesses"} or arg.startswith("--numprocesses=") for arg in args)


def _default_pytest_args(pytest_args: list[str]) -> list[str]:
    args = ["-vv"]
    if not _has_worker_arg(pytest_args):
        worker_count = min(os.cpu_count() or 1, 16)
        args.extend(["-n", str(worker_count), "--dist", "worksteal"])
    return args


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run pytest and tee output to logs/test-runs.",
    )
    parser.add_argument("--label", default="pytest")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(argv)
    if parsed.pytest_args[:1] == ["--"]:
        parsed.pytest_args = parsed.pytest_args[1:]
    return parsed


def main(argv: list[str] | None = None) -> int:
    parsed = _parse_args(list(sys.argv[1:] if argv is None else argv))
    log_dir = Path("logs") / "test-runs"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = log_dir / f"{parsed.label}-{timestamp}.log"

    command = [
        sys.executable,
        "-m",
        "pytest",
        *_default_pytest_args(parsed.pytest_args),
        *parsed.pytest_args,
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    with log_path.open("w", encoding="utf-8") as log_file:
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="")
            log_file.write(line)

    exit_code = process.wait()
    print(f"LOG_PATH={log_path}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
