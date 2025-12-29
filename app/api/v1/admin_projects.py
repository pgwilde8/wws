from fastapi import APIRouter, Depends, Request, Query, Path
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
import math

from app.db.session import get_session
from app.core.security import require_admin_auth
from app.models.project import Project

router = APIRouter(
    prefix="/admin/projects",
    tags=["Admin Projects"],
    dependencies=[Depends(require_admin_auth)]
)

templates = Jinja2Templates(directory="app/templates")

# JSON API for UI fetch()
@router.get("/api")
async def list_projects_api(
    page: int = 1,
    search: str = Query("", max_length=100),
    status: str = "",
    tier: str = "",
    session: AsyncSession = Depends(get_session)
):
    limit = 12
    offset = (page - 1) * limit
    q = f"%{search}%"

    stmt = text("""
        SELECT id, client_id, name, description, status, plan_tier, total_budget, created_at, updated_at,
               COUNT(*) OVER() AS total
        FROM projects
        WHERE name ILIKE :q
          AND (:status = '' OR status = :status)
          AND (:tier = '' OR plan_tier = :tier)
        ORDER BY updated_at DESC
        LIMIT :limit OFFSET :offset
    """)

    result = await session.execute(stmt, {
        "q": q,
        "status": status,
        "tier": tier,
        "limit": limit,
        "offset": offset
    })
    rows = result.mappings().all()

    total = rows[0]["total"] if rows else 0
    total_pages = math.ceil(total / limit) if total else 1

    return {
        "projects": rows,
        "page": page,
        "total_pages": total_pages,
        "total": total
    }

# HTML page route (UI render)
@router.get("")
async def projects_page(
    request: Request,
    page: int = 1,
    search: str = Query("", max_length=100),
    status: str = "",
    tier: str = "",
    session: AsyncSession = Depends(get_session)
):
    limit = 12
    offset = (page - 1) * limit
    q = f"%{search}%"

    # Simple text query to fetch projects with status and domain
    rows = await session.execute(
        text(
            """
            SELECT id, client_id, name, status, plan_tier, updated_at, created_at,
                   COUNT(*) OVER() AS total
            FROM projects
            WHERE name ILIKE :q
              AND (:status = '' OR status = :status)
              AND (:tier = '' OR plan_tier = :tier)
            ORDER BY updated_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"q": q, "status": status, "tier": tier, "limit": limit, "offset": offset},
    )
    projects = rows.mappings().all()
    total = projects[0]["total"] if projects else 0
    total_pages = math.ceil(total / limit) if total else 1

    return templates.TemplateResponse(
        "admin/projects.html",
        {
            "request": request,
            "projects": projects,
            "page": page,
            "search": search,
            "status": status,
            "tier": tier,
            "total_pages": total_pages,
            "total": total,
        },
    )

# Update project status
@router.patch("/{project_id}/status")
async def update_project_status(
    project_id: int = Path(..., ge=1),
    status: str = Query(..., max_length=30),
    session: AsyncSession = Depends(get_session)
):
    project = await session.get(Project, project_id)
    if not project:
        return {"error": "Project not found"}

    project.status = status
    await session.commit()
    return {"success": True, "status": status}

# Archive project
@router.patch("/{project_id}/archive")
async def archive_project(
    project_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_session)
):
    project = await session.get(Project, project_id)
    if not project:
        return {"error": "Project not found"}

    project.status = "archived"
    await session.commit()
    return {"success": True, "archived": True}

# Delete project
@router.delete("/{project_id}")
async def delete_project(
    project_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_session)
):
    project = await session.get(Project, project_id)
    if not project:
        return {"error": "Project not found"}

    await session.delete(project)
    await session.commit()
    return {"success": True}

