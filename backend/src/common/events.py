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
"""Event definitions and handling."""


import logging

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from src.common.schema.media_item_model import MediaItem
from src.source_assets.schema.source_asset_model import SourceAsset
from src.users.user_model import User

logger = logging.getLogger(__name__)


@event.listens_for(Session, "do_orm_execute")
def _add_soft_delete_criteria(execute_state):
    """Event listener to automatically filter out soft-deleted Users and
    MediaItems."""
    include_deleted = execute_state.execution_options.get(
        "include_deleted", False
    )

    # Only apply to SELECT statements
    if not execute_state.is_select:
        return

    if include_deleted:
        return

    # Apply the filter using with_loader_criteria
    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            User,
            lambda cls: cls.deleted_at.is_(None),
            include_aliases=True,
            propagate_to_loaders=True,
        ),
        with_loader_criteria(
            MediaItem,
            lambda cls: cls.deleted_at.is_(None),
            include_aliases=True,
            propagate_to_loaders=True,
        ),
        with_loader_criteria(
            SourceAsset,
            lambda cls: cls.deleted_at.is_(None),
            include_aliases=True,
            propagate_to_loaders=True,
        ),
    )
    logger.debug("Applied soft delete criteria for User and MediaItem")
