from __future__ import annotations

from pathlib import Path

import yaml

from propstore.compiler.workflows import build_repository
from propstore.repository import Repository
from tests.conftest import normalize_concept_payloads


def test_build_repository_reports_missing_sidecar_instead_of_zero_success(
    tmp_path: Path,
    monkeypatch,
) -> None:
    concept_payload = normalize_concept_payloads(
        [
            {
                "id": "velocity",
                "canonical_name": "velocity",
                "status": "accepted",
                "definition": "Speed with direction.",
                "domain": "physics",
                "form": "missing_form",
            }
        ],
        default_domain="physics",
    )[0]
    repo = Repository.init(tmp_path / "knowledge")
    repo.git.commit_files(
        {
            "concepts/velocity.yaml": yaml.dump(
                concept_payload,
                sort_keys=False,
            ).encode("utf-8"),
        },
        "seed concept",
    )

    def _no_sidecar(*args, **kwargs):
        return False

    monkeypatch.setattr("propstore.sidecar.build.build_sidecar", _no_sidecar)

    report = build_repository(repo, force=True)

    assert report.sidecar_missing is True
    assert any(message.code == "sidecar.missing" for message in report.messages)
