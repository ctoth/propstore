from __future__ import annotations

from pathlib import Path

from propstore.provenance import read_provenance_note
from propstore.repository import Repository
from propstore.source import promote_source_branch
from tests.test_source_promotion_alignment import _save_source
