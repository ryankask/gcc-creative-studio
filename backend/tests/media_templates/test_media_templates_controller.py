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
"""Tests for Media Templates Controller."""


from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.auth_guard import get_current_user
from src.media_templates.media_templates_controller import router
from src.media_templates.media_templates_service import MediaTemplateService
from src.users.user_model import UserModel, UserRoleEnum


@pytest.fixture(name="mock_admin")
def fixture_mock_admin():
    return UserModel(
        id=1,
        email="admin@example.com",
        name="Admin",
        roles=[UserRoleEnum.ADMIN],
    )


@pytest.fixture(name="mock_service")
def fixture_mock_service():
    service = AsyncMock()
    service.create_template_from_media_item = AsyncMock()
    service.find_all_templates = AsyncMock()
    service.get_template_by_id = AsyncMock()
    service.update_template = AsyncMock()
    service.delete_template = AsyncMock()
    return service


@pytest.fixture(name="client")
def fixture_client(mock_admin, mock_service):
    app = FastAPI()
    app.include_router(router)

    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[MediaTemplateService] = lambda: mock_service

    return TestClient(app)


def get_dummy_template_dict():
    return {
        "id": 1,
        "name": "Template 1",
        "description": "Description 1",
        "mime_type": "image/png",
        "gcs_uris": ["gs://bucket/asset1.png"],
        "thumbnail_uris": [],
        "generation_parameters": {
            "prompt": "Enhanced prompt",
            "model": "imagen",
            "aspect_ratio": "1:1",
        },
    }


def test_create_template_success(client, mock_service):
    mock_template = get_dummy_template_dict()
    mock_service.create_template_from_media_item.return_value = mock_template

    response = client.post("/api/media-templates/from-media-item/100")

    assert response.status_code == 201
    assert response.json()["id"] == 1
    mock_service.create_template_from_media_item.assert_called_once()


def test_find_templates_success(client, mock_service):
    from src.common.dto.pagination_response_dto import PaginationResponseDto

    # In controller response_model=PaginationResponseDto[MediaTemplateResponse]
    # We can just return items inside list
    mock_item = get_dummy_template_dict()

    mock_response = PaginationResponseDto(
        count=1,
        data=[mock_item],
        page=1,
        page_size=10,
        total_pages=1,
    )
    mock_service.find_all_templates.return_value = mock_response

    response = client.get("/api/media-templates")

    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


def test_get_template_success(client, mock_service):
    mock_template = get_dummy_template_dict()
    mock_template["id"] = 2
    mock_service.get_template_by_id.return_value = mock_template

    response = client.get("/api/media-templates/2")

    assert response.status_code == 200
    assert response.json()["id"] == 2


def test_get_template_not_found(client, mock_service):
    mock_service.get_template_by_id.return_value = None

    response = client.get("/api/media-templates/999")

    assert response.status_code == 404


def test_update_template_success(client, mock_service):
    mock_template = get_dummy_template_dict()
    mock_template["id"] = 3
    mock_template["name"] = "Updated"
    mock_service.update_template.return_value = mock_template

    payload = {"name": "Updated"}
    response = client.put("/api/media-templates/3", json=payload)

    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


def test_delete_template_success(client, mock_service):
    mock_service.delete_template.return_value = True

    response = client.delete("/api/media-templates/4")

    assert response.status_code == 204


def test_create_template_not_found(client, mock_service):
    mock_service.create_template_from_media_item.return_value = None
    response = client.post("/api/media-templates/from-media-item/999")
    assert response.status_code == 404


def test_update_template_not_found(client, mock_service):
    mock_service.update_template.return_value = None
    payload = {"name": "Updated"}
    response = client.put("/api/media-templates/999", json=payload)
    assert response.status_code == 404


def test_delete_template_not_found(client, mock_service):
    mock_service.delete_template.return_value = False
    response = client.delete("/api/media-templates/999")
    assert response.status_code == 404
