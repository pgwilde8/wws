from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi.templating import Jinja2Templates
from app.db.session import get_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def webhooks_page(request: Request, db: AsyncSession = Depends(get_session)):
    res = await db.execute(
        text(
            """
            SELECT id, event_type, status, received_at
            FROM webhook_events
            ORDER BY received_at DESC
            LIMIT 20
            """
        )
    )
    events = [dict(r) for r in res.mappings().all()]
    return templates.TemplateResponse(
        "admin/webhooks.html",
        {"request": request, "events": events},
    )


@router.get("/{event_id}")
async def webhook_detail(request: Request, event_id: int, db: AsyncSession = Depends(get_session)):
    res = await db.execute(
        text(
            """
            SELECT id, event_type, status, received_at, raw_payload
            FROM webhook_events
            WHERE id = :eid
            LIMIT 1
            """
        ),
        {"eid": event_id},
    )
    row = res.mappings().first()
    return templates.TemplateResponse(
        "admin/webhook_detail.html",
        {"request": request, "event": dict(row) if row else None},
    )


