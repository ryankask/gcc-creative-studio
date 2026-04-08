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
"""Tests for Workspace Auth Guard."""


from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.workspaces.schema.workspace_model import (
    WorkspaceModel,
    WorkspaceScopeEnum,
)
from src.workspaces.workspace_auth_guard import WorkspaceAuth


@pytest.fixture(name="mock_workspace_repo_auth")
def fixture_mock_workspace_repo_auth():
    return AsyncMock()


@pytest.fixture(name="workspace_auth")
def fixture_workspace_auth(mock_workspace_repo_auth):
    return WorkspaceAuth(workspace_repo=mock_workspace_repo_auth)


class TestWorkspaceAuthAuthorize:
    """Tests for WorkspaceAuth.authorize."""

    @pytest.mark.anyio
    async def test_authorize_not_found(
        self,
        workspace_auth,
        mock_workspace_repo_auth,
        mock_user,
    ):
        mock_workspace_repo_auth.get_scope.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await workspace_auth.authorize(999, mock_user)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.anyio
    async def test_authorize_admin_access(
        self,
        workspace_auth,
        mock_workspace_repo_auth,
        mock_admin,
    ):
        # Private workspace, but user is ADMIN
        mock_workspace_repo_auth.get_scope.return_value = (
            WorkspaceScopeEnum.PRIVATE
        )

        mock_workspace = WorkspaceModel(id=1, name="Private", owner_id=99)
        mock_workspace_repo_auth.get_by_id.return_value = mock_workspace

        result = await workspace_auth.authorize(1, mock_admin)

        assert result == mock_workspace
        mock_workspace_repo_auth.is_member.assert_not_called()

    @pytest.mark.anyio
    async def test_authorize_public_workspace(
        self,
        workspace_auth,
        mock_workspace_repo_auth,
        mock_user,
    ):
        # Public workspace, user is regular user
        mock_workspace_repo_auth.get_scope.return_value = (
            WorkspaceScopeEnum.PUBLIC
        )

        mock_workspace = WorkspaceModel(id=1, name="Public", owner_id=99)
        mock_workspace_repo_auth.get_by_id.return_value = mock_workspace

        result = await workspace_auth.authorize(1, mock_user)

        assert result == mock_workspace
        mock_workspace_repo_auth.is_member.assert_not_called()

    @pytest.mark.anyio
    async def test_authorize_private_member(
        self,
        workspace_auth,
        mock_workspace_repo_auth,
        mock_user,
    ):
        # Private workspace, user is regular user, but IS a member
        mock_workspace_repo_auth.get_scope.return_value = (
            WorkspaceScopeEnum.PRIVATE
        )
        mock_workspace_repo_auth.is_member.return_value = True

        mock_workspace = WorkspaceModel(id=1, name="Private", owner_id=99)
        mock_workspace_repo_auth.get_by_id.return_value = mock_workspace

        result = await workspace_auth.authorize(1, mock_user)

        assert result == mock_workspace
        mock_workspace_repo_auth.is_member.assert_called_once_with(
            1, mock_user.id
        )

    @pytest.mark.anyio
    async def test_authorize_private_not_member(
        self,
        workspace_auth,
        mock_workspace_repo_auth,
        mock_user,
    ):
        # Private workspace, user is regular user, NOT a member
        mock_workspace_repo_auth.get_scope.return_value = (
            WorkspaceScopeEnum.PRIVATE
        )
        mock_workspace_repo_auth.is_member.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await workspace_auth.authorize(1, mock_user)

        assert exc_info.value.status_code == 403
        assert "do not have permission" in exc_info.value.detail
        mock_workspace_repo_auth.is_member.assert_called_once_with(
            1, mock_user.id
        )
