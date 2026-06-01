from __future__ import annotations

from pathlib import Path
import tempfile

from fastapi.testclient import TestClient
from hypothesis import HealthCheck, given, settings, strategies as st
import pytest

from propstore.web.app import create_app
from tests.web_demo_fixture import seed_web_demo_repository


MALFORMED_FTS_QUERIES = ('"', "alpha OR", "alpha NEAR(", '"unterminated')


@pytest.mark.property
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.sampled_from(MALFORMED_FTS_QUERIES))
def test_malformed_concept_fts_queries_never_return_500(tmp_path, query: str) -> None:
    with tempfile.TemporaryDirectory(dir=tmp_path) as temp_dir:
        fixture = seed_web_demo_repository(Path(temp_dir))
        client = TestClient(create_app(repository_root=fixture.repo.root))
        response = client.get("/concepts.json", params={"q": query})

    assert response.status_code == 400
