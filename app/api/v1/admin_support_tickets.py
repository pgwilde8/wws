from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.templating import Jinja2Templates
from fastapi import Request

from app.db.session import get_session
from app.core.security import require_admin_auth

router = APIRouter(prefix="/admin/support", tags=["Admin Support"], dependencies=[Depends(require_admin_auth)])
templates = Jinja2Templates(directory="app/templates")


@router.get("/client/{client_id}")
async def support_list_for_client(
    request: Request,
    client_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_session),
):
    res = await db.execute(
        text(
            """
            SELECT id, subject, status, priority, created_at, updated_at
            FROM support_tickets
            WHERE client_id = :cid
            ORDER BY updated_at DESC
            """
        ),
        {"cid": client_id},
    )
    tickets = [dict(r) for r in res.mappings().all()]
    return templates.TemplateResponse(
        "admin/support_inbox.html",
        {"request": request, "tickets": tickets, "client_id": client_id},
    )


@router.get("/tickets/{ticket_id}")
async def support_ticket_detail(
    request: Request,
    ticket_id: int = Path(..., ge=1),
    db: AsyncSession = Depends(get_session),
):
    # Ticket
    res = await db.execute(
        text(
            """
            SELECT id, client_id, project_id, subject, status, priority, created_at, updated_at
            FROM support_tickets
            WHERE id = :tid
            LIMIT 1
            """
        ),
        {"tid": ticket_id},
    )
    ticket = res.mappings().first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Messages
    res2 = await db.execute(
        text(
            """
            SELECT id, ticket_id, sender, message, created_at
            FROM support_messages
            WHERE ticket_id = :tid
            ORDER BY created_at DESC
            """
        ),
        {"tid": ticket_id},
    )
    messages = [dict(r) for r in res2.mappings().all()]

    return templates.TemplateResponse(
        "admin/support_detail.html",
        {"request": request, "ticket": dict(ticket), "messages": messages},
    )


@router.post("/tickets/{ticket_id}/reply")
async def admin_reply(
    ticket_id: int = Path(..., ge=1),
    message: str = "",
    db: AsyncSession = Depends(get_session),
):
    body = (message or "").strip()
    if not body:
        raise HTTPException(status_code=400, detail="Message required")

    try:
        await db.execute(
            text(
                """
                INSERT INTO support_messages (ticket_id, sender, message, created_at)
                VALUES (:tid, 'admin', :msg, NOW())
                """
            ),
            {"tid": ticket_id, "msg": body},
        )
        await db.execute(
            text(
                """
                UPDATE support_tickets
                SET status = 'open', updated_at = NOW()
                WHERE id = :tid
                """
            ),
            {"tid": ticket_id},
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Could not save reply") from exc

    return {"status": "ok"}

