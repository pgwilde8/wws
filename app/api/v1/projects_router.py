from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.project import Project
from sqlalchemy import select, func
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/projects")
async def admin_projects(
    request: Request,
    page: int = Query(1, ge=1),
    status: str | None = None,
    tier: str | None = None,
    client: str | None = None,
    db: AsyncSession = Depends(get_session)
):
    per_page = 9
    offset = (page - 1) * per_page

    query = select(Project)
    count_query = select(func.count(Project.id))

    if status:
        query = query.where(Project.status == status)
        count_query = count_query.where(Project.status == status)

    if tier:
        query = query.where(Project.plan_tier == tier)
        count_query = count_query.where(Project.plan_tier == tier)

    query = query.offset(offset).limit(per_page)

    total = (await db.execute(count_query)).scalar() or 0
    projects = (await db.execute(query)).scalars().all()

    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse(
        "admin/projects.html",
        {
            "request": request,
            "projects": projects,
            "page": page,
            "total_pages": total_pages,
            "total": total,
        }
    )

@router.get("/")
async def api_list_projects(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Project).order_by(Project.updated_at.desc()))
    return {"projects": result.scalars().all()}
