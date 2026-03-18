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
"""Tests for Email Service."""


from unittest.mock import MagicMock, patch

import pytest
from googleapiclient.errors import HttpError

from src.common.email_service import EmailService
from src.config.config_service import config_service


@pytest.fixture(name="email_service")
def fixture_email_service():
    # Use patch to ensure SENDER_EMAIL is available during initialization
    with (
        patch.object(
            config_service,
            "FRONTEND_URL",
            "http://localhost:4200",
        ),
        patch.object(config_service, "SENDER_EMAIL", "test@example.com"),
    ):
        service = EmailService()
        yield service


def test_send_workspace_invitation_email_success(email_service):
    with (
        patch("google.auth.default") as mock_auth,
        patch(
            "src.common.email_service.build",
        ) as mock_build,
    ):
        mock_creds = MagicMock()
        mock_auth.return_value = (mock_creds, None)

        mock_delegated_creds = MagicMock()
        mock_creds.with_subject.return_value = mock_delegated_creds

        mock_gmail_service = MagicMock()
        mock_build.return_value = mock_gmail_service

        mock_messages = mock_gmail_service.users().messages()
        mock_send = mock_messages.send
        mock_send.return_value.execute.return_value = {"id": "12345"}

        email_service.send_workspace_invitation_email(
            recipient_email="recipient@example.com",
            inviter_name="Inviter",
            workspace_name="Workspace",
            workspace_id=1,
        )

        mock_auth.assert_called_once()
        mock_build.assert_called_once()
        mock_messages.send.assert_called_once()


def test_send_workspace_invitation_email_no_sender(email_service):
    # Set to None to trigger simulation branch
    with patch.object(email_service, "sender_email", None):
        email_service.send_workspace_invitation_email(
            recipient_email="recipient@example.com",
            inviter_name="Inviter",
            workspace_name="Workspace",
            workspace_id=1,
        )


def test_send_workspace_invitation_email_http_error(email_service):
    with (
        patch("google.auth.default") as mock_auth,
        patch(
            "src.common.email_service.build",
        ) as mock_build,
    ):
        mock_creds = MagicMock()
        mock_auth.return_value = (mock_creds, None)
        mock_creds.with_subject.return_value = MagicMock()

        mock_gmail_service = MagicMock()
        mock_build.return_value = mock_gmail_service

        mock_messages = mock_gmail_service.users().messages()

        # httplib2 is required for HttpError creation
        # create a dummy response
        class DummyResponse:
            def __init__(self, status):
                self.status = status
                self.reason = "Error"

        error = HttpError(resp=DummyResponse(400), content=b"Bad Request")
        mock_messages.send().execute.side_effect = error

        email_service.send_workspace_invitation_email(
            recipient_email="recipient@example.com",
            inviter_name="Inviter",
            workspace_name="Workspace",
            workspace_id=1,
        )


def test_send_workspace_invitation_email_general_exception(email_service):
    with patch("google.auth.default") as mock_auth:
        mock_auth.side_effect = Exception("System Crash")

        email_service.send_workspace_invitation_email(
            recipient_email="recipient@example.com",
            inviter_name="Inviter",
            workspace_name="Workspace",
            workspace_id=1,
        )
