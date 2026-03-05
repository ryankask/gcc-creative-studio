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

import asyncio
import io
import logging
import zipfile
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.auth.iam_signer_credentials_service import IamSignerCredentials
from src.common.dto.pagination_response_dto import PaginationResponseDto
from src.common.schema.media_item_model import (
    AssetRoleEnum,
    JobStatusEnum,
    MediaItemModel,
    SourceAssetLink,
    SourceMediaItemLink,
)
from src.galleries.dto.gallery_response_dto import (
    MediaItemResponse,
    SourceAssetLinkResponse,
    SourceMediaItemLinkResponse,
)
from src.common.base_dto import (
    AspectRatioEnum,
    GenerationModelEnum,
    MimeTypeEnum,
)
from src.galleries.dto.gallery_search_dto import GallerySearchDto
from src.images.dto.upscale_imagen_dto import UpscaleImagenDto
from src.images.imagen_service import ImagenService
from src.images.repository.media_item_repository import MediaRepository
from src.source_assets.repository.source_asset_repository import (
    SourceAssetRepository,
)
from src.users.user_model import UserModel, UserRoleEnum
from src.users.repository.user_repository import UserRepository
from src.galleries.dto.unified_gallery_response import UnifiedGalleryItemResponse
from src.galleries.repository.unified_gallery_repository import UnifiedGalleryRepository
from src.workspaces.repository.workspace_repository import WorkspaceRepository
from src.workspaces.schema.workspace_model import WorkspaceScopeEnum
from src.workspaces.workspace_auth_guard import WorkspaceAuth
from src.galleries.dto.bulk_delete_dto import BulkDeleteDto 
from src.galleries.dto.bulk_download_dto import BulkDownloadDto
from src.galleries.dto.bulk_copy_dto import BulkCopyDto
from src.common.storage_service import GcsService

logger = logging.getLogger(__name__)


class GalleryService:
    """
    Provides business logic for querying media items and preparing them for the gallery.
    """

    def __init__(
        self,
        media_repo: MediaRepository = Depends(),
        source_asset_repo: SourceAssetRepository = Depends(),
        unified_gallery_repo: UnifiedGalleryRepository = Depends(),
        user_repo: UserRepository = Depends(),
        workspace_repo: WorkspaceRepository = Depends(),
        iam_signer_credentials: IamSignerCredentials = Depends(),
        workspace_auth: WorkspaceAuth = Depends(),
        imagen_service: ImagenService = Depends(),
    ):
        """Initializes the service with its dependencies."""
        self.media_repo = media_repo
        self.source_asset_repo = source_asset_repo
        self.unified_gallery_repo = unified_gallery_repo
        self.user_repo = user_repo
        self.workspace_repo = workspace_repo
        self.iam_signer_credentials = iam_signer_credentials
        self.workspace_auth = workspace_auth
        self.imagen_service = imagen_service 

    async def _enrich_source_asset_link(
        self, link: SourceAssetLink
    ) -> Optional[SourceAssetLinkResponse]:
        """
        Fetches the source asset document and generates a presigned URL for it.
        """
        asset_doc = await self.source_asset_repo.get_by_id(link.asset_id)
        
        if not asset_doc:
            return None

        tasks = [
            asyncio.to_thread(
                self.iam_signer_credentials.generate_presigned_url,
                asset_doc.gcs_uri,
            )
        ]

        # Check if the asset has a thumbnail and create a task for it.
        # This requires the SourceAsset model to have a `thumbnail_gcs_uri` field.
        if asset_doc.thumbnail_gcs_uri:
            tasks.append(
                asyncio.to_thread(
                    self.iam_signer_credentials.generate_presigned_url,
                    asset_doc.thumbnail_gcs_uri,
                )
            )

        results = await asyncio.gather(*tasks)
        presigned_url = results[0]
        presigned_thumbnail_url = results[1] if len(results) > 1 else None

        return SourceAssetLinkResponse(
            **link.model_dump(),
            presigned_url=presigned_url,
            presigned_thumbnail_url=presigned_thumbnail_url,
            gcs_uri=asset_doc.gcs_uri,
        )

    async def _enrich_source_media_item_link(
        self, link: SourceMediaItemLink
    ) -> Optional[SourceMediaItemLinkResponse]:
        """
        Fetches the parent MediaItem document and generates a presigned URL
        for the specific image that was used as input.
        """
        parent_item = await self.media_repo.get_by_id(link.media_item_id)
        if (
            not parent_item
            or not parent_item.gcs_uris
            or not (0 <= link.media_index < len(parent_item.gcs_uris))
        ):
            return None

        # Get the specific GCS URI of the parent image that was edited.
        parent_gcs_uri = parent_item.gcs_uris[link.media_index]

        # Prepare tasks for both the main media and its thumbnail
        tasks = [
            asyncio.to_thread(
                self.iam_signer_credentials.generate_presigned_url,
                parent_gcs_uri,
            )
        ]

        parent_thumbnail_gcs_uri = None
        if parent_item.thumbnail_uris and 0 <= link.media_index < len(
            parent_item.thumbnail_uris
        ):
            parent_thumbnail_gcs_uri = parent_item.thumbnail_uris[
                link.media_index
            ]
            tasks.append(
                asyncio.to_thread(
                    self.iam_signer_credentials.generate_presigned_url,
                    parent_thumbnail_gcs_uri,
                )
            )

        results = await asyncio.gather(*tasks)
        presigned_url = results[0]
        presigned_thumbnail_url = results[1] if len(results) > 1 else None

        return SourceMediaItemLinkResponse(
            **link.model_dump(),
            presigned_url=presigned_url,
            presigned_thumbnail_url=presigned_thumbnail_url,
            gcs_uri=parent_gcs_uri,
        )

    async def _create_gallery_response(
        self, item: MediaItemModel
    ) -> MediaItemResponse:
        """
        Helper function to convert a MediaItem into a GalleryItemResponse
        by generating presigned URLs in parallel for its GCS URIs.
        """
        all_gcs_uris = item.gcs_uris or []

        # 1. Create tasks for main media URLs
        main_url_tasks = [
            asyncio.to_thread(
                self.iam_signer_credentials.generate_presigned_url, uri
            )
            for uri in all_gcs_uris
            if uri
        ]

        # 1.5 Create tasks for original media URLs
        all_original_gcs_uris = item.original_gcs_uris or []
        original_url_tasks = [
            asyncio.to_thread(
                self.iam_signer_credentials.generate_presigned_url, uri
            )
            for uri in all_original_gcs_uris
            if uri
        ]

        # 2. Create tasks for thumbnail URLs
        thumbnail_tasks = [
            asyncio.to_thread(
                self.iam_signer_credentials.generate_presigned_url, uri
            )
            for uri in (item.thumbnail_uris or "")
            if uri
        ]

        # 3. Create tasks for source asset URLs
        source_asset_tasks = []
        if item.source_assets:
            source_asset_tasks = [
                self._enrich_source_asset_link(link)
                for link in item.source_assets
            ]

        # 4. Create tasks for generated input asset URLs
        source_media_item_tasks = []
        if item.source_media_items:
            source_media_item_tasks = [
                self._enrich_source_media_item_link(link)
                for link in item.source_media_items
            ]

        # 5. Gather all results concurrently
        (
            presigned_urls,
            original_presigned_urls,
            presigned_thumbnail_urls,
            enriched_source_assets_with_nones,
            enriched_source_media_items_with_nones,
        ) = await asyncio.gather(
            asyncio.gather(*main_url_tasks),
            asyncio.gather(*original_url_tasks),
            asyncio.gather(*thumbnail_tasks),
            asyncio.gather(*source_asset_tasks),
            asyncio.gather(*source_media_item_tasks),
        )

        enriched_source_assets = [
            asset for asset in enriched_source_assets_with_nones if asset
        ]
        enriched_source_media_items = [
            asset for asset in enriched_source_media_items_with_nones if asset
        ]

        # Create the response DTO, copying all original data and adding the new URLs
        return MediaItemResponse(
            **item.model_dump(exclude={"source_assets"}),
            presigned_urls=presigned_urls,
            original_presigned_urls=original_presigned_urls,
            presigned_thumbnail_urls=presigned_thumbnail_urls,
            enriched_source_media_items=enriched_source_media_items or None,
        )

    async def _enrich_unified_item(
        self, item: UnifiedGalleryItemResponse
    ) -> UnifiedGalleryItemResponse:
        """
        Enriches a UnifiedGalleryItemResponse with presigned URLs.
        """
        
        # Helper to safely get list or string as list
        def as_list(val):
            if isinstance(val, list):
                return val
            return [val] if val else []

        uris_to_sign = []
        thumbnail_uris_to_sign = []
        
        uris_to_sign = item.gcs_uris or []
        thumbnail_uris_to_sign = item.thumbnail_uris or []

        # Create tasks
        url_tasks = [
             asyncio.to_thread(
                self.iam_signer_credentials.generate_presigned_url, uri
            )
            for uri in uris_to_sign if uri
        ]
        
        thumbnail_tasks = [
             asyncio.to_thread(
                self.iam_signer_credentials.generate_presigned_url, uri
            )
            for uri in thumbnail_uris_to_sign if uri
        ]
        
        (presigned_urls, presigned_thumbnail_urls) = await asyncio.gather(
            asyncio.gather(*url_tasks),
            asyncio.gather(*thumbnail_tasks)
        )
        
        item.presigned_urls = presigned_urls
        item.presigned_thumbnail_urls = presigned_thumbnail_urls
        return item

    async def get_paginated_gallery(
        self, search_dto: GallerySearchDto, current_user: UserModel
    ) -> PaginationResponseDto[UnifiedGalleryItemResponse]:
        """
        Performs a paginated and filtered search for media items.
        Authorization is handled by a dependency in the controller.
        """
        is_admin = UserRoleEnum.ADMIN in current_user.roles
        # If the user is not an admin, force the search to only show completed items
        if not is_admin:
            search_dto.status = JobStatusEnum.COMPLETED
        
        user_id = None
        if search_dto.user_email:
            user = await self.user_repo.get_by_email(search_dto.user_email)
            if user:
                user_id = user.id

        # Run the database query directly (it is async)
        # We assume UnifiedGalleryRepository.query handles user_id filtering
        unified_items_query = await self.unified_gallery_repo.query(
            search_dto,
            user_id=user_id,
        )
        unified_items = unified_items_query.data or []

        # Convert each MediaItem to a GalleryItemResponse in parallel
        response_tasks = [
            self._enrich_unified_item(item) for item in unified_items
        ]
        enriched_items = await asyncio.gather(*response_tasks)

        return PaginationResponseDto[UnifiedGalleryItemResponse](
            count=unified_items_query.count,
            page=unified_items_query.page,
            page_size=unified_items_query.page_size,
            total_pages=unified_items_query.total_pages,
            data=enriched_items,
        )

    async def get_media_by_id(
        self, item_id: int, current_user: UserModel
    ) -> Optional[MediaItemResponse]:
        """
        Retrieves a single media item, performs an authorization check,
        and enriches it with presigned URLs.
        """
        # Run the synchronous database query in a separate thread
        item = await self.media_repo.get_by_id(item_id)

        if not item:
            return None

        # Fetch the workspace for authorization check
        workspace = await self.workspace_repo.get_by_id(item.workspace_id)

        # This should ideally not happen if data is consistent, but it's a good safeguard.
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent workspace for this item not found.",
            )

        # Use the centralized authorization logic
        await self.workspace_auth.authorize(
            workspace_id=item.workspace_id,
            user=current_user,
        )

        return await self._create_gallery_response(item)

    async def bulk_delete(
        self, bulk_delete_dto: BulkDeleteDto, current_user: UserModel
    ) -> dict:
        """
        Deletes multiple gallery items after authorizing the workspace access.
        """
        # 1. Authorize workspace access
        await self.workspace_auth.authorize(
            workspace_id=bulk_delete_dto.workspace_id,
            user=current_user,
        )

        deleted_count = 0
        for item in bulk_delete_dto.items:
            try:
                if item.type == "media_item":
                    # Check if user owns it or is admin
                    media_item = await self.media_repo.get_by_id(item.id)
                    if not media_item:
                        continue
                        
                    is_admin = UserRoleEnum.ADMIN in current_user.roles
                    if media_item.user_id != current_user.id and not is_admin:
                        logger.warning(f"User {current_user.id} unauthorized to delete media {item.id}")
                        continue

                    await self.media_repo.soft_delete(item.id, deleted_by=current_user.id)
                    deleted_count += 1
                elif item.type == "source_asset":
                    asset = await self.source_asset_repo.get_by_id(item.id)
                    if not asset:
                        continue
                        
                    is_admin = UserRoleEnum.ADMIN in current_user.roles
                    if asset.user_id != current_user.id and not is_admin:
                         logger.warning(f"User {current_user.id} unauthorized to delete asset {item.id}")
                         continue

                    await self.source_asset_repo.soft_delete(item.id, deleted_by=current_user.id)
                    deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting {item.type} {item.id}: {e}")

        return {"deleted_count": deleted_count}

    async def bulk_download(
        self, bulk_download_dto: BulkDownloadDto, current_user: UserModel
    ) -> StreamingResponse:
        """
        Creates a ZIP archive of the selected media items and streams it to the client.
        """
        # 1. Authorize workspace access
        await self.workspace_auth.authorize(
            workspace_id=bulk_download_dto.workspace_id,
            user=current_user,
        )

        zip_buffer = io.BytesIO()
        gcs_service = GcsService()

        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for item in bulk_download_dto.items:
                try:
                    gcs_uri = None
                    filename = None
                    
                    if item.type == "media_item":
                        media_item = await self.media_repo.get_by_id(item.id)
                        if media_item and media_item.gcs_uris:
                            gcs_uri = media_item.gcs_uris[0]
                            # Use mime_type to determine extension
                            ext = "bin"
                            mime_type = getattr(media_item, "mime_type", None)
                            if mime_type:
                                mime_str = str(mime_type)
                                if "image/png" in mime_str: ext = "png"
                                elif "image/jpeg" in mime_str: ext = "jpg"
                                elif "video/mp4" in mime_str: ext = "mp4"
                                elif "audio/mpeg" in mime_str: ext = "mp3"
                                elif "audio/wav" in mime_str: ext = "wav"
                                elif "/" in mime_str:
                                    ext = mime_str.split("/")[-1]
                            
                            if ext == "bin" and "." in gcs_uri:
                                ext = gcs_uri.split(".")[-1]
                                
                            filename = f"media_{item.id}.{ext}"
                    elif item.type == "source_asset":
                        asset = await self.source_asset_repo.get_by_id(item.id)
                        if asset and asset.gcs_uri:
                            gcs_uri = asset.gcs_uri
                            ext = gcs_uri.split('.')[-1] if '.' in gcs_uri else 'bin'
                            filename = f"asset_{item.id}.{ext}"

                    if gcs_uri and filename:
                        content = gcs_service.download_bytes_from_gcs(gcs_uri)
                        if content:
                            zip_file.writestr(filename, content)
                except Exception as e:
                    logger.error(f"Error adding {item.type} {item.id} to ZIP: {e}")

        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/x-zip-compressed",
            headers={"Content-Disposition": "attachment; filename=gallery_export.zip"}
        )

    async def bulk_copy(
        self, bulk_copy_dto: BulkCopyDto, current_user: UserModel
    ) -> dict:
        """
        Copies multiple gallery items to a target workspace.
        """
        # 1. Authorize target workspace access
        await self.workspace_auth.authorize(
            workspace_id=bulk_copy_dto.target_workspace_id,
            user=current_user,
        )

        copied_count = 0
        for item in bulk_copy_dto.items:
            try:
                if item.type == "media_item":
                    media_item = await self.media_repo.get_by_id(item.id)
                    if not media_item:
                        continue
                    
                    # Authorize source workspace access (where the item is currently)
                    await self.workspace_auth.authorize(
                        workspace_id=media_item.workspace_id,
                        user=current_user,
                    )

                    # Create a new MediaItem instance with updated workspace_id
                    # exclude 'id', 'created_at', 'updated_at', 'deleted_at', 'deleted_by'
                    new_item_data = media_item.model_dump(
                        exclude={"id", "created_at", "updated_at", "deleted_at", "deleted_by", "workspace_id"}
                    )
                    new_item_data["workspace_id"] = bulk_copy_dto.target_workspace_id
                    
                    # Ensure user_id and user_email are set to the current user copying
                    new_item_data["user_id"] = current_user.id
                    new_item_data["user_email"] = current_user.email
                    
                    await self.media_repo.create(new_item_data)
                    copied_count += 1

                elif item.type == "source_asset":
                    asset = await self.source_asset_repo.get_by_id(item.id)
                    if not asset:
                        continue
                    
                    # Authorize source workspace access
                    await self.workspace_auth.authorize(
                        workspace_id=asset.workspace_id,
                        user=current_user,
                    )

                    # Create a new SourceAsset instance with updated workspace_id
                    new_asset_data = asset.model_dump(
                        exclude={"id", "created_at", "updated_at", "deleted_at", "deleted_by", "workspace_id"}
                    )
                    new_asset_data["workspace_id"] = bulk_copy_dto.target_workspace_id
                    
                    # Ensure user_id is set to the current user copying
                    new_asset_data["user_id"] = current_user.id
                    
                    await self.source_asset_repo.create(new_asset_data)
                    copied_count += 1

            except Exception as e:
                logger.error(f"Error copying {item.type} {item.id}: {e}")

        return {"copied_count": copied_count}
    