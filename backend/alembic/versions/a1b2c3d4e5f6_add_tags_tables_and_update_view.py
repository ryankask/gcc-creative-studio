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

"""add tags tables and update view

Revision ID: a1b2c3d4e5f6
Revises: e4b12d7ae0d3
Create Date: 2026-03-31 13:21:00.000000

"""

from collections.abc import Sequence
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "e4b12d7ae0d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create tags table
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "color", sa.String(), nullable=False, server_default="#E8EAED"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "name", "workspace_id", name="uq_tag_name_workspace"
        ),
    )

    # 2. Create media_item_tags table
    op.create_table(
        "media_item_tags",
        sa.Column("media_item_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["media_item_id"], ["media_items.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("media_item_id", "tag_id"),
    )

    # 3. Create source_asset_tags table
    op.create_table(
        "source_asset_tags",
        sa.Column("source_asset_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_asset_id"], ["source_assets.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("source_asset_id", "tag_id"),
    )

    # 4. Update unified_gallery_view to include tags (aggregated objects)
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
            'is_audio', (mi.mime_type like 'audio%'),
            'tags', (
                SELECT jsonb_agg(jsonb_build_object('id', t.id, 'name', t.name, 'color', t.color, 'workspace_id', t.workspace_id))
                FROM media_item_tags mit
                JOIN tags t ON mit.tag_id = t.id
                WHERE mit.media_item_id = mi.id
            )
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
            'is_audio', (sa.mime_type like 'audio%'),
            'tags', (
                SELECT jsonb_agg(jsonb_build_object('id', t.id, 'name', t.name, 'color', t.color, 'workspace_id', t.workspace_id))
                FROM source_asset_tags sat
                JOIN tags t ON sat.tag_id = t.id
                WHERE sat.source_asset_id = sa.id
            )
        ) AS metadata
    FROM source_assets sa
    JOIN users u ON sa.user_id = u.id;
    """,
    )


def downgrade() -> None:
    # 1. Revert unified_gallery_view to previous definition (without tags)
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

    # 2. Drop tables
    op.drop_table("source_asset_tags")
    op.drop_table("media_item_tags")
    op.drop_table("tags")
