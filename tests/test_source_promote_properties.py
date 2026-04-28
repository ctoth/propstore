from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner
from hypothesis import given, settings
from hypothesis import strategies as st

from propstore.families.identity.claims import normalize_canonical_claim_payload
from propstore.repository import Repository
from tests.builders import SourceClaimSpec
from tests.test_source_promote_dangling_refs import (
    _add_claims,
    _finalize_and_promote,
    _init_source,
    _propose_claims_identical,
    _seed_master_concept,
)

_SOURCE_NAME = st.from_regex(r"[A-Za-z][A-Za-z0-9]{0,5}", fullmatch=True)
_TEXT = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd", "Zs"),
        min_codepoint=32,
        max_codepoint=126,
    ),
    min_size=1,
    max_size=60,
).filter(lambda value: bool(value.strip()))
_SOURCE_LOCAL_FIELD_VALUES = st.dictionaries(
    keys=st.sampled_from(("id", "source_local_id", "artifact_code")),
    values=st.text(min_size=1, max_size=24),
    min_size=1,
    max_size=3,
)


@pytest.mark.property
@given(source_name=_SOURCE_NAME, statement=_TEXT)
@settings(deadline=None, max_examples=5)
def test_ws_e_generated_repromote_preserves_claim_artifacts(
    source_name: str,
    statement: str,
) -> None:
    """WS-E property: re-promoting generated content is not a partial write."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Repository.init(Path(tmp_dir) / "knowledge")
        runner = CliRunner()
        _seed_master_concept(repo)
        _init_source(repo, runner, source_name)
        _propose_claims_identical(repo, runner, source_name)
        _add_claims(
            repo,
            runner,
            source_name,
            Path(tmp_dir),
            [
                SourceClaimSpec(
                    local_id="c1",
                    claim_type="observation",
                    statement=statement,
                    concepts=("claims_identical",),
                    page=1,
                )
            ],
        )

        _finalize_and_promote(repo, runner, source_name)
        first = yaml.safe_load(repo.git.read_file(f"claims/{source_name}.yaml"))
        _finalize_and_promote(repo, runner, source_name)
        second = yaml.safe_load(repo.git.read_file(f"claims/{source_name}.yaml"))

        assert [claim["artifact_id"] for claim in first["claims"]] == [
            claim["artifact_id"] for claim in second["claims"]
        ]
        assert len(second["claims"]) == 1


@pytest.mark.property
@given(source_local_fields=_SOURCE_LOCAL_FIELD_VALUES)
def test_ws_e_generated_source_local_fields_do_not_enter_canonical_claims(
    source_local_fields: dict[str, str],
) -> None:
    """WS-E property: source-local promotion metadata is not canonical identity."""
    promoted = {
        "artifact_id": "ps:claim:demo",
        "type": "observation",
        "context": "ctx_test",
        "statement": "A generated source-local field stripping check.",
        "provenance": {"paper": "demo", "page": 1},
        **source_local_fields,
    }

    normalized = normalize_canonical_claim_payload(
        promoted,
        strip_source_local=True,
    )

    assert not ({"id", "source_local_id", "artifact_code"} & set(normalized))
