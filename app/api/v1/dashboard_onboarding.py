import json
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.onboarding import ClientOnboardIn
from pydantic import BaseModel
from fastapi import HTTPException
from openai import OpenAI
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/onboarding")
async def onboarding_page(request: Request):
    """
    Serve the client onboarding intake form.
    """
    return templates.TemplateResponse(
        "dashboard/onboarding.html",
        {"request": request},
    )


class PromptGenRequest(BaseModel):
    raw_text: str


@router.post("/onboarding/generate-prompt")
async def generate_prompt(
    payload: PromptGenRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    user = getattr(request.state, "user", None)
    client_id = getattr(user, "id", None) if user else None
    if not client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Get OpenAI key from credentials
    cred_row = await db.execute(
        text(
            """
            SELECT openai_api_key
            FROM credentials
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    cred = cred_row.mappings().first()
    api_key = cred.get("openai_api_key") if cred else None
    if not api_key:
        # Fallback to server key so early users can generate a prompt before providing theirs
        api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OpenAI key found. Add your key in Integrations or set OPENAI_API_KEY on the server.",
        )

    system_prompt = (
        "You are a prompt builder. Convert the user's rough business notes into a polished, structured system prompt "
        "for a website AI assistant. Include services, offers, policies, tone, booking/lead handling, FAQs, and automation goals. "
        "Return only the final prompt text, concise and ready to paste."
    )

    try:
        client = OpenAI(
            api_key=api_key,
            default_headers={"OpenAI-Beta": "assistants=v2"},
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": payload.raw_text},
            ],
        )
        content = resp.choices[0].message.content if resp.choices else ""
        return {"prompt": content}
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error generating prompt: {exc}")


@router.post("/onboarding")
async def submit_onboarding(
    payload: ClientOnboardIn,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    user = getattr(request.state, "user", None)
    client_id = getattr(user, "id", None) if user else None
    if not client_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    # Ensure a matching client row exists for FK; upsert minimal stub using user email.
    try:
        user_email_row = await db.execute(
            text("SELECT email FROM users WHERE id = :uid LIMIT 1"),
            {"uid": client_id},
        )
        user_email = user_email_row.scalar_one_or_none()
    except Exception:
        user_email = None

    if not user_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User email missing for onboarding")

    await db.execute(
        text(
            """
            INSERT INTO clients (id, email, name, created_at)
            VALUES (:cid, :email, :name, NOW())
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {"cid": client_id, "email": user_email, "name": payload.business_name},
    )

    wants_calling = payload.calling_direction != "none"
    wants_sms = payload.wants_sms if wants_calling else False
    wants_payments = payload.wants_payments
    uses_cloudflare = payload.uses_cloudflare

    twilio_sid = payload.twilio_sid if wants_calling else None
    twilio_token = payload.twilio_token.get_secret_value() if wants_calling and payload.twilio_token else None
    twilio_from_number = payload.twilio_from_number if wants_calling else None

    stripe_publishable_key = payload.stripe_publishable_key if wants_payments else None
    stripe_secret_key = payload.stripe_secret_key.get_secret_value() if wants_payments and payload.stripe_secret_key else None
    openai_api_key = payload.openai_api_key.get_secret_value() if payload.openai_api_key else None

    cloudflare_email = str(payload.cloudflare_email) if uses_cloudflare and payload.cloudflare_email else None

    # Upsert credentials without relying on a unique constraint
    cred_existing = await db.execute(
        text("SELECT id FROM credentials WHERE client_id = :cid LIMIT 1"),
        {"cid": client_id},
    )
    cred_row = cred_existing.mappings().first()

    if cred_row:
        await db.execute(
            text(
                """
                UPDATE credentials SET
                    stripe_publishable_key = COALESCE(:spk, stripe_publishable_key),
                    stripe_secret_key     = COALESCE(:ssk, stripe_secret_key),
                    openai_api_key        = COALESCE(:oak, openai_api_key),
                    twilio_sid            = COALESCE(:tsid, twilio_sid),
                    twilio_token          = COALESCE(:ttok, twilio_token),
                    twilio_from_number    = COALESCE(:tfrom, twilio_from_number),
                    updated_at            = NOW()
                WHERE client_id = :cid
                """
            ),
            {
                "cid": client_id,
                "spk": stripe_publishable_key,
                "ssk": stripe_secret_key,
                "oak": openai_api_key,
                "tsid": twilio_sid,
                "ttok": twilio_token,
                "tfrom": twilio_from_number,
            },
        )
    else:
        await db.execute(
            text(
                """
                INSERT INTO credentials (
                    client_id,
                    stripe_publishable_key, stripe_secret_key,
                    openai_api_key, twilio_sid, twilio_token, twilio_from_number, dns_api_key,
                    created_at, updated_at
                )
                VALUES (
                    :cid,
                    :spk, :ssk,
                    :oak, :tsid, :ttok, :tfrom, NULL,
                    NOW(), NOW()
                )
                """
            ),
            {
                "cid": client_id,
                "spk": stripe_publishable_key,
                "ssk": stripe_secret_key,
                "oak": openai_api_key,
                "tsid": twilio_sid,
                "ttok": twilio_token,
                "tfrom": twilio_from_number,
            },
        )

    params = {
        "client_id": client_id,
        "full_name": payload.full_name,
        "business_name": payload.business_name,
        "industry": payload.industry,
        "site_description": payload.site_description,
        "target_audience": payload.target_audience,
        "phone": payload.phone,
        "domain_name": payload.domain_name,
        "lead_forward_email": str(payload.lead_forward_email),
        "calling_direction": payload.calling_direction,
        "wants_sms": wants_sms,
        "wants_payments": wants_payments,
        "uses_cloudflare": uses_cloudflare,
        "cloudflare_email": cloudflare_email,
        "has_logo": payload.has_logo,
        "brand_colors": payload.brand_colors,
        "logo_url": payload.logo_url,
    }

    update_result = await db.execute(
        text(
            """
            UPDATE client_onboarding SET
                full_name = :full_name,
                business_name = :business_name,
                industry = :industry,
                site_description = :site_description,
                target_audience = :target_audience,
                phone = :phone,
                domain_name = :domain_name,
                lead_forward_email = :lead_forward_email,
                calling_direction = :calling_direction,
                wants_sms = :wants_sms,
                wants_payments = :wants_payments,
                uses_cloudflare = :uses_cloudflare,
                cloudflare_email = :cloudflare_email,
                has_logo = :has_logo,
                brand_colors = :brand_colors,
                logo_url = :logo_url,
                created_at = COALESCE(created_at, NOW())
            WHERE client_id = :client_id
            """
        ),
        params,
    )

    if update_result.rowcount == 0:
        await db.execute(
            text(
                """
                INSERT INTO client_onboarding (
                    client_id,
                    full_name,
                    business_name,
                    industry,
                    site_description,
                    target_audience,
                    phone,
                    domain_name,
                    lead_forward_email,
                    calling_direction,
                    wants_sms,
                    wants_payments,
                    uses_cloudflare,
                    cloudflare_email,
                    has_logo,
                    brand_colors,
                    logo_url,
                    created_at
                )
                VALUES (
                    :client_id,
                    :full_name,
                    :business_name,
                    :industry,
                    :site_description,
                    :target_audience,
                    :phone,
                    :domain_name,
                    :lead_forward_email,
                    :calling_direction,
                    :wants_sms,
                    :wants_payments,
                    :uses_cloudflare,
                    :cloudflare_email,
                    :has_logo,
                    :brand_colors,
                    :logo_url,
                    NOW()
                )
                """
            ),
            params,
        )

    # Activity log (optional; skip if table is missing)
    try:
        await db.execute(
            text(
                """
                INSERT INTO activity_logs (client_id, action, meta, created_at)
                VALUES (:client_id, 'client_onboarding_submitted', CAST(:meta_json AS jsonb), NOW())
                """
            ),
            {
                "client_id": client_id,
                "meta_json": json.dumps(
                    {
                        "calling_direction": payload.calling_direction,
                        "wants_sms": wants_sms,
                        "wants_payments": wants_payments,
                        "uses_cloudflare": uses_cloudflare,
                    }
                ),
            },
        )
    except Exception:
        # If activity_logs table doesn't exist, continue without blocking onboarding
        pass

    await db.commit()

    return {"status": "onboarding_saved", "client_id": client_id}
