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
"""API endpoints for workbench."""


import logging
import shutil

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from src.workbench.schemas import TimelineRequest
from src.workbench.service import WorkbenchService

router = APIRouter(
    prefix="/api/workbench",
    tags=["workbench"],
)

logger = logging.getLogger(__name__)


def cleanup_temp_dir(path: str):
    try:
        shutil.rmtree(path)
        logger.info("Cleaned up temp dir: %s", path)
    except Exception as e:
        logger.error("Failed to cleanup temp dir %s: %s", path, e)


@router.post("/render")
async def render_timeline(
    request: TimelineRequest,
    service: WorkbenchService = Depends(),
):
    video_path, temp_dir = await service.render_timeline(request)

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename="export.mp4",
        background=BackgroundTask(cleanup_temp_dir, temp_dir),
    )
