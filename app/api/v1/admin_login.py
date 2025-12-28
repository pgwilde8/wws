from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import hashlib

from app.db.session import get_session
from app.middleware.auth import signer

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin/login")
async def admin_login(request: Request):
    return templates.TemplateResponse("admin/admin-login.html", {"request": request})


@router.get("/admin/dashboard")
async def admin_dashboard_page(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    # Stats
    total_clients = (await db.execute(text("SELECT COUNT(*) FROM clients"))).scalar() or 0
    total_projects = (await db.execute(text("SELECT COUNT(*) FROM projects"))).scalar() or 0
    total_orders = (await db.execute(text("SELECT COUNT(*) FROM orders"))).scalar() or 0
    active_subs = 0

    # Recent webhook events
    events_res = await db.execute(
        text(
            """
            SELECT event_type, status
            FROM webhook_events
            ORDER BY received_at DESC
            LIMIT 5
            """
        )
    )
    recent_events = [dict(r) for r in events_res.mappings().all()]

    # Client preview with open support counts
    clients_res = await db.execute(
        text(
            """
            SELECT
              c.id,
              c.name,
              c.email,
              ''::text AS phone,
              COALESCE(t.open_count, 0) AS open_support
            FROM clients c
            LEFT JOIN (
              SELECT client_id, COUNT(*) AS open_count
              FROM support_tickets
              WHERE status = 'open'
              GROUP BY client_id
            ) t ON t.client_id = c.id
            ORDER BY c.created_at DESC
            LIMIT 10
            """
        )
    )
    clients_preview = [dict(r) for r in clients_res.mappings().all()]

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "total_clients": total_clients,
            "total_projects": total_projects,
            "total_orders": total_orders,
            "active_subs": active_subs,
            "recent_events": recent_events,
            "clients_preview": clients_preview,
        },
    )


@router.post("/admin/login")
async def admin_login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    res = await db.execute(
        text(
            """
            SELECT id, hashed_password
            FROM users
            WHERE email = :email AND role = 'admin'
            LIMIT 1
            """
        ),
        {"email": email},
    )
    row = res.mappings().first()
    if not row:
        return RedirectResponse("/admin/login?error=invalid", status_code=303)

    incoming_hash = hashlib.sha256(password.encode()).hexdigest()
    if row["hashed_password"] != incoming_hash:
        return RedirectResponse("/admin/login?error=invalid", status_code=303)

    token = signer.sign(str(row["id"])).decode()
    resp = RedirectResponse("/admin/dashboard", status_code=303)
    resp.set_cookie(
        "admin_session",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return resp

