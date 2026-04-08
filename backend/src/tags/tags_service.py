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

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, func
from src.common.dto.pagination_response_dto import PaginationResponseDto
from src.tags.dto.tags_dto import BulkAssignTagsDto, TagCreateDto, TagUpdateDto
from src.tags.repository.tags_repository import TagsRepository
from src.tags.schema.tags_model import TagModel


PASTEL_COLORS = [
    "#FADBD8",
    "#EBDEF0",
    "#E8F8F5",
    "#FEF9E7",
    "#FBEEE6",
    "#EAEDED",
    "#D4EFDF",
    "#FCF3CF",
    "#D6EAF8",
    "#F5CBA7",
    "#E6B0AA",
    "#D7BDE2",
    "#A2D9CE",
    "#F9E79F",
    "#EDBB99",
    "#D5D8DC",
    "#ABEBC6",
    "#FAD7A0",
    "#AED6F1",
    "#F1948A",
]


class TagsService:
    """Provides business logic for tag operations."""

    def __init__(self, repo: TagsRepository = Depends()):
        self.repo = repo

    async def list_tags(
        self,
        workspace_id: int | None = None,
        search: str | None = None,
        limit: int = 10,
        offset: int = 0,
        user_id: int | None = None,
    ) -> PaginationResponseDto[TagModel]:
        """Lists tags, optionally filtered by workspace and search query."""
        if workspace_id:
            return await self.repo.get_by_workspace(
                workspace_id, search, limit, offset, user_id
            )

        # For find_all case (admin listing all tags)
        tags = await self.repo.find_all(limit=limit, offset=offset)

        # Get total count for find_all
        result = await self.repo.db.execute(
            select(func.count(self.repo.model.id))
        )
        total_count = result.scalar_one()

        page = (offset // limit) + 1
        page_size = limit
        total_pages = (total_count + page_size - 1) // page_size

        return PaginationResponseDto[TagModel](
            count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            data=tags,
        )

    async def create_tag(self, dto: TagCreateDto, user_id: int) -> TagModel:
        """Creates a new tag if it doesn't already exist."""
        existing = await self.repo.find_by_name(dto.name, dto.workspace_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag with name '{dto.name}' already exists in this workspace.",
            )

        if not dto.color:
            count = await self.repo.count_by_workspace(dto.workspace_id)
            dto.color = PASTEL_COLORS[count % len(PASTEL_COLORS)]

        data = dto.model_dump()
        data["user_id"] = user_id
        return await self.repo.create(data)

    async def update_tag(
        self, id: int, dto: TagUpdateDto, user_id: int, is_admin: bool
    ) -> TagModel:
        """Updates a tag."""
        tag = await self.repo.get_by_id(id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
            )

        if not is_admin and tag.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this tag",
            )

        updated = await self.repo.update_tag(id, dto.name, dto.color)
        return updated

    async def delete_tag(
        self, id: int, user_id: int, is_admin: bool, tag: TagModel | None = None
    ) -> bool:
        """Deletes a tag by its ID."""
        if not tag:
            tag = await self.repo.get_by_id(id)
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
            )

        if not is_admin and tag.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this tag",
            )

        return await self.repo.delete(id)

    async def bulk_assign(self, dto: BulkAssignTagsDto, user_id: int):
        """Bulk assigns tags to multiple items, replacing existing ones."""
        # Resolve tag names to IDs
        tag_ids = []
        for name in dto.tag_names:
            tag = await self.repo.find_by_name(name, dto.workspace_id)
            if not tag:
                # Create it if it doesn't exist
                count = await self.repo.count_by_workspace(dto.workspace_id)
                color = PASTEL_COLORS[count % len(PASTEL_COLORS)]
                tag = await self.repo.create(
                    {
                        "name": name,
                        "workspace_id": dto.workspace_id,
                        "color": color,
                        "user_id": user_id,
                    }
                )
            tag_ids.append(tag.id)

        if dto.item_type == "media_item":
            await self.repo.clear_tags_for_items(dto.item_ids, "media_item")
            await self.repo.assign_tags_to_items(
                dto.item_ids, tag_ids, "media_item"
            )
        elif dto.item_type == "source_asset":
            await self.repo.clear_tags_for_items(dto.item_ids, "source_asset")
            await self.repo.assign_tags_to_items(
                dto.item_ids, tag_ids, "source_asset"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid item_type: {dto.item_type}",
            )

        await self.repo.db.commit()
        return True
