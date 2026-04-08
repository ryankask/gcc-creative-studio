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
from typing import Any

from pydantic import Field
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.common.base_repository import BaseStringDocument
from src.database import Base
from src.workflows.schema.workflow_model import WorkflowRunStatusEnum


class WorkflowRun(Base):
    """SQLAlchemy model for the 'workflow_runs' table.
    Stores the execution history and the snapshot of the workflow definition.
    """

    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    workspace_id: Mapped[int] = mapped_column(
        nullable=True,
    )  # Denormalized if needed, or linked to workspace table? Keeping generic int for now.

    status: Mapped[str] = mapped_column(
        String,
        default=WorkflowRunStatusEnum.RUNNING.value,
        nullable=False,
    )

    workflow_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False
    )

    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        insert_default=func.now(),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class WorkflowRunModel(BaseStringDocument):
    """Pydantic model for Workflow Execution, including the snapshot."""

    workflow_id: str
    user_id: int
    workspace_id: int | None = None
    status: WorkflowRunStatusEnum = Field(default=WorkflowRunStatusEnum.RUNNING)
    started_at: datetime.datetime
    completed_at: datetime.datetime | None = None

    workflow_snapshot: dict[str, Any]
