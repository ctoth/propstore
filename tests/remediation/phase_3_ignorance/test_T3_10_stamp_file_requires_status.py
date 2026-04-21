from pathlib import Path

import pytest

from propstore.provenance import stamp_file


def test_stamp_file_requires_status_arg(tmp_path: Path) -> None:
    path = tmp_path / "artifact.yaml"
    path.write_text("source:\n  name: test-paper\n", encoding="utf-8")

    with pytest.raises(TypeError):
        stamp_file(path, agent="x", skill="reader")
