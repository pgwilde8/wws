from fastapi import APIRouter, Depends, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.templating import Jinja2Templates

from app.db.session import get_session
from app.core.security import require_admin_auth

router = APIRouter(
    prefix="/admin/calls",
    tags=["Admin Calls"],
    dependencies=[Depends(require_admin_auth)],
)
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def list_calls(request: Request, session: AsyncSession = Depends(get_session)):
    res = await session.execute(
        text(
            """
            SELECT id, name, email, phone, preferred_date, preferred_time, timezone, message, status, created_at
            FROM support_calls
            ORDER BY created_at DESC
            LIMIT 50
            """
        )
    )
    calls = [dict(r) for r in res.mappings().all()]
    return templates.TemplateResponse(
        "admin/calls.html",
        {"request": request, "calls": calls},
    )


@router.get("/{call_id}")
async def call_detail(
    request: Request,
    call_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_session),
):
    res = await session.execute(
        text(
            """
            SELECT id, name, email, phone, preferred_date, preferred_time, timezone, message, status, created_at
            FROM support_calls
            WHERE id = :cid
            LIMIT 1
            """
        ),
        {"cid": call_id},
    )
    row = res.mappings().first()
    return templates.TemplateResponse(
        "admin/call_detail.html",
        {"request": request, "call": dict(row) if row else None},
    )
from fastapi import APIRouter, Depends, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.core.security import require_admin_auth
from math import ceil

router = APIRouter(prefix="/admin/calls", tags=["Admin Calls"], dependencies=[Depends(require_admin_auth)])

@router.get("")
async def list_calls(
    request: Request,
    page: int = Query(1, ge=1),
    search: str = Query("", max_length=100),
    client_id: int = Query(None),
    project_id: int = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Contract: Return call bookings + pagination
    """
    q = f"%{search}%"
    offset = (page - 1) * 12

    sql = "SELECT * FROM call_bookings WHERE client_name ILIKE :q"
    params = {"q": q, "offset": offset}

    if client_id:
        sql += " AND client_id = :cid"
        params["cid"] = client_id

    if project_id:
        sql += " AND project_id = :pid"
        params["pid"] = project_id

    sql += " ORDER BY received_at DESC LIMIT 12 OFFSET :offset"

    result = await session.execute(sql, params)
    calls = result.scalars().all()

    # Count total pages
    count_sql = "SELECT COUNT(*) FROM call_bookings WHERE client_name ILIKE :q"
    if client_id:
        count_sql += " AND client_id = :cid"
    if project_id:
        count_sql += " AND project_id = :pid"

    count_result = await session.execute(count_sql, params)
    total = count_result.scalar() or 0
    total_pages = ceil(total / 12)

    return {
        "calls": calls,
        "page": page,
        "search": search,
        "total_pages": total_pages
    }

@router.get("/{call_id}")
async def call_detail(
    request: Request,
    call_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_session)
):
    """
    Contract: Load 1 call booking (detail page rendered separately)
    """
    call = await session.get(Project, call_id)
    if not call:
        return {"error": "Call booking not found"}

    return {"call": call}
