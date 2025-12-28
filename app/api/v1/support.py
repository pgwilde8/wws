from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_session
from app.middleware.auth import _get_client_id

router = APIRouter()


class SupportMessagePayload(BaseModel):
    subject: str
    message: str
    priority: str | None = None


async def _get_client_project(db: AsyncSession, client_id: int) -> int | None:
    res = await db.execute(
        text("SELECT id FROM projects WHERE client_id = :cid LIMIT 1"),
        {"cid": client_id},
    )
    row = res.mappings().first()
    return row["id"] if row else None


@router.post("/support/tickets")
async def create_support_ticket(
    payload: SupportMessagePayload,
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    body = payload.message.strip()
    subject = payload.subject.strip()
    priority = (payload.priority or "normal").lower()

    # Create support_tickets row and a first support_messages row
    try:
        project_id = await _get_client_project(db, client_id)
        res = await db.execute(
            text(
                """
                INSERT INTO support_tickets (client_id, project_id, subject, status, priority, created_at, updated_at)
                VALUES (:cid, :pid, :subject, 'open', :priority, NOW(), NOW())
                RETURNING id
                """
            ),
            {"cid": client_id, "pid": project_id, "subject": subject, "priority": priority},
        )
        ticket_id = res.scalar_one()

        await db.execute(
            text(
                """
                INSERT INTO support_messages (ticket_id, sender, message, created_at)
                VALUES (:tid, 'client', :message, NOW())
                """
            ),
            {"tid": ticket_id, "message": body},
        )

        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Could not create support ticket") from exc

    return {"status": "ok", "ticket_id": ticket_id}


@router.get("/support/tickets")
async def list_support_tickets(
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    res = await db.execute(
        text(
            """
            SELECT id, subject, status, priority, created_at, updated_at
            FROM support_tickets
            WHERE client_id = :cid
            ORDER BY updated_at DESC
            LIMIT 20
            """
        ),
        {"cid": client_id},
    )
    tickets = [dict(r) for r in res.mappings().all()]
    return {"tickets": tickets}

