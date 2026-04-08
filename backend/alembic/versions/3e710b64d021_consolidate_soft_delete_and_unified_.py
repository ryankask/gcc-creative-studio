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

"""consolidate soft delete and unified gallery changes

Revision ID: 3e710b64d021
Revises: f214a6d75867
Create Date: 2026-03-05 18:42:06.661301

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3e710b64d021"
down_revision: str | None = "f214a6d75867"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add soft delete columns
    op.add_column(
        "media_items",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "media_items", sa.Column("deleted_by", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "media_items_deleted_by_fkey",
        "media_items",
        "users",
        ["deleted_by"],
        ["id"],
    )

    op.add_column(
        "source_assets",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "source_assets", sa.Column("deleted_by", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "source_assets_deleted_by_fkey",
        "source_assets",
        "users",
        ["deleted_by"],
        ["id"],
    )

    # 2. Update unified gallery view
    op.execute("DROP VIEW IF EXISTS unified_gallery_view;")
    op.execute(
        """
    CREATE VIEW unified_gallery_view AS
    SELECT
        mi.id,
        mi.workspace_id,
        mi.user_id,
        mi.created_at,
        'media_item'::text AS item_type,
        mi.status,
        mi.gcs_uris,
        mi.thumbnail_uris,
        mi.deleted_at,
        jsonb_build_object(
            'model', mi.model,
            'prompt', mi.prompt,
            'original_prompt', mi.original_prompt,
            'negative_prompt', mi.negative_prompt,
            'aspect_ratio', mi.aspect_ratio,
            'mime_type', mi.mime_type,
            'style', mi.style,
            'lighting', mi.lighting,
            'num_media', mi.num_media,
            'generation_time', mi.generation_time,
            'user_email', mi.user_email,
            'is_video', (mi.mime_type like 'video%'),
            'is_audio', (mi.mime_type like 'audio%')
        ) AS metadata
    FROM media_items mi
    UNION ALL
    SELECT
        sa.id,
        sa.workspace_id,
        sa.user_id,
        sa.created_at,
        'source_asset'::text AS item_type,
        'completed'::text AS status,
        ARRAY[sa.gcs_uri] AS gcs_uris,
        CASE
            WHEN (sa.thumbnail_gcs_uri IS NOT NULL) THEN ARRAY[sa.thumbnail_gcs_uri]
            ELSE '{}'::text[]
        END AS thumbnail_uris,
        sa.deleted_at,
        jsonb_build_object(
            'original_filename', sa.original_filename,
            'mime_type', sa.mime_type,
            'aspect_ratio', sa.aspect_ratio,
            'asset_type', sa.asset_type,
            'user_email', u.email,
            'is_video', (sa.mime_type like 'video%'),
            'is_audio', (sa.mime_type like 'audio%')
        ) AS metadata
    FROM source_assets sa
    JOIN users u ON sa.user_id = u.id;
    """,
    )


def downgrade() -> None:
    # 1. Revert unified gallery view to original definition (from f214a6d75867)
    op.execute("DROP VIEW IF EXISTS unified_gallery_view;")
    op.execute(
        """
    CREATE VIEW unified_gallery_view AS
    SELECT
        id,
        workspace_id,
        user_id,
        created_at,
        'media_item'::text as item_type,
        status,
        gcs_uris,
        thumbnail_uris,
        jsonb_build_object(
            'model', model,
            'prompt', prompt,
            'negative_prompt', negative_prompt,
            'aspect_ratio', aspect_ratio,
            'mime_type', mime_type,
            'style', style,
            'lighting', lighting,
            'num_media', num_media,
            'duration_seconds', duration_seconds,
            'is_video', (mime_type like 'video%'),
            'is_audio', (mime_type like 'audio%')
        ) as metadata
    FROM media_items
    UNION ALL
    SELECT
        id,
        workspace_id,
        user_id,
        created_at,
        'source_asset'::text as item_type,
        'completed'::text as status,
        ARRAY[gcs_uri] as gcs_uris,
        CASE WHEN thumbnail_gcs_uri IS NOT NULL THEN ARRAY[thumbnail_gcs_uri] ELSE '{}'::text[] END as thumbnail_uris,
        jsonb_build_object(
            'original_filename', original_filename,
            'mime_type', mime_type,
            'aspect_ratio', aspect_ratio,
            'asset_type', asset_type,
            'is_video', (mime_type like 'video%'),
            'is_audio', (mime_type like 'audio%')
        ) as metadata
    FROM source_assets;
    """,
    )

    # 2. Drop soft delete columns and constraints
    op.drop_constraint(
        "source_assets_deleted_by_fkey",
        "source_assets",
        type_="foreignkey",
    )
    op.drop_column("source_assets", "deleted_by")
    op.drop_column("source_assets", "deleted_at")

    op.drop_constraint(
        "media_items_deleted_by_fkey", "media_items", type_="foreignkey"
    )
    op.drop_column("media_items", "deleted_by")
    op.drop_column("media_items", "deleted_at")
