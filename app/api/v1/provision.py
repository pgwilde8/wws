from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.middleware.auth import _get_client_id

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None

router = APIRouter(prefix="/api/provision", tags=["Provision"])


async def _get_client(conn: AsyncSession, client_id: int) -> Optional[dict]:
    res = await conn.execute(
        text(
            """
            SELECT id, openai_assistant_id, assistant_status,
                   twilio_voice_agent_sid, twilio_status
            FROM clients
            WHERE id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    row = res.mappings().first()
    return dict(row) if row else None


async def _get_credentials(conn: AsyncSession, client_id: int) -> dict:
    res = await conn.execute(
        text(
            """
            SELECT stripe_publishable_key, stripe_secret_key,
                   openai_api_key, twilio_sid, twilio_token, twilio_from_number, dns_api_key
            FROM credentials
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    row = res.mappings().first()
    return dict(row) if row else {}


@router.get("/status")
async def provision_status(
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    client = await _get_client(db, client_id) or {}
    creds = await _get_credentials(db, client_id)
    return {
        "assistant": {
            "id": client.get("openai_assistant_id"),
            "status": client.get("assistant_status") or "not_provisioned",
        },
        "twilio": {
            "id": client.get("twilio_voice_agent_sid"),
            "status": client.get("twilio_status") or "not_provisioned",
            "from_number": creds.get("twilio_from_number"),
        },
    }


@router.post("/openai-assistant")
async def create_openai_assistant(
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    creds = await _get_credentials(db, client_id)
    api_key = creds.get("openai_api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="OpenAI key not found. Save it first.")
    if OpenAI is None:
        raise HTTPException(
            status_code=500,
            detail="OpenAI SDK not installed on server. Install 'openai' to proceed.",
        )

    client = OpenAI(api_key=api_key)
    try:
        assistant = client.beta.assistants.create(
            name="WebWise Assistant",
            instructions="You are the assistant for a WebWise Solutions client.",
            model="gpt-4o-mini",
        )
    except Exception as exc:  # pragma: no cover - external API failure
        raise HTTPException(status_code=502, detail=f"OpenAI error: {exc}") from exc

    await db.execute(
        text(
            """
            UPDATE clients
            SET openai_assistant_id = :aid,
                assistant_status = 'provisioned'
            WHERE id = :cid
            """
        ),
        {"aid": assistant.id, "cid": client_id},
    )
    await db.commit()
    return {"status": "ok", "assistant_id": assistant.id}


@router.post("/twilio-caller")
async def create_twilio_caller(
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    creds = await _get_credentials(db, client_id)
    sid = creds.get("twilio_sid")
    token = creds.get("twilio_token")
    from_number = creds.get("twilio_from_number")
    if not sid or not token:
        raise HTTPException(status_code=400, detail="Twilio SID/Token not found. Save them first.")
    if not from_number:
        raise HTTPException(status_code=400, detail="Twilio from-number not found. Add it first.")

    # For now, store the intent to provision and record the from-number; external provisioning can be added later.
    fake_agent_sid = f"agent-{uuid.uuid4()}"
    await db.execute(
        text(
            """
            UPDATE clients
            SET twilio_voice_agent_sid = :sid_val,
                twilio_status = 'recorded'
            WHERE id = :cid
            """
        ),
        {"sid_val": fake_agent_sid, "cid": client_id},
    )
    await db.commit()
    return {"status": "ok", "voice_agent_sid": fake_agent_sid, "from_number": from_number}

