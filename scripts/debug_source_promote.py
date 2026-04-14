from __future__ import annotations

from pathlib import Path
import tempfile
import yaml

from click.testing import CliRunner

from propstore.cli import cli
from propstore.cli.repository import Repository


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="propstore-debug-"))
    repo = Repository.init(root / "knowledge")
    runner = CliRunner()
    claims_file = root / "claims.yaml"
    claims_file.write_text(
        yaml.safe_dump(
            {
                "source": {"paper": "demo"},
                "claims": [
                    {
                        "id": "claim1",
                        "type": "observation",
                        "statement": "A testable claim",
                        "concepts": ["test_concept"],
                        "provenance": {"paper": "demo", "page": 1},
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    commands = [
        [
            "-C", str(repo.root),
            "source", "init", "demo",
            "--kind", "academic_paper",
            "--origin-type", "manual", "--origin-value", "demo",
        ],
        [
            "-C", str(repo.root),
            "source", "propose-concept", "demo",
            "--name", "test_concept",
            "--definition", "A test concept",
            "--form", "category",
        ],
        [
            "-C", str(repo.root),
            "source", "add-claim", "demo",
            "--batch", str(claims_file),
        ],
        [
            "-C", str(repo.root),
            "source", "promote", "demo",
        ],
    ]
    for command in commands:
        result = runner.invoke(cli, command)
        print(command)
        print("exit:", result.exit_code)
        print(result.output)

    tip = repo.git.branch_sha("source/demo")
    print("branch tip:", tip)
    if tip is not None:
        try:
            print(repo.git.read_file("merge/finalize/demo.yaml", commit=tip).decode("utf-8"))
        except FileNotFoundError:
            print("finalize report missing")


if __name__ == "__main__":
    main()
