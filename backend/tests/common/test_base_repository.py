# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for Base Repository."""


import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.common.base_repository import BaseRepository
from src.source_assets.schema.source_asset_model import (
    SourceAsset,
    SourceAssetModel,
)


def get_dummy_source_asset(**kwargs):
    now = datetime.datetime.now(datetime.UTC)
    defaults = {
        "id": 1,
        "workspace_id": 1,
        "user_id": 1,
        "gcs_uri": "gs://bucket/asset.png",
        "original_filename": "asset.png",
        "mime_type": "image/png",
        "aspect_ratio": "1:1",
        "file_hash": "hash123",
        "scope": "private",
        "asset_type": "generic_image",
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    defaults.update(kwargs)
    return SourceAsset(**defaults)


class TestRepository(BaseRepository[SourceAsset, SourceAssetModel]):
    def __init__(self, db):
        super().__init__(model=SourceAsset, schema=SourceAssetModel, db=db)


@pytest.mark.anyio
async def test_get_by_id_success():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_asset = get_dummy_source_asset(id=10)
    mock_result.scalar_one_or_none.return_value = mock_asset
    mock_db.execute.return_value = mock_result

    repo = TestRepository(db=mock_db)
    response = await repo.get_by_id(item_id=10)

    assert response is not None
    assert response.id == 10


@pytest.mark.anyio
async def test_get_by_id_not_found():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    repo = TestRepository(db=mock_db)
    response = await repo.get_by_id(item_id=99)

    assert response is None


@pytest.mark.anyio
async def test_create_success():
    mock_db = AsyncMock()
    repo = TestRepository(db=mock_db)

    input_model = SourceAssetModel(
        workspace_id=1,
        user_id=1,
        gcs_uri="gs://b/1",
        original_filename="1",
        file_hash="h1",
        mime_type="image/png",
        aspect_ratio="1:1",
        scope="private",
        asset_type="generic_image",
    )

    async def mock_refresh(obj):
        obj.id = 100
        obj.created_at = datetime.datetime.now(datetime.UTC)
        obj.updated_at = datetime.datetime.now(datetime.UTC)
        obj.aspect_ratio = "1:1"
        obj.scope = "private"
        obj.asset_type = "generic_image"

    mock_db.refresh.side_effect = mock_refresh

    response = await repo.create(schema=input_model)

    assert response is not None
    assert response.id == 100
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


@pytest.mark.anyio
async def test_update_success():
    mock_db = AsyncMock()
    mock_asset = get_dummy_source_asset(id=20)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_asset
    mock_db.execute.return_value = mock_result

    repo = TestRepository(db=mock_db)

    update_data = {"original_filename": "updated.png"}
    response = await repo.update(item_id=20, update_data=update_data)

    assert response is not None
    assert response.original_filename == "updated.png"
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_success():
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db.execute.return_value = mock_result

    repo = TestRepository(db=mock_db)
    response = await repo.delete(item_id=30)

    assert response is True
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_soft_delete_success():
    mock_db = AsyncMock()
    mock_asset = get_dummy_source_asset(id=40)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_asset
    mock_db.execute.return_value = mock_result

    repo = TestRepository(db=mock_db)
    response = await repo.soft_delete(item_id=40)

    assert response is True
    assert mock_asset.deleted_at is not None
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_restore_success():
    mock_db = AsyncMock()
    mock_asset = get_dummy_source_asset(
        id=50,
        deleted_at=datetime.datetime.now(datetime.UTC),
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_asset
    mock_db.execute.return_value = mock_result

    repo = TestRepository(db=mock_db)
    response = await repo.restore(item_id=50)

    assert response is True
    assert mock_asset.deleted_at is None
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_find_all_success():
    mock_db = AsyncMock()
    mock_asset = get_dummy_source_asset(id=60)
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_asset]
    mock_db.execute.return_value = mock_result

    repo = TestRepository(db=mock_db)
    response = await repo.find_all()

    assert len(response) == 1
    assert response[0].id == 60
