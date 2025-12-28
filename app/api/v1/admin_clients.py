from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from types import SimpleNamespace
from app.db.session import get_session
from fastapi.templating import Jinja2Templates

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

# ADMIN DASHBOARD (client-focused)
@router.get("/admin")
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    # Replace these with real queries later
    total_clients = (await db.execute(select(func.count(Client.id)))).scalar()
    total_projects = (await db.execute(select(func.count()).select_from(Client.projects))).scalar()

    return templates.TemplateResponse("dashboard/dashboard.html", {
        "request": request,
        "total_clients": total_clients or 0,
        "total_projects": total_projects or 0,
    })

# Admin Clients listing page
@router.get("/admin/clients")
async def list_clients(
    request: Request,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_session)
):
    per_page = 9
    offset = (page - 1) * per_page

    rows = await db.execute(
        text(
            """
            SELECT
              c.id,
              c.name,
              c.email,
              c.live_domain,
              c.domain_connected,
              c.stripe_account_id,
              c.created_at,
              COALESCE(t.open_count, 0) AS open_support
            FROM clients c
            LEFT JOIN (
              SELECT client_id, COUNT(*) AS open_count
              FROM support_tickets
              WHERE status = 'open'
              GROUP BY client_id
            ) t ON t.client_id = c.id
            ORDER BY c.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"limit": per_page, "offset": offset},
    )
    data = [SimpleNamespace(**dict(r)) for r in rows.mappings().all()]

    total_res = await db.execute(text("SELECT COUNT(*) FROM clients"))
    total = total_res.scalar() or 0
    total_pages = max(1, (total + per_page - 1) // per_page)

    return templates.TemplateResponse("admin/clients.html", {
        "request": request,
        "clients": data,
        "page": page,
        "total_pages": total_pages,
    })
