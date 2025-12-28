from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_session
from app.middleware.auth import _get_client_id  # now provided by middleware

router = APIRouter()


class ForwardEmailPayload(BaseModel):
    forward_email: EmailStr


@router.post("/lead-forwarding")
async def save_forward_email(
    payload: ForwardEmailPayload,
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    try:
        await db.execute(
            text(
                """
                INSERT INTO lead_forward_emails (client_id, email, created_at)
                VALUES (:client_id, :email, NOW())
                ON CONFLICT (client_id, email) DO UPDATE SET created_at = NOW()
                """
            ),
            {"client_id": client_id, "email": payload.forward_email},
        )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save forwarding email.") from exc

    return {"status": "saved", "email": payload.forward_email}


@router.get("/lead-forwarding")
async def get_forward_email(
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    res = await db.execute(
        text(
            """
            SELECT email, created_at
            FROM lead_forward_emails
            WHERE client_id = :client_id
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"client_id": client_id},
    )
    row = res.mappings().first()
    if not row:
        return {}
    return dict(row)

