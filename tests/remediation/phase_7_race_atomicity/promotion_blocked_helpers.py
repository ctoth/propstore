from __future__ import annotations

from pathlib import Path

from quire.derived_store import DerivedStoreHandle
from quire.sqlalchemy_store import create_sqlalchemy_store

from propstore.families.claims.declaration import (
    PromotionBlockedModels,
    write_promotion_blocked_models,
)
from propstore.families.world_charters import world_sqlalchemy_schema


def create_world_store(path: Path) -> None:
    create_sqlalchemy_store(path, world_sqlalchemy_schema())


def flush_promotion_blocked(path: Path, rows: PromotionBlockedModels) -> None:
    schema = world_sqlalchemy_schema()
    handle = DerivedStoreHandle(
        projection_id="propstore.world",
        source_commit="test",
        content_hash="",
        cache_key="promotion-blocked-test",
        path=path,
    )
    with handle.writable_session(schema) as derived:
        write_promotion_blocked_models(derived, rows)
        derived.commit()
