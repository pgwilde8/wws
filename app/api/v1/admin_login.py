from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import hashlib

import os

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
    
    # Pending testimonials count
    pending_testimonials_count = (
        await db.execute(text("SELECT COUNT(*) FROM testimonials WHERE approved = false"))
    ).scalar() or 0

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

    openai_admin_key = os.getenv("OPENAI_ADMIN_KEY") or os.getenv("OPENAI_MASTER_ADMIN_KEY")
    openai_admin_configured = bool((openai_admin_key or "").strip())

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "total_clients": total_clients,
            "total_projects": total_projects,
            "total_orders": total_orders,
            "active_subs": active_subs,
            "pending_testimonials_count": pending_testimonials_count,
            "recent_events": recent_events,
            "clients_preview": clients_preview,
            "openai_admin_configured": openai_admin_configured,
            "openai_project_label": os.getenv("OPENAI_PROJECT_LABEL", "ClosingPitch_Prod (env)"),
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


async def _get_admin_id(request: Request, db: AsyncSession) -> int:
    """
    Helper to extract authenticated admin user ID from admin_session cookie.
    Raises HTTPException if not authenticated or not admin.
    """
    cookie = request.cookies.get("admin_session")
    if not cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        admin_id = int(signer.unsign(cookie).decode())
        res = await db.execute(
            text("SELECT id FROM users WHERE id = :id AND role = 'admin' LIMIT 1"),
            {"id": admin_id},
        )
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not an admin user")
        return admin_id
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid session")
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.get("/admin/change-password")
async def admin_change_password_page(
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    """Render password change page for admin users."""
    # Verify admin authentication
    try:
        await _get_admin_id(request, db)
    except HTTPException:
        return RedirectResponse("/admin/login", status_code=303)
    
    return templates.TemplateResponse(
        "admin/change-password.html",
        {
            "request": request,
        },
    )


@router.post("/admin/change-password")
async def admin_change_password_post(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    """Handle password change for admin users."""
    
    # Get admin ID and verify authentication
    try:
        admin_id = await _get_admin_id(request, db)
    except HTTPException as e:
        return RedirectResponse("/admin/login", status_code=303)
    
    # Validate new password length
    if len(new_password) < 8:
        return RedirectResponse(
            "/admin/change-password?error=length",
            status_code=303
        )
    
    # Get current password hash from database
    res = await db.execute(
        text(
            """
            SELECT hashed_password
            FROM users
            WHERE id = :user_id AND role = 'admin'
            LIMIT 1
            """
        ),
        {"user_id": admin_id},
    )
    row = res.mappings().first()
    
    if not row:
        return RedirectResponse(
            "/admin/change-password?error=notfound",
            status_code=303
        )
    
    # Verify current password
    current_hash = hashlib.sha256(current_password.encode()).hexdigest()
    if row["hashed_password"] != current_hash:
        return RedirectResponse(
            "/admin/change-password?error=invalid",
            status_code=303
        )
    
    # Hash new password
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    # Update password in database
    await db.execute(
        text(
            """
            UPDATE users
            SET hashed_password = :new_hash
            WHERE id = :user_id AND role = 'admin'
            """
        ),
        {"user_id": admin_id, "new_hash": new_hash},
    )
    await db.commit()
    
    return RedirectResponse(
        "/admin/change-password?success=true",
        status_code=303
    )

