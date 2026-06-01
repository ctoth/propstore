from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import assume, given, strategies as st
from quire.git_store import HeadMismatchError

from propstore.repository import Repository


_SAFE_NAME = st.text(
    alphabet=st.characters(
        whitelist_categories=("Ll", "Lu", "Nd"), min_codepoint=48, max_codepoint=122
    ),
    min_size=1,
    max_size=12,
)
_PAYLOAD = st.binary(min_size=1, max_size=64)
