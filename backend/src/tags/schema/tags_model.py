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

import datetime
from pydantic import Field
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Table,
    DateTime,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from src.common.base_repository import BaseDocument
from src.database import Base

# Association table for MediaItem and Tag
media_item_tags = Table(
    "media_item_tags",
    Base.metadata,
    Column(
        "media_item_id",
        ForeignKey("media_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)

# Association table for SourceAsset and Tag
source_asset_tags = Table(
    "source_asset_tags",
    Base.metadata,
    Column(
        "source_asset_id",
        ForeignKey("source_assets.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Tag(Base):
    """SQLAlchemy model for the 'tags' table."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str] = mapped_column(
        String, nullable=False, server_default="#E8EAED"
    )
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("name", "workspace_id", name="uq_tag_name_workspace"),
    )


class TagModel(BaseDocument):
    """Represents a tag in a workspace."""

    id: int | None = None
    name: str = Field(description="The name of the tag.")
    workspace_id: int = Field(
        description="The ID of the workspace this tag belongs to."
    )
    color: str | None = Field(
        default="#E8EAED", description="The color of the tag in hex format."
    )
    user_id: int | None = Field(
        default=None, description="The ID of the user who created the tag."
    )
