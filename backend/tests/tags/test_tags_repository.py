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
"""Tests for Tags Repository."""

from unittest.mock import AsyncMock, MagicMock
import pytest
from datetime import datetime

from src.tags.repository.tags_repository import TagsRepository
from src.tags.schema.tags_model import Tag, TagModel


@pytest.mark.anyio
async def test_get_by_workspace():
    """Tests get_by_workspace."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    now = datetime.now()
    mock_tag = Tag(
        id=1, name="tag1", workspace_id=1, created_at=now, updated_at=now
    )
    mock_result.scalars().all.return_value = [mock_tag]
    mock_db.execute.return_value = mock_result

    repo = TagsRepository(db=mock_db)
    result = await repo.get_by_workspace(1)

    assert len(result.data) == 1
    assert result.data[0].name == "tag1"
    assert isinstance(result.data[0], TagModel)


@pytest.mark.anyio
async def test_find_by_name_found():
    """Tests find_by_name when tag is found."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    now = datetime.now()
    mock_tag = Tag(
        id=1, name="tag1", workspace_id=1, created_at=now, updated_at=now
    )
    mock_result.scalar_one_or_none.return_value = mock_tag
    mock_db.execute.return_value = mock_result

    repo = TagsRepository(db=mock_db)
    result = await repo.find_by_name("tag1", 1)

    assert result is not None
    assert result.name == "tag1"


@pytest.mark.anyio
async def test_find_by_name_not_found():
    """Tests find_by_name when tag is not found."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    repo = TagsRepository(db=mock_db)
    result = await repo.find_by_name("tag1", 1)

    assert result is None


@pytest.mark.anyio
async def test_assign_tag_to_media_item():
    """Tests assign_tag_to_media_item."""
    mock_db = AsyncMock()

    repo = TagsRepository(db=mock_db)
    await repo.assign_tag_to_media_item(1, 10)

    assert mock_db.execute.call_count == 2
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_get_tags_for_media_item():
    """Tests get_tags_for_media_item."""
    mock_db = AsyncMock()
    mock_result = MagicMock()
    now = datetime.now()
    mock_tag = Tag(
        id=1, name="tag1", workspace_id=1, created_at=now, updated_at=now
    )
    mock_result.scalars().all.return_value = [mock_tag]
    mock_db.execute.return_value = mock_result

    repo = TagsRepository(db=mock_db)
    result = await repo.get_tags_for_media_item(1)

    assert len(result) == 1
    assert result[0].name == "tag1"


@pytest.mark.anyio
async def test_clear_tags_for_items():
    """Tests clear_tags_for_items."""
    mock_db = AsyncMock()
    repo = TagsRepository(db=mock_db)

    await repo.clear_tags_for_items([1, 2], "media_item")

    assert mock_db.execute.call_count == 1
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_clear_tags_for_items_no_commit():
    """Tests clear_tags_for_items with commit=False."""
    mock_db = AsyncMock()
    repo = TagsRepository(db=mock_db)

    await repo.clear_tags_for_items([1, 2], "media_item", commit=False)

    assert mock_db.execute.call_count == 1
    mock_db.commit.assert_not_called()


@pytest.mark.anyio
async def test_assign_tags_to_items():
    """Tests assign_tags_to_items."""
    mock_db = AsyncMock()
    repo = TagsRepository(db=mock_db)

    await repo.assign_tags_to_items([1, 2], [10, 20], "media_item")

    # 1 for insert, 1 for update tags
    assert mock_db.execute.call_count == 2
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_assign_tags_to_items_no_commit():
    """Tests assign_tags_to_items with commit=False."""
    mock_db = AsyncMock()
    repo = TagsRepository(db=mock_db)

    await repo.assign_tags_to_items(
        [1, 2], [10, 20], "media_item", commit=False
    )

    assert mock_db.execute.call_count == 2
    mock_db.commit.assert_not_called()
