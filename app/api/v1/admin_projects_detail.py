from fastapi import APIRouter, Depends, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.core.security import require_admin_auth
from app.models.project import Project
from app.models.project_milestone import ProjectMilestone
from app.models.project_credentials import ProjectCredentials
from sqlalchemy import select

router = APIRouter(
    prefix="/admin/projects",
    tags=["Admin Project Detail"],
    dependencies=[Depends(require_admin_auth)]
)

@router.get("/{project_id}")
async def view_project(
    request: Request,
    project_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_session)
):
    project = await session.get(Project, project_id)
    if not project:
        return {"error": "Project not found"}

    # ORM query for milestones
    ms = await session.execute(
        select(ProjectMilestone)
        .where(ProjectMilestone.project_id == project_id)
        .order_by(ProjectMilestone.sort_order)
        .limit(50)
    )
    milestones = ms.scalars().all()

    # ORM query for creds
    cr = await session.execute(
        select(ProjectCredentials)
        .where(ProjectCredentials.project_id == project_id)
        .limit(1)
    )
    creds = cr.scalars().first()

    return {
        "project": project,
        "milestones": milestones,
        "creds": creds
    }
