from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.middleware.auth import _get_client_id

router = APIRouter()


class CredentialsPayload(BaseModel):
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    twilio_sid: Optional[str] = None
    twilio_token: Optional[str] = None
    dns_api_key: Optional[str] = None


def _mask(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    if len(value) <= 4:
        return "****"
    return f"{'*' * (len(value) - 4)}{value[-4:]}"


@router.get("/credentials")
async def get_credentials(
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    res = await db.execute(
        text(
            """
            SELECT stripe_publishable_key, stripe_secret_key,
                   openai_api_key, twilio_sid, twilio_token, dns_api_key
            FROM credentials
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    row = res.mappings().first()
    if not row:
        return {
            "stripe": {"connected": False, "publishable_key": None, "secret_key": None},
            "openai": {"connected": False, "api_key": None},
            "twilio": {"connected": False, "sid": None, "token": None},
            "dns": {"connected": False, "api_key": None},
        }

    return {
        "stripe": {
            "connected": bool(row.get("stripe_secret_key") or row.get("stripe_publishable_key")),
            "publishable_key": _mask(row.get("stripe_publishable_key")),
            "secret_key": _mask(row.get("stripe_secret_key")),
        },
        "openai": {
            "connected": bool(row.get("openai_api_key")),
            "api_key": _mask(row.get("openai_api_key")),
        },
        "twilio": {
            "connected": bool(row.get("twilio_sid") or row.get("twilio_token")),
            "sid": _mask(row.get("twilio_sid")),
            "token": _mask(row.get("twilio_token")),
        },
        "dns": {
            "connected": bool(row.get("dns_api_key")),
            "api_key": _mask(row.get("dns_api_key")),
        },
    }


@router.post("/credentials")
async def upsert_credentials(
    payload: CredentialsPayload,
    db: AsyncSession = Depends(get_session),
    client_id: int = Depends(_get_client_id),
):
    params = {
        "cid": client_id,
        "spk": payload.stripe_publishable_key,
        "ssk": payload.stripe_secret_key,
        "oak": payload.openai_api_key,
        "tsid": payload.twilio_sid,
        "ttok": payload.twilio_token,
        "dns": payload.dns_api_key,
    }

    try:
        existing = await db.execute(
            text(
                """
                SELECT id,
                       stripe_publishable_key, stripe_secret_key,
                       openai_api_key, twilio_sid, twilio_token, dns_api_key
                FROM credentials
                WHERE client_id = :cid
                LIMIT 1
                """
            ),
            {"cid": client_id},
        )
        row = existing.mappings().first()

        if row:
            await db.execute(
                text(
                    """
                    UPDATE credentials SET
                        stripe_publishable_key = COALESCE(:spk, stripe_publishable_key),
                        stripe_secret_key = COALESCE(:ssk, stripe_secret_key),
                        openai_api_key = COALESCE(:oak, openai_api_key),
                        twilio_sid = COALESCE(:tsid, twilio_sid),
                        twilio_token = COALESCE(:ttok, twilio_token),
                        dns_api_key = COALESCE(:dns, dns_api_key),
                        updated_at = NOW()
                    WHERE client_id = :cid
                    """
                ),
                params,
            )
        else:
            await db.execute(
                text(
                    """
                    INSERT INTO credentials (
                        client_id,
                        stripe_publishable_key, stripe_secret_key,
                        openai_api_key, twilio_sid, twilio_token, dns_api_key,
                        created_at, updated_at
                    )
                    VALUES (
                        :cid,
                        :spk, :ssk,
                        :oak, :tsid, :ttok, :dns,
                        NOW(), NOW()
                    )
                    """
                ),
                params,
            )

        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save credentials.") from exc

    return {"status": "saved"}

