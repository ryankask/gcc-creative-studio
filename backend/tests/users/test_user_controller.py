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
"""Tests for User Controller."""


from unittest.mock import AsyncMock

import pytest
from fastapi import status

from main import app
from src.common.dto.pagination_response_dto import PaginationResponseDto
from src.users.user_model import UserModel
from src.users.user_service import UserService


@pytest.fixture(name="mock_user_service")
def fixture_mock_user_service():
    """Provides a mocked UserService."""
    return AsyncMock()


@pytest.fixture(name="override_user_service", autouse=True)
def fixture_override_user_service(mock_user_service):
    """Overrides the UserService dependency in the app."""
    app.dependency_overrides[UserService] = lambda: mock_user_service
    yield
    # Cleanup after test
    if UserService in app.dependency_overrides:
        del app.dependency_overrides[UserService]


class TestGetMyProfile:
    """Tests for GET /api/users/me."""

    def test_get_my_profile_success(self, api_client, mock_user):
        response = api_client.get("/api/users/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == mock_user.email
        assert data["name"] == mock_user.name


class TestListAllUsers:
    """Tests for GET /api/users."""

    def test_list_all_users_admin_success(
        self,
        admin_client,
        mock_user_service,
        mock_user,
    ):
        # Setup mock response
        mock_pagination = PaginationResponseDto[UserModel](
            count=1,
            page=1,
            page_size=10,
            total_pages=1,
            data=[mock_user],
        )
        mock_user_service.find_all_users.return_value = mock_pagination

        response = admin_client.get("/api/users")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["count"] == 1
        assert len(data["data"]) == 1

    def test_list_all_users_regular_user_forbidden(self, api_client):
        # Regular user should be rejected by RoleChecker
        response = api_client.get("/api/users")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetUserById:
    """Tests for GET /api/users/{id}."""

    def test_get_user_by_id_admin_success(
        self,
        admin_client,
        mock_user_service,
        mock_user,
    ):
        mock_user_service.get_user_by_id.return_value = mock_user

        response = admin_client.get("/api/users/1")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1

    def test_get_user_by_id_not_found(self, admin_client, mock_user_service):
        mock_user_service.get_user_by_id.return_value = None

        response = admin_client.get("/api/users/999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_user_by_id_regular_user_forbidden(self, api_client):
        response = api_client.get("/api/users/1")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestDeleteUser:
    """Tests for DELETE /api/users/{id}."""

    def test_delete_user_admin_success(self, admin_client, mock_user_service):
        mock_user_service.delete_user.return_value = True

        response = admin_client.delete(
            "/api/users/1"
        )  # Delete ID 1 (Admin is 2)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_user_service.delete_user.assert_called_once()

    def test_delete_user_prevent_self_deletion(self, admin_client, mock_admin):
        # Admin is ID 2, trying to delete ID 2
        response = admin_client.delete("/api/users/2")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "cannot delete yourself" in response.json()["detail"]

    def test_delete_user_regular_user_forbidden(self, api_client):
        response = api_client.delete("/api/users/1")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateUserRole:
    """Tests for PUT /api/users/{id}."""

    def test_update_user_role_admin_success(
        self,
        admin_client,
        mock_user_service,
        mock_user,
    ):
        mock_user_service.update_user_role.return_value = mock_user

        response = admin_client.put("/api/users/1", json={"roles": ["admin"]})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1

    def test_update_user_role_not_found(self, admin_client, mock_user_service):
        mock_user_service.update_user_role.return_value = None

        response = admin_client.put("/api/users/999", json={"roles": ["admin"]})

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRestoreUser:
    """Tests for POST /api/users/{id}/restore."""

    def test_restore_user_admin_success(self, admin_client, mock_user_service):
        mock_user_service.restore_user.return_value = True

        response = admin_client.post("/api/users/1/restore")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["message"] == "User restored successfully"

    def test_restore_user_not_found(self, admin_client, mock_user_service):
        mock_user_service.restore_user.return_value = False

        response = admin_client.post("/api/users/999/restore")

        assert response.status_code == status.HTTP_404_NOT_FOUND
