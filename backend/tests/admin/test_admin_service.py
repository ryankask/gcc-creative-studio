# Copyright 2025 Google LLC
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

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.admin.admin_service import AdminService


@pytest.mark.asyncio
async def test_get_overview_stats():
    db = MagicMock()

    # side_effect for async execute calls (total users, total workspaces, media counts)
    mock_users_result = MagicMock()
    mock_users_result.scalar_one.return_value = 10

    mock_workspaces_result = MagicMock()
    mock_workspaces_result.scalar_one.return_value = 5

    mock_media_result = MagicMock()
    media_counts = MagicMock()
    media_counts.images = 100
    media_counts.videos = 50
    media_counts.audios = 25
    mock_media_result.first.return_value = media_counts

    mock_uploaded_result = MagicMock()
    mock_uploaded_result.scalar_one.return_value = 2

    db.execute = AsyncMock(
        side_effect=[
            mock_users_result,
            mock_workspaces_result,
            mock_uploaded_result,
            mock_media_result,
        ]
    )

    service = AdminService(db)
    result = await service.get_overview_stats()

    assert result.total_users == 10
    assert result.total_workspaces == 5
    assert result.images_generated == 100
    assert result.videos_generated == 50
    assert result.audios_generated == 25
    assert result.total_media == 175


@pytest.mark.asyncio
async def test_get_media_over_time():
    db = MagicMock()
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.date = "2026-04"
    mock_row.count = 10
    mock_row.images = 5
    mock_row.videos = 3
    mock_row.audios = 2
    mock_result.all.return_value = [mock_row]
    db.execute = AsyncMock(return_value=mock_result)

    service = AdminService(db)
    result = await service.get_media_over_time()
    assert len(result) == 1
    assert result[0].date == "2026-04"
    assert result[0].total_generated == 10


@pytest.mark.asyncio
async def test_get_workspace_stats():
    db = MagicMock()
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.workspace_id = 1
    mock_row.workspace_name = "Test Workspace"
    mock_row.count = 10
    mock_row.images = 5
    mock_row.videos = 3
    mock_row.audios = 2
    mock_result.all.return_value = [mock_row]
    db.execute = AsyncMock(return_value=mock_result)

    service = AdminService(db)
    result = await service.get_workspace_stats()
    assert len(result) == 1
    assert result[0].workspace_id == 1
    assert result[0].total_media == 10


@pytest.mark.asyncio
async def test_get_active_roles():
    db = MagicMock()
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.role = "ADMIN"
    mock_row.count = 2
    mock_result.all.return_value = [mock_row]
    db.execute = AsyncMock(return_value=mock_result)

    service = AdminService(db)
    result = await service.get_active_roles()
    assert len(result) == 1
    assert result[0].role == "ADMIN"
    assert result[0].count == 2


@pytest.mark.asyncio
async def test_get_generation_health():
    db = MagicMock()
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.status = "COMPLETED"
    mock_row.count = 8
    mock_result.all.return_value = [mock_row]
    db.execute = AsyncMock(return_value=mock_result)

    service = AdminService(db)
    result = await service.get_generation_health()
    assert len(result) == 1
    assert result[0].status == "COMPLETED"
    assert result[0].count == 8


@pytest.mark.asyncio
async def test_get_active_users_monthly():
    db = MagicMock()
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.month = "2026-04"
    mock_row.count = 3
    mock_result.all.return_value = [mock_row]
    db.execute = AsyncMock(return_value=mock_result)

    service = AdminService(db)
    result = await service.get_active_users_monthly()
    assert len(result) == 7
