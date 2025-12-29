from fastapi import APIRouter, Depends, Request, Query, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, func
from types import SimpleNamespace
from app.db.session import get_session
from fastapi.templating import Jinja2Templates
from app.services.provisioning import provision_openai_assistant, provision_twilio_voice

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

# ADMIN DASHBOARD (client-focused)
@router.get("/admin")
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    total_clients = (await db.execute(text("SELECT COUNT(*) FROM clients"))).scalar() or 0
    total_projects = (await db.execute(text("SELECT COUNT(*) FROM projects"))).scalar() or 0
    total_orders = (await db.execute(text("SELECT COUNT(*) FROM orders"))).scalar() or 0

    # Latest clients with onboarding snapshot
    rows = await db.execute(
        text(
            """
            SELECT
              c.id,
              COALESCE(c.name, o.business_name) AS display_name,
              c.email,
              o.domain_name,
              o.lead_forward_email,
              o.created_at AS submitted_at
            FROM clients c
            LEFT JOIN client_onboarding o ON o.client_id = c.id
            ORDER BY COALESCE(o.created_at, c.created_at) DESC
            LIMIT 10
            """
        )
    )
    clients_preview = rows.mappings().all()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "total_clients": total_clients or 0,
            "total_projects": total_projects or 0,
            "total_orders": total_orders or 0,
            "active_subs": 0,
            "clients_preview": clients_preview,
        },
    )

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


@router.get("/admin/clients/by-email")
async def client_lookup_by_email(
    email: str = Query(..., min_length=3),
    request: Request = None,
    db: AsyncSession = Depends(get_session),
):
    res = await db.execute(
        text("SELECT id FROM clients WHERE email = :email LIMIT 1"),
        {"email": email},
    )
    cid = res.scalar_one_or_none()
    if cid:
        return RedirectResponse(url=f"/admin/clients/{cid}", status_code=302)
    # reuse not-found template
    return templates.TemplateResponse(
        "admin/client_not_found.html",
        {"request": request},
        status_code=404,
    )


@router.get("/admin/clients/{client_id}")
async def client_detail(
    client_id: int,
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    client_row = await db.execute(
        text(
            """
            SELECT id, name, email,
                   openai_assistant_id, assistant_status,
                   twilio_voice_agent_sid, twilio_status,
                   stripe_account_id, created_at
            FROM clients
            WHERE id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    client = client_row.mappings().first()
    if not client:
        return templates.TemplateResponse("admin/client_not_found.html", {"request": request}, status_code=404)

    onboarding_row = await db.execute(
        text(
            """
            SELECT
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
                twilio_sid,
                twilio_from_number,
                stripe_publishable_key,
                has_logo,
                brand_colors,
                created_at
            FROM client_onboarding
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    onboarding = onboarding_row.mappings().first()

    cred_row = await db.execute(
        text(
            """
            SELECT
                stripe_publishable_key,
                stripe_secret_key,
                openai_api_key,
                twilio_sid,
                twilio_token,
                twilio_from_number,
                dns_api_key
            FROM credentials
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    credentials = cred_row.mappings().first()

    return templates.TemplateResponse(
        "admin/client_detail.html",
        {
            "request": request,
            "client": client,
            "onboarding": onboarding,
            "credentials": credentials,
        },
    )


@router.get("/admin/clients/{client_id}/credentials/raw")
async def client_credentials_raw(
    client_id: int,
    db: AsyncSession = Depends(get_session),
):
    cred_row = await db.execute(
        text(
            """
            SELECT
                stripe_publishable_key,
                stripe_secret_key,
                openai_api_key,
                twilio_sid,
                twilio_token,
                twilio_from_number,
                dns_api_key
            FROM credentials
            WHERE client_id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    credentials = cred_row.mappings().first()
    if not credentials:
        raise HTTPException(status_code=404, detail="No credentials for this client.")
    return {"credentials": dict(credentials)}


@router.post("/admin/clients/{client_id}/provision/openai")
async def admin_provision_openai(
    client_id: int,
    db: AsyncSession = Depends(get_session),
):
    await provision_openai_assistant(client_id, db)
    return {"status": "ok"}


@router.post("/admin/clients/{client_id}/provision/twilio")
async def admin_provision_twilio(
    client_id: int,
    db: AsyncSession = Depends(get_session),
):
    await provision_twilio_voice(client_id, db)
    return {"status": "ok"}


@router.get("/admin/clients/{client_id}/provision/raw")
async def admin_provision_raw(
    client_id: int,
    db: AsyncSession = Depends(get_session),
):
    row = await db.execute(
        text(
            """
            SELECT openai_assistant_id, twilio_voice_agent_sid
            FROM clients
            WHERE id = :cid
            LIMIT 1
            """
        ),
        {"cid": client_id},
    )
    data = row.mappings().first()
    if not data:
        raise HTTPException(status_code=404, detail="Client not found.")
    return {"provisioning": dict(data)}
