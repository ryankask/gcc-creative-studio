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
"""Tests for global soft-delete event listeners logic using mocks."""

from unittest.mock import MagicMock

from src.common.events import _add_soft_delete_criteria


def test_add_soft_delete_criteria_not_select():
    mock_execute_state = MagicMock()
    mock_execute_state.is_select = False

    _add_soft_delete_criteria(mock_execute_state)

    # Statement should not be modified
    assert not mock_execute_state.statement.options.called


def test_add_soft_delete_criteria_include_deleted():
    mock_execute_state = MagicMock()
    mock_execute_state.is_select = True
    mock_execute_state.execution_options = {"include_deleted": True}

    _add_soft_delete_criteria(mock_execute_state)

    # Statement should not be modified
    assert not mock_execute_state.statement.options.called


def test_add_soft_delete_criteria_applied():
    mock_execute_state = MagicMock()
    mock_execute_state.is_select = True
    mock_execute_state.execution_options = {"include_deleted": False}

    # Mock current statement
    mock_statement = MagicMock()
    mock_execute_state.statement = mock_statement

    _add_soft_delete_criteria(mock_execute_state)

    # Verify options was called to add criteria
    mock_statement.options.assert_called_once()
    assert mock_execute_state.statement == mock_statement.options.return_value
