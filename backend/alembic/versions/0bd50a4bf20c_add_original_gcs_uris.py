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

"""add_original_gcs_uris

Revision ID: 0bd50a4bf20c
Revises: 9393a3d298c6
Create Date: 2026-01-29 12:53:26.493393

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0bd50a4bf20c"
down_revision: str | None = "9393a3d298c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    media_columns = [c["name"] for c in inspector.get_columns("media_items")]
    if "original_gcs_uris" not in media_columns:
        op.add_column(
            "media_items",
            sa.Column(
                "original_gcs_uris", sa.ARRAY(sa.String()), nullable=True
            ),
        )

    source_columns = [c["name"] for c in inspector.get_columns("source_assets")]
    if "original_gcs_uri" not in source_columns:
        op.add_column(
            "source_assets",
            sa.Column("original_gcs_uri", sa.String(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("source_assets", "original_gcs_uri")
    op.drop_column("media_items", "original_gcs_uris")
