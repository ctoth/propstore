from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from propstore.families.identity.micropubs import (
    canonical_micropub_payload,
    micropub_artifact_id,
)
from propstore.uri import verify_ni_uri
