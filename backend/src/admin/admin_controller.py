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

from fastapi import APIRouter, Depends
from src.auth.auth_guard import RoleChecker
from src.users.user_model import UserRoleEnum
from src.admin.admin_service import AdminService
from src.admin.dto.admin_response_dto import (
    AdminOverviewStats,
    AdminMediaOverTime,
    AdminWorkspaceStats,
    AdminActiveRole,
    AdminGenerationHealth,
    AdminMonthlyActiveUsers,
)

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin Dashboard"],
    dependencies=[Depends(RoleChecker(allowed_roles=[UserRoleEnum.ADMIN]))],
)


@router.get("/overview-stats", response_model=AdminOverviewStats)
async def get_overview_stats(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    return await admin_service.get_overview_stats(
        start_date=start_date, end_date=end_date
    )


@router.get("/media-over-time", response_model=list[AdminMediaOverTime])
async def get_media_over_time(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    return await admin_service.get_media_over_time(
        start_date=start_date, end_date=end_date
    )


@router.get("/workspace-stats", response_model=list[AdminWorkspaceStats])
async def get_workspace_stats(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    return await admin_service.get_workspace_stats(
        start_date=start_date, end_date=end_date
    )


@router.get("/active-roles", response_model=list[AdminActiveRole])
async def get_active_roles(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    return await admin_service.get_active_roles(
        start_date=start_date, end_date=end_date
    )


@router.get("/generation-health", response_model=list[AdminGenerationHealth])
async def get_generation_health(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    return await admin_service.get_generation_health(
        start_date=start_date, end_date=end_date
    )


@router.get(
    "/active-users-monthly", response_model=list[AdminMonthlyActiveUsers]
)
async def get_active_users_monthly(
    start_date: str | None = None,
    end_date: str | None = None,
    admin_service: AdminService = Depends(),
):
    return await admin_service.get_active_users_monthly(
        start_date=start_date, end_date=end_date
    )


@router.post("/cleanup-stuck-jobs")
async def cleanup_stuck_jobs(admin_service: AdminService = Depends()):
    count = await admin_service.cleanup_stuck_jobs()
    return {"message": f"Cleaned up {count} stuck jobs", "count": count}
