from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from propstore.families.micropublications.declaration import MicropublicationDocument
from propstore.families.identity.micropubs import (
    canonical_micropub_payload,
    micropub_artifact_id,
)
from quire.documents import convert_document_value
