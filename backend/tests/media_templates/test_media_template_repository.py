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
"""Tests for MediaTemplateRepository using mocks."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.media_templates.dto.template_search_dto import TemplateSearchDto
from src.media_templates.repository.media_template_repository import (
    MediaTemplateRepository,
)
from src.media_templates.schema.media_template_model import IndustryEnum


@pytest.fixture(name="mock_db")
def fixture_mock_db():
    return AsyncMock()


@pytest.mark.anyio
async def test_query_various_filters(mock_db):
    repo = MediaTemplateRepository(db=mock_db)

    # Mock DB return values
    mock_count_result = MagicMock()
    mock_count_result.scalar_one.return_value = 1
    mock_data_result = MagicMock()
    mock_data_result.scalars.return_value.all.return_value = []
    mock_db.execute.side_effect = [mock_count_result, mock_data_result]

    search_dto = TemplateSearchDto(
        industry=IndustryEnum.TECHNOLOGY,
        brand="Brand X",
        tag="new",
        limit=10,
        offset=0,
    )

    await repo.query(search_dto)
    assert mock_db.execute.call_count == 2


@pytest.mark.anyio
async def test_get_by_name(mock_db):
    repo = MediaTemplateRepository(db=mock_db)

    # Mock return none
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_res

    res = await repo.get_by_name("Nonexistent")
    assert res is None
