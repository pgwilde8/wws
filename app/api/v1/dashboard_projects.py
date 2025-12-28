from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi.templating import Jinja2Templates
from app.db.session import get_session
from app.models.project import Project


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/projects")
async def client_projects(
    request: Request,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_session)
):
    per_page = 9
    offset = (page - 1) * per_page

    total = (await db.execute(select(func.count(Project.id)))).scalar()
    projects = (
        await db.execute(
            select(Project)
            .order_by(Project.updated_at.desc())
            .offset(offset)
            .limit(per_page)
        )
    ).scalars().all()

    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse(
        "dashboard/project_overview.html",
        {
            "request": request,
            "projects": projects,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        }
    )
